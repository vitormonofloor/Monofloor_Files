"""Analise de execucao real: da 1a camada aplicada ate finalizacao.

Mede quanto tempo de fato leva a execucao por faixa de metragem,
separando entrega limpa vs retorno. Usa camadas_aplicadas como
referencia primaria (data real de aplicacao pelo time).

Uso:
  python analise/dados/analise_execucao.py
"""
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, date
from pathlib import Path
from statistics import median

BASE = Path(__file__).parent
JORN_PATH = BASE.parent / "lab-hermeneuta" / "dados" / "jornadas.json"
OUT_JSON = BASE / "execucao-por-faixa.json"
OUT_HTML = BASE.parent / "execucao.html"

HOJE = date.today()
HOJE_STR = HOJE.isoformat()

# Datas artefato: data de processamento do pipeline, nao de aplicacao real
DATAS_ARTEFATO = {"2026-02-28"}

STATUS_EM_EXECUCAO = {"em_execucao"}
STATUS_RETRABALHO = {"reparo", "marcas_rolo_cera"}
STATUS_EM_CAMPO = STATUS_EM_EXECUCAO | STATUS_RETRABALHO

CORTE_INICIO = "2026-01-01"

FAIXA_ORDER = ["PP", "P", "M", "G", "GG", "XG"]
FAIXA_COLORS = {
    "PP": "#8a5cb0", "P": "#4a7ab8", "M": "#3d8a5a",
    "G": "#b89a4a", "GG": "#c47a4a", "XG": "#c45a5a",
}
FAIXA_RANGES = {
    "PP": "<60", "P": "60-100", "M": "100-150",
    "G": "150-220", "GG": "220-300", "XG": ">300",
}


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
    """Agrupa datas em blocos de trabalho continuo (gap <= gap_max dias).

    Retorna lista de (inicio, fim, n_dias) por bloco.
    """
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


def extrair_execucao(obra):
    """Extrai datas de execucao real de uma obra.

    Filtra datas artefato (2026-02-28), clusteriza camadas em blocos
    de trabalho continuo, calcula dias de aplicacao como soma dos blocos.
    """
    camadas = obra.get("camadas_aplicadas", [])
    ciclos = obra.get("ciclos", [])
    marcos = obra.get("marcos", [])
    fases = obra.get("fases", [])

    inicio_exec = None
    fim_exec = None
    dias_aplicacao_real = None
    n_blocos = 0
    fonte = None

    if camadas:
        dates = [parse_date(c.get("data")) for c in camadas]
        dates = [d for d in dates if d and d.isoformat() not in DATAS_ARTEFATO]
        if dates:
            inicio_exec = min(dates)
            fim_exec = max(dates)
            blocos = clusterizar_blocos(dates, gap_max=14)
            dias_aplicacao_real = sum(b[2] for b in blocos)
            n_blocos = len(blocos)
            fonte = "camadas"

    if not inicio_exec:
        for f in fases:
            nome = f.get("nome", "")
            if "xecu" in nome.lower() and "pr" not in nome[:4].lower():
                d = parse_date(f.get("inicio"))
                if d:
                    inicio_exec = d
                    fim_exec = parse_date(f.get("fim")) or d
                    dias_aplicacao_real = None
                    n_blocos = 0
                    fonte = "fase"
                    break

    if not inicio_exec:
        return None

    # Cross-check com tempo_execucao_dias do jornadas
    tempo_exec_jornadas = obra.get("tempo_execucao_dias") or 0

    # Finalizacao: marco finalizacao
    fim_final = None
    finaliz_marcos = [m for m in marcos if m.get("tipo") == "finalizacao"]
    if finaliz_marcos:
        dates_fin = [parse_date(m.get("data")) for m in finaliz_marcos]
        dates_fin = [d for d in dates_fin if d]
        if dates_fin:
            fim_final = max(dates_fin)

    # Se nao tem marco de finalizacao, usar ultima camada como proxy
    if not fim_final:
        status = obra.get("status", "")
        if status in ("finalizado", "concluido"):
            fim_final = fim_exec
        else:
            fim_final = None

    n_ciclos = len(ciclos) if ciclos else 0
    cls = obra.get("classificacao", "")
    tem_retorno = (
        n_ciclos > 1
        or "retrabalho" in cls.lower()
        or obra.get("status", "") in ("reparo", "marcas_rolo_cera")
        or n_blocos >= 2
    )

    dias_total = None
    if fim_final and fim_final >= inicio_exec:
        dias_total = (fim_final - inicio_exec).days
    elif not fim_final:
        dias_total = (HOJE - inicio_exec).days

    if dias_aplicacao_real is not None and dias_total is not None and dias_aplicacao_real > dias_total:
        dias_aplicacao_real = dias_total

    return {
        "cliente": obra.get("cliente", "?"),
        "faixa": obra.get("faixa_metragem"),
        "m2": obra.get("metragem", 0),
        "status": obra.get("status", ""),
        "classificacao": cls,
        "fonte": fonte,
        "inicio_exec": inicio_exec.isoformat() if inicio_exec else None,
        "fim_exec": fim_exec.isoformat() if fim_exec else None,
        "fim_final": fim_final.isoformat() if fim_final else None,
        "n_ciclos": n_ciclos,
        "n_blocos": n_blocos,
        "tem_retorno": tem_retorno,
        "finalizada": obra.get("status", "") in ("finalizado", "concluido"),
        "em_campo": obra.get("status", "") in STATUS_EM_CAMPO,
        "em_execucao": obra.get("status", "") in STATUS_EM_EXECUCAO,
        "em_retrabalho": obra.get("status", "") in STATUS_RETRABALHO,
        "dias_aplicacao": dias_aplicacao_real,
        "dias_aplicacao_jornadas": tempo_exec_jornadas,
        "dias_total_exec": dias_total,
    }


