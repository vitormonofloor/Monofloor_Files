#!/usr/bin/env bash
# ATENA — Auditor Estratégico · Varredura diária da Central de Qualidade
# Executa 5 análises heurísticas (UX, Insights, Lacunas, Bugs, Oportunidades)
# Gera JSONs em analise/dados/atena/YYYY-MM-DD-{olho}.json + index.json

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
DADOS="$DIR/dados"
ATENA="$DADOS/atena"
DASHBOARD="$DIR/dashboard.html"
PAINEL="$DADOS/painel-temporal.json"
HIST="$DADOS/backlog-historico.json"
mkdir -p "$ATENA"

TODAY=$(TZ=America/Sao_Paulo date +%Y-%m-%d)
NOW_UTC=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "=== ATENA — Varredura $TODAY ==="
echo "  dashboard: $(wc -c < "$DASHBOARD") bytes"
echo "  painel-temporal: $(wc -c < "$PAINEL") bytes"

# ─────────────────────────────────────────
# Usa python3 inline para todas as análises
# ─────────────────────────────────────────
python3 - "$DASHBOARD" "$PAINEL" "$HIST" "$ATENA" "$TODAY" "$NOW_UTC" "$DADOS" <<'PYEOF'
import json, os, sys, re, glob
from collections import Counter, defaultdict
from datetime import datetime

DASHBOARD_PATH = sys.argv[1]
PAINEL_PATH    = sys.argv[2]
HIST_PATH      = sys.argv[3]
ATENA_DIR      = sys.argv[4]
TODAY           = sys.argv[5]
NOW_UTC         = sys.argv[6]
DADOS_DIR       = sys.argv[7]

# ============================================================
# CARREGAR DADOS
# ============================================================
with open(DASHBOARD_PATH, encoding="utf-8") as f:
    dashboard_html = f.read()

with open(PAINEL_PATH, encoding="utf-8-sig") as f:
    painel = json.load(f)

hist = []
if os.path.exists(HIST_PATH):
    with open(HIST_PATH, encoding="utf-8") as f:
        hist = json.load(f)

cruz_files = glob.glob(os.path.join(DADOS_DIR, "cruz-*.json"))
cruz_data = {}
for cf in cruz_files:
    nome = os.path.basename(cf).replace("cruz-", "").replace(".json", "")
    try:
        with open(cf, encoding="utf-8") as f:
            cruz_data[nome] = json.load(f)
    except:
        pass

INATIVAS = {"finalizado", "concluido", "cancelado"}
ativas = [o for o in painel if o.get("status") not in INATIVAS]

