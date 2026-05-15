# 🎯 RETOMAR TIMELINE · contexto rápido pra qualquer agente

> **Última atualização:** 2026-05-15 · assertividade 94% + pre_contrato + 6a fonte materiais + consultor normalizado + alerta parada + Camada 1 benchmark

---

## 🆕 SESSÃO 2026-05-15 · O QUE FECHAMOS HOJE

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
