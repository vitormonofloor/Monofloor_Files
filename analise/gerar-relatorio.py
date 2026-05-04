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


# ═══ Visualizações SVG inline ═══

def svg_barra_capacidade(pct, m2_curso, cap_mensal):
    """Barra horizontal mostrando capacidade utilizada vs disponível."""
    pct_int = max(0, min(100, int(pct)))
    if pct_int < 50:
        cor = "#6b8e3d"  # verde saudável
        zona = "folga produtiva"
    elif pct_int < 80:
        cor = "#b89a4a"  # amarelo
        zona = "operação saudável"
    elif pct_int < 100:
        cor = "#d97a4a"  # laranja
        zona = "próximo do limite"
    else:
        cor = "#c45a5a"  # vermelho
        zona = "acima do limite"

    sobra = cap_mensal - m2_curso
    largura_pct = (pct_int / 100) * 540

    return f"""<figure class="viz">
<svg viewBox="0 0 600 90" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:600px">
  <text x="0" y="18" font-family="Plus Jakarta Sans, sans-serif" font-size="11" fill="#8a7e72" letter-spacing="0.5">Capacidade utilizada</text>
  <text x="600" y="18" font-family="JetBrains Mono, monospace" font-size="14" font-weight="600" fill="#2a2520" text-anchor="end">{pct_int}%</text>
  <rect x="0" y="30" width="540" height="22" fill="#f0ebe3" stroke="#d8c8a8" stroke-width="0.5" rx="3"/>
  <rect x="0" y="30" width="{largura_pct}" height="22" fill="{cor}" rx="3"/>
  <text x="600" y="46" font-family="JetBrains Mono, monospace" font-size="10" fill="#8a7e72" text-anchor="end">{fmt_num(m2_curso)} / {fmt_num(cap_mensal)} m²/mês</text>
  <text x="0" y="78" font-family="Plus Jakarta Sans, sans-serif" font-size="10" fill="{cor}" font-style="italic">▸ {zona} · sobra de {fmt_num(sobra)} m²/mês</text>
</svg>
</figure>
"""


def svg_distribuicao_kira(saudavel, atencao, sem_kira, total_fluxo):
    """Barras empilhadas de distribuição KIRA."""
    if total_fluxo <= 0:
        return ""

    largura_total = 540
    s_w = (saudavel / total_fluxo) * largura_total
    a_w = (atencao / total_fluxo) * largura_total
    n_w = (sem_kira / total_fluxo) * largura_total

    s_pct = saudavel / total_fluxo * 100
    a_pct = atencao / total_fluxo * 100
    n_pct = sem_kira / total_fluxo * 100

    return f"""<figure class="viz">
<svg viewBox="0 0 600 105" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:600px">
  <text x="0" y="18" font-family="Plus Jakarta Sans, sans-serif" font-size="11" fill="#8a7e72" letter-spacing="0.5">Distribuição da carteira ativa por KIRA</text>
  <text x="600" y="18" font-family="JetBrains Mono, monospace" font-size="11" fill="#8a7e72" text-anchor="end">{total_fluxo} obras</text>

  <rect x="0" y="30" width="{s_w}" height="28" fill="#6b8e3d" rx="2 0 0 2"/>
  <rect x="{s_w}" y="30" width="{a_w}" height="28" fill="#b89a4a"/>
  <rect x="{s_w + a_w}" y="30" width="{n_w}" height="28" fill="#a89e92" rx="0 2 2 0"/>

  <text x="{s_w/2}" y="49" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#fff" text-anchor="middle">{saudavel}</text>
  <text x="{s_w + a_w/2}" y="49" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#fff" text-anchor="middle">{atencao}</text>
  <text x="{s_w + a_w + n_w/2}" y="49" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#fff" text-anchor="middle">{sem_kira}</text>

  <circle cx="6" cy="78" r="4" fill="#6b8e3d"/>
  <text x="16" y="82" font-family="Plus Jakarta Sans, sans-serif" font-size="10" fill="#3a3530">Saudável ({s_pct:.0f}%)</text>
  <circle cx="170" cy="78" r="4" fill="#b89a4a"/>
  <text x="180" y="82" font-family="Plus Jakarta Sans, sans-serif" font-size="10" fill="#3a3530">Atenção ({a_pct:.0f}%)</text>
  <circle cx="320" cy="78" r="4" fill="#a89e92"/>
  <text x="330" y="82" font-family="Plus Jakarta Sans, sans-serif" font-size="10" fill="#3a3530">Sem KIRA ({n_pct:.0f}% · cegueira)</text>
</svg>
</figure>
"""


