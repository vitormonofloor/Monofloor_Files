# Export Pipefy — preservação pré-descontinuação

Snapshot dos cards do pipe OE (Ordem de Execução) puxados via API Pipefy.
Pipefy será descontinuado — esses arquivos garantem que os dados ficam.

## Arquivos

### `pipefy-export-leve-2026-04-29.json` (143 KB · 591 cards · 9 campos)
- Origem: `https://raw.githubusercontent.com/vitormonofloor/cargo-assistente/main/pipefy_cards.json`
- Atualizado por: `agente_operacional.py` (cargo-assistente, daily 07:30 BRT)
- **Ponto forte**: melhor cobertura de **m²** (73,1% — 432 obras) e **data_entrada/data_fim** (40-49%)
- Campos: `id`, `title`, `phase`, `nome_projeto`, `m2`, `created_at`, `finished_at`, `data_entrada`, `data_fim`

### `pipefy-export-completo-2026-04-27.json` (2,8 MB · 648 cards · 20 campos)
- Origem: `cargo-assistente/cerebro_monofloor/snapshots/pipefy_cards_2026-04-27.json`
- Atualizado por: `agente_historico.py` (cargo-assistente, seg+sex 05:00 BRT)
- **Ponto forte**: tem **phases_history** completo (movimentação por fase com timestamps + duração) e métricas temporais (`t0_criacao`, `t1_inicio_obra`, `t2_fim_obra`, `tf_finished_at`, `dias_total`, `dias_admin`, etc)
- **Limitação**: cobertura de m² é só 40% (mapping de campo customizado a corrigir no `agente_historico.py`)
- Campos: `id`, `title`, `phase_atual`, `finalizado`, `t0_criacao`, `t1_inicio_obra`, `t2_fim_obra`, `tf_finished_at`, `dias_contato_inicio`, `dias_execucao`, `dias_total`, `dias_admin`, `m2`, `valor`, `estado`, `cidade`, `produto`, `nome_projeto`, `phases_history[]`, `total_fases_percorridas`

### CSVs derivados (consulta rápida)
- `pipefy-export-resumo-2026-04-27.csv` (108 KB · 648 linhas) — 1 linha por obra, campos resumo
- `pipefy-export-fases-2026-04-27.csv` (1,1 MB · 8.108 linhas) — 1 linha por fase atravessada por cada obra
- `pipefy-export-2026-04-29.csv` (78 KB · 591 linhas) — versão leve em CSV

## Throughput entregue 2026 (fonte: snapshot leve, melhor cobertura m²)

| Mês | Obras finalizadas | m² entregues |
|-----|-------------------|--------------|
| jan/26 | 22 | 2.049 |
| fev/26 | 33 | 4.211 |
| mar/26 | 25 | 3.314 |

(abril/26 ainda incompleto no snapshot)

## Lacunas identificadas (pra preencher antes do Pipefy ir embora)

- **159 obras (27%) não têm m² preenchido no snapshot leve** — 67% no completo. Custom field do Pipefy provavelmente vazio em parte das obras antigas.
- `valor`, `cidade`, `produto`, `dias_total` retornam 0% no snapshot completo — bug de mapping no `agente_historico.py` (FIELD_*_CANDIDATOS não bate com internal_id real). Corrigir antes de descontinuar Pipefy pra capturar esses dados.

## Próximo refresh

O `agente_historico` roda automaticamente seg+sex 05:00 BRT e commita novo snapshot em `cargo-assistente/cerebro_monofloor/snapshots/`. Próximo: sex 02/05.
