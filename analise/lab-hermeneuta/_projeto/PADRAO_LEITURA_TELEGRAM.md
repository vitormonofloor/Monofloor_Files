# 📡 Padrão de leitura do Telegram (via Painel) · guia portável

> Documento-guia pra qualquer agente/terminal que precisa ler mensagens do Telegram via Painel pra qualquer propósito (jornada, relatório de ativas, dashboard, alerta, etc).
>
> **Reaproveitar conhecimento** · **não mexer no Lab Orion vivo**.

---

## 1 · Convenção de coexistência

Vários terminais podem trabalhar em paralelo se cada um respeitar:

### O que pode ser COMPARTILHADO entre terminais

- **Endpoints do Painel** · `/api/projects/...` · não há rate limit conhecido · podem chamar à vontade
- **Princípios de filtragem** (este doc · seção 3)
- **Aliases de senders** (este doc · seção 4)
- **Vocabulário do time** (este doc · seção 5)
- **Protocolo de calibração de regex** (este doc · seção 6)

### O que cada terminal escreve/edita SOMENTE NO SEU PRÓPRIO

| Item | Pertence ao Lab Orion · NÃO MEXER | Pertence ao OUTRO terminal · seu próprio |
|---|---|---|
| Script | `agente/gerar_jornada.py` `agente/cruzar_kira.py` `agente/varredura.py` | `agente/<seu_script>.py` |
| Output JSON | `dados/jornadas.json` `dados/discordancias-v3.json` | `dados/<seu_arquivo>.json` |
| Markdown | `_jornadas/*.md` `_storytelling/*.md` `_projeto/*.md` | `_<seu_diretorio>/*.md` |
| HTML | `index.html` `jornada.html` | `<seu_arquivo>.html` |
| Memórias | `feedback_kira_*.md` `feedback_telegram_nomes_*.md` | criar suas próprias com prefixo claro |

### Lock anti-concorrência

- O `varredura.py` mantém `agente/.varredura.lock` pra evitar 2 varreduras simultâneas
- **Outro terminal NÃO PRECISA mexer com lock** se rodar script PRÓPRIO (não invoca varredura)
- Scripts standalone (não chamados pelo varredura) não conflitam · podem rodar em paralelo

### Em caso de dúvida

- Antes de criar arquivo · verificar se nome está livre (ls em `dados/`, `_projeto/`, etc)
- Dúvida vira pergunta pro Vitor · **não inferir** que pode mexer em algo do Lab Orion

---

## 2 · Fontes do Painel · endpoints

Base: `https://cliente.monofloor.cloud/api`

| Endpoint | Uso | Observações |
|---|---|---|
| `/projects?ativa=true` | Lista de obras ativas (227+ no momento) | Sem paginação · retorna tudo |
| `/projects/{id}` | Detail completo (40+ campos) | `responsavelOperacoes`, `tagKira`, `situacaoAtual`, `acessoDetalhes.labels`, etc |
| `/projects/{id}/messages?source=telegram&limit=2000` | **Core** · todas msgs do grupo | Áudio já transcrito · foto descrita pelo Kira |
| `/projects/{id}/messages?source=whatsapp&limit=2000` | Msgs WhatsApp do cliente | KIRA já interpretou e resumiu em `pendenciaManual.whatsappSummary` |
| `/projects/{id}/ocorrencias` | Fricção formal · severidade alta/critica | Status atual (aberta/resolvida) |
| `/projects/{id}/materiais` | Escopo formal · m², produtos, cores | `tipoSuperficie="Reaplicação"` sinal explícito |
| `/projects/{id}/equipe` | Líder + aplicadores oficiais por obra | Use pra identificar quem é aplicador na msg |
| `/projects/{id}/documentos` | Lista de docs (OS Indústria, escopos, contratos) | `urlLocal` é o caminho real · use `/api + urlLocal` pra baixar PDF |
| `/projects/{id}/fases` | Cronograma implícito | Pouco usado |
| `/projects/{id}/pausas` | Pausas formais | Geralmente vazio |

### Download de PDF da OS Indústria

```python
url = "https://cliente.monofloor.cloud/api" + doc.urlLocal
# urlOriginal é signed URL do Pipefy que expira · NÃO usar
```

