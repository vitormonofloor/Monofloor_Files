"""
timeline_10obras.py · Δt entre marcos · 10 obras-piloto (aleatórias com mix)
============================================================================

Script STANDALONE · não toca em arquivos do Lab Orion.
Reusa regex calibradas (copiadas de gerar_jornada.py) + filtros do PADRAO_LEITURA_TELEGRAM.md.

OBJETIVO:
  - Validar se o método de extração de marcos via Telegram bate com pre_execucao_mediana=107d
    do rodrigo-stats · OU expor a defasagem do Painel.
  - Mix: 5 finalizadas + 3 em execução + 2 reparo (10 total).

OUTPUT:
  - dados/timeline_10obras.json (schema com marcos[] + intervalos[] + Δt totais)

Uso: python agente/timeline_10obras.py
"""

import io
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import pdfplumber
    PDF_OK = True
except ImportError:
    PDF_OK = False

sys.path.insert(0, str(Path(__file__).parent))
try:
    from _util import setup_utf8
    setup_utf8()
except ImportError:
    pass

ROOT = Path(__file__).parent.parent
SAIDA_PILOTO = ROOT / "dados" / "timeline_10obras.json"
SAIDA_MASSA = ROOT / "dados" / "timeline_obras.json"
MANIFEST_PATH = ROOT / "dados" / "manifest_obras.json"
BASE_API = "https://cliente.monofloor.cloud/api/projects"

HOJE = datetime.now(timezone.utc)

# ============================================================
# CONSTANTES CONFIGURÁVEIS · Rendimento de materiais (Camada 2)
# Valores conservadores · declarados como constante, nunca hardcode
# Fonte: estimativa engenharia Monofloor (validar com time industrial)
# ============================================================

# Rendimento TOTAL em m² por unidade de material enviado
# (considera múltiplas camadas de aplicação — a OS envia material pra TODAS as demãos)
# Aplicação típica: STELION 2-3 camadas, LILIT 2 camadas, LEONA 2 camadas
# Rendimento per-coat: STELION ~8m²/kg, LILIT ~6m²/kg
# Rendimento TOTAL (considerando multi-coat): dividir por número médio de camadas
# IMPORTANTE: valores aproximados · validar com time industrial
RENDIMENTO_M2_POR_KG = {
    "STELION":  3.0,   # ~8 m²/kg per coat × ~2.5 camadas ≈ 3.2 → arredonda pra 3.0 (conservador)
    "LILIT":    3.0,   # ~6 m²/kg per coat × ~2 camadas ≈ 3.0
    "LEONA":    3.0,   # base/nivelamento · 2 camadas
    "TERON":    3.0,   # LEONA renomeado abr/2026
    "LUMINA":   6.0,   # verniz 2 camadas · alto rendimento per coat (~12 m²/kg)
    "PRIMER":   6.0,   # selante 2 camadas · similar ao verniz
    "SELADOR":  5.0,   # estimativa conservadora
    "PU ULTRA": 6.0,   # variante LUMINA
}

# Margem de tolerância para classificação de superdimensionamento
# Se material enviado > (1 + MARGEM_SUPERDIMENSIONAMENTO) * cobertura teórica → superdimensionado
MARGEM_SUPERDIMENSIONAMENTO = 0.30  # 30% acima do teórico

# Mapeamento de nome do material na OS → família canônica
# Ordem importa: PRIMER antes de LUMINA (senão "LUMINA PRIMER" cai em LUMINA)
FAMILIA_PRODUTO = {
    "STELION":        "STELION",
    "LILIT":          "LILIT",
    "LEONA":          "LEONA",
    "TERON":          "LEONA",
    "LUMINA PRIMER":  "PRIMER",
    "PRIMER":         "PRIMER",
    "LUMINA":         "LUMINA",
    "VERNIZ":         "LUMINA",
    "PU ULTRA":       "LUMINA",
    "PU":             "LUMINA",
    "SELADOR":        "SELADOR",
}

# Famílias que são PRODUTO-BASE (cobrem m² diretamente)
# LUMINA/PRIMER/SELADOR são acabamento — não competem diretamente com m² do piso
FAMILIAS_BASE = {"STELION", "LILIT", "LEONA"}

# ============================================================
# CONSTANTES CONFIGURÁVEIS · Score preditivo de risco (Camada 3)
# Pesos ajustáveis · score 0-100 onde 100 = máximo risco
# Fácil de calibrar: basta alterar os pesos abaixo
# ============================================================

RISCO_PESO_INATIVO_30 = 25       # dias_inativo > 30 (obra parada é sinal grave)
RISCO_PESO_INATIVO_60 = 15       # dias_inativo > 60 (adicional, total 40)
RISCO_PESO_POSTERGACAO_2 = 15    # n_postergacoes >= 2 (postergação cascata)
RISCO_PESO_REPROVACAO_1 = 20     # n_reprovacoes >= 1 (já teve problema)
RISCO_PESO_REPROVACAO_3 = 10     # n_reprovacoes >= 3 (adicional)
RISCO_PESO_OCORRENCIAS_3 = 10    # n_ocorrencias >= 3 (muitas ocorrências formais)
RISCO_PESO_SEM_MARCOS = 15       # estagio == "sem_marcos" (obra invisível)
RISCO_PESO_RETORNO = 5           # natureza == "retorno" (retornos têm mais risco base)
RISCO_PESO_POUCA_MSG = 10        # n_msgs_telegram < 5 (pouca comunicação)

RISCO_FAIXAS = [
    (0,  20, "baixo",    "#4caf50"),  # verde
    (21, 40, "moderado", "#d4a017"),  # amarelo
    (41, 60, "alto",     "#e67e22"),  # laranja
    (61, 100, "critico", "#c45a5a"),  # vermelho
]

# Origens elegíveis para score (pre_contrato e incerta ficam N/A)
RISCO_ORIGENS_ELEGIVEIS = {"nova", "retorno"}

# Regex de sinais de consumo no Telegram (Dimensão C)
PAD_SINAL_SOBRA = re.compile(
    r"\b("
    r"sobrou\s+(material|balde|kit|produto|stelion|lilit|leona|teron|verniz|primer)"
    r"|material\s+sobr(ou|ando)"
    r"|sobraram?\s+\d+\s+(balde|kit|kg)"
    r"|sobra\s+de\s+material"
    r"|material\s+que\s+sobrou"
    r"|muito\s+material\s+sobrando"
    r"|devolver\s+(o\s+)?(material|balde|kit)"
    r"|devolv(er|endo|eu)\s+material"
    r"|material\s+(pra|para)\s+(devol|retorn)"
    r")\b",
    re.IGNORECASE,
)

PAD_SINAL_FALTA = re.compile(
    r"\b("
    r"(material|balde|kit|produto|stelion|lilit|leona|teron|verniz|primer)\s+(acabou|acabando|acabaram)"
    r"|acabou\s+(o\s+)?(material|balde|kit|produto)"
    r"|falt(ou|ando|a|aram)\s+(material|balde|kit|produto|stelion|lilit|leona|teron|verniz|primer)"
    r"|material\s+(insuficiente|n[ãa]o\s+(vai\s+)?dar|n[ãa]o\s+chega)"
    r"|sem\s+material\s+(pra|para|em)"
    r"|precis(o|a|amos)\s+(de\s+)?mais\s+(material|balde|kit)"
    r"|manda(r)?\s+mais\s+(material|balde|kit)"
    r"|envia(r)?\s+mais\s+(material|balde|kit)"
    r"|material\s+n[ãa]o\s+(deu|d[áa])"
    r"|n[ãa]o\s+(vai\s+)?ter\s+material\s+(suficiente|pra|para)"
    r")\b",
    re.IGNORECASE,
)

# Seed reproduzível pra modo piloto (aleatório validável)
random.seed(20260506)

# Mix piloto · usado quando rodado sem --massa
MIX = {
    "finalizadas": (5, ["finalizado", "concluido"]),
    "execucao":    (3, ["em_execucao"]),
    "reparo":      (2, ["reparo", "marcas_rolo_cera"]),
}

# Critério Qualidade · obras "vivas" reais (exclui finalizado, concluido, cancelado)
# Painel UI inclui cancelado em "ativa" mas pra análise de Qualidade isso polui
STATUS_VIVOS_QUALIDADE = {
    'planejamento', 'aguardando_execucao', 'em_execucao', 'reparo',
    'contrato', 'pausado', 'marcas_rolo_cera', 'aguardando_clima',
}

# Workers paralelos pra ThreadPoolExecutor · bom equilíbrio I/O × API
WORKERS = 6

# Status que indicam retorno definitivo
STATUS_RETORNO = {'reparo', 'marcas_rolo_cera'}

# Nome do card indica fase posterior
PAD_NOME_RETORNO = re.compile(
    r"(2[ªa°]|3[ªa°]|segunda|terceira)\s*(fase|etapa)"
    r"|(?:^|\s)-?\s*(?:area|área)\s+(externa|interna|[2-9]|II|III)",
    re.IGNORECASE)

# Sinais no Telegram de que o LOCAL já teve aplicação Monofloor antes
SINAIS_RETORNO_TELEGRAM = [
    (re.compile(r"(obra|aplica[çc][ãa]o|execu[çc][ãa]o|piso|verniz)\s+(anterior|existente|antig[oa])", re.IGNORECASE),
     "referência a trabalho anterior"),
    (re.compile(r"j[áa]\s+(aplicamos|executamos|fizemos|passamos|entregamos)", re.IGNORECASE),
     "referência a execução prévia"),
    (re.compile(r"(acionou?|acionar|ativou?)\s+garantia|garantia\s+(acionada|do\s+piso|ativada)", re.IGNORECASE),
     "acionamento de garantia"),
    (re.compile(r"p[óo]s[\s\-]?vendas?\s+acionad", re.IGNORECASE),
     "pós-vendas acionado"),
    (re.compile(r"retorno\s+(para|pra)\s+(reparo|garantia|corre[çc][ãa]o|corrigir|resolver)", re.IGNORECASE),
     "retorno para reparo/garantia"),
    (re.compile(r"(na|da)\s+(primeira|1[ªa°])\s*(fase|etapa|vez|aplica)", re.IGNORECASE),
     "referência a primeira fase"),
    (re.compile(r"(piso|verniz)\s+(descascou|soltou|soltando|descascando|craquel|estufou|estufando|levantou|levantando)", re.IGNORECASE),
     "defeito de aplicação existente"),
    (re.compile(r"quando\s+(fizemos|aplicamos|passamos|executamos)", re.IGNORECASE),
     "referência a execução prévia"),
    (re.compile(r"(refazer|retocar|reaplicar)\s+.{0,20}(que\s+j[áa]|anterior|existente|antigo)", re.IGNORECASE),
     "refazer trabalho anterior"),
]

# ============================================================
# Regex calibradas (copiadas de gerar_jornada.py · evita import)
# ============================================================

SENDERS_ALIAS = {
    "taquinho": "Gilmar Taquinho",
    "francisco beats": "Francisco",  # outro terminal usa "Francisco Beats Monofloor"
}

def normalizar_sender(sender):
    if not sender:
        return sender
    s_low = sender.lower()
    for token, canonico in SENDERS_ALIAS.items():
        if re.search(rf"\b{re.escape(token)}\b", s_low):
            return canonico
    return sender

PAD_CARD_BOT_SEPARATOR = re.compile(r"-{10,}")
PAD_CARD_BOT_CAMPOS = re.compile(r"APLICADOR\s*:.*SUPERVISOR\s*:.*CLIENTE\s*:", re.DOTALL | re.IGNORECASE)
# Card de criação (sem SUPERVISOR · só APLICADOR + Cliente + Endereço · ex: P2B/JAQUES/PALLOMA)
PAD_CARD_CRIACAO = re.compile(r"APLICADOR\s*:.*Cliente\s*:.*(Endereço|Fone)", re.DOTALL | re.IGNORECASE)

def is_card_bot(texto):
    if not texto:
        return False
    if PAD_CARD_BOT_SEPARATOR.search(texto):
        return True
    if PAD_CARD_BOT_CAMPOS.search(texto):
        return True
    if PAD_CARD_CRIACAO.search(texto):
        return True
    return False

PAD_CONTRATO = re.compile(r"\b(contrato\s+assinado|contrato\s+ok)\b", re.IGNORECASE)
PAD_VT_AGENDADA = re.compile(r"\bvt\s+(de\s+)?(aferi[çc][aã]o|entrada|orienta[çc][aã]o)\s+agendada\b|\bvisita\s+(de\s+)?(orienta[çc][aã]o|aferi[çc][aã]o)\s+agendada\b", re.IGNORECASE)
PAD_VT_ENTRADA_REALIZADA = re.compile(
    r"\b("
    r"vt\s+(de\s+)?entrada\s+(realizada|feita|ok|conclu[ií]da)"
    r"|visita\s+de\s+entrada\s+realizada"
    r")\b",
    re.IGNORECASE,
)
PAD_VT_REALIZADA = re.compile(
    r"\b("
    r"vt\s+(de\s+)?aferi[çc][aã]o\s+(realizada|feita|ok|conclu[ií]da)"
    r"|vt\s+ok"
    r"|visita\s+(de\s+(qualidade|aferi[çc][aã]o)\s+)?realizada"
    r"|visita\s+t[eé]cnica\s+realizada"
    r")\b",
    re.IGNORECASE,
)
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
    r"|reaplicar"
    r"|reparo\s+(necess[áa]rio|solicitado|pendente)"
    r"|in[íi]cio\s+de\s+reparo"
    r"|reparos?\s+e\s+ajustes\s+(finalizad|conclu)"
    r"|retorno\s+(em\s+obra|necess[áa]rio|para\s+reparo)"
    r"|refazer\s+(a|o|essa|esse)\s+(parede|piso|paredão|área)"
    # NOVOS · defeitos visuais detectados em vistoria/cura (frases compostas pra evitar amplitude)
    r"|ficou\s+(bem\s+|muito\s+)?marcad"
    r"|afundad[ao]\s+(grande|aqui|aparece|no\s+piso|do\s+piso)"
    r"|afundamento\s+(no|do|na)"
    r"|depress[aã]o\s+no\s+piso"
    r"|marca\s+(grande|do\s+rolinho|de\s+rolinho)"
    r"|faixa\s+(central|mais\s+forte)\s+(de\s+verniz|no\s+piso|aqui)?"
    r"|linha\s+(mais\s+forte|bem\s+marcad)"
    r")\b",
    re.IGNORECASE,
)
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
# FIX BUG: \b final exigia boundary após "finaliz" mas time escreve "finalizada/finalizado" · solução: aceitar sufixo via \w*
PAD_FINALIZACAO = re.compile(r"\b(obra\s+(finaliz\w*|conclu\w*)|verniz\s+finaliz\w*|piso\s+(finaliz\w*|aprovad\w*|conclu\w*))", re.IGNORECASE)
PAD_APROVACAO_CLIENTE = re.compile(r"\b(obra\s+aprovad\w*|cliente\s+aprov(ou|ado|ada)|aprov(ado|ada|ação).*cliente|v[íi]deo\s+de\s+aprova[çc][aã]o)\b", re.IGNORECASE)

