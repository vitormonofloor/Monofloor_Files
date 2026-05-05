# 7 · INVENTÁRIO · Mapa físico · onde mora cada coisa

> Toda peça do projeto Orion · com path · função · estado

## Repos envolvidos

| Repo | Local | GitHub | Função |
|---|---|---|---|
| `Monofloor_Files` | `C:\Users\vitor\Monofloor_Files\` | `vitormonofloor/Monofloor_Files` | **CANÔNICO** · pipeline + agente + dados |
| `lab-hermeneuta-pub` | `C:\Users\vitor\lab-hermeneuta-pub\` | `vitormonofloor/orion-pub` | Frontend público + CF Worker |

`publicar.py` no canônico mantém o pub sincronizado.

## Monofloor_Files · arquivos do Orion

### `analise/lab-hermeneuta/` · raiz do projeto

| Arquivo | Estado | Função |
|---|---|---|
| `index.html` | ATIVO · canônico | Lab Orion HTML · publicar.py copia pro pub |
| `RETOMAR.md` | ATIVO · atualizado 2026-05-04 | Overview rápido pra agentes |
| `README.md` | ATIVO | Setup + visão geral |
| `ROADMAP_CAMINHO_B.md` | ATIVO · pendente execução | 5 frentes do refactor estrutural |
| `_projeto/` | ATIVO · esta pasta | Síntese do desenvolvimento |
| `agente/` | ATIVO | Pipeline Python |
| `dados/` | ATIVO · gerado | JSONs de saída |

### `analise/lab-hermeneuta/agente/` · scripts

| Script | Estado | Encaixe |
|---|---|---|
| `_util.py` | ATIVO | Helpers compartilhados |
| `varredura.py` | ATIVO · orquestrador | Raiz do pipeline · 13 etapas |
| `extrair_timeline.py` | ATIVO · refatorado 2026-05-04 | Bloco telegram + timeline · dossiê opcional |
| `aplicar_regua.py` | ATIVO | Bucket SLA + marcos PP:001 |
| `extrair_equipe.py` | ATIVO | Cadastro × Telegram + overrides |
| `extrair_cores.py` | ATIVO | Cores + tendência |
| `extrair_kira_whatsapp.py` | ATIVO | Espelha pendenciaManual |
| `inferir_consultor.py` | ATIVO | Overrides consultor |
| `sanitizar_json.py` | ATIVO | Limpeza |
| `registrar_kpis.py` | ATIVO | Série temporal |
| `sentinela.py` | ATIVO | 9 checks |
| `publicar.py` | ATIVO | Atomic + git push + wrangler deploy |
| `analisar_recorte.py` | ATIVO · MANUAL | IA gpt-4o-mini · GitHub Models |
| `arquivar_versao.py` | ATIVO · MANUAL | Backup pré-IA |
| `secretario-prompt.md` | ATIVO | Briefing IA secretário |
| `hermeneuta-prompt.md` | ATIVO | Briefing IA HERMENEUTA v3 |

### `analise/lab-hermeneuta/agente/telethon/` · coleta

| Script | Estado | Função |
|---|---|---|
| `selecionar_piloto.py` | ATIVO | `--todas-ativas` (227 obras) ou `--todas` (legado) |
| `coletar_painel.py` | ATIVO · refatorado 2026-05-04 | Painel API · TG+WA · 2000/90d |
| `monitorar.py` | LEGADO | Telethon morto · NÃO chamado mais |
| `listar_grupos.py` | LEGADO | Gerava grupos.json via Telethon |
| `grupos.json` | LEGADO | Pareamento Telegram (modo --todas) |
| `piloto.json` | GERADO | Output de selecionar_piloto |
| `telegram-snapshot.json` | GERADO | Corpus atual (TG + WA por obra) |
| `telegram-snapshot-prev.json` | GERADO · LEGADO uso | Cópia anterior pra diff |
| `README-SETUP.md` | DOCS | Setup Telethon (legado) |

**Cortar no Caminho B B3:** `monitorar.py`, `listar_grupos.py`, `grupos.json`, `telegram-snapshot-prev.json`.

### `analise/lab-hermeneuta/dados/` · JSONs gerados

| Arquivo | Função |
|---|---|
| `discordancias-v3.json` | **JSON principal** · 230 obras · cards finais |
| `painel-snapshot.json` | Lista 1038 obras (ativas + finalizadas) |
| `details-snapshot/{id}.json` | Detail por obra (cliente, fase, situação, KIRA) |
| `dossies/{id}.json` | OPCIONAL · enriquece timeline (legado IA manual) |
| `status.json` | Sentinela output (9 checks) |
| `pipeline-errors.json` | Flags de falha por step |
| `historico-kpis.json` | Série temporal pra sparkline |
| `cores-catalogo.json` | Hex codes das cores Monofloor (12 ainda chutados) |
| `equipes.json` | Cadastro de equipes · cruzar com Telegram |
| `backups/` | Rolling 14 dias × 2 varreduras = 28 backups |
| `historico/` | Backups manuais pré-IA (`arquivar_versao.py`) |

### Outros caminhos do Monofloor_Files

| Path | Estado | Função |
|---|---|---|
| `workers/analisar-orion/` | DORMENTE · pronto | CF Worker proxy pra Opção B click→IA |
| `.github/workflows/analisar-orion.yml` | DORMENTE · pronto | Action trigger via repository_dispatch |

## lab-hermeneuta-pub · frontend público

```
lab-hermeneuta-pub/
├── public/
│   ├── index.html              ← cópia do canônico (publicar.py mantém)
│   ├── dados/                  ← cópia de dados/ (publicar.py mantém)
│   ├── style.css               ← estilo Lab Orion
│   ├── tour.js                 ← onboarding
│   └── ...                     ← assets diversos
├── src/
│   └── index.js                ← CF Worker · Basic Auth · cookie 24h · run_worker_first
├── wrangler.toml               ← config CF · LAB_USER + LAB_PASS env vars
└── README.md                   ← deploy + setup
```

URL: `https://lab.monofloor.cloud` · custom domain CF.