def analisar_por_faixa(execucoes):
    """Agrupa execucoes por faixa e calcula metricas."""
    por_faixa = defaultdict(list)
    for e in execucoes:
        f = e["faixa"]
        if f:
            por_faixa[f].append(e)

    resultado = []
    for faixa in FAIXA_ORDER:
        obras = por_faixa.get(faixa, [])
        if not obras:
            continue

        finalizadas = [o for o in obras if o["finalizada"]]
        em_campo = [o for o in obras if o["em_campo"]]
        em_exec = [o for o in obras if o["em_execucao"]]
        em_retrab = [o for o in obras if o["em_retrabalho"]]
        com_retorno = [o for o in obras if o["tem_retorno"]]

        dias_aplic = [o["dias_aplicacao"] for o in obras if o["dias_aplicacao"] is not None]

        dias_total_fin = [o["dias_total_exec"] for o in finalizadas if o["dias_total_exec"] is not None]

        fin_com_ret = [o for o in finalizadas if o["tem_retorno"]]
        fin_sem_ret = [o for o in finalizadas if not o["tem_retorno"]]
        dias_fin_com = [o["dias_total_exec"] for o in fin_com_ret if o["dias_total_exec"] is not None]
        dias_fin_sem = [o["dias_total_exec"] for o in fin_sem_ret if o["dias_total_exec"] is not None]

        exec_com_ret = [o for o in em_exec if o["tem_retorno"]]
        exec_sem_ret = [o for o in em_exec if not o["tem_retorno"]]
        dias_exec = [o["dias_total_exec"] for o in em_exec if o["dias_total_exec"] is not None]
        dias_retrab = [o["dias_total_exec"] for o in em_retrab if o["dias_total_exec"] is not None]

        resultado.append({
            "faixa": faixa,
            "range": FAIXA_RANGES.get(faixa, "?"),
            "n_obras": len(obras),
            "n_finalizadas": len(finalizadas),
            "n_com_retorno": len(com_retorno),
            "pct_retorno": round(len(com_retorno) / len(obras) * 100, 1) if obras else 0,
            "dias_aplicacao": {
                "media": safe_avg(dias_aplic),
                "mediana": safe_median(dias_aplic),
                "min": min(dias_aplic) if dias_aplic else 0,
                "max": max(dias_aplic) if dias_aplic else 0,
            },
            "dias_total_finalizadas": {
                "media": safe_avg(dias_total_fin),
                "mediana": safe_median(dias_total_fin),
                "min": min(dias_total_fin) if dias_total_fin else 0,
                "max": max(dias_total_fin) if dias_total_fin else 0,
                "n": len(dias_total_fin),
                "n_com_retorno": len(fin_com_ret),
                "n_sem_retorno": len(fin_sem_ret),
            },
            "dias_com_retorno": {
                "media": safe_avg(dias_fin_com),
                "mediana": safe_median(dias_fin_com),
                "n": len(dias_fin_com),
            },
            "dias_sem_retorno": {
                "media": safe_avg(dias_fin_sem),
                "mediana": safe_median(dias_fin_sem),
                "n": len(dias_fin_sem),
            },
            "em_exec": {
                "n": len(em_exec),
                "n_com_retorno": len(exec_com_ret),
                "n_sem_retorno": len(exec_sem_ret),
                "dias_mediana": safe_median(dias_exec),
                "dias_media": safe_avg(dias_exec),
            },
            "em_retrab": {
                "n": len(em_retrab),
                "dias_mediana": safe_median(dias_retrab),
                "dias_media": safe_avg(dias_retrab),
            },
            "obras_destaque": sorted(
                [o for o in obras if o["dias_total_exec"] is not None],
                key=lambda o: o["dias_total_exec"], reverse=True
            )[:5],
        })

    return resultado


