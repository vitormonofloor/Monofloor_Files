"""
Aplica régua temporal Monofloor nos dossiês das obras
======================================================

Pra cada obra do piloto:
1. Extrai data_inicio (X) dos dossiês — varre datas_mencionadas + evidencias_fortes
   procurando por padrões "INÍCIO: DD/MM/AAAA" ou eventos com palavra "início"
2. Calcula bucket temporal (em_execucao / ≤7d / ≤20d / 20-60d / >60d / reparo / pausada)
3. Calcula 4 marcos SLA Monofloor (PP:001):
   - VT aferição:  X-60d
   - Cor escolhida: X-35d
   - VT entrada:    X-10d
   - Equipe:        X-7d
4. Cruza com flags do HERMENEUTA pra status do marco (aplicador_indefinido → Equipe pendente alta)
5. Injeta `regua` em cada obra do discordancias-v3.json

Custo: zero · roda local.
"""

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import write_discord, setup_utf8

setup_utf8()

ROOT = Path(__file__).parent.parent
DOSSIES_DIR = ROOT / "dados" / "dossies"
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"
SNAPSHOT_PATH = ROOT / "agente" / "telethon" / "telegram-snapshot.json"

HOJE = datetime.now(timezone.utc)

# SLAs PP:001 da Monofloor (dias antes do início X)
MARCOS_SLA = [
    {"id": "vt_afericao", "label": "VT aferição",   "antes_x": 60},
    {"id": "cor",         "label": "Cor escolhida", "antes_x": 35},
    {"id": "vt_entrada",  "label": "VT entrada",    "antes_x": 10},
    {"id": "equipe",      "label": "Equipe definida","antes_x": 7},
]

# Buckets temporais
def bucket_temporal(status: str, dias_ate_x: int | None) -> dict:
    """Retorna {id, label, cor, descricao}."""
    if status in ("concluido", "finalizado", "cancelado"):
        return {"id": "fechada", "label": "Fechada", "cor": "#c8bfb4", "descricao": "Fora do fluxo ativo"}
    if status in ("reparo", "marcas_rolo_cera"):
        return {"id": "reparo", "label": "Reparo / Retrabalho", "cor": "#9a3a3a", "descricao": "Patologia ou acabamento ativo"}
    if status in ("pausado", "aguardando_clima"):
        return {"id": "pausada", "label": "Pausada / Aguardando", "cor": "#b89a4a", "descricao": "Travada por clima ou outro motivo"}
    if status == "em_execucao":
        return {"id": "em_execucao", "label": "EM EXECUÇÃO", "cor": "#c45a5a", "descricao": "Obra acontecendo agora"}

    # planejamento, aguardando_execucao, contrato — depende de dias_ate_x
    if dias_ate_x is None:
        return {"id": "sem_data", "label": "Sem data definida", "cor": "#8a7e72", "descricao": "Início não fixado"}
    if dias_ate_x < 0:
        return {"id": "atrasada", "label": "ATRASADA · X passou", "cor": "#9a3a3a", "descricao": f"Data de início era {abs(dias_ate_x)}d atrás"}
    if dias_ate_x <= 7:
        return {"id": "entra_7d", "label": "Entra em ≤7d", "cor": "#c45a5a", "descricao": "Preparação crítica"}
    if dias_ate_x <= 20:
        return {"id": "entra_20d", "label": "Entra em ≤20d", "cor": "#d4943a", "descricao": "Atenção alta"}
    if dias_ate_x <= 60:
        return {"id": "entra_60d", "label": "Entra em 20-60d", "cor": "#7aa898", "descricao": "Acompanhamento médio"}
    return {"id": "futura", "label": f"Futura · {dias_ate_x}d", "cor": "#c8bfb4", "descricao": "Atenção baixa"}


# Padrões pra extrair data_inicio
RE_DATA_INI_TEXTO = re.compile(r"in[ií]cio[\s:]+(\d{2})[/\-](\d{2})[/\-](\d{4})", re.IGNORECASE)
RE_DATA_ISO       = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
RE_DATA_BR        = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


def parse_iso(s: str):
    if not s:
        return None
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except (ValueError, TypeError):
        return None


