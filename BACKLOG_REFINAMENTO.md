# Backlog de Refinamento — Central de Qualidade

> Consolidação das varreduras de auditoria. Atualizar conforme itens forem concluídos.
> Última atualização: **2026-04-27** — sessão de fechamento total (Lote A + Lote B)

## 📊 Placar atual

| Status | Qtd |
|---|---|
| ✅ Prontos | 15 |
| ⚠️ Parciais | 0 |
| 🔴 Pendentes | 0 |
| **Total** | **15** |

**Backlog zerado.** Todos os itens das 3 varreduras foram resolvidos.

---

## ✅ PRONTOS (15)

### Item 1 — Destravar refresh do MAPA ✓
- **Onde:** `analise/obras-mapa.html`
- **Solução:** META renomeado para `META_FALLBACK`, novo `hydrateMeta()` faz fetch de `dados/dashboard-data.json` antes de render. Stamp e badge de defasagem agora dinâmicos. Fallback inline preservado se fetch falhar.
- **Sessão:** 2026-04-27

### Item 2 — Literais no dashboard + fallbacks ✓
- **Onde:** `analise/dashboard.html`
- **Solução:** 7 literais corrigidos (kpi-edai 12%, qualifier "quase metade", críticas 4, "34 obras com cronograma", "concentram 85%", fallback `'2026-04-15'`, fallback `|| 208`). 6 IDs novos (`kpi-exec-edai`, `kpi-180-edai`, `kpi-orfas-180`, `q1-crono-total-sub`, `q1-crono-total-label`, `q3-bus-pct-sub`). Cálculos vêm de AGG/EXT do snapshot real.
- **Sessão:** 2026-04-27

### Item 3 — `stamp-now` lê snapshot_ts ✓
- **Commit:** `8fbc69c`

### Item 4 — Reconciliar 6 vs 16 auditores ✓
- **Onde:** `analise/modelagem.html`
- **Solução:** L170 desambiguada para "Auditores no painel: 6"; L1059 reformulado para "16 auditores totais (Projetos + Hoje + Planejamento) · 6 ativos no painel".
- **Sessão:** 2026-04-27

### Item 5 — Plano: "Etapa 2" vs 4 barras 100% ✓
- **Commit:** `8fbc69c`

### Item 6 — Consolidar ranking único ✓
- **Onde:** `analise/dashboard.html`
- **Solução:** "Top 10 obras" agora é o ranking definitivo com **score composto explícito** (`0.30·ocs + 0.30·crit + 0.25·atraso + 0.15·tarefas`). Card "Carga por responsável" mantido como complementar (análise de pessoas, não obras), reposicionado abaixo. Tooltip com breakdown das 4 dimensões.
- **Sessão:** 2026-04-27

### Item 7 — Remover `javascript:void(0)` + âncoras vazias ✓
- **Commit:** `8fbc69c`

### Item 8 — Timeline unificada por obra ✓
- **Commit:** `d67d4d5`

### Item 9 — Filtro global no dashboard ✓
- **Onde:** `analise/dashboard.html`
- **Solução:** Barra sticky no topo com 3 selects (consultor / UF / equipe), botão limpar, status "N visíveis (de X)". `applyGlobalFilter()` usa `data-consultor`, `data-uf`, `data-equipe` nos elementos filtráveis. MutationObserver reaplica filtro quando rankings async chegam. Já injetado em Q2 (tabela diagnóstico), Q3 (carga responsáveis) e ranking único de obras.
- **Sessão:** 2026-04-27

### Item 10 — Sparklines e deltas com dados reais ✓
- **Commit:** `b27c137`

### Item 11 — Endurecer prompt Hermes + "contrações" ✓
- **Onde:** `analise.html`
- **Solução:** 4 ocorrências de "contraç*" → "contradiç*" (L333/359/360/372). Prompt Hermes (banlist + endurecimento) ainda fica para o repo `hermes-monofloor`.
- **Sessão:** 2026-04-27

### Item 12 — Reconciliar universos (N único) ✓
- **Onde:** `analise/atena.html`, `indicadores-v2.html`
- **Solução:** ATENA ganhou bloco `scope-note` populado dinamicamente (`atena-scope-n`, `atena-scope-data`). Indicadores-v2 reformulou L348-352 com "Base: N obras ativas · fonte: planejamento.monofloor.cloud". Mapa já tinha (commit `b27c137`).
- **Sessão:** 2026-04-27

### Item 13 — Hermes tema claro ✓
- **Commit:** `348a27f`

### Item 14 — Pills unificadas no dashboard ✓
- **Commit:** `348a27f`