# === MARCOS NOVOS calibrados a partir do P2B (vocabulário real do time) ===

# Obra postergada · marco super frequente (P2B teve 5x) · indica reset de cronograma
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

# Relatório VT qualidade · frase-padrão Caroline/Luana (já documentada no PADRAO_LEITURA seção 5)
PAD_RELATORIO_VT_QUALIDADE = re.compile(
    r"recebemos\s+(as\s+)?(imagens|informações)\s+e?\s*(informações)?\s*referentes\s+(à|a)\s+(nossa\s+)?(última\s+)?visita",
    re.IGNORECASE,
)

# Escopo aprovado · marco padrão da equipe projetos
PAD_ESCOPO_APROVADO = re.compile(r"(♦️\s*)?escopo\s+aprovad\w*", re.IGNORECASE)

# Equipe definida · alocação dos aplicadores
PAD_EQUIPE_DEFINIDA = re.compile(
    r"\b("
    r"prestadores\s+dessa\s+obra\s+ser[áa]o"
    r"|aplicador(es)?\s+ser[áa]o"
    r"|equipe\s+definida"
    r"|equipe\s+alocada"
    r")",
    re.IGNORECASE,
)

# Material entregue em obra · "Material chegou agora" estilo P2B
PAD_MATERIAL_ENTREGUE = re.compile(
    r"\b("
    r"material\s+chegou(\s+(agora|hoje|aqui))?"
    r"|chegou\s+(o\s+)?material"
    r"|recebimento\s+(do\s+)?material"
    r"|material(\s+em\s+obra)?\s+conferido"
    r")",
    re.IGNORECASE,
)

# Vistoria cliente agendada
PAD_VISTORIA_CLIENTE = re.compile(
    r"\b("
    r"agendar\s+(a\s+)?vistoria\s+com\s+(o\s+)?cliente"
    r"|vistoria\s+(com\s+(o|a)\s+cliente|do\s+cliente)"
    r"|visita\s+agendada\s+com\s+(o|a)\s+\w+\s+da\s+obra"
    r"|cliente\s+vai\s+passar\s+(a[íi]|na\s+obra)"
    r")",
    re.IGNORECASE,
)

# Última camada / pronto pro verniz · transição final da execução
PAD_ULTIMA_CAMADA = re.compile(
    r"\b("
    r"finalizamos\s+(a\s+)?[úu]ltima\s+camada"
    r"|[úu]ltima\s+camada\s+(aplicad|finaliz)"
    r"|preparado\s+pra\s+aplica[çc][aã]o\s+do\s+verniz"
    r"|pronto\s+pro\s+verniz"
    r")",
    re.IGNORECASE,
)

# Solicitação de material durante execução · "preciso de mais kit", "manda outro rolo"
PAD_SOLICITACAO_MATERIAL = re.compile(
    r"\b("
    # FIX falso positivo · "preciso de uma ligação" virava material · agora exige token de material
    r"precis(o|a|amos)\s+(de\s+)?(mais|outro|outra|um|uma|nov[ao])\s+(kit|balde|tela|massa|primer|verniz|stelion|lillit|teron|cera|material|rolo|pinc[éeê]l|lixa|fita)"
    r"|manda(r)?\s+(mais|outro|outra|nov[ao])\s+(kit|balde|tela|massa|primer|verniz|stelion|lillit|teron|cera|material|rolo|pinc[éeê]l|lixa|fita)"
    r"|envia(r)?\s+(mais|outro|outra|nov[ao])\s+(kit|balde|tela|massa|primer|verniz|stelion|lillit|teron|cera|material|rolo|pinc[éeê]l|lixa|fita)"
    r"|falt(a|ou|aram?)\s+(material|kit|balde|tela|massa|primer|verniz|stelion|lillit|teron|cera|rolo|pinc[éeê]l|lixa|fita)"
    r"|comprar\s+(material|kit|rolo|pinc[éeê]l|lixa|fita|tela|massa)"
    r"|sair\s+para\s+comprar"
    r"|preciso\s+da\s+libera[çc][aã]o.*pagamento"
    r"|necessito\s+comprar"
    r")",
    re.IGNORECASE,
)

# Cobrança de status · APENAS PERGUNTA · vem de pessoal Monofloor cobrando aplicador
# Removido "previsão de chegada" (era falso positivo · captura também aviso proativo)
PAD_COBRANCA_STATUS = re.compile(
    r"\b("
    r"(temos|tem|h[áa])\s+equipe\s+em\s+obra\??"
    r"|alguém\s+(j[áa]\s+)?em\s+obra\??"
    r"|j[áa]\s+chegou(\s+(algu[ée]m|equipe))?\?"
    r"|chegou\?"
    r"|chegaram\??"
    r"|equipe\s+chegou\??"
    r"|status\s+(da\s+obra)?\??"
    r"|alguma\s+(novidade|atualiza[çc][aã]o)\??"
    r"|qual\s+a\s+previs[aã]o"
    r")",
    re.IGNORECASE,
)

# Aviso proativo de chegada · líder anuncia que vem ou está chegando · separa de equipe_chegou (já chegou)
PAD_AVISO_CHEGADA = re.compile(
    r"\b("
    r"est(ou|amos)\s+a\s+caminho"
    r"|previs[aã]o\s+de\s+chegada\s+(entre|às|para)"
    r"|cheguei\s+por\s+aqui"
    r"|saindo\s+(daqui|de\s+casa)\s+pra\s+obra"
    r"|chegando\s+em\s+\d"
    r")",
    re.IGNORECASE,
)

# Evento externo · problemas FORA da alçada da Monofloor (vazamento, terceiro atrapalhando, civil pendente)
# Mede o "grau de problemas além da alçada da equipe" · sinal de obra mal preparada pelo cliente
PAD_EVENTO_EXTERNO = re.compile(
    r"\b("
    r"vazament\w+(\s+(do|de|aqui|na|aparelhamento))?"
    r"|infiltra[çc][aã]o\s+(no|na|de)"
    r"|outros\s+prestadores\s+em\s+obra"
    r"|eletricista\s+(encostand|atrapalh|com\s+escada)"
    r"|escada\s+do\s+eletricista\s+encostad"
    r"|mestre\s+de\s+obras\s+(vai|ir[áa]|precisa)"
    r"|obra\s+civil\s+(ainda|em\s+andamento|pendente)"
    r"|contrapiso\s+(ainda|em\s+execu|pendente)"
    r"|cobertura\s+provis[óo]ria"
    r"|janelas\s+(n[ãa]o\s+instal|sem\s+instalar|aguardando\s+instala)"
    r"|vidros?\s+(n[ãa]o\s+chegou|sem\s+instalar|aguardando)"
    r"|ralos?\s+(sem\s+instalar|n[ãa]o\s+instalad|sem\s+grelha)"
    r"|interven[çc][õo]es?\s+civis"
    r"|contamina[çc][aã]o\s+(entre|da|de)\s+camad"
    r"|chuva\s+(forte|interrompendo|inundo|inundou)"
    r"|prego\s+da\s+laje"
    r"|porta\s+n[ãa]o\s+(foi\s+)?retirad"
    r"|fechamento\s+(n[ãa]o\s+foi|ainda\s+(n[ãa]o|sem))"
    r")",
    re.IGNORECASE,
)

# Aditivo aprovado · separa de aditivo_negociando
PAD_ADITIVO_APROVADO = re.compile(
    r"\b("
    r"aditivo\s+(de\s+\w+\s+)?aprovad\w*"
    r"|(arquiteta|cliente)\s+aprovou\s+(o\s+)?aditivo"
    r"|aprovou.*\baditivo"
    r")",
    re.IGNORECASE,
)

# Equipe chegou em obra · marco crítico de início de execução
# Vocabulário real do P2B/SILVANA: "Estou em obra", "Estamos em obra", "Equipe em obra", "Cheguei agora"
PAD_EQUIPE_CHEGOU = re.compile(
    r"\b("
    r"est(ou|amos)\s+(j[áa]\s+)?em\s+obra"
    r"|equipe\s+em\s+obra"
    r"|cheguei\s+(em\s+obra|na\s+obra|agora|hoje|aqui)"
    r"|chegando\s+(agora|na\s+obra)"
    r"|equipe\s+chegou"
    r"|chegamos\s+(em\s+obra|na\s+obra|agora)?"
    r")",
    re.IGNORECASE,
)

# === Marcos calibrados a partir da SILVANA ===

# Aplicação de camada de produto · genérico · ex: "primeira de mão de lilit", "2° de teron", "primeira camada Stellion"
PAD_CAMADA_PRODUTO = re.compile(
    r"\b("
    r"(primeira|segunda|terceira|1[ªa°]?|2[ªa°]?|3[ªa°]?)\s+(de\s+)?(m[ãa]o|camada|demão)\s+(de\s+)?(stelion|stellion|lillit|lilit|teron|verniz|primer|steliona)"
    r"|aplica[çc][aã]o\s+(de\s+)?(stelion|stellion|lillit|lilit|teron|primer)\s+(nas?\s+paredes|no\s+piso)?"
    r"|(stelion|stellion|lillit|lilit|teron|primer)\s+(aplicad|nas?\s+parede)"
    r")",
    re.IGNORECASE,
)

# Interrupção por falta de material · marco crítico de cronograma
PAD_INTERRUPCAO_MATERIAL = re.compile(
    r"\b("
    r"material\s+(vai\s+chegar\s+apenas|n[ãa]o\s+chegou\s+ainda)"
    r"|aguardando\s+(o\s+)?material(\s+chegar)?"
    r"|retornamos.*(devido\s+ao\s+material|por\s+conta\s+do\s+material)"
    r"|sem\s+material\s+(em\s+obra|pra\s+aplicar)"
    r"|previs[ãa]o\s+de\s+retorno.*chegada\s+(dos|do)\s+mat"
    r")",
    re.IGNORECASE,
)

# Troca de aplicador · informação relevante de equipe
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

# Dia sem expediente · registro pra bot · marca pausa
PAD_DIA_SEM_EXPEDIENTE = re.compile(
    r"\b("
    r"n[ãa]o\s+(tivemos|teve|teremos|tem)\s+expediente(\s+nessa\s+obra)?"
    r"|sem\s+expediente\s+(hoje|nessa\s+obra)"
    r"|expediente\s+(suspenso|interrompido)"
    r")",
    re.IGNORECASE,
)

# === Marcos calibrados a partir da PALLOMA ===

# Escopo em revisão · marca da equipe projetos antes da aprovação
PAD_ESCOPO_REVISAO = re.compile(r"(♦️\s*)?verificando\s+escopo", re.IGNORECASE)

# Escopo atualizado · mudança formal após aprovação inicial
PAD_ESCOPO_ATUALIZADO = re.compile(
    r"(♦️\s*)?escopo\s+atualizad\w*|cliente\s+incluindo\s+superf[íi]cies",
    re.IGNORECASE,
)

# Aditivo negociando · cobrança de mudança de escopo · gargalo financeiro
PAD_ADITIVO_NEGOCIANDO = re.compile(
    r"\b("
    r"negociando\s+aditivo"
    r"|aditivo\s+(em\s+)?negocia[çc][aã]o"
    r"|cliente\s+incluindo\s+(superf[íi]cies|escopo|metragem)"
    r"|cobrar\s+aditivo"
    r")",
    re.IGNORECASE,
)

# Postergação explícita · texto livre (não tem 🚨)
PAD_POSTERGACAO_EXPLICITA = re.compile(
    r"\b("
    r"obra\s+n[ãa]o\s+tem\s+como\s+entrar"
    r"|n[ãa]o\s+conseguimos\s+entrar\s+(nessa|nesse|na)"
    r"|atualizar\s+postergação"
    r"|postergar\s+(a\s+)?(entrada|obra)"
    r"|adiar\s+(a\s+)?(entrada|obra)"
    r")",
    re.IGNORECASE,
)

# Anúncio nova data · re-cronograma após postergação
PAD_ANUNCIO_NOVA_DATA = re.compile(
    r"\b("
    r"prevendo\s+(nossa\s+)?entrada\s+(para|na)"
    r"|nova\s+previs[ãa]o\s+(de\s+)?entrada"
    r"|nossa\s+entrada\s+(ficar[áa]\s+)?(para|prevista)"
    r"|reagenda(r|do|mento)\s+(da\s+)?entrada"
    r")",
    re.IGNORECASE,
)

# Cobrança cor · gargalo G1 (267 amostras presas)
PAD_COBRANCA_COR = re.compile(
    r"\b("
    r"cobr(ei|ar|ando|amos)\s+a\s+(defini[çc][ãa]o|escolha)\s+(de|da)\s+cor"
    r"|aguardando\s+(defini[çc][ãa]o|escolha)\s+(de\s+)?cor"
    r"|aguardando\s+amostras?\s+para\s+defini[çc][ãa]o"
    r")",
    re.IGNORECASE,
)