Use `pdfplumber` pra extrair tabelas (instalar via `pip install pdfplumber`).

---

## 3 · Filtros prévios obrigatórios

Antes de aplicar QUALQUER regex em msgs do Telegram, sempre filtrar:

### a) Cards de bot (bots que postam status com formato fixo)

Detectar se a msg tem:
- 10+ caracteres `-` consecutivos: `re.compile(r"-{10,}")`
- OU padrão `APLICADOR:.*SUPERVISOR:.*CLIENTE:` juntos: `re.compile(r"APLICADOR\s*:.*SUPERVISOR\s*:.*CLIENTE\s*:", re.DOTALL | re.IGNORECASE)`

Se um dos dois bate · **PULAR** a msg pra detecção de marcos. Esses cards repetem campos (COR, INÍCIO, etc) e geram falso positivo brutal.

### b) Transcrições de áudio/vídeo (linguagem ambígua)

Detectar:
- `🎬` (vídeo)
- `🎙️` (áudio)

São transcrições brutas · contém comentários que não correspondem a marcos formais. **PULAR** a msg pra detecção de marcos textuais.

### c) Negações específicas

Pra detectores de solicitação/pedido (não de marcos genéricos):
- "não precisa" / "sem necessidade" → **invalidam** o pedido
- "não pode" / "não vai dar" → idem

---

## 4 · Aliases de senders (mesma pessoa · grafias diferentes)

No Telegram, o sender pode aparecer com múltiplas grafias. Unificar antes de contar:

```python
SENDERS_ALIAS = {
    "taquinho": "Gilmar Taquinho",  # Taquinho == aplicador | Gilmar Taquinho == Gilmar
}

def normalizar_sender(sender):
    s = (sender or "").lower()
    for token, canonico in SENDERS_ALIAS.items():
        if re.search(rf"\b{re.escape(token)}\b", s):
            return canonico
    return sender
```

### Pessoas conhecidas com função (atualizar quando mudar)

- **Braiam / Braian** · até dez/2025 era APLICADOR · a partir de 2026 é FISCAL DE QUALIDADE
- **Nathan** · fiscal de qualidade / VT
- **Gilmar / Gilmar Taquinho / Taquinho** · MESMA pessoa · líder/aplicador de campo
- **Wesley** · `responsavelOperacoes` em obras Monofloor (operações)
- **Luana** · `responsavelOperacoes` em obras Monofloor (operações)
- **Pedro / Mayara** · atendimento PRÉ-obra (não confundir com dono operacional)

⚠ **Cuidado**: labels com pipe `|` podem confundir — `"William|Braiam Aplicador SP"` é label do William, não do Braiam.

---

## 5 · Vocabulário do time Monofloor (regex literal NÃO casa)

**Princípio:** time não escreve em "português acadêmico" · escreve do jeito da operação. Regex literal/dicionário ZERA detecções.

### Tradução literal → real (validado em KRYSTAL/GURGEL)

| Conceito | Acadêmico (NÃO USE) | Real (USE) |
|---|---|---|
| Reprovação | "cliente reprovou obra" | "balde acabou marcando o piso" · "ideal é reaplicar" · "cliente optou pela reaplicação" |
| Reparo | "reparo necessário" | "início de reparo dia 26/03" · "Reparos e ajustes finalizados" · "tem que refazer a parede" |
| Material em obra | "material entregue" | "Material em obra Conferido" · "OS produzida" · "Bom dia equipe em obra" |
| Início do dia | "equipe iniciou trabalho" | "Estamos chegando agora" · "Bom dia, equipe em obra" |
| Cobrança | "perguntar status" | "Tem equipe em obra?" · "alguém em obra?" |
| Visita técnica | "VT realizada" | "vt de qualidade agendada" · "Visita agendada com os responsáveis" · "Recebemos imagens da visita de qualidade" |
| Camadas Stelion | "1ª aplicação" | "primeira camada de Stelion 3G, com consumo de 7 kits" · "Hoje Lixamento teron Aplicação primeira camada stelion" |

### Frases-padrão da Caroline (mensagens recorrentes)

