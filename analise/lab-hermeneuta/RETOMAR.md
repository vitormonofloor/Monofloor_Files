# 🎯 RETOMAR · contexto rápido pra qualquer agente

> **Última atualização:** 2026-05-26 · Compilador reestruturado + paleta premium + sidebar sticky

---

## 🆕 SESSAO 2026-05-26 · O QUE FECHAMOS HOJE

### Compilador reestruturado (sidebar + conteudo)
- ✅ Layout migrado de secoes empilhadas para sidebar minimal (180px) + painel de conteudo (blog-style)
- ✅ 3 pilares: Material, Prazo, Qualidade — cada um com resumo em cards + secao de detalhe
- ✅ Sidebar: icone SVG + nome curto, sticky, click alterna pilar ativo
- ✅ Chart.js resize automatico ao alternar pilar (canvas em display:none)

### Pilar PRAZO construido do zero
- ✅ Narrativa conectando metricas-chave (% no prazo, mediana desvio, obras sem prazo)
- ✅ Grafico distribuicao horizontal (4 faixas: no prazo, leve, medio, grave)
- ✅ Grafico tendencia mensal dual-axis (% no prazo + mediana desvio)
- ✅ Decomposicao temporal (planejamento/hibernacao/execucao — barra empilhada)
- ✅ Tabela detalhada com Obra, Prometido, Executado, Desvio, Status
- ✅ Insight: hibernacao (74d mediana) e o real consumidor de tempo, nao execucao (8d)

### Filtro Consultor removido do Compilador
- ✅ Select e variavel `co` removidos de compFiltrar/compInit

### Paleta premium Orion (diferenciacao visual da Central)
- ✅ Fundo areia #e8e1d6 (Central usa #f0ebe3) + cards brancos #ffffff
- ✅ Sombras refinadas (shadow-sm/md/lg mais presentes)
- ✅ ~20 cores hardcoded migradas pra CSS vars (--line, --surface, --surface-2)
- ✅ Header bg alinhado com nova paleta

### Sidebar Compilador sticky
- ✅ top:16px → top:120px para acompanhar scroll abaixo do header+tab-bar
- ✅ Menu MATERIAL/PRAZO/QUALIDADE sempre visivel durante leitura do conteudo

### Deploy Cloudflare
- ✅ 4 deploys manuais via wrangler (paleta iterada 3x + sidebar sticky)

### Memorias novas
- `feedback_layout_sidebar_conteudo.md`
- `feedback_paleta_premium_contraste.md`

### Pendencias pra proxima sessao

| Ordem | Item | Custo est. |
|---|---|---|
| 1 | Panorama mensal (evolucao carteira mes a mes) | ~1h |
| 2 | Camada 2 — Triangulo de consistencia material | ~2h |
| 3 | Camada 3 — Score preditivo de risco (obras ativas) | ~2h |
| 4 | Pilar Qualidade — detalhar com graficos/narrativa (mesma profundidade do Prazo) | ~1h |

### Comando pra retomar (cole no Claude Code)

```
Le analise/lab-hermeneuta/RETOMAR.md · secao topo "SESSAO 2026-05-26". Compilador com sidebar+conteudo + paleta premium areia/branco. Sidebar sticky. Pendente: panorama mensal + Camada 2 material + Camada 3 score + pilar Qualidade.
```

---

## 📜 SESSAO 2026-05-25 · HISTORICO

### Universo expandido (252 → 301 obras)
- ✅ Cruzamento Painel × Telegram revelou 49 obras invisiveis (em fases de execucao mas fora do pipeline)
- ✅ `_obras_2026_ids.json` expandido de 236 para 287 IDs
- ✅ Cobertura efetiva: 97.2% (212/218 obras que executaram)
- ✅ 6 gaps residuais = reparos antigos sem Telegram (limite aceito do sistema)

### 4a camada data_inicio_real: previsao_painel
- ✅ Fallback em `gerar_jornada.py`: se dataExecucaoPrevista ja venceu e nao tem outra fonte → usa como data_inicio_real
- ✅ Cobertura por origem: card_operacional 70% | marco_telegram 19% | painel 9% | previsao_painel 2%

### Pipeline diario automatizado
- ✅ `agente/atualizar_universo.py` — busca TODAS obras da API, detecta novas em fases de execucao, expande IDs
- ✅ `agente/pipeline_diario.py` — orquestrador (universo + jornada + relatorio cobertura)
- ✅ `agente/pipeline_diario.bat` — wrapper para Windows Task Scheduler
- ✅ Windows Task Scheduler: tarefa "Orion Pipeline Diario" rodando diario as 7:00 AM
- ✅ Log em `dados/pipeline-diario.log` + `dados/universo-log.json` (rolling 90d)

