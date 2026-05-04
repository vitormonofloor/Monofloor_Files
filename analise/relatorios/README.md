# Relatório Quinzenal de Qualidade

> **Status:** esqueleto em construção · iniciado 2026-05-04
> **Esse documento descreve o sistema. O template em si é `template-quinzenal.md`.**

## DNA do documento (regra inegociável)

Cada problema citado no relatório vem com **2 acompanhamentos obrigatórios**:
1. **Hipótese de causa** (curta, declarada como hipótese se não for certeza)
2. **Ação sugerida ou pergunta orientada**

Princípio firmado por Vitor em 2026-05-04:
> *"A leitura sempre buscando a informação clara, de modo que nunca, em hipótese alguma, fique confuso a leitura. Pelo contrário, que o leitor saia com respostas e ideias de correção e não desesperado."*

**Nunca jogar problema sem caminho.** Frase tipo "tivemos 12 retrabalhos no período" sem causa nem ação é proibida.

## Decisões fechadas (2026-05-04)

| Item | Decisão |
|---|---|
| **Tom** | Moderno e direto · zero "ressaltando, pautando, possibilitando" |
| **Frequência** | Quinzenal (a cada 15 dias) |
| **Público** | Diretoria pode ler · peso executivo |
| **Formato fonte** | Markdown editável |
| **Formato entrega** | PDF com cabeçalho/footer Monofloor (gerado de MD via Pandoc) |
| **Modo de geração** | ~80% automatizado · 20% lacunas pra revisão (com rascunho automático bom o suficiente como fallback) |
| **Gatilho** | Híbrido · botão no hub + aviso Telegram a cada 15 dias |

## Estrutura (12 seções)

1. **Resumo Executivo** — manchete + score + KPIs + 3 destaques + 3 alertas (cada alerta com causa + ação)
2. **Indicadores do Período** — tabela KPIs com delta vs quinzena anterior
3. **Diagnóstico Operacional** — síntese fluida das 9 seções do dashboard
4. **Análise de Atrasos · caso a caso** — timeline KIRA por obra atrasada
5. **Retrabalho · análise de causa-raiz** — categorização por motivo *[Fase 2]*
6. **Geografia** — distribuição por estado
7. **Tonalidades Aplicadas** — pizza por m² + barra por quantidade *[Fase 2]*
8. **Análise por Equipe** — supervisores + aplicadores
9. **Sinais Painel × Telegram (Lab Orion)** — divergências detectadas
10. **Conclusões e Recomendações** — observação · hipótese · ação
11. **Anexo A · Listagem nominal das obras**
12. **Fontes e Disclaimer**

## Status dos dados (origem de cada seção)

| Seção | Status | Origem |
|---|---|---|
| 1, 2 | ✓ Pronto | `headline.json` + `rodrigo-stats.json` + `score-historico.json` |
| 3 | ✓ Pronto | dashboard.html data + `whatsappSummary` agregado |
| 4 | ✓ Pronto | `details/*.json` (timeline KIRA por obra) |
| **5** | **✗ Pendente** | precisa categorização de causa-raiz no Painel ou no coletor |
| 6 | ✓ Pronto | `rodrigo-stats.json` (classificação por estado) |
| **7** | **✗ Pendente** | precisa coletor extrair tonalidades aplicadas no período |
| 8 | ✓ Parcial | tem por consultor · falta fortalecer m² por aplicador |
| 9 | ✓ Pronto | `lab-hermeneuta-pub/public/dados/discordancias-v3.json` |
| 10, 11, 12 | ✓ Pronto | derivados do que está acima |

## Roadmap de implementação

### Fase 1 · esqueleto + gerador básico (próxima sessão)
- [x] Pasta `analise/relatorios/` criada
- [x] Template Markdown estruturado (`template-quinzenal.md`)
- [x] Manifesto + roadmap (este arquivo)
- [ ] Script `gerar-relatorio.py` puxando dados das fontes prontas
- [ ] Pipeline MD → PDF (Pandoc + CSS Monofloor)
- [ ] Botão no hub "Gerar relatório quinzenal" com seletor de datas
- [ ] Saída em `analise/relatorios/YYYY-Qn-quinzena-N.md` + `.pdf`

### Fase 2 · enriquecer com dados pendentes
- [ ] Coletor de causa-raiz dos retrabalhos (Painel ou tag manual)
- [ ] Coletor de tonalidades aplicadas no período
- [ ] Fortalecer m² por aplicador na Q3

### Fase 3 · automação + notificações
- [ ] Cron quinzenal · bot Telegram avisa "está na hora · clique pra gerar"
- [ ] Histórico comparativo de relatórios (delta entre quinzenas, tendências)
- [ ] Refinamento estético do PDF

## Convenções no template

- `[AUTO]` = preenchido automaticamente pelo gerador
- `[REVISAR]` = lacuna pra Vitor editar · rascunho automático fica como fallback
- `[DADO PENDENTE]` = aguardando coletor novo · seção mostra placeholder honesto

## Anti-padrões a evitar

Sinais de alerta no rascunho que devem ser corrigidos antes de publicar:
- ✗ "Pontos de atenção" sem dizer qual ação tomar
- ✗ "Dado em destaque" sem explicar por que importa
- ✗ "Resultado abaixo do esperado" sem hipótese de causa
- ✗ Lista com >10 itens sem agrupamento
- ✗ Parágrafo com >4 linhas sem ponto-chave em **negrito**
- ✗ Jargão dev ou estatístico (P75/P90 sem explicação contextual)

## Exemplo do padrão certo

✓ **Bom:**
> *"3 obras travadas há >40d em SP. Padrão comum: cliente mudou escopo após início.
> → propor revisão do checklist de Visita Técnica de Aferição pra capturar mudanças antes da execução."*

✗ **Ruim:**
> *"Identificamos um total de 3 obras com tempo de execução superior à média esperada,
> requerendo análise mais aprofundada para compreender as variáveis envolvidas."*
> (nada acionável + jargão)
