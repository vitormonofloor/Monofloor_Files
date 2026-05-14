# Retomar · Timeline de Obras

> Última atualização: **2026-05-14** (diagnóstico narrativo + barra de fluxo + filtros por perfil)
> Próximo terminal: começa lendo isso aqui pra recuperar contexto em 30s.

---

## 🆕 SESSÃO 2026-05-14 · Entrega completa do fluxo operacional

### O que foi fechado
- Refoco do projeto: doc-âncora `_projeto/ESCOPO_TIMELINE.md` criado, escopo amarrado (E1-E5)
- E1 (universo 189 obras 2026), E2 (fases), E3 (perfis A-F), E4 (gaps), E5 (propostas)
- Diagnóstico narrativo dinâmico na Tela 1 (4 blocos: panorama, desvios, velocidade, ações)
- Badge de perfil (A-F) + barra de fluxo (8 etapas) por obra na Tela 2
- Filtros por perfil (B/C/D/E/F) integrados ao sistema de filtros existente
- Stats atualizados: 4% caminho feliz, 80% reprovação (calculados dos dados)
- Legenda da barra de fluxo na Tela 2
- Acentos corrigidos em todos os textos visíveis

### Arquivos novos
- `_projeto/ESCOPO_TIMELINE.md` — doc-âncora de escopo
- `agente/e3_perfis.py` — script standalone de classificação em perfis
- `agente/e5_propostas_melhoria.md` — 6 propostas priorizadas P0-P2

### Memórias novas
- `feedback_nao_dispersar_timeline.md` — amarrar escopo antes de construir
- `feedback_dados_narrativos.md` — dados sem narrativa = decoração

### Pendências (NÃO urgentes)
- Visual: Vitor precisa usar no dia a dia e dar feedback visual
- Correlações dinâmicas (ex: "obras com VT têm X% menos reprovação")
- Sem novas ramificações — escopo fechado

### Comando pra retomar
```
Retomando timeline de obras. Leia RETOMAR_TIMELINE.md e _projeto/ESCOPO_TIMELINE.md. O site timeline_obras.html está com diagnóstico narrativo completo. O que precisa de ajuste ou refinamento?
```

---

## SESSÃO 2026-05-13 · Caminhos A, B e C fechados · D descartado

### Caminho A · Quantificação na carteira (220 vivas + 1042 histórico)

Os 7 padrões identificados nas 10 obras destrinchadas foram **testados nas 1262 obras totais**. Resultado salvo em `leituras/_padroes/2026-05-12-quantificacao-na-carteira.md` (já visível na bancada).

**3 descobertas relevantes:**
1. **44% da carteira viva está em paralisação silenciosa** (densidade <0.05 marcos/dia · 60 obras zumbis) — número novo, mais grave que imaginado
2. **MARCOS VEIGA não era o pior** — KRYSTAL LURI NUMA tem 14 reprovações em 632d (dobro do MARCOS)
3. **Hipótese P2 revisada honestamente** — reprovação pós-finalização NÃO é "em dias" (mediana 81d nas vivas, 103d histórico) · cauda longa 60-180d

**6 KPIs quantificados:**

| KPI | Vivas | Histórico |
|---|---|---|
| Cauda pós-Painel | 66.1% (158/239) | 82.5% (504/611) |
| Mediana pós-finalização | 81d | 103d |
| Postergação cascata (2+) | 24 obras | 51 obras |
| Divergência canal (formal>Telegram) | 20 obras | 46 obras |
| Paralisação silenciosa | 60 (44.4%) | 134 (41.9%) |
| Feridas abertas | 5 | 9 |

### Caminho B · Indicadores na Central de Qualidade

**Arquivos criados:**
- `analise/gerar_jornada_obras_kpis.py` · script Python que lê os 2 JSONs do timeline e gera `dados/cruz-jornada-obras.json`
- `analise/jornada-obras-qualidade.html` · página dedicada na Central · tema claro · 6 cards + 3 achados em destaque
- `dashboard.html` · 2 links cirúrgicos (header sticky + rodapé técnico) apontando pra página nova

