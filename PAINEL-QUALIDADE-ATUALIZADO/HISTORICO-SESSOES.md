# Histórico de Sessões · Linha do Tempo da Construção

> Registro cronológico das sessões de construção · 2026-04 a 2026-05.

---

## 2026-04 · Construção do Dashboard Central

**Acúmulo → Cruzamentos → Dashboard → Tema claro**

- 9 painéis dinâmicos construídos
- 26 cruzamentos de dados
- Dashboard dinâmico (fetch JSON · sem hardcode)
- Dock vertical lateral
- Tema claro aprovado: Plus Jakarta Sans · cream `#f0ebe3` · zero emojis (exceto Q2)
- 223 obras ativas no fechamento

Memória: `project_central_qualidade.md`, `project_arquitetura_paineis.md`, `project_sessao_central_2026_04.md`

---

## 2026-04-30 · Auditoria Q3+Q4+Agenda+Operacional

**12+ commits · sessão extensa**

- Auditoria completa de 4 blocos
- Líder remapeado (Gilmar/Egberto inativos no cadastro mas ativos na operação)
- Mapa real do Brasil (substituiu cartograma feio)
- Banner retrabalho separado de atraso
- Banner KIRA defasado (>60d)

Memória: `project_sessao_2026_04_30.md`

---

## 2026-05-01 (DIA) · Fechamento honesto do dashboard

**25+ commits · sessão MUITO extensa**

### Reforma Operacional (KIRA whatsappSummary)
- **Achado crítico:** KIRA está VIVO! Os campos `tagKira/whatsappGroupId/whatsappSummary` só vêm em `/api/projects/{id}` (detail), NÃO no listing
- Coletor passou a baixar 228 details em loop sequencial (~3min, cabe em 30min)
- Classificação por climaGeral: saudavel/atencao/sem_kira/retrabalho
- 203 fluxo · 82 saudáveis · 47 em atenção · 74 sem KIRA · **63.6% saudáveis das monitoradas**
- UI: KPI grande + 3 stats clicáveis + lista expandível com timeline
- **Timeline KIRA**: SVG horizontal com pontos coloridos (vermelho/cinza/verde por palavras-chave). Hover = tooltip. Click = detalhe inline
- Chip de frescor: "lido hoje / lido ontem / lido há Nd"

### Cortes deliberados
- Problemas (12 blocos → 0) · duplicação massiva e hardcodes
- Carteira/Baldes (10 baldes → 0) · sobreposição com Q1/Q2/Q3/Q4
- obras-mapa.html (720 linhas → deletado) · ninguém usava

### Refator Hero
- Manchete dinâmica no topo (zona verde/amarela/vermelha)
- Row de 5 cards (Score + 4 KPIs com mesmo peso)
- Score + delta semanal ▲▼◆
- "ⓘ Fontes" como chip discreto com tooltip flutuante

### Correções importantes
- "A INICIAR" usa `data_de_entrada` (Painel) em vez de `dataExecucaoPrevista` (chute do sistema)
- 17/22/30 firmadas (real) em vez de 43/72/115 (chutes)
- Q4_DATAS + EXT.zumbi/orfas agora fresh 30min

### Identidade compartilhada firmada
*"Hoje nós dois somos a Qualidade Monofloor."* — Vitor

Memória: `project_sessao_2026_05_01.md`

---

## 2026-05-01 (NOITE) · Lab Orion fechado + Hub integrado

**4h+ noturnas**

- Hero épico do Orion com constelação cinematográfica
- Tour dramático
- Drawer lateral
- Sentinela-balde (saúde do sistema)
- Recortes do tema
- Card-orion no Hub
- ATENA extinto · "cópia pobre do que o Lab Orion já entrega"

Memória: `project_sessao_2026_05_01_orion_noite.md`

---

## 2026-05-04 · Relatório Quinzenal de Qualidade

**Sessão atual · 30+ commits · projeto novo**

### Construção em fases
- **Fase 1.1a:** gerador funcional + 1º exemplo
- **Fase 1.1b:** 4 endpoints subutilizados integrados
- **Fase 1.1c (futura):** listagem nominal Anexo
- **Fase A:** Pipeline MD → HTML estilizado
- **Fase B (pendente):** botão no hub
- **Fase C (pendente):** bot Telegram quinzenal

### Construção em camadas
1. Esqueleto v1 com 12 seções genéricas
2. v2 com 100% Dashboard + Orion (sem indicadores antigos)
3. v3 com receitas propositivas (Como/Custo/Impacto/Risco)
4. v4 com brainstorm em todas as seções
5. P0, P0 nova, P0 nova-2 (18 fixes em 3 leituras frias externas)
6. P1 quase fechada (Brief + Glossário + Conclusão Executiva + Score com fórmula)
7. Visualizações SVG inline
8. Cargo Vitor corrigido pra Gerente da Qualidade

### Adições no Hub e Dashboard
- Dock cross-tool (Central + Dashboard + Orion)
- Modal "Como navegar" atualizado (Orion + perguntas-rota + dock)

### Memórias criadas
- `project_relatorio_quinzenal.md` (este projeto vivo)
- `feedback_relatorio_orientado_a_acao.md` (DNA do documento)
- `feedback_inventar_identidade_visual.md` (não inventar)
- `feedback_editar_canonico_nao_derivado.md` (regenerador)
- `reference_relatorio_backlog.md` (pointer pro backlog)

---

## Princípios firmados ao longo das sessões

| Princípio | Sessão de origem |
|---|---|
| Hardcode é dívida moral | 04/2026 |
| Painel de Obras, nunca Pipefy | 05/01 |
| Retrabalho separado de atraso | 04-30 |
| Frescor 30min máximo | 04 |
| Honestidade visual ativa | 04-30 |
| Cortar sem dó o que duplica | 05-01 |
| Deletar exige caçar referências | 05-01 noite |
| DNA da dupla "nós dois somos a Qualidade" | 05-01 |
| Leitor sai com respostas, não desesperado | 05-04 |
| Não inventar identidade visual | 05-01 noite |
| Editar canônico, não derivado | 05-04 |

---

## Volume de trabalho consolidado

- **5 ferramentas funcionando** (Hub · Dashboard · Orion · Coletores · Relatório)
- **9 seções no Dashboard** com 26 cruzamentos de dados
- **16 seções no Relatório** com 6 receitas propositivas e 4 visuais SVG
- **18 fixes em 3 rodadas de auditoria externa**
- **30+ pendências travadas em backlog priorizado**
- **5 fontes de API integradas** (cliente · planejamento · WhatsApp · Orion · histórico)
- **3 repositórios git** (Monofloor_Files · lab-hermeneuta-pub · cargo-assistente)
- **2 Cloudflare Workers** (refresh-all · orion-pub)
- **1 Telegram bot** (`@monofloor_op_bot`)

---

**Próximo passo natural:** P1 nova do relatório quinzenal (~45min) ou Fase B (botão no hub).
