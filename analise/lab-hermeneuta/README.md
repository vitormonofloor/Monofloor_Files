# Lab HERMENEUTA — sandbox isolada

> Experimento de agente que **interpreta** o que KIRA capturou e confronta com o status declarado pelo painel-amigo.

**Criado:** 2026-04-28
**Risco no site principal:** ZERO — pasta autônoma, não linkada do hub/dashboard/atena/labs.html.
**Acesso:** abrir direto `analise/lab-hermeneuta/index.html` (URL não publicada).

## Pergunta que o lab responde

> *"Onde o que o sistema diz sobre uma obra discorda do que o cliente está dizendo no grupo?"*

Caso emblemático: GUSTAVO DE SOUZA PEREIRA aparece como **pausado · 273d** no painel, mas o Telegram tem mensagem recente "obra finalizada". KIRA viu (capturou na narrativa). O painel não reflete. **Hermeneuta detecta essa discordância.**

## Como funciona

```
1. Filtro de candidatos (heurística local · sem LLM)
   → top N obras "suspeitas" (>180d OU pausado OU clima=tenso OU sem WA)
2. Para cada obra suspeita:
   - Reúne narrativa KIRA (whatsappSummary + tagKira + situacaoAtual + alertas)
   - Reúne status declarado (painel-temporal: status, faseAtual, idade)
   - Despacha subagente Claude (via Claude Code) com prompt de interpretação
3. Subagente retorna JSON: { concorda, estado_real, confianca, evidencia }
4. Consolida em discordancias.json
5. index.html lista discordâncias com evidência textual
```

## Sem API key, sem GH Actions

- Roda **sob demanda** via Claude Code (este Claude)
- Vitor abre o terminal e pede *"rodar hermeneuta nas 10 primeiras obras"*
- Custo zero adicional (já paga Claude Code)
- Não automatiza por cron — futuro pode migrar pra GH Actions

## Estrutura

```
lab-hermeneuta/
├── README.md                ← este arquivo
├── index.html               ← tela do lab
├── dados/
│   ├── details-snapshot/    ← 1028 arquivos copiados (cópia congelada de KIRA)
│   ├── painel-snapshot.json ← cópia de painel-temporal.json
│   ├── cruz-silenciosas-snapshot.json
│   ├── cruz-ocorrencias-snapshot.json
│   ├── cruz-diagnostico-kira-snapshot.json
│   └── discordancias.json   ← saída do agente (gerada sob demanda)
└── agente/
    ├── hermeneuta-prompt.md ← prompt versionado · ajustar tom aqui
    └── obras-suspeitas.json ← lista filtrada de IDs (não as 227 todas)
```

## Quando rodar

Atualmente snapshot é congelado em **2026-04-28**. Pra testar com dados frescos, basta refazer o `cp -r` dos arquivos de `analise/dados/`.

## Próximos passos (após validação)

- Se interpretações ficarem boas → integra como chip "X9: discordâncias painel × KIRA" no Banner Achados
- Se prompt precisar ajuste → versiona em `hermeneuta-prompt.md`
- Se quiser cron automático → migra pra GH Actions (precisa decidir LLM)
