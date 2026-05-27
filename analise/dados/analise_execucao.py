"""Fases e Desempenho por Faixa — Qualidade Monofloor

Mede quanto tempo leva cada fase da obra (planejamento, hibernacao,
execucao, pos-execucao) por faixa de metragem. Fonte: jornadas.json.

Uso:
  python analise/dados/analise_execucao.py
"""
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
from statistics import median

BASE = Path(__file__).parent
JORN_PATH = BASE.parent / "lab-hermeneuta" / "dados" / "jornadas.json"
OUT_JSON = BASE / "execucao-por-faixa.json"
OUT_HTML = BASE.parent / "execucao.html"

HOJE = date.today()
HOJE_STR = HOJE.isoformat()

CLASSIFICACOES_ELEGIVEIS = {
    "entrega_limpa", "entrega_com_ressalvas", "entrega_com_retrabalho",
    "em_execucao", "em_execucao_com_retrabalho", "retrabalho_ativo",
}

STATUS_EM_EXECUCAO = {"em_execucao"}
STATUS_RETRABALHO = {"reparo", "marcas_rolo_cera"}
STATUS_EM_CAMPO = STATUS_EM_EXECUCAO | STATUS_RETRABALHO

CORTE_INICIO = "2026-01-01"
DATAS_ARTEFATO = {"2026-02-28"}

FAIXA_ORDER = ["PP", "P", "M", "G", "GG", "XG"]
FAIXA_COLORS = {
    "PP": "#8a5cb0", "P": "#4a7ab8", "M": "#3d8a5a",
    "G": "#b89a4a", "GG": "#c47a4a", "XG": "#c45a5a",
}
FAIXA_RANGES = {
    "PP": "<60", "P": "60-100", "M": "100-150",
    "G": "150-220", "GG": "220-300", "XG": ">300",
}

FASE_CATS = ["planejamento", "pre_execucao", "hibernacao", "execucao", "pos_execucao"]
FASE_LABELS = {
    "planejamento": "Planejamento",
    "pre_execucao": "Pré-execução",
    "hibernacao": "Hibernação",
    "execucao": "Execução",
    "pos_execucao": "Pós-execução",
}
FASE_COLORS = {
    "planejamento": "#4a7ab8",
    "pre_execucao": "#8a5cb0",
    "hibernacao": "#b89a4a",
    "execucao": "#3d8a5a",
    "pos_execucao": "#c47a4a",
}

