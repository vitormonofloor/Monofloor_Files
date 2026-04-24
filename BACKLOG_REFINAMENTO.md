# Backlog de Refinamento — Central de Qualidade

> Consolidação das varreduras de auditoria. Atualizar conforme itens forem concluídos.
> Última atualização: **2026-04-24** (pós commits `348a27f` e `8cd3445`)

## 📊 Placar atual

| Status | Qtd |
|---|---|
| ✅ Prontos | 7 |
| ⚠️ Parciais | 4 |
| 🔴 Pendentes | 4 |
| **Total** | **15** |

---

## ✅ PRONTOS (7)

### Item 3 — `stamp-now` lê snapshot_ts
- **Onde:** `analise/dashboard.html` L2243
- **Validação:** usa `AGG.snapshot_date`, não `new Date()` do cliente
- **Commit:** `8fbc69c`

### Item 5 — Plano: "Etapa 2" vs 4 barras 100%
- **Onde:** `analise/plano.html` L135
- **Validação:** label agora diz "Concluído — 4 etapas finalizadas"
- **Commit:** `8fbc69c`

### Item 7 — Remover `javascript:void(0)` + âncoras vazias
- **Onde:** `indicadores-v2.html`
- **Validação:** grep por `javascript:void(0)` não retorna; âncoras `#sec-*` têm SVG+label
- **Commit:** `8fbc69c`

### Item 8 — Timeline unificada por obra
- **Onde:** `analise/timeline-lab.html` (33KB, criado 24/04 17:15)
- **Validação:** drill-down do dashboard abre `timeline-lab.html` com obra selecionada
- **Commit:** `d67d4d5` (drill) + construção anterior da timeline

### Item 10 — Sparklines e deltas com dados reais
- **Onde:** `analise/dashboard.html` L3936-3944 (JS runtime)
- **Validação:** `delta null→novo · <0→▼down · >0→▲up · 0→=same`. Fetch de `backlog-historico.json` L3910. HTML inicial é placeholder.
- **Commit:** anterior (`b27c137` verificou)

### Item 13 — Hermes tema claro
- **Onde:** `analise.html`
- **Validação:** grep por `#0a0a0a`/`Inter`/`#c4a77d` não retorna nada
- **Commit:** `348a27f`

### Item 14 — Pills unificadas no dashboard
- **Onde:** `analise/dashboard.html` L794 (`pill-agenda`), L795 (`pill-carteira`), L1354 (AGENDA), L1407 (PROBLEMAS), L1900 (CARTEIRA)
- **Validação:** grep `section-pill` aparece em Q1-Q4, AGENDA, PROBLEMAS, CARTEIRA
- **Commit:** `348a27f`

---

## ⚠️ PARCIAIS (4)

### Item 2 — Literais no dashboard + fallbacks
- **Progresso:** commit `8cd3445` removeu 4x "208 ativas". **Falta ainda:**
  - L1043 `"apenas 12% da carteira ativa"` (kpi-edai)
  - L1044 `"quase metade da carteira — acima de 6 meses"`
  - L1045 `"críticas: 4 com 180+"`
  - L1061 `"Das 34 obras com cronograma"`
  - L1151 `"concentram 85% de todas as obras ativas"`
  - L1160 `id="q3-bus-pct">85%</span>` + `id="q3-bus-180">91%</span>` (fallbacks inline)
  - L3542 `const snapISO = AGG.snapshot_date || '2026-04-15';`
  - L3797 `const ativas = AGG.total_ativas || 208;`
- **Esforço restante:** P (varrer e trocar)
- **Critério de fechamento:** grep por `"208 "`, `"85%"`, `"91%"`, `"|| 208"`, `"|| '2026-04-15'"` retornar vazio em `.sub`/`.scope-note`/`.kpi-edai`

### Item 6 — Consolidar ranking único
- **Progresso:** reduziu de 3 rankings para 2. **Falta consolidar em 1.**
- **Onde:** `analise/dashboard.html` L1447 "Carga de tarefas por responsável" + L1453 "Top 10 obras que precisam de atenção"
- **Meta:** 1 tabela única com score composto (`w1·idade + w2·ocorrências + w3·tarefas_atraso + w4·sem_responsável`)
- **Esforço:** M

### Item 12 — Reconciliar universos (N único)
- **Progresso:** MAPA ✅ ganhou nota de recorte (L262+L280) + badge de defasagem (L275-278). **ATENA e INDICADORES ainda sem.**
- **Onde falta:** `analise/atena.html` (sem N declarado), `indicadores-v2.html` L348 "159 projetos ativos" sem justificativa do recorte
- **Esforço:** P

