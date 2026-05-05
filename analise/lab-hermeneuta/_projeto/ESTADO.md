# 2 · ESTADO ATUAL · O que está bom · o que tem problema

> Snapshot do dia **2026-05-04 noite** · pós-Caminho A · commit `97a209a`

## ✅ O QUE ESTÁ BOM

### Cobertura de dados
- **190/230 cards** com bloco `telegram` real (era 10)
- **20.166 msgs Telegram + 9.455 WhatsApp** no snapshot atual
- **119 obras com atividade últimos 7d** detectadas (era 9)
- **40 obras com `?`** = de fato sem grupo Telegram cadastrado no Painel · ausência real, não bug

### Pipeline
- `varredura.py` em **47s** · 13 etapas encadeadas
- Lock anti-concorrência com PID alive check (não só TTL)
- Atomic write em todos os JSONs principais
- Backup rolling 14 dias × 2 varreduras = 28 backups
- Pipeline-errors flag (`dados/pipeline-errors.json`) detectado pela sentinela
- Wrangler deploy garantido (não confia em CF auto-sync)

### Sentinela
- 9 checks · gera `dados/status.json` em ~1s
- Drift directional (só ALERT em regressão · crescimento = OK)
- Indicador discreto na tela (badge canto inferior esquerdo)

### Integrações
- Painel API substituiu Telethon · sem auth · sem rate limit
- GitHub Models gratuito conectado pra IA on-demand (`analisar_recorte.py`)
- CF Worker `lab.monofloor.cloud` com Basic Auth + cookie 24h

### Detecções reais surgindo
| Cliente | Msgs | Silêncio | Sinais (tenso/positivo) |
|---|---:|---:|---|
| MANOELA LATINI 2ª FASE | 899 | 4d | 5/0 |
| AVVA HOUSE — Mozart | 632 | 5d | **12/0** ← gritando |
| GINACERCHI CREMA | 144 | 7d | 11/2 |
| REPULLO | 73 | 4d | 9/1 |

Esse tipo de leitura **não existia antes** do Caminho A.

---

## 🟡 O QUE TEM PROBLEMA (não-bloqueador)

### 1. Veredito IA é heurística cega em 96% das obras
- `status_sugerido` / `urgencia` / `acao_consultor` / `tipo_demanda` / `confianca` das 220 não-piloto são preenchidos copiando `fase_atual` do painel
- "Sugestão" vira tautologia ("painel diz X · sugere X")
- `confianca: 0.8` fabricada sem base
- **Impacto:** vereditos parecem inteligentes mas não leram nada
- **Resolve em:** Caminho B · frente B1

### 2. Cards "com IA" e "sem IA" indistinguíveis
- Visual idêntico no frontend
- Leitor não sabe se está vendo análise real ou cópia de campo
- **Impacto:** quebra confiança quando descobre
- **Resolve em:** Caminho B · frente B2

### 3. Tom por keyword é tapa-buraco
- Pega "atraso" mesmo na frase "sem atraso"
- Funciona pra triagem grossa · falha em nuance
- **Impacto:** alguns falsos positivos no top 5 alertas
- **Resolve em:** Caminho B · frente B5

### 4. Detail-snapshot pode estar até 26d defasado
- Foi o caso da KRYSTAL na investigação
- `updatedAt: 2026-04-08` enquanto Painel atual é diferente
- Cron de refresh do detail roda em outro lugar (cargo-assistente?)
- **Impacto:** raro · refresh manual resolve quando notar
- **Workaround:** rodar coletor de detail antes da varredura crítica

### 5. Pipeline tem 13 etapas com acoplamento implícito
- Etapa N+1 espera arquivo gravado pela etapa N
- Drift silencioso possível se uma falhar
- **Impacto:** debug fica caro
- **Resolve em:** Caminho B · frente B3 (colapsa em 4 etapas)

---

## ❌ O QUE ESTÁ QUEBRADO

(idealmente nada · se algo entrar aqui, prioridade máxima)

- *(nenhum item · estado pós-A está estável)*

---

## Métricas

| Métrica | Valor | Antes Caminho A |
|---|---:|---:|
| Obras com bloco telegram preenchido | 190 / 230 | 10 / 230 |
| Total msgs Telegram cobertas | 20.166 | ~5.000 |
| Total msgs WhatsApp cobertas | 9.455 | 0 (não coletava) |
| Obras vivas (atividade últimos 7d) | 119 | 9 |
| Tempo varredura completa | 47s | ~70s |
| Tempo coletor isolado | ~30s | ~5min |
| Etapas do pipeline | 13 | 13 |
| Custo IA mensal | R$ 0 | R$ 0 |

## Arquivos críticos · onde mora o quê

```
analise/lab-hermeneuta/
├── index.html                        ← Lab Orion canônico (publicar.py copia pro pub)
├── RETOMAR.md                        ← Overview rápido · entrada pra agentes
├── ROADMAP_CAMINHO_B.md              ← Refactor estrutural pendente
├── _projeto/                         ← VOCÊ ESTÁ AQUI
├── agente/
│   ├── _util.py                      ← write_discord, validar, backup, pipeline-errors
│   ├── varredura.py                  ← Orquestrador · 13 etapas
│   ├── extrair_timeline.py           ← Bloco telegram · timeline · dossiê opcional
│   ├── aplicar_regua.py              ← Bucket SLA · marcos PP:001
│   ├── extrair_equipe.py             ← Cadastro × Telegram + overrides
│   ├── extrair_cores.py              ← Cores + tendência
│   ├── extrair_kira_whatsapp.py      ← Espelha pendenciaManual
│   ├── inferir_consultor.py          ← Overrides consultor
│   ├── sanitizar_json.py             ← Limpeza
│   ├── registrar_kpis.py             ← Série temporal sparkline
│   ├── sentinela.py                  ← 9 checks · status.json
│   ├── publicar.py                   ← Atomic + git push + wrangler deploy
│   ├── analisar_recorte.py           ← IA gpt-4o-mini · MANUAL
│   ├── arquivar_versao.py            ← Backup pré-IA
│   ├── secretario-prompt.md          ← Briefing IA secretário
│   ├── hermeneuta-prompt.md          ← Briefing IA HERMENEUTA v3
│   └── telethon/
│       ├── selecionar_piloto.py      ← --todas-ativas (227 obras)
│       ├── coletar_painel.py         ← Painel API · Telegram + WhatsApp
│       ├── monitorar.py              ← LEGADO Telethon (corte no Caminho B)
│       ├── listar_grupos.py          ← LEGADO (corte no Caminho B)
│       ├── grupos.json               ← LEGADO (corte no Caminho B)
│       └── telegram-snapshot*.json   ← Corpus coletado
└── dados/
    ├── discordancias-v3.json         ← JSON principal · cards · 230 obras
    ├── painel-snapshot.json          ← Lista de 1038 obras (ativas + finalizadas)
    ├── details-snapshot/{id}.json    ← Detail por obra (cliente, fase, situação)
    ├── dossies/{id}.json             ← OPCIONAL · enriquece timeline
    ├── status.json                   ← Sentinela output
    ├── pipeline-errors.json          ← Flag de falhas detectadas
    ├── historico-kpis.json           ← Série temporal
    └── backups/                      ← Rolling 14 dias
```
