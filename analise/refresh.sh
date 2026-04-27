#!/usr/bin/env bash
# Refresh automático Monofloor — fetch + snapshot + regen dashboard-data
# Roda 1x a cada 30 min via GitHub Actions
# Modo LEVE: atualiza data.json
# Modo PESADO (1ª vez do dia): details + painel-temporal + snapshot + backlog + dashboard-data.json
#
# ROBUSTO: respostas API vão pra ARQUIVOS TEMP, Python lê de arquivo (nunca heredoc com JSON)

API="https://cliente.monofloor.cloud/api"
DIR="$(cd "$(dirname "$0")" && pwd)"
DADOS="$DIR/dados"
SNAPSHOTS="$DADOS/snapshots"
DETAILS="$DADOS/details"
TMP="$DADOS/.tmp"
mkdir -p "$DETAILS" "$SNAPSHOTS" "$TMP"

TODAY=$(TZ=America/Sao_Paulo date +%Y-%m-%d)
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SNAP="$SNAPSHOTS/$TODAY.json"

echo "=== Refresh Monofloor === $NOW"

# ─── 1) LEVE: fetch 5 listas ───
echo "[1] Fetch listas..."
curl -sf --max-time 30 "$API/projects?limit=2000" -o "$TMP/projects.json" || { echo "ERRO: /projects falhou"; exit 1; }
curl -sf --max-time 30 "$API/dashboard"         -o "$TMP/dashboard.json"  || echo "AVISO: /dashboard falhou"
curl -sf --max-time 30 "$API/analise"            -o "$TMP/analise.json"   || echo "AVISO: /analise falhou"
curl -sf --max-time 30 "$API/escalacao-diaria"   -o "$TMP/escalacao.json" || echo "AVISO: /escalacao falhou"
curl -sf --max-time 30 "$API/equipes"            -o "$TMP/equipes.json"   || echo "AVISO: /equipes falhou"

# Validar projects (obrigatório)
python3 -c "import json; json.load(open('$TMP/projects.json'))" 2>/dev/null || { echo "ERRO: projects.json inválido"; exit 1; }

# Montar data.json
python3 -c "
import json, os
TMP = '$TMP'
DIR = '$DIR'
NOW = '$NOW'
p = json.load(open(os.path.join(TMP, 'projects.json')))
d = json.load(open(os.path.join(TMP, 'dashboard.json'))) if os.path.exists(os.path.join(TMP, 'dashboard.json')) else {}
a = json.load(open(os.path.join(TMP, 'analise.json'))) if os.path.exists(os.path.join(TMP, 'analise.json')) else {}
e = json.load(open(os.path.join(TMP, 'escalacao.json'))) if os.path.exists(os.path.join(TMP, 'escalacao.json')) else {}
eq = json.load(open(os.path.join(TMP, 'equipes.json'))) if os.path.exists(os.path.join(TMP, 'equipes.json')) else []
with open(os.path.join(DIR, 'data.json'), 'w') as f:
    json.dump({'projects':p,'dashboard':d,'analise':a,'escalacao':e,'equipes':eq,'fetchedAt':NOW}, f, ensure_ascii=False)
print(f'  data.json OK ({len(p)} projects)')
"

# ─── 2) PESADO? ───
if [ -f "$SNAP" ]; then
  echo "[done] Snapshot do dia já existe. Refresh LEVE concluído."
  rm -rf "$TMP"
  exit 0
fi
echo "[2] Modo PESADO — snapshot do dia não existe"

# ─── 3) Fetch details das ativas ───
echo "[3] Fetch details..."
python3 -c "
import json
p = json.load(open('$TMP/projects.json'))
skip = {'finalizado','concluido','cancelado'}
ids = [x['id'] for x in p if x.get('status') not in skip]
print(f'  {len(ids)} ativas')
with open('$TMP/ids.txt','w') as f:
    f.write('\n'.join(ids))
"

# Download em paralelo (max 10, timeout 15s cada)
cat "$TMP/ids.txt" | xargs -I {} -P 10 bash -c '
  curl -sf --max-time 15 "'"$API"'/projects/$1" -o "'"$DETAILS"'/$1.json" 2>/dev/null || true
' _ {} 2>/dev/null || true