# ============================================================
# OLHO 1: UX — Análise do HTML do dashboard
# ============================================================
def olho_ux():
    achados = []
    html = dashboard_html

    # 1. Contar TODOs/FIXMEs
    todos = re.findall(r'(?:TODO|FIXME|HACK|XXX)[:\s].*', html, re.IGNORECASE)
    if todos:
        achados.append({
            "severidade": "baixa",
            "titulo": f"{len(todos)} marcadores TODO/FIXME encontrados no HTML",
            "descricao": f"Existem {len(todos)} comentarios de desenvolvimento pendentes no dashboard.html",
            "evidencia": "; ".join(t.strip()[:80] for t in todos[:5])
        })

    # 2. IDs duplicados
    ids_found = re.findall(r'\bid=["\']([^"\']+)["\']', html)
    id_counts = Counter(ids_found)
    dupes = {k: v for k, v in id_counts.items() if v > 1}
    if dupes:
        achados.append({
            "severidade": "media",
            "titulo": f"{len(dupes)} IDs duplicados no HTML",
            "descricao": "IDs HTML devem ser unicos. Duplicatas podem causar bugs no JS.",
            "evidencia": ", ".join(f"{k} ({v}x)" for k, v in sorted(dupes.items(), key=lambda x: -x[1])[:10])
        })

    # 3. Imagens sem alt
    imgs = re.findall(r'<img\b[^>]*>', html)
    imgs_no_alt = [i for i in imgs if 'alt=' not in i.lower()]
    if imgs_no_alt:
        achados.append({
            "severidade": "baixa",
            "titulo": f"{len(imgs_no_alt)} imagens sem atributo alt",
            "descricao": "Imagens sem alt prejudicam acessibilidade.",
            "evidencia": imgs_no_alt[0][:120] if imgs_no_alt else ""
        })

    # 4. Elementos interativos sem aria-label
    buttons = re.findall(r'<button\b[^>]*>.*?</button>', html, re.DOTALL)
    btns_no_aria = [b for b in buttons if 'aria-label' not in b and 'aria-labelledby' not in b]
    if btns_no_aria:
        achados.append({
            "severidade": "baixa",
            "titulo": f"{len(btns_no_aria)} botoes sem aria-label",
            "descricao": "Botoes interativos devem ter aria-label para acessibilidade.",
            "evidencia": re.sub(r'\s+', ' ', btns_no_aria[0][:120]) if btns_no_aria else ""
        })

    # 5. Inline styles (indicador de codigo nao-modular)
    inline_styles = re.findall(r'style="[^"]{80,}"', html)
    if inline_styles:
        achados.append({
            "severidade": "baixa",
            "titulo": f"{len(inline_styles)} estilos inline longos (>80 chars)",
            "descricao": "Estilos inline extensos dificultam manutencao. Considerar mover para CSS.",
            "evidencia": inline_styles[0][:120] + "..." if inline_styles else ""
        })

    # 6. Tamanho do arquivo
    size_kb = len(html.encode("utf-8")) / 1024
    if size_kb > 250:
        sev = "alta" if size_kb > 500 else "media"
        achados.append({
            "severidade": sev,
            "titulo": f"Dashboard com {size_kb:.0f} KB",
            "descricao": f"Arquivo monolitico com {size_kb:.0f} KB. Paginas acima de 250 KB impactam tempo de carregamento.",
            "evidencia": f"dashboard.html = {size_kb:.1f} KB, {len(html.splitlines())} linhas"
        })

    # 7. Scripts inline vs externos
    scripts_inline = re.findall(r'<script(?:\s[^>]*)?>[^<]{100,}', html)
    achados.append({
        "severidade": "baixa" if len(scripts_inline) <= 3 else "media",
        "titulo": f"{len(scripts_inline)} blocos <script> inline com >100 chars",
        "descricao": "Scripts inline extensos dificultam cache e manutencao.",
        "evidencia": f"{len(scripts_inline)} blocos encontrados"
    })

    # 8. Console.log residuais
    console_logs = re.findall(r'console\.\w+\s*\(', html)
    if console_logs:
        achados.append({
            "severidade": "baixa",
            "titulo": f"{len(console_logs)} chamadas console.* no codigo",
            "descricao": "Console.log residuais devem ser removidos em producao.",
            "evidencia": f"{len(console_logs)} ocorrencias"
        })

    metricas = {
        "tamanho_kb": round(size_kb, 1),
        "linhas": len(html.splitlines()),
        "ids_unicos": len(set(ids_found)),
        "ids_duplicados": len(dupes),
        "scripts_inline": len(scripts_inline),
        "todos_fixme": len(todos),
        "imagens_total": len(imgs),
        "imagens_sem_alt": len(imgs_no_alt),
        "console_logs": len(console_logs)
    }

    return achados, metricas

