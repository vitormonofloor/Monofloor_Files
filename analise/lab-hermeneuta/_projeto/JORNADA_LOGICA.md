# 🧠 Jornada do Projeto · Lógica de detecção

> Documenta como `agente/gerar_jornada.py` lê as mensagens do Telegram (via Painel) e identifica fases, marcos, solicitações, cobranças e materiais. Atualizado em 2026-05-06.

## Visão geral

**Fonte única:** `cliente.monofloor.cloud/api/projects/{id}/...` (Painel) · 6 endpoints + 1 storage de PDF.

**Escopo TELEGRAM-ONLY:** zero WhatsApp · zero análise de áudio em tempo real (mas usamos as transcrições já feitas pelo Kira nas msgs).

**Saída:** `dados/jornadas.json` com a jornada estruturada de cada obra-piloto + `_jornadas/{obra_id}.md` (narrativa em prosa template-based).

**Hardcoded hoje:** 2 obras (KRYSTAL, GURGEL). Detector automático de "obras finalizadas" é Fase D futura.

---

## 1 · Endpoints consumidos

| Endpoint | Uso |
|---|---|
| `/api/projects/{id}` (detail) | Identidade · datas previstas/confirmadas · responsavelOperacoes/Atendimento · consultorNome · vendedor |
| `/api/projects/{id}/messages?source=telegram&limit=2000` | **Core** · todas as mensagens cronológicas (até 2000 ou histórico completo) |
| `/api/projects/{id}/ocorrencias` | Fricção formal · severidade alta/média/baixa/critica |
| `/api/projects/{id}/materiais` | Escopo formal · m² · produtos · cores · `tipoSuperficie=Reaplicação` |
| `/api/projects/{id}/equipe` | Líder + aplicadores oficiais (identifica aplicador no Telegram) |
| `/api/projects/{id}/documentos` | Lista de OS Indústria, escopos, contratos · `urlLocal` para baixar |
| `/api/storage/documentos/{id}/{nome}.pdf` | Download direto do PDF (signed URL `urlOriginal` expira) |

---

## 2 · Cluster de execução (detecta os "dias da obra")

A obra tem várias mensagens dispersas no tempo. **Cluster de execução** = janela densa ao redor da data de execução confirmada.

```
janela = [dataExecucaoConfirmada - 7 dias, dataExecucaoConfirmada + 7 dias]
cluster = dias dentro da janela com ≥5 mensagens
cluster_inicio = primeiro dia do cluster
cluster_fim    = último dia do cluster
```

Configurável via constantes:
- `EXEC_JANELA_DIAS = 7`
- `EXEC_CLUSTER_MSGS_DIA = 5`

**Por que isso funciona:** durante execução o grupo conversa muito (10-50+ msgs/dia). Antes/depois fica esparso.

---

## 3 · Fases automaticamente detectadas

A jornada vira uma sequência de fases, decididas por **gaps de mensagens** e o cluster de execução:

```
1. Planejamento inicial   = 1ª msg até primeiro gap ≥30d
2. Hibernação #N          = qualquer gap ≥30d sem msg
3. Atividade retomada     = msg após hibernação · até próxima hibernação ou execução
4. Despertar e pré-execução = atividade retomada que precede o cluster
5. Execução               = cluster_inicio → cluster_fim
6. Pós-execução           = msgs depois de cluster_fim até última msg
```

Configurável: `HIBERNACAO_GAP_DIAS = 30`.

---

## 4 · Marcos textuais (timeline geral · NÃO os de execução)

Aplica regex em todas as msgs · **filtra cards de bot** (msgs com `-{10,}` ou padrão `APLICADOR:.*SUPERVISOR:.*CLIENTE:`).