def extrair_data_inicio(dossie: dict, snapshot_obra: dict | None = None) -> dict:
    """
    Coleta candidatas de data_inicio + detecta REMARCAÇÕES.

    Retorna dict:
      - data_x: ISO da data atual (mais recente mencionada)
      - fonte: descrição da origem
      - data_anterior: ISO da data anterior distinta (se houve remarcação)
      - alterada: bool · True se há >=2 datas distintas
      - historico: lista cronológica de {data_x, msg_data, tipo}

    Lógica:
    1. Varre snapshot pra coletar TODAS as datas distintas em ordem cronológica
    2. A MAIS RECENTE (msg_data desc) é a atual
    3. A penúltima distinta é a anterior
    4. Se houver duas ou mais distintas → alterada=True
    """
    candidatos = []  # tuplas (data_x, fonte, msg_data_iso)
    KEYWORDS = ("início", "inicio", "reaplicação", "reaplicacao", "retorno", "data de inicio")

    # === FONTE 1: SNAPSHOT (mensagens recentes) — prioridade ===
    if snapshot_obra:
        msgs = snapshot_obra.get("telegram", {}).get("mensagens", [])
        # Itera mais recentes primeiro
        for m in reversed(msgs):
            txt = m.get("texto") or ""
            if not txt:
                continue
            mat = RE_DATA_INI_TEXTO.search(txt)
            if mat:
                iso = f"{mat.group(3)}-{mat.group(2)}-{mat.group(1)}"
                d = parse_iso(iso)
                if d:
                    msg_data = m.get("data", "")
                    # Detecta tipo (RETORNO, REAPLICAÇÃO, INÍCIO normal)
                    tipo = "INÍCIO"
                    txt_low = txt.lower()
                    if "postergada" in txt_low or "postergado" in txt_low:
                        tipo = "POSTERGADA"
                    elif "retorno" in txt_low:
                        tipo = "RETORNO"
                    elif "reaplicação" in txt_low or "reaplicacao" in txt_low:
                        tipo = "REAPLICAÇÃO"
                    fonte = f"telegram msg {m.get('id')} ({msg_data[:16]}) · {tipo}"
                    candidatos.append((d, fonte, msg_data))

    # === FONTE 2: DOSSIÊ (interpretação congelada) ===
    leitura = dossie.get("leitura_secretario", {})
    for dm in leitura.get("datas_mencionadas", []):
        evento = (dm.get("evento") or "").lower()
        if any(k in evento for k in KEYWORDS):
            d = parse_iso(dm.get("data"))
            if d:
                candidatos.append((d, f"dossiê datas_mencionadas: {(dm.get('evento') or '')[:50]}", ""))

    for ev in leitura.get("evidencias_fortes", []):
        trecho = ev.get("trecho_curto") or ""
        m = RE_DATA_INI_TEXTO.search(trecho)
        if m:
            iso = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
            d = parse_iso(iso)
            if d:
                candidatos.append((d, f"dossiê evidência: {trecho[:50]}", ev.get("data", "")))

    ult = leitura.get("ultima_atividade_significativa", {})
    if isinstance(ult, dict):
        evento_txt = ult.get("evento") or ""
        if any(k in evento_txt.lower() for k in KEYWORDS):
            m = RE_DATA_INI_TEXTO.search(evento_txt)
            if m:
                iso = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
                d = parse_iso(iso)
                if d:
                    candidatos.append((d, f"dossiê ultima_atividade: {evento_txt[:50]}", ""))

    if not candidatos:
        return {"data_x": None, "fonte": "não localizada", "data_anterior": None, "alterada": False, "historico": []}

    # Separar candidatos do snapshot (têm msg_data) dos do dossiê (sem msg_data confiável)
    do_snapshot = [(d, f, msg_d) for d, f, msg_d in candidatos if msg_d]
    do_dossie   = [(d, f) for d, f, msg_d in candidatos if not msg_d]

    # === PRIORIDADE 1: snapshot ===
    if do_snapshot:
        # Ordena cronologicamente (msg mais antiga → mais nova)
        do_snapshot.sort(key=lambda t: t[2])

        # Coleta sequência de datas distintas em ordem cronológica das menções
        historico = []
        ultima_data_vista = None
        for d, fonte, msg_d in do_snapshot:
            if d != ultima_data_vista:
                historico.append({
                    "data_x": d.strftime("%Y-%m-%d"),
                    "msg_data": msg_d[:16],
                    "fonte": fonte,
                })
                ultima_data_vista = d

        # A última (mais recente em msg_data) é a atual; a penúltima distinta é a anterior
        atual = historico[-1]
        anterior = historico[-2] if len(historico) >= 2 else None
        alterada = len(historico) >= 2

        return {
            "data_x": atual["data_x"],
            "fonte": atual["fonte"],
            "data_anterior": anterior["data_x"] if anterior else None,
            "alterada": alterada,
            "historico": historico,
        }

    # === PRIORIDADE 2: dossiê ===
    if do_dossie:
        unicos = list({d: f for d, f in do_dossie}.items())
        futuras = sorted([(d, f) for d, f in unicos if d >= HOJE], key=lambda x: x[0])
        if futuras:
            d, f = futuras[0]
            return {"data_x": d.strftime("%Y-%m-%d"), "fonte": f, "data_anterior": None, "alterada": False, "historico": []}
        passadas = sorted(unicos, key=lambda x: x[0], reverse=True)
        d, f = passadas[0]
        return {"data_x": d.strftime("%Y-%m-%d"), "fonte": f + " [só passadas]", "data_anterior": None, "alterada": False, "historico": []}

    return {"data_x": None, "fonte": "não localizada", "data_anterior": None, "alterada": False, "historico": []}