def calcular_global(execucoes):
    finalizadas = [e for e in execucoes if e["finalizada"]]
    com_retorno = [e for e in execucoes if e["tem_retorno"]]
    dias_aplic = [e["dias_aplicacao"] for e in execucoes if e["dias_aplicacao"] is not None]
    dias_total = [e["dias_total_exec"] for e in finalizadas if e["dias_total_exec"] is not None]

    fin_com = [e for e in finalizadas if e["tem_retorno"]]
    fin_sem = [e for e in finalizadas if not e["tem_retorno"]]
    dias_com = [e["dias_total_exec"] for e in fin_com if e["dias_total_exec"] is not None]
    dias_sem = [e["dias_total_exec"] for e in fin_sem if e["dias_total_exec"] is not None]

    n_com_camadas = sum(1 for e in execucoes if e["fonte"] == "camadas")

    return {
        "total_analisadas": len(execucoes),
        "finalizadas": len(finalizadas),
        "finalizadas_com_retorno": len(fin_com),
        "finalizadas_sem_retorno": len(fin_sem),
        "ativas": len(execucoes) - len(finalizadas),
        "com_retorno": len(com_retorno),
        "pct_retorno": round(len(com_retorno) / len(execucoes) * 100, 1) if execucoes else 0,
        "pct_retorno_fin": round(len(fin_com) / len(finalizadas) * 100, 1) if finalizadas else 0,
        "n_com_camadas": n_com_camadas,
        "dias_aplicacao_media": safe_avg(dias_aplic),
        "dias_aplicacao_mediana": safe_median(dias_aplic),
        "dias_total_finalizadas_media": safe_avg(dias_total),
        "dias_total_finalizadas_mediana": safe_median(dias_total),
        "dias_com_retorno_media": safe_avg(dias_com),
        "dias_com_retorno_mediana": safe_median(dias_com),
        "dias_sem_retorno_media": safe_avg(dias_sem),
        "dias_sem_retorno_mediana": safe_median(dias_sem),
        "impacto_retorno_dias": round(safe_avg(dias_com) - safe_avg(dias_sem), 1) if dias_com and dias_sem else 0,
        "em_campo_total": sum(1 for e in execucoes if e["em_campo"]),
        "em_campo_exec": sum(1 for e in execucoes if e["em_execucao"]),
        "em_campo_retrab": sum(1 for e in execucoes if e["em_retrabalho"]),
        "em_campo_dias_mediana": safe_median([e["dias_total_exec"] for e in execucoes if e["em_campo"] and e["dias_total_exec"] is not None]),
        "em_campo_dias_media": safe_avg([e["dias_total_exec"] for e in execucoes if e["em_campo"] and e["dias_total_exec"] is not None]),
        "em_campo_exec_mediana": safe_median([e["dias_total_exec"] for e in execucoes if e["em_execucao"] and e["dias_total_exec"] is not None]),
        "em_campo_retrab_mediana": safe_median([e["dias_total_exec"] for e in execucoes if e["em_retrabalho"] and e["dias_total_exec"] is not None]),
    }


def gerar_html(faixas, globais, execucoes):
    faixas_json = json.dumps(faixas, ensure_ascii=False)
    globais_json = json.dumps(globais, ensure_ascii=False)

    def make_rows(lista):
        rows = ""
        for e in sorted(lista, key=lambda x: -(x["dias_total_exec"] or 0)):
            if e["dias_total_exec"] is None:
                continue
            ret_badge = '<span class="badge ret">retorno</span>' if e["tem_retorno"] else '<span class="badge ok">limpa</span>'
            faixa_color = FAIXA_COLORS.get(e["faixa"], "#999")
            aplic_str = str(e["dias_aplicacao"]) if e["dias_aplicacao"] is not None else "-"
            status_short = e["status"].replace("_", " ")[:18]
            rows += f"""<tr>
              <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{e["cliente"]}</td>
              <td><span class="faixa-badge" style="background:{faixa_color}22;color:{faixa_color};border:1px solid {faixa_color}44">{e["faixa"] or "?"}</span></td>
              <td class="num">{e["m2"] or "-"}</td>
              <td class="num">{aplic_str}</td>
              <td class="num bold">{e["dias_total_exec"]}</td>
              <td>{ret_badge}</td>
              <td class="num">{e["n_ciclos"]}</td>
              <td class="status-cell">{status_short}</td>
            </tr>\n"""
        return rows

    fin_list = [e for e in execucoes if e["finalizada"]]
    exec_list = [e for e in execucoes if e["em_execucao"]]
    retrab_list = [e for e in execucoes if e["em_retrabalho"]]

    fin_ret_list = [e for e in fin_list if e["tem_retorno"]]
    fin_limpa_list = [e for e in fin_list if not e["tem_retorno"]]
    exec_ret_list = [e for e in exec_list if e["tem_retorno"]]

    rows_fin = make_rows(fin_list)
    rows_fin_ret = make_rows(fin_ret_list)
    rows_fin_limpa = make_rows(fin_limpa_list)
    rows_exec = make_rows(exec_list)
    rows_exec_ret = make_rows(exec_ret_list)
    rows_retrab = make_rows(retrab_list)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Execucao · Qualidade Monofloor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #ddd7cd; --card: #ffffff; --card-2: #f7f4ef; --card-3: #f0ebe3;
  --border: #e0d8cc; --text: #3a3530; --text-2: #2a2520; --muted: #8a7e72;
  --muted-2: #b8b0a4; --accent: #b8a080; --green: #3d8a5a; --amber: #b89a4a;
  --red: #c45a5a; --blue: #4a7ab8; --purple: #8a5cb0;
  --mono: 'JetBrains Mono', ui-monospace, monospace;
  --sans: 'Plus Jakarta Sans', system-ui, sans-serif;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ background: var(--bg); color: var(--text); font-family: var(--sans); font-size: 13px; line-height: 1.55; }}
body {{ min-height: 100vh; }}

