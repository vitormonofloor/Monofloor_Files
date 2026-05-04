# PAINEL QUALIDADE · COMPILAÇÃO ATUALIZADA

> **Snapshot completo do sistema de gestão de Qualidade da Monofloor.**
> Compilado em 2026-05-04 · 3 cópias sincronizadas (repo · máquina · Obsidian).

---

## Como navegar

| # | Arquivo | O que tem |
|---|---|---|
| — | **`README.md`** (este) | Mapa de leitura |
| 01 | `01-VISAO-GERAL.md` | Arquitetura geral · 4 componentes principais |
| 02 | `02-DASHBOARD.md` | Dashboard executivo · 9 seções |
| 03 | `03-ORION.md` | Lab Orion · cruzamento Painel × Telegram |
| 04 | `04-RELATORIO-QUINZENAL.md` | Relatório pra Diretoria · 16 seções |
| 05 | `05-PRINCIPIOS.md` | DNA do trabalho · regras inegociáveis |
| 06 | `06-PENDENCIAS.md` | Roadmap consolidado |
| 07 | `07-FONTES-DE-DADOS.md` | APIs, coletores, integrações |
| 99 | `HISTORICO-SESSOES.md` | Linha do tempo das construções |
| snapshot | `relatorio-2026-05-quinzena-1.{md,html}` | Exemplo do último relatório gerado |

---

## TL;DR · estado em 2026-05-04

A Qualidade da Monofloor opera com **4 ferramentas integradas**, todas construídas dentro do repositório `Monofloor_Files` e publicadas via GitHub Pages:

1. **Hub** (`hub.html`) · ponto de entrada com 2 cards: Dashboard + Orion
2. **Dashboard Executivo** (`analise/dashboard.html`) · 9 seções, refresh 30min do Painel de Obras
3. **Lab Orion** (`orion-pub.workers.dev`) · piloto que cruza Painel × Telegram em 10 obras
4. **Relatório Quinzenal** (`analise/gerar-relatorio.py`) · gera Markdown + HTML pra Diretoria

**Princípio central** (firmado em 2026-05-01):
> *"Hoje nós dois somos a Qualidade Monofloor."* — Vitor

---

## Onde os arquivos vivos moram (não nesta pasta · esta é resumo)

| Componente | Caminho canônico |
|---|---|
| Hub | `Monofloor_Files/hub.html` |
| Dashboard | `Monofloor_Files/analise/dashboard.html` |
| Lab Orion (canônico) | `Monofloor_Files/analise/lab-hermeneuta/index.html` |
| Lab Orion (publicado) | `lab-hermeneuta-pub/public/index.html` (Cloudflare Worker) |
| Relatório Quinzenal | `Monofloor_Files/analise/relatorios/` |
| Coletores | `Monofloor_Files/analise/*.sh`, `*.py` |
| Backlog | `Monofloor_Files/analise/relatorios/MELHORIAS-PENDENTES.md` |

---

## Status

- **Dashboard:** ✅ funcional · 9 seções honestas · refresh 30min
- **Lab Orion:** ✅ funcional · piloto 10 obras · varredura 12h e 18h
- **Hub:** ✅ funcional · constelação Orion fiel ao Lab · dock cross-tool
- **Relatório Quinzenal:** ✅ funcional · 18 fixes em 3 rodadas · pronto pra uso
- **Pendências:** 🟡 P1 nova (estrutura) · ✏ P2 nova (refinamento) · 🚀 Fases B+C (botão hub + Telegram)

Detalhe completo de pendências em `06-PENDENCIAS.md`.

---

## Atualização desta pasta

Esta compilação é **um snapshot**. Os arquivos vivos no repo evoluem. Pra atualizar:

```bash
cd C:/Users/vitor/Monofloor_Files

# Regerar relatório (exemplo no snapshot)
cd analise && python coletar-relatorio-extras.py && python gerar-relatorio.py

# Atualizar a pasta de compilação manualmente OU peça pra mim
# "atualiza a PAINEL QUALIDADE ATUALIZADO" e eu sincronizo as 3 cópias
```
