"""
gerar-relatorio.py — Gerador do Relatório Quinzenal de Qualidade
================================================================

Lê dados do Dashboard (rodrigo-stats + headline + score-historico) e do
Lab Orion (discordancias-v3), calcula deltas vs quinzena anterior e gera
o relatório Markdown em analise/relatorios/YYYY-MM-quinzena-N.md.

Princípio do relatório (firmado 2026-05-04):
- Cada problema citado vem com hipótese de causa + ação sugerida
- Tom moderno e direto · zero "ressaltando, pautando, possibilitando"
- Conteúdo 100% derivado das fontes existentes (sem inventar indicadores)

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
    """
    Formata delta com seta direcional.
    invert=True quando MENOS é melhor (ex: cluster paralisado, retrabalho).
    """
    if anterior is None or atual is None:
        return "—"
    diff = atual - anterior
    if diff == 0:
        return "◆ 0"
    melhorou = (diff > 0 and not invert) or (diff < 0 and invert)
    seta = "▲" if diff > 0 else "▼"
    sinal = "+" if diff > 0 else ""
    cor_dica = "" if melhorou else "⚠"
    return f"{seta} {sinal}{fmt_num(diff, 0 if isinstance(diff, int) or diff == int(diff) else 1)}{suffix}{cor_dica}".replace(
        "+-", "-"
    )


def fmt_pct(v):
    """Formata percentual."""
    if v is None:
        return "—"
    return f"{v:.0f}%" if v == int(v) else f"{v:.1f}%"


def buscar_no_historico(historico, data_alvo, campo="score"):
    """Acha entry mais próxima da data_alvo. Fallback: entry mais antiga."""
    if not historico or not isinstance(historico, list):
        return None
    iso_alvo = data_alvo.isoformat() if hasattr(data_alvo, "isoformat") else data_alvo
    # Filtra entries válidas (valor > 0 evita os zeros do dia 1)
    validos = [e for e in historico if e.get(campo, 0) > 0 and e.get("date", "") <= iso_alvo]
    if validos:
        return validos[-1]
    # Fallback: primeira entry com valor válido
    todos_validos = [e for e in historico if e.get(campo, 0) > 0]
    return todos_validos[0] if todos_validos else None


# ═══ Argumentos ═══

def parse_args():
    p = argparse.ArgumentParser(description="Gera relatório quinzenal de Qualidade.")
    p.add_argument("--inicio", help="Data início YYYY-MM-DD (default: hoje-14d)")
    p.add_argument("--fim", help="Data fim YYYY-MM-DD (default: hoje)")
    p.add_argument("--saida", help="Caminho do arquivo de saída (default: auto-nomeado)")
    return p.parse_args()


def calcular_periodos(args):
    """Retorna (inicio, fim, inicio_anterior, fim_anterior)."""
    fim = date.fromisoformat(args.fim) if args.fim else date.today()
    inicio = date.fromisoformat(args.inicio) if args.inicio else fim - timedelta(days=14)
    duracao = (fim - inicio).days + 1
    fim_ant = inicio - timedelta(days=1)
    inicio_ant = fim_ant - timedelta(days=duracao - 1)
    return inicio, fim, inicio_ant, fim_ant


def nome_arquivo_auto(inicio, fim):
    """Gera nome padronizado: 2026-05-quinzena-1.md (1 = primeira do mês, 2 = segunda)."""
    quinzena = 1 if fim.day <= 15 else 2
    return f"{fim.year}-{fim.month:02d}-quinzena-{quinzena}"


# ═══ Seções do relatório ═══

def secao_header(inicio, fim):
    quinzena = 1 if fim.day <= 15 else 2
    meses = [
        "",
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]
    periodo = f"{inicio.strftime('%d/%m')} a {fim.strftime('%d/%m/%Y')}"
    return f"""# Relatório Quinzenal de Qualidade

**Período:** {periodo} · Quinzena {quinzena} de {meses[fim.month]}
**Setor de Qualidade Monofloor · Vitor Gomes, Coordenador**
**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

