# ESCOPO TIMELINE — Documento-ancora

> **LEITURA OBRIGATORIA** antes de qualquer trabalho no pipeline Timeline.
> Criado em 2026-05-14 por decisao explicita do Vitor.
> Qualquer agente IA que tocar neste projeto DEVE ler isso primeiro.

---

## Objetivo unico

Estudar as obras que **iniciaram em 2026** para:

1. **Mapear os marcos reais** de cada fase do fluxo operacional
2. **Identificar os gaps** — onde trava, onde pula etapa, onde demora mais que deveria
3. **Criar padroes** — "o caminho normal e A->B->C em Xd, mas em Y% das obras acontece Z"
4. **Propor melhorias concretas** no fluxo operacional baseadas nos padroes

O resultado final e uma **analise que mostre o fluxo real vs o esperado e onde intervir**.

---

## O que NAO fazer

- NAO criar dashboards novos, paginas novas, ou telas de monitoramento
- NAO criar sistema de alertas ou gatilhos automaticos
- NAO criar KPIs derivados ou indicadores executivos
- NAO criar bancada de leituras narrativas
- NAO expandir pra obras historicas (pre-2026) a menos que Vitor peca explicitamente
- NAO propor ramificacoes ("e se a gente tambem fizesse X?")
- NAO construir infra (cron, workers, CI) alem do que ja existe

Quando surgir uma ideia fora do escopo: **anotar em 1 linha no final deste arquivo na secao "Ideias estacionadas"** e voltar ao trabalho.

---

## Universo

**Obras que iniciaram em 2026** — criterio a definir (data de inicio de execucao confirmada >= 2026-01-01, ou primeiro marco de execucao em 2026).

O pipeline de extracao (`timeline_10obras.py --massa`) ja roda e gera `timeline_obras.json`. Usar esse JSON como materia-prima. Nao precisa reconstruir nada.

---

## Entregas esperadas (em ordem)

### E1 — Levantamento do universo
Quantas obras iniciaram em 2026. Cobertura de marcos. Distribuicao por status/fase.

### E2 — Mapeamento fase a fase
Pra cada obra: sequencia real de marcos, tempo entre marcos, fases puladas, fases invertidas.

### E3 — Padroes emergentes
Agrupar obras por comportamento similar. Identificar o "caminho feliz" (maioria) e os desvios.

### E4 — Gaps e gargalos
Onde o fluxo trava. Quais transicoes demoram mais. Quais etapas sao puladas com frequencia.

### E5 — Propostas de melhoria
Pra cada gap/gargalo: hipotese de causa + sugestao de intervencao operacional.

---

## O que ja existe e pode ser reaproveitado

- `timeline_obras.json` — 221 obras vivas com marcos extraidos (cron 5x/dia)
- `timeline_historico_2026-05-07.json` — 1042 obras historicas (frozen)
- `gerar_html_timelines.py` — HTML acordeao (referencia visual, nao e a entrega)
- `_projeto/VOCABULARIO_OPERACIONAL.md` — termos reais do time
- `_projeto/JORNADA_LOGICA.md` — como os marcos sao detectados

---

## Ideias estacionadas

(anotar aqui em 1 linha quando surgir algo fora do escopo)