header {{ position: sticky; top: 0; z-index: 50; background: rgba(255,255,255,.92); border-bottom: 1px solid var(--border); backdrop-filter: blur(16px); }}
.top-row {{ display: flex; align-items: center; gap: 20px; max-width: 1200px; margin: 0 auto; padding: 0 32px; height: 52px; }}
.brand {{ display: flex; align-items: center; gap: 10px; }}
.brand-mark {{ width: 26px; height: 26px; border-radius: 6px; background: linear-gradient(135deg, var(--accent), #9a8060); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 11px; color: #fff; }}
.brand-text {{ font-size: 14px; font-weight: 300; letter-spacing: 5px; text-transform: uppercase; }}
.top-sep {{ width: 1px; height: 22px; background: var(--border); }}
.top-title {{ font-size: 13px; font-weight: 600; color: var(--text-2); }}
.top-stamp {{ margin-left: auto; font-size: 10px; color: var(--muted-2); font-family: var(--mono); }}

.container {{ max-width: 1200px; margin: 0 auto; padding: 28px 32px 80px; }}

.headline {{ background: var(--card); border-radius: 12px; padding: 24px 28px; border: 1px solid var(--border); margin-bottom: 24px; }}
.headline h2 {{ font-size: 16px; font-weight: 700; color: var(--text-2); margin-bottom: 12px; }}
.headline .manchete {{ font-size: 13px; color: var(--text); font-weight: 500; margin-bottom: 8px; line-height: 1.7; }}
.headline p {{ font-size: 12px; color: var(--muted); line-height: 1.7; }}

.kpis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }}
.kpi {{ background: var(--card); border-radius: 10px; padding: 16px 18px; border: 1px solid var(--border); }}
.kpi-label {{ font-size: 10px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin-bottom: 6px; }}
.kpi-value {{ font-family: var(--mono); font-size: 24px; font-weight: 700; color: var(--text-2); }}
.kpi-value small {{ font-size: 12px; font-weight: 400; color: var(--muted); margin-left: 4px; }}
.kpi-sub {{ font-size: 11px; color: var(--muted); margin-top: 4px; }}
.kpi-compare {{ display: flex; gap: 8px; margin-top: 8px; }}
.kpi-compare span {{ font-family: var(--mono); font-size: 10px; padding: 2px 6px; border-radius: 4px; }}
.kpi-compare .limpa {{ background: rgba(61,138,90,.1); color: var(--green); }}
.kpi-compare .retorno {{ background: rgba(196,90,90,.1); color: var(--red); }}

.section-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); font-weight: 600; margin: 32px 0 12px; }}

.tabs {{ display: flex; gap: 0; margin-bottom: 24px; }}
.tab {{ padding: 10px 24px; font-size: 12px; font-weight: 600; cursor: pointer; border: 1px solid var(--border); background: var(--card-3); color: var(--muted); transition: all .2s; }}
.tab:first-child {{ border-radius: 8px 0 0 8px; }}
.tab:last-child {{ border-radius: 0 8px 8px 0; }}
.tab.active {{ background: var(--card); color: var(--text-2); border-color: var(--accent); z-index: 1; }}
.tab .tab-count {{ font-family: var(--mono); font-size: 10px; margin-left: 6px; padding: 1px 5px; border-radius: 3px; background: rgba(0,0,0,.06); }}
.tab.active .tab-count {{ background: rgba(184,160,128,.15); color: var(--accent); }}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}

.faixas-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; margin-bottom: 24px; }}
.faixa-card {{ background: var(--card); border-radius: 12px; padding: 20px; border: 1px solid var(--border); }}
.faixa-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }}
.faixa-badge {{ font-family: var(--mono); font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 6px; }}
.faixa-range {{ font-size: 11px; color: var(--muted); }}
.faixa-n {{ font-family: var(--mono); font-size: 11px; color: var(--muted-2); margin-left: auto; }}
.faixa-main {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }}
.faixa-metric-label {{ font-size: 10px; text-transform: uppercase; color: var(--muted); letter-spacing: .04em; }}
.faixa-metric-value {{ font-family: var(--mono); font-size: 20px; font-weight: 700; color: var(--text-2); }}
.faixa-metric-value small {{ font-size: 11px; font-weight: 400; color: var(--muted); }}
.faixa-bar {{ height: 8px; border-radius: 4px; background: var(--card-3); margin: 12px 0 8px; overflow: hidden; display: flex; }}
.faixa-bar-seg {{ height: 100%; transition: width .6s ease; }}
.faixa-detail {{ font-size: 11px; color: var(--muted); line-height: 1.7; }}
.faixa-detail strong {{ color: var(--text); }}

.insight {{ background: var(--card-3); border-radius: 10px; padding: 16px 20px; border-left: 3px solid var(--accent); margin-bottom: 16px; font-size: 12px; color: var(--text); line-height: 1.7; }}
.insight strong {{ color: var(--text-2); }}
.insight .neg {{ color: var(--red); font-weight: 600; }}
.insight .pos {{ color: var(--green); font-weight: 600; }}

