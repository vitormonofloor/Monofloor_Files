# 4 · PENDÊNCIAS · Em ordem de prioridade

## A · ~Caminho B IA-pesado~ → DESCARTADO em 2026-05-05 · substituído por cruzar_kira

**Status:** ✅ Resolvido por outra rota (Kira-driven · zero IA · zero rate limit)

Proposta original era rodar IA externa nas 228. Descobertas que mataram:
- GitHub Models tem 150 req/dia (não 8k)
- IA confundia `status` (macro) com `fase` (específica) → 100% falso positivo
- Em interrupção, perdia trabalho processado

Pivô (sugestão Vitor): *"o Kira já fez · só pegar e cruzar"*. Resultado: `cruzar_kira.py` em 213 linhas · determinístico · auditável · 3.6 min nas 228.

**Frentes do antigo Caminho B status:**
- B1 IA em todas → ~~necessário~~ · cruzar_kira cobre
- B2 Honestidade visual → parcialmente (cada veredicto tem trilha) · pendente UI
- B3 Pipeline 13→4 etapas → DESPRIORIZADO · pipeline está estável
- B4 Snapshot vira cache → DESPRIORIZADO
- B5 Tom IA-driven → DESPRIORIZADO · tom keyword é display secundário

## A2 · Refinamentos do cruzar_kira (futuro · não-bloqueador)

### R5 · Regra pra urgência média
Hoje 0 obras com `urgencia=media` (só alta/baixa). Possíveis disparos:
- Ocorrência **média** recente (≤7d) → media
- Silêncio 14-29 dias → media
- situacaoAtual com sinais de atenção mas sem palavra crítica → media

### R6 · Cruzamento whatsappSummary × ocorrencias
Detectar "dor não registrada":
- `pendenciaManual.whatsappSummary` menciona problema X
- `ocorrencias` não tem ocorrência relacionada a X
- → flag `dor_nao_registrada`

### R7 · Cruzamento materiais × mensagens
- `materiais.usaTela == false` MAS msgs contém "tela total"
- → flag `escopo_aumentando` (aditivo informal)

### UI honestidade visual
- Badge "X regras disparadas" no card
- Tooltip mostra trilha completa
- Diferenciar visualmente "coerente sem regra" de "coerente com 1 regra que não promove urgência"

---

## B · Storytelling de obra finalizada (ideia Rodrigo)

**Quando:** ~1h · pode ser hoje · não depende do Caminho B

**Origem:** Rodrigo sugeriu mapear narrativa cronológica completa de uma obra finalizada · tempo, solicitações, materiais, eventos. Vitor imediatamente pensou no Orion (é pra isso que ele serve).

**Por que dá pra fazer agora:**
- Para 1 obra específica, posso rodar `analisar_recorte.py --obra-ids <id>` cirurgicamente
- IA gpt-4o-mini · GitHub Models · custo zero · 2-3 min
- Obra finalizada = dados estáticos · snapshot defasado não machuca
- Validação retroativa do pipeline · se narrativa fica fiel, Orion entrega

**Plus:** demo poderosa pra diretoria · "olha o que o sistema lê sozinho"

**Como fazer:**
1. Vitor escolhe 1 obra finalizada que conhece bem (validação de fidelidade)
2. Rodar `analisar_recorte.py` cirurgicamente nela
3. Cruzar: corpus Telegram + análise IA + detail-snapshot + KIRA + cores + equipe
4. Montar narrativa cronológica · "Dia X chegou pedido Y · Dia Z aplicador Fulano marcou VT · materiais usados · tom evoluiu de neutro pra tenso quando Z..."
5. Saída: 1 documento estruturado · pode virar template pra outras obras

**Critérios pra escolher obra-piloto:**
- Finalizada (`fase_atual: CLIENTE FINALIZADO`)
- Corpus rico (>200 msgs · narrativa terá densidade)
- Vitor conhece bem o caso (pra validar fidelidade)

---

## C · Cores oficiais do catálogo

**Quando:** ~30min · tarefa autônoma
**Memória:** `project_orion_cores_oficiais.md`

- 21 cores oficiais no PDF do catálogo Monofloor
- 9 estão chutadas no JSON · faltam 12 hex codes
- Extrair via screenshot do PDF + amostra de pixel
- Plus ideia: "fundo rotativo · cada visita é uma obra" (cor random como BG)

---

## D · Opção B click→IA (PAUSADA)

