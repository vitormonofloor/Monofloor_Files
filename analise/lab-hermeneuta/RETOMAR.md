# 🎯 RETOMAR · contexto rápido pra qualquer agente

> **Última atualização:** 2026-05-04 · noite (Caminho A entregue · cobertura 10→190 cards reais)
> Se você é um agente IA chegando agora · LEIA este arquivo primeiro. Em ~30s você terá contexto suficiente pra trabalhar sem confundir nada.

## ⚠ ANTES DE TUDO — ler na ordem

1. `personality_qualidade_monofloor.md` (na pasta de memória) — DNA da dupla com 19+ princípios + auto-crítica honesta antes de propor
2. `project_orion_caminho_a_2026_05_04.md` (memória) — narrativa do fix de hoje · achado do schema fantasma
3. `feedback_verificar_consumidor_antes_coletor.md` (memória) — learning estrutural · grep do consumidor antes de mexer no coletor
4. Este arquivo (estado técnico)
5. `ROADMAP_CAMINHO_B.md` (este diretório) — 5 frentes pra refactor estrutural

## O que é este lab em 1 frase

Sandbox que cruza grupos Telegram + WhatsApp **via API do Painel de Obras** (Kira já transcreveu áudios e descreveu fotos · nossa função é só extrair e analisar) com a fase oficial da obra pra detectar divergências invisíveis. **227 obras ativas** cobertas pelo `--todas-ativas` · varredura via Task Scheduler 12h e 18h.

## Naming

**ORION** (rebranding HERMENEUTA → ORION aplicado em 2026-05-01). Caçador de visão aguçada · 3 estrelas do cinturão = painel × telegram × KIRA · termina em ON igual STELION/TERON.

## URL ativa

`https://lab.monofloor.cloud` · CF Worker com Basic Auth + cookie 24h · senha gerenciada pelo Vitor.

## Audiência

Vitor + (em breve) Rodrigo + diretoria. Acesso via card-orion no Hub Monofloor. **ATENA foi extinto** (era cópia pobre do Orion).

---

## ✅ O que está bom (pós-Caminho A · 2026-05-04)

- **Cobertura Telegram: 190/230 cards** com sinal real (era 10) · 20.166 msgs Telegram + 9.455 WhatsApp coletados
- **Migração Telethon → Painel API completa** · sem auth, sem rate limit, multi-canal, descrições de foto/áudio já incluídas
- **Pipeline `varredura.py`** roda em ~47s · 13 etapas encadeadas com lock anti-concorrência + atomic write + backup rolling 14 dias
- **Bloco `telegram` (ultima_msg/dias_silencio/tom_grupo/total_msgs)** calculado direto do snapshot · zero IA · custo zero
- **Timeline de eventos** das mensagens · independente de dossiê (era bloqueador antes)
- **Sentinela com 9 checks** + indicador na tela
- **Top alertas reais surgindo:** AVVA HOUSE 632 msgs · 12 sinais tensos · 0 positivos (tipo de leitura impossível antes)

## 🟡 O que ainda tem problema (Caminho B é o próximo)

- **96% dos vereditos é heurística cega** · `status_sugerido`/`urgencia`/`acao_consultor` das 220 obras não-piloto são preenchidos copiando `fase_atual` do painel · "sugestão" é tautologia · confiança 0.8 fabricada
- **Cards "com IA" e "sem IA" indistinguíveis visualmente** · leitor não sabe que está vendo veredito sintético
- **Tom por keyword é tapa-buraco** · pega "atraso" mesmo quando a frase é "sem atraso" · funciona pra triagem grossa, falha em nuance
- **Detail-snapshot pode estar até 26d defasado** em algumas obras · quando isso machucar (raro), refresh manual do Painel resolve
- **40 obras com `?` no telegram** · são as que de fato não têm grupo Telegram cadastrado no Painel · ausência real, não bug

## ⏳ Pendências (ordem de prioridade)

