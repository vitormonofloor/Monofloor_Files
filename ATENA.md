# ATENA -- Auditor Estrategico da Central de Qualidade

> Deusa da sabedoria. Varre diariamente o dashboard executivo com 5 olhos heuristicos e identifica problemas, lacunas e oportunidades.

---

## Dados Tecnicos

| Campo | Valor |
|---|---|
| **Repositorio** | `vitormonofloor/Monofloor_Files` |
| **Deploy** | GitHub Actions (cron diario) |
| **Workflow** | `.github/workflows/atena.yml` |
| **Ciclo** | 1x por dia as 10h UTC (07h BR) |
| **Versao atual** | v1.0 |
| **Dashboard** | `vitormonofloor.github.io/Monofloor_Files/analise/atena.html` |

## Pipeline

1. Cron dispara `atena-scan.sh` via GitHub Actions
2. Le `dashboard.html`, `painel-temporal.json`, `cruz-*.json`, `backlog-historico.json`
3. Executa 5 analises heuristicas (sem LLM):
   - **UX**: IDs duplicados, TODOs, tamanho HTML, scripts inline, console.log, acessibilidade
   - **Insights**: concentracao consultores, idade media/mediana/P90, fases top, deltas vs historico
   - **Lacunas**: campos do painel nao usados no dashboard, cruzamentos ausentes
   - **Bugs**: zumbis, orfas, datas estranhas, idades extremas, strings hardcoded, coerencia
   - **Oportunidades**: cruzamentos nao explorados, fases gargalo, consultores sobrecarregados, obras sem data
4. Gera 5 JSONs + index.json em `analise/dados/atena/`
5. Commita automaticamente via monofloor-bot

## Estrutura de Dados

```
analise/dados/atena/
  index.json                    # indice mestre (sumario, varreduras, saude)
  2026-04-16-ux.json           # achados do olho UX
  2026-04-16-insights.json     # achados do olho Insights
  2026-04-16-lacunas.json      # achados do olho Lacunas
  2026-04-16-bugs.json         # achados do olho Bugs
  2026-04-16-oportunidades.json # achados do olho Oportunidades
```

Cada olho segue o schema:
```json
{
  "olho": "bugs",
  "executado_em": "2026-04-16T10:00:00Z",
  "achados": [
    {"severidade": "alta|media|baixa", "titulo": "...", "descricao": "...", "evidencia": "..."}
  ],
  "metricas": {...},
  "comparativo_vs_anterior": "..."
}
```

## Interface

`analise/atena.html` -- mesmo design system Monofloor (#0a0a0a, #c4a77d, Inter, JetBrains Mono).
- Hero com indice de saude (arc SVG) + 4 KPIs
- 5 abas (UX, Insights, Lacunas, Bugs, Oportunidades)
- Achados ordenados por severidade (alta primeiro)
- Metricas por olho
- Linha do tempo das varreduras

## Integracao com Dashboard

Botao discreto no header do `dashboard.html`:
- Link com icone diamante + badge de contagem alta severidade
- Badge carrega via fetch do `dados/atena/index.json`
- Verde se 0, vermelho se >0

## Conexoes

```
KIRA (cliente.monofloor.cloud)
  |
refresh.sh (30min) --> dados/ (painel-temporal, cruz-*, snapshots)
  |
ATENA (diario 07h BR)
  |-> Le dados/ + dashboard.html
  |-> Gera analise/dados/atena/*.json
  |-> atena.html visualiza

ARGOS (Railway, 6h) --> indicadores.html
HERMES (Railway, 8h) --> analise.html
ATENA (GH Actions, 7h) --> atena.html
```

## Evolucao

| Versao | Data | Mudanca |
|---|---|---|
| v1.0 | 16/04/2026 | 5 olhos heuristicos, interface HTML, badge no dashboard |

---

*Criado em: 16/04/2026*
*Tags: #agente #auditor #atena #heuristicas #qualidade*
