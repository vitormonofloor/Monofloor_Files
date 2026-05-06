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

import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import setup_utf8

setup_utf8()

ROOT = Path(__file__).parent.parent
JORNADAS_PATH = ROOT / "dados" / "jornadas.json"
JORNADAS_DIR = ROOT / "_jornadas"
BASE_API = "https://cliente.monofloor.cloud/api/projects"

# Obras-piloto (hardcoded · Fase A)
OBRAS_PILOTO = [
    "a79f00f0-19b1-43d4-b9d7-6ab8d219c205",  # KRYSTAL LURI NUMA
    "3e5c6392-af93-427a-9e29-3a927e6d5dc6",  # GURGEL DALFONSO
]

HOJE = datetime.now(timezone.utc)
HOJE_DATE = HOJE.date()

# Janelas e thresholds
HIBERNACAO_GAP_DIAS = 30  # gap mínimo entre msgs pra contar hibernação
EXEC_CLUSTER_MSGS_DIA = 5  # ≥N msgs/dia = cluster denso (execução)
EXEC_JANELA_DIAS = 7  # janela ao redor de dataExecucaoConfirmada pra cluster

# ============================================================
# Utilitários de fetch e parsing
# ============================================================

def fetch(url: str, max_retries: int = 2):
    last_err = None
    for tentativa in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "lab-orion/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
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
PAD_VT_REALIZADA = re.compile(
    r"\b("
    r"vt\s+(de\s+)?(aferi[çc][aã]o|entrada)\s+(realizada|feita|ok|conclu[ií]da)"
    r"|vt\s+ok"
    r"|visita\s+(de\s+(qualidade|aferi[çc][aã]o|entrada)\s+)?realizada"
    r"|visita\s+t[eé]cnica\s+realizada"
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
PAD_FINALIZACAO = re.compile(r"\b(obra\s+(finaliz|conclu)|verniz\s+finaliz|piso\s+(finaliz|aprovad|conclu))\b", re.IGNORECASE)
PAD_APROVACAO_CLIENTE = re.compile(r"\b(obra\s+aprovada|cliente\s+aprov(ou|ado)|aprov(ado|ação).*cliente|v[íi]deo\s+de\s+aprova[çc][aã]o)\b", re.IGNORECASE)

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

# Problemas
PAD_PROBLEMA = re.compile(r"\b(trinca|fissura|rachadura|infiltrac[aã]o|patolog|errad[ao]|atras[ao]u?|problema|defeito|reclamac[aã]o)\b", re.IGNORECASE)


def detectar_marco_em_msg(msg, tipo_pad, padrao):
    """Verifica se a msg tem o padrão. Retorna dict com info do marco ou None."""
    texto = msg.get("content") or ""
    m = padrao.search(texto)
    if not m:
        return None
    return {
        "tipo": tipo_pad,
        "data": (msg.get("timestamp") or "")[:10],
        "data_iso": msg.get("timestamp"),
        "autor": (msg.get("sender") or "?")[:35],
        "trecho": texto[:160].replace("\n", " ").strip(),
        "msg_id": msg.get("id"),
        "match": m.group(0)[:50],
    }


# ============================================================
# Cálculo de fases (cluster por densidade)
# ============================================================

def calcular_fases(msgs_ordenadas, data_exec_confirmada, data_criacao):
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
    cluster_exec_inicio, cluster_exec_fim = None, None
    if data_exec_confirmada:
        janela_ini = data_exec_confirmada - timedelta(days=EXEC_JANELA_DIAS)
        janela_fim = data_exec_confirmada + timedelta(days=EXEC_JANELA_DIAS)
        dias_no_cluster = [d for d in dias_com_msg if janela_ini <= d <= janela_fim and msgs_por_dia[d] >= EXEC_CLUSTER_MSGS_DIA]
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
        for idx, (h_ini, h_fim, gap) in enumerate(hibernacoes):
            n_msgs_hib = sum(n for d, n in msgs_por_dia.items() if h_ini < d < h_fim)
            fases.append({
                "nome": f"Hibernação{' #' + str(idx+1) if len(hibernacoes) > 1 else ''}",
                "inicio": h_ini.isoformat(),
                "fim": h_fim.isoformat(),
                "duracao_dias": gap,
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
        ("vt_agendada", PAD_VT_AGENDADA),
        ("vt_realizada", PAD_VT_REALIZADA),
        ("cor_aprovada", PAD_COR_APROVADA),
        ("inicio_anunciado", PAD_INICIO_ANUNCIADO),
        ("material_produzido", PAD_MATERIAL_PRODUZIDO),
        ("aprovacao_cliente", PAD_APROVACAO_CLIENTE),
        ("finalizacao", PAD_FINALIZACAO),
    ]
    # Pra cada tipo · mantém SÓ o PRIMEIRO match cronológico (a menos que sejam eventos repetíveis)
    UNICOS = {"contrato_assinado", "cor_aprovada", "vt_agendada", "vt_realizada", "material_produzido"}
    primeiro_de_cada = {}
    todos = []

    for m in msgs_ordenadas:
        # Filtra cards de bot
        if is_card_bot(m.get("content") or ""):
            continue
        for tipo, pad in padroes:
            marco = detectar_marco_em_msg(m, tipo, pad)
            if marco:
                if tipo in UNICOS:
                    if tipo not in primeiro_de_cada:
                        primeiro_de_cada[tipo] = marco
                else:
                    # eventos repetíveis (finalizacao, aprovacao_cliente, inicio_anunciado) · dedup por dia
                    chave = (tipo, marco["data"])
                    if chave not in {(t["tipo"], t["data"]) for t in todos}:
                        todos.append(marco)

    marcos = list(primeiro_de_cada.values()) + todos
    return sorted(marcos, key=lambda x: x["data_iso"] or "")


def detectar_solicitacoes_material(msgs_ordenadas, cluster_exec_inicio, cluster_exec_fim):
    """Detecta solicitações de material durante execução (regex em msgs)."""
    if not cluster_exec_inicio:
        return []
    solicitacoes = []
    janela_ini = (cluster_exec_inicio - timedelta(days=2)).isoformat()
    janela_fim = (cluster_exec_fim + timedelta(days=2)).isoformat() if cluster_exec_fim else HOJE.isoformat()
    for m in msgs_ordenadas:
        ts = (m.get("timestamp") or "")[:10]
        if not (janela_ini <= ts <= janela_fim):
            continue
        texto = m.get("content") or ""
        if PAD_MAT_SOLIC.search(texto) or PAD_TELA_TOTAL.search(texto):
            solicitacoes.append({
                "data": ts,
                "autor": (m.get("sender") or "?")[:30],
                "trecho": texto[:200].replace("\n", " ").strip(),
                "tela_total": bool(PAD_TELA_TOTAL.search(texto)),
            })
    return solicitacoes


def detectar_consumo(msgs_ordenadas):
    """Extrai menções a quantidades consumidas/sobras (regex 'X kits/baldes')."""
    consumos = []
    sobras = []
    for m in msgs_ordenadas:
        texto = m.get("content") or ""
        # Quantidades consumidas
        for q_match in PAD_QTD_KIT.finditer(texto):
            consumos.append({
                "data": (m.get("timestamp") or "")[:10],
                "autor": (m.get("sender") or "?")[:30],
                "qtd": q_match.group(1),
                "unidade": q_match.group(2).lower(),
                "trecho": texto[:120].replace("\n", " ").strip(),
            })
        # Sobras
        if PAD_SOBROU.search(texto):
            sobras.append({
                "data": (m.get("timestamp") or "")[:10],
                "autor": (m.get("sender") or "?")[:30],
                "trecho": texto[:160].replace("\n", " ").strip(),
            })
    return consumos, sobras


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
                "autor": (m.get("sender") or "?")[:30],
                "trecho": texto[:200].replace("\n", " ").strip(),
            })
    return sinais


