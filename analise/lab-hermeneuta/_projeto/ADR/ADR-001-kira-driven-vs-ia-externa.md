# ADR-001 · Lab Orion · Kira-driven em vez de IA externa

**Status:** Aceito
**Data:** 2026-05-05
**Quem decidiu:** Vitor + Claude (sessão pivô Caminho B)

## Contexto

Lab Orion precisava categorizar 228 obras quanto a "saúde / urgência / abandono". Plano original (Caminho B IA-pesado) era rodar IA externa (GPT-4o-mini via GitHub Models) interpretando msgs Telegram + dados do Painel pra cada obra.

Bloqueios descobertos rodando:
- GitHub Models tem **150 req/dia** (não 8k que líamos antes) · esgota antes de cobrir 228
- IA confundia campos `status` (macro) com `fase` (específica) · 100% falso positivo na primeira rodada
- Em interrupção (TaskStop), perdia trabalho processado · 138 obras consumiram quota e não geraram output

Vitor sinalizou: *"Estamos indo na contramão da sabedoria"*. Questão real: **o Kira (sistema do Painel) já fez a análise semântica · só precisamos cruzar os campos prontos**.

## Decisão

**Não usar IA externa** pra reinterpretar msgs/dados. Em vez disso, escrever **regras determinísticas** que cruzam campos semânticos já prontos no Painel (`pendenciaManual.whatsappSummary`, `tagKira`, `situacaoAtual`, `acessoDetalhes.labels`, `ocorrencias`).

Resultado: `cruzar_kira.py` em 213 linhas · 4 regras determinísticas · roda nas 228 obras em 3.6 min · zero IA · zero rate limit · 100% auditável.

## Alternativas descartadas

- **IA externa via GitHub Models** · rate limit fatal · prompt engineering frágil · sem auditoria do "porquê" da resposta
- **IA local via Ollama** · custo de manter modelo · latência alta · sem ganho semântico vs Kira já-mastigado
- **Não fazer · só varrer fonte bruta** · perderia o trabalho que o Kira já faz

## Consequências · como saberemos se foi errado

- **Sintoma:** regras determinísticas não cobrem casos novos que IA pegaria → revisar (e talvez complementar com IA cirúrgica em obras específicas, não em massa)
- **Sintoma:** Kira mudar formato dos campos sem aviso → cruzamento quebra → revisar contrato com Rodrigo (dev do planejamento)
- **Sintoma:** discrepâncias detectadas se acumulam em padrões que IA poderia agrupar → considerar IA pós-cruzamento pra clusterização (não pra classificação primária)

## Memórias relacionadas

- `feedback_kira_ja_interpretou.md` · não reinventar o que a fonte já interpretou
- `project_orion_pivo_kira_driven_2026_05_05.md` · contexto pleno
- `project_orion_opcao_b_pausada.md` · automação click→IA dormente
