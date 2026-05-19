"""
gerar_jornada.py · Análise retrospectiva da Jornada do Projeto
================================================================

Pra cada obra-piloto, fetcha tudo do Painel API (Kira) e gera análise
determinística de toda a jornada · do contrato à entrega · TELEGRAM-ONLY.

ESCOPO FASE A:
  - 2 obras hardcoded (KRYSTAL + GURGEL)
  - Saída: dados/jornadas.json + _jornadas/{obra_id}.md (narrativa)
  - Sem WhatsApp · sem detector automático

FONTES:
  - /api/projects/{id} (detail · metadados)
  - /api/projects/{id}/messages?source=telegram (CORE)
  - /api/projects/{id}/ocorrencias
  - /api/projects/{id}/materiais
  - /api/projects/{id}/equipe

OUTPUT:
  - dados/jornadas.json (estruturado · 1 entrada por obra)
  - _jornadas/{obra_id}.md (narrativa em prosa · 5 atos)

Uso: python agente/gerar_jornada.py
"""

import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import setup_utf8

try:
    import pdfplumber
    PDF_OK = True
except ImportError:
    PDF_OK = False

setup_utf8()

ROOT = Path(__file__).parent.parent
JORNADAS_PATH = ROOT / "dados" / "jornadas.json"
JORNADAS_DIR = ROOT / "_jornadas"
BASE_API = "https://cliente.monofloor.cloud/api/projects"

# Obras-piloto (hardcoded · Fase A)
OBRAS_PILOTO = [
    # Pilotos originais (sessões 2026-05-05/06)
    "a79f00f0-19b1-43d4-b9d7-6ab8d219c205",  # KRYSTAL LURI NUMA
    "3e5c6392-af93-427a-9e29-3a927e6d5dc6",  # GURGEL DALFONSO

    # Calibração F3 (sessão 2026-05-08) · finalizadas/concluídas com sinal Telegram rico
    # Mix: 5 com retrabalho · 3 entrega direta · 1 problemática (GUSTAVO)
    "0e4e10b2-9fbe-49a4-9e42-08ae5624b39c",  # GETULIO TURATTI OST · 2 ciclos · clássico retrabalho
    "63623d90-e0c0-48e7-bc9d-eb45cc923af5",  # LUIS FERNANDO DE LIMA CARVALHO · 3 ciclos · jornada longuíssima
    "e6b38375-4075-4f79-9319-f15566722963",  # TALLY FELDMAN SINGAL GROSS · 91m · sinal mais rico
    "0f3e836e-8e36-4436-bac8-51ef678b17c9",  # P2B ENGENHARIA · entrega direta corporativa
    "687fbc05-b847-4c52-8af1-d7833b3a4590",  # GUSTAVO DE SOUZA PEREIRA · 2000 msgs · marcas/pausada
    "b055e234-ebef-41d3-b464-54c2102c0895",  # JAQUES AJZENTAL · poucas msgs · processo paralelo
    "b8fbadd8-778c-4a3b-9e18-81bba29a6a8e",  # ANDRE KEUNECKE SALERNO · 2 ciclos · sinal médio
    "9a190357-99d5-4a25-bba2-436ab65542ed",  # RODRIGO DE ALMEIDA SCHMIDT · entrega direta longa

    # Expansão sessão 2026-05-12 · obras finalizadas/concluídas a partir de dez/2025 (corte temporal)
    # Mix variado: 4 ciclos (raro), 3 ciclos, 2 ciclos, consultores diversos
    "50068c67-3854-49dd-9302-1a8636cf4a6a",  # MANUELA VILLAS BOAS SOUZA MARTIN · 53m · 4 ciclos · Wesley
    "e1fe5106-083e-4958-8af0-2a491c826b5b",  # MARCOS ANTONIO TADEU EXPOSTO JUNIOR · 34m · 4 ciclos
    "c1621370-4f28-4e9b-9f02-10032f9bf7a0",  # MANOELA LATINI GAVASSI FRANCISCO 2ª FASE · 63m · Wesley
    "c3d79452-b378-4d23-895c-3ba5e8a060ea",  # MARIANA PORTO FACCHINI · 43m · 3 ciclos · Juliana Santos
    "994a0d5b-e532-44fb-ab3b-19b686d147a6",  # ÁUREO EUSTÁQUIO BRANDÃO · 42m · 3 ciclos · Pedro Alexandre Santana
    "edc779fb-2dca-4d1a-864a-6234236cf145",  # NATHALIA DE FIGUEIREDO NUNES RABELO · 85m · super-rica · Wesley
    "13d9ca18-e5fc-42bc-907c-174a2e02ae9f",  # YAHYA EL HASSAN · 57m · 2 ciclos · Wesley
    "56cd74a9-44ee-40f2-b389-8773ac6df222",  # CHRISTIAN KORVER · 40m · 258 msgs (poucas · testa detector) · Luana
    "0d0c35bd-3b00-4de2-b898-4dfc61e6fdae",  # LEONARDO KAWANO · 39m · 2 ciclos · Wesley
    "1b292a9b-8c57-47bd-92e1-824fcd0b7fff",  # BM VAREJO – M. FASHION 1 FASE · 39m · obra corporativa · Wesley
]

HOJE = datetime.now(timezone.utc)
HOJE_DATE = HOJE.date()

FAIXAS_METRAGEM = [
    ("PP", "Ate 60",        0,    60),
    ("P",  "60-100",       60,   100),
    ("M",  "100-150",     100,   150),
    ("G",  "150-220",     150,   220),
    ("GG", "220-300",     220,   300),
    ("XG", "Acima 300",   300, 99999),
]

def classificar_faixa_metragem(m2):
    if not isinstance(m2, (int, float)) or m2 <= 0:
        return None
    for cod, nome, lo, hi in FAIXAS_METRAGEM:
        if lo <= m2 < hi:
            return cod
    return None

# Aliases de senders no Telegram · normaliza pessoas que aparecem com múltiplas grafias
# Formato: token-detector (lowercase) → nome canônico
# Atualizar quando descobrir nova pessoa com múltiplas grafias.
SENDERS_ALIAS = {
    "taquinho": "Gilmar Taquinho",  # KRYSTAL: Taquinho = aplicador | Gilmar Taquinho
    "b®":       "Braiam Novo",      # RODRIGO/GETULIO: B® com símbolo = Braiam · fiscal qualidade desde 2026
}


def normalizar_sender(sender: str) -> str:
    """Aplica aliases pra unificar pessoa que aparece com nomes diferentes.
    Ex: 'Taquinho' E 'aplicador | Gilmar Taquinho' viram ambos 'Gilmar Taquinho'.
    Tokens com caractere especial (ex: 'b®') usam match de substring · sem word boundary."""
    if not sender:
        return sender
    s_low = sender.lower()
    for token, canonico in SENDERS_ALIAS.items():
        token_low = token.lower()
        # Tokens com caracteres não-word (ex: ®) usam substring direto
        if re.search(r'\W', token_low):
            if token_low in s_low:
                return canonico
        else:
            if re.search(rf"\b{re.escape(token_low)}\b", s_low):
                return canonico
    return sender

# Janelas e thresholds
HIBERNACAO_GAP_DIAS = 30  # gap mínimo entre msgs pra contar hibernação
EXEC_CLUSTER_MSGS_DIA = 5  # ≥N msgs/dia = cluster denso (execução)
EXEC_JANELA_DIAS = 7  # janela ao redor de dataExecucaoConfirmada pra cluster

# ============================================================
# Utilitários de fetch e parsing
# ============================================================

FETCH_TIMEOUT = int(os.environ.get("ORION_FETCH_TIMEOUT", "15"))

def fetch(url: str, max_retries: int = 2):
    last_err = None
    for tentativa in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "lab-orion/1.0"})
            with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
                return json.load(r)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            last_err = e
            if tentativa < max_retries:
                time.sleep(2 ** tentativa)
    raise RuntimeError(f"fetch falhou: {last_err}")


def fetch_safe(url: str):
    try:
        return fetch(url, max_retries=1)
    except Exception:
        return None


def _to_float(v):
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def parse_iso(s):
    if not s:
        return None
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00").replace(" ", "T"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except (ValueError, TypeError):
        return None


def parse_data_simples(s):
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def diff_dias(d1, d2):
    """Diff em dias entre 2 datas/datetimes · None se faltar."""
    if not d1 or not d2:
        return None
    if isinstance(d1, datetime):
        d1 = d1.date()
    if isinstance(d2, datetime):
        d2 = d2.date()
    return (d1 - d2).days


# ============================================================
# Detecção de marcos via mensagens Telegram
# ============================================================

PAD_CONTRATO = re.compile(r"\b(contrato\s+assinado|contrato\s+ok)\b", re.IGNORECASE)
PAD_VT_AGENDADA = re.compile(r"\bvt\s+(de\s+)?(aferi[çc][aã]o|entrada)\s+agendada\b", re.IGNORECASE)
# vt_entrada_realizada · MAIS específica · prioridade na detecção
PAD_VT_ENTRADA_REALIZADA = re.compile(
    r"\b("
    r"vt\s+(de\s+)?entrada\s+(realizada|feita|ok|conclu[ií]da)"
    r"|visita\s+de\s+entrada\s+realizada"
    r")\b",
    re.IGNORECASE,
)
# vt_realizada genérica/aferição (qualidade/aferição/sem especificar)
PAD_VT_REALIZADA = re.compile(
    r"\b("
    r"vt\s+(de\s+)?aferi[çc][aã]o\s+(realizada|feita|ok|conclu[ií]da)"
    r"|vt\s+ok"
    r"|visita\s+(de\s+(qualidade|aferi[çc][aã]o)\s+)?realizada"
    r"|visita\s+t[eé]cnica\s+realizada"
    r")\b",
    re.IGNORECASE,
)
# Reprovação / retorno · linguagem REAL do time Monofloor (calibrada com KRYSTAL/GURGEL)
PAD_REPROVACAO_RETORNO = re.compile(
    r"\b("
    r"cliente\s+(reprov\w+|n[ãa]o\s+aprov\w+|recus\w+)"
    r"|reprov\w+\s+(da\s+)?obra|obra\s+reprov\w+"
    r"|necessidade\s+de\s+(retorno|reparo|reaplica[çc][aã]o)"
    r"|marcas?\s+(de\s+)?(rolo|cera)"
    r"|marc(a|ou)\w*\s+(o\s+)?piso"
    r"|piso\s+(marcad[ao]|com\s+marca)"
    r"|seguir\s+com\s+(a\s+)?reaplica[çc][aã]o"
    r"|reaplica[çc][aã]o\s+(necess[áa]ria|pendente|solicitada|das?\s+|dos?\s+)"
    r"|vamos\s+reaplicar|precisa\s+reaplicar|ter[áa]\s+(que\s+)?reaplicar|in[íi]cio\s+(da\s+)?reaplica[çc][aã]o"
    r"|reparo\s+(necess[áa]rio|solicitado|pendente)"
    r"|in[íi]cio\s+de\s+reparo"
    r"|reparos?\s+e\s+ajustes\s+(finalizad|conclu)"
    r"|retorno\s+(em\s+obra|necess[áa]rio|para\s+reparo)"
    r"|refazer\s+(a|o|essa|esse)\s+(parede|piso|paredão|área)"
    r")\b",
    re.IGNORECASE,
)
# Vocabulário pra extrair keyword (palavra-chave) de cada marco · entidades operacionais
KEYWORD_TOKENS = {
    "acao": [
        "reaplicar", "reaplicação", "reaplicacao",
        "refazer", "remover", "reparar", "reparo", "reparos",
        "ajustar", "ajustes", "marcar", "marcou", "marca",
        "trincar", "trinca", "fissura", "fissurar",
        "descolamento", "rachadura",
        "agendar", "agendada", "agenda",
        "enviar", "fazer",
    ],
    "area": [
        "piso", "parede", "paredes",
        "box", "sala", "cozinha", "lavanderia", "banheiro", "banheiros",
        "área", "areas", "faixa", "rodapé", "ralo",
    ],
    "material": [
        "stelion", "lilit", "lumina", "primer",
        "cera", "verniz", "hiper", "teron", "tela",
    ],
    "cor": [
        "argento", "kalahari", "gengibre", "areia",
        "personalizada",
    ],
    "qualificador": [
        "completo", "completa", "total",
        "parcial", "pontual", "novamente",
        "antiderrapante",
    ],
}


def extrair_keyword(texto, subtipo=None):
    """Extrai palavra-chave curta sintetizando o que a msg trata.
    Combina entidades detectadas em uma frase legível.
    """
    if not texto:
        return None
    txt = texto.lower()

    # Casos específicos com padrão fixo · prioridade alta
    # "fazer N resumos" / "X resumos"
    m = re.search(r"fazer\s+(\d+)\s+resumos?", txt)
    if m:
        return f"fazer {m.group(1)} resumos"

    # "início de reparo dia DD/MM" · "reaplicação dia DD/MM"
    m = re.search(r"\b(reparo|reaplica\w+)\s+(\w+\s+){0,3}?(dia\s+)?(\d{1,2}/\d{1,2})", txt)
    if m:
        return f"{m.group(1)} dia {m.group(4)}"

    # "balde marcou/marcando" + área
    m = re.search(r"balde\s+(?:acabou\s+)?(?:marc\w+)\s+(?:o\s+)?(\w+)", txt)
    if m:
        return f"balde marcou {m.group(1)}"

    # Detecta entidades genéricas (1 token por categoria · primeiro hit)
    entidades = {}
    for cat, tokens in KEYWORD_TOKENS.items():
        for t in tokens:
            if re.search(rf"\b{re.escape(t)}\b", txt):
                entidades[cat] = t
                break

    # Compõe a keyword baseada nas entidades disponíveis
    partes = []
    if "acao" in entidades:
        partes.append(entidades["acao"])
    if "cor" in entidades and entidades.get("cor") != "personalizada":
        partes.append(entidades["cor"])
    if "area" in entidades:
        partes.append(entidades["area"])
    if "material" in entidades and "area" not in entidades:
        partes.append(entidades["material"])
    if "qualificador" in entidades and len(partes) < 3:
        partes.append(entidades["qualificador"])

    if not partes:
        # Fallback · só pra subtipos especiais
        if subtipo == "relatorio_qualidade":
            return "VT qualidade · imagens"
        if subtipo == "confirmacao_pendente":
            return "confirmação pendente"
        # Pega 4 primeiras palavras significativas
        STOP = {"a","o","os","as","de","da","do","das","dos","em","no","na","e","ou","que","é","com","por","para","sem","sobre","ai","lá","aqui","já","não","sim","mas","só","tem","tudo","isso"}
        palavras = re.findall(r"\b[a-zà-ú]+\b", txt)
        sig = [p for p in palavras if p not in STOP and len(p) > 2][:4]
        return " ".join(sig) if sig else None

    return " ".join(partes[:3])


# Subtipos de reprovacao_retorno · classifica cada ciclo de retrabalho pela natureza da mensagem
# Ordem importa · mais específico primeiro · primeiro match vence
SUBTIPOS_REPROVACAO = [
    ("relatorio_qualidade",  re.compile(r"recebemos\s+(as\s+)?(imagens|informações).*visita\s+de\s+qualidade|durante\s+a\s+visita\s+(de\s+qualidade)?|visita\s+de\s+qualidade\s+realizada", re.IGNORECASE)),
    ("agendamento_reparo",   re.compile(r"agenda\s+de\s+(visita|retorno)|in[íi]cio\s+de\s+reparo\s+dia|confirmad[ao]\s+para\s+o\s+dia|continuidade\s+(na|da)\s+reaplica|dar\s+continuidade", re.IGNORECASE)),
    ("decisao_cliente",      re.compile(r"cliente\s+(optou|definiu|decidiu|escolheu)|(\w+)\s+(definiu|optou\s+pela)\s+(fazer\s+)?(uma\s+)?(faixa\s+de\s+|reaplica)", re.IGNORECASE)),
    # FIX bug #4 auditoria · subtipos novos · MAIS ESPECÍFICOS ANTES de escopo_definido
    ("reaplicacao_verniz",   re.compile(r"reaplica[çc][aã]o\s+(do\s+|de\s+)?(verniz|lumina|pu)|reaplicar\s+(o\s+|a\s+)?(verniz|lumina|pu)|nova\s+camada\s+(de\s+)?(verniz|lumina|pu)", re.IGNORECASE)),
    ("reaplicacao_completa", re.compile(r"reaplica[çc][aã]o\s+(do\s+)?piso\s+(total|completa|completo|inteiro)|reaplica[çc][aã]o\s+completa|refazer\s+(toda\s+|todo\s+)?(o\s+|a\s+)?(piso|obra|aplica[çc][aã]o)|remover\s+(toda\s+|todo\s+)?(o\s+|a\s+)?piso\s+e\s+reaplicar", re.IGNORECASE)),
    ("escopo_definido",      re.compile(r"escopo\s+(para|da|de)\s+reaplica|iremos\s+reaplicar|essas?\s+paredes?\s+para\s+reaplicar|reaplica[çc][aã]o\s+(da\s+área|da\s+sala|das?\s+parede)", re.IGNORECASE)),
    ("defeito_relatado",     re.compile(r"marc(a|ou)\w*\s+(o\s+)?piso|piso\s+(marcad|com\s+marca)|trinca|fissura|rachadura|descolamento|cliente\s+(est[aá]\s+)?questionando|tendo\s+problema", re.IGNORECASE)),
    ("proposta_tecnica",     re.compile(r"ideal\s+(é|eh|seria)\s+reaplicar|vai\s+(ter\s+que|precisar)\s+refazer|tem\s+que\s+refazer|acredito\s+que.*(ajuste|resolve)|alguns\s+ajustes\s+(j[áa]\s+)?resolve", re.IGNORECASE)),
    ("solicitacao_admin",    re.compile(r"fazer\s+\d+\s+resumos?|poderia\s+fazer\s+(\d+\s+)?resumos?|preciso\s+(de\s+|do\s+)?resumo", re.IGNORECASE)),
    ("confirmacao_pendente", re.compile(r"\b[ée]\s+a\s+reaplica[çc][aã]o\s+(do|da)\b|fica\s+combinad[ao]", re.IGNORECASE)),

    # FIX bug #3 · subtipos ampliados · reduz fallback "tratativa" de 72% pra ~30%
    # Ordem: mais específico primeiro · subtipos de natureza do problema

    # Verniz/brilho (LUMINA/verniz/PU/brilho) · AMPLO · pega msgs que falam do verniz sem ser reaplicação formal
    ("problema_verniz",     re.compile(
        r"\b(verniz|lumina|brilho|pu\b|poliuretano|primer|resina)"
        r"|\b(fosco|opaco|amarelad|esbranqui[çc]|descascando|descascou|soltando|soltou)"
        r".*\b(piso|chão|superf[íi]cie)?"
        r"|\b(piso|chão)\s+(fosco|opaco|sem\s+brilho|perdeu\s+(o\s+)?brilho)",
        re.IGNORECASE)),

    # Marcas de superfície (marcas/rolo/cera/riscos/manchas de aplicação)
    ("problema_marcas",     re.compile(
        r"\b(marc[ao]s?\s+(de\s+)?(rolo|cera|aplica[çc][aã]o|esp[áa]tula|desempenadeira))"
        r"|rolo\s+(de\s+)?cera"
        r"|marc[ao]s?\s+(no|na|do|da)\s+(piso|chão|superf[íi]cie)"
        r"|\b(risc[oa]s?|arranhõ|arranhad)\w*\s*(no|na|do|da)?\s*(piso|chão|superf[íi]cie)?"
        r"|cera\s+(marc|excess|acumul)\w*"
        r"|balde\s+(marc|acabou\s+marc)\w*",
        re.IGNORECASE)),

    # Problemas de cor/tom/mancha (diferença de cor, manchas, tom diferente)
    ("problema_cor",        re.compile(
        r"\b(mancha|manchad[oa]|manchas)\b"
        r"|\b(tom|tonalidade)\s+(diferente|errad[oa]|desigual|irregular)"
        r"|\b(diferen[çc]a|varia[çc][aã]o)\s+(de\s+)?(cor|tom|tonalidade)"
        r"|\bcor\s+(diferente|errad[oa]|desigual|irregular|escur[oa]|clar[oa])"
        r"|\b(descolor|desbota|amarel)\w+"
        r"|\b(piso|chão)\s+(manchad|com\s+mancha)",
        re.IGNORECASE)),

    # Refazer completo (amplo · pega linguagem informal de reaplicação total)
    ("problema_refazer",    re.compile(
        r"\brefazer\b|\breaplica[çc][aã]o\b|\breaplicar\b"
        r"|\blixar\s+(tudo|todo|toda)"
        r"|\bremover\s+(o\s+|a\s+)?(piso|aplica[çc][aã]o)"
        r"|\b(arranc|retir)\w+\s+(o\s+|a\s+)?(piso|aplica[çc][aã]o)",
        re.IGNORECASE)),
]