# ============================================================
# OLHO 2: INSIGHTS — Comparar snapshots, detectar mudancas
# ============================================================
def olho_insights():
    achados = []

    # Dados atuais
    n_ativas = len(ativas)
    n_total = len(painel)

    # Distribuicao por fase
    fases = Counter(o.get("faseAtual", "?") for o in ativas)

    # Distribuicao por consultor
    consultores = Counter()
    for o in ativas:
        c = (o.get("consultorNome") or "").strip()
        if c and c != "[]":
            consultores[c] += 1

    # Concentracao: top 3 consultores
    top3 = consultores.most_common(3)
    total_top3 = sum(v for _, v in top3)
    if n_ativas > 0 and total_top3 / n_ativas > 0.4:
        achados.append({
            "severidade": "media",
            "titulo": f"Concentracao: {total_top3} obras ({total_top3*100//n_ativas}%) em 3 consultores",
            "descricao": f"Os 3 consultores com mais obras concentram {total_top3*100//n_ativas}% do total ativo.",
            "evidencia": ", ".join(f"{n} ({v})" for n, v in top3)
        })

    # Idade media vs mediana
    idades = sorted(o.get("idade_dias") or 0 for o in ativas if o.get("idade_dias"))
    if idades:
        media = sum(idades) / len(idades)
        mediana = idades[len(idades)//2]
        p90 = idades[int(len(idades)*0.9)]

        achados.append({
            "severidade": "media" if media > 150 else "baixa",
            "titulo": f"Idade media das obras ativas: {media:.0f} dias (mediana {mediana}d, P90 {p90}d)",
            "descricao": f"De {len(idades)} obras com data, a media eh {media:.0f}d e a mediana {mediana}d. P90 = {p90}d.",
            "evidencia": f"media={media:.0f}d, mediana={mediana}d, P90={p90}d, max={idades[-1]}d"
        })

    # Fases com mais obras paradas
    fases_top = fases.most_common(5)
    achados.append({
        "severidade": "baixa",
        "titulo": f"Top 5 fases com mais obras ativas",
        "descricao": "Distribuicao das obras ativas por fase atual.",
        "evidencia": "; ".join(f"{f}: {n}" for f, n in fases_top)
    })

    # Cruzamentos: tamanho relativo
    if cruz_data:
        cruz_sizes = {k: len(json.dumps(v)) for k, v in cruz_data.items()}
        biggest = max(cruz_sizes, key=cruz_sizes.get)
        achados.append({
            "severidade": "baixa",
            "titulo": f"{len(cruz_data)} cruzamentos ativos, maior: {biggest}",
            "descricao": "Mapa dos cruzamentos (cruz-*.json) disponíveis.",
            "evidencia": "; ".join(f"{k}: {v//1024}KB" for k, v in sorted(cruz_sizes.items(), key=lambda x: -x[1])[:5])
        })

    # Comparar com historico (backlog-historico.json)
    if len(hist) >= 2:
        prev = hist[-2] if hist[-1].get("date") == TODAY else hist[-1]
        curr = hist[-1]
        pi = prev.get("indices", {})
        ci = curr.get("indices", {})

        for idx_name in ["zumbi", "orfas", "conflitos", "lideres_ocultos", "lote_vt"]:
            p_total = pi.get(idx_name, {}).get("total", 0)
            c_total = ci.get(idx_name, {}).get("total", 0)
            delta = c_total - p_total
            if delta != 0:
                direcao = "subiu" if delta > 0 else "caiu"
                sev = "media" if abs(delta) >= 3 else "baixa"
                if idx_name == "zumbi" and delta > 0:
                    sev = "alta"
                achados.append({
                    "severidade": sev,
                    "titulo": f"{idx_name} {direcao}: {p_total} -> {c_total} ({'+' if delta>0 else ''}{delta})",
                    "descricao": f"Indice {idx_name} mudou de {p_total} para {c_total} entre {prev.get('date')} e {curr.get('date')}.",
                    "evidencia": f"delta={delta:+d}"
                })

    metricas = {
        "obras_ativas": n_ativas,
        "obras_total": n_total,
        "consultores_distintos": len(consultores),
        "fases_distintas": len(fases),
        "cruzamentos_ativos": len(cruz_data),
        "idade_media": round(sum(idades)/len(idades), 1) if idades else None,
        "idade_mediana": idades[len(idades)//2] if idades else None,
        "idade_p90": idades[int(len(idades)*0.9)] if idades else None
    }

    return achados, metricas

# ============================================================
# OLHO 3: LACUNAS — Campos no painel que nao aparecem no dashboard
# ============================================================
def olho_lacunas():
    achados = []

    # Campos disponiveis no painel-temporal
    if painel:
        campos_painel = set(painel[0].keys())
    else:
        campos_painel = set()

    # Campos referenciados no dashboard HTML (procurar por chave de acesso JS)
    html = dashboard_html
    campos_usados_html = set()
    # Padroes: .campo, ["campo"], get("campo")
    for pat in [r'\.\b([a-zA-Z_][a-zA-Z0-9_]*)\b', r'\["([a-zA-Z_][a-zA-Z0-9_]*)"\]', r"get\(['\"]([a-zA-Z_][a-zA-Z0-9_]*)['\"]"]:
        campos_usados_html.update(re.findall(pat, html))

    # Campos do painel nao usados no dashboard
    nao_usados = campos_painel - campos_usados_html
    # Filtrar campos meta (id, ativa) que podem nao aparecer literalmente
    nao_usados_relevantes = {c for c in nao_usados if c not in {"ativa"}}

    if nao_usados_relevantes:
        achados.append({
            "severidade": "media" if len(nao_usados_relevantes) > 3 else "baixa",
            "titulo": f"{len(nao_usados_relevantes)} campos do painel-temporal nao usados no dashboard",
            "descricao": "Campos disponiveis nos dados mas que nao aparecem referenciados no HTML do dashboard.",
            "evidencia": ", ".join(sorted(nao_usados_relevantes))
        })

    # Cruzamentos que existem mas nao sao referenciados no dashboard
    cruz_nomes = set(cruz_data.keys())
    cruz_no_dashboard = set()
    for nome in cruz_nomes:
        if f"cruz-{nome}" in html or nome.replace("-", "_") in html or nome in html:
            cruz_no_dashboard.add(nome)

    cruz_ausentes = cruz_nomes - cruz_no_dashboard
    if cruz_ausentes:
        achados.append({
            "severidade": "media" if len(cruz_ausentes) > 5 else "baixa",
            "titulo": f"{len(cruz_ausentes)} cruzamentos sem referencia no dashboard",
            "descricao": "Cruzamentos (cruz-*.json) que existem nos dados mas nao parecem ser carregados pelo dashboard.",
            "evidencia": ", ".join(sorted(cruz_ausentes))
        })

    # Verificar se backlog-historico eh usado no dashboard
    if "backlog-historico" not in html and "backlog_historico" not in html:
        achados.append({
            "severidade": "baixa",
            "titulo": "backlog-historico.json nao referenciado no dashboard",
            "descricao": "O historico de backlog existe nos dados mas nao eh carregado pelo dashboard.",
            "evidencia": "arquivo existe com dados de " + str(len(hist)) + " dias"
        })

    # Campos usados no dashboard que nao existem no painel
    campos_possiveis_js = {"clienteNome", "projetoCidade", "status", "faseAtual", "consultorNome",
                           "projetoMetragem", "pipefyCardId", "data_radar", "idade_dias", "id",
                           "data_radar_fonte", "pipefy_created_at", "pipefyCreatedAt_api", "ativa"}
    campos_desconhecidos = campos_usados_html.intersection(campos_possiveis_js) - campos_painel
    if campos_desconhecidos:
        achados.append({
            "severidade": "media",
            "titulo": f"{len(campos_desconhecidos)} campos usados no dashboard que nao existem no painel",
            "descricao": "O dashboard referencia campos que nao existem nos dados atuais do painel-temporal.",
            "evidencia": ", ".join(sorted(campos_desconhecidos))
        })

    metricas = {
        "campos_painel": len(campos_painel),
        "campos_referenciados_html": len(campos_usados_html),
        "campos_nao_usados": len(nao_usados_relevantes),
        "cruzamentos_total": len(cruz_nomes),
        "cruzamentos_no_dashboard": len(cruz_no_dashboard),
        "cruzamentos_ausentes": len(cruz_ausentes)
    }

    return achados, metricas

# ============================================================
# OLHO 4: BUGS — Coerencia numerica, datas estranhas, hardcoded
# ============================================================
def olho_bugs():
    achados = []

    # 1. Datas estranhas no painel (ano <2020 ou >2030)
    datas_estranhas = []
    for o in painel:
        dr = o.get("data_radar")
        if dr:
            try:
                ano = int(dr[:4])
                if ano < 2020 or ano > 2030:
                    datas_estranhas.append({
                        "id": o["id"][:8],
                        "cliente": o.get("clienteNome", "?"),
                        "data_radar": dr,
                        "ano": ano
                    })
            except:
                pass

    if datas_estranhas:
        achados.append({
            "severidade": "alta",
            "titulo": f"{len(datas_estranhas)} obras com data_radar fora do range 2020-2030",
            "descricao": "Datas de radar com ano improvavel, possivel erro de cadastro.",
            "evidencia": "; ".join(f"{d['id']} ({d['cliente'][:30]}): {d['data_radar']}" for d in datas_estranhas[:5])
        })

    # 2. Obras ativas com idade negativa
    idades_neg = [o for o in ativas if (o.get("idade_dias") or 0) < 0]
    if idades_neg:
        achados.append({
            "severidade": "media",
            "titulo": f"{len(idades_neg)} obras ativas com idade negativa",
            "descricao": "Idade negativa indica data_radar no futuro, possivel erro.",
            "evidencia": "; ".join(f"{o['id'][:8]}: {o.get('idade_dias')}d" for o in idades_neg[:5])
        })

    # 3. Obras ativas com idade > 500 dias (anormal)
    idades_extremas = [o for o in ativas if (o.get("idade_dias") or 0) > 500]
    if idades_extremas:
        achados.append({
            "severidade": "alta",
            "titulo": f"{len(idades_extremas)} obras ativas com idade > 500 dias",
            "descricao": "Obras com mais de 500 dias ativas sao anomalas. Verificar se deviam estar finalizadas.",
            "evidencia": "; ".join(f"{o['id'][:8]} ({o.get('clienteNome','?')[:25]}): {o.get('idade_dias')}d" for o in sorted(idades_extremas, key=lambda x: -(x.get('idade_dias') or 0))[:5])
        })

    # 4. Zumbi check: status ativo mas fase CLIENTE FINALIZADO
    zumbis = [o for o in ativas if (o.get("faseAtual") or "").strip().upper() == "CLIENTE FINALIZADO"]
    if zumbis:
        achados.append({
            "severidade": "alta",
            "titulo": f"{len(zumbis)} obras zumbi (ativas + CLIENTE FINALIZADO)",
            "descricao": "Obras com status ativo mas fase terminal. Deviam estar finalizadas.",
            "evidencia": "; ".join(f"{o['id'][:8]} ({o.get('clienteNome','?')[:25]})" for o in zumbis[:5])
        })

    # 5. Orfas: ativas sem consultor
    orfas = [o for o in ativas if not (o.get("consultorNome") or "").strip() or (o.get("consultorNome") or "").strip() == "[]"]
    if orfas:
        achados.append({
            "severidade": "media",
            "titulo": f"{len(orfas)} obras orfas (sem consultor atribuido)",
            "descricao": "Obras ativas sem consultor responsavel.",
            "evidencia": "; ".join(f"{o['id'][:8]}" for o in orfas[:8])
        })

    # 6. Strings hardcoded suspeitas no HTML
    html = dashboard_html
    hardcoded_patterns = [
        (r'(?:2026-04-\d\d)', "datas fixas 2026-04-xx"),
        (r'(?:de 1[\.,]028|de 228|de 208)', "contagens hardcoded"),
    ]
    for pat, desc in hardcoded_patterns:
        matches = re.findall(pat, html)
        if matches:
            uniq = set(matches)
            achados.append({
                "severidade": "media",
                "titulo": f"Strings hardcoded no HTML: {desc}",
                "descricao": f"Encontrados {len(matches)} ocorrencias de {desc} fixas no HTML. Deviam ser dinamicas.",
                "evidencia": ", ".join(sorted(uniq)[:8])
            })

    # 7. Coerencia: obras com status finalizado mas sem faseAtual coerente
    finalizados_sem_fase = [o for o in painel if o.get("status") in INATIVAS and not o.get("faseAtual")]
    if finalizados_sem_fase:
        achados.append({
            "severidade": "baixa",
            "titulo": f"{len(finalizados_sem_fase)} obras finalizadas sem faseAtual",
            "descricao": "Obras com status inativo mas campo faseAtual vazio.",
            "evidencia": f"{len(finalizados_sem_fase)} registros"
        })

    # Saude: calcular indice
    n_ativas = len(ativas)
    n_criticos = len(zumbis) + len(orfas) + len(idades_extremas)
    saude = max(0, min(100, round(100 - (n_criticos / max(n_ativas, 1)) * 100)))

    metricas = {
        "indice_saude": saude,
        "obras_ativas": n_ativas,
        "zumbis": len(zumbis),
        "orfas": len(orfas),
        "idades_extremas_500": len(idades_extremas),
        "datas_estranhas": len(datas_estranhas),
        "idades_negativas": len(idades_neg),
        "finalizados_sem_fase": len(finalizados_sem_fase)
    }

    return achados, metricas

# ============================================================
# OLHO 5: OPORTUNIDADES — Correlacoes e sugestoes
# ============================================================
def olho_oportunidades():
    achados = []

    # 1. Cruzamentos possiveis que nao existem ainda
    cruz_existentes = set(cruz_data.keys())

    # Dimensoes nos dados
    dimensoes = {"idade", "fase", "consultor", "geo", "metragem", "tipo", "status"}
    # Cruzamentos possiveis = pares de dimensoes
    pares_possiveis = []
    dim_list = sorted(dimensoes)
    for i, d1 in enumerate(dim_list):
        for d2 in dim_list[i+1:]:
            par = f"{d1}-{d2}"
            # Verificar se algum cruzamento existente cobre esse par
            coberto = any(d1 in c and d2 in c for c in cruz_existentes)
            if not coberto:
                pares_possiveis.append(par)

    if pares_possiveis:
        achados.append({
            "severidade": "baixa",
            "titulo": f"{len(pares_possiveis)} cruzamentos bidimensionais nao explorados",
            "descricao": "Combinacoes de dimensoes que poderiam revelar padroes novos.",
            "evidencia": ", ".join(pares_possiveis[:8])
        })

    # 2. Consultores com mais obras velhas (>180d) — oportunidade de redistribuicao
    consultor_velhas = defaultdict(list)
    for o in ativas:
        c = (o.get("consultorNome") or "").strip()
        idade = o.get("idade_dias") or 0
        if c and c != "[]" and idade > 180:
            consultor_velhas[c].append(idade)

    top_velhas = sorted(consultor_velhas.items(), key=lambda x: -len(x[1]))[:3]
    if top_velhas and len(top_velhas[0][1]) >= 3:
        achados.append({
            "severidade": "media",
            "titulo": "Consultores com acumulo de obras antigas (>180d)",
            "descricao": "Oportunidade de redistribuicao ou priorizacao.",
            "evidencia": "; ".join(f"{c}: {len(v)} obras (media {sum(v)//len(v)}d)" for c, v in top_velhas)
        })

    # 3. Fases gargalo — fases com mais obras e maior idade media
    fase_stats = defaultdict(lambda: {"n": 0, "idades": []})
    for o in ativas:
        f = o.get("faseAtual") or "?"
        fase_stats[f]["n"] += 1
        if o.get("idade_dias"):
            fase_stats[f]["idades"].append(o["idade_dias"])

    gargalos = []
    for fase, st in fase_stats.items():
        if st["n"] >= 5 and st["idades"]:
            media = sum(st["idades"]) / len(st["idades"])
            if media > 150:
                gargalos.append((fase, st["n"], media))

    gargalos.sort(key=lambda x: -x[2])
    if gargalos:
        achados.append({
            "severidade": "alta" if len(gargalos) >= 3 else "media",
            "titulo": f"{len(gargalos)} fases com gargalo (>=5 obras + media >150d)",
            "descricao": "Fases onde obras acumulam com idade elevada. Candidatas a intervencao.",
            "evidencia": "; ".join(f"{f}: {n} obras, media {m:.0f}d" for f, n, m in gargalos[:5])
        })

    # 4. Obras sem data_radar — oportunidade de cadastro
    sem_radar = [o for o in ativas if not o.get("data_radar")]
    if sem_radar:
        achados.append({
            "severidade": "media",
            "titulo": f"{len(sem_radar)} obras ativas sem data_radar",
            "descricao": "Obras sem data de entrada no radar. Sem data, nao eh possivel calcular SLAs.",
            "evidencia": "; ".join(f"{o['id'][:8]}" for o in sem_radar[:8])
        })

    # 5. Distribuicao regional — cidades com mais obras
    cidades = Counter()
    for o in ativas:
        c = (o.get("projetoCidade") or "").strip()
        if c:
            cidades[c] += 1

    top_cidades = cidades.most_common(5)
    achados.append({
        "severidade": "baixa",
        "titulo": f"Concentracao regional: {len(cidades)} cidades",
        "descricao": "Distribuicao geografica das obras ativas.",
        "evidencia": "; ".join(f"{c}: {n}" for c, n in top_cidades)
    })

    metricas = {
        "cruzamentos_nao_explorados": len(pares_possiveis),
        "fases_gargalo": len(gargalos),
        "obras_sem_radar": len(sem_radar),
        "cidades_distintas": len(cidades),
        "consultores_com_acumulo_180d": len([c for c, v in consultor_velhas.items() if len(v) >= 3])
    }

    return achados, metricas

# ============================================================
# EXECUTAR TODOS OS OLHOS
# ============================================================
olhos = {
    "ux":             olho_ux,
    "insights":       olho_insights,
    "lacunas":        olho_lacunas,
    "bugs":           olho_bugs,
    "oportunidades":  olho_oportunidades,
}

resultados = {}
for nome, fn in olhos.items():
    print(f"  [{nome}] executando...")
    try:
        achados, metricas = fn()
        resultado = {
            "olho": nome,
            "executado_em": NOW_UTC,
            "achados": achados,
            "metricas": metricas,
            "comparativo_vs_anterior": None
        }

        # Comparar com varredura anterior do mesmo olho
        prev_file = None
        for f in sorted(glob.glob(os.path.join(ATENA_DIR, f"*-{nome}.json")), reverse=True):
            if os.path.basename(f) != f"{TODAY}-{nome}.json":
                prev_file = f
                break
        if prev_file:
            try:
                with open(prev_file, encoding="utf-8") as pf:
                    prev = json.load(pf)
                prev_n = len(prev.get("achados", []))
                curr_n = len(achados)
                prev_alta = sum(1 for a in prev.get("achados", []) if a.get("severidade") == "alta")
                curr_alta = sum(1 for a in achados if a.get("severidade") == "alta")
                resultado["comparativo_vs_anterior"] = f"achados: {prev_n}->{curr_n} ({curr_n-prev_n:+d}), alta: {prev_alta}->{curr_alta} ({curr_alta-prev_alta:+d})"
            except:
                pass

        resultados[nome] = resultado

        out_path = os.path.join(ATENA_DIR, f"{TODAY}-{nome}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)

        n_alta = sum(1 for a in achados if a.get("severidade") == "alta")
        n_media = sum(1 for a in achados if a.get("severidade") == "media")
        n_baixa = sum(1 for a in achados if a.get("severidade") == "baixa")
        print(f"    {len(achados)} achados ({n_alta} alta, {n_media} media, {n_baixa} baixa)")
    except Exception as e:
        print(f"    ERRO: {e}")
        resultados[nome] = {"olho": nome, "executado_em": NOW_UTC, "achados": [], "metricas": {}, "erro": str(e)}

# ============================================================
# GERAR INDEX.JSON
# ============================================================
total_achados = sum(len(r.get("achados", [])) for r in resultados.values())
total_alta = sum(sum(1 for a in r.get("achados", []) if a.get("severidade") == "alta") for r in resultados.values())
total_media = sum(sum(1 for a in r.get("achados", []) if a.get("severidade") == "media") for r in resultados.values())
total_baixa = sum(sum(1 for a in r.get("achados", []) if a.get("severidade") == "baixa") for r in resultados.values())

# Saude (do olho bugs)
saude = resultados.get("bugs", {}).get("metricas", {}).get("indice_saude", None)

# Listar todas as varreduras existentes
varreduras = []
existing_dates = set()
for f in sorted(glob.glob(os.path.join(ATENA_DIR, "????-??-??-*.json"))):
    bn = os.path.basename(f)
    parts = bn.replace(".json", "").split("-")
    if len(parts) >= 4:
        date = "-".join(parts[:3])
        olho = "-".join(parts[3:])
        existing_dates.add(date)

for d in sorted(existing_dates):
    olhos_dia = []
    for o_name in ["ux", "insights", "lacunas", "bugs", "oportunidades"]:
        fp = os.path.join(ATENA_DIR, f"{d}-{o_name}.json")
        if os.path.exists(fp):
            olhos_dia.append(o_name)
    varreduras.append({"date": d, "olhos": olhos_dia, "completa": len(olhos_dia) == 5})

index = {
    "ultima_varredura": NOW_UTC,
    "proxima_varredura": f"{TODAY}T10:00:00Z",
    "total_achados": total_achados,
    "achados_alta": total_alta,
    "achados_media": total_media,
    "achados_baixa": total_baixa,
    "indice_saude": saude,
    "varreduras": varreduras,
    "sumario_hoje": {
        nome: {
            "achados": len(r.get("achados", [])),
            "alta": sum(1 for a in r.get("achados", []) if a.get("severidade") == "alta"),
            "media": sum(1 for a in r.get("achados", []) if a.get("severidade") == "media"),
            "baixa": sum(1 for a in r.get("achados", []) if a.get("severidade") == "baixa"),
        }
        for nome, r in resultados.items()
    }
}

idx_path = os.path.join(ATENA_DIR, "index.json")
with open(idx_path, "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

print(f"\n=== ATENA completa ===")
print(f"  {total_achados} achados ({total_alta} alta, {total_media} media, {total_baixa} baixa)")
print(f"  indice de saude: {saude}")
print(f"  {len(varreduras)} varredura(s) no historico")
PYEOF

echo "[done] ATENA varredura $TODAY concluida em $NOW_UTC"