## Memórias relacionadas (em `~/.claude/projects/.../memory/`)

| Arquivo | Tipo | Função |
|---|---|---|
| `personality_qualidade_monofloor.md` | personality | DNA da dupla · LER PRIMEIRO de tudo |
| `project_orion_caminho_a_2026_05_04.md` | project | Estado pós-fix de hoje · Caminho B é próximo |
| `project_orion_opcao_b_pausada.md` | project | Worker click→IA dormente · só ativar com novo usuário |
| `project_orion_cores_oficiais.md` | project | 12 hex codes pendentes |
| `project_hermeneuta_lab.md` | project | LEGADO · pré-rebranding · histórico |
| `project_sessao_2026_05_01_orion_noite.md` | project | Sessão fechamento Lab + Hub |
| `feedback_verificar_consumidor_antes_coletor.md` | feedback | Schema fantasma · grep do consumidor |
| `feedback_apresentar_decisoes.md` | feedback | Impacto > jargão dev |
| `feedback_propor_com_honestidade.md` | feedback | Auto-crítica honesta antes de propor |
| `feedback_editar_canonico_nao_derivado.md` | feedback | Editar fonte · não derivado |
| `feedback_git_push_ci.md` | feedback | Git push em CI sem retry silencioso |
| `feedback_inventar_identidade_visual.md` | feedback | Não inventar visual · conferir fonte |
| `reference_orion_atualizar_dados.md` | reference | Playbook do botão ↻ |

## Tokens / secrets necessários

| Secret | Onde guardar | Usado por |
|---|---|---|
| `GITHUB_TOKEN` | Env var local Vitor | `analisar_recorte.py` |
| `LAB_USER` + `LAB_PASS` | CF Worker env (orion-pub) | Basic Auth do Lab |
| `GH_TOKEN` (Worker) | CF (DORMENTE) | Opção B reativada |
| `PAT_LAB_PUB` | GitHub Secrets (DORMENTE) | Action analisar-orion |
| `CLOUDFLARE_API_TOKEN` | GitHub Secrets (DORMENTE) | Action wrangler deploy |
| `CLOUDFLARE_ACCOUNT_ID` | GitHub Secrets (DORMENTE) | Action wrangler deploy |

## Commits importantes do Caminho A (2026-05-04)

| Hash | Conteúdo |
|---|---|
| `5151bde` | 🔧 fix: cobertura Telegram 10→190 obras · bloco órfão resolvido |
| `debcfb6` | 📋 docs: ROADMAP Caminho B · refactor estrutural Lab Orion |
| `97a209a` | 📋 docs: RETOMAR.md atualizado · estado pós-Caminho A |

## URL ativa

- **Lab Orion público:** https://lab.monofloor.cloud
- **Painel de Obras (fonte):** https://cliente.monofloor.cloud
- **GitHub Models (IA):** https://models.inference.ai.azure.com
- **GitHub repos:**
  - https://github.com/vitormonofloor/Monofloor_Files
  - https://github.com/vitormonofloor/orion-pub