```
"KRYSTAL: Olá, pessoal. Bom dia! Tudo bem?
Recebemos as imagens e informações referentes à visita de qualidade realizada..."
```

Esse padrão aparece a cada VT de qualidade. Reconhecer como **marco "relatório VT qualidade"**, não como mensagem isolada.

---

## 6 · Protocolo de calibração de regex (obrigatório antes de propor marco novo)

7 passos · cumprir TODOS antes de integrar regex no código:

### Passo 1 · NÃO comece pela regex

Acadêmico zera. Comece pelos dados.

### Passo 2 · Mapeie a linguagem REAL

`grep` nas msgs do Telegram das obras-piloto (KRYSTAL `a79f00f0-...` · GURGEL `3e5c6392-...`) com **termos AMPLOS** (palavra raiz):

```python
TERMOS_AMPLOS = ['reaplica', 'reparo', 'marca', 'retorno', 'refazer', 'visita', 'amostra']
# Pra cada termo · listar primeira/última msg · contagem · quem disse
```

### Passo 3 · Construa regex a partir do que VIU

Use exatamente os termos detectados como base:

```
ENCONTRADO: "balde acabou marcando o piso"
REGEX:       \bmarc(a|ou)\w*\s+(o\s+)?piso

ENCONTRADO: "Reparos e ajustes finalizados"
REGEX:       \breparos?\s+e\s+ajustes\s+(finalizad|conclu)
```

NÃO ampliar pra termos NÃO vistos · regex inventada gera falso positivo silencioso.

### Passo 4 · Filtros prévios

Sempre aplicar (seção 3 acima):
- Cards de bot
- Transcrições
- Negações se aplicável

### Passo 5 · Tipo · único vs repetível

- **Único:** primeira ocorrência cronológica vence
- **Repetível:** dedup por (data + tipo) · um por dia

### Passo 6 · Sanity check qualitativo

- KRYSTAL é REAPLICAÇÃO (label Painel) · deve disparar `reprovacao_retorno`
- GURGEL é obra normal · não deve disparar (ou bem pouco)
- Use isso como prova de fogo

### Passo 7 · Documentar

Atualize seu MD-guia com a regex final calibrada · não a acadêmica.

---

## 7 · Como rodar em paralelo ao Lab Orion sem conflito

### Setup mínimo do seu script

```python
# agente/<seu_script>.py
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
SUA_SAIDA = ROOT / "dados" / "<seu_arquivo>.json"
BASE_API = "https://cliente.monofloor.cloud/api/projects"

# Reuse os filtros e aliases deste doc
# ... seu código aqui ...

SUA_SAIDA.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
```

### Não precisa do lock

Seu script é independente · não toca em `discordancias-v3.json`, `jornadas.json`, ou qualquer arquivo compartilhado. Pode rodar 24/7 sem afetar o Lab.

### Quando precisar atualizar este doc

Se você descobrir nova grafia de sender, novo padrão de linguagem do time, ou regex calibrada que vale pra todos · **proponha edição neste MD** (`_projeto/PADRAO_LEITURA_TELEGRAM.md`) · Vitor revisa e mescla.

---

## 8 · Checklist final antes de rodar seu script pela 1ª vez

- [ ] Você LEU este MD inteiro
- [ ] Seu script é PRÓPRIO (não toca em `gerar_jornada.py`, `cruzar_kira.py`, `varredura.py`)
- [ ] Seu output vai pra arquivo PRÓPRIO em `dados/` (não sobrescreve `discordancias-v3.json`, `jornadas.json`)
- [ ] Seu HTML (se tiver) é arquivo PRÓPRIO (não edita `index.html`, `jornada.html`)
- [ ] Você aplicou os filtros prévios (cards de bot, transcrições)
- [ ] Você normalizou senders com `SENDERS_ALIAS`
- [ ] Você seguiu os 7 passos de calibração de regex (se for criar regex nova)
- [ ] Você fez sanity check qualitativo (KRYSTAL vs GURGEL)
- [ ] Memórias compartilhadas relevantes lidas: `feedback_kira_ja_interpretou`, `feedback_telegram_nomes_terceiros`, `feedback_calibrar_regex_marcos`

Se faltou algum item · pare e resolva antes de rodar.