| Marco | Regex (fragmento) | Tipo |
|---|---|---|
| `contrato_assinado` | `\b(contrato\s+assinado|contrato\s+ok)\b` | único · 1ª ocorrência |
| `vt_agendada` | `\bvt\s+(de\s+)?(aferição|entrada)\s+agendada\b` | único |
| `vt_entrada_realizada` | `vt\s+(de\s+)?entrada\s+realizada\|visita\s+de\s+entrada\s+realizada` | único · marco-divisor pré-execução → execução |
| `vt_realizada` | `vt\s+aferição\s+realizada\|visita\s+(de\s+qualidade|de\s+aferição)\s+realizada` | único · 1ª VT (Nathan tipicamente) |
| `amostra_solicitada` | `solicit.*amostra\|amostra\s+(solicit\|pendente\|enviada\|recebida\|chegou)\|envia.*amostra\|preciso\s+de\s+amostra\|nova\s+amostra` | repetível · detecta gargalo de cor |
| `cor_aprovada` | `amostra\s+(aprovada\|escolhida\|confirmada)\|cor\s+(escolhida\|aprovada\|definida\|confirmada)\|escolheu cor\|cliente aprovou cor` | único · padrão FORTE (não casa "COR: X" do card) |
| `inicio_anunciado` | `início\s+(da\s+obra\|previsto\|confirmado)\s*[:]\s*\d+/\d+` | repetível · dedup por dia |
| `material_produzido` | `material\s+produzido\|os\s+produzida\|indústria\s+(finaliz\|conclu)\|material\s+(saiu\|em obra\|enviado)` | único |
| `aprovacao_cliente` | `obra\s+aprovada\|cliente\s+aprov\|vídeo\s+de\s+aprovação` | repetível |
| `reprovacao_retorno` | `cliente reprovou\|marcou\s+o\s+piso\|seguir\s+com\s+reaplicação\|reaplicar\|início\s+de\s+reparo\|reparos.*finalizados\|refazer\s+(parede\|piso)` | repetível · captura ciclo pós-entrega · `marcas_rolo_cera` no Painel |
| `finalizacao` | `obra\s+(finaliz\|conclu)\|verniz\s+finaliz\|piso\s+(finaliz\|aprovad\|conclu)` | repetível |

**Filtros prévios pra TODOS os marcos textuais:**
- Pula cards de bot (`-{10,}` ou padrão `APLICADOR:.*SUPERVISOR:.*CLIENTE:`)
- Pula transcrições (`🎬` ou `🎙️`) · ambíguas demais

**Únicos:** mantém só a primeira ocorrência cronológica.
**Repetíveis:** dedup por (data + tipo).

---

## 5 · Marcos técnicos de execução (Gantt diário)

Detecta **dentro do cluster de execução** (com janela ±2d nos limites pra capturar preparação/finalização).

**Filtros prévios:**
- Pula cards de bot
- Pula msgs vazias

**Padrões (ordem importa · primeiro match vence):**

