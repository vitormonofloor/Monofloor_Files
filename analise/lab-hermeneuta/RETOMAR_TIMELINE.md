# 🎯 RETOMAR TIMELINE · contexto rápido pra qualquer agente

> **Última atualização:** 2026-05-20 · Pipeline unificado + snapshot semanal + Timeline virou ferramenta viva (fetch dinâmico)

---

## 🆕 SESSÃO 2026-05-20 · O QUE FECHAMOS HOJE

### Pipeline unificado — ENTREGUE
- ✅ `analise/dados/pipeline_unificado.py` — lê 3 fontes (dashboard-data, timeline_obras, jornadas), cruza por obra_id
- ✅ CONSULTOR_ALIAS normaliza variantes → nomes canônicos (Wesley, Luana, Pedro, etc.)
- ✅ Calcula faixa metragem, todos indicadores com fórmula auditável (numerador/denominador)
- ✅ Output: `analise/dados/analise-unificada.json` (205KB, 216 obras, 204 com 3 fontes)
- ✅ `validar_sanidade()` no final — guardrail automático

### Snapshot semanal — ENTREGUE
- ✅ `analise/dados/snapshot_semanal.py` — salva cópia datada em `snapshots-unificados/YYYY-MM-DD.json`
- ✅ Delta vs snapshot anterior (radar, portfolio, retrabalho por consultor)
- ✅ Primeiro snapshot salvo: `2026-05-20.json`

### Timeline como ferramenta viva — ENTREGUE
- ✅ `analise/mockup-timeline-v2.html` reescrito: fetch de `dados/analise-unificada.json`
- ✅ Todas seções renderizadas dinamicamente (trail, signals, radar, eixos, atenção, risco, cross-obra, aside)
- ✅ Animações preservadas (trail reveal, radar expand+breathe, eixo entrance, cross scroll-triggered)
- ✅ Zero hardcode — tudo vem do JSON
- ✅ Pendente: verificação visual completa pelo Vitor

### Dados evoluíram vs sessão anterior
- Total: 214→216 obras, retrabalho: 21→24, Wesley retrab: 9→14 (43%→58%)
- Sem consultor: 41→15 (normalização CONSULTOR_ALIAS absorveu variantes)
- Faixas agora incluem G/GG/XG (m2 atualizado pelo dashboard)

### Memórias atualizadas
- `project_arquitetura_4_camadas.md` — pipeline e snapshot marcados como ENTREGUE

### Pendências pra próxima sessão

| Ordem | Item | Custo est. |
|---|---|---|
| 1 | Verificação visual completa da Timeline live | ~30min |
| 2 | Panorama mensal (evolução carteira mês a mês) | ~1h |
| 3 | Camada 2 — Triângulo de consistência material | ~2h |
| 4 | Camada 3 — Score preditivo de risco (obras ativas) | ~2h |
| 5 | Cross-obra: padrões por consultor × tipo problema | ~1h |
| 6 | Relatório narrativo automático (ideia #6 do brainstorm) | ~2h |

### Comando pra retomar (cole no Claude Code)

```
Lê analise/lab-hermeneuta/RETOMAR_TIMELINE.md primeiro · seção topo "SESSÃO 2026-05-20". Pipeline unificado entregue (analise/dados/pipeline_unificado.py → analise-unificada.json). Snapshot semanal entregue. Timeline HTML reescrita como ferramenta viva (fetch dinâmico). Memória: project_arquitetura_4_camadas.md. 216 obras, radar auditável. Próximo passo: verificação visual + panorama mensal (~1h).
```

---

## 📜 SESSÃO 2026-05-19 · O QUE FECHAMOS

### Timeline v2 — mockup alimentado com dados 100% reais
- ✅ `analise/mockup-timeline-v2.html` — 30+ pontos de dados substituídos, auditoria 30/30
- ✅ Trail SVG: 6 nós reais (Planej.88 → Contrato19 → Ag.Exec43 → EmExec36 → Retrab21 → Parado7)
- ✅ Signals: Idade 179d, Gargalo PLANEJ., Silêncio 8.4%, Acima benchmark 53.4%
- ✅ Radar com fórmulas declaráveis: Tempo 39.7% (<=150d/total), Fluxo 91.6% (sem alerta/total), Qualidade 90.2% (sem retrab/total), Risco 78.4% (baixo+mod/scored)
- ✅ Eixo cards com dados reais: faixas PP/P/M, 18 alertas breakdown, 21 obras retrabalho, 40 alto+crítico
- ✅ Tabela atenção: 5 obras críticas reais (Flávia Augusta, Priscila Miranda, Glaucia Alves, Monalisa, Mariana Loiacono)
- ✅ Cross-obras: Wesley 43% retrabalho (9/21), Sem consultor 41 obras 84d (são as MAIS NOVAS), Planejamento gargalo 88 vs 36

### Arquitetura 4 camadas definida
- ✅ Central (snapshot executivo) → Orion (per-obra detalhe) → Jornada (per-obra narrativa) → Timeline (análise agregada)
- ✅ Cada camada com papel exclusivo, sem sobreposição
- ✅ Princípio: todo score/métrica = fórmula auditável dos dados, nunca heurística do modelo

### Correções durante auditoria
- ✅ Faixa m2=0 classificava como PP → guard `if m2 <= 0: return '?'`
- ✅ PP benchmark 175d→179d, P 178d→180d após fix (merge m2 de 3 fontes)
- ✅ Benchmark % recalculado: P +1%, M +19% (base PP 179d)
- ✅ Discrepância timeline 215 vs dashboard 214 identificada (GUILHERME HAIDAR extra)

### Brainstorm estratégico — 10 ideias para próximas sessões

**Previsão:** 1) Radar trajetória (velocidade risco), 2) Simulador "e se" (mover obras/consultores)
**Padrões ocultos:** 3) DNA obra (clustering), 4) Padrão recuperação, 5) Previsibilidade por consultor
**Visão executiva:** 6) Relatório narrativo automático (semanal), 7) Dupla lente (Central vs Timeline)
**Operação:** 8) Throughput real (fila planejamento), 9) Dispersão (entropia), 10) Sazonalidade por mês

