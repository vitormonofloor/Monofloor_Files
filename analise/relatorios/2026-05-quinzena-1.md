# Relatório Quinzenal de Qualidade

**Período:** 20/04 a 04/05/2026 · Quinzena 1 de Maio
**Setor de Qualidade Monofloor · Vitor Gomes, Coordenador**
**Gerado em:** 04/05/2026 12:28

---

## 1 · Resumo Executivo

> [REVISAR · rascunho auto] Operação fechou a quinzena com Score 48/100 (zona vermelha), ▼ -1 ⚠ vs quinzena anterior. 262 obras ativas em fluxo, 37 em execução agora, 53 atrasadas e 25 em pós-entrega (reparo + marcas).

**Score Saúde Operacional:** 48/100 (▼ -1 ⚠)

| KPI | Atual | Anterior | Δ |
|---|---|---|---|
| Total ativas em fluxo | 262 | — | — |
| Em execução agora | 37 | — | — |
| Atrasadas (Painel) | 53 | — | — |
| Obras em retorno (reparo + marcas) | 25 | — | — |
| Capacidade utilizada | 35% | — | — |
| Score Saúde Operacional | 48/100 | 49 | ▼ -1 ⚠ |


**3 destaques do período:**
1. Operação a 35% da capacidade · espaço produtivo considerável (4.689 m²/mês livres)
2. Cobertura KIRA em 64.7% (132 de 204 obras) · melhor visibilidade de comunicação com cliente
3. 82 obras com clima saudável (62.1% das monitoradas pelo KIRA)

**3 alertas críticos:**
1. **JONATHAS DE ALMEIDA NUNES LUKAS** — Projeto deveria estar em "INFORMAÇÕES LOGÍSTICAS" mas está em "AGEND. VT - AFERIÇÃO/ORIENTAÇÃO" · **Causa:** fase atual atrás da prevista pelo cronograma · **→ Ação:** acelerar transição pra fase **INFORMAÇÕES LOGÍSTICAS**
2. **JONATHAS DE ALMEIDA NUNES LUKAS** — Projeto sem equipe definida a 0 dias do início · **Causa:** equipe ainda não alocada · **→ Ação:** alocar equipe pro projeto **JONATHAS DE ALMEIDA NUNES LUKAS**
3. **NINA RODRIGUES FIALDINI** — Projeto deveria estar em "INFORMAÇÕES LOGÍSTICAS" mas está em "PROJETOS  - 1ª REVISÃO" · **Causa:** fase atual atrás da prevista pelo cronograma · **→ Ação:** acelerar transição pra fase **INFORMAÇÕES LOGÍSTICAS**

---

## 2 · Indicadores do Período

| Indicador | Atual | Anterior | Δ | Fonte |
|---|---|---|---|---|
| Total ativas em fluxo | 262 | — | — | rodrigo-stats |
| Em execução agora | 37 | — | — | rodrigo-stats |
| Atrasadas (Painel) | 53 | — | — | analise |
| → Críticas | 21 | — | — | analise |
| → Alto risco | 27 | — | — | analise |
| Obras em retorno (reparo + marcas) | 25 | — | — | rodrigo-stats |
| Cluster paralisado (Q2) | 5 | — | — | rodrigo-stats |
| Score Saúde Operacional | 48/100 | 49 | ▼ -1 ⚠ | headline |
| TEMPO médio de ciclo | 172d | — | — | rodrigo-stats |
| VOLUME m² em curso | 4.507 | — | — | rodrigo-stats |
| Capacidade utilizada | 35% | — | — | rodrigo-stats |
| A INICIAR firmadas (30d) | 0 | — | — | rodrigo-stats |
| Cobertura KIRA | 64.7% | — | — | rodrigo-stats |
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
- **Cobertura:** 132 de 204 obras ativas têm grupo de WhatsApp acompanhado (64.7%)
- **Saudável:** 82 (62.1% das monitoradas)
- **Em atenção:** 50
- **Sem KIRA:** 72 *(cegueira — obras que pra Qualidade são silêncio)*

> [REVISAR] Comentário narrativo de 1-2 frases sobre o que esses números contam juntos.

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

---

## 5 · Retrabalho & Pós-entrega

> Obras em **reparo** e **marcas_rolo_cera** são pós-entrega — cronograma original já cumprido. Mostradas separadamente do atraso.