LABELS_SUBTIPO = {
    "relatorio_qualidade":  "Relatório VT qualidade",
    "agendamento_reparo":   "Agendamento de reparo",
    "decisao_cliente":      "Decisão do cliente",
    "reaplicacao_verniz":   "Reaplicação de verniz",
    "reaplicacao_completa": "Reaplicação completa",
    "escopo_definido":      "Escopo de reaplicação",
    "defeito_relatado":     "Defeito relatado",
    "proposta_tecnica":     "Proposta técnica",
    "solicitacao_admin":    "Solicitação admin",
    "confirmacao_pendente": "Confirmação pendente",
    # Subtipos novos (bug #3)
    "problema_verniz":      "Problema de verniz/brilho",
    "problema_marcas":      "Marcas de superfície",
    "problema_cor":         "Problema de cor/tom",
    "problema_refazer":     "Reaplicação necessária",
    "tratativa":            "Tratativa",
}

# Amostra solicitada · antecede cor_aprovada · gargalo de cor (CORES pipe)
PAD_AMOSTRA_SOLICITADA = re.compile(
    r"\b("
    r"solicit\w+\s+(de\s+)?amostra"
    r"|amostra\s+(solicitada|pendente|enviada|recebida|chegou)"
    r"|(envia|manda|enviar|mandar)\s+(uma\s+|outra\s+|nova\s+)?amostra"
    r"|preciso\s+de\s+amostra"
    r"|aguardando\s+amostra"
    r"|nova\s+amostra"
    r")\b",
    re.IGNORECASE,
)
# Cor: padrões FORTES (sinal explícito · não "COR: X" do card)
PAD_COR_APROVADA = re.compile(
    r"\b("
    r"amostra\s+(aprovada|escolhida|confirmada)"
    r"|cor\s+(escolhida|aprovada|definida|confirmada)"
    r"|escolheu\s+(a\s+)?cor"
    r"|cliente\s+(aprovou|escolheu|definiu)\s+(a\s+)?cor"
    r")\b",
    re.IGNORECASE,
)
PAD_INICIO_ANUNCIADO = re.compile(r"in[íi]cio\s+(da\s+obra|previsto|confirmado)\s*[:\s]*(\d{1,2}[/-]\d{1,2})", re.IGNORECASE)
PAD_MATERIAL_PRODUZIDO = re.compile(r"\b(material\s+produzido|os\s+produzida|ind[uú]stria\s+(finaliz|conclu)|material\s+saiu|material\s+em\s+obra|material\s+enviado)\b", re.IGNORECASE)
# FIX BUG: \b após "finaliz" bloqueava "obra finalizada" (no boundary entre z e a) · trocar por \w*
PAD_FINALIZACAO = re.compile(r"\b(obra\s+(finaliz\w*|conclu\w*)|piso\s+(finaliz\w*|conclu\w*))", re.IGNORECASE)
PAD_APROVACAO_CLIENTE = re.compile(r"\b(obra\s+aprovad\w*|cliente\s+aprov(ou|ado|ada)|aprov(ado|ada|ação).*cliente|v[íi]deo\s+de\s+aprova[çc][aã]o)\b", re.IGNORECASE)

# === MARCOS DE FASE GRANDE · trazidos do timeline_10obras (calibrados em P2B/SILVANA/PALLOMA) ===
# Filtragem cuidadosa: APENAS marcos de fase macro · NÃO trazer detalhe operacional (camada individual,
# cobrança granular, ocorrência formal · esses são do outro propósito ou já cobertos no Lab Orion)

# Escopo aprovado · marco-charneira pré-obra → liberação
PAD_ESCOPO_APROVADO = re.compile(r"(♦️\s*)?escopo\s+aprovad\w*", re.IGNORECASE)

# Equipe definida · alocação dos aplicadores (sinal de pré-execução fechando)
PAD_EQUIPE_DEFINIDA = re.compile(
    r"\b("
    r"prestadores\s+dessa\s+obra\s+ser[áa]o"
    r"|aplicador(es)?\s+ser[áa]o"
    r"|equipe\s+definida"
    r"|equipe\s+alocada"
    r")",
    re.IGNORECASE,
)

# Material entregue em obra (logística OK · pronto pra começar)
PAD_MATERIAL_ENTREGUE = re.compile(
    r"\b("
    r"material\s+chegou(\s+(agora|hoje|aqui))?"
    r"|chegou\s+(o\s+)?material"
    r"|recebimento\s+(do\s+)?material"
    r"|material(\s+em\s+obra)?\s+conferido"
    r")",
    re.IGNORECASE,
)

# Relatório VT qualidade · frase-padrão Caroline pós-execução · disparo de retrabalho
PAD_RELATORIO_VT_QUALIDADE = re.compile(
    r"recebemos\s+(as\s+)?(imagens|informações)\s+e?\s*(informações)?\s*referentes\s+(à|a)\s+(nossa\s+)?(última\s+)?visita",
    re.IGNORECASE,
)

# Obra postergada · sinal de fricção · cronograma reset (importante pra macro-etapas)
PAD_OBRA_POSTERGADA = re.compile(
    r"\b("
    r"obra\s+postergad\w*"
    r"|projeto\s+postergad\w*"
    r"|nossa\s+entrada\s+ser[áa]\s+postergad"
    r"|entrada\s+postergad\w*"
    r"|🚨\s*obra\s+postergad"
    r")",
    re.IGNORECASE,
)

# Última camada · transição final da execução (pronto pro verniz)
PAD_ULTIMA_CAMADA = re.compile(
    r"\b("
    r"finalizamos\s+(a\s+)?[úu]ltima\s+camada"
    r"|[úu]ltima\s+camada\s+(aplicad|finaliz)"
    r"|preparado\s+pra\s+aplica[çc][aã]o\s+do\s+verniz"
    r"|pronto\s+pro\s+verniz"
    r")",
    re.IGNORECASE,
)

# Troca de aplicador em obra · sinal de problema de pessoa
PAD_TROCA_APLICADOR = re.compile(
    r"\b("
    r"(prestador|aplicador|equipe|filho)\s+\w+\s+assumir[áa]?\s+(as\s+)?atividades?"
    r"|(no\s+lugar\s+(dele|dela|do\s+\w+))"
    r"|(em\s+seu\s+lugar\s+est[áa])"
    r"|(\w+)\s+est[áa]\s+de\s+atestado\s+m[ée]dico"
    r"|substitu(i[çc][aã]o|indo)\s+(do|na\s+equipe)"
    r")",
    re.IGNORECASE,
)

# Detector de "card de bot" · msgs com separators longos `------` ou padrão APLICADOR:/SUPERVISOR:/CLIENTE: juntos
PAD_CARD_BOT_SEPARATOR = re.compile(r"-{10,}")
PAD_CARD_BOT_CAMPOS = re.compile(r"APLICADOR\s*:.*SUPERVISOR\s*:.*CLIENTE\s*:", re.DOTALL | re.IGNORECASE)


def is_card_bot(texto):
    """Detecta se a msg é card de status do bot (separators ou campos padronizados)."""
    if not texto:
        return False
    if PAD_CARD_BOT_SEPARATOR.search(texto):
        return True
    if PAD_CARD_BOT_CAMPOS.search(texto):
        return True
    return False

# Solicitação de material durante execução
PAD_MAT_SOLIC = re.compile(r"\b(precis[ao]|preciso|preciso\s+de|manda\s+(a|o|mais)|envia(r)?\s+(mais|outro|outra)|fal(ta|tou)|comprar|preciso\s+comprar|sair\s+para\s+comprar)\b", re.IGNORECASE)
PAD_TELA_TOTAL = re.compile(r"\btela\s+(total|por\s+completo|no\s+piso\s+total|inteir[ao])\b", re.IGNORECASE)
PAD_QTD_KIT = re.compile(r"(\d+)\s*(kits?|baldes?|latas?|sacos?)\b", re.IGNORECASE)
PAD_SOBROU = re.compile(r"\bsobr(ou|ar[ao])\s+(\d+)?\s*(\w+)?", re.IGNORECASE)

# Camada/demão + produto · ditas pelo aplicador (com ordinal explícito)
# Ex: "Segunda camada de stelion" · "Primeira demão de lumina aplicado" · "Aplicação primeira camada stelion"
PAD_CAMADA_PRODUTO = re.compile(
    r"\b(1[ªa°]|2[ªa°]|3[ªa°]|4[ªa°]|primeira|segunda|terceira|quarta)\s+(camada|aplica[çc][ãa]o|dem[ãa]o)\b[^\n]{0,80}?\b(stelion|lilit|leona|lumina|teron|kalahari|argento|primer|verniz|pu)\b",
    re.IGNORECASE
)
# Aplicação "simples" sem ordinal · vira camada 1 inferida
# Ex: "Aplicação de primer" · "aplicando verniz" · "Programação aplicação verniz lumina"
PAD_APLICACAO_SIMPLES = re.compile(
    r"\baplica(?:ndo|[çc][ãa]o)\b(?:[^\n]{0,40}?)\b(stelion|lilit|leona|lumina|teron|kalahari|argento|primer|verniz|pu)\b",
    re.IGNORECASE
)
# Produto + finalizado/aplicado/concluído (sem ordinal)
# Ex: "Verniz finalizado" · "primer aplicado" · "Stelion concluído"
PAD_PRODUTO_FINALIZADO = re.compile(
    r"\b(stelion|lilit|leona|lumina|teron|kalahari|argento|primer|verniz|pu)\s+(?:foi\s+)?(?:finaliz|conclu|aplicad)",
    re.IGNORECASE
)
# Sobra com produto · "Sobrou 3 teron fechado" · "sobraram 2 baldes de stelion"
PAD_SOBROU_PRODUTO = re.compile(
    r"\bsobr(?:ou|aram?)\s+(\d+)?\s*(?:\w+\s+){0,2}?\b(stelion|lilit|leona|lumina|teron|kalahari|argento|primer|verniz|pu)\b",
    re.IGNORECASE
)
# Verbos pra classificar snapshots de material em 2026+
PAD_VERBO_ENTRADA = re.compile(r"\b(chegou|chegaram|entreg(?:a|ou|aram|amos)|recebi|recebido|envia(?:do|r|ndo|mos)|mandar|mandei|veio|vieram|sa[ií]ram|saiu)\b", re.IGNORECASE)
PAD_VERBO_ESTOQUE = re.compile(r"\b(temos|tem|tinha|tenho|estamos\s+com|ainda\s+(?:tem|temos)|dispon[ií]ve|material\s+em\s+obra)\b", re.IGNORECASE)
PAD_VERBO_SOBRA   = re.compile(r"\bsobr(?:ou|aram?|a)\b", re.IGNORECASE)
PAD_VERBO_SOLIC   = re.compile(r"\b(precis[ao]\b|preciso\b|(?:vamos|iremos)\s+precisar|manda(?:r)?\s+(?:mais|outr))", re.IGNORECASE)
PAD_VERBO_CONSUMO = re.compile(
    r"\b("
    r"consum[oeiu]"  # consumo, consumiu, consumindo, consumimos
    r"|gast(?:ei|ou|amos|aram)"
    r"|usamos|usaram|usado[as]?|foram\s+usad"  # NOVO · "usados", "usaram", "foram usados"
    r"|aplicamos|aplicaram|aplicad[oa]s?"
    r"|tivemos\s+que\s+usar"  # NOVO · "tivemos que usar X kit"
    r"|fizemos|fez\s+em"
    r")",
    re.IGNORECASE
)
# Cores, renomeações e vocabulário do campo → família de produto-mãe na OS Indústria
# IMPORTANTE: aplicadores no Telegram usam apelidos diferentes do nome do produto na OS:
#   - "verniz" no Telegram = LUMINA (produto base) na OS
#   - "primer" no Telegram = LUMINA PRIMER na OS (mas como tem "PRIMER" literal, mapeamos só PRIMER)
#   - "teron" no Telegram = LEONA na OS (renomeação abr/2026)
#   - "kalahari" / "argento" = cores do STELION
PRODUTO_FAMILIA = {
    "KALAHARI": "STELION",  # cor STELION
    "ARGENTO":  "STELION",  # cor STELION
    "MIRAGE":   "LILIT",    # cor LILIT (paredes) · ex: TALLY FELDMAN
    "ARÁBIA":   "STELION",  # cor STELION · ex: P2B ENGENHARIA
    # SAARA NÃO está aqui · cor COMPARTILHADA STELION/LILIT
    # ANDRE KEUNECKE: 58 baldes STELION cor Saara · GUSTAVO: 12 baldes LILIT cor Saara
    # Família deve vir do contexto da OS (nome do material), não do nome da cor
    "TERON":    "LEONA",    # nome novo do produto (abr/2026); LEONA é o nome canônico mantido
    "VERNIZ":   "LUMINA",   # aplicador fala "verniz", produto na OS é LUMINA
    "PU":       "LUMINA",   # alguns aplicadores chamam o verniz de "PU" (poliuretano)
}

# Problemas
PAD_PROBLEMA = re.compile(r"\b(trinca|fissura|rachadura|infiltrac[aã]o|patolog|errad[ao]|atras[ao]u?|problema|defeito|reclamac[aã]o)\b", re.IGNORECASE)

# Marcos técnicos de execução (dito por aplicadores no Telegram)
# Ordem importa · padrões mais específicos primeiro pra evitar falso positivo
MARCOS_EXECUCAO = [
    ("visita_durante_obra", re.compile(r"\b(cliente\s+(em\s+obra|visitou|esteve\s+em\s+obra|chegou\s+em\s+obra)|visita\s+do\s+cliente|visita\s+(t[eé]cnica\s+)?durante\s+(a\s+)?obra|visita\s+de\s+qualidade|vt\s+de\s+qualidade|inspe[çc][aã]o\s+(em\s+obra|de\s+qualidade)|t[eé]cnico\s+em\s+obra\s+hoje|visita\s+agendada\s+com\s+(os\s+)?respons[áa]veis)\b", re.IGNORECASE)),
    ("verniz_finalizado",  re.compile(r"\b(verniz\s+finaliz|verniz\s+aplicad|finaliza[çc][aã]o\s+do\s+verniz)", re.IGNORECASE)),
    ("obra_finalizada",    re.compile(r"\b(obra\s+finaliz|piso\s+finaliz|piso\s+conclu)", re.IGNORECASE)),
    ("verniz_iniciado",    re.compile(r"\b(programa[çc][aã]o\s+aplica[çc][aã]o\s+verniz|aplica[çc][aã]o\s+(de\s+)?verniz|aplicando\s+verniz|verniz\s+lumina|envie\s+.*verniz|precisar.*verniz|falta.*verniz)", re.IGNORECASE)),
    ("cura",               re.compile(r"\b(aguardando\s+cura|em\s+cura|cura\s+do\s+(piso|stelion|material)|cura\s+t[eé]cnica)", re.IGNORECASE)),
    ("camada_3",           re.compile(r"\b(terceira\s+camada|3[ªao°]?\s*camada|3[ªa]\s+demão|terceira\s+demão|tr[eê]s\s+(m[aã]os|camadas|dem[aã]os))", re.IGNORECASE)),
    ("camada_2",           re.compile(r"\b(segunda\s+camada|2[ªao°]?\s*camada|2[ªa]\s+demão|segunda\s+demão|duas\s+(m[aã]os|camadas|dem[aã]os))", re.IGNORECASE)),
    ("camada_1",           re.compile(r"\b(primeira\s+camada|1[ªao°]?\s*camada|1[ªa]\s+demão|primeira\s+demão|uma\s+(m[aã]o|camada|dem[aã]o))", re.IGNORECASE)),
    ("aplicacao_stelion",  re.compile(r"\b(aplic\w+\s+.*ste?li|ste?li\w*\s+aplic|m[aã]os?\s+de\s+ste?li|reparos?\s+.*ste?li|ste?li\w*\s+no\s+piso|passamos?\s+.*ste?li|aplicamos?\s+.*ste?li)", re.IGNORECASE)),
    ("aplicacao_lilit",    re.compile(r"\b(aplic\w+\s+.*lilit|lilit\w*\s+aplic|m[aã]os?\s+de\s+lilit|reparos?\s+.*lilit|passamos?\s+.*lilit|aplicamos?\s+.*lilit)", re.IGNORECASE)),
    ("reparo",             re.compile(r"\b(reparos?\s+(apontad|realizad|feit|conclu)|fiz\w*\s+.*reparos?|reparando|reaplicar|reaplica[çc][aã]o)", re.IGNORECASE)),
    ("lixamento",          re.compile(r"\b(lixamento|lixad[ao]|lixando|lixar)\b", re.IGNORECASE)),
    ("aplicacao_tela",     re.compile(r"\b(aplica[çc][aã]o\s+(de\s+)?tela|tela\s+aplicad|telar)\b", re.IGNORECASE)),
    ("aplicacao_teron",    re.compile(r"\b(aplica[çc][aã]o\s+(de\s+)?teron|teron\s+aplicad|selador\s+aplic|aplic\w+\s+selador)\b", re.IGNORECASE)),
    ("aplicacao_primer",   re.compile(r"\b(aplica[çc][aã]o\s+(de\s+)?primer|primer\s+aplicad|passamos?\s+.*primer|aplicamos?\s+.*primer)\b", re.IGNORECASE)),
    ("preparacao",         re.compile(r"\b(limpeza|prote[çc][aã]o\s+(das\s+áreas|do\s+ambiente)|requadro|substitui[çc][aã]o\s+de\s+fitas|troca\s+(de\s+)?fitas)", re.IGNORECASE)),
    ("diario_obra",        re.compile(r"\b(di[áa]rio\s+de\s+obra|dia\s+\d{1,2}[/\-]\d{1,2}\b)", re.IGNORECASE)),
    ("inicio_dia",         re.compile(r"\b(equipe\s+em\s+obra|chegando\s+agora|chegamos|estamos\s+chegando|estou\s+(retornando|chegando|na\s+obra|indo)|j[áa]\s+est(ou|amos)\s+(na\s+obra|em\s+obra|chegando)|retornando\s+(pra|para|à)\s+obra|retorno\s+hoje|bom\s+dia[,.]?\s*(pessoal|equipe|galera)?[,.]?\s*(estamos|cheg|iniciar|em\s+obra)|chegarei\s+[àa]s?\s+\d)", re.IGNORECASE)),
    ("fim_dia",            re.compile(r"\b(saindo\s+(de|da)\s+obra|equipe\s+saindo|acabamos\s+(agora|hoje)|encerrando\s+o\s+dia|finalizamos\s+o\s+dia)", re.IGNORECASE)),
]

