"""
gerar-relatorio.py — Gerador do Relatório Quinzenal de Qualidade
================================================================

Lê dados do Dashboard (rodrigo-stats + headline + score-historico),
do Lab Orion (discordancias-v3) e dos endpoints subutilizados
(relatorio-extras: analise + alerts + forecast + dashboard),
calcula deltas vs quinzena anterior e gera o relatório Markdown.

Princípio do relatório (firmado 2026-05-04):
- Cada problema citado vem com hipótese de causa + ação sugerida
- Tom moderno e direto · zero "ressaltando, pautando, possibilitando"
- Conteúdo 100% derivado das fontes existentes (sem inventar indicadores)

Fontes:
- analise/dados/headline.json
- analise/dados/rodrigo-stats.json
- analise/dados/score-historico.json
- analise/dados/relatorio-extras.json (gerar com: python coletar-relatorio-extras.py)
- C:/Users/vitor/lab-hermeneuta-pub/public/dados/discordancias-v3.json

Uso:
    python gerar-relatorio.py
    python gerar-relatorio.py --inicio 2026-04-20 --fim 2026-05-04
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# ═══ Paths ═══
ROOT = Path(__file__).parent
DADOS = ROOT / "dados"
ORION_DADOS = Path("C:/Users/vitor/lab-hermeneuta-pub/public/dados")
SAIDA = ROOT / "relatorios"


# ═══ Helpers ═══

def load_json(path):
    """Lê JSON com tolerância a BOM (utf-8-sig)."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def fmt_num(n, casas=0):
    """Formata número com separador de milhar PT-BR."""
    if n is None:
        return "—"
    if casas == 0:
        return f"{n:,.0f}".replace(",", ".")
    return f"{n:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_delta(atual, anterior, suffix="", invert=False):
    """Formata delta com seta direcional. invert=True quando MENOS é melhor."""
    if anterior is None or atual is None:
        return "—"
    diff = atual - anterior
    if diff == 0:
        return "◆ 0"
    melhorou = (diff > 0 and not invert) or (diff < 0 and invert)
    seta = "▲" if diff > 0 else "▼"
    sinal = "+" if diff > 0 else ""
    icone = "" if melhorou else " ⚠"
    return f"{seta} {sinal}{fmt_num(diff)}{suffix}{icone}".replace("+-", "-")


def fmt_pct(v):
    if v is None:
        return "—"
    return f"{v:.0f}%" if v == int(v) else f"{v:.1f}%"


def buscar_no_historico(historico, data_alvo, campo="score"):
    if not historico or not isinstance(historico, list):
        return None
    iso_alvo = data_alvo.isoformat() if hasattr(data_alvo, "isoformat") else data_alvo
    validos = [e for e in historico if e.get(campo, 0) > 0 and e.get("date", "") <= iso_alvo]
    if validos:
        return validos[-1]
    todos = [e for e in historico if e.get(campo, 0) > 0]
    return todos[0] if todos else None


# ═══ Argumentos & período ═══

def parse_args():
    p = argparse.ArgumentParser(description="Gera relatório quinzenal de Qualidade.")
    p.add_argument("--inicio", help="Data início YYYY-MM-DD (default: hoje-14d)")
    p.add_argument("--fim", help="Data fim YYYY-MM-DD (default: hoje)")
    p.add_argument("--saida", help="Caminho do arquivo de saída (default: auto-nomeado)")
    return p.parse_args()


def calcular_periodos(args):
    fim = date.fromisoformat(args.fim) if args.fim else date.today()
    inicio = date.fromisoformat(args.inicio) if args.inicio else fim - timedelta(days=14)
    duracao = (fim - inicio).days + 1
    fim_ant = inicio - timedelta(days=1)
    inicio_ant = fim_ant - timedelta(days=duracao - 1)
    return inicio, fim, inicio_ant, fim_ant


def nome_arquivo_auto(inicio, fim):
    quinzena = 1 if fim.day <= 15 else 2
    return f"{fim.year}-{fim.month:02d}-quinzena-{quinzena}"


# ═══ Seções do relatório ═══

def secao_header(inicio, fim):
    quinzena = 1 if fim.day <= 15 else 2
    meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    periodo = f"{inicio.strftime('%d/%m')} a {fim.strftime('%d/%m/%Y')}"
    return f"""# Relatório Quinzenal de Qualidade

**Período:** {periodo} · Quinzena {quinzena} de {meses[fim.month]}
**Setor de Qualidade Monofloor · Vitor Gomes, Coordenador**
**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

---
"""


