# Schema dos JSONs — Central de Qualidade

> Mapa do que cada JSON contém + norma para quem vier depois.
> Última revisão: 2026-04-27.

## Princípio

**Campos vindos da API** mantêm o nome de origem (camelCase, herdado de `cliente.monofloor.cloud`).
**Campos calculados localmente** usam `snake_case`.
**Top-level de JSONs novos** usa `snake_case`.

Esta convenção é **pragmática**: refatorar nomes da API quebra todos os painéis que leem o dado. Documentar a fronteira evita confusão futura sem quebrar o que existe.

---

## Arquivos-base

### `headline.json` (FONTE ÚNICA dos números-âncora) ⭐
**Lido por:** hub.html, dashboard.html, atena.html, indicadores-v2.html, obras-mapa.html (FASE 1)
**Gerado por:** `refresh.sh` (modo PESADO, fim do PYEOF)

| Campo | Tipo | Origem | Descrição |
|---|---|---|---|
| `schema_version` | int | constante | versão do contrato — incrementar se quebrar campos |
| `snapshot_date` | "YYYY-MM-DD" | calculado | data do snapshot que originou os números |
| `atualizado_em` | ISO-8601 UTC | calculado | quando o refresh.sh terminou |
| `ativas` | int | calculado | total de obras ativas (não finalizado/cancelado) |
| `score` | int 0-100 | calculado | score de saúde — fórmula em `SCORE-FORMULA.md` |
| `score_componentes.zumbi_pct` | float | calculado | % zumbi sobre ativas |
| `score_componentes.orfas_pct` | float | calculado | % órfãs sobre ativas |
| `score_componentes.ciclo_180_pct` | float | calculado | % obras 180+ sobre ativas |
| `score_componentes.ciclo_mediano` | int | calculado | dias mediana de idade |
| `score_componentes.ciclo_meta` | int | constante 150 | meta de ciclo em dias |
| `score_componentes.lote_vt_270d` | int | calculado | n. obras presas em VT 258-262 dias |
| `alertas.zumbi` | int | calculado | n. obras em CLIENTE FINALIZADO sem fechar |
| `alertas.orfas` | int | calculado | n. obras sem consultor |
| `alertas.lote_vt_270d` | int | calculado | mesmo que score_componentes |
| `alertas.ciclo_270_plus` | int | calculado | n. obras com idade ≥ 270 |
| `alertas.novos_hoje` | int | calculado | total de eventos delta vs ontem |
| `fonte` | string | constante | origem dos dados |

---

### `painel-temporal.json` (1037 obras com idade)
**Lido por:** dashboard.html, obras-mapa.html, ATENA scan
**Gerado por:** `refresh.sh` modo PESADO (linha ~178)

Array de obras. Cada obra tem campos da API (camelCase) + calculados (snake_case):

| Campo | Tipo | Origem | Descrição |
|---|---|---|---|
| `id` | UUID | API | identificador único |
| `clienteNome` | string | API | nome do cliente |
| `projetoCidade` | string | API | cidade da obra |
| `status` | string | API | aguardando_execucao, em_execucao, finalizado, etc |
| `faseAtual` | string | API | fase no Pipefy (ex: "CLIENTE FINALIZADO") |
| `consultorNome` | string\|null | API | nome do consultor (null = órfã) |
| `projetoMetragem` | string | API | m² (string, converter pra float) |
| `pipefyCardId` | string | API | id do card no Pipefy |
| `pipefyCreatedAt_api` | ISO-8601 | API | data criação Pipefy via API |
| `pipefy_snapshot_created_at` | "YYYY-MM-DD" | calculado | data via snapshot do cargo-assistente |
| `data_radar` | "YYYY-MM-DD" | calculado | data canônica usada para idade (prefere snapshot, fallback API) |
| `data_radar_fonte` | enum | calculado | "pipefy_snapshot" \| "pipefy_api" \| "sem_data" |
| `idade_dias` | int\|null | calculado | hoje - data_radar |
| `ativa` | bool | calculado | status not in {finalizado, concluido, cancelado} |

---

### `dashboard-data.json` (185 KB — fonte do dashboard executivo)
**Lido por:** dashboard.html (`fetch('dados/dashboard-data.json')`)
**Gerado por:** `refresh.sh` modo PESADO (linha ~457)

Top-level keys:
- `snapshot_date` — "YYYY-MM-DD"
- `AGG` — agregados (snake_case puro)
- `Q2_OBRAS` — array de obras com **nomes ENCURTADOS** (`cliente`, `fase`, `consultor`, `m2`, `idade`) — diferente de painel-temporal! ⚠
- `EXT` — extensões (mistura snake e camelCase: `vt_por_consultor`, `atRiskTop`, `sem_wa_top`) ⚠
- `Q1_*`, `Q3_*`, `Q4_*` — dados das seções homônimas
- `SYNC_*` — flags de sincronia

#### `AGG` (snake_case)