LABELS_EXECUCAO = {
    "inicio_dia":          "Início do dia",
    "cobranca_status":     "Cobrança de status",
    "preparacao":          "Preparação",
    "aplicacao_primer":    "Primer",
    "aplicacao_tela":      "Tela aplicada",
    "aplicacao_teron":     "Selador/Teron",
    "aplicacao_stelion":   "Aplicação Stelion",
    "aplicacao_lilit":     "Aplicação Lilit",
    "reparo":              "Reparo",
    "lixamento":           "Lixamento",
    "camada_1":            "1ª camada",
    "camada_2":            "2ª camada",
    "camada_3":            "3ª camada",
    "cura":                "Aguardando cura",
    "verniz_iniciado":     "Verniz",
    "verniz_finalizado":   "Verniz finalizado",
    "obra_finalizada":     "Obra finalizada",
    "diario_obra":         "Diário de obra",
    "fim_dia":             "Fim do dia",
    "visita_durante_obra": "Visita em obra",
}

# Padrão de cobrança de status (msg de não-aplicador perguntando se tem equipe em obra)
PAD_COBRANCA = re.compile(
    r"\b(temos\s+equipe\s+em\s+obra|tem\s+equipe\s+em\s+obra|j[áa]\s+chegou|chegou\?|chegaram\??|alguém\s+em\s+obra|equipe\s+chegou|status\s+da\s+obra|status\??$)\b",
    re.IGNORECASE,
)


def detectar_marco_em_msg(msg, tipo_pad, padrao):
    """Verifica se a msg tem o padrão. Retorna dict com info do marco ou None.
    FIX bug #5 auditoria · guards contra falsos positivos:
    - Negação no contexto (até 30 chars antes do match): 'não aprovou', 'sem aprovação', etc
    - Pergunta literal (msg termina em ? ou match seguido de ?): 'tem material?' não é fato
    - Predição futura (verbos no futuro): 'finalizara', 'finalizará', 'irá finalizar'"""
    texto = msg.get("content") or ""
    m = padrao.search(texto)
    if not m:
        return None

    # GUARD 1 · Negação até 30 chars antes do match
    inicio = m.start()
    contexto_antes = texto[max(0, inicio - 30):inicio].lower()
    if re.search(r"\bn[ãa]o\s+\w{0,20}$", contexto_antes) or re.search(r"\bsem\s+\w{0,20}$", contexto_antes):
        return None

    # GUARD 2 · Pergunta · marcos de FATO não cabem em interrogação
    TIPOS_QUE_NAO_ACEITAM_PERGUNTA = {
        "material_produzido", "equipe_definida", "material_entregue",
        "finalizacao", "aprovacao_cliente", "ultima_camada"
    }
    if tipo_pad in TIPOS_QUE_NAO_ACEITAM_PERGUNTA:
        # Pega 60 chars ao redor do match · se tem '?' próximo, suspeito
        ao_redor = texto[max(0, inicio - 30):min(len(texto), m.end() + 30)]
        if "?" in ao_redor:
            return None

    # GUARD 3 · Predição futura (apenas finalizacao) · "finalizara" / "finalizará" / "irá finalizar"
    if tipo_pad == "finalizacao":
        match_str = m.group(0).lower()
        if re.search(r"finaliz(ar[áa]|ará|aremos|ará?o)", match_str):
            return None
        # "irá finalizar", "vai finalizar"
        if re.search(r"\b(irá|ira|vai|vamos)\s+\w{0,10}\s*finaliz", contexto_antes):
            return None

    out = {
        "tipo": tipo_pad,
        "data": (msg.get("timestamp") or "")[:10],
        "data_iso": msg.get("timestamp"),
        "autor": normalizar_sender(msg.get("sender") or "?")[:35],
        "trecho": texto[:160].replace("\n", " ").strip(),
        "msg_id": msg.get("id"),
        "match": m.group(0)[:50],
    }
    # Detecta subtipo pra reprovacao_retorno · classificação por natureza da mensagem
    if tipo_pad == "reprovacao_retorno":
        subtipo = "tratativa"  # default
        for st, pad_st in SUBTIPOS_REPROVACAO:
            if pad_st.search(texto):
                subtipo = st
                break
        out["subtipo"] = subtipo
        out["label_subtipo"] = LABELS_SUBTIPO.get(subtipo, subtipo)
        out["keyword"] = extrair_keyword(texto, subtipo)
    else:
        out["keyword"] = extrair_keyword(texto, tipo_pad)
    return out


# ============================================================
# Cálculo de fases (cluster por densidade)
# ============================================================

def calcular_fases(msgs_ordenadas, data_exec_confirmada, data_criacao, data_exec_prevista=None):
    """
    Detecta fases automaticamente baseado em densidade de msgs Telegram:
      1. Planejamento inicial · da 1ª msg até primeira pausa ≥30d
      2. Hibernação · gap ≥30d sem msg significativa
      3. Despertar · 1ª msg após hibernação
      4. Pré-execução · do despertar até cluster denso de execução
      5. Execução · cluster denso (≥5 msgs/dia em janela de 7d ao redor de dataExecucaoConfirmada)
      6. Pós · após cluster até hoje
    """
    if not msgs_ordenadas:
        return []

    # Agrupa por dia
    msgs_por_dia = defaultdict(int)
    primeira_data = parse_iso(msgs_ordenadas[0].get("timestamp")).date() if parse_iso(msgs_ordenadas[0].get("timestamp")) else None
    ultima_data = parse_iso(msgs_ordenadas[-1].get("timestamp")).date() if parse_iso(msgs_ordenadas[-1].get("timestamp")) else None

    for m in msgs_ordenadas:
        dt = parse_iso(m.get("timestamp"))
        if dt:
            msgs_por_dia[dt.date()] += 1

    if not primeira_data or not ultima_data:
        return []

    # Detecta gaps de hibernação (≥30d sem msgs)
    fases = []
    dias_com_msg = sorted(msgs_por_dia.keys())

    # Fase 1: Planejamento inicial · 1ª msg até primeiro gap ≥30d (ou até data_exec - 30 se sem gap)
    fase_inicio = primeira_data
    fase_fim = None
    hibernacoes = []
    for i in range(1, len(dias_com_msg)):
        gap = (dias_com_msg[i] - dias_com_msg[i - 1]).days
        if gap >= HIBERNACAO_GAP_DIAS:
            hibernacoes.append((dias_com_msg[i - 1], dias_com_msg[i], gap))

    # Identifica cluster de execução
    # FIX bug #2 auditoria · obras sem data_exec_confirmada (só prevista no passado) zeravam o cluster
    # Estratégia: tenta exec_confirmada primeiro · fallback pra exec_prevista (se já passou) · fallback final
    # pra janela mais ampla buscando o dia mais denso da obra
    cluster_exec_inicio, cluster_exec_fim = None, None
    data_referencia_exec = data_exec_confirmada or (
        data_exec_prevista if (data_exec_prevista and data_exec_prevista <= HOJE_DATE) else None
    )
    if data_referencia_exec:
        janela_ini = data_referencia_exec - timedelta(days=EXEC_JANELA_DIAS)
        janela_fim = data_referencia_exec + timedelta(days=EXEC_JANELA_DIAS)
        dias_no_cluster = [d for d in dias_com_msg if janela_ini <= d <= janela_fim and msgs_por_dia[d] >= EXEC_CLUSTER_MSGS_DIA]
        if dias_no_cluster:
            cluster_exec_inicio = min(dias_no_cluster)
            cluster_exec_fim = max(dias_no_cluster)
    # Fallback final: se ainda não achou cluster, busca o dia mais denso de toda a obra (≥ 2× threshold)
    if not cluster_exec_inicio and dias_com_msg:
        densos = [(d, msgs_por_dia[d]) for d in dias_com_msg if msgs_por_dia[d] >= EXEC_CLUSTER_MSGS_DIA * 2]
        if densos:
            # Pega cluster centrado no dia MAIS denso · janela ±5 dias com threshold normal
            dia_pico = max(densos, key=lambda x: x[1])[0]
            j_ini = dia_pico - timedelta(days=5)
            j_fim = dia_pico + timedelta(days=5)
            dias_no_cluster = [d for d in dias_com_msg if j_ini <= d <= j_fim and msgs_por_dia[d] >= EXEC_CLUSTER_MSGS_DIA]
            if dias_no_cluster:
                cluster_exec_inicio = min(dias_no_cluster)
                cluster_exec_fim = max(dias_no_cluster)

    # Monta fases sequenciais
    if hibernacoes:
        # Planejamento até primeira hibernação
        fim_planej = hibernacoes[0][0]
        n_msgs_planej = sum(n for d, n in msgs_por_dia.items() if fase_inicio <= d <= fim_planej)
        fases.append({
            "nome": "Planejamento inicial",
            "inicio": fase_inicio.isoformat(),
            "fim": fim_planej.isoformat(),
            "duracao_dias": (fim_planej - fase_inicio).days + 1,
            "n_msgs": n_msgs_planej,
        })
        # Hibernações + despertares
        # FIX bug fronteiras sobrepostas · h_ini é o último dia COM msg antes do gap,
        # h_fim é o primeiro dia COM msg depois do gap. A hibernação real é o intervalo
        # ENTRE eles: de (h_ini+1) até (h_fim-1). Antes: inicio/fim incluíam os dias
        # de fronteira, causando sobreposição com Planejamento e Despertar (672 dias
        # contados 2x no dataset).
        for idx, (h_ini, h_fim, gap) in enumerate(hibernacoes):
            hib_inicio_real = h_ini + timedelta(days=1)
            hib_fim_real = h_fim - timedelta(days=1)
            duracao_hib = max(1, (hib_fim_real - hib_inicio_real).days + 1)
            n_msgs_hib = sum(n for d, n in msgs_por_dia.items() if hib_inicio_real <= d <= hib_fim_real)
            fases.append({
                "nome": f"Hibernação{' #' + str(idx+1) if len(hibernacoes) > 1 else ''}",
                "inicio": hib_inicio_real.isoformat(),
                "fim": hib_fim_real.isoformat(),
                "duracao_dias": duracao_hib,
                "n_msgs": n_msgs_hib,
            })
            # Despertar = msgs depois de h_fim até próxima hibernação ou cluster ou fim
            proxima_marca = (
                hibernacoes[idx + 1][0] if idx + 1 < len(hibernacoes)
                else cluster_exec_inicio if cluster_exec_inicio
                else ultima_data
            )
            # Despertar é da retomada até a próxima marca
            nome_despertar = "Despertar e pré-execução" if (idx + 1 == len(hibernacoes) and cluster_exec_inicio) else "Atividade retomada"
            n_msgs_desp = sum(n for d, n in msgs_por_dia.items() if h_fim <= d < proxima_marca)
            fases.append({
                "nome": nome_despertar,
                "inicio": h_fim.isoformat(),
                "fim": (proxima_marca - timedelta(days=1)).isoformat() if proxima_marca > h_fim else h_fim.isoformat(),
                "duracao_dias": max(1, (proxima_marca - h_fim).days),
                "n_msgs": n_msgs_desp,
            })
    else:
        # Sem hibernação · só planejamento direto
        fim_planej = cluster_exec_inicio - timedelta(days=1) if cluster_exec_inicio else ultima_data
        n_msgs_planej = sum(n for d, n in msgs_por_dia.items() if fase_inicio <= d <= fim_planej)
        fases.append({
            "nome": "Planejamento + pré-execução",
            "inicio": fase_inicio.isoformat(),
            "fim": fim_planej.isoformat(),
            "duracao_dias": (fim_planej - fase_inicio).days + 1,
            "n_msgs": n_msgs_planej,
        })

    # Execução
    if cluster_exec_inicio and cluster_exec_fim:
        n_msgs_exec = sum(n for d, n in msgs_por_dia.items() if cluster_exec_inicio <= d <= cluster_exec_fim)
        fases.append({
            "nome": "Execução",
            "inicio": cluster_exec_inicio.isoformat(),
            "fim": cluster_exec_fim.isoformat(),
            "duracao_dias": (cluster_exec_fim - cluster_exec_inicio).days + 1,
            "n_msgs": n_msgs_exec,
        })
        # Pós
        if cluster_exec_fim < ultima_data:
            n_msgs_pos = sum(n for d, n in msgs_por_dia.items() if cluster_exec_fim < d <= ultima_data)
            fases.append({
                "nome": "Pós-execução",
                "inicio": (cluster_exec_fim + timedelta(days=1)).isoformat(),
                "fim": ultima_data.isoformat(),
                "duracao_dias": (ultima_data - cluster_exec_fim).days,
                "n_msgs": n_msgs_pos,
            })

    return fases


# ============================================================
# Detecção de marcos via mensagens
# ============================================================

def detectar_marcos(msgs_ordenadas):
    """Aplica regex em todas as msgs · retorna lista cronológica de marcos detectados.
    Filtra cards de bot pra evitar falso positivo (cards têm 'COR: X', 'INÍCIO: dd/mm', etc)."""
    marcos = []
    padroes = [
        ("contrato_assinado", PAD_CONTRATO),
        ("escopo_aprovado", PAD_ESCOPO_APROVADO),
        ("vt_agendada", PAD_VT_AGENDADA),
        # vt_entrada_realizada vem ANTES de vt_realizada · regex mais específica vence
        ("vt_entrada_realizada", PAD_VT_ENTRADA_REALIZADA),
        ("vt_realizada", PAD_VT_REALIZADA),
        ("amostra_solicitada", PAD_AMOSTRA_SOLICITADA),
        ("cor_aprovada", PAD_COR_APROVADA),
        ("equipe_definida", PAD_EQUIPE_DEFINIDA),
        ("material_entregue", PAD_MATERIAL_ENTREGUE),
        ("inicio_anunciado", PAD_INICIO_ANUNCIADO),
        ("material_produzido", PAD_MATERIAL_PRODUZIDO),
        ("obra_postergada", PAD_OBRA_POSTERGADA),
        ("ultima_camada", PAD_ULTIMA_CAMADA),
        ("troca_aplicador", PAD_TROCA_APLICADOR),
        ("aprovacao_cliente", PAD_APROVACAO_CLIENTE),
        ("relatorio_vt_qualidade", PAD_RELATORIO_VT_QUALIDADE),
        ("reprovacao_retorno", PAD_REPROVACAO_RETORNO),
        ("finalizacao", PAD_FINALIZACAO),
    ]
    # Pra cada tipo · mantém SÓ o PRIMEIRO match cronológico (a menos que sejam eventos repetíveis)
    # NOVOS únicos: escopo_aprovado, equipe_definida (acontecem 1x na obra)
    # Repetíveis (dedup por dia): material_entregue, obra_postergada, ultima_camada, troca_aplicador, relatorio_vt_qualidade
    UNICOS = {"contrato_assinado", "escopo_aprovado", "equipe_definida",
              "cor_aprovada", "vt_agendada", "vt_realizada", "vt_entrada_realizada",
              "material_produzido"}
    primeiro_de_cada = {}
    todos = []

    for m in msgs_ordenadas:
        # Filtra cards de bot E transcrições (ambíguas demais)
        texto_msg = m.get("content") or ""
        if is_card_bot(texto_msg) or "🎬" in texto_msg or "🎙️" in texto_msg:
            continue
        for tipo, pad in padroes:
            marco = detectar_marco_em_msg(m, tipo, pad)
            if marco:
                if tipo in UNICOS:
                    if tipo not in primeiro_de_cada:
                        primeiro_de_cada[tipo] = marco
                else:
                    todos.append(marco)

    marcos = list(primeiro_de_cada.values()) + todos
    marcos.sort(key=lambda x: x["data_iso"] or "")
    return _dedup_marcos_janela(marcos, janela_dias=5)


def _dedup_marcos_janela(marcos, janela_dias=5):
    """Agrupa marcos consecutivos do mesmo tipo dentro de uma janela de N dias.
    Mantém o primeiro de cada grupo e descarta os seguintes."""
    if not marcos:
        return marcos
    resultado = []
    ultimo_por_tipo = {}
    for m in marcos:
        tipo = m["tipo"]
        data = m.get("data", "")
        chave_anterior = ultimo_por_tipo.get(tipo)
        if chave_anterior and data:
            try:
                d_ant = datetime.strptime(chave_anterior, "%Y-%m-%d")
                d_cur = datetime.strptime(data, "%Y-%m-%d")
                if (d_cur - d_ant).days <= janela_dias:
                    continue
            except ValueError:
                pass
        resultado.append(m)
        if data:
            ultimo_por_tipo[tipo] = data
    return resultado


PAD_RESOLUCAO = re.compile(
    r"\b("
    r"ok|blz|beleza|combinado|perfeito|positivo|certo"
    r"|n[ãa]o\s+precisa|sem\s+necessidade"
    r"|libera(do|d[ao])?|aprovado|autorizado"
    r"|manda|envia|pode\s+(mandar|enviar)"
    r"|fica\s+aguardando|aguarda|aguardando"
    r"|fechado|fechou|fica\s+combinado"
    r"|n[ãa]o\s+pode|n[ãa]o\s+vai\s+dar"
    r")\b",
    re.IGNORECASE,
)


def detectar_solicitacoes_material(msgs_ordenadas, cluster_exec_inicio, cluster_exec_fim):
    """Detecta solicitações de material durante execução · cada uma com resolução pareada.
    Filtra:
      - transcrições de áudio/vídeo (🎬 / 🎙️)
      - negações ('não precisa', 'sem necessidade')
      - duplicatas: mesma palavra-chave + mesmo autor em <15min vira 1 só."""
    if not cluster_exec_inicio:
        return []
    janela_ini_iso = (cluster_exec_inicio - timedelta(days=2)).isoformat()
    janela_fim_iso = (cluster_exec_fim + timedelta(days=2)).isoformat() if cluster_exec_fim else HOJE.isoformat()

    # Coleta msgs da janela
    msgs_janela = []
    for m in msgs_ordenadas:
        ts = m.get("timestamp") or ""
        if not (janela_ini_iso <= ts[:10] <= janela_fim_iso):
            continue
        if is_card_bot(m.get("content") or ""):
            continue
        texto = (m.get("content") or "").strip()
        if not texto:
            continue
        # Pula transcrições (não são solicitações)
        if "🎬" in texto or "🎙️" in texto:
            continue
        msgs_janela.append(m)

    PAD_NEGACAO = re.compile(r"\b(n[ãa]o\s+precisa|sem\s+necessidade|n[ãa]o\s+precisamos|n[ãa]o\s+precisar[áa]?)\b", re.IGNORECASE)
    PAD_SOBRA_FOTO = re.compile(r"\bsobr[ao]u?\s+(de\s+)?material|sobra\s+de\s+material", re.IGNORECASE)
    PAD_PRECISA_ACAO = re.compile(r"\bprecis[ao]\s+(acess?ar|buscar|retirar|ir|verificar)\b", re.IGNORECASE)

    def palavras_chave(texto):
        """Extrai palavras-chave do tópico (tela, massa, primer, etc) pra dedup."""
        kws = set()
        for pad, kw in [
            (r"\btela\b", "tela"),
            (r"\bmassa\s*hard\b", "massa"),
            (r"\bprimer\b", "primer"),
            (r"\blumina\b", "lumina"),
            (r"\bteron\b", "teron"),
            (r"\bstelion\b", "stelion"),
            (r"\bverniz\b", "verniz"),
            (r"\bcera\b", "cera"),
            (r"\bbalde\b", "balde"),
            (r"\bkit\b", "kit"),
        ]:
            if re.search(pad, texto, re.IGNORECASE):
                kws.add(kw)
        return kws

    solicitacoes = []
    JANELA_RESOLUCAO_MIN = 60
    JANELA_DEDUP_TOPICO_MIN = 60  # mesmo tópico (palavra-chave) em 60min vira 1 solicitação

    for idx, m in enumerate(msgs_janela):
        texto = m.get("content") or ""
        # Filtros de exclusão
        if PAD_NEGACAO.search(texto):
            continue
        if PAD_SOBRA_FOTO.search(texto):
            continue  # informe de sobra · já capturado em sobras
        if PAD_PRECISA_ACAO.search(texto):
            continue  # "precisa acessar/buscar" · ação de fluxo, não material
        if not (PAD_MAT_SOLIC.search(texto) or PAD_TELA_TOTAL.search(texto)):
            continue
        ts_iso = m.get("timestamp") or ""
        ts_dt = parse_iso(ts_iso)
        sender = (m.get("sender") or "?")[:30]
        kws_atual = palavras_chave(texto)

        # Dedup por TÓPICO: mesma palavra-chave em ≤60min vira 1 só (independente de autor)
        duplicata = False
        for s in solicitacoes:
            s_dt = parse_iso(s.get("ts_iso"))
            if not s_dt or not ts_dt:
                continue
            delta_min = (ts_dt - s_dt).total_seconds() / 60
            if delta_min > JANELA_DEDUP_TOPICO_MIN:
                continue
            kws_s = s.get("_kws") or set()
            if kws_atual & kws_s and kws_atual:  # mesma palavra-chave (set não vazio)
                duplicata = True
                break
        if duplicata:
            continue

        # Busca resposta de OUTRO autor (até 60min) com palavra de fechamento
        resolucao = None
        for nxt in msgs_janela[idx + 1: idx + 50]:
            n_sender = (nxt.get("sender") or "")[:30]
            if n_sender == sender:
                continue
            n_ts = parse_iso(nxt.get("timestamp"))
            if not n_ts or not ts_dt:
                continue
            delta_min = (n_ts - ts_dt).total_seconds() / 60
            if delta_min > JANELA_RESOLUCAO_MIN:
                break
            n_texto = nxt.get("content") or ""
            if PAD_RESOLUCAO.search(n_texto):
                resolucao = {
                    "data": (nxt.get("timestamp") or "")[:10],
                    "hora": (nxt.get("timestamp") or "")[11:16],
                    "autor": n_sender,
                    "trecho": n_texto[:160].replace("\n", " ").strip(),
                    "delta_min": int(delta_min),
                }
                break

        solicitacoes.append({
            "data": ts_iso[:10],
            "hora": ts_iso[11:16],
            "ts_iso": ts_iso,
            "autor": sender,
            "trecho": texto[:200].replace("\n", " ").strip(),
            "tela_total": bool(PAD_TELA_TOTAL.search(texto)),
            "resolucao": resolucao,
            "_kws": kws_atual,
        })

    # Remove campos auxiliares antes de retornar
    for s in solicitacoes:
        s.pop("_kws", None)
        s.pop("ts_iso", None)
    return solicitacoes


