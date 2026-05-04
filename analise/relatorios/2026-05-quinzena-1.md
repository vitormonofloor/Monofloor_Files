# Relatório Quinzenal de Qualidade

**Período:** 20/04 a 04/05/2026 · Quinzena 1 de Maio
**Setor de Qualidade Monofloor · Vitor Gomes, Coordenador**
**Gerado em:** 04/05/2026 14:53

---

## 1 · Resumo Executivo

> [REVISAR · rascunho auto] Operação fechou a quinzena com Score 48/100 (zona vermelha), ▼ -1 ⚠ vs quinzena anterior. 260 obras ativas em fluxo, 36 em execução agora, 53 atrasadas e 27 em pós-entrega (reparo + marcas).

**Score Saúde Operacional:** 48/100 (▼ -1 ⚠)

| KPI | Atual | Anterior | Δ |
|---|---|---|---|
| Total ativas em fluxo | 260 | — | — |
| Em execução agora | 36 | — | — |
| Atrasadas (Painel) | 53 | — | — |
| Obras em retorno (reparo + marcas) | 27 | — | — |
| Capacidade utilizada | 35% | — | — |
| Score Saúde Operacional | 48/100 | 49 | ▼ -1 ⚠ |


**3 destaques do período:**
1. Operação a 35% da capacidade · espaço produtivo considerável (4.791 m²/mês livres)
2. Cobertura KIRA em 64.5% (129 de 200 obras) · melhor visibilidade de comunicação com cliente
3. 81 obras com clima saudável (62.8% das monitoradas pelo KIRA)

**3 alertas críticos:**
1. **JONATHAS DE ALMEIDA NUNES LUKAS** — Projeto deveria estar em "INFORMAÇÕES LOGÍSTICAS" mas está em "AGEND. VT - AFERIÇÃO/ORIENTAÇÃO" · **Causa:** fase atual atrás da prevista pelo cronograma · **→ Ação:** acelerar transição pra fase **INFORMAÇÕES LOGÍSTICAS**
2. **JONATHAS DE ALMEIDA NUNES LUKAS** — Projeto sem equipe definida a 0 dias do início · **Causa:** equipe ainda não alocada · **→ Ação:** alocar equipe pro projeto **JONATHAS DE ALMEIDA NUNES LUKAS**
3. **NINA RODRIGUES FIALDINI** — Projeto deveria estar em "INFORMAÇÕES LOGÍSTICAS" mas está em "PROJETOS  - 1ª REVISÃO" · **Causa:** fase atual atrás da prevista pelo cronograma · **→ Ação:** acelerar transição pra fase **INFORMAÇÕES LOGÍSTICAS**

---

## 2 · Indicadores do Período

| Indicador | Atual | Anterior | Δ | Fonte |
|---|---|---|---|---|
| Total ativas em fluxo | 260 | — | — | rodrigo-stats |
| Em execução agora | 36 | — | — | rodrigo-stats |
| Atrasadas (Painel) | 53 | — | — | analise |
| → Críticas | 21 | — | — | analise |
| → Alto risco | 27 | — | — | analise |
| Obras em retorno (reparo + marcas) | 27 | — | — | rodrigo-stats |
| Cluster paralisado (Q2) | 5 | — | — | rodrigo-stats |
| Score Saúde Operacional | 48/100 | 49 | ▼ -1 ⚠ | headline |
| TEMPO médio de ciclo | 172d | — | — | rodrigo-stats |
| VOLUME m² em curso | 4.405 | — | — | rodrigo-stats |
| Capacidade utilizada | 35% | — | — | rodrigo-stats |
| A INICIAR firmadas (30d) | 0 | — | — | rodrigo-stats |
| Cobertura KIRA | 64.5% | — | — | rodrigo-stats |
| Ocorrências abertas | 950 | — | — | dashboard |

> Deltas vs quinzena anterior em construção · score-historico ainda acumulando (iniciado 2026-05-01).

---

## 3 · Diagnóstico Operacional

### Saúde geral da carteira
- **184** obras ativas analisadas
- **107** sem problemas relevantes
- **21** críticas + **27** em alto risco
- **53** com atraso identificado pelo Painel

