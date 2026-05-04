# 02 · Dashboard Executivo

> **URL:** https://vitormonofloor.github.io/Monofloor_Files/analise/dashboard.html
> **Arquivo:** `analise/dashboard.html` · single-page app vanilla, ~9 mil linhas
> **Refresh:** 30 minutos automático

---

## Visão · pra que serve

Visão executiva pra a Diretoria responder em 30 segundos: *como está a operação?*

Não é um relatório operacional (cada operacional tem o Painel de Obras direto). É a **camada de Qualidade** que mostra o que a operação não enxerga sozinha.

---

## As 9 seções (em ordem de leitura)

### Hero · topo
- Manchete narrativa dinâmica (zona verde/amarela/vermelha)
- Score Saúde Operacional (0-100 · com delta semanal)
- 4 KPIs com mesmo peso visual (Total Ativas · Em Execução · Em Atraso · Em Retorno)
- Pilares (SLA · Qual · Idade · Risco) em linha discreta abaixo

### Estratégicos · 4 cards
- **TEMPO** · ciclo total mediano (172d hoje · meta 150d)
- **VOLUME** · m² em curso (4.403 hoje)
- **CAPACIDADE** · % utilização (35% hoje)
- **A INICIAR** · obras com data firmada nos próximos 30 dias

### Q1 · Higiene do Cronograma
- % no prazo · atraso mediano · obras atrasadas
- Diferenciação fluxo normal × retrabalho (princípio firmado)

### Q2 · Obras Paradas
- Cluster paralisado (5 hoje)
- Razões (cliente, clima, suprimento)

### Q3 · Equipe
- Luana × Wesley (consultoras) com %
- 6 supervisores + ~115 aplicadores
- Ranking 7 dias
- Líder remapeado quando cadastro está defasado (Gilmar/Egberto)

### Q4 · Volume
- Estado da carteira: RODANDO / ESTAGNADO / PENDENTE
- Top fases · Mapa BR clicável · Funil pré-execução
- Banner retrabalho (separado de atraso)

### Agenda
- Timeline + 10 marcos próximos
- Chip "em N dias" por evento

### Operacional · Pulso KIRA
- Cards expansíveis com timeline cronológica de eventos (extraídos do whatsappSummary)
- Classificação climática: saudável / atenção / sem KIRA / retrabalho
- Cobertura % (~65% hoje)

### Banner Retrabalho
- Obras em `reparo` + `marcas_rolo_cera`
- Separadas do atraso (princípio firmado)

---

## Como dados chegam

```
cliente.monofloor.cloud/api/projects (1.038 obras)
                  +
cliente.monofloor.cloud/api/projects/{id} (detalhe · 60+ campos)
                  ▼
        coletar-rodrigo-stats.sh (a cada 30 min · GitHub Actions)
                  ▼
        analise/dados/rodrigo-stats.json (fonte canônica única)
                  ▼
        analise/dashboard.html (fetch · render dinâmico)
```

Outros JSONs derivados:
- `headline.json` (Score + componentes · refresh PESADO 1×/dia)
- `score-historico.json` (acumula 1 entry/dia desde 2026-05-01)
- `historico-aplicadores.json` (90 dias)
- `q1-classificacoes.json` (overrides manuais)
- `details/*.json` (228 obras com whatsappSummary)

---

## Princípios firmados durante a construção

### Frescor é prioridade absoluta
Latência máxima 30 min pra dados principais. Dado congelado = banner amarelo explícito ("Dados congelados há N dias"), nunca disfarçar.

### Honestidade visual ativa
Heurística com 75% precisão? Declarar 75%. Dado ausente? Travessão `—` em vez de zero falso.

### Cortar sem dó o que duplica
Já cortamos: Problemas (12 blocos), Carteira/Baldes (10 baldes), obras-mapa.html (720 linhas), ATENA, Labs (11 arquivos), Hermes, Indicadores-v2.

### Retrabalho separado de atraso
Status `reparo` e `marcas_rolo_cera` são pós-entrega — cronograma original já cumprido. Banner próprio, não soma em estatísticas de prazo.

### Painel de Obras, nunca Pipefy
Pipefy descontinuado. Em qualquer texto visível: "Painel de Obras". JSON pode ter chaves legadas, mas usuário não vê.

---

## Pendências do dashboard (do `project_pendencias_dashboard.md`)

- 4 críticos
- 5 médios
- 5 refinamentos

Lista detalhada na memória do agente · arquivo `analise/relatorios/MELHORIAS-PENDENTES.md` é só do relatório quinzenal, não do dashboard.

---

## Histórico de construção

- **2026-04** · construção inicial · 9 painéis dinâmicos
- **2026-04-24** · tema claro aprovado (cream + Plus Jakarta + zero emojis exceto Q2)
- **2026-04-30** · auditoria Q3-Q4-Agenda-Operacional (12+ commits)
- **2026-05-01** · fechamento honesto (25+ commits) · Operacional v3 com timeline KIRA · cortes massivos
- **2026-05-04** · adição do dock cross-tool (Central + Dashboard + Orion)

Detalhe em `HISTORICO-SESSOES.md`.
