"""
gerar_html_timelines.py · HTML de visualização das timelines
==============================================================

Lê dados/timeline_10obras.json e gera HTML standalone.
Tema visual replica jornada.html do Lab Orion (cream #f0ebe3 + gold #b8884a + Plus Jakarta Sans + JetBrains Mono).

Uso: python agente/gerar_html_timelines.py
"""

import html
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
JSON_MASSA = ROOT / "dados" / "timeline_obras.json"
JSON_PILOTO = ROOT / "dados" / "timeline_10obras.json"
HTML_MASSA = ROOT / "dados" / "timeline_obras.html"
HTML_PILOTO = ROOT / "dados" / "timeline_10obras.html"

# Obras destrinchadas manualmente pra calibrar vocabulário (match por substring no clienteNome)
OBRAS_DESTRINCHADAS = [
    # Sessão 06/05
    "P2B ENGENHARIA",
    "SILVANA PANDOLFI",
    "PALLOMA BIANCA",
    # Sessão 08/05
    "GINACERCHI CREMA",
    "DONA CORINA",
    # Sessão 12/05 · fechamento da meta de 10
    "JEAN LUC SENAC",
    "ARIANE RIBEIRO",
    "GUSTAVO FONTES",
    "MARCOS JOS",  # MARCOS JOSÉ VEIGA GOMES (encoding · matchar substring sem acentos)
    "JORGE LUIZ BARBIERI",
]

def is_destrinchada(cliente):
    if not cliente:
        return False
    cli_up = cliente.upper()
    return any(d in cli_up for d in OBRAS_DESTRINCHADAS)


# ============================================================
# Correlações · interpretação por encadeamento de marcos
# Cada função recebe lista de marcos e retorna lista de insights
# ============================================================

def _parse_d(s):
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _diff_dias(a, b):
    da, db = _parse_d(a), _parse_d(b)
    if not da or not db:
        return None
    return (da - db).days


def derivar_insights(obra):
    """Deriva insights correlacionais a partir dos marcos da obra.
    Retorna lista de {tipo, severidade, titulo, descricao, evidencia}.
    Severidade: 'alta' (bandeira vermelha) · 'media' · 'info'.
    """
    insights = []
    marcos = obra.get("marcos") or []
    if not marcos:
        return insights

    by_tipo = {}
    for m in marcos:
        by_tipo.setdefault(m["tipo"], []).append(m)

    # Helper · retorna lista de marcos de um tipo
    def todos(tipo):
        return by_tipo.get(tipo) or []

    # 1. FINALIZAÇÃO SEM APROVAÇÃO FORMAL
    if todos("finalizacao") and not todos("aprovacao_cliente"):
        fin = todos("finalizacao")[0]
        insights.append({
            "tipo": "finalizacao_sem_aprovacao",
            "severidade": "alta",
            "titulo": "Finalização sem aprovação formal",
            "descricao": f"Obra registrada como finalizada em {fmt_data(fin['data'])} sem 'cliente aprovou' anterior nas mensagens.",
            "evidencia": [fin["data"]],
        })

    # 2. RETRABALHO RELÂMPAGO (aprovação seguida de reprovação em <14d)
    aprov = todos("aprovacao_cliente")
    reprov = todos("reprovacao_retorno")
    for a in aprov:
        for r in reprov:
            d = _diff_dias(r["data"], a["data"])
            if d is not None and 0 < d <= 14:
                insights.append({
                    "tipo": "retrabalho_relampago",
                    "severidade": "alta",
                    "titulo": f"Retrabalho em {d} dias após aprovação",
                    "descricao": f"Cliente aprovou em {fmt_data(a['data'])} mas houve reprovação/retorno em {fmt_data(r['data'])}.",
                    "evidencia": [a["data"], r["data"]],
                })
                break  # só registra a primeira ocorrência

    # 3. POSTERGAÇÃO CUMULATIVA (3+ postergações em 60 dias)
    posts = sorted(todos("obra_postergada") + todos("postergacao_explicita"), key=lambda m: m["data"])
    if len(posts) >= 3:
        primeira = posts[0]["data"]
        ultima = posts[-1]["data"]
        span = _diff_dias(ultima, primeira) or 0
        insights.append({
            "tipo": "postergacao_cumulativa",
            "severidade": "alta" if len(posts) >= 4 else "media",
            "titulo": f"{len(posts)} postergações registradas",
            "descricao": f"Obra postergou {len(posts)}x entre {fmt_data(primeira)} e {fmt_data(ultima)} ({span}d). Sinal de cronograma instável ou cliente recorrente em adiar.",
            "evidencia": [p["data"] for p in posts],
        })

    # 4. ESCOPO INSTÁVEL (mudanças de escopo recorrentes)
    escopo_mudancas = todos("escopo_atualizado") + todos("aditivo_negociando") + todos("aditivo_aprovado")
    if len(escopo_mudancas) >= 3:
        insights.append({
            "tipo": "escopo_instavel",
            "severidade": "media",
            "titulo": f"Escopo mudou {len(escopo_mudancas)} vezes",
            "descricao": "Múltiplas atualizações/aditivos no escopo · processo comercial pode estar fechando obra com requisitos incompletos.",
            "evidencia": [m["data"] for m in escopo_mudancas[:5]],
        })

    # 5. GAPS DE PARALISAÇÃO · categorizados por gravidade real
    # 45-59d  → pausa_normal       (info · feriado, férias, cliente fora)
    # 60-89d  → pausa_preocupante  (media · obra parando)
    # 90-179d → obra_parada        (alta · paralisação formal)
    # 180+d   → obra_zumbi         (crítica · obra abandonada)
    if len(marcos) >= 2:
        marcos_ord = sorted(marcos, key=lambda m: m.get("data") or "")
        gaps_encontrados = []
        for i in range(1, len(marcos_ord)):
            d = _diff_dias(marcos_ord[i]["data"], marcos_ord[i-1]["data"])
            if d and d >= 45:
                janela_ini = marcos_ord[i-1]["data"]
                janela_fim = marcos_ord[i]["data"]
                # Há postergação registrada nesse intervalo?
                tem_post = any(janela_ini <= p["data"] <= janela_fim for p in posts)
                if tem_post:
                    continue
                gaps_encontrados.append({"dias": d, "ini": janela_ini, "fim": janela_fim})
        # Reporta até 2 maiores gaps (descendente · pior caso primeiro)
        gaps_encontrados.sort(key=lambda g: -g["dias"])
        for g in gaps_encontrados[:2]:
            d = g["dias"]
            if d >= 180:
                tipo = "obra_zumbi"
                sev = "critica"
                titulo = f"Obra zumbi · {d} dias sem registro"
                desc = f"Gap crítico de {d} dias entre {fmt_data(g['ini'])} e {fmt_data(g['fim'])} sem postergação declarada · obra possivelmente abandonada."
            elif d >= 90:
                tipo = "obra_parada"
                sev = "alta"
                titulo = f"Obra parada · {d} dias sem registro"
                desc = f"Gap de {d} dias entre {fmt_data(g['ini'])} e {fmt_data(g['fim'])} sem postergação declarada · paralisação formal."
            elif d >= 60:
                tipo = "pausa_preocupante"
                sev = "media"
                titulo = f"Pausa preocupante · {d} dias"
                desc = f"Obra ficou {d} dias sem marcos entre {fmt_data(g['ini'])} e {fmt_data(g['fim'])} sem postergação declarada."
            else:
                tipo = "pausa_normal"
                sev = "info"
                titulo = f"Pausa normal · {d} dias"
                desc = f"Pausa de {d} dias entre {fmt_data(g['ini'])} e {fmt_data(g['fim'])} · provavelmente feriado/férias/cliente fora."
            insights.append({
                "tipo": tipo,
                "severidade": sev,
                "titulo": titulo,
                "descricao": desc,
                "evidencia": [g["ini"], g["fim"]],
            })

    # 6. COBRANÇA RECORRENTE (aplicador silencioso)
    cobs = todos("cobranca_status")
    if len(cobs) >= 5:
        insights.append({
            "tipo": "cobranca_recorrente",
            "severidade": "media",
            "titulo": f"{len(cobs)} cobranças de status",
            "descricao": "Pessoal Monofloor cobrou status do aplicador várias vezes · aplicador silencioso ou comunicação fragilizada.",
            "evidencia": [c["data"] for c in cobs[:5]],
        })

    # 7. TEMPO ADITIVO (negociação → aprovação)
    aditivos_neg = todos("aditivo_negociando")
    aditivos_apr = todos("aditivo_aprovado")
    if aditivos_neg and aditivos_apr:
        primeiro_neg = aditivos_neg[0]["data"]
        primeiro_apr = aditivos_apr[0]["data"]
        d = _diff_dias(primeiro_apr, primeiro_neg)
        if d is not None and d > 0:
            insights.append({
                "tipo": "tempo_aditivo",
                "severidade": "info",
                "titulo": f"Aditivo aprovado em {d} dias",
                "descricao": f"Negociação iniciou em {fmt_data(primeiro_neg)} e foi aprovada em {fmt_data(primeiro_apr)}.",
                "evidencia": [primeiro_neg, primeiro_apr],
            })

    # 8. INTERRUPÇÃO MATERIAL RECORRENTE
    interr = todos("interrupcao_material")
    if len(interr) >= 2:
        insights.append({
            "tipo": "interrupcao_recorrente",
            "severidade": "alta",
            "titulo": f"{len(interr)} interrupções por material",
            "descricao": "Falta de material parou a obra mais de uma vez · logística falhando recorrente.",
            "evidencia": [i["data"] for i in interr],
        })

    # 9. EVENTOS EXTERNOS · obra com problemas fora da alçada Monofloor
    eventos_ext = todos("evento_externo")
    if eventos_ext:
        n = len(eventos_ext)
        sev = "alta" if n >= 3 else ("media" if n == 2 else "info")
        insights.append({
            "tipo": "eventos_externos",
            "severidade": sev,
            "titulo": f"{n} evento{'s' if n != 1 else ''} fora da alçada Monofloor",
            "descricao": "Problemas externos afetando a obra (vazamentos, terceiros, civil pendente) · não é falha da equipe Monofloor mas trava o cronograma.",
            "evidencia": [e["data"] for e in eventos_ext[:5]],
        })

    return insights

# Prefere massa se existir · fallback piloto
if JSON_MASSA.exists():
    JSON_PATH = JSON_MASSA
    HTML_PATH = HTML_MASSA
else:
    JSON_PATH = JSON_PILOTO
    HTML_PATH = HTML_PILOTO

# Cores dos marcos · alinhadas com paleta de fases do jornada.html
COR_MARCO = {
    # Comercial (azul soft do planejamento)
    "contrato_assinado":      "#7ea0b7",
    "amostra_solicitada":     "#7ea0b7",
    "cor_aprovada":           "#7ea0b7",
    "cobranca_cor":           "#c45a5a",
    # Escopo (cobre · gold-soft)
    "escopo_em_revisao":      "#d4a548",
    "escopo_aprovado":        "#b8884a",
    "escopo_atualizado":      "#d4a548",
    "aditivo_negociando":     "#c45a5a",
    "aditivo_aprovado":       "#7ea0b7",
    # Vistoria (cinza cool)
    "vt_agendada":            "#9bbacc",
    "vt_realizada":           "#7ea0b7",
    "vt_entrada_realizada":   "#7ea0b7",
    "relatorio_vt_qualidade": "#8b5cf6",
    "vistoria_cliente":       "#8b5cf6",
    # Logística (despertar · amber)
    "equipe_definida":        "#e8c078",
    "material_produzido":     "#e8c078",
    "material_entregue":      "#5fa073",
    "inicio_anunciado":       "#f5d199",
    "anuncio_nova_data":      "#f5d199",
    # Execução (verde da fase execução)
    "aviso_chegada":          "#a8d4b3",
    "equipe_chegou":          "#7eb88d",
    "camada_produto":         "#5fa073",
    "ultima_camada":          "#2a5a18",
    "solicitacao_material":   "#e8c078",  # amber · troca normal de material
    "cobranca_status":        "#c45a5a",  # vermelho · sinal de fricção
    # Aprovação (verde escuro · sucesso)
    "aprovacao_cliente":      "#2a5a18",
    "finalizacao":            "#2a5a18",
    # Problemas (vermelho)
    "obra_postergada":        "#c45a5a",
    "postergacao_explicita":  "#c45a5a",
    "reprovacao_retorno":     "#c45a5a",
    "troca_aplicador":        "#e07878",
    "interrupcao_material":   "#e07878",
    "dia_sem_expediente":     "#a89e92",
    "ocorrencia_formal":      "#8b1538",  # bordô · marca da operação · severo
    "evento_externo":         "#6b21a8",  # roxo · problema fora da alçada Monofloor
}

LABELS_MARCO = {
    "contrato_assinado":      "Contrato assinado",
    "amostra_solicitada":     "Amostra solicitada",
    "cor_aprovada":           "Cor aprovada",
    "cobranca_cor":           "Cobrança de cor",
    "escopo_em_revisao":      "Escopo em revisão",
    "escopo_aprovado":        "Escopo aprovado",
    "escopo_atualizado":      "Escopo atualizado",
    "aditivo_negociando":     "Aditivo em negociação",
    "aditivo_aprovado":       "Aditivo aprovado",
    "vt_agendada":            "VT agendada",
    "vt_realizada":           "VT realizada",
    "vt_entrada_realizada":   "VT de entrada",
    "relatorio_vt_qualidade": "Relatório VT qualidade",
    "vistoria_cliente":       "Vistoria cliente",
    "equipe_definida":        "Equipe definida",
    "material_produzido":     "Material produzido",
    "material_entregue":      "Material entregue",
    "inicio_anunciado":       "Início anunciado",
    "anuncio_nova_data":      "Nova data de entrada",
    "aviso_chegada":          "Aviso de chegada",
    "equipe_chegou":          "Equipe chegou",
    "camada_produto":         "Camada aplicada",
    "ultima_camada":          "Última camada",
    "solicitacao_material":   "Solicitação material",
    "cobranca_status":        "Cobrança de status",
    "aprovacao_cliente":      "Cliente aprovou",
    "finalizacao":            "Finalização",
    "obra_postergada":        "Postergação 🚨",
    "postergacao_explicita":  "Postergação",
    "reprovacao_retorno":     "Reprovação · retorno",
    "troca_aplicador":        "Troca de aplicador",
    "interrupcao_material":   "Falta de material",
    "dia_sem_expediente":     "Sem expediente",
    "ocorrencia_formal":      "Ocorrência formal",
    "evento_externo":         "Evento externo · fora da alçada",
}


def fmt_data(s):
    if not s:
        return "—"
    try:
        d = datetime.strptime(s[:10], "%Y-%m-%d")
        return d.strftime("%d/%m/%y")
    except Exception:
        return s[:10]


def card_marco(m, dias_desde_inicio=None):
    cor = COR_MARCO.get(m["tipo"], "#a89e92")
    label = LABELS_MARCO.get(m["tipo"], m["tipo"].replace("_", " "))
    autor = html.escape(m.get("autor") or "")
    trecho = html.escape((m.get("trecho") or "").strip())
    dia_meta = f' · <span class="marco-card-dia">+{dias_desde_inicio}d</span>' if dias_desde_inicio is not None else ""
    return f"""
    <div class="marco-card" title="{trecho}">
      <span class="marco-card-bola" style="background:{cor}"></span>
      <span class="marco-card-data">{fmt_data(m["data"])}{dia_meta}</span>
      <span class="marco-card-label">{html.escape(label)}</span>
      <span class="marco-card-autor">{autor}</span>
    </div>
    """


def agrupar_marcos_por_fase(marcos, taxonomia):
    """Agrupa marcos por (fase, marco_principal) preservando ordem cronológica dentro de cada principal."""
    grupos = {}  # fase_key → {marco_principal_key → [marcos]}
    for m in marcos:
        fase_k = m.get("fase") or "sem_fase"
        mp_k = m.get("marco_principal") or "outros"
        grupos.setdefault(fase_k, {}).setdefault(mp_k, []).append(m)
    return grupos


def renderizar_grupos(marcos, taxonomia):
    """Renderiza marcos como Kanban · cada fase = 1 coluna lado a lado.
    Colunas vazias mostram '—' pra preservar visualmente o fluxo de fases."""
    if not marcos:
        return ""

    grupos = agrupar_marcos_por_fase(marcos, taxonomia)

    # Ordem das fases da taxonomia recebida (já filtrada pelo chamador)
    def ordem_fase(k):
        return (taxonomia.get(k) or {}).get("ordem", 999)

    todas_fases_keys = sorted(taxonomia.keys(), key=ordem_fase)
    # Se a taxonomia tem só Pré-obra, usa 1 coluna larga; se tem Durante+Pós, usa 2:1
    n_fases = len(todas_fases_keys)

    colunas = []
    for fase_k in todas_fases_keys:
        fase_meta = taxonomia.get(fase_k) or {"label": fase_k, "cor": "#a89e92"}
        cor_fase = fase_meta.get("cor", "#a89e92")
        label_fase = fase_meta.get("label", fase_k)
        marcos_da_fase = grupos.get(fase_k, {})
        n_fase = sum(len(v) for v in marcos_da_fase.values())
        ativa = n_fase > 0

        # Marcos principais dentro da fase · ordenados pela DATA do 1º submarco (cronológico real)
        marcos_principais_meta = fase_meta.get("marcos_principais") or {}

        def primeira_data_principal(mp_key):
            sub_lista = marcos_da_fase.get(mp_key) or []
            if not sub_lista:
                return ("9999-99-99",)
            datas = sorted(s.get("data") or "9999-99-99" for s in sub_lista)
            return (datas[0],)

        principais_keys = sorted(marcos_da_fase.keys(), key=primeira_data_principal)

        principais_html = []
        for mp_k in principais_keys:
            mp_meta = marcos_principais_meta.get(mp_k) or {}
            mp_label = mp_meta.get("label", mp_k)
            sub_lista = marcos_da_fase[mp_k]

            sub_items = []
            for m in sub_lista:
                cor = COR_MARCO.get(m["tipo"], cor_fase)
                label_sub = LABELS_MARCO.get(m["tipo"], m["tipo"].replace("_", " "))
                autor = html.escape(m.get("autor") or "")
                trecho = html.escape((m.get("trecho") or "").strip())
                # Subtipo (motivo) — aparece como tag colorida ao lado do label
                subtipo_label = m.get("subtipo_label")
                subtipo_html = ""
                if subtipo_label:
                    subtipo_classe = "subtipo-tag-" + (m.get("subtipo") or "")
                    subtipo_html = f'<span class="subtipo-tag {subtipo_classe}">{html.escape(subtipo_label)}</span>'
                sub_items.append(f"""
                <div class="sub-item" title="{trecho}">
                  <span class="sub-bola" style="background:{cor}"></span>
                  <div class="sub-info">
                    <div class="sub-top">
                      <span class="sub-data">{fmt_data(m["data"])}</span>
                      <span class="sub-label">{html.escape(label_sub)}</span>
                      {subtipo_html}
                    </div>
                    <div class="sub-autor">{autor}</div>
                  </div>
                </div>""")

            principais_html.append(f"""
            <div class="principal-bloco">
              <div class="principal-titulo">
                <span class="principal-nome">{html.escape(mp_label)}</span>
                <span class="principal-count">{len(sub_lista)}</span>
              </div>
              <div class="sub-lista">{"".join(sub_items)}</div>
            </div>""")

        if not principais_html:
            principais_html.append('<div class="coluna-vazia">—</div>')

        ordem_num = fase_meta.get("ordem", 0)
        ordem_str = f"{ordem_num}" if ordem_num < 99 else "↺"
        classe_extra = "coluna-ativa" if ativa else "coluna-inativa"
        if fase_k == "x_retrabalho":
            classe_extra += " coluna-retrabalho"

        # Duração da fase · max-min das datas dos marcos
        dt_fase = ""
        if ativa:
            datas_fase = sorted(m.get("data") for sub in marcos_da_fase.values() for m in sub if m.get("data"))
            if len(datas_fase) >= 2:
                try:
                    delta = (datetime.strptime(datas_fase[-1], "%Y-%m-%d") - datetime.strptime(datas_fase[0], "%Y-%m-%d")).days
                    dt_fase = f'<span class="fase-coluna-dt" title="Dias entre o primeiro e o último marco desta fase">{delta}d</span>'
                except Exception:
                    pass

        colunas.append(f"""
        <div class="fase-coluna {classe_extra}" style="--fase-cor: {cor_fase}">
          <header class="fase-coluna-head">
            <span class="fase-coluna-ordem">{ordem_str}</span>
            <span class="fase-coluna-nome">{html.escape(label_fase)}</span>
            {dt_fase}
            <span class="fase-coluna-count">{n_fase}</span>
          </header>
          <div class="fase-coluna-corpo">{"".join(principais_html)}</div>
        </div>""")

    classe_grid = f"fases-kanban kanban-{n_fases}fases"
    return f'<div class="{classe_grid}">{"".join(colunas)}</div>'