PADROES = [
    ("contrato_assinado",        PAD_CONTRATO),
    ("vt_agendada",              PAD_VT_AGENDADA),
    ("vt_entrada_realizada",     PAD_VT_ENTRADA_REALIZADA),
    ("vt_realizada",             PAD_VT_REALIZADA),
    ("amostra_solicitada",       PAD_AMOSTRA_SOLICITADA),
    ("cobranca_cor",             PAD_COBRANCA_COR),          # NOVO PALLOMA
    ("cor_aprovada",             PAD_COR_APROVADA),
    ("escopo_em_revisao",        PAD_ESCOPO_REVISAO),        # NOVO PALLOMA
    ("aditivo_aprovado",         PAD_ADITIVO_APROVADO),      # NOVO DONA CORINA · ANTES de escopo_aprovado (mais específico)
    ("escopo_aprovado",          PAD_ESCOPO_APROVADO),       # NOVO P2B
    ("escopo_atualizado",        PAD_ESCOPO_ATUALIZADO),     # NOVO PALLOMA
    ("aditivo_negociando",       PAD_ADITIVO_NEGOCIANDO),    # NOVO PALLOMA
    ("equipe_definida",          PAD_EQUIPE_DEFINIDA),       # NOVO P2B
    ("inicio_anunciado",         PAD_INICIO_ANUNCIADO),
    ("anuncio_nova_data",        PAD_ANUNCIO_NOVA_DATA),     # NOVO PALLOMA
    ("material_produzido",       PAD_MATERIAL_PRODUZIDO),
    ("material_entregue",        PAD_MATERIAL_ENTREGUE),     # NOVO P2B
    ("relatorio_vt_qualidade",   PAD_RELATORIO_VT_QUALIDADE),# NOVO P2B
    ("vistoria_cliente",         PAD_VISTORIA_CLIENTE),      # NOVO P2B
    ("aviso_chegada",            PAD_AVISO_CHEGADA),         # NOVO DONA CORINA · ANTES de equipe_chegou
    ("equipe_chegou",            PAD_EQUIPE_CHEGOU),         # NOVO P2B/SILVANA
    ("solicitacao_material",     PAD_SOLICITACAO_MATERIAL),  # NOVO bloco "ouro fácil"
    ("cobranca_status",          PAD_COBRANCA_STATUS),       # NOVO bloco "ouro fácil"
    ("camada_produto",           PAD_CAMADA_PRODUTO),        # NOVO SILVANA
    ("ultima_camada",            PAD_ULTIMA_CAMADA),         # NOVO P2B
    ("interrupcao_material",     PAD_INTERRUPCAO_MATERIAL),  # NOVO SILVANA
    ("troca_aplicador",          PAD_TROCA_APLICADOR),       # NOVO SILVANA
    ("dia_sem_expediente",       PAD_DIA_SEM_EXPEDIENTE),    # NOVO SILVANA
    ("evento_externo",           PAD_EVENTO_EXTERNO),        # NOVO JEAN LUC · problemas fora da alçada Monofloor
    ("aprovacao_cliente",        PAD_APROVACAO_CLIENTE),
    ("reprovacao_retorno",       PAD_REPROVACAO_RETORNO),
    ("postergacao_explicita",    PAD_POSTERGACAO_EXPLICITA), # NOVO PALLOMA
    ("obra_postergada",          PAD_OBRA_POSTERGADA),       # NOVO P2B
    ("finalizacao",              PAD_FINALIZACAO),
]

UNICOS = {"contrato_assinado", "cor_aprovada", "vt_agendada", "vt_realizada",
          "vt_entrada_realizada", "material_produzido", "amostra_solicitada",
          "escopo_em_revisao", "escopo_aprovado", "equipe_definida", "ultima_camada"}

# ============================================================
# Subtipos · classificam motivo dentro de marcos polissêmicos
# Ordem importa · primeiro match vence
# ============================================================

SUBTIPOS_POSTERGACAO = [
    ("cliente_solicitou", re.compile(
        r"respons[áa]veis\s+pela\s+obra|"
        r"cliente\s+(solicitou|pediu|postergou)|"
        r"vão\s+encaminhar\s+(o\s+)?(novo\s+)?cronograma|"
        r"nova\s+data\s+(do\s+)?cliente|"
        r"obra\s+postergada\s+para\s+o\s+dia",
        re.IGNORECASE,
    )),
    ("tecnico_obra", re.compile(
        r"autonivelante|"
        r"contrapiso\s+(ainda|em\s+execu)|"
        r"preparação\s+(da\s+)?obra\s+(pendente|ainda)|"
        r"condições?\s+(da\s+)?obra|"
        r"riscos?\s+(de\s+)?entrar|"
        r"aguardando\s+(secagem|cura|preparação)|"
        r"ainda\s+vão\s+lixar",
        re.IGNORECASE,
    )),
    ("escopo_pendente", re.compile(
        r"aguardando\s+(defini[çc][ãa]o\s+(de\s+)?(cor|escopo|amostra)|"
        r"escopo\s+pendente|amostras?\s+para\s+defini[çc][ãa]o)",
        re.IGNORECASE,
    )),
    ("cronograma", re.compile(
        r"n[ãa]o\s+tem\s+como\s+entrar|"
        r"n[ãa]o\s+conseguimos\s+entrar|"
        r"atualizar\s+postergação|"
        r"reagendamento",
        re.IGNORECASE,
    )),
]

LABELS_POSTERGACAO = {
    "cliente_solicitou":  "Cliente postergou",
    "tecnico_obra":       "Condição técnica",
    "escopo_pendente":    "Escopo pendente",
    "cronograma":         "Cronograma",
    "sem_motivo":         "Sem motivo registrado",
}

# Subtipos de reprovação · base do gerar_jornada.py + ampliação calibrada com vocabulário real
SUBTIPOS_REPROVACAO = [
    ("relatorio_qualidade",  re.compile(
        r"recebemos\s+(as\s+)?(imagens|informações).*visita\s+de\s+qualidade|"
        r"durante\s+a\s+visita\s+(de\s+qualidade)?|"
        r"visita\s+de\s+qualidade\s+realizada",
        re.IGNORECASE)),
    ("agendamento_reparo",   re.compile(
        r"agenda\s+de\s+(visita|retorno)|"
        r"in[íi]cio\s+de\s+reparo\s+dia|"
        r"confirmad[ao]\s+para\s+o\s+dia|"
        r"continuidade\s+(na|da)\s+reaplica|"
        r"dar\s+continuidade|"
        r"cliente\s+solicitou\s+(a\s+)?data\s+(do\s+)?dia|"
        r"data\s+(do\s+)?dia\s+\d+/\d+\s+para\s+(realização|reaplica)|"
        r"retorno\s+em\s+obra|nosso\s+retorno\s+em\s+obra|"
        r"retornamos\s+amanh[ãa]|retornar(emos)?\s+no\s+dia|"
        r"data\s+agendada\s+para\s+o\s+retorno|"
        r"tudo\s+certo\s+para\s+(nosso\s+)?retorno",
        re.IGNORECASE)),
    ("defeito_relatado",     re.compile(
        r"marc(a|ou)\w*\s+(o\s+)?piso|"
        r"piso\s+(marcad|com\s+marca)|"
        r"trinca|fissura|rachadura|descolamento|desplac\w+|"
        r"cliente\s+(est[aá]\s+)?question(a|ando)|"
        r"diferen[çc]a\s+de\s+tonalidade|"
        r"tendo\s+problema|"
        r"marcas?\s+de\s+rolo|"
        r"problema\s+de\s+cor|"
        r"infiltra[çc][aã]o|vazamento|vazad[ao]\s+de\s+[áa]gua|"
        r"danos?\s+significativ|"
        r"piso\s+(solto|est[áa]\s+solto)|material\s+(que\s+)?(est[aá]\s+)?solto|"
        r"manchad[ao]|foi\s+manchad|"
        r"bolhas?\s+(pr[oó]xim|no\s+piso|na\s+parede)|"
        r"deformidade",
        re.IGNORECASE)),
    ("decisao_cliente",      re.compile(
        r"cliente\s+(optou|definiu|decidiu|escolheu|solicitou|pediu|reprovou|recusou|n[ãa]o\s+aprov)|"
        r"(ela|ele)\s+pediu\s+(dia\s+)?\d+/\d+\s+(a\s+|o\s+)?reaplica|"
        r"(\w+)\s+(definiu|optou\s+pela)\s+(fazer\s+)?(uma\s+)?(faixa\s+de\s+|reaplica)|"
        r"cliente\s+n[ãa]o\s+vai\s+querer|"
        r"(ela|ele)\s+(n[ãa]o\s+)?(quer|quis)\s+reaplicar|"
        r"ela\s+n[aã]o\s+ira\s+reaplicar",
        re.IGNORECASE)),
    ("proposta_tecnica",     re.compile(
        r"ideal\s+(é|eh|seria)\s+reaplicar|"
        r"vai\s+(ter\s+que|precisar)\s+(refazer|reaplicar)|"
        r"tem\s+que\s+refazer|"
        r"precisa\s+reaplicar|precisa(mos)?\s+reaplicar|"
        r"teremos\s+que\s+reaplicar|temos\s+que\s+reaplicar|"
        r"vamos\s+ter\s+que\s+reaplicar|"
        r"acredito\s+que.*(ajuste|resolve)|"
        r"alguns\s+ajustes\s+(j[áa]\s+)?resolve|"
        r"removedor\s+de\s+cera|"
        r"lixar\s+(e\s+|pra\s+)?reaplicar|"
        r"remover\s+(e\s+|pra\s+)?reaplicar|remover\s+todo\s+(o\s+)?material|"
        r"ser[áa]\s+necess[áa]rio\s+reaplicar|"
        r"aqui\s+(vamos\s+)?ter\s+que\s+reaplicar|"
        r"ter[áa]\s+que\s+reaplicar",
        re.IGNORECASE)),
    ("escopo_definido",      re.compile(
        r"escopo\s+(para|da|de)\s+reaplica|"
        r"iremos\s+reaplicar|"
        r"essas?\s+paredes?\s+para\s+reaplicar|"
        r"reaplica[çc][aã]o\s+(do|da|dos|das|na|de)\b|"
        r"retornar\s+para\s+reaplicar|"
        r"realizaremos\s+(apenas\s+)?(a\s+)?reaplica|"
        r"vamos\s+reaplicar|"
        r"(?:áreas?|metragens?)\s+(?:que\s+)?vamos\s+reaplicar|"
        r"(?:piso|parede|bancada|teto|verniz|rodap[ée])\s+(?:para|pra)\s+reaplicar|"
        r"para\s+(?:poder\s+)?reaplicar|"
        r"quer\s+reaplicar|"
        r"(?:quando|onde)\s+vamos\s+reaplicar|"
        r"conseguimos\s+reaplicar|"
        r"(?:material|baldes?)\s+(?:para|pra)\s+reaplicar|"
        r"temos\s+material\s+para\s+reaplicar|"
        r"reaplicar\s+(o\s+)?(verniz|piso|material|stelion|lilit|leona|parede|bancada|teto)|"
        r"precisar\s+reaplicar|"
        r"(?:reparo|reparos?)\s+(?:a\s+ser\s+)?realizad|"
        r"reaplicar\s+(?:essa?|aquela?|toda|mais\s+uma)|"
        r"(?:lixar|retocar)\s+.{0,15}reaplicar",
        re.IGNORECASE)),
    ("registro_campo",       re.compile(
        r"(?:s[oó]\s+)?para\s+registro\s*[:\.]|"
        r"apenas\s+para\s+registro|"
        r"s[oó]\s+para\s+registro",
        re.IGNORECASE)),
    ("solicitacao_admin",    re.compile(
        r"fazer\s+\d+\s+resumos?|"
        r"poderia\s+fazer\s+(\d+\s+)?resumos?|"
        r"preciso\s+(de\s+|do\s+)?resumo|"
        r"poderia\s+fazer\s+o\s+resumo\s+para",
        re.IGNORECASE)),
    ("confirmacao_pendente", re.compile(
        r"\b[ée]\s+a\s+reaplica[çc][aã]o\s+(do|da)\b|"
        r"fica\s+combinad[ao]|"
        r"podemos\s+seguir\s+com\s+(a\s+)?reaplica",
        re.IGNORECASE)),
]

LABELS_REPROVACAO = {
    "relatorio_qualidade":  "Relatório VT qualidade",
    "agendamento_reparo":   "Agendamento de reparo",
    "decisao_cliente":      "Decisão do cliente",
    "escopo_definido":      "Escopo de reaplicação",
    "defeito_relatado":     "Defeito relatado",
    "proposta_tecnica":     "Proposta técnica",
    "registro_campo":       "Registro de campo",
    "solicitacao_admin":    "Solicitação admin",
    "confirmacao_pendente": "Confirmação pendente",
    "tratativa":            "Tratativa",
}


def classificar_subtipo(tipo, texto):
    """Retorna (subtipo, label) se aplicável · senão (None, None)."""
    if tipo in ("obra_postergada", "postergacao_explicita"):
        for st, pad in SUBTIPOS_POSTERGACAO:
            if pad.search(texto):
                return st, LABELS_POSTERGACAO[st]
        return "sem_motivo", LABELS_POSTERGACAO["sem_motivo"]
    if tipo == "reprovacao_retorno":
        for st, pad in SUBTIPOS_REPROVACAO:
            if pad.search(texto):
                return st, LABELS_REPROVACAO[st]
        return "tratativa", LABELS_REPROVACAO["tratativa"]
    return None, None

# ============================================================
# Taxonomia hierárquica · 6 fases naturais + caminho alt. de retrabalho
# Cada fase tem marcos principais · cada principal tem sub-marcos
# Ordem importa pra cálculo de fase derivada (mais avançada = fase real)
# ============================================================