### A) **Caminho B · refactor estrutural** (4-6h em sessão dedicada)
Ler `ROADMAP_CAMINHO_B.md` neste diretório. 5 frentes:
- B1 IA em todas 230 obras (não só recortes) — destrava B2
- B2 Honestidade visual (badge IA vs heurística)
- B3 Pipeline 13→4 etapas + cortar legado Telethon
- B4 Snapshot vira cache, não corredor obrigatório
- B5 Tom IA-driven (substitui keyword)

### B) **Storytelling de obra finalizada** (~1h)
Ideia do Rodrigo (2026-05-04) · escolher 1 obra concluída, rodar `analisar_recorte.py` cirurgicamente, montar narrativa cronológica completa (tempo, solicitações, materiais, eventos). Funciona HOJE com dados corretos · não precisa esperar Caminho B.

### C) **Cores oficiais do catálogo** (memória `project_orion_cores_oficiais.md`)
Extrair hex codes reais das 21 cores do PDF (9 chutadas estão no JSON, faltam 12) + fundo rotativo "cada visita é uma obra".

### D) **Opção B click→IA** (memória `project_orion_opcao_b_pausada.md` · PAUSADA)
Worker + Action prontos mas dormentes. Reativar quando outras pessoas (não Vitor) usarem.

---

## Pipeline atual (13 passos · após Caminho A)

```
1.  adquirir_lock (PID alive check)
2.  fazer_backup (rolling 14 dias em dados/backups/)
3.  shutil.copy snapshot Telegram → snapshot-prev (pra diff · CANDIDATO A CORTAR no Caminho B)
4a. selecionar_piloto.py --todas-ativas (227 obras)
4b. coletar_painel.py (Painel API · Telegram + WhatsApp · 2000 msgs/90d)
5.  calcular_diff_msgs (msgs novas por obra)
6.  extrair_timeline.py (eventos + bloco telegram do snapshot · dossiê opcional)
7.  aplicar_regua.py (bucket SLA + marcos PP:001 + fallback painel-snapshot)
8.  extrair_equipe.py (cadastro × telegram + overrides)
9.  extrair_cores.py (cores + tendência · regex `[ \t]*` + filtro keyword)
10. extrair_kira_whatsapp.py (espelha pendenciaManual.whatsappSummary)
11. inferir_consultor.py (overrides consultor formal × real)
12. sanitizar_json.py (remove flag cliente_ausente + campos mortos)
13. registrar_kpis.py (série temporal pra sparkline)
14. marcar_refresh_status (flag stale por obra)
15. sentinela.py (9 checks · gera status.json)
16. publicar.py (atomic + git push pub repo + wrangler deploy CF)
17. liberar_lock
```

## Scripts críticos em `agente/`

| Script | Função | Encaixe pipeline |
|---|---|---|
| `_util.py` | Helpers · write_discord · validar · backup · pipeline-errors flag | importado por todos |
| `varredura.py` | Orquestrador · adquire lock · executa pipeline · libera lock | RAIZ |
| `telethon/selecionar_piloto.py` | `--todas-ativas` (novo) ou `--todas` (legado) | passo 4a |
| `telethon/coletar_painel.py` | Painel API · Telegram + WhatsApp · 2000/90d | passo 4b |
| `extrair_timeline.py` | Bloco telegram + eventos · dossiê opcional | passo 6 |
| `aplicar_regua.py` | Bucket SLA + marcos PP:001 + fallback painel | passo 7 |
| `extrair_equipe.py` | Cadastro × Telegram + overrides | passo 8 |
| `extrair_cores.py` | Cores + agregado · regex fix + keyword filter | passo 9 |
| `extrair_kira_whatsapp.py` | Espelha KIRA WhatsApp do detail | passo 10 |
| `inferir_consultor.py` | Overrides consultor formal × real | passo 11 |
| `sanitizar_json.py` | Limpeza · cliente_ausente + campos mortos | passo 12 |
| `registrar_kpis.py` | Série temporal pra sparkline | passo 13 |
| `sentinela.py` | 9 checks · gera status.json + lê pipeline-errors.json | passo 15 |
| `publicar.py` | Atomic + git push + wrangler deploy | passo 16 |
| `analisar_recorte.py` | IA gpt-4o-mini · GitHub Models · gratuito 8k req/dia | manual |
| `arquivar_versao.py` | Backup pré-IA · suporta `--evolucao OBRA_ID` | manual |

