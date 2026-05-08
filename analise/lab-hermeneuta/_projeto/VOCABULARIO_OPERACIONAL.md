# 🏷 Vocabulário Operacional Monofloor

> Documento canônico consolidando todos os termos, apelidos, traduções e nomenclaturas usados na operação Monofloor.
> Qualquer terminal/agente que mexer com obras DEVE consultar isto antes de escrever regex, classificação ou copy.
> Memórias específicas continuam vivas com detalhes · este doc é o índice + tabelas rápidas.

---

## 1 · Produtos · OS Indústria × campo

Aplicadores no Telegram NÃO usam o nome canônico do produto. Eles usam apelido de campo. Sem essa tradução, qualquer cálculo de consumo/cobertura/camadas cai em famílias separadas e mente.

| Produto na OS | Aplicador no Telegram diz | Família canônica |
|---|---|---|
| **STELION** | "stelion", "kalahari" (cor), "argento" (cor) | STELION |
| **LILIT** | "lilit" | LILIT |
| **LEONA** *(pré abr/2026)* / **TERON** *(abr/2026 em diante)* | "leona", "teron" | LEONA |
| **LUMINA** | **"verniz"**, "lumina" | LUMINA |
| **LUMINA PRIMER** | **"primer"** | PRIMER |

### Pontos de atenção
- **LUMINA é o verniz** · *"Verniz finalizado"* significa LUMINA (item da OS) aplicado · não existe item separado "VERNIZ"
- **Primer é LUMINA PRIMER** · aplicador diz só "primer" · OS lista "LUMINA PRIMER - 1KG"
- **TERON renomeação abr/2026** · OS pode listar LEONA enquanto aplicador diz "teron" no mesmo dia (transição)
- **Cores STELION** (Kalahari, Argento) · aplicador pode usar a cor como sinônimo do produto

→ Memória detalhada: `reference_nomenclatura_produtos.md`

---

## 2 · Termos de operação

### Macro-etapas da Jornada

| Termo | Definição |
|---|---|
| **Pré-obra** | Tudo que antecede a aplicação física · planejamento, escolha de cor, VT, agendamento |
| **Execução** | Aplicação física do material em obra (1ª entrega · Ciclo 1) |
| **Tratativas** | Negociações, definições, relatórios e acompanhamento dentro de ciclo de retrabalho · sem trabalho físico ainda |
| **Retrabalho** | Reaplicação física com prestadores em obra após reprovação · só dias de aplicação nova |
| **Pós-obra** | Após aprovação final do cliente · acompanhamento e fechamento |
| **Hibernação** | 30+ dias consecutivos sem mensagens · tempo morto entre interações |

→ ADR canônico: `ADR-002-tratativas-vs-retrabalho.md` · `ADR-003-macro-etapas-5-categorias.md`
→ Memória detalhada: `reference_tratativas_vs_retrabalho.md`

### Visitas

| Sigla | Termo | Quando |
|---|---|---|
| **VT Aferição** | Visita Técnica de aferição | Pré-obra · X − 60 dias da execução · diagnóstico |
| **VT Entrada** | Visita Técnica de entrada | Pré-obra · X − 10 dias da execução · confirmação |
| **VT Qualidade** | Visita Técnica de qualidade | Pós-execução · diagnóstico de problemas/reaplicação |

### Outros

| Termo | Definição |
|---|---|
| **Reaplicação** | Aplicação de novo material após reprovação da entrega original |
| **Marco** | Evento detectado em mensagem do Telegram · texto literal |
| **Snapshot de material** | Foto textual do material em obra · detectada em msg (estoque/entrada/sobra/consumo) |
| **Ocorrência formal** | Registro oficial no Painel · severidade categorizada |
| **Ciclo** | Bloco temporal da obra · Ciclo 1 = entrega original · Ciclo 2+ = retrabalho |
| **Tela total** | Tela aplicada em piso completo · sinal de obra com superfície porosa · custo de Leona/Teron sobe |

---