TAXONOMIA = {
    "1_pre_obra": {
        "label": "Pré-obra",
        "ordem": 1,
        "cor": "#7ea0b7",
        "marcos_principais": {
            "contrato": {
                "label": "Contrato",
                "submarcos": ["contrato_assinado"],
            },
            "escopo": {
                "label": "Escopo",
                "submarcos": ["escopo_em_revisao", "escopo_aprovado", "escopo_atualizado", "aditivo_negociando", "aditivo_aprovado"],
            },
            "amostra": {
                "label": "Amostra",
                "submarcos": ["amostra_solicitada"],
            },
            "cor": {
                "label": "Cor",
                "submarcos": ["cor_aprovada", "cobranca_cor"],
            },
            "vt": {
                "label": "VT (visita técnica)",
                "submarcos": ["vt_agendada", "vt_realizada", "vt_entrada_realizada", "relatorio_vt_qualidade"],
            },
            "postergacao": {
                "label": "Postergação",
                "submarcos": ["obra_postergada", "postergacao_explicita"],
            },
            "equipe_definicao": {
                "label": "Equipe definida",
                "submarcos": ["equipe_definida"],
            },
            "cronograma": {
                "label": "Cronograma",
                "submarcos": ["inicio_anunciado", "anuncio_nova_data"],
            },
            "material": {
                "label": "Material",
                "submarcos": ["material_produzido", "material_entregue"],
            },
        },
    },
    "2_execucao": {
        "label": "Execução",
        "ordem": 2,
        "cor": "#5fa073",
        "marcos_principais": {
            "equipe_em_obra": {
                "label": "Equipe em obra",
                "submarcos": ["aviso_chegada", "equipe_chegou"],
            },
            "camada": {
                "label": "Camadas",
                "submarcos": ["camada_produto", "ultima_camada"],
            },
            "trocas_obra": {
                "label": "Trocas em obra",
                "submarcos": ["solicitacao_material", "cobranca_status"],
            },
            "incidente": {
                "label": "Incidentes",
                "submarcos": ["interrupcao_material", "troca_aplicador", "dia_sem_expediente", "ocorrencia_formal"],
            },
            "evento_externo_grupo": {
                "label": "Eventos externos · fora da alçada",
                "submarcos": ["evento_externo"],
            },
            "vistoria_final": {
                "label": "Vistoria cliente",
                "submarcos": ["vistoria_cliente"],
            },
            "aprovacao": {
                "label": "Aprovação cliente",
                "submarcos": ["aprovacao_cliente"],
            },
            "encerramento": {
                "label": "Finalização",
                "submarcos": ["finalizacao"],
            },
        },
    },
    "x_retrabalho": {
        "label": "Pós · Retrabalho",
        "ordem": 99,  # não conta como avanço · é caminho paralelo
        "cor": "#c45a5a",
        "marcos_principais": {
            "reprovacao": {
                "label": "Reprovação · retorno",
                "submarcos": ["reprovacao_retorno"],
            },
        },
    },
}

# Index reverso: submarco → (fase_key, marco_principal_key)
_INDEX_SUBMARCO = {}
for _fase_key, _fase in TAXONOMIA.items():
    for _mp_key, _mp in _fase["marcos_principais"].items():
        for _sub in _mp["submarcos"]:
            _INDEX_SUBMARCO[_sub] = (_fase_key, _mp_key)


def classificar_marco(tipo):
    """Retorna metadados hierárquicos do marco · ou None se desconhecido."""
    res = _INDEX_SUBMARCO.get(tipo)
    if not res:
        return None
    fase_key, mp_key = res
    fase = TAXONOMIA[fase_key]
    mp = fase["marcos_principais"][mp_key]
    return {
        "fase": fase_key,
        "fase_label": fase["label"],
        "fase_ordem": fase["ordem"],
        "marco_principal": mp_key,
        "marco_principal_label": mp["label"],
        "cor_fase": fase["cor"],
    }


def detectar_ciclos(marcos):
    """Detecta ciclos de execução pelo cluster de camadas (gap <30d entre camadas consecutivas).
    Retorna {pre_obra_marcos, ciclos: [{nome, inicio, fim, duracao_dias, marcos}], gap_entre_dias}."""
    GAP_CICLO_DIAS = 30

    # Separa marcos pré-obra dos ativos (durante/retrabalho)
    pre_obra = [m for m in marcos if m.get("fase") == "1_pre_obra"]
    ativos = [m for m in marcos if m.get("fase") != "1_pre_obra"]
    ativos = sorted(ativos, key=lambda m: m.get("data") or "")

    # Camadas como espinha do ciclo
    camadas = [m for m in ativos if m["tipo"] == "camada_produto"]

    if not camadas:
        # Sem camadas = sem ciclos · todos marcos ativos vão pra "Ciclo único"
        if ativos:
            d_ini = ativos[0]["data"]
            d_fim = ativos[-1]["data"]
            try:
                duracao = (datetime.strptime(d_fim, "%Y-%m-%d") - datetime.strptime(d_ini, "%Y-%m-%d")).days
            except Exception:
                duracao = None
            ciclos = [{"nome": "Ciclo único", "ordem": 1, "inicio": d_ini, "fim": d_fim, "duracao_dias": duracao, "marcos": ativos}]
        else:
            ciclos = []
        return {"pre_obra_marcos": pre_obra, "ciclos": ciclos, "gaps_entre": []}

    # Cluster por gap <30d
    clusters = [[camadas[0]]]
    for c in camadas[1:]:
        try:
            gap = (datetime.strptime(c["data"], "%Y-%m-%d") - datetime.strptime(clusters[-1][-1]["data"], "%Y-%m-%d")).days
        except Exception:
            gap = 0
        if gap < GAP_CICLO_DIAS:
            clusters[-1].append(c)
        else:
            clusters.append([c])

    # Define janela de cada ciclo
    # Janela útil = [inicio_cluster, fim_cluster + 7d]
    # Marcos no GAP (entre fim do ciclo N e início do ciclo N+1) vão pro PRÓXIMO ciclo (são preparação pra retorno)
    TOLERANCIA_POS_CLUSTER_DIAS = 7

    def _add_dias(data_str, n):
        try:
            d = datetime.strptime(data_str, "%Y-%m-%d") + timedelta(days=n)
            return d.strftime("%Y-%m-%d")
        except Exception:
            return data_str

    ciclos_meta = []
    for i, cluster in enumerate(clusters):
        inicio_cluster = cluster[0]["data"]
        fim_cluster = cluster[-1]["data"]
        fim_efetivo = _add_dias(fim_cluster, TOLERANCIA_POS_CLUSTER_DIAS)
        ciclos_meta.append({
            "ordem": i + 1,
            "inicio_cluster": inicio_cluster,
            "fim_cluster": fim_cluster,
            "fim_efetivo": fim_efetivo,
            "marcos": [],
        })

    # Distribui marcos ativos pelos ciclos OU pro gap entre eles
    # - antes do 1º cluster → ciclo 1
    # - dentro de [inicio, fim_efetivo] de algum ciclo → ciclo
    # - no gap (entre fim_efetivo do N e inicio do N+1) → MARCOS_GAP (separado)
    # - depois do último ciclo → último ciclo
    marcos_por_gap = [[] for _ in range(len(ciclos_meta) - 1)]  # gap[i] entre ciclo[i] e ciclo[i+1]
    inicio_primeiro = ciclos_meta[0]["inicio_cluster"]
    for m in ativos:
        d = m.get("data") or ""
        if d < inicio_primeiro:
            ciclos_meta[0]["marcos"].append(m)
            continue
        atribuido = False
        for i, c in enumerate(ciclos_meta):
            if c["inicio_cluster"] <= d <= c["fim_efetivo"]:
                c["marcos"].append(m)
                atribuido = True
                break
            # Gap: depois do fim_efetivo deste ciclo, antes do início do próximo
            if i + 1 < len(ciclos_meta) and c["fim_efetivo"] < d < ciclos_meta[i + 1]["inicio_cluster"]:
                marcos_por_gap[i].append(m)
                atribuido = True
                break
        if not atribuido:
            # Depois do último ciclo
            ciclos_meta[-1]["marcos"].append(m)

    # Fim do ciclo = fim do CLUSTER (última camada) + tolerância · não o último marco arbitrário
    ciclos = []
    nomes_ciclo = ["Original", "Retorno 1", "Retorno 2", "Retorno 3", "Retorno 4", "Retorno 5"]
    for i, c in enumerate(ciclos_meta):
        m_lista = c["marcos"]
        if not m_lista:
            continue
        d_ini = c["inicio_cluster"]
        d_fim = c["fim_cluster"]  # fim REAL = última camada do cluster
        try:
            duracao = (datetime.strptime(d_fim, "%Y-%m-%d") - datetime.strptime(d_ini, "%Y-%m-%d")).days
        except Exception:
            duracao = None
        nome = nomes_ciclo[i] if i < len(nomes_ciclo) else f"Retorno {i}"
        ciclos.append({
            "ordem": i + 1,
            "nome": nome,
            "inicio": d_ini,
            "fim": d_fim,
            "duracao_dias": duracao,
            "marcos": sorted(m_lista, key=lambda x: x.get("data") or ""),
        })

    # Gaps entre ciclos consecutivos · agora carregam marcos do período intermediário
    gaps = []
    for i in range(1, len(ciclos)):
        try:
            gap_dias = (datetime.strptime(ciclos[i]["inicio"], "%Y-%m-%d") - datetime.strptime(ciclos[i-1]["fim"], "%Y-%m-%d")).days
        except Exception:
            gap_dias = None
        gap_marcos_idx = i - 1
        gap_marcos = sorted(marcos_por_gap[gap_marcos_idx], key=lambda m: m.get("data") or "") if gap_marcos_idx < len(marcos_por_gap) else []
        # Resumo dos motivos no gap (subtipos das reprovações + outros)
        from collections import Counter as _C
        resumo = _C()
        for m in gap_marcos:
            label = m.get("subtipo_label") or m.get("tipo")
            resumo[label] += 1
        resumo_lista = [{"label": k, "count": v} for k, v in resumo.most_common()]
        gaps.append({
            "depois_do_ciclo": i,
            "dias": gap_dias,
            "marcos": gap_marcos,
            "resumo": resumo_lista,
        })

    return {"pre_obra_marcos": pre_obra, "ciclos": ciclos, "gaps_entre": gaps}


PAD_KIRA_RETORNO = re.compile(
    r"reaplica[çc][ãa]o|reaplicar|reparo|retorno\s+(em|na|pra)\s+obra"
    r"|garantia\s+acionad|p[óo]s[\s-]?vendas?\s+acionad"
    r"|defeito|descascou|soltou|craquel|patologia",
    re.IGNORECASE)

PAD_KIRA_NOVA = re.compile(
    r"grupo\s+criado|boas[\s-]?vindas|sem\s+atividade|ficha\s+obra"
    r"|contrato|novo\s+projeto|obra\s+civil\s+n[ãa]o\s+iniciad"
    r"|manual\s+manuten[çc][ãa]o\s+enviad|aditivo\s+enviad"
    r"|vt\s+aferi[çc][ãa]o|material\s+ind[uú]stria|pr[eé][\s-]?obra",
    re.IGNORECASE)


def classificar_origem_obra(msgs, status, nome_cliente, marcos=None, tag_kira="", situacao_kira="", tem_reaplicacao=False):
    """Classifica se a obra é 'nova' (do zero) ou 'retorno' (local já teve aplicação Monofloor).

    Combina 6 fontes: status, nome, materiais (tipoSuperficie), ciclo nos marcos, msgs Telegram, campos Kira do Painel.
    Retorna dict com origem, fonte, sinais, confianca.
    """
    sinais = []
    fonte = None

    # 0. Contrato sem nenhum dado = pre_contrato (card recem-criado no Painel)
    if (status or '').lower() == 'contrato' and not msgs and not (marcos or []):
        return {"origem": "pre_contrato", "fonte": "status_contrato", "sinais": ["status contrato sem dados operacionais"], "confianca": "alta"}

    # 1. Status definitivo
    if (status or '').lower() in STATUS_RETORNO:
        sinais.append(f"status '{status}' indica reparo/retrabalho")
        fonte = "status"

    # 2. Nome do card indica fase posterior
    if PAD_NOME_RETORNO.search(nome_cliente or ''):
        sinais.append(f"nome indica fase posterior")
        if not fonte:
            fonte = "nome"

    # 2b. Materiais com tipoSuperficie=Reaplicação
    if tem_reaplicacao:
        sinais.append("materiais com tipoSuperficie 'Reaplicação'")
        if not fonte:
            fonte = "materiais"

    # 3. Ciclo completo nos marcos: grupo antigo (pré-2026) + execução + finalização
    MARCOS_EXEC = {'equipe_chegou', 'camada_produto', 'inicio_obra'}
    MARCOS_FINAL = {'finalizacao', 'aprovacao_cliente'}
    data_1a = (msgs[0].get("timestamp") or "")[:4] if msgs else ""
    grupo_antigo = data_1a and data_1a < "2026"
    if marcos and grupo_antigo:
        tipos_m = set(m.get("tipo") for m in marcos)
        tem_exec = bool(tipos_m & MARCOS_EXEC)
        tem_final = bool(tipos_m & MARCOS_FINAL)
        if tem_exec and tem_final:
            sinais.append(f"ciclo completo (exec+final) com grupo de {data_1a}")
            if not fonte:
                fonte = "ciclo"
        elif tem_exec:
            sinais.append(f"execução detectada com grupo de {data_1a} (sem finalização)")
            if not fonte:
                fonte = "ciclo_parcial"

    # 4. Scan nas mensagens do Telegram
    msgs_sinais = set()
    for msg in (msgs or []):
        texto = msg.get("text", "")
        if not texto or len(texto) < 10:
            continue
        for pad, descricao in SINAIS_RETORNO_TELEGRAM:
            if pad.search(texto):
                msgs_sinais.add(descricao)
    for s in sorted(msgs_sinais):
        sinais.append(f"telegram: {s}")
    if msgs_sinais and not fonte:
        fonte = "telegram"

    # 5. Kira do Painel (tagKira + situacaoAtual) — resolve "sem dados" quando não tem Telegram
    kira_texto = f"{tag_kira} {situacao_kira}".strip()
    if kira_texto:
        if PAD_KIRA_RETORNO.search(kira_texto):
            sinais.append(f"Kira indica retorno: '{kira_texto[:60]}'")
            if not fonte:
                fonte = "kira"

    # Classificação final
    if fonte in ("status", "nome", "ciclo", "kira", "materiais"):
        return {"origem": "retorno", "fonte": fonte, "sinais": sinais, "confianca": "alta"}

    if fonte == "ciclo_parcial":
        return {"origem": "incerta", "fonte": fonte, "sinais": sinais, "confianca": "media"}

    if sinais:
        confianca = "media" if len(sinais) >= 2 else "baixa"
        return {"origem": "retorno", "fonte": fonte or "telegram", "sinais": sinais, "confianca": confianca}

    # Sem Telegram — tentar classificar via Kira
    if not msgs:
        if kira_texto and PAD_KIRA_NOVA.search(kira_texto):
            return {"origem": "nova", "fonte": "kira", "sinais": [f"Kira: '{kira_texto[:60]}'"], "confianca": "media"}
        if kira_texto:
            return {"origem": "nova", "fonte": "kira", "sinais": [f"Kira sem sinal retorno: '{kira_texto[:60]}'"], "confianca": "baixa"}
        return {"origem": "pre_contrato", "fonte": "fase_inicial", "sinais": [], "confianca": "media"}

    if grupo_antigo:
        return {"origem": "nova", "fonte": "telegram", "sinais": [f"grupo de {data_1a} sem marcos de execução"], "confianca": "media"}

    return {"origem": "nova", "fonte": "telegram", "sinais": [], "confianca": "alta"}