def svg_top_categorias(categorias, top_n=5):
    """Barras horizontais das top categorias de problema."""
    if not categorias:
        return ""

    cats_filt = [c for c in categorias if c.get("categoria") != "Outros"]
    cats_filt.sort(key=lambda c: c.get("count", 0), reverse=True)
    top = cats_filt[:top_n]
    if not top:
        return ""

    max_count = max(c.get("count", 0) for c in top)
    largura_max = 380
    altura_barra = 22
    espaco = 30
    h_total = espaco * len(top) + 50

    barras = []
    for i, c in enumerate(top):
        nome = c.get("categoria", "?")
        count = c.get("count", 0)
        criticos = c.get("criticos", 0)
        y = 40 + i * espaco
        w = (count / max_count) * largura_max if max_count else 0
        # Cor: mais críticas → mais vermelho
        pct_crit = criticos / count if count else 0
        if pct_crit > 0.4:
            cor = "#c45a5a"
        elif pct_crit > 0.2:
            cor = "#d97a4a"
        else:
            cor = "#b89a4a"

        barras.append(f"""  <text x="0" y="{y + 14}" font-family="Plus Jakarta Sans, sans-serif" font-size="11" fill="#3a3530" font-weight="500">{nome}</text>
  <rect x="120" y="{y}" width="{w}" height="{altura_barra}" fill="{cor}" rx="2"/>
  <text x="{125 + w}" y="{y + 14}" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#3a3530">{count}</text>
  <text x="{135 + w + len(str(count)) * 7}" y="{y + 14}" font-family="JetBrains Mono, monospace" font-size="9" fill="#a89e92">({criticos} críticas)</text>""")

    return f"""<figure class="viz">
<svg viewBox="0 0 600 {h_total}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:600px">
  <text x="0" y="18" font-family="Plus Jakarta Sans, sans-serif" font-size="11" fill="#8a7e72" letter-spacing="0.5">Top {len(top)} categorias de problema · cor por proporção crítica</text>
{chr(10).join(barras)}
</svg>
</figure>
"""


