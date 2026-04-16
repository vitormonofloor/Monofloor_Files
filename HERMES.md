# HERMES — Agente Narrativo de Análise Operacional

> O mensageiro dos deuses. Traduz indicadores em narrativa estratégica na voz do Vitor Gomes.

---

## Dados Técnicos

| Campo | Valor |
|---|---|
| **Repositório** | `vitormonofloor/hermes-monofloor` |
| **Deploy** | Railway — projeto `vivacious-hope` |
| **URL pública** | `hermes-monofloor-production.up.railway.app` |
| **Ciclo** | 1x por dia às 8h BR |
| **Versão atual** | v1.1 |
| **LLM** | Groq — `llama-3.3-70b-versatile` |
| **Dashboard** | `vitormonofloor.github.io/Monofloor_Files/analise.html` |

## Endpoints

- `/` — status do agente (JSON)
- `/api/executar` — dispara análise manual
- `/api/ultima` — última análise gerada (JSON com manchete, insights, ações)
- `/api/historico` — histórico de análises

## Pipeline

1. Busca dados do **Argos** via `/api/dados`
2. Calcula **diff** vs execução anterior (o que mudou)
3. Monta contexto com: indicadores, problematicos, tipos de ocorrência, carga por consultor, distribuição regional, contradições
4. Chama **Groq LLM** com system prompt calibrado na voz do Vitor:
   - Direto, decisivo, sem floreios
   - Foco em ações concretas
   - Identifica padrões não-óbvios
5. Recebe JSON estruturado: manchete, contexto, 3 insights, plano de ação, projeção semanal
6. Renderiza **analise.html** como apresentação com slides verticais:
   - Hero com manchete
   - Contexto operacional
   - KPIs + sparkline + tipos de ocorrência
   - Comparativo (o que mudou)
   - Insights não-óbvios
   - Plano de ação (cards com prioridade)
   - Projeção da semana
7. Publica no GitHub Pages
8. Notifica Telegram com manchete + top 3 ações + link

## System Prompt (voz do Vitor)

O Hermes gera narrativa na personalidade do Vitor:
- Frases curtas, sem disclaimers
- Chama as coisas pelo nome ("Wesley está sobrecarregado")
- Usa dados específicos (nomes de projetos, números exatos)
- Identifica padrões que os números sozinhos não mostram
- Honesto sobre o que não funciona

## Variáveis Railway (9)

- `GROQ_API_KEY` — chave da API Groq
- `GROQ_MODEL` — llama-3.3-70b-versatile
- `ARGOS_URL` — https://argos-monofloor-production.up.railway.app
- `GITHUB_TOKEN` — token com scope `repo`
- `GITHUB_REPO` — vitormonofloor/Monofloor_Files
- `GITHUB_FILE` — analise.html
- `TELEGRAM_BOT_TOKEN` — token do @monofloor_op_bot
- `VITOR_CHAT_ID` — 8151246424
- `HORA_EXECUCAO` — 8

## Design Visual

- Layout denso sem scroll-snap (v1.1)
- Hero com `min-height: 85vh`, manchete 68px
- Container `max-width: 1100px`
- Slides com `padding: 80px`, fade-in progressivo via IntersectionObserver
- Eyebrow com background sutil (pill dourada)
- KPIs com gradiente e hover
- Back-link com `backdrop-filter: blur(8px)` → volta pro indicadores.html
- Branding: #c4a77d, Inter, #0a0a0a bg

## Evolução

| Versão | Data | Mudança |
|---|---|---|
| v1.0 | 16/04/2026 | Apresentação com slides verticais scroll-snap |
| v1.1 | 16/04/2026 | Layout denso, tipografia equilibrada, fade-in progressivo |

## Conexões

- **Fonte de dados**: [[ARGOS]] (`/api/dados`)
- **LLM**: Groq (gratuito, sem cartão)
- **Notifica**: Telegram (VITOR_CHAT_ID)
- **Publica em**: GitHub Pages (`Monofloor_Files/analise.html`)
- **Acessível via**: Botão ◆ Hermes no painel do [[ARGOS]] (com animação de asas douradas)

---

## Arquitetura do Ecossistema

```
KIRA (alheia, cliente.monofloor.cloud)
  ↓ classifica mensagens TG/WA → ocorrências
  
ARGOS (Railway, 6h)
  ↓ extrai KIRA → publica indicadores.html
  ↓                ↘
TELEGRAM           HERMES (Railway, 8h BR)
                     ↓ lê Argos → Groq LLM → analise.html
                     ↓
                   TELEGRAM (manchete + ações)
```

Railway projeto `vivacious-hope` hospeda 3 serviços: Teleagente, Argos, Hermes.

---

*Criado em: 16/04/2026*
*Tags: #agente #narrativo #hermes #groq #llm #railway*