.table-wrap {{ background: var(--card); border-radius: 12px; padding: 4px; border: 1px solid var(--border); margin-bottom: 24px; overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
th {{ text-align: left; padding: 10px 8px; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); white-space: nowrap; }}
td {{ padding: 7px 8px; border-bottom: 1px solid rgba(224,216,204,.3); }}
.num {{ font-family: var(--mono); text-align: right; }}
.bold {{ font-weight: 700; color: var(--text-2); }}
tr:hover {{ background: var(--card-2); }}
.badge {{ font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: 600; white-space: nowrap; }}
.badge.ret {{ background: rgba(196,90,90,.1); color: var(--red); }}
.badge.ok {{ background: rgba(61,138,90,.1); color: var(--green); }}
.status-cell {{ font-size: 11px; color: var(--muted); white-space: nowrap; }}

footer {{ text-align: center; padding: 40px 0 20px; font-size: 10px; color: var(--muted-2); }}
@media(max-width:800px) {{ .kpis {{ grid-template-columns: repeat(2, 1fr); }} .faixas-grid {{ grid-template-columns: 1fr; }} .container {{ padding: 16px; }} }}
</style>
</head>
<body>
<header>
  <div class="top-row">
    <div class="brand"><div class="brand-mark">M</div><div class="brand-text">monofloor</div></div>
    <div class="top-sep"></div>
    <div class="top-title">Execucao por Faixa</div>
    <div class="top-stamp">{HOJE_STR}</div>
  </div>
</header>

<div class="container">
  <div class="headline" id="headline"></div>

  <div class="tabs">
    <div class="tab active" onclick="switchTab('fin')">Finalizadas<span class="tab-count">{len(fin_list)}</span></div>
    <div class="tab" onclick="switchTab('exec')">Em execucao<span class="tab-count">{len(exec_list)}</span></div>
    <div class="tab" onclick="switchTab('retrab')">Retrabalho<span class="tab-count">{len(retrab_list)}</span></div>
  </div>

  <!-- FINALIZADAS -->
  <div id="panel-fin" class="tab-panel active">
    <div class="kpis" id="kpis-fin"></div>
    <div class="section-title">Por faixa de metragem (finalizadas)</div>
    <div class="faixas-grid" id="faixasGrid-fin"></div>
    <div class="section-title">Insights</div>
    <div id="insights"></div>

    <div class="section-title" style="color:var(--red)">Obras com retorno ({len(fin_ret_list)})</div>
    <div class="table-wrap" style="border-left:3px solid var(--red)">
      <table>
        <thead><tr>
          <th>Cliente</th><th>Faixa</th><th>m2</th><th>Aplic.</th><th>Total exec</th><th>Tipo</th><th>Ciclos</th><th>Status</th>
        </tr></thead>
        <tbody>{rows_fin_ret}</tbody>
      </table>
    </div>

    <div class="section-title" style="color:var(--green)">Entregas limpas ({len(fin_limpa_list)})</div>
    <div class="table-wrap" style="border-left:3px solid var(--green)">
      <table>
        <thead><tr>
          <th>Cliente</th><th>Faixa</th><th>m2</th><th>Aplic.</th><th>Total exec</th><th>Tipo</th><th>Ciclos</th><th>Status</th>
        </tr></thead>
        <tbody>{rows_fin_limpa}</tbody>
      </table>
    </div>
  </div>

  <!-- EM EXECUCAO -->
  <div id="panel-exec" class="tab-panel">
    <div class="kpis" id="kpis-exec"></div>
    <div class="section-title">Por faixa de metragem (em execucao)</div>
    <div class="faixas-grid" id="faixasGrid-exec"></div>
    {'<div class="section-title" style="color:var(--red)">Com sinal de retorno (' + str(len(exec_ret_list)) + ')</div><div class="table-wrap" style="border-left:3px solid var(--red)"><table><thead><tr><th>Cliente</th><th>Faixa</th><th>m2</th><th>Aplic.</th><th>Dias em curso</th><th>Tipo</th><th>Ciclos</th><th>Status</th></tr></thead><tbody>' + rows_exec_ret + '</tbody></table></div>' if exec_ret_list else ''}
    <div class="section-title">Todas em execucao ({len(exec_list)})</div>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Cliente</th><th>Faixa</th><th>m2</th><th>Aplic.</th><th>Dias em curso</th><th>Tipo</th><th>Ciclos</th><th>Status</th>
        </tr></thead>
        <tbody>{rows_exec}</tbody>
      </table>
    </div>
  </div>

  <!-- RETRABALHO -->
  <div id="panel-retrab" class="tab-panel">
    <div class="kpis" id="kpis-retrab"></div>
    <div class="section-title">Por faixa de metragem (retrabalho)</div>
    <div class="faixas-grid" id="faixasGrid-retrab"></div>
    <div class="section-title">Obras em retrabalho ({len(retrab_list)} com dados)</div>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Cliente</th><th>Faixa</th><th>m2</th><th>Aplic.</th><th>Dias em curso</th><th>Tipo</th><th>Ciclos</th><th>Status</th>
        </tr></thead>
        <tbody>{rows_retrab}</tbody>
      </table>
    </div>
  </div>

  <div class="section-title" style="margin-top:40px">Metodologia</div>
  <div class="insight" style="border-left-color:var(--muted-2)">
    <strong>Corte temporal:</strong> somente obras com inicio de execucao a partir de {CORTE_INICIO}.
    <strong>Fonte primaria:</strong> datas de camadas aplicadas (Telegram). <strong>Fallback:</strong> fase Execucao do Painel.
    Datas artefato (2026-02-28) filtradas. Camadas agrupadas em blocos de trabalho (gap &le; 14d).
    Mediana de {len(fin_list)} finalizadas. Em execucao = status em_execucao no Painel ({len(exec_list)} com dados). Retrabalho = reparo + marcas_rolo_cera ({len(retrab_list)} com dados).
  </div>
</div>
<footer>Qualidade Monofloor · Execucao por Faixa · {HOJE_STR}</footer>

<script>
const F = {faixas_json};
const G = {globais_json};
const FAIXA_COLORS = {json.dumps(FAIXA_COLORS)};

function switchTab(id) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + id).classList.add('active');
  event.target.closest('.tab').classList.add('active');
}}