### Painel desatualizado (descoberta)
- 59 obras com Telegram ativo mas Painel em planejamento/contrato
- Telegram confirmado como fonte de verdade para execucao
- Pipeline contorna isso via 4 camadas de fallback

### Material validado mes a mes
- ✅ Jan-Mai 2026: 91-100% cobertura de dados de material
- ✅ Campos corretos: `materiais_enviados`, `solicitacoes_material`, `consumos`

### Memorias novas
- `feedback_painel_desatualizado_telegram_verdade.md`
- `reference_pipeline_diario_compilador.md`

### Pendencias pra proxima sessao

| Ordem | Item | Custo est. |
|---|---|---|
| 1 | Verificacao visual completa (abrir localhost:8765/jornada.html) | ~15min |
| 2 | Deploy Cloudflare (wrangler deploy apos validacao) | ~5min |
| 3 | Panorama mensal (evolucao carteira mes a mes) | ~1h |
| 4 | Camada 2 — Triangulo de consistencia material | ~2h |
| 5 | Camada 3 — Score preditivo de risco (obras ativas) | ~2h |

### Comando pra retomar (cole no Claude Code)

```
Le analise/lab-hermeneuta/RETOMAR.md · secao topo "SESSAO 2026-05-25". Pipeline diario automatizado (Task Scheduler 7h). Universo 301 obras, cobertura 97.2%. Pendente: validacao visual + deploy CF + panorama mensal.
```

---

## 📜 SESSAO 2026-05-22 · HISTORICO

### Fix #4: tempo-pills crash (JS)
- ✅ `jornada.html`: adicionado `<div id="tempo-pills">` no HTML do detalhe de obra
- ✅ `renderTempoPills(j)` chamada dentro de `renderDetalhes()` (antes era orfã — existia mas nunca era chamada)
- ✅ Guard `if (!cont) return` pra evitar crash se container nao existir

### Fix #1: classificacao entrega_limpa mais rigorosa
- ✅ `_entrega_tem_ressalvas()` expandida: 1 ocorrencia media+ ou 2+ de qualquer severidade = com_ressalvas
- ✅ Antes: so nivel critico/alto ou >= 3 ocorrencias
- ✅ Impacto: UNKE reclassificada (2 occ media) · entrega_limpa 9→8 · 8 restantes genuinamente limpas (0 occ)
- ✅ Pipeline regenerado: 252 obras OK, 283s

### Fix #3: metragem anomala — visual aprimorado
- ✅ Alertas ja existiam no pipeline (metragem_zero + metragem_suspeita)
- ✅ Badge na sidebar agora vermelho (`.alerta-metragem`) em vez de roxo genérico — grita mais
- ✅ 10 obras metragem_zero + 12 metragem_suspeita detectadas

### Fix #2: duplicacao Telegram — ja implementado + visual aprimorado
- ✅ `_detectar_telegram_compartilhado()` ja existia e funciona: 17 obras em 10 pares
- ✅ Badge na sidebar agora laranja (`.alerta-telegram`) — distingue de alertas genericos
- ✅ Detalhe da obra ja mostra parceiros + aviso de marcos duplicados

### Dados regenerados (2026-05-22T13:03:10Z)
- 252 obras OK (1 erro HTTP 404 — obra deletada)
- Classificacao: pre_obra 100 | entrega_com_retrabalho 44 | entrega_com_ressalvas 30 | aguardando_execucao 30 | retrabalho_ativo 19 | em_execucao 12 | entrega_limpa 8 | em_execucao_com_retrabalho 5 | cancelada 2 | pausada 2

### Pendencias pra proxima sessao

| Ordem | Item | Custo est. |
|---|---|---|
| 1 | Verificacao visual completa (abrir localhost:8765/jornada.html e validar os 4 fixes) | ~15min |
| 2 | Deploy Cloudflare (wrangler deploy apos validacao visual) | ~5min |
| 3 | Panorama mensal (evolucao carteira mes a mes) | ~1h |
| 4 | Camada 2 — Triangulo de consistencia material | ~2h |
| 5 | Camada 3 — Score preditivo de risco (obras ativas) | ~2h |
| 6 | Cross-obra: padroes por consultor x tipo problema | ~1h |

### Comando pra retomar (cole no Claude Code)

```
Le analise/lab-hermeneuta/RETOMAR.md primeiro · secao topo "SESSAO 2026-05-22". 4 fixes aplicados (tempo-pills, entrega_limpa, metragem visual, telegram visual). Pipeline regenerado 252 obras. Pendente: validacao visual + deploy CF + panorama mensal.
```

---

## 📜 SESSAO 2026-05-21 · HISTORICO

