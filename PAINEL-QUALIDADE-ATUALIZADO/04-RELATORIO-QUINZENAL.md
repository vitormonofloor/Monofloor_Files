# 04 · Relatório Quinzenal de Qualidade

> **Iniciado:** 2026-05-04 · **Estado:** funcional, em refinamento ativo
> **Geração:** `python analise/gerar-relatorio.py`
> **Saída:** `analise/relatorios/YYYY-MM-quinzena-N.{md,html}`

---

## Pra que serve

Documento **pra Diretoria** que consolida a saúde da Qualidade a cada 15 dias. Diretor abre, lê em 60s o Brief Executivo, e sai com:
- Estado da operação (manchete + KPIs com sinaleira)
- 3 alertas críticos pra deliberar
- 3 recomendações priorizadas
- Implicação sintética

Quem quiser detalhe técnico desce pras seções 1-9. Quem quiser plano de ação completo vai pra Seção 10.

---

## Decisões fechadas

| Item | Decisão |
|---|---|
| **Tom** | Moderno e direto · zero "ressaltando, pautando, possibilitando" |
| **Frequência** | Quinzenal |
| **Público** | Diretoria · peso executivo |
| **Formato fonte** | Markdown editável |
| **Formato entrega** | HTML estilizado · Ctrl+P → "Salvar como PDF" no Chrome |
| **Modo de geração** | ~80% automático · 20% lacunas pra Vitor revisar (com rascunho automático bom como fallback) |
| **Gatilho** | Híbrido · botão no hub + Telegram **(NÃO IMPLEMENTADO)** |
| **Conteúdo** | 100% Dashboard + Orion · relatórios antigos (Set/Out 2024) foram só inspiração de formato |

---

## Estrutura · 16 seções · 638 linhas

```
Seção 0 · Brief Executivo (60s pra Diretoria)
  ├── Manchete narrativa
  ├── Painel de 6 KPIs com sinaleira 🟢🟡🔴🔵
  ├── 3 recomendações priorizadas
  └── Implicação sintética

Seção 1 · Resumo do Período (panorama)
Seção 2 · Indicadores do Período (14 KPIs)
Seção 3 · Diagnóstico Operacional + Pulso KIRA
Seção 4 · Análise de Atrasos · caso a caso (top 5)
Seção 5 · Retrabalho & Pós-entrega
Seção 6 · Geografia
Seção 7 · Capacidade × Demanda
Seção 8 · Análise por Equipe
Seção 9 · Sinais Painel × Telegram (Lab Orion)
Seção 10 · Conclusões e Recomendações ◀ receitas com Como/Custo/Impacto/Risco

Conclusão Executiva (2 parágrafos amarrando)
Anexo A · Obras do período (status)
Anexo B · Glossário (8 termos)
Fontes e Disclaimer
```

---

## DNA inegociável (firmado em 2026-05-04)

> *"A leitura sempre buscando a informação clara, de modo que nunca, em hipótese alguma, fique confuso. Pelo contrário, que o leitor saia com respostas e ideias de correção e não desesperado."*

3 regras:

1. **Toda informação ruim vem com 2 acompanhamentos:**
   - Hipótese de causa
   - Ação sugerida ou pergunta orientada

2. **Hierarquia visual rigorosa**
   - Brief no topo (1 página)
   - Detalhes em ordem de importância
   - Anexos no fim

3. **Densidade controlada**
   - 1 página = 1 ideia central
   - Tabelas curtas (≤8 linhas)
   - >10 itens viram agrupamento por padrão

---

## Catálogo de receitas (`receitas-qualidade.json`)

6 receitas de problema · cada uma com diagnóstico template + caminhos viáveis (Como/Custo do tempo/Impacto/Risco) + recomendação combinada:

| Trigger | Receita | Caminhos |
|---|---|---|
| Score < 50 | `score_baixo` | Mutirão zumbis · Gargalo VT · Padronização preventiva |
| Comunicação >50 obras | `categoria_comunicacao` | Diário obrigatório · Auditoria · Bloqueio direto |
| Infiltração >40 ou >20 críticas | `categoria_infiltracao` | Auditoria técnica · Critério VT |
| Capacidade <50% | `capacidade_ociosa` | Sinalizar Comercial · Reduzir prazo · Redimensionar |
| Cegueira KIRA >50 | `cegueira_kira` | Checklist obrigatório · Mutirão retroativo · Aceitar parcial |
| Críticas >15 | `alto_atraso_critico` | Triagem semanal · Escalação automática |

Cada caminho com **Como** (ação concreta), **Custo do tempo** (ex: 10h/sem por 2 semanas), **Impacto** (ex: zumbi_pct cai 18.8% → 5%), **Risco** (ex: pendência real não-mapeada).

---

## Visualizações SVG inline (sem dependência)

- Sinaleira 🟢🟡🔴🔵 nos 6 KPIs do Brief
- Top 5 categorias de problema (barras horizontais com cor por proporção crítica)
- Distribuição KIRA (barras empilhadas saudável/atenção/sem KIRA)
- Capacidade utilizada (barra horizontal com zona)

---

## Fontes integradas (5)

1. **Painel de Obras** (`cliente.monofloor.cloud`) · refresh 30min
2. **`/api/analise`** · 50 obras com diagnóstico textual + 11 categorias problema + teamPerformance
3. **`/api/analytics/alerts`** · 9 alertas estruturados (HIGH/MED/LOW)
4. **`/api/analytics/weekly-forecast`** · projeção 13 semanas
5. **`/api/dashboard`** · ocorrências abertas
6. **Lab Orion** · cruzamento Painel × Telegram
7. **Score Histórico** · acumula desde 2026-05-01

---

## 18 fixes em 3 rodadas de auditoria externa

| Rodada | Itens | Status |
|---|---|---|
| 1ª leitura fria | 9 P0 + 5 P1 originais | P0 [x] · P1 4/5 [x] |
| 2ª leitura fria | 14 itens novos | P0 nova [x] (5 fixes) |
| 3ª leitura fria | 15 itens novos | P0 nova-2 [x] (4 fixes) |

Lista completa em `Monofloor_Files/analise/relatorios/MELHORIAS-PENDENTES.md`.

---

## Pendente

### 🟡 P1 nova (~45min)
- Cortar Seção 1 (duplica Brief)
- Consolidar 3 alertas com mesmo padrão em 1 alerta-padrão
- Cortar 3 destaques que duplicam KPIs
- Consolidar 32+ "Caminhos a explorar" espalhados

### ✏ P2 nova (~30min)
- Seção 4 condensada
- Equipe Michael (9 ativos · 0 lideradas) com nota
- Resumo Orion em bullets
- Lab Orion declarar amostra (10 de 260)
- Anexo A com TOTAL
- Caixa "Observação da Gerência" · voz humana
- Tradução de gírias

### 🟢 P2 original (depende de coleta)
- Comparativo histórico real (precisa 14+ dias)
- Implicação financeira em R$
- Top 3 obras de risco pessoal

### 🚀 Fases B e C
- **B:** botão no hub "Gerar relatório quinzenal"
- **C:** bot Telegram avisando quinzenalmente

---

## Comandos pra retomar

```bash
cd C:/Users/vitor/Monofloor_Files/analise

# 1. Atualizar dados extras (4 endpoints)
python coletar-relatorio-extras.py

# 2. Gerar relatório (chama gerar-pdf.py automaticamente)
python gerar-relatorio.py

# 3. Abrir HTML pra ver/imprimir
start "" relatorios/2026-05-quinzena-1.html
```

Pra exportar PDF: Ctrl+P no browser · Salvar como PDF · A4 · margens padrão.
