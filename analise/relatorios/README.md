# Relatório Quinzenal de Qualidade

> **Status:** esqueleto v2 · iniciado 2026-05-04 · revisado 2026-05-04
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
| **Conteúdo** | 100% derivado do Dashboard + Orion · relatórios antigos foram inspiração de **formato/tom**, não de indicadores |

## Estrutura (12 seções)

1. **Resumo Executivo** — manchete + score + KPIs + 3 destaques + 3 alertas (cada alerta com causa + ação)
2. **Indicadores do Período** — tabela KPIs com delta vs quinzena anterior
3. **Diagnóstico Operacional** — síntese fluida das 9 seções do dashboard, **incluindo Pulso KIRA explícito** (climas, cobertura, alertas)
4. **Análise de Atrasos · caso a caso** — timeline KIRA por obra atrasada
5. **Retrabalho & Pós-entrega** — obras em reparo + marcas/rolo/cera, separadas de atraso
6. **Geografia** — distribuição por estado
7. **Capacidade × Demanda** — *aceitamos mais obras ou estamos no limite?* (Capacidade × Volume × A Iniciar firmadas)
8. **Análise por Equipe** — consultoras (Luana × Wesley) + supervisores
9. **Sinais Painel × Telegram (Lab Orion)** — top 5 divergências detectadas
10. **Conclusões e Recomendações** — observação · hipótese · ação
11. **Anexo A · Obras do período** — RODANDO / ESTAGNADO / PENDENTE + encerradas + em retorno
12. **Fontes e Disclaimer**

## Status dos dados (origem de cada seção)

> **Tudo que está no template usa dados que já temos hoje.** Sem `[DADO PENDENTE]`.

| Seção | Origem |
|---|---|
| 1, 2 | `headline.json` + `rodrigo-stats.json` + `score-historico.json` |
| 3 | dashboard.html data + `whatsappSummary` agregado em `operacional_kira` |
| 4 | `details/*.json` (timeline KIRA por obra) + `q1-classificacoes.json` |
| 5 | `rodrigo-stats.json` (banner retrabalho) + status `reparo` / `marcas_rolo_cera` |
| 6 | `rodrigo-stats.json` (classificação por estado) |
| 7 | `rodrigo-stats.json` (capacidade) + EXT.firmadas (data_de_entrada) |
| 8 | dashboard Q3 + `historico-aplicadores.json` |
| 9 | `lab-hermeneuta-pub/public/dados/discordancias-v3.json` |
| 10, 11, 12 | derivados do que está acima |

## Roadmap de implementação

### Fase 1 · esqueleto + gerador básico (próxima sessão)
- [x] Pasta `analise/relatorios/` criada
- [x] Template Markdown estruturado v2 (`template-quinzenal.md`)
- [x] Manifesto + roadmap (este arquivo)
- [ ] Script `gerar-relatorio.py` puxando dados das fontes prontas
- [ ] Pipeline MD → PDF (Pandoc + CSS Monofloor)
- [ ] Botão no hub "Gerar relatório quinzenal" com seletor de datas
- [ ] Saída em `analise/relatorios/YYYY-Qn-quinzena-N.md` + `.pdf`

### Fase 2 · refinamento + Telegram bot
- [ ] Cron quinzenal · bot Telegram avisa "está na hora · clique pra gerar"
- [ ] Histórico comparativo de relatórios (delta entre quinzenas, tendências)
- [ ] Refinamento estético do PDF (CSS Monofloor)

### Fase 3 (opcional · futuro) · enriquecimento
- [ ] Categorização de causa-raiz dos retrabalhos (precisa coletor novo OU campo manual no Painel)
- [ ] Tonalidades aplicadas no período (precisa coletor extrair do Painel)
- [ ] m² por aplicador (hoje só por consultor)

## Convenções no template

- `[AUTO]` = preenchido automaticamente pelo gerador
- `[REVISAR]` = lacuna pra Vitor editar · rascunho automático fica como fallback

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

## Histórico de revisões

- **2026-05-04 v1** — esqueleto inicial baseado parcialmente nos relatórios antigos (Set/Out 2024). Continha seções `[DADO PENDENTE]` (Tonalidades, Causa-raiz Retrabalho).
- **2026-05-04 v2** — reformado pra usar 100% Dashboard + Orion. Cortou Tonalidades, substituiu "Retrabalho com causa-raiz" por "Retrabalho & Pós-entrega" (separação firmada), substituiu Tonalidades por "Capacidade × Demanda", reforçou Diagnóstico (Pulso KIRA explícito) e Orion (top 5 divergências). Anexo agora usa RODANDO/ESTAGNADO/PENDENTE. Sem dependência de coletor novo.