### Fix Compilados (JS quebrado)
- ✅ SyntaxError `const hoje` duplicado em `compMaterial()` — impedia parse do script inteiro
- ✅ Deploy Cloudflare: git push nao basta, `wrangler deploy` obrigatorio
- ✅ Filtro temporal Compilados: default exec >= Jan/2026 (222 obras)
- ✅ Filtro faixa metragem no Compilados

### Auditoria profunda solicitacoes de material
- ✅ 21.407 msgs brutas do Telegram varridas com rede ampliada
- ✅ PAD_MAT_SOLIC expandido: verbos futuro, progressivo, acabou/nao tem mais
- ✅ Resultado: 115→169 solicitacoes (+47%), 51→65 obras (+27%)

---

## 📜 SESSAO 2026-05-19 · HISTORICO

### 3 refinamentos prescritivos encerrados
- ✅ Postergacoes: badge "Nx remarc." sidebar + mencao veredito (184 deteccoes, 83 obras)
- ✅ Acoes pendentes: bloco "O que fazer agora" com prioridade (205 obras)
- ✅ Friccao cliente: DESCARTADO (Telegram = time interno, cliente = WhatsApp, Orion nao le)

### Fixes da auditoria (66 obras maio/2026)
- ✅ Score para finalizadas/concluidas: antes null, agora retrospectivo (253/253 com score)
- ✅ Bug genero friccao: "critico" != "critica" — score NUNCA pontuava friccao. 33→4 inversoes
- ✅ Sidebar separada: ativas em cima, encerradas em bloco colapsavel `<details>`
- ✅ score_medio mensal: campo "score" nao "valor" + mes de inicio correto
- ✅ Publicado no orion-pub

### Memorias novas
- `feedback_escopo_focado_qualidade.md` — auditar so o recorte pedido
- `reference_bug_genero_friccao.md` — bug historico corrigido

### Pendencias pra proxima sessao

| Ordem | Item | Custo est. |
|---|---|---|
| 1 | Classificacao entrega_limpa: incluir ocorrencias (13/17 questionaveis) | ~30min |
| 2 | Duplicacao Telegram: detectar/alertar pares (7 confirmados no universo) | ~1h |
| 3 | Metragem anomala: 3 obras 0m2 finalizadas, 7 com <10m2 | ~30min |
| 4 | Camada 2 — Triangulo de consistencia material | ~2h |
| 5 | Camada 3 — Score preditivo refinado | ~2h |

### Comando pra retomar amanha (cole no Claude Code)

```
Le analise/lab-hermeneuta/RETOMAR.md primeiro · secao topo "SESSAO 2026-05-19". Memoria: project_jornada_refinamento_3pontos.md. Proximo passo: fix classificacao entrega_limpa (~30min) e duplicacao telegram (~1h). Focar so nas 66 de maio, nao expandir.
```

---

## 🆕 SESSÃO 2026-05-15 · O QUE FECHAMOS HOJE

### Assertividade 84% → 93.9%
- ✅ Fix 1: `classificar_obra()` usa `fase_atual_painel` como override (status stale → entrega_limpa/com_retrabalho)
- ✅ Fix 2: consultor fallback `monof.get("consultor") or monof.get("operacoes")`
- ✅ Fix 3: tempo_total fallback usa HOJE_DATE para obras ativas sem fim calculado
- ✅ `auditar_assertividade.py` — script novo com 10 critérios, campos controlados 99.2%

### Camada 1 — Benchmark por faixa de metragem ✅
- ✅ `classificar_faixa_metragem()` + `_injetar_benchmark_faixa()` em gerar_jornada.py
- ✅ 6 faixas: PP(<60) P(60-100) M(100-150) G(150-220) GG(220-300) XG(300+)
- ✅ Bloco visual no drawer (exec/total/hib/aplicadores vs mediana da faixa)
- ✅ Badge de faixa na sidebar (ex: "P · 45m²")
- ✅ Insight: PP tem 66% retrabalho — o dobro das faixas maiores

### Memórias novas
- `reference_faixas_metragem.md` — 6 faixas definidas pelo Vitor
- `project_macrodados_3_camadas.md` — roadmap 3 camadas + panorama mensal

### Pendências pra próxima sessão

| Ordem | Item | Custo est. |
|---|---|---|
| 1 | Panorama mensal (click mês → obras, faixas, tempo médio) | ~1h |
| 2 | Camada 2 — Triângulo de consistência material | ~2h |
| 3 | Camada 3 — Score preditivo de risco (obras ativas) | ~2h |
| 4 | 7 bugs da auditoria 2026-05-12 (continuam pendentes) | ~5h |

### Comando pra retomar amanhã (cole no Claude Code)

