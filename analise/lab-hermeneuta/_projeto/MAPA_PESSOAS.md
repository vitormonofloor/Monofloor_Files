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
- **No Telegram aparece como:** "monofloor | Caroline - Atendim"

---

## 4 · Fiscais de qualidade

### Braiam / Braian Novo
- **Função atual (2026):** Fiscal de qualidade
- **Função histórica (até dez/2025):** Aplicador
- ⚠ Mudança importante · ao analisar msgs antigas dele em obras de 2025, ele fala como aplicador (não como fiscal)
- **No Telegram aparece como:** "Braiam Novo"

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
- Wiguens · Líder
- João Carlos · Líder
- Júlio Miranda · Líder
- Egberto · Líder
- Geysson · Líder

### Aplicadores oficiais por obra
- Cada obra tem `prestadores` no `/api/projects/{id}/equipe`
- Em 100% das obras testadas no piloto, esse endpoint **veio vazio** (info real só sai do Telegram)
- Detecção alternativa: sender com "aplicador|preparador|lider" no nome (formato Telegram do Painel: `"aplicador | William"`)

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