## 3 · Aliases de senders Telegram

Mesma pessoa pode aparecer com múltiplas grafias no Telegram. Sempre normalizar antes de contar.

| Token detectado | Pessoa canônica |
|---|---|
| `taquinho` | Gilmar Taquinho |

```python
SENDERS_ALIAS = {"taquinho": "Gilmar Taquinho"}
```

⚠ **Cuidado com pipes:** label `"William|Braiam Aplicador SP"` é label do William, NÃO do Braiam.

→ Memória detalhada: `reference_padrao_leitura_telegram.md`

---

## 4 · Pessoas com função (Telegram)

Em campo aparecem várias pessoas. Função pode evoluir com o tempo.

| Nome | Função atual | Função histórica |
|---|---|---|
| Braiam / Braian | **Fiscal de qualidade** (desde jan/2026) | Aplicador (até dez/2025) |
| Nathan | Fiscal de qualidade · VT | — |
| Gilmar / Gilmar Taquinho / Taquinho | Líder/aplicador de campo | — |
| Wesley | Operações Monofloor (`responsavelOperacoes`) | — |
| Luana | Operações Monofloor (`responsavelOperacoes`) | — |
| Pedro / Mayara | Atendimento PRÉ-obra | — |
| Caroline | Frase-padrão "Recebemos as imagens..." em VT qualidade | — |
| Rodrigo | Dev do `planejamento.monofloor.cloud` · NÃO pedir pra atualizar cadastros Telegram | — |

→ Memória detalhada: `feedback_telegram_nomes_terceiros.md`

⚠ **Nomes esquisitos no Telegram são realidade.** Cadastros feitos por terceiros · Rodrigo não vai mexer · não sugerir "pedir pra atualizar".

---

## 5 · Status de obra (Painel)

| Status (API) | Descrição | Conta como "viva"? |
|---|---|---|
| `planejamento` | Pré-execução · em escopo/cor/VT | ✓ |
| `aguardando_execucao` | Pronta · aguardando data | ✓ |
| `em_execucao` | Prestadores aplicando | ✓ |
| `reparo` | Pós-entrega · obra com retrabalho ativo | ✓ |
| `marcas_rolo_cera` | Pós-entrega · marcas detectadas | ✓ |
| `aguardando_clima` | Aguardando condição climática | ✓ |
| `pausado` | Pausada formalmente | ✓ |
| `contrato` | Contrato em assinatura | ✓ |
| `concluido` | Aprovada/finalizada | × |
| `finalizado` | Finalizada definitiva | × |
| `cancelado` | Cancelada · não vamos processar (Qualidade) | × |

**Critério Painel UI "ativa":** todas exceto `finalizado` e `concluido` (inclui cancelado · 257 obras)
**Critério Qualidade "viva":** todas exceto `finalizado`, `concluido`, `cancelado` (222 obras)

→ ADR canônico: `ADR-004-universo-qualidade-222-vivas.md`
→ Memória detalhada: `reference_api_painel_obras.md`

⚠ **Retrabalho ≠ atraso.** Status `reparo` e `marcas_rolo_cera` são pós-entrega · cronograma original já cumprido · NÃO contar como atraso em estatísticas de prazo.

---

## 6 · Vocabulário REAL × acadêmico (regex)

**Princípio:** time não escreve em "português acadêmico" · escreve do jeito da operação. Regex literal/dicionário ZERA detecções.

| Conceito | Acadêmico (NÃO USE) | Real (USE) |
|---|---|---|
| Reprovação | "cliente reprovou obra" | "balde acabou marcando o piso" · "ideal é reaplicar" · "cliente optou pela reaplicação" |
| Reparo | "reparo necessário" | "início de reparo dia 26/03" · "Reparos e ajustes finalizados" · "tem que refazer a parede" |
| Material em obra | "material entregue" | "Material em obra Conferido" · "OS produzida" |
| Início do dia | "equipe iniciou trabalho" | "Estamos chegando agora" · "Bom dia, equipe em obra" |
| Cobrança | "perguntar status" | "Tem equipe em obra?" · "alguém em obra?" |
| Visita técnica | "VT realizada" | "vt de qualidade agendada" · "Visita agendada com os responsáveis" |
| Camadas Stelion | "1ª aplicação" | "primeira camada de Stelion 3G" · "Lixamento teron Aplicação primeira camada stelion" |