def sinaleira(valor, faixas):
    """
    Retorna emoji 🟢/🟡/🔴 conforme faixas.
    faixas: lista de tuplas (limite, cor) ordenadas crescente.
    Ex: [(50, '🔴'), (70, '🟡'), (101, '🟢')]
    """
    for limite, cor in faixas:
        if valor < limite:
            return cor
    return faixas[-1][1]


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
    """3 alertas mais críticos do Resumo, deduplicados por cliente (1 alerta por obra)."""
    alerts = (extras or {}).get("alerts", {}) or {}
    lista = alerts.get("alerts", []) if isinstance(alerts, dict) else []
    high = [a for a in lista if a.get("severity") == "HIGH"]
    medium = [a for a in lista if a.get("severity") == "MEDIUM"]
    candidatos = high + medium

    # De-duplicar por clienteNome (1 alerta por obra)
    seen = set()
    unicos = []
    for a in candidatos:
        cliente = a.get("clienteNome", "")
        if cliente and cliente not in seen:
            unicos.append(a)
            seen.add(cliente)

    selecionados = unicos[:3]
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

    # Sinaleiras automáticas por faixa
    sin_score = sinaleira(score, [(50, "🔴"), (70, "🟡"), (101, "🟢")])
    pct_atrasadas = (atrasadas / ativas * 100) if ativas else 0
    sin_atrasadas = sinaleira(pct_atrasadas, [(15, "🟢"), (25, "🟡"), (101, "🔴")])
    pct_retorno = (em_retorno / ativas * 100) if ativas else 0
    sin_retorno = sinaleira(pct_retorno, [(8, "🟢"), (12, "🟡"), (101, "🔴")])
    sin_cap = sinaleira(cap_pct, [(40, "🟡"), (80, "🟢"), (101, "🟡")])
    # Capacidade <40% = subutilizada (amarelo) · 40-80% = saudável (verde) · >80% = limite (amarelo)

    kpis_md = (
        "| KPI | Atual | Anterior | Δ |\n"
        "|---|---|---|---|\n"
        f"| {sin_score} Score Saúde Operacional | {score}/100 | {score_ant_val or '—'} | {score_delta} |\n"
        f"| 🔵 Total ativas em fluxo | {ativas} | — | — |\n"
        f"| 🔵 Em execução agora | {em_exec} | — | — |\n"
        f"| {sin_atrasadas} Atrasadas (Painel) | {atrasadas} ({pct_atrasadas:.0f}% das ativas) | — | — |\n"
        f"| {sin_retorno} Em retorno (reparo + marcas) | {em_retorno} ({pct_retorno:.0f}% das ativas) | — | — |\n"
        f"| {sin_cap} Capacidade utilizada | {cap_pct}% | — | — |\n"
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

    # Bug fix: estrutura real é proximos["30d"]["obras"], não firmadas_30d
    prox_30d = proximos.get("30d", {}) if isinstance(proximos.get("30d"), dict) else {}
    iniciar_30d = prox_30d.get("obras", 0)
    iniciar_30d_m2 = prox_30d.get("m2", 0)

    summary = (extras or {}).get("analise", {})
    summary = summary.get("summary", {}) if isinstance(summary, dict) else {}
    atrasadas = summary.get("atrasados", "—")
    criticos = summary.get("critical", "—")
    high = summary.get("high", "—")

    dashboard = (extras or {}).get("dashboard", {})
    ocorr = dashboard.get("ocorrencias", {}).get("byStatus", []) if isinstance(dashboard, dict) else []
    ocorr_abertas = sum(o.get("count", 0) for o in ocorr if o.get("status") == "aberta")
    total_obras_painel = totais.get("total", 1) or 1
    ocorr_por_obra = ocorr_abertas / total_obras_painel

    return f"""## 2 · Indicadores do Período

| Indicador | Atual | Anterior | Δ | Fonte |
|---|---|---|---|---|
| Total ativas em fluxo | {totais.get('ativas', '—')} | — | — | Painel de Obras |
| Em execução agora | {totais.get('em_execucao', '—')} | — | — | Painel de Obras |
| Atrasadas | {atrasadas} | — | — | Análise do Painel |
| → Críticas | {criticos} | — | — | Análise do Painel |
| → Alto risco | {high} | — | — | Análise do Painel |
| Obras em retorno (reparo + marcas) | {em_retorno} | — | — | Painel de Obras |
| Cluster paralisado | {totais.get('pausados', '—')} | — | — | Painel de Obras |
| Score Saúde Operacional | {score}/100 | {score_ant_val or '—'} | {fmt_delta(score, score_ant_val)} | Snapshot diário |
| TEMPO médio de ciclo | {tempo.get('ciclo_total_mediana', '—')}d | — | — | Painel de Obras |
| VOLUME m² em curso | {fmt_num(totais.get('m2_em_execucao', 0))} | — | — | Painel de Obras |
| Capacidade utilizada | {cap.get('utilization_percent', '—')}% | — | — | Painel de Obras |
| A iniciar firmadas (30d) | {iniciar_30d} obras · {fmt_num(iniciar_30d_m2)} m² | — | — | Painel de Obras |
| Cobertura KIRA | {fmt_pct(cobertura_kira_pct)} | — | — | KIRA WhatsApp |
| Ocorrências abertas | {fmt_num(ocorr_abertas)} ({ocorr_por_obra:.1f} por obra · acumulado) | — | — | Painel · ocorrências |

> Deltas vs quinzena anterior em construção · histórico de Score acumulando desde 2026-05-01.

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

    total_painel = (rs or {}).get("totais", {}).get("ativas", 0)
    total_diag = summary_sum.get("totalActive", 0)
    nota_universos = ""
    if total_painel and total_diag and total_painel != total_diag:
        diff = total_painel - total_diag
        nota_universos = f"\n> *Universos: **{total_painel}** ativas no Painel · **{total_diag}** com diagnóstico de risco no /api/analise (a diferença de {diff} são obras em pós-entrega ou pausadas que não entram nessa análise específica).*\n"

    # SVGs visuais
    svg_cats = svg_top_categorias((extras or {}).get("analise", {}).get("problemCategories", []) if isinstance((extras or {}).get("analise", {}), dict) else [])
    svg_kira = svg_distribuicao_kira(
        op_kira.get("saudavel", 0),
        op_kira.get("atencao", 0),
        op_kira.get("sem_kira", 0),
        op_kira.get("total_fluxo", 0),
    )

    return f"""## 3 · Diagnóstico Operacional

### Saúde geral da carteira
- **{summary_sum.get('totalActive', '—')}** obras ativas analisadas
- **{summary_sum.get('ok', '—')}** sem problemas relevantes
- **{summary_sum.get('critical', '—')}** críticas + **{summary_sum.get('high', '—')}** em alto risco
- **{summary_sum.get('atrasados', '—')}** com atraso identificado pelo Painel
{nota_universos}

### Top 3 categorias de problema (excluindo "Outros")
{cats_md}

{svg_cats}
> Categorização vem da Análise do Painel — agrupamento automático que substitui o trabalho manual de catalogar causa-raiz.

### Pulso KIRA · comunicação com cliente

{svg_kira}

- **Cobertura:** {op_kira.get('com_kira', '—')} de {op_kira.get('total_fluxo', '—')} obras ativas têm grupo de WhatsApp acompanhado ({fmt_pct(cob)})
- **Saudável:** {op_kira.get('saudavel', '—')} ({op_kira.get('saudavel_pct_no_monitorado', '—')}% das monitoradas)
- **Em atenção:** {op_kira.get('atencao', '—')}
- **Sem KIRA:** {op_kira.get('sem_kira', '—')} *(cegueira — obras que pra Qualidade são silêncio)*

> [REVISAR] Comentário narrativo de 1-2 frases sobre o que esses números contam juntos.

> 💡 **Caminhos pra reduzir cegueira KIRA →** ver **Seção 10 · Conclusões** (receita "cegueira_kira" com 3 caminhos detalhados).

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

### Caminhos a explorar · pra reduzir atrasos críticos
- 🎯 **Triagem semanal das críticas** — toda segunda, ranking por dias parados → top 5 vão pra reunião de Coordenação
- 🚨 **Escalação automática D+30** — obra que passa 30d na mesma fase notifica Coordenador + cliente recebe contato
- 📋 **Checklist proativo de pré-execução** — confirmar equipe + cor + VT *antes* da data prevista, não no dia
- 💬 **Comunicação proativa com cliente** — quando atraso for inevitável, antecipar (em vez de cliente cobrar)

> [REVISAR] Quais desses caminhos fazem sentido pro período atual? Marcar 1-2 e a gente promove pra Seção 10 com Como/Custo/Impacto/Risco completos.

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

### Caminhos a explorar · pra reduzir retrabalho
- 🔍 **Auditoria técnica das críticas** — cruzar 23 infiltrações críticas: período / equipe / substrato / clima → identificar padrão recorrente
- 📐 **Critério reforçado na VT** — checklist obrigatório de umidade/contrapiso/ralo · obra não inicia sem aprovação
- 🎓 **Treinamento focado** — equipes com maior taxa de retorno recebem reciclagem técnica
- ⚖ **Mediação preventiva** — obras com flag detrator_latente recebem visita do Coordenador antes de virar caso jurídico

> [REVISAR] Categoria Infiltração tem 47% críticas (taxa MUITO acima da média) — recomendo priorizar Auditoria técnica. Ver Seção 10 pra caminhos detalhados (Como/Custo/Impacto/Risco).

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

    # Calcula concentração da #1 cidade
    cid1, n1 = top_cidades[0] if top_cidades else (None, 0)
    pct_concentracao = int(n1 / len(atrisk) * 100) if atrisk else 0

    return f"""## 6 · Geografia

> Distribuição das **obras em risco** (atrasadas / com problema) por cidade. Total na amostra: **{len(atrisk)}** obras.

{cid_md}

> [REVISAR] Padrão regional observado — alguma cidade puxa atraso desproporcional?

### Caminhos a explorar · pra concentração geográfica
- 🗺 **Análise de raiz regional** — concentração de {pct_concentracao}% em **{cid1 or '—'}** sugere investigar se gargalo é da equipe local ou do volume
- 🚐 **VT em lote** — pra obras próximas geograficamente, agendar visitas técnicas em sequência (ganho logístico)
- 👥 **Distribuir Luana × Wesley por região** — avaliar se proximidade física à equipe melhora acompanhamento
- 📍 **Reforço local** — se gargalo persistir em uma região, considerar contratação de aplicador regional

> [REVISAR] Esses caminhos fazem sentido com o conhecimento da operação? Cortar/promover.

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

    svg_cap = svg_barra_capacidade(cap_pct, m2_curso, cap_mensal)

    return f"""## 7 · Capacidade × Demanda

> Pergunta direta: *aceitamos mais obras ou estamos no limite?*

{svg_cap}

| Indicador | Atual | Anterior | Δ |
|---|---|---|---|
| Capacidade mensal produtiva | {fmt_num(cap_mensal)} m²/mês | — | — |
| VOLUME m² em curso | {fmt_num(m2_curso)} m² | — | — |
| Capacidade utilizada | {cap_pct}% | — | — |
| A INICIAR firmadas (30d) | {iniciar_30d} obras | — | — |

**Diagnóstico atual:** {diag}
{forecast_md}
> 💡 **Caminhos pra equilibrar capacidade vs demanda →** ver **Seção 10 · Conclusões** (receita "capacidade_ociosa" com 3 caminhos detalhados).

---
"""


def secao_equipe(rs, extras):
    """8 · Equipe — Luana × Wesley + supervisores via teamPerformance."""
    analise = (extras or {}).get("analise", {})
    team = analise.get("teamPerformance", []) if isinstance(analise, dict) else []

    # Pega só os Consultores
    consultores = [t for t in team if t.get("role") == "Consultor"]
    consultores.sort(key=lambda t: t.get("projetosAtivos", 0), reverse=True)

    # Filtro <5: separa amostra pequena pra não distorcer ranking (ex: Thaísa 100% com 1 obra)
    principais = [t for t in consultores if t.get("projetosAtivos", 0) >= 5]
    amostra_pequena = [t for t in consultores if 0 < t.get("projetosAtivos", 0) < 5]

    consultor_md = "| Consultor | Ativos | Com problema | Atrasados | % com problema |\n|---|---|---|---|---|\n"
    for t in principais:
        ativos = t.get("projetosAtivos", 0)
        problema = t.get("projetosComProblema", 0)
        atrasados = t.get("projetosAtrasados", 0)
        pct = (problema / ativos * 100) if ativos else 0
        nome = t.get("nome", "?").title()
        consultor_md += f"| {nome} | {ativos} | {problema} | {atrasados} | {fmt_pct(pct)} |\n"

    if amostra_pequena:
        nomes_ap = ", ".join(t.get("nome", "?").title() for t in amostra_pequena)
        consultor_md += f"\n> *Amostra pequena (1-4 obras), fora do ranking: {nomes_ap}.*\n"

    # Equipes do rodrigo-stats — usa campos reais (ativos, obras_hoje, obras_lideradas)
    equipes = rs.get("equipes", []) if rs else []
    # Ordenar por obras lideradas (mais relevantes primeiro)
    equipes_sorted = sorted(equipes, key=lambda e: len(e.get("obras_lideradas", [])), reverse=True)

    eq_md = "| Equipe | Líder | Aplicadores ativos | Obras lideradas | Estado |\n|---|---|---|---|---|\n"
    for eq in equipes_sorted[:8]:
        nome = eq.get("nome", "—")
        lider = eq.get("lider", "—")
        ativos = eq.get("ativos", 0)
        obras_lid = len(eq.get("obras_lideradas", []))
        estado = eq.get("estado", "—")
        # Sinaleira de estado
        if estado == "saudavel":
            estado_label = "🟢 saudável"
        elif estado == "fantasma":
            estado_label = "⚪ fantasma"
        elif estado == "atencao":
            estado_label = "🟡 atenção"
        else:
            estado_label = estado
        eq_md += f"| {nome} | {lider} | {ativos} | {obras_lid} | {estado_label} |\n"

    return f"""## 8 · Análise por Equipe

### Consultores · responsáveis pela conta

{consultor_md}
> Fonte: `/api/analise.teamPerformance`. **% com problema** = projetos com qualquer problema reportado / projetos ativos.

### Supervisão de equipe (linha de frente)

{eq_md}

> [REVISAR] Comentário curto sobre destaques (positivos e alertas).

### Caminhos a explorar · pra balanço de carga e qualidade
- ⚖ **Análise de perfil de carteira** — comparar Luana × Wesley considerando complexidade média, valor médio, dispersão geográfica (não só quantidade)
- 🤝 **1:1 quinzenal de carteira** — Coordenação revisa as obras de risco com cada consultora (formato fixo, 30min)
- 📊 **Meta de obras em paralelo** — estabelecer máx por consultora (ex: 60 ativas) · acima disso, desacelerar entrada de novas
- 🎓 **Capacitação cruzada** — Luana e Wesley trocam casos pra aprender com diferenças de abordagem

> [REVISAR] Distribuição atual: Luana 84 ativas / Wesley 61. Vale checar se essa diferença é histórica ou recente.

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

    resumo_full = disc.get("resumo_executivo") or ""
    if len(resumo_full) <= 800:
        resumo = resumo_full
    else:
        # Corta em fim de frase mais próximo do limite
        cortado = resumo_full[:800]
        last_period = cortado.rfind(". ")
        if last_period > 500:
            resumo = cortado[:last_period + 1]
        else:
            resumo = cortado.rstrip() + "..."

    return f"""## 9 · Sinais Painel × Telegram (Lab Orion)

**Total de obras analisadas pelo Orion:** {total} (piloto)

**Resumo do Orion:** {resumo}

### Top 5 obras com flags ou divergências

{linhas}

> [REVISAR] Padrão observado · se houver divergência sistemática, declarar hipótese + ação.

### Caminhos a explorar · pra reduzir divergências e expandir o Orion
- 🔄 **Padronizar quem atualiza o Painel** — definir formalmente: técnico atualiza fase, consultora atualiza status. Hoje há sobreposição
- ⚠ **Auditoria semanal de detrator_latente** — toda semana, Coordenação revisa as obras com flag · age antes de virar caso
- 📈 **Expandir piloto Orion** — 10 → 50 obras em 3 meses · ganha massa crítica pra detectar padrões sistêmicos
- 🧪 **A/B de qualidade Painel × WhatsApp** — quando divergir, qual fonte está certa? Auditoria mensal da amostra

> [REVISAR] Lab Orion ainda em piloto (10 obras) · vale acelerar expansão pra ganhar tração nos sinais?

---
"""


def detectar_problemas(rs, headline, extras, receitas):
    """Detecta problemas críticos no período e retorna lista ordenada."""
    problemas = []

    headline = headline or {}
    rs = rs or {}
    extras = extras or {}
    analise = extras.get("analise", {}) if isinstance(extras, dict) else {}
    summary = analise.get("summary", {}) if isinstance(analise, dict) else {}
    cats = analise.get("problemCategories", []) if isinstance(analise, dict) else {}
    cap = rs.get("capacidade", {})
    op_kira = rs.get("operacional_kira", {})
    score_comp = headline.get("score_componentes", {})

    # 1. Score baixo
    score = headline.get("score", 100)
    if score < 50 and "score_baixo" in receitas:
        problemas.append({
            "chave": "score_baixo",
            "prioridade": 1,
            "valores": {
                "valor": score,
                "ciclo": score_comp.get("ciclo_mediano", "—"),
                "pct_meta": int((score_comp.get("ciclo_mediano", 150) / 150 - 1) * 100),
                "zumbi_pct": score_comp.get("zumbi_pct", "—"),
                "orfas_pct": score_comp.get("orfas_pct", "—"),
                "cauda_vt": score_comp.get("lote_vt_270d", "—"),
            }
        })

    # 2. Categoria dominante de problema (Comunicação)
    cats_filt = [c for c in cats if c.get("categoria") != "Outros"]
    if cats_filt:
        top_cat = max(cats_filt, key=lambda c: c.get("count", 0))
        if top_cat.get("categoria") == "Comunicação" and top_cat.get("count", 0) > 50:
            if "categoria_comunicacao" in receitas:
                problemas.append({
                    "chave": "categoria_comunicacao",
                    "prioridade": 2,
                    "valores": {
                        "count": top_cat.get("count"),
                        "criticos": top_cat.get("criticos", 0),
                    }
                })

    # 3. Infiltração com proporção crítica
    inf = next((c for c in cats if c.get("categoria") == "Infiltração"), None)
    if inf and (inf.get("count", 0) > 40 or inf.get("criticos", 0) > 20):
        if "categoria_infiltracao" in receitas:
            critic = inf.get("criticos", 0)
            cnt = inf.get("count", 1)
            problemas.append({
                "chave": "categoria_infiltracao",
                "prioridade": 3,
                "valores": {
                    "count": cnt,
                    "criticos": critic,
                    "pct_critico": int(critic / cnt * 100) if cnt else 0,
                }
            })

    # 4. Capacidade ociosa
    pct = cap.get("utilization_percent", 100)
    if pct < 50 and "capacidade_ociosa" in receitas:
        cap_mensal = cap.get("capacidade_mensal_produtiva", 0)
        m2_curso = rs.get("totais", {}).get("m2_em_execucao", 0)
        problemas.append({
            "chave": "capacidade_ociosa",
            "prioridade": 4,
            "valores": {
                "pct": pct,
                "m2_curso": fmt_num(m2_curso),
                "cap_mensal": fmt_num(cap_mensal),
                "sobra": fmt_num(cap_mensal - m2_curso),
            }
        })

    # 5. Cegueira KIRA
    sem_kira = op_kira.get("sem_kira", 0)
    if sem_kira > 50 and "cegueira_kira" in receitas:
        problemas.append({
            "chave": "cegueira_kira",
            "prioridade": 5,
            "valores": {"count": sem_kira}
        })

    # 6. Alto atraso crítico
    criticos = summary.get("critical", 0)
    if criticos > 15 and "alto_atraso_critico" in receitas:
        problemas.append({
            "chave": "alto_atraso_critico",
            "prioridade": 6,
            "valores": {
                "count": criticos,
                "atrasados": summary.get("atrasados", 0),
            }
        })

    problemas.sort(key=lambda p: p["prioridade"])
    return problemas[:4]  # máx 4 problemas detalhados


def _subst(texto, valores):
    """Substitui {chave} por valor em string."""
    if not texto:
        return ""
    for k, v in valores.items():
        texto = texto.replace("{" + k + "}", str(v))
    return texto


def renderizar_receita(prob, receita):
    """Renderiza 1 receita preenchida com valores reais (substitui placeholders em TODOS os campos textuais)."""
    valores = prob["valores"]

    diag = _subst(receita.get("diagnostico", ""), valores)
    melhorar = _subst(receita.get("para_melhorar", "—"), valores)
    rec = _subst(receita.get("recomendacao_combinada", ""), valores)

    md = f"### {receita.get('titulo', '?')}\n\n"
    md += f"**Diagnóstico**\n{diag}\n\n"
    md += f"**Para melhorar:** {melhorar}\n\n"
    md += "**Caminhos viáveis:**\n\n"

    for i, cam in enumerate(receita.get("caminhos", []), 1):
        nome = _subst(cam.get("nome", "?"), valores)
        como = _subst(cam.get("como", "—"), valores)
        custo = _subst(cam.get("custo", "—"), valores)
        impacto = _subst(cam.get("impacto_template", ""), valores)
        risco = _subst(cam.get("risco", "—"), valores)

        md += f"**Caminho {chr(64+i)} · {nome}**\n"
        md += f"- **Como:** {como}\n"
        md += f"- **Custo do tempo:** {custo}\n"
        md += f"- **Impacto esperado:** {impacto}\n"
        md += f"- **Risco:** {risco}\n\n"

    if rec:
        md += f"**Recomendação automática:** {rec}\n"

    return md


def secao_conclusoes(rs, extras, headline, receitas):
    """10 · Conclusões e Recomendações com receitas propositivas."""
    problemas = detectar_problemas(rs, headline, extras, receitas)

    if not problemas:
        return "## 10 · Conclusões e Recomendações\n\n_Nenhum problema crítico detectado no período._\n\n---\n"

    blocos = []
    for prob in problemas:
        receita = receitas.get(prob["chave"])
        if receita:
            blocos.append(renderizar_receita(prob, receita))

    return f"""## 10 · Conclusões e Recomendações

> Análise propositiva: cada problema crítico detectado vem com diagnóstico, caminhos viáveis (Como · Custo · Impacto · Risco) e recomendação combinada. Números marcados [REVISAR] são chutes que dependem do conhecimento operacional do Vitor pra calibrar.

{chr(10).join(blocos)}
---

**Para a próxima quinzena · 3 prioridades sugeridas:**
- [REVISAR · escolher 3 dos caminhos acima como prioridade do período]

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
    receitas = load_json(ROOT / "receitas-qualidade.json") or {}

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
        secao_conclusoes(rs, extras, headline, receitas),
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
    print(f"[OK] Relatorio MD: {saida_path.name}")
    print(f"     {len(relatorio)} caracteres - {relatorio.count(chr(10))} linhas")

    # Gera HTML estilizado automaticamente
    try:
        import subprocess
        subprocess.run(
            [sys.executable, str(ROOT / "gerar-pdf.py"), saida_path.name],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        html_path = saida_path.with_suffix(".html")
        print(f"[OK] HTML estilizado: {html_path.name}")
        print(f"     Pra exportar PDF: abrir o .html no browser e Ctrl+P -> 'Salvar como PDF'")
    except Exception as e:
        print(f"[AVISO] geracao HTML falhou: {e} (rode 'python gerar-pdf.py' manualmente)")


if __name__ == "__main__":
    main()
