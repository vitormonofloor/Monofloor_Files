# Princípio orientador — Central de Qualidade Monofloor

> Documento que filtra **o que NÃO fazer** antes de decidir **o que fazer**.
> Aplicar em TODA decisão de painel novo, cruzamento, refactor.
> Última revisão: **2026-04-27**.

---

## A regra

> **Complementar o enxugamento do Rodrigo. Nunca recriar o Pipefy.**

A doutrina cabe nessas duas linhas. Tudo abaixo é desdobramento.

---

## Contexto histórico

| Momento | Pipefy | Realidade |
|---|---|---|
| Início (~2024) | Substituiu planilhas → kanban com 49 fases | Ganho real |
| Hoje (2026) | Gigantesco · 49 fases · fluxos paralelos (principal + pós-venda) | **A complexidade virou o problema** |
| Em curso | Substituição pelo painel `cliente.monofloor.cloud` | Enxugar = remédio |

A granularidade granular do Pipefy revela diagnóstico (mostra onde trava), mas mata operação (ninguém atualiza). A solução do Rodrigo é **simplicidade intencional** — menos fases, mais clareza.

Nosso papel: **capturar os sinais que se perderiam** quando granularidade for cortada — sem **adicionar a complexidade que ele veio resolver**.

---

## 4 anti-padrões (o que NÃO fazer)

### 1. Não recriar fases granulares no nosso dashboard

❌ Painéis tipo *"obras em PROJETOS - 1ª REVISÃO"*, *"obras em CONFIRMAÇÕES OP 2"*, *"obras em RESULTADO VT - ENTRADA"*.

✅ Em vez: painéis que **agregam por sinal** — *"obras em risco"*, *"cauda longa"*, *"comunicação morta"*. O que importa é o estado, não a fase administrativa exata.

### 2. Não investir em ferramentas que dependam de operação manter atualização manual

❌ Quadros que exigem que alguém marque "feito" em 49 lugares diferentes.

✅ Em vez: ferramentas que **inferem estado** automaticamente (KIRA escutando grupos, `painel-amigo` integrando dados, `details/*.json` cruzados).

### 3. Não duplicar visualização sem agregar interpretação

❌ Mostrar a mesma lista de 227 obras em 5 lugares com filtros levemente diferentes.

✅ Em vez: cada painel responde **uma pergunta única** que nenhum outro responde. Se duas perguntas se sobrepõem, fundi-las.

### 4. Não confiar em uma fonte como "verdade universal"

❌ "Painel-amigo é a verdade" ou "Pipefy é a verdade".

✅ Em vez: cada sistema é **autoritativo num domínio**. Quando autoridades discordam, **a divergência é o produto** (operação esqueceu de fechar). Vide [I2 — mapa de autoridades](#i2---mapa-de-autoridades).

---

## Mapa de autoridades por domínio

| Domínio | Autoridade hoje | Autoridade futura | Confiança |
|---|---|---|---|
| Marco "obra acabou?" | **Pipefy CLIENTE FINALIZADO** | provavelmente passa pra painel-amigo | transitória |
| Idade da carteira (dias) | **Painel-amigo** (data_radar) | mantém | estável |
| Status operacional (em_execucao, pausado, reparo) | **Painel-amigo** | mantém | estável |
| Voz do grupo (narrativa, sentimento) | **KIRA** (em painel-amigo) | mantém | estável |
| Marcos administrativos (contrato, VT feita, OEC) | **Pipefy** | provavelmente passa pra painel-amigo | transitória |
| Data prometida ao cliente | **Planejamento** (planejamento.monofloor.cloud) | mantém | estável |

Quando pipefy for descomissionado, **F1 (Ficha 360°)** deve continuar funcionando — coluna "fonte autoritativa" é dinâmica, não fixa.

---

## Filtro de decisão (use antes de criar painel novo)

Pergunte:

1. **Que sinal único isto entrega?** Se a resposta é "uma versão da fase X do Pipefy", é anti-padrão #1 → não construir.
2. **Depende de operação manter atualização manual em N lugares?** Se sim, anti-padrão #2 → repensar pra inferência automática.
3. **Outro painel já mostra isso?** Se sim, anti-padrão #3 → fundir, não duplicar.
4. **Assume uma fonte como verdade absoluta?** Se sim, anti-padrão #4 → mostrar autoridade explícita por campo.

Se passou pelos 4, faz sentido construir. Se não, abandona ou refatora.

---

## Convenções práticas

### Painéis (HTMLs em `/analise/`)

- Cada painel responde **uma pergunta específica** declarada no header
- Footer sempre mostra: fonte (`cruz-X.json` / `details/*` / API), data de geração, esforço de regeração
- Usar `cruz-frescor.json` (Q4) pra alertar visualmente quando snapshot está estático >30 dias
- Em vez de "Indicadores" como entidade, expor a métrica direta na seção `#operacional` do dashboard (FASE 6.B)

### Cruzamentos (`cruz-*.json`)

- Devem ter campo `gerado_em` ou `data_referencia` — sem isso, frescor é caixa-preta
- Documentar fonte e regeração em `dados/CRUZAMENTOS-FRESCOR.md`
- Quando virar painel, declarar AUTORIDADE de cada coluna (Pipefy, painel-amigo, KIRA, etc)

### KIRA (camada narrativa)

- KIRA é nosso **complemento permanente** ao painel-amigo. Não substituível por nada.
- Quando o Pipefy morrer e o painel-amigo enxugar, KIRA continua sendo o que captura **o que ninguém escreveu em campo estruturado**.
- Investimento em KIRA é investimento em diagnóstico de longo prazo.

### Pipefy

- Tratá-lo como **fonte transicional**: hoje autoritativo em marcos, daqui a meses pode ser desligado.
- `cruz-pipefy-fantasmas.json` é o auditor da operação que esquece de fechar — preservar enquanto Pipefy estiver vivo.
- Não construir feature que dependa do Pipefy responder corretamente.

---

## Quando rever este princípio

- Se Rodrigo anunciar nova fase do enxugamento
- Se Pipefy for descomissionado oficialmente
- Se KIRA ganhar nova capacidade (categorização granular, evento estruturado, etc)
- Se a equipe operacional adotar novo sistema
- A cada 90 dias por padrão (auditoria leve)

---

## Referências

- `dados/SCHEMA.md` — convenção de nomenclatura (FASE 0.2 do outro terminal)
- `dados/SCORE-FORMULA.md` — fórmula do índice de saúde (FASE 0.1)
- `dados/CRUZAMENTOS-FRESCOR.md` — inventário de frescor (Q4)
- `dados/archive/README.md` — arquivamento de cruz-* órfãos (FASE 7.1)
- `BACKLOG_REFINAMENTO.md` — backlog histórico (consolidado em 2026-04-24)
