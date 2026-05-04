# 07 · Fontes de Dados · APIs, Coletores e Integrações

> **⚠ Aviso LGPD:** todos endpoints abaixo retornam 200 SEM autenticação. Expõem nomes, telefones, endereços, resumos WhatsApp publicamente. Issue conhecida (S4 · task #45).

---

## 2 backends Monofloor Cloud

### `cliente.monofloor.cloud` (Next.js · plataforma operacional canônica)

**Listas:**
- `GET /api/projects?limit=2000` — 1.038 obras (total)
- `GET /api/projects/{id}` — detalhe individual com ~60 campos (`acessoDetalhes.allFields`, `pendenciaManual.whatsappSummary`)
- `GET /api/dashboard` — totals · sla.byKey · readiness · phases · ocorrencias.byStatus
- `GET /api/analise` — atRisk (50 obras · diagnóstico textual) · problemCategories (11) · recentEvents (32) · teamPerformance (6 consultores)
- `GET /api/escalacao-diaria` — 25 obras hoje
- `GET /api/equipes` — 6 equipes (Wiguens/João/Júlio/Gilmar/Egberto/Michael)

**WhatsApp:**
- `GET /api/whatsapp/conversations` — 317 conversas
- `GET /api/whatsapp/messages?phone={phone}` — mensagens (text/image/video/audio)
- `GET /api/whatsapp/summary?projectId={id}` — resumo IA por obra (KIRA)
- `POST /api/whatsapp/send`, `/api/whatsapp/suggest` (KIRA)

**Endpoints fantasma (existem mas retornam null):**
`pp001`, `estrela`, `clienteEmail`, `lastActivity`, `eventos`, `mensagens`, `dashboard.pausas[]`, `onboardingStatus`

**Endpoints inexistentes (404):**
`/api/hoje`, `/api/today`, `/api/agenda`, `/api/eventos`, `/api/timeline`, `/api/atividades`, `/api/telegram`, `/api/kira`

### `planejamento.monofloor.cloud` (Vite/React · standalone)

**Schema DIFERENTE** do cliente — bancos paralelos não-sincronizados.

- `GET /api/obras` — 40 obras com cronograma (`dados_json` é STRING JSON aninhada)
- `GET /api/projects` — 1.037 registros comerciais
- `GET /api/equipes` — 13 equipes ativas · 70 prestadores · 6 líderes
- `GET /api/stats` — KPIs canônicos do painel home
- `GET /api/orchestrator/status` — operação viva (activeJourneys 405, pendingTasks 1947)
- `GET /api/analytics/capacity` — capacidade real (utilization 35% saudável)
- `GET /api/analytics/alerts` — 9 alertas estruturados (HIGH/MED)
- `GET /api/analytics/weekly-forecast` — projeção 13 semanas
- `GET /api/estoque` — vazio · indústria não digitalizada

---

## Coletores ativos

### `coletar-rodrigo-stats.sh` (Bash · 30 min · GitHub Actions)
- Baixa 1.038 obras + 228 details (com whatsappSummary)
- Calcula: aplicadores, lw (Luana × Wesley), equipes (com líder remapeado), historico, operacional_kira, q4_datas_fresh, ext_fresh, proximos
- Workaround Windows curl SSL: validate JSON pelo primeiro byte `{`
- Saída: `analise/dados/rodrigo-stats.json`

### `coletar-relatorio-extras.py` (Python · sob demanda)
- Busca 4 endpoints subutilizados:
  1. `/api/analise` (cliente)
  2. `/api/analytics/alerts` (planejamento)
  3. `/api/analytics/weekly-forecast` (planejamento)
  4. `/api/dashboard` (cliente)
- Saída: `analise/dados/relatorio-extras.json`

### `refresh.sh` (Bash · 30 min · GitHub Actions)
- Calcula score · acumula score-historico · regenera headline
- Saída: `analise/dados/headline.json`, `score-historico.json`

### `agente/varredura.py` + `publicar.py` (Python · 2x/dia · Task Scheduler)
- Lab Orion · 12h e 18h
- Coleta + analisa + publica `discordancias-v3.json`
- Copia canônico → pub no Cloudflare Worker

---

## Storage estático

```
analise/dados/
├── headline.json              # Score + componentes (refresh PESADO 1×/dia)
├── rodrigo-stats.json         # KPIs canônicos (refresh 30min)
├── score-historico.json       # 1 entry/dia desde 2026-05-01
├── historico-aplicadores.json # 90 dias
├── q1-classificacoes.json     # overrides manuais Q1 (Vitor edita)
├── relatorio-extras.json      # 4 endpoints subutilizados
├── br-map.svg                 # mapa real Brasil 54KB MIT
├── details/                   # 228 obras (~3min coleta) com KIRA
│   └── *.json
└── cruz-*.json                # cruzamentos diários (8 ouros)
```

---

## Outros sistemas

### Pipefy (descontinuado pra usuário · backend ainda usado)
- Pipes: OE 306410007 · OEC 306446640 · OEI 306446401 · OECT 306431675
- Token salvo em `.env` no Railway (`teleagente`)
- Snapshot externo: `cargo-assistente/main/pipefy_cards.json` (591 cards)

### Telegram (Teleagente)
- Bot: `@monofloor_op_bot` · ID 8685770674
- Railway: `teleagente-production.up.railway.app`
- Comandos: `/obras`, `/gargalos`, `/atrasadas`, `/aproveitamento`, `/alerta`, `/status`, `/semana`

### Cloudflare Workers
- `monofloor-refresh` · proxy do botão "Atualizar agora" do dashboard
- `orion-pub` · Lab Orion publicado com Basic Auth

### GitHub Actions
- `refresh-all.yml` · dispara coletores em paralelo (30 min)
- Sem GitHub Action no `lab-hermeneuta-pub` · deploy via auto-publish CF→Git OU `wrangler deploy` manual

### D4Sign
- Assinatura digital de contratos · 115 finalizados

### Omie
- ERP financeiro · ⚠ ACESSO PENDENTE · trava 5/8 indicadores financeiros

---

## Pessoas-chave (operação)

| Função | Pessoas |
|---|---|
| Consultoras (conta) | Luana Patrícia (89 ativas · mediana 208d) · Wesley Matheus (88 · 175d) |
| Atendimento | Pedro Marçal · Mayara |
| Outros consultores | Pedro Alexandre Santana (7) · Juliana Santos (2) · Renata Garcia Penna (1) · Thaísa de Lara Barbosa |
| Líderes equipe | Wiguens Louis · João Carlos · Júlio Miranda |
| Líderes inativos no cadastro mas ativos na operação | Gilmar · Egberto Sulivan · Cosme Eduardo Ragno (cadastrado errado como líder Michael) |
| Encarregados ocultos | UUIDs sem cadastro mas lideram escalação (5 obras hoje) |
| VT/Agendamentos | Nathan · Braiam |
| Coordenador Financeiro | Júlio César Bielenki Taporosky |
| Diretoria Operacional | Kassandra Martinho |
| Gerente da Qualidade | **Vitor Gomes** (autor) |

---

## Bloqueadores ativos

1. **ANTHROPIC_API_KEY** — trava Cérebro + Teleagente `/semana`
2. **Acesso Omie** — trava 5/8 indicadores financeiros
3. **G1 coleta amostras** — 267 cards, 260 dias avg
4. **API cliente sem auth** — risco LGPD (S4 · S5)