_PAD_PRODUTO_CONTEXTO = re.compile(
    r"\b(stelion|stellion|lilit|lilith|lilite|leona|steleona|lumina|lamina|teron|kalahari|argento|mirage|primer|prime|verniz|pu|selador|hiper)\b",
    re.IGNORECASE,
)

def _extrair_produto_contexto(texto, pos_match, janela=60):
    """Busca nome de produto MAIS PRÓXIMO do match de qtd (±janela chars)."""
    inicio = max(0, pos_match - janela)
    fim = min(len(texto), pos_match + janela)
    trecho = texto[inicio:fim]
    melhor = None
    melhor_dist = 999
    pos_rel = pos_match - inicio
    for hit in _PAD_PRODUTO_CONTEXTO.finditer(trecho):
        dist = abs(hit.start() - pos_rel)
        if dist < melhor_dist:
            melhor_dist = dist
            melhor = hit
    if not melhor:
        return None, None
    lit = melhor.group(1).upper()
    if lit in ("STELLION", "ACABAMENTO"): lit = "STELION"
    elif lit in ("LILITH", "LILITE"): lit = "LILIT"
    elif lit == "STELEONA": lit = "LEONA"
    elif lit == "LAMINA": lit = "LUMINA"
    elif lit == "PRIME": lit = "PRIMER"
    fam = PRODUTO_FAMILIA.get(lit, lit)
    return lit, fam


def detectar_consumo(msgs_ordenadas):
    """Extrai menções a quantidades consumidas/sobras (regex 'X kits/baldes').
    Agora associa produto buscando no entorno da menção de quantidade.
    Sobras tentam extrair qtd + produto: 'Sobrou 3 teron fechado' → qtd=3, produto=TERON, fam=LEONA."""
    consumos = []
    sobras = []
    for m in msgs_ordenadas:
        texto = m.get("content") or ""
        # Quantidades consumidas
        for q_match in PAD_QTD_KIT.finditer(texto):
            prod_lit, prod_fam = _extrair_produto_contexto(texto, q_match.start())
            consumos.append({
                "data": (m.get("timestamp") or "")[:10],
                "autor": normalizar_sender(m.get("sender") or "?")[:30],
                "qtd": q_match.group(1),
                "unidade": q_match.group(2).lower(),
                "produto": prod_lit,
                "produto_familia": prod_fam,
                "trecho": texto[:120].replace("\n", " ").strip(),
            })
        # Sobras com produto explícito (preferido)
        sobra_prod = PAD_SOBROU_PRODUTO.search(texto)
        if sobra_prod:
            qtd_sobra = sobra_prod.group(1)
            produto_lit = sobra_prod.group(2).upper()
            produto_fam = PRODUTO_FAMILIA.get(produto_lit, produto_lit)
            sobras.append({
                "data": (m.get("timestamp") or "")[:10],
                "autor": normalizar_sender(m.get("sender") or "?")[:30],
                "qtd": qtd_sobra,
                "produto": produto_lit,
                "produto_familia": produto_fam,
                "trecho": texto[:200].replace("\n", " ").strip(),
            })
        elif PAD_SOBROU.search(texto):
            # fallback sem produto identificado
            sobras.append({
                "data": (m.get("timestamp") or "")[:10],
                "autor": normalizar_sender(m.get("sender") or "?")[:30],
                "qtd": None, "produto": None, "produto_familia": None,
                "trecho": texto[:200].replace("\n", " ").strip(),
            })
    return consumos, sobras


DATA_CORTE_MATERIAL = "2026-01-01"  # Vitor: 2025 não interessa mais


def detectar_snapshots_material(msgs_ordenadas, data_min=DATA_CORTE_MATERIAL):
    """Lista cronológica de snapshots de material em msgs Telegram (a partir de data_min).
    Cada snapshot = msg com qtd+unidade plausível, classificada em SOBRA/ENTRADA/ESTOQUE/SOLIC/?.
    Captura também produtos mencionados na msg e (data + autor + trecho)."""
    snaps = []
    for m in msgs_ordenadas:
        texto = m.get("content") or ""
        if not texto:
            continue
        if is_card_bot(texto):
            continue
        if "🎬" in texto or "🎙️" in texto:
            continue
        ts = (m.get("timestamp") or "")[:10]
        if not ts or ts < data_min:
            continue
        hits = list(PAD_QTD_KIT.finditer(texto))
        # Filtra qtds plausíveis (≤ 100, evita ruído)
        qtds = []
        for h in hits:
            try:
                n = int(h.group(1))
                if 1 <= n <= 100:
                    qtds.append({"qtd": n, "unidade": h.group(2).lower()})
            except Exception:
                pass
        if not qtds:
            continue
        # Classe (hierarquia: SOBRA > CONSUMO > SOLIC > ENTRADA > ESTOQUE > ?)
        if PAD_VERBO_SOBRA.search(texto):
            classe = "SOBRA"
        elif PAD_VERBO_CONSUMO.search(texto):
            classe = "CONSUMO"
        elif PAD_VERBO_SOLIC.search(texto):
            classe = "SOLIC"
        elif PAD_VERBO_ENTRADA.search(texto):
            classe = "ENTRADA"
        elif PAD_VERBO_ESTOQUE.search(texto):
            classe = "ESTOQUE"
        else:
            classe = "?"
        # Produtos mencionados (família canônica)
        prods_lit = set(p.upper() for p in re.findall(r"\b(stelion|lilit|leona|lumina|teron|kalahari|argento|primer|verniz|pu)\b", texto, re.IGNORECASE))
        prods_fam = sorted(set(PRODUTO_FAMILIA.get(p, p) for p in prods_lit))
        snaps.append({
            "data": ts,
            "autor": normalizar_sender(m.get("sender") or "?")[:40],
            "classe": classe,
            "qtds": qtds,
            "produtos": prods_fam,
            "trecho": texto[:240].replace("\n", " ").strip(),
        })
    snaps.sort(key=lambda x: x["data"])
    return snaps


def _ordinal_pra_int(s):
    s = (s or "").lower().strip()
    if s.startswith("1") or s == "primeira": return 1
    if s.startswith("2") or s == "segunda":  return 2
    if s.startswith("3") or s == "terceira": return 3
    if s.startswith("4") or s == "quarta":   return 4
    return None


PAD_SENDER_ROLE_CAMPO = re.compile(r"\b(aplicador|preparador|lider|líder|aplicadora)\b", re.IGNORECASE)


def is_aplicador_telegram(sender, aplicadores_set):
    """is_aplicador relaxado · aceita também senders cujo nome contém 'aplicador|preparador|lider'
    (formato Telegram do Painel: 'aplicador | William'). Esses são aplicadores externos não cadastrados
    em /equipe da obra."""
    if is_aplicador(sender, aplicadores_set):
        return True
    if sender and PAD_SENDER_ROLE_CAMPO.search(sender):
        return True
    return False


def detectar_camadas_aplicadas(msgs_ordenadas, aplicadores_set):
    """Detecta menções de aplicação de camada/demão de produto, ditas por aplicadores.
    Suporta 2 modos:
      - 'ordinal': ordinal explícito ('Segunda camada de stelion') · camada=N
      - 'inferida': aplicação sem ordinal ('Aplicação de primer', 'Verniz finalizado') · camada=1
    Filtra cards de bot, transcrições, admin pedindo foto.
    Dedup: pra cada (data + produto_familia), prefere ordinal sobre inferida.
    Inferida só entra se NÃO houver ordinal pro mesmo (data + produto_familia)."""
    ordinais = []
    inferidas = []
    for m in msgs_ordenadas:
        texto = m.get("content") or ""
        if not texto:
            continue
        if is_card_bot(texto):
            continue
        if "🎬" in texto or "🎙️" in texto:
            continue
        sender = m.get("sender") or ""
        if not is_aplicador_telegram(sender, aplicadores_set):
            continue
        data_msg = (m.get("timestamp") or "")[:10]
        autor = (m.get("sender") or "?")[:30]
        trecho = texto[:200].replace("\n", " ").strip()

        # Ordinal explícito
        for hit in PAD_CAMADA_PRODUTO.finditer(texto):
            cam_n = _ordinal_pra_int(hit.group(1))
            if not cam_n:
                continue
            produto_lit = hit.group(3).upper()
            produto_fam = PRODUTO_FAMILIA.get(produto_lit, produto_lit)
            ordinais.append({
                "data": data_msg, "autor": autor,
                "produto": produto_lit, "produto_familia": produto_fam,
                "camada": cam_n, "tipo": "ordinal", "trecho": trecho,
            })

        # Aplicação simples (sem ordinal) → camada 1 inferida
        for hit in PAD_APLICACAO_SIMPLES.finditer(texto):
            produto_lit = hit.group(1).upper()
            produto_fam = PRODUTO_FAMILIA.get(produto_lit, produto_lit)
            inferidas.append({
                "data": data_msg, "autor": autor,
                "produto": produto_lit, "produto_familia": produto_fam,
                "camada": 1, "tipo": "inferida", "trecho": trecho,
            })
        # Produto + finalizado/aplicado
        for hit in PAD_PRODUTO_FINALIZADO.finditer(texto):
            produto_lit = hit.group(1).upper()
            produto_fam = PRODUTO_FAMILIA.get(produto_lit, produto_lit)
            inferidas.append({
                "data": data_msg, "autor": autor,
                "produto": produto_lit, "produto_familia": produto_fam,
                "camada": 1, "tipo": "inferida", "trecho": trecho,
            })

    # Dedup ordinais: 1 por (data + produto_familia + camada)
    seen_ord = set()
    out_ord = []
    familias_com_ordinal = set()
    for a in ordinais:
        k = (a["data"], a["produto_familia"], a["camada"])
        if k in seen_ord: continue
        seen_ord.add(k)
        out_ord.append(a)
        familias_com_ordinal.add(a["produto_familia"])

    # Inferidas só entram se família NÃO tem ordinal (evita ruído)
    seen_inf = set()
    out_inf = []
    for a in inferidas:
        if a["produto_familia"] in familias_com_ordinal:
            continue
        k = (a["produto_familia"],)  # 1 inferida por família é suficiente
        if k in seen_inf: continue
        seen_inf.add(k)
        out_inf.append(a)

    out = out_ord + out_inf
    out.sort(key=lambda x: (x["data"], x["produto_familia"], x["camada"]))
    return out


def get_aplicadores_set(equipe_endpoint):
    """Set de primeiros nomes (lowercase) dos aplicadores oficiais (líder + aplicadores + preparadores)."""
    nomes = set()
    for p in (equipe_endpoint or {}).get("prestadores", []) or []:
        nome = (p.get("nome") or "").strip()
        funcao = (p.get("funcao") or "").upper()
        if not nome:
            continue
        if "LIDER" in funcao or "APLICADOR" in funcao or "PREPARADOR" in funcao:
            for token in re.split(r"\s+", nome):
                t = token.lower().strip()
                if len(t) >= 3:
                    nomes.add(t)
    return nomes


def is_aplicador(sender, aplicadores_set):
    """True se o sender Telegram é um aplicador oficial (matching de tokens)."""
    if not sender or not aplicadores_set:
        return False
    apl_lower = {a.lower() for a in aplicadores_set}
    s = sender.lower()
    if s in apl_lower:
        return True
    for token in re.split(r"[\s|]+", s):
        t = token.strip()
        if t and t in apl_lower:
            return True
    return False


def detectar_marcos_execucao(msgs_ordenadas, cluster_inicio, cluster_fim, aplicadores_set):
    """Detecta marcos técnicos da execução. Distingue:
    - inicio_dia: SÓ vale se vem de aplicador
    - cobranca_status: msg de NÃO-aplicador perguntando status, ANTES do início_dia daquele dia
    - cobrança ganha tempo_resposta_min (delta até próxima msg de aplicador)
    Demais marcos: regex normal · 1 por (data + tipo)."""
    if not cluster_inicio or not cluster_fim:
        return []
    ini_iso = cluster_inicio.isoformat()
    fim_iso = (cluster_fim + timedelta(days=2)).isoformat()

    # Filtra msgs da janela e remove cards de bot
    msgs_janela = []
    for m in msgs_ordenadas:
        data = (m.get("timestamp") or "")[:10]
        if not (ini_iso <= data <= fim_iso):
            continue
        if is_card_bot(m.get("content") or ""):
            continue
        if not (m.get("content") or "").strip():
            continue
        msgs_janela.append(m)

    marcos = []
    visto = set()
    inicio_dia_por_data = {}  # data → idx do marco no array (pra pesquisar depois)
    cobrancas_pendentes = []  # cobranças aguardando próxima msg de aplicador pra calcular tempo
    cobranca_diario_ontem = False  # flag: alguém pediu "diário de ontem" → próxima msg de aplicador é retroativa

    PAD_ONTEM = re.compile(r"\bontem\b", re.IGNORECASE)
    PAD_DIARIO_ONTEM = re.compile(r"\b(di[áa]rio\s+de\s+ontem|di[áa]rio\s+do\s+dia\s+anterior|o\s+que\s+(fizeram|fez|foi\s+feito)\s+ontem|temos\s+di[áa]rio\s+de\s+ontem)\b", re.IGNORECASE)

    for idx_m, m in enumerate(msgs_janela):
        ts = m.get("timestamp") or ""
        data = ts[:10]
        hora = ts[11:16]
        sender = (m.get("sender") or "?")[:30]
        texto = m.get("content") or ""
        eh_aplicador = is_aplicador(sender, aplicadores_set)

        # Resolve cobranças pendentes do dia: se essa msg é de aplicador, fecha cobrança
        if eh_aplicador and cobrancas_pendentes:
            for cob in list(cobrancas_pendentes):
                if cob["data"] != data:
                    cobrancas_pendentes.remove(cob)
                    continue
                try:
                    cob_ts = datetime.fromisoformat(cob["data_iso"].replace("Z", "+00:00"))
                    msg_ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    delta_min = int((msg_ts - cob_ts).total_seconds() / 60)
                    cob["tempo_resposta_min"] = delta_min
                    cob["respondido_por"] = sender
                    cob["respondido_em"] = hora
                except Exception:
                    pass
                cobrancas_pendentes.remove(cob)

        # Detecta cobrança de diário de ontem (não-aplicador pedindo)
        if not eh_aplicador and PAD_DIARIO_ONTEM.search(texto):
            cobranca_diario_ontem = True

        # Determina se esta msg se refere a "ontem" (retroativa)
        retroativa = False
        if eh_aplicador and (PAD_ONTEM.search(texto) or cobranca_diario_ontem):
            retroativa = True
            cobranca_diario_ontem = False  # consome a flag

        # Data efetiva: se retroativa, atribui ao dia anterior
        data_efetiva = data
        if retroativa:
            try:
                d = date.fromisoformat(data)
                data_efetiva = (d - timedelta(days=1)).isoformat()
            except ValueError:
                pass

        # Detecta marcos técnicos
        marco_detectado = None
        for tipo, pad in MARCOS_EXECUCAO:
            match = pad.search(texto)
            if match:
                # inicio_dia só vale pra aplicador
                if tipo == "inicio_dia" and not eh_aplicador:
                    continue
                # inicio_dia não faz sentido retroativo
                if tipo == "inicio_dia" and retroativa:
                    continue
                # inicio_dia descarta se "amanhã" aparece antes do match (fala do futuro, não do agora)
                if tipo == "inicio_dia" and re.search(r"\bamanh[aã]\b", texto[:match.start()], re.IGNORECASE):
                    continue
                chave = (data_efetiva, tipo)
                if chave in visto:
                    if tipo == "inicio_dia":
                        break
                    break
                visto.add(chave)
                marco_detectado = {
                    "data": data_efetiva,
                    "hora": hora if not retroativa else "retro",
                    "autor": sender,
                    "tipo": tipo,
                    "label": LABELS_EXECUCAO.get(tipo, tipo),
                    "trecho": texto[:200].replace("\n", " ").strip(),
                }
                if retroativa:
                    marco_detectado["retroativo"] = True
                marcos.append(marco_detectado)
                if tipo == "inicio_dia":
                    inicio_dia_por_data[data_efetiva] = len(marcos) - 1
                break

        # Se não detectou marco técnico E é não-aplicador E ainda não houve inicio_dia no dia → cobrança
        if not marco_detectado and not eh_aplicador and data not in inicio_dia_por_data:
            if PAD_COBRANCA.search(texto):
                chave = (data, "cobranca_status")
                if chave not in visto:
                    visto.add(chave)
                    cob = {
                        "data": data,
                        "data_iso": ts,
                        "hora": hora,
                        "autor": sender,
                        "tipo": "cobranca_status",
                        "label": LABELS_EXECUCAO["cobranca_status"],
                        "trecho": texto[:200].replace("\n", " ").strip(),
                        "tempo_resposta_min": None,
                        "respondido_por": None,
                        "respondido_em": None,
                    }
                    marcos.append(cob)
                    cobrancas_pendentes.append(cob)

    return marcos


def detectar_problemas_msg(msgs_ordenadas):
    """Detecta sinais de problema nas mensagens (regex)."""
    sinais = []
    vistos_data = set()
    for m in msgs_ordenadas:
        texto = m.get("content") or ""
        if PAD_PROBLEMA.search(texto):
            data = (m.get("timestamp") or "")[:10]
            chave = (data, (m.get("sender") or "?")[:20])
            if chave in vistos_data:
                continue
            vistos_data.add(chave)
            sinais.append({
                "data": data,
                "autor": normalizar_sender(m.get("sender") or "?")[:30],
                "trecho": texto[:200].replace("\n", " ").strip(),
            })
    return sinais


