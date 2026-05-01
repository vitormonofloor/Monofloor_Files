# 🎯 RETOMAR · contexto rápido pra qualquer agente

> **Última sessão:** 2026-04-30 · noite
> Se você é um agente IA chegando agora · LEIA este arquivo primeiro. Em ~30s você terá contexto suficiente pra trabalhar sem confundir nada.

---

## O que é este lab em 1 frase

Sandbox que cruza grupos Telegram (via Telethon · userbot do Vitor) com PAINEL DE OBRAS oficial pra detectar divergências invisíveis ao KIRA. **10 obras-piloto** rodando · varredura automática **12h e 18h** via Task Scheduler.

## Decisão de naming pendente

**Nome novo decidido: ORION** (substitui "Hermeneuta"). Ainda **NÃO aplicado no código** (intencional). Aplicar quando Vitor presente.

## Audiência

Hoje: Vitor + Rodrigo (diretoria). Site privado em `lab.monofloor.cloud` (a 1h de cliques de subir).

---

## Estado em 5 linhas

- ✅ Pipeline: **14 passos** rodando OK · Task Scheduler 12h e 18h
- ✅ Robustez: 3 fases aplicadas (atomic write · lock PID · backup rolling · schema validator · sentinela)
- ✅ Sentinela: 9 checks · gera `dados/status.json` · indicador na tela
- 🟡 Sentinela mostra 2 warnings hoje (KIRA tag 16d atrás · 2 falhas no log antigo · sem ação necessária)
- ⏳ Site `lab.monofloor.cloud` aguardando Vitor criar repo no GitHub e configurar Cloudflare Pages

---

## Pipeline atual (14 passos)

```
1.  adquirir_lock (PID alive check)
2.  fazer_backup (rolling 14 dias em dados/backups/)
3.  shutil.copy snapshot Telegram → snapshot-prev (pra diff)
4.  monitorar.py (Telethon · retry 2× backoff · abort se ≥30% obras com erro)
5.  calcular_diff_msgs (msgs novas por obra)
6.  extrair_timeline.py (eventos 4 semanas)
7.  aplicar_regua.py (bucket SLA + remarcação data + schema validator)
8.  extrair_equipe.py (cadastro × telegram + overrides)
9.  extrair_cores.py (cores + tendência)
10. extrair_kira_whatsapp.py (espelha pendenciaManual.whatsappSummary)
11. inferir_consultor.py (overrides consultor formal × real)
12. sanitizar_json.py (remove flag cliente_ausente + campos mortos)
13. registrar_kpis.py (série temporal pra sparkline)
14. marcar_refresh_status (flag stale por obra)
15. sentinela.py (9 checks · gera status.json)
16. publicar.py (best-effort · git push pra repo lab-hermeneuta-pub)
17. liberar_lock
```

## Scripts em `agente/`

| Script | Função | Encaixe pipeline |
|---|---|---|
| `_util.py` | Helpers · write_json_atomic · validar_discord · fazer_backup · setup_utf8 · now_utc | importado por todos |
| `varredura.py` | Orquestrador · adquire lock · executa pipeline · libera lock | RAIZ |
| `telethon/monitorar.py` | Puxa msgs Telegram com retry+abort | passo 4 |
| `extrair_timeline.py` | Eventos 4 semanas | passo 6 |
| `aplicar_regua.py` | Bucket SLA + marcos PP:001 + remarcação data | passo 7 |
| `extrair_equipe.py` | Cadastro × Telegram + overrides | passo 8 |
| `extrair_cores.py` | Cores + agregado | passo 9 |
| `extrair_kira_whatsapp.py` | Espelha KIRA WhatsApp do detail | passo 10 |
| `inferir_consultor.py` | Overrides consultor formal × real | passo 11 |
| `sanitizar_json.py` | Limpeza · cliente_ausente + campos mortos | passo 12 |
| `registrar_kpis.py` | Série temporal pra sparkline | passo 13 |
| `sentinela.py` | 9 checks · gera status.json | passo 15 |
| `publicar.py` | Git push pra lab-hermeneuta-pub (best-effort) | passo 16 |
| `arquivar_versao.py` | Backup pré-IA · suporta `--evolucao OBRA_ID` | manual |
| `secretario-prompt.md` | Briefing do subagente IA "secretário" | rodada IA |
| `hermeneuta-prompt.md` | Briefing v3 do agente IA HERMENEUTA | rodada IA |

## Princípios fixos · NÃO QUEBRAR

1. **Telegram > painel** quando divergem · verdade está nas mensagens
2. **Telegram = canal interno** Monofloor · cliente fica no WhatsApp via KIRA
3. **Custo zero** sempre que possível · IA on-demand · operador decide
4. **Versionar tudo** (`dados/historico/` · `dados/backups/`)
5. **Não inventar** · sempre citar `msg_id` como fonte
6. **`whatsappSummary.geradoEm` ≠ última msg** · é quando KIRA sintetizou
7. **Rebranding pendente:** HERMENEUTA → ORION (não aplicar sem confirmar com Vitor)

## Camadas de proteção ativas

- ✅ Atomic write (`_util.write_json_atomic`)
- ✅ Schema validator (`_util.validar_discord` + `write_json_atomic_validado`)
- ✅ Backup rolling (14 dias × 2 varreduras = 28 backups)
- ✅ Lock com PID alive check (não só TTL)
- ✅ Retry exponencial Telethon + abort 30%
- ✅ HOJE dinâmico (`datetime.now(utc)` em todos)
- ✅ Encoding utf-8-sig na leitura
- ✅ Sentinela com 9 checks
- ✅ Indicador discreto na tela (badge canto inferior esquerdo)

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

Roda os 14+ passos em ~6-10s. Tem lock · se outra rodando, sai sem fazer nada.

## Como subir tela local

```powershell
cd C:\Users\vitor\Monofloor_Files\analise\lab-hermeneuta
python -m http.server 8765
```

Abrir http://localhost:8765/

---

## Pendente do Vitor (próxima sessão)

### A) Subir site `lab.monofloor.cloud`
Estrutura pronta em `C:\Users\vitor\lab-hermeneuta-pub\`. Falta:
1. Criar repo privado `lab-hermeneuta-pub` no GitHub
2. `git init && git push` (comandos no `lab-hermeneuta-pub/README.md`)
3. Cloudflare Pages: connect repo · save and deploy
4. Env vars: `LAB_USER` + `LAB_PASS`
5. Custom domain: `lab.monofloor.cloud`
6. Próxima varredura publica sozinha via `publicar.py`

### B) Aplicar rebranding ORION
Quando Vitor presente · não fazer sozinho. Atualiza:
- title da página + h1 + lab-tag + tooltips
- nome dos prompts
- pasta Obsidian
- comentários nos scripts (não-funcional · só estética)

### C) Falar com Rodrigo (não-bloqueador)
- Atualizar `telegramUserId` do Gilmar e Josias no cadastro `/equipes`
- Padronizar nome dos fiscais Braian e Nathan no Telegram com `| Monofloor`

---

## Comando pra retomar (cole no Claude Code na próxima sessão)

```
Lê analise/lab-hermeneuta/RETOMAR.md e me dá overview do estado.
Roda python agente/sentinela.py e me mostra o resultado.
Lista o que está pendente do meu lado.
```

Esse comando faz qualquer agente: (1) carregar contexto, (2) validar saúde, (3) listar tarefas pendentes · em uma resposta só.
