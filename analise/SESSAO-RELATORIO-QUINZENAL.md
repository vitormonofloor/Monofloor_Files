# Sessão · Relatório Quinzenal de Qualidade

> **Briefing pra retomar em qualquer terminal.** Última atualização: 2026-05-04.
> Lê isso antes de mexer no projeto do relatório quinzenal.

---

## Estado em uma frase

Sistema gerador de **relatório quinzenal pra Diretoria** está **funcional** com 16 seções, 4 visuais SVG, 6 receitas propositivas, 18 fixes aplicados em 3 rodadas de auditoria externa. Pronto pra uso operacional como **rascunho que Vitor revisa** antes de compartilhar — falta apenas Fase B (botão no hub) e refinamentos P1 nova / P2 nova.

---

## TL;DR · o que foi construído

### Arquitetura
- **Coletor 1:** `coletar-relatorio-extras.py` · busca 4 endpoints públicos subutilizados (`/api/analise`, `/api/analytics/alerts`, `/api/analytics/weekly-forecast`, `/api/dashboard`)
- **Gerador:** `gerar-relatorio.py` · lê dados + receitas + histórico → produz Markdown
- **Conversor:** `gerar-pdf.py` · MD → HTML estilizado (CSS Monofloor) · zero dependências externas
- **Catálogo:** `receitas-qualidade.json` · 6 receitas de problema com diagnóstico + caminhos viáveis (Como/Custo/Impacto/Risco)
- **Backlog:** `relatorios/MELHORIAS-PENDENTES.md` · fonte única de verdade pra evolução

### Fluxo de uso
```bash
cd C:/Users/vitor/Monofloor_Files/analise

# Atualizar dados extras (15s · GET de 4 endpoints)
python coletar-relatorio-extras.py

# Gerar relatório (chama gerar-pdf.py automaticamente)
python gerar-relatorio.py

# Saída: relatorios/YYYY-MM-quinzena-N.{md,html}
# Pra PDF: abrir HTML no Chrome → Ctrl+P → "Salvar como PDF"
```

### Integrações
1. Painel de Obras (`cliente.monofloor.cloud`)
2. Lab Orion (`orion-pub.workers.dev`) — cruzamento Painel × Telegram
3. KIRA WhatsApp (via rodrigo-stats)
4. Score Histórico (acumula 1 entry/dia desde 2026-05-01)
5. 4 endpoints subutilizados (analise + alerts + forecast + dashboard)

---

## Estrutura final do relatório (16 seções · 638 linhas)

```
Seção 0 · Brief Executivo                  ◀ Diretoria · 60s
Seção 1 · Resumo do Período                ◀ Gerência · 3min
Seção 2 · Indicadores do Período (14 KPIs)
Seção 3 · Diagnóstico Operacional + Pulso KIRA
Seção 4 · Análise de Atrasos · caso a caso (top 5)
Seção 5 · Retrabalho & Pós-entrega
Seção 6 · Geografia
Seção 7 · Capacidade × Demanda (com projeção semana)
Seção 8 · Análise por Equipe (consultoras + supervisores)
Seção 9 · Sinais Painel × Telegram (Lab Orion)
Seção 10 · Conclusões e Recomendações       ◀ Receitas com Como/Custo/Impacto/Risco
Conclusão Executiva                         ◀ 2 parágrafos amarrando
Anexo A · Obras do período (status)
Anexo B · Glossário
Fontes e Disclaimer
```

### Visuais SVG inline (sem dependência)
- Sinaleira 🟢🟡🔴🔵 nos 6 KPIs do Brief
- Top 5 categorias de problema (barras com cor por proporção crítica)
- Distribuição KIRA (barras empilhadas saudável/atenção/sem KIRA)
- Capacidade utilizada (barra horizontal com zona)

---

## Decisões fechadas (não renegociar sem motivo claro)

| Item | Decisão |
|---|---|
| Tom | Moderno e direto · zero "ressaltando, pautando, possibilitando" |
| Frequência | Quinzenal |
| Público | Diretoria pode ler · peso executivo |
| Formato fonte | Markdown editável |
| Formato entrega | HTML estilizado · Ctrl+P → PDF no browser |
| Modo de geração | ~80% automatizado · 20% lacunas pra Vitor revisar |
| Gatilho | Híbrido · botão no hub + Telegram **(NÃO IMPLEMENTADO ainda)** |
| Conteúdo | 100% Dashboard + Orion · relatórios antigos foram só inspiração de formato |

---

## DNA do documento (regra inegociável)

Toda informação ruim vem com **(1) hipótese de causa + (2) ação sugerida ou pergunta orientada**. Hierarquia visual rigorosa. Densidade controlada (1 página = 1 ideia central). **Leitor sai com respostas e ideias de correção, não desesperado.**

---

## Histórico de auditorias externas (3 rodadas)

| Rodada | Itens identificados | Fixes aplicados |
|---|---|---|
| **1ª leitura** | 9 P0 + 5 P1 originais | P0 [x] · P1 4/5 [x] |
| **2ª leitura** | 14 itens novos | P0 nova [x] (5 fixes) |
| **3ª leitura** | 15 itens novos | P0 nova-2 [x] (4 fixes) |
| **TOTAL** | | **18 fixes** |