function init() {{
  renderHeadline();
  renderKPIsFin();
  renderKPIsExec();
  renderKPIsRetrab();
  renderFaixasFin();
  renderFaixasExec();
  renderFaixasRetrab();
  renderInsights();
}}

function renderHeadline() {{
  document.getElementById('headline').innerHTML = `
    <h2>Quanto tempo leva a execucao real?</h2>
    <div class="manchete">Da primeira camada ate a finalizacao: <strong>${{G.dias_total_finalizadas_mediana}} dias</strong> (mediana). Das ${{G.finalizadas}} finalizadas: <span style="color:var(--green);font-weight:600">${{G.finalizadas_sem_retorno}} limpas</span> + <span style="color:var(--red);font-weight:600">${{G.finalizadas_com_retorno}} com retorno</span> (${{G.pct_retorno_fin}}%). O retorno adiciona em media <span style="color:var(--red);font-weight:600">+${{G.impacto_retorno_dias}} dias</span>.</div>
    <p>${{G.total_analisadas}} obras com dados. ${{G.finalizadas}} finalizadas, ${{G.em_campo_exec}} em execucao, ${{G.em_campo_retrab}} em retrabalho.</p>`;
}}

function renderKPIsFin() {{
  document.getElementById('kpis-fin').innerHTML = `
    <div class="kpi"><div class="kpi-label">Finalizadas</div><div class="kpi-value">${{G.finalizadas}}<small>obras</small></div><div class="kpi-sub">1a camada ate finalizacao</div>
      <div class="kpi-compare"><span class="limpa">${{G.finalizadas_sem_retorno}} limpas</span><span class="retorno">${{G.finalizadas_com_retorno}} com retorno</span></div></div>
    <div class="kpi"><div class="kpi-label">Exec. total (mediana)</div><div class="kpi-value">${{G.dias_total_finalizadas_mediana}}<small>dias</small></div><div class="kpi-sub">Mediana geral</div>
      <div class="kpi-compare"><span class="limpa">${{G.dias_sem_retorno_mediana}}d limpa</span><span class="retorno">${{G.dias_com_retorno_mediana}}d c/ retorno</span></div></div>
    <div class="kpi"><div class="kpi-label">Taxa de retorno (fin.)</div><div class="kpi-value" style="color:var(--red)">${{G.pct_retorno_fin}}<small>%</small></div><div class="kpi-sub">${{G.finalizadas_com_retorno}} de ${{G.finalizadas}} finalizadas</div></div>
    <div class="kpi"><div class="kpi-label">Custo do retorno</div><div class="kpi-value" style="color:var(--red)">+${{G.impacto_retorno_dias}}<small>dias</small></div><div class="kpi-sub">Media adicional vs entrega limpa</div></div>`;
}}

function renderKPIsExec() {{
  document.getElementById('kpis-exec').innerHTML = `
    <div class="kpi"><div class="kpi-label">Em execucao</div><div class="kpi-value">${{G.em_campo_exec}}<small>obras</small></div><div class="kpi-sub">Status em_execucao no Painel</div></div>
    <div class="kpi"><div class="kpi-label">Dias em curso (mediana)</div><div class="kpi-value">${{G.em_campo_exec_mediana}}<small>dias</small></div><div class="kpi-sub">Desde inicio da execucao</div></div>
    <div class="kpi"><div class="kpi-label">Benchmark fin.</div><div class="kpi-value" style="color:var(--muted)">${{G.dias_total_finalizadas_mediana}}<small>dias</small></div><div class="kpi-sub">Mediana das finalizadas</div></div>
    <div class="kpi"><div class="kpi-label">Aplicacao fisica</div><div class="kpi-value">${{G.dias_aplicacao_mediana}}<small>dias</small></div><div class="kpi-sub">Mediana geral (camadas)</div></div>`;
}}

function renderKPIsRetrab() {{
  document.getElementById('kpis-retrab').innerHTML = `
    <div class="kpi"><div class="kpi-label">Em retrabalho</div><div class="kpi-value" style="color:var(--red)">${{G.em_campo_retrab}}<small>obras</small></div><div class="kpi-sub">Reparo + marcas rolo cera</div></div>
    <div class="kpi"><div class="kpi-label">Dias em curso (mediana)</div><div class="kpi-value" style="color:var(--red)">${{G.em_campo_retrab_mediana}}<small>dias</small></div><div class="kpi-sub">Desde inicio da execucao</div></div>
    <div class="kpi"><div class="kpi-label">Custo do retorno</div><div class="kpi-value" style="color:var(--red)">+${{G.impacto_retorno_dias}}<small>dias</small></div><div class="kpi-sub">Media adicional vs entrega limpa</div></div>
    <div class="kpi"><div class="kpi-label">Benchmark fin.</div><div class="kpi-value" style="color:var(--muted)">${{G.dias_total_finalizadas_mediana}}<small>dias</small></div><div class="kpi-sub">Mediana das finalizadas</div></div>`;
}}

