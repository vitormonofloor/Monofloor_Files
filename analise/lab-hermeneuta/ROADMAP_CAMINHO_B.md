# Lab Orion · ROADMAP Caminho B

**Origem:** sessão 2026-05-04 noite. O Caminho A (commit `5151bde`) destravou cobertura Telegram de 10→190 cards · ainda restam buracos estruturais que o A não cobriu.

**Objetivo do Caminho B:** transformar o Lab num produto honesto, sem mentiras heurísticas, com pipeline auditável.

---

## Contexto · o que continua quebrado

Pós-Caminho A, **190/230 cards mostram leitura Telegram real** (tom, dias de silêncio, total de msgs, timeline com 10 eventos). Bom. Mas:

- **96% dos vereditos é heurística cega** · `status_sugerido`/`urgencia`/`acao_consultor`/`tipo_demanda`/`confianca` das 220 obras não-piloto são preenchidas copiando `fase_atual` do painel · "sugestão" é tautologia · confiança 0.8 fabricada.
- **Cards "com IA" e "sem IA" são visualmente indistinguíveis** · leitor não sabe que está vendo veredito sintético.
- **Pipeline tem etapas mortas** · `monitorar.py` (Telethon) já fora do `varredura.py`, mas arquivos correlatos seguem versionados (`grupos.json`, `listar_grupos.py`, `snapshot-prev.json`).
- **Tom keyword é tapa-buraco** · pega "atraso" mesmo quando a frase é "sem atraso". Funciona pra triagem grossa, falha em nuance.

---

## Itens · marcar `[x]` ao concluir

### B1 · IA em todas as 230 obras
- [ ] Adaptar `analisar_recorte.py` pra varrer todas obras ativas (hoje só recortes manuais · max 50)
- [ ] Decidir cadência: rodar IA dentro do `varredura.py` automático, ou em script separado disparado manualmente
- [ ] Custo estimado: 230 obras × gpt-4o-mini · GitHub Models tem 8k req/dia gratuito · cobertura folgada
- [ ] Schema unificado · garantir que `veredicto`, `status_sugerido`, `urgencia`, `acao_consultor`, `tipo_demanda`, `confianca`, `flags` venham TODOS da IA, não de heurística

### B2 · Honestidade visual
- [ ] Adicionar campo `obra.fonte_veredicto` ("ia" · "heuristica" · "sem-corpus")
- [ ] Frontend: badge ou degradê visível indicando quando o card é heurística vs IA real
- [ ] Tooltip explicando: "Heurística cega · status copiado do Painel" vs "Análise IA com X mensagens"
- [ ] Critério: leitor casual vê em 1s se o card foi lido ou só ecoado

### B3 · Pipeline 13 → 4 etapas
- [ ] **Etapa 1:** fetch painel + mensagens (substitui selecionar_piloto + coletar_painel)
- [ ] **Etapa 2:** IA em todas (substitui analisar_recorte + heurística)
- [ ] **Etapa 3:** régua/equipe/cores (mantém · enriquecimento)
- [ ] **Etapa 4:** publica
- [ ] Cortar arquivos definitivamente: `agente/telethon/grupos.json`, `agente/telethon/listar_grupos.py`, `agente/telethon/monitorar.py`, `agente/telethon/telegram-snapshot-prev.json`
- [ ] Avaliar: dossiês ainda agregam valor? Se sim, formalizar geração; se não, cortar `extrair_eventos_dossie()`

### B4 · Snapshot vira cache, não corredor
- [ ] Documentar: snapshot é debug/cache · cada etapa consome painel direto via memória
- [ ] Detectar staleness · alarme se snapshot >24h ainda for usado
- [ ] Reduzir acoplamento entre etapas · etapa N não deve quebrar se N-1 não rodou

### B5 · Tom IA-driven
- [ ] Substituir heurística keyword por leitura IA do tom
- [ ] Reservar heurística atual como fallback quando IA falhar
- [ ] Validar com 5 obras conhecidas · comparar tom heurístico vs IA

---

## Critério de pronto

1. Abrir Lab Orion · todos 230 cards mostram veredito IA real, não cópia de campo
2. Cards heurísticos (sem corpus) **claramente sinalizados** como tal
3. Pipeline com no máximo 5 scripts em `varredura.py` (hoje são 13)
4. Sem arquivos legados Telethon no repo
5. Tempo de varredura ≤ 3 min (hoje 47s sem IA · IA adiciona ~2-3 min com 230 obras)

---

## Nota sobre custo de tempo

Estimativa: **4-6h em sessão dedicada**. Não fazer em pedacinhos · cirurgia precisa de bloco contínuo pra validar end-to-end.

Pré-requisito: ler `project_orion_caminho_a_2026_05_04.md` na memória antes de começar.