# ---------------------------------------------------------------------------
# CSS (string puro, sem f-string)
# ---------------------------------------------------------------------------
_CSS = """
:root {
  --bg: #ddd7cd; --card: #ffffff; --card-2: #f7f4ef; --card-3: #f0ebe3;
  --border: #e0d8cc; --text: #3a3530; --text-2: #2a2520; --muted: #8a7e72;
  --muted-2: #b8b0a4; --accent: #b8a080; --green: #3d8a5a; --amber: #b89a4a;
  --red: #c45a5a; --blue: #4a7ab8; --purple: #8a5cb0;
  --mono: 'JetBrains Mono', ui-monospace, monospace;
  --sans: 'Plus Jakarta Sans', system-ui, sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { background: var(--bg); color: var(--text); font-family: var(--sans); font-size: 13px; line-height: 1.55; }
body { min-height: 100vh; }

header { position: sticky; top: 0; z-index: 50; background: rgba(255,255,255,.92); border-bottom: 1px solid var(--border); backdrop-filter: blur(16px); }
.top-row { display: flex; align-items: center; gap: 20px; max-width: 1200px; margin: 0 auto; padding: 0 32px; height: 52px; }
.brand { display: flex; align-items: center; gap: 10px; }
.brand-mark { width: 26px; height: 26px; border-radius: 6px; background: linear-gradient(135deg, var(--accent), #9a8060); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 11px; color: #fff; }
.brand-text { font-size: 14px; font-weight: 300; letter-spacing: 5px; text-transform: uppercase; }
.top-sep { width: 1px; height: 22px; background: var(--border); }
.top-title { font-size: 13px; font-weight: 600; color: var(--text-2); }
.top-stamp { margin-left: auto; font-size: 10px; color: var(--muted-2); font-family: var(--mono); }

.container { max-width: 1200px; margin: 0 auto; padding: 28px 32px 80px; }

.headline { background: var(--card); border-radius: 12px; padding: 24px 28px; border: 1px solid var(--border); margin-bottom: 24px; }
.headline h2 { font-size: 16px; font-weight: 700; color: var(--text-2); margin-bottom: 12px; }
.headline .manchete { font-size: 13px; color: var(--text); font-weight: 500; margin-bottom: 8px; line-height: 1.7; }
.headline p { font-size: 12px; color: var(--muted); line-height: 1.7; }

.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
.kpi { background: var(--card); border-radius: 10px; padding: 16px 18px; border: 1px solid var(--border); }
.kpi-label { font-size: 10px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin-bottom: 6px; }
.kpi-value { font-family: var(--mono); font-size: 24px; font-weight: 700; color: var(--text-2); }
.kpi-value small { font-size: 12px; font-weight: 400; color: var(--muted); margin-left: 4px; }
.kpi-sub { font-size: 11px; color: var(--muted); margin-top: 4px; }
.kpi-compare { display: flex; gap: 8px; margin-top: 8px; }
.kpi-compare span { font-family: var(--mono); font-size: 10px; padding: 2px 6px; border-radius: 4px; }
.kpi-compare .limpa { background: rgba(61,138,90,.1); color: var(--green); }
.kpi-compare .retorno { background: rgba(196,90,90,.1); color: var(--red); }

.section-title { font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); font-weight: 600; margin: 32px 0 12px; }

.tabs { display: flex; gap: 0; margin-bottom: 24px; }
.tab { padding: 10px 24px; font-size: 12px; font-weight: 600; cursor: pointer; border: 1px solid var(--border); background: var(--card-3); color: var(--muted); transition: all .2s; }
.tab:first-child { border-radius: 8px 0 0 8px; }
.tab:last-child { border-radius: 0 8px 8px 0; }
.tab.active { background: var(--card); color: var(--text-2); border-color: var(--accent); z-index: 1; }
.tab .tab-count { font-family: var(--mono); font-size: 10px; margin-left: 6px; padding: 1px 5px; border-radius: 3px; background: rgba(0,0,0,.06); }
.tab.active .tab-count { background: rgba(184,160,128,.15); color: var(--accent); }
.tab-panel { display: none; }
.tab-panel.active { display: block; }

.stacked-chart { background: var(--card); border-radius: 12px; padding: 20px 24px; border: 1px solid var(--border); margin-bottom: 24px; }
.stack-legend { display: flex; gap: 16px; margin-bottom: 16px; font-size: 11px; color: var(--muted); flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 5px; }
.legend-dot { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
.stack-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.stack-label { min-width: 170px; display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.stack-range { font-size: 10px; color: var(--muted); }
.stack-n { font-size: 10px; color: var(--muted-2); font-family: var(--mono); }
.stack-bar { flex: 1; display: flex; height: 28px; border-radius: 6px; overflow: hidden; background: var(--card-3); }
.stack-seg { display: flex; align-items: center; justify-content: center; font-family: var(--mono); font-size: 10px; color: #fff; font-weight: 600; min-width: 0; overflow: hidden; }
.stack-total { font-family: var(--mono); font-size: 12px; font-weight: 700; color: var(--text-2); min-width: 45px; text-align: right; }

.faixas-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; margin-bottom: 24px; }
.faixa-card { background: var(--card); border-radius: 12px; padding: 20px; border: 1px solid var(--border); }
.faixa-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.faixa-badge { font-family: var(--mono); font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 6px; }
.faixa-range { font-size: 11px; color: var(--muted); }
.faixa-n { font-family: var(--mono); font-size: 11px; color: var(--muted-2); margin-left: auto; }
.faixa-main { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
.faixa-metric-label { font-size: 10px; text-transform: uppercase; color: var(--muted); letter-spacing: .04em; }
.faixa-metric-value { font-family: var(--mono); font-size: 20px; font-weight: 700; color: var(--text-2); }
.faixa-metric-value small { font-size: 11px; font-weight: 400; color: var(--muted); }
.faixa-bar { height: 8px; border-radius: 4px; background: var(--card-3); margin: 8px 0; overflow: hidden; display: flex; }
.faixa-bar-seg { height: 100%; }
.faixa-detail { font-size: 11px; color: var(--muted); line-height: 1.7; }
.faixa-detail strong { color: var(--text); }

.insight { background: var(--card-3); border-radius: 10px; padding: 16px 20px; border-left: 3px solid var(--accent); margin-bottom: 16px; font-size: 12px; color: var(--text); line-height: 1.7; }
.insight strong { color: var(--text-2); }
.insight .neg { color: var(--red); font-weight: 600; }
.insight .pos { color: var(--green); font-weight: 600; }

.table-wrap { background: var(--card); border-radius: 12px; padding: 4px; border: 1px solid var(--border); margin-bottom: 24px; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { text-align: left; padding: 10px 8px; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); white-space: nowrap; }
td { padding: 7px 8px; border-bottom: 1px solid rgba(224,216,204,.3); }
.num { font-family: var(--mono); text-align: right; }
.bold { font-weight: 700; color: var(--text-2); }
tr:hover { background: var(--card-2); }
.badge { font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 600; white-space: nowrap; }
.badge.ret { background: rgba(196,90,90,.1); color: var(--red); }
.badge.ok { background: rgba(61,138,90,.1); color: var(--green); }
.status-cell { font-size: 11px; color: var(--muted); white-space: nowrap; }

.score-panel { background: var(--card); border-radius: 12px; padding: 28px; border: 1px solid var(--border); }
.score-main { text-align: center; margin-bottom: 28px; }
.score-number { font-family: var(--mono); font-size: 56px; font-weight: 700; line-height: 1; }
.score-level { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: .1em; margin-top: 6px; }
.score-label { font-size: 11px; color: var(--muted); margin-top: 4px; }
.score-components { display: flex; flex-direction: column; gap: 16px; }
.comp-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.comp-label { font-size: 11px; color: var(--text); }
.comp-pts { font-family: var(--mono); font-size: 12px; font-weight: 700; }
.comp-bar { height: 8px; border-radius: 4px; background: var(--card-3); overflow: hidden; }
.comp-fill { height: 100%; border-radius: 4px; }
.comp-detail { font-size: 10px; color: var(--muted-2); margin-top: 3px; font-family: var(--mono); }
.score-flags { padding-top: 16px; border-top: 1px solid var(--border); margin-top: 20px; }
.flag-item { font-size: 12px; color: var(--text); padding: 8px 0; border-bottom: 1px solid rgba(224,216,204,.3); display: flex; align-items: center; }
.flag-count { font-family: var(--mono); font-weight: 700; color: var(--amber); margin-right: 10px; min-width: 24px; }

footer { text-align: center; padding: 40px 0 20px; font-size: 10px; color: var(--muted-2); }
@media(max-width:800px) {
  .kpis { grid-template-columns: repeat(2, 1fr); }
  .faixas-grid { grid-template-columns: 1fr; }
  .container { padding: 16px; }
  .stack-label { min-width: 100px; }
  .tabs { flex-wrap: wrap; }
}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_date(s):
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def safe_median(lst):
    return round(median(lst)) if lst else 0


def safe_avg(lst):
    return round(sum(lst) / len(lst), 1) if lst else 0


def clusterizar_blocos(dates, gap_max=14):
    if not dates:
        return []
    sorted_dates = sorted(set(dates))
    blocos = []
    bloco_ini = sorted_dates[0]
    bloco_fim = sorted_dates[0]
    for d in sorted_dates[1:]:
        if (d - bloco_fim).days <= gap_max:
            bloco_fim = d
        else:
            blocos.append((bloco_ini, bloco_fim, (bloco_fim - bloco_ini).days))
            bloco_ini = d
            bloco_fim = d
    blocos.append((bloco_ini, bloco_fim, (bloco_fim - bloco_ini).days))
    return blocos


def categorizar_fase(nome):
    n = (nome or "").strip().lower()
    if n == "planejamento inicial":
        return "planejamento"
    if n in ("planejamento + pré-execução", "despertar e pré-execução",
             "atividade retomada",
             "planejamento + pre-execucao", "despertar e pre-execucao"):
        return "pre_execucao"
    if n.startswith("hibernação") or n.startswith("hibernacao"):
        return "hibernacao"
    if n in ("execução", "execucao"):
        return "execucao"
    if n in ("pós-execução", "pos-execucao"):
        return "pos_execucao"
    return "outro"


# ---------------------------------------------------------------------------
# Extracao por obra
# ---------------------------------------------------------------------------
def extrair_obra(obra):
    cls = obra.get("classificacao", "")
    status = obra.get("status", "")

    if status == "cancelado" or cls == "cancelada":
        return None
    if cls not in CLASSIFICACOES_ELEGIVEIS:
        return None

    inicio_exec = parse_date(obra.get("data_inicio_real"))
    if not inicio_exec:
        return None

    camadas = obra.get("camadas_aplicadas", [])
    fases = obra.get("fases", [])
    marcos = obra.get("marcos", [])

    cam_dates = []
    if camadas:
        cam_dates = [parse_date(c.get("data")) for c in camadas]
        cam_dates = [d for d in cam_dates if d and d.isoformat() not in DATAS_ARTEFATO]
    n_camadas_detectadas = len(cam_dates)

    n_blocos = 0
    dias_aplicacao_real = None
    fim_exec = None
    fonte = None

    if cam_dates:
        fim_exec = max(cam_dates)
        blocos = clusterizar_blocos(cam_dates, gap_max=14)
        dias_aplicacao_real = sum(b[2] for b in blocos)
        n_blocos = len(blocos)
        fonte = "camadas"

    if not fim_exec:
        for f in fases:
            if f.get("nome", "").strip() == "Execução":
                d_fim = parse_date(f.get("fim"))
                if d_fim:
                    fim_exec = d_fim
                    fonte = fonte or "fase"
                    break

    if not fim_exec:
        t = obra.get("tempo_execucao_dias")
        if t and t > 0:
            fim_exec = inicio_exec + timedelta(days=t)
            fonte = fonte or "tempo_jornadas"

    if not fim_exec and not cam_dates:
        return None

    fim_final = None
    finaliz_marcos = [m for m in marcos if m.get("tipo") == "finalizacao"]
    if finaliz_marcos:
        dates_fin = [parse_date(m.get("data")) for m in finaliz_marcos]
        dates_fin = [d for d in dates_fin if d]
        if dates_fin:
            fim_final = max(dates_fin)

    if not fim_final and status in ("finalizado", "concluido"):
        fim_final = fim_exec or inicio_exec

    exec_start = inicio_exec
    if cam_dates and min(cam_dates) < inicio_exec:
        exec_start = min(cam_dates)

    datas_invertidas = False
    if fim_final and fim_final < exec_start:
        datas_invertidas = True
        fim_final = None

    finalizada = (
        status in ("finalizado", "concluido")
        or (cls.startswith("entrega_") and status not in STATUS_EM_CAMPO)
    )
    em_campo = not finalizada
    em_execucao = status in STATUS_EM_EXECUCAO
    em_retrabalho = status in STATUS_RETRABALHO

    ciclos = obra.get("ciclos", [])
    n_ciclos = len(ciclos) if ciclos else 0
    tem_retorno = (
        n_ciclos > 1
        or "retrabalho" in cls
        or status in STATUS_RETRABALHO
        or n_blocos >= 2
    )

    dias_total = None
    if finalizada:
        if fim_final:
            dias_total = (fim_final - exec_start).days
        elif fim_exec and fim_exec >= exec_start:
            dias_total = (fim_exec - exec_start).days
    elif em_campo:
        dias_total = (HOJE - inicio_exec).days

    if dias_aplicacao_real is not None and dias_total is not None and dias_aplicacao_real > dias_total:
        dias_aplicacao_real = dias_total

    dias_por_fase = defaultdict(int)
    for f in fases:
        cat = categorizar_fase(f.get("nome", ""))
        dur = f.get("duracao_dias", 0) or 0
        dias_por_fase[cat] += dur

    if not dias_por_fase.get("execucao"):
        t = obra.get("tempo_execucao_dias")
        if t and t > 0:
            dias_por_fase["execucao"] = t
    if not dias_por_fase.get("hibernacao"):
        t = obra.get("tempo_hibernacao_dias")
        if t and t > 0:
            dias_por_fase["hibernacao"] = t

    ciclo_total = sum(dias_por_fase.get(c, 0) for c in FASE_CATS)
    ciclo_total += dias_por_fase.get("outro", 0)

    eficiencia = round(dias_por_fase.get("execucao", 0) / ciclo_total, 3) if ciclo_total > 0 else 0

    if n_camadas_detectadas >= 2:
        confianca = "alta"
    elif fonte in ("camadas", "fase"):
        confianca = "media"
    else:
        confianca = "baixa"

    return {
        "cliente": obra.get("cliente", "?"),
        "obra_id": obra.get("obra_id"),
        "faixa": obra.get("faixa_metragem"),
        "m2": obra.get("metragem") or 0,
        "status": status,
        "classificacao": cls,
        "consultor": obra.get("consultor"),
        "fonte": fonte,
        "confianca": confianca,
        "inicio_exec": inicio_exec.isoformat(),
        "fim_exec": fim_exec.isoformat() if fim_exec else None,
        "fim_final": fim_final.isoformat() if fim_final else None,
        "n_ciclos": n_ciclos,
        "n_blocos": n_blocos,
        "n_camadas": n_camadas_detectadas,
        "tem_retorno": tem_retorno,
        "datas_invertidas": datas_invertidas,
        "finalizada": finalizada,
        "em_campo": em_campo,
        "em_execucao": em_execucao,
        "em_retrabalho": em_retrabalho,
        "dias_aplicacao": dias_aplicacao_real,
        "dias_total_exec": dias_total,
        "dias_planejamento": dias_por_fase.get("planejamento", 0),
        "dias_pre_execucao": dias_por_fase.get("pre_execucao", 0),
        "dias_hibernacao": dias_por_fase.get("hibernacao", 0),
        "dias_execucao": dias_por_fase.get("execucao", 0),
        "dias_pos_execucao": dias_por_fase.get("pos_execucao", 0),
        "ciclo_total": ciclo_total,
        "eficiencia": eficiencia,
    }


# ---------------------------------------------------------------------------
# Agregacao
# ---------------------------------------------------------------------------
def agregar_por_faixa(execucoes):
    por_faixa = defaultdict(list)
    for e in execucoes:
        if e["faixa"]:
            por_faixa[e["faixa"]].append(e)

    resultado = []
    for faixa in FAIXA_ORDER:
        obras = por_faixa.get(faixa, [])
        if not obras:
            continue

        finalizadas = [o for o in obras if o["finalizada"]]
        em_campo_l = [o for o in obras if o["em_campo"]]
        com_retorno = [o for o in obras if o["tem_retorno"]]

        fases_stats = {}
        for cat in FASE_CATS:
            key = f"dias_{cat}"
            vals = [o[key] for o in obras if o[key] > 0]
            fases_stats[cat] = {
                "mediana": safe_median(vals),
                "media": safe_avg(vals),
                "n": len(vals),
            }

        ciclos = [o["ciclo_total"] for o in obras if o["ciclo_total"] > 0]
        eficiencias = [o["eficiencia"] for o in obras if o["ciclo_total"] > 0]

        dias_aplic = [o["dias_aplicacao"] for o in obras if o["dias_aplicacao"] is not None]
        dias_total_fin = [o["dias_total_exec"] for o in finalizadas if o["dias_total_exec"] is not None]

        fin_com_ret = [o for o in finalizadas if o["tem_retorno"]]
        fin_sem_ret = [o for o in finalizadas if not o["tem_retorno"]]
        dias_fin_com = [o["dias_total_exec"] for o in fin_com_ret if o["dias_total_exec"] is not None]
        dias_fin_sem = [o["dias_total_exec"] for o in fin_sem_ret if o["dias_total_exec"] is not None]

        dias_campo = [o["dias_total_exec"] for o in em_campo_l if o["dias_total_exec"] is not None]
        n_exec = sum(1 for o in em_campo_l if o["em_execucao"])
        n_retrab = sum(1 for o in em_campo_l if o["em_retrabalho"])

        resultado.append({
            "faixa": faixa,
            "range": FAIXA_RANGES.get(faixa, "?"),
            "n_obras": len(obras),
            "n_finalizadas": len(finalizadas),
            "n_em_campo": len(em_campo_l),
            "n_com_retorno": len(com_retorno),
            "pct_retorno": round(len(com_retorno) / len(obras) * 100, 1) if obras else 0,
            "fases": fases_stats,
            "ciclo_total": {
                "mediana": safe_median(ciclos),
                "media": safe_avg(ciclos),
            },
            "eficiencia": {
                "mediana": round(median(eficiencias), 3) if eficiencias else 0,
                "media": round(sum(eficiencias) / len(eficiencias), 3) if eficiencias else 0,
            },
            "dias_aplicacao": {
                "mediana": safe_median(dias_aplic),
                "media": safe_avg(dias_aplic),
                "min": min(dias_aplic) if dias_aplic else 0,
                "max": max(dias_aplic) if dias_aplic else 0,
            },
            "dias_total_finalizadas": {
                "mediana": safe_median(dias_total_fin),
                "media": safe_avg(dias_total_fin),
                "min": min(dias_total_fin) if dias_total_fin else 0,
                "max": max(dias_total_fin) if dias_total_fin else 0,
                "n": len(dias_total_fin),
                "n_com_retorno": len(fin_com_ret),
                "n_sem_retorno": len(fin_sem_ret),
            },
            "dias_com_retorno": {
                "mediana": safe_median(dias_fin_com),
                "media": safe_avg(dias_fin_com),
                "n": len(dias_fin_com),
            },
            "dias_sem_retorno": {
                "mediana": safe_median(dias_fin_sem),
                "media": safe_avg(dias_fin_sem),
                "n": len(dias_fin_sem),
            },
            "em_campo": {
                "n": len(em_campo_l),
                "n_exec": n_exec,
                "n_retrab": n_retrab,
                "dias_mediana": safe_median(dias_campo),
                "dias_media": safe_avg(dias_campo),
            },
            "obras_destaque": sorted(
                [o for o in obras if o["dias_total_exec"] is not None],
                key=lambda o: o["dias_total_exec"], reverse=True
            )[:5],
        })
    return resultado


def calcular_global(execucoes):
    finalizadas = [e for e in execucoes if e["finalizada"]]
    em_campo_l = [e for e in execucoes if e["em_campo"]]
    com_retorno = [e for e in execucoes if e["tem_retorno"]]

    dias_total = [e["dias_total_exec"] for e in finalizadas if e["dias_total_exec"] is not None]
    dias_aplic = [e["dias_aplicacao"] for e in execucoes if e["dias_aplicacao"] is not None]

    fin_com = [e for e in finalizadas if e["tem_retorno"]]
    fin_sem = [e for e in finalizadas if not e["tem_retorno"]]
    dias_com = [e["dias_total_exec"] for e in fin_com if e["dias_total_exec"] is not None]
    dias_sem = [e["dias_total_exec"] for e in fin_sem if e["dias_total_exec"] is not None]

    fase_medians = {}
    for cat in FASE_CATS:
        key = f"dias_{cat}"
        vals = [e[key] for e in execucoes if e[key] > 0]
        fase_medians[cat] = safe_median(vals)

    ciclos = [e["ciclo_total"] for e in execucoes if e["ciclo_total"] > 0]
    eficiencias = [e["eficiencia"] for e in execucoes if e["ciclo_total"] > 0]

    return {
        "total_analisadas": len(execucoes),
        "finalizadas": len(finalizadas),
        "em_campo": len(em_campo_l),
        "finalizadas_com_retorno": len(fin_com),
        "finalizadas_sem_retorno": len(fin_sem),
        "com_retorno": len(com_retorno),
        "pct_retorno": round(len(com_retorno) / len(execucoes) * 100, 1) if execucoes else 0,
        "pct_retorno_fin": round(len(fin_com) / len(finalizadas) * 100, 1) if finalizadas else 0,
        "n_com_camadas": sum(1 for e in execucoes if e["fonte"] == "camadas"),
        "dias_aplicacao_mediana": safe_median(dias_aplic),
        "dias_total_finalizadas_mediana": safe_median(dias_total),
        "dias_total_finalizadas_media": safe_avg(dias_total),
        "dias_com_retorno_mediana": safe_median(dias_com),
        "dias_sem_retorno_mediana": safe_median(dias_sem),
        "impacto_retorno_dias": round(safe_avg(dias_com) - safe_avg(dias_sem), 1) if dias_com and dias_sem else 0,
        "fase_medians": fase_medians,
        "ciclo_total_mediana": safe_median(ciclos),
        "eficiencia_mediana": round(median(eficiencias) * 100, 1) if eficiencias else 0,
        "em_campo_exec": sum(1 for e in em_campo_l if e["em_execucao"]),
        "em_campo_retrab": sum(1 for e in em_campo_l if e["em_retrabalho"]),
        "em_campo_dias_mediana": safe_median(
            [e["dias_total_exec"] for e in em_campo_l if e["dias_total_exec"] is not None]
        ),
    }


def calcular_confianca(execucoes, n_total_corte, n_elegiveis_corte):
    n = len(execucoes)
    if n == 0:
        return {"total": 0, "componentes": {}, "flags": {}}

    n_alta = sum(1 for e in execucoes if e["n_camadas"] >= 2)
    n_valida = sum(1 for e in execucoes if e["fonte"] in ("camadas", "fase", "tempo_jornadas"))
    n_sem_inversao = sum(1 for e in execucoes if not e["datas_invertidas"])
    n_com_fase_exec = sum(1 for e in execucoes if e["dias_execucao"] > 0)
    n_visiveis = sum(1 for e in execucoes if e["finalizada"] or e["em_campo"])

    c1 = round(n_alta / n * 25)
    c2 = round(n_valida / n * 15)
    c3 = round(n_sem_inversao / n * 15)
    c4 = round(n_elegiveis_corte / n_total_corte * 15) if n_total_corte > 0 else 15
    c5 = round(n_com_fase_exec / n * 15)
    c6 = round(n_visiveis / n * 15)
    total = c1 + c2 + c3 + c4 + c5 + c6

    return {
        "total": total,
        "componentes": {
            "fonte_alta": {
                "pts": c1, "max": 25, "n": n_alta, "total": n,
                "label": "Fonte alta qualidade (camadas Telegram)",
            },
            "fonte_valida": {
                "pts": c2, "max": 15, "n": n_valida, "total": n,
                "label": "Fonte válida (camadas ou fase)",
            },
            "qualidade_datas": {
                "pts": c3, "max": 15, "n": n_sem_inversao, "total": n,
                "label": "Sem datas invertidas",
            },
            "elegibilidade": {
                "pts": c4, "max": 15, "n": n_elegiveis_corte, "total": n_total_corte,
                "label": "Elegíveis no corte temporal",
            },
            "cobertura_fases": {
                "pts": c5, "max": 15, "n": n_com_fase_exec, "total": n,
                "label": "Fase execução identificada",
            },
            "visibilidade": {
                "pts": c6, "max": 15, "n": n_visiveis, "total": n,
                "label": "Visíveis nas abas (zero fantasma)",
            },
        },
        "flags": {
            "datas_invertidas": sum(1 for e in execucoes if e["datas_invertidas"]),
            "sem_faixa": sum(1 for e in execucoes if not e["faixa"]),
            "sem_fonte": sum(1 for e in execucoes if not e["fonte"]),
            "confiança_baixa": sum(1 for e in execucoes if e["confianca"] == "baixa"),
        },
    }


# ---------------------------------------------------------------------------
# Geradores HTML (strings puras, inseridas no f-string principal)
# ---------------------------------------------------------------------------
def _stacked_bar_html(faixas):
    h = '<div class="stacked-chart">\n<div class="stack-legend">'
    for cat in FASE_CATS:
        h += f'<span class="legend-item"><span class="legend-dot" style="background:{FASE_COLORS[cat]}"></span>{FASE_LABELS[cat]}</span>'
    h += '</div>\n'
    for f in faixas:
        total = f["ciclo_total"]["mediana"]
        if total <= 0:
            continue
        color = FAIXA_COLORS.get(f["faixa"], "#999")
        h += '<div class="stack-row">'
        h += (
            f'<div class="stack-label">'
            f'<span class="faixa-badge" style="background:{color}22;color:{color};border:1px solid {color}44">{f["faixa"]}</span>'
            f' <span class="stack-range">{f["range"]} m²</span>'
            f' <span class="stack-n">{f["n_obras"]}x</span></div>'
        )
        h += '<div class="stack-bar">'
        for cat in FASE_CATS:
            d = f["fases"][cat]["mediana"]
            pct = round(d / total * 100, 1) if total > 0 else 0
            if pct > 0:
                label = f'{d}d' if pct > 8 else ''
                h += (
                    f'<div class="stack-seg" style="width:{pct}%;background:{FASE_COLORS[cat]}"'
                    f' title="{FASE_LABELS[cat]}: {d}d ({pct}%)">{label}</div>'
                )
        h += '</div>'
        h += f'<div class="stack-total">{total}d</div>'
        h += '</div>\n'
    h += '</div>\n'
    return h


def _composition_table_html(faixas):
    h = '<div class="table-wrap"><table>\n<thead><tr><th>Faixa</th>'
    for cat in FASE_CATS:
        h += f'<th class="num">{FASE_LABELS[cat]}</th>'
    h += '<th class="num">Total</th><th class="num">Eficiência</th></tr></thead>\n<tbody>\n'
    for f in faixas:
        total = f["ciclo_total"]["mediana"]
        eff_pct = round(f["eficiencia"]["mediana"] * 100, 1)
        color = FAIXA_COLORS.get(f["faixa"], "#999")
        h += (
            f'<tr><td><span class="faixa-badge" style="background:{color}22;color:{color};'
            f'border:1px solid {color}44">{f["faixa"]}</span></td>'
        )
        for cat in FASE_CATS:
            d = f["fases"][cat]["mediana"]
            pct = round(d / total * 100) if total > 0 else 0
            h += f'<td class="num">{d}d <small style="color:var(--muted)">({pct}%)</small></td>'
        h += f'<td class="num bold">{total}d</td>'
        h += f'<td class="num">{eff_pct}%</td></tr>\n'
    h += '</tbody></table></div>\n'
    return h


def _obra_rows_html(lista, is_campo=False):
    rows = ""
    for e in sorted(lista, key=lambda x: -(x["dias_total_exec"] or 0)):
        if e["dias_total_exec"] is None:
            continue
        ret_badge = ('<span class="badge ret">retorno</span>' if e["tem_retorno"]
                     else '<span class="badge ok">limpa</span>')
        faixa_color = FAIXA_COLORS.get(e["faixa"], "#999")
        aplic_str = str(e["dias_aplicacao"]) if e["dias_aplicacao"] is not None else "-"
        status_short = e["status"].replace("_", " ")[:18]
        if is_campo:
            if e["em_retrabalho"]:
                st_badge = '<span class="badge ret">retrabalho</span>'
            elif e["em_execucao"]:
                st_badge = '<span class="badge ok">em exec</span>'
            else:
                st_badge = (f'<span class="badge" style="background:rgba(184,160,128,.15);'
                            f'color:var(--accent)">{status_short}</span>')
        else:
            st_badge = status_short
        rows += (
            f'<tr>'
            f'<td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{e["cliente"]}</td>'
            f'<td><span class="faixa-badge" style="background:{faixa_color}22;color:{faixa_color};'
            f'border:1px solid {faixa_color}44">{e["faixa"] or "?"}</span></td>'
            f'<td class="num">{e["m2"] or "-"}</td>'
            f'<td class="num">{aplic_str}</td>'
            f'<td class="num bold">{e["dias_total_exec"]}</td>'
            f'<td>{ret_badge}</td>'
            f'<td class="num">{e["n_ciclos"]}</td>'
            f'<td class="status-cell">{st_badge}</td>'
            f'</tr>\n'
        )
    return rows


def _faixa_cards_fin_html(faixas):
    h = '<div class="faixas-grid">\n'
    for f in faixas:
        if f["n_finalizadas"] == 0:
            continue
        color = FAIXA_COLORS.get(f["faixa"], "#999")
        nFin = f["dias_total_finalizadas"]["n"]
        nRet = f["dias_total_finalizadas"]["n_com_retorno"]
        nLimpa = f["dias_total_finalizadas"]["n_sem_retorno"]
        pctRet = round(nRet / nFin * 100) if nFin > 0 else 0
        pctLimpa = 100 - pctRet

        total_ciclo = f["ciclo_total"]["mediana"]
        mini_bar = ''
        if total_ciclo > 0:
            mini_bar = '<div class="faixa-bar" style="height:6px;margin:4px 0">'
            for cat in FASE_CATS:
                d = f["fases"][cat]["mediana"]
                pct = round(d / total_ciclo * 100, 1) if total_ciclo > 0 else 0
                if pct > 0:
                    mini_bar += (f'<div class="faixa-bar-seg" style="width:{pct}%;'
                                 f'background:{FASE_COLORS[cat]}" title="{FASE_LABELS[cat]}: {d}d"></div>')
            mini_bar += '</div>'

        detail_parts = []
        if nLimpa > 0:
            detail_parts.append(
                f'<strong>Limpa:</strong> {f["dias_sem_retorno"]["mediana"]}d mediana ({nLimpa} obras).'
            )
        if nRet > 0:
            detail_parts.append(
                f'<strong>Com retorno:</strong> {f["dias_com_retorno"]["mediana"]}d mediana ({nRet} obras).'
            )
        top = [o for o in f["obras_destaque"] if o["finalizada"]][:3]
        if top:
            nomes = ', '.join(
                f'{o["cliente"][:25]} ({o["dias_total_exec"]}d{"" if not o["tem_retorno"] else " ret"})'
                for o in top
            )
            detail_parts.append(f'<br>Mais longas: {nomes}')

        h += (
            f'<div class="faixa-card" style="border-top:3px solid {color}">'
            f'<div class="faixa-header">'
            f'<span class="faixa-badge" style="background:{color}22;color:{color};border:1px solid {color}44">{f["faixa"]}</span>'
            f'<span class="faixa-range">{f["range"]} m²</span>'
            f'<span class="faixa-n">{nFin} fin</span></div>'
            f'<div class="faixa-main">'
            f'<div><div class="faixa-metric-label">Exec. total (med)</div>'
            f'<div class="faixa-metric-value">{f["dias_total_finalizadas"]["mediana"]}<small>d</small></div></div>'
            f'<div><div class="faixa-metric-label">Aplicação (med)</div>'
            f'<div class="faixa-metric-value">{f["dias_aplicacao"]["mediana"]}<small>d</small></div></div>'
            f'<div><div class="faixa-metric-label">Composição</div>'
            f'<div class="faixa-metric-value" style="font-size:14px">'
            f'<span style="color:var(--green)">{nLimpa} limpas</span> + '
            f'<span style="color:var(--red)">{nRet} ret</span></div></div>'
            f'<div><div class="faixa-metric-label">% retorno</div>'
            f'<div class="faixa-metric-value" style="color:var(--red)">{pctRet}<small>%</small></div></div>'
            f'</div>'
            f'{mini_bar}'
            f'<div class="faixa-bar">'
            f'<div class="faixa-bar-seg" style="width:{pctLimpa}%;background:{color}88"></div>'
            f'<div class="faixa-bar-seg" style="width:{pctRet}%;background:var(--red)"></div></div>'
            f'<div class="faixa-detail">{" ".join(detail_parts)}</div>'
            f'</div>\n'
        )
    h += '</div>\n'
    return h


def _faixa_cards_campo_html(faixas):
    h = '<div class="faixas-grid">\n'
    for f in faixas:
        c = f["em_campo"]
        if c["n"] == 0:
            continue
        color = FAIXA_COLORS.get(f["faixa"], "#999")
        benchFin = f["dias_total_finalizadas"]["mediana"]
        excede = c["dias_mediana"] > benchFin and benchFin > 0
        style_val = ' style="color:var(--red)"' if excede else ''
        alert_msg = ('<strong style="color:var(--red)">Mediana já excede benchmark das finalizadas.</strong>'
                     if excede else
                     '<strong style="color:var(--green)">Dentro do benchmark.</strong>')
        h += (
            f'<div class="faixa-card" style="border-top:3px solid {color}">'
            f'<div class="faixa-header">'
            f'<span class="faixa-badge" style="background:{color}22;color:{color};border:1px solid {color}44">{f["faixa"]}</span>'
            f'<span class="faixa-range">{f["range"]} m²</span>'
            f'<span class="faixa-n">{c["n"]} em campo</span></div>'
            f'<div class="faixa-main">'
            f'<div><div class="faixa-metric-label">Dias em curso (med)</div>'
            f'<div class="faixa-metric-value"{style_val}>{c["dias_mediana"]}<small>d</small></div></div>'
            f'<div><div class="faixa-metric-label">Benchmark fin.</div>'
            f'<div class="faixa-metric-value" style="color:var(--muted)">{benchFin}<small>d</small></div></div>'
            f'</div>'
            f'<div class="faixa-detail">{alert_msg}'
            f'<br>{c["n_exec"]} em execução, {c["n_retrab"]} em retrabalho.</div>'
            f'</div>\n'
        )
    h += '</div>\n'
    return h


def _insights_fases_html(faixas, globais):
    h = ''
    fm = globais.get("fase_medians", {})
    total = sum(fm.values())
    if total > 0:
        hib_pct = round(fm.get("hibernacao", 0) / total * 100)
        exec_pct = round(fm.get("execucao", 0) / total * 100)
        plan_pct = round(fm.get("planejamento", 0) / total * 100)

        if hib_pct > exec_pct:
            h += (
                f'<div class="insight"><strong>Hibernação domina o ciclo:</strong> '
                f'{fm.get("hibernacao", 0)}d mediana (<span class="neg">{hib_pct}%</span> do ciclo total) '
                f'vs execução {fm.get("execucao", 0)}d (<span class="pos">{exec_pct}%</span>). '
                f'Obras ficam mais tempo paradas do que em aplicação.</div>'
            )

        h += (
            f'<div class="insight"><strong>Composição global:</strong> '
            f'planejamento {fm.get("planejamento", 0)}d ({plan_pct}%), '
            f'hibernação {fm.get("hibernacao", 0)}d ({hib_pct}%), '
            f'execução {fm.get("execucao", 0)}d ({exec_pct}%). '
            f'Eficiência global: <span class="pos">{globais.get("eficiencia_mediana", 0)}%</span>.</div>'
        )

    if len(faixas) >= 2:
        best = max(faixas, key=lambda f: f["eficiencia"]["mediana"])
        worst = min(faixas, key=lambda f: f["eficiencia"]["mediana"])
        if best["faixa"] != worst["faixa"]:
            h += (
                f'<div class="insight"><strong>Eficiência por faixa:</strong> '
                f'{best["faixa"]} ({best["range"]} m²) é a mais eficiente com '
                f'<span class="pos">{round(best["eficiencia"]["mediana"] * 100, 1)}%</span> '
                f'do ciclo em execução. {worst["faixa"]} ({worst["range"]} m²) tem '
                f'<span class="neg">{round(worst["eficiencia"]["mediana"] * 100, 1)}%</span>.</div>'
            )
    return h


def _insights_fin_html(faixas, globais):
    h = ''
    with_data = [f for f in faixas if f["n_obras"] >= 3]
    if with_data:
        worst = max(with_data, key=lambda f: f["pct_retorno"])
        best = min(with_data, key=lambda f: f["pct_retorno"])
        h += (
            f'<div class="insight"><strong>Faixa com mais retorno:</strong> '
            f'{worst["faixa"]} ({worst["range"]} m²) com '
            f'<span class="neg">{worst["pct_retorno"]}% de retorno</span>.'
        )
        if best["faixa"] != worst["faixa"]:
            h += f' Menor taxa: {best["faixa"]} com <span class="pos">{best["pct_retorno"]}%</span>.'
        h += '</div>'

    if globais["impacto_retorno_dias"] > 0:
        h += (
            f'<div class="insight"><strong>Impacto do retorno no prazo:</strong> '
            f'obras com retorno levam em média '
            f'<span class="neg">+{globais["impacto_retorno_dias"]} dias</span> '
            f'que entregas limpas ({globais["dias_com_retorno_mediana"]}d vs '
            f'{globais["dias_sem_retorno_mediana"]}d mediana).</div>'
        )

    with_fin = [f for f in faixas if f["dias_total_finalizadas"]["n"] > 0]
    if with_fin:
        fastest = min(with_fin, key=lambda f: f["dias_total_finalizadas"]["mediana"])
        h += (
            f'<div class="insight"><strong>Faixa mais rápida:</strong> '
            f'{fastest["faixa"]} ({fastest["range"]} m²) com mediana de '
            f'<span class="pos">{fastest["dias_total_finalizadas"]["mediana"]} dias</span> '
            f'da 1ª camada até finalização.</div>'
        )
    return h


def _score_panel_html(score):
    total = score["total"]
    if total >= 90:
        level, level_color = "excelente", "var(--green)"
    elif total >= 75:
        level, level_color = "bom", "var(--accent)"
    elif total >= 60:
        level, level_color = "regular", "var(--amber)"
    else:
        level, level_color = "baixo", "var(--red)"

    h = '<div class="score-panel">'
    h += (
        f'<div class="score-main">'
        f'<div class="score-number" style="color:{level_color}">{total}</div>'
        f'<div class="score-level" style="color:{level_color}">{level}</div>'
        f'<div class="score-label">Score de Confiança</div></div>'
    )
    h += '<div class="score-components">'
    for comp in score["componentes"].values():
        pct = round(comp["pts"] / comp["max"] * 100) if comp["max"] > 0 else 0
        if pct >= 80:
            bc = "var(--green)"
        elif pct >= 60:
            bc = "var(--accent)"
        elif pct >= 40:
            bc = "var(--amber)"
        else:
            bc = "var(--red)"
        h += (
            f'<div>'
            f'<div class="comp-header">'
            f'<span class="comp-label">{comp["label"]}</span>'
            f'<span class="comp-pts" style="color:{bc}">{comp["pts"]}/{comp["max"]}</span></div>'
            f'<div class="comp-bar"><div class="comp-fill" style="width:{pct}%;background:{bc}"></div></div>'
            f'<div class="comp-detail">{comp["n"]}/{comp["total"]} obras</div></div>'
        )
    h += '</div>'

    flags = score.get("flags", {})
    has_flags = any(v > 0 for v in flags.values())
    if has_flags:
        h += '<div class="score-flags">'
        h += '<div class="section-title" style="margin-top:0">Flags de qualidade</div>'
        for key, val in flags.items():
            if val > 0:
                label = key.replace("_", " ")
                h += f'<div class="flag-item"><span class="flag-count">{val}</span> {label}</div>'
        h += '</div>'
    h += '</div>'
    return h


# ---------------------------------------------------------------------------
# Gerador HTML principal
# ---------------------------------------------------------------------------
def gerar_html(faixas, globais, execucoes, score):
    fin_list = [e for e in execucoes if e["finalizada"]]
    campo_list = [e for e in execucoes if e["em_campo"]]
    fin_ret = [e for e in fin_list if e["tem_retorno"]]
    fin_limpa = [e for e in fin_list if not e["tem_retorno"]]

    stacked = _stacked_bar_html(faixas)
    comp_table = _composition_table_html(faixas)
    insights_fases = _insights_fases_html(faixas, globais)
    faixa_cards_fin = _faixa_cards_fin_html(faixas)
    insights_fin = _insights_fin_html(faixas, globais)
    faixa_cards_campo = _faixa_cards_campo_html(faixas)
    score_panel = _score_panel_html(score)
    rows_fin_ret = _obra_rows_html(fin_ret)
    rows_fin_limpa = _obra_rows_html(fin_limpa)
    rows_campo = _obra_rows_html(campo_list, is_campo=True)

    fm = globais.get("fase_medians", {})
    sc = score["total"]

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fases e Desempenho por Faixa · Qualidade Monofloor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
{_CSS}
</style>
</head>
<body>
<header>
  <div class="top-row">
    <div class="brand"><div class="brand-mark">M</div><div class="brand-text">monofloor</div></div>
    <div class="top-sep"></div>
    <div class="top-title">Fases e Desempenho por Faixa</div>
    <div class="top-stamp">{HOJE_STR} · score {sc}/100</div>
  </div>
</header>

<div class="container">
  <div class="headline">
    <h2>Quanto tempo leva cada fase de uma obra?</h2>
    <div class="manchete">Ciclo total mediana: <strong>{globais["ciclo_total_mediana"]}d</strong>.
      Execução real: <strong>{fm.get("execucao", 0)}d</strong> ({globais["eficiencia_mediana"]}% do ciclo).
      Hibernação: <strong>{fm.get("hibernacao", 0)}d</strong>.
      Das {globais["finalizadas"]} finalizadas:
      <span style="color:var(--green);font-weight:600">{globais["finalizadas_sem_retorno"]} limpas</span> +
      <span style="color:var(--red);font-weight:600">{globais["finalizadas_com_retorno"]} com retorno</span>
      ({globais["pct_retorno_fin"]}%).</div>
    <p>{globais["total_analisadas"]} obras analisadas. {globais["finalizadas"]} finalizadas, {globais["em_campo"]} em campo. Corte: início execução a partir de {CORTE_INICIO}.</p>
  </div>

  <div class="tabs">
    <div class="tab active" onclick="switchTab('fases')">Visão de Fases<span class="tab-count">{globais["total_analisadas"]}</span></div>
    <div class="tab" onclick="switchTab('fin')">Finalizadas<span class="tab-count">{len(fin_list)}</span></div>
    <div class="tab" onclick="switchTab('campo')">Em Campo<span class="tab-count">{len(campo_list)}</span></div>
    <div class="tab" onclick="switchTab('score')">Confiança<span class="tab-count">{sc}</span></div>
  </div>

  <!-- VISÃO DE FASES -->
  <div id="panel-fases" class="tab-panel active">
    <div class="kpis">
      <div class="kpi"><div class="kpi-label">Ciclo total (mediana)</div><div class="kpi-value">{globais["ciclo_total_mediana"]}<small>dias</small></div><div class="kpi-sub">Do planejamento à pós-execução</div></div>
      <div class="kpi"><div class="kpi-label">Execução (mediana)</div><div class="kpi-value" style="color:var(--green)">{fm.get("execucao", 0)}<small>dias</small></div><div class="kpi-sub">Fase de aplicação real</div></div>
      <div class="kpi"><div class="kpi-label">Hibernação (mediana)</div><div class="kpi-value" style="color:var(--amber)">{fm.get("hibernacao", 0)}<small>dias</small></div><div class="kpi-sub">Tempo parado</div></div>
      <div class="kpi"><div class="kpi-label">Eficiência</div><div class="kpi-value">{globais["eficiencia_mediana"]}<small>%</small></div><div class="kpi-sub">% do ciclo em execução</div></div>
    </div>

    <div class="section-title">Composição por faixa de metragem</div>
    {stacked}

    <div class="section-title">Tabela de composição</div>
    {comp_table}

    <div class="section-title">Insights</div>
    {insights_fases}
  </div>

  <!-- FINALIZADAS -->
  <div id="panel-fin" class="tab-panel">
    <div class="kpis">
      <div class="kpi"><div class="kpi-label">Finalizadas</div><div class="kpi-value">{globais["finalizadas"]}<small>obras</small></div><div class="kpi-sub">1ª camada até finalização</div>
        <div class="kpi-compare"><span class="limpa">{globais["finalizadas_sem_retorno"]} limpas</span><span class="retorno">{globais["finalizadas_com_retorno"]} com retorno</span></div></div>
      <div class="kpi"><div class="kpi-label">Exec. total (mediana)</div><div class="kpi-value">{globais["dias_total_finalizadas_mediana"]}<small>dias</small></div><div class="kpi-sub">Mediana geral</div>
        <div class="kpi-compare"><span class="limpa">{globais["dias_sem_retorno_mediana"]}d limpa</span><span class="retorno">{globais["dias_com_retorno_mediana"]}d c/ retorno</span></div></div>
      <div class="kpi"><div class="kpi-label">Taxa de retorno</div><div class="kpi-value" style="color:var(--red)">{globais["pct_retorno_fin"]}<small>%</small></div><div class="kpi-sub">{globais["finalizadas_com_retorno"]} de {globais["finalizadas"]} finalizadas</div></div>
      <div class="kpi"><div class="kpi-label">Custo do retorno</div><div class="kpi-value" style="color:var(--red)">+{globais["impacto_retorno_dias"]}<small>dias</small></div><div class="kpi-sub">Média adicional vs entrega limpa</div></div>
    </div>

    <div class="section-title">Por faixa de metragem</div>
    {faixa_cards_fin}

    <div class="section-title">Insights</div>
    {insights_fin}

    <div class="section-title" style="color:var(--red)">Obras com retorno ({len(fin_ret)})</div>
    <div class="table-wrap" style="border-left:3px solid var(--red)">
      <table><thead><tr><th>Cliente</th><th>Faixa</th><th>m²</th><th>Aplic.</th><th>Total exec</th><th>Tipo</th><th>Ciclos</th><th>Status</th></tr></thead>
      <tbody>{rows_fin_ret}</tbody></table>
    </div>

    <div class="section-title" style="color:var(--green)">Entregas limpas ({len(fin_limpa)})</div>
    <div class="table-wrap" style="border-left:3px solid var(--green)">
      <table><thead><tr><th>Cliente</th><th>Faixa</th><th>m²</th><th>Aplic.</th><th>Total exec</th><th>Tipo</th><th>Ciclos</th><th>Status</th></tr></thead>
      <tbody>{rows_fin_limpa}</tbody></table>
    </div>
  </div>

  <!-- EM CAMPO -->
  <div id="panel-campo" class="tab-panel">
    <div class="kpis">
      <div class="kpi"><div class="kpi-label">Em campo</div><div class="kpi-value">{len(campo_list)}<small>obras</small></div><div class="kpi-sub">{globais["em_campo_exec"]} exec + {globais["em_campo_retrab"]} retrab</div></div>
      <div class="kpi"><div class="kpi-label">Dias em curso (mediana)</div><div class="kpi-value">{globais["em_campo_dias_mediana"]}<small>dias</small></div><div class="kpi-sub">Desde início da execução</div></div>
      <div class="kpi"><div class="kpi-label">Benchmark fin.</div><div class="kpi-value" style="color:var(--muted)">{globais["dias_total_finalizadas_mediana"]}<small>dias</small></div><div class="kpi-sub">Mediana das finalizadas</div></div>
      <div class="kpi"><div class="kpi-label">Aplicação (mediana)</div><div class="kpi-value">{globais["dias_aplicacao_mediana"]}<small>dias</small></div><div class="kpi-sub">Camadas detectadas</div></div>
    </div>

    <div class="section-title">Por faixa de metragem</div>
    {faixa_cards_campo}

    <div class="section-title">Todas em campo ({len(campo_list)})</div>
    <div class="table-wrap">
      <table><thead><tr><th>Cliente</th><th>Faixa</th><th>m²</th><th>Aplic.</th><th>Dias em curso</th><th>Tipo</th><th>Ciclos</th><th>Status</th></tr></thead>
      <tbody>{rows_campo}</tbody></table>
    </div>
  </div>

  <!-- CONFIANÇA -->
  <div id="panel-score" class="tab-panel">
    {score_panel}

    <div class="section-title" style="margin-top:24px">Metodologia</div>
    <div class="insight" style="border-left-color:var(--muted-2)">
      <strong>Corte temporal:</strong> somente obras com início de execução a partir de {CORTE_INICIO}.
      <strong>Classificações elegíveis:</strong> entrega_limpa, entrega_com_ressalvas, entrega_com_retrabalho, em_execucao, em_execucao_com_retrabalho, retrabalho_ativo.
      <strong>Fonte primária:</strong> datas de camadas aplicadas (Telegram). <strong>Fallback:</strong> fase Execução do Painel.
      Datas artefato (2026-02-28) filtradas. Camadas agrupadas em blocos de trabalho (gap &le; 14d).
      <strong>Fases:</strong> extraídas do jornadas.json (gerar_jornada.py), categorizadas em planejamento / pré-execução / hibernação / execução / pós-execução.
      <strong>Eficiência:</strong> % do ciclo total ocupado por execução real (mediana por obra).
    </div>
  </div>
</div>

<footer>Qualidade Monofloor · Fases e Desempenho por Faixa · {HOJE_STR}</footer>

<script>
function switchTab(id) {{
  document.querySelectorAll('.tab').forEach(function(t) {{ t.classList.remove('active'); }});
  document.querySelectorAll('.tab-panel').forEach(function(p) {{ p.classList.remove('active'); }});
  document.getElementById('panel-' + id).classList.add('active');
  event.target.closest('.tab').classList.add('active');
}}
</script>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("Carregando jornadas.json...")
    data = json.loads(JORN_PATH.read_text(encoding="utf-8"))
    obras_raw = data["obras"]
    print(f"  {len(obras_raw)} obras no jornadas.json")

    print("Extraindo dados...")
    execucoes = []
    n_cancelada = 0
    n_inelegivel = 0
    n_sem_dados = 0
    for o in obras_raw:
        cls = o.get("classificacao", "")
        status = o.get("status", "")
        if status == "cancelado" or cls == "cancelada":
            n_cancelada += 1
            continue
        if cls not in CLASSIFICACOES_ELEGIVEIS:
            n_inelegivel += 1
            continue
        e = extrair_obra(o)
        if e:
            execucoes.append(e)
        else:
            n_sem_dados += 1

    n_pre = len(execucoes)
    execucoes = [e for e in execucoes if e["inicio_exec"] >= CORTE_INICIO]
    n_cortadas = n_pre - len(execucoes)

    n_total_corte = sum(
        1 for o in obras_raw
        if o.get("classificacao", "") in CLASSIFICACOES_ELEGIVEIS
        and o.get("status", "") != "cancelado"
        and o.get("classificacao", "") != "cancelada"
        and (o.get("data_inicio_real") or "") >= CORTE_INICIO
    )
    n_elegiveis_corte = len(execucoes)

    n_camadas = sum(1 for e in execucoes if e["fonte"] == "camadas")
    n_fase = sum(1 for e in execucoes if e["fonte"] == "fase")
    n_tempo = sum(1 for e in execucoes if e["fonte"] == "tempo_jornadas")
    n_nenhuma = sum(1 for e in execucoes if not e["fonte"])

    print(f"  Canceladas filtradas: {n_cancelada}")
    print(f"  Inelegíveis filtradas: {n_inelegivel}")
    print(f"  Sem dados suficientes: {n_sem_dados}")
    print(f"  Corte >= {CORTE_INICIO}: {n_cortadas} removidas, {len(execucoes)} restantes")
    print(f"  Fonte camadas: {n_camadas} | fase: {n_fase} | tempo: {n_tempo} | nenhuma: {n_nenhuma}")

    faixas = agregar_por_faixa(execucoes)
    globais = calcular_global(execucoes)
    score = calcular_confianca(execucoes, n_total_corte, n_elegiveis_corte)

    print(f"\n{'=' * 60}")
    print(f"  FASES E DESEMPENHO · {globais['total_analisadas']} obras")
    print(f"{'=' * 60}")
    fm = globais["fase_medians"]
    print(f"  Ciclo total mediana:   {globais['ciclo_total_mediana']}d")
    print(f"  Execução mediana:      {fm.get('execucao', 0)}d")
    print(f"  Hibernação mediana:    {fm.get('hibernacao', 0)}d")
    print(f"  Eficiência:            {globais['eficiencia_mediana']}%")
    print(f"  Finalizadas:           {globais['finalizadas']} ({globais['finalizadas_sem_retorno']} limpas + {globais['finalizadas_com_retorno']} retorno)")
    print(f"  Em campo:              {globais['em_campo']} ({globais['em_campo_exec']} exec + {globais['em_campo_retrab']} retrab)")
    print(f"  Score confiança:       {score['total']}/100")
    print()

    for f in faixas:
        eff = round(f['eficiencia']['mediana'] * 100, 1)
        print(
            f"  {f['faixa']:3s} ({f['range']:7s}) | {f['n_obras']:3d} obras "
            f"| exec {f['fases']['execucao']['mediana']:3d}d "
            f"| hib {f['fases']['hibernacao']['mediana']:3d}d "
            f"| ciclo {f['ciclo_total']['mediana']:3d}d "
            f"| eff {eff:5.1f}%"
        )

    out_execucoes = [{k: v for k, v in e.items()} for e in execucoes]
    out = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "score": score["total"],
        "globais": globais,
        "por_faixa": faixas,
        "confianca": score,
        "obras": out_execucoes,
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON: {OUT_JSON.name} ({OUT_JSON.stat().st_size // 1024} KB)")

    html = gerar_html(faixas, globais, execucoes, score)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"HTML: {OUT_HTML.name} ({OUT_HTML.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