```
Lê analise/lab-hermeneuta/RETOMAR.md primeiro · seção topo "SESSÃO 2026-05-15". Memória: project_macrodados_3_camadas.md. Próximo passo: panorama mensal (~1h) e depois Camada 2 (consumo material). Entregar sequencial, não dispersar.
```

---

## 🆕 SESSÃO 2026-05-14 · O QUE FECHAMOS HOJE

### Marcos retroativos (atribuição D-1)
- ✅ Quando aplicador escreve "ontem fizemos X", marco atribuído ao dia anterior com `hora: "retro"` e `retroativo: True`
- ✅ Gantt SVG: retroativos com borda tracejada branca + icone ↩ no lugar da hora
- ✅ Swimlane: retroativos com borda tracejada dourada + tag "(retroativo)" no tooltip
- ✅ 6 marcos retroativos legítimos em 5 obras na primeira varredura

### Regex inicio_dia expandido + filtro amanhã
- ✅ 5+ padrões novos: "estou retornando/chegando/na obra", "já estou/estamos em obra", "retornando pra obra", "chegarei às"
- ✅ Filtro "amanhã" — descarta inicio_dia se "amanhã" aparece antes do match no texto (evita falso positivo tipo "amanhã já estou retornando")
- ✅ **Guilherme Haidar corrigido:** 0 → 6 marcos (dias 05 e 06/05), Gantt funcional
- ✅ 724 marcos totais, guardrails OK, deployado via publicar.py

### Pendências pra próxima sessão (7 bugs da auditoria 2026-05-12 continuam)

| Ordem | Bug | Custo | Onde |
|---|---|---|---|
| 1 | `status` ausente em 20/20 | 15min | gerar_jornada.py coleta |
| 2 | `tempo_execucao = None` em 6-8 obras | 1h | Cluster fallback |
| 3 | Hibernação engolida dentro de fase-mãe | 1h | Detector hibernação |
| 4 | 72% reprovacao no fallback "tratativa" | 30min | Subtipos verniz/completa |
| 5 | Falsos positivos por negação/pergunta | 45min | 5 regex novas |
| 6 | Kira/Bot como aplicador | 10min | PESSOAS_MONOFLOOR |
| 7 | qtd=None em 100% das OS | 1h | pdfplumber bug |

**Total: ~5h** pra eliminar todos os achados da auditoria.

### Comando pra retomar amanhã (cole no Claude Code)

```
Lê analise/lab-hermeneuta/RETOMAR.md primeiro · seção topo "SESSÃO 2026-05-14". Memórias críticas: project_auditoria_20_obras_2026_05_12.md. Próximo passo: bug #1 (campo status ausente no JSON · ~15min). Lista os 7 bugs em ordem com plano de fix pra cada.
```

---

## 📜 SESSÃO 2026-05-12 · HISTÓRICO

### Lab Orion · refinamento profundo da Jornada
- ✅ Sidebar esquerda (320px sticky) com busca + filtro status + filtro "vistas" (localStorage) · escala pra 200+ obras
- ✅ Botão "📋 Gerar relatório" no header da obra · drawer slide-in da direita · narrativa em prosa + gráficos (donut tempo + barra severidades) · imprimível com `window.print()` (Salvar como PDF nativo)
- ✅ Relatório editorial (sem cara de IA/dashboard) · 5 parágrafos com inferências determinísticas
- ✅ Tracking "obras já vistas" · localStorage · badge ✓ na sidebar
- ✅ Refinamento Gantt categorias · pulso intra-swimlane (zigzag vertical) quando bolinhas colidem
- ✅ Material no Telegram · SVG horizontal com swimlanes por classe (ENTRADA/CONSUMO/SOBRA/SOLIC/MATERIAL EM OBRA)
- ✅ Detalhamento conceitual: ESTOQUE renomeado pra "Material em obra" · CONSUMO regex ampliada · TRATATIVAS vs RETRABALHO refinado · "reaplicação verniz" como subtipo
- ✅ Datas uniformizadas em todo lugar (DD/MM/AA)

### Piloto expandido · 10 → 20 obras
- ✅ +10 obras finalizadas/concluídas com fim ≥ dez/2025 e 8+ marcos (MANUELA VILLAS BOAS, MARCOS ANTONIO, MANOELA LATINI, MARIANA PORTO, ÁUREO, NATHALIA, YAHYA, CHRISTIAN KORVER, LEONARDO KAWANO, BM VAREJO)
- ✅ Critério "corte temporal dez/2025" capturado em memória pra próximas expansões
- ✅ Benchmark "tempo entre marcos" funcionando · 17d mediana Última→Aprovação, 81d Aprovação→VT qualidade, etc

