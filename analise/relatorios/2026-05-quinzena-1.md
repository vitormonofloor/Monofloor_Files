# Relatório Quinzenal de Qualidade

**Período:** 22/04 a 06/05/2026 · Quinzena 1 de Maio
**Setor de Qualidade Monofloor · Vitor Gomes, Gerente da Qualidade**
**Gerado em:** 06/05/2026 10:27

---

## 0 · Brief Executivo

> **Leitura de 60 segundos pra Diretoria.** Análise técnica nas Seções 1-8 · recomendações detalhadas na Seção 9.

### Manchete

🔴 **Operação em zona vermelha** · Score 47/100 (▼ -2 ⚠ vs snapshot de 4 dias atrás). 259 obras ativas · 53 atrasadas (21 críticas) · 25 em retorno · capacidade utilizada em 32% (folga produtiva).

### Painel de Saúde · 6 KPIs

| | Indicador | Valor | Status |
|---|---|---|---|
| 🔴 | Score Saúde | **47/100** (▼ -2 ⚠) | abaixo da zona saudável (≥70) |
| 🔵 | Obras ativas em fluxo | **259** (38 em execução) | volume da carteira |
| 🟡 | Atrasadas | **53** (21 críticas) | 20% das ativas |
| 🟡 | Em retorno (reparo/marcas) | **25** | 10% da carteira em pós-entrega |
| 🟡 | Capacidade utilizada | **32%** | folga produtiva |
| 🟡 | Cobertura KIRA | **65%** | 65% da carteira monitorada · 70 sem grupo |


> Sinaleira: 🟢 saudável · 🟡 atenção · 🔴 crítico · 🔵 informativo

### 3 recomendações priorizadas do mês

1. **Score Saúde abaixo da zona saudável** — Mutirão + Padronização preventiva combinados — mutirão zera estoque agora, padronização previne. Gargalo VT fica pra próxima quinzena se mutirão der certo.
2. **Comunicação é a categoria dominante de problema** — Diário obrigatório + Auditoria amostral dão tração rápida. Bloqueio cultural só vale se já houver casos crônicos comprovados.
3. **Infiltração com volume alto e proporção crítica** — Auditoria primeiro pra entender raiz. Critério reforçado vem como ação derivada do que a auditoria descobrir.

> Cada recomendação acima é a **combinação automática** da receita correspondente na Seção 9. Para Como/Custo/Impacto/Risco completos, consultar a seção.

### 3 alertas críticos · obras pra deliberar essa semana

1. **JONATHAS DE ALMEIDA NUNES LUKAS** — Projeto deveria estar em "INFORMAÇÕES LOGÍSTICAS" mas está em "AGEND. VT - AFERIÇÃO/ORIENTAÇÃO" · **Causa:** fase atual atrás da prevista pelo cronograma · **→ Ação:** acelerar transição pra fase **INFORMAÇÕES LOGÍSTICAS**
2. **NINA RODRIGUES FIALDINI** — Projeto deveria estar em "INFORMAÇÕES LOGÍSTICAS" mas está em "PROJETOS  - 1ª REVISÃO" · **Causa:** fase atual atrás da prevista pelo cronograma · **→ Ação:** acelerar transição pra fase **INFORMAÇÕES LOGÍSTICAS**
3. **ELLIOTT ROBERT MICHEL FRES** — Projeto deveria estar em "INFORMAÇÕES LOGÍSTICAS" mas está em "CONFIRMAÇÕES OP 1" · **Causa:** fase atual atrás da prevista pelo cronograma · **→ Ação:** acelerar transição pra fase **INFORMAÇÕES LOGÍSTICAS**

### Implicação sintética

> Operação respira (capacidade 32%), mas com **21 obras críticas** e **70 sem KIRA** — o gargalo é qualitativo, não de volume.

---

## 1 · Indicadores do Período

| Indicador | Atual | Anterior | Δ | Fonte |
|---|---|---|---|---|
| Total ativas em fluxo | 259 | — | — | Painel de Obras |
| Em execução agora | 38 | — | — | Painel de Obras |
| Atrasadas | 53 | — | — | Análise do Painel |
| → Críticas | 21 | — | — | Análise do Painel |
| → Alto risco | 27 | — | — | Análise do Painel |
| Obras em retorno (reparo + marcas) | 25 | — | — | Painel de Obras |
| Cluster paralisado | 5 | — | — | Painel de Obras |
| Score Saúde Operacional | 47/100 | 49 | ▼ -2 ⚠ | Snapshot diário |
| TEMPO médio de ciclo | 172d | — | — | Painel de Obras |
| VOLUME m² em curso | 4.453 | — | — | Painel de Obras |
| Capacidade utilizada | 32% | — | — | Painel de Obras |
| A iniciar firmadas (30d) | 18 obras · 1.824 m² | — | — | Painel de Obras |
| Cobertura KIRA | 65.2% | — | — | KIRA WhatsApp |
| Ocorrências abertas | 950 (0.9 por obra · acumulado) | — | — | Painel · ocorrências |

> Deltas vs quinzena anterior em construção · histórico de Score acumulando desde 2026-05-01.

---

## 2 · Diagnóstico Operacional

