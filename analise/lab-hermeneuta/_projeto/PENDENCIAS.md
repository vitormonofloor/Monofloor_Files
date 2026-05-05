# 4 · PENDÊNCIAS · Em ordem de prioridade

## A · Caminho B · refactor estrutural

**Quando:** sessão dedicada · 4-6h em bloco contínuo · não fazer em pedaços
**Pré-requisito:** ler `project_orion_caminho_a_2026_05_04.md` na memória
**Fonte canônica:** `analise/lab-hermeneuta/ROADMAP_CAMINHO_B.md`

5 frentes em sequência (B1 destrava B2 · B3 finaliza limpeza):

### B1 · IA em todas as 230 obras
- Adaptar `analisar_recorte.py` pra varrer ativas (hoje só recortes manuais com max 50)
- Decidir cadência: dentro do `varredura.py` automático ou script separado disparado manual
- Custo: 230 × gpt-4o-mini · GitHub Models 8k req/dia gratuito · folgado
- Schema unificado: `veredicto`, `status_sugerido`, `urgencia`, `acao_consultor`, `tipo_demanda`, `confianca`, `flags` TODOS da IA · não heurística

### B2 · Honestidade visual
- Adicionar campo `obra.fonte_veredicto` ("ia" · "heuristica" · "sem-corpus")
- Frontend: badge ou degradê visível indicando fonte
- Tooltip: "Heurística cega · status copiado do Painel" vs "Análise IA com X mensagens"
- Critério: leitor casual vê em 1s se card foi lido ou só ecoado

### B3 · Pipeline 13 → 4 etapas
- Etapa 1: fetch painel + mensagens (substitui selecionar_piloto + coletar_painel)
- Etapa 2: IA em todas (substitui analisar_recorte + heurística)
- Etapa 3: régua/equipe/cores (mantém · enriquecimento)
- Etapa 4: publica
- **Cortar arquivos:** `agente/telethon/grupos.json`, `listar_grupos.py`, `monitorar.py`, `telegram-snapshot-prev.json`
- Avaliar: dossiês ainda agregam valor? Se não, cortar `extrair_eventos_dossie()`

### B4 · Snapshot vira cache, não corredor
- Documentar: snapshot é debug/cache · cada etapa consome painel direto via memória
- Detectar staleness · alarme se snapshot >24h ainda for usado
- Reduzir acoplamento entre etapas · etapa N não deve quebrar se N-1 não rodou

### B5 · Tom IA-driven
- Substituir heurística keyword por leitura IA do tom
- Reservar heurística atual como fallback quando IA falhar
- Validar com 5 obras conhecidas · comparar tom heurístico vs IA

**Critério de pronto do Caminho B:**
1. Lab Orion · todos 230 cards com veredito IA real, não cópia de campo
2. Cards heurísticos (sem corpus) claramente sinalizados
3. Pipeline com no máximo 5 scripts em `varredura.py` (hoje 13)
4. Sem arquivos legados Telethon no repo
5. Tempo varredura ≤ 3 min (hoje 47s sem IA · IA adiciona ~2-3 min)

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