function renderFaixasFin() {{
  const grid = document.getElementById('faixasGrid-fin');
  F.forEach(f => {{
    if (f.n_finalizadas === 0) return;
    const color = FAIXA_COLORS[f.faixa] || '#999';
    const nFin = f.dias_total_finalizadas.n;
    const nRet = f.dias_total_finalizadas.n_com_retorno;
    const nLimpa = f.dias_total_finalizadas.n_sem_retorno;
    const pctRet = nFin > 0 ? Math.round(nRet / nFin * 100) : 0;
    const pctLimpa = 100 - pctRet;
    const topObras = f.obras_destaque.filter(o => o.finalizada).slice(0,3).map(o => `${{o.cliente.substring(0,25)}} (${{o.dias_total_exec}}d${{o.tem_retorno?' ret':''}})`).join(', ');

    grid.innerHTML += `
      <div class="faixa-card" style="border-top:3px solid ${{color}}">
        <div class="faixa-header">
          <span class="faixa-badge" style="background:${{color}}22;color:${{color}};border:1px solid ${{color}}44">${{f.faixa}}</span>
          <span class="faixa-range">${{f.range}} m2</span>
          <span class="faixa-n">${{nFin}} fin</span>
        </div>
        <div class="faixa-main">
          <div><div class="faixa-metric-label">Exec. total (med)</div><div class="faixa-metric-value">${{f.dias_total_finalizadas.mediana}}<small>d</small></div></div>
          <div><div class="faixa-metric-label">Aplicacao (med)</div><div class="faixa-metric-value">${{f.dias_aplicacao.mediana}}<small>d</small></div></div>
          <div><div class="faixa-metric-label">Composicao</div><div class="faixa-metric-value" style="font-size:14px"><span style="color:var(--green)">${{nLimpa}} limpas</span> + <span style="color:var(--red)">${{nRet}} ret</span></div></div>
          <div><div class="faixa-metric-label">% retorno</div><div class="faixa-metric-value" style="color:var(--red)">${{pctRet}}<small>%</small></div></div>
        </div>
        <div class="faixa-bar">
          <div class="faixa-bar-seg" style="width:${{pctLimpa}}%;background:${{color}}88"></div>
          <div class="faixa-bar-seg" style="width:${{pctRet}}%;background:var(--red)"></div>
        </div>
        <div class="faixa-detail">
          ${{f.dias_sem_retorno.n > 0 ? '<strong>Limpa:</strong> ' + f.dias_sem_retorno.mediana + 'd mediana (' + f.dias_sem_retorno.n + ' obras). ' : ''}}
          ${{f.dias_com_retorno.n > 0 ? '<strong>Com retorno:</strong> ' + f.dias_com_retorno.mediana + 'd mediana (' + f.dias_com_retorno.n + ' obras). ' : ''}}
          ${{topObras ? '<br>Mais longas: ' + topObras : ''}}
        </div>
      </div>`;
  }});
}}

function renderFaixasGeneric(gridId, dataKey, label) {{
  const grid = document.getElementById(gridId);
  F.forEach(f => {{
    const c = f[dataKey];
    if (c.n === 0) return;
    const color = FAIXA_COLORS[f.faixa] || '#999';
    const benchFin = f.dias_total_finalizadas.mediana;
    const excede = c.dias_mediana > benchFin && benchFin > 0;

    grid.innerHTML += `
      <div class="faixa-card" style="border-top:3px solid ${{color}}">
        <div class="faixa-header">
          <span class="faixa-badge" style="background:${{color}}22;color:${{color}};border:1px solid ${{color}}44">${{f.faixa}}</span>
          <span class="faixa-range">${{f.range}} m2</span>
          <span class="faixa-n">${{c.n}} ${{label}}</span>
        </div>
        <div class="faixa-main">
          <div><div class="faixa-metric-label">Dias em curso (med)</div><div class="faixa-metric-value" ${{excede ? 'style="color:var(--red)"' : ''}}>${{c.dias_mediana}}<small>d</small></div></div>
          <div><div class="faixa-metric-label">Benchmark fin.</div><div class="faixa-metric-value" style="color:var(--muted)">${{benchFin}}<small>d</small></div></div>
        </div>
        <div class="faixa-detail">
          ${{excede ? '<strong style="color:var(--red)">Mediana ja excede benchmark das finalizadas.</strong>' : '<strong style="color:var(--green)">Dentro do benchmark.</strong>'}}
        </div>
      </div>`;
  }});
}}

function renderFaixasExec() {{ renderFaixasGeneric('faixasGrid-exec', 'em_exec', 'em exec'); }}
function renderFaixasRetrab() {{ renderFaixasGeneric('faixasGrid-retrab', 'em_retrab', 'retrab'); }}