### Memórias novas
- `feedback_scores_derivados_dados.md` — todo score precisa fórmula auditável
- `project_arquitetura_4_camadas.md` — 4 camadas + pipeline unificado + 10 ideias

### Pendências pra próxima sessão

| Ordem | Item | Custo est. |
|---|---|---|
| 1 | Pipeline unificado (1 script Python → analise-unificada.json) | ~2h |
| 2 | Snapshots semanais (salvar estado toda segunda, habilita tendência) | ~1h |
| 3 | Panorama mensal (evolução carteira mês a mês) | ~1h |
| 4 | Camada 2 — Triângulo de consistência material | ~2h |
| 5 | Camada 3 — Score preditivo de risco (obras ativas) | ~2h |
| 6 | Cross-obra: padrões por consultor × tipo problema | ~1h |
| 7 | Relatório narrativo automático (ideia #6 do brainstorm) | ~2h |

### Comando pra retomar (cole no Claude Code)

```
Lê analise/lab-hermeneuta/RETOMAR_TIMELINE.md primeiro · seção topo "SESSÃO 2026-05-19". Memórias: project_arquitetura_4_camadas.md, feedback_scores_derivados_dados.md. Timeline v2 mockup pronto com dados reais (30/30 auditoria). Próximo passo: pipeline unificado (~2h) ou snapshots semanais (~1h). 214 obras dashboard, radar com fórmulas declaráveis (Tempo 39.7%, Fluxo 91.6%, Qualidade 90.2%, Risco 78.4%). 10 ideias estratégicas documentadas na memória.
```

---

## 📜 SESSÃO 2026-05-15 · Assertividade 94% + Camada 1 benchmark

### Assertividade 84% → 93.9% (Parte 1)
- ✅ `classificar_obra()` usa `fase_atual_painel` como override (status stale → entrega_limpa/com_retrabalho)
- ✅ Consultor fallback `monof.get("consultor") or monof.get("operacoes")`
- ✅ tempo_total fallback usa HOJE_DATE para obras ativas sem fim calculado
- ✅ `auditar_assertividade.py` — script novo com 10 critérios, campos controlados 99.2%

### Camada 1 — Benchmark por faixa de metragem ✅
- ✅ 6 faixas: PP(<60) P(60-100) M(100-150) G(150-220) GG(220-300) XG(300+)
- ✅ Bloco visual no drawer + badge de faixa na sidebar
- ✅ Insight: PP tem 66% retrabalho — o dobro das faixas maiores

### Qualidade dos dados do pipeline Timeline (Parte 2)
- ✅ Rename `indeterminada`/`sem dados` → `pre_contrato`/`Pré-contrato` (pipeline + HTML + CSS azul #3a5a8c + filtros)
- ✅ Normalização consultor: `CONSULTOR_ALIAS` + `_fix_latin1_in_utf8()` + limpeza `[]` → 8 consultores limpos
- ✅ 6a fonte classificação origem: `tipoSuperficie=Reaplicação` no endpoint `/materiais` (corrigiu PAULA DAYAN + BERNARDO MAGALHÃES)
- ✅ 7 obras nova baixa-confiança auditadas: 2 reclassificadas, 5 confirmadas
- ✅ Distribuição final: 116 nova · 82 retorno · 10 pre_contrato · 9 incerta (217 total)

### Detecção de obras paradas
- ✅ `estagio` derivado de marcos (em_execucao/equipe_em_obra/pos_vt/pos_contrato/com_atividade/sem_marcos)
- ✅ `dias_inativo` + `ultima_atividade` timezone-aware
- ✅ `alerta_parada` >30d: 16 obras (2 contrato_sem_avanço + 14 obra_dormindo)
- ✅ Badge visual com pulso no HTML (vermelho >60d, amarelo 30-60d)

### Bugs auditoria 2026-05-12 — TODOS RESOLVIDOS
- ✅ 5 fixes aplicados · 2 falsos positivos · auditoria encerrada

### Memórias novas/atualizadas
- `reference_faixas_metragem.md` · `project_macrodados_3_camadas.md` · `feedback_dados_limpos_antes_cruzar.md` (novos)
- `project_auditoria_20_obras_2026_05_12.md` (atualizado: FECHADO)

### Pendências pra próxima sessão

| Ordem | Item | Custo est. |
|---|---|---|
| 1 | Panorama mensal (evolução carteira mês a mês) | ~1h |
| 2 | Camada 2 — Triângulo de consistência material | ~2h |
| 3 | Camada 3 — Score preditivo de risco (obras ativas) | ~2h |
| 4 | Cross-obra: padrões por consultor × tipo problema | ~1h |
| 5 | Cross-obra: tempo entre marcos × faixa metragem | ~1h |

### Comando pra retomar (cole no Claude Code)

```
Lê analise/lab-hermeneuta/RETOMAR_TIMELINE.md primeiro · seção topo "SESSÃO 2026-05-15". Memórias: project_macrodados_3_camadas.md, reference_faixas_metragem.md. Próximo passo: panorama mensal (~1h) e depois Camada 2 (consumo material). 217 obras com dados assertivos (116 nova, 82 retorno, 10 pre_contrato, 9 incerta). Pipeline timeline_10obras.py já consulta /materiais.
```

---

## 📜 SESSÃO 2026-05-14 · Entrega completa do fluxo operacional

- Refoco: doc-âncora `_projeto/ESCOPO_TIMELINE.md`, escopo E1-E5 amarrado
- Diagnóstico narrativo dinâmico (4 blocos) na Tela 1
- Badge perfil A-F + barra de fluxo (8 etapas) por obra na Tela 2
- Filtros por perfil integrados · stats: 4% caminho feliz, 80% reprovação

---

## 📜 SESSÃO 2026-05-13 · Caminhos A, B e C fechados · D descartado

- A: 7 padrões testados nas 1262 obras · 44% paralisação silenciosa
- B: `jornada-obras-qualidade.html` na Central · 6 cards + 3 achados
- C: `gerar_alertas_jornada.py` → 52 alertas (15 crit)

---

## 📜 SESSÃO 2026-05-12 · Bancada de Leituras

- 10 obras destrinchadas · 7 padrões cross-obras · bancada `leituras.html`
- Agente global `analista-jornada-obras` com 5 modos

---

## 📜 SESSÃO 2026-05-07 · Pipeline em produção

- 222 obras vivas · 2295 marcos · cron 5x/dia · manifest incremental
- 1042 obras históricas (frozen)

---

## Arquivos-chave deste terminal

| Arquivo | Função |
|---|---|
| `agente/timeline_10obras.py` | Pipeline principal · 6 fontes classificação · consultor · estagio · alerta |
| `agente/gerar_html_timelines.py` | Gerador HTML acordeão · badges · filtros · alerta parada |
| `agente/gerar_jornada.py` | Jornada completa · faixas metragem · benchmark · assertividade |
| `agente/auditar_assertividade.py` | Audit script · 10 critérios |
| `dados/timeline_obras.json` | Output 217 obras vivas |
| `dados/timeline_obras.html` | HTML acordeão |
| `dados/manifest_obras.json` | Cache incremental (deletar = reprocessamento total ~166s) |

## DNA do projeto

- **Standalone** · não toca em arquivos do Lab Orion (`varredura.py`, `jornadas.json`, `index.html`)
- **Sem IA · sem token · custo zero** · puro Python regex + HTTP + pdfplumber
- **Tom diplomático** · "Painel registra X · Telegram indica Y"
