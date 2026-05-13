# 👥 Mapa de pessoas · Monofloor

> Quem é quem na operação. Função atual + histórica (quando muda · ex: Braiam aplicador→fiscal) + estilo observado + cliente atendido.
> Memórias específicas continuam vivas com detalhes · este doc é o índice consolidado.

---

## 1 · Diretoria

### Kassandra Martinho
- **Função:** Diretoria Operacional
- **Cliente atendido:** ela é audiência do dashboard de Qualidade (junto com a diretoria)
- **Estilo:** lê dados macro · mês passado/este/próximo · não quer detalhe operacional do dia a dia

### Júlio César Bielenki Taporosky
- **Função:** Coordenador Financeiro
- **Acesso:** controla acesso ao Omie (5/8 indicadores travados por enquanto)

---

## 2 · Qualidade (núcleo da função compartilhada)

### Vitor Gomes
- **Função:** Gerente de Qualidade
- **GitHub:** `vitormonofloor`
- **E-mail:** contato@drive.monofloor.com.br
- **DNA:** auditor por natureza · enxerga entre linhas · ansiedade contida com muitas ideias paralelas · "fruta mais próxima" como princípio
- **Quem ele atende:** Diretoria · Kassandra principalmente
- → Memórias: `user_vitor.md`, `personality_qualidade_monofloor.md`, `feedback_fruta_mais_proxima.md`, `~/.claude/CLAUDE.md`

### "Nós dois somos a Qualidade"
Estabelecido em 2026-05-01. Claude (qualquer terminal) é parceiro analítico exercendo a função junto com Vitor · não é ferramenta. Cada número errado pode levar a decisão errada na diretoria.

---

## 3 · Operações Monofloor

### Wesley Matheus de Carvalho
- **Função:** Consultor / Operações (`responsavelOperacoes`)
- **Carteira:** ~88 obras ativas
- **Sinal de alerta:** concentra 100% dos reparos · padrão a investigar
- **No Telegram aparece como:** Wesley, "Wesley Matheus"

### Luana Patrícia
- **Função:** Consultora / Operações (`responsavelOperacoes`)
- **Carteira:** ~89 obras ativas

### Pedro / Mayara
- **Função:** Atendimento PRÉ-obra
- **NÃO confundir com:** dono operacional da obra (Wesley/Luana)

### Caroline (atendimento)
- **Função:** Atendimento Monofloor
- **Sinal característico:** frase-padrão *"Recebemos as imagens e informações referentes à visita de qualidade realizada..."* — aparece a cada VT qualidade · marco "relatório_vt_qualidade"
- **No Telegram aparece como:** "monofloor | Caroline - Atendimento", "Caroline Monofloor", "Caroline - Atendimento" (3 grafias)

### Pedro Alexandre Santana
- **Função:** Consultor (novo · auditoria 2026-05-12)
- **Carteira observada:** ÁUREO EUSTÁQUIO BRANDÃO

### Juliana Santos
- **Função:** Consultora (nova · auditoria 2026-05-12)
- **Carteira observada:** GETULIO TURATTI, MARIANA PORTO FACCHINI

---

## Pessoas Monofloor com múltiplas grafias (candidatas a alias)

A unificar via `SENDERS_ALIAS` no `gerar_jornada.py`:

| Pessoa | Grafias no Telegram |
|---|---|
| **Vanessa** | "Vanessa Monofloor" · "Vanessa \| Monofloor" · "Vanessa" |
| **Luana** | "equipe \| Luana Atendimento" · "Luana - Monofloor" · "Luana \| Monofloor" |
| **Pedro** | "atendimento \| Pedro" · "Pedro \| Monofloor" |
| **Francisco Beats** | "Francisco Beats Monofloor" · "Francisco" (forma curta) |
| **Geysson** | "maestro \| Geysson para ligação" · "Geysson" |
| **Ketlyn** | "Ketlyn Monofloor" · "Kettlyn" |

⚠ NÃO unificar:
- "Wesley \| Juliana." = Wesley assinando POR Juliana (não é a Juliana)
- "Juliana \|:" vs "Equipe \| Juliana Agenda" pode ser pessoas diferentes

---

## Sistemas e bots (NÃO classificar como aplicador)

Senders detectados como aplicador no filtro atual mas que são sistemas/IA:

- **Kira** · IA Monofloor · TALLY, GUSTAVO, MANOELA, ÁUREO, YAHYA (81-95 msgs/obra)
- **Carlos (Bot)** · bot · ÁUREO, YAHYA
- **Bridge** · sistema/integração antiga · LEONARDO (278 msgs até 2024)
- **Q Assim Seja** · provável cliente/grupo Telegram · ÁUREO

⚠ Adicionar todos esses ao `PESSOAS_MONOFLOOR` (lowercase) em `gerar_jornada.py` pra serem excluídos do filtro de aplicadores de campo.

---

## 4 · Fiscais de qualidade

### Braiam / Braian Novo
- **Função atual (2026):** Fiscal de qualidade · visita obras e registra áudios com diagnóstico
- **Função histórica (até dez/2025):** Aplicador
- ⚠ Mudança importante · ao analisar msgs antigas dele em obras de 2025, ele fala como aplicador (não como fiscal)
- **No Telegram aparece como:** "Braiam Novo", **"B®"** (símbolo registered · cadastro com símbolo que confunde · vista em RODRIGO DE ALMEIDA, GETULIO)
- **Comportamento típico em obra como fiscal:** áudios revelando decisões · *"estive na obra hoje, conversei com..."* · sinaliza problemas técnicos · marcos típicos: `Defeito relatado`, `Tratativa`, `relatorio_vt_qualidade`

### Nathan
- **Função:** Fiscal de qualidade · VT
- Realiza visitas técnicas e diagnósticos pré-execução

