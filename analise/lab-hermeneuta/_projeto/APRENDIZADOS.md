# 6 · APRENDIZADOS · Padrões consolidados

> Lições de batalha que valem mais que documentação genérica · padrões a seguir e armadilhas a evitar

## 1 · Antes de culpar coletor, verificar consumidor

**Origem:** 2026-05-04 · Caminho A · KRYSTAL com `telegram.ultima_msg=null`

**Padrão:** quando dado some, reflexo é "coletor quebrou". Mas existe pior: NINGUÉM monta o campo · é schema fantasma herdado.

**Como aplicar:**
1. Antes de assumir coletor quebrado · `grep -r "<nome_do_campo>" --include="*.py"` no projeto
2. Se aparece só em arquivos de prompt/schema/docs e em nenhum `<obra>["campo"] = ...` ou similar · é ÓRFÃO
3. Em pipelines com etapas legadas + novas, conferir se runner principal ainda chama scripts mortos · etapa fantasma esconde quem deveria estar fazendo o trabalho
4. Quando 2 sistemas (legado + novo) compartilham mesmo schema, o "schema vira contrato fantasma" · leitor espera campos que escritor não popula

**Custo da lição:** 220 obras mentindo "silêncio prolongado" por dias até descobrir.

## 2 · Painel é o produto do Kira · etapa intermediária é candidata a corte

**Origem:** 2026-05-04 · diagnóstico das redundâncias

**Padrão:** Painel de Obras (Kira) já transcreveu áudios, descreveu fotos, indexou mensagens. Nossa função é EXTRAIR e ANALISAR. Toda etapa entre fetch e análise é candidata a deletar.

**Como aplicar:**
1. Ao desenhar pipeline · perguntar "essa etapa adiciona inteligência ou só transforma formato?"
2. Snapshots intermediários são úteis pra debug · não pra arquitetura
3. Cada JSON intermediário cria oportunidade de drift silencioso · medir custo/benefício

**Trade-off honesto:** snapshots ajudam debug e cache. Mas viram corredor obrigatório por inércia. Decidir explicitamente.

## 3 · Custo de tempo · 4-6h corridos > pedacinhos

**Origem:** 2026-05-04 · Vitor "vai" pro Caminho B vs auto-crítica do Claude

**Padrão:** refactor estrutural de pipeline tem custo de contexto · trocar de cabeça mid-flight é caro. Tarefa de 4-6h corrida é mais segura que 4 sessões de 1h.

**Como aplicar:**
1. Estimar tarefa em "blocos contínuos" · não em "horas de trabalho"
2. Se tarefa tem >2h e exige validação end-to-end · agendar bloco dedicado
3. Não começar refactor de noite após sessão pesada · cabeça cansada gera bug

**Sinal de alerta:** "vai" do usuário depois de jornada longa · auto-crítica honesta pode bater o impulso de produzir.

## 4 · Honestidade visual

**Origem:** 2026-05-04 · descoberta de que cards heurísticos parecem inteligentes

**Padrão:** quando sistema mistura análise IA com fallback heurístico, o leitor PRECISA distinguir. Se não distinguir, o sistema mente por omissão.

**Como aplicar:**
1. Sempre adicionar campo `fonte_*` no schema (ex: `fonte_veredicto: "ia" | "heuristica" | "sem-corpus"`)
2. Frontend mostra badge / degradê / tooltip indicando origem do dado
3. "Confiança" fabricada (ex: 0.8 hardcoded) é pior que "confiança ausente"

**Custo da lição:** 220/230 cards do Lab Orion parecendo veredito IA quando eram heurística cega copiando campo do Painel.

## 5 · Git push em CI · `add -A` + `pull rebase autostash` + `exit 1`

**Origem:** sessões anteriores · 21h de silêncio porque CI falhou silenciosamente

**Padrão:** scripts CI que fazem `git push` precisam de:
- `git add -A` · não lista fixa de arquivos (esquece arquivo novo)
- `git pull --rebase --autostash` · resolve diverge
- `exit 1` · não retry silencioso (esconde falha real)

**Memória:** `feedback_git_push_ci.md`

## 6 · Identidade visual · NÃO inventar · confirmar fonte primeiro

**Origem:** 2026-05-XX · 2 retrabalhos no card+overlay Orion

**Padrão:** quando pedido é "inspire-se em X" · PARAR e conferir X (curl/screenshot) antes de escrever 1 linha de SVG/CSS.

**Memória:** `feedback_inventar_identidade_visual.md`

## 7 · Quando há regenerador automático · editar a FONTE

**Origem:** Orion tem `publicar.py` que copia HTML do canônico pro pub

**Padrão:** sempre identificar o arquivo canônico VS arquivos derivados antes de editar. Mexer em derivado é desperdício · próxima varredura sobrescreve.

**No Orion:** HTML canônico em `analise/lab-hermeneuta/index.html` · NÃO editar `lab-hermeneuta-pub/public/index.html`.

## 8 · Apresentar decisões em IMPACTO, não jargão dev

**Origem:** Vitor faz leitura dinâmica em opções técnicas e clica ok sem avaliar

**Padrão:** traduzir cada opção técnica em:
- Impacto operacional ("destrava 220 cards" > "fix do bloco órfão")
- Custo do tempo do Vitor ("você esperaria 1h" > "rodando varredura")
- Trade-off honesto (prós e contras do leitor · não só do código)

**Memória:** `feedback_apresentar_decisoes.md`

## 9 · Auto-crítica honesta antes de propor

**Origem:** DNA Qualidade Monofloor consolidado

**Padrão:** antes de sugerir mudança · perguntar honestamente:
- O que ficaria MELHOR?
- O que poderia ficar PIOR / mais confuso?
- Existe simplificação que não pensei?

Se a auto-crítica for vazia ("tudo melhora") · provavelmente não pensei direito.

**Exemplo aplicado hoje:** Vitor disse "pode seguir". Em vez de atacar Caminho B, auto-crítica revelou que eu mesmo recomendara "bloco contínuo de 4-6h, não pedaços". Honestidade venceu impulso de produzir.

## 10 · Tom keyword é tapa-buraco aceitável

**Origem:** 2026-05-04 · `calcular_bloco_telegram` no Caminho A

**Padrão:** quando tarefa pede análise semântica e IA não está disponível na hora, heurística keyword é aceitável SE:
1. Sinalizar como heurística (não fingir IA)
2. Documentar limitações (pega "atraso" em "sem atraso")
3. Reservar substituição por IA pra próxima iteração

**Não fazer:** heurística disfarçada de IA com confiança fabricada.
