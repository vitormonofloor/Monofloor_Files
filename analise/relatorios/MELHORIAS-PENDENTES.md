# Melhorias do Relatório Quinzenal · backlog priorizado

> **Norte de implementação.** Lista travada pra não perder fio durante as efetivações.
> Criado em 2026-05-04 após auditoria do relatório como leitor externo.
> Marcar `[x]` conforme implementar. Adicionar item novo no fim da prioridade correspondente.

## Convenções

- **P0** · gatilho crítico (quebra credibilidade pra diretoria) · resolver agora
- **P1** · estrutura (Camada Executiva + Glossário) · próxima sessão
- **P2** · dado faltante (depende de coleta acumular) · médio prazo
- **P3** · visualização gráfica (Fase 2) · futuro
- **P4** · lapidação contínua (sempre rolando)

Cada item: `[status] · [referência] · descrição curta · why`

---

## 🔥 P0 · Cleanup de gatilhos (sessão imediata · ~30-45min)

> Esses items são bugs visíveis ao leitor final que destroem credibilidade.

- [ ] **`[REVISAR]` vazado pro output final** — marcadores de bastidor aparecem no relatório que iria pra diretoria. Filtrar/esconder no gerador final.
  *Why:* Vitor não conseguiu revisar antes de gerar, e o relatório foi entregue cru.

- [ ] **Tabela equipes de linha de frente vazia** (Seção 8) — todas com `—`. Ou preencher com dados reais (cruzar com `equipes`/`details`) ou remover a tabela.
  *Why:* Tabela só com travessões parece bug.

- [ ] **Alertas duplicados pra mesma obra** (Seção 1) — JONATHAS aparece 2× nos 3 alertas. Agrupar por obra ou de-duplicar.
  *Why:* Falta de curadoria. Diretoria pensa "sistema burro".

- [ ] **Resumo Orion truncado** (Seção 9) — corta no meio com `...` no caractere 500. Aumentar pra 800-1000 ou cortar em fim de frase.
  *Why:* Parece bug de truncamento.

- [ ] **Jargão técnico em colunas "Fonte"** (Seção 2) — `rodrigo-stats`, `/api/analise`, `headline` visíveis. Trocar por nomes amigáveis ("Painel", "Análise do Painel", "Snapshot diário") OU remover coluna inteira.
  *Why:* Diretoria não quer ver `*.json`.

- [ ] **Filtro `< 5 obras` no ranking de Consultores** (Seção 8) — Thaísa 100% problema (1 obra) e Pedro Marçal/Renata (1 obra cada) distorcem. Excluir do ranking quem tem < 5 obras OU marcar com asterisco.
  *Why:* Estatística de cauda longa engana leitor.

- [ ] **Reconciliar 184 vs 260 obras** (Seções 1 e 3) — números diferentes na mesma análise sem explicação. Declarar a diferença ("260 ativas no Painel · 184 com diagnóstico no /api/analise") OU usar o mesmo universo nas duas seções.
  *Why:* Auditor externo vê inconsistência.

- [ ] **`A INICIAR firmadas (30d) = 0`** — investigar se é bug ou fato real. Se zero é real, declarar contexto ("nenhuma obra com data_de_entrada confirmada nos próximos 30d"). Se é bug, corrigir consulta ao Painel.
  *Why:* Zero solto parece bug ou crise.

- [ ] **`Ocorrências abertas: 950`** sem contexto (Seção 2) — adicionar denominador ou janela ("950 abertas em 1.038 obras totais" ou "950 acumuladas desde início do Painel").
  *Why:* Número solto assusta sem ancoragem.

---

## 📐 P1 · Estrutura · Camada Executiva + Glossário (1-2 sessões)

> Reorganização que separa "leitura de diretoria" (curta) de "leitura técnica" (atual).

- [ ] **Camada 1 · Brief Executivo (2 páginas, antes do Resumo atual)**
  - Manchete única em 1-2 frases de impacto
  - 6 KPIs com sinaleira verde/amarelo/vermelho + interpretação curta
  - 3 alertas-chave pra Diretoria deliberar
  - Top 3 recomendações do mês (consolidadas, não 4 receitas espalhadas)
  - Implicação sintética em 1 frase

- [ ] **Glossário (Anexo B, fim do documento)** — 1 box explicando:
  - KIRA · Painel de Obras · Lab Orion · Score Saúde
  - Fases típicas (AGEND.VT-AFERIÇÃO, INFORMAÇÕES LOGÍSTICAS, etc)
  - Termos: zumbi, órfã, pós-entrega, fluxo normal, retrabalho

- [ ] **Conclusão executiva única no fim** (após Seção 10) — 1 parágrafo de fechamento amarrando o que diretoria deve sair pensando. Diferente do "Para próxima quinzena · 3 prioridades [REVISAR]".