### Saúde geral da carteira
- **184** obras ativas analisadas
- **107** sem problemas relevantes
- **21** críticas + **27** em alto risco
- **53** com atraso identificado pelo Painel

> *Universos: **259** ativas no Painel · **184** com diagnóstico de risco no /api/analise (a diferença de 75 são obras em pós-entrega ou pausadas que não entram nessa análise específica).*


### Top 3 categorias de problema (excluindo "Outros")
- **Comunicação** — 77 obras (20 críticas)
- **Material** — 64 obras (8 críticas)
- **Infiltração** — 48 obras (23 críticas)

<figure class="viz">
<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:600px">
  <text x="0" y="18" font-family="Plus Jakarta Sans, sans-serif" font-size="11" fill="#8a7e72" letter-spacing="0.5">Top 5 categorias de problema · cor por proporção crítica</text>
  <text x="0" y="54" font-family="Plus Jakarta Sans, sans-serif" font-size="11" fill="#3a3530" font-weight="500">Comunicação</text>
  <rect x="120" y="40" width="380.0" height="22" fill="#d97a4a" rx="2"/>
  <text x="505.0" y="54" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#3a3530">77</text>
  <text x="529.0" y="54" font-family="JetBrains Mono, monospace" font-size="9" fill="#a89e92">(20 críticas)</text>
  <text x="0" y="84" font-family="Plus Jakarta Sans, sans-serif" font-size="11" fill="#3a3530" font-weight="500">Material</text>
  <rect x="120" y="70" width="315.84415584415586" height="22" fill="#b89a4a" rx="2"/>
  <text x="440.84415584415586" y="84" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#3a3530">64</text>
  <text x="464.84415584415586" y="84" font-family="JetBrains Mono, monospace" font-size="9" fill="#a89e92">(8 críticas)</text>
  <text x="0" y="114" font-family="Plus Jakarta Sans, sans-serif" font-size="11" fill="#3a3530" font-weight="500">Infiltração</text>
  <rect x="120" y="100" width="236.88311688311688" height="22" fill="#c45a5a" rx="2"/>
  <text x="361.8831168831169" y="114" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#3a3530">48</text>
  <text x="385.8831168831169" y="114" font-family="JetBrains Mono, monospace" font-size="9" fill="#a89e92">(23 críticas)</text>
  <text x="0" y="144" font-family="Plus Jakarta Sans, sans-serif" font-size="11" fill="#3a3530" font-weight="500">Manchas/Defeitos</text>
  <rect x="120" y="130" width="202.33766233766232" height="22" fill="#b89a4a" rx="2"/>
  <text x="327.3376623376623" y="144" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#3a3530">41</text>
  <text x="351.3376623376623" y="144" font-family="JetBrains Mono, monospace" font-size="9" fill="#a89e92">(8 críticas)</text>
  <text x="0" y="174" font-family="Plus Jakarta Sans, sans-serif" font-size="11" fill="#3a3530" font-weight="500">Substrato</text>
  <rect x="120" y="160" width="133.24675324675326" height="22" fill="#b89a4a" rx="2"/>
  <text x="258.24675324675326" y="174" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#3a3530">27</text>
  <text x="282.24675324675326" y="174" font-family="JetBrains Mono, monospace" font-size="9" fill="#a89e92">(2 críticas)</text>
</svg>
</figure>

> Categorização vem da Análise do Painel — agrupamento automático que substitui o trabalho manual de catalogar causa-raiz.

### Pulso KIRA · comunicação com cliente

<figure class="viz">
<svg viewBox="0 0 600 105" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:600px">
  <text x="0" y="18" font-family="Plus Jakarta Sans, sans-serif" font-size="11" fill="#8a7e72" letter-spacing="0.5">Distribuição da carteira ativa por KIRA</text>
  <text x="600" y="18" font-family="JetBrains Mono, monospace" font-size="11" fill="#8a7e72" text-anchor="end">201 obras</text>

  <rect x="0" y="30" width="214.92537313432837" height="28" fill="#6b8e3d" rx="2 0 0 2"/>
  <rect x="214.92537313432837" y="30" width="137.01492537313433" height="28" fill="#b89a4a"/>
  <rect x="351.94029850746267" y="30" width="188.05970149253733" height="28" fill="#a89e92" rx="0 2 2 0"/>

  <text x="107.46268656716418" y="49" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#fff" text-anchor="middle">80</text>
  <text x="283.43283582089555" y="49" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#fff" text-anchor="middle">51</text>
  <text x="445.97014925373134" y="49" font-family="JetBrains Mono, monospace" font-size="11" font-weight="600" fill="#fff" text-anchor="middle">70</text>

  <circle cx="6" cy="78" r="4" fill="#6b8e3d"/>
  <text x="16" y="82" font-family="Plus Jakarta Sans, sans-serif" font-size="10" fill="#3a3530">Saudável (40%)</text>
  <circle cx="170" cy="78" r="4" fill="#b89a4a"/>
  <text x="180" y="82" font-family="Plus Jakarta Sans, sans-serif" font-size="10" fill="#3a3530">Atenção (25%)</text>
  <circle cx="320" cy="78" r="4" fill="#a89e92"/>
  <text x="330" y="82" font-family="Plus Jakarta Sans, sans-serif" font-size="10" fill="#3a3530">Sem KIRA (35% · cegueira)</text>