# ============================================================
# Camada 2 · Triângulo de Consistência Material
# Cruza: m² da obra × material enviado × sinais de consumo Telegram
# ============================================================

def _classificar_familia(nome_material):
    """Mapeia nome do material da OS para família canônica.
    Ordem importa: PRIMER antes de LUMINA (LUMINA PRIMER → PRIMER)."""
    if not nome_material:
        return None
    n = nome_material.upper().strip()
    # Match por substring, na ordem correta
    for chave, familia in FAMILIA_PRODUTO.items():
        if chave in n:
            return familia
    return None


def _parse_qtd_br(s):
    """Converte quantidade no formato brasileiro ('20,00') para float."""
    if not s:
        return 0.0
    try:
        return float(str(s).replace(".", "").replace(",", "."))
    except (ValueError, TypeError):
        return 0.0


def _detectar_sinais_campo(marcos, msgs):
    """Detecta sinais de consumo de material nas mensagens Telegram.
    Retorna dict com sinal_sobra, sinal_falta, detalhes[]."""
    sinal_sobra = False
    sinal_falta = False
    detalhes = []

    # Scan nos marcos existentes (solicitacao_material + interrupcao_material já detectados)
    for m in (marcos or []):
        tipo = m.get("tipo")
        if tipo == "interrupcao_material":
            sinal_falta = True
            detalhes.append(f"Marco '{tipo}' em {m.get('data', '?')}: {m.get('trecho', '')[:80]}")
        elif tipo == "solicitacao_material":
            sinal_falta = True
            detalhes.append(f"Marco '{tipo}' em {m.get('data', '?')}: {m.get('trecho', '')[:80]}")

    # Scan adicional por padrões de sobra/falta nas mensagens brutas
    for msg in (msgs or []):
        texto = msg.get("content") or msg.get("text") or ""
        if not texto or len(texto) < 8:
            continue
        if PAD_SINAL_SOBRA.search(texto):
            sinal_sobra = True
            detalhes.append(f"Sobra em {(msg.get('timestamp') or '')[:10]}: {texto[:80]}")
        if PAD_SINAL_FALTA.search(texto):
            sinal_falta = True
            detalhes.append(f"Falta em {(msg.get('timestamp') or '')[:10]}: {texto[:80]}")

    return {
        "sinal_sobra": sinal_sobra,
        "sinal_falta": sinal_falta,
        "detalhes": detalhes[:10],  # limita pra não inflar JSON
    }


def analisar_consistencia_material(obra_dict, marcos=None, msgs=None):
    """Triângulo de consistência: m² × material enviado × sinais de campo.

    Retorna dict com classificação, números e sinais.
    Classificação:
      - material_ok: enviado compatível com m² E sem sinais de falta
      - subdimensionado: enviado < teórico OU sinais de falta
      - superdimensionado: enviado > 130% teórico OU sinais de sobra
      - sem_dados: m² ou materiais ausentes
    """
    metragem_raw = obra_dict.get("metragem")
    materiais_enviados = obra_dict.get("materiais_enviados") or []
    materiais_api = obra_dict.get("materiais_api") or []

    # ---- Dimensão A: metragem ----
    m2 = None
    if metragem_raw:
        try:
            m2 = float(str(metragem_raw).replace(",", "."))
        except (ValueError, TypeError):
            m2 = None

    # ---- Dimensão B: material enviado (OS PDF + API) ----
    # Consolida todos os itens de material por família
    itens_por_familia = defaultdict(float)  # familia → kg total

    # Fonte 1: OS Indústria (PDF)
    for envio in materiais_enviados:
        for item in envio.get("materiais") or []:
            familia = _classificar_familia(item.get("material"))
            qtd = _parse_qtd_br(item.get("quantidade"))
            if familia and qtd > 0:
                itens_por_familia[familia] += qtd

    # Fonte 2: API /materiais (se disponível)
    for item in materiais_api:
        nome = item.get("produto") or item.get("nome") or item.get("material") or ""
        familia = _classificar_familia(nome)
        qtd = 0.0
        for campo_qtd in ("quantidade", "qtd", "quantidadeEnviada"):
            val = item.get(campo_qtd)
            if val:
                qtd = _parse_qtd_br(val)
                if qtd > 0:
                    break
        if familia and qtd > 0:
            itens_por_familia[familia] += qtd

    # Total de material-base enviado (STELION/LILIT/LEONA — o que cobre m²)
    material_base_kg = sum(v for k, v in itens_por_familia.items() if k in FAMILIAS_BASE)
    material_total_kg = sum(itens_por_familia.values())
    tem_material = material_base_kg > 0

    # ---- Dimensão C: sinais de campo (Telegram) ----
    sinais = _detectar_sinais_campo(marcos, msgs)
    sinal_sobra = sinais["sinal_sobra"]
    sinal_falta = sinais["sinal_falta"]

    # ---- Cobertura teórica ----
    # Calcula quanto material-base seria necessário pra cobrir m²
    # Usa a família dominante (maior volume enviado) pra definir rendimento
    cobertura_teorica_kg = None
    rendimento_usado = None
    familia_dominante = None

    if m2 and m2 > 0:
        # Tenta usar a família dominante do material enviado
        familias_base_enviadas = {k: v for k, v in itens_por_familia.items() if k in FAMILIAS_BASE}
        if familias_base_enviadas:
            familia_dominante = max(familias_base_enviadas, key=familias_base_enviadas.get)
            rendimento_usado = RENDIMENTO_M2_POR_KG.get(familia_dominante, 7.0)
        else:
            # Sem material-base enviado · usa média conservadora STELION
            rendimento_usado = RENDIMENTO_M2_POR_KG.get("STELION", 8.0)
            familia_dominante = "STELION (estimado)"
        cobertura_teorica_kg = m2 / rendimento_usado

    # ---- Classificação ----
    classificacao = "sem_dados"
    detalhe = ""

    if not m2 and not tem_material:
        classificacao = "sem_dados"
        detalhe = "Sem m² e sem materiais enviados"
    elif not m2:
        classificacao = "sem_dados"
        detalhe = f"Sem m² · {material_base_kg:.1f} kg de material-base enviados"
    elif not tem_material:
        if sinal_falta:
            classificacao = "subdimensionado"
            detalhe = f"{m2:.0f} m² sem material registrado + sinais de falta no Telegram"
        elif sinal_sobra:
            classificacao = "sem_dados"
            detalhe = f"{m2:.0f} m² sem material registrado (sinal de sobra, mas sem base pra comparar)"
        else:
            classificacao = "sem_dados"
            detalhe = f"{m2:.0f} m² sem material registrado nas OS/API"
    else:
        # Temos m² e material · podemos calcular ratio
        ratio = material_base_kg / cobertura_teorica_kg if cobertura_teorica_kg else 0

        if sinal_falta:
            classificacao = "subdimensionado"
            detalhe = (f"Enviado {material_base_kg:.1f} kg ({familia_dominante}) "
                       f"para {m2:.0f} m² (teórico: {cobertura_teorica_kg:.1f} kg) "
                       f"+ sinais de falta no Telegram")
        elif ratio < 0.85:
            classificacao = "subdimensionado"
            detalhe = (f"Enviado {material_base_kg:.1f} kg ({familia_dominante}) "
                       f"para {m2:.0f} m² · ratio {ratio:.0%} do teórico ({cobertura_teorica_kg:.1f} kg)")
        elif sinal_sobra:
            classificacao = "superdimensionado"
            detalhe = (f"Enviado {material_base_kg:.1f} kg ({familia_dominante}) "
                       f"para {m2:.0f} m² + sinais de sobra no Telegram")
        elif ratio > (1 + MARGEM_SUPERDIMENSIONAMENTO):
            classificacao = "superdimensionado"
            detalhe = (f"Enviado {material_base_kg:.1f} kg ({familia_dominante}) "
                       f"para {m2:.0f} m² · ratio {ratio:.0%} do teórico ({cobertura_teorica_kg:.1f} kg)")
        else:
            classificacao = "material_ok"
            detalhe = (f"Enviado {material_base_kg:.1f} kg ({familia_dominante}) "
                       f"para {m2:.0f} m² · ratio {ratio:.0%} · compatível")

    return {
        "classificacao": classificacao,
        "m2": m2,
        "cobertura_teorica_kg": round(cobertura_teorica_kg, 1) if cobertura_teorica_kg else None,
        "material_base_kg": round(material_base_kg, 1) if material_base_kg else 0,
        "material_total_kg": round(material_total_kg, 1) if material_total_kg else 0,
        "itens_por_familia": {k: round(v, 1) for k, v in itens_por_familia.items()} if itens_por_familia else {},
        "familia_dominante": familia_dominante,
        "rendimento_usado_m2_kg": rendimento_usado,
        "sinais_campo": sinais,
        "detalhe": detalhe,
    }


def derivar_fase_real(marcos):
    """A partir dos marcos detectados, calcula a fase REAL da obra (a mais avançada · ignora retrabalho)."""
    if not marcos:
        return None
    classificados = [classificar_marco(m["tipo"]) for m in marcos]
    classificados = [c for c in classificados if c]
    if not classificados:
        return None

    # Fases observadas (excluindo retrabalho)
    ordens_observadas = sorted({c["fase_ordem"] for c in classificados if c["fase_ordem"] < 99})
    if not ordens_observadas:
        # Só tem retrabalho · estado anômalo
        return {
            "fase_real": "x_retrabalho",
            "fase_label": "Retrabalho (caminho alternativo)",
            "fase_ordem": 99,
            "fases_observadas": ["x_retrabalho"],
            "gaps_de_fase": [],
            "tem_retrabalho": True,
            "n_marcos_por_fase": {"x_retrabalho": len(classificados)},
        }

    ordem_max = max(ordens_observadas)
    # Recupera a key da fase pela ordem
    fase_max_key = next(k for k, v in TAXONOMIA.items() if v["ordem"] == ordem_max)

    # Gaps entre min e max
    gaps_ordens = [n for n in range(ordens_observadas[0], ordem_max + 1) if n not in ordens_observadas]
    gaps_keys = [next(k for k, v in TAXONOMIA.items() if v["ordem"] == n) for n in gaps_ordens]

    # Marcos por fase
    n_por_fase = {}
    for c in classificados:
        n_por_fase[c["fase"]] = n_por_fase.get(c["fase"], 0) + 1

    fases_observadas_keys = [next(k for k, v in TAXONOMIA.items() if v["ordem"] == n) for n in ordens_observadas]
    tem_retrabalho = any(c["fase_ordem"] == 99 for c in classificados)
    if tem_retrabalho:
        n_por_fase["x_retrabalho"] = sum(1 for c in classificados if c["fase_ordem"] == 99)

    return {
        "fase_real": fase_max_key,
        "fase_label": TAXONOMIA[fase_max_key]["label"],
        "fase_ordem": ordem_max,
        "fases_observadas": fases_observadas_keys,
        "gaps_de_fase": gaps_keys,
        "tem_retrabalho": tem_retrabalho,
        "n_marcos_por_fase": n_por_fase,
    }

# ============================================================
# Util
# ============================================================

def fetch(url, max_retries=2):
    last = None
    for t in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "timeline-10obras/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            last = e
            if t < max_retries:
                time.sleep(2 ** t)
    raise RuntimeError(f"fetch falhou {url}: {last}")

def fetch_safe(url):
    try:
        return fetch(url, max_retries=1)
    except Exception:
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

def diff_dias_iso(d1_iso, d2_iso):
    if not d1_iso or not d2_iso:
        return None
    try:
        d1 = datetime.fromisoformat(d1_iso[:10]).date()
        d2 = datetime.fromisoformat(d2_iso[:10]).date()
        return (d1 - d2).days
    except Exception:
        return None

# ============================================================
# Detecção de marcos
# ============================================================