Lista completa em `relatorios/MELHORIAS-PENDENTES.md`.

### Achados-chave dos fixes
- `[REVISAR]` filtrado do HTML (mantém no MD pra Vitor editar)
- "Coordenador" → "Gerente da Qualidade" (cargo atual)
- 4 endpoints subutilizados integrados (analise/alerts/forecast/dashboard)
- Score "vs quinzena anterior" → "vs snapshot de Nd atrás" (honestidade)
- 184 vs 260 reconciliado (universo Painel vs Análise do Painel)
- A INICIAR firmadas (30d) corrigido (bug `proximos["30d"]["obras"]`)
- Glossário com 8 termos (KIRA/Painel/Orion/Score+fórmula/zumbi/órfã/fantasma/Apenas CEP/Concluído vs Finalizado)
- Sinaleira nos 6 KPIs do Brief
- 3 SVGs visuais (Capacidade, Categorias, KIRA)
- Brief Executivo (Seção 0) · 60s pra Diretoria
- Conclusão Executiva amarrando relatório
- Equipes da Seção 8 com dados reais (líder + ativos + obras lideradas + estado com sinaleira)

---

## O que ainda falta (priorizado)

### 🟡 P1 nova (~45min · próxima sessão natural)
- Cortar Seção 1 (Resumo do Período duplica Brief)
- Consolidar 3 alertas críticos com mesmo padrão em 1 alerta-padrão "Gargalo sistêmico em INFORMAÇÕES LOGÍSTICAS"
- Cortar 3 destaques que duplicam KPIs
- Consolidar 32+ "Caminhos a explorar" espalhados

### ✏ P2 nova (~30min)
- Seção 4 condensada (5 obras × 4-10 linhas é denso)
- Equipe Michael (9 ativos · 0 lideradas) com nota explicativa
- Resumo Orion em bullets
- Lab Orion declarar amostra (10 de 260 = 3.8%)
- Anexo A com TOTAL
- Caixa "Observação da Gerência" (voz humana)
- Tradução de gírias no Brief ("zumbi/mutirão")

### 🟢 P2 original (depende de coleta · médio prazo)
- Comparativo 3-6 meses (precisa histórico acumular · ~14d)
- Implicação financeira em R$
- Top 3 obras de risco pessoal da Diretoria
- Benchmark de setor

### 🎨 P3 (futuro)
- Tendência Score 6 meses · sparklines · pizza categorias

### 🚀 Fases B e C pendentes
- **Fase B:** botão no hub "Gerar relatório quinzenal" disparando o pipeline
- **Fase C:** bot Telegram avisando quinzenalmente "está na hora · clique pra gerar"

---

## Como retomar (próxima sessão · qualquer terminal)

```bash
# 1. Vai pro projeto
cd C:/Users/vitor/Monofloor_Files

# 2. Ler backlog atualizado
cat analise/relatorios/MELHORIAS-PENDENTES.md

# 3. Ver último relatório gerado
ls -lh analise/relatorios/*.html | tail -1

# 4. Atualizar dados (se necessário)
cd analise && python coletar-relatorio-extras.py

# 5. Gerar relatório atual
python gerar-relatorio.py

# 6. Abrir HTML pra ver estado atual
start "" relatorios/2026-05-quinzena-1.html
```

### Próximo alvo natural
**P1 nova** (45min) — consolidar redundâncias estruturais. Depois Fase B (botão no hub) pra fechar pipeline ponta-a-ponta.

---

## Princípios firmados durante o desenvolvimento

1. **Indicadores antigos (Set/Out 2024) foram inspiração de formato, não conteúdo** — usar 100% Dashboard + Orion
2. **Cargo do Vitor:** Gerente da Qualidade (não Coordenador, isso era 2024)
3. **Score Histórico ainda imaturo** (4 dias) — comparativos honestos só com 14+ dias
4. **`atRisk` retorna estado atual + diagnóstico textual antigo** — declarar pra não enganar
5. **`[REVISAR]` no MD é pra editar · `gerar-pdf.py` filtra do HTML final**
6. **Universo Painel (260) ≠ Universo /api/analise (184)** — sempre reconciliar quando aparecerem juntos

---

## Memórias do agente relacionadas

- `project_relatorio_quinzenal.md` (este projeto)
- `feedback_relatorio_orientado_a_acao.md` (DNA do documento)
- `reference_relatorio_backlog.md` (pointer pro backlog)
- `feedback_inventar_identidade_visual.md` (não inventar)
- `feedback_editar_canonico_nao_derivado.md` (regenerador)
- `personality_qualidade_monofloor.md` (DNA da dupla)
- `user_vitor.md` (cargo atual + perfil)

---

**Última geração:** 2026-05-04 18:22 · arquivo `relatorios/2026-05-quinzena-1.{md,html}` · 638 linhas · 36KB MD / ~38KB HTML.