</svg>
</figure>


- **Cobertura:** 131 de 201 obras ativas têm grupo de WhatsApp acompanhado (65.2%)
- **Saudável:** 80 (61.1% das monitoradas)
- **Em atenção:** 51
- **Sem KIRA:** 70 *(cegueira — obras que pra Qualidade são silêncio)*

> [REVISAR] Comentário narrativo de 1-2 frases sobre o que esses números contam juntos.

> 💡 **Caminhos pra reduzir cegueira KIRA →** ver **Seção 9 · Conclusões** (receita "cegueira_kira" com 3 caminhos detalhados).

---

## 3 · Análise de Atrasos · caso a caso

> Top 5 obras com maior atraso e diagnóstico textual disponível. **Estado atual** (dias de atraso · fase) é fresco, mas o **diagnóstico narrativo** abaixo é a última análise registrada no Painel — pode ter datas anteriores ao período do relatório se a análise não foi atualizada. Cabe à Gerência da Qualidade verificar se o quadro descrito ainda é válido.

### ADRIANA FERNANDES PERES · SÃO PAULO · 40 dias de atraso
**Fase atual:** INDÚSTRIA - EM PRODUÇÃO

DIAGNÓSTICO 15/03/2026 — Execução prevista 25/03 (8 dias).

🔴 BLOQUEIO 1: EQUIPE NÃO DEFINIDA — 166m² piso+parede em SP sem equipe alocada a 8 dias da execução.
🔴 BLOQUEIO 2: Ainda em INDÚSTRIA (EM PRODUÇÃO) — material pode não estar pronto a tempo. Produção + logística SP exige mínimo 7-10 dias.
🟡 ALERTA: Data de execução NÃO CONFIRMADA (apenas prevista).
🟡 ALERTA: Cor PERSONALIZADA — verificar se amostra foi aprovada e produção iniciada.

### MISCI BRASIL COMERCIO DE MODA LTDA  · RIO DE JANEIRO · 40 dias de atraso
**Fase atual:** AGEND. VT - ENTRADA

DIAGNÓSTICO 15/03/2026 — Execução prevista 25/03 (8 dias).

🔴 BLOQUEIO: Ainda em AGEND. VT ENTRADA — VT sequer realizada. Sem VT não há como aprovar substrato, definir escopo final e iniciar produção.
🟡 RISCO: OBRA EXTERNA em RJ (Ipanema) — dependência climática.
🟡 RISCO: Autonivelante Quartzolit utilizado (RISCO CRÍTICO de patologias — conforme situação registrada).
🟢 POSITIVO: Equipe MICHAEL definida. Metragem pequena (8m²).

### PALLOMA BIANCA RAMIREZ URIZZI · SÃO PAULO · 34 dias de atraso
**Fase atual:** LOGÍSTICA - EM ENTREGA

DIAGNÓSTICO OPERACIONAL — PALLOMA BIANCA RAMIREZ
=================================================

ESTADO REAL DA OBRA:
Obra com longo histórico de preparação. Múltiplas VTs realizadas (03/12/25, 06/01/26, 19/02/26) com extensas listas de pendências do contrapiso. Cliente ameaçou ação judicial e devolução do valor em 26/02. Diretor Geral visitou obra para mediar. Situação parcialmente estabilizada — equipe operacional designada com início 16/03.


### SILVANA PANDOLFI JANETE · BERTIOGA · 14 dias de atraso
**Fase atual:** REVISÃO FINAL OP

PROJETO: SILVANA PANDOLFI JANETE | SP - Bertioga (Riviera de São Lourenço) | Fase: REVISÃO FINAL OP

RESUMO: 45 mensagens (38 WA + 7 TG). Obra em fase de definição de cor. Cliente/arquiteta solicitam amostras Everest (não veio na caixa Stelion). Data alterada para 20/04. Monofloor migrou canal de comunicação (grupo será encerrado) e pediu ponto focal único.

PONTOS DE ATENÇÃO: (1) Cor indefinida - produção requer 12 dias úteis. (2) Migração de canal pode gerar falha de comunicação. (3) Responsável por alinhamento não definido no novo canal.


### MONTRELUX SOLUÇÕES EM VIDRO LTDA · CURITIBA · 10 dias de atraso
**Fase atual:** INDÚSTRIA - EM PRODUÇÃO

DIAGNÓSTICO 15/03/2026 — Execução prevista 13/04 (29 dias).

🔴 BLOQUEIO: EQUIPE NÃO DEFINIDA — 665m² piso+parede em CURITIBA. É a MAIOR obra confirmada do período.
🟡 ATENÇÃO: Em INDÚSTRIA EM PRODUÇÃO — material em fabricação. 29 dias é prazo adequado para produção.
🟡 RISCO: 665m² requer equipe GRANDE + planejamento logístico extenso.


> [REVISAR] Padrões observados nos casos acima (1-2 frases) · *qual o tema dominante?*

