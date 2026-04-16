# ARGOS — Agente Autônomo de Indicadores Operacionais

> O vigilante de 100 olhos. Extrai, computa e publica indicadores da operação Monofloor a cada 6 horas.

---

## Dados Técnicos

| Campo | Valor |
|---|---|
| **Repositório** | `vitormonofloor/argos-monofloor` |
| **Deploy** | Railway — projeto `vivacious-hope` |
| **URL pública** | `argos-monofloor-production.up.railway.app` |
| **Ciclo** | A cada 6h (0h, 6h, 12h, 18h BR) |
| **Versão atual** | v1.5 |
| **Dashboard** | `vitormonofloor.github.io/Monofloor_Files/indicadores.html` |

## Endpoints

- `/` — status do agente (JSON)
- `/api/dados` — última extração completa (JSON)
- `/api/historico` — histórico de execuções
- `/api/executar` — dispara ciclo manual

## Pipeline

1. Extrai todos os projetos da **KIRA** (`cliente.monofloor.cloud/api`)
2. Para cada projeto: mensagens (TG + WA), ocorrências, alertas, materiais
3. Computa indicadores agregados (msgs 30d, taxa atraso, silêncio, ocorrências por tipo/severidade/consultor/região)
4. Gera **indicadores.html** com:
   - KPIs clicáveis com modais analíticos
   - Blocos por categoria com stack bars de severidade
   - Sparkline de tendência 30 dias
   - Abas: Por Tipo, Lista Detalhada, Definição
   - Botão **Hermes** com animação de asas douradas (2.8s)
5. Publica no GitHub Pages via API
6. Notifica Telegram com resumo

## Variáveis Railway (7)

- `KIRA_API_URL` — https://cliente.monofloor.cloud/api
- `GITHUB_TOKEN` — token com scope `repo`
- `GITHUB_REPO` — vitormonofloor/Monofloor_Files
- `GITHUB_FILE` — indicadores.html
- `TELEGRAM_BOT_TOKEN` — token do @monofloor_op_bot
- `VITOR_CHAT_ID` — 8151246424
- `INTERVALO_HORAS` — 6

## Evolução

| Versão | Data | Mudança |
|---|---|---|
| v1.0 | 16/04/2026 | Painel básico com KPIs e tabelas |
| v1.1 | 16/04/2026 | KPIs clicáveis com modais de drill-down |
| v1.2 | 16/04/2026 | Modais analíticos com gráficos, tendência e blocos por categoria |
| v1.3 | 16/04/2026 | Botão Hermes no header |
| v1.4 | 16/04/2026 | Portal Hermes com animação de asas SVG |
| v1.5 | 16/04/2026 | Animação definitiva com asa dourada real (PNG), 2.8s fluida |

## Conexões

- **Fonte de dados**: [[KIRA]] (alheia, sem auth)
- **Consumidor**: [[HERMES]] (lê `/api/dados`)
- **Notifica**: Telegram (VITOR_CHAT_ID)
- **Publica em**: GitHub Pages (`Monofloor_Files/indicadores.html`)
- **Asset**: `hermes-wing.png` hospedada em Monofloor_Files

---

*Criado em: 16/04/2026*
*Tags: #agente #indicadores #argos #railway #kira*
