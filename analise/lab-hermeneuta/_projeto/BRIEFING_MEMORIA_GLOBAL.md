# 📦 Briefing pra terminal paralelo · consolidar memória global do Vitor

> Cole isto inteiro no Claude Code de outro terminal. Ele tem contexto zero — o briefing é self-contained.

---

## Quem está te pedindo isso

Vitor Gomes — Gerente de Qualidade Monofloor. Ele quer **memória global persistente** que TODOS os terminais Claude Code dele leiam, em qualquer pasta, em vez de manter o conhecimento sobre ele preso a 1 working dir.

Hoje as memórias vivem em `C:\Users\vitor\.claude\projects\C--Users-vitor\memory\` (55 arquivos · auto-memory por projeto). Isso fica restrito ao projeto atual.

---

## Objetivo

Criar **2 arquivos** em `C:\Users\vitor\.claude\`:

| Arquivo | Auto-load? | Conteúdo |
|---|---|---|
| `CLAUDE.md` | ✅ SIM (em toda sessão) | **Vitor Gerente Monofloor** · denso, essencial, presente em 100% dos terminais |
| `PERFIL_VITOR_PESSOA.md` | ❌ NÃO (leitura sob demanda) | **Vitor pessoa** · leve, projetos pessoais (reforma, DIY), curiosidades |

A separação é decisão explícita do Vitor: ele usa "Vitor pessoa" pouquíssimo, não vale poluir o contexto de toda sessão com isso.

---

## Princípios de qualidade (NÃO NEGOCIÁVEIS)

1. **Enxuto** · `CLAUDE.md` global ~150-200 linhas no MAX. Texto denso, sem enfeite. Esse arquivo entra em TODA sessão Claude Code do Vitor — cada linha custa contexto.
2. **PT-BR** sempre.
3. **Sem emoji decorativo** (exceto se já estavam nos títulos das memórias-fonte).
4. **Não duplicar memórias de projeto** · Lab Orion, dashboard, relatório quinzenal, sessões datadas, bugs específicos — TUDO isso continua em `~/.claude/projects/C--Users-vitor/memory/`. O `CLAUDE.md` global aponta pra elas, não copia o conteúdo.
5. **Não inventar nada** · só consolide o que já está nas memórias-fonte. Se não está lá, não entra.
6. **Apresente pro Vitor antes de salvar** · ele revisa, ajusta, aí você grava.

---

## Fontes a ler (categorize ANTES de escrever)

Diretório-fonte: `C:\Users\vitor\.claude\projects\C--Users-vitor\memory\`

### Vão pro CLAUDE.md global (Gerente Monofloor)

**Personalidade · alma · DNA**
- `personalidade.md`
- `personality_qualidade_monofloor.md`
- `user_vitor.md`

**Princípios de trabalho universais**
- `feedback_abordagem.md`
- `feedback_apresentar_decisoes.md`
- `feedback_propor_com_honestidade.md`
- `feedback_fruta_mais_proxima.md` ← criada hoje 2026-05-06, importante
- `feedback_inventar_identidade_visual.md`
- `feedback_editar_canonico_nao_derivado.md`
- `feedback_relatorio_orientado_a_acao.md`
- `feedback_diretoria_perguntas.md`
- `feedback_dashboard_visao.md`
- `feedback_design_obras_mapa.md`
- `feedback_git_push_ci.md`
- `feedback_kira_ja_interpretou.md`
- `feedback_calibrar_regex_marcos.md`
- `feedback_telegram_nomes_terceiros.md`
- `feedback_nomenclatura_painel_obras.md`
- `feedback_retrabalho_separado.md`
- `feedback_ritual_fim_sessao.md`
- `feedback_verificar_consumidor_antes_coletor.md`
- `esquadrao_auditoria.md`

**Contexto Monofloor (síntese, não cópia)**
- `reference_monofloor_cloud.md` (resumir endpoints — não copiar URL completa de cada um)
- 1 parágrafo sobre a empresa (piso polido STELION/LILIT, 228 obras, BR todo, ticket médio)
- Sistemas em uso (Pipefy, Telegram, WhatsApp, Omie, D4Sign) — só lista, sem detalhe
- Pessoas-chave (1 linha cada)

### Vão pro PERFIL_VITOR_PESSOA.md (não auto-load)

- `pessoal_reforma_corredor.md`
- `pessoal_reforma_banheiro.md`
- `feedback_planta_geometria_3segmentos.md` (é da reforma do banheiro)

### NÃO entram em nenhum dos dois (continuam onde estão)

- Tudo que começa com `project_*` (estado de projeto)
- Tudo que começa com `reference_*` exceto `reference_monofloor_cloud` (são links externos · ponteiro basta)
- `backlog_refinamento_central.md`
- Sessões datadas (`project_sessao_*`)

---

## Estrutura sugerida do CLAUDE.md global

Seções, em ordem (ajuste se ficar mais natural diferente):

1. **Quem é Vitor** · cargo, função, GitHub, repos principais
2. **Monofloor em 1 parágrafo** · empresa, produto, escala
3. **Como Vitor pensa** · princípios consolidados (DNA da dupla, fruta mais próxima, ansiedade contida, qualidade > velocidade quando há custo de retrabalho, "nós dois somos a Qualidade")
4. **Como Vitor decide** · apresentar opções em IMPACTO operacional não jargão dev, propor com honestidade prós/contras, leitura dinâmica (ele clica ok sem avaliar se você não traduzir)
5. **Como trabalhar com Vitor** · ação direta, técnico/analítico sem decoração, PT-BR sempre, sem emoji exceto pedido
6. **Lições registradas** · incidentes que valem evitar repetir (git push em CI, identidade visual não-inventada, editar canônico não derivado, regex calibrada com linguagem real, schema fantasma)
7. **Convenções Monofloor** · "Painel de Obras" nunca "Pipefy", retrabalho ≠ atraso, Telegram nomes esquisitos são realidade, Kira já interpretou (não reinventar)
8. **Branding** · #0a0a0a fundo, #c4a77d dourado, Inter (tema escuro padrão · há projetos em tema claro)
9. **Sistemas em uso** · 1 linha cada (Pipefy, Telegram, WhatsApp Business, Omie, D4Sign)
10. **Pessoas-chave** · 1 linha cada
11. **Onde mora cada projeto** · ponteiros · *"Lab Orion · `~/.claude/projects/.../memory/project_orion_*` · pivô Kira-driven 2026-05-05"* etc

No fim do CLAUDE.md, 1 frase: *"Quando o assunto for não-Monofloor (reforma, DIY, projeto pessoal), leia também `~/.claude/PERFIL_VITOR_PESSOA.md`."*

---

## Estrutura do PERFIL_VITOR_PESSOA.md

Curto · ~30-50 linhas. Tipo:

- 1 parágrafo: Vitor fora do trabalho — DIY, projetos pessoais, gosta de planejar antes de fazer
- **Reforma corredor** · 1 parágrafo do que é · ponteiro pra memória detalhada
- **Reforma banheiro** · idem · inclui o aprendizado de geometria 3 segmentos
- Regra: NÃO confundir com trabalho Monofloor

---

## Como rodar (passo a passo)

1. Lê este briefing inteiro
2. Lê as memórias-fonte listadas acima (use Read · não invente nada)
3. **Antes de escrever**, mostre pro Vitor um esqueleto (só os títulos das seções + 1 frase de cada) pra ele aprovar a estrutura
4. Aprovado o esqueleto, escreve os 2 arquivos
5. Mostra **prévia em texto** dos 2 arquivos no chat (não grava ainda)
6. Vitor revisa, aponta ajustes
7. Aplica ajustes
8. **Aí sim** salva nos paths definitivos:
   - `C:\Users\vitor\.claude\CLAUDE.md`
   - `C:\Users\vitor\.claude\PERFIL_VITOR_PESSOA.md`
9. Confirma com `ls C:\Users\vitor\.claude\*.md` que os 2 estão lá
10. Avisa o Vitor que tá pronto

---

## Critérios de aceite

- `CLAUDE.md` global tem ≤ 200 linhas, denso, sem repetir o que está em memórias de projeto
- Contém todos os 19 princípios listados acima (sem perder nuance — `feedback_fruta_mais_proxima` é especialmente importante, foi consolidado hoje)
- Contém ponteiros pros projetos vivos (Lab Orion, dashboard, relatório quinzenal) sem copiar conteúdo deles
- `PERFIL_VITOR_PESSOA.md` separado, ≤ 50 linhas, fora do auto-load
- Vitor leu, ajustou, aprovou antes de gravar

---

## O que NÃO fazer

- ❌ NÃO mexer em `MEMORY.md` ou em qualquer arquivo dentro de `~/.claude/projects/C--Users-vitor/memory/` · esse sistema continua vivo
- ❌ NÃO criar pasta nova em `~/.claude/` · só os 2 arquivos no nível raiz
- ❌ NÃO copiar conteúdo de memórias de projeto pro CLAUDE.md global · só ponteiros
- ❌ NÃO inventar princípios que não estão nas memórias-fonte
- ❌ NÃO encher de emojis ou decoração — texto denso, profissional, técnico
- ❌ NÃO fazer commit/push automático · esses arquivos são locais (estão em `~/.claude/`, fora de qualquer repo git)

---

## Contexto extra que ajuda

- Vitor trabalha "ansiedade contida" · muitas ideias paralelas · risco real é dispersão. O princípio "fruta mais próxima" foi cunhado por ele hoje (2026-05-06).
- A dupla Vitor + Claude se identifica como "Qualidade Monofloor" desde 2026-05-01 — não é só user/assistant, é função compartilhada.
- O outro terminal (você) está fazendo isso EM PARALELO enquanto o terminal principal segue trabalhando na "Jornada do Projeto" do Lab Orion. Não interrompa o Vitor a menos que algo esteja realmente bloqueando.
- Tempo estimado: 30-45min de leitura cuidadosa + 20-30min de redação + revisão. Se passar de 1h30, sinaliza.

Boa sorte. Faça denso, faça útil, faça pro Vitor não precisar refazer.