| Indicador | Atual | Anterior | Δ |
|---|---|---|---|
| Obras em retorno (total) | 25 | — | — |
| → em reparo | 21 | — | — |
| → em marcas / rolo / cera | 4 | — | — |
| % da carteira ativa | 9.5% | — | — |

### Categorias de problema relacionadas a retrabalho

- **Material**: 64 obras (sendo 8 críticas)
- **Infiltração**: 48 obras (sendo 23 críticas)
- **Manchas/Defeitos**: 41 obras (sendo 8 críticas)
- **Substrato**: 27 obras (sendo 2 críticas)

> Fonte: `/api/analise`. Cada categoria conta obras com problema reportado no Painel — ajuda a identificar **padrões de causa-raiz** sem coleta manual.

> [REVISAR] Hipótese sobre a categoria dominante · qual ação pra reduzir?

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

---

## 7 · Capacidade × Demanda

> Pergunta direta: *aceitamos mais obras ou estamos no limite?*

| Indicador | Atual | Anterior | Δ |
|---|---|---|---|
| Capacidade mensal produtiva | 9.196 m²/mês | — | — |
| VOLUME m² em curso | 4.507 m² | — | — |
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

---

## 10 · Conclusões e Recomendações

1. **Comunicação** é a categoria de problema com maior volume — 77 obras (20 críticas)
   *Causa provável:* padrão recorrente em comunicação pode indicar gargalo sistêmico
   *→ Ação sugerida:* investigar fluxo específico de **Comunicação** com a equipe operacional · validar se há ação preventiva possível

2. Capacidade utilizada em apenas 35%
   *Causa provável:* demanda atual abaixo da capacidade instalada
   *→ Ação sugerida:* alinhar com Comercial pra acelerar fechamentos · ou reavaliar dimensionamento

3. **72 obras sem KIRA** (sem grupo de WhatsApp acompanhado)
   *Causa provável:* cegueira da Qualidade · obras invisíveis pra detecção de problemas via grupo
   *→ Ação sugerida:* padronizar criação de grupo desde o início da obra · meta: zerar cegueira

4. 21 obras em estado crítico (53 no total atrasadas)
   *Causa provável:* concentração de problemas que demanda atenção imediata
   *→ Ação sugerida:* priorizar contato direto com as **top 5 mais antigas** (ver Seção 4) · validar se demandam intervenção da Coordenação


**Para a próxima quinzena:**
- [REVISAR · 3 prioridades baseadas nos pontos acima]

---

## Anexo A · Obras do período

> Distribuição da carteira por status no fechamento da quinzena.

| Status | Quantidade |
|---|---|
| Em execução | 37 |
| Aguardando execução | 47 |
| Planejamento | 105 |
| Pausado | 5 |
| Aguardando clima | 3 |
| Em reparo | 21 |
| Em marcas / rolo / cera | 4 |
| Concluído | 235 |
| Finalizado | 541 |
| Cancelado | 33 |

> [REVISAR · Fase 1.1c] Listagem nominal de cada bucket (nomes dos clientes) — virá numa próxima iteração consultando o details/.

---

## Fontes e Disclaimer

**Fontes consultadas:**
- **Painel de Obras** (`cliente.monofloor.cloud`) · refresh automático 30min · snapshot `2026-05-04T13:09:20Z`
- **`/api/analise`** · diagnósticos textuais + categorização de problemas + teamPerformance · snapshot `2026-05-04T12:20:07.727981`
- **`/api/analytics/alerts`** · alertas estruturados (stage_delay + sem_equipe)
- **`/api/analytics/weekly-forecast`** · projeção de 13 semanas (starting + inExecution + capacity)
- **`/api/dashboard`** · ocorrências abertas + SLA + readiness
- **Lab Orion** (`orion-pub.workers.dev`) · varredura 12h e 18h · snapshot `2026-05-04T15:00:44Z`
- **KIRA WhatsApp** · agregado em `rodrigo-stats.json` · snapshot `2026-05-04T13:09:31Z`
- **Score Histórico** · `score-historico.json` (acumula 1 entry/dia desde 2026-05-01)

**Disclaimer:**
Análise concluída com base nos registros sistêmicos disponíveis ao Setor de Qualidade. Foco exclusivo nos dados, sem inferências sobre o cumprimento dos processos padrões estabelecidos pela operação. Casos de retrabalho e pós-entrega estão sujeitos a influências externas e são gerenciados dentro da margem de tolerância do processo. Heurísticas declaradas em cada seção quando aplicáveis.

---

*Relatório gerado pelo Sistema de Qualidade Monofloor · v0.2*