def render_insights(obra):
    """Renderiza bloco 'Padrões observados' com insights correlacionais."""
    insights = derivar_insights(obra)
    if not insights:
        return ""
    items = []
    for ins in insights:
        sev = ins.get("severidade", "info")
        items.append(f"""
        <div class="insight-item insight-{sev}">
          <div class="insight-titulo">{html.escape(ins['titulo'])}</div>
          <div class="insight-desc">{html.escape(ins['descricao'])}</div>
        </div>""")
    return f"""
    <div class="insights-wrap">
      <div class="bloco-fase-titulo">Padrões observados · {len(insights)} insight{"s" if len(insights) != 1 else ""}</div>
      <div class="insights-grid">{"".join(items)}</div>
    </div>
    """


def render_heatmap(obra):
    """Heatmap horizontal de msgs/dia · 1 célula por dia entre 1ª msg e última."""
    msgs_por_dia = obra.get("msgs_por_dia") or []
    if not msgs_por_dia:
        return ""
    # Reconstrói série completa preenchendo dias zero entre 1ª e última msg
    try:
        primeiro = datetime.strptime(msgs_por_dia[0]["data"], "%Y-%m-%d")
        ultimo = datetime.strptime(msgs_por_dia[-1]["data"], "%Y-%m-%d")
    except Exception:
        return ""
    span = (ultimo - primeiro).days + 1
    if span > 600:
        return ""  # série muito longa · pula heatmap
    mapa = {m["data"]: m["n"] for m in msgs_por_dia}
    max_n = max((m["n"] for m in msgs_por_dia), default=1)

    cells = []
    for i in range(span):
        d = primeiro + timedelta(days=i)
        d_iso = d.strftime("%Y-%m-%d")
        n = mapa.get(d_iso, 0)
        if n == 0:
            cor = "transparent"
            opacidade = 0.06
        else:
            opacidade = min(1.0, 0.25 + 0.75 * (n / max_n))
            cor = "var(--gold)"
        title = f"{d.strftime('%d/%m/%y')} · {n} msg{'s' if n != 1 else ''}"
        cells.append(f'<span class="heat-cell" style="background:{cor};opacity:{opacidade}" title="{title}"></span>')

    return f"""
    <div class="heatmap-wrap">
      <div class="heatmap-titulo">Atividade no Telegram · {span} dias · pico {max_n} msgs/dia</div>
      <div class="heatmap-grid">{"".join(cells)}</div>
      <div class="heatmap-eixo">
        <span>{primeiro.strftime("%d/%m/%y")}</span>
        <span>{ultimo.strftime("%d/%m/%y")}</span>
      </div>
    </div>
    """


def render_materiais_enviados(obra):
    """Bloco com OS Indústria · materiais enviados (sem anexar PDF, só dados escritos)."""
    envios = obra.get("materiais_enviados") or []
    if not envios:
        return ""
    blocos = []
    for e in envios:
        os_data = fmt_data(e.get("os_data"))
        nome_curto = (e.get("os_nome") or "").replace("field_", "").replace("card_principal_", "")
        nome_curto = nome_curto[:60]
        materiais_rows = []
        for m in e.get("materiais") or []:
            qtd = html.escape(str(m.get("quantidade") or "—"))
            mat = html.escape(str(m.get("material") or "—"))
            cor = html.escape(str(m.get("cor") or "—"))
            materiais_rows.append(f"""
            <tr>
              <td class="num">{qtd}</td>
              <td>{mat}</td>
              <td>{cor}</td>
            </tr>""")
        if not materiais_rows:
            continue
        blocos.append(f"""
        <div class="os-bloco">
          <div class="os-head">
            <span class="os-data">{os_data}</span>
            <span class="os-nome">{html.escape(nome_curto)}</span>
            <span class="os-count">{len(e.get('materiais') or [])} itens</span>
          </div>
          <table class="os-tabela">
            <thead><tr><th>Qtd</th><th>Material</th><th>Cor</th></tr></thead>
            <tbody>{"".join(materiais_rows)}</tbody>
          </table>
        </div>""")
    if not blocos:
        return ""
    return f"""
    <div class="bloco-fase-titulo">Materiais enviados pela Indústria · {len(envios)} OS</div>
    <div class="os-wrap">{"".join(blocos)}</div>
    """


def card_obra(obra, taxonomia):
    cliente = html.escape(obra.get("cliente") or "—")
    status = obra.get("status") or "—"
    fase_painel = html.escape(obra.get("fase_atual_painel") or obra.get("fase_atual") or "—")
    grupo = obra.get("grupo_mix") or "—"
    metragem = obra.get("metragem") or "—"
    n_msgs = obra.get("n_msgs_telegram", 0)
    marcos = obra.get("marcos") or []
    n_marcos = len(marcos)
    dt_total = obra.get("dt_total_marcos_dias")
    dt_painel = obra.get("dt_1a_msg_ate_exec_dias")
    d_exec = fmt_data(obra.get("data_exec_confirmada") or obra.get("data_exec_prevista"))
    obra_id_curto = (obra.get("obra_id") or "")[:8]
    fd = obra.get("fase_derivada") or {}

    grupo_classe = {"finalizadas": "g-fin", "execucao": "g-exec", "reparo": "g-rep"}.get(grupo, "")
    grupo_label = {"finalizadas": "Finalizada", "execucao": "Execução", "reparo": "Reparo"}.get(grupo, grupo)

    # Equipe · 3 categorias
    eq_mf = obra.get("equipe_monofloor") or {}
    aplic_oficiais = obra.get("aplicadores_oficiais") or []
    aplic_obs = obra.get("aplicadores_observados") or []
    presenca_mf = obra.get("presenca_monofloor") or []

    grupos_equipe = []

    # Monofloor (operações + atendimento + consultor)
    chips_mf = []
    if eq_mf.get("operacoes"):
        chips_mf.append(f'<span class="aplic-chip mf-ops" title="Responsável Operações">{html.escape(eq_mf["operacoes"])}</span>')
    if eq_mf.get("atendimento"):
        chips_mf.append(f'<span class="aplic-chip mf-aten" title="Responsável Atendimento">{html.escape(eq_mf["atendimento"])}</span>')
    if eq_mf.get("consultor"):
        chips_mf.append(f'<span class="aplic-chip mf-cons" title="Consultor">{html.escape(eq_mf["consultor"])}</span>')
    if chips_mf:
        grupos_equipe.append(f'<div class="eq-grupo"><span class="eq-grupo-label">Monofloor</span>{"".join(chips_mf)}</div>')

    # Aplicadores (oficiais do /equipe + observados via "estou em obra")
    chips_ap = []
    for a in aplic_oficiais:
        funcao = f' · {a["funcao"]}' if a.get("funcao") else ""
        chips_ap.append(f'<span class="aplic-chip oficial" title="Aplicador oficial{funcao}">⭐ {html.escape(a["nome"])}</span>')
    for a in aplic_obs:
        nome = a["nome"]
        chips_ap.append(f'<span class="aplic-chip observado" title="Disse \'estou em obra\' em {a.get("primeira_chegada","")}">{html.escape(nome)}</span>')
    if chips_ap:
        grupos_equipe.append(f'<div class="eq-grupo"><span class="eq-grupo-label">Aplicadores</span>{"".join(chips_ap)}</div>')

    # Presença Monofloor em obra (Pedro/Wesley/Vanessa que foram visitar)
    if presenca_mf:
        chips_pres = "".join(
            f'<span class="aplic-chip presenca" title="Pessoal Monofloor em obra · {a.get("primeira_chegada","")}">{html.escape(a["nome"])}</span>'
            for a in presenca_mf
        )
        grupos_equipe.append(f'<div class="eq-grupo"><span class="eq-grupo-label">Visitas Monofloor</span>{chips_pres}</div>')

    equipe_html = ""
    if grupos_equipe:
        equipe_html = f'<div class="equipe-blocos">{"".join(grupos_equipe)}</div>'

    # Badge fase derivada
    badge_fd = ""
    if fd:
        cor_fd = (taxonomia.get(fd.get("fase_real")) or {}).get("cor", "#b8884a")
        retr = ' · 🚨 retrabalho ativo' if fd.get("tem_retrabalho") else ""
        gaps = fd.get("gaps_de_fase") or []
        gaps_txt = ""
        if gaps:
            gaps_labels = [(taxonomia.get(g) or {}).get("label", g).split(" ")[0] for g in gaps]
            gaps_txt = f' · sem registro em: {", ".join(gaps_labels)}'
        badge_fd = f"""<span class="fase-derivada-badge" style="background:{cor_fd}">
          Fase atual: {html.escape(fd.get("fase_label", "—"))}{retr}{gaps_txt}
        </span>"""

    # Renderização: cada ciclo vira UMA FAIXA de 3 colunas (Pré · Execução · Pós)
    # Pré-obra só ocupa a coluna 1 do CICLO 1; demais ciclos têm coluna 1 vazia
    ciclos_info = obra.get("ciclos_info") or {}
    pre_obra_marcos = ciclos_info.get("pre_obra_marcos") or []
    ciclos = ciclos_info.get("ciclos") or []
    gaps = ciclos_info.get("gaps_entre") or []

    if not marcos:
        grupos_html = f'<div class="vazio">Sem marcos detectados · {n_msgs} msgs Telegram</div>'
    else:
        tax_pre = {k: v for k, v in taxonomia.items() if k == "1_pre_obra"}
        tax_durante = {k: v for k, v in taxonomia.items() if k == "2_execucao"}
        tax_pos = {k: v for k, v in taxonomia.items() if k == "x_retrabalho"}

        # Se não há ciclos detectados, cria um ciclo "virtual" só pra renderizar pré-obra
        if not ciclos and pre_obra_marcos:
            ciclos = [{"ordem": 1, "nome": "Sem execução detectada", "inicio": None, "fim": None, "duracao_dias": None, "marcos": []}]

        partes = []
        for i, c in enumerate(ciclos):
            # Gap antes deste ciclo (depois do anterior)
            if i > 0 and i - 1 < len(gaps):
                g = gaps[i - 1]
                if g.get("dias") and g["dias"] > 0:
                    gap_marcos = g.get("marcos") or []
                    resumo = g.get("resumo") or []
                    label_gap = "Pausa entre ciclos" if not gap_marcos else "Negociação entre ciclos"
                    # Header com sumário
                    resumo_html = ""
                    if resumo:
                        chips = "".join(f'<span class="gap-chip">{html.escape(r["label"])} · <b>{r["count"]}</b></span>' for r in resumo)
                        resumo_html = f'<div class="gap-resumo">{chips}</div>'
                    # Lista de marcos do gap (compacta · 1 linha cada)
                    marcos_html_gap = ""
                    if gap_marcos:
                        items = []
                        for m in gap_marcos:
                            cor = COR_MARCO.get(m["tipo"], "#a89e92")
                            # No gap, "reprovacao_retorno" não é reprovação · é tratativa pro retorno
                            if m["tipo"] == "reprovacao_retorno":
                                label_m = "Tratativa de retorno"
                            else:
                                label_m = LABELS_MARCO.get(m["tipo"], m["tipo"].replace("_", " "))
                            sub_lbl = m.get("subtipo_label")
                            sub_html = f' <span class="subtipo-tag">{html.escape(sub_lbl)}</span>' if sub_lbl else ""
                            autor = html.escape(m.get("autor") or "")
                            trecho = html.escape((m.get("trecho") or "").strip())
                            items.append(f"""
                            <div class="gap-marco" title="{trecho}">
                              <span class="gap-marco-bola" style="background:{cor}"></span>
                              <span class="gap-marco-data">{fmt_data(m["data"])}</span>
                              <span class="gap-marco-label">{html.escape(label_m)}{sub_html}</span>
                              <span class="gap-marco-autor">{autor}</span>
                            </div>""")
                        marcos_html_gap = f'<div class="gap-marcos-lista">{"".join(items)}</div>'
                    partes.append(f"""
                    <div class="gap-bloco">
                      <div class="gap-divider">↓ {label_gap} · <strong>{g["dias"]} dias</strong> · {len(gap_marcos)} interaç{"ão" if len(gap_marcos)==1 else "ões"} no período</div>
                      {resumo_html}
                      {marcos_html_gap}
                    </div>""")

            duracao_str = f' · {c["duracao_dias"]} dias' if c.get("duracao_dias") is not None else ""
            badge_ciclo = "ciclo-original" if c.get("ordem") == 1 else "ciclo-retorno"
            partes.append(f"""
            <div class="ciclo-header {badge_ciclo}">
              <span class="ciclo-num">Ciclo {c["ordem"]}</span>
              <span class="ciclo-nome">{html.escape(c.get("nome", ""))}</span>
              <span class="ciclo-periodo">{fmt_data(c.get("inicio"))} → {fmt_data(c.get("fim"))}{duracao_str}</span>
              <span class="ciclo-count">{len(c.get("marcos") or [])} marcos</span>
            </div>""")

            # Marcos do ciclo: separa por fase
            marcos_ciclo = c.get("marcos") or []
            durante = [m for m in marcos_ciclo if m.get("fase") == "2_execucao"]
            pos = [m for m in marcos_ciclo if m.get("fase") == "x_retrabalho"]
            pre_neste_ciclo = pre_obra_marcos if i == 0 else []

            partes.append('<div class="ciclo-grid">')

            # Coluna 1 · Pré-obra (apenas no ciclo 1)
            if pre_neste_ciclo:
                partes.append(renderizar_grupos(pre_neste_ciclo, tax_pre))
            else:
                partes.append('<div class="ciclo-col-vazia">—</div>')

            # Coluna 2 · Execução
            if durante:
                partes.append(renderizar_grupos(durante, tax_durante))
            else:
                partes.append('<div class="ciclo-col-vazia">—</div>')

            # Coluna 3 · Pós (retrabalho)
            if pos:
                partes.append(renderizar_grupos(pos, tax_pos))
            else:
                partes.append('<div class="ciclo-col-vazia">—</div>')

            partes.append('</div>')

        grupos_html = "".join(partes)

    pills = ""
    if dt_total is not None:
        pills += f"""
        <div class="tempo-pill principal">
          <div class="tempo-pill-label">Tempo entre marcos</div>
          <div class="tempo-pill-num">{dt_total}<small>dias</small></div>
        </div>"""
    if dt_painel is not None:
        pills += f"""
        <div class="tempo-pill">
          <div class="tempo-pill-label">1ª mensagem → execução</div>
          <div class="tempo-pill-num">{dt_painel}<small>dias</small></div>
        </div>"""
    if n_marcos > 0:
        pills += f"""
        <div class="tempo-pill">
          <div class="tempo-pill-label">Marcos detectados</div>
          <div class="tempo-pill-num">{n_marcos}</div>
        </div>"""

    # Resumo compacto pra summary do acordeão
    n_ciclos = len(ciclos_info.get("ciclos") or [])
    fase_real_label = (fd.get("fase_label") or "—") if fd else "—"
    fase_real_key = fd.get("fase_real") if fd else None
    cor_fr = (taxonomia.get(fase_real_key) or {}).get("cor", "#a89e92")

    # Sinaleira de fase: 3 dots representando Pré · Durante · Pós
    fases_obs = (fd.get("fases_observadas") or []) if fd else []
    tem_pre = "1_pre_obra" in fases_obs
    tem_durante = "2_execucao" in fases_obs
    tem_pos = (fd.get("tem_retrabalho") if fd else False) or "x_retrabalho" in fases_obs
    dots_html = (
        f'<span class="dot {"on" if tem_pre else ""}" title="Pré-obra"></span>'
        f'<span class="dot {"on durante" if tem_durante else ""}" title="Execução"></span>'
        f'<span class="dot {"on pos" if tem_pos else ""}" title="Pós-obra · retrabalho"></span>'
    )

    badge_retr = '<span class="mini-badge retr">🚨</span>' if (fd and fd.get("tem_retrabalho")) else ""
    badge_ciclos = f'<span class="mini-badge ciclos">{n_ciclos} ciclos</span>' if n_ciclos > 1 else ""
    dt_resumo = f'{dt_total}d' if dt_total is not None else (f'{dt_painel}d' if dt_painel else "—")

    # Perfil de fluxo (A-F)
    seq_chave = _seq_chave(marcos)
    perfil = _classificar_perfil(n_marcos, seq_chave)
    perfil_label = PERFIL_LABELS.get(perfil, perfil)
    perfil_cor = PERFIL_CORES.get(perfil, "#999")
    badge_perfil = f'<span class="mini-badge perfil-badge" style="background:{perfil_cor};color:#fff" title="{perfil_label}">{perfil}</span>'

    # Barra de fluxo esperado
    FLUXO_ETAPAS = [
        ("contrato_assinado", "Contrato"),
        ("escopo_em_revisao", "Escopo"),
        ("vt_agendada", "VT"),
        ("material_produzido", "Material"),
        ("equipe_chegou", "Equipe"),
        ("camada_produto", "Camada"),
        ("finalizacao", "Final"),
        ("aprovacao_cliente", "Aprovacao"),
    ]
    fluxo_items = []
    prev_data = None
    for tipo_f, label_f in FLUXO_ETAPAS:
        if tipo_f in seq_chave:
            dt = seq_chave[tipo_f]
            delta = ""
            if prev_data:
                d = _diff_d(prev_data, dt)
                if d is not None and d >= 0:
                    delta = f'<span class="fluxo-delta">{d}d</span>'
            prev_data = dt
            fluxo_items.append(f'<div class="fluxo-step ok" title="{label_f}: {dt}">'
                               f'<div class="fluxo-dot ok"></div>'
                               f'<div class="fluxo-label">{label_f}</div>'
                               f'{delta}</div>')
        else:
            estado = "pulado" if perfil in ("D", "E", "F") or (perfil == "C" and tipo_f in ("contrato_assinado", "escopo_em_revisao", "vt_agendada", "material_produzido")) else "pendente"
            cls = "skip" if estado == "pulado" else "pend"
            fluxo_items.append(f'<div class="fluxo-step {cls}" title="{label_f}: {estado}">'
                               f'<div class="fluxo-dot {cls}"></div>'
                               f'<div class="fluxo-label">{label_f}</div></div>')
    if seq_chave.get("reprovacao_retorno"):
        fluxo_items.append(f'<div class="fluxo-step reprova" title="Reprovacao: {seq_chave["reprovacao_retorno"]}">'
                           f'<div class="fluxo-dot reprova"></div>'
                           f'<div class="fluxo-label">Reprov.</div></div>')
    barra_fluxo = f'<div class="fluxo-barra">{"".join(fluxo_items)}</div>' if fluxo_items else ""

    # Atributos pra filtro client-side (busca por cliente, status, fase)
    data_cliente = html.escape((obra.get("cliente") or "").lower(), quote=True)
    data_status = html.escape((obra.get("status") or "").lower(), quote=True)
    data_fase = html.escape((fase_painel or "").lower(), quote=True)
    data_busca = f"{data_cliente} {data_status} {data_fase}"
    destrinchada_class = " destrinchada" if is_destrinchada(obra.get("cliente")) else ""
    badge_destr = '<span class="mini-badge destrinchada-tag" title="Já destrinchada · usada pra calibrar vocabulário">🔬</span>' if is_destrinchada(obra.get("cliente")) else ""

    # Origem da obra: nova / retorno / pre_contrato (vem do pipeline)
    origem = (obra.get('origem_obra') or {}).get('origem', 'pre_contrato')
    origem_fonte = (obra.get('origem_obra') or {}).get('fonte', '?')
    origem_sinais = (obra.get('origem_obra') or {}).get('sinais', [])
    origem_tip = "; ".join(origem_sinais[:3]) if origem_sinais else "sem sinais detectados"
    if origem == "retorno":
        badge_natureza = f'<span class="mini-badge natureza-retro" title="Retorno — {html.escape(origem_tip)}">RETORNO</span>'
    elif origem == "incerta":
        badge_natureza = f'<span class="mini-badge natureza-incerta" title="Incerta — {html.escape(origem_tip)}">INCERTA</span>'
    elif origem == "pre_contrato":
        badge_natureza = '<span class="mini-badge natureza-precontrato" title="Fase inicial de contratação — sem dados operacionais ainda">PRÉ-CONTRATO</span>'
    else:
        badge_natureza = ""

    # Badge de alerta de obra parada
    alerta = obra.get("alerta_parada")
    badge_alerta = ""
    if alerta:
        dias_a = alerta.get("dias", 0)
        tipo_a = alerta.get("tipo", "")
        label_a = {"contrato_sem_avanço": "PARADA", "obra_dormindo": "DORMINDO", "pos_vt_sem_execucao": "SEM EXEC"}.get(tipo_a, "INATIVA")
        cor_a = "#c45a5a" if dias_a > 60 else "#d4a017"
        badge_alerta = f'<span class="mini-badge alerta-parada" style="background:{cor_a};color:#fff" title="{tipo_a} · {dias_a} dias sem atividade">{label_a} {dias_a}d</span>'

    # Categorias derivadas dos insights pra filtro client-side
    insights_obra = derivar_insights(obra)
    categorias = set()
    for ins in insights_obra:
        categorias.add(ins["tipo"])
    if fd.get("tem_retrabalho"):
        categorias.add("retrabalho_ativo")
    if is_destrinchada(obra.get("cliente")):
        categorias.add("destrinchada")
    categorias.add(f"status_{(obra.get('status') or 'desconhecido').lower()}")
    categorias.add(f"perfil_{perfil}")
    categorias.add(f"origem_{origem}")
    estagio = obra.get("estagio") or "desconhecido"
    categorias.add(f"estagio_{estagio}")
    if alerta:
        categorias.add("alerta_parada")
    data_categorias = " ".join(sorted(categorias))

    return f"""
    <details class="obra-card{destrinchada_class}" data-busca="{data_busca}" data-categorias="{data_categorias}">
      <summary class="obra-summary">
        <span class="sum-grupo grupo-tag {grupo_classe}">{grupo_label}</span>
        <span class="sum-cli">{cliente}</span>
        <span class="sum-dots" title="Fases já registradas: pré-obra · execução · pós-obra">{dots_html}</span>
        <span class="sum-fase" style="--fr-cor: {cor_fr}">{html.escape(fase_real_label)}</span>
        <span class="sum-stats">
          <span class="sum-stat"><b>{n_marcos}</b> marcos</span>
          <span class="sum-stat"><b>{dt_resumo}</b></span>
          <span class="sum-stat"><b>{n_msgs}</b> msgs</span>
        </span>
        <span class="sum-badges">{badge_alerta}{badge_natureza}{badge_perfil}{badge_destr}{badge_ciclos}{badge_retr}</span>
        <span class="sum-toggle">▾</span>
      </summary>
      <div class="obra-detail">
        <header class="obra-card-head">
          <div class="obra-card-id">
            <span class="mono">{obra_id_curto}</span>
            <span class="obra-meta-item"><strong>Status:</strong> {status}</span>
            <span class="obra-meta-item"><strong>Painel:</strong> {fase_painel}</span>
            <span class="obra-meta-item"><strong>{metragem}</strong> m²</span>
            <span class="obra-meta-item"><strong>Exec:</strong> {d_exec}</span>
          </div>
          {equipe_html}
          {badge_fd}
        </header>

        {barra_fluxo}

        <div class="tempo-pills">{pills}</div>

        {render_insights(obra)}

        {render_heatmap(obra)}

        {render_materiais_enviados(obra)}

        <div class="ciclo-marcos-lista">
          {grupos_html}
        </div>
      </div>
    </details>
    """