def gerar_alertas_executivos(extras):
    """3 alertas mais críticos do Resumo, vindos de /api/analytics/alerts."""
    alerts = (extras or {}).get("alerts", {}) or {}
    lista = alerts.get("alerts", []) if isinstance(alerts, dict) else []
    high = [a for a in lista if a.get("severity") == "HIGH"]
    if len(high) < 3:
        high += [a for a in lista if a.get("severity") == "MEDIUM" and a not in high]
    selecionados = high[:3]

    if not selecionados:
        return None

    out = []
    for a in selecionados:
        cliente = a.get("clienteNome", "?")
        msg = a.get("message", "")
        tipo = a.get("type", "")
        # Causa + ação inferidas pelo tipo
        if tipo == "NO_TEAM":
            causa = "equipe ainda não alocada"
            acao = f"alocar equipe pro projeto **{cliente}**"
        elif tipo == "STAGE_DELAY":
            causa = "fase atual atrás da prevista pelo cronograma"
            stage = a.get("expectedStage", "")
            acao = f"acelerar transição pra fase **{stage}**" if stage else "acelerar transição de fase"
        else:
            causa = "alerta sistêmico do Painel"
            acao = "investigar caso"
        out.append(f"**{cliente}** — {msg} · **Causa:** {causa} · **→ Ação:** {acao}")
    return out


def gerar_destaques_executivos(rs, extras, score_atual, score_ant):
    """3 destaques positivos do período."""
    destaques = []

    # Destaque 1: capacidade
    cap = (rs or {}).get("capacidade", {})
    pct = cap.get("utilization_percent", 0)
    if pct < 50:
        destaques.append(
            f"Operação a {pct}% da capacidade · espaço produtivo considerável "
            f"({fmt_num(cap.get('capacidade_mensal_produtiva', 0) - (rs.get('totais', {}) or {}).get('m2_em_execucao', 0))} m²/mês livres)"
        )

    # Destaque 2: cobertura KIRA boa
    op_kira = (rs or {}).get("operacional_kira", {})
    if op_kira.get("total_fluxo", 0) > 0:
        cob = op_kira.get("com_kira", 0) / op_kira["total_fluxo"] * 100
        if cob > 60:
            destaques.append(
                f"Cobertura KIRA em {fmt_pct(cob)} ({op_kira.get('com_kira')} de {op_kira['total_fluxo']} obras) · "
                f"melhor visibilidade de comunicação com cliente"
            )

    # Destaque 3: % saudáveis
    saudavel_pct = op_kira.get("saudavel_pct_no_monitorado", 0)
    if saudavel_pct > 60:
        destaques.append(
            f"{op_kira.get('saudavel', 0)} obras com clima saudável "
            f"({fmt_pct(saudavel_pct)} das monitoradas pelo KIRA)"
        )

    # Destaque 4 (fallback): score acima de 50
    if not destaques and score_atual:
        destaques.append(f"Score Saúde em {score_atual}/100")

    # Garante 3
    while len(destaques) < 3:
        destaques.append("[REVISAR]")
    return destaques[:3]


def secao_resumo_executivo(headline, rs, score_ant, extras):
    score = headline.get("score", 0) if headline else 0
    score_ant_val = score_ant.get("score") if score_ant else None
    score_delta = fmt_delta(score, score_ant_val)

    totais = rs.get("totais", {}) if rs else {}
    ativas = totais.get("ativas", 0)
    em_exec = totais.get("em_execucao", 0)
    por_status = rs.get("por_status", {}) if rs else {}
    em_retorno = por_status.get("reparo", 0) + por_status.get("marcas_rolo_cera", 0)
    cap = rs.get("capacidade", {}) if rs else {}
    cap_pct = cap.get("utilization_percent", 0)

    summary = (extras or {}).get("analise", {}) or {}
    summary = summary.get("summary", {}) if isinstance(summary, dict) else {}
    atrasadas = summary.get("atrasados", 0)

    # Manchete
    if score >= 70:
        zona = "verde"
    elif score >= 50:
        zona = "amarela"
    else:
        zona = "vermelha"
    manchete = (
        f"Operação fechou a quinzena com Score {score}/100 (zona {zona}), "
        f"{score_delta} vs quinzena anterior. "
        f"{ativas} obras ativas em fluxo, {em_exec} em execução agora, "
        f"{atrasadas} atrasadas e {em_retorno} em pós-entrega (reparo + marcas)."
    )

    kpis_md = (
        "| KPI | Atual | Anterior | Δ |\n"
        "|---|---|---|---|\n"
        f"| Total ativas em fluxo | {ativas} | — | — |\n"
        f"| Em execução agora | {em_exec} | — | — |\n"
        f"| Atrasadas (Painel) | {atrasadas} | — | — |\n"
        f"| Obras em retorno (reparo + marcas) | {em_retorno} | — | — |\n"
        f"| Capacidade utilizada | {cap_pct}% | — | — |\n"
        f"| Score Saúde Operacional | {score}/100 | {score_ant_val or '—'} | {score_delta} |\n"
    )

    destaques = gerar_destaques_executivos(rs, extras, score, score_ant_val)
    alertas = gerar_alertas_executivos(extras) or [
        "[REVISAR]", "[REVISAR]", "[REVISAR]"
    ]

    destaques_md = "\n".join(f"{i+1}. {d}" for i, d in enumerate(destaques))
    alertas_md = "\n".join(f"{i+1}. {a}" for i, a in enumerate(alertas))

    return f"""## 1 · Resumo Executivo

> [REVISAR · rascunho auto] {manchete}

**Score Saúde Operacional:** {score}/100 ({score_delta})

{kpis_md}

**3 destaques do período:**
{destaques_md}

**3 alertas críticos:**
{alertas_md}

---
"""