### Caminhos a explorar · pra reduzir atrasos críticos
- 🎯 **Triagem semanal das críticas** — toda segunda, ranking por dias parados → top 5 vão pra reunião da Gerência da Qualidade
- 🚨 **Escalação automática D+30** — obra que passa 30d na mesma fase notifica a Gerência da Qualidade + cliente recebe contato
- 📋 **Checklist proativo de pré-execução** — confirmar equipe + cor + VT *antes* da data prevista, não no dia
- 💬 **Comunicação proativa com cliente** — quando atraso for inevitável, antecipar (em vez de cliente cobrar)

> [REVISAR] Quais desses caminhos fazem sentido pro período atual? Marcar 1-2 e a gente promove pra Seção 9 com Como/Custo/Impacto/Risco completos.

---

## 4 · Retrabalho & Pós-entrega

> Obras em **reparo** e **marcas_rolo_cera** são pós-entrega — cronograma original já cumprido. Mostradas separadamente do atraso.

| Indicador | Atual | Anterior | Δ |
|---|---|---|---|
| Obras em retorno (total) | 25 | — | — |
| → em reparo | 21 | — | — |
| → em marcas / rolo / cera | 4 | — | — |
| % da carteira ativa | 9.7% | — | — |

### Categorias de problema relacionadas a retrabalho

- **Material**: 64 obras (sendo 8 críticas)
- **Infiltração**: 48 obras (sendo 23 críticas)
- **Manchas/Defeitos**: 41 obras (sendo 8 críticas)
- **Substrato**: 27 obras (sendo 2 críticas)

> Fonte: `/api/analise`. Cada categoria conta obras com problema reportado no Painel — ajuda a identificar **padrões de causa-raiz** sem coleta manual.

### Caminhos a explorar · pra reduzir retrabalho
- 🔍 **Auditoria técnica das críticas** — cruzar 23 infiltrações críticas: período / equipe / substrato / clima → identificar padrão recorrente
- 📐 **Critério reforçado na VT** — checklist obrigatório de umidade/contrapiso/ralo · obra não inicia sem aprovação
- 🎓 **Treinamento focado** — equipes com maior taxa de retorno recebem reciclagem técnica
- ⚖ **Mediação preventiva** — obras com flag detrator_latente recebem visita da Gerência da Qualidade antes de virar caso jurídico

> [REVISAR] Categoria Infiltração tem 47% críticas (taxa MUITO acima da média) — recomendo priorizar Auditoria técnica. Ver Seção 9 pra caminhos detalhados (Como/Custo/Impacto/Risco).

---

## 5 · Geografia

> Distribuição das **obras em risco** (atrasadas / com problema) por cidade. Total na amostra: **50** obras.

| Cidade | Obras em risco |
|---|---|
| São Paulo | 26 |
| Rio De Janeiro | 5 |
| Apenas CEP | 4 |
| Campinas | 2 |
| Curitiba | 2 |
| Cascavel | 1 |
| Florianópolis | 1 |
| Porto Alegre | 1 |


> [REVISAR] Padrão regional observado — alguma cidade puxa atraso desproporcional?

### Caminhos a explorar · pra concentração geográfica
- 🗺 **Análise de raiz regional** — concentração de 52% em **São Paulo** sugere investigar se gargalo é da equipe local ou do volume
- 🚐 **VT em lote** — pra obras próximas geograficamente, agendar visitas técnicas em sequência (ganho logístico)
- 👥 **Distribuir Luana × Wesley por região** — avaliar se proximidade física à equipe melhora acompanhamento
- 📍 **Reforço local** — se gargalo persistir em uma região, considerar contratação de aplicador regional

> [REVISAR] Esses caminhos fazem sentido com o conhecimento da operação? Cortar/promover.

---

## 6 · Capacidade × Demanda

> Pergunta direta: *aceitamos mais obras ou estamos no limite?*

<figure class="viz">
<svg viewBox="0 0 600 90" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:600px">
  <text x="0" y="18" font-family="Plus Jakarta Sans, sans-serif" font-size="11" fill="#8a7e72" letter-spacing="0.5">Capacidade utilizada</text>
  <text x="600" y="18" font-family="JetBrains Mono, monospace" font-size="14" font-weight="600" fill="#2a2520" text-anchor="end">32%</text>
  <rect x="0" y="30" width="540" height="22" fill="#f0ebe3" stroke="#d8c8a8" stroke-width="0.5" rx="3"/>
  <rect x="0" y="30" width="172.8" height="22" fill="#6b8e3d" rx="3"/>
  <text x="600" y="46" font-family="JetBrains Mono, monospace" font-size="10" fill="#8a7e72" text-anchor="end">4.453 / 9.196 m²/mês</text>
  <text x="0" y="78" font-family="Plus Jakarta Sans, sans-serif" font-size="10" fill="#6b8e3d" font-style="italic">▸ folga produtiva · sobra de 4.743 m²/mês</text>
</svg>
</figure>


| Indicador | Atual | Anterior | Δ |
|---|---|---|---|
| Capacidade mensal produtiva | 9.196 m²/mês | — | — |
| VOLUME m² em curso | 4.453 m² | — | — |
| Capacidade utilizada | 32% | — | — |
| A INICIAR firmadas (30d) | 18 obras · 1.824 m² | — | — |

**Diagnóstico atual:** Operação a 32% da capacidade mensal · sobra produtiva considerável. **→ Comercial pode acelerar fechamentos** · cabe sinalizar pro time de vendas.