**Estrutura da tela jornada:**
- Bloco "Achados críticos do dia" no topo (3 itens)
- Camada 1 (severidade alta): Paralisação Silenciosa · Feridas Abertas · Cauda pós-Painel
- Camada 2 (detalhe): Mediana pós-finalização (histograma) · Postergação Cascata · Divergência de Canal
- Cada card expande mostrando lista de obras nominalmente (top 15)
- Feridas abertas com `<details open>` — sempre visível pra reunião semanal

**Princípio respeitado:** fonte canônica JSON · zero hardcode no HTML · página separada não invade dashboard executivo.

### Caminho C · Alertas automáticos no pipeline — FECHADO

`gerar_alertas_jornada.py` → `dados/alertas-jornada-obras.json` · 3 gatilhos (postergação cascata, vigia pós-finalização, bandeira zumbi) · integrado ao cron como passo 4/4 · HTML consome com filtros por tipo e severidade.

52 alertas ativos (15 críticos · 13 alta · 24 média) em 221 obras.

### Caminho D · Relatório executivo pra Kassandra — DESCARTADO

Vitor decidiu não fazer (2026-05-13).

---

## 📦 SESSÃO 2026-05-12 · Bancada de Leituras criada

### Estado em uma frase
O pipeline técnico já roda sozinho. Hoje **subimos uma camada nova de interpretação**: bancada pessoal do Vitor (tela escura, fora do hub) onde leituras narrativas das obras são acumuladas, padrões cross-obras consolidados, e hipóteses testadas. **Agente global `analista-jornada-obras` criado** pra executar o trabalho em sessões futuras.

### O que entregamos hoje
1. **Meta dos 10 destrinchados fechada** — JEAN LUC, ARIANE, GUSTAVO, MARCOS VEIGA, JORGE GALLO somadas às 5 anteriores (P2B, SILVANA, PALLOMA, GINACERCHI, DONA CORINA)
2. **Análise correlacional cross-obras** — 7 padrões emergentes em 283 marcos
3. **Bancada de Leituras** (camada nova · separada do pipeline):
   - Pasta `leituras/` com `_padroes/`, `_hipoteses/`, `obras/`, `_index.json`
   - Agente global `~/.claude/agents/analista-jornada-obras.md` (5 modos: destrincha, padrões, testa, melhoria, candidatas)
   - Script `agente/gerar_leituras_html.py` · tema escuro, tabs nos padrões, tabelas md, drawer expandido
   - Tela `dados/leituras.html` — bancada pessoal, fora do hub público
4. **1ª obra na bancada (P2B Engenharia)** — leitura narrativa de 600 palavras + padrões detectados + sinais não-capturados pela regex
5. **1º padrão consolidado** — `_padroes/2026-05-12-padroes-cross-10-destrinchadas.md` com 7 sub-padrões e síntese final

### Os 7 padrões já identificados

1. **Reprovação acontece DEPOIS do Painel dizer "pronto"** · 65% das reprovações em fase "OBRA CONCLUÍDA"/"CLIENTE FINALIZADO"
2. **Vistoria final → reprovação em dias, não meses** · GUSTAVO 0d, ARIANE 5d, JORGE 17d
3. **Postergação não vem sozinha** · P2B (4x), ARIANE (3x) em janelas curtas
4. **Ocorrências formais (OS/KIRA) captam mais que Telegram puro** · PALLOMA: 15 ocorr formais, 0 reprov Telegram
5. **Eventos externos concentram-se em 4 obras** · GINACERCHI/DONA CORINA são "obras-ambiente"
6. **Densidade marcos/dia separa ritmo** · <0.05 = paralisada (JORGE 0.04 em 414d)
7. **MARCOS VEIGA é caso paradigmático** · 7 reprov + 8 ocorr formais em 397d

**Padrão maior:** o ciclo Monofloor não termina quando o Painel diz "concluído". Cauda longa 0-60d depois.

### ⚠ PENDÊNCIA ABERTA · Vitor vai decidir entre 5 caminhos

| Letra | Caminho | Custo | Resultado |
|---|---|---|---|
| **A** | Testar os 7 padrões nas 222 obras inteiras | 1-2h | 4 indicadores quantificados na carteira |
| **B** | Indicadores derivados na Central de Qualidade | 2-3h | 4 cards novos no dashboard executivo |
| **C** | Alertas automáticos no pipeline (gatilhos) | meio dia | Sistema avisa antes do problema escalar |
| **D** | Relatório executivo pra diretoria | 1 dia | Síntese estratégica saindo do Lab pra Kassandra |
| **E** | Continuar destrinchando (10 → 20 → 50) | alto, contínuo | Retorno marginal decrescente |