function renderInsights() {{
  const el = document.getElementById('insights');
  let html = '';

  const worstRet = F.reduce((a,b) => a.pct_retorno > b.pct_retorno ? a : b);
  const bestRet = F.filter(f=>f.n_obras>=3).reduce((a,b) => a.pct_retorno < b.pct_retorno ? a : b, F[0]);
  html += '<div class="insight"><strong>Faixa com mais retorno:</strong> ' + worstRet.faixa + ' (' + worstRet.range + ' m2) com <span class="neg">' + worstRet.pct_retorno + '% de retorno</span>. ';
  if (bestRet.faixa !== worstRet.faixa) html += 'Menor taxa: ' + bestRet.faixa + ' com <span class="pos">' + bestRet.pct_retorno + '%</span>.';
  html += '</div>';

  if (G.impacto_retorno_dias > 0) {{
    html += '<div class="insight"><strong>Impacto do retorno no prazo:</strong> obras com retorno levam em media <span class="neg">+' + G.impacto_retorno_dias + ' dias</span> que entregas limpas (' + G.dias_com_retorno_mediana + 'd vs ' + G.dias_sem_retorno_mediana + 'd mediana).</div>';
  }}

  const fastest = F.filter(f=>f.dias_total_finalizadas.n>0).reduce((a,b) => a.dias_total_finalizadas.mediana < b.dias_total_finalizadas.mediana ? a : b, F[0]);
  html += '<div class="insight"><strong>Faixa mais rapida:</strong> ' + fastest.faixa + ' (' + fastest.range + ' m2) com mediana de <span class="pos">' + fastest.dias_total_finalizadas.mediana + ' dias</span> da 1a camada ate finalizacao.</div>';

  const alertasExec = F.filter(f => f.em_exec.n > 0 && f.dias_total_finalizadas.n > 0 && f.em_exec.dias_mediana > f.dias_total_finalizadas.mediana);
  if (alertasExec.length > 0) {{
    html += '<div class="insight" style="border-left-color:var(--amber)"><strong>Execucao acima do benchmark:</strong> ';
    html += alertasExec.map(f => f.faixa + ' (' + f.em_exec.dias_mediana + 'd vs ' + f.dias_total_finalizadas.mediana + 'd)').join(', ');
    html += '.</div>';
  }}

  el.innerHTML = html;
}}

init();
</script>
</body>
</html>"""
    return html


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("Carregando jornadas.json...")
    obras = json.loads(JORN_PATH.read_text(encoding="utf-8"))["obras"]
    print(f"  {len(obras)} obras")

    print("Extraindo dados de execucao...")
    execucoes = []
    sem_dados = 0
    for o in obras:
        e = extrair_execucao(o)
        if e:
            execucoes.append(e)
        else:
            sem_dados += 1

    n_pre = len(execucoes)
    execucoes = [e for e in execucoes if e["inicio_exec"] and e["inicio_exec"] >= CORTE_INICIO]
    n_cortadas = n_pre - len(execucoes)

    n_camadas = sum(1 for e in execucoes if e["fonte"] == "camadas")
    n_fase = sum(1 for e in execucoes if e["fonte"] == "fase")
    print(f"  {n_pre} com dados de execucao, {sem_dados} sem dados")
    print(f"  Corte >= {CORTE_INICIO}: {n_cortadas} removidas, {len(execucoes)} restantes")
    print(f"  Fonte camadas: {n_camadas} | Fonte fase: {n_fase}")
    print(f"  dias_aplicacao disponivel: {sum(1 for e in execucoes if e['dias_aplicacao'] is not None)} obras")

    faixas = analisar_por_faixa(execucoes)
    globais = calcular_global(execucoes)

    print(f"\n{'='*60}")
    print(f"  EXECUCAO REAL · {globais['total_analisadas']} obras")
    print(f"{'='*60}")
    print(f"  1a camada -> finalizacao: {globais['dias_total_finalizadas_mediana']}d mediana ({globais['dias_total_finalizadas_media']}d media)")
    print(f"  Aplicacao fisica:         {globais['dias_aplicacao_mediana']}d mediana")
    print(f"  Taxa de retorno:          {globais['pct_retorno']}% ({globais['com_retorno']}/{globais['total_analisadas']})")
    print(f"  Sem retorno:              {globais['dias_sem_retorno_mediana']}d mediana")
    print(f"  Com retorno:              {globais['dias_com_retorno_mediana']}d mediana")
    print(f"  Impacto do retorno:       +{globais['impacto_retorno_dias']}d")
    print(f"\n  EM CAMPO AGORA:")
    print(f"  Total em campo:           {globais['em_campo_total']} ({globais['em_campo_exec']} exec + {globais['em_campo_retrab']} retrab)")
    print(f"  Dias em curso (mediana):  {globais['em_campo_dias_mediana']}d")
    print(f"  Exec mediana:             {globais['em_campo_exec_mediana']}d")
    print(f"  Retrab mediana:           {globais['em_campo_retrab_mediana']}d")
    print()

    for f in faixas:
        print(f"  {f['faixa']:3s} ({f['range']:7s}) | {f['n_obras']:3d} obras | aplic {f['dias_aplicacao']['mediana']:3d}d | total {f['dias_total_finalizadas']['mediana']:3d}d | retorno {f['pct_retorno']:5.1f}%")

    out = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "globais": globais,
        "por_faixa": faixas,
        "obras": execucoes,
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON: {OUT_JSON.name} ({OUT_JSON.stat().st_size // 1024} KB)")

    html = gerar_html(faixas, globais, execucoes)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"HTML: {OUT_HTML.name} ({OUT_HTML.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