def secao_indicadores(headline, rs, score_ant, extras):
    score = headline.get("score", 0) if headline else 0
    score_ant_val = score_ant.get("score") if score_ant else None

    totais = rs.get("totais", {}) if rs else {}
    por_status = rs.get("por_status", {}) if rs else {}
    cap = rs.get("capacidade", {}) if rs else {}
    tempo = rs.get("tempo", {}) if rs else {}
    op_kira = rs.get("operacional_kira", {}) if rs else {}
    proximos = rs.get("proximos", {}) if rs else {}

    em_retorno = por_status.get("reparo", 0) + por_status.get("marcas_rolo_cera", 0)
    cobertura_kira_pct = (
        op_kira.get("com_kira", 0) / op_kira.get("total_fluxo", 1) * 100
        if op_kira.get("total_fluxo", 0) > 0 else 0
    )

    iniciar_30d = proximos.get("firmadas_30d", proximos.get("c_data_30d", 0))

    summary = (extras or {}).get("analise", {})
    summary = summary.get("summary", {}) if isinstance(summary, dict) else {}
    atrasadas = summary.get("atrasados", "—")
    criticos = summary.get("critical", "—")
    high = summary.get("high", "—")

    dashboard = (extras or {}).get("dashboard", {})
    ocorr = dashboard.get("ocorrencias", {}).get("byStatus", []) if isinstance(dashboard, dict) else []
    ocorr_abertas = sum(o.get("count", 0) for o in ocorr if o.get("status") == "aberta")

    return f"""## 2 · Indicadores do Período

| Indicador | Atual | Anterior | Δ | Fonte |
|---|---|---|---|---|
| Total ativas em fluxo | {totais.get('ativas', '—')} | — | — | rodrigo-stats |
| Em execução agora | {totais.get('em_execucao', '—')} | — | — | rodrigo-stats |
| Atrasadas (Painel) | {atrasadas} | — | — | analise |
| → Críticas | {criticos} | — | — | analise |
| → Alto risco | {high} | — | — | analise |
| Obras em retorno (reparo + marcas) | {em_retorno} | — | — | rodrigo-stats |
| Cluster paralisado (Q2) | {totais.get('pausados', '—')} | — | — | rodrigo-stats |
| Score Saúde Operacional | {score}/100 | {score_ant_val or '—'} | {fmt_delta(score, score_ant_val)} | headline |
| TEMPO médio de ciclo | {tempo.get('ciclo_total_mediana', '—')}d | — | — | rodrigo-stats |
| VOLUME m² em curso | {fmt_num(totais.get('m2_em_execucao', 0))} | — | — | rodrigo-stats |
| Capacidade utilizada | {cap.get('utilization_percent', '—')}% | — | — | rodrigo-stats |
| A INICIAR firmadas (30d) | {iniciar_30d} | — | — | rodrigo-stats |
| Cobertura KIRA | {fmt_pct(cobertura_kira_pct)} | — | — | rodrigo-stats |
| Ocorrências abertas | {fmt_num(ocorr_abertas)} | — | — | dashboard |

> Deltas vs quinzena anterior em construção · score-historico ainda acumulando (iniciado 2026-05-01).

---
"""


