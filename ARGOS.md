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
| **Dashboard** | `vitormonofloor.github.io/Monofloor_Files/indicadores-v2.html` |
| **Splash** | `vitormonofloor.github.io/Monofloor_Files/splash.html` |
| **Design** | Light/bege (#f0ebe3), Plus Jakarta Sans, identidade cliente.monofloor.cloud |

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
| v2.0 | 17/04/2026 | Redesign completo: visual light/bege, 4 níveis (Fogo→Panorama→Consultores→Hermes), KPIs autoexplicativos clicáveis, semáforo automático (Régua de Saúde), consultores interativos com severidades animadas, sparkline com tooltip, splash page com animação espátula |

## Conexões

- **Fonte de dados**: [[KIRA]] (alheia, sem auth)
- **Consumidor**: [[HERMES]] (lê `/api/dados`)
- **Notifica**: Telegram (VITOR_CHAT_ID)
- **Publica em**: GitHub Pages (`Monofloor_Files/indicadores-v2.html` + `splash.html`)
- **Asset**: `hermes-wing.png` hospedada em Monofloor_Files
- **Logo**: Wixstatic `2bc4fe_d7fd788ceb094e96b86315e020950bda~mv2.png`

## Indicadores v2 — Funcionalidades

- **Nível 1 — Fogo**: Cards gigantes (problemas detectados + taxa atraso) com micro-ações clicáveis
- **Nível 2 — Panorama**: 12 KPIs em 6 grupos (Comunicação, Qualidade, Performance, Operações, Logística, Comercial), semáforo auto, pulso variação, explicações clicáveis (O que é, Por que importa, Escala, Analogia, Como calcula)
- **Nível 3 — Consultores**: Botões individuais (Wesley, Luana, Juliana, Pedro, Sem consultor), painel interativo com 4 KPIs, tipos expandíveis com definição+metodologia, severidades animadas pulsantes com drill-down
- **Nível 4 — Hermes CTA**: Link para analise.html
- **Sparkline**: Interativo com tooltip (dia da semana + data + valor), eixos X/Y
- **Splash**: Animação espátula (2 passadas), logo Monofloor original, fade-out ao clicar
- **Bloco de contexto**: 4 bullets com ícones (📡🤖🎯🔄) explicando o painel, agente Argos, frequência 4x/dia, período 30 dias

---

*Criado em: 16/04/2026*
*Tags: #agente #indicadores #argos #railway #kira*