# ============================================================
# Equipe (cruza fontes)
# ============================================================

# Pessoas Monofloor conhecidas (do MAPA_PESSOAS) · usadas pra filtrar senders Telegram
# e inferir quem é equipe de campo (sender que NÃO é Monofloor)
PESSOAS_MONOFLOOR = {
    'wesley', 'luana', 'pedro', 'mayara', 'caroline', 'kassandra',
    'rodrigo', 'nathan', 'cauã', 'caua', 'eduarda', 'karine', 'júlio', 'julio',
    'francisco', 'thaísa', 'thaisa', 'vanessa', 'mariana', 'gabriel',
    'juliana', 'mateus', 'taporosky',
    # Braiam · era aplicador até 2025-12 · fiscal de qualidade desde 2026
    'braiam', 'braian',
    # Sistemas / bots / IA · NÃO classificar como aplicador (auditoria 2026-05-12)
    'kira',    # IA Monofloor que faz triagem · vista em TALLY, GUSTAVO, MANOELA, ÁUREO, YAHYA
    'bot',     # genérico
    'bridge',  # sistema/integração antiga em LEONARDO
    'q',       # "Q Assim Seja" em ÁUREO · provável cliente/grupo, não aplicador
    # Consultores Monofloor novos (auditoria 2026-05-12)
    'ketlyn',
    'maria',   # cobre "Maria Clara Monofloor" e similares
    'isabella', # apareceu como Monofloor em GETULIO
    'ana',     # cobre "Ana | Monofloor", etc
    'adriana',
    'jonathan', # bot/sistema que posta "Contrato assinado"
}
PAD_LABEL_MONOFLOOR = re.compile(
    r'\b(monofloor|opera[çc][õo]es|atendimento|qualidade|projetos|admin|comercial|consultor|financeiro|equipe\s+projetos|equipe\s+\|)',
    re.IGNORECASE
)

def is_sender_monofloor(sender_nome):
    """True se o sender é Monofloor (atendimento/operações/qualidade/etc) · excluir da equipe de campo."""
    if not sender_nome:
        return False
    s = sender_nome.lower()
    if PAD_LABEL_MONOFLOOR.search(s):
        return True
    # Bot/sistema em qualquer parte do nome · "Carlos (Bot)", "X · bot", "SomeBot", etc
    # FIX bug #1 · pega compostos como "CarlosBot", "BotSystem", "Kira", "Bridge"
    if re.search(r"bot(?:\s|\)|$)|\bbot\b|\bkira\b|\bbridge\b", s, re.IGNORECASE):
        return True
    # Pega o primeiro nome (antes de "|" ou espaço)
    primeiro = re.split(r'[\s|]+', s)[0].strip()
    if primeiro in PESSOAS_MONOFLOOR:
        return True
    return False


def montar_equipe(detail, equipe_endpoint, msgs_ordenadas):
    """Cruza /equipe + detail (responsavel*) + senders das msgs Telegram."""
    monofloor = {
        "atendimento": detail.get("responsavelAtendimento"),
        "operacoes": detail.get("responsavelOperacoes"),
        "consultor": detail.get("consultorNome") if isinstance(detail.get("consultorNome"), str) else None,
        "vendedor": (detail.get("acessoDetalhes") or {}).get("vendedor"),
    }
    prestadores_oficiais = []
    for p in (equipe_endpoint or {}).get("prestadores", []) or []:
        prestadores_oficiais.append({
            "nome": p.get("nome"),
            "funcao": p.get("funcao"),
        })

    # Senders das msgs Telegram (top 15 por contagem · com aliases unificados)
    sender_count = Counter()
    sender_primeira = {}
    sender_ultima = {}
    for m in msgs_ordenadas:
        s_raw = (m.get("sender") or "").strip()
        if not s_raw or s_raw.lower() == "🎬 transcrição" or s_raw.lower() == "🎙️ transcrição":
            continue
        s = normalizar_sender(s_raw)
        sender_count[s] += 1
        ts = m.get("timestamp")
        if s not in sender_primeira:
            sender_primeira[s] = ts
        sender_ultima[s] = ts

    senders = []
    for s, n in sender_count.most_common(20):
        senders.append({
            "nome": s,
            "n_msgs": n,
            "primeira_msg": sender_primeira[s],
            "ultima_msg": sender_ultima[s],
        })

    # Inferir equipe de campo dos senders Telegram quando /equipe veio vazio
    # Filtra senders Monofloor (atendimento, operações, qualidade) · sobra a equipe de campo
    # FIX bug #1 · bots como aplicador · filtro explícito de nomes conhecidos de bots/sistemas
    _NOMES_BOT = re.compile(r"\bkira\b|bot\b|bot$|\bmonofloor\b|\bbridge\b|\bsistema\b", re.IGNORECASE)
    aplicadores_telegram = []
    for s in senders:
        if is_sender_monofloor(s["nome"]):
            continue
        # Filtro extra: nomes que contenham "bot", "kira", "monofloor" não são aplicadores
        if _NOMES_BOT.search(s["nome"]):
            continue
        # Só considera "aplicador real" se tem volume mínimo (5+ msgs · evita ruído)
        if s["n_msgs"] >= 5:
            aplicadores_telegram.append({
                "nome": s["nome"],
                "n_msgs": s["n_msgs"],
                "primeira_msg": s["primeira_msg"],
                "ultima_msg": s["ultima_msg"],
            })

    return {
        "monofloor": monofloor,
        "prestadores_oficiais": prestadores_oficiais,
        "senders_telegram": senders,
        "aplicadores_telegram": aplicadores_telegram,
    }


# ============================================================
# Padrões observados
# ============================================================

def detectar_ciclos(marcos, fases, data_1a_msg, data_ultima_msg):
    """Divide a jornada em ciclos · separados por aprovacao_cliente seguida de reprovacao_retorno.
    Cada ciclo tem início, fim, fases e marcos próprios. Obra sem reprovação = 1 ciclo único."""
    if not marcos or not data_1a_msg or not data_ultima_msg:
        return []

    aprovacoes = [m for m in marcos if m.get("tipo") == "aprovacao_cliente"]
    reprovacoes = [m for m in marcos if m.get("tipo") == "reprovacao_retorno"]

    # Sem reprovação · 1 ciclo só · não devolve nada (UI usa fases/marcos atuais)
    if not reprovacoes:
        return []

    ciclos = []
    cursor_inicio = data_1a_msg

    # Pra cada aprovação, fecha um ciclo · próxima reprovação abre o próximo
    for i, aprov in enumerate(aprovacoes):
        data_aprov = aprov["data"]
        if data_aprov < cursor_inicio:
            continue  # aprovação antes do cursor (já contada)
        nome_ciclo = f"Ciclo {len(ciclos)+1} · entrega" if len(ciclos) == 0 else f"Ciclo {len(ciclos)+1} · retrabalho"
        ciclos.append(_recortar_ciclo(nome_ciclo, cursor_inicio, data_aprov, fases, marcos))
        # Próxima reprovação após essa aprovação inicia novo ciclo
        proxima = next((r for r in reprovacoes if r["data"] > data_aprov), None)
        if proxima:
            cursor_inicio = proxima["data"]
        else:
            cursor_inicio = None
            break

    # Ciclo em aberto · há reprovação após última aprovação (ou obra nunca aprovou)
    if cursor_inicio:
        nome = f"Ciclo {len(ciclos)+1} · retrabalho em andamento"
        ciclos.append(_recortar_ciclo(nome, cursor_inicio, data_ultima_msg, fases, marcos))
    elif not aprovacoes:
        # Obra com reprovações mas sem nenhuma aprovação ainda
        ciclos.append(_recortar_ciclo("Ciclo 1 · em andamento", data_1a_msg, data_ultima_msg, fases, marcos))

    return ciclos


def _recortar_ciclo(nome, dt_ini, dt_fim, fases, marcos):
    """Filtra fases e marcos que caem dentro do intervalo do ciclo."""
    fases_ciclo = []
    for f in fases or []:
        f_ini, f_fim = f.get("inicio"), f.get("fim")
        if not f_ini or not f_fim:
            continue
        # Inclui fase se TEM SOBREPOSIÇÃO com o intervalo do ciclo
        if f_fim < dt_ini or f_ini > dt_fim:
            continue
        # Recorta fase pra caber no ciclo
        f_recortada = dict(f)
        if f_ini < dt_ini:
            f_recortada["inicio"] = dt_ini
        if f_fim > dt_fim:
            f_recortada["fim"] = dt_fim
        # Recalcula duração
        try:
            d_ini = datetime.fromisoformat(f_recortada["inicio"]).date()
            d_fim = datetime.fromisoformat(f_recortada["fim"]).date()
            f_recortada["duracao_dias"] = max(1, (d_fim - d_ini).days + 1)
        except Exception:
            pass
        fases_ciclo.append(f_recortada)

    marcos_ciclo = [m for m in marcos or [] if dt_ini <= m.get("data", "") <= dt_fim]

    # Duração total do ciclo em dias
    try:
        d1 = datetime.fromisoformat(dt_ini).date()
        d2 = datetime.fromisoformat(dt_fim).date()
        duracao = (d2 - d1).days + 1
    except Exception:
        duracao = None

    return {
        "nome": nome,
        "inicio": dt_ini,
        "fim": dt_fim,
        "duracao_dias": duracao,
        "fases": fases_ciclo,
        "marcos": marcos_ciclo,
    }


SEVERIDADE_PESO = {"critica": 4, "alta": 3, "media": 2, "baixa": 1}

def calcular_friccao_nivel(ocorrencias):
    """Retorna nível de fricção: critico/alto/medio/baixo/nenhum."""
    if not ocorrencias:
        return "nenhum"
    score = sum(SEVERIDADE_PESO.get((o.get("severidade") or "").lower(), 1) for o in ocorrencias)
    sev_max = max((SEVERIDADE_PESO.get((o.get("severidade") or "").lower(), 1) for o in ocorrencias), default=0)
    if sev_max >= 4 or score >= 12:
        return "critico"
    if sev_max >= 3 or score >= 8:
        return "alto"
    if score >= 4:
        return "medio"
    return "baixo"


def classificar_obra(jornada):
    """Selo de como a obra terminou/está. Usado pra filtrar e comparar cross-obra."""
    status = (jornada.get("status") or "").lower()
    fase = (jornada.get("fase_atual_painel") or "").upper()
    ciclos = jornada.get("ciclos", [])
    n_ciclos = len(ciclos) if ciclos else 1
    marcos = jornada.get("marcos", [])
    tem_reprovacao = any(m.get("tipo") == "reprovacao_retorno" for m in marcos)

    if status == "cancelado":
        return "cancelada"
    if status == "pausado":
        return "pausada"
    if status in ("reparo", "marcas_rolo_cera"):
        return "retrabalho_ativo"
    if status in ("finalizado", "concluido"):
        return "entrega_com_retrabalho" if (n_ciclos >= 2 or tem_reprovacao) else "entrega_limpa"

    # Fase do painel diz finalizada mas status ficou stale
    if ("FINALIZADO" in fase or "CONCLU" in fase) and status in (
        "em_execucao", "aguardando_execucao", "aguardando_clima", "planejamento", "contrato",
    ):
        return "entrega_com_retrabalho" if (n_ciclos >= 2 or tem_reprovacao) else "entrega_limpa"

    if status == "em_execucao":
        return "em_execucao_com_retrabalho" if tem_reprovacao else "em_execucao"
    if status in ("aguardando_execucao", "aguardando_clima"):
        return "aguardando_execucao"
    if status in ("planejamento", "contrato"):
        return "pre_obra"
    return "desconhecido"


LABELS_CLASSIFICACAO = {
    "entrega_limpa":              "Entrega limpa",
    "entrega_com_retrabalho":     "Entrega com retrabalho",
    "retrabalho_ativo":           "Retrabalho ativo",
    "em_execucao":                "Em execução",
    "em_execucao_com_retrabalho": "Em execução (retrabalho)",
    "aguardando_execucao":        "Aguardando execução",
    "pre_obra":                   "Pré-obra",
    "pausada":                    "Pausada",
    "cancelada":                  "Cancelada",
    "desconhecido":           "—",
}


def classificar_origem_retrabalho(jornada):
    """Se obra tem retrabalho, classifica se a aplicacao original foi no ano corrente ou anterior."""
    classif = jornada.get("classificacao", "")
    eh_retrab = "retrabalho" in classif
    if not eh_retrab:
        return None
    ciclos = jornada.get("ciclos", [])
    if not ciclos:
        return "incerto"
    fases_c1 = ciclos[0].get("fases", [])
    if not fases_c1:
        return "incerto"
    c1_inicio = fases_c1[0].get("inicio")
    if not c1_inicio:
        return "incerto"
    ano_atual = str(HOJE_DATE.year)
    return "recente" if c1_inicio[:4] == ano_atual else "heranca"


def extrair_severidade_max(ocorrencias):
    """Retorna a severidade máxima dentre as ocorrências formais."""
    ORDEM = {"critica": 4, "alta": 3, "media": 2, "baixa": 1}
    best = 0
    best_label = None
    for o in ocorrencias:
        sev = (o.get("severidade") or "").lower()
        if ORDEM.get(sev, 0) > best:
            best = ORDEM[sev]
            best_label = sev
    return best_label


def extrair_regiao(endereco):
    """Extrai UF/cidade do endereço pra agrupamento cross-obra."""
    if not endereco or endereco == "—":
        return None
    end = endereco.upper()
    import re as _re
    m = _re.search(r"([A-ZÀ-Ú\s]+)/([A-Z]{2})", end)
    if m:
        return f"{m.group(1).strip()}/{m.group(2)}"
    for uf in ["SP", "RJ", "MG", "PR", "SC", "RS", "BA", "DF", "GO", "CE", "PE"]:
        if f"/{uf}" in end or f", {uf}" in end or f"-{uf}" in end:
            return uf
    return None


def montar_resumo_cross(jornada):
    """Campos normalizados pra análise cross-obra (filtros, agrupamentos, comparações)."""
    ciclos = jornada.get("ciclos", [])
    n_ciclos = len(ciclos) if ciclos else 1
    marcos = jornada.get("marcos", [])
    ocorrencias = jornada.get("friccao", {}).get("ocorrencias_formais", [])
    equipe = jornada.get("equipe", {})
    monof = equipe.get("monofloor", {})

    reprovacoes = [m for m in marcos if m.get("tipo") == "reprovacao_retorno"]
    subtipos_repr = [m.get("subtipo") for m in marcos
                     if m.get("tipo") == "reprovacao_retorno" and m.get("subtipo")]

    tipo_retrabalho = None
    if n_ciclos >= 2:
        # FIX bug #3 · reconhece subtipos novos (problema_verniz, problema_marcas, problema_cor, problema_refazer)
        tem_verniz = any("verniz" in (s or "") for s in subtipos_repr)
        tem_marcas = any("marcas" in (s or "") for s in subtipos_repr)
        tem_cor = any("cor" in (s or "") for s in subtipos_repr)
        tem_completa = any("completa" in (s or "") or "refazer" in (s or "") for s in subtipos_repr)
        categorias = sum([tem_verniz, tem_marcas, tem_cor, tem_completa])
        if categorias >= 2:
            tipo_retrabalho = "mista"
        elif tem_verniz:
            tipo_retrabalho = "verniz"
        elif tem_marcas:
            tipo_retrabalho = "marcas"
        elif tem_cor:
            tipo_retrabalho = "cor"
        elif tem_completa:
            tipo_retrabalho = "completa"
        else:
            tipo_retrabalho = "nao_classificado"

    prestadores = equipe.get("prestadores_oficiais", [])
    lider = next((p.get("nome") for p in prestadores if (p.get("funcao") or "").upper() == "LIDER"), None)
    if not lider:
        aplicadores = equipe.get("aplicadores_telegram", [])
        if aplicadores:
            lider = max(aplicadores, key=lambda a: a.get("n_msgs", 0)).get("nome")

    return {
        "classificacao": jornada.get("classificacao"),
        "qtd_ciclos": n_ciclos,
        "tem_retrabalho": n_ciclos >= 2 or any(m.get("tipo") == "reprovacao_retorno" for m in marcos),
        "tipo_retrabalho": tipo_retrabalho,
        "consultor": monof.get("consultor") or monof.get("operacoes"),
        "operacoes": monof.get("operacoes"),
        "lider_campo": lider,
        "severidade_max": extrair_severidade_max(ocorrencias),
        "qtd_ocorrencias": len(ocorrencias),
        "qtd_marcos": len(marcos),
        "produto_principal": (jornada.get("produtos") or ["—"])[0] if jornada.get("produtos") else None,
        "regiao": extrair_regiao(jornada.get("endereco")),
        "metragem": jornada.get("metragem"),
    }


def detectar_padroes(jornada):
    padroes = []
    ciclos = jornada.get("ciclos", [])
    n_ciclos = len(ciclos) if ciclos else 1
    marcos = jornada.get("marcos", [])
    ocorrencias = jornada.get("friccao", {}).get("ocorrencias_formais", [])
    problemas = jornada.get("friccao", {}).get("sinais_msg_telegram", [])

    # Hibernação longa
    if jornada["tempo_hibernacao_dias"] and jornada["tempo_hibernacao_dias"] >= 60:
        padroes.append(f"hibernacao_longa · obra ficou {jornada['tempo_hibernacao_dias']}d praticamente parada")

    # Execução concentrada (< 5% do tempo total)
    if jornada["tempo_execucao_dias"] and jornada["tempo_total_dias"]:
        pct = jornada["tempo_execucao_dias"] / jornada["tempo_total_dias"] * 100
        if pct < 5:
            padroes.append(f"execucao_concentrada · só {pct:.1f}% do tempo total ({jornada['tempo_execucao_dias']}d de {jornada['tempo_total_dias']}d)")

    # Mudança de escopo durante execução
    if jornada.get("solicitacoes_material") and any(s.get("tela_total") for s in jornada["solicitacoes_material"]):
        padroes.append("mudanca_escopo_dia_execucao · cliente pediu tela total durante execução")

    # Retrabalho recorrente (2+ ciclos)
    if n_ciclos >= 2:
        tipo_r = jornada.get("resumo_cross", {}).get("tipo_retrabalho", "")
        padroes.append(f"retrabalho_{n_ciclos}_ciclos · tipo: {tipo_r or 'a classificar'}")

    # Cliente sumido (3+ falhas de comunicação)
    falhas_com = [o for o in ocorrencias if o.get("tipo") == "falha_comunicacao"]
    if len(falhas_com) >= 3:
        padroes.append(f"cliente_sumido · {len(falhas_com)} ocorrências de falha de comunicação")

    # Pressão de prazo verbalizada
    PRESSAO_KW = ["prazo apertado", "não tem mais tempo", "sem margem", "prazo curto",
                   "urgente", "não tem tempo", "correndo contra o tempo", "apertado"]
    hits_pressao = 0
    for p in problemas:
        trecho = (p.get("trecho") or "").lower()
        if any(kw in trecho for kw in PRESSAO_KW):
            hits_pressao += 1
    for m in marcos:
        trecho = (m.get("trecho") or "").lower()
        if any(kw in trecho for kw in PRESSAO_KW):
            hits_pressao += 1
    if hits_pressao:
        padroes.append(f"pressao_prazo_verbalizada · {hits_pressao} sinais detectados nas msgs")

    # VT qualidade tardia (>60d pós-execução)
    vts = [m for m in marcos if m.get("tipo") == "relatorio_vt_qualidade"]
    exec_ref = jornada.get("data_exec_confirmada") or jornada.get("data_exec_prevista")
    if vts and exec_ref:
        for vt in vts:
            vt_d = vt.get("data")
            if vt_d and vt_d > exec_ref:
                try:
                    delta = (datetime.strptime(vt_d, "%Y-%m-%d") - datetime.strptime(exec_ref, "%Y-%m-%d")).days
                    if delta > 60:
                        padroes.append(f"vt_qualidade_tardia · {delta}d após execução")
                        break
                except ValueError:
                    pass

    # Troca de equipe entre ciclos (senders diferentes por fase)
    if n_ciclos >= 2 and len(ciclos) >= 2:
        def _senders_ciclo(c):
            return {m.get("autor") for m in c.get("marcos", []) if m.get("autor")}
        s1 = _senders_ciclo(ciclos[0])
        for c in ciclos[1:]:
            sn = _senders_ciclo(c)
            if sn and s1 and not sn & s1:
                padroes.append("troca_equipe_entre_ciclos · equipe diferente no retrabalho")
                break

    # Alta densidade de ocorrências (>= 8)
    if len(ocorrencias) >= 8:
        padroes.append(f"alta_friccao · {len(ocorrencias)} ocorrências formais registradas")

    return padroes