def secao_diagnostico(rs, extras):
    op_kira = rs.get("operacional_kira", {}) if rs else {}
    summary = (extras or {}).get("analise", {})
    if isinstance(summary, dict):
        summary_sum = summary.get("summary", {})
        cats = summary.get("problemCategories", [])
    else:
        summary_sum = {}
        cats = []

    top3_cats = sorted(
        [c for c in cats if c.get("categoria") != "Outros"],
        key=lambda c: c.get("count", 0),
        reverse=True,
    )[:3]

    cats_md = "\n".join(
        f"- **{c.get('categoria')}** — {c.get('count')} obras ({c.get('criticos', 0)} críticas)"
        for c in top3_cats
    ) or "_sem dados de categorização disponíveis_"

    # Pulso KIRA
    cob = (
        op_kira.get("com_kira", 0) / op_kira["total_fluxo"] * 100
        if op_kira.get("total_fluxo", 0) > 0 else 0
    )

    return f"""## 3 · Diagnóstico Operacional

### Saúde geral da carteira
- **{summary_sum.get('totalActive', '—')}** obras ativas analisadas
- **{summary_sum.get('ok', '—')}** sem problemas relevantes
- **{summary_sum.get('critical', '—')}** críticas + **{summary_sum.get('high', '—')}** em alto risco
- **{summary_sum.get('atrasados', '—')}** com atraso identificado pelo Painel

### Top 3 categorias de problema (excluindo "Outros")
{cats_md}

> Categorização vem do `/api/analise` do Painel — agrupamento automático que substitui o trabalho manual de catalogar causa-raiz.

### Pulso KIRA · comunicação com cliente
- **Cobertura:** {op_kira.get('com_kira', '—')} de {op_kira.get('total_fluxo', '—')} obras ativas têm grupo de WhatsApp acompanhado ({fmt_pct(cob)})
- **Saudável:** {op_kira.get('saudavel', '—')} ({op_kira.get('saudavel_pct_no_monitorado', '—')}% das monitoradas)
- **Em atenção:** {op_kira.get('atencao', '—')}
- **Sem KIRA:** {op_kira.get('sem_kira', '—')} *(cegueira — obras que pra Qualidade são silêncio)*

> [REVISAR] Comentário narrativo de 1-2 frases sobre o que esses números contam juntos.

---
"""


def secao_atrasos(extras):
    """4 · Análise de Atrasos · usa atRisk com diagnóstico textual já pronto."""
    analise = (extras or {}).get("analise", {})
    if not isinstance(analise, dict):
        return "## 4 · Análise de Atrasos · caso a caso\n\n> Dados do `/api/analise` indisponíveis.\n\n---\n"
    atrisk = analise.get("atRisk", []) or []

    # Prioriza obras com DIAGNÓSTICO textual (mais informativas), depois mais atrasadas
    com_diag = [o for o in atrisk if (o.get("diagnostico") or "").strip()]
    sem_diag = [o for o in atrisk if not (o.get("diagnostico") or "").strip() and o.get("diasAtraso", 0) > 0]
    com_diag.sort(key=lambda o: o.get("diasAtraso", 0), reverse=True)
    sem_diag.sort(key=lambda o: o.get("diasAtraso", 0), reverse=True)
    top5 = (com_diag[:5] + sem_diag)[:5]
    if not top5:
        return "## 4 · Análise de Atrasos · caso a caso\n\n_Nenhuma obra atrasada no período._\n\n---\n"

    blocos = []
    for o in top5:
        cliente = o.get("clienteNome", "?")
        cidade = o.get("cidade", "—")
        fase = o.get("fase", "—")
        dias = o.get("diasAtraso", 0)
        diag = (o.get("diagnostico") or "").strip()

        # Quebra primeira linha do diagnóstico (geralmente data + previsão)
        diag_curto = "\n".join(diag.split("\n")[:6]) if diag else "_sem diagnóstico textual disponível_"

        blocos.append(f"""### {cliente} · {cidade} · {dias} dias de atraso
**Fase atual:** {fase}

{diag_curto}
""")

    return f"""## 4 · Análise de Atrasos · caso a caso

> Top 5 obras mais atrasadas no momento. Diagnóstico textual extraído direto do Painel (`/api/analise`).

{chr(10).join(blocos)}
> [REVISAR] Padrões observados nos casos acima (1-2 frases) · *qual o tema dominante?*

---
"""