# ============================================================
# Equipe (cruza fontes)
# ============================================================

def montar_equipe(detail, equipe_endpoint, msgs_ordenadas):
    """Cruza /equipe + detail (responsavel*) + senders das msgs Telegram."""
    monofloor = {
        "atendimento": detail.get("responsavelAtendimento"),
        "operacoes": detail.get("responsavelOperacoes"),
        "consultor": detail.get("consultorNome"),
        "vendedor": (detail.get("acessoDetalhes") or {}).get("vendedor"),
    }
    prestadores_oficiais = []
    for p in (equipe_endpoint or {}).get("prestadores", []) or []:
        prestadores_oficiais.append({
            "nome": p.get("nome"),
            "funcao": p.get("funcao"),
        })

    # Senders das msgs Telegram (top 15 por contagem)
    sender_count = Counter()
    sender_primeira = {}
    sender_ultima = {}
    for m in msgs_ordenadas:
        s = (m.get("sender") or "").strip()
        if not s or s.lower() == "🎬 transcrição" or s.lower() == "🎙️ transcrição":
            continue
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

    return {"monofloor": monofloor, "prestadores_oficiais": prestadores_oficiais, "senders_telegram": senders}


# ============================================================
# Padrões observados
# ============================================================

def detectar_padroes(jornada):
    padroes = []
    if jornada["tempo_hibernacao_dias"] and jornada["tempo_hibernacao_dias"] >= 60:
        padroes.append(f"hibernacao_longa · obra ficou {jornada['tempo_hibernacao_dias']}d praticamente parada")
    if jornada["tempo_execucao_dias"] and jornada["tempo_total_dias"]:
        pct = jornada["tempo_execucao_dias"] / jornada["tempo_total_dias"] * 100
        if pct < 5:
            padroes.append(f"execucao_concentrada · só {pct:.1f}% do tempo total ({jornada['tempo_execucao_dias']}d de {jornada['tempo_total_dias']}d)")
    if jornada.get("solicitacoes_material") and any(s.get("tela_total") for s in jornada["solicitacoes_material"]):
        padroes.append("mudanca_escopo_dia_execucao · cliente pediu tela total durante execução")
    return padroes


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