### Esquadrão de auditoria · 6 agentes paralelos
- ✅ 6 subagentes Claude lançados simultaneamente · cada um em 1 dimensão (datas, marcos, personagens, materiais, ocorrências, padrões cross-obras)
- ✅ Tempo total: ~20min · achados ricos em todas frentes

### Vocabulário expandido (gravado em memória)
- ✅ 12 cores novas (Ash, Everest, Terracota, Atena, Javier, Gengibre, Linho Branco, Ghost, Vert, Sweet, Cherry, Sasha, Camelo)
- ✅ 4 cores compartilhadas STELION+LILIT (Saara, Ash, Everest, Terracota)
- ✅ 7 variantes industriais (STELION + ESPESSANTE, STELION 3G DILUIDO, STELION LEONA, LUMINA FOSCO, LUMINA ANTIDERRAPANTE, PU ULTRA, SELADOR)
- ✅ 10+ pessoas novas (Michael Marinho, Jaú Microcimento, Juninho, F Lucena, Jorge Ribero, Laercio, Josias, Kaike, Pedro Alexandre Santana, Juliana Santos)
- ✅ 8 variantes de grafia Monofloor identificadas
- ✅ Bots classificados errado (Kira, Carlos Bot, Bridge, Q Assim Seja) · pra excluir de aplicadores

### Memórias novas/atualizadas
- `project_auditoria_20_obras_2026_05_12.md` · novo · snapshot consolidado
- `feedback_corte_temporal_obras_historico.md` · novo
- `reference_nomenclatura_produtos.md` · atualizado (cores + variantes)
- `_projeto/MAPA_PESSOAS.md` · atualizado (8 pessoas + variantes + bots)
- `_projeto/VOCABULARIO_OPERACIONAL.md` · atualizado (pressão de prazo, reparo pontual, reaplicação verniz)

### Pendências pra próxima sessão (7 bugs priorizados)

| Ordem | Bug | Custo | Onde |
|---|---|---|---|
| 1 | `status` ausente em 20/20 | 15min | gerar_jornada.py coleta |
| 2 | `tempo_execucao = None` em 6-8 obras | 1h | Cluster fallback |
| 3 | Hibernação engolida dentro de fase-mãe | 1h | Detector hibernação |
| 4 | 72% reprovacao no fallback "tratativa" | 30min | Subtipos verniz/completa |
| 5 | Falsos positivos por negação/pergunta | 45min | 5 regex novas |
| 6 | Kira/Bot como aplicador | 10min | PESSOAS_MONOFLOOR |
| 7 | qtd=None em 100% das OS | 1h | pdfplumber bug |

**Total: ~5h** pra eliminar todos os achados da auditoria.

### Comando pra retomar amanhã (cole no Claude Code)

```
Lê analise/lab-hermeneuta/RETOMAR.md primeiro · seção topo "SESSÃO 2026-05-12". Memórias críticas: project_auditoria_20_obras_2026_05_12.md, reference_nomenclatura_produtos.md, _projeto/MAPA_PESSOAS.md. Próximo passo: bug #1 (campo status ausente no JSON · ~15min). Lista os 7 bugs em ordem com plano de fix pra cada.
```

---

## 📜 HISTÓRICO ANTERIOR

> **Última atualização:** 2026-05-07 · F1 (Timeline em escala) + F2 (Calibração de memória) fechadas
> Se você é um agente IA chegando agora · LEIA este arquivo primeiro. Em ~30s você terá contexto suficiente pra trabalhar sem confundir nada.

---

## 🆕 SESSÃO 2026-05-07 · O QUE FECHAMOS HOJE

### Frente 1 · Timeline Obras em produção (✅)
- **Bloqueio "260 vs 200" resolvido:** API default de 200, `?ativa=true` é ignorado · universo real é 1042 · UI conta 257 · Universo Qualidade D = **222 vivas** (exclui finalizado/concluido/cancelado)
- **Paralelização** ThreadPoolExecutor 6 workers · primeira rodada 144s · sequencial seria ~12min
- **Manifest incremental** validado · `dados/manifest_obras.json` · rodadas seguintes 5-30s (skip via `updatedAt`)
- **Modo `--historico`** (outro terminal) · processou 1042 obras em 9.4min · 6057 marcos · `dados/timeline_historico_2026-05-07.json` (frozen reference pra mediana populacional)
- **Cobertura por status descoberta:** vivas operacionais 80-100% Telegram · histórico finalizado só 12% (Pipefy puro pré-Telegram) · concluídas 51%
- **Disparo HÍBRIDO** · 2 crons + botão:
  - `Monofloor_Timeline_Obras` · 04:00 diário (esta sessão · `cron_timeline_obras.bat`)
  - `MonofloorTimelineUpdate` · 8h/12h/16h/20h durante expediente (outro terminal · `update_timeline.bat`)
  - Botão **↻ Atualizar agora** no header copia comando pro clipboard
  - Manifest dedup garante zero conflito entre crons