def secao_retrabalho(rs, extras):
    por_status = rs.get("por_status", {}) if rs else {}
    reparo = por_status.get("reparo", 0)
    marcas = por_status.get("marcas_rolo_cera", 0)
    total_retorno = reparo + marcas
    ativas = rs.get("totais", {}).get("ativas", 1) if rs else 1
    pct_carteira = (total_retorno / ativas * 100) if ativas else 0

    # Categorias relacionadas a retrabalho
    analise = (extras or {}).get("analise", {})
    cats = analise.get("problemCategories", []) if isinstance(analise, dict) else []
    rt_categorias = [c for c in cats if c.get("categoria") in
                     ("Manchas/Defeitos", "Infiltração", "Substrato", "Material")]

    rt_md = "\n".join(
        f"- **{c.get('categoria')}**: {c.get('count')} obras (sendo {c.get('criticos', 0)} críticas)"
        for c in rt_categorias
    ) or "_sem dados_"

    return f"""## 5 · Retrabalho & Pós-entrega

> Obras em **reparo** e **marcas_rolo_cera** são pós-entrega — cronograma original já cumprido. Mostradas separadamente do atraso.

| Indicador | Atual | Anterior | Δ |
|---|---|---|---|
| Obras em retorno (total) | {total_retorno} | — | — |
| → em reparo | {reparo} | — | — |
| → em marcas / rolo / cera | {marcas} | — | — |
| % da carteira ativa | {fmt_pct(pct_carteira)} | — | — |

### Categorias de problema relacionadas a retrabalho

{rt_md}

> Fonte: `/api/analise`. Cada categoria conta obras com problema reportado no Painel — ajuda a identificar **padrões de causa-raiz** sem coleta manual.

> [REVISAR] Hipótese sobre a categoria dominante · qual ação pra reduzir?

---
"""


def normalizar_cidade(cid):
    """Reduz variações tipo 'SÃO PAULO / SP' / 'São Paulo/São Paulo' a forma única."""
    if not cid:
        return "Não informada"
    c = cid.strip()
    # Detecta CEP
    if c.upper().startswith("CEP") or "CEP:" in c.upper():
        return "Apenas CEP"
    # Pega só primeiro nome de cidade antes de "/" ou ";"
    for sep in ("/", ";", "-"):
        if sep in c:
            c = c.split(sep)[0].strip()
            break
    # Title case
    c = c.title()
    # Acerta acentos comuns
    c = c.replace("Sao Paulo", "São Paulo")
    return c


def secao_geografia(extras):
    """6 · Geografia — agrega por cidade do atRisk com normalização."""
    analise = (extras or {}).get("analise", {})
    atrisk = analise.get("atRisk", []) if isinstance(analise, dict) else []
    if not atrisk:
        return "## 6 · Geografia\n\n> Dados de geografia indisponíveis.\n\n---\n"

    por_cidade = {}
    for o in atrisk:
        cid = normalizar_cidade(o.get("cidade", ""))
        por_cidade[cid] = por_cidade.get(cid, 0) + 1

    top_cidades = sorted(por_cidade.items(), key=lambda x: x[1], reverse=True)[:8]
    cid_md = "| Cidade | Obras em risco |\n|---|---|\n"
    for cidade, n in top_cidades:
        cid_md += f"| {cidade} | {n} |\n"

    return f"""## 6 · Geografia

> Distribuição das **obras em risco** (atrasadas / com problema) por cidade. Total na amostra: **{len(atrisk)}** obras.

{cid_md}

> [REVISAR] Padrão regional observado — alguma cidade puxa atraso desproporcional?

---
"""