### Projeção pra próxima semana (2026-05-04 a 2026-05-11)

| Indicador | Próxima semana |
|---|---|
| Obras iniciando | 2 (984 m²) |
| Em execução | 8 (2.651 m²) |
| Capacidade prevista | 25% |

> Fonte: `/api/analytics/weekly-forecast` · projeção baseada em data_de_entrada firmada.

> 💡 **Caminhos pra equilibrar capacidade vs demanda →** ver **Seção 9 · Conclusões** (receita "capacidade_ociosa" com 3 caminhos detalhados).

---

## 7 · Análise por Equipe

### Consultores · responsáveis pela conta

| Consultor | Ativos | Com problema | Atrasados | % com problema |
|---|---|---|---|---|
| Luana Patricia De Andrade Lima | 84 | 34 | 17 | 40.5% |
| Wesley Matheus De Carvalho | 61 | 26 | 9 | 42.6% |
| Pedro Alexandre Santana | 7 | 1 | 0 | 14.3% |

> *Amostra pequena (1-4 obras), fora do ranking: Thaísa De Lara Barbosa, Pedro Marçal, Renata Garcia Penna.*

> Fonte: `/api/analise.teamPerformance`. **% com problema** = projetos com qualquer problema reportado / projetos ativos.

### Supervisão de equipe (linha de frente)

| Equipe | Líder | Aplicadores ativos | Obras lideradas | Estado |
|---|---|---|---|---|
| Equipe Wiguens | Wiguens Louis | 13 | 5 | 🟢 saudável |
| Equipe João | João Carlos | 0 | 3 | ⚪ fantasma |
| Equipe Gilmar | Gilmar Gomes Rafael | 1 | 3 | 🟡 parcial |
| Equipe Egberto | Egberto Sullivan Tavares de Oliveira | 0 | 3 | ⚪ fantasma |
| Equipe Júlio | Júlio Miranda | 8 | 2 | 🟢 saudável |
| Equipe Michael | Cosme Eduardo Soares Ragno | 9 | 0 | 🟢 saudável |


> [REVISAR] Comentário curto sobre destaques (positivos e alertas).

### Caminhos a explorar · pra balanço de carga e qualidade
- ⚖ **Análise de perfil de carteira** — comparar Luana × Wesley considerando complexidade média, valor médio, dispersão geográfica (não só quantidade)
- 🤝 **1:1 quinzenal de carteira** — Gerência da Qualidade revisa as obras de risco com cada consultora (formato fixo, 30min)
- 📊 **Meta de obras em paralelo** — estabelecer máx por consultora (ex: 60 ativas) · acima disso, desacelerar entrada de novas
- 🎓 **Capacitação cruzada** — Luana e Wesley trocam casos pra aprender com diferenças de abordagem

> [REVISAR] Distribuição atual: Luana 84 ativas / Wesley 61. Vale checar se essa diferença é histórica ou recente.

---

## 8 · Sinais Painel × Telegram (Lab Orion)

**Total de obras analisadas pelo Orion:** 230 (piloto)

**Resumo do Orion:** Das 230 obras analisadas (228 ativas), 205 coerentes (89%), 3 com status desatualizado e 20 em silêncio prolongado (abandono detectado · ≥30d sem msg em obra ativa). 54 obras com urgência alta · ação imediata recomendada. Detecção via cruzar_kira · 4 regras determinísticas · trilha auditável em cada obra (campo `analise_kira_trilha`). 2 obras sem análise (resíduo · finalizadas ou erro de fetch).

### Top 5 obras com flags ou divergências

| Obra | Painel diz | Tom Telegram | Veredicto |
|---|---|---|---|
| GETULIO TURATTI OST | marcas_rolo_cera | tom: neutro | coerente |
| MICHELLE CRISTINA FREITAS GARDENAL | planejamento | tom: neutro | coerente |
| LUIS FERNANDO DE LIMA CARVALHO | finalizado | tom: ? | status_desatualizado |
| PAULA CORREA NOGUEIRA | planejamento | tom: tenso | coerente |
| VANESSA AUGUSTA DELGADO DE AZEVEDO PIMENTEL | aguardando_execucao | tom: neutro | coerente |


> [REVISAR] Padrão observado · se houver divergência sistemática, declarar hipótese + ação.

### Caminhos a explorar · pra reduzir divergências e expandir o Orion
- 🔄 **Padronizar quem atualiza o Painel** — definir formalmente: técnico atualiza fase, consultora atualiza status. Hoje há sobreposição
- ⚠ **Auditoria semanal de detrator_latente** — toda semana, Gerência da Qualidade revisa as obras com flag · age antes de virar caso
- 📈 **Expandir piloto Orion** — 10 → 50 obras em 3 meses · ganha massa crítica pra detectar padrões sistêmicos
- 🧪 **A/B de qualidade Painel × WhatsApp** — quando divergir, qual fonte está certa? Auditoria mensal da amostra

> [REVISAR] Lab Orion ainda em piloto (10 obras) · vale acelerar expansão pra ganhar tração nos sinais?

---

## 9 · Conclusões e Recomendações

> Análise propositiva: cada problema crítico detectado vem com diagnóstico, caminhos viáveis (Como · Custo · Impacto · Risco) e recomendação combinada. Números marcados [REVISAR] são chutes que dependem do conhecimento operacional do Vitor pra calibrar.

