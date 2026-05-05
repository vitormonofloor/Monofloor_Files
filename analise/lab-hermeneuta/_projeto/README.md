# 🛰 Lab Orion · Projeto · README

> **Atualizado:** 2026-05-04 · noite (pós-Caminho A · cobertura 10→190 cards)

Pasta-síntese do desenvolvimento do Lab Orion. Qualquer agente IA chegando agora deve **ler esta pasta na ordem 1→7** pra entender em ~5min onde estamos, o que foi feito, o que falta.

## Estrutura

| # | Arquivo | Propósito |
|---|---|---|
| 1 | `HISTORIA.md` | Linha do tempo + decisões arquiteturais (por que escolhemos X em vez de Y) |
| 2 | `ESTADO.md` | O que está bom · o que tem problema · métricas atuais · arquivos críticos |
| 3 | `ARQUITETURA.md` | Pipeline 13 etapas + scripts + data-flow + APIs externas |
| 4 | `PENDENCIAS.md` | Caminho B + Storytelling + Cores + Opção B (com prioridades) |
| 5 | `RUNBOOK.md` | Como rodar varredura/IA cirúrgica/publicar/debugar |
| 6 | `APRENDIZADOS.md` | Padrões consolidados (schema fantasma, honestidade visual, custo de tempo) |
| 7 | `INVENTARIO.md` | Mapa físico: onde mora cada arquivo (repo, frontend pub, worker, memória) |

## O que é o Orion em 1 frase

Sandbox que cruza grupos Telegram + WhatsApp **via Painel de Obras (Kira já mastigou os dados)** com a fase oficial pra detectar divergências invisíveis. Custo zero · 227 obras ativas · varredura 12h+18h.

## Estado em 5 linhas

- ✅ **190/230 cards** com sinal Telegram real (era 10) · 20.166 msgs cobertas
- ✅ Pipeline `varredura.py` em **47s** · 13 etapas com lock/atomic/backup
- ✅ URL ativa: `https://lab.monofloor.cloud` · CF Worker + Basic Auth
- 🟡 **96% dos vereditos é heurística cega** (Caminho B resolve · 4-6h)
- ⏳ Próximo: storytelling de 1 obra finalizada (ideia Rodrigo · ~1h, dá pra hoje)

## Como retomar (cole no Claude Code)

```
Lê analise/lab-hermeneuta/_projeto/README.md e segue na ordem 1→7.
Roda python agente/sentinela.py.
Lista o que está pendente do meu lado em ordem de prioridade.
```

## Memórias relacionadas (em `~/.claude/projects/.../memory/`)

- `project_orion_caminho_a_2026_05_04.md` · estado pós-fix de hoje
- `project_orion_opcao_b_pausada.md` · Worker click→IA dormente
- `project_orion_cores_oficiais.md` · 12 hex codes pendentes
- `feedback_verificar_consumidor_antes_coletor.md` · learning do schema fantasma
- `personality_qualidade_monofloor.md` · DNA da dupla (LER PRIMEIRO de tudo)