def secao_capacidade(rs, extras):
    cap = rs.get("capacidade", {}) if rs else {}
    totais = rs.get("totais", {}) if rs else {}
    proximos = rs.get("proximos", {}) if rs else {}

    cap_mensal = cap.get("capacidade_mensal_produtiva", 0)
    m2_curso = totais.get("m2_em_execucao", 0)
    cap_pct = cap.get("utilization_percent", 0)
    iniciar_30d = proximos.get("firmadas_30d", proximos.get("c_data_30d", 0))

    # Forecast próxima semana
    forecast = (extras or {}).get("forecast", []) or []
    prox_semana = forecast[0] if isinstance(forecast, list) and forecast else {}
    starting = prox_semana.get("starting", {}) if isinstance(prox_semana, dict) else {}
    in_exec = prox_semana.get("inExecution", {}) if isinstance(prox_semana, dict) else {}
    cap_sem = prox_semana.get("capacity", {}) if isinstance(prox_semana, dict) else {}

    if cap_pct < 50:
        diag = (
            f"Operação a {cap_pct}% da capacidade mensal · sobra produtiva considerável. "
            f"**→ Comercial pode acelerar fechamentos** · cabe sinalizar pro time de vendas."
        )
    elif cap_pct < 80:
        diag = (
            f"Operação a {cap_pct}% · espaço residual pra absorver demanda. "
            f"**→ Monitorar próximas 4 semanas** · se a INICIAR firmadas crescer, ajustar."
        )
    elif cap_pct < 100:
        diag = (
            f"Operação a {cap_pct}% · próximo do limite. "
            f"**→ Avaliar contratações ou rever prazo de aceitação** das próximas obras."
        )
    else:
        diag = (
            f"Operação a {cap_pct}% · acima do limite saudável. "
            f"**→ Risco de atraso sistêmico nas próximas obras** · revisar agenda + capacidade."
        )

    forecast_md = ""
    if prox_semana:
        forecast_md = f"""
### Projeção pra próxima semana ({prox_semana.get('startDate', '?')} a {prox_semana.get('endDate', '?')})

| Indicador | Próxima semana |
|---|---|
| Obras iniciando | {starting.get('count', 0)} ({fmt_num(starting.get('totalM2', 0))} m²) |
| Em execução | {in_exec.get('count', 0)} ({fmt_num(in_exec.get('totalM2', 0))} m²) |
| Capacidade prevista | {cap_sem.get('utilizationPercent', '—')}% |

> Fonte: `/api/analytics/weekly-forecast` · projeção baseada em data_de_entrada firmada.
"""

    return f"""## 7 · Capacidade × Demanda

> Pergunta direta: *aceitamos mais obras ou estamos no limite?*

| Indicador | Atual | Anterior | Δ |
|---|---|---|---|
| Capacidade mensal produtiva | {fmt_num(cap_mensal)} m²/mês | — | — |
| VOLUME m² em curso | {fmt_num(m2_curso)} m² | — | — |
| Capacidade utilizada | {cap_pct}% | — | — |
| A INICIAR firmadas (30d) | {iniciar_30d} obras | — | — |

**Diagnóstico atual:** {diag}
{forecast_md}
---
"""


def secao_equipe(rs, extras):
    """8 · Equipe — Luana × Wesley + supervisores via teamPerformance."""
    analise = (extras or {}).get("analise", {})
    team = analise.get("teamPerformance", []) if isinstance(analise, dict) else []

    # Pega só os Consultores
    consultores = [t for t in team if t.get("role") == "Consultor"]
    consultores.sort(key=lambda t: t.get("projetosAtivos", 0), reverse=True)

    consultor_md = "| Consultor | Ativos | Com problema | Atrasados | % com problema |\n|---|---|---|---|---|\n"
    for t in consultores:
        ativos = t.get("projetosAtivos", 0)
        problema = t.get("projetosComProblema", 0)
        atrasados = t.get("projetosAtrasados", 0)
        pct = (problema / ativos * 100) if ativos else 0
        nome = t.get("nome", "?").title()
        consultor_md += f"| {nome} | {ativos} | {problema} | {atrasados} | {fmt_pct(pct)} |\n"

    # Equipes do rodrigo-stats
    equipes = rs.get("equipes", []) if rs else []
    eq_md = "| Supervisor / Equipe | Obras ativas |\n|---|---|\n"
    for eq in equipes[:8]:
        nome = eq.get("nome", "—")
        obras = eq.get("obras_ativas", eq.get("obras", "—"))
        eq_md += f"| {nome} | {obras} |\n"

    return f"""## 8 · Análise por Equipe

### Consultores · responsáveis pela conta

{consultor_md}
> Fonte: `/api/analise.teamPerformance`. **% com problema** = projetos com qualquer problema reportado / projetos ativos.

### Supervisão de equipe (linha de frente)

{eq_md}

> [REVISAR] Comentário curto sobre destaques (positivos e alertas).

---
"""


def secao_orion(disc):
    if not disc:
        return "## 9 · Sinais Painel × Telegram (Lab Orion)\n\n> Lab Orion offline ou sem dados.\n\n---\n"
    total = disc.get("total_obras", 0)
    obras = disc.get("obras", [])
    com_flags = [o for o in obras if o.get("flags") or o.get("veredicto") != "coerente"]
    top5 = com_flags[:5]

    if top5:
        linhas = "| Obra | Painel diz | Tom Telegram | Veredicto |\n|---|---|---|---|\n"
        for o in top5:
            cliente = o.get("cliente", "—")
            painel = (o.get("painel", {}) or {}).get("status_atual", "—")
            tg = (o.get("telegram", {}) or {}).get("tom_grupo", "—")
            verdict = o.get("veredicto", "—")
            linhas += f"| {cliente} | {painel} | tom: {tg} | {verdict} |\n"
    else:
        linhas = "_Nenhuma divergência crítica detectada no período._\n"

    resumo = (disc.get("resumo_executivo") or "")[:500]

    return f"""## 9 · Sinais Painel × Telegram (Lab Orion)

**Total de obras analisadas pelo Orion:** {total} (piloto)

**Resumo do Orion:** {resumo}{'...' if len(disc.get('resumo_executivo', '')) > 500 else ''}

### Top 5 obras com flags ou divergências

{linhas}

> [REVISAR] Padrão observado · se houver divergência sistemática, declarar hipótese + ação.

---
"""