### Scripts LEGADOS (candidatos a corte no Caminho B · não rodam mais)

- `telethon/monitorar.py` (Telethon morto · substituído por coletar_painel)
- `telethon/listar_grupos.py` (gerava grupos.json via Telethon)
- `telethon/grupos.json` (legado modo `--todas` pareadas)
- `telethon/telegram-snapshot-prev.json` (só serve pra diff de mensagens novas · valor marginal)

## Princípios fixos · NÃO QUEBRAR

1. **Painel de Obras é o produto do Kira** · transcrição de áudio + descrição de foto + indexação · nossa função é só extrair e analisar. Toda etapa intermediária é candidata a corte.
2. **Telegram > painel** quando divergem · verdade está nas mensagens
3. **Telegram = canal interno** Monofloor · cliente fica no WhatsApp via KIRA
4. **Custo zero** sempre que possível · IA on-demand via GitHub Models gratuito
5. **Versionar tudo** (`dados/historico/` · `dados/backups/` · 14 dias)
6. **Não inventar** · sempre citar `msg_id` como fonte
7. **`whatsappSummary.geradoEm` ≠ última msg** · é quando KIRA sintetizou
8. **Antes de culpar coletor, verificar se consumidor existe** · grep do campo no código antes de mexer no fetch · learning do schema fantasma 2026-05-04

## Camadas de proteção ativas

- ✅ Atomic write (`_util.write_json_atomic`)
- ✅ Schema validator (`_util.validar_discord` + `write_discord`)
- ✅ Backup rolling (14 dias × 2 varreduras = 28 backups)
- ✅ Lock com PID alive check (não só TTL)
- ✅ Retry exponencial Painel API + abort 30%
- ✅ Pipeline-errors flag (`dados/pipeline-errors.json` · sentinela detecta)
- ✅ HOJE dinâmico (`datetime.now(utc)` em todos)
- ✅ Encoding utf-8-sig na leitura
- ✅ Sentinela com 9 checks · drift directional (só ALERT em regressão, não em crescimento)
- ✅ Wrangler deploy garantido (não confia em CF auto-sync)

## Como verificar saúde rápido

```powershell
cd C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta
python agente/sentinela.py
```

Saída em ~1s mostrando 9 checks · `ok` / `warn` / `crit` · cada um com sugestão de ação.

## Como rodar varredura manual

```powershell
python agente/varredura.py
```

Roda os 13 passos em ~47s. Tem lock · se outra rodando, sai sem fazer nada.

## Como rodar IA cirurgicamente em 1 obra (custo zero)

```powershell
$env:GITHUB_TOKEN = "<PAT com escopo repo>"
python agente/analisar_recorte.py --obra-ids "<obra_id>" --recorte "manual"
python agente/publicar.py
```

Análise gpt-4o-mini via GitHub Models · usado pra storytelling, validação de obra específica, etc.

## Como subir tela local

```powershell
cd C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta
python -m http.server 8765
```

Abrir http://localhost:8765/

---

## Comando pra retomar (cole no Claude Code na próxima sessão)

```
Lê analise/lab-hermeneuta/RETOMAR.md e me dá overview do estado.
Roda python agente/sentinela.py e me mostra o resultado.
Lista o que está pendente do meu lado.
```

Esse comando faz qualquer agente: (1) carregar contexto, (2) validar saúde, (3) listar tarefas pendentes · em uma resposta só.