def detectar_marco(msg, tipo, padrao):
    texto = msg.get("content") or ""
    m = padrao.search(texto)
    if not m:
        return None
    out = {
        "tipo": tipo,
        "data": (msg.get("timestamp") or "")[:10],
        "data_iso": msg.get("timestamp"),
        "autor": normalizar_sender((msg.get("sender") or "?")[:35]),
        "trecho": texto[:140].replace("\n", " ").strip(),
        "match": m.group(0)[:60],
    }
    cls = classificar_marco(tipo)
    if cls:
        out["fase"] = cls["fase"]
        out["marco_principal"] = cls["marco_principal"]
    # Subtipo (motivo) pra postergações e reprovações
    subtipo, subtipo_label = classificar_subtipo(tipo, texto)
    if subtipo:
        out["subtipo"] = subtipo
        out["subtipo_label"] = subtipo_label
    return out

def extrair_marcos(msgs_ordenadas):
    primeiro_de_cada = {}
    TIPOS_ACEITAM_TRANSCRICAO = {"reprovacao_retorno"}

    repetiveis = []
    descarte = {"bot": 0, "transcricao": 0, "sem_match": 0, "dedup": 0, "match": 0}
    amostra_sem_match = []

    for m in msgs_ordenadas:
        texto = m.get("content") or ""
        if is_card_bot(texto):
            descarte["bot"] += 1
            continue
        is_transcricao = "🎬" in texto or "🎙️" in texto
        casou = False
        for tipo, pad in PADROES:
            if is_transcricao and tipo not in TIPOS_ACEITAM_TRANSCRICAO:
                continue
            marco = detectar_marco(m, tipo, pad)
            if marco:
                casou = True
                if tipo in UNICOS:
                    if tipo not in primeiro_de_cada:
                        primeiro_de_cada[tipo] = marco
                        descarte["match"] += 1
                    else:
                        descarte["dedup"] += 1
                else:
                    chave = (tipo, marco["data"])
                    if chave not in {(t["tipo"], t["data"]) for t in repetiveis}:
                        repetiveis.append(marco)
                        descarte["match"] += 1
                    else:
                        descarte["dedup"] += 1
                break
        if not casou:
            if is_transcricao:
                descarte["transcricao"] += 1
            else:
                descarte["sem_match"] += 1
                if len(amostra_sem_match) < 30:
                    txt = texto[:150].replace("\n", " ").strip()
                    if len(txt) > 15:
                        amostra_sem_match.append({
                            "sender": (m.get("sender") or "")[:30],
                            "data": (m.get("timestamp") or "")[:10],
                            "trecho": txt,
                        })

    marcos = list(primeiro_de_cada.values()) + repetiveis
    marcos_sorted = sorted(marcos, key=lambda x: x["data_iso"] or "")
    return marcos_sorted, descarte, amostra_sem_match

def calcular_intervalos(marcos):
    """Δt em dias entre marcos consecutivos."""
    if len(marcos) < 2:
        return []
    out = []
    for i in range(1, len(marcos)):
        delta = diff_dias_iso(marcos[i]["data_iso"], marcos[i-1]["data_iso"])
        out.append({
            "de": marcos[i-1]["tipo"],
            "para": marcos[i]["tipo"],
            "data_de": marcos[i-1]["data"],
            "data_para": marcos[i]["data"],
            "dias": delta,
        })
    return out

# ============================================================
# Seleção das 10 obras
# ============================================================

def selecionar_mix(todas):
    """Mix balanceado: 5 finalizadas + 3 execução + 2 reparo · seed reproduzível."""
    pools = {grupo: [o for o in todas if o.get("status") in statuses]
             for grupo, (_, statuses) in MIX.items()}

    selecionadas = {}
    for grupo, (n, _) in MIX.items():
        pool = pools[grupo]
        if len(pool) < n:
            print(f"  ⚠ pool '{grupo}' tem só {len(pool)} obras · pegando todas")
            n = len(pool)
        selecionadas[grupo] = random.sample(pool, n)
    return selecionadas

# ============================================================
# Construir timeline de uma obra
# ============================================================

# Padrões de sender que indicam pessoal Monofloor (não aplicador externo)
PAD_SENDER_MONOFLOOR = re.compile(
    r"\b(monofloor|operações|opera[çc][õo]es|atendimento|equipe\s+projetos|"
    r"luana|mayara|pedro\s*\||caroline|thaisa|tha[íi]sa|mariana|vanessa|"
    r"jonathan|braiam|brian|nathan\s|kettlyn|gabi)",
    re.IGNORECASE,
)


def is_sender_monofloor(sender):
    """True se sender parece ser pessoal Monofloor (não aplicador externo)."""
    if not sender:
        return False
    return bool(PAD_SENDER_MONOFLOOR.search(sender))


CONSULTOR_ALIAS = {
    "luana": "Luana Lima",
    "luana ": "Luana Lima",
    "luana patricia de andrade lima": "Luana Lima",
    "luana lima": "Luana Lima",
    "wesley": "Wesley Carvalho",
    "wesley matheus de carvalho": "Wesley Carvalho",
    "wesley carvalho": "Wesley Carvalho",
    "pedro": "Pedro Santana",
    "pedro alexandre santana": "Pedro Santana",
    "pedro santana": "Pedro Santana",
    "pedro marçal": "Pedro Santana",
    "pedro marcal": "Pedro Santana",
    "juliana santos": "Juliana Santos",
    "juliana": "Juliana Santos",
    "mayara": "Mayara",
    "caroline": "Caroline",
}

NAO_E_CONSULTOR = {
    "thaísa de lara barbosa", "thaisa de lara barbosa", "thaísa barbosa", "thaisa barbosa",
    "renata garcia penna", "renata penna",
}


def _fix_latin1_in_utf8(s):
    """API retorna codepoints Latin-1 (0xe7=ç, 0xed=í) dentro de JSON UTF-8.
    Corrige os mais comuns sem precisar de tabela completa."""
    return s.replace("\xe7", "ç").replace("\xed", "í").replace("\xe3", "ã").replace(
        "\xe1", "á").replace("\xf3", "ó").replace("\xfa", "ú").replace(
        "\xea", "ê").replace("\xe9", "é").replace("\xf4", "ô")


def normalizar_consultor(raw):
    """Normaliza nome do consultor: limpa [], encoding Latin-1, unifica grafias.
    Retorna None se nome pertence a NAO_E_CONSULTOR (projetos, comercial, etc)."""
    if not raw or raw == "[]" or not isinstance(raw, str):
        return None
    nome = _fix_latin1_in_utf8(raw).strip()
    if not nome:
        return None
    lookup = nome.lower()
    if lookup in NAO_E_CONSULTOR:
        return None
    if lookup in CONSULTOR_ALIAS:
        return CONSULTOR_ALIAS[lookup]
    return nome


def extrair_equipe_monofloor(detail):
    """Equipe Monofloor (operações, atendimento, consultor, líder de qualidade) do detail."""
    return {
        "operacoes": detail.get("responsavelOperacoes"),
        "atendimento": detail.get("responsavelAtendimento"),
        "consultor": normalizar_consultor(detail.get("consultorNome")),
    }


def extrair_equipe_oficial(equipe_resp):
    """Aplicadores oficiais cadastrados no Painel (`/equipe.prestadores`).
    Geralmente vazio · estrutura: prestadores=[{nome, funcao}]."""
    if not equipe_resp:
        return []
    out = []
    for p in equipe_resp.get("prestadores") or []:
        nome = (p.get("nome") or "").strip()
        funcao = (p.get("funcao") or "").strip()
        if nome:
            out.append({"nome": nome, "funcao": funcao})
    return out


LABELS_OCORRENCIA = {
    "falha_comunicacao": "Falha de comunicação",
    "reclamacao_cliente": "Reclamação do cliente",
    "atraso_cronograma": "Atraso de cronograma",
    "problema_material": "Problema de material",
    "problema_qualidade": "Problema de qualidade",
    "problema_logistica": "Problema logístico",
    "outros": "Outros",
}