def calcular_marcos(data_inicio_iso: str | None, status: str, flags: list, hoje: datetime) -> list:
    """Pra cada marco SLA, calcula deadline absoluto + status."""
    if not data_inicio_iso:
        return []

    x = parse_iso(data_inicio_iso)
    if not x:
        return []

    flags = flags or []
    marcos = []
    for m in MARCOS_SLA:
        deadline = x - timedelta(days=m["antes_x"])
        dias_restantes = (deadline - hoje).days
        passou = dias_restantes < 0

        # Heurística de status do marco · cruzando com flags do HERMENEUTA
        marco_status = "no_prazo"
        if m["id"] == "equipe" and "aplicador_indefinido" in flags:
            marco_status = "atrasado_critico" if passou else ("alerta" if dias_restantes <= 7 else "pendente")
        elif passou:
            # Marco passou · sem evidência de conclusão · marca como precisa_confirmar
            # (futura iteração: cruzar com mensagens pra confirmar conclusão)
            if status in ("contrato", "planejamento") and m["id"] == "vt_afericao":
                marco_status = "atrasado_critico"  # status indica que ainda não fez
            else:
                marco_status = "passou_verificar"
        else:
            if dias_restantes <= 7:
                marco_status = "alerta"

        marcos.append({
            "id": m["id"],
            "label": m["label"],
            "antes_x_dias": m["antes_x"],
            "deadline": deadline.strftime("%Y-%m-%d"),
            "dias_restantes": dias_restantes,
            "status": marco_status,  # no_prazo | alerta | passou_verificar | atrasado_critico | concluido
        })
    return marcos


def main():
    if not DISCORD_PATH.exists():
        print(f"ERRO: {DISCORD_PATH} não existe")
        sys.exit(1)

    discord = json.loads(DISCORD_PATH.read_text(encoding="utf-8"))

    # Carrega snapshot pra varrer mensagens recentes (sobrescreve dossiê quando há data nova)
    snapshot_by_id = {}
    if SNAPSHOT_PATH.exists():
        snap = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
        snapshot_by_id = {o["obra_id"]: o for o in snap.get("obras", [])}

    print(f"{'Cliente':<42} {'Status':<22} {'Início (X)':<12} {'Dias':<6} Bucket")
    print("-" * 110)

    # Carrega painel-snapshot pra obras SEM dossiê (fallback de dataExecucaoPrevista)
    painel_snapshot = []
    painel_path = ROOT / "dados" / "painel-snapshot.json"
    if painel_path.exists():
        try:
            painel_snapshot = json.loads(painel_path.read_text(encoding="utf-8-sig"))
        except Exception:
            painel_snapshot = []
    painel_by_id = {o.get("id"): o for o in (painel_snapshot or []) if isinstance(o, dict)}

    bucket_count = {}
    for obra in discord.get("obras", []):
        oid = obra.get("obra_id")
        dossie_path = DOSSIES_DIR / f"{oid}.json"
        dossie_existe = dossie_path.exists()

        if dossie_existe:
            dossie = json.loads(dossie_path.read_text(encoding="utf-8"))
        else:
            # Sem dossiê (obra adicionada via expansão · sem análise IA ainda)
            # Usa fallback do painel-snapshot pra ter bucket + dias_ate_inicio
            dossie = {}

        status = (obra.get("painel") or {}).get("status_atual") or "?"
        flags = obra.get("flags") or []
        snapshot_obra = snapshot_by_id.get(oid)

        if dossie_existe:
            info_x = extrair_data_inicio(dossie, snapshot_obra)
            data_x = info_x["data_x"]
        else:
            # Fallback: pega dataExecucaoPrevista do painel-snapshot
            p = painel_by_id.get(oid, {})
            data_x = p.get("dataExecucaoPrevista")
            info_x = {
                "data_x": data_x,
                "fonte": "painel-snapshot (fallback · sem dossiê)",
                "data_anterior": None,
                "alterada": False,
                "historico": [],
            }

        x = parse_iso(data_x) if data_x else None
        dias_ate_x = (x - HOJE).days if x else None

        bucket = bucket_temporal(status, dias_ate_x)
        marcos = calcular_marcos(data_x, status, flags, HOJE)

        obra["regua"] = {
            "data_inicio_x": data_x,
            "data_inicio_fonte": info_x["fonte"],
            "data_inicio_anterior": info_x["data_anterior"],
            "data_inicio_alterada": info_x["alterada"],
            "data_inicio_historico": info_x["historico"],
            "dias_ate_inicio": dias_ate_x,
            "bucket": bucket,
            "marcos_sla": marcos,
            "calculado_em": HOJE.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        bucket_count[bucket["id"]] = bucket_count.get(bucket["id"], 0) + 1

        cliente = obra.get("cliente", "")[:40]
        d_str = "—" if dias_ate_x is None else f"{dias_ate_x}d"
        x_str = data_x or "—"
        print(f"{cliente:<42} {status:<22} {x_str:<12} {d_str:<6} {bucket['label']}")

    # bucket_count usado só pra log local · não persiste no JSON

    write_discord(DISCORD_PATH, discord)
    print()
    print("Distribuição por bucket:")
    for b, n in sorted(bucket_count.items(), key=lambda x: -x[1]):
        print(f"  {n:2d}  {b}")
    print(f"\n[OK] {DISCORD_PATH}")


if __name__ == "__main__":
    main()