LABELS_DISCREPANCIA = {
    "finalizado_sem_marcos":   "Finalizado sem registro",
    "retrabalho_oculto":       "Retrabalho não declarado",
    "execucao_com_retrabalho": "Execução com retrabalho",
    "painel_adianta":          "Status à frente",
    "reparo_sem_retrabalho":   "Reparo sem registro",
    "painel_atrasa":           "Status atrás",
}


MARCOS_FLUXO_CHAVE = [
    "contrato_assinado", "escopo_em_revisao", "escopo_aprovado", "cor_aprovada",
    "amostra_solicitada", "vt_agendada", "vt_realizada", "material_produzido",
    "material_entregue", "equipe_chegou", "camada_produto", "ultima_camada",
    "finalizacao", "aprovacao_cliente", "vistoria_cliente", "reprovacao_retorno",
]

PERFIL_LABELS = {
    "A": "Sem marcos",
    "B": "Pré-obra",
    "C": "Em execução",
    "D": "Caminho feliz",
    "E": "Final + reprovação",
    "F": "Reprovação sem final",
}

PERFIL_CORES = {
    "A": "#a89e92",
    "B": "#b89a4a",
    "C": "#4a7ab8",
    "D": "#3d8a5a",
    "E": "#c45a5a",
    "F": "#b83a3a",
}


def _seq_chave(marcos_raw):
    marcos = sorted(marcos_raw, key=lambda m: m.get("data", ""))
    seq = {}
    for m in marcos:
        t = m.get("tipo")
        if t in MARCOS_FLUXO_CHAVE and t not in seq:
            seq[t] = m.get("data", "")[:10]
    return seq


def _classificar_perfil(n_marcos, seq):
    tem = set(seq.keys())
    tem_exec = bool(tem & {"equipe_chegou", "camada_produto"})
    tem_final = "finalizacao" in tem
    tem_repro = "reprovacao_retorno" in tem
    if n_marcos == 0:
        return "A"
    if not tem_exec and not tem_final:
        return "B"
    if tem_exec and not tem_final and not tem_repro:
        return "C"
    if tem_final and not tem_repro:
        return "D"
    if tem_repro and tem_final:
        return "E"
    if tem_repro and not tem_final:
        return "F"
    if tem_exec:
        return "C"
    return "B"


def _is_2026(o):
    dec = o.get("data_exec_confirmada", "")
    dep = o.get("data_exec_prevista", "")
    marcos_raw = o.get("marcos") or []
    primeiro_exec = None
    for m in sorted(marcos_raw, key=lambda x: x.get("data", "")):
        if m.get("fase") == "2_execucao" and m.get("tipo") not in ("ocorrencia_formal",):
            primeiro_exec = m.get("data", "")[:10]
            break
    if dec and dec[:4] == "2026":
        return True
    if primeiro_exec and primeiro_exec[:4] == "2026":
        return True
    if dep and dep[:4] == "2026":
        return True
    return False


def _diff_d(d1, d2):
    try:
        return (datetime.strptime(d2[:10], "%Y-%m-%d") - datetime.strptime(d1[:10], "%Y-%m-%d")).days
    except Exception:
        return None


