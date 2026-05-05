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

## Snapshot da prioridade

```
prioridade  item                          custo    bloqueia        status
─────────────────────────────────────────────────────────────────────────
1           Storytelling obra finalizada   ~1h      —               aguarda Vitor escolher obra
2           Caminho B (5 frentes)          4-6h     B1→B2           ROADMAP versionado
3           Cores oficiais                 ~30min   —               12 hex pendentes
4           Opção B click→IA               5min     —               PAUSADA · só com novo usuário
```