# ============================================================
# Cruzamento andamento: Telegram (nosso) × Painel (manual)
# ============================================================

# Mapeamento: tipo de marco_execucao → etapa do andamento_obra no Painel
MARCO_PARA_ETAPA = {
    "preparacao":        ["Proteção", "Limpeza"],
    "aplicacao_primer":  ["Preparo de juntas/Primer", "Preparo das juntas/Primer"],
    "aplicacao_tela":    ["Massa nas juntas"],
    "lixamento":         ["Lixamento 1", "Lixamento 2", "Lixamento 3", "Lixamento 4"],
    "camada_1":          ["1ª Camada"],
    "camada_2":          ["2ª Camada"],
    "camada_3":          ["3ª Camada"],
    "aplicacao_stelion": ["1ª Camada", "2ª Camada", "3ª Camada"],
    "aplicacao_lilit":   ["1ª Camada", "2ª Camada", "3ª Camada"],
    "reparo":            [],
    "verniz_iniciado":   ["Verniz"],
    "verniz_finalizado": ["Verniz"],
    "obra_finalizada":   [],
    "aplicacao_teron":   ["Selador"],
}

ETAPAS_ORDENADAS = [
    "Limpeza", "Proteção", "Preparo de juntas/Primer",
    "Massa nas juntas", "Selador",
    "1ª Camada", "2ª Camada", "3ª Camada", "4ª Camada",
    "Lixamento 1", "Lixamento 2", "Lixamento 3", "Lixamento 4",
    "Verniz",
]

SINONIMOS_ETAPA = {
    "Preparo das juntas/Primer": "Preparo de juntas/Primer",
}


def cruzar_andamento(detail, marcos_execucao):
    """Cruza andamento detectado no Telegram com checklist manual do Painel.
    Retorna dict com etapas, datas, e status de cada cruzamento."""
    # 1. Andamento do Painel (checklist manual)
    all_fields = (detail.get("acessoDetalhes") or {}).get("allFields") or {}
    andamento_painel = all_fields.get("andamento_obra") or all_fields.get("copy_of_andamento_obra_piso") or []
    if isinstance(andamento_painel, str):
        try:
            parsed = json.loads(andamento_painel)
            if isinstance(parsed, list):
                andamento_painel = [str(s).strip() for s in parsed if s]
            else:
                andamento_painel = [s.strip() for s in andamento_painel.split(",") if s.strip()]
        except (json.JSONDecodeError, ValueError):
            andamento_painel = [s.strip() for s in andamento_painel.split(",") if s.strip()]
    andamento_painel = [SINONIMOS_ETAPA.get(s, s) for s in andamento_painel]
    painel_set = set(andamento_painel)

    # 2. Andamento do Telegram (nosso, com datas)
    telegram_etapas = {}  # etapa → {data, hora, autor, tipo_marco}
    for m in (marcos_execucao or []):
        tipo = m.get("tipo", "")
        etapas_correspondentes = MARCO_PARA_ETAPA.get(tipo, [])
        for etapa_raw in etapas_correspondentes:
            etapa = SINONIMOS_ETAPA.get(etapa_raw, etapa_raw)
            if etapa not in telegram_etapas:
                telegram_etapas[etapa] = {
                    "data": m.get("data"),
                    "hora": m.get("hora"),
                    "autor": m.get("autor"),
                    "tipo_marco": tipo,
                }
    telegram_set = set(telegram_etapas.keys())

    # 3. Cruzamento
    todas_etapas = set(ETAPAS_ORDENADAS) | painel_set | telegram_set
    resultado = []
    for etapa in ETAPAS_ORDENADAS:
        if etapa not in todas_etapas:
            continue
        no_painel = etapa in painel_set
        no_telegram = etapa in telegram_set
        if no_painel and no_telegram:
            status_cruz = "confirmado"
        elif no_telegram and not no_painel:
            status_cruz = "detectado_sem_painel"
        elif no_painel and not no_telegram:
            status_cruz = "painel_sem_deteccao"
        else:
            status_cruz = "pendente"
        item = {
            "etapa": etapa,
            "status": status_cruz,
            "painel": no_painel,
            "telegram": no_telegram,
        }
        if no_telegram:
            item["data_detectada"] = telegram_etapas[etapa]["data"]
            item["hora_detectada"] = telegram_etapas[etapa]["hora"]
            item["autor"] = telegram_etapas[etapa]["autor"]
        resultado.append(item)

    # Etapas do Painel que não estão na lista ordenada (custom)
    for etapa in sorted(painel_set - set(ETAPAS_ORDENADAS)):
        resultado.append({
            "etapa": etapa,
            "status": "painel_sem_deteccao" if etapa not in telegram_set else "confirmado",
            "painel": True,
            "telegram": etapa in telegram_set,
        })

    n_confirmado = sum(1 for r in resultado if r["status"] == "confirmado")
    n_detectado = sum(1 for r in resultado if r["status"] == "detectado_sem_painel")
    n_painel_only = sum(1 for r in resultado if r["status"] == "painel_sem_deteccao")
    n_pendente = sum(1 for r in resultado if r["status"] == "pendente")

    return {
        "etapas": resultado,
        "andamento_painel": andamento_painel,
        "resumo": {
            "confirmado": n_confirmado,
            "detectado_sem_painel": n_detectado,
            "painel_sem_deteccao": n_painel_only,
            "pendente": n_pendente,
            "total_etapas": len(resultado),
        },
    }


_PAD_FAMILIA_OS = re.compile(r"\b(STELION|LILIT|LEONA|TERON|LUMINA|PRIMER|SELADOR|PU)\b", re.IGNORECASE)

RENDIMENTO_ESPERADO = {
    "STELION": 4.0,
    "LILIT": 5.0,
    "LEONA": 4.0,
    "LUMINA": 12.0,
    "PRIMER": 15.0,
    "SELADOR": 12.0,
}

def _parse_qtd_os(s):
    """Converte string de quantidade da OS para float.
    Formatos aceitos: "18,00", "18.00", "18", "1.500,00", "18 un", espaços extras."""
    if not s:
        return 0.0
    txt = str(s).strip()
    # Remove sufixos de unidade (un, kg, lt, pç, m², etc.)
    txt = re.sub(r"\s*(un|kg|lt|pç|pc|m2|m²|cx|gl|bd|rl|sc)\s*$", "", txt, flags=re.IGNORECASE).strip()
    if not txt:
        return 0.0
    # Detecta formato brasileiro 1.500,00 (ponto milhar, vírgula decimal)
    if re.match(r"^\d{1,3}(\.\d{3})+(,\d+)?$", txt):
        txt = txt.replace(".", "").replace(",", ".")
    else:
        # Formato simples: troca vírgula por ponto decimal
        txt = txt.replace(",", ".")
    # Remove caracteres não-numéricos remanescentes (exceto ponto)
    txt = re.sub(r"[^\d.]", "", txt)
    try:
        return float(txt) if txt else 0.0
    except ValueError:
        return 0.0


def _familia_do_material_os(nome_material):
    if not nome_material:
        return None
    hit = _PAD_FAMILIA_OS.search(nome_material)
    if not hit:
        return None
    lit = hit.group(1).upper()
    return PRODUTO_FAMILIA.get(lit, lit)


def calcular_consistencia_material(jornada):
    """Camada 2: cruza material enviado (OS Industria) x consumo (Telegram) x metragem.
    Retorna dict com resumo por familia de produto + veredito de consistencia."""
    metragem = jornada.get("metragem")
    envios = jornada.get("materiais_enviados") or []
    consumos = jornada.get("consumos") or []
    snapshots = jornada.get("snapshots_material") or []
    sobras = jornada.get("sobras") or []

    enviado = {}
    for envio in envios:
        for mat in envio.get("materiais") or []:
            fam = _familia_do_material_os(mat.get("material"))
            if not fam:
                continue
            qtd = _parse_qtd_os(mat.get("quantidade"))
            if qtd <= 0:
                continue
            enviado[fam] = enviado.get(fam, 0) + qtd

    consumido = {}
    for c in consumos:
        fam = c.get("produto_familia")
        if not fam:
            continue
        try:
            qtd = int(c["qtd"])
        except (ValueError, TypeError, KeyError):
            continue
        if 1 <= qtd <= 100:
            consumido[fam] = consumido.get(fam, 0) + qtd

    for snap in snapshots:
        if snap.get("classe") != "CONSUMO":
            continue
        prods = snap.get("produtos") or []
        qtds = snap.get("qtds") or []
        total_snap = sum(q.get("qtd", 0) for q in qtds)
        if total_snap <= 0 or not prods:
            continue
        por_prod = total_snap / len(prods)
        for p in prods:
            consumido[p] = consumido.get(p, 0) + por_prod

    sobra_total = {}
    for s in sobras:
        fam = s.get("produto_familia")
        if not fam:
            continue
        try:
            qtd = int(s["qtd"])
        except (ValueError, TypeError, KeyError):
            continue
        if 1 <= qtd <= 100:
            sobra_total[fam] = sobra_total.get(fam, 0) + qtd

    todas_familias = sorted(set(list(enviado.keys()) + list(consumido.keys())))
    if not todas_familias:
        return None

    produtos = []
    alertas = []
    for fam in todas_familias:
        env = enviado.get(fam, 0)
        cons = round(consumido.get(fam, 0))
        sob = sobra_total.get(fam, 0)
        rend = RENDIMENTO_ESPERADO.get(fam)
        esperado = round(metragem / rend) if (metragem and rend) else None

        veredito = None
        if env > 0 and cons > 0:
            ratio = cons / env
            if ratio > 1.2:
                veredito = "consumo_acima"
                alertas.append(f"{fam}: consumiu {cons} vs enviou {env}")
            elif ratio < 0.6:
                veredito = "sobra_provavel"
            else:
                veredito = "compativel"
        elif env > 0 and cons == 0:
            veredito = "sem_registro_consumo"
        elif env == 0 and cons > 0:
            veredito = "sem_os_industria"

        produtos.append({
            "familia": fam,
            "enviado": env,
            "consumido": cons,
            "sobra_declarada": sob,
            "esperado_m2": esperado,
            "veredito": veredito,
        })

    n_compat = sum(1 for p in produtos if p["veredito"] == "compativel")
    n_alerta = sum(1 for p in produtos if p["veredito"] in ("consumo_acima", "sobra_provavel"))
    nivel = "ok" if n_alerta == 0 else "atencao" if n_alerta <= 1 else "critico"

    return {
        "produtos": produtos,
        "alertas": alertas,
        "nivel": nivel,
        "tem_os": bool(enviado),
        "tem_consumo_telegram": bool(consumido),
        "tem_metragem": bool(metragem),
    }


STATUS_ENCERRADOS = {"finalizado", "concluido", "cancelado"}

def calcular_score_risco(jornada):
    """Score preditivo 0-100 pra obras ATIVAS. Quanto maior, mais atenção precisa.
    Retorna None pra obras já encerradas."""
    status = (jornada.get("status") or "").lower()
    if status in STATUS_ENCERRADOS:
        return None

    sinais = []
    score = 0

    # 1 · Silêncio no Telegram (dias sem msg)
    ultima_msg = jornada.get("data_ultima_msg")
    if ultima_msg:
        try:
            delta = (HOJE_DATE - datetime.strptime(ultima_msg[:10], "%Y-%m-%d").date()).days
        except (ValueError, TypeError):
            delta = 0
        if delta >= 30:
            score += 30
            sinais.append(f"silencio_{delta}d")
        elif delta >= 14:
            score += 20
            sinais.append(f"silencio_{delta}d")
        elif delta >= 7:
            score += 10
            sinais.append(f"silencio_{delta}d")
    else:
        score += 15
        sinais.append("sem_msg_telegram")

    # 2 · Postergações detectadas nos marcos
    marcos = jornada.get("marcos", [])
    n_postergacoes = sum(1 for m in marcos if m.get("tipo") == "postergacao")
    if n_postergacoes >= 3:
        score += 20
        sinais.append(f"postergacoes_{n_postergacoes}")
    elif n_postergacoes >= 1:
        score += 10
        sinais.append(f"postergacoes_{n_postergacoes}")

    # 3 · Reprovações sem resolução (obra ativa com reprovação = risco)
    tem_reprovacao = any(m.get("tipo") == "reprovacao_retorno" for m in marcos)
    if tem_reprovacao:
        score += 15
        sinais.append("reprovacao_ativa")

    # 4 · Fricção alta sem resolução
    fric_nivel = (jornada.get("friccao", {}).get("nivel") or "").lower()
    if fric_nivel in ("critica", "alta"):
        score += 15
        sinais.append(f"friccao_{fric_nivel}")
    elif fric_nivel == "media":
        score += 5
        sinais.append("friccao_media")

    # 5 · Tempo de execução acima da mediana da faixa (benchmark)
    bench = jornada.get("benchmark_faixa")
    if bench and bench.get("comparativo"):
        ratio_exec = bench["comparativo"].get("exec_vs_mediana", 1.0)
        if ratio_exec >= 2.0:
            score += 15
            sinais.append(f"exec_{ratio_exec:.1f}x_mediana")
        elif ratio_exec >= 1.5:
            score += 10
            sinais.append(f"exec_{ratio_exec:.1f}x_mediana")

    # 6 · Status stale (painel diz fase avançada mas status ficou pra trás)
    fase = (jornada.get("fase_atual_painel") or "").upper()
    if ("FINALIZADO" in fase or "CONCLU" in fase) and status not in STATUS_ENCERRADOS:
        score += 10
        sinais.append("status_stale")

    nivel = "critico" if score >= 60 else "alto" if score >= 40 else "medio" if score >= 20 else "baixo"
    return {
        "score": min(score, 100),
        "nivel": nivel,
        "sinais": sinais,
    }


def gerar_veredito(jornada):
    """Parágrafo-resumo determinístico da jornada. O que a diretoria lê."""
    cliente = jornada["cliente"]
    total_d = jornada.get("tempo_total_dias")
    exec_d = jornada.get("tempo_execucao_dias")
    ciclos = jornada.get("ciclos", [])
    n_ciclos = len(ciclos) if ciclos else 1
    classif = jornada.get("classificacao", "")
    ocorrencias = jornada.get("friccao", {}).get("ocorrencias_formais", [])
    padroes = jornada.get("padroes", [])
    status = (jornada.get("status") or "").lower()
    marcos = jornada.get("marcos", [])

    partes = []

    # Frase 1: resumo temporal + classificação
    if classif in ("entrega_limpa", "entrega_com_retrabalho"):
        if total_d:
            partes.append(f"Obra finalizada em {total_d} dias")
        else:
            partes.append("Obra finalizada")
        if exec_d:
            partes.append(f" com {exec_d} dias de execução real.")
        else:
            partes.append(".")
    elif classif == "retrabalho_ativo":
        partes.append(f"Obra com retrabalho ativo")
        if total_d:
            partes.append(f", {total_d} dias desde o início.")
        else:
            partes.append(".")
    elif classif == "em_execucao":
        partes.append("Obra em execução no momento.")
    elif classif == "pre_obra":
        partes.append("Obra em fase de planejamento/pré-execução.")
    elif classif == "pausada":
        partes.append("Obra pausada.")
    elif classif == "cancelada":
        partes.append("Obra cancelada.")
    else:
        partes.append("Obra em andamento.")

    # Frase 2: retrabalho
    if n_ciclos >= 2:
        tipo_r = jornada.get("resumo_cross", {}).get("tipo_retrabalho", "")
        label_r = {"verniz": "reaplicação de verniz", "completa": "reaplicação completa",
                    "mista": "reaplicação mista (verniz + base)", "nao_classificado": "retrabalho"}.get(tipo_r, "retrabalho")
        partes.append(f" Passou por {n_ciclos} ciclos — {label_r}.")

    # Frase 3: problema principal (ocorrência mais grave)
    criticas = [o for o in ocorrencias if (o.get("severidade") or "").lower() == "critica"]
    altas = [o for o in ocorrencias if (o.get("severidade") or "").lower() == "alta"]
    if criticas:
        partes.append(f" {len(criticas)} ocorrência(s) crítica(s): {criticas[0].get('titulo', '—')[:80]}.")
    elif altas:
        partes.append(f" {len(altas)} ocorrência(s) de alta severidade.")

    # Frase 4: padrões que chamam atenção
    flags = []
    for p in padroes:
        if "cliente_sumido" in p:
            flags.append("cliente sem resposta")
        elif "pressao_prazo" in p:
            flags.append("pressão de prazo verbalizada")
        elif "troca_equipe" in p:
            flags.append("equipe trocada no retrabalho")
        elif "vt_qualidade_tardia" in p:
            flags.append("VT qualidade tardia")
    if flags:
        partes.append(f" Sinais: {', '.join(flags)}.")

    return "".join(partes).strip()


# ============================================================
# Geração da narrativa em prosa (markdown · template)
# ============================================================