### Score Saúde abaixo da zona saudável

**Diagnóstico**
Score em 47/100 (zona vermelha · meta ≥70). Componentes que puxam pra baixo:
- Ciclo total mediano em 221d (meta 150d) — 47% acima da meta
- 18.5% de obras zumbi (CLIENTE FINALIZADO sem encerrar)
- 15.0% órfãs (sem consultor responsável)
- 20 obras na cauda longa AGEND.VT-AFERIÇÃO (>270d)

**Para melhorar:** Reduzir o ciclo total e fechar zumbis acumuladas.

**Caminhos viáveis:**

**Caminho A · Mutirão de zumbis**
- **Como:** Força-tarefa de 2 semanas pra encerrar as obras presas em CLIENTE FINALIZADO há mais de 90 dias.
- **Custo do tempo:** ~10h/semana da consultoria por 2 semanas
- **Impacto esperado:** zumbi_pct cai de 18.5% para ~5% · Score sobe ~3-4 pontos [REVISAR número]
- **Risco:** Algumas zumbis podem ter pendência real não-mapeada (descobrir não é problema, mas ajusta a expectativa)

**Caminho B · Atacar gargalo AGEND.VT-AFERIÇÃO**
- **Como:** Revisar SLA de Visita Técnica + reorganizar alocação Luana/Wesley pra desbloquear a cauda longa.
- **Custo do tempo:** Organizacional · alinhamento de agenda da consultoria
- **Impacto esperado:** Ciclo mediano cai 221d → ~190d · Score sobe ~5 pontos [REVISAR número]
- **Risco:** Pressão por velocidade pode comprometer qualidade da VT — não pode ser corrida

**Caminho C · Padronização preventiva (encerramento)**
- **Como:** Gatilho automático D+15 após CLIENTE FINALIZADO pra forçar encerramento (ou pedir justificativa).
- **Custo do tempo:** ~1 sprint de dev no Painel de Obras
- **Impacto esperado:** Previne futuras zumbis · não resolve estoque atual [REVISAR]
- **Risco:** Baixo — se errar, basta desativar a automação

**Recomendação automática:** **Mutirão + Padronização preventiva** combinados — mutirão zera estoque agora, padronização previne. Gargalo VT fica pra próxima quinzena se mutirão der certo.

### Comunicação é a categoria dominante de problema

**Diagnóstico**
77 obras com problema de Comunicação reportado no Painel (20 críticas). É a maior categoria depois de "Outros". Padrões típicos: técnico não responde no grupo, alinhamento direto técnico↔cliente sem passar pela operação, falta de diário de obra.

**Para melhorar:** Aumentar disciplina de registro nos grupos e cortar rotas paralelas técnico↔cliente.

**Caminhos viáveis:**

**Caminho A · Reforço de processo · Diário de Obra obrigatório**
- **Como:** Padronizar postagem diária no grupo Telegram + alerta automático quando passar 24h sem registro.
- **Custo do tempo:** 1-2 reuniões com supervisores + ajuste no bot do Telegram
- **Impacto esperado:** Reduzir Comunicação como categoria em ~30-40% [REVISAR número]
- **Risco:** Resistência cultural · técnicos podem postar 'tudo ok' só pra cumprir

**Caminho B · Auditoria amostral semanal**
- **Como:** Toda sexta, sortear 10 obras ativas e checar registro completo no grupo (consultora + supervisor).
- **Custo do tempo:** ~2h/semana da consultoria
- **Impacto esperado:** Pressão sustentada · expõe técnicos faltosos [REVISAR efeito real]
- **Risco:** Vira micro-gestão se não for acompanhado de feedback construtivo

**Caminho C · Bloquear comunicação direta técnico↔cliente**
- **Como:** Política explícita: qualquer alinhamento de prazo/escopo passa pela consultoria. Técnico que descumpre é notificado.
- **Custo do tempo:** Comunicação interna formal + apoio da Diretoria
- **Impacto esperado:** Resolve a raiz de ~50% dos casos críticos [REVISAR]
- **Risco:** Pode atrasar decisões pequenas que técnico resolveria sozinho

**Recomendação automática:** **Diário obrigatório + Auditoria amostral** dão tração rápida. Bloqueio cultural só vale se já houver casos crônicos comprovados.

### Infiltração com volume alto e proporção crítica

**Diagnóstico**
48 obras com problema de Infiltração reportado (23 críticas — 47% das de infiltração são críticas, taxa muito acima da média de outras categorias).

**Para melhorar:** Reforçar fase de preparação do substrato + critério de aceite da VT.

**Caminhos viáveis:**

**Caminho A · Auditoria técnica das infiltrações críticas**
- **Como:** Cruzar as 23 críticas: período de aplicação, equipe, substrato, condição climática · identificar padrão.
- **Custo do tempo:** ~8h da Qualidade + apoio técnico
- **Impacto esperado:** Identifica raiz · permite ação direcionada (ex: treinamento de equipe específica) [REVISAR]
- **Risco:** Análise pode revelar fragilidade de produto ou processo que demanda investimento