N_DET=$(ls "$DETAILS"/*.json 2>/dev/null | wc -l)
echo "  $N_DET details salvos"

# ─── 4) Snapshot + painel-temporal + backlog + dashboard-data ───
echo "[4] Snapshot + painel-temporal + backlog + dashboard-data..."
curl -sf --max-time 30 "https://raw.githubusercontent.com/vitormonofloor/cargo-assistente/main/pipefy_cards.json" -o "$TMP/pipefy.json" || echo "AVISO: pipefy falhou"

# Exportar paths via ENV para o Python (heredoc com aspas = sem expansão shell)
export DADOS_DIR="$DADOS"
export DETAILS_DIR="$DETAILS"
export TMP_DIR="$TMP"
export TODAY_STR="$TODAY"
export NOW_STR="$NOW"
export SNAP_FILE="$SNAP"
export DIR_STR="$DIR"

python3 << 'PYEOF'
import json, os, sys
from datetime import datetime

DADOS = os.environ["DADOS_DIR"]
DETAILS = os.environ["DETAILS_DIR"]
TMP = os.environ["TMP_DIR"]
TODAY = os.environ["TODAY_STR"]
NOW = os.environ["NOW_STR"]
SNAP = os.environ["SNAP_FILE"]
DIR = os.environ["DIR_STR"]

today = datetime.strptime(TODAY, "%Y-%m-%d").date()

# ──── Pipefy snapshot (lê de arquivo, não de variável) ────
pipefy = {}
pf = os.path.join(TMP, "pipefy.json")
if os.path.exists(pf):
    try:
        for c in json.load(open(pf)):
            if c.get("id"):
                pipefy[str(c["id"])] = c
    except Exception as e:
        print(f"  AVISO: pipefy snapshot inválido ({e}), seguindo sem ele")

# ──── Equipes (lê de arquivo) ────
equipes = []
eq_path = os.path.join(TMP, "equipes.json")
if os.path.exists(eq_path):
    try:
        equipes = json.load(open(eq_path))
    except:
        equipes = []

# Set de IDs cadastrados em /api/equipes
ids_cadastrados = set()
for eq in (equipes or []):
    for m in (eq.get("membros") or []):
        if m.get("id"):
            ids_cadastrados.add(m["id"])
    if eq.get("liderId"):
        ids_cadastrados.add(eq["liderId"])

SKIP = {"finalizado", "concluido", "cancelado"}
FINALIZADO_FASE = "CLIENTE FINALIZADO"
obras = []

for fn in os.listdir(DETAILS):
    if not fn.endswith(".json"):
        continue
    try:
        o = json.load(open(os.path.join(DETAILS, fn)))
    except:
        continue
    pid = o.get("id")
    if not pid:
        continue

    pcid = (o.get("acessoDetalhes") or {}).get("pipefyCardId") or o.get("pipefyCardId")
    pdt = (o.get("acessoDetalhes") or {}).get("pipefyCreatedAt")
    sdt = pipefy.get(str(pcid), {}).get("created_at") if pcid else None

    dr, src = None, "sem_data"
    if sdt:
        dr, src = sdt[:10], "pipefy_snapshot"
    elif pdt:
        dr, src = pdt[:10], "pipefy_api"

    idade = None
    if dr:
        try:
            idade = (today - datetime.strptime(dr, "%Y-%m-%d").date()).days
        except:
            pass

    st = o.get("status")
    obras.append({
        "id": pid, "clienteNome": o.get("clienteNome"), "projetoCidade": o.get("projetoCidade"),
        "status": st, "faseAtual": o.get("faseAtual"), "consultorNome": o.get("consultorNome"),
        "projetoMetragem": o.get("projetoMetragem"), "pipefyCardId": pcid,
        "pipefy_snapshot_created_at": sdt,
        "pipefyCreatedAt_api": pdt,
        "data_radar": dr, "data_radar_fonte": src, "idade_dias": idade,
        "ativa": st not in SKIP
    })

# ──── Salvar painel-temporal ────
with open(os.path.join(DADOS, "painel-temporal.json"), "w") as f:
    json.dump(obras, f, ensure_ascii=False, indent=2)

ativas = [o for o in obras if o["ativa"]]
print(f"  painel-temporal: {len(obras)} obras ({len(ativas)} ativas)")

# ──── Snapshot do dia ────
snap = [{"id": o["id"], "clienteNome": o["clienteNome"], "status": o["status"],
         "faseAtual": o["faseAtual"], "consultorNome": o["consultorNome"], "idade_dias": o["idade_dias"]}
        for o in ativas]
with open(SNAP, "w") as f:
    json.dump({"date": TODAY, "fetchedAt": NOW, "ativas": snap}, f, ensure_ascii=False)
print(f"  snapshot {TODAY}: {len(snap)} ativas")

# ════════════════════════════════════════════
# BACKLOG HISTORICO
# ════════════════════════════════════════════
hist_path = os.path.join(DADOS, "backlog-historico.json")
try:
    hist = json.load(open(hist_path))
except:
    hist = []

# 1) ZUMBI
zumbi_ids, zumbi_cli, zumbi_idade = [], {}, {}
for o in ativas:
    if (o.get("faseAtual") or "").strip().upper() == FINALIZADO_FASE:
        if o.get("status") == "reparo":
            continue
        sid = o["id"][:8]
        zumbi_ids.append(sid)
        zumbi_cli[sid] = (o.get("clienteNome") or "").strip()
        zumbi_idade[sid] = o.get("idade_dias")

# 2) ORFAS
def is_orfa(c):
    if c is None:
        return True
    s = str(c).strip()
    return s == "" or s == "[]"

orfas_ids, orfas_cli = [], {}
for o in ativas:
    if is_orfa(o.get("consultorNome")):
        sid = o["id"][:8]
        orfas_ids.append(sid)
        orfas_cli[sid] = (o.get("clienteNome") or "").strip()

# 3) LOTE VT
lote_ids, lote_cli = [], {}
for o in ativas:
    fase = (o.get("faseAtual") or "").upper()
    if "AGEND" in fase and "VT" in fase:
        idade = o.get("idade_dias")
        if idade and 258 <= idade <= 262:
            sid = o["id"][:8]
            lote_ids.append(sid)
            lote_cli[sid] = (o.get("clienteNome") or "").strip()

# 4) LIDERES OCULTOS + CONFLITOS
try:
    with open(os.path.join(DIR, "data.json"), encoding="utf-8") as f:
        dataj = json.load(f)
    escalacao = dataj.get("escalacao") or []
except:
    escalacao = []

lideres_hoje = {}
membros_hoje = {}
for esc in (escalacao or []):
    obra_id = esc.get("projetoId") or esc.get("id") or ""
    obra_short = obra_id[:8] if obra_id else ""
    lid = esc.get("liderId")
    if lid:
        lideres_hoje.setdefault(lid, set()).add(obra_short)
    for m in (esc.get("membros") or []):
        mid = m.get("id") or m.get("aplicadorId")
        if mid:
            membros_hoje.setdefault(mid, []).append(obra_short)

ocultos = {lid: len(obras_set) for lid, obras_set in lideres_hoje.items()
           if lid and lid not in ids_cadastrados}

conflitos = {}
for mid, obras_list in membros_hoje.items():
    obras_unicas = list(set(o for o in obras_list if o))
    if len(obras_unicas) >= 2 and mid not in lideres_hoje:
        nome = None
        for eq in (equipes or []):
            for m in (eq.get("membros") or []):
                if m.get("id") == mid:
                    nome = m.get("nome")
                    break
            if nome:
                break
        conflitos[mid] = {"nome": nome or mid[:8], "obras": obras_unicas}

# Monta entrada de hoje
entrada_hoje = {
    "date": TODAY,
    "indices": {
        "zumbi": {
            "total": len(zumbi_ids),
            "ids": sorted(zumbi_ids),
            "clientes": zumbi_cli,
            "idades": zumbi_idade
        },
        "lideres_ocultos": {
            "total": len(ocultos),
            "ids": [lid[:8] for lid in ocultos.keys()],
            "obras_lideradas": {lid[:8]: n for lid, n in ocultos.items()}
        },
        "orfas": {
            "total": len(orfas_ids),
            "ids": sorted(orfas_ids),
            "clientes": orfas_cli
        },
        "conflitos": {
            "total": len(conflitos),
            "nomes": sorted([v["nome"] for v in conflitos.values()]),
            "detalhe": {v["nome"]: {"obras": v["obras"]} for v in conflitos.values()}
        },
        "lote_vt": {
            "total": len(lote_ids),
            "ids": sorted(lote_ids),
            "clientes": lote_cli
        }
    },
    "mudancas_vs_anterior": None
}

# Detectar mudancas vs anterior
panel_by_short = {o["id"][:8]: o for o in ativas}

if hist and hist[-1].get("date") == TODAY:
    hist = hist[:-1]

prev = hist[-1] if hist else None

def detectar_mudancas(prev, atual):
    if not prev:
        return None
    p = prev["indices"]
    a = atual["indices"]
    out = {}

    p_zumbi = set(p.get("zumbi", {}).get("ids", []))
    a_zumbi = set(a.get("zumbi", {}).get("ids", []))
    saiu_zumbi = p_zumbi - a_zumbi
    if saiu_zumbi:
        out["zumbi_saiu"] = []
        for sid in sorted(saiu_zumbi):
            cli = p.get("zumbi", {}).get("clientes", {}).get(sid, sid)
            idade = p.get("zumbi", {}).get("idades", {}).get(sid)
            out["zumbi_saiu"].append({
                "id": sid, "cliente": cli,
                "idade_quando_saiu": idade,
                "motivo": "saiu de CLIENTE FINALIZADO ou foi finalizado"
            })

    p_orf = set(p.get("orfas", {}).get("ids", []))
    a_orf = set(a.get("orfas", {}).get("ids", []))
    atrib = p_orf - a_orf
    if atrib:
        out["orfas_atribuida"] = []
        for sid in sorted(atrib):
            cli = p.get("orfas", {}).get("clientes", {}).get(sid, sid)
            cons = (panel_by_short.get(sid, {}).get("consultorNome") or "").strip()
            cons_short = cons.split()[0] if cons else "(?)"
            out["orfas_atribuida"].append({
                "id": sid, "cliente": cli,
                "novo_consultor": cons_short
            })

    p_lid = set(p.get("lideres_ocultos", {}).get("ids", []))
    a_lid = set(a.get("lideres_ocultos", {}).get("ids", []))
    formaliz = p_lid - a_lid
    if formaliz:
        out["lideres_formalizado"] = [
            {"id": sid, "motivo": "agora aparece em /api/equipes"}
            for sid in sorted(formaliz)
        ]

    p_conf = set(p.get("conflitos", {}).get("nomes", []))
    a_conf = set(a.get("conflitos", {}).get("nomes", []))
    resolv = p_conf - a_conf
    if resolv:
        out["conflitos_resolvido"] = [
            {"nome": n, "motivo": "não está mais escalado em ≥2 obras"}
            for n in sorted(resolv)
        ]

    p_vt = set(p.get("lote_vt", {}).get("ids", []))
    a_vt = set(a.get("lote_vt", {}).get("ids", []))
    destrav = p_vt - a_vt
    if destrav:
        out["lote_vt_destravada"] = []
        for sid in sorted(destrav):
            cli = p.get("lote_vt", {}).get("clientes", {}).get(sid, sid)
            out["lote_vt_destravada"].append({
                "id": sid, "cliente": cli,
                "motivo": "mudou de fase AGEND. VT"
            })

    return out or None

entrada_hoje["mudancas_vs_anterior"] = detectar_mudancas(prev, entrada_hoje)

hist.append(entrada_hoje)
if len(hist) > 90:
    hist = hist[-90:]

with open(hist_path, "w") as f:
    json.dump(hist, f, ensure_ascii=False, indent=2)

n_mud = sum(len(v) for v in (entrada_hoje["mudancas_vs_anterior"] or {}).values())
print(f"  backlog-historico: {len(hist)} entries | zumbi={len(zumbi_ids)} ocultos={len(ocultos)} orfas={len(orfas_ids)} conf={len(conflitos)} vt={len(lote_ids)} | mudancas={n_mud}")

# ════════════════════════════════════════════
# DASHBOARD-DATA.JSON
# ════════════════════════════════════════════
dd = {
    "snapshot_date": TODAY,
    "AGG": {
        "total_ativas": len(ativas),
        "total_obras": len(obras),
        "status_dist": {},
        "n_180_plus": sum(1 for o in ativas if (o.get("idade_dias") or 0) >= 180),
        "n_270_plus": sum(1 for o in ativas if (o.get("idade_dias") or 0) >= 270),
        "n_lt90": sum(1 for o in ativas if (o.get("idade_dias") or 0) < 90 and o.get("idade_dias") is not None),
        "n_90_180": sum(1 for o in ativas if 90 <= (o.get("idade_dias") or 0) < 180),
        "metragem_total": sum(float(o.get("projetoMetragem") or 0) for o in ativas),
        "idade_media": round(sum(o["idade_dias"] for o in ativas if o.get("idade_dias")) / max(1, sum(1 for o in ativas if o.get("idade_dias"))), 1),
        "idade_mediana": 0,
        "sem_consultor_ativas": len(orfas_ids),
    },
    "Q2_OBRAS": [{"id": o["id"], "cliente": o.get("clienteNome"), "cidade": o.get("projetoCidade"),
                   "fase": o.get("faseAtual"), "consultor": o.get("consultorNome"),
                   "status": o.get("status"), "m2": float(o.get("projetoMetragem") or 0),
                   "idade": o.get("idade_dias")} for o in ativas],
}

# Status distribution
for o in ativas:
    s = o.get("status", "?")
    dd["AGG"]["status_dist"][s] = dd["AGG"]["status_dist"].get(s, 0) + 1

# Top consultores
cons = {}
for o in ativas:
    c = o.get("consultorNome") or "(sem)"
    if str(c).strip() in ("", "[]"):
        c = "(sem)"
    cons[c] = cons.get(c, 0) + 1
dd["AGG"]["top_consultores"] = sorted([{"nome": k, "n": v} for k, v in cons.items()], key=lambda x: -x["n"])

# Top fases
fases = {}
for o in ativas:
    f = o.get("faseAtual") or "(sem)"
    fases[f] = fases.get(f, 0) + 1
dd["AGG"]["top_fases"] = sorted([{"fase": k, "n": v} for k, v in fases.items()], key=lambda x: -x["n"])[:10]

# Mediana
idades = sorted([o["idade_dias"] for o in ativas if o.get("idade_dias")])
dd["AGG"]["idade_mediana"] = idades[len(idades) // 2] if idades else 0

# Preservar campos extras do JSON existente
dd_path = os.path.join(DADOS, "dashboard-data.json")
if os.path.exists(dd_path):
    try:
        old = json.load(open(dd_path))
        for k in ("EXT", "Q2_DIAG", "Q4_RESP_OPS", "Q4_ESCALACAO", "Q4_DATAS", "Q1_PLAN_OBRAS", "Q1_TOTAIS",
                   "SYNC_LIMBO", "SYNC_ESCALACAO_INV", "SYNC_BUGARRAY", "Q3_EQUIPES", "Q3_OBRAS_HOJE"):
            if k in old and k not in dd:
                dd[k] = old[k]
    except:
        pass

with open(dd_path, "w") as f:
    json.dump(dd, f, ensure_ascii=False)
print(f"  dashboard-data.json: {len(ativas)} ativas, snapshot {TODAY}")

# ════════════════════════════════════════════
# HEADLINE.JSON — fonte única dos números-âncora
# Lido por hub.html, dashboard.html, atena.html, indicadores-v2.html, obras-mapa.html
# Fórmula do score documentada em dados/SCORE-FORMULA.md
# ════════════════════════════════════════════
total_at = max(1, len(ativas))
n_zumbi = len(zumbi_ids)
n_orfas = len(orfas_ids)
n_lote_vt = len(lote_ids)
n_180 = dd["AGG"]["n_180_plus"]
n_270 = dd["AGG"]["n_270_plus"]
mediana = dd["AGG"]["idade_mediana"] or 0
meta_ciclo = 150

pct_zumbi = round(n_zumbi / total_at * 100, 1)
pct_orfas = round(n_orfas / total_at * 100, 1)
pct_180 = round(n_180 / total_at * 100, 1)
pct_lote_vt = round(n_lote_vt / total_at * 100, 1)
excesso_ciclo = round(max(0, (mediana - meta_ciclo) / meta_ciclo) * 100, 1) if mediana else 0

# Pesos — alteração requer atualizar dados/SCORE-FORMULA.md
PESO_ZUMBI = 0.8
PESO_ORFAS = 0.5
PESO_180 = 0.2
PESO_CICLO = 0.3
PESO_LOTE_VT = 0.6

penalidade = (
    PESO_ZUMBI * pct_zumbi
    + PESO_ORFAS * pct_orfas
    + PESO_180 * pct_180
    + PESO_CICLO * excesso_ciclo
    + PESO_LOTE_VT * pct_lote_vt
)
score = max(0, round(100 - penalidade))

# Eventos novos hoje (deltas vs anterior)
mud = entrada_hoje.get("mudancas_vs_anterior") or {}
novos_hoje = sum(len(v) for v in mud.values()) if mud else 0

headline = {
    "schema_version": 1,
    "snapshot_date": TODAY,
    "atualizado_em": NOW,
    "ativas": len(ativas),
    "score": score,
    "score_componentes": {
        "zumbi_pct": pct_zumbi,
        "orfas_pct": pct_orfas,
        "ciclo_180_pct": pct_180,
        "ciclo_mediano": mediana,
        "ciclo_meta": meta_ciclo,
        "lote_vt_270d": n_lote_vt
    },
    "alertas": {
        "zumbi": n_zumbi,
        "orfas": n_orfas,
        "lote_vt_270d": n_lote_vt,
        "ciclo_270_plus": n_270,
        "novos_hoje": novos_hoje
    },
    "fonte": "refresh.sh + dashboard-data.json + backlog-historico.json"
}

with open(os.path.join(DADOS, "headline.json"), "w") as f:
    json.dump(headline, f, ensure_ascii=False, indent=2)
print(f"  headline.json: score={score} ativas={len(ativas)} alertas={n_zumbi+n_orfas+n_lote_vt} novos_hoje={novos_hoje}")

# ════════════════════════════════════════════
# ALERTA-YYYY-MM-DD.json — eventos do dia (FASE 4.4)
# Detalhamento dos deltas críticos. Hub mostra contagem (novos_hoje), modal abre detalhes.
# ════════════════════════════════════════════
alerta_dir = os.path.join(DADOS, "alertas")
os.makedirs(alerta_dir, exist_ok=True)
alerta = {
    "schema_version": 1,
    "date": TODAY,
    "gerado_em": NOW,
    "eventos": [],
    "resumo": {"total": 0, "negativos": 0, "positivos": 0}
}

def add_evento(tipo, titulo, descricao, severidade, alvo):
    alerta["eventos"].append({
        "tipo": tipo,
        "titulo": titulo,
        "descricao": descricao,
        "severidade": severidade,
        "alvo": alvo
    })

if mud:
    if mud.get("zumbi_saiu"):
        n = len(mud["zumbi_saiu"])
        add_evento("zumbi_saiu", f"{n} obras encerradas", "saíram da fase CLIENTE FINALIZADO desde a varredura anterior", "info", "atena")
    if mud.get("orfas_atribuida"):
        n = len(mud["orfas_atribuida"])
        add_evento("orfas_atribuida", f"{n} obras ganharam consultor", "atribuições recentes", "info", "atena")
    if mud.get("lote_vt_destravada"):
        n = len(mud["lote_vt_destravada"])
        add_evento("lote_vt_destravada", f"{n} obras destravadas de VT", "saíram da fase AGEND. VT", "info", "atena")
    if mud.get("lideres_formalizado"):
        n = len(mud["lideres_formalizado"])
        add_evento("lideres_formalizado", f"{n} líderes formalizados", "agora cadastrados em /api/equipes", "info", "atena")
    if mud.get("conflitos_resolvido"):
        n = len(mud["conflitos_resolvido"])
        add_evento("conflitos_resolvido", f"{n} conflitos resolvidos", "não há mais aplicador escalado em ≥2 obras simultâneas", "info", "atena")

# Detecção de pioras (delta dos indicadores principais)
if hist and len(hist) >= 2:
    prev_idx = hist[-2]["indices"] if hist[-2].get("indices") else {}
    cur_idx = entrada_hoje["indices"]
    pZ = (prev_idx.get("zumbi") or {}).get("total", 0)
    cZ = (cur_idx.get("zumbi") or {}).get("total", 0)
    pO = (prev_idx.get("orfas") or {}).get("total", 0)
    cO = (cur_idx.get("orfas") or {}).get("total", 0)
    pV = (prev_idx.get("lote_vt") or {}).get("total", 0)
    cV = (cur_idx.get("lote_vt") or {}).get("total", 0)
    if cZ > pZ:
        add_evento("zumbi_subiu", f"+{cZ - pZ} zumbi vs anterior", f"de {pZ} para {cZ}", "alta", "atena")
    if cO > pO:
        add_evento("orfas_subiu", f"+{cO - pO} órfãs vs anterior", f"de {pO} para {cO}", "media", "atena")
    if cV > pV:
        add_evento("lote_vt_subiu", f"+{cV - pV} VT travadas vs anterior", f"de {pV} para {cV}", "media", "atena")

alerta["resumo"]["total"] = len(alerta["eventos"])
alerta["resumo"]["positivos"] = sum(1 for e in alerta["eventos"] if e["severidade"] == "info")
alerta["resumo"]["negativos"] = alerta["resumo"]["total"] - alerta["resumo"]["positivos"]

# VEREDITO — status semantico: distingue "sem mudancas" (esperado) de "vazio sem motivo claro"
if not alerta["eventos"]:
    if mud is None:
        alerta["status"] = "sem_mudancas"
        alerta["status_label"] = "Sem mudanças desde a varredura anterior"
    else:
        alerta["status"] = "estavel"
        alerta["status_label"] = "Estado estável (mudanças detectadas mas não notáveis)"
elif alerta["resumo"]["negativos"] > 0:
    alerta["status"] = "atencao"
    alerta["status_label"] = f"{alerta['resumo']['negativos']} alertas de piora detectados"
else:
    alerta["status"] = "positivo"
    alerta["status_label"] = f"{alerta['resumo']['positivos']} eventos positivos no período"

with open(os.path.join(alerta_dir, f"{TODAY}.json"), "w") as f:
    json.dump(alerta, f, ensure_ascii=False, indent=2)
print(f"  alertas/{TODAY}.json: {alerta['resumo']['total']} eventos · status={alerta['status']}")
PYEOF

# ─── Q4 — cruz-frescor.json ───
# Mapeia idade de cada cruz-*.json (gerado_em / geradoEm / data_referencia)
# Permite UI alertar quando snapshot está estático há muito tempo.
echo "[Q4] Gerando cruz-frescor.json..."
python3 -c "
import json, os, datetime
DADOS = '$DADOS'
TODAY = '$TODAY'
hoje = datetime.date.fromisoformat(TODAY)

frescor = { 'gerado_em': '$NOW', 'snapshot_date': TODAY, 'cruzamentos': [] }
for f in sorted(os.listdir(DADOS)):
    if not f.startswith('cruz-') or not f.endswith('.json'):
        continue
    path = os.path.join(DADOS, f)
    info = { 'arquivo': f, 'tamanho_kb': round(os.path.getsize(path) / 1024, 1) }
    try:
        with open(path, encoding='utf-8') as fh:
            d = json.load(fh)
        # tenta vários campos comuns
        ge = d.get('gerado_em') or d.get('geradoEm') or d.get('data_referencia') or d.get('data_base')
        if ge:
            ge_str = str(ge)[:10]
            try:
                ge_date = datetime.date.fromisoformat(ge_str)
                idade = (hoje - ge_date).days
                info['gerado_em'] = ge_str
                info['idade_dias'] = idade
                if idade <= 1:
                    info['frescor'] = 'fresco'
                elif idade <= 7:
                    info['frescor'] = 'recente'
                elif idade <= 30:
                    info['frescor'] = 'antigo'
                else:
                    info['frescor'] = 'estatico'
            except:
                info['gerado_em'] = ge_str
                info['frescor'] = 'desconhecido'
        else:
            info['frescor'] = 'sem_data'
    except Exception as e:
        info['erro'] = str(e)[:80]
        info['frescor'] = 'erro'
    frescor['cruzamentos'].append(info)

# resumo
freq = {}
for c in frescor['cruzamentos']:
    f = c.get('frescor', 'sem_data')
    freq[f] = freq.get(f, 0) + 1
frescor['resumo'] = freq
frescor['total'] = len(frescor['cruzamentos'])

with open(os.path.join(DADOS, 'cruz-frescor.json'), 'w', encoding='utf-8') as fh:
    json.dump(frescor, fh, ensure_ascii=False, indent=2)
print(f'  cruz-frescor.json: {len(frescor[\"cruzamentos\"])} cruz-* avaliados (resumo: {freq})')
"

echo "[done] Refresh PESADO concluído em $NOW"
rm -rf "$TMP"