def secao_conclusoes(rs, extras):
    """10 · Conclusões automáticas baseadas em padrões."""
    analise = (extras or {}).get("analise", {})
    summary = analise.get("summary", {}) if isinstance(analise, dict) else {}
    cats = analise.get("problemCategories", []) if isinstance(analise, dict) else []
    cap = (rs or {}).get("capacidade", {})

    conclusoes = []

    # Conclusão 1: top categoria de problema (ignorando "Outros")
    cats_filtradas = [c for c in cats if c.get("categoria") != "Outros"]
    if cats_filtradas:
        top_cat = max(cats_filtradas, key=lambda c: c.get("count", 0))
        conclusoes.append({
            "obs": f"**{top_cat.get('categoria')}** é a categoria de problema com maior volume — {top_cat.get('count')} obras ({top_cat.get('criticos', 0)} críticas)",
            "causa": f"padrão recorrente em {top_cat.get('categoria').lower()} pode indicar gargalo sistêmico",
            "acao": f"investigar fluxo específico de **{top_cat.get('categoria')}** com a equipe operacional · validar se há ação preventiva possível"
        })

    # Conclusão 2: capacidade
    pct = cap.get("utilization_percent", 0)
    if pct < 50:
        conclusoes.append({
            "obs": f"Capacidade utilizada em apenas {pct}%",
            "causa": "demanda atual abaixo da capacidade instalada",
            "acao": "alinhar com Comercial pra acelerar fechamentos · ou reavaliar dimensionamento"
        })
    elif pct >= 80:
        conclusoes.append({
            "obs": f"Capacidade utilizada em {pct}% · próximo ou acima do limite saudável",
            "causa": "demanda alta + capacidade instalada limitada",
            "acao": "revisar prazo de aceitação das próximas obras · avaliar contratações"
        })

    # Conclusão 3: cobertura KIRA
    op_kira = (rs or {}).get("operacional_kira", {})
    sem_kira = op_kira.get("sem_kira", 0)
    if sem_kira > 50:
        conclusoes.append({
            "obs": f"**{sem_kira} obras sem KIRA** (sem grupo de WhatsApp acompanhado)",
            "causa": "cegueira da Qualidade · obras invisíveis pra detecção de problemas via grupo",
            "acao": "padronizar criação de grupo desde o início da obra · meta: zerar cegueira"
        })

    # Conclusão 4: atrasados
    atrasados = summary.get("atrasados", 0)
    criticos = summary.get("critical", 0)
    if criticos > 10:
        conclusoes.append({
            "obs": f"{criticos} obras em estado crítico ({atrasados} no total atrasadas)",
            "causa": "concentração de problemas que demanda atenção imediata",
            "acao": "priorizar contato direto com as **top 5 mais antigas** (ver Seção 4) · validar se demandam intervenção da Coordenação"
        })

    while len(conclusoes) < 3:
        conclusoes.append({"obs": "[REVISAR]", "causa": "[REVISAR]", "acao": "[REVISAR]"})

    md = ""
    for i, c in enumerate(conclusoes[:5], 1):
        # obs já pode conter ** internos (negrito), então não embrulhar de novo
        md += f"\n{i}. {c['obs']}\n   *Causa provável:* {c['causa']}\n   *→ Ação sugerida:* {c['acao']}\n"

    return f"""## 10 · Conclusões e Recomendações
{md}

**Para a próxima quinzena:**
- [REVISAR · 3 prioridades baseadas nos pontos acima]

---
"""