**Caminho B · Critério reforçado de aceite na VT**
- **Como:** Adicionar checklist obrigatório de umidade/contrapiso/ralo na Visita Técnica de Aferição · obra não inicia sem aprovação.
- **Custo do tempo:** Atualização do POP de VT + treinamento Nathan/Braiam
- **Impacto esperado:** Reduz infiltrações em obras NOVAS · efeito visível em 60-90d [REVISAR]
- **Risco:** VT fica mais longa · pode atrasar início de obras

**Recomendação automática:** **Auditoria** primeiro pra entender raiz. **Critério reforçado** vem como ação derivada do que a auditoria descobrir.

### Capacidade da operação subutilizada

**Diagnóstico**
Operação a 32% da capacidade mensal · 4.453 m² em curso vs 9.196 m²/mês de capacidade produtiva. Sobra de aproximadamente 4.743 m²/mês não aproveitada.

**Para melhorar:** Acelerar conversão comercial OU revisar dimensionamento da equipe.

**Caminhos viáveis:**

**Caminho A · Sinalizar pro Comercial · pipeline de fechamento**
- **Como:** Compartilhar capacidade real (32%) com time de vendas + projeção 13 semanas. Vendas prioriza fechamentos de Mai-Jun.
- **Custo do tempo:** 1 reunião + relatório semanal compartilhado
- **Impacto esperado:** Conversão acelerada de propostas pendentes · capacidade vai pra 60-70% em 2 meses [REVISAR]
- **Risco:** Pipe pode estar vazio · sinalizar não cria demanda do nada

**Caminho B · Reduzir prazo de aceitação de novos contratos**
- **Como:** Atualmente aceita-se com prazo X dias · reduzir pra X-15d, comunicando capacidade folgada.
- **Custo do tempo:** Alinhamento Comercial + ajuste no funil de proposta
- **Impacto esperado:** Atrai clientes com pressa · ganha 3-5 obras/mês [REVISAR]
- **Risco:** Concorrência pode usar prazo menor como atrativo · não vira diferencial sustentável

**Caminho C · Reavaliar dimensionamento da equipe**
- **Como:** Se ociosidade for estrutural (não pico), avaliar redução de aplicadores ou redistribuição regional.
- **Custo do tempo:** Decisão de RH · estratégica
- **Impacto esperado:** Reduz custo fixo · perde flexibilidade pra picos de demanda [REVISAR]
- **Risco:** Difícil reverter · perda de aplicadores treinados é cara

**Recomendação automática:** **Sinalizar pro Comercial + monitorar 4 semanas** antes de decidir reduzir prazo ou redimensionar.

---

**Para a próxima quinzena · 3 prioridades sugeridas:**
- [REVISAR · escolher 3 dos caminhos acima como prioridade do período]

---

## Conclusão Executiva

A operação fechou a quinzena demandando ação corretiva, com Score 47/100 e capacidade utilizada em 32%. Da carteira de **259** obras ativas no Painel, **184** foram diagnosticadas pela Análise do Painel (a diferença são obras em pós-entrega ou pausadas, fora desse recorte) — dessas, **107** sem problemas relevantes e **21** em estado crítico, concentração que não deve passar despercebida pela próxima quinzena. A categoria de problema dominante segue sendo **Comunicação** (77 obras), sinalizando onde a Gerência da Qualidade deve focar esforço analítico e de processo.

A leitura honesta deste relatório é que a folga de capacidade convive com fragilidade qualitativa em frentes específicas (cobertura de comunicação, infiltrações, alinhamento técnico-cliente). Os caminhos viáveis estão detalhados na Seção 9 com Como/Custo/Impacto/Risco — cabe à Diretoria selecionar 1-3 prioridades pra implementação na próxima quinzena.

> **Próximo ciclo de medição:** quinzena seguinte. As recomendações priorizadas no Brief Executivo deveriam mostrar tração mensurável neste mesmo relatório no próximo período.

---

## Anexo A · Obras do período

> Distribuição da carteira por status no fechamento da quinzena.

| Status | Quantidade |
|---|---|
| Em execução | 38 |
| Aguardando execução | 46 |
| Planejamento | 99 |
| Pausado | 5 |
| Aguardando clima | 3 |
| Em reparo | 21 |
| Em marcas / rolo / cera | 4 |
| Concluído | 235 |
| Finalizado | 547 |
| Cancelado | 33 |

> [REVISAR · Fase 1.1c] Listagem nominal de cada bucket (nomes dos clientes) — virá numa próxima iteração consultando o details/.

---

## Anexo B · Glossário

> Termos e sistemas mencionados neste relatório, pra leitor externo ou consultor que recebe o documento.

### Sistemas

- **Painel de Obras** (`cliente.monofloor.cloud`) · plataforma operacional canônica da Monofloor. Registro de cada obra com fases, equipe, datas, escopo, ocorrências. Refresh automático no relatório a cada 30 min.
- **Lab Orion** (`orion-pub.workers.dev`) · sistema piloto de Qualidade que cruza o que o **Painel** registra com o que os **grupos de WhatsApp/Telegram** das obras contam. Detecta divergências (status do Painel ≠ realidade narrada). Hoje em piloto com 10 obras.
- **KIRA WhatsApp** · resumo automático dos grupos de obra. Classifica clima (saudável/atenção/sem KIRA/retrabalho) e detecta alertas/pendências. Cobertura ≠ 100% — obras sem grupo monitorado são "cegueira" pra Qualidade.