| Campo | Tipo | Descrição |
|---|---|---|
| `total_ativas` | int | obras ativas |
| `total_obras` | int | total no JSON (= ativas, esse arquivo só carrega ativas) |
| `status_dist` | dict | {status: count} |
| `n_180_plus` | int | obras com idade ≥ 180 |
| `n_270_plus` | int | obras com idade ≥ 270 |
| `n_lt90` | int | obras com idade < 90 |
| `n_90_180` | int | obras com idade entre 90 e 180 |
| `metragem_total` | float | soma de m² |
| `idade_media` | float | média de idade |
| `idade_mediana` | int | mediana |
| `sem_consultor_ativas` | int | n. órfãs |
| `top_consultores` | array | [{nome, n}] |
| `top_fases` | array | [{fase, n}, ...] (top 10) |

---

### `backlog-historico.json` (rolling 90 dias)
**Lido por:** atena.html (sparklines), dashboard.html (evolução)
**Gerado por:** `refresh.sh` (linha ~390)

Array de entries diárias (snake_case puro):

```
[
  {
    "date": "2026-04-27",
    "indices": {
      "zumbi": {"total": int, "ids": [...], "clientes": {id: nome}, "idades": {id: dias}},
      "lideres_ocultos": {"total": int, "ids": [...], "obras_lideradas": {...}},
      "orfas": {"total": int, "ids": [...], "clientes": {...}},
      "conflitos": {"total": int, "nomes": [...], "detalhe": {...}},
      "lote_vt": {"total": int, "ids": [...], "clientes": {...}}
    },
    "mudancas_vs_anterior": {
      "zumbi_saiu": [{...}], "orfas_atribuida": [{...}],
      "lideres_formalizado": [...], "conflitos_resolvido": [...],
      "lote_vt_destravada": [...]
    } | null
  },
  ...
]
```

⚠ Limitação atual: só 5 entries (15/04, 24-27/04). Falha de 9 dias entre 15 e 24/04. Sparklines ficam ruidosas.

---

### `data.json` (modo LEVE, atualizado a cada 30 min)
**Lido por:** indicadores-v2.html (parcial), modelagem.html

```
{
  "projects": [...],          // /api/projects?limit=2000
  "dashboard": {...},          // /api/dashboard
  "analise": {...},            // /api/analise
  "escalacao": [...],          // /api/escalacao-diaria
  "equipes": [...],            // /api/equipes
  "fetchedAt": "ISO-8601 UTC"
}
```

---

### `snapshots/YYYY-MM-DD.json` (1 por dia)
**Lido por:** atena.html (tab EVOLUÇÃO)
**Gerado por:** `refresh.sh` (linha ~189)

```
{
  "date": "YYYY-MM-DD",
  "fetchedAt": "ISO-8601",
  "ativas": [
    {"id": UUID, "clienteNome": str, "status": str, "faseAtual": str, "consultorNome": str, "idade_dias": int},
    ...
  ]
}
```

⚠ Cobertura atual: 4 dias só (24-27/04).

---

## Cruzamentos `cruz-*.json` (29 arquivos)

| Padrão observado | Exemplo |
|---|---|
| Top-level com metadata + dados | `{gerado_em, total_obras, resumo, obras, ranking_*}` |
| Naming: snake_case na maioria | `cruz-bloqueadores.json` |
| Mistura ocasional | `cruz-diagnostico-kira.json` (`com_situacao_atual` snake + `obras` ambíguo) |
| Geração: scripts ad-hoc | sem padrão único de regeneração |

**Status real:** apenas ~10 dos 29 são consumidos por painéis. Outros são lixo histórico. FASE 7.1 arquiva os órfãos em `dados/archive/`.

---

## Divergências conhecidas (registrar, não corrigir)

| # | Onde | Divergência | Decisão |
|---|---|---|---|
| 1 | painel-temporal vs Q2_OBRAS | `clienteNome` vs `cliente`, `faseAtual` vs `fase`, `projetoMetragem` vs `m2`, `idade_dias` vs `idade` | manter — Q2_OBRAS é versão slim para o dashboard, painel-temporal é fonte completa |
| 2 | EXT do dashboard-data | mistura `vt_por_consultor` (snake) com `atRiskTop` (camel) | rastrear: corrigir só quando um campo for tocado por outro motivo |
| 3 | painel-temporal | mistura `clienteNome` (camel API) com `idade_dias` (snake calculado) | esperado pelo princípio (origem mista) |
| 4 | cruz-* | esquemas heterogêneos por arquivo | aceitável — cada cruzamento responde uma pergunta diferente |

---

## Norma para JSONs novos

1. Top-level **sempre** snake_case
2. Adicionar `schema_version: int` para JSONs com contrato público (lidos por mais de 1 painel)
3. Adicionar `gerado_em` ou `atualizado_em` em ISO-8601 UTC
4. Documentar no SCHEMA.md **antes** de painel passar a ler
5. Se o JSON sai de campos da API, manter o nome da API; campos derivados em snake_case

---

## Como descobrir o schema rapidamente

```powershell
$d = Get-Content 'caminho.json' -Raw | ConvertFrom-Json
$d.PSObject.Properties.Name      # top-level keys
$d.AGG.PSObject.Properties.Name  # nested
$d[0].PSObject.Properties.Name   # se for array
```

Em bash com jq:

```bash
jq 'keys' arquivo.json                       # top-level
jq '.AGG | keys' arquivo.json                # nested
jq '.[0] | keys' arquivo.json                # se array
```
