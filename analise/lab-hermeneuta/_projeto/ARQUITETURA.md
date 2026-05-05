# 3 · ARQUITETURA · Pipeline + scripts + data-flow

## Diagrama macro

```
                 ┌──────────────────────────────────────┐
                 │  PAINEL DE OBRAS (Kira · backend)    │
                 │  cliente.monofloor.cloud/api/...     │
                 │  · transcrição de áudio              │
                 │  · descrição de foto                 │
                 │  · indexação de mensagens            │
                 └─────────────────┬────────────────────┘
                                   │ GET (sem auth)
                                   ▼
                 ┌──────────────────────────────────────┐
                 │   selecionar_piloto.py               │
                 │   --todas-ativas → 227 obras         │
                 │   gera: piloto.json                  │
                 └─────────────────┬────────────────────┘
                                   ▼
                 ┌──────────────────────────────────────┐
                 │   coletar_painel.py                  │
                 │   GET /messages?source=telegram      │
                 │   GET /messages?source=whatsapp      │
                 │   limit=2000 · janela=90d            │
                 │   gera: telegram-snapshot.json       │
                 └─────────────────┬────────────────────┘
                                   ▼
       ┌───────────────────────────┴──────────────────────────┐
       ▼                           ▼                          ▼
extrair_timeline      aplicar_regua    extrair_equipe/cores/kira
 (bloco telegram                                              │
  + eventos)                                                  │
       │                           │                          │
       └─────────────┬─────────────┴──────────────────────────┘
                     ▼
          ┌──────────────────────────┐
          │ discordancias-v3.json    │ ← injeção sequencial · 230 obras
          │ (JSON principal)         │
          └──────────────┬───────────┘
                         ▼
          ┌──────────────────────────┐
          │ inferir_consultor        │
          │ sanitizar_json           │
          │ registrar_kpis           │
          │ marcar_refresh_status    │
          │ sentinela (9 checks)     │
          └──────────────┬───────────┘
                         ▼
          ┌──────────────────────────┐
          │ publicar.py              │
          │ · git push pub repo      │
          │ · wrangler deploy        │
          └──────────────┬───────────┘
                         ▼
              ┌──────────────────────┐
              │ lab.monofloor.cloud  │
              │ (CF Worker + assets) │
              └──────────────────────┘
```

## Pipeline detalhado · `varredura.py`

```
1.  adquirir_lock              · PID alive check + TTL 30min
2.  fazer_backup               · rolling 14d · dados/backups/
3.  cp snapshot → snapshot-prev · pra calcular diff (CANDIDATO A CORTAR)
4a. selecionar_piloto.py       · --todas-ativas · 227 obras
4b. coletar_painel.py          · Painel API · TG+WA · 2000/90d
5.  calcular_diff_msgs         · qtd msgs novas por obra
6.  extrair_timeline.py        · bloco telegram + eventos · dossiê opcional
7.  aplicar_regua.py           · bucket SLA + marcos PP:001 + fallback painel
8.  extrair_equipe.py          · cadastro × telegram + overrides
9.  extrair_cores.py           · cores + tendência · regex+keyword filter
10. extrair_kira_whatsapp.py   · espelha pendenciaManual.whatsappSummary
11. inferir_consultor.py       · overrides consultor formal × real
12. sanitizar_json.py          · remove flags + campos mortos
13. registrar_kpis.py          · série temporal pra sparkline
14. marcar_refresh_status      · função interna · flag stale por obra
14b. cruzar_kira.py            · 4 regras determinísticas Kira × Operação · veredicto + urgência + flags + trilha
15. sentinela.py               · 9 checks · gera status.json
16. publicar.py                · atomic + git push + wrangler deploy
17. liberar_lock               · finally
```

## Scripts em `agente/`

### Orquestração e infra
| Script | Função | Notas |
|---|---|---|
| `_util.py` | Helpers · write_discord · validar_discord · fazer_backup · marcar_step_falho · limpar_erros_pipeline · setup_utf8 | Importado por todos |
| `varredura.py` | Orquestrador raiz · adquire lock · executa 13 etapas · libera lock | Lock anti-concorrência com PID alive |
| `arquivar_versao.py` | Backup pré-IA · suporta `--evolucao OBRA_ID` | Manual |

### Coleta
| Script | Função | I/O |
|---|---|---|
| `telethon/selecionar_piloto.py` | `--todas-ativas` lista 227 ativas; `--todas` modo legado pareado | painel-snapshot → piloto.json |
| `telethon/coletar_painel.py` | Painel API · Telegram + WhatsApp · 2000/90d · ordena cronológico | piloto.json → telegram-snapshot.json |

### Enriquecimento (lê snapshot · escreve discord-v3)
| Script | Função |
|---|---|
| `extrair_timeline.py` | Bloco `telegram` (ultima_msg/dias_silencio/tom_grupo/total_msgs) + `timeline_recente` |
| `aplicar_regua.py` | `regua` (bucket SLA + marcos PP:001) · fallback `dataExecucaoPrevista` quando sem dossiê |
| `extrair_equipe.py` | `equipe_em_campo` (cadastro × telegram + overrides) |
| `extrair_cores.py` | `cores` (regex `[ \t]*` + filtro `KEYWORDS_NAO_COR`) |
| `extrair_kira_whatsapp.py` | `kira_whatsapp` (espelha `pendenciaManual.whatsappSummary`) |
| `inferir_consultor.py` | `consultor` (overrides Repullo, Paula, Maria Heydi, Mayara) |
| `sanitizar_json.py` | Remove `cliente_ausente` + campos mortos |
| `registrar_kpis.py` | Append em `historico-kpis.json` · sparkline |