def construir_jornada(obra_id):
    print(f"  · {obra_id[:8]} · fetch detail + telegram + ocorrencias + materiais + equipe...")
    detail = fetch(f"{BASE_API}/{obra_id}")
    msgs_resp = fetch(f"{BASE_API}/{obra_id}/messages?source=telegram&limit=2000") or {}
    ocorrencias = fetch_safe(f"{BASE_API}/{obra_id}/ocorrencias") or []
    materiais = fetch_safe(f"{BASE_API}/{obra_id}/materiais") or {}
    equipe_ep = fetch_safe(f"{BASE_API}/{obra_id}/equipe") or {}

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
    cluster_exec_inicio, cluster_exec_fim = None, None
    if data_exec_confirmada and msgs_ordenadas:
        msgs_por_dia = defaultdict(int)
        for m in msgs_ordenadas:
            dt = parse_iso(m.get("timestamp"))
            if dt:
                msgs_por_dia[dt.date()] += 1
        janela_ini = data_exec_confirmada - timedelta(days=EXEC_JANELA_DIAS)
        janela_fim = data_exec_confirmada + timedelta(days=EXEC_JANELA_DIAS)
        dias_no_cluster = sorted([d for d in msgs_por_dia if janela_ini <= d <= janela_fim and msgs_por_dia[d] >= EXEC_CLUSTER_MSGS_DIA])
        if dias_no_cluster:
            cluster_exec_inicio = dias_no_cluster[0]
            cluster_exec_fim = dias_no_cluster[-1]

    # Cálculos
    tempo_total = None
    if primeira_msg and data_exec_confirmada:
        tempo_total = (data_exec_confirmada - primeira_msg.date()).days
    tempo_execucao = None
    if cluster_exec_inicio and cluster_exec_fim:
        tempo_execucao = (cluster_exec_fim - cluster_exec_inicio).days + 1

    # Hibernações totais
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
            tempo_hibernacao += gap

    # Fases
    fases = calcular_fases(msgs_ordenadas, data_exec_confirmada, data_criacao.date() if data_criacao else None)

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
        "produtos": sorted({(m.get("produto") or "").strip() for m in mat_items if m.get("produto")}),
        "cores": sorted({(m.get("cor") or "").strip() for m in mat_items if m.get("cor")}),
    }

    # Solicitações + consumo + sobras
    solicitacoes = detectar_solicitacoes_material(msgs_ordenadas, cluster_exec_inicio, cluster_exec_fim)
    consumos, sobras = detectar_consumo(msgs_ordenadas)

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

    # Equipe
    equipe = montar_equipe(detail, equipe_ep, msgs_ordenadas)

    # Endereço completo
    endereco = detail.get("projetoEndereco") or "—"

    # Monta jornada
    jornada = {
        "obra_id": obra_id,
        "cliente": detail.get("clienteNome"),
        "endereco": endereco,
        "metragem": detail.get("projetoMetragem") or mat_totals.get("totalM2"),
        "produtos": materiais_resumo["produtos"],
        "cores": materiais_resumo["cores"],
        "data_1a_msg": primeira_msg.date().isoformat() if primeira_msg else None,
        "data_ultima_msg": ultima_msg.date().isoformat() if ultima_msg else None,
        "data_criacao_painel": data_criacao_iso[:10] if data_criacao_iso else None,
        "data_exec_prevista": data_exec_prevista.isoformat() if data_exec_prevista else None,
        "data_exec_confirmada": data_exec_confirmada.isoformat() if data_exec_confirmada else None,
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
            "ocorrencias_formais": ocorrencias_fmt,
            "sinais_msg_telegram": problemas_msg,
        },
        "gerado_em": HOJE.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    jornada["padroes"] = detectar_padroes(jornada)

    return jornada


# ============================================================
# Main
# ============================================================

def main():
    JORNADAS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Gerando jornadas pra {len(OBRAS_PILOTO)} obras-piloto · só Telegram")
    print()

    out = {
        "gerado_em": HOJE.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "obras": [],
    }
    inicio = time.time()
    for oid in OBRAS_PILOTO:
        try:
            j = construir_jornada(oid)
            out["obras"].append(j)
            md = gerar_narrativa_md(j)
            md_path = JORNADAS_DIR / f"{oid}.md"
            md_path.write_text(md, encoding="utf-8")
            print(f"     ✓ {j['cliente']} · {j.get('tempo_total_dias','?')}d total · {j.get('tempo_execucao_dias','?')}d exec · {len(j['marcos'])} marcos · MD em {md_path.name}")
        except Exception as e:
            print(f"     ✗ ERRO: {e}")
            raise

    # Salva JSON
    JORNADAS_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    elapsed = time.time() - inicio
    print()
    print(f"[OK] {JORNADAS_PATH} · {elapsed:.1f}s · {len(out['obras'])} obras")
    print(f"[OK] Markdowns em {JORNADAS_DIR}")


if __name__ == "__main__":
    main()