### Top 3 categorias de problema (excluindo "Outros")
- **Comunicação** — 77 obras (20 críticas)
- **Material** — 64 obras (8 críticas)
- **Infiltração** — 48 obras (23 críticas)

> Categorização vem do `/api/analise` do Painel — agrupamento automático que substitui o trabalho manual de catalogar causa-raiz.

### Pulso KIRA · comunicação com cliente
- **Cobertura:** 129 de 200 obras ativas têm grupo de WhatsApp acompanhado (64.5%)
- **Saudável:** 81 (62.8% das monitoradas)
- **Em atenção:** 48
- **Sem KIRA:** 71 *(cegueira — obras que pra Qualidade são silêncio)*

> [REVISAR] Comentário narrativo de 1-2 frases sobre o que esses números contam juntos.

> 💡 **Caminhos pra reduzir cegueira KIRA →** ver **Seção 10 · Conclusões** (receita "cegueira_kira" com 3 caminhos detalhados).

---

## 4 · Análise de Atrasos · caso a caso

> Top 5 obras mais atrasadas no momento. Diagnóstico textual extraído direto do Painel (`/api/analise`).

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
- 🎯 **Triagem semanal das críticas** — toda segunda, ranking por dias parados → top 5 vão pra reunião de Coordenação
- 🚨 **Escalação automática D+30** — obra que passa 30d na mesma fase notifica Coordenador + cliente recebe contato
- 📋 **Checklist proativo de pré-execução** — confirmar equipe + cor + VT *antes* da data prevista, não no dia
- 💬 **Comunicação proativa com cliente** — quando atraso for inevitável, antecipar (em vez de cliente cobrar)

> [REVISAR] Quais desses caminhos fazem sentido pro período atual? Marcar 1-2 e a gente promove pra Seção 10 com Como/Custo/Impacto/Risco completos.

---

## 5 · Retrabalho & Pós-entrega

> Obras em **reparo** e **marcas_rolo_cera** são pós-entrega — cronograma original já cumprido. Mostradas separadamente do atraso.

| Indicador | Atual | Anterior | Δ |
|---|---|---|---|
| Obras em retorno (total) | 27 | — | — |
| → em reparo | 23 | — | — |
| → em marcas / rolo / cera | 4 | — | — |
| % da carteira ativa | 10.4% | — | — |

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
- ⚖ **Mediação preventiva** — obras com flag detrator_latente recebem visita do Coordenador antes de virar caso jurídico

> [REVISAR] Categoria Infiltração tem 47% críticas (taxa MUITO acima da média) — recomendo priorizar Auditoria técnica. Ver Seção 10 pra caminhos detalhados (Como/Custo/Impacto/Risco).

---

## 6 · Geografia

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

## 7 · Capacidade × Demanda

> Pergunta direta: *aceitamos mais obras ou estamos no limite?*

| Indicador | Atual | Anterior | Δ |
|---|---|---|---|
| Capacidade mensal produtiva | 9.196 m²/mês | — | — |
| VOLUME m² em curso | 4.405 m² | — | — |
| Capacidade utilizada | 35% | — | — |
| A INICIAR firmadas (30d) | 0 obras | — | — |

**Diagnóstico atual:** Operação a 35% da capacidade mensal · sobra produtiva considerável. **→ Comercial pode acelerar fechamentos** · cabe sinalizar pro time de vendas.

### Projeção pra próxima semana (2026-05-04 a 2026-05-11)

| Indicador | Próxima semana |
|---|---|
| Obras iniciando | 2 (984 m²) |
| Em execução | 8 (2.651 m²) |
| Capacidade prevista | 25% |

> Fonte: `/api/analytics/weekly-forecast` · projeção baseada em data_de_entrada firmada.

> 💡 **Caminhos pra equilibrar capacidade vs demanda →** ver **Seção 10 · Conclusões** (receita "capacidade_ociosa" com 3 caminhos detalhados).

---

## 8 · Análise por Equipe

### Consultores · responsáveis pela conta