### Frente 2 · Calibração da memória institucional (✅)
- **`_projeto/ADR/`** com 7 Architecture Decision Records + README/template:
  - ADR-001 Kira-driven · ADR-002 Tratativas×Retrabalho · ADR-003 Macro-etapas · ADR-004 Universo D · ADR-005 Manifest · ADR-006 Disparo híbrido · ADR-007 ATENA descontinuado
- **`_projeto/VOCABULARIO_OPERACIONAL.md`** · 10 seções consolidadas (produtos OS×campo, termos, aliases, status, vocabulário real, cores, filtros, convenções)
- **`_projeto/MAPA_PESSOAS.md`** · 9 seções (quem é quem, função atual+histórica, princípios)
- **Item 1+4 ativos:** captura proativa de princípios + lição estruturada no `/sync_save` (6 categorias)

### Memórias novas desta sessão
- `reference_api_painel_obras.md` · vocabulário institucional do Painel
- `reference_orion_docs_canonicos.md` · índice dos 13 docs do `_projeto/` + 7 ADRs

### Pendências pra próxima sessão
- **Frente 3 · Lab Orion Jornada · piloto expandido (10-15 obras)** (~3h) · calibrar regex em massa antes da rodada cheia · onde mora ~70% do aprendizado de regex que vamos usar pra sempre
- **Bugs cold read** B1 (Gantt diário vazio em KRYSTAL) e B2 (encoding "C�sar")
- **Cores oficiais STELION** · 12 hex pendentes de extrair do PDF do catálogo
- **Storytelling de 1 obra finalizada** (~1h) · ideia Rodrigo · pode ser hoje

### Comando pra retomar nesta sessão (cole no Claude Code)

```
Lê analise/lab-hermeneuta/RETOMAR.md primeiro · depois _projeto/README.md em ordem 1→13 (incluindo VOCABULARIO_OPERACIONAL.md, MAPA_PESSOAS.md, ADR/README.md) · então `python agente/sentinela.py` pra status atual · liste o que está pendente em ordem de prioridade.
```

---

## 📜 HISTÓRICO RESUMIDO (anterior)
> Estado em 2026-05-04 mantido abaixo pra contexto histórico do projeto.

> 📚 **Pasta-síntese completa:** `_projeto/README.md` (entrada · navega 1→7 pra entender em 5min)
> Esse RETOMAR é overview rápido · `_projeto/` é a fonte canônica de história, estado, arquitetura, pendências, runbook, aprendizados e inventário.

## ⚠ ANTES DE TUDO — ler na ordem

1. `personality_qualidade_monofloor.md` (na pasta de memória) — DNA da dupla com 19+ princípios + auto-crítica honesta antes de propor
2. `project_orion_caminho_a_2026_05_04.md` (memória) — narrativa do fix de hoje · achado do schema fantasma
3. `feedback_verificar_consumidor_antes_coletor.md` (memória) — learning estrutural · grep do consumidor antes de mexer no coletor
4. Este arquivo (estado técnico)
5. `ROADMAP_CAMINHO_B.md` (este diretório) — 5 frentes pra refactor estrutural

## O que é este lab em 1 frase

Sandbox que cruza grupos Telegram + WhatsApp **via API do Painel de Obras** (Kira já transcreveu áudios e descreveu fotos · nossa função é só extrair e analisar) com a fase oficial da obra pra detectar divergências invisíveis. **227 obras ativas** cobertas pelo `--todas-ativas` · varredura via Task Scheduler 12h e 18h.

## Naming

**ORION** (rebranding HERMENEUTA → ORION aplicado em 2026-05-01). Caçador de visão aguçada · 3 estrelas do cinturão = painel × telegram × KIRA · termina em ON igual STELION/TERON.

## URL ativa

`https://lab.monofloor.cloud` · CF Worker com Basic Auth + cookie 24h · senha gerenciada pelo Vitor.

## Audiência

Vitor + (em breve) Rodrigo + diretoria. Acesso via card-orion no Hub Monofloor. **ATENA foi extinto** (era cópia pobre do Orion).

---

## ✅ O que está bom (pós-Caminho A · 2026-05-04)