---
"""


def secao_resumo_executivo(headline, rs, score_ant):
    """1 · Resumo Executivo — manchete, score, KPIs principais, destaques, alertas."""
    score = headline.get("score", 0) if headline else 0
    score_ant_val = score_ant.get("score") if score_ant else None
    score_delta = fmt_delta(score, score_ant_val)

    totais = rs.get("totais", {}) if rs else {}
    ativas = totais.get("ativas", 0)
    em_exec = totais.get("em_execucao", 0)
    pausadas = totais.get("pausados", 0)

    por_status = rs.get("por_status", {}) if rs else {}
    em_retorno = por_status.get("reparo", 0) + por_status.get("marcas_rolo_cera", 0)

    cap = rs.get("capacidade", {}) if rs else {}
    cap_pct = cap.get("utilization_percent", 0)

    # Manchete rascunho automático (Vitor revisa)
    if score >= 70:
        zona = "verde"
    elif score >= 50:
        zona = "amarela"
    else:
        zona = "vermelha"

    manchete_auto = f"Operação fechou a quinzena com Score {score}/100 (zona {zona})"
    if score_delta != "—" and score_delta != "◆ 0":
        manchete_auto += f", {score_delta} vs quinzena anterior"
    manchete_auto += f". {ativas} obras ativas em fluxo, {em_exec} em execução agora."

    # Tabela KPIs principais (5 mais importantes pro topo)
    kpis_md = (
        "| KPI | Atual | Anterior | Δ |\n"
        "|---|---|---|---|\n"
        f"| Total ativas em fluxo | {ativas} | — | — |\n"
        f"| Em execução agora | {em_exec} | — | — |\n"
        f"| Obras em retorno (reparo + marcas) | {em_retorno} | — | — |\n"
        f"| Capacidade utilizada | {cap_pct}% | — | — |\n"
        f"| Score Saúde Operacional | {score}/100 | {score_ant_val or '—'} | {score_delta} |\n"
    )

    return f"""## 1 · Resumo Executivo

> [REVISAR · rascunho auto] {manchete_auto}

**Score Saúde Operacional:** {score}/100 ({score_delta})

{kpis_md}

**3 destaques** (auto-gerados — TODO Fase 1.1b):
1. [REVISAR]
2. [REVISAR]
3. [REVISAR]

**3 alertas** (auto-gerados — TODO Fase 1.1b):
1. [REVISAR] · **Causa provável:** [REVISAR] · **→ Ação sugerida:** [REVISAR]
2. [REVISAR] · **Causa provável:** [REVISAR] · **→ Ação sugerida:** [REVISAR]
3. [REVISAR] · **Causa provável:** [REVISAR] · **→ Ação sugerida:** [REVISAR]

---
"""


def secao_indicadores(headline, rs, score_ant):
    """2 · Indicadores do Período — tabela completa de KPIs."""
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
        (op_kira.get("com_kira", 0) / op_kira.get("total_fluxo", 1) * 100)
        if op_kira.get("total_fluxo", 0) > 0
        else 0
    )

    # A INICIAR firmadas (próximos 30d com data_de_entrada)
    iniciar_30d = proximos.get("firmadas_30d", proximos.get("c_data_30d", 0))

    return f"""## 2 · Indicadores do Período

| Indicador | Atual | Anterior | Δ | Fonte |
|---|---|---|---|---|
| Total ativas em fluxo | {totais.get('ativas', '—')} | — | — | rodrigo-stats |
| Em execução agora | {totais.get('em_execucao', '—')} | — | — | rodrigo-stats |
| Atraso mediano (Q1) | — | — | — | TODO Fase 1.1b |
| Obras em retorno (reparo + marcas) | {em_retorno} | — | — | rodrigo-stats |
| Cluster paralisado (Q2) | {totais.get('pausados', '—')} | — | — | rodrigo-stats |
| Score Saúde Operacional | {score}/100 | {score_ant_val or '—'} | {fmt_delta(score, score_ant_val)} | headline |
| TEMPO médio de ciclo | {tempo.get('ciclo_total_mediana', '—')}d | — | — | rodrigo-stats |
| VOLUME m² em curso | {fmt_num(totais.get('m2_em_execucao', 0))} | — | — | rodrigo-stats |
| Capacidade utilizada | {cap.get('utilization_percent', '—')}% | — | — | rodrigo-stats |
| A INICIAR firmadas (30d) | {iniciar_30d} | — | — | rodrigo-stats |
| Cobertura KIRA | {fmt_pct(cobertura_kira_pct)} | — | — | operacional_kira |