### Saúde e publicação
| Script | Função |
|---|---|
| `sentinela.py` | 9 checks · drift directional · pipeline-errors flag · gera `status.json` |
| `publicar.py` | Atomic write · git push pub repo · wrangler deploy CF (PATH injection pra Windows Node) |

### Veredicto principal · determinístico (no pipeline · 14b)
| Script | Função |
|---|---|
| `cruzar_kira.py` | 4 regras determinísticas (R1-R4) · usa fontes Kira (tagKira/situacaoAtual/ocorrencias) + telegram block · gera veredicto + urgência + flags + trilha auditável |

### IA externa · FALLBACK opcional (não no pipeline)
| Script | Função |
|---|---|
| `analisar_recorte.py` | Recebe `--obra-ids` ou `--todas-ativas` · GitHub Models gpt-4o-mini · injeta veredicto IA · útil pra recortes manuais · LIMITE 150 req/dia descoberto em 2026-05-05 |
| `secretario-prompt.md` | Briefing do subagente "secretário" (legado IA manual) |
| `hermeneuta-prompt.md` | Briefing v3 do agente HERMENEUTA (legado IA manual) |

### Legados (corte programado no Caminho B · frente B3)
| Script | Status |
|---|---|
| `telethon/monitorar.py` | Telethon morto · não está mais no varredura |
| `telethon/listar_grupos.py` | Gerava grupos.json via Telethon |
| `telethon/grupos.json` | Pareamento Telegram (modo legado --todas) |
| `telegram-snapshot-prev.json` | Só serve pra diff de mensagens novas · valor marginal |

## Data-flow

```
Painel API
   │
   ▼
piloto.json (227 obras IDs)
   │
   ▼
telegram-snapshot.json (corpus bruto · TG + WA por obra)
   │
   ├────► discordancias-v3.json (cards finais)
   │      ▲
   │      │ injeção: timeline, regua, equipe, cores, kira, consultor
   │      │
   ├────► historico-kpis.json (série temporal)
   │
   ├────► status.json (saúde do pipeline)
   │
   └────► pipeline-errors.json (flags de falha)

discordancias-v3.json
   │
   ▼ publicar.py
   │
   ├────► Monofloor_Files git push (histórico)
   │
   └────► lab-hermeneuta-pub git push + wrangler deploy
              │
              ▼
         lab.monofloor.cloud (CF Worker)
              │
              ▼ frontend fetch
         Lab Orion no browser
```

## APIs externas usadas

### Painel de Obras (`cliente.monofloor.cloud`)
- `GET /api/projects?ativa=true` · lista obras (1038 total · 227 ativas)
- `GET /api/projects/{id}` · detail por obra (clienteNome, faseAtual, situacaoAtual, tagKira, etc)
- `GET /api/projects/{id}/messages?source=telegram&limit=2000` · mensagens TG
- `GET /api/projects/{id}/messages?source=whatsapp&limit=2000` · mensagens WA
- Sem auth · público · sem rate limit conhecido

### GitHub Models (`models.inference.ai.azure.com`)
- `POST /chat/completions` · gpt-4o-mini
- Auth via `GITHUB_TOKEN` · escopo `repo`
- Gratuito · 8k req/dia
- Usado por `analisar_recorte.py` e (futuro) Caminho B B1

### CF Workers + Static Assets
- Repo: `vitormonofloor/orion-pub` (separado do Monofloor_Files)
- Auth: Basic Auth · cookie 24h · `LAB_USER` + `LAB_PASS`
- `run_worker_first=true` garante que auth roda antes de servir assets
- Domain: `lab.monofloor.cloud` (Cloudflare custom)
- Deploy via `wrangler deploy` (publicar.py executa)

### GitHub Actions (workflow `analisar-orion.yml` · DORMENTE)
- Trigger: `workflow_dispatch` ou `repository_dispatch type=analisar-orion`
- Permissions: `contents: write` + `models: read`
- Steps: checkout · python · node22 · wrangler · roda analisar_recorte · publica
- Status: pronto mas dormente · ver `project_orion_opcao_b_pausada.md`

## Estrutura de repos

```
Monofloor_Files (este repo)
├── analise/lab-hermeneuta/         ← FONTE CANÔNICA
│   ├── index.html                  ← Lab Orion HTML
│   ├── agente/                     ← Pipeline Python
│   ├── dados/                      ← JSONs gerados
│   ├── _projeto/                   ← VOCÊ ESTÁ AQUI
│   └── ROADMAP_CAMINHO_B.md
├── workers/analisar-orion/         ← CF Worker proxy (Opção B · dormente)
└── .github/workflows/analisar-orion.yml  ← Action (Opção B · dormente)

lab-hermeneuta-pub (repo separado · público)
├── public/
│   ├── index.html                  ← copiado de Monofloor_Files
│   └── dados/                      ← copiados de Monofloor_Files
├── src/index.js                    ← CF Worker com Basic Auth
└── wrangler.toml                   ← config deploy
```

`publicar.py` mantém os dois sincronizados.
