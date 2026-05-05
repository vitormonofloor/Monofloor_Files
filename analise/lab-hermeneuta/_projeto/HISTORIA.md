# 1 · HISTÓRIA · Linha do tempo + decisões arquiteturais

## Origem

**HERMENEUTA-LAB** começa como sandbox em abril/2026 · ideia: cruzar grupos Telegram (verdade do que está acontecendo na obra) com Painel oficial (verdade burocrática) pra detectar divergências invisíveis pra gerência. Hipótese central: **operação fala mais a verdade no Telegram que no formulário do painel**.

## 2026-04-XX · Construção inicial

- Telethon (userbot do Vitor) puxa msgs de grupos pareados por similaridade de título
- Pipeline em scripts Python · saída JSON · frontend HTML estático
- Modo `--todas` pareadas: 82 obras (das 227 ativas) · resto sem grupo Telegram identificado
- Janela 15 dias / cap 80 msgs · herança Telethon (rate limit)
- IA HERMENEUTA v3 manual via copy-paste de prompt + corpus

## 2026-05-01 · Fechamento Lab + Hub integrado · NOITE

Sessão pesada de ~4h:
- **Rebranding HERMENEUTA → ORION** aplicado (nome do caçador · 3 estrelas do cinturão = painel × telegram × KIRA · termina em ON igual STELION/TERON)
- Hero épico + tour + drawer + sentinela-balde + recortes
- Card-orion no Hub Monofloor (constelação cinematográfica)
- **ATENA extinto** (era cópia pobre do Orion · não recriar)
- Identidade compartilhada formalizada: "Nós dois somos a Qualidade Monofloor"

## 2026-05-04 · MIGRAÇÃO Telethon → Painel API

Investigação "Em execução: 6" levou à descoberta: **Painel de Obras já tem API pública** (`cliente.monofloor.cloud/api/projects/{id}/messages`) com:
- Telegram + WhatsApp na mesma obra
- Áudios transcritos pela IA do backend
- Fotos descritas pela IA do backend
- Sem auth, sem rate limit

Trocamos `telethon/monitorar.py` por `telethon/coletar_painel.py` (drop-in compatível).

## 2026-05-04 NOITE · Caminho A · cirurgia do schema fantasma

Investigando KRYSTAL LURI NUMA (1 obra) descobrimos buraco estrutural:

- 220/230 cards com `telegram.ultima_msg = null`
- 45 das 54 obras com corpus tinham o corpus DESCARTADO
- 35 obras com mensagem nos últimos 7d aparecendo como silêncio

**Causas-raiz (3 forks paralelos):**
1. Bloco `telegram` órfão · NENHUM script vivo montava `ultima_msg/dias_silencio/tom_grupo` · era schema fantasma herdado da IA legada manual
2. `extrair_timeline.py:184` abortava sem dossiê (maioria não tem) · eventos zeravam
3. `coletar_painel.py` truncava em 80 msgs/15d sem motivo (herança Telethon · API não precisa)
4. `varredura.py:201` ainda chamava `monitorar.py` (Telethon morto) · etapa fantasma rodando

**Fix em 3 arquivos · commit `5151bde`:**
- `coletar_painel.py` · defaults 2000/90d · ordena cronológico
- `extrair_timeline.py` · dossiê opcional + função `calcular_bloco_telegram()` (heurística keyword pra tom · zero IA)
- `varredura.py` · troca Telethon morto por `selecionar_piloto --todas-ativas + coletar_painel`

**Resultado medido:** 190/230 cards reais · 20.166 msgs cobertas · 119 obras com atividade últimos 7d · top alerta AVVA HOUSE 12 sinais tensos · 0 positivos.

## 2026-05-04 noite · ROADMAP Caminho B

Mapeamos 5 frentes pra refactor estrutural (sessão dedicada 4-6h):
- B1 IA em todas 230 (não só recortes)
- B2 Honestidade visual (cards com IA vs heurística distinguíveis)
- B3 Pipeline 13→4 etapas + cortar legado Telethon
- B4 Snapshot vira cache, não corredor obrigatório
- B5 Tom IA-driven (substitui keyword)

Versionado em `ROADMAP_CAMINHO_B.md` (commit `debcfb6`).

## 2026-05-04 noite · Storytelling proposto pelo Rodrigo

Ideia: pegar 1 obra finalizada e mapear narrativa cronológica completa (tempo, solicitações, materiais, eventos). **Pode fazer hoje** · não depende de Caminho B (rodando IA cirurgicamente em 1 obra via `analisar_recorte.py`).