**Status:** dormente · NÃO ATIVAR sem confirmar
**Memória:** `project_orion_opcao_b_pausada.md`

- Worker `orion-analise` deployado na CF · falta secret `GH_TOKEN`
- Workflow `analisar-orion.yml` no repo · falta push + 3 secrets
- Frontend revertido pra copy-paste manual

**Reativar quando:** outras pessoas (Rodrigo/Kassandra/diretoria) começarem a usar Orion sozinhas. Hoje Vitor é único usuário · copy-paste manual basta.

**Lição registrada:** auto-crítica antes de over-engineer · vale só com USUÁRIO REAL diferente do Vitor.

---

## E · Setup site lab.monofloor.cloud (FEITO 2026-05-04)

~~Estrutura pronta em lab-hermeneuta-pub~~
~~Configurar Cloudflare Pages~~
~~Custom domain~~

**Status:** ✅ feito · `lab.monofloor.cloud` no ar com CF Worker + Basic Auth + cookie 24h

---

## F · Refino de leitura fria · Jornada (SETADO · NÃO ATACAR AGORA)

**Quando:** depois que a arquitetura do que-mostrar estiver fechada · ~2-3h total no conjunto
**Origem:** leitura fria 2026-05-06 · simulação de leitor que nunca viu Lab Orion
**Princípio:** *foco atual é arquitetura · refino visual é última milha · fechar antes de pintar*

### Fricções priorizadas (impacto × custo)

| # | Item | Sintoma | Ação | Custo |
|---|---|---|---|---|
| F1 | Página não se apresenta | Header só diz "Lab Orion · Jornada · TELEGRAM" sem explicar o que é | Sub-header de 1 frase abaixo do título · *"Reconstrução do caminho de cada obra finalizada, lida das mensagens do Telegram do grupo da obra"* | 10min |
| F2 | Linha do tempo sem legenda visível | 6 fases coloridas, leitor depende do hover | Faixa de chips coloridos abaixo da timeline · sempre visível · 1 chip por fase com nome | 30min |
| F3 | Glossário ausente | "Hibernação", "VT", "Reaplicação", "Marco", "Atores" são jargão interno | Tooltip `?` ao lado de cada termo · 1 linha de definição cada · sem modal | 30min |
| F4 | Padrões com `snake_case` exposto | `hibernacao_longa · obra ficou 177d…` aparece como código vazado | Mapear nome técnico → label humano · "Hibernação longa" + ícone | 10min |
| F5 | "Solicitações em obra" escondida | Está embutida no card "Material" · leitor frio não acha | Card próprio · mesmo peso de "Marcos detectados" | 20min |
| F6 | Falta benchmark | "665d total · 7d execução" sem com-quê comparar · não sei se é normal ou anômalo | Linha sob as pills · *"Média Monofloor: X dias total · Y dias execução"* (provisória ok) | 30min |

### Bugs vistos na leitura fria

| # | Bug | Diagnóstico provável |
|---|---|---|
| B1 | KRYSTAL `marcos_execucao=1` mas `tempo_execucao_dias=7` | Janela de cluster ±7d pode estar perdendo dias com poucas msgs · Gantt sai vazio na obra-vitrine |
| B2 | Endereço KRYSTAL com encoding quebrado ("C�sar") | UTF-8 vs CP1252 na origem ou no fetch · normalizar string antes de salvar no JSON |

### O que NÃO mexer nesse refino

- Arquitetura de seções · ordem dos cards · estrutura JSON · pipeline de detecção
- Adicionar marco novo · subtipo novo · cor nova
- Storytelling automatizada · IA · narrativa em prosa
- Qualquer coisa que não esteja na tabela acima

**Regra de fechamento:** quando arquitetura travar, ataca F1→F6 em sequência · ~2h30 + 30min bugs · então congela.

---

## Snapshot da prioridade

```
prioridade  item                          custo    bloqueia        status
─────────────────────────────────────────────────────────────────────────
1           Storytelling obra finalizada   ~1h      —               aguarda Vitor escolher obra
2           Caminho B (5 frentes)          4-6h     B1→B2           ROADMAP versionado
3           Cores oficiais                 ~30min   —               12 hex pendentes
4           Refino leitura fria (F1-F6)    ~2h30    —               SETADO · pós-arquitetura
5           Opção B click→IA               5min     —               PAUSADA · só com novo usuário
```
