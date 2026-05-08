# ADR-007 · ATENA descontinuado · absorvido pelo Lab Orion

**Status:** Aceito
**Data:** 2026-05-01
**Quem decidiu:** Vitor (após análise)

## Contexto

Existiam 2 ferramentas de análise de obras concorrentes:
- **Lab Orion** · sandbox Telegram × Painel · `lab.monofloor.cloud`
- **ATENA** · ferramenta paralela com escopo similar (análise de obras com sinais de alerta)

Análise revelou que ATENA era *"cópia pobre do que o Lab Orion já entrega"* — sobreposição de função, divergência de conceitos, custo de manter os dois sincronizados, risco de relatórios contraditórios pra diretoria.

## Decisão

**Descontinuar ATENA.** Toda funcionalidade que tinha valor único migra pro Lab Orion. Recursos não-essenciais simplesmente desaparecem. Não recriar.

Lab Orion vira fonte única de verdade pra análise cruzada Telegram × Painel × Ocorrências.

## Alternativas descartadas

- **Manter os dois** · custo de sincronizar · risco de relatórios contraditórios · esforço dobrado
- **Deletar Orion, manter ATENA** · ATENA era inferior em quase tudo · custo de migrar features ricas seria maior
- **Migrar features do ATENA pro Orion antes de deletar** · Vitor avaliou que não havia features únicas valendo a pena · decisão foi corte limpo

## Consequências · como saberemos se foi errado

- **Sintoma:** alguém pedir feature do ATENA que não está no Orion → reabrir só pra avaliar se vale portar · não recriar a ferramenta
- **Sintoma:** análise de obras virar ainda mais complexa · um Lab pode ficar denso demais · considerar VIEWS especializadas dentro do Orion (mas não outra ferramenta)

## Memórias relacionadas

- `project_atena.md` · registro do projeto descontinuado
- `project_hermeneuta_lab.md` · contexto do Lab Orion (originalmente "Hermeneuta-Lab")