**Sequência sugerida:** A → B → C → D. Comecei recomendando **A** porque destrava B/C/D com 1h de trabalho.

### Hipóteses pra testar (próximas)

1. Wesley concentra 100% dos reparos?
2. Líderes diferentes têm perfis de reprovação diferentes? (Wiguens × Mendes × Michael)
3. Obras >200 msgs Telegram correlacionam com mais reprovação?
4. Postergação 2+ correlaciona com reprovação pós-finalização?

### Faltam destrinchar nas leituras (9 das 10 sem .md ainda)
SILVANA · PALLOMA · GINACERCHI · DONA CORINA · JEAN LUC · ARIANE · GUSTAVO · MARCOS VEIGA · JORGE GALLO

Em sessão futura: `Agent(subagent_type="analista-jornada-obras", prompt="destrincha SILVANA PANDOLFI")` resolve cada uma.

### Princípio de coexistência (importante)

- **Pipeline técnico** (`timeline_obras.html`) = "o que aconteceu" (marcos extraídos por regex · 220 obras)
- **Bancada de leituras** (`leituras.html`) = "como você entendeu" (interpretação narrativa)
- Não conflitam · funções distintas · NÃO misturar telas

---

## 📦 SESSÃO 2026-05-07 · Pipeline em produção

### Estado em uma frase

Sistema de timeline cronológica de obras está **em produção rodando sozinho**. Cron Windows dispara 5x/dia. Manifest incremental garante que cada rodada custa segundos. Universo: 222 obras vivas + 1042 históricas (frozen).

## Onde tudo mora

```
analise/lab-hermeneuta/
├── agente/
│   ├── timeline_10obras.py        # Script principal · 3 modos (piloto / --massa / --historico)
│   ├── gerar_html_timelines.py    # Gera HTML do JSON da massa (fallback piloto)
│   ├── gerar_leituras_html.py     # NOVO 2026-05-12 · Gera HTML da bancada de leituras
│   ├── update_timeline.bat        # BAT do cron 8/12/16/20h (4x dia)
│   └── cron_timeline_obras.bat    # BAT do cron 04h (outro terminal · 1x dia)
├── dados/
│   ├── timeline_obras.json        # 222 obras vivas · sobrescreve a cada rodada
│   ├── timeline_obras.html        # HTML acordeão · regerado automático (pipeline)
│   ├── leituras.html              # NOVO · Bancada pessoal do Vitor (tema escuro)
│   ├── timeline_historico_2026-05-07.json   # 1042 obras · frozen · 11MB
│   ├── timeline_10obras.json      # piloto · não usar mais (mantido só de regressão)
│   └── manifest_obras.json        # Cache incremental por updatedAt
├── leituras/                      # NOVO 2026-05-12 · Bancada de análise
│   ├── _index.json                # Índice gerado por gerar_leituras_html.py
│   ├── _padroes/                  # Análises cross-obras (1 .md por padrão)
│   ├── _hipoteses/                # Testes de hipótese
│   └── obras/                     # 1 .md narrativo por obra destrinchada
└── logs/
    └── update_timeline.log        # Histórico de execuções

# Agente global (mora fora do repo):
~/.claude/agents/analista-jornada-obras.md   # NOVO 2026-05-12 · 5 modos
```

## Comandos úteis

```bash
cd C:/Users/vitor/Monofloor_Files/analise

# Pipeline técnico
python lab-hermeneuta/agente/timeline_10obras.py --massa       # incremental · usa manifest
python lab-hermeneuta/agente/gerar_html_timelines.py            # regenera timeline_obras.html
python lab-hermeneuta/agente/timeline_10obras.py --historico   # 1x · 9.4min · NÃO repetir
python lab-hermeneuta/agente/timeline_10obras.py                # piloto · regressão

# Bancada de leituras (NOVO)
python lab-hermeneuta/agente/gerar_leituras_html.py             # regenera leituras.html

# Abrir telas
start "" "lab-hermeneuta/dados/timeline_obras.html"             # pipeline
start "" "lab-hermeneuta/dados/leituras.html"                    # bancada
```

