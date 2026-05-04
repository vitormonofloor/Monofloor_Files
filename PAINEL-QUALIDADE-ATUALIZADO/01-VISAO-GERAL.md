# 01 · Visão Geral · Arquitetura do Sistema de Qualidade

## Os 4 componentes integrados

```
                         ┌─────────────────────┐
                         │   HUB (hub.html)    │
                         │   2 cards animados  │
                         └──────────┬──────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                                       ▼
        ┌──────────────┐                       ┌──────────────┐
        │  DASHBOARD   │                       │  LAB ORION   │
        │  Executivo   │ ◄── cross-dock ──►    │   (piloto)   │
        │  9 seções    │                       │  10 obras    │
        └──────┬───────┘                       └──────┬───────┘
               │                                      │
               └──────────────┬───────────────────────┘
                              ▼
                  ┌──────────────────────┐
                  │  RELATÓRIO           │
                  │  QUINZENAL           │
                  │  pra Diretoria       │
                  │  16 seções · MD+HTML │
                  └──────────────────────┘
```

---

## Hub · ponto de entrada

- **URL pública:** https://vitormonofloor.github.io/Monofloor_Files/hub.html
- **Arquivo:** `hub.html` (raiz do repo)
- **Conteúdo:** 2 cards animados (Dashboard + Orion) · constelação fiel ao Lab Orion · particles dourados · transição dramática 3.5s ao clicar
- **Modal "?":** explica navegação · 3 estruturas (Hub, Dashboard, Orion) · perguntas-rota · atalhos visuais

## Dashboard Executivo

- **URL pública:** https://vitormonofloor.github.io/Monofloor_Files/analise/dashboard.html
- **Arquivo:** `analise/dashboard.html` (9 mil linhas, single-page app vanilla)
- **9 seções:** Hero (Score+manchete) · Estratégicos · Q1 Cronograma · Q2 Paradas · Q3 Equipe · Q4 Volume · Agenda · Operacional KIRA · Banner Retrabalho
- **Refresh:** 30 min via GitHub Actions + Cloudflare Worker (`refresh-all`)
- **Dock cross-tool:** ícones Central + Dashboard + Orion no lado esquerdo
- Detalhe em `02-DASHBOARD.md`

## Lab Orion · cruzamento Painel × Telegram

- **URL pública:** https://orion-pub.vitor-monofloor.workers.dev (área restrita · Basic Auth)
- **Arquivo canônico:** `analise/lab-hermeneuta/index.html` (Monofloor_Files)
- **Arquivo publicado:** `lab-hermeneuta-pub/public/index.html` (Cloudflare Worker)
- **Sincronização:** `agente/publicar.py` copia canônico → publicado a cada varredura (12h e 18h)
- **Saída:** `discordancias-v3.json` (cruzamento) · `historico-kpis.json` · `status.json`
- **Hoje:** 10 obras piloto · expansão prevista pra 50 em 3 meses
- Detalhe em `03-ORION.md`

## Relatório Quinzenal · pra Diretoria

- **Arquivo gerador:** `analise/gerar-relatorio.py` (Python · sem dependências)
- **Arquivo conversor:** `analise/gerar-pdf.py` (MD → HTML estilizado)
- **Arquivo coletor:** `analise/coletar-relatorio-extras.py` (4 endpoints subutilizados)
- **Saída:** `analise/relatorios/YYYY-MM-quinzena-N.{md,html}`
- **16 seções** · 638 linhas · 4 visuais SVG · 6 receitas propositivas
- **Frequência:** quinzenal
- Detalhe em `04-RELATORIO-QUINZENAL.md`

---

## Stack técnico

| Camada | Tecnologia |
|---|---|
| Frontend (dashboards) | HTML/CSS/JS vanilla · Plus Jakarta Sans · cream `#f0ebe3` |
| Hospedagem (público) | GitHub Pages (`vitormonofloor.github.io/Monofloor_Files`) |
| Hospedagem (privado) | Cloudflare Workers (`orion-pub.workers.dev`) |
| Coleta de dados | Bash + Python · GitHub Actions |
| Storage | JSON estático em `analise/dados/` |
| APIs externas | `cliente.monofloor.cloud`, `planejamento.monofloor.cloud` |
| Notificações futuras | Telegram bot @monofloor_op_bot |

---

## Princípio firmado pela arquitetura

**100% derivado de fontes vivas.** Nada hardcoded — tudo amarrado em fonte canônica do Painel de Obras. Hardcode é dívida moral.

Cada componente usa as MESMAS fontes:
- `cliente.monofloor.cloud/api/projects` (1.038 obras)
- `cliente.monofloor.cloud/api/projects/{id}` (detalhe + KIRA whatsappSummary)
- `cliente.monofloor.cloud/api/analise` (50 obras com diagnóstico textual + 11 categorias)
- `planejamento.monofloor.cloud/api/analytics/*` (alerts + capacity + forecast)

Detalhe das fontes em `07-FONTES-DE-DADOS.md`.