### Métricas

- **Score Saúde Operacional** · indicador 0-100 calculado a partir de 4 componentes:
  1. **% obras zumbi** (CLIENTE FINALIZADO sem encerrar há mais de 90d)
  2. **% obras órfãs** (sem consultor responsável)
  3. **% obras com ciclo > 180d**
  4. **Lote AGEND.VT-AFERIÇÃO > 270d** (cauda longa)

  Faixas: **0-49 vermelho** (ação corretiva) · **50-69 amarelo** (atenção) · **70-100 verde** (saudável).

- **Capacidade utilizada** · razão entre m² em curso e capacidade mensal produtiva (m² aplicáveis com a equipe atual). Faixas: <40% subutilizada · 40-80% saudável · >80% próximo do limite.

- **Ciclo total mediano** · dias entre início e fim de obra (mediana). Meta 150d.

### Termos operacionais

- **Fluxo normal** · obras em execução conforme cronograma, sem retrabalho ativo.
- **Retrabalho · pós-entrega** · obras em status `reparo` ou `marcas_rolo_cera`. **Cronograma original já cumprido** — tratadas separadamente do atraso. Influências externas (cliente solicita reparo, exigência climática etc) podem disparar retrabalho sem indicar falha de execução.
- **Cluster paralisado** · obras em status `pausado` por motivo externo (cliente, clima, suprimento).
- **Detrator latente** (Orion) · obra com flag de risco jurídico/comercial baseado em histórico de quase-distrato ou reclamação técnica recente.
- **Equipe "fantasma"** (Seção 7) · equipe cadastrada com líder e obras sob liderança, mas com **zero aplicadores ativos** registrados. Geralmente significa que a equipe é gerenciada por encarregado oculto (sem cadastro formal) ou que o cadastro está defasado.
- **"Apenas CEP"** (Seção 5) · obras cujo cadastro de endereço no Painel tem só o CEP, sem cidade preenchida. Não é um lugar — é uma indicação de cadastro incompleto.
- **Concluído vs Finalizado** (Anexo A) · ambos são fases pós-execução, mas refletem etapas distintas do processo Painel: **Concluído** = obra terminou execução · **Finalizado** = obra encerrada formalmente após todas as pendências (incluindo cobrança, pós-venda). Por isso aparecem separadas.

### Fases típicas (Painel de Obras)

Sequência típica de uma obra nova até execução:
1. **AGEND. VT - AFERIÇÃO/ORIENTAÇÃO** — agendamento da Visita Técnica de Aferição
2. **PROJETOS · 1ª REVISÃO** — alinhamento de escopo
3. **CONFIRMAÇÕES OP 1** — confirmação operacional
4. **INFORMAÇÕES LOGÍSTICAS** — preparação de logística
5. **INDÚSTRIA · EM PRODUÇÃO** — fabricação do material
6. **LOGÍSTICA · EM ENTREGA** — transporte
7. **EM EXECUÇÃO** — aplicação na obra
8. **REVISÃO FINAL OP** — aferição final
9. **CLIENTE FINALIZADO** — entrega oficial

Pós-entrega: **REPARO**, **MARCAS / ROLO / CERA**.

### Pessoas-chave

- **Vitor Gomes** · Gerente da Qualidade · autor deste relatório.
- **Luana** e **Wesley** · consultoras (responsáveis pela conta da obra junto ao cliente).
- **Equipes de aplicação** · liderança operacional (Wiguens, João, Júlio, Gilmar, Egberto, Michael e líderes ocultos detectados pelo cruzamento Painel × escalação).

---

## Fontes e Disclaimer

**Fontes consultadas:**
- **Painel de Obras** (`cliente.monofloor.cloud`) · refresh automático 30min · snapshot `2026-05-05T23:53:58Z`
- **`/api/analise`** · diagnósticos textuais + categorização de problemas + teamPerformance · snapshot `2026-05-04T12:20:07.727981`
- **`/api/analytics/alerts`** · alertas estruturados (stage_delay + sem_equipe)
- **`/api/analytics/weekly-forecast`** · projeção de 13 semanas (starting + inExecution + capacity)
- **`/api/dashboard`** · ocorrências abertas + SLA + readiness
- **Lab Orion** (`orion-pub.workers.dev`) · varredura 12h e 18h · snapshot `2026-05-06T00:04:05Z`
- **KIRA WhatsApp** · agregado em `rodrigo-stats.json` · snapshot `2026-05-05T23:54:11Z`
- **Score Histórico** · `score-historico.json` (acumula 1 entry/dia desde 2026-05-01)

**Disclaimer:**
Análise concluída com base nos registros sistêmicos disponíveis ao Setor de Qualidade. Foco exclusivo nos dados, sem inferências sobre o cumprimento dos processos padrões estabelecidos pela operação. Casos de retrabalho e pós-entrega estão sujeitos a influências externas e são gerenciados dentro da margem de tolerância do processo. Heurísticas declaradas em cada seção quando aplicáveis.

---

*Relatório gerado pelo Sistema de Qualidade Monofloor · v0.2*