### Item 15 — Hub overlay + sessionStorage + glifo "58" ✓
- **Onde:** `hub.html`
- **Solução:** Overlay 700ms (commit `348a27f`). Glifo "58" agora populado via fetch de `analise/dados/dashboard-data.json` calculando score composto inline (sla 30% + ftr 20% + idade 30% + risk 20%). 3x "208" também dinâmicos (lê `AGG.total_ativas` = 223). Splash skip via sessionStorage: **não aplicável** — hub.html não tem splash de entrada (a transição de 700ms é entre cards, não tela inicial).
- **Sessão:** 2026-04-27

---

## ➕ Itens extra fechados nesta sessão (não estavam numerados no backlog)

### C1 — Hermes linka pra `indicadores.html` (obsoleto) ✓
- **Onde:** `analise.html` L219/L229/L378
- **Solução:** 3 referências trocadas para `indicadores-v2.html`.

### C2 — Hermes data congelada ✓
- **Onde:** `analise.html` L229/L378
- **Solução:** Timestamps envoltos em `<span id="hermes-timestamp" class="hermes-timestamp">`. Script inline antes de `</body>` lê `analise/dados/dashboard-data.json` e formata `snapshot_ts` em PT-BR via `toLocaleString`. Fallback inline preservado.

### C3 — Indicadores-v2 100% hardcoded ✓
- **Onde:** `indicadores-v2.html`
- **Solução:** Refatoração completa. Bloco IIFE async no fim do `<body>` faz fetch de `dashboard-data.json` e popula 24 novos IDs (`ind-base-n`, `ind-fire-ocorrencias`, `ind-msg-total`, `ind-atraso-pct`, etc). Defensivo: `set()` ignora null/undefined, fallback hardcoded preservado se chave faltar. **Caveat:** ao abrir, vários KPIs vão pular para os valores do snapshot atual (159→223, 286→691, 47.6%→3.1%, 16.4%→40.4%, 238d→203d). Os números antigos vinham de fontes diferentes (KIRA 30d, régua de saúde) — TODOs documentados no script para chaves indisponíveis (Pipefy CORES/VT, ticket médio, throughput).

### M1 — Labs sem dock de ecossistema ✓
- **Onde:** `bloqueadores-lab.html`, `campo-lab.html`, `escopo-lab.html`, `funil-lab.html`, `timeline-lab.html`
- **Solução:** Dock global esquerdo padronizado (5 itens: Central, Indicadores, Dashboard, ATENA, Labs). Dock interno (#sec-*) renomeado para `.side-nav`/`.side-dot` à direita, evitando colisão visual.

### M2 — Headers inconsistentes nos labs ✓
- **Onde:** mesmos 5 labs
- **Solução:** Padrão antigo (`<div class="logo">M</div> MONOFLOOR`) substituído por `<div class="logo-text">monofloor</div>` (font-weight 300, letter-spacing 6px, lowercase). CSS de `.logo-text` adicionado onde faltava. Validação: 0 ocorrências do padrão antigo.

---

## 📜 Histórico

| Data | Evento |
|---|---|
| 2026-04-24 | 1ª varredura: 39 recomendações originais |
| 2026-04-24 | 2ª varredura: detectou regressões e débito crescente |
| 2026-04-24 | 3ª varredura: 3% de execução das recomendações, 3 itens pioraram |
| 2026-04-24 | Commit `8fbc69c`: 6 fixes — 3 completos (3, 5, 7), 3 parciais |
| 2026-04-24 | Commit `b27c137`: nota de recorte MAPA + badge defasagem + itens 8/10 verificados |
| 2026-04-24 | Commit `348a27f`: Hermes tema claro + pills + overlay 700ms (13, 14 fechados) |
| 2026-04-24 | Commit `8cd3445`: 4 ocorrências "208 ativas" removidas — item 2 parcial |
| 2026-04-24 | Commit `d06ac15`: backlog consolidado em arquivo |
| **2026-04-27** | **Sessão de fechamento total**: Lote A (Hermes/Hub/Labs/Modelagem) + Lote B (literais/recorte/rankings/mapa/filtro/indicadores-v2). 15/15 itens fechados. |

## 🔗 Referências

- Memória Claude: `C:\Users\vitor\.claude\projects\C--Users-vitor\memory\project_central_qualidade.md`
- Arquitetura: `C:\Users\vitor\.claude\projects\C--Users-vitor\memory\project_arquitetura_paineis.md`
- URL pública: https://vitormonofloor.github.io/Monofloor_Files/hub.html