def baixar_pdf(url_local):
    """Baixa PDF do storage interno do Painel via /api/storage/..."""
    if not url_local or not url_local.startswith("/storage/"):
        return None
    full_url = "https://cliente.monofloor.cloud/api" + url_local
    try:
        req = urllib.request.Request(full_url, headers={"User-Agent": "timeline-10obras/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except Exception:
        return None


def extrair_materiais_enviados(pdf_bytes):
    """Extrai a tabela 'Descrição dos materiais enviados' de uma OS Indústria.
    Retorna lista de {codigo, quantidade, material, cor, valor}."""
    if not PDF_OK or not pdf_bytes:
        return []
    materiais = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables() or []
                for tab in tables:
                    idx_header = None
                    for i, row in enumerate(tab):
                        joined = " ".join((c or "") for c in row).lower()
                        if "descri" in joined and ("material" in joined or "enviad" in joined):
                            idx_header = i
                            break
                    if idx_header is None:
                        continue
                    for row in tab[idx_header + 2:]:
                        cels = [(c or "").strip() for c in row]
                        if not any(cels):
                            continue
                        joined = " ".join(cels).lower()
                        if joined.startswith("total") or "observ" in joined or "assinatur" in joined:
                            break
                        material = qtd = codigo = cor = valor = None
                        for c in cels:
                            if not c:
                                continue
                            if codigo is None and re.match(r"^\d{3,6}$", c):
                                codigo = c
                                continue
                            if qtd is None and re.match(r"^\d+[,\.]\d+$", c.replace(" ", "")):
                                qtd = c
                                continue
                            if qtd is None and re.match(r"^\d{1,3}$", c):
                                qtd = c
                                continue
                            if material is None and len(c) > 3 and re.search(r"[A-Z]{3,}", c):
                                if c.lower() not in ("personalizada", "padrão", "padrao") and not c.startswith("R$"):
                                    material = c
                                    continue
                            if material and cor is None and len(c) < 30 and re.search(r"[a-zà-ú]", c.lower()):
                                cor = c
                                continue
                            if valor is None and (c.startswith("R$") or (re.match(r"^[\d.,]+$", c) and "," in c)):
                                valor = c
                                continue
                        if material and qtd:
                            materiais.append({
                                "codigo": codigo,
                                "quantidade": qtd,
                                "material": material,
                                "cor": cor,
                                "valor": valor,
                            })
                    if materiais:
                        return materiais
    except Exception:
        pass
    return materiais


def coletar_materiais_enviados(docs):
    """Pra cada OS Indústria PDF, baixa e extrai a tabela. Retorna lista de envios."""
    if not PDF_OK:
        return []
    envios = []
    vistos = set()
    for d in docs or []:
        nome = d.get("nome") or ""
        nome_low = nome.lower()
        if d.get("mimeType") != "application/pdf":
            continue
        if not ("o.s." in nome_low or re.search(r"\bos\s*\d", nome_low) or "industria" in nome_low or "indstria" in nome_low or "ind_stria" in nome_low):
            continue
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


def ocorrencia_to_marco(oc):
    """Converte uma ocorrência formal do endpoint em marco-pseudo · fica em Incidentes da fase Execução."""
    tipo_oc = oc.get("tipo") or "outros"
    severidade = oc.get("severidade") or "media"
    status = oc.get("status") or "aberta"
    titulo = (oc.get("titulo") or "").strip()
    descricao = (oc.get("descricao") or "").strip()
    resolucao = (oc.get("resolucao") or "").strip()
    resolvida_por = (oc.get("resolvidaPor") or "").strip()
    resolvida_em = (oc.get("resolvidaEm") or "")[:10]

    marco = {
        "tipo": "ocorrencia_formal",
        "data": (oc.get("createdAt") or "")[:10],
        "data_iso": oc.get("createdAt"),
        "autor": f"Sistema · ocorrência {status}",
        "trecho": f"{titulo} · {descricao}"[:200].replace("\n", " "),
        "match": titulo[:60],
        "fase": "2_execucao",
        "marco_principal": "incidente",
        "subtipo": tipo_oc,
        "subtipo_label": LABELS_OCORRENCIA.get(tipo_oc, tipo_oc.replace("_", " ").title()),
        "severidade": severidade,
        "status_oc": status,
    }
    if resolucao:
        marco["resolucao"] = resolucao[:200]
    if resolvida_por:
        marco["resolvida_por"] = resolvida_por
    if resolvida_em:
        marco["resolvida_em"] = resolvida_em
    return marco


# ============================================================
# Score preditivo de risco (Camada 3)
# ============================================================

def calcular_score_risco(obra_dict):
    """Calcula score preditivo de risco para obra ativa.
    Retorna dict {valor, nivel, cor, sinais, detalhe} ou None se obra não elegível.
    Obras pre_contrato e incerta retornam None (dados insuficientes).
    """
    origem = (obra_dict.get("origem_obra") or {}).get("origem", "")
    if origem not in RISCO_ORIGENS_ELEGIVEIS:
        return None

    sinais = []
    valor = 0

    # 1. Inatividade
    dias_inativo = obra_dict.get("dias_inativo") or 0
    if dias_inativo > 60:
        valor += RISCO_PESO_INATIVO_30 + RISCO_PESO_INATIVO_60
        sinais.append(f"Inativa {dias_inativo}d (>60d)")
    elif dias_inativo > 30:
        valor += RISCO_PESO_INATIVO_30
        sinais.append(f"Inativa {dias_inativo}d (>30d)")

    # 2. Postergações (derivadas dos marcos)
    counts = obra_dict.get("counts_por_tipo") or {}
    n_postergacoes = counts.get("obra_postergada", 0) + counts.get("postergacao_explicita", 0)
    if n_postergacoes >= 2:
        valor += RISCO_PESO_POSTERGACAO_2
        sinais.append(f"{n_postergacoes} postergacoes")

    # 3. Reprovações (derivadas dos marcos)
    n_reprovacoes = counts.get("reprovacao_retorno", 0)
    if n_reprovacoes >= 3:
        valor += RISCO_PESO_REPROVACAO_1 + RISCO_PESO_REPROVACAO_3
        sinais.append(f"{n_reprovacoes} reprovacoes (>=3)")
    elif n_reprovacoes >= 1:
        valor += RISCO_PESO_REPROVACAO_1
        sinais.append(f"{n_reprovacoes} reprovacao(oes)")

    # 4. Ocorrências formais
    n_ocorrencias = obra_dict.get("n_ocorrencias") or 0
    if n_ocorrencias >= 3:
        valor += RISCO_PESO_OCORRENCIAS_3
        sinais.append(f"{n_ocorrencias} ocorrencias formais")

    # 5. Estágio
    estagio = obra_dict.get("estagio") or ""
    if estagio == "sem_marcos":
        valor += RISCO_PESO_SEM_MARCOS
        sinais.append("Sem marcos detectados")

    # 6. Natureza retorno
    if origem == "retorno":
        valor += RISCO_PESO_RETORNO
        sinais.append("Retorno (risco base maior)")

    # 7. Pouca comunicação
    n_msgs = obra_dict.get("n_msgs_telegram") or 0
    if n_msgs < 5:
        valor += RISCO_PESO_POUCA_MSG
        sinais.append(f"Apenas {n_msgs} msgs Telegram")

    # Cap em 100
    valor = min(valor, 100)

    # Classificar por faixa
    nivel = "baixo"
    cor = "#4caf50"
    for faixa_min, faixa_max, faixa_nivel, faixa_cor in RISCO_FAIXAS:
        if faixa_min <= valor <= faixa_max:
            nivel = faixa_nivel
            cor = faixa_cor
            break

    # Detalhe legível
    if sinais:
        detalhe = " | ".join(sinais)
    else:
        detalhe = "Nenhum sinal de risco detectado"

    return {
        "valor": valor,
        "nivel": nivel,
        "cor": cor,
        "sinais": sinais,
        "detalhe": detalhe,
    }


def timeline_obra(obra_listing, grupo):
    obra_id = obra_listing["id"]
    print(f"  · [{grupo}] {obra_listing.get('clienteNome','?')[:40]} ({obra_id[:8]}) · fetch...")

    detail = fetch_safe(f"{BASE_API}/{obra_id}") or {}
    msgs_resp = fetch_safe(f"{BASE_API}/{obra_id}/messages?source=telegram&limit=2000") or {}
    equipe_resp = fetch_safe(f"{BASE_API}/{obra_id}/equipe") or {}
    ocorrencias_resp = fetch_safe(f"{BASE_API}/{obra_id}/ocorrencias") or []
    documentos_resp = fetch_safe(f"{BASE_API}/{obra_id}/documentos") or []
    materiais_resp = fetch_safe(f"{BASE_API}/{obra_id}/materiais") or {}
    materiais_items = materiais_resp.get("items") if isinstance(materiais_resp, dict) else (materiais_resp if isinstance(materiais_resp, list) else [])
    msgs = sorted(msgs_resp.get("messages", []) or [], key=lambda m: m.get("timestamp") or "")

    # Frequência de msgs por dia (heatmap)
    freq_por_dia = defaultdict(int)
    for m in msgs:
        d = (m.get("timestamp") or "")[:10]
        if d:
            freq_por_dia[d] += 1
    msgs_por_dia = [{"data": d, "n": n} for d, n in sorted(freq_por_dia.items())]

    # Materiais enviados das OS Indústria (PDFs do /documentos)
    print(f"     · extraindo materiais enviados das OS Indústria...")
    materiais_enviados = coletar_materiais_enviados(documentos_resp) if PDF_OK else []
    n_envios = len(materiais_enviados)
    n_itens_enviados = sum(len(e["materiais"]) for e in materiais_enviados)
    if n_envios:
        print(f"     · {n_envios} OS · {n_itens_enviados} itens enviados")

    equipe_monofloor = extrair_equipe_monofloor(detail)
    aplicadores_oficiais = extrair_equipe_oficial(equipe_resp)

    marcos, descarte_log, amostra_sem_match = extrair_marcos(msgs)

    ocorrencias_marcos = [ocorrencia_to_marco(oc) for oc in (ocorrencias_resp or []) if isinstance(oc, dict)]
    if ocorrencias_marcos:
        marcos = sorted(marcos + ocorrencias_marcos, key=lambda x: x.get("data_iso") or "")

    intervalos = calcular_intervalos(marcos)

    # Senders com marco "equipe_chegou" · separa aplicadores externos vs presença Monofloor
    aplicadores_observados = []
    presenca_monofloor = []
    senders_chegada = {}
    for m in marcos:
        if m["tipo"] == "equipe_chegou":
            autor = m.get("autor")
            if autor and autor not in senders_chegada:
                senders_chegada[autor] = m["data"]
    for autor, primeira_data in senders_chegada.items():
        info = {"nome": autor, "primeira_chegada": primeira_data}
        if is_sender_monofloor(autor):
            presenca_monofloor.append(info)
        else:
            aplicadores_observados.append(info)

    # Δt total entre primeiro e último marco
    dt_total = None
    if len(marcos) >= 2:
        dt_total = diff_dias_iso(marcos[-1]["data_iso"], marcos[0]["data_iso"])

    # Δt da 1ª msg até execução confirmada (proxy de ciclo)
    dt_painel = None
    primeira_msg = msgs[0].get("timestamp") if msgs else None
    data_exec = detail.get("dataExecucaoConfirmada") or detail.get("dataExecucaoPrevista")
    if primeira_msg and data_exec:
        dt_painel = diff_dias_iso(data_exec, primeira_msg)

    # Counts por tipo
    counts = Counter(m["tipo"] for m in marcos)

    # Fase derivada por marcos detectados
    fase_derivada = derivar_fase_real(marcos)
    # Ciclos detectados por cluster de camadas
    ciclos_info = detectar_ciclos(marcos)

    # Origem da obra: nova (do zero) vs retorno (local já teve aplicação)
    nome_cli = detail.get("clienteNome") or obra_listing.get("clienteNome") or ""
    status_obra = detail.get("status") or obra_listing.get("status") or ""
    tag_kira = (detail.get("tagKira") or "").strip()
    situacao_kira = (detail.get("situacaoAtual") or "").strip()
    tem_reaplicacao = any("reaplica" in (it.get("tipoSuperficie") or "").lower() for it in (materiais_items or []))
    origem_obra = classificar_origem_obra(msgs, status_obra, nome_cli, marcos, tag_kira, situacao_kira, tem_reaplicacao)

    # Camada 2 · Triângulo de consistência material
    obra_para_analise = {
        "metragem": detail.get("projetoMetragem") or obra_listing.get("projetoMetragem"),
        "materiais_enviados": materiais_enviados,
        "materiais_api": materiais_items or [],
    }
    consistencia_material = analisar_consistencia_material(obra_para_analise, marcos=marcos, msgs=msgs)

    n_ocorrencias = sum(1 for m in marcos if m.get("tipo") == "ocorrencia_formal")
    consultor = equipe_monofloor.get("consultor") or normalizar_consultor(equipe_monofloor.get("operacoes"))

    # Estagio derivado + alerta de obra parada
    tipos_marcos = set(m.get("tipo") for m in marcos)
    if tipos_marcos & {"camada_produto"}:
        estagio = "em_execucao"
    elif tipos_marcos & {"equipe_chegou"}:
        estagio = "equipe_em_obra"
    elif tipos_marcos & {"vt_agendada", "vt_realizada"}:
        estagio = "pos_vt"
    elif tipos_marcos & {"contrato_assinado"}:
        estagio = "pos_contrato"
    elif marcos:
        estagio = "com_atividade"
    else:
        estagio = "sem_marcos"

    # Dias desde ultima atividade (marco ou msg)
    datas_atividade = []
    if marcos:
        ult_marco = marcos[-1].get("data")
        if ult_marco:
            datas_atividade.append(ult_marco)
    ultima_msg_data = (msgs[-1].get("timestamp") if msgs else "")[:10]
    if ultima_msg_data:
        datas_atividade.append(ultima_msg_data)
    if not datas_atividade:
        dc = (detail.get("createdAt") or "")[:10]
        if dc:
            datas_atividade.append(dc)

    dias_inativo = None
    ultima_atividade = None
    if datas_atividade:
        ultima_atividade = max(datas_atividade)
        try:
            dias_inativo = (HOJE - datetime.strptime(ultima_atividade[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)).days
        except ValueError:
            pass

    alerta_parada = None
    if dias_inativo is not None and dias_inativo > 30:
        if estagio == "pos_contrato":
            alerta_parada = {"tipo": "contrato_sem_avanço", "dias": dias_inativo}
        elif estagio in ("sem_marcos", "com_atividade"):
            alerta_parada = {"tipo": "obra_dormindo", "dias": dias_inativo}
        elif estagio == "pos_vt":
            alerta_parada = {"tipo": "pos_vt_sem_execucao", "dias": dias_inativo}

    resultado = {
        "obra_id": obra_id,
        "cliente": _fix_latin1_in_utf8(detail.get("clienteNome") or obra_listing.get("clienteNome") or ""),
        "status": detail.get("status") or obra_listing.get("status"),
        "fase_atual_painel": detail.get("faseAtual") or obra_listing.get("faseAtual"),
        "metragem": detail.get("projetoMetragem") or obra_listing.get("projetoMetragem"),
        "consultor": consultor,
        "data_criacao": (detail.get("createdAt") or "")[:10] or None,
        "data_exec_prevista": (detail.get("dataExecucaoPrevista") or "")[:10] or None,
        "data_exec_confirmada": (detail.get("dataExecucaoConfirmada") or "")[:10] or None,
        "data_1a_msg": (primeira_msg or "")[:10] or None,
        "data_ultima_msg": (msgs[-1].get("timestamp") if msgs else "")[:10] or None,
        "n_msgs_telegram": len(msgs),
        "n_ocorrencias": n_ocorrencias,
        "grupo_mix": grupo,
        "fase_derivada": fase_derivada,
        "ciclos_info": ciclos_info,
        "equipe_monofloor": equipe_monofloor,
        "aplicadores_oficiais": aplicadores_oficiais,
        "aplicadores_observados": aplicadores_observados,
        "presenca_monofloor": presenca_monofloor,
        "msgs_por_dia": msgs_por_dia,
        "materiais_enviados": materiais_enviados,
        "marcos": marcos,
        "intervalos": intervalos,
        "dt_total_marcos_dias": dt_total,
        "dt_1a_msg_ate_exec_dias": dt_painel,
        "counts_por_tipo": dict(counts),
        "descarte_msgs": descarte_log,
        "amostra_sem_match": amostra_sem_match,
        "origem_obra": origem_obra,
        "consistencia_material": consistencia_material,
        "estagio": estagio,
        "dias_inativo": dias_inativo,
        "ultima_atividade": ultima_atividade,
        "alerta_parada": alerta_parada,
    }

    # Score preditivo de risco (Camada 3)
    resultado["score_risco"] = calcular_score_risco(resultado)

    return resultado

# ============================================================
# Main
# ============================================================

# ============================================================
# Manifest incremental + rodada em massa
# ============================================================

def carregar_manifest():
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def salvar_manifest(manifest):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def selecionar_universo_massa(todas):
    """Filtra universo D (Qualidade): vivas reais (exclui finalizado/concluido/cancelado)."""
    return [o for o in todas if o.get('status') in STATUS_VIVOS_QUALIDADE]


def aplicar_manifest(universo, manifest):
    """Compara universo atual com manifest. Retorna 4 listas:
    - novas: IDs presentes no universo, ausentes no manifest
    - modificadas: IDs em ambos com updatedAt diferente
    - inalteradas: IDs em ambos com updatedAt igual
    - sumiram: IDs do manifest que não estão mais no universo (status mudou pra final)
    """
    ids_universo = {o['id']: o for o in universo}
    ids_manifest = set(manifest.keys())
    ids_atuais = set(ids_universo.keys())

    novas = []
    modificadas = []
    inalteradas = []
    for oid, obra in ids_universo.items():
        if oid not in manifest:
            novas.append(obra)
            continue
        upd_atual = obra.get('updatedAt', '')
        upd_manifest = manifest[oid].get('ultimo_updatedAt', '')
        if upd_atual != upd_manifest:
            modificadas.append(obra)
        else:
            inalteradas.append(obra)
    sumiram = list(ids_manifest - ids_atuais)
    return novas, modificadas, inalteradas, sumiram


def processar_paralelo(obras_a_processar, workers=WORKERS):
    """Roda timeline_obra em paralelo. Retorna (timelines_ok, erros)."""
    timelines = []
    erros = []
    feitos = 0
    total = len(obras_a_processar)

    def _work(o):
        return timeline_obra(o, o.get('status', '?'))

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_work, o): o for o in obras_a_processar}
        for fut in as_completed(futures):
            o = futures[fut]
            feitos += 1
            try:
                t = fut.result()
                timelines.append(t)
                print(f"     [{feitos:>3}/{total}] ✓ {(t.get('cliente','?') or '?')[:35]:<35} · {len(t.get('marcos', []))} marcos")
            except Exception as e:
                erros.append({'obra_id': o.get('id'), 'cliente': o.get('clienteNome'), 'erro': str(e)[:200]})
                print(f"     [{feitos:>3}/{total}] ✗ {(o.get('clienteNome','?') or '?')[:35]:<35} · ERRO: {str(e)[:80]}")
    return timelines, erros


def main_massa():
    """Modo massa · processa universo D (vivas) com paralelização e manifest incremental."""
    print(f"Timeline obras · MODO MASSA (universo Qualidade · paralelo {WORKERS} workers)")
    print()

    print("[1/5] fetching universo total · /api/projects?limit=5000...")
    todas = fetch(f"{BASE_API}?limit=5000")
    print(f"     · {len(todas)} obras no universo total")

    universo = selecionar_universo_massa(todas)
    print(f"     · {len(universo)} obras vivas (universo D · exclui finalizado/concluido/cancelado)")
    sts = Counter(o.get('status') for o in universo)
    for s, n in sts.most_common():
        print(f"       {s:<25} {n:>3}")
    print()

    print("[2/5] aplicando manifest incremental...")
    manifest = carregar_manifest()
    novas, modificadas, inalteradas, sumiram = aplicar_manifest(universo, manifest)
    print(f"     · novas:        {len(novas)} (entraram no universo)")
    print(f"     · modificadas:  {len(modificadas)} (updatedAt mudou desde última rodada)")
    print(f"     · inalteradas:  {len(inalteradas)} (pulam · sem mudança)")
    print(f"     · sumiram:      {len(sumiram)} (saíram do universo · marcadas arquivadas)")
    print()

    a_processar = novas + modificadas
    if not a_processar:
        # Sem mudanças na API, mas pode ter campo novo (ex: score_risco) a adicionar
        # Carrega timelines anteriores e enriquece
        if SAIDA_MASSA.exists():
            try:
                antigo = json.loads(SAIDA_MASSA.read_text(encoding="utf-8"))
                tl_ant = antigo.get('timelines', [])
                precisa_score = any("score_risco" not in t for t in tl_ant)
                precisa_consultor = any(not t.get("consultor") and (t.get("equipe_monofloor") or {}).get("operacoes") for t in tl_ant)
                if precisa_score or precisa_consultor:
                    print("[3/5] enriquecendo timelines com campos novos...")
                    n_enriq = 0
                    n_fix_c = 0
                    for t in tl_ant:
                        if "score_risco" not in t:
                            t["score_risco"] = calcular_score_risco(t)
                            n_enriq += 1
                        if not t.get("consultor"):
                            eq = t.get("equipe_monofloor") or {}
                            fb = normalizar_consultor(eq.get("operacoes"))
                            if fb:
                                t["consultor"] = fb
                                n_fix_c += 1
                    antigo['gerado_em'] = HOJE.strftime('%Y-%m-%dT%H:%M:%SZ')
                    SAIDA_MASSA.write_text(json.dumps(antigo, ensure_ascii=False, indent=2), encoding="utf-8")
                    print(f"     · {n_enriq} scores + {n_fix_c} consultores enriquecidos · JSON regravado")
                else:
                    print("[3/5] nada a processar · universo sem mudanças desde última rodada.")
            except Exception:
                print("[3/5] nada a processar · universo sem mudanças desde última rodada.")
        else:
            print("[3/5] nada a processar · universo sem mudanças desde última rodada.")
        return

    print(f"[3/5] processando {len(a_processar)} obras em paralelo ({WORKERS} workers)...")
    inicio = time.time()
    timelines_novas, erros = processar_paralelo(a_processar)
    elapsed = time.time() - inicio
    print(f"     · {len(timelines_novas)} timelines geradas em {elapsed:.1f}s ({len(erros)} erros)")
    print()

    # Carrega timelines anteriores das inalteradas (do output anterior se existir)
    print("[4/5] mesclando timelines inalteradas...")
    timelines_anteriores = {}
    if SAIDA_MASSA.exists():
        try:
            antigo = json.loads(SAIDA_MASSA.read_text(encoding="utf-8"))
            for t in antigo.get('timelines', []):
                timelines_anteriores[t.get('obra_id')] = t
        except Exception:
            pass
    timelines_finais = list(timelines_novas)
    for o in inalteradas:
        if o['id'] in timelines_anteriores:
            timelines_finais.append(timelines_anteriores[o['id']])
    print(f"     · {len(timelines_finais)} timelines totais (novas+modificadas+inalteradas reaproveitadas)")

    # Enriquecer consultor: fallback para responsavelOperacoes (cache pode ter consultor=None)
    n_fix_consultor = 0
    for t in timelines_finais:
        if not t.get("consultor"):
            eq = t.get("equipe_monofloor") or {}
            fallback = normalizar_consultor(eq.get("operacoes"))
            if fallback:
                t["consultor"] = fallback
                n_fix_consultor += 1
    if n_fix_consultor:
        print(f"     · {n_fix_consultor} obras com consultor recuperado via responsavelOperacoes")

    # Enriquecer com score preditivo de risco (Camada 3)
    # Roda em todas as timelines (inclusive cache) pra garantir que o campo existe
    n_com_score = 0
    for t in timelines_finais:
        if "score_risco" not in t:
            t["score_risco"] = calcular_score_risco(t)
        if t.get("score_risco"):
            n_com_score += 1
    print(f"     · {n_com_score} obras com score de risco · {len(timelines_finais) - n_com_score} N/A")
    print()

    # Atualiza manifest
    print("[5/5] atualizando manifest + salvando JSON...")
    novo_manifest = {}
    for o in universo:
        novo_manifest[o['id']] = {
            'cliente': o.get('clienteNome', '')[:80],
            'status': o.get('status'),
            'ultimo_updatedAt': o.get('updatedAt', ''),
            'processada_em': HOJE.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
    # Mantém arquivadas no manifest pra histórico (com flag)
    for oid in sumiram:
        if oid in manifest:
            novo_manifest[oid] = {**manifest[oid], 'arquivada_em': HOJE.strftime('%Y-%m-%dT%H:%M:%SZ')}
    salvar_manifest(novo_manifest)

    descarte_agg = {"bot": 0, "transcricao": 0, "sem_match": 0, "dedup": 0, "match": 0}
    amostras_agg = []
    for t in timelines_finais:
        dl = t.get("descarte_msgs") or {}
        for k in descarte_agg:
            descarte_agg[k] += dl.get(k, 0)
        for a in (t.get("amostra_sem_match") or []):
            if len(amostras_agg) < 100:
                amostras_agg.append({**a, "obra": (t.get("cliente") or "?")[:30]})
    total_msgs = sum(descarte_agg.values())
    if total_msgs:
        descarte_agg["taxa_aproveitamento_pct"] = round(descarte_agg["match"] / total_msgs * 100, 1)

    out = {
        'gerado_em': HOJE.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'modo': 'massa',
        'universo_total': len(todas),
        'universo_qualidade': len(universo),
        'distribuicao_status': dict(sts),
        'rodada': {
            'novas': len(novas),
            'modificadas': len(modificadas),
            'inalteradas': len(inalteradas),
            'sumiram': len(sumiram),
            'erros': erros,
            'tempo_processamento_s': round(elapsed, 1),
        },
        'cobertura_regex': descarte_agg,
        'amostra_msgs_sem_match': amostras_agg,
        'taxonomia': TAXONOMIA,
        'timelines': timelines_finais,
    }
    SAIDA_MASSA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_MASSA.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"     · {SAIDA_MASSA}")
    print(f"     · manifest: {MANIFEST_PATH}")
    print()
    print(f"[OK] Massa: {len(timelines_finais)} timelines · {elapsed:.1f}s processando · {len(erros)} erros")

    # Auditoria automática: compara JSON gerado com estado atual do Painel
    print()
    auditar_sincronia(timelines_finais, todas)


def auditar_sincronia(timelines, todas_api):
    """Compara JSON gerado com listing atual do Painel. Grita se divergir."""
    print("[AUDIT] Verificando sincronia com Painel de Obras...")
    painel_idx = {o["id"]: o for o in todas_api}
    STATUS_VIVOS = {'planejamento', 'aguardando_execucao', 'em_execucao', 'reparo',
                    'contrato', 'pausado', 'marcas_rolo_cera', 'aguardando_clima'}

    problemas = []

    # Status divergente
    for t in timelines:
        oid = t.get("obra_id", "")
        if oid in painel_idx:
            sp = painel_idx[oid].get("status", "")
            sj = t.get("status", "")
            if sp != sj:
                problemas.append(f"  STATUS | {t['cliente'][:40]:40s} | nosso={sj} | painel={sp}")

    # Obras vivas no Painel que não estão no JSON
    json_ids = {t.get("obra_id") for t in timelines}
    ausentes = [o for o in todas_api if o.get("status") in STATUS_VIVOS and o["id"] not in json_ids]
    for o in ausentes:
        problemas.append(f"  AUSENTE | {(o.get('clienteNome') or '?')[:40]:40s} | status={o.get('status')}")

    if problemas:
        print(f"[AUDIT] ⚠ {len(problemas)} DIVERGENCIAS DETECTADAS:")
        for p in problemas[:20]:
            print(p)
        if len(problemas) > 20:
            print(f"  ... e mais {len(problemas) - 20}")
    else:
        print(f"[AUDIT] ✓ Sincronizado · {len(timelines)} obras = {sum(1 for o in todas_api if o.get('status') in STATUS_VIVOS)} no Painel")


def main_historico():
    """Modo histórico · processa TODAS as 1042 obras (1x · sem manifest · referência permanente)."""
    print(f"Timeline obras · MODO HISTÓRICO (universo TOTAL · paralelo {WORKERS} workers)")
    print()

    print("[1/4] fetching universo total · /api/projects?limit=5000...")
    todas = fetch(f"{BASE_API}?limit=5000")
    print(f"     · {len(todas)} obras no universo total")
    sts = Counter(o.get('status') for o in todas)
    for s, n in sts.most_common():
        print(f"       {s:<25} {n:>3}")
    print()

    print(f"[2/4] processando {len(todas)} obras em paralelo ({WORKERS} workers)...")
    inicio = time.time()
    timelines, erros = processar_paralelo(todas)
    elapsed = time.time() - inicio
    print(f"     · {len(timelines)} timelines geradas em {elapsed:.1f}s ({len(erros)} erros)")
    print()

    print("[3/4] preparando saída...")
    saida_historico = ROOT / "dados" / f"timeline_historico_{HOJE.strftime('%Y-%m-%d')}.json"
    out = {
        'gerado_em': HOJE.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'modo': 'historico',
        'universo_total': len(todas),
        'distribuicao_status': dict(sts),
        'rodada': {
            'erros': erros,
            'tempo_processamento_s': round(elapsed, 1),
        },
        'taxonomia': TAXONOMIA,
        'timelines': timelines,
    }

    print("[4/4] salvando JSON...")
    saida_historico.parent.mkdir(parents=True, exist_ok=True)
    saida_historico.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"     · {saida_historico}")
    print()
    print(f"[OK] Histórico: {len(timelines)} timelines · {elapsed:.1f}s processando · {len(erros)} erros")
    print(f"     Frozen reference (não atualiza · use pra calibrar mediana populacional)")