> Deltas vs quinzena anterior em construção · score-historico ainda acumulando (iniciado 2026-05-01).

---
"""


def secao_diagnostico(rs):
    """3 · Diagnóstico Operacional — TODO Fase 1.1b · placeholder honesto."""
    op_kira = rs.get("operacional_kira", {}) if rs else {}
    return f"""## 3 · Diagnóstico Operacional

> [REVISAR · TODO Fase 1.1b] Síntese das 9 seções do dashboard em parágrafos fluidos.

### Pulso KIRA · comunicação com cliente
**Cobertura KIRA:** {op_kira.get('com_kira', '—')} de {op_kira.get('total_fluxo', '—')} obras ativas têm grupo de WhatsApp acompanhado.

**Distribuição de climas:**
- Saudável: {op_kira.get('saudavel', '—')} ({op_kira.get('saudavel_pct_no_monitorado', '—')}% das monitoradas)
- Em atenção: {op_kira.get('atencao', '—')}
- Sem KIRA: {op_kira.get('sem_kira', '—')}

**Hipótese sobre o período:** [REVISAR]
**→ Ação sugerida:** [REVISAR]

---
"""


def secao_atrasos():
    """4 · Análise de Atrasos · caso a caso · TODO Fase 1.1b."""
    return """## 4 · Análise de Atrasos · caso a caso

> [REVISAR · TODO Fase 1.1b] Cada obra atrasada do período vai receber bloco com timeline KIRA + causa identificada. Requer cruzar `details/*.json` com filtro de período.

---
"""


def secao_retrabalho(rs, por_status_ant=None):
    """5 · Retrabalho & Pós-entrega."""
    por_status = rs.get("por_status", {}) if rs else {}
    reparo = por_status.get("reparo", 0)
    marcas = por_status.get("marcas_rolo_cera", 0)
    total_retorno = reparo + marcas

    ativas = rs.get("totais", {}).get("ativas", 1) if rs else 1
    pct_carteira = (total_retorno / ativas * 100) if ativas else 0

    return f"""## 5 · Retrabalho & Pós-entrega

> Obras em **reparo** e **marcas_rolo_cera** são pós-entrega — cronograma original já cumprido. Mostradas separadamente do atraso.

| Indicador | Atual | Anterior | Δ |
|---|---|---|---|
| Obras em retorno (total) | {total_retorno} | — | — |
| → em reparo | {reparo} | — | — |
| → em marcas / rolo / cera | {marcas} | — | — |
| % da carteira ativa | {fmt_pct(pct_carteira)} | — | — |

**Hipótese sobre o período:** [REVISAR · TODO Fase 1.1b — listar top 5 mais antigas]
**→ Ação sugerida:** [REVISAR]

---
"""


def secao_geografia(rs):
    """6 · Geografia — distribuição por estado."""
    # TODO: rodrigo-stats tem distribuição por estado em algum lugar?
    # Por enquanto placeholder honesto.
    return """## 6 · Geografia

> [REVISAR · TODO Fase 1.1b] Tabela por estado (SP/RJ/PR/Outros) com obras ativas, em execução, % no prazo, delta. Requer agregação por estado em rodrigo-stats.