- **Cobertura Telegram: 190/230 cards** com sinal real (era 10) · 20.166 msgs Telegram + 9.455 WhatsApp coletados
- **Migração Telethon → Painel API completa** · sem auth, sem rate limit, multi-canal, descrições de foto/áudio já incluídas
- **Pipeline `varredura.py`** roda em ~47s · 13 etapas encadeadas com lock anti-concorrência + atomic write + backup rolling 14 dias
- **Bloco `telegram` (ultima_msg/dias_silencio/tom_grupo/total_msgs)** calculado direto do snapshot · zero IA · custo zero
- **Timeline de eventos** das mensagens · independente de dossiê (era bloqueador antes)
- **Sentinela com 9 checks** + indicador na tela
- **Top alertas reais surgindo:** AVVA HOUSE 632 msgs · 12 sinais tensos · 0 positivos (tipo de leitura impossível antes)

## 🟡 O que ainda tem problema (Caminho B é o próximo)

- **96% dos vereditos é heurística cega** · `status_sugerido`/`urgencia`/`acao_consultor` das 220 obras não-piloto são preenchidos copiando `fase_atual` do painel · "sugestão" é tautologia · confiança 0.8 fabricada
- **Cards "com IA" e "sem IA" indistinguíveis visualmente** · leitor não sabe que está vendo veredito sintético
- **Tom por keyword é tapa-buraco** · pega "atraso" mesmo quando a frase é "sem atraso" · funciona pra triagem grossa, falha em nuance
- **Detail-snapshot pode estar até 26d defasado** em algumas obras · quando isso machucar (raro), refresh manual do Painel resolve
- **40 obras com `?` no telegram** · são as que de fato não têm grupo Telegram cadastrado no Painel · ausência real, não bug

## ⏳ Pendências (ordem de prioridade)

### A) **Caminho B · refactor estrutural** (4-6h em sessão dedicada)
Ler `ROADMAP_CAMINHO_B.md` neste diretório. 5 frentes:
- B1 IA em todas 230 obras (não só recortes) — destrava B2
- B2 Honestidade visual (badge IA vs heurística)
- B3 Pipeline 13→4 etapas + cortar legado Telethon
- B4 Snapshot vira cache, não corredor obrigatório
- B5 Tom IA-driven (substitui keyword)

### B) **Storytelling de obra finalizada** (~1h)
Ideia do Rodrigo (2026-05-04) · escolher 1 obra concluída, rodar `analisar_recorte.py` cirurgicamente, montar narrativa cronológica completa (tempo, solicitações, materiais, eventos). Funciona HOJE com dados corretos · não precisa esperar Caminho B.

### C) **Cores oficiais do catálogo** (memória `project_orion_cores_oficiais.md`)
Extrair hex codes reais das 21 cores do PDF (9 chutadas estão no JSON, faltam 12) + fundo rotativo "cada visita é uma obra".

### D) **Opção B click→IA** (memória `project_orion_opcao_b_pausada.md` · PAUSADA)
Worker + Action prontos mas dormentes. Reativar quando outras pessoas (não Vitor) usarem.

---

## Pipeline atual (13 passos · após Caminho A)

```
1.  adquirir_lock (PID alive check)
2.  fazer_backup (rolling 14 dias em dados/backups/)
3.  shutil.copy snapshot Telegram → snapshot-prev (pra diff · CANDIDATO A CORTAR no Caminho B)
4a. selecionar_piloto.py --todas-ativas (227 obras)
4b. coletar_painel.py (Painel API · Telegram + WhatsApp · 2000 msgs/90d)
5.  calcular_diff_msgs (msgs novas por obra)
6.  extrair_timeline.py (eventos + bloco telegram do snapshot · dossiê opcional)
7.  aplicar_regua.py (bucket SLA + marcos PP:001 + fallback painel-snapshot)
8.  extrair_equipe.py (cadastro × telegram + overrides)
9.  extrair_cores.py (cores + tendência · regex `[ \t]*` + filtro keyword)
10. extrair_kira_whatsapp.py (espelha pendenciaManual.whatsappSummary)
11. inferir_consultor.py (overrides consultor formal × real)
12. sanitizar_json.py (remove flag cliente_ausente + campos mortos)
13. registrar_kpis.py (série temporal pra sparkline)
14. marcar_refresh_status (flag stale por obra)
15. sentinela.py (9 checks · gera status.json)
16. publicar.py (atomic + git push pub repo + wrangler deploy CF)
17. liberar_lock
```

## Scripts críticos em `agente/`