def calcular_perfis_fluxo(timelines):
    from collections import Counter as _C
    obras_2026 = [o for o in timelines if _is_2026(o)]
    perfis = _C()
    grupos = {}
    for o in obras_2026:
        marcos_raw = o.get("marcos") or []
        seq = _seq_chave(marcos_raw)
        p = _classificar_perfil(len(marcos_raw), seq)
        perfis[p] += 1
        grupos.setdefault(p, []).append({"cliente": o.get("cliente", "?"), "seq": seq, "n": len(marcos_raw), "status": o.get("status", "?")})

    total = len(obras_2026)
    com_exec = sum(perfis.get(p, 0) for p in ("C", "D", "E", "F"))
    com_final = perfis.get("D", 0) + perfis.get("E", 0)
    com_repro = perfis.get("E", 0) + perfis.get("F", 0)
    taxa_repro = round(perfis.get("E", 0) / com_final * 100) if com_final else 0

    transicoes = {}
    pares = [
        ("contrato_assinado", "equipe_chegou", "Contrato a Equipe em obra"),
        ("equipe_chegou", "camada_produto", "Equipe a 1a camada"),
        ("camada_produto", "finalizacao", "1a camada a Finalização"),
        ("contrato_assinado", "finalizacao", "Contrato a Finalização"),
        ("finalizacao", "reprovacao_retorno", "Finalização a Reprovação"),
    ]
    for a, b, label in pares:
        dias = []
        for o in obras_2026:
            seq = _seq_chave(o.get("marcos") or [])
            if a in seq and b in seq:
                d = _diff_d(seq[a], seq[b])
                if d is not None and d >= 0:
                    dias.append(d)
        if dias:
            dias.sort()
            transicoes[label] = {"mediana": dias[len(dias)//2], "min": min(dias), "max": max(dias), "n": len(dias)}

    inversoes = {}
    pares_inv = [
        ("equipe_chegou", "camada_produto", "Equipe chega depois da 1a camada"),
        ("material_produzido", "equipe_chegou", "Material depois da equipe"),
        ("vt_agendada", "equipe_chegou", "VT depois da equipe"),
        ("finalizacao", "reprovacao_retorno", "Finalização depois da reprovação"),
    ]
    for a, b, label in pares_inv:
        n_inv = 0
        n_total_par = 0
        for o in obras_2026:
            seq = _seq_chave(o.get("marcos") or [])
            if a in seq and b in seq:
                n_total_par += 1
                if seq[a] > seq[b]:
                    n_inv += 1
        if n_total_par:
            inversoes[label] = {"invertido": n_inv, "total": n_total_par, "pct": round(n_inv / n_total_par * 100)}

    ausentes_repro = {}
    repro_obras = grupos.get("E", []) + grupos.get("F", [])
    for etapa in ["vt_realizada", "escopo_em_revisao", "vt_agendada", "material_produzido", "aprovacao_cliente"]:
        n_aus = sum(1 for o in repro_obras if etapa not in o["seq"])
        if repro_obras:
            ausentes_repro[etapa] = {"ausente": n_aus, "total": len(repro_obras), "pct": round(n_aus / len(repro_obras) * 100)}

    return {
        "total_2026": total,
        "perfis": dict(perfis),
        "com_exec": com_exec,
        "com_final": com_final,
        "com_repro": com_repro,
        "taxa_repro_final": taxa_repro,
        "transicoes": transicoes,
        "inversoes": inversoes,
        "ausentes_repro": ausentes_repro,
    }


def render_perfis_fluxo(pf):
    total = pf["total_2026"]
    if not total:
        return ""

    perfil_bars = ""
    for p in ("A", "B", "C", "D", "E", "F"):
        n = pf["perfis"].get(p, 0)
        pct = round(n / total * 100)
        w = max(pct, 2)
        cor = PERFIL_CORES.get(p, "#999")
        label = PERFIL_LABELS.get(p, p)
        perfil_bars += f'<div style="flex:{w};background:{cor};border-radius:4px;padding:8px 6px;color:#fff;font-size:10px;text-align:center;min-width:40px" title="{label}: {n} obras ({pct}%)"><b>{n}</b><br>{p}</div>'

    trans_rows = ""
    for label, d in pf["transicoes"].items():
        trans_rows += f'<tr><td>{html.escape(label)}</td><td class="num">{d["mediana"]}d</td><td class="num">{d["min"]}d</td><td class="num">{d["max"]}d</td><td class="num">{d["n"]}</td></tr>'

    inv_rows = ""
    for label, d in pf["inversoes"].items():
        if d["invertido"] > 0:
            inv_rows += f'<tr><td>{html.escape(label)}</td><td class="num">{d["invertido"]}/{d["total"]}</td><td class="num">{d["pct"]}%</td></tr>'

    aus_rows = ""
    for etapa, d in sorted(pf["ausentes_repro"].items(), key=lambda x: -x[1]["pct"]):
        aus_rows += f'<tr><td>{html.escape(etapa)}</td><td class="num">{d["ausente"]}/{d["total"]}</td><td class="num">{d["pct"]}%</td></tr>'

    return f"""
    <div class="analise-bloco" style="grid-column:1/-1">
      <h3 class="analise-titulo">Perfis de comportamento · {total} obras 2026</h3>
      <div class="analise-sub">Cada obra classificada pela sequência de marcos atingidos · caminho feliz = finalizou sem reprovação</div>
      <div style="display:flex;gap:3px;margin-bottom:14px;align-items:stretch;min-height:44px">{perfil_bars}</div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px;font-size:11px">
        <div class="stat" style="padding:10px 12px"><div class="v" style="font-size:18px">{pf["com_exec"]}</div><div class="l">Executaram</div></div>
        <div class="stat" style="padding:10px 12px"><div class="v" style="font-size:18px">{pf["com_final"]}</div><div class="l">Finalizaram</div></div>
        <div class="stat" style="padding:10px 12px"><div class="v" style="font-size:18px">{pf["com_repro"]}</div><div class="l">Com reprovação</div></div>
        <div class="stat" style="padding:10px 12px"><div class="v" style="font-size:18px;color:#c45a5a">{pf["taxa_repro_final"]}%</div><div class="l">Reprovação entre finalizadas</div></div>
      </div>
      <div style="display:flex;gap:8px;font-size:9px;color:var(--ink-faint);margin-bottom:6px">
        {"".join(f'<span style="display:flex;align-items:center;gap:3px"><span style="width:8px;height:8px;border-radius:2px;background:{PERFIL_CORES[p]}"></span>{PERFIL_LABELS[p]}</span>' for p in ("A","B","C","D","E","F"))}
      </div>
    </div>
    <div class="analise-bloco">
      <h3 class="analise-titulo">Tempos entre marcos-chave</h3>
      <div class="analise-sub">Mediana de dias entre transições · todas as obras 2026</div>
      <table class="analise-tabela">
        <thead><tr><th>Transição</th><th>Mediana</th><th>Min</th><th>Max</th><th>N</th></tr></thead>
        <tbody>{trans_rows}</tbody>
      </table>
    </div>
    <div class="analise-bloco{"  grave" if any(d["pct"] > 20 for d in pf["inversoes"].values()) else ""}">
      <h3 class="analise-titulo">Inversões de ordem</h3>
      <div class="analise-sub">Etapas que aconteceram na ordem errada · indica fluxo quebrado ou registro atrasado</div>
      <table class="analise-tabela">
        <thead><tr><th>Inversão</th><th>Obras</th><th>%</th></tr></thead>
        <tbody>{inv_rows}</tbody>
      </table>
    </div>
    <div class="analise-bloco grave">
      <h3 class="analise-titulo">Etapas ausentes em obras com reprovação</h3>
      <div class="analise-sub">Obras que reprovaram e NÃO tinham essas etapas registradas · correlação com qualidade</div>
      <table class="analise-tabela">
        <thead><tr><th>Etapa</th><th>Ausente em</th><th>%</th></tr></thead>
        <tbody>{aus_rows}</tbody>
      </table>
    </div>"""


def render_diagnostico(pf):
    total = pf.get("total_2026", 0)
    if not total:
        return ""
    perfis = pf.get("perfis", {})
    n_a = perfis.get("A", 0)
    n_b = perfis.get("B", 0)
    n_c = perfis.get("C", 0)
    n_d = perfis.get("D", 0)
    n_e = perfis.get("E", 0)
    n_f = perfis.get("F", 0)
    pct_b = round(n_b / total * 100)
    pct_d = round(n_d / total * 100)
    com_exec = pf.get("com_exec", 0)
    com_final = pf.get("com_final", 0)
    com_repro = pf.get("com_repro", 0)
    taxa_repro = pf.get("taxa_repro_final", 0)

    trans = pf.get("transicoes", {})
    med_contrato_equipe = trans.get("Contrato a Equipe em obra", {}).get("mediana", "?")
    med_equipe_camada = trans.get("Equipe a 1a camada", {}).get("mediana", "?")
    med_final_repro = trans.get("Finalização a Reprovação", {}).get("mediana", "?")

    vt_aus = pf.get("ausentes_repro", {}).get("vt_realizada", {})
    pct_vt_aus = vt_aus.get("pct", 0) if vt_aus else 0

    mat_inv = pf.get("inversoes", {}).get("Material depois da equipe", {})
    pct_mat_inv = mat_inv.get("pct", 0) if mat_inv else 0
    n_mat_inv = mat_inv.get("invertido", 0) if mat_inv else 0
    n_mat_total = mat_inv.get("total", 0) if mat_inv else 0

    vt_inv = pf.get("inversoes", {}).get("VT depois da equipe", {})
    pct_vt_inv = vt_inv.get("pct", 0) if vt_inv else 0

    # --- Bloco 1: Panorama ---
    panorama = f"""<div class="narr-bloco">
      <div class="narr-titulo">Panorama do fluxo</div>
      <p>De <strong>{total} obras</strong> iniciadas em 2026, apenas <strong>{n_d} ({pct_d}%)</strong> seguiram
      o caminho ideal: contrato &rarr; escopo &rarr; VT &rarr; material &rarr; equipe &rarr; camada &rarr;
      finalização &rarr; aprovação do cliente.</p>
      <p><strong>{n_b} obras ({pct_b}%)</strong> ainda estão em pré-obra — contrato assinado, escopo em revisão
      ou VT agendada, mas nenhuma execução iniciada. Dessas, {n_a} nem têm registro de marco no Telegram.</p>
      <p>Das que chegaram a executar ({com_exec}), <strong>{com_final}</strong> finalizaram e
      <strong>{com_repro}</strong> tiveram reprovação registrada.</p>
    </div>"""

    # --- Bloco 2: Onde o fluxo quebra ---
    desvios_items = []

    if pct_vt_aus >= 40:
        desvios_items.append(f"""<div class="narr-desvio narr-grave">
          <span class="narr-pct">{pct_vt_aus}%</span>
          <div><strong>das obras reprovadas não tiveram VT registrada.</strong>
          A Visita Técnica é a principal barreira de prevenção antes da execução. Quando é pulada
          para não atrasar o cronograma, os problemas que ela pegaria aparecem como reprovação
          {med_final_repro} dias depois.</div>
        </div>""")

    if pct_mat_inv >= 30:
        desvios_items.append(f"""<div class="narr-desvio narr-alerta">
          <span class="narr-pct">{pct_mat_inv}%</span>
          <div><strong>das obras receberam material depois da equipe chegar.</strong>
          Em {n_mat_inv} de {n_mat_total} casos, a produção (OEI) e o cronograma (OE) correram
          em paralelo sem sincronização. Equipe chega e o material não está lá — ou está errado.</div>
        </div>""")

    if taxa_repro >= 50:
        desvios_items.append(f"""<div class="narr-desvio narr-grave">
          <span class="narr-pct">{taxa_repro}%</span>
          <div><strong>das obras finalizadas tiveram reprovação.</strong>
          De {com_final} finalizadas, {n_e} receberam retorno do cliente. A mediana entre finalização
          e reprovação é de {med_final_repro} dias — a maioria dos problemas não é detectada na hora,
          aparece com o uso.</div>
        </div>""")

    if pct_b >= 30:
        desvios_items.append(f"""<div class="narr-desvio narr-alerta">
          <span class="narr-pct">{pct_b}%</span>
          <div><strong>da carteira parada em pré-obra.</strong>
          {n_b} obras com contrato mas sem execução. Não há gatilho que force a transição
          de uma etapa pra outra — obra com contrato assinado fica dormindo sem cobrança do próximo passo.</div>
        </div>""")

    desvios_html = "".join(desvios_items)

    desvios = f"""<div class="narr-bloco">
      <div class="narr-titulo">Onde o fluxo quebra</div>
      <div class="narr-desvios">{desvios_html}</div>
    </div>""" if desvios_items else ""

    # --- Bloco 3: Velocidade ---
    velocidade = f"""<div class="narr-bloco">
      <div class="narr-titulo">Velocidade entre marcos</div>
      <p>A mediana entre <strong>contrato assinado e equipe em obra</strong> é de
      <strong>{med_contrato_equipe} dias</strong> — o gargalo está no pré-obra, não na execução.</p>
      <p>Uma vez que a equipe chega, a primeira camada acontece em <strong>{med_equipe_camada} dias</strong>.
      A execução em si é rápida. Quando demora mais de 15 dias entre equipe e camada, geralmente
      faltou algo: material, definição de cor, autorização do cliente ou superfície não preparada.</p>
    </div>"""

    # --- Bloco 4: O que os dados sugerem ---
    acoes = f"""<div class="narr-bloco narr-acoes">
      <div class="narr-titulo">O que os dados sugerem</div>
      <div class="narr-acao-grid">
        <div class="narr-acao">
          <div class="narr-acao-tag narr-p0">P0</div>
          <div><strong>Destravar pré-obra.</strong> Alerta para obra com contrato há +30 dias sem próximo marco.
          Reunião semanal de desbloqueio: consultor apresenta as 5 obras mais antigas.</div>
        </div>
        <div class="narr-acao">
          <div class="narr-acao-tag narr-p0">P0</div>
          <div><strong>VT obrigatória antes da execução.</strong> Equipe não agenda sem VT realizada registrada.
          Se dispensada, registrar "VT dispensada" com justificativa.</div>
        </div>
        <div class="narr-acao">
          <div class="narr-acao-tag narr-p1">P1</div>
          <div><strong>Sincronizar material com cronograma.</strong> Material confirmado em obra antes de agendar
          data de execução. OEI com flag "material entregue" que desbloqueia agendamento no OE.</div>
        </div>
        <div class="narr-acao">
          <div class="narr-acao-tag narr-p1">P1</div>
          <div><strong>Monitorar equipe &rarr; camada.</strong> Se passar de 7 dias é alerta amarelo, 15 dias vermelho.
          Indica que faltou algo na preparação.</div>
        </div>
      </div>
    </div>"""

    return f"""
    <div class="diagnostico">
      <div class="section-title">Diagnóstico do fluxo · {total} obras 2026</div>
      {panorama}
      {desvios}
      {velocidade}
      {acoes}
    </div>"""


# ============================================================
# Compilação de problemas · contagem por OBRAS únicas
# ============================================================

CATEGORIAS_OCF = {
    "Desvio de qualidade": ["desvio_qualidade", "qualidade"],
    "Defeito de material": ["defeito_material", "erro_producao"],
    "Problema técnico": ["problema_tecnico"],
    "Reclamação do cliente": ["reclamacao_cliente"],
    "Falha de comunicação": ["falha_comunicacao"],
    "Problema logístico": ["problema_logistico", "atraso_entrega", "atraso"],
    "Incidente de obra": ["incidente_obra"],
}

CATEGORIAS_REPRO = {
    "Defeito relatado": ["defeito_relatado"],
    "Tratativa": ["tratativa"],
    "Escopo/expectativa": ["escopo_definido", "decisao_cliente"],
    "Proposta técnica": ["proposta_tecnica"],
    "Agendamento reparo": ["agendamento_reparo"],
    "Registro de campo": ["registro_campo"],
}


def calcular_compilacao_problemas(timelines):
    total = len(timelines)
    if not total:
        return {}

    ocf = {}
    for cat, subs in CATEGORIAS_OCF.items():
        afetadas = {}
        for o in timelines:
            cli = o.get("cliente", "?")
            n = sum(1 for m in (o.get("marcos") or [])
                    if m.get("tipo") == "ocorrencia_formal" and m.get("subtipo") in subs)
            if n > 0:
                afetadas[cli] = n
        ocf[cat] = {"n_obras": len(afetadas),
                     "top5": sorted(afetadas.items(), key=lambda x: -x[1])[:5]}

    repro = {}
    for cat, subs in CATEGORIAS_REPRO.items():
        afetadas = {}
        for o in timelines:
            cli = o.get("cliente", "?")
            n = sum(1 for m in (o.get("marcos") or [])
                    if m.get("tipo") == "reprovacao_retorno" and m.get("subtipo") in subs)
            if n > 0:
                afetadas[cli] = n
        repro[cat] = {"n_obras": len(afetadas),
                       "top5": sorted(afetadas.items(), key=lambda x: -x[1])[:5]}

    criticas = [o for o in timelines if o.get("status") in ("reparo", "marcas_rolo_cera")]
    criticas_sem_registro = []
    for o in criticas:
        marcos = o.get("marcos") or []
        tem = any(m.get("tipo") in ("ocorrencia_formal", "reprovacao_retorno") for m in marcos)
        if not tem:
            criticas_sem_registro.append(o.get("cliente", "?"))

    obras_com_qualquer = set()
    for o in timelines:
        for m in (o.get("marcos") or []):
            if m.get("tipo") in ("ocorrencia_formal", "reprovacao_retorno"):
                obras_com_qualquer.add(o.get("cliente", "?"))

    retrabalho_n = sum(1 for o in timelines if (o.get("fase_derivada") or {}).get("tem_retrabalho"))

    ranking = []
    for cat, v in ocf.items():
        ranking.append((cat, v["n_obras"], "ocorrencia"))
    for cat, v in repro.items():
        ranking.append((cat, v["n_obras"], "reprovacao"))
    ranking.append(("Retrabalho ativo", retrabalho_n, "status"))
    ranking.append(("Status reparo/marcas", len(criticas), "status"))
    ranking.sort(key=lambda x: -x[1])

    return {
        "total": total,
        "com_problema": len(obras_com_qualquer),
        "sem_problema": total - len(obras_com_qualquer),
        "pct_com": round(len(obras_com_qualquer) / total * 100),
        "ocf": ocf,
        "repro": repro,
        "ranking": ranking,
        "criticas_total": len(criticas),
        "criticas_sem_registro": criticas_sem_registro,
        "retrabalho_n": retrabalho_n,
    }


def render_compilacao_problemas(comp):
    if not comp or not comp.get("total"):
        return ""
    total = comp["total"]
    com = comp["com_problema"]
    sem = comp["sem_problema"]
    pct = comp["pct_com"]

    panorama = f"""<div class="narr-bloco">
      <div class="narr-titulo">Raio-x dos problemas</div>
      <p>De <strong>{total} obras vivas</strong>, <strong>{com} ({pct}%)</strong> têm pelo menos
      um problema registrado (ocorrência formal ou reprovação). As outras <strong>{sem}</strong>
      estão limpas nos dados — não necessariamente sem problema, mas sem registro capturado.</p>
    </div>"""

    # Ranking
    rows = ""
    for cat, n, tipo in comp["ranking"]:
        pct_r = round(n / total * 100)
        tipo_class = "prob-ocf" if tipo == "ocorrencia" else ("prob-repro" if tipo == "reprovacao" else "prob-status")
        bar_w = max(2, round(n / total * 100))
        rows += f"""<tr class="{tipo_class}">
          <td class="prob-nome">{html.escape(cat)}</td>
          <td class="prob-n mono">{n}</td>
          <td class="prob-pct mono">{pct_r}%</td>
          <td class="prob-bar-cell"><div class="prob-bar" style="width:{bar_w}%"></div></td>
        </tr>"""

    ranking_html = f"""<div class="narr-bloco">
      <div class="narr-titulo">Quantas obras têm cada tipo de problema</div>
      <table class="prob-ranking">
        <thead><tr><th>Indicador</th><th>Obras</th><th>%</th><th></th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <div class="prob-legenda">
        <span class="prob-leg-item"><span class="prob-leg-dot prob-ocf"></span>Ocorrência formal</span>
        <span class="prob-leg-item"><span class="prob-leg-dot prob-repro"></span>Reprovação</span>
        <span class="prob-leg-item"><span class="prob-leg-dot prob-status"></span>Status/retrabalho</span>
      </div>
    </div>"""

    # Destaques narrativos
    destaques = []

    # Destaque 1: desvio de qualidade
    dq = comp["ocf"].get("Desvio de qualidade", {})
    if dq.get("n_obras", 0) >= 10:
        n_dq = dq["n_obras"]
        pct_dq = round(n_dq / total * 100)
        top3 = ", ".join(f"{c[:25]} ({n}x)" for c, n in dq["top5"][:3])
        destaques.append(f"""<div class="narr-desvio narr-grave">
          <span class="narr-pct">{pct_dq}%</span>
          <div><strong>das obras tiveram desvio de qualidade.</strong>
          {n_dq} obras com pelo menos um registro de desvio. Concentração maior em: {top3}.
          É o problema real mais prevalente — diferente de tratativas, aqui o produto ou processo falhou.</div>
        </div>""")

    # Destaque 2: obras em reparo SEM registro
    csr = comp["criticas_sem_registro"]
    if csr:
        pct_csr = round(len(csr) / comp["criticas_total"] * 100) if comp["criticas_total"] else 0
        destaques.append(f"""<div class="narr-desvio narr-grave">
          <span class="narr-pct">{pct_csr}%</span>
          <div><strong>das obras em reparo não têm registro de problema.</strong>
          {len(csr)} de {comp["criticas_total"]} obras em status crítico (reparo/marcas_rolo_cera) não possuem
          nenhuma ocorrência formal nem reprovação nos dados. O problema existe na realidade mas é invisível
          para o pipeline — gap de visibilidade que precisa de investigação.</div>
        </div>""")

    # Destaque 3: tratativa vs defeito real
    trat = comp["repro"].get("Tratativa", {})
    defeito = comp["repro"].get("Defeito relatado", {})
    if trat.get("n_obras", 0) > 0 and defeito.get("n_obras", 0) > 0:
        n_t = trat["n_obras"]
        n_d = defeito["n_obras"]
        destaques.append(f"""<div class="narr-desvio narr-alerta">
          <span class="narr-pct">{n_t}<small style="font-size:11px">/{n_d}</small></span>
          <div><strong>Tratativa vs. defeito confirmado.</strong>
          {n_t} obras tiveram tratativa (negociação, acompanhamento) contra apenas {n_d} com defeito
          relatado confirmado. Tratativa não é necessariamente problema técnico — é discussão comercial
          ou alinhamento de expectativa. O índice real de defeito é menor do que o volume bruto sugere.</div>
        </div>""")

    destaques_html = "".join(destaques)
    destaques_bloco = f"""<div class="narr-bloco">
      <div class="narr-titulo">Destaques</div>
      <div class="narr-desvios">{destaques_html}</div>
    </div>""" if destaques else ""

    # Top concentradores (top 3 por categoria principal)
    concentradores = []
    for cat in ("Desvio de qualidade", "Falha de comunicação", "Problema logístico", "Reclamação do cliente"):
        info = comp["ocf"].get(cat, {})
        if info.get("top5"):
            items = " · ".join(f"{c[:20]} ({n}x)" for c, n in info["top5"][:3])
            concentradores.append(f"<div class='prob-conc-item'><strong>{cat}:</strong> {items}</div>")

    conc_html = ""
    if concentradores:
        conc_html = f"""<div class="narr-bloco">
          <div class="narr-titulo">Onde se concentra</div>
          <div class="prob-concentradores">{"".join(concentradores)}</div>
        </div>"""

    return f"""
    <div class="compilacao-problemas">
      <div class="section-title">Compilação de problemas · {total} obras</div>
      {panorama}
      {ranking_html}
      {destaques_bloco}
      {conc_html}
    </div>"""


def render_narrativa_unificada(pf, comp, n_total, n_marcos, n_com, n_sem, cobertura, n_novas=0, n_retorno=0, n_pre_contrato=0, n_incerta=0):
    """Narrativa unificada da Tela 1: historia completa de cima a baixo."""
    total_2026 = pf.get("total_2026", 0) or 1
    perfis = pf.get("perfis", {})
    n_d = perfis.get("D", 0)
    n_b = perfis.get("B", 0)
    n_e = perfis.get("E", 0)
    n_f = perfis.get("F", 0)
    pct_d = round(n_d / total_2026 * 100)
    pct_b = round(n_b / total_2026 * 100)
    com_exec = pf.get("com_exec", 0)
    com_final = pf.get("com_final", 0)
    com_repro = pf.get("com_repro", 0)
    taxa_repro = pf.get("taxa_repro_final", 0)

    trans = pf.get("transicoes", {})
    med_contrato_equipe = trans.get("Contrato a Equipe em obra", {}).get("mediana", "?")
    med_equipe_camada = trans.get("Equipe a 1a camada", {}).get("mediana", "?")
    med_final_repro = trans.get("Finalização a Reprovação", {}).get("mediana", "?")

    vt_aus = pf.get("ausentes_repro", {}).get("vt_realizada", {})
    pct_vt_aus = vt_aus.get("pct", 0) if vt_aus else 0

    mat_inv = pf.get("inversoes", {}).get("Material depois da equipe", {})
    pct_mat_inv = mat_inv.get("pct", 0) if mat_inv else 0
    n_mat_inv = mat_inv.get("invertido", 0) if mat_inv else 0
    n_mat_total = mat_inv.get("total", 0) if mat_inv else 0

    com_prob = comp.get("com_problema", 0) if comp else 0
    pct_prob = comp.get("pct_com", 0) if comp else 0
    criticas_total = comp.get("criticas_total", 0) if comp else 0
    criticas_sem = comp.get("criticas_sem_registro", []) if comp else []
    ranking = comp.get("ranking", []) if comp else []
    ocf = comp.get("ocf", {}) if comp else {}
    repro = comp.get("repro", {}) if comp else {}
    retrabalho_n = comp.get("retrabalho_n", 0) if comp else 0

    pct_cobertura = round(n_com / n_total * 100) if n_total else 0
    taxa_regex = cobertura.get("taxa_aproveitamento_pct", 0) if cobertura else 0

    # === CAPITULO 1 · ABERTURA ===
    pct_novas = round(n_novas / n_total * 100) if n_total else 0
    pct_retro = round(n_retorno / n_total * 100) if n_total else 0
    cap1 = f"""<div class="narr-capitulo">
      <div class="narr-cap-num">01</div>
      <div class="narr-cap-corpo">
        <div class="narr-titulo">O que sabemos hoje</div>
        <p>Existem <strong>{n_total} obras vivas</strong> no Painel de Obras. Cruzando status, nome do card,
        data da primeira mensagem do Telegram, marcos de execução e visão do Kira, classificamos cada obra
        por origem — se é a primeira aplicação Monofloor no local ou se já houve trabalho anterior.</p>
        <div class="narr-indicadores narr-ind-5">
          <div class="narr-ind narr-ind-nova">
            <div class="narr-ind-valor">{n_novas}</div>
            <div class="narr-ind-label">novas — do zero ({pct_novas}%)</div>
          </div>
          <div class="narr-ind narr-ind-retro">
            <div class="narr-ind-valor">{n_retorno}</div>
            <div class="narr-ind-label">retornos ({pct_retro}%)</div>
          </div>
          <div class="narr-ind narr-ind-incerta">
            <div class="narr-ind-valor">{n_incerta}</div>
            <div class="narr-ind-label">incertas</div>
          </div>
          <div class="narr-ind narr-ind-precontrato">
            <div class="narr-ind-valor">{n_pre_contrato}</div>
            <div class="narr-ind-label">pré-contrato</div>
          </div>
          <div class="narr-ind">
            <div class="narr-ind-valor">{n_marcos}</div>
            <div class="narr-ind-label">marcos detectados</div>
          </div>
        </div>
        <p style="font-size:12px;color:var(--ink-soft);margin-top:8px"><strong>Novas</strong> = primeira
        aplicação Monofloor no local (confirmado via Telegram ou Kira).
        <strong>Retornos</strong> = local que já teve aplicação anterior (status, nome, ciclo completo
        ou Kira indica retrabalho).
        <strong>Incertas</strong> = grupo antigo com execução mas sem finalização clara.
        <strong>Pré-contrato</strong> = obras em fase inicial de contratação, ainda sem dados operacionais.</p>
      </div>
    </div>"""

    # === CAPITULO 2 · SAUDE ===
    saude_itens = []
    if pct_b >= 25:
        saude_itens.append(f"""<div class="narr-stat narr-stat-alerta">
          <div class="narr-stat-num">{n_b}</div>
          <div class="narr-stat-desc"><strong>{pct_b}% paradas em pré-obra.</strong> Contrato assinado
          mas sem execução iniciada. Não há gatilho que force a transição — obra dorme sem cobrança.</div>
        </div>""")
    if com_exec:
        saude_itens.append(f"""<div class="narr-stat">
          <div class="narr-stat-num">{com_exec}</div>
          <div class="narr-stat-desc"><strong>Executaram.</strong> Dessas, {com_final} finalizaram e
          {com_repro} tiveram reprovação. A mediana entre contrato e equipe em obra é de
          <strong>{med_contrato_equipe} dias</strong> — o gargalo está no pré-obra.</div>
        </div>""")
    if taxa_repro >= 40:
        saude_itens.append(f"""<div class="narr-stat narr-stat-grave">
          <div class="narr-stat-num" style="color:#c45a5a">{taxa_repro}%</div>
          <div class="narr-stat-desc"><strong>Taxa de reprovação entre finalizadas.</strong> De {com_final}
          finalizadas, {n_e} receberam retorno do cliente. A mediana entre finalização e reprovação é de
          {med_final_repro} dias — o problema não aparece na hora, aparece com o uso.</div>
        </div>""")

    cap2 = f"""<div class="narr-capitulo">
      <div class="narr-cap-num">02</div>
      <div class="narr-cap-corpo">
        <div class="narr-titulo">Saúde da carteira</div>
        <p>Das <strong>{total_2026} obras 2026</strong>, apenas <strong>{n_d} ({pct_d}%)</strong> seguiram
        o caminho ideal completo. A grande maioria desvia em algum ponto — e isso não é exceção, é o padrão.</p>
        <div class="narr-stats-lista">{"".join(saude_itens)}</div>
      </div>
    </div>"""

    # === CAPITULO 3 · PROBLEMAS REAIS ===
    prob_rows = ""
    for cat, n, tipo in ranking[:8]:
        pct_r = round(n / n_total * 100)
        tipo_class = "prob-ocf" if tipo == "ocorrencia" else ("prob-repro" if tipo == "reprovacao" else "prob-status")
        bar_w = max(2, round(n / n_total * 100))
        prob_rows += f"""<tr class="{tipo_class}">
          <td class="prob-nome">{html.escape(cat)}</td>
          <td class="prob-n mono">{n}</td>
          <td class="prob-pct mono">{pct_r}%</td>
          <td class="prob-bar-cell"><div class="prob-bar" style="width:{bar_w}%"></div></td>
        </tr>"""

    desvios_narrativos = []

    dq = ocf.get("Desvio de qualidade", {})
    if dq.get("n_obras", 0) >= 5:
        n_dq = dq["n_obras"]
        pct_dq = round(n_dq / n_total * 100)
        top3 = ", ".join(f"{c[:22]} ({n}x)" for c, n in dq["top5"][:3])
        desvios_narrativos.append(f"""<div class="narr-desvio narr-grave">
          <span class="narr-pct">{pct_dq}%</span>
          <div><strong>das obras tiveram desvio de qualidade</strong> — {n_dq} obras. O problema real
          mais prevalente. Concentração: {top3}.</div>
        </div>""")

    if pct_vt_aus >= 40:
        desvios_narrativos.append(f"""<div class="narr-desvio narr-grave">
          <span class="narr-pct">{pct_vt_aus}%</span>
          <div><strong>das obras reprovadas não tiveram VT registrada.</strong> A visita técnica é a
          barreira de prevenção. Quando é pulada, os problemas aparecem como reprovação
          {med_final_repro} dias depois.</div>
        </div>""")

    if pct_mat_inv >= 25:
        desvios_narrativos.append(f"""<div class="narr-desvio narr-alerta">
          <span class="narr-pct">{pct_mat_inv}%</span>
          <div><strong>das obras receberam material depois da equipe chegar.</strong>
          Em {n_mat_inv} de {n_mat_total} casos, equipe chegou e o material não estava lá.</div>
        </div>""")

    trat = repro.get("Tratativa", {})
    defeito = repro.get("Defeito relatado", {})
    if trat.get("n_obras", 0) > 0 and defeito.get("n_obras", 0) > 0:
        n_t = trat["n_obras"]
        n_def = defeito["n_obras"]
        desvios_narrativos.append(f"""<div class="narr-desvio narr-alerta">
          <span class="narr-pct">{n_t}<small>/{n_def}</small></span>
          <div><strong>Tratativa vs. defeito confirmado.</strong> {n_t} obras tiveram tratativa
          (negociação) contra {n_def} com defeito real. O índice de defeito é menor do que o
          volume bruto sugere.</div>
        </div>""")

    concentradores = []
    for cat in ("Desvio de qualidade", "Falha de comunicação", "Reclamação do cliente"):
        info = ocf.get(cat, {})
        if info.get("top5"):
            items = " · ".join(f"{c[:20]} ({n}x)" for c, n in info["top5"][:3])
            concentradores.append(f"<div class='prob-conc-item'><strong>{cat}:</strong> {items}</div>")

    conc_html = f"""<div class="narr-concentradores">{"".join(concentradores)}</div>""" if concentradores else ""

    cap3 = f"""<div class="narr-capitulo">
      <div class="narr-cap-num">03</div>
      <div class="narr-cap-corpo">
        <div class="narr-titulo">Os problemas reais</div>
        <p><strong>{com_prob} de {n_total} obras ({pct_prob}%)</strong> têm pelo menos um problema registrado.
        Contagem por obras únicas afetadas — não por volume de ocorrências dentro de uma mesma obra.</p>
        <table class="prob-ranking">
          <thead><tr><th>Indicador</th><th>Obras</th><th>%</th><th></th></tr></thead>
          <tbody>{prob_rows}</tbody>
        </table>
        <div class="prob-legenda">
          <span class="prob-leg-item"><span class="prob-leg-dot prob-ocf"></span>Ocorrência formal</span>
          <span class="prob-leg-item"><span class="prob-leg-dot prob-repro"></span>Reprovação</span>
          <span class="prob-leg-item"><span class="prob-leg-dot prob-status"></span>Status/retrabalho</span>
        </div>
        <div class="narr-desvios" style="margin-top:16px">{"".join(desvios_narrativos)}</div>
        {conc_html}
      </div>
    </div>"""

    # === CAPITULO 4 · O QUE ESCAPA ===
    gaps = []
    if n_sem > 0:
        gaps.append(f"""<div class="narr-gap">
          <span class="narr-gap-num">{n_sem}</span>
          <div><strong>obras sem grupo Telegram</strong> — invisíveis para o pipeline.
          Nenhum marco, nenhum desvio, nenhum sinal. Se um problema acontece nessas obras,
          não aparece aqui.</div>
        </div>""")

    if criticas_sem:
        pct_csr = round(len(criticas_sem) / criticas_total * 100) if criticas_total else 0
        gaps.append(f"""<div class="narr-gap">
          <span class="narr-gap-num">{len(criticas_sem)}/{criticas_total}</span>
          <div><strong>obras em reparo sem registro de problema.</strong> {pct_csr}% das obras em
          status crítico não têm nenhuma ocorrência nos dados. O problema existe mas não foi
          capturado.</div>
        </div>""")

    if taxa_regex and taxa_regex < 5:
        gaps.append(f"""<div class="narr-gap">
          <span class="narr-gap-num">{taxa_regex}%</span>
          <div><strong>das mensagens Telegram viram marco.</strong> O restante são conversas, fotos,
          áudios e mensagens operacionais que o pipeline não classifica. Pode haver sinais
          relevantes que escapam da detecção.</div>
        </div>""")

    cap4 = ""
    if gaps:
        cap4 = f"""<div class="narr-capitulo">
          <div class="narr-cap-num">04</div>
          <div class="narr-cap-corpo">
            <div class="narr-titulo">O que o dado não mostra</div>
            <p>Esses são os limites conhecidos do pipeline. Cada um representa informação que existe na
            realidade mas que não chega até aqui.</p>
            <div class="narr-gaps">{"".join(gaps)}</div>
          </div>
        </div>"""

    # === CAPITULO 5 · ACOES ===
    cap5 = f"""<div class="narr-capitulo">
      <div class="narr-cap-num">05</div>
      <div class="narr-cap-corpo">
        <div class="narr-titulo">O que os dados sugerem</div>
        <div class="narr-acao-grid">
          <div class="narr-acao">
            <div class="narr-acao-tag narr-p0">P0</div>
            <div><strong>Destravar pré-obra.</strong> {n_b} obras com contrato e sem execução.
            Alerta para obra com contrato há +30 dias sem próximo marco.</div>
          </div>
          <div class="narr-acao">
            <div class="narr-acao-tag narr-p0">P0</div>
            <div><strong>VT obrigatória antes da execução.</strong> Equipe não agenda sem VT
            realizada. Se dispensada, registrar com justificativa.</div>
          </div>
          <div class="narr-acao">
            <div class="narr-acao-tag narr-p1">P1</div>
            <div><strong>Sincronizar material × cronograma.</strong> Material confirmado em obra
            antes de agendar execução.</div>
          </div>
          <div class="narr-acao">
            <div class="narr-acao-tag narr-p1">P1</div>
            <div><strong>Investigar obras em reparo sem registro.</strong> {len(criticas_sem)} obras
            em status crítico sem nenhuma ocorrência nos dados.</div>
          </div>
        </div>
      </div>
    </div>"""

    return f"""<div class="narrativa-unificada">{cap1}{cap2}{cap3}{cap4}{cap5}</div>"""


def calcular_analise_cross_obras(timelines, taxonomia):
    """Agrega métricas cross-obras: mentiras do Painel, medianas populacionais, sinais graves."""
    from collections import Counter as _C
    from statistics import median as _median

    # 1. Discrepâncias no Painel · status declarado vs fase derivada
    discrepancias = []
    for t in timelines:
        fd = t.get("fase_derivada") or {}
        if not fd or not fd.get("fase_real"):
            continue
        status_painel = (t.get("status") or "").lower()
        fase_real = fd.get("fase_real")
        fase_real_label = fd.get("fase_label")
        fases_obs = fd.get("fases_observadas") or []
        tem_retrabalho = fd.get("tem_retrabalho") or False
        marcos = t.get("marcos") or []
        tipos = {m.get("tipo") for m in marcos}
        tem_aprovacao = "aprovacao_cliente" in tipos
        tem_finalizacao = "finalizacao" in tipos

        # H1 · status="finalizado" mas obra não tem aprovacao_cliente NEM finalizacao registrada no Telegram
        if status_painel in ("finalizado", "concluido") and not tem_aprovacao and not tem_finalizacao:
            discrepancias.append({
                "cliente": t.get("cliente"),
                "tipo": "finalizado_sem_marcos",
                "status_painel": status_painel,
                "fase_real": fase_real_label,
                "razao": "Painel registra finalizado · Telegram sem aprovação cliente nem finalização",
            })
            continue

        # H2 · status="finalizado" + tem retrabalho ativo
        if status_painel in ("finalizado", "concluido") and tem_retrabalho:
            discrepancias.append({
                "cliente": t.get("cliente"),
                "tipo": "retrabalho_oculto",
                "status_painel": status_painel,
                "fase_real": fase_real_label,
                "razao": "Painel registra finalizado · marcos indicam retrabalho ativo",
            })
            continue

        # H3 · status="em_execucao" + tem retrabalho ativo (deveria ser reparo)
        if status_painel == "em_execucao" and tem_retrabalho:
            discrepancias.append({
                "cliente": t.get("cliente"),
                "tipo": "execucao_com_retrabalho",
                "status_painel": status_painel,
                "fase_real": fase_real_label,
                "razao": "Painel registra em_execucao · marcos indicam retrabalho ativo",
            })
            continue

        # H4 · status="em_execucao" mas só tem marcos de pré-obra (camadas não chegaram)
        if status_painel == "em_execucao" and "2_execucao" not in fases_obs:
            discrepancias.append({
                "cliente": t.get("cliente"),
                "tipo": "painel_adianta",
                "status_painel": status_painel,
                "fase_real": fase_real_label,
                "razao": "Painel registra em_execucao · Telegram só registrou pré-obra",
            })
            continue

        # H5 · status=reparo/marcas_rolo_cera mas SEM retrabalho detectado
        if status_painel in ("reparo", "marcas_rolo_cera") and not tem_retrabalho:
            discrepancias.append({
                "cliente": t.get("cliente"),
                "tipo": "reparo_sem_retrabalho",
                "status_painel": status_painel,
                "fase_real": fase_real_label,
                "razao": "Painel registra reparo/pós-venda · Telegram sem retrabalho ativo",
            })
            continue

        # H6 · status indica fase inicial mas Telegram já está em execução
        if status_painel in ("contrato", "planejamento", "aguardando_execucao", "aguardando_clima") and "2_execucao" in fases_obs:
            discrepancias.append({
                "cliente": t.get("cliente"),
                "tipo": "painel_atrasa",
                "status_painel": status_painel,
                "fase_real": fase_real_label,
                "razao": "Painel ainda em fase inicial · Telegram já registrou execução",
            })
            continue

    # 2. Painel adianta exec confirmada (1ª msg DEPOIS da exec) · sinal grave
    painel_adianta_exec = []
    for t in timelines:
        dt = t.get("dt_1a_msg_ate_exec_dias")
        if dt is not None and dt < 0:
            painel_adianta_exec.append({
                "cliente": t.get("cliente"),
                "dias_diferenca": dt,
                "data_exec": t.get("data_exec_confirmada"),
                "data_1a_msg": t.get("data_1a_msg"),
            })

    # 3. Δt mediana por fase populacional (todas obras)
    dts_por_fase = defaultdict(list)
    for t in timelines:
        marcos = t.get("marcos") or []
        if not marcos:
            continue
        marcos_por_fase = defaultdict(list)
        for m in marcos:
            f = m.get("fase")
            if f:
                marcos_por_fase[f].append(m)
        for fase_k, ms in marcos_por_fase.items():
            datas = sorted(m["data"] for m in ms if m.get("data"))
            if len(datas) >= 2:
                try:
                    delta = (datetime.strptime(datas[-1], "%Y-%m-%d") - datetime.strptime(datas[0], "%Y-%m-%d")).days
                    dts_por_fase[fase_k].append(delta)
                except Exception:
                    pass
    medianas_fase = {}
    for fase_k, dts in dts_por_fase.items():
        if dts:
            label_f = (taxonomia.get(fase_k) or {}).get("label", fase_k)
            medianas_fase[fase_k] = {
                "label": label_f,
                "n": len(dts),
                "mediana": int(_median(dts)),
                "min": min(dts),
                "max": max(dts),
            }

    # 4. Distribuição de subtipos · postergações + reprovações + ocorrências
    subtipo_dist = {"postergacao": _C(), "reprovacao": _C(), "ocorrencia": _C()}
    for t in timelines:
        for m in t.get("marcos") or []:
            sl = m.get("subtipo_label")
            if not sl:
                continue
            if m["tipo"] in ("obra_postergada", "postergacao_explicita"):
                subtipo_dist["postergacao"][sl] += 1
            elif m["tipo"] == "reprovacao_retorno":
                subtipo_dist["reprovacao"][sl] += 1
            elif m["tipo"] == "ocorrencia_formal":
                subtipo_dist["ocorrencia"][sl] += 1

    # 5. Obras com gaps grandes entre ciclos (potencial pós-venda travado)
    gaps_grandes = []
    for t in timelines:
        ci = t.get("ciclos_info") or {}
        for g in ci.get("gaps_entre") or []:
            if g.get("dias") and g["dias"] > 30:
                gaps_grandes.append({
                    "cliente": t.get("cliente"),
                    "dias": g["dias"],
                    "n_interacoes": len(g.get("marcos") or []),
                })
    gaps_grandes.sort(key=lambda x: -x["dias"])

    return {
        "discrepancias_painel": discrepancias,
        "painel_adianta_exec": painel_adianta_exec,
        "medianas_por_fase": medianas_fase,
        "subtipo_distribuicao": {k: dict(v) for k, v in subtipo_dist.items()},
        "gaps_grandes": gaps_grandes,
    }


def render_analise_cross(an, taxonomia):
    """Renderiza painel de análise cross-obras no topo do HTML."""
    blocos = []

    # Discrepâncias no Painel
    discrepancias = an.get("discrepancias_painel") or []
    if discrepancias:
        rows = "".join(
            f"""<tr>
              <td>{html.escape(m["cliente"] or "—")}</td>
              <td><span class="mentira-tag tipo-{m["tipo"]}">{html.escape(LABELS_DISCREPANCIA.get(m["tipo"], m["tipo"]))}</span></td>
              <td class="mono">{html.escape(m["status_painel"])}</td>
              <td>{html.escape(m["fase_real"] or "—")}</td>
              <td class="razao">{html.escape(m["razao"])}</td>
            </tr>"""
            for m in discrepancias
        )
        blocos.append(f"""
        <div class="analise-bloco">
          <h3 class="analise-titulo">⚠ Discrepâncias no Painel · {len(discrepancias)} obra{"s" if len(discrepancias) != 1 else ""}</h3>
          <div class="analise-sub">Status declarado pelo Painel diverge da fase derivada das mensagens</div>
          <table class="analise-tabela">
            <thead><tr><th>Cliente</th><th>Tipo</th><th>Status Painel</th><th>Fase real</th><th>Razão</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>""")

    # Status registrado antes da 1ª msg
    pa = an.get("painel_adianta_exec") or []
    if pa:
        rows = "".join(
            f"""<tr>
              <td>{html.escape(p["cliente"] or "—")}</td>
              <td class="num">{p["dias_diferenca"]}d</td>
              <td class="mono">{p.get("data_exec", "—")}</td>
              <td class="mono">{p.get("data_1a_msg", "—")}</td>
            </tr>"""
            for p in pa
        )
        blocos.append(f"""
        <div class="analise-bloco grave">
          <h3 class="analise-titulo">🚨 Status registrado antes da 1ª msg · {len(pa)} obra{"s" if len(pa) != 1 else ""}</h3>
          <div class="analise-sub">Data de execução confirmada está no Painel antes do Telegram registrar a 1ª mensagem</div>
          <table class="analise-tabela">
            <thead><tr><th>Cliente</th><th>Diferença</th><th>Execução confirmada</th><th>1ª mensagem</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>""")

    # Tempo médio por fase
    medianas = an.get("medianas_por_fase") or {}
    if medianas:
        ord_fase = lambda k: (taxonomia.get(k) or {}).get("ordem", 999)
        items = []
        for fase_k in sorted(medianas.keys(), key=ord_fase):
            m = medianas[fase_k]
            cor = (taxonomia.get(fase_k) or {}).get("cor", "#a89e92")
            items.append(f"""
            <div class="med-card" style="--med-cor: {cor}">
              <div class="med-fase">{html.escape(m["label"])}</div>
              <div class="med-num"><b>{m["mediana"]}</b><small>d</small> <span class="med-range">(de {m["min"]} a {m["max"]} dias)</span></div>
              <div class="med-n">{m["n"]} obra{"s" if m["n"] != 1 else ""}</div>
            </div>""")
        blocos.append(f"""
        <div class="analise-bloco">
          <h3 class="analise-titulo">📊 Tempo médio por fase · todas as obras</h3>
          <div class="analise-sub">Dias entre o primeiro e o último marco de cada fase · valor mediano · faixa observada · número de obras</div>
          <div class="med-grid">{"".join(items)}</div>
        </div>""")

    # Distribuição de subtipos
    sd = an.get("subtipo_distribuicao") or {}
    chips_html = []
    for grupo, dist in [("Postergações", sd.get("postergacao", {})), ("Reprovações", sd.get("reprovacao", {})), ("Ocorrências formais", sd.get("ocorrencia", {}))]:
        if not dist:
            continue
        chips = "".join(f'<span class="dist-chip">{html.escape(k)} · <b>{v}</b></span>' for k, v in sorted(dist.items(), key=lambda x: -x[1]))
        total = sum(dist.values())
        chips_html.append(f'<div class="dist-grupo"><div class="dist-grupo-titulo">{grupo} · total {total}</div>{chips}</div>')
    if chips_html:
        blocos.append(f"""
        <div class="analise-bloco">
          <h3 class="analise-titulo">🏷 Distribuição de motivos · agregada</h3>
          <div class="analise-sub">Por que as obras postergam / reprovam / abrem ocorrências</div>
          <div class="dist-wrap">{"".join(chips_html)}</div>
        </div>""")

    # Gaps grandes
    gg = an.get("gaps_grandes") or []
    if gg:
        rows = "".join(
            f"""<tr>
              <td>{html.escape(g["cliente"] or "—")}</td>
              <td class="num">{g["dias"]}d</td>
              <td class="num">{g["n_interacoes"]}</td>
            </tr>"""
            for g in gg[:10]
        )
        blocos.append(f"""
        <div class="analise-bloco">
          <h3 class="analise-titulo">⏱ Gaps grandes entre ciclos · {len(gg)} ocorrência{"s" if len(gg) != 1 else ""}</h3>
          <div class="analise-sub">Períodos longos (&gt;30d) entre execuções · indica retrabalho parado ou pós-venda travado</div>
          <table class="analise-tabela">
            <thead><tr><th>Cliente</th><th>Gap</th><th>Interações no período</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>""")

    return "".join(blocos)


def main():
    d = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    timelines = d.get("timelines") or []

    taxonomia = d.get("taxonomia") or {}
    analise_cross = calcular_analise_cross_obras(timelines, taxonomia)
    perfis_fluxo = calcular_perfis_fluxo(timelines)
    compilacao_prob = calcular_compilacao_problemas(timelines)
    cobertura_regex = d.get("cobertura_regex") or {}

    com_marcos = [t for t in timelines if (t.get("marcos") or [])]
    sem_marcos = [t for t in timelines if not (t.get("marcos") or [])]

    # Origem: nova / retorno / incerta / pre_contrato (vem do pipeline)
    n_novas = sum(1 for t in timelines if (t.get('origem_obra') or {}).get('origem') == 'nova')
    n_retorno = sum(1 for t in timelines if (t.get('origem_obra') or {}).get('origem') == 'retorno')
    n_incerta = sum(1 for t in timelines if (t.get('origem_obra') or {}).get('origem') == 'incerta')
    n_pre_contrato = sum(1 for t in timelines if (t.get('origem_obra') or {}).get('origem') == 'pre_contrato')

    # Ordena: mais marcos primeiro
    com_marcos.sort(key=lambda t: -len(t.get("marcos") or []))

    # Separa em 2 blocos: destrinchadas (calibração) vs ainda não destrinchadas
    destrinchadas = [t for t in com_marcos if is_destrinchada(t.get("cliente"))]
    ainda_nao = [t for t in com_marcos if not is_destrinchada(t.get("cliente"))]

    cards_destrinchadas_html = "".join(card_obra(o, taxonomia) for o in destrinchadas)
    cards_ainda_nao_html = "".join(card_obra(o, taxonomia) for o in ainda_nao)
    cards_html = "".join(card_obra(o, taxonomia) for o in com_marcos)  # mantém pra fallback

    # Contagem de obras por categoria (pra mostrar nos chips de filtro)
    from collections import Counter as _C
    cat_counts = _C()
    for t in com_marcos:
        ins = derivar_insights(t)
        for i in ins:
            cat_counts[i["tipo"]] += 1
        if (t.get("fase_derivada") or {}).get("tem_retrabalho"):
            cat_counts["retrabalho_ativo"] += 1
        if is_destrinchada(t.get("cliente")):
            cat_counts["destrinchada"] += 1
        seq = _seq_chave(t.get("marcos") or [])
        p = _classificar_perfil(len(t.get("marcos") or []), seq)
        cat_counts[f"perfil_{p}"] += 1

    sem_rows = ""
    for o in sem_marcos:
        sem_rows += f"""
        <tr>
          <td>{html.escape(o.get("cliente") or "—")}</td>
          <td><span class="grupo-tag g-{o.get("grupo_mix", "")[:3]}">{o.get("grupo_mix", "—")}</span></td>
          <td>{o.get("status") or "—"}</td>
          <td>{html.escape(o.get("fase_atual") or "—")}</td>
          <td class="num">{o.get("n_msgs_telegram", 0)}</td>
          <td class="mono">{fmt_data(o.get("data_exec_confirmada") or o.get("data_exec_prevista"))}</td>
        </tr>"""

    n_total = len(timelines)
    n_marcos_total = sum(len(t.get("marcos") or []) for t in timelines)
    gerado_em = d.get("gerado_em", "")
    pct_feliz = round(perfis_fluxo["perfis"].get("D", 0) / perfis_fluxo["total_2026"] * 100) if perfis_fluxo["total_2026"] else 0
    taxa_repro_2026 = perfis_fluxo.get("taxa_repro_final", 0)

    # Subtítulo do header · adapta entre piloto e massa
    modo_massa = (d.get("modo") == "massa")
    if modo_massa:
        subtitulo_header = "obras vivas no Painel · atualizado diariamente 04:00"
    else:
        subtitulo_header = "calibração de regex via msgs Telegram"

    # Legenda de cores agrupadas por categoria
    categorias_legenda = [
        ("Comercial",  ["contrato_assinado", "amostra_solicitada", "cor_aprovada"]),
        ("Escopo",     ["escopo_em_revisao", "escopo_aprovado", "escopo_atualizado", "aditivo_negociando"]),
        ("Vistoria",   ["vt_agendada", "vt_realizada", "relatorio_vt_qualidade", "vistoria_cliente"]),
        ("Logística",  ["equipe_definida", "material_entregue", "anuncio_nova_data"]),
        ("Execução",   ["camada_produto", "ultima_camada"]),
        ("Aprovação",  ["aprovacao_cliente", "finalizacao"]),
        ("Problemas",  ["obra_postergada", "troca_aplicador", "interrupcao_material", "cobranca_cor"]),
    ]
    legenda_html = ""
    for cat, tipos in categorias_legenda:
        chips = "".join(
            f'<span class="leg-chip"><span class="leg-dot" style="background:{COR_MARCO.get(t)}"></span>{LABELS_MARCO.get(t, t)}</span>'
            for t in tipos if t in COR_MARCO
        )
        legenda_html += f'<div class="leg-grupo"><div class="leg-grupo-titulo">{cat}</div>{chips}</div>'

    html_out = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Timelines · 10 obras-piloto · calibração de regex</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  :root {{
    --bg: #f0ebe3;
    --surface: #faf6ee;
    --surface-2: #f5efe3;
    --ink: #2a2520;
    --ink-soft: #6b6156;
    --ink-faint: #a89e92;
    --line: #d6cdbd;
    --line-soft: #e6dfd0;
    --gold: #b8884a;
    --gold-soft: #d4a548;
    --gold-bg: #fdfaf4;
    --shadow-sm: 0 1px 2px rgba(42,37,32,0.04), 0 1px 1px rgba(42,37,32,0.06);
    --shadow-md: 0 4px 10px rgba(42,37,32,0.06), 0 2px 4px rgba(42,37,32,0.04);
    --shadow-lg: 0 12px 28px rgba(42,37,32,0.10), 0 4px 8px rgba(42,37,32,0.04);
  }}

  html, body {{
    background: var(--bg);
    color: var(--ink);
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    font-size: 14px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }}
  .mono {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.04em; color: var(--ink-faint); }}

  /* Header sticky */
  header.top {{
    position: sticky; top: 0; z-index: 100;
    background: rgba(250, 246, 238, 0.92);
    backdrop-filter: blur(14px) saturate(1.2);
    -webkit-backdrop-filter: blur(14px) saturate(1.2);
    border-bottom: 1px solid var(--line);
    padding: 16px 40px;
    display: flex; align-items: center; gap: 24px;
  }}
  .top-title {{ font-weight: 800; font-size: 16px; color: var(--ink); letter-spacing: -0.01em; }}
  .top-title small {{ color: var(--ink-soft); font-weight: 400; margin-left: 10px; font-size: 12px; }}
  .top-action {{
    margin-left: auto;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 11.5px; font-weight: 700; letter-spacing: 0.04em;
    padding: 8px 14px;
    background: var(--gold); color: #fff;
    border: none; border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
  }}
  .top-action:hover {{
    background: var(--ink); transform: translateY(-1px); box-shadow: var(--shadow-md);
  }}
  .top-action.copiado {{ background: #5fa073; }}
  .top-stamp {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: var(--ink-faint); letter-spacing: 0.06em; text-transform: uppercase;
  }}

  /* Container */
  main {{ max-width: 1500px; margin: 0 auto; padding: 32px 40px 64px; }}

  .section-title {{
    font-size: 10.5px; font-weight: 700; color: var(--ink-soft);
    text-transform: uppercase; letter-spacing: 0.16em;
    margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--line);
    display: flex; align-items: center; gap: 10px;
  }}
  .section-title::before {{ content: ''; width: 4px; height: 14px; background: var(--gold); border-radius: 2px; }}

  /* Diagnóstico narrativo */
  .diagnostico {{ margin-bottom: 32px; }}
  .narr-bloco {{
    background: var(--surface); border: 1px solid var(--line-soft); border-radius: 12px;
    padding: 20px 24px; margin-bottom: 14px;
  }}
  .narr-titulo {{
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;
    color: var(--gold); margin-bottom: 10px;
  }}
  .narr-bloco p {{
    font-size: 13px; line-height: 1.7; color: var(--ink-soft); margin: 0 0 8px;
  }}
  .narr-bloco p:last-child {{ margin-bottom: 0; }}
  .narr-bloco p strong {{ color: var(--ink); }}
  .narr-desvios {{ display: flex; flex-direction: column; gap: 10px; }}
  .narr-desvio {{
    display: flex; gap: 16px; align-items: flex-start;
    padding: 14px 16px; border-radius: 8px;
    font-size: 12.5px; line-height: 1.6; color: var(--ink-soft);
    border-left: 4px solid var(--line);
  }}
  .narr-desvio strong {{ color: var(--ink); }}
  .narr-desvio.narr-grave {{ background: #fef2f2; border-left-color: #c45a5a; }}
  .narr-desvio.narr-alerta {{ background: #fefce8; border-left-color: #b89a4a; }}
  .narr-pct {{
    font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 800;
    min-width: 56px; text-align: center; color: var(--ink); flex-shrink: 0;
    line-height: 1.1;
  }}
  .narr-acoes {{ background: var(--bg); }}
  .narr-acao-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; }}
  .narr-acao {{
    display: flex; gap: 10px; align-items: flex-start;
    background: var(--surface); border: 1px solid var(--line-soft); border-radius: 8px;
    padding: 12px 14px; font-size: 12px; line-height: 1.6; color: var(--ink-soft);
  }}
  .narr-acao strong {{ color: var(--ink); }}
  .narr-acao-tag {{
    font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 800;
    padding: 3px 8px; border-radius: 4px; flex-shrink: 0; letter-spacing: 0.05em;
  }}
  .narr-p0 {{ background: #c45a5a; color: #fff; }}
  .narr-p1 {{ background: #b89a4a; color: #fff; }}

  /* Narrativa unificada */
  .narrativa-unificada {{ margin-bottom: 32px; }}
  .narr-capitulo {{
    display: flex; gap: 20px; padding: 28px 0;
    border-bottom: 1px solid var(--line-soft);
  }}
  .narr-capitulo:last-child {{ border-bottom: none; }}
  .narr-cap-num {{
    font-family: 'JetBrains Mono', monospace; font-size: 28px; font-weight: 800;
    color: var(--line); min-width: 44px; line-height: 1; padding-top: 2px;
  }}
  .narr-cap-corpo {{ flex: 1; }}
  .narr-indicadores {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 16px;
  }}
  .narr-ind {{
    background: var(--surface); border: 1px solid var(--line-soft); border-radius: 10px;
    padding: 14px 16px; text-align: center;
  }}
  .narr-ind-valor {{
    font-family: 'JetBrains Mono', monospace; font-size: 26px; font-weight: 800;
    color: var(--ink); line-height: 1.1;
  }}
  .narr-ind-valor small {{ font-size: 14px; }}
  .narr-ind-label {{ font-size: 10px; color: var(--ink-faint); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.08em; }}
  .narr-stats-lista {{ display: flex; flex-direction: column; gap: 12px; margin-top: 14px; }}
  .narr-stat {{
    display: flex; gap: 16px; align-items: flex-start;
    background: var(--surface); border: 1px solid var(--line-soft); border-radius: 10px;
    padding: 16px 18px;
  }}
  .narr-stat-alerta {{ border-left: 4px solid #b89a4a; }}
  .narr-stat-grave {{ border-left: 4px solid #c45a5a; }}
  .narr-stat-num {{
    font-family: 'JetBrains Mono', monospace; font-size: 28px; font-weight: 800;
    min-width: 56px; text-align: center; color: var(--ink); flex-shrink: 0;
    line-height: 1.1;
  }}
  .narr-stat-desc {{ font-size: 13px; line-height: 1.6; color: var(--ink-soft); }}
  .narr-stat-desc strong {{ color: var(--ink); }}
  .narr-concentradores {{ margin-top: 14px; padding: 14px 16px; background: var(--surface); border: 1px solid var(--line-soft); border-radius: 10px; }}
  .narr-gaps {{ display: flex; flex-direction: column; gap: 12px; }}
  .narr-gap {{
    display: flex; gap: 16px; align-items: flex-start;
    background: #faf5ee; border: 1px dashed var(--gold-soft); border-radius: 10px;
    padding: 16px 18px;
  }}
  .narr-gap-num {{
    font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 800;
    min-width: 56px; text-align: center; color: var(--gold); flex-shrink: 0;
    line-height: 1.1;
  }}
  .narr-gap div {{ font-size: 13px; line-height: 1.6; color: var(--ink-soft); }}
  .narr-gap strong {{ color: var(--ink); }}
  @media (max-width: 700px) {{
    .narr-capitulo {{ flex-direction: column; gap: 8px; }}
    .narr-cap-num {{ font-size: 20px; }}
    .narr-indicadores {{ grid-template-columns: repeat(2, 1fr); }}
  }}

  /* Compilação de problemas */
  .compilacao-problemas {{ margin-bottom: 32px; }}
  .prob-ranking {{ width: 100%; border-collapse: collapse; font-size: 12.5px; }}
  .prob-ranking th {{
    text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--ink-faint); padding: 6px 8px; border-bottom: 1px solid var(--line);
  }}
  .prob-ranking td {{ padding: 8px 8px; border-bottom: 1px solid var(--line-soft); }}
  .prob-ranking tr:last-child td {{ border-bottom: none; }}
  .prob-nome {{ color: var(--ink); font-weight: 600; }}
  .prob-n {{ text-align: right; color: var(--ink); font-weight: 700; }}
  .prob-pct {{ text-align: right; color: var(--ink-soft); min-width: 40px; }}
  .prob-bar-cell {{ width: 40%; padding-left: 12px !important; }}
  .prob-bar {{
    height: 8px; border-radius: 4px; min-width: 3px;
    transition: width 0.3s;
  }}
  .prob-ocf .prob-bar {{ background: #c45a5a; }}
  .prob-ocf .prob-nome::before {{ content: ''; display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #c45a5a; margin-right: 8px; }}
  .prob-repro .prob-bar {{ background: #b89a4a; }}
  .prob-repro .prob-nome::before {{ content: ''; display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #b89a4a; margin-right: 8px; }}
  .prob-status .prob-bar {{ background: var(--ink-faint); }}
  .prob-status .prob-nome::before {{ content: ''; display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: var(--ink-faint); margin-right: 8px; }}
  .prob-legenda {{
    display: flex; gap: 16px; margin-top: 12px; font-size: 10.5px; color: var(--ink-faint);
  }}
  .prob-leg-item {{ display: flex; align-items: center; gap: 5px; }}
  .prob-leg-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
  .prob-leg-dot.prob-ocf {{ background: #c45a5a; }}
  .prob-leg-dot.prob-repro {{ background: #b89a4a; }}
  .prob-leg-dot.prob-status {{ background: var(--ink-faint); }}
  .prob-concentradores {{ display: flex; flex-direction: column; gap: 6px; }}
  .prob-conc-item {{
    font-size: 12.5px; line-height: 1.6; color: var(--ink-soft);
    padding: 6px 0; border-bottom: 1px solid var(--line-soft);
  }}
  .prob-conc-item:last-child {{ border-bottom: none; }}
  .prob-conc-item strong {{ color: var(--ink); font-weight: 600; }}

  /* Stats topo */
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 32px; }}
  .stat {{ background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 18px 20px; box-shadow: var(--shadow-sm); }}
  .stat .v {{ font-family: 'JetBrains Mono', monospace; font-size: 26px; font-weight: 700; color: var(--ink); letter-spacing: -0.02em; line-height: 1; }}
  .stat .v small {{ font-size: 13px; color: var(--ink-faint); font-weight: 500; margin-left: 4px; }}
  .stat .l {{ font-size: 9.5px; color: var(--ink-faint); letter-spacing: 0.12em; text-transform: uppercase; margin-top: 8px; font-weight: 600; }}

  /* Análise cross-obras */
  .analise-cross {{ display: grid; gap: 14px; margin-bottom: 32px; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); }}
  .analise-bloco {{
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: 18px 20px;
    box-shadow: var(--shadow-sm);
  }}
  .analise-bloco.grave {{ border-left: 4px solid #c45a5a; background: #fef5f0; }}
  .analise-titulo {{ font-size: 14px; font-weight: 800; color: var(--ink); margin-bottom: 4px; letter-spacing: -0.01em; }}
  .analise-sub {{ color: var(--ink-soft); font-size: 11.5px; margin-bottom: 12px; }}
  .analise-tabela {{ width: 100%; border-collapse: collapse; font-size: 11.5px; }}
  .analise-tabela th {{ text-align: left; font-weight: 700; font-size: 9.5px; color: var(--ink-faint); text-transform: uppercase; letter-spacing: 0.1em; padding: 6px 8px; border-bottom: 1px solid var(--line); }}
  .analise-tabela td {{ padding: 7px 8px; border-bottom: 1px solid var(--line-soft); color: var(--ink); }}
  .analise-tabela td.num, .analise-tabela td.mono {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; }}
  .analise-tabela tr:last-child td {{ border-bottom: none; }}
  .analise-tabela td.razao {{ color: var(--ink-soft); font-size: 11px; font-style: italic; }}
  .mentira-tag {{
    font-size: 9.5px; padding: 2px 8px; border-radius: 100px;
    font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
  }}
  .mentira-tag.tipo-painel_adianta {{ background: #fef3c7; color: #92400e; }}
  .mentira-tag.tipo-painel_atrasa {{ background: #dbeafe; color: #1e40af; }}
  .mentira-tag.tipo-retrabalho_oculto {{ background: #fee2e2; color: #991b1b; }}
  .mentira-tag.tipo-finalizado_sem_marcos {{ background: #fce7f3; color: #9d174d; }}
  .mentira-tag.tipo-execucao_com_retrabalho {{ background: #ffe4e6; color: #881337; }}
  .mentira-tag.tipo-reparo_sem_retrabalho {{ background: #f3e8ff; color: #6b21a8; }}

  /* Medianas por fase */
  .med-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }}
  .med-card {{
    background: var(--bg); border-left: 3px solid var(--med-cor);
    border-radius: 6px; padding: 10px 12px;
  }}
  .med-fase {{ font-size: 10px; font-weight: 700; color: var(--ink-soft); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; }}
  .med-num {{ font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 700; color: var(--ink); line-height: 1; }}
  .med-num small {{ font-size: 11px; color: var(--ink-faint); margin-left: 2px; font-weight: 500; }}
  .med-range {{ font-size: 10px; color: var(--ink-faint); font-weight: 500; margin-left: 4px; }}
  .med-n {{ font-size: 9.5px; color: var(--ink-faint); margin-top: 4px; }}

  /* Distribuição de subtipos */
  .dist-wrap {{ display: flex; flex-direction: column; gap: 12px; }}
  .dist-grupo-titulo {{ font-size: 10px; font-weight: 800; color: var(--gold); text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 6px; }}
  .dist-chip {{
    display: inline-block; font-size: 10.5px;
    padding: 3px 10px; border-radius: 100px;
    background: var(--gold-bg); color: var(--ink);
    border: 1px solid var(--line-soft);
    margin: 2px 4px 2px 0;
  }}
  .dist-chip b {{ font-family: 'JetBrains Mono', monospace; color: var(--gold); font-weight: 700; margin-left: 3px; }}

  /* Legenda categorias */
  .legenda {{
    background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
    padding: 18px 22px; margin-bottom: 32px; box-shadow: var(--shadow-sm);
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 18px;
  }}
  .leg-grupo-titulo {{
    font-size: 9.5px; font-weight: 700; color: var(--gold);
    text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 8px;
  }}
  .leg-chip {{
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11.5px; color: var(--ink-soft);
    padding: 3px 8px 3px 4px; margin: 2px 6px 2px 0;
  }}
  .leg-dot {{ width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; box-shadow: 0 0 0 1px var(--line); }}

  /* Card de obra · ACORDEÃO (details/summary) */
  .obra-card {{
    background: var(--surface); border: 1px solid var(--line); border-radius: 10px;
    margin-bottom: 8px; box-shadow: var(--shadow-sm);
    overflow: hidden;
    transition: box-shadow 0.2s;
  }}
  .obra-card[open] {{ box-shadow: var(--shadow-md); }}

  /* Linha summary · 1 obra por linha · 56px de altura */
  .obra-summary {{
    display: grid;
    grid-template-columns: 110px 1.5fr 80px 1.2fr 280px 90px 28px;
    gap: 14px; align-items: center;
    padding: 14px 18px;
    cursor: pointer; user-select: none;
    list-style: none;
    transition: background 0.15s;
  }}
  .obra-summary::-webkit-details-marker {{ display: none; }}
  .obra-summary:hover {{ background: var(--gold-bg); }}
  .obra-card[open] .obra-summary {{
    background: var(--surface-2);
    border-bottom: 1px solid var(--line);
  }}

  .sum-grupo {{ justify-self: start; }}
  .sum-cli {{ font-weight: 700; font-size: 13.5px; color: var(--ink); letter-spacing: -0.01em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .sum-dots {{ display: inline-flex; gap: 5px; }}
  .sum-dots .dot {{
    width: 9px; height: 9px; border-radius: 50%;
    background: var(--line-soft); border: 1px solid var(--line);
  }}
  .sum-dots .dot.on {{ background: #7ea0b7; border-color: #5a7a91; }}
  .sum-dots .dot.on.durante {{ background: #5fa073; border-color: #3d7050; }}
  .sum-dots .dot.on.pos {{ background: #c45a5a; border-color: #8a3838; }}
  .sum-fase {{
    font-size: 11px; font-weight: 700; color: #fff;
    background: var(--fr-cor); padding: 4px 12px; border-radius: 100px;
    text-align: center; letter-spacing: 0.02em;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }}
  .sum-stats {{ display: flex; gap: 16px; justify-content: flex-end; }}
  .sum-stat {{ font-size: 11px; color: var(--ink-faint); white-space: nowrap; }}
  .sum-stat b {{ font-family: 'JetBrains Mono', monospace; color: var(--ink); font-weight: 700; font-size: 12.5px; margin-right: 3px; }}
  .sum-badges {{ display: flex; gap: 4px; justify-content: flex-end; }}
  .mini-badge {{
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    padding: 3px 7px; border-radius: 100px; font-weight: 700;
    background: var(--bg); color: var(--ink-faint); border: 1px solid var(--line-soft);
  }}
  .mini-badge.ciclos {{ background: #fef3c7; color: #92400e; border-color: #fde68a; }}
  .mini-badge.retr {{ background: #fee2e2; border-color: #fca5a5; padding: 3px 6px; }}
  .mini-badge.perfil-badge {{ border: none; font-size: 11px; font-weight: 800; letter-spacing: 0.04em; padding: 3px 8px; }}

  /* Barra de fluxo esperado */
  .fluxo-barra {{
    display: flex; align-items: flex-start; gap: 2px;
    background: var(--surface-2); border: 1px solid var(--line-soft); border-radius: 8px;
    padding: 12px 14px; margin-bottom: 12px; overflow-x: auto;
  }}
  .fluxo-step {{
    display: flex; flex-direction: column; align-items: center; gap: 3px;
    min-width: 62px; flex: 1; position: relative;
  }}
  .fluxo-step::after {{
    content: ''; position: absolute; top: 8px; left: 55%; right: -50%; height: 2px;
    background: var(--line-soft); z-index: 0;
  }}
  .fluxo-step:last-child::after {{ display: none; }}
  .fluxo-dot {{
    width: 16px; height: 16px; border-radius: 50%; border: 2px solid var(--line);
    background: var(--surface); z-index: 1; flex-shrink: 0;
  }}
  .fluxo-dot.ok {{ background: #3d8a5a; border-color: #3d8a5a; }}
  .fluxo-dot.skip {{ background: #fff; border-color: #c45a5a; }}
  .fluxo-dot.skip::after {{ content: '×'; color: #c45a5a; font-size: 11px; font-weight: 800; display: flex; align-items: center; justify-content: center; margin-top: -1px; }}
  .fluxo-dot.pend {{ background: var(--surface); border-color: var(--line); }}
  .fluxo-dot.reprova {{ background: #c45a5a; border-color: #c45a5a; }}
  .fluxo-step.ok .fluxo-label {{ color: var(--ink); font-weight: 600; }}
  .fluxo-step.skip .fluxo-label {{ color: #c45a5a; font-weight: 600; text-decoration: line-through; }}
  .fluxo-step.pend .fluxo-label {{ color: var(--ink-faint); }}
  .fluxo-step.reprova .fluxo-label {{ color: #c45a5a; font-weight: 700; }}
  .fluxo-label {{ font-size: 9px; text-transform: uppercase; letter-spacing: 0.06em; text-align: center; }}
  .fluxo-delta {{
    font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--ink-soft);
    background: var(--surface); border: 1px solid var(--line-soft); border-radius: 3px;
    padding: 1px 4px; margin-top: 1px;
  }}

  .sum-toggle {{
    color: var(--ink-faint); font-size: 14px;
    transition: transform 0.2s;
    text-align: center;
  }}
  .obra-card[open] .sum-toggle {{ transform: rotate(180deg); }}

  /* Detalhe expandido */
  .obra-detail {{ padding: 22px 26px 26px; }}

  .obra-card-head {{ margin-bottom: 16px; }}
  .obra-card-id {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }}
  .obra-meta {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .obra-meta-item {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px; background: var(--bg); border-radius: 6px;
    font-size: 11px; color: var(--ink-soft);
  }}
  .obra-meta-item strong {{ color: var(--ink-faint); font-weight: 700; font-size: 9px; text-transform: uppercase; letter-spacing: 0.08em; margin-right: 2px; }}

  .grupo-tag {{
    font-size: 9.5px; padding: 4px 12px; border-radius: 100px;
    font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;
  }}
  .g-fin {{ background: #d8e3eb; color: #4a6478; }}
  .g-exec {{ background: #c7e0ce; color: #2a5a18; }}
  .g-rep {{ background: #f0c8c8; color: #6b1a1a; }}

  /* Pills de tempo */
  .tempo-pills {{
    display: flex; flex-wrap: wrap; gap: 12px;
    margin: 18px 0 22px; padding: 16px 0;
    border-top: 1px solid var(--line-soft); border-bottom: 1px solid var(--line-soft);
  }}
  .tempo-pill {{
    display: inline-flex; flex-direction: column; padding: 10px 18px;
    background: var(--gold-bg); border: 1px solid var(--line);
    border-radius: 100px; min-width: 130px;
  }}
  .tempo-pill.principal {{
    background: linear-gradient(135deg, #b8884a 0%, #d4a548 100%);
    border: none; color: #fff; box-shadow: 0 4px 12px rgba(184,136,74,0.3);
  }}
  .tempo-pill-label {{
    font-size: 8.5px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.14em; color: var(--ink-faint); margin-bottom: 4px;
  }}
  .tempo-pill.principal .tempo-pill-label {{ color: rgba(255,255,255,0.85); }}
  .tempo-pill-num {{
    font-family: 'JetBrains Mono', monospace; font-size: 20px;
    font-weight: 700; letter-spacing: -0.02em; color: var(--ink); line-height: 1;
  }}
  .tempo-pill.principal .tempo-pill-num {{ font-size: 22px; color: #fff; }}
  .tempo-pill-num small {{ font-size: 11px; font-weight: 500; color: var(--ink-faint); margin-left: 3px; }}
  .tempo-pill.principal .tempo-pill-num small {{ color: rgba(255,255,255,0.75); }}

  /* Lista cronológica de marcos */
  .ciclo-marcos-lista {{ margin-top: 8px; }}
  .marcos-lista-titulo {{
    font-size: 9.5px; font-weight: 700; color: var(--ink-soft);
    text-transform: uppercase; letter-spacing: 0.16em;
    margin-bottom: 14px; padding-left: 4px;
  }}

  /* Fase derivada · badge no header do card */
  .fase-derivada-badge {{
    display: inline-block; margin-top: 12px;
    padding: 6px 14px; border-radius: 100px;
    color: #fff; font-size: 11px; font-weight: 700;
    letter-spacing: 0.04em; box-shadow: var(--shadow-sm);
  }}

  /* Equipe · 3 grupos (Monofloor, Aplicadores, Visitas) */
  .equipe-blocos {{ display: flex; flex-direction: column; gap: 6px; margin-top: 12px; }}
  .eq-grupo {{ display: flex; flex-wrap: wrap; gap: 5px; align-items: center; }}
  .eq-grupo-label {{
    font-size: 9px; font-weight: 800; letter-spacing: 0.14em;
    color: var(--ink-faint); text-transform: uppercase;
    margin-right: 4px; min-width: 110px;
  }}
  .aplic-chip {{
    display: inline-flex; align-items: center;
    font-size: 11px; font-weight: 600;
    padding: 3px 10px; border-radius: 100px;
    background: var(--bg); color: var(--ink-soft);
    border: 1px solid var(--line-soft);
  }}
  /* Monofloor */
  .aplic-chip.mf-ops {{ background: #dbeafe; color: #1e40af; border-color: #93c5fd; }}
  .aplic-chip.mf-aten {{ background: #f3e8ff; color: #6b21a8; border-color: #d8b4fe; }}
  .aplic-chip.mf-cons {{ background: #fef3c7; color: #92400e; border-color: #fde68a; }}
  /* Aplicadores */
  .aplic-chip.oficial {{ background: linear-gradient(135deg, #b8884a 0%, #d4a548 100%); color: #fff; border: none; }}
  .aplic-chip.observado {{ background: #dcfce7; color: #166534; border-color: #86efac; }}
  /* Visitas Monofloor */
  .aplic-chip.presenca {{ background: var(--gold-bg); color: var(--gold); border-color: var(--gold-soft); }}

  /* Bloco Pré-obra · título antes do kanban */
  .bloco-fase-titulo {{
    font-size: 10px; font-weight: 800; color: var(--ink-soft);
    text-transform: uppercase; letter-spacing: 0.14em;
    margin: 12px 0 8px;
    padding-bottom: 6px; border-bottom: 1px solid var(--gold);
  }}

  /* Insights · padrões observados */
  .insights-wrap {{ margin: 18px 0 14px; }}
  .insights-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px; }}
  .insight-item {{
    padding: 10px 14px; border-radius: 6px;
    border-left: 3px solid var(--ink-soft);
    background: var(--bg);
  }}
  .insight-titulo {{
    font-size: 12px; font-weight: 700; color: var(--ink);
    margin-bottom: 3px; letter-spacing: -0.01em;
  }}
  .insight-desc {{
    font-size: 11px; color: var(--ink-soft); line-height: 1.45;
  }}
  .insight-critica {{
    border-left-color: #6b1a1a;
    background: #fce4e4;
    border-left-width: 5px;
  }}
  .insight-critica .insight-titulo {{ color: #6b1a1a; font-weight: 800; }}
  .insight-alta {{
    border-left-color: #c45a5a;
    background: #fef5f0;
  }}
  .insight-alta .insight-titulo {{ color: #991b1b; }}
  .insight-media {{
    border-left-color: var(--gold);
    background: var(--gold-bg);
  }}
  .insight-info {{
    border-left-color: #7ea0b7;
    background: #f0f5f9;
  }}

  /* Heatmap msgs/dia */
  .heatmap-wrap {{ margin: 14px 0 18px; }}
  .heatmap-titulo {{
    font-size: 10px; font-weight: 700; color: var(--ink-soft);
    text-transform: uppercase; letter-spacing: 0.14em;
    margin-bottom: 6px;
  }}
  .heatmap-grid {{
    display: flex; flex-wrap: nowrap; gap: 1px;
    overflow-x: auto;
    padding: 4px 0;
  }}
  .heat-cell {{
    width: 5px; height: 14px;
    flex-shrink: 0;
    border-radius: 1px;
    cursor: help;
  }}
  .heatmap-eixo {{
    display: flex; justify-content: space-between;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; color: var(--ink-faint);
    margin-top: 2px;
  }}

  /* OS Indústria · tabela de materiais enviados */
  .os-wrap {{ display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; }}
  .os-bloco {{
    background: var(--surface);
    border: 1px solid var(--line-soft);
    border-radius: 6px;
    padding: 10px 12px;
  }}
  .os-head {{
    display: flex; align-items: center; gap: 12px;
    padding-bottom: 6px; margin-bottom: 6px;
    border-bottom: 1px solid var(--line-soft);
  }}
  .os-data {{
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: var(--gold); font-weight: 700;
  }}
  .os-nome {{
    font-size: 11.5px; color: var(--ink); font-weight: 600;
    flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }}
  .os-count {{
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    color: var(--ink-faint); background: var(--bg);
    padding: 2px 8px; border-radius: 100px;
    border: 1px solid var(--line-soft); font-weight: 700;
  }}
  .os-tabela {{
    width: 100%; border-collapse: collapse;
    font-size: 11px;
  }}
  .os-tabela th {{
    text-align: left; font-weight: 700; font-size: 9px;
    color: var(--ink-faint); text-transform: uppercase; letter-spacing: 0.1em;
    padding: 5px 8px; border-bottom: 1px solid var(--line-soft);
  }}
  .os-tabela td {{
    padding: 5px 8px; border-bottom: 1px solid var(--line-soft);
    color: var(--ink);
  }}
  .os-tabela tr:last-child td {{ border-bottom: none; }}
  .os-tabela td.num, .os-tabela td.mono {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; }}

  /* Header de ciclo · separador entre ciclos */
  .ciclo-header {{
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
    padding: 8px 14px; margin: 14px 0 8px;
    background: linear-gradient(135deg, #b8884a 0%, #d4a548 100%);
    color: #fff; border-radius: 6px;
    box-shadow: var(--shadow-sm);
  }}
  .ciclo-header.ciclo-retorno {{
    background: linear-gradient(135deg, #c45a5a 0%, #e07878 100%);
  }}
  .ciclo-num {{
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    background: rgba(255,255,255,0.22); padding: 4px 10px;
    border-radius: 100px; font-weight: 700; letter-spacing: 0.06em;
  }}
  .ciclo-nome {{
    font-size: 14px; font-weight: 800;
    text-transform: uppercase; letter-spacing: 0.06em;
  }}
  .ciclo-periodo {{
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    opacity: 0.92; margin-left: auto;
  }}
  .ciclo-count {{
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    background: rgba(255,255,255,0.22); padding: 3px 9px;
    border-radius: 100px; font-weight: 600;
  }}

  /* Gap entre ciclos · agora com bloco de contexto */
  .gap-bloco {{
    margin: 10px 0;
    background: var(--bg);
    border: 1px dashed var(--line);
    border-left: 3px solid var(--gold-soft);
    border-radius: 6px;
    padding: 8px 14px 10px;
  }}
  .gap-divider {{
    color: var(--ink-soft); font-size: 11px;
    padding-bottom: 6px;
    border-bottom: 1px dashed var(--line-soft);
    margin-bottom: 8px;
    font-weight: 600;
  }}
  .gap-divider strong {{ color: var(--gold); font-family: 'JetBrains Mono', monospace; font-weight: 700; }}

  .gap-resumo {{
    display: flex; flex-wrap: wrap; gap: 5px;
    margin-bottom: 8px;
  }}
  .gap-chip {{
    font-size: 10px; padding: 2px 8px; border-radius: 100px;
    background: var(--gold-bg); color: var(--gold);
    border: 1px solid var(--line-soft);
    white-space: nowrap;
  }}
  .gap-chip b {{ font-family: 'JetBrains Mono', monospace; font-weight: 700; }}

  .gap-marcos-lista {{ display: flex; flex-direction: column; gap: 2px; }}
  .gap-marco {{
    display: grid; grid-template-columns: 8px 50px 1fr auto;
    gap: 8px; align-items: center;
    padding: 4px 8px; border-radius: 4px;
    background: var(--surface);
    border: 1px solid var(--line-soft);
    cursor: help; font-size: 11px;
  }}
  .gap-marco:hover {{ background: var(--gold-bg); border-color: var(--gold); }}
  .gap-marco-bola {{ width: 8px; height: 8px; border-radius: 50%; box-shadow: 0 0 0 1px var(--line); }}
  .gap-marco-data {{ font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--gold); font-weight: 700; }}
  .gap-marco-label {{ color: var(--ink); font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .gap-marco-autor {{ font-size: 10px; color: var(--ink-faint); font-style: italic; max-width: 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}

  /* KANBAN interno · 1 coluna por bloco renderizado (cada chamada de renderizar_grupos) */
  .fases-kanban {{
    display: grid;
    gap: 8px; padding-bottom: 4px;
  }}
  .fases-kanban.kanban-1fases {{ grid-template-columns: 1fr; }}
  .fases-kanban.kanban-2fases {{ grid-template-columns: 3fr 1fr; }}
  .fases-kanban.kanban-3fases {{ grid-template-columns: 2fr 2fr 1fr; }}

  /* Ciclo · 3 colunas externas (Pré · Execução · Pós) */
  .ciclo-grid {{
    display: grid;
    grid-template-columns: 1fr 1.4fr 1fr;
    gap: 12px;
    margin-bottom: 12px;
  }}
  .ciclo-col-vazia {{
    background: var(--bg);
    border: 1px dashed var(--line-soft);
    border-radius: 6px;
    color: var(--ink-faint);
    text-align: center;
    padding: 24px 8px;
    font-size: 13px; font-style: italic;
    align-self: stretch;
  }}

  .fase-coluna {{
    background: var(--bg);
    border: 1px solid var(--line-soft);
    border-top: 3px solid var(--fase-cor);
    border-radius: 6px;
    padding: 8px 10px 10px;
    min-width: 180px;
    display: flex;
    flex-direction: column;
  }}
  .fase-coluna.coluna-inativa {{ opacity: 0.45; }}
  .fase-coluna.coluna-retrabalho {{
    border-style: dashed;
    background: #fef5f0;
  }}

  .fase-coluna-head {{
    display: flex; align-items: center; gap: 6px;
    padding-bottom: 6px; margin-bottom: 8px;
    border-bottom: 1px solid var(--line-soft);
  }}
  .fase-coluna-ordem {{
    width: 16px; height: 16px; border-radius: 50%;
    background: var(--fase-cor); color: #fff;
    font-family: 'JetBrains Mono', monospace; font-size: 9px;
    font-weight: 700; display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }}
  .fase-coluna-nome {{
    font-weight: 700; font-size: 10.5px;
    color: var(--ink); letter-spacing: 0;
    flex: 1; line-height: 1.2;
  }}
  .fase-coluna-count {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px; color: var(--ink-faint); font-weight: 700;
    background: var(--surface); padding: 1px 5px; border-radius: 100px;
    border: 1px solid var(--line-soft);
    min-width: 18px; text-align: center;
  }}
  .fase-coluna-dt {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; color: #fff; font-weight: 700;
    background: var(--fase-cor); padding: 2px 7px; border-radius: 100px;
    letter-spacing: 0.02em;
  }}
  .fase-coluna-corpo {{
    display: flex; flex-direction: column;
    gap: 8px; flex: 1;
  }}

  .coluna-vazia {{
    color: var(--ink-faint); font-style: italic; text-align: center;
    font-size: 13px; padding: 8px 0;
  }}

  /* Bloco de MARCO PRINCIPAL dentro da coluna */
  .principal-bloco {{ }}
  .principal-titulo {{
    display: flex; align-items: center; gap: 5px;
    font-size: 8.5px; font-weight: 800;
    color: var(--ink-soft); text-transform: uppercase;
    letter-spacing: 0.12em; margin-bottom: 4px;
    padding-left: 2px;
  }}
  .principal-count {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.5px; color: var(--ink-faint);
    background: var(--surface); padding: 1px 4px; border-radius: 3px;
    border: 1px solid var(--line-soft); font-weight: 700;
    margin-left: auto;
  }}

  /* SUB-MARCOS · 1 LINHA · compacto */
  .sub-lista {{ display: flex; flex-direction: column; gap: 2px; }}
  .sub-item {{
    display: grid; grid-template-columns: 8px 36px 1fr auto;
    gap: 6px; align-items: center;
    padding: 4px 6px; border-radius: 4px;
    background: var(--surface);
    border: 1px solid var(--line-soft);
    cursor: help; transition: background 0.12s, border-color 0.12s;
  }}
  .sub-item:hover {{
    background: var(--gold-bg);
    border-color: var(--gold);
  }}
  .sub-bola {{
    width: 8px; height: 8px; border-radius: 50%;
    box-shadow: 0 0 0 1px var(--line);
  }}
  .sub-info {{ display: contents; }}
  .sub-top {{ display: contents; }}
  .sub-data {{
    font-family: 'JetBrains Mono', monospace; font-size: 9.5px;
    color: var(--gold); font-weight: 700; letter-spacing: 0.04em;
    white-space: nowrap;
  }}
  .sub-label {{
    font-weight: 600; color: var(--ink); font-size: 11px;
    line-height: 1.25; min-width: 0;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }}
  .sub-autor {{
    font-size: 9.5px; color: var(--ink-faint); font-style: italic;
    text-align: right;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    max-width: 110px;
  }}

  /* Subtipo · motivo da postergação ou natureza da reprovação */
  .subtipo-tag {{
    display: inline-block;
    font-size: 8px; font-weight: 700;
    padding: 1px 5px; border-radius: 100px;
    text-transform: uppercase; letter-spacing: 0.04em;
    background: var(--bg); color: var(--ink-soft);
    border: 1px solid var(--line-soft);
    white-space: nowrap;
    margin-left: 4px;
  }}
  /* Postergação · cores por motivo */
  .subtipo-tag-cliente_solicitou {{ background: #fee2e2; color: #991b1b; border-color: #fca5a5; }}
  .subtipo-tag-tecnico_obra      {{ background: #fef3c7; color: #92400e; border-color: #fde68a; }}
  .subtipo-tag-escopo_pendente   {{ background: #f3e8ff; color: #6b21a8; border-color: #d8b4fe; }}
  .subtipo-tag-cronograma        {{ background: #dbeafe; color: #1e40af; border-color: #93c5fd; }}
  .subtipo-tag-sem_motivo        {{ background: #f1f5f9; color: #64748b; border-color: #cbd5e1; }}
  /* Reprovação · cores por natureza */
  .subtipo-tag-defeito_relatado     {{ background: #fee2e2; color: #991b1b; border-color: #fca5a5; }}
  .subtipo-tag-proposta_tecnica     {{ background: #fef3c7; color: #92400e; border-color: #fde68a; }}
  .subtipo-tag-decisao_cliente      {{ background: #dbeafe; color: #1e40af; border-color: #93c5fd; }}
  .subtipo-tag-escopo_definido      {{ background: #f3e8ff; color: #6b21a8; border-color: #d8b4fe; }}
  .subtipo-tag-agendamento_reparo   {{ background: #fce7f3; color: #9d174d; border-color: #f9a8d4; }}
  .subtipo-tag-relatorio_qualidade  {{ background: #ecfccb; color: #3f6212; border-color: #bef264; }}
  .subtipo-tag-confirmacao_pendente {{ background: #ffedd5; color: #9a3412; border-color: #fdba74; }}
  .subtipo-tag-solicitacao_admin    {{ background: #f1f5f9; color: #475569; border-color: #cbd5e1; }}
  .subtipo-tag-tratativa            {{ background: #f5f5f4; color: #57534e; border-color: #d6d3d1; }}
  /* Ocorrências formais · cores por tipo */
  .subtipo-tag-falha_comunicacao    {{ background: #fed7aa; color: #7c2d12; border-color: #fdba74; }}
  .subtipo-tag-reclamacao_cliente   {{ background: #fee2e2; color: #7f1d1d; border-color: #fca5a5; }}
  .subtipo-tag-atraso_cronograma    {{ background: #fef3c7; color: #78350f; border-color: #fde68a; }}
  .subtipo-tag-problema_material    {{ background: #fce7f3; color: #831843; border-color: #f9a8d4; }}
  .subtipo-tag-problema_qualidade   {{ background: #ffe4e6; color: #881337; border-color: #fda4af; }}
  .subtipo-tag-problema_logistica   {{ background: #e0e7ff; color: #312e81; border-color: #a5b4fc; }}

  .vazio {{
    color: var(--ink-faint); font-style: italic; font-size: 12.5px;
    padding: 16px; text-align: center; background: var(--bg); border-radius: 6px;
  }}

  /* Tabela obras sem marcos */
  table.obras-vazias {{
    width: 100%; border-collapse: collapse;
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 12px; overflow: hidden; box-shadow: var(--shadow-sm); margin-top: 12px;
  }}
  table.obras-vazias th {{
    text-align: left; font-weight: 700; font-size: 9.5px;
    color: var(--ink-faint); text-transform: uppercase; letter-spacing: 0.1em;
    padding: 14px 16px; border-bottom: 2px solid var(--line); background: var(--surface-2);
  }}
  table.obras-vazias td {{
    padding: 13px 16px; border-bottom: 1px solid var(--line-soft);
    color: var(--ink); font-size: 13px;
  }}
  table.obras-vazias td.num, table.obras-vazias td.mono {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; }}
  table.obras-vazias tr:last-child td {{ border-bottom: none; }}
  table.obras-vazias tr:hover td {{ background: var(--bg); }}

  h2.bloco {{
    font-size: 18px; font-weight: 800; color: var(--ink);
    margin: 40px 0 6px; letter-spacing: -0.015em;
  }}
  .bloco-sub {{ color: var(--ink-soft); font-size: 13px; margin-bottom: 20px; }}

  /* Controles de bulk expand/collapse */
  .acordeon-controles {{
    display: flex; gap: 10px; align-items: center;
  }}

  /* Filtro de obras */
  .filtros-wrap {{
    display: flex; gap: 14px; align-items: center;
    margin-bottom: 18px;
    flex-wrap: wrap;
  }}
  .busca-input {{
    flex: 1; min-width: 280px;
    padding: 10px 16px; font-size: 13px;
    border: 1px solid var(--line); border-radius: 8px;
    background: var(--surface); color: var(--ink);
    font-family: inherit;
    transition: all 0.15s;
  }}
  .busca-input:focus {{
    outline: none; border-color: var(--gold);
    box-shadow: 0 0 0 3px rgba(184,136,74,0.15);
  }}
  .busca-input[data-resultado]::after {{
    content: attr(data-resultado);
  }}

  /* Sub-blocos · destrinchadas vs ainda não */
  .sub-bloco {{
    font-size: 14px; font-weight: 800; color: var(--ink);
    margin: 28px 0 4px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--gold-soft);
    letter-spacing: -0.01em;
  }}
  .sub-bloco-info {{
    font-size: 11.5px; color: var(--ink-soft);
    margin-bottom: 14px; font-style: italic;
  }}
  .bloco-obras {{ margin-bottom: 32px; }}

  /* Card destrinchada · borda dourada destacada */
  .obra-card.destrinchada {{
    border-color: var(--gold);
    background: linear-gradient(to right, var(--gold-bg) 0px, var(--surface) 4px);
  }}
  .destrinchada-tag {{
    background: linear-gradient(135deg, #b8884a 0%, #d4a548 100%);
    color: #fff;
    border: none;
    font-size: 11px;
    padding: 2px 6px;
  }}

  /* Badge retorno/pre-contrato */
  .natureza-retro {{
    background: #8b4513; color: #fff; border: none;
    font-size: 9px; font-weight: 800; letter-spacing: 0.08em;
    padding: 2px 6px; border-radius: 3px;
  }}
  .natureza-precontrato {{
    background: #3a5a8c; color: #b8d4f0; border: none;
    font-size: 9px; font-weight: 700; letter-spacing: 0.06em;
    padding: 2px 6px; border-radius: 3px;
  }}
  .alerta-parada {{
    font-size: 9px; font-weight: 800; letter-spacing: 0.06em;
    padding: 2px 8px; border-radius: 3px; border: none;
    animation: pulse-alerta 2s ease-in-out infinite;
  }}
  @keyframes pulse-alerta {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.7; }}
  }}

  /* Filtro origem da obra */
  .natureza-filtro {{
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 14px;
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: 12px 18px;
    box-shadow: var(--shadow-sm);
  }}
  .nat-label {{
    font-size: 10.5px; font-weight: 700; color: var(--ink-soft);
    text-transform: uppercase; letter-spacing: 0.12em;
    margin-right: 6px;
  }}
  .nat-btn {{
    padding: 8px 18px; border-radius: 8px;
    font-size: 13px; font-weight: 600;
    border: 2px solid var(--line);
    background: var(--surface); color: var(--ink);
    cursor: pointer; transition: all 0.15s;
  }}
  .nat-btn b {{ font-family: 'JetBrains Mono', monospace; font-size: 15px; margin-left: 6px; }}
  .nat-btn:hover {{ border-color: var(--gold-soft); }}
  .nat-btn.nat-ativa {{ border-color: var(--gold); background: var(--gold-bg); color: var(--gold); }}
  .nat-btn.nat-nova.nat-ativa {{ border-color: #4a9; background: rgba(68,170,153,0.12); color: #4a9; }}
  .nat-btn.nat-retro.nat-ativa {{ border-color: #8b4513; background: rgba(139,69,19,0.12); color: #c47a3a; }}
  .nat-btn.nat-incerta.nat-ativa {{ border-color: #b8860b; background: rgba(184,134,11,0.12); color: #d4a017; }}
  .nat-btn.nat-precontrato.nat-ativa {{ border-color: #3a5a8c; background: rgba(58,90,140,0.12); color: #6b9fd4; }}

  /* Badge incerta */
  .natureza-incerta {{
    background: #8b7500; color: #fff; border: none;
    font-size: 9px; font-weight: 700; letter-spacing: 0.06em;
    padding: 2px 6px; border-radius: 3px;
  }}

  /* Indicador visual origem nos cards da narrativa */
  .narr-ind-nova .narr-ind-valor {{ color: #4a9; }}
  .narr-ind-retro .narr-ind-valor {{ color: #c47a3a; }}
  .narr-ind-incerta .narr-ind-valor {{ color: #d4a017; }}
  .narr-ind-precontrato .narr-ind-valor {{ color: #6b9fd4; }}
  .narr-ind-5 {{ grid-template-columns: repeat(5, 1fr); }}

  /* Card filtrado (oculto via JS) · garantia visual */
  .obra-card.filtrada {{ display: none !important; }}

  /* Chips de filtro por categoria */
  .cat-filtros {{
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; padding: 14px 18px;
    margin-bottom: 18px;
    box-shadow: var(--shadow-sm);
  }}
  .cat-filtros-titulo {{
    font-size: 10.5px; font-weight: 700; color: var(--ink-soft);
    text-transform: uppercase; letter-spacing: 0.12em;
    margin-bottom: 12px;
  }}
  .cat-grupo {{
    display: flex; flex-wrap: wrap; gap: 6px;
    align-items: center;
    margin-bottom: 8px;
  }}
  .cat-grupo:last-child {{ margin-bottom: 0; }}
  .cat-grupo-label {{
    font-size: 10px; font-weight: 700; color: var(--ink-faint);
    letter-spacing: 0.08em; text-transform: uppercase;
    margin-right: 8px; min-width: 130px;
  }}
  .cat-chip {{
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 600;
    padding: 5px 12px; border-radius: 100px;
    cursor: pointer; user-select: none;
    border: 1px solid var(--line);
    background: var(--bg); color: var(--ink-soft);
    font-family: inherit;
    transition: all 0.15s;
  }}
  .cat-chip b {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; font-weight: 700;
    background: rgba(0,0,0,0.06);
    padding: 1px 6px; border-radius: 100px;
  }}
  .cat-chip:hover {{ background: var(--gold-bg); border-color: var(--gold); }}
  .cat-chip.ativa {{
    background: var(--ink); color: #fff; border-color: var(--ink);
    box-shadow: var(--shadow-sm);
  }}
  .cat-chip.ativa b {{ background: rgba(255,255,255,0.18); color: #fff; }}
  /* Cores por gravidade na borda quando inativa */
  .cat-chip.cat-critica {{ border-left: 3px solid #6b1a1a; }}
  .cat-chip.cat-alta {{ border-left: 3px solid #c45a5a; }}
  .cat-chip.cat-media {{ border-left: 3px solid var(--gold); }}
  .cat-chip.cat-info {{ border-left: 3px solid #7ea0b7; }}
  .cat-chip.cat-status {{ border-left: 3px solid #94a3b8; }}
  .cat-chip.cat-destrinchada {{ border-left: 3px solid #b8884a; }}
  .cat-chip.cat-perfil-A {{ border-left: 3px solid #a89e92; }}
  .cat-chip.cat-perfil-B {{ border-left: 3px solid #b89a4a; }}
  .cat-chip.cat-perfil-C {{ border-left: 3px solid #4a7ab8; }}
  .cat-chip.cat-perfil-D {{ border-left: 3px solid #3d8a5a; }}
  .cat-chip.cat-perfil-E {{ border-left: 3px solid #c45a5a; }}
  .cat-chip.cat-perfil-F {{ border-left: 3px solid #b83a3a; }}
  .cat-chip.cat-perfil-A.ativa {{ background: #a89e92; border-color: #a89e92; }}
  .cat-chip.cat-perfil-B.ativa {{ background: #b89a4a; border-color: #b89a4a; }}
  .cat-chip.cat-perfil-C.ativa {{ background: #4a7ab8; border-color: #4a7ab8; }}
  .cat-chip.cat-perfil-D.ativa {{ background: #3d8a5a; border-color: #3d8a5a; }}
  .cat-chip.cat-perfil-E.ativa {{ background: #c45a5a; border-color: #c45a5a; }}
  .cat-chip.cat-perfil-F.ativa {{ background: #b83a3a; border-color: #b83a3a; }}

  .resultado-filtros {{
    display: none;
    background: var(--gold-bg); border: 1px solid var(--gold-soft);
    color: var(--gold); padding: 10px 16px;
    border-radius: 8px; font-size: 12px;
    margin-bottom: 14px;
  }}
  .resultado-filtros strong {{ font-family: 'JetBrains Mono', monospace; font-size: 14px; }}

  /* CTA · botões grandes pra navegar entre telas */
  .cta-tela {{
    display: flex; align-items: center; justify-content: space-between;
    width: 100%; margin: 40px 0 20px;
    padding: 22px 32px;
    background: linear-gradient(135deg, #b8884a 0%, #d4a548 100%);
    color: #fff; border: none; border-radius: 14px;
    cursor: pointer; font-family: inherit;
    box-shadow: 0 6px 18px rgba(184,136,74,0.3), 0 2px 4px rgba(0,0,0,0.06);
    transition: all 0.2s cubic-bezier(0.2, 0.9, 0.3, 1);
  }}
  .cta-tela:hover {{
    transform: translateY(-2px);
    box-shadow: 0 10px 24px rgba(184,136,74,0.42), 0 3px 6px rgba(0,0,0,0.08);
  }}
  .cta-tela:active {{ transform: translateY(0); }}
  .cta-label {{
    font-size: 18px; font-weight: 800;
    letter-spacing: -0.01em;
  }}
  .cta-meta {{
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    opacity: 0.85; letter-spacing: 0.04em;
    flex: 1; text-align: center; margin: 0 20px;
  }}
  .cta-arrow {{
    font-size: 24px; font-weight: 700;
    transition: transform 0.2s;
  }}
  .cta-tela:hover .cta-arrow {{ transform: translateX(6px); }}

  .cta-voltar {{
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--surface); border: 1px solid var(--line);
    color: var(--ink-soft); font-family: inherit;
    font-size: 12px; font-weight: 600;
    padding: 10px 18px; border-radius: 8px;
    cursor: pointer; margin-bottom: 24px;
    transition: all 0.15s;
    box-shadow: var(--shadow-sm);
  }}
  .cta-voltar:hover {{
    background: var(--gold-bg); color: var(--gold);
    border-color: var(--gold); transform: translateX(-3px);
  }}
  .ac-btn {{
    background: var(--surface); border: 1px solid var(--line);
    border-radius: 6px; padding: 6px 14px;
    font-size: 11px; font-weight: 600; color: var(--ink-soft);
    cursor: pointer; font-family: inherit;
    transition: all 0.15s;
  }}
  .ac-btn:hover {{ background: var(--gold-bg); color: var(--gold); border-color: var(--gold); }}

  @media (max-width: 1100px) {{
    .fases-kanban {{ grid-template-columns: 1fr; }}
    .ciclo-grid {{ grid-template-columns: 1fr; }}
    .obra-summary {{ grid-template-columns: 90px 1fr 70px 90px 30px; gap: 10px; }}
    .sum-fase {{ display: none; }}
    .sum-stats {{ display: none; }}
    .sum-badges {{ display: none; }}
  }}
  @media (max-width: 800px) {{
    main {{ padding: 20px 16px; }}
    .obra-detail {{ padding: 16px 14px; }}
  }}
</style>
</head>
<body>

<header class="top">
  <div>
    <div class="top-title">Timelines · {n_total} obras<small>{subtitulo_header}</small></div>
  </div>
  <button class="top-action" id="btn-atualizar" onclick="copiarComandoAtualizar()" title="Copia comando pro terminal · roda massa + regera HTML">↻ Atualizar agora</button>
  <div class="top-stamp">{gerado_em}</div>
</header>

<main>

  <!-- ========== TELA 1 · VISÃO GERAL ========== -->
  <section id="tela-resumo" class="tela">

    {render_narrativa_unificada(perfis_fluxo, compilacao_prob, n_total, n_marcos_total, len(com_marcos), len(sem_marcos), cobertura_regex, n_novas, n_retorno, n_pre_contrato, n_incerta)}

    <button class="cta-tela" onclick="mostrarTela('tela-obras')">
      <span class="cta-label">Ver obras detalhadas</span>
      <span class="cta-meta">{len(com_marcos)} timelines · {n_marcos_total} marcos</span>
      <span class="cta-arrow">→</span>
    </button>

    <details class="secao-colapsavel">
      <summary class="section-title" style="cursor:pointer;user-select:none">Detalhamento técnico · Perfis, transições e inversões</summary>
      <div class="analise-cross">{render_perfis_fluxo(perfis_fluxo)}</div>
    </details>

    <details class="secao-colapsavel">
      <summary class="section-title" style="cursor:pointer;user-select:none">Análise cross-obras</summary>
      <div class="analise-cross">{render_analise_cross(analise_cross, taxonomia)}</div>
    </details>

    <details class="secao-colapsavel">
      <summary class="section-title" style="cursor:pointer;user-select:none">Categorias de marco</summary>
      <div class="legenda">{legenda_html}</div>
    </details>

  </section>

  <!-- ========== TELA 2 · OBRAS DETALHADAS ========== -->
  <section id="tela-obras" class="tela" style="display:none">

    <button class="cta-voltar" onclick="mostrarTela('tela-resumo')">← Voltar ao resumo</button>

    <h2 class="bloco">Obras com timeline detectada</h2>
    <div class="bloco-sub">Clique numa obra para expandir. A barra de fluxo mostra as 8 etapas esperadas:
      <span style="color:#3d8a5a;font-weight:700">●</span> completou
      <span style="color:#c45a5a;font-weight:700">✕</span> pulou
      <span style="color:var(--ink-faint)">○</span> pendente
      · Dias entre etapas em destaque.
    </div>

    <div class="filtros-wrap">
      <input type="text" id="busca-obras" class="busca-input" placeholder="🔎 Filtrar por cliente, status ou fase..." oninput="aplicarFiltros()">
      <div class="acordeon-controles">
        <button class="ac-btn" onclick="document.querySelectorAll('.obra-card:not(.filtrada)').forEach(d=>d.open=true)">Expandir visíveis</button>
        <button class="ac-btn" onclick="document.querySelectorAll('.obra-card').forEach(d=>d.open=false)">Colapsar todos</button>
        <button class="ac-btn" onclick="limparFiltros()">Limpar filtros</button>
      </div>
    </div>

    <div class="natureza-filtro">
      <div class="nat-label">Origem da obra</div>
      <button class="nat-btn nat-todas nat-ativa" onclick="filtrarNatureza(this, 'todas')">Todas <b>{n_total}</b></button>
      <button class="nat-btn nat-nova" onclick="filtrarNatureza(this, 'nova')">Novas (do zero) <b>{n_novas}</b></button>
      <button class="nat-btn nat-retro" onclick="filtrarNatureza(this, 'retorno')">Retornos <b>{n_retorno}</b></button>
      <button class="nat-btn nat-incerta" onclick="filtrarNatureza(this, 'incerta')">Incertas <b>{n_incerta}</b></button>
      <button class="nat-btn nat-precontrato" onclick="filtrarNatureza(this, 'pre_contrato')">Pré-contrato <b>{n_pre_contrato}</b></button>
    </div>

    <div class="cat-filtros">
      <div class="cat-filtros-titulo">Filtrar por categoria · clique para ativar/desativar</div>
      <div class="cat-grupo">
        <span class="cat-grupo-label">⏱ Paralisação</span>
        <button class="cat-chip cat-critica" data-cat="obra_zumbi" onclick="toggleCat(this)">🚨 Obra zumbi (180+d) <b>{cat_counts.get("obra_zumbi", 0)}</b></button>
        <button class="cat-chip cat-alta" data-cat="obra_parada" onclick="toggleCat(this)">🚩 Obra parada (90-179d) <b>{cat_counts.get("obra_parada", 0)}</b></button>
        <button class="cat-chip cat-media" data-cat="pausa_preocupante" onclick="toggleCat(this)">⚠ Pausa preocupante (60-89d) <b>{cat_counts.get("pausa_preocupante", 0)}</b></button>
        <button class="cat-chip cat-info" data-cat="pausa_normal" onclick="toggleCat(this)">ℹ Pausa normal (45-59d) <b>{cat_counts.get("pausa_normal", 0)}</b></button>
      </div>
      <div class="cat-grupo">
        <span class="cat-grupo-label">🔧 Fricção / problemas</span>
        <button class="cat-chip cat-alta" data-cat="finalizacao_sem_aprovacao" onclick="toggleCat(this)">Finalizado sem aprovação <b>{cat_counts.get("finalizacao_sem_aprovacao", 0)}</b></button>
        <button class="cat-chip cat-alta" data-cat="retrabalho_relampago" onclick="toggleCat(this)">Retrabalho relâmpago <b>{cat_counts.get("retrabalho_relampago", 0)}</b></button>
        <button class="cat-chip cat-alta" data-cat="retrabalho_ativo" onclick="toggleCat(this)">Retrabalho ativo <b>{cat_counts.get("retrabalho_ativo", 0)}</b></button>
        <button class="cat-chip cat-alta" data-cat="postergacao_cumulativa" onclick="toggleCat(this)">Postergação cumulativa <b>{cat_counts.get("postergacao_cumulativa", 0)}</b></button>
        <button class="cat-chip cat-media" data-cat="escopo_instavel" onclick="toggleCat(this)">Escopo instável <b>{cat_counts.get("escopo_instavel", 0)}</b></button>
        <button class="cat-chip cat-media" data-cat="cobranca_recorrente" onclick="toggleCat(this)">Cobrança recorrente <b>{cat_counts.get("cobranca_recorrente", 0)}</b></button>
        <button class="cat-chip cat-alta" data-cat="interrupcao_recorrente" onclick="toggleCat(this)">Falta de material <b>{cat_counts.get("interrupcao_recorrente", 0)}</b></button>
        <button class="cat-chip cat-media" data-cat="eventos_externos" onclick="toggleCat(this)">Eventos externos (fora alçada) <b>{cat_counts.get("eventos_externos", 0)}</b></button>
      </div>
      <div class="cat-grupo">
        <span class="cat-grupo-label">📌 Status do Painel</span>
        <button class="cat-chip cat-status" data-cat="status_em_execucao" onclick="toggleCat(this)">Em execução</button>
        <button class="cat-chip cat-status" data-cat="status_planejamento" onclick="toggleCat(this)">Planejamento</button>
        <button class="cat-chip cat-status" data-cat="status_aguardando_execucao" onclick="toggleCat(this)">Aguardando execução</button>
        <button class="cat-chip cat-status" data-cat="status_reparo" onclick="toggleCat(this)">Reparo</button>
        <button class="cat-chip cat-status" data-cat="status_pausado" onclick="toggleCat(this)">Pausado</button>
        <button class="cat-chip cat-status" data-cat="status_marcas_rolo_cera" onclick="toggleCat(this)">Marcas rolo/cera</button>
      </div>
      <div class="cat-grupo">
        <span class="cat-grupo-label">Perfil de fluxo</span>
        {"".join(f'<button class="cat-chip cat-perfil-{p}" data-cat="perfil_{p}" onclick="toggleCat(this)">{p} {PERFIL_LABELS[p]} <b>{cat_counts.get(f"perfil_{p}", 0)}</b></button>' for p in ("B","C","D","E","F") if cat_counts.get(f"perfil_{p}", 0) > 0)}
      </div>
      <div class="cat-grupo">
        <span class="cat-grupo-label">Outros</span>
        <button class="cat-chip cat-destrinchada" data-cat="destrinchada" onclick="toggleCat(this)">Destrinchadas (calibracao) <b>{cat_counts.get("destrinchada", 0)}</b></button>
      </div>
    </div>

    <div class="resultado-filtros" id="resultado-filtros"></div>

    <h3 class="sub-bloco">🔬 Bloco 1 · Obras destrinchadas (calibração de vocabulário) · {len(destrinchadas)} obras</h3>
    <div class="sub-bloco-info">P2B · SILVANA · PALLOMA · GINACERCHI · DONA CORINA — usadas pra calibrar marcos e vocabulário</div>
    <div class="bloco-obras">{cards_destrinchadas_html}</div>

    <h3 class="sub-bloco">📋 Bloco 2 · Obras ainda não lidas · {len(ainda_nao)} obras</h3>
    <div class="sub-bloco-info">Processadas pelo método mas não destrinchadas manualmente · cobertura via vocabulário calibrado</div>
    <div class="bloco-obras">{cards_ainda_nao_html}</div>

    <h2 class="bloco">Obras sem marcos · gap de coverage do Painel</h2>
    <div class="bloco-sub">Painel marca como ativas mas grupo Telegram está vazio · não é falha do método, é dado faltante na fonte</div>
    <table class="obras-vazias">
      <thead><tr><th>Cliente</th><th>Mix</th><th>Status</th><th>Fase</th><th>Msgs</th><th>Exec</th></tr></thead>
      <tbody>{sem_rows}</tbody>
    </table>

  </section>

</main>

<script>
  function mostrarTela(id) {{
    document.querySelectorAll('.tela').forEach(t => t.style.display = 'none');
    document.getElementById(id).style.display = 'block';
    window.scrollTo({{top: 0, behavior: 'smooth'}});
  }}

  // Filtros ativos (multi-categoria + busca textual + natureza)
  const catsAtivas = new Set();
  let naturezaAtiva = 'todas';

  function filtrarNatureza(btn, tipo) {{
    naturezaAtiva = tipo;
    document.querySelectorAll('.nat-btn').forEach(b => b.classList.remove('nat-ativa'));
    btn.classList.add('nat-ativa');
    aplicarFiltros();
  }}

  function toggleCat(btn) {{
    const cat = btn.getAttribute('data-cat');
    if (catsAtivas.has(cat)) {{
      catsAtivas.delete(cat);
      btn.classList.remove('ativa');
    }} else {{
      catsAtivas.add(cat);
      btn.classList.add('ativa');
    }}
    aplicarFiltros();
  }}

  function limparFiltros() {{
    catsAtivas.clear();
    naturezaAtiva = 'todas';
    document.querySelectorAll('.cat-chip.ativa').forEach(b => b.classList.remove('ativa'));
    document.querySelectorAll('.nat-btn').forEach(b => b.classList.remove('nat-ativa'));
    document.querySelector('.nat-todas').classList.add('nat-ativa');
    document.getElementById('busca-obras').value = '';
    aplicarFiltros();
  }}

  function aplicarFiltros() {{
    const termo = (document.getElementById('busca-obras').value || '').toLowerCase().trim();
    let total = 0;
    let visiveis = 0;
    let blocosVisiveis = {{ destrinchadas: 0, ainda_nao: 0 }};

    document.querySelectorAll('.obra-card').forEach(card => {{
      total++;
      const busca = card.getAttribute('data-busca') || '';
      const cats = (card.getAttribute('data-categorias') || '').split(' ');
      const matchBusca = !termo || busca.includes(termo);
      const matchCats = catsAtivas.size === 0 || [...catsAtivas].every(c => cats.includes(c));
      const matchNat = naturezaAtiva === 'todas' || cats.includes('origem_' + naturezaAtiva);
      const match = matchBusca && matchCats && matchNat;
      if (match) {{
        card.classList.remove('filtrada');
        card.style.display = '';
        visiveis++;
        if (card.classList.contains('destrinchada')) blocosVisiveis.destrinchadas++;
        else blocosVisiveis.ainda_nao++;
      }} else {{
        card.classList.add('filtrada');
        card.style.display = 'none';
      }}
    }});

    const res = document.getElementById('resultado-filtros');
    const numFiltros = catsAtivas.size + (termo ? 1 : 0) + (naturezaAtiva !== 'todas' ? 1 : 0);
    const natLabel = naturezaAtiva === 'nova' ? ' · mostrando novas (do zero)' : (naturezaAtiva === 'retorno' ? ' · mostrando retornos' : (naturezaAtiva === 'incerta' ? ' · mostrando incertas' : (naturezaAtiva === 'pre_contrato' ? ' · mostrando pré-contrato' : '')));
    if (numFiltros > 0) {{
      res.innerHTML = `<strong>${{visiveis}}</strong> de ${{total}} obras visíveis · ${{numFiltros}} filtro${{numFiltros>1?'s':''}} ativo${{numFiltros>1?'s':''}}${{natLabel}}`;
      res.style.display = 'block';
    }} else {{
      res.style.display = 'none';
    }}
  }}

  function copiarComandoAtualizar() {{
    const cmd = 'cd C:\\\\Users\\\\vitor\\\\Monofloor_Files\\\\analise\\\\lab-hermeneuta && python agente\\\\timeline_10obras.py --massa && python agente\\\\gerar_html_timelines.py';
    const btn = document.getElementById('btn-atualizar');
    const txtOriginal = btn.textContent;
    navigator.clipboard.writeText(cmd).then(() => {{
      btn.textContent = '✓ Comando copiado · cole no terminal';
      btn.classList.add('copiado');
      setTimeout(() => {{ btn.textContent = txtOriginal; btn.classList.remove('copiado'); }}, 4000);
    }}).catch(() => {{
      btn.textContent = '⚠ Erro · copie manualmente';
      setTimeout(() => {{ btn.textContent = txtOriginal; }}, 3000);
    }});
  }}
</script>

</body>
</html>
"""

    HTML_PATH.write_text(html_out, encoding="utf-8")
    print(f"[OK] {HTML_PATH}")
    print(f"     · {n_total} obras · {n_marcos_total} marcos · {len(com_marcos)} com timeline · {len(sem_marcos)} sem msgs")


if __name__ == "__main__":
    main()