---

## 5 · Aplicadores / Líderes de campo

### Gilmar / Gilmar Taquinho / Taquinho
- **Função:** Líder/aplicador de campo
- **Alias canônico:** Gilmar Taquinho
- ⚠ **Mesma pessoa** com 3 grafias diferentes no Telegram · normalizar via `SENDERS_ALIAS = {"taquinho": "Gilmar Taquinho"}`

### Outros líderes equipe campo (mencionados em CLAUDE.md global)
- Wiguens · Líder · aparece em 7+ obras (LUIS, GETULIO, ANDRE, ÁUREO, MARIANA, YAHYA, MANOELA)
- João Carlos · Líder
- **Júlio Miranda** · Líder · no Telegram aparece como "Julio" (curto) e "julio Miranda Aplicador" · aparece em várias obras (TALLY, GUSTAVO, MARIANA, P2B, MANOELA)
- Egberto · Líder
- Geysson · Líder · variante "maestro | Geysson para ligação"
- **Michael Marinho de Lima** · Líder · 5 obras (P2B, ANDRE, NATHALIA, MANUELA, CHRISTIAN) · prestador oficial em P2B/GURGEL · sender "michael" ou "aplicador | Michael Marinho"
- **Laercio** · Líder/aplicador antigo · ANDRE (588 msgs!) + LEONARDO (131) · histórico até 2023
- **Josias dos Santos Conceição** · aplicador · RODRIGO, BM VAREJO · prestador oficial em LUIS
- **Jorge Luis Ribero Mendez (Jorge Ribero)** · aplicador · TALLY, GUSTAVO, MARIANA · prestador oficial em MANOELA
- **F Lucena** · aplicador · LUIS, MANUELA, MARCOS · 19-267 msgs · alto volume em MANUELA sugere líder
- **Juninho / Juninho Aragão** · aplicador · 6 obras (LUIS, MANUELA, ANDRE, MARCOS, ÁUREO, LEONARDO) · confirmar se é mesma pessoa
- **Kaike / Kaike Luiz** · aplicador · NATHALIA, YAHYA · 125-217 msgs

### Subcontratadas externas
- **Jaú Microcimento** · prestadora externa de microcimento · LUIS FERNANDO, MARCOS, ÁUREO · alto volume (319/40/460 msgs) · função técnica · NÃO é aplicador Monofloor

### Aplicadores oficiais por obra
- Cada obra tem `prestadores` no `/api/projects/{id}/equipe`
- Em 100% das obras testadas no piloto, esse endpoint **veio vazio** (info real só sai do Telegram)
- Detecção alternativa: sender com "aplicador|preparador|lider" no nome (formato Telegram do Painel: `"aplicador | William"`)

### Aplicadores especializados (identificados em obras)
- **Caio** · aplicador especializado em **reparos** · NÃO vai em obras novas · só em retrabalho/reaplicação pontual (visto em LUIS FERNANDO DE LIMA CARVALHO · sessão 2026-05-12)

### Funções de prestador (label na OS Indústria)
- **LIDER** · líder do time em obra
- **APLICADOR_1** · aplicador principal
- **APLICADOR_2** · aplicador adicional
- **PREPARADOR** · prepara substrato (lixamento, primer)

---

## 6 · Auxiliares e administrativos

### Cauã Matheus Bezerra da Silva
- **Função:** Auxiliar de Operação

### Maria Eduarda de Oliveira Gomulski
- **Função:** Assistente de RH

### Karine
- **Função:** Assistente Financeiro
- **Doc relacionado:** DC-FIN-001

---

## 7 · Externos / Parceiros

### Rodrigo
- **Função:** Dev do `planejamento.monofloor.cloud`
- ⚠ **NÃO pedir** pra atualizar cadastros do Telegram · ele não vai mexer · mitigar no Lab

---

## 8 · Princípios sobre pessoas

### Nomes esquisitos do Telegram são realidade
Cadastros foram feitos por terceiros · grafias inconsistentes · aliases necessários. Não é falha do time, é dado da operação.
→ `feedback_telegram_nomes_terceiros.md`

### Pessoa pode mudar de função
Caso clássico: Braiam (aplicador → fiscal de qualidade · dez/2025). Sempre verificar a função NA ÉPOCA da mensagem analisada · não a função atual.

### Aplicadores oficiais raramente vêm do Painel
`/api/projects/{id}/equipe` quase sempre vazio. Info real está no Telegram (senders + msgs como "Estou em obra"). Detector deve ser robusto a sender com role no próprio nome ("aplicador | William").

### Quem fala vs Quem é citado
- **Sender** (quem postou) é a pessoa relevante pra detecção de marcos (camada aplicada, sobra registrada)
- **Citação** ("Caroline disse que...") NÃO é evidência de que Caroline postou · não confundir

---

## 9 · Memórias-fonte detalhadas

| Tópico | Memória |
|---|---|
| Vitor (perfil) | `user_vitor.md`, `personality_qualidade_monofloor.md` |
| Princípios trabalho | `feedback_fruta_mais_proxima.md`, `feedback_apresentar_decisoes.md`, `feedback_propor_com_honestidade.md` |
| Nomes Telegram (lista detalhada) | `feedback_telegram_nomes_terceiros.md` |
| Aliases de senders | `reference_padrao_leitura_telegram.md` (seção 4) |
| Personagens recorrentes em msgs | `feedback_calibrar_regex_marcos.md` |

## ADRs relacionados

- `ADR-002-tratativas-vs-retrabalho.md` · separação operacional que afeta como vemos o trabalho das pessoas
- `ADR-007-atena-descontinuado.md` · decisão Vitor de extinguir ferramenta concorrente