---
"""


def secao_capacidade(rs):
    """7 · Capacidade × Demanda — pergunta executiva pra diretoria."""
    cap = rs.get("capacidade", {}) if rs else {}
    totais = rs.get("totais", {}) if rs else {}
    proximos = rs.get("proximos", {}) if rs else {}

    cap_mensal = cap.get("capacidade_mensal_produtiva", 0)
    m2_curso = totais.get("m2_em_execucao", 0)
    cap_pct = cap.get("utilization_percent", 0)
    iniciar_30d = proximos.get("firmadas_30d", proximos.get("c_data_30d", 0))

    # Diagnóstico automático
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

    return f"""## 7 · Capacidade × Demanda

> Pergunta direta: *aceitamos mais obras ou estamos no limite?*

| Indicador | Atual | Anterior | Δ |
|---|---|---|---|
| Capacidade mensal produtiva | {fmt_num(cap_mensal)} m²/mês | — | — |
| VOLUME m² em curso | {fmt_num(m2_curso)} m² | — | — |
| Capacidade utilizada | {cap_pct}% | — | — |
| A INICIAR firmadas (30d) | {iniciar_30d} obras | — | — |

**Diagnóstico:** {diag}

---
"""


def secao_equipe(rs):
    """8 · Análise por Equipe — Luana × Wesley + supervisores."""
    lw = rs.get("lw", {}) if rs else {}
    equipes = rs.get("equipes", []) if rs else []

    # Luana × Wesley
    luana = lw.get("luana", {})
    wesley = lw.get("wesley", {})

    # Equipes top
    equipes_md = "| Supervisor / Equipe | Obras ativas | m² em curso |\n|---|---|---|\n"
    for eq in equipes[:8]:
        nome = eq.get("nome", "—")
        obras = eq.get("obras_ativas", eq.get("obras", "—"))
        m2 = eq.get("m2_em_curso", eq.get("m2", "—"))
        equipes_md += f"| {nome} | {obras} | {fmt_num(m2) if isinstance(m2, (int, float)) else m2} |\n"

    return f"""## 8 · Análise por Equipe

### Consultoras (responsáveis pela conta)

| Consultora | Obras ativas | Em retrabalho |
|---|---|---|
| Luana | {luana.get('obras_ativas', '—')} | {luana.get('retrabalho', '—')} |
| Wesley | {wesley.get('obras_ativas', '—')} | {wesley.get('retrabalho', '—')} |

### Supervisão de equipe

{equipes_md}

> [REVISAR · TODO Fase 1.1b] Comentário curto por equipe destaque/alerta.

---
"""


def secao_orion(disc):
    """9 · Sinais Painel × Telegram (Lab Orion)."""
    if not disc:
        return """## 9 · Sinais Painel × Telegram (Lab Orion)

> Lab Orion offline ou sem dados.

---
"""
    total = disc.get("total_obras", 0)
    obras = disc.get("obras", [])

    # Top 5 com flags relevantes (detrator_latente, risco_tecnico, etc)
    com_flags = [o for o in obras if o.get("flags") or o.get("veredicto") != "coerente"]
    top5 = com_flags[:5]

    if top5:
        linhas = "| Obra | Painel diz | Telegram conta | Veredicto |\n|---|---|---|---|\n"
        for o in top5:
            cliente = o.get("cliente", "—")
            painel = o.get("painel", {}).get("status_atual", "—")
            tg_tom = o.get("telegram", {}).get("tom_grupo", "—")
            verdict = o.get("veredicto", "—")
            linhas += f"| {cliente} | {painel} | tom: {tg_tom} | {verdict} |\n"
    else:
        linhas = "_Nenhuma divergência crítica detectada no período._\n"

    resumo = disc.get("resumo_executivo", "")
    return f"""## 9 · Sinais Painel × Telegram (Lab Orion)

**Total de obras analisadas pelo Orion:** {total} (piloto)

**Resumo do Orion:** {resumo[:400]}{'...' if len(resumo) > 400 else ''}

### Top 5 obras com flags ou divergências

{linhas}

> [REVISAR] Padrão observado no período. Se houver divergência sistemática (ex: silêncio do técnico), declarar hipótese + ação.

---
"""


def secao_conclusoes():
    """10 · Conclusões e Recomendações · TODO Fase 1.1b."""
    return """## 10 · Conclusões e Recomendações