| Consultor | Ativos | Com problema | Atrasados | % com problema |
|---|---|---|---|---|
| Luana Patricia De Andrade Lima | 84 | 34 | 17 | 40.5% |
| Wesley Matheus De Carvalho | 61 | 26 | 9 | 42.6% |
| Pedro Alexandre Santana | 7 | 1 | 0 | 14.3% |
| Thaísa De Lara Barbosa | 1 | 1 | 1 | 100% |
| Pedro Marçal | 1 | 0 | 0 | 0% |
| Renata Garcia Penna | 1 | 0 | 0 | 0% |

> Fonte: `/api/analise.teamPerformance`. **% com problema** = projetos com qualquer problema reportado / projetos ativos.

### Supervisão de equipe (linha de frente)

| Supervisor / Equipe | Obras ativas |
|---|---|
| Equipe Wiguens | — |
| Equipe João | — |
| Equipe Gilmar | — |
| Equipe Júlio | — |
| Equipe Egberto | — |
| Equipe Michael | — |


> [REVISAR] Comentário curto sobre destaques (positivos e alertas).

### Caminhos a explorar · pra balanço de carga e qualidade
- ⚖ **Análise de perfil de carteira** — comparar Luana × Wesley considerando complexidade média, valor médio, dispersão geográfica (não só quantidade)
- 🤝 **1:1 quinzenal de carteira** — Coordenação revisa as obras de risco com cada consultora (formato fixo, 30min)
- 📊 **Meta de obras em paralelo** — estabelecer máx por consultora (ex: 60 ativas) · acima disso, desacelerar entrada de novas
- 🎓 **Capacitação cruzada** — Luana e Wesley trocam casos pra aprender com diferenças de abordagem

> [REVISAR] Distribuição atual: Luana 84 ativas / Wesley 61. Vale checar se essa diferença é histórica ou recente.

---

## 9 · Sinais Painel × Telegram (Lab Orion)

**Total de obras analisadas pelo Orion:** 10 (piloto)

**Resumo do Orion:** Das 10 obras analisadas, 6 têm status do painel coerente com a narrativa Telegram e 4 estão desatualizadas — nenhuma em abandono e nenhum detrator manifesto. Cinco obras estão em ciclo de retorno técnico (patologia, retrabalho de acabamento ou reparo de dano), três em planejamento pré-execução com aplicador 'a definir', uma em fim de execução prestes a virar concluída (Luis Fernando) e uma em transição de pausa para execução (Amendoeiras). Quatro obras carregam o flag detrator_latente por histór...

### Top 5 obras com flags ou divergências

| Obra | Painel diz | Tom Telegram | Veredicto |
|---|---|---|---|
| GETULIO TURATTI OST | marcas_rolo_cera | tom: tenso | coerente |
| REPULLO ASSESSORIA EM INFORMATICA LTDA | planejamento | tom: ativo | coerente |
| DANIEL BECKER | aguardando_execucao | tom: ativo | status_desatualizado |
| MICHELLE CRISTINA FREITAS GARDENAL | planejamento | tom: ativo | coerente |
| AMENDOEIRAS SOCIEDADE DE PROPOSITO ESPECIFICO LTDA | pausado | tom: ativo | status_desatualizado |


> [REVISAR] Padrão observado · se houver divergência sistemática, declarar hipótese + ação.

### Caminhos a explorar · pra reduzir divergências e expandir o Orion
- 🔄 **Padronizar quem atualiza o Painel** — definir formalmente: técnico atualiza fase, consultora atualiza status. Hoje há sobreposição
- ⚠ **Auditoria semanal de detrator_latente** — toda semana, Coordenação revisa as obras com flag · age antes de virar caso
- 📈 **Expandir piloto Orion** — 10 → 50 obras em 3 meses · ganha massa crítica pra detectar padrões sistêmicos
- 🧪 **A/B de qualidade Painel × WhatsApp** — quando divergir, qual fonte está certa? Auditoria mensal da amostra

> [REVISAR] Lab Orion ainda em piloto (10 obras) · vale acelerar expansão pra ganhar tração nos sinais?

---

## 10 · Conclusões e Recomendações

> Análise propositiva: cada problema crítico detectado vem com diagnóstico, caminhos viáveis (Como · Custo · Impacto · Risco) e recomendação combinada. Números marcados [REVISAR] são chutes que dependem do conhecimento operacional do Vitor pra calibrar.

### Score Saúde abaixo da zona saudável