- [ ] **Score Saúde com fórmula declarada** (Seção 1 ou Glossário) — explicar que é calculado a partir de zumbi_pct, orfas_pct, ciclo_180_pct, lote_vt_270d. Faixas: 0-49 vermelho, 50-69 amarelo, 70-100 verde.

- [ ] **Coluna "Anterior" da Seção 2** — quando score-historico tiver dados (mais 7-10 dias), preencher com valores reais. Hoje todos `—`.

---

## 📊 P2 · Dados faltantes (médio prazo · dependem de coleta)

- [ ] **Comparativo histórico 3 e 6 meses** — score, capacidade, % atraso, retrabalho. Precisa `score-historico` e `historico-aplicadores` acumularem mais dias (iniciados 2026-05-01).

- [ ] **Implicação financeira sintética** — quanto em R$ representa 53 obras atrasadas + 27 em retrabalho? Precisa cruzar com `valorTotal`/`metragemM2` de cada obra (já temos parcialmente no `acessoDetalhes.allFields`). Output: "R$ X em obras atrasadas (Y% do faturamento mês)".

- [ ] **Top 3 obras de risco pessoal da Diretoria** — não as mais atrasadas, mas as com **flag detrator_latente** + **valor R$ alto** + **silêncio recente**. Cruzar Orion + Painel + valor.

- [ ] **Benchmark do setor** — 35% capacidade é folga ou crise pra mercado de piso polido? Pesquisa externa ou definir meta interna como ancora ("meta interna: capacidade 60-75% saudável").

- [ ] **Período avaliado claro** (Seção 4) — as 5 obras detalhadas têm diagnósticos de 15/03 (50 dias antes da quinzena). Filtrar pra "obras que entraram em crítico DURANTE a quinzena" OU declarar que é "estado atual da crítica" (foto, não filme).

---

## 🎨 P3 · Visualização gráfica (Fase 2 · futuro)

- [ ] **Gráfico de tendência Score 6 meses** — linha simples com marcadores semanais. Vai virar SVG inline no HTML.

- [ ] **Mapa BR mini-resumido** — versão simplificada do Q4 com coloração por concentração de risco.

- [ ] **Mini-charts de delta inline** (sparklines) — em cada KPI da tabela, mostrar mini-gráfico das últimas 8 quinzenas.

- [ ] **Pizza de categorias de problema** — visual no lugar da lista textual da Seção 3.

- [ ] **Capacidade × Demanda em barras horizontais** — visual da Seção 7 com 3 barras (capacidade / volume / a iniciar).

---

## 🔧 P4 · Lapidação contínua (sempre rolando)

- [ ] **Calibrar números [REVISAR] das receitas** — Vitor refina os impactos chutados ("Score sobe ~3-4 pontos") com conhecimento operacional real.

- [ ] **Promover caminhos enxutos pra receitas formais** — quando um caminho aparece bom em uso, mover do markdown enxuto pra `receitas-qualidade.json` com Como/Custo/Impacto/Risco completos.

- [ ] **Listagem nominal Anexo A** (Fase 1.1c) — RODANDO/ESTAGNADO/PENDENTE com nomes dos clientes. Cruzar `details/*.json`.

- [ ] **Comentários narrativos `[REVISAR]`** — frases de transição em Diagnóstico, Atrasos, Retrabalho, Geografia, Equipe, Orion. Vitor escreve quando tiver tempo.

- [ ] **Acompanhar evolução das categorias** — Comunicação está caindo ou subindo MoM? Infiltração? Adicionar delta nas categorias.

- [ ] **Receitas adicionais no catálogo** — adicionar receitas pra problemas que ainda não têm:
  - alto retrabalho (>30 obras em retorno)
  - cluster paralisado crescendo
  - desbalanço Luana × Wesley
  - cauda longa AGEND.VT-AFERIÇÃO específica

---

## Decisões fechadas (referência)

- **Tom:** moderno e direto · zero "ressaltando, pautando, possibilitando"
- **Frequência:** quinzenal
- **Público:** diretoria pode ler · peso executivo
- **Formato fonte:** Markdown editável
- **Formato entrega:** PDF (gerado de MD via Pandoc OU Ctrl+P do browser)
- **Modo de geração:** ~80% automatizado · 20% lacunas pra revisão
- **Gatilho:** híbrido · botão no hub + aviso Telegram quinzenal
- **Conteúdo:** 100% derivado de Dashboard + Orion · relatórios antigos foram inspiração de formato/tom

---

## DNA inegociável

> Cada problema citado vem com (1) hipótese de causa + (2) ação sugerida ou pergunta orientada.
> Hierarquia visual rigorosa. Densidade controlada (1 página = 1 ideia).
> Leitor sai com **respostas e ideias de correção**, não desesperado.

---

## Histórico de revisões deste documento

- **2026-05-04** · v1 · criado após auditoria de leitor externo. 9 P0 + 5 P1 + 5 P2 + 5 P3 + 6 P4 = **30 itens** travados.