## Comandos do agente analista-jornada-obras (em nova sessão Claude Code)

```python
# 5 modos disponíveis:
Agent(subagent_type="analista-jornada-obras", prompt="destrincha SILVANA PANDOLFI")
Agent(subagent_type="analista-jornada-obras", prompt="padrões")
Agent(subagent_type="analista-jornada-obras", prompt="testa: Wesley concentra 100% dos reparos?")
Agent(subagent_type="analista-jornada-obras", prompt="melhoria: postergacao-em-cascata")
Agent(subagent_type="analista-jornada-obras", prompt="candidatas")
```

## Cron Windows (2 tarefas convivendo)

```cmd
# Listar
schtasks /Query /FO LIST | findstr Monofloor

# Ver detalhes
schtasks /Query /TN "MonofloorTimelineUpdate" /V /FO LIST

# Rodar manualmente
schtasks /Run /TN "MonofloorTimelineUpdate"

# Tarefas vivas:
# - "Monofloor_Timeline_Obras"  · diário 04h     · cron_timeline_obras.bat
# - "MonofloorTimelineUpdate"   · 8/12/16/20h    · update_timeline.bat
```

## Resultados últimos da massa

- **222 obras vivas** processadas · 2295 marcos · 0 erros · 4.9s incremental
- **1042 obras históricas** processadas · 6057 marcos · 0 erros · 9.4min (1x)
- **Cobertura por status**: vivas operacionais 80-100% Telegram · finalizadas antigas só 12% (Pipefy puro pré-Telegram)

## Achados qualitativos descobertos no caminho

- **Bloqueio 260 vs 200 era paginação escondida** · API tem default 200 sem `?limit` · `?ativa=true` é IGNORADO · usar `?limit=5000` pra pegar tudo (1042)
- **257 da UI** = `status not in (finalizado, concluido)` · inclui canceladas (35)
- **222 vivas Qualidade** = `STATUS_VIVOS_QUALIDADE` (exclui cancelado · uso oficial)
- **3 ciclos detectados em GETULIO** (caso clássico) · 1ª execução → gap 75d → reaplicação
- **Aplicadores oficiais (`/equipe.prestadores`) vêm vazios em ~100% das obras** · info real só vem do Telegram (senders + "estou em obra")
- **Discrepâncias do Painel detectadas**: status registrado antes da 1ª msg · finalizado sem aprovação · em_execucao com retrabalho ativo · etc.

## Próximos passos opcionais (deixados em aberto)

1. **HTML do histórico** · renderizar as 1042 obras em uma 2ª página (reusa código de `gerar_html_timelines.py` apontando pra `timeline_historico_2026-05-07.json`)
2. **Análise comparativa vivas × histórico** · medianas populacionais robustas com N=1042
3. **Calibrar mais obras** · destrinchamos só P2B/SILVANA/PALLOMA · vocabulário de outras equipes pode ter padrões próprios
4. **Filtro/busca client-side no HTML** quando 222 obras ficarem pesadas de navegar

## DNA do projeto

- **Standalone** · não toca em arquivos do Lab Orion (`gerar_jornada.py`, `cruzar_kira.py`, `varredura.py`, `jornadas.json`, `index.html`)
- **Princípio de coexistência** documentado em `_projeto/PADRAO_LEITURA_TELEGRAM.md`
- **Sem IA · sem token · custo zero** · puro Python regex + HTTP + pdfplumber
- **Linguagem leiga** · "Tempo entre marcos" não "Δt" · "Discrepâncias" não "Mentiras" · "Execução" não "Durante · Execução até finalização"
- **Tom diplomático** com discrepâncias do Painel · "Painel registra X · Telegram indica Y"

## Memórias do agente

- `project_timeline_obras_2026_05_06.md` (este projeto · histórico completo)
- `reference_api_painel_obras.md` (vocabulário do `/api/projects` · CONSULTAR antes de mexer em massa)
- `reference_padrao_leitura_telegram.md` (princípio de coexistência multi-terminal)
- `feedback_calibrar_regex_marcos.md` (regex literal vs vocabulário real)
- `feedback_kira_ja_interpretou.md` (campos semânticos prontos · não pedir IA externa)