→ Memória detalhada: `feedback_calibrar_regex_marcos.md`

### Frases-padrão recorrentes

**Caroline · relatório VT qualidade:**
> "KRYSTAL: Olá, pessoal. Bom dia! Recebemos as imagens e informações referentes à visita de qualidade realizada..."

Aparece a cada VT de qualidade · reconhecer como **marco "relatório VT qualidade"**, não como msg isolada.

---

## 7 · Cores STELION (catálogo)

Catálogo oficial Monofloor tem **21 cores STELION**. Hex codes:
- 9 chutadas no JSON (precisam ser confirmadas)
- 12 pendentes de extração do PDF do catálogo

→ Memória detalhada: `project_orion_cores_oficiais.md` (PENDENTE · sessão 2026-05-02)

Cores conhecidas que aparecem no Telegram:
- **Kalahari** · cor STELION
- **Argento** · cor STELION
- "Personalizada" · cor especial · enriquecer com o nome real do projeto se houver

---

## 8 · Filtros prévios obrigatórios (Telegram)

Antes de aplicar qualquer regex em msgs do Telegram, sempre filtrar:

### a) Cards de bot (ignorar)
- 10+ caracteres `-` consecutivos: `re.compile(r"-{10,}")`
- Padrão `APLICADOR:.*SUPERVISOR:.*CLIENTE:` juntos: `re.compile(r"APLICADOR\s*:.*SUPERVISOR\s*:.*CLIENTE\s*:", re.DOTALL | re.IGNORECASE)`
- Padrão de criação (sem SUPERVISOR · só APLICADOR + Cliente + Endereço/Fone)

### b) Transcrições de áudio/vídeo
- `🎬` (vídeo) · `🎙️` (áudio)
- Pular pra detecção de marcos textuais (linguagem ambígua)

### c) Negações específicas
- "não precisa" / "sem necessidade" → invalidam pedido
- "não pode" / "não vai dar" → idem

→ Memória detalhada: `reference_padrao_leitura_telegram.md` · seção 3

---

## 9 · Convenções de produto

- **"Painel de Obras"** em todo texto visível ao usuário · NUNCA "Pipefy" (descontinuado) · código pode manter nomes legados
- **Sem valores financeiros** em dashboards de Qualidade (diretoria não quer ver receita/custo por ora)
- **Hardcode = dívida moral** · nenhum número fixo no HTML · tudo amarrado em fonte canônica

→ Memória detalhada: `feedback_nomenclatura_painel_obras.md`

---

## 10 · Memórias-fonte detalhadas

| Tópico | Memória |
|---|---|
| Produtos OS × campo | `reference_nomenclatura_produtos.md` |
| API Painel | `reference_api_painel_obras.md` |
| Padrão leitura Telegram (regex, filtros, calibração) | `reference_padrao_leitura_telegram.md` |
| Tratativas × Retrabalho | `reference_tratativas_vs_retrabalho.md` |
| Vocabulário real × acadêmico | `feedback_calibrar_regex_marcos.md` |
| Nomes Telegram | `feedback_telegram_nomes_terceiros.md` |
| Painel ≠ Pipefy | `feedback_nomenclatura_painel_obras.md` |
| Retrabalho ≠ atraso | `feedback_retrabalho_separado.md` |
| Cores oficiais (pendente extrair) | `project_orion_cores_oficiais.md` |

## ADRs relacionados

- `ADR-001-kira-driven-vs-ia-externa.md`
- `ADR-002-tratativas-vs-retrabalho.md`
- `ADR-003-macro-etapas-5-categorias.md`
- `ADR-004-universo-qualidade-222-vivas.md`