> [REVISAR · TODO Fase 1.1b] Pré-preenchida com 3-5 itens. Cada item: observação · hipótese · ação.

1. **[REVISAR]**
   *Causa provável:* [REVISAR]
   *→ Ação sugerida:* [REVISAR]

**Para a próxima quinzena:**
- [REVISAR]
- [REVISAR]
- [REVISAR]

---
"""


def secao_anexo():
    """11 · Anexo · TODO Fase 1.1b."""
    return """## Anexo A · Obras do período

> [REVISAR · TODO Fase 1.1b] Listagem nominal por estado de fluxo (RODANDO / ESTAGNADO / PENDENTE) + encerradas + em retorno.

---
"""


def secao_fontes(headline, rs, disc):
    """12 · Fontes e Disclaimer."""
    head_atualizado = headline.get("atualizado_em", "—") if headline else "—"
    rs_atualizado = rs.get("atualizado_em", "—") if rs else "—"
    orion_gerado = disc.get("gerado_em", "—") if disc else "—"

    return f"""## Fontes e Disclaimer

**Fontes consultadas:**
- **Painel de Obras** (`cliente.monofloor.cloud`) · refresh automático 30min · snapshot `{head_atualizado}`
- **Lab Orion** (`orion-pub.workers.dev`) · varredura 12h e 18h · snapshot `{orion_gerado}`
- **KIRA WhatsApp** · agregado em `rodrigo-stats.json` · snapshot `{rs_atualizado}`
- **Score Histórico** · `score-historico.json` (acumula 1 entry/dia desde 2026-05-01)

**Disclaimer:**
Análise concluída com base nos registros sistêmicos disponíveis ao Setor de Qualidade. Foco exclusivo nos dados, sem inferências sobre o cumprimento dos processos padrões estabelecidos pela operação. Casos de retrabalho e pós-entrega estão sujeitos a influências externas e são gerenciados dentro da margem de tolerância do processo. Heurísticas declaradas em cada seção quando aplicáveis.

---

*Relatório gerado pelo Sistema de Qualidade Monofloor · v0.1*
"""


# ═══ Main ═══

def main():
    args = parse_args()
    inicio, fim, inicio_ant, fim_ant = calcular_periodos(args)

    print(f"Gerando relatório · período: {inicio} a {fim}")
    print(f"Comparativo: {inicio_ant} a {fim_ant}")

    # Carrega fontes
    headline = load_json(DADOS / "headline.json")
    rs = load_json(DADOS / "rodrigo-stats.json")
    score_hist = load_json(DADOS / "score-historico.json") or []
    disc = load_json(ORION_DADOS / "discordancias-v3.json")

    if not headline or not rs:
        print("ERRO: headline.json ou rodrigo-stats.json não encontrados", file=sys.stderr)
        sys.exit(1)

    # Score anterior (15 dias atrás aprox)
    score_ant = buscar_no_historico(score_hist, fim_ant, "score")

    # Monta o relatório
    partes = [
        secao_header(inicio, fim),
        secao_resumo_executivo(headline, rs, score_ant),
        secao_indicadores(headline, rs, score_ant),
        secao_diagnostico(rs),
        secao_atrasos(),
        secao_retrabalho(rs),
        secao_geografia(rs),
        secao_capacidade(rs),
        secao_equipe(rs),
        secao_orion(disc),
        secao_conclusoes(),
        secao_anexo(),
        secao_fontes(headline, rs, disc),
    ]

    relatorio = "\n".join(partes)

    # Salva
    SAIDA.mkdir(exist_ok=True)
    saida_path = (
        Path(args.saida)
        if args.saida
        else SAIDA / f"{nome_arquivo_auto(inicio, fim)}.md"
    )
    saida_path.write_text(relatorio, encoding="utf-8")
    print(f"[OK] Relatório salvo em: {saida_path}")
    print(f"     Tamanho: {len(relatorio)} caracteres · {relatorio.count(chr(10))} linhas")


if __name__ == "__main__":
    main()
