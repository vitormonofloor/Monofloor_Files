"""
cruzar_kira.py · Cruzamento determinístico Kira × Operação
===========================================================

Pega o que o Kira já interpretou no Painel (tagKira, situacaoAtual, ocorrencias)
e compara com o status macro pra detectar discrepâncias. Zero IA · zero rate limit.

4 REGRAS ESSENCIAIS:
  R1 · tagKira indica concluído mas status ainda ativo  → status_desatualizado
  R2 · ocorrência severidade=alta nos últimos 7 dias    → urgência alta + flag
  R3 · situacaoAtual contém URGENTE/RISCO/atraso        → flags correspondentes
  R4 · dias_silencio ≥ 30 e obra ativa                  → abandono

Saída: discordancias-v3.json com:
  veredicto · urgencia · flags · status_sugerido · acao_consultor
  + analise_kira_trilha (lista das regras que dispararam · AUDITÁVEL)
  + analise_kira_em (timestamp)

Uso: python cruzar_kira.py
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import setup_utf8, write_discord

setup_utf8()

ROOT = Path(__file__).parent.parent
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"
BASE_API = "https://cliente.monofloor.cloud/api/projects"
HOJE = datetime.now(timezone.utc)
JANELA_OCORRENCIA_DIAS = 7
SILENCIO_ABANDONO_DIAS = 30

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


def aplicar_regras(obra_v3: dict, detail: dict, ocorrencias: list) -> dict:
    """Aplica R1-R4. Retorna dict com mudanças + trilha auditável."""
    trilha = []
    flags = set()
    veredicto = "coerente"
    urgencia = "baixa"
    status_sugerido = None

    status_atual = (detail.get("status") or "").lower()
    tagKira = (detail.get("tagKira") or "").strip()
    tagKira_lower = tagKira.lower()
    situacao = detail.get("situacaoAtual") or ""

    # R1 · tagKira indica concluído mas status ainda ativo
    indica_concluido = bool(re.search(r"conclu[ií]d|finaliza[dç]|encerrad", tagKira_lower))
    if indica_concluido and status_atual not in ("concluido", "finalizado"):
        veredicto = "status_desatualizado"
        status_sugerido = "concluido"
        trilha.append(f"R1 · tagKira='{tagKira}' indica concluído · status atual='{status_atual}'")

    # R2 · ocorrência alta nos últimos 7 dias
    cutoff = HOJE - timedelta(days=JANELA_OCORRENCIA_DIAS)
    altas_recentes = []
    for oc in ocorrencias or []:
        if oc.get("severidade") != "alta":
            continue
        dt = parse_iso(oc.get("createdAt") or oc.get("data"))
        if dt and dt >= cutoff:
            altas_recentes.append(oc)
    if altas_recentes:
        urgencia = "alta"
        for oc in altas_recentes[:3]:
            tipo = oc.get("tipo") or "ocorrencia"
            titulo = (oc.get("titulo") or "")[:80]
            trilha.append(f"R2 · ocorrência alta '{tipo}' · {titulo}")
            if "comunic" in tipo:
                flags.add("silencio_anomalo")
            elif "qualid" in tipo or "tecnic" in tipo:
                flags.add("risco_tecnico")

    # R3 · situacaoAtual com palavras-chave (texto livre do Kira)
    if PAD_URGENTE.search(situacao):
        urgencia = "alta"
        trilha.append("R3a · situacaoAtual contém palavra urgente/crítico")
    if PAD_RISCO.search(situacao):
        flags.add("risco_tecnico")
        trilha.append("R3b · situacaoAtual contém palavra de risco/patologia")
    if PAD_ATRASO.search(situacao):
        flags.add("atrasado")
        trilha.append("R3c · situacaoAtual contém palavra de atraso")

    # R4 · silêncio prolongado em obra ativa
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

    # Ação do consultor (templates simples · prioridade do que dispara mais grave)
    if veredicto == "abandono":
        acao = "Verificar com cliente · obra silenciada há mais de 30 dias"
    elif veredicto == "status_desatualizado":
        acao = f"Atualizar painel · Kira indica '{tagKira or 'concluído'}'"
    elif "risco_tecnico" in flags:
        acao = "Validar técnico em campo · risco identificado"
    elif "silencio_anomalo" in flags:
        acao = "Responder cliente em até 48h"
    elif "atrasado" in flags:
        acao = "Validar prazo · sinal de atraso no painel"
    elif urgencia == "alta":
        acao = "Revisar obra · urgência alta detectada"
    else:
        acao = None

    return {
        "veredicto": veredicto,
        "urgencia": urgencia,
        "flags": sorted(flags),
        "status_sugerido": status_sugerido,
        "acao_consultor": acao,
        "analise_kira_trilha": trilha,
        "analise_kira_em": HOJE.strftime("%Y-%m-%dT%H:%M:%SZ"),
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
    print(f"Cruzando {len(ativas)} obras ativas (de {len(obras_v3)} totais) · zero IA · 2 fetches por obra")
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
            ocorrencias = fetch(f"{BASE_API}/{oid}/ocorrencias") or []
        except Exception as e:
            print(f"  [{i}/{len(ativas)}] {cliente:<37} · ERRO: {str(e)[:60]}")
            erros += 1
            continue

        resultado = aplicar_regras(obra_v3, detail, ocorrencias)
        for k, v in resultado.items():
            obra_v3[k] = v

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
    print()
    print("Veredictos:")
    for v, n in contagem_v.items():
        print(f"  {n:4d}  {v}")
    print("Urgências:")
    for u, n in contagem_u.items():
        print(f"  {n:4d}  {u}")


if __name__ == "__main__":
    main()
