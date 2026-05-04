# Melhorias do Relatório Quinzenal · backlog priorizado

> **Norte de implementação.** Lista travada pra não perder fio durante as efetivações.
> Criado em 2026-05-04 após auditoria do relatório como leitor externo.
> Marcar `[x]` conforme implementar. Adicionar item novo no fim da prioridade correspondente.

## Histórico de leituras frias

- **2026-05-04 · 1ª leitura externa** → 9 P0 + 5 P1 originais. P0 toda fechada · P1 4/5.
- **2026-05-04 · 2ª leitura externa** → 14 itens novos identificados. **P0 nova fechada** (5 itens críticos): bug A INICIAR Seção 7, REVISAR-bullet vazando, Score "anterior 49" enganoso (declarado "snapshot N dias atrás"), Seção 4 com diagnósticos antigos (declarado), Glossário ganhou fantasma/Apenas CEP/Concluído vs Finalizado. Pendentes ainda P1 nova (cortar Seção 1 redundante, conectar 3 alertas mesmo padrão, cortar 3 destaques) + P2 nova (impactos chutados marcados, gírias renomeadas).

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

- [x] **`[REVISAR]` vazado pro output final** — `gerar-pdf.py` agora pré-processa o MD antes de virar HTML: remove linhas-só-de-revisar, mantém rascunhos automáticos sem o tag.

- [x] **Tabela equipes de linha de frente vazia** (Seção 8) — preenchida com dados reais (Líder + Aplicadores ativos + Obras lideradas + Estado com sinaleira 🟢/⚪/🟡).

- [x] **Alertas duplicados pra mesma obra** (Seção 1) — `gerar_alertas_executivos` agora deduplica por `clienteNome` antes de selecionar top 3.

- [x] **Resumo Orion truncado** (Seção 9) — agora corta em fim de frase mais próximo de 800 chars (com fallback pra ... só se não achar ponto).

- [x] **Jargão técnico em colunas "Fonte"** (Seção 2) — substituído por nomes amigáveis: rodrigo-stats → "Painel de Obras", headline → "Snapshot diário", analise → "Análise do Painel", operacional_kira → "KIRA WhatsApp", dashboard → "Painel · ocorrências".

- [x] **Filtro `< 5 obras` no ranking de Consultores** (Seção 8) — separa amostra pequena em nota: *"Amostra pequena (1-4 obras), fora do ranking: Thaísa, Marçal, Renata."*

- [x] **Reconciliar 184 vs 260 obras** (Seções 1 e 3) — adicionada nota: *"Universos: 260 ativas no Painel · 184 com diagnóstico de risco no /api/analise (a diferença de 76 são obras em pós-entrega ou pausadas)."*

- [x] **`A INICIAR firmadas (30d) = 0`** — bug do gerador: estrutura real era `proximos["30d"]["obras"]`, não `firmadas_30d`. Agora mostra **23 obras · 3.738 m²**.

- [x] **`Ocorrências abertas: 950`** sem contexto (Seção 2) — adicionado denominador: **950 (0.9 por obra · acumulado)**.

---

## 📐 P1 · Estrutura · Camada Executiva + Glossário (1-2 sessões)

> Reorganização que separa "leitura de diretoria" (curta) de "leitura técnica" (atual).

- [x] **Camada 1 · Brief Executivo (Seção 0 antes do Resumo)** — manchete impactante com sinaleira de zona, 6 KPIs com sinaleira + interpretação curta, Top 3 recomendações consolidadas (puxa das receitas), implicação sintética em 1 frase. Resumo de 60s pra Diretoria.

- [x] **Glossário (Anexo B, fim do documento)** — 4 sub-seções: Sistemas (Painel/Orion/KIRA), Métricas (Score com fórmula, Capacidade, Ciclo), Termos operacionais (fluxo normal, retrabalho, cluster, detrator), Fases típicas (sequência das 9 fases), Pessoas-chave.

- [x] **Conclusão executiva única no fim** — 2 parágrafos amarrando: tom da operação + leitura honesta + ponteiro pra próxima medição.

- [x] **Score Saúde com fórmula declarada** — incluído no Glossário (Anexo B) com 4 componentes (zumbi/órfã/ciclo180/cauda270) + faixas explícitas (0-49 vermelho · 50-69 amarelo · 70-100 verde).

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
- **2026-05-04** · v2 · **P0 fechada** (9 itens marcados [x]). Próximo alvo: P1 (Brief Executivo + Glossário).
- **2026-05-04** · v3 · **P1 quase fechada** (4 de 5 [x]). Brief Executivo + Glossário + Conclusão Executiva + Score com fórmula. Único item P1 pendente: coluna "Anterior" da Seção 2 (depende de histórico acumular). Visuais SVG inline também adicionados (Top categorias, KIRA, Capacidade) + sinaleira nos 6 KPIs. Cargo Vitor corrigido pra "Gerente da Qualidade".