def secao_anexo(rs):
    """11 · Anexo — listagem nominal por status."""
    if not rs:
        return "## Anexo A · Obras do período\n\n_Dados indisponíveis._\n\n---\n"
    por_status = rs.get("por_status", {})
    return f"""## Anexo A · Obras do período

> Distribuição da carteira por status no fechamento da quinzena.

| Status | Quantidade |
|---|---|
| Em execução | {por_status.get('em_execucao', 0)} |
| Aguardando execução | {por_status.get('aguardando_execucao', 0)} |
| Planejamento | {por_status.get('planejamento', 0)} |
| Pausado | {por_status.get('pausado', 0)} |
| Aguardando clima | {por_status.get('aguardando_clima', 0)} |
| Em reparo | {por_status.get('reparo', 0)} |
| Em marcas / rolo / cera | {por_status.get('marcas_rolo_cera', 0)} |
| Concluído | {por_status.get('concluido', 0)} |
| Finalizado | {por_status.get('finalizado', 0)} |
| Cancelado | {por_status.get('cancelado', 0)} |

> [REVISAR · Fase 1.1c] Listagem nominal de cada bucket (nomes dos clientes) — virá numa próxima iteração consultando o details/.

---
"""


def secao_fontes(headline, rs, disc, extras):
    head = headline.get("atualizado_em", "—") if headline else "—"
    rsa = rs.get("atualizado_em", "—") if rs else "—"
    orion = disc.get("gerado_em", "—") if disc else "—"
    extras_a = extras.get("atualizado_em", "—") if extras else "—"

    return f"""## Fontes e Disclaimer

**Fontes consultadas:**
- **Painel de Obras** (`cliente.monofloor.cloud`) · refresh automático 30min · snapshot `{head}`
- **`/api/analise`** · diagnósticos textuais + categorização de problemas + teamPerformance · snapshot `{extras_a}`
- **`/api/analytics/alerts`** · alertas estruturados (stage_delay + sem_equipe)
- **`/api/analytics/weekly-forecast`** · projeção de 13 semanas (starting + inExecution + capacity)
- **`/api/dashboard`** · ocorrências abertas + SLA + readiness
- **Lab Orion** (`orion-pub.workers.dev`) · varredura 12h e 18h · snapshot `{orion}`
- **KIRA WhatsApp** · agregado em `rodrigo-stats.json` · snapshot `{rsa}`
- **Score Histórico** · `score-historico.json` (acumula 1 entry/dia desde 2026-05-01)

**Disclaimer:**
Análise concluída com base nos registros sistêmicos disponíveis ao Setor de Qualidade. Foco exclusivo nos dados, sem inferências sobre o cumprimento dos processos padrões estabelecidos pela operação. Casos de retrabalho e pós-entrega estão sujeitos a influências externas e são gerenciados dentro da margem de tolerância do processo. Heurísticas declaradas em cada seção quando aplicáveis.

---

*Relatório gerado pelo Sistema de Qualidade Monofloor · v0.2*
"""


# ═══ Main ═══

def main():
    args = parse_args()
    inicio, fim, inicio_ant, fim_ant = calcular_periodos(args)

    print(f"Gerando relatorio - periodo: {inicio} a {fim}")
    print(f"Comparativo: {inicio_ant} a {fim_ant}")

    headline = load_json(DADOS / "headline.json")
    rs = load_json(DADOS / "rodrigo-stats.json")
    score_hist = load_json(DADOS / "score-historico.json") or []
    extras = load_json(DADOS / "relatorio-extras.json")
    disc = load_json(ORION_DADOS / "discordancias-v3.json")

    if not headline or not rs:
        print("ERRO: headline.json ou rodrigo-stats.json nao encontrados", file=sys.stderr)
        sys.exit(1)
    if not extras:
        print("AVISO: relatorio-extras.json nao encontrado - rode 'python coletar-relatorio-extras.py' primeiro")

    score_ant = buscar_no_historico(score_hist, fim_ant, "score")

    partes = [
        secao_header(inicio, fim),
        secao_resumo_executivo(headline, rs, score_ant, extras),
        secao_indicadores(headline, rs, score_ant, extras),
        secao_diagnostico(rs, extras),
        secao_atrasos(extras),
        secao_retrabalho(rs, extras),
        secao_geografia(extras),
        secao_capacidade(rs, extras),
        secao_equipe(rs, extras),
        secao_orion(disc),
        secao_conclusoes(rs, extras),
        secao_anexo(rs),
        secao_fontes(headline, rs, disc, extras),
    ]
    relatorio = "\n".join(partes)

    SAIDA.mkdir(exist_ok=True)
    saida_path = (
        Path(args.saida)
        if args.saida
        else SAIDA / f"{nome_arquivo_auto(inicio, fim)}.md"
    )
    saida_path.write_text(relatorio, encoding="utf-8")
    print(f"[OK] Relatorio salvo em: {saida_path}")
    print(f"     Tamanho: {len(relatorio)} caracteres - {relatorio.count(chr(10))} linhas")


if __name__ == "__main__":
    main()