def gerar_narrativa_md(j):
    """Gera markdown em prosa a partir do schema da jornada."""
    cliente = j["cliente"]
    eq = j["equipe"]
    monof = eq["monofloor"]
    md = []
    md.append(f"# 🎬 JORNADA · {cliente}")
    md.append("")
    md.append(f"> Reconstrução retrospectiva · só Telegram + endpoints estruturais do Painel · gerado em {j['gerado_em'][:10]}")
    md.append("")

    # Ficha técnica
    md.append("## 📋 Ficha técnica")
    md.append("")
    md.append("| Campo | Valor |")
    md.append("|---|---|")
    md.append(f"| Cliente | {cliente} |")
    md.append(f"| Endereço | {j.get('endereco','—')} |")
    md.append(f"| Metragem | {j.get('metragem','—')} m² |")
    md.append(f"| Produto | {', '.join(j.get('produtos',[])) or '—'} |")
    md.append(f"| Cor | {', '.join(j.get('cores',[])) or '—'} |")
    md.append(f"| 1ª msg Telegram | {j.get('data_1a_msg','—')} |")
    md.append(f"| Execução prevista | {j.get('data_exec_prevista','—')} |")
    md.append(f"| Execução confirmada | {j.get('data_exec_confirmada','—')} |")
    md.append(f"| **Tempo total contrato → entrega** | **{j.get('tempo_total_dias','—')} dias** |")
    md.append(f"| **Tempo de execução real** | **{j.get('tempo_execucao_dias','—')} dias** |")
    if j.get('tempo_hibernacao_dias'):
        md.append(f"| **Tempo em hibernação** | **{j['tempo_hibernacao_dias']} dias** |")
    classif = j.get("classificacao", "")
    label_classif = LABELS_CLASSIFICACAO.get(classif, classif)
    md.append(f"| **Classificação** | **{label_classif}** |")
    rc = j.get("resumo_cross", {})
    if rc.get("qtd_ciclos", 1) >= 2:
        md.append(f"| Ciclos | {rc['qtd_ciclos']} ({rc.get('tipo_retrabalho','—')}) |")
    md.append("")

    # Veredito
    if j.get("veredito"):
        md.append(f"> **{j['veredito']}**")
        md.append("")

    # Equipe
    md.append("## 👥 Elenco")
    md.append("")
    md.append("**Time Monofloor**")
    md.append("")
    md.append("| Função | Pessoa |")
    md.append("|---|---|")
    md.append(f"| Vendedor(a) | {monof.get('vendedor') or '—'} |")
    md.append(f"| Atendimento | {monof.get('atendimento') or '—'} |")
    md.append(f"| Operações | {monof.get('operacoes') or '—'} |")
    md.append(f"| Consultor formal | {monof.get('consultor') or '—'} |")
    md.append("")
    if eq.get("prestadores_oficiais"):
        md.append("**Equipe de campo (prestadores oficiais)**")
        md.append("")
        md.append("| Nome | Função |")
        md.append("|---|---|")
        for p in eq["prestadores_oficiais"]:
            md.append(f"| {p['nome']} | {p['funcao']} |")
        md.append("")
    if eq.get("senders_telegram"):
        md.append("**Atores no grupo Telegram (top 10 por volume)**")
        md.append("")
        md.append("| Nome | Msgs | 1ª aparição | Última |")
        md.append("|---|---:|---|---|")
        for s in eq["senders_telegram"][:10]:
            md.append(f"| {s['nome']} | {s['n_msgs']} | {(s['primeira_msg'] or '')[:10]} | {(s['ultima_msg'] or '')[:10]} |")
        md.append("")

    # Linha do tempo (fases)
    md.append("## 🗺 Linha do tempo")
    md.append("")
    if j.get("fases"):
        md.append("| Fase | Início | Fim | Duração | Msgs Telegram |")
        md.append("|---|---|---|---:|---:|")
        for f in j["fases"]:
            md.append(f"| **{f['nome']}** | {f['inicio']} | {f['fim']} | {f['duracao_dias']}d | {f['n_msgs']} |")
        md.append("")

    # Marcos
    md.append("## 📍 Marcos detectados nas mensagens")
    md.append("")
    if j.get("marcos"):
        for marco in j["marcos"][:20]:
            md.append(f"- **{marco['data']} · {marco['tipo']}** · _{marco['autor']}_: \"{marco['trecho'][:130]}\"")
        md.append("")
    else:
        md.append("_(sem marcos textuais detectados via regex)_")
        md.append("")

    # Materiais
    md.append("## 📦 Material")
    md.append("")
    mat = j.get("materiais", {})
    md.append("**Escopo formal (Painel `/materiais`):**")
    md.append("")
    md.append("| Campo | Valor |")
    md.append("|---|---|")
    md.append(f"| Total m² | {mat.get('total_m2','—')} |")
    md.append(f"| Stelion m² | {mat.get('stelion_m2','—')} |")
    md.append(f"| Lilit m² | {mat.get('lilit_m2','—')} |")
    md.append(f"| Ambientes | {mat.get('ambientes','—')} |")
    md.append(f"| Itens (linhas) | {mat.get('n_items','—')} |")
    if mat.get("n_reaplicacao"):
        md.append(f"| Itens em REAPLICAÇÃO | {mat['n_reaplicacao']} |")
    md.append("")
    if j.get("solicitacoes_material"):
        md.append(f"**Solicitações durante execução ({len(j['solicitacoes_material'])}):**")
        md.append("")
        for s in j["solicitacoes_material"][:10]:
            tag = " [TELA TOTAL]" if s.get("tela_total") else ""
            md.append(f"- **{s['data']}** · _{s['autor']}_{tag}: \"{s['trecho'][:140]}\"")
        md.append("")
    if j.get("consumos"):
        md.append(f"**Consumo registrado em msgs ({len(j['consumos'])}):**")
        md.append("")
        for c in j["consumos"][:10]:
            md.append(f"- {c['data']} · {c['qtd']} {c['unidade']} · _{c['autor']}_")
        md.append("")
    if j.get("sobras"):
        md.append(f"**Sobras mencionadas ({len(j['sobras'])}):**")
        md.append("")
        for s in j["sobras"][:5]:
            md.append(f"- {s['data']} · _{s['autor']}_: \"{s['trecho'][:120]}\"")
        md.append("")

    # Problemas / Fricção
    md.append("## ⚠ Pontos de fricção")
    md.append("")
    fr = j.get("friccao", {})
    if fr.get("ocorrencias_formais"):
        md.append(f"**Ocorrências formais (Painel `/ocorrencias` · {len(fr['ocorrencias_formais'])}):**")
        md.append("")
        for o in fr["ocorrencias_formais"][:10]:
            md.append(f"- **{o['data']}** [{o['severidade']}] {o['tipo']} · _{o['titulo']}_")
        md.append("")
    if fr.get("sinais_msg_telegram"):
        md.append(f"**Sinais de problema nas mensagens ({len(fr['sinais_msg_telegram'])}):**")
        md.append("")
        for s in fr["sinais_msg_telegram"][:8]:
            md.append(f"- **{s['data']}** · _{s['autor']}_: \"{s['trecho'][:140]}\"")
        md.append("")

    # Padrões
    md.append("## 🔍 Padrões observados")
    md.append("")
    if j.get("padroes"):
        for p in j["padroes"]:
            md.append(f"- {p}")
    else:
        md.append("_(sem padrões automáticos detectados)_")
    md.append("")

    return "\n".join(md)


# ============================================================
# Construção da jornada por obra
# ============================================================

def baixar_pdf(url_local: str) -> bytes | None:
    """Baixa PDF do storage local do Painel via /api/storage/..."""
    if not url_local or not url_local.startswith("/storage/"):
        return None
    full_url = "https://cliente.monofloor.cloud/api" + url_local
    try:
        req = urllib.request.Request(full_url, headers={"User-Agent": "lab-orion/1.0"})
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
            return r.read()
    except Exception:
        return None


def extrair_materiais_enviados(pdf_bytes: bytes) -> list:
    """Extrai a tabela 'Descrição dos materiais enviados' de uma OS Indústria.
    Schema esperado da tabela: Código | Quantidade | Material | Lote | Cor | Valor.
    Retorna lista de dicts (1 por linha de material). Vazio se não achar."""
    if not PDF_OK or not pdf_bytes:
        return []
    materiais = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables() or []
                for tab in tables:
                    # Procura linha "Descrição dos materiais enviados"
                    idx_header = None
                    for i, row in enumerate(tab):
                        joined = " ".join((c or "") for c in row).lower()
                        if "descri" in joined and ("material" in joined or "enviad" in joined):
                            idx_header = i
                            break
                    if idx_header is None:
                        continue
                    # A linha seguinte é o cabeçalho de colunas (Código | Quantidade | ...)
                    # Dados começam 2 linhas depois
                    # Detecta posição das colunas pelo cabeçalho real
                    header_row = tab[idx_header + 1] if idx_header + 1 < len(tab) else []
                    col_map = {}
                    for ci, hcel in enumerate(header_row):
                        h = (hcel or "").strip().lower()
                        if "digo" in h or h == "cod" or h == "código":
                            col_map["codigo"] = ci
                        elif "quant" in h or h == "qtd" or h == "qtde":
                            col_map["quantidade"] = ci
                        elif "material" in h or "descri" in h or "produto" in h:
                            col_map["material"] = ci
                        elif h == "lote":
                            col_map["lote"] = ci
                        elif h == "cor" or h == "cores":
                            col_map["cor"] = ci
                        elif "valor" in h or h == "total" or "preço" in h or "preco" in h:
                            col_map["valor"] = ci

                    for row in tab[idx_header + 2:]:
                        # Limpa células
                        cels = [(c or "").strip() for c in row]
                        # Pula linha vazia ou linha de "Total"
                        if not any(cels):
                            continue
                        joined = " ".join(cels).lower()
                        if joined.startswith("total") or "observ" in joined or "assinatur" in joined:
                            break

                        material = None
                        qtd = None
                        codigo = None
                        cor = None
                        lote = None
                        valor = None

                        # === Estratégia 1: mapeamento posicional (se cabeçalho foi detectado) ===
                        if col_map:
                            def _cel(key, _cm=col_map, _cs=cels):
                                idx = _cm.get(key)
                                if idx is not None and idx < len(_cs):
                                    return _cs[idx]
                                return ""
                            codigo = _cel("codigo") or None
                            qtd_raw = _cel("quantidade")
                            material = _cel("material") or None
                            lote = _cel("lote") or None
                            cor = _cel("cor") or None
                            valor = _cel("valor") or None
                            # Valida quantidade: precisa ser numérica
                            if qtd_raw:
                                cleaned = re.sub(r"\s*(un|kg|lt|pç|pc|m2|m²|cx|gl|bd|rl|sc)\s*$", "", qtd_raw, flags=re.IGNORECASE).strip()
                                if re.match(r"^\d[\d.,\s]*$", cleaned):
                                    qtd = qtd_raw

                        # === Estratégia 2: heurística (fallback se posicional falhou) ===
                        if not material or not qtd:
                            nao_vazias = [c for c in cels if c]
                            for c in cels:
                                if not c:
                                    continue
                                # Regex de quantidade robusto (aceita "18,00", "18.00", "18", "1.500,00", "18 un")
                                c_limpo = re.sub(r"\s*(un|kg|lt|pç|pc|m2|m²|cx|gl|bd|rl|sc)\s*$", "", c, flags=re.IGNORECASE).strip()
                                # Código · 3-6 dígitos sem decimal · vem PRIMEIRO no PDF
                                if codigo is None and re.match(r"^\d{3,6}$", c_limpo):
                                    codigo = c_limpo
                                    continue
                                # Quantidade · número com decimal (vírgula ou ponto), incluindo milhar
                                if qtd is None and re.match(r"^\d[\d.,]*\d$|^\d$", c_limpo):
                                    # Confirma que não é um valor R$ (tipicamente > 4 dígitos com vírgula)
                                    if not c.startswith("R$"):
                                        qtd = c_limpo
                                        continue
                                # Material · texto significativo
                                if material is None and len(c) > 3 and re.search(r"[A-Z]{3,}", c):
                                    if c.lower() not in ("personalizada", "padrão", "padrao") and not c.startswith("R$"):
                                        material = c
                                        continue
                                # Cor (vem depois do material tipicamente)
                                if material and cor is None and len(c) < 30 and re.search(r"[a-zà-ú]", c.lower()):
                                    cor = c
                                    continue
                                # Valor (R$ X,XX)
                                if valor is None and (c.startswith("R$") or (re.match(r"^[\d.,]+$", c) and "," in c and len(c) > 6)):
                                    valor = c
                                    continue

                        # Registra se tem material (quantidade None é aceita, parseada depois)
                        if material:
                            materiais.append({
                                "codigo": codigo,
                                "quantidade": qtd,
                                "material": material,
                                "lote": lote,
                                "cor": cor,
                                "valor": valor,
                            })
                    if materiais:
                        return materiais
    except Exception as e:
        print(f"     ⚠ erro extraindo materiais do PDF: {e}")
    return materiais


def coletar_materiais_enviados(docs: list) -> list:
    """Pra cada OS Indústria PDF, baixa e extrai a tabela. Retorna lista de envios."""
    if not PDF_OK:
        return []
    envios = []
    vistos = set()  # evita reprocessar PDFs duplicados (mesmo nome)
    for d in docs or []:
        nome = d.get("nome") or ""
        nome_low = nome.lower()
        # Filtra OS Indústria PDF
        if d.get("mimeType") != "application/pdf":
            continue
        if not ("o.s." in nome_low or re.search(r"\bos\s*\d", nome_low) or "ind_stria" in nome_low or "industria" in nome_low or "indstria" in nome_low):
            continue
        # Dedup por nome base (ignora prefixos)
        chave = re.sub(r"^(field_|card_principal_)", "", nome).strip().lower()
        if chave in vistos:
            continue
        vistos.add(chave)
        url_local = d.get("urlLocal")
        pdf_bytes = baixar_pdf(url_local)
        if not pdf_bytes:
            continue
        materiais = extrair_materiais_enviados(pdf_bytes)
        if materiais:
            envios.append({
                "os_nome": nome,
                "os_data": (d.get("createdAt") or "")[:10],
                "materiais": materiais,
            })
    return envios


def categorizar_documentos(docs):
    """Agrupa documentos por categoria interpretada do nome/categoria · descarta duplicatas."""
    categorias = {"os_industria": [], "escopos": [], "relatorios_visita": [], "contrato": [], "outros": []}
    vistos = set()
    for d in docs or []:
        nome = (d.get("nome") or "").strip()
        if not nome:
            continue
        cat_pipefy = (d.get("categoria") or "").lower()
        nome_low = nome.lower()
        # Dedup por nome base (ignora prefixos field_/card_principal_)
        chave_base = re.sub(r"^(field_|card_principal_)", "", nome).strip()
        if chave_base in vistos:
            continue
        vistos.add(chave_base)
        item = {
            "nome": nome,
            "nome_limpo": chave_base,
            "data": (d.get("createdAt") or "")[:10],
            "tipo": d.get("tipo") or "-",
            "mime": d.get("mimeType") or "-",
            "url": d.get("urlOriginal") or d.get("urlLocal") or "",
        }
        # Classifica
        if "o.s." in nome_low or re.search(r"\bos\s*\d", nome_low) or "industria" in nome_low or "indstria" in nome_low or "ind_stria" in nome_low:
            categorias["os_industria"].append(item)
        elif "contrato" in nome_low and "escopo" not in nome_low:
            categorias["contrato"].append(item)
        elif "relat" in nome_low and "visita" in nome_low:
            categorias["relatorios_visita"].append(item)
        elif cat_pipefy == "escopo" or "escopo" in nome_low:
            categorias["escopos"].append(item)
        else:
            categorias["outros"].append(item)
    return categorias