| Tipo | Regex | Cor (Gantt) |
|---|---|---|
| `verniz_finalizado` | `verniz\s+finaliz\|verniz\s+aplicad\|finalização\s+do\s+verniz` | bronze |
| `obra_finalizada` | `obra\s+finaliz\|piso\s+finaliz\|piso\s+conclu` | verde escuro |
| `verniz_iniciado` | `programação\s+aplicação\s+verniz\|aplicação\s+(de\s+)?verniz\|verniz\s+lumina` | bronze claro |
| `cura` | `aguardando\s+cura\|em\s+cura\|cura\s+do\s+(piso\|stelion)` | azul claro |
| `camada_3` | `terceira\s+camada\|3ª?\s*camada\|3ª\s+demão` | verde |
| `camada_2` | `segunda\s+camada\|2ª?\s*camada\|2ª\s+demão` | verde |
| `camada_1` | `primeira\s+camada\|1ª?\s*camada\|1ª\s+demão` | verde |
| `lixamento` | `lixamento\|lixad[ao]\|lixando\|lixar` | bege |
| `aplicacao_tela` | `aplicação\s+(de\s+)?tela\|tela\s+aplicad\|telar` | dourado |
| `aplicacao_teron` | `aplicação\s+(de\s+)?teron\|teron\s+aplicad` | dourado |
| `aplicacao_primer` | `aplicação\s+(de\s+)?primer\|primer\s+aplicad` | dourado |
| `preparacao` | `limpeza\|proteção\s+(das\s+áreas\|do\s+ambiente)\|requadro\|substituição\s+de\s+fitas\|troca\s+(de\s+)?fitas` | azul |
| `diario_obra` | `diário\s+de\s+obra` | cinza |
| `inicio_dia` | `equipe\s+em\s+obra\|chegando\s+agora\|chegamos\|estamos\s+chegando` | verde (proativo) |
| `fim_dia` | `saindo\s+(de\|da)\s+obra\|equipe\s+saindo\|acabamos\s+(agora\|hoje)` | cinza |
| `visita_durante_obra` | `cliente\s+(em\s+obra\|visitou\|esteve)\|visita\s+do\s+cliente\|vt\s+de\s+qualidade\|visita\s+de\s+qualidade\|visita\s+agendada\s+com\s+responsáveis\|inspeção\s+(em\s+obra\|de\s+qualidade)` | roxo (#8b5cf6 · evento externo de auditoria) |

**Dedup:** 1 marco por (data + tipo). Apenas a 1ª ocorrência do dia conta.

**Configuração:** ver `MARCOS_EXECUCAO` em `gerar_jornada.py`.

---

## 6 · Cobrança × Resposta (KPI de comportamento)

Distingue **inicio_dia proativo** vs **cobrança seguida de resposta**:

### Quem é aplicador?

`get_aplicadores_set(equipe_endpoint)` extrai primeiros nomes (lowercase) de `/equipe.prestadores` cuja função contém `LIDER | APLICADOR | PREPARADOR`.

`is_aplicador(sender, set)` faz matching de tokens · separa por espaço/pipe e checa se algum token está no set. Cobre formatos como `"michael"`, `"Wesley | Operações"`, `"aplicador | Gilmar Taquinho"`.

### Lógica

```
para cada msg da janela de execução (ordenada cronologicamente):
  se msg é de APLICADOR e contém regex de inicio_dia:
    → marco "Início do dia"  (proativo · verde)
    marca o dia como "já tem início"

  se msg é de NÃO-APLICADOR e contém regex PAD_COBRANCA
     E o dia AINDA NÃO tem inicio_dia registrado:
    → marco "Cobrança de status"  (vermelho)
    deixa pendente · aguardando próxima msg de aplicador

  se msg é de APLICADOR e há cobranças pendentes do mesmo dia:
    → calcula delta_min = msg.timestamp - cobrança.timestamp
    → preenche cobrança.tempo_resposta_min e cobrança.respondido_por
    → fecha as cobranças pendentes do dia
```

### Regex `PAD_COBRANCA`

```regex
\b(temos\s+equipe\s+em\s+obra
  |tem\s+equipe\s+em\s+obra
  |já\s+chegou
  |chegou\?
  |chegaram\??
  |alguém\s+em\s+obra
  |equipe\s+chegou
  |status\s+da\s+obra
  |status\??$)\b
```

**Nota:** "Bom dia!" sozinho NÃO conta como cobrança · ambíguo demais.

---

## 7 · Solicitações de material (Pedido × Resolução)

Detecta solicitações nas msgs do cluster (±2d) e tenta parear com a resposta.

### Filtros de exclusão

```
- Cards de bot (separator longo ou padrão)
- Msgs vazias
- Transcrições · contém 🎬 ou 🎙️
- Negações ("não precisa", "sem necessidade") → não conta como solicitação
- Sobras ("sobra de material", "sobrou X material") → vai pra outra seção
- Ações de fluxo ("precisa acessar", "precisa buscar", "precisa retirar") → não é material
```

### Regex de detecção

```regex
PAD_MAT_SOLIC = \b(precis[ao]|preciso|preciso\s+de|manda\s+(a|o|mais)
                  |envia(r)?\s+(mais|outro|outra)|fal(ta|tou)
                  |comprar|preciso\s+comprar|sair\s+para\s+comprar)\b

PAD_TELA_TOTAL = \btela\s+(total|por\s+completo|no\s+piso\s+total|inteir[ao])\b
```

### Dedup por tópico

`palavras_chave(texto)` → set de keywords (`tela`, `massa`, `primer`, `lumina`, `teron`, `stelion`, `verniz`, `cera`, `balde`, `kit`).

**Regra:** se já existe solicitação no mesmo dia com pelo menos 1 keyword em comum em ≤60min → considera duplicata · pula.

Independe de autor (Wesley pedindo tela + Michael respondendo "tela no piso total" 2min depois viram 1 só).

### Resolução pareada

Pra cada solicitação · busca nas próximas 50 msgs (até 60min depois) a primeira mensagem de OUTRO autor que contenha palavra de fechamento:

```regex
PAD_RESOLUCAO = \b(ok|blz|beleza|combinado|perfeito|positivo|certo
                   |não\s+precisa|sem\s+necessidade
                   |libera(do)?|aprovado|autorizado
                   |manda|envia|pode\s+(mandar|enviar)
                   |fica\s+aguardando|aguarda
                   |fechado|fechou|fica\s+combinado
                   |não\s+pode|não\s+vai\s+dar)\b
```

Quando encontra · grava `delta_min`, `autor`, `trecho` da resposta.
Se não encontra em 60min · `resolucao = null`.

---

## 8 · Material enviado (OS Indústria PDF)

Para obras com OS Indústria PDF: baixa, abre com `pdfplumber` e extrai a tabela "Descrição dos materiais enviados".

### Download

```
url = "https://cliente.monofloor.cloud/api" + doc.urlLocal
```

(o `urlOriginal` é signed URL do Pipefy que expira em ~5h · usar urlLocal direto via `/api/storage/...` é estável)

### Filtro de PDFs

```
nome contém "O.S." OU "OS\s*\d+" OU "indústria/industria/ind_stria"
mimeType = "application/pdf"
dedup por nome base (ignora prefixos field_ / card_principal_)
```

### Parsing da tabela

```
pra cada página · extract_tables()
  procura linha com "descrição" + ("material" OU "enviados")
  cabeçalho = idx_header + 1
  dados começam em idx_header + 2
  para cada linha:
    para cada célula não-vazia:
      - se ^\d{3,6}$ e codigo vazio    → codigo
      - se ^\d+[,\.]\d+$ e qtd vazia    → quantidade (decimal)
      - se ^\d{1,3}$ e qtd vazia        → quantidade (inteiro fallback)
      - se [A-Z]{3,} e material vazio    → material (STELION, LUMINA, etc)
      - se já tem material e cor vazia  → cor (Personalizada, Gengibre, etc)
      - se R$ ou tem vírgula            → valor

  para se aparece "Total", "Observação" ou "Assinatura"
```

### Cor "Personalizada" enriquecida

UI mostra `Personalizada · Gengibre` quando o produto tem cor "Personalizada" e a obra tem cor real em `j.cores`. A cor real vem de `/materiais.items[].cor`.

---

## 9 · Padrões observados (heurística simples)

Derivados dos dados calculados, não de regex em msgs:

```
hibernacao_longa             · tempo_hibernacao_dias ≥ 60
execucao_concentrada         · tempo_execucao / tempo_total < 5%
mudanca_escopo_dia_execucao  · alguma solicitação tem tela_total = true
```

Lista vai crescer com a maturidade.

---

## 10 · O que NÃO está implementado

- Detecção automática de obra finalizada (Fase D)
- Análise de WhatsApp (escopo descartado)
- Parsing de assinaturas/aceite no PDF
- Detecção de pausa/retorno explícito (ex: "obra pausada porque...")
- Tom semântico das mensagens (sem IA externa · só keyword)
- Comparação inter-obras (futuro · com mais obras processadas)
- IA externa pra interpretação livre · uso é limitado pra recortes pontuais

---

## 11 · Configuração rápida (constantes)

| Constante | Valor | O que faz |
|---|---:|---|
| `HIBERNACAO_GAP_DIAS` | 30 | Gap mínimo pra contar como hibernação |
| `EXEC_CLUSTER_MSGS_DIA` | 5 | Limiar de densidade pra detectar execução |
| `EXEC_JANELA_DIAS` | 7 | Janela ao redor de `dataExecucaoConfirmada` |
| `JANELA_RESOLUCAO_MIN` | 60 | Tempo máximo pra parear pedido↔resposta |
| `JANELA_DEDUP_TOPICO_MIN` | 60 | Tempo dentro do qual mesma palavra-chave vira 1 solicitação |
| `OBRAS_PILOTO` | lista hardcoded | IDs das obras a processar |

---

## 12 · Por que tudo isso é determinístico (sem IA externa)?

- **Auditável:** abre o JSON · vê QUAL regex disparou ou qual regra de fase aplicou · sem caixa-preta
- **Custo zero:** zero tokens, zero rate limit, zero risco de outage
- **Reproduzível:** mesma entrada = mesma saída · sem variação por dia/temperatura
- **Simples de refinar:** adicionar regex é trivial · ajustar threshold é 1 linha

A IA do Kira já fez o trabalho pesado nas mensagens (transcrição de áudio, descrição de foto). Aqui só extraímos e cruzamos.

**Princípio:** *"não reinvente o que a fonte já interpretou"* · ver `APRENDIZADOS.md` · aprendizado #0.