**Diagnóstico**
Score em 48/100 (zona vermelha · meta ≥70). Componentes que puxam pra baixo:
- Ciclo total mediano em 215d (meta 150d) — 43% acima da meta
- 18.8% de obras zumbi (CLIENTE FINALIZADO sem encerrar)
- 14.0% órfãs (sem consultor responsável)
- 21 obras na cauda longa AGEND.VT-AFERIÇÃO (>270d)

**Para melhorar:** Reduzir o ciclo total e fechar zumbis acumuladas.

**Caminhos viáveis:**

**Caminho A · Mutirão de zumbis**
- **Como:** Força-tarefa de 2 semanas pra encerrar as obras presas em CLIENTE FINALIZADO há mais de 90 dias.
- **Custo do tempo:** ~10h/semana da consultoria por 2 semanas
- **Impacto esperado:** zumbi_pct cai de 18.8% para ~5% · Score sobe ~3-4 pontos [REVISAR número]
- **Risco:** Algumas zumbis podem ter pendência real não-mapeada (descobrir não é problema, mas ajusta a expectativa)

**Caminho B · Atacar gargalo AGEND.VT-AFERIÇÃO**
- **Como:** Revisar SLA de Visita Técnica + reorganizar alocação Luana/Wesley pra desbloquear a cauda longa.
- **Custo do tempo:** Organizacional · alinhamento de agenda da consultoria
- **Impacto esperado:** Ciclo mediano cai 215d → ~190d · Score sobe ~5 pontos [REVISAR número]
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
Operação a 35% da capacidade mensal · 4.405 m² em curso vs 9.196 m²/mês de capacidade produtiva. Sobra de aproximadamente 4.791 m²/mês não aproveitada.

**Para melhorar:** Acelerar conversão comercial OU revisar dimensionamento da equipe.

**Caminhos viáveis:**

**Caminho A · Sinalizar pro Comercial · pipeline de fechamento**
- **Como:** Compartilhar capacidade real (35%) com time de vendas + projeção 13 semanas. Vendas prioriza fechamentos de Mai-Jun.
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

## Anexo A · Obras do período

> Distribuição da carteira por status no fechamento da quinzena.

| Status | Quantidade |
|---|---|
| Em execução | 36 |
| Aguardando execução | 47 |
| Planejamento | 102 |
| Pausado | 5 |
| Aguardando clima | 3 |
| Em reparo | 23 |
| Em marcas / rolo / cera | 4 |
| Concluído | 235 |
| Finalizado | 543 |
| Cancelado | 33 |

> [REVISAR · Fase 1.1c] Listagem nominal de cada bucket (nomes dos clientes) — virá numa próxima iteração consultando o details/.

---

## Fontes e Disclaimer

**Fontes consultadas:**
- **Painel de Obras** (`cliente.monofloor.cloud`) · refresh automático 30min · snapshot `2026-05-04T15:31:20Z`
- **`/api/analise`** · diagnósticos textuais + categorização de problemas + teamPerformance · snapshot `2026-05-04T12:20:07.727981`
- **`/api/analytics/alerts`** · alertas estruturados (stage_delay + sem_equipe)
- **`/api/analytics/weekly-forecast`** · projeção de 13 semanas (starting + inExecution + capacity)
- **`/api/dashboard`** · ocorrências abertas + SLA + readiness
- **Lab Orion** (`orion-pub.workers.dev`) · varredura 12h e 18h · snapshot `2026-05-04T17:36:10Z`
- **KIRA WhatsApp** · agregado em `rodrigo-stats.json` · snapshot `2026-05-04T15:31:31Z`
- **Score Histórico** · `score-historico.json` (acumula 1 entry/dia desde 2026-05-01)

**Disclaimer:**
Análise concluída com base nos registros sistêmicos disponíveis ao Setor de Qualidade. Foco exclusivo nos dados, sem inferências sobre o cumprimento dos processos padrões estabelecidos pela operação. Casos de retrabalho e pós-entrega estão sujeitos a influências externas e são gerenciados dentro da margem de tolerância do processo. Heurísticas declaradas em cada seção quando aplicáveis.

---

*Relatório gerado pelo Sistema de Qualidade Monofloor · v0.2*