def main():
    # Flag --massa ativa modo escalado vivas (manifest incremental)
    if '--massa' in sys.argv:
        return main_massa()
    # Flag --historico ativa modo 1042 obras · 1x · sem manifest
    if '--historico' in sys.argv:
        return main_historico()

    print(f"Timeline 10 obras-piloto · seed=20260506")
    print()

    print("[1/4] fetching /api/projects?limit=5000...")
    todas = fetch(f"{BASE_API}?limit=5000")
    print(f"     · {len(todas)} obras no universo total")
    print()

    print("[2/4] selecionando mix (5 finalizadas + 3 execução + 2 reparo)...")
    selecionadas = selecionar_mix(todas)
    n_total = sum(len(v) for v in selecionadas.values())
    for grupo, lst in selecionadas.items():
        print(f"     · {grupo}: {len(lst)} obras")
    print(f"     · TOTAL: {n_total}")
    print()

    print("[3/4] construindo timelines...")
    inicio = time.time()
    timelines = []
    for grupo, obras in selecionadas.items():
        for o in obras:
            try:
                t = timeline_obra(o, grupo)
                timelines.append(t)
                print(f"     ✓ {t['cliente'][:30]:30} · {len(t['marcos'])} marcos · Δt={t['dt_total_marcos_dias']}d (marcos) · {t['dt_1a_msg_ate_exec_dias']}d (msg→exec)")
            except Exception as e:
                print(f"     ✗ {o.get('clienteNome','?')}: {e}")
    print()

    # Estatísticas globais
    finalizadas = [t for t in timelines if t["grupo_mix"] == "finalizadas"]
    dts_marcos = [t["dt_total_marcos_dias"] for t in finalizadas if t["dt_total_marcos_dias"] is not None]
    dts_painel = [t["dt_1a_msg_ate_exec_dias"] for t in finalizadas if t["dt_1a_msg_ate_exec_dias"] is not None]

    def mediana(lst):
        if not lst:
            return None
        s = sorted(lst)
        n = len(s)
        return s[n//2] if n % 2 else (s[n//2-1] + s[n//2]) / 2

    estatisticas = {
        "n_total": len(timelines),
        "por_grupo": {grupo: sum(1 for t in timelines if t["grupo_mix"] == grupo) for grupo in MIX},
        "finalizadas_dt_marcos": {
            "n": len(dts_marcos),
            "mediana": mediana(dts_marcos),
            "min": min(dts_marcos) if dts_marcos else None,
            "max": max(dts_marcos) if dts_marcos else None,
        },
        "finalizadas_dt_msg_ate_exec": {
            "n": len(dts_painel),
            "mediana": mediana(dts_painel),
            "min": min(dts_painel) if dts_painel else None,
            "max": max(dts_painel) if dts_painel else None,
        },
        "comparativo_rodrigo_stats": {
            "pre_execucao_mediana_d": 107,
            "execucao_mediana_d": 26,
            "nota": "valores oficiais do rodrigo-stats · sanity check",
        },
    }

    print("[4/4] salvando JSON...")
    out = {
        "gerado_em": HOJE.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed": 20260506,
        "mix_alvo": {grupo: n for grupo, (n, _) in MIX.items()},
        "taxonomia": TAXONOMIA,
        "estatisticas": estatisticas,
        "timelines": timelines,
    }
    SAIDA_PILOTO.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_PILOTO.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    elapsed = time.time() - inicio
    print(f"     ✓ {SAIDA_PILOTO}")
    print(f"     · {elapsed:.1f}s · {len(timelines)} timelines")
    print()
    print("Resumo:")
    print(f"  · finalizadas Δt marcos · mediana={estatisticas['finalizadas_dt_marcos']['mediana']}d (rodrigo-stats: 107d pré-exec)")
    print(f"  · finalizadas Δt msg→exec · mediana={estatisticas['finalizadas_dt_msg_ate_exec']['mediana']}d")


if __name__ == "__main__":
    main()
