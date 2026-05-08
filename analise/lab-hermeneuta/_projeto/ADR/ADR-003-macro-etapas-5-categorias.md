# ADR-003 · Lab Orion · Macro-etapas em 5 categorias

**Status:** Aceito
**Data:** 2026-05-06
**Quem decidiu:** Vitor + Claude (sessão arquitetura Jornada)

## Contexto

A página Jornada tinha 11 fases granulares (Planejamento + Hibernação ×N + Atividade retomada ×N + Despertar + Execução + Pós-execução). Leitor frio precisava somar mentalmente pra responder *"essa obra demorou por causa de quê?"*. Vitor pediu agregar em macro-etapas com semântica de negócio.

Risco de redundância: já havia (1) timeline cronológica colorida com fases · (2) pills "Jornada total / Execução / Hibernação" · (3) macro-etapas. Três visualizações de duração competindo · cold read disse que era confuso.

## Decisão

5 macro-etapas + categoria especial:

- **Pré-obra** · planejamento, atividade retomada, despertar, pré-execução · tudo antes da aplicação física do Ciclo 1
- **Execução** · só fase "Execução" do Ciclo 1 · trabalho físico da entrega original
- **Tratativas** · todo o ciclo de retrabalho (≥ Ciclo 2) que não é fase Execução pura · negociação, definição, agendamento, acompanhamento
- **Retrabalho** · só fase "Execução" em ciclo ≥ 2 · aplicação física nova após reprovação
- **Pós-obra** · Pós-execução do Ciclo 1 quando obra fechou aprovada
- **Hibernação** · 30+ dias sem msgs (categoria de tempo morto, não fase do projeto · visual hachurado)

Removemos a "barra stacked" redundante que só repetia o que a timeline mostrava. Mantivemos o header denso (3 números agregados) + chips clicáveis com badge de marcos por macro.

## Alternativas descartadas

- **Manter as 11 fases** · leitor sem capacidade de agregar mentalmente · zero síntese
- **3 macro-etapas (Pré · Exec · Pós)** · mistura retrabalho dentro de Exec → mascara o gargalo
- **6+ macro-etapas com Hibernação dividida em N tipos** · over-engineered · cauda longa pouco útil
- **Manter barra stacked + timeline + pills (3 visualizações)** · redundância confunde leitor frio

## Consequências · como saberemos se foi errado

- **Sintoma:** obra com 3+ ciclos de retrabalho · Tratativas inflacionado · pode ser útil quebrar em "Tratativas Ciclo N"
- **Sintoma:** leitor frio pergunta repetidamente "qual a diferença entre Tratativas e Pré-obra?" → glossário ou rotular melhor
- **Sintoma:** diretoria começar a confundir "Retrabalho 7d" com "obra finalizada em 7d" → adicionar sinalização visual de ciclo

## Memórias relacionadas

- `ADR-002` · Tratativas × Retrabalho · classificação operacional
- `reference_tratativas_vs_retrabalho.md` · definição canônica