Storytelling GURGEL DALFONSO entregue (commit `c71b8e3`) · 5 atos · 207 dias contrato → entrega · 4 dias execução real. Surge a lente analítica "tempo de retomada vs tempo morto" (próxima sessão dedicada).

## 2026-05-05 · Pivô do Caminho B · IA externa → cruzar_kira (Kira-driven)

Tentativa inicial: rodar IA externa (gpt-4o-mini via GitHub Models) nas 228 ativas.
Problemas descobertos:
- Limite real é **150 req/dia**, não 8k como eu tinha lido
- IA confundia `status` (categoria macro) com `fase` (estágio específico) · sempre dava `status_desatualizado`
- Em interrupção (TaskStop), o script perdeu 138 obras processadas (salvava só no fim)
- Custo de prompt engineering iterativo · frágil

**Pivô (sugestão do Vitor):** *"pegar o que já tem no Kira no Painel, compilar no Orion e cruzar pra verificar atualizações. Processo curto e detalhado."*

Insight: o Kira **já interpretou semântica** em vários campos do Painel — `tagKira`, `situacaoAtual`, `ocorrencias` (com severidade!), `pendenciaManual.whatsappSummary`. Estávamos pedindo IA externa pra **reinterpretar o que já estava interpretado**.

Solução simples: `cruzar_kira.py` · 213 linhas · 4 regras determinísticas:
- R1 · tagKira indica concluído mas status ativo → status_desatualizado
- R2 · ocorrência alta nos últimos 7d → urgência alta + flag
- R3 · situacaoAtual com URGENTE/RISCO/atraso → flags
- R4 · dias_silencio ≥30 + ativa → abandono

**Resultados em 228 obras · 3.6 min:**
- 204 coerentes (89.9%)
- 20 abandonos detectados (8.8%) ← ninguém via
- 3 status_desatualizado com sugestão clara
- 47 com urgência alta · 100% rastreável a fonte (ocorrência ou texto-fonte)
- Cada veredicto tem `analise_kira_trilha` · auditável

Integrado no `varredura.py` como passo 12b (entre `marcar_refresh_status` e `sentinela`). Roda 12h+18h sem rate limit, sem custo, sem token.

`analisar_recorte.py` (IA externa) mantido como fallback opcional · não é mais o caminho principal.

---

## Decisões arquiteturais que importam

### Por que **Painel API** (não Telethon)
- Sem auth · público
- Sem rate limit Telegram
- Multi-canal (TG + WA)
- Áudio/foto já descritos pela IA do Kira
- **Insight Vitor:** "tudo já foi feito pelo Kira · nossa função é só extrair e analisar"

### Por que **GitHub Models** (não Anthropic API)
- Gratuito (~~8k~~ **150 req/dia** · descoberto em 2026-05-05 · suficiente pra rodadas pontuais, não pra todas 228)
- gpt-4o-mini é bom o suficiente pra triagem
- Anthropic API ficaria cara e seria bloqueador (token pendente)
- **Atualização 2026-05-05:** GitHub Models virou fallback · caminho principal é determinístico (`cruzar_kira.py` aproveitando interpretação do Kira)

### Por que **Kira-driven** (não IA externa) [adicionado 2026-05-05]
- O Painel já tem semântica do Kira em `tagKira`/`situacaoAtual`/`ocorrencias`
- IA externa estava re-interpretando dados já interpretados · redundância
- Determinístico = auditável (cada veredicto tem trilha)
- Zero rate limit, zero custo, ~3.6 min nas 228

### Por que **CF Workers + Static Assets** (não CF Pages)
- Worker permite Basic Auth + cookie 24h sem hassle
- Static Assets serve `/dados/*.json` direto (sem build)
- `run_worker_first=true` garante que auth roda antes de tudo
- Pages exigia auth via env vars + roteamento mais complicado

### Por que **custo zero** sempre que possível
- Heurística determinística > IA quando a tarefa é cálculo (datas, contagens)
- IA reservada pra leitura semântica (veredicto, tom)
- Backup rolling local · não depende de cloud paga
- Decisão de DNA: "Monofloor opera em margem · não dá pra entupir de SaaS"

### Por que **pipeline 13 etapas** (e por que vai virar 4 no B3)
- 13 etapas vieram do crescimento orgânico · cada nova feature virou script
- Vantagem: cada etapa testável isoladamente
- Problema: muitos JSONs intermediários · acoplamento implícito · drift silencioso
- Caminho B vai colapsar em 4: fetch · IA · enriquecimento · publica
