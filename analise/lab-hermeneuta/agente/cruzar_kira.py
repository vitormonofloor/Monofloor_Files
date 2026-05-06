"""
cruzar_kira.py · Cruzamento determinístico Kira × Operação · v2 (pacote completo)
===================================================================================

Pega o que o Kira já interpretou no Painel (tagKira, situacaoAtual, ocorrencias,
materiais, equipe, fases, datas) e compara com status macro pra detectar
discrepâncias. Zero IA · zero rate limit · auditável.

REGRAS:
  R1 · tagKira indica concluído mas status ativo  → status_desatualizado
  R2 · ocorrência severidade alta/critica em 7d   → urgência alta + flag
  R3 · situacaoAtual com URGENTE/RISCO/atraso     → flags
  R4 · dias_silencio ≥30 + obra ativa              → abandono
  R5 · label "REAPLICAÇÃO" OU /materiais com       → flag reaplicacao
       tipoSuperficie="Reaplicação"
  R6 · pendenciaManual.industriaCheck.*=false      → flag os_pendente / projeto_pendente
  R7 · dataExecucaoConfirmada após dataExecucaoPrevista
       OU dataTerminoPrevista passada com obra ativa  → flag atrasado + atraso_dias

EFEITOS COLATERAIS POSITIVOS (resolvem defasagem do detail-snapshot LOCAL):
  - Salva detail fresco em dados/details-snapshot/{id}.json (cascata pros outros scripts)
  - Mapeia obra.consultor = responsavelOperacoes || consultorNome (dono REAL na operação)
  - Adiciona obra.painel.labels (lista completa, não só fase_atual)
  - Adiciona obra.painel.atraso_dias (diferença prevista × confirmada)
  - Adiciona obra.kira_materiais (totais simples · m², ambientes, usaTela, items count)
  - Adiciona obra.kira_equipe (líder + aplicadores nomeados, do endpoint /equipe)

Saída: discordancias-v3.json + atualização de details-snapshot/*.json
Uso: python cruzar_kira.py
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import setup_utf8, write_discord

setup_utf8()

ROOT = Path(__file__).parent.parent
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"
DETAIL_SNAPSHOT_DIR = ROOT / "dados" / "details-snapshot"  # local pro Lab Orion
DETAIL_GLOBAL_DIR = ROOT.parent / "dados" / "details"  # global · usado por extrair_kira_whatsapp e outros (mantido também por refresh.sh externo)
BASE_API = "https://cliente.monofloor.cloud/api/projects"
HOJE = datetime.now(timezone.utc)
HOJE_DATE = HOJE.date()
JANELA_OCORRENCIA_DIAS = 7
SILENCIO_ABANDONO_DIAS = 30
ATRASO_TOLERANCIA_DIAS = 7  # tolerância antes de marcar flag atrasado

# Regex pra R3 (texto livre do Kira em situacaoAtual)
PAD_URGENTE = re.compile(r"\b(URGENTE|EMERGÊNC|EMERGENC|CRÍTIC|CRITIC|RISCO ALTO)\b", re.IGNORECASE)
PAD_RISCO = re.compile(r"\b(risco|patolog|fissur|infiltrac|trinca|rachadura)\b", re.IGNORECASE)
PAD_ATRASO = re.compile(r"\b(atraso|atrasad|prazo passad|janela.*perdid)\b", re.IGNORECASE)


def fetch(url: str, max_retries: int = 2):
    """GET JSON com retry simples."""
    last_err = None
    for tentativa in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "lab-orion/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            last_err = e
            if tentativa < max_retries:
                time.sleep(2 ** tentativa)
    raise RuntimeError(f"fetch falhou: {last_err}")


def fetch_safe(url: str):
    """Como fetch mas retorna None em caso de erro · não trava varredura."""
    try:
        return fetch(url, max_retries=1)
    except Exception:
        return None


def parse_iso(s: str):
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except (ValueError, TypeError):
        return None


def parse_data_simples(s):
    """YYYY-MM-DD → date · ou None."""
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def salvar_detail_snapshot(oid: str, detail: dict):
    """Salva detail fresco em AMBOS os diretórios (cascata pros outros scripts):
    - lab-hermeneuta/dados/details-snapshot/ (local · backup)
    - analise/dados/details/ (global · onde extrair_kira_whatsapp e inferir_consultor leem)
    """
    payload = json.dumps(detail, ensure_ascii=False, indent=2)
    for dir_path in (DETAIL_SNAPSHOT_DIR, DETAIL_GLOBAL_DIR):
        if not dir_path.exists():
            continue
        path = dir_path / f"{oid}.json"
        try:
            tmp = path.with_suffix(".tmp")
            tmp.write_text(payload, encoding="utf-8")
            tmp.replace(path)
        except OSError:
            pass


def aplicar_regras(obra_v3: dict, detail: dict, ocorrencias: list,
                   materiais: dict, equipe: dict, fases: dict) -> dict:
    """Aplica R1-R7. Retorna dict com mudanças + trilha auditável."""
    trilha = []
    flags = set()
    veredicto = "coerente"
    urgencia = "baixa"
    status_sugerido = None

    status_atual = (detail.get("status") or "").lower()
    tagKira = (detail.get("tagKira") or "").strip()
    tagKira_lower = tagKira.lower()
    situacao = detail.get("situacaoAtual") or ""
    acessoDet = detail.get("acessoDetalhes") or {}
    labels = acessoDet.get("labels") or []

    # ============ R1 · tagKira indica concluído mas status ainda ativo ============
    indica_concluido = bool(re.search(r"conclu[ií]d|finaliza[dç]|encerrad", tagKira_lower))
    if indica_concluido and status_atual not in ("concluido", "finalizado"):
        veredicto = "status_desatualizado"
        status_sugerido = "concluido"
        trilha.append(f"R1 · tagKira='{tagKira}' indica concluído · status atual='{status_atual}'")

    # ============ R2 · ocorrência alta OU crítica nos últimos 7 dias ============
    cutoff = HOJE - timedelta(days=JANELA_OCORRENCIA_DIAS)
    altas_recentes = []
    for oc in ocorrencias or []:
        sev = oc.get("severidade")
        if sev not in ("alta", "critica"):
            continue
        dt = parse_iso(oc.get("createdAt") or oc.get("data"))
        if dt and dt >= cutoff:
            altas_recentes.append(oc)
    if altas_recentes:
        urgencia = "alta"
        for oc in altas_recentes[:3]:
            tipo = oc.get("tipo") or "ocorrencia"
            sev = oc.get("severidade") or "?"
            titulo = (oc.get("titulo") or "")[:80]
            trilha.append(f"R2 · ocorrência {sev} '{tipo}' · {titulo}")
            if "comunic" in tipo:
                flags.add("silencio_anomalo")
            elif "qualid" in tipo or "tecnic" in tipo:
                flags.add("risco_tecnico")

    # ============ R3 · situacaoAtual com palavras-chave ============
    if PAD_URGENTE.search(situacao):
        urgencia = "alta"
        trilha.append("R3a · situacaoAtual contém palavra urgente/crítico")
    if PAD_RISCO.search(situacao):
        flags.add("risco_tecnico")
        trilha.append("R3b · situacaoAtual contém palavra de risco/patologia")
    if PAD_ATRASO.search(situacao):
        flags.add("atrasado")
        trilha.append("R3c · situacaoAtual contém palavra de atraso")

    # ============ R4 · silêncio prolongado em obra ativa ============
    tg = obra_v3.get("telegram") or {}
    dias_silencio = tg.get("dias_silencio")
    if (
        isinstance(dias_silencio, int)
        and dias_silencio >= SILENCIO_ABANDONO_DIAS
        and status_atual not in ("concluido", "finalizado")
    ):
        veredicto = "abandono"
        urgencia = "alta"
        trilha.append(f"R4 · dias_silencio={dias_silencio} + status='{status_atual}'")

    # ============ R5 · reaplicação detectada ============
    labels_upper = [str(l).upper() for l in labels]
    if any("REAPLICA" in l for l in labels_upper):
        flags.add("reaplicacao")
        trilha.append("R5a · label 'REAPLICAÇÃO' presente · obra é retrabalho")
    matitems = (materiais or {}).get("items") or []
    reaplic_count = sum(
        1 for m in matitems
        if "reaplica" in (m.get("tipoSuperficie") or "").lower()
    )
    if reaplic_count > 0:
        flags.add("reaplicacao")
        trilha.append(f"R5b · {reaplic_count} item(s) /materiais com tipoSuperficie='Reaplicação'")

    # ============ R6 · pendência industrial ============
    pm = (detail.get("pendenciaManual") or {}).get("industriaCheck") or {}
    if pm.get("osOk") is False:
        flags.add("os_pendente")
        trilha.append("R6a · pendenciaManual.industriaCheck.osOk=false · OS pendente")
    if pm.get("projetoOk") is False:
        flags.add("projeto_pendente")
        trilha.append("R6b · pendenciaManual.industriaCheck.projetoOk=false · projeto pendente")

    # ============ R7 · atraso real ============
    dPrevista = parse_data_simples(detail.get("dataExecucaoPrevista"))
    dConfirmada = parse_data_simples(detail.get("dataExecucaoConfirmada"))
    dTermino = parse_data_simples(acessoDet.get("dataTerminoPrevista"))
    atraso_dias = None
    if dPrevista and dConfirmada:
        delta = (dConfirmada - dPrevista).days
        atraso_dias = delta
        if delta > ATRASO_TOLERANCIA_DIAS:
            flags.add("atrasado")
            trilha.append(f"R7a · dataExecucaoConfirmada {delta}d após dataExecucaoPrevista")
    if dTermino and status_atual not in ("concluido", "finalizado"):
        dias_passados = (HOJE_DATE - dTermino).days
        if dias_passados > 0:
            flags.add("atrasado")
            trilha.append(f"R7b · dataTerminoPrevista venceu há {dias_passados}d · obra ainda ativa")

    # ============ Ação consultor (templates · prioridade do mais grave) ============
    if veredicto == "abandono":
        acao = "Verificar com cliente · obra silenciada há mais de 30 dias"
    elif veredicto == "status_desatualizado":
        acao = f"Atualizar painel · Kira indica '{tagKira or 'concluído'}'"
    elif "risco_tecnico" in flags:
        acao = "Validar técnico em campo · risco identificado"
    elif "silencio_anomalo" in flags:
        acao = "Responder cliente em até 48h"
    elif "reaplicacao" in flags and ("os_pendente" in flags or "projeto_pendente" in flags):
        acao = "Reaplicação com pendência industrial · destravar OS/projeto"
    elif "atrasado" in flags:
        acao = "Validar prazo · sinal de atraso"
    elif "os_pendente" in flags or "projeto_pendente" in flags:
        acao = "Resolver pendência industrial (OS ou projeto)"
    elif urgencia == "alta":
        acao = "Revisar obra · urgência alta detectada"
    else:
        acao = None

    # ============ Tipo demanda (casos óbvios) ============
    if veredicto == "abandono":
        tipo_demanda = "pausa"
    elif status_sugerido == "concluido":
        tipo_demanda = "finalizacao"
    elif "reaplicacao" in flags:
        tipo_demanda = "retrabalho_acabamento"
    elif "risco_tecnico" in flags:
        tipo_demanda = "patologia"
    else:
        tipo_demanda = None

    # ============ Resumos pro JSON (consumíveis pela UI) ============
    # Equipe real (do endpoint /equipe · não da heurística msgs)
    kira_equipe = None
    if equipe:
        prestadores = equipe.get("prestadores") or []
        lider = next((p for p in prestadores if (p.get("funcao") or "").upper() == "LIDER"), None)
        kira_equipe = {
            "lider": (lider or {}).get("nome"),
            "aplicadores": [p.get("nome") for p in prestadores if "APLICADOR" in (p.get("funcao") or "").upper()],
            "outros": [p.get("nome") for p in prestadores if "APLICADOR" not in (p.get("funcao") or "").upper() and (p.get("funcao") or "").upper() != "LIDER"],
            "total_prestadores": len(prestadores),
        }

    # Materiais resumo (do endpoint /materiais)
    kira_materiais = None
    if materiais:
        totals = materiais.get("totals") or {}
        kira_materiais = {
            "total_m2": totals.get("totalM2"),
            "stelion_m2": totals.get("stelionM2"),
            "lilit_m2": totals.get("lilitM2"),
            "ambientes": totals.get("ambientes"),
            "n_items": len(matitems),
            "n_reaplicacao": reaplic_count,
            "produtos": sorted({(m.get("produto") or "").strip() for m in matitems if m.get("produto")}),
            "cores": sorted({(m.get("cor") or "").strip() for m in matitems if m.get("cor")}),
            "todos_concluidos": all(m.get("concluido") for m in matitems) if matitems else None,
        }

    # Dono operacional REAL (responsavelOperacoes > consultorNome > deixa o que tinha)
    consultor_real = detail.get("responsavelOperacoes") or detail.get("consultorNome")

    return {
        "veredicto": veredicto,
        "urgencia": urgencia,
        "flags": sorted(flags),
        "status_sugerido": status_sugerido,
        "tipo_demanda": tipo_demanda,
        "acao_consultor": acao,
        "analise_kira_trilha": trilha,
        "analise_kira_em": HOJE.strftime("%Y-%m-%dT%H:%M:%SZ"),
        # Campos novos · disponíveis pra UI / outros scripts
        "_consultor_real": consultor_real,         # se != None, sobrescreve obra.consultor
        "_painel_labels": labels,                  # array completo de labels do Painel
        "_painel_atraso_dias": atraso_dias,        # int (positivo = atraso) ou None
        "_kira_equipe": kira_equipe,
        "_kira_materiais": kira_materiais,
    }


def main():
    if not DISCORD_PATH.exists():
        print(f"ERRO: {DISCORD_PATH} não encontrado")
        sys.exit(1)

    data = json.loads(DISCORD_PATH.read_text(encoding="utf-8"))
    obras_v3 = data.get("obras", [])
    ativas = [
        o for o in obras_v3
        if (o.get("painel") or {}).get("status_atual") not in ("concluido", "finalizado")
    ]
    print(f"Cruzando {len(ativas)} obras ativas (de {len(obras_v3)} totais) · 5 endpoints/obra · zero IA")
    print()

    sucesso = 0
    erros = 0
    contagem_v = {"coerente": 0, "status_desatualizado": 0, "abandono": 0}
    contagem_u = {"alta": 0, "media": 0, "baixa": 0}
    inicio = time.time()

    for i, obra_v3 in enumerate(ativas, 1):
        oid = obra_v3["obra_id"]
        cliente = (obra_v3.get("cliente") or "?")[:35]
        try:
            detail = fetch(f"{BASE_API}/{oid}")
        except Exception as e:
            print(f"  [{i}/{len(ativas)}] {cliente:<37} · ERRO detail: {str(e)[:60]}")
            erros += 1
            continue

        # Salva detail fresco no snapshot LOCAL (cascata pros outros scripts)
        salvar_detail_snapshot(oid, detail)

        # Endpoints adicionais (best-effort · não trava se falhar)
        ocorrencias = fetch_safe(f"{BASE_API}/{oid}/ocorrencias") or []
        materiais = fetch_safe(f"{BASE_API}/{oid}/materiais") or {}
        equipe = fetch_safe(f"{BASE_API}/{oid}/equipe") or {}
        fases = fetch_safe(f"{BASE_API}/{oid}/fases") or {}

        resultado = aplicar_regras(obra_v3, detail, ocorrencias, materiais, equipe, fases)

        # Aplica campos básicos
        for k in ("veredicto", "urgencia", "flags", "status_sugerido", "tipo_demanda",
                  "acao_consultor", "analise_kira_trilha", "analise_kira_em"):
            obra_v3[k] = resultado[k]

        # Sobrescreve consultor SE temos um real (responsavelOperacoes preenchido)
        if resultado["_consultor_real"]:
            obra_v3["consultor"] = resultado["_consultor_real"]

        # Adiciona labels múltiplas no bloco painel
        if resultado["_painel_labels"]:
            obra_v3.setdefault("painel", {})["labels"] = resultado["_painel_labels"]

        # Adiciona atraso_dias (mesmo se zero · vira KPI)
        if resultado["_painel_atraso_dias"] is not None:
            obra_v3.setdefault("painel", {})["atraso_dias"] = resultado["_painel_atraso_dias"]

        # Adiciona blocos kira_equipe e kira_materiais se temos
        if resultado["_kira_equipe"]:
            obra_v3["kira_equipe"] = resultado["_kira_equipe"]
        if resultado["_kira_materiais"]:
            obra_v3["kira_materiais"] = resultado["_kira_materiais"]

        sucesso += 1
        contagem_v[resultado["veredicto"]] = contagem_v.get(resultado["veredicto"], 0) + 1
        contagem_u[resultado["urgencia"]] = contagem_u.get(resultado["urgencia"], 0) + 1

        if i % 25 == 0 or i == len(ativas):
            elapsed = time.time() - inicio
            eta = (elapsed / i) * (len(ativas) - i)
            print(f"  [{i}/{len(ativas)}] · {elapsed:.0f}s · ETA {eta:.0f}s")

    write_discord(DISCORD_PATH, data)

    elapsed = time.time() - inicio
    print()
    print(f"[OK] {DISCORD_PATH} · {elapsed:.1f}s total · {sucesso} sucesso · {erros} erro")
    print(f"     Detail-snapshots atualizados em {DETAIL_SNAPSHOT_DIR}")
    print()
    print("Veredictos:")
    for v, n in contagem_v.items():
        print(f"  {n:4d}  {v}")
    print("Urgências:")
    for u, n in contagem_u.items():
        print(f"  {n:4d}  {u}")


if __name__ == "__main__":
    main()