### Item 15 — Hub overlay + sessionStorage + glifo "58"
- **Progresso:** overlay reduzido 2500→700ms (L297 `setTimeout(..., 700)`). ✅
- **Falta:**
  - **Glifo "58" hardcoded** em `hub.html` L173 e L244 (`<text class="dash-score">58</text>`) — deveria ser dinâmico ou removido
  - **`sessionStorage` para pular splash** em visitas recorrentes (salvar `splashSeen=1` no botão Entrar; `hub.html` verifica e se já viu, não mostra splash)
- **Esforço:** P

---

## 🔴 PENDENTES (4)

### Item 1 — Destravar refresh do MAPA
- **Problema:** `obras-mapa.html` L333 tem `META` hardcoded com `"ultAtual":"2026-04-15"`. Dados do MAPA não atualizam automaticamente.
- **Opções:**
  - Migrar para fetch dinâmico (`fetch('dados/mapa-obras.json')`)
  - Automatizar rebuild do `META` via script que roda no refresh
- **Esforço:** M
- **Mitigação atual:** nota de recorte + badge de defasagem avisam que dados estão parados

### Item 4 — Reconciliar 6 vs 16 auditores
- **Problema:** `analise/modelagem.html` tem 3 pontos conflitantes:
  - L170: `<span>Auditores: <b>6</b></span>`
  - L215: `<div class="num">6</div>` ("Operadores ativos")
  - L1059: `Modelagem v3 · ... · 16 auditores (Projetos + Hoje + Planejamento)`
- **Ação:** decidir se é 6 ou 16 (ou se são conceitos diferentes) e propagar/distinguir
- **Esforço:** P

### Item 9 — Filtro global no dashboard
- **Problema:** não há filtro global no topo. Toda análise reinicia do zero por seção.
- **Meta:** dropdown/chip no topo (consultor/equipe/UF) que propague estado para Q1/Q2/Q3/Diagnóstico/Carteira via dataset compartilhado
- **Esforço:** M

### Item 11 — Endurecer prompt Hermes + "contrações"
- **Problema 1:** `analise.html` L359 e L372 têm "contrações detectadas" (é "contradições")
- **Problema 2:** prompt Groq ainda gera linguagem mole ("pode afetar", "merece atenção", "é um problema")
- **Ação:**
  - Corrigir literal no HTML (ou no prompt que gera o HTML)
  - Adicionar banlist no system prompt do Groq
  - Exigir ≥1 número concreto por parágrafo
- **Onde fica o prompt:** investigar `analise/refresh.sh` ou `.github/workflows/` ou script de geração Hermes
- **Esforço:** P

---

## 🎯 Lotes sugeridos pra próxima tacada

### Lote A — baratos, paralelos (6 itens, ~1h total)
| # | Ação | Esforço |
|---|---|---|
| 2 | Limpar 6 literais restantes + 2 fallbacks do dashboard | P |
| 4 | Decidir 6 ou 16 auditores e propagar | P |
| 11 | "contrações"→"contradições" + banlist no prompt | P |
| 12b | Nota de recorte em ATENA + INDICADORES | P |
| 15b | Glifo "58" dinâmico + `sessionStorage` no splash | P |

### Lote B — médios, foco individual (3 itens, 2-3h cada)
| # | Ação | Esforço |
|---|---|---|
| 1 | Migrar MAPA de META hardcoded para fetch dinâmico | M |
| 6 | Consolidar 2 rankings em 1 único com score composto | M |
| 9 | Filtro global (consultor/equipe/UF) no dashboard | M |

---

## 📜 Histórico

| Data | Evento |
|---|---|
| 2026-04-24 | 1ª varredura: 39 recomendações originais |
| 2026-04-24 | 2ª varredura: detectou regressões e débito crescente |
| 2026-04-24 | 3ª varredura: 3% de execução das recomendações, 3 itens pioraram |
| 2026-04-24 | Commit `8fbc69c`: 6 fixes — 3 completos (3, 5, 7), 3 parciais (2, 6, item extra) |
| 2026-04-24 | Commit `b27c137`: nota de recorte MAPA + badge defasagem + itens 8/10 verificados |
| 2026-04-24 | Commit `348a27f`: Hermes tema claro + pills + overlay 700ms — 2 completos (13, 14), 1 parcial (15) |
| 2026-04-24 | Commit `8cd3445`: 4 ocorrências "208 ativas" removidas — item 2 parcial |

## 🔗 Referências

- Memória Claude: `C:\Users\vitor\.claude\projects\C--Users-vitor\memory\project_central_qualidade.md`
- Arquitetura: `C:\Users\vitor\.claude\projects\C--Users-vitor\memory\project_arquitetura_paineis.md`
- URL pública: https://vitormonofloor.github.io/Monofloor_Files/hub.html