| Script | Função | Encaixe pipeline |
|---|---|---|
| `_util.py` | Helpers · write_discord · validar · backup · pipeline-errors flag | importado por todos |
| `varredura.py` | Orquestrador · adquire lock · executa pipeline · libera lock | RAIZ |
| `telethon/selecionar_piloto.py` | `--todas-ativas` (novo) ou `--todas` (legado) | passo 4a |
| `telethon/coletar_painel.py` | Painel API · Telegram + WhatsApp · 2000/90d | passo 4b |
| `extrair_timeline.py` | Bloco telegram + eventos · dossiê opcional | passo 6 |
| `aplicar_regua.py` | Bucket SLA + marcos PP:001 + fallback painel | passo 7 |
| `extrair_equipe.py` | Cadastro × Telegram + overrides | passo 8 |
| `extrair_cores.py` | Cores + agregado · regex fix + keyword filter | passo 9 |
| `extrair_kira_whatsapp.py` | Espelha KIRA WhatsApp do detail | passo 10 |
| `inferir_consultor.py` | Overrides consultor formal × real | passo 11 |
| `sanitizar_json.py` | Limpeza · cliente_ausente + campos mortos | passo 12 |
| `registrar_kpis.py` | Série temporal pra sparkline | passo 13 |
| `sentinela.py` | 9 checks · gera status.json + lê pipeline-errors.json | passo 15 |
| `publicar.py` | Atomic + git push + wrangler deploy | passo 16 |
| `analisar_recorte.py` | IA gpt-4o-mini · GitHub Models · gratuito 8k req/dia | manual |
| `arquivar_versao.py` | Backup pré-IA · suporta `--evolucao OBRA_ID` | manual |

### Scripts LEGADOS (candidatos a corte no Caminho B · não rodam mais)

- `telethon/monitorar.py` (Telethon morto · substituído por coletar_painel)
- `telethon/listar_grupos.py` (gerava grupos.json via Telethon)
- `telethon/grupos.json` (legado modo `--todas` pareadas)
- `telethon/telegram-snapshot-prev.json` (só serve pra diff de mensagens novas · valor marginal)

## Princípios fixos · NÃO QUEBRAR

1. **Painel de Obras é o produto do Kira** · transcrição de áudio + descrição de foto + indexação · nossa função é só extrair e analisar. Toda etapa intermediária é candidata a corte.
2. **Telegram > painel** quando divergem · verdade está nas mensagens
3. **Telegram = canal interno** Monofloor · cliente fica no WhatsApp via KIRA
4. **Custo zero** sempre que possível · IA on-demand via GitHub Models gratuito
5. **Versionar tudo** (`dados/historico/` · `dados/backups/` · 14 dias)
6. **Não inventar** · sempre citar `msg_id` como fonte
7. **`whatsappSummary.geradoEm` ≠ última msg** · é quando KIRA sintetizou
8. **Antes de culpar coletor, verificar se consumidor existe** · grep do campo no código antes de mexer no fetch · learning do schema fantasma 2026-05-04

## Camadas de proteção ativas

- ✅ Atomic write (`_util.write_json_atomic`)
- ✅ Schema validator (`_util.validar_discord` + `write_discord`)
- ✅ Backup rolling (14 dias × 2 varreduras = 28 backups)
- ✅ Lock com PID alive check (não só TTL)
- ✅ Retry exponencial Painel API + abort 30%
- ✅ Pipeline-errors flag (`dados/pipeline-errors.json` · sentinela detecta)
- ✅ HOJE dinâmico (`datetime.now(utc)` em todos)
- ✅ Encoding utf-8-sig na leitura
- ✅ Sentinela com 9 checks · drift directional (só ALERT em regressão, não em crescimento)
- ✅ Wrangler deploy garantido (não confia em CF auto-sync)

## Como verificar saúde rápido

```powershell
cd C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta
python agente/sentinela.py
```

Saída em ~1s mostrando 9 checks · `ok` / `warn` / `crit` · cada um com sugestão de ação.

## Como rodar varredura manual

```powershell
python agente/varredura.py
```

Roda os 13 passos em ~47s. Tem lock · se outra rodando, sai sem fazer nada.

## Como rodar IA cirurgicamente em 1 obra (custo zero)

```powershell
$env:GITHUB_TOKEN = "<PAT com escopo repo>"
python agente/analisar_recorte.py --obra-ids "<obra_id>" --recorte "manual"
python agente/publicar.py
```

Análise gpt-4o-mini via GitHub Models · usado pra storytelling, validação de obra específica, etc.

## Como subir tela local

```powershell
cd C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta
python -m http.server 8765
```

Abrir http://localhost:8765/

---

## Comando pra retomar (cole no Claude Code na próxima sessão)

```
Lê analise/lab-hermeneuta/RETOMAR.md e me dá overview do estado.
Roda python agente/sentinela.py e me mostra o resultado.
Lista o que está pendente do meu lado.
```

Esse comando faz qualquer agente: (1) carregar contexto, (2) validar saúde, (3) listar tarefas pendentes · em uma resposta só.