def construir_jornada(obra_id):
    print(f"  · {obra_id[:8]} · fetch detail + telegram + ocorrencias + materiais + equipe + documentos...")
    detail = fetch(f"{BASE_API}/{obra_id}")
    msgs_resp = fetch(f"{BASE_API}/{obra_id}/messages?source=telegram&limit=2000") or {}
    ocorrencias = fetch_safe(f"{BASE_API}/{obra_id}/ocorrencias") or []
    materiais = fetch_safe(f"{BASE_API}/{obra_id}/materiais") or {}
    equipe_ep = fetch_safe(f"{BASE_API}/{obra_id}/equipe") or {}
    documentos = fetch_safe(f"{BASE_API}/{obra_id}/documentos") or []

    msgs_telegram = msgs_resp.get("messages", []) or []
    msgs_ordenadas = sorted(msgs_telegram, key=lambda m: m.get("timestamp") or "")

    # Datas chave
    data_criacao_iso = detail.get("createdAt")
    data_criacao = parse_iso(data_criacao_iso)
    data_exec_prevista = parse_data_simples(detail.get("dataExecucaoPrevista"))
    data_exec_confirmada = parse_data_simples(detail.get("dataExecucaoConfirmada"))

    primeira_msg = parse_iso(msgs_ordenadas[0].get("timestamp")) if msgs_ordenadas else None
    ultima_msg = parse_iso(msgs_ordenadas[-1].get("timestamp")) if msgs_ordenadas else None

    # Detecta cluster de execução
    # FIX bug #2 · fallback pra exec_prevista (se passou) + fallback final pro dia mais denso
    cluster_exec_inicio, cluster_exec_fim = None, None
    if msgs_ordenadas:
        msgs_por_dia = defaultdict(int)
        for m in msgs_ordenadas:
            dt = parse_iso(m.get("timestamp"))
            if dt:
                msgs_por_dia[dt.date()] += 1
        data_referencia_exec = data_exec_confirmada or (
            data_exec_prevista if (data_exec_prevista and data_exec_prevista <= HOJE_DATE) else None
        )
        if data_referencia_exec:
            janela_ini = data_referencia_exec - timedelta(days=EXEC_JANELA_DIAS)
            janela_fim = data_referencia_exec + timedelta(days=EXEC_JANELA_DIAS)
            dias_no_cluster = sorted([d for d in msgs_por_dia if janela_ini <= d <= janela_fim and msgs_por_dia[d] >= EXEC_CLUSTER_MSGS_DIA])
            if dias_no_cluster:
                cluster_exec_inicio = dias_no_cluster[0]
                cluster_exec_fim = dias_no_cluster[-1]
        # Fallback: busca dia mais denso da obra (≥ 2× threshold)
        if not cluster_exec_inicio:
            densos = [(d, msgs_por_dia[d]) for d in msgs_por_dia if msgs_por_dia[d] >= EXEC_CLUSTER_MSGS_DIA * 2]
            if densos:
                dia_pico = max(densos, key=lambda x: x[1])[0]
                j_ini = dia_pico - timedelta(days=5)
                j_fim = dia_pico + timedelta(days=5)
                dias_no_cluster = sorted([d for d in msgs_por_dia if j_ini <= d <= j_fim and msgs_por_dia[d] >= EXEC_CLUSTER_MSGS_DIA])
                if dias_no_cluster:
                    cluster_exec_inicio = dias_no_cluster[0]
                    cluster_exec_fim = dias_no_cluster[-1]

    # Cálculos · pra obras em andamento (sem data_exec_confirmada), usa data_ultima_msg como fim
    # FIX bug hibernação engolida · base_inicio usa primeira_msg (alinhado com fases e hibernação)
    # data_criacao do Painel é irrelevante: 187/253 obras = 2026-03-14 (migração em massa do Pipefy)
    # Antes: base_inicio = data_criacao (que podia ser ANOS depois da 1a msg) → tempo_total artificialmente
    # curto, tempo_hibernacao > tempo_total em 123 obras, proporções absurdas
    tempo_total = None
    base_inicio = (primeira_msg.date() if primeira_msg else None) or (data_criacao.date() if data_criacao else None)
    if base_inicio:
        fim_calc = ultima_msg.date() if ultima_msg else (data_exec_confirmada or None)
        if not fim_calc or fim_calc < base_inicio:
            st = (detail.get("status") or "").lower()
            if st not in ("finalizado", "concluido", "cancelado"):
                fim_calc = HOJE_DATE
        if fim_calc and fim_calc >= base_inicio:
            tempo_total = (fim_calc - base_inicio).days
    tempo_execucao = 0
    if cluster_exec_inicio and cluster_exec_fim:
        tempo_execucao = (cluster_exec_fim - cluster_exec_inicio).days + 1

    # Hibernações totais
    # FIX bug hibernação engolida · gap entre dias_com_msg[i-1] e dias_com_msg[i] inclui os
    # dias de fronteira (que têm msgs). A hibernação real é gap-1 (período sem msgs).
    # Alinhado com a correção nas fases onde inicio = h_ini+1 e fim = h_fim-1.
    msgs_por_dia = defaultdict(int)
    for m in msgs_ordenadas:
        dt = parse_iso(m.get("timestamp"))
        if dt:
            msgs_por_dia[dt.date()] += 1
    dias_com_msg = sorted(msgs_por_dia.keys())
    tempo_hibernacao = 0
    for i in range(1, len(dias_com_msg)):
        gap = (dias_com_msg[i] - dias_com_msg[i - 1]).days
        if gap >= HIBERNACAO_GAP_DIAS:
            tempo_hibernacao += gap - 1  # exclui dia de fronteira (pertence à fase ativa)

    # Fases
    fases = calcular_fases(msgs_ordenadas, data_exec_confirmada, data_criacao.date() if data_criacao else None, data_exec_prevista=data_exec_prevista)

    # Marcos
    marcos = detectar_marcos(msgs_ordenadas)

    # Materiais
    mat_totals = (materiais or {}).get("totals") or {}
    mat_items = (materiais or {}).get("items") or []
    materiais_resumo = {
        "total_m2": mat_totals.get("totalM2"),
        "stelion_m2": mat_totals.get("stelionM2"),
        "lilit_m2": mat_totals.get("lilitM2"),
        "ambientes": mat_totals.get("ambientes"),
        "n_items": len(mat_items),
        "n_reaplicacao": sum(1 for m in mat_items if "reaplica" in (m.get("tipoSuperficie") or "").lower()),
        "produtos": sorted({(m.get("produto") or "").strip().upper() for m in mat_items if m.get("produto")}),
        "cores": sorted({(m.get("cor") or "").strip() for m in mat_items if m.get("cor")}),
    }

    # Solicitações + consumo + sobras
    solicitacoes = detectar_solicitacoes_material(msgs_ordenadas, cluster_exec_inicio, cluster_exec_fim)
    consumos, sobras = detectar_consumo(msgs_ordenadas)

    # Equipe (precisa rodar antes dos marcos pra alimentar aplicadores_set)
    equipe = montar_equipe(detail, equipe_ep, msgs_ordenadas)

    # Marcos técnicos de execução (msgs durante cluster · distingue aplicador × cobrança)
    aplicadores_set = get_aplicadores_set(equipe_ep)
    # Fallback: se endpoint /equipe veio vazio, usar nomes inferidos do Telegram
    if not aplicadores_set:
        for apl in equipe.get("aplicadores_telegram", []):
            nome = apl.get("nome", "")
            for token in re.split(r"\s+", nome):
                t = token.lower().strip()
                if len(t) >= 3:
                    aplicadores_set.add(t)
    marcos_execucao = detectar_marcos_execucao(msgs_ordenadas, cluster_exec_inicio, cluster_exec_fim, aplicadores_set)

    # Camadas aplicadas detectadas no Telegram (só msgs de aplicadores oficiais)
    camadas_aplicadas = detectar_camadas_aplicadas(msgs_ordenadas, aplicadores_set)

    # Snapshots de material no Telegram · só obras com execução ≥ 2026-01-01
    exec_iso = data_exec_confirmada.isoformat() if data_exec_confirmada else None
    if exec_iso and exec_iso >= DATA_CORTE_MATERIAL:
        snapshots_material = detectar_snapshots_material(msgs_ordenadas)
    else:
        snapshots_material = []

    # Problemas
    problemas_msg = detectar_problemas_msg(msgs_ordenadas)
    ocorrencias_fmt = []
    for o in ocorrencias or []:
        ocorrencias_fmt.append({
            "data": (o.get("createdAt") or "")[:10],
            "severidade": o.get("severidade"),
            "tipo": o.get("tipo"),
            "titulo": o.get("titulo"),
        })
    ocorrencias_fmt.sort(key=lambda o: o["data"])

    # Documentos categorizados (debug · não vai pra UI)
    docs_cats = categorizar_documentos(documentos)
    docs_total = sum(len(v) for v in docs_cats.values())

    # Materiais enviados extraídos das OS Indústria PDFs
    print(f"     · extraindo materiais enviados das OS Indústria...")
    envios_materiais = coletar_materiais_enviados(documentos)
    n_envios = len(envios_materiais)
    n_itens_enviados = sum(len(e["materiais"]) for e in envios_materiais)
    print(f"     · {n_envios} OS · {n_itens_enviados} itens enviados")

    # Endereço completo
    endereco = detail.get("projetoEndereco") or "—"

    # Data de término prevista + metragem pendente
    data_termino_prevista = parse_data_simples(detail.get("dataTerminoPrevista"))
    metragem_pendente = detail.get("metragemPendente")

    # Monta jornada
    # FIX bug #2 · status ausente · fallback pra fase_atual_painel ou "desconhecido"
    _status_raw = detail.get("status")
    if not _status_raw or not str(_status_raw).strip():
        _fase_raw = detail.get("faseAtual") or ""
        _fase_up = _fase_raw.upper()
        if "FINALIZADO" in _fase_up or "CONCLU" in _fase_up:
            _status_raw = "finalizado"
        elif "CANCELADO" in _fase_up:
            _status_raw = "cancelado"
        elif "PAUSADO" in _fase_up or "SUSPEN" in _fase_up:
            _status_raw = "pausado"
        elif "EXECU" in _fase_up:
            _status_raw = "em_execucao"
        elif "PLANEJ" in _fase_up or "AGUAR" in _fase_up:
            _status_raw = "planejamento"
        elif "CONTRATO" in _fase_up:
            _status_raw = "contrato"
        else:
            _status_raw = "desconhecido"

    jornada = {
        "obra_id": obra_id,
        "cliente": detail.get("clienteNome"),
        "status": _status_raw,
        "fase_atual_painel": detail.get("faseAtual"),
        "endereco": endereco,
        "metragem": _to_float(detail.get("projetoMetragem")) if detail.get("projetoMetragem") is not None else _to_float(mat_totals.get("totalM2")),
        "faixa_metragem": classificar_faixa_metragem(_to_float(detail.get("projetoMetragem")) if detail.get("projetoMetragem") is not None else _to_float(mat_totals.get("totalM2"))),
        "metragem_pendente": metragem_pendente,
        "produtos": materiais_resumo["produtos"],
        "cores": materiais_resumo["cores"],
        "data_1a_msg": primeira_msg.date().isoformat() if primeira_msg else None,
        "data_ultima_msg": ultima_msg.date().isoformat() if ultima_msg else None,
        "data_criacao_painel": data_criacao_iso[:10] if data_criacao_iso else None,
        "data_exec_prevista": data_exec_prevista.isoformat() if data_exec_prevista else None,
        "data_exec_confirmada": data_exec_confirmada.isoformat() if data_exec_confirmada else None,
        "data_termino_prevista": data_termino_prevista.isoformat() if data_termino_prevista else None,
        "tempo_total_dias": tempo_total,
        "tempo_execucao_dias": tempo_execucao,
        "tempo_hibernacao_dias": tempo_hibernacao,
        "n_msgs_telegram_total": len(msgs_ordenadas),
        "fases": fases,
        "marcos": marcos,
        "equipe": equipe,
        "materiais": materiais_resumo,
        "solicitacoes_material": solicitacoes,
        "consumos": consumos,
        "sobras": sobras,
        "friccao": {
            "nivel": calcular_friccao_nivel(ocorrencias_fmt),
            "ocorrencias_formais": ocorrencias_fmt,
            "sinais_msg_telegram": problemas_msg,
        },
        "documentos": {
            "total": docs_total,
            **docs_cats,
        },
        "materiais_enviados": envios_materiais,
        "marcos_execucao": marcos_execucao,
        "camadas_aplicadas": camadas_aplicadas,
        "snapshots_material": snapshots_material,
        "ciclos": detectar_ciclos(
            marcos,
            fases,
            primeira_msg.date().isoformat() if primeira_msg else None,
            ultima_msg.date().isoformat() if ultima_msg else None,
        ),
        "gerado_em": HOJE.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    jornada["classificacao"] = classificar_obra(jornada)
    jornada["origem_retrabalho"] = classificar_origem_retrabalho(jornada)
    jornada["resumo_cross"] = montar_resumo_cross(jornada)
    jornada["padroes"] = detectar_padroes(jornada)
    jornada["veredito"] = gerar_veredito(jornada)
    jornada["andamento_cruzado"] = cruzar_andamento(detail, marcos_execucao)

    alertas = []
    fase = (jornada.get("fase_atual_painel") or "").upper()
    st = (jornada.get("status") or "").lower()
    if "FINALIZADO" in fase and st in ("em_execucao", "planejamento", "aguardando_execucao", "contrato"):
        alertas.append("status_fase_discrepante")
    if "CONCLU" in fase and st in ("em_execucao", "planejamento", "aguardando_execucao"):
        alertas.append("status_fase_discrepante")
    if jornada.get("n_msgs_telegram_total", 0) >= 2000:
        alertas.append("teto_api_msgs")
    jornada["alertas"] = alertas

    return jornada


def _mediana(vals):
    if not vals:
        return None
    s = sorted(vals)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _injetar_benchmark_faixa(obras):
    """Calcula medianas por faixa de metragem e injeta comparativo em cada obra."""
    por_faixa = {}
    for o in obras:
        fx = o.get("faixa_metragem")
        if not fx:
            continue
        por_faixa.setdefault(fx, []).append(o)

    benchmarks = {}
    for fx, grupo in por_faixa.items():
        n = len(grupo)
        exec_vals = [o["tempo_execucao_dias"] for o in grupo if o.get("tempo_execucao_dias") and o["tempo_execucao_dias"] > 0]
        total_vals = [o["tempo_total_dias"] for o in grupo if o.get("tempo_total_dias") and o["tempo_total_dias"] > 0]
        hib_vals = [o["tempo_hibernacao_dias"] for o in grupo if o.get("tempo_hibernacao_dias") and o["tempo_hibernacao_dias"] > 0]
        apl_vals = [len(o.get("equipe", {}).get("aplicadores_telegram", [])) for o in grupo]
        apl_vals = [a for a in apl_vals if a > 0]
        m2_vals = [o["metragem"] for o in grupo if isinstance(o.get("metragem"), (int, float)) and o["metragem"] > 0]

        retrab = sum(1 for o in grupo if o.get("classificacao", "").startswith("entrega_com_retrabalho") or o.get("classificacao") == "retrabalho_ativo" or o.get("classificacao") == "em_execucao_com_retrabalho")

        benchmarks[fx] = {
            "faixa": fx,
            "label": dict(FAIXAS_METRAGEM_LABELS).get(fx, fx),
            "n_obras": n,
            "metragem_mediana": round(_mediana(m2_vals), 1) if m2_vals else None,
            "exec_dias_mediana": _mediana(exec_vals),
            "total_dias_mediana": _mediana(total_vals),
            "hib_dias_mediana": _mediana(hib_vals),
            "n_aplicadores_mediana": _mediana(apl_vals),
            "pct_retrabalho": round(retrab / n * 100) if n else 0,
            "m2_por_dia_mediana": round(_mediana([o["metragem"] / o["tempo_execucao_dias"] for o in grupo if isinstance(o.get("metragem"), (int, float)) and o.get("tempo_execucao_dias") and o["tempo_execucao_dias"] > 0 and o["metragem"] > 0]), 1) if exec_vals else None,
            "m2_por_aplicador_mediana": round(_mediana([o["metragem"] / len(o.get("equipe", {}).get("aplicadores_telegram", [])) for o in grupo if isinstance(o.get("metragem"), (int, float)) and len(o.get("equipe", {}).get("aplicadores_telegram", [])) > 0 and o["metragem"] > 0]), 1) if apl_vals else None,
        }

    for o in obras:
        fx = o.get("faixa_metragem")
        if not fx or fx not in benchmarks:
            o["benchmark_faixa"] = None
            continue

        bench = benchmarks[fx]
        comparativo = {}

        if o.get("tempo_execucao_dias") and bench["exec_dias_mediana"]:
            ratio = o["tempo_execucao_dias"] / bench["exec_dias_mediana"]
            comparativo["exec_vs_mediana"] = round(ratio, 2)

        if o.get("tempo_total_dias") and bench["total_dias_mediana"]:
            ratio = o["tempo_total_dias"] / bench["total_dias_mediana"]
            comparativo["total_vs_mediana"] = round(ratio, 2)

        if o.get("tempo_hibernacao_dias") and bench["hib_dias_mediana"]:
            ratio = o["tempo_hibernacao_dias"] / bench["hib_dias_mediana"]
            comparativo["hib_vs_mediana"] = round(ratio, 2)

        n_apls = len(o.get("equipe", {}).get("aplicadores_telegram", []))
        if n_apls > 0 and bench["n_aplicadores_mediana"]:
            comparativo["apls_vs_mediana"] = round(n_apls / bench["n_aplicadores_mediana"], 2)

        o["benchmark_faixa"] = {
            "faixa": bench,
            "comparativo": comparativo,
        }


FAIXAS_METRAGEM_LABELS = [
    ("PP", "Até 60m²"),
    ("P",  "60–100m²"),
    ("M",  "100–150m²"),
    ("G",  "150–220m²"),
    ("GG", "220–300m²"),
    ("XG", "Acima de 300m²"),
]


# ============================================================
# Main
# ============================================================

def main():
    JORNADAS_DIR.mkdir(parents=True, exist_ok=True)

    # Lista dinâmica: se existe _obras_2026_ids.json, usa (merge com piloto). Senão, só piloto.
    ids_extra_path = Path(__file__).parent / "_obras_2026_ids.json"
    if ids_extra_path.exists():
        with open(ids_extra_path, "r") as f:
            ids_extra = json.load(f)
        seen = set()
        obra_ids = []
        for oid in OBRAS_PILOTO + ids_extra:
            if oid not in seen:
                seen.add(oid)
                obra_ids.append(oid)
        print(f"Gerando jornadas pra {len(obra_ids)} obras (piloto {len(OBRAS_PILOTO)} + extras {len(ids_extra)}, dedup {len(obra_ids)})")
    else:
        obra_ids = OBRAS_PILOTO
        print(f"Gerando jornadas pra {len(obra_ids)} obras-piloto · só Telegram")
    print()

    out = {
        "gerado_em": HOJE.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "obras": [],
    }
    erros = []
    inicio = time.time()
    max_workers = int(os.environ.get("ORION_WORKERS", "4"))

    def _processar(oid):
        j = construir_jornada(oid)
        md = gerar_narrativa_md(j)
        md_path = JORNADAS_DIR / f"{oid}.md"
        md_path.write_text(md, encoding="utf-8")
        return j

    done_count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_processar, oid): oid for oid in obra_ids}
        for fut in as_completed(futures):
            oid = futures[fut]
            done_count += 1
            try:
                j = fut.result()
                out["obras"].append(j)
                print(f"  [{done_count:3d}/{len(obra_ids)}] ✓ {j['cliente'][:45]} · {j.get('tempo_total_dias','?')}d · {len(j['marcos'])} marcos")
            except Exception as e:
                erros.append((oid, str(e)))
                print(f"  [{done_count:3d}/{len(obra_ids)}] ✗ {oid[:8]} · {e}")

    # Benchmark por faixa de metragem
    _injetar_benchmark_faixa(out["obras"])

    # Score preditivo de risco (depende de benchmark_faixa)
    for o in out["obras"]:
        o["score_risco"] = calcular_score_risco(o)

    # Camada 2: consistência material (enviado x consumido x metragem)
    for o in out["obras"]:
        o["consistencia_material"] = calcular_consistencia_material(o)

    # Salva JSON
    JORNADAS_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    elapsed = time.time() - inicio
    print()
    print(f"[OK] {JORNADAS_PATH} · {elapsed:.1f}s · {len(out['obras'])} obras OK · {len(erros)} erros")
    print(f"[OK] Markdowns em {JORNADAS_DIR}")
    if erros:
        print(f"\nErros ({len(erros)}):")
        for oid, err in erros:
            print(f"  {oid[:8]}: {err[:80]}")

    # ============================================================
    # GUARDRAILS · sanity checks pós-pipeline
    # ============================================================
    validar_sanidade(out["obras"])


def validar_sanidade(obras):
    """Guardrails automáticos: gritam quando algo não faz sentido."""
    n = len(obras)
    if n == 0:
        print("\n[GUARDRAIL] CRITICO · 0 obras geradas!")
        return

    alertas = []

    # 1. Cobertura de marcos de execução
    com_marcos = sum(1 for o in obras if len(o.get("marcos_execucao", [])) > 0)
    pct_marcos = 100 * com_marcos / n
    if pct_marcos < 30:
        alertas.append(f"CRITICO · Só {pct_marcos:.0f}% das obras têm marcos_execucao (esperado >30%)")

    # 2. Obras com muitas msgs mas zero marcos = detector com falha
    suspeitas_silenciosas = []
    for o in obras:
        senders = o.get("equipe", {}).get("senders_telegram", [])
        total_msgs = sum(s.get("msgs", 0) for s in senders) if senders else 0
        n_marcos_exec = len(o.get("marcos_execucao", []))
        if total_msgs >= 200 and n_marcos_exec == 0:
            suspeitas_silenciosas.append(f"  {o['cliente'][:40]:40s} · {total_msgs} msgs · 0 marcos")
    if suspeitas_silenciosas:
        alertas.append(f"AVISO · {len(suspeitas_silenciosas)} obras com >=200 msgs e 0 marcos de execução:")
        alertas.extend(suspeitas_silenciosas[:10])

    # 3. Aplicadores detectados vs usados
    obras_com_apl = sum(1 for o in obras if len(o.get("equipe", {}).get("aplicadores_telegram", [])) > 0)
    pct_apl = 100 * obras_com_apl / n
    if pct_apl < 20:
        alertas.append(f"CRITICO · Só {pct_apl:.0f}% das obras detectaram aplicadores no Telegram (esperado >20%)")

    # 4. is_aplicador sanity: se tem aplicadores mas nenhum marco veio de aplicador
    marcos_de_aplicador = 0
    marcos_total = 0
    for o in obras:
        apl_names = {a["nome"] for a in o.get("equipe", {}).get("aplicadores_telegram", [])}
        for m in o.get("marcos_execucao", []):
            marcos_total += 1
            if m.get("autor") in apl_names or any(a.lower() in (m.get("autor") or "").lower() for a in apl_names):
                marcos_de_aplicador += 1
    if marcos_total > 0:
        pct_apl_marcos = 100 * marcos_de_aplicador / marcos_total
        if pct_apl_marcos < 15:
            alertas.append(f"CRITICO · Só {pct_apl_marcos:.0f}% dos marcos_execucao vêm de aplicadores (esperado >15%) — possível bug em is_aplicador")

    # 5. Andamento cruzado: se tem painel preenchido mas zero confirmados em tudo
    total_confirmados = sum(
        o.get("andamento_cruzado", {}).get("resumo", {}).get("confirmado", 0) for o in obras
    )
    total_painel = sum(
        o.get("andamento_cruzado", {}).get("resumo", {}).get("painel_sem_deteccao", 0) for o in obras
    )
    if total_painel > 50 and total_confirmados == 0:
        alertas.append(f"CRITICO · {total_painel} etapas no Painel mas 0 confirmados — cruzamento possivelmente quebrado")

    # 6. Gantts vazios
    gantts_vazios = sum(1 for o in obras if len(o.get("marcos_execucao", [])) == 0)
    pct_vazio = 100 * gantts_vazios / n
    if pct_vazio > 70:
        alertas.append(f"AVISO · {pct_vazio:.0f}% das obras com Gantt vazio (esperado <70%)")

    # Relatório
    print()
    print(f"{'='*60}")
    print(f"GUARDRAILS · {n} obras")
    print(f"{'='*60}")
    print(f"  Marcos execução:  {com_marcos}/{n} obras ({pct_marcos:.0f}%)")
    print(f"  Aplicadores:      {obras_com_apl}/{n} obras ({pct_apl:.0f}%)")
    print(f"  Marcos total:     {marcos_total} · de aplicador: {marcos_de_aplicador} ({100*marcos_de_aplicador/marcos_total:.0f}% )" if marcos_total else "  Marcos total:     0")
    print(f"  Andamento:        {total_confirmados} confirmados · {total_painel} só painel")
    print(f"  Gantts vazios:    {gantts_vazios}/{n} ({pct_vazio:.0f}%)")

    if alertas:
        print()
        for a in alertas:
            print(f"  [GUARDRAIL] {a}")
        print()
        print(f"  >>> {len([a for a in alertas if 'CRITICO' in a])} críticos · {len([a for a in alertas if 'AVISO' in a])} avisos")
    else:
        print()
        print("  [OK] Todos os guardrails passaram")

    print(f"{'='*60}")


if __name__ == "__main__":
    main()
