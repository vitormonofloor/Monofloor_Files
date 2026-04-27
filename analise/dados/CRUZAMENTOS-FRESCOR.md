# Frescor dos cruz-*.json

> Última auditoria: **2026-04-27**. Próximas atualizações automáticas via `refresh.sh` (Q4) — mas só do arquivo `cruz-frescor.json`, **não dos cruz-* em si**.
> Documento vivo. Atualizar quando algum cruz-* for regenerado.

## Estado atual (auditado pelo `refresh.sh` em cada execução PESADA)

```json
// dados/cruz-frescor.json
{
  "snapshot_date": "YYYY-MM-DD",
  "cruzamentos": [
    { "arquivo": "cruz-X.json", "gerado_em": "YYYY-MM-DD", "idade_dias": N, "frescor": "fresco|recente|antigo|estatico|sem_data" }
  ],
  "resumo": { "fresco": N, "recente": N, ... }
}
```

### Faixas

| Categoria | Idade | Cor sugerida no painel |
|---|---|---|
| `fresco` | ≤ 1 dia | verde |
| `recente` | 2–7 dias | verde claro |
| `antigo` | 8–30 dias | âmbar |
| `estatico` | > 30 dias | vermelho |
| `sem_data` | sem campo `gerado_em` | cinza |

## Inventário (snapshot 27/04/2026)

### 🟢 Recentes — atualizam via `refresh.sh` PESADO (1×/dia)

Esses 6 arquivos **rodam automaticamente**. São derivados de `dashboard-data.json` ou `details/*.json` que o refresh já gera.

| Arquivo | Gerado | Fonte | Frequência |
|---|---|---|---|
| `cruz-bloqueadores.json` | 24/04 | refresh.sh PESADO | diário |
| `cruz-diagnostico-kira.json` | 24/04 | refresh.sh PESADO (de `details/*`) | diário |
| `cruz-ocorrencias-por-obra.json` | 24/04 | refresh.sh PESADO | diário |
| `cruz-progresso-obras.json` | 24/04 | refresh.sh PESADO | diário |
| `cruz-relatorios.json` | 24/04 | refresh.sh PESADO | diário (amostra 9 obras — Q6) |
| `cruz-tarefas.json` | 24/04 | refresh.sh PESADO | diário |

### 🟡 Antigos — snapshot manual de 15-16/04, sem regeração automática

Esses 13 arquivos foram gerados em scripts ad-hoc (PowerShell/build.ps1, etc) e não rodam via refresh.sh. Cada um precisa de pipeline próprio para virar fresco.

| Arquivo | Gerado | Lógica de regeração | Esforço estimado |
|---|---|---|---|
| `cruz-luana-vs-wesley.json` | 15/04 | Agregar `dashboard-data.AGG.consultor_dist` + Q2_OBRAS por consultor | P |
| `cruz-agend-vt.json` | 15/04 | Filtrar Q2_OBRAS por `fase=AGEND.VT-AFERIÇÃO` + agrupar por idade (3 faixas) | P |
| `cruz-pipefy-fantasmas.json` | 16/04 | Cruzar Q2_OBRAS.faseAtual com painel.status (já temos lógica em I1) | P |
| `cruz-zumbi.json` | 15/04 | Filtrar Q2_OBRAS onde `fase=CLIENTE FINALIZADO` AND `status=ativo` | P |
| `cruz-orfas.json` | 15/04 | Filtrar Q2_OBRAS onde `consultor` é null/vazio/`[]` | P |
| `cruz-cores.json` | 15/04 | Cruzar `details/*.cores` com status — campo na API `details` | M |
| `cruz-reparo.json` | 15/04 | Filtrar Q2_OBRAS onde `status=reparo` + agregar por consultor/prestador | P |
| `cruz-silenciosas.json` | 15/04 | Cruzar com `whatsappSummary` em `details/*` — clima por obra | M |
| `cruz-alertas.json` | 15/04 | Extrair `alertas[]` de `details/*.pendenciaManual.whatsappSummary` | M |
| `cruz-ocorrencias.json` | 15/04 | Extrair `atRisk_detalhe` da API `/api/projects/[id]` (M2 endpoint) | M |
| `cruz-cronograma-fossil.json` | 16/04 | Cruzar `planejamento.monofloor.cloud/api/obras` com painel | G (outra API) |
| `cruz-success-dna.json` | 16/04 | Filtrar `painel-temporal` por obras finalizadas com idade<150d, agregar perfil | M |
| `cruz-receita-risco.json` | 16/04 | (Vitor pediu sem valores — descontinuar) | — |

### 🔴 Sem data

| Arquivo | Tamanho | Status |
|---|---|---|
| `cruz-organograma-real.json` (249 KB) | sem campo `gerado_em` | adicionar campo no script gerador (esforço P) |

## Arquivos arquivados (`dados/archive/`)

Vide `dados/archive/README.md` (FASE 7.1). 7 cruz-* sem consumidor, preservados para restauração futura.

## Próximas ações (não bloqueantes para painéis atuais)

1. **Q4-a — Adicionar campo `gerado_em`** em `cruz-organograma-real.json`. Esforço P.
2. **Q4-b — Migrar 4 cruz-* fáceis para refresh.sh** (`luana-vs-wesley`, `agend-vt`, `zumbi`, `orfas`). Cada um vira ~30 linhas de Python no fim do refresh PESADO. Esforço M total.
3. **Q4-c — Migrar 4 cruz-* médios** (`cores`, `silenciosas`, `alertas`, `success-dna`, `reparo`). Dependem da estrutura `details/*` mais a fundo. Esforço M-G.
4. **Q4-d — `cronograma-fossil`** depende da API `planejamento.monofloor.cloud` (outra fonte). Coordenar com Rodrigo. Esforço G.
5. **Q4-e — Descontinuar `receita-risco`** (Vitor pediu sem valores monetários).

## Como o painel deve usar `cruz-frescor.json`

Componente reutilizável em cada lab/seção que consome um cruz-*:

```js
// pseudo
const frescor = await fetch('dados/cruz-frescor.json').then(r => r.json());
const meu = frescor.cruzamentos.find(c => c.arquivo === 'cruz-X.json');
if (meu.idade_dias > 30) {
  // mostra badge vermelho "estático há N dias"
} else if (meu.idade_dias > 7) {
  // badge âmbar
} else {
  // verde
}
```

Componente similar ao `headline-badge.js` (FASE 0.4) — pode ser feito como `cruz-frescor-badge.js` em iteração futura.
