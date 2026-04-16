#!/usr/bin/env bash
# Refresh automático Monofloor — fetch + snapshot + regen obras-mapa
# Roda 1x a cada 30 min via GitHub Actions
# Hoje (refresh leve): atualiza data.json + escalacao
# Primeiro run do dia (Brasília): atualiza details + painel-temporal + snapshot + obras-mapa

set -euo pipefail

API_CLI="https://cliente.monofloor.cloud/api"
API_PLAN="https://planejamento.monofloor.cloud/api"
DIR="$(cd "$(dirname "$0")" && pwd)"
DADOS="$DIR/dados"
DETAILS="$DADOS/details"
SNAPSHOTS="$DADOS/snapshots"
mkdir -p "$DETAILS" "$SNAPSHOTS"

TODAY=$(TZ=America/Sao_Paulo date +%Y-%m-%d)
NOW_UTC=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SNAP_FILE="$SNAPSHOTS/$TODAY.json"

# ─────────────────────────────────────────
# 1) REFRESH LEVE (sempre) — 5 listas
# ─────────────────────────────────────────
echo "[1/5] Fetch listas leves..."
P=$(curl -s --max-time 30 "$API_CLI/projects?limit=2000")
D=$(curl -s --max-time 30 "$API_CLI/dashboard")
A=$(curl -s --max-time 30 "$API_CLI/analise")
E=$(curl -s --max-time 30 "$API_CLI/escalacao-diaria")
EQ=$(curl -s --max-time 30 "$API_CLI/equipes")

# valida JSONs (não sobrescreve se vier corrompido)
for V in "$P" "$D" "$A" "$E" "$EQ"; do
  echo "$V" | python3 -c "import sys,json; json.load(sys.stdin)" > /dev/null 2>&1 || {
    echo "ERRO: resposta inválida de uma das APIs. Abortando."
    exit 1
  }
done

# data.json consolidado
cat > "$DIR/data.json" <<EOF
{"projects":$P,"dashboard":$D,"analise":$A,"escalacao":$E,"equipes":$EQ,"fetchedAt":"$NOW_UTC"}
EOF
echo "  data.json: $(wc -c < "$DIR/data.json") bytes"

# ─────────────────────────────────────────
# 2) DECIDIR SE FAZ REFRESH PESADO
# ─────────────────────────────────────────
DO_HEAVY=0
if [ ! -f "$SNAP_FILE" ]; then
  DO_HEAVY=1
  echo "[2/5] Snapshot do dia ($TODAY) ainda não existe → refresh PESADO"
else
  echo "[2/5] Snapshot do dia já existe → refresh LEVE apenas"
fi

if [ "$DO_HEAVY" -eq 0 ]; then
  echo "[done] Refresh leve concluído em $NOW_UTC"
  exit 0
fi

# ─────────────────────────────────────────
# 3) FETCH DETAILS (apenas ativas + recentes)
# ─────────────────────────────────────────
echo "[3/5] Fetch dos details..."

# Extrai IDs ativos (status NOT IN finalizado/concluido/cancelado)
IDS=$(echo "$P" | python3 -c "
import sys, json
d = json.load(sys.stdin)
inativos = {'finalizado','concluido','cancelado'}
for p in d:
    if p.get('status') not in inativos:
        print(p['id'])
")

N_ATIVAS=$(echo "$IDS" | wc -l)
echo "  $N_ATIVAS obras ativas a buscar"

# baixa em paralelo (lotes de 20)
echo "$IDS" | xargs -I {} -P 20 bash -c '
  ID="$1"
  OUT="'"$DETAILS"'/$ID.json"
  curl -s --max-time 20 "'"$API_CLI"'/projects/$ID" -o "$OUT" 2>/dev/null
  [ -s "$OUT" ] || rm -f "$OUT"
' _ {}

N_OK=$(ls "$DETAILS" | wc -l)
echo "  $N_OK details salvos"

# ─────────────────────────────────────────
# 4) REGENERAR painel-temporal.json
# ─────────────────────────────────────────
echo "[4/5] Regenerando painel-temporal.json..."

# Snapshot Pipefy (fonte auxiliar de created_at)
PIPEFY=$(curl -s --max-time 30 "https://raw.githubusercontent.com/vitormonofloor/cargo-assistente/main/pipefy_cards.json")

python3 - <<PYEOF
import json, os, sys
from datetime import datetime, timezone

DETAILS_DIR = "$DETAILS"
PIPEFY_RAW = '''$PIPEFY'''
OUT = "$DADOS/painel-temporal.json"
TODAY = datetime.strptime("$TODAY", "%Y-%m-%d").date()

# Indexar Pipefy snapshot por id (string)
try:
    pipefy_list = json.loads(PIPEFY_RAW)
    pipefy_by_id = {str(c.get("id")): c for c in pipefy_list if c.get("id")}
except Exception as e:
    print(f"  AVISO: pipefy snapshot inválido ({e}), seguindo sem ele")
    pipefy_by_id = {}

INATIVAS = {"finalizado", "concluido", "cancelado"}
out = []

for fname in os.listdir(DETAILS_DIR):
    if not fname.endswith(".json"):
        continue
    try:
        with open(os.path.join(DETAILS_DIR, fname), encoding="utf-8") as f:
            o = json.load(f)
    except Exception:
        continue

    pid = o.get("id")
    if not pid:
        continue

    pipefyCardId = (o.get("acessoDetalhes") or {}).get("pipefyCardId") or o.get("pipefyCardId")
    pipefy_api_dt = (o.get("acessoDetalhes") or {}).get("pipefyCreatedAt")

    pipefy_snap_dt = None
    if pipefyCardId and str(pipefyCardId) in pipefy_by_id:
        pipefy_snap_dt = pipefy_by_id[str(pipefyCardId)].get("created_at")

    # data_radar: prioridade snapshot Pipefy > API
    data_radar, fonte = None, "sem_data"
    if pipefy_snap_dt:
        data_radar, fonte = pipefy_snap_dt[:10], "pipefy_snapshot"
    elif pipefy_api_dt:
        data_radar, fonte = pipefy_api_dt[:10], "pipefy_api"

    idade_dias = None
    if data_radar:
        try:
            idade_dias = (TODAY - datetime.strptime(data_radar, "%Y-%m-%d").date()).days
        except Exception:
            pass

    status = o.get("status")
    out.append({
        "id": pid,
        "clienteNome": o.get("clienteNome"),
        "projetoCidade": o.get("projetoCidade"),
        "status": status,
        "faseAtual": o.get("faseAtual"),
        "consultorNome": o.get("consultorNome"),
        "projetoMetragem": o.get("projetoMetragem"),
        "pipefyCardId": pipefyCardId,
        "pipefy_snapshot_created_at": pipefy_snap_dt,
        "pipefyCreatedAt_api": pipefy_api_dt,
        "data_radar": data_radar,
        "data_radar_fonte": fonte,
        "idade_dias": idade_dias,
        "ativa": status not in INATIVAS,
    })

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

ativas = sum(1 for o in out if o["ativa"])
com_data = sum(1 for o in out if o["data_radar"])
print(f"  painel-temporal.json: {len(out)} obras ({ativas} ativas, {com_data} com data)")
PYEOF

# ─────────────────────────────────────────
# 5) SNAPSHOT DIÁRIO + regen obras-mapa.html
# ─────────────────────────────────────────
echo "[5/5] Snapshot do dia + regen obras-mapa..."

# Snapshot diário compacto: apenas {id, clienteNome, status, faseAtual, consultorNome, idade_dias}
python3 - <<PYEOF
import json
src = json.load(open("$DADOS/painel-temporal.json", encoding="utf-8"))
snap = [{
    "id": o["id"],
    "clienteNome": o["clienteNome"],
    "status": o["status"],
    "faseAtual": o["faseAtual"],
    "consultorNome": o["consultorNome"],
    "idade_dias": o["idade_dias"],
} for o in src if o.get("ativa")]
with open("$SNAP_FILE", "w", encoding="utf-8") as f:
    json.dump({"date": "$TODAY", "fetchedAt": "$NOW_UTC", "ativas": snap}, f, ensure_ascii=False)
print(f"  snapshot $TODAY.json: {len(snap)} obras ativas")
PYEOF

# Regen obras-mapa.html via PowerShell (já existe no repo)
if command -v pwsh > /dev/null 2>&1; then
  echo "  rodando build-mapa.ps1..."
  pwsh -ExecutionPolicy Bypass -File "$DIR/build-mapa.ps1" 2>&1 | tail -20 || echo "  AVISO: build-mapa.ps1 falhou (não bloqueia o refresh)"
else
  echo "  AVISO: pwsh não disponível, pulando regen obras-mapa.html"
fi

# ─────────────────────────────────────────
# 6) HISTÓRICO BACKLOG — calcula 5 índices, compara, anexa
# ─────────────────────────────────────────
echo "[6/6] Atualizando backlog-historico.json..."

HIST_FILE="$DADOS/backlog-historico.json"
EQUIPES_RAW="$EQ"

python3 - <<PYEOF
import json, os, sys
from datetime import datetime, date, timedelta

DADOS  = "$DADOS"
TODAY  = "$TODAY"
HIST_F = "$HIST_FILE"

# ---------- Carrega painel-temporal (fonte das obras) ----------
panel_path = os.path.join(DADOS, "painel-temporal.json")
with open(panel_path, encoding="utf-8") as f:
    panel = json.load(f)

# ---------- Carrega /api/equipes (fonte de líderes cadastrados) ----------
try:
    equipes = json.loads('''$EQUIPES_RAW''')
except Exception:
    equipes = []

# Set de IDs cadastrados em /api/equipes (todos os membros, qualquer função)
ids_cadastrados = set()
for eq in (equipes or []):
    for m in (eq.get("membros") or []):
        if m.get("id"):
            ids_cadastrados.add(m["id"])
    if eq.get("liderId"):
        ids_cadastrados.add(eq["liderId"])

INATIVAS = {"finalizado", "concluido", "cancelado"}
FINALIZADO_FASE = "CLIENTE FINALIZADO"

# ============================================================
# 1) ZUMBI: ativa + faseAtual=CLIENTE FINALIZADO
# ============================================================
zumbi_ids   = []
zumbi_cli   = {}
zumbi_idade = {}
for o in panel:
    if o.get("status") in INATIVAS:
        continue
    if (o.get("faseAtual") or "").strip().upper() == FINALIZADO_FASE:
        sid = o["id"][:8]
        zumbi_ids.append(sid)
        zumbi_cli[sid]   = (o.get("clienteNome") or "").strip()
        zumbi_idade[sid] = o.get("idade_dias")

# ============================================================
# 2) ÓRFÃS: ativa + consultorNome vazio/null/literal "[]"
# ============================================================
orfas_ids = []
orfas_cli = {}
def is_orfa(c):
    if c is None: return True
    s = str(c).strip()
    return s == "" or s == "[]"
for o in panel:
    if o.get("status") in INATIVAS: continue
    if is_orfa(o.get("consultorNome")):
        sid = o["id"][:8]
        orfas_ids.append(sid)
        orfas_cli[sid] = (o.get("clienteNome") or "").strip()

# ============================================================
# 3) LOTE VT: idade_dias entre 258-262 (lote dos 260d ±2)
# ============================================================
lote_ids = []
lote_cli = {}
for o in panel:
    if o.get("status") in INATIVAS: continue
    fase = (o.get("faseAtual") or "").upper()
    if "AGEND" in fase and "VT" in fase:
        idade = o.get("idade_dias")
        if idade and 258 <= idade <= 262:
            sid = o["id"][:8]
            lote_ids.append(sid)
            lote_cli[sid] = (o.get("clienteNome") or "").strip()

# ============================================================
# 4) LÍDERES OCULTOS + CONFLITOS — precisa de escalacao-diaria
# ============================================================
# Tenta carregar escalação do data.json (já fetched no passo 1)
try:
    with open(os.path.join("$DIR", "data.json"), encoding="utf-8") as f:
        dataj = json.load(f)
    escalacao = dataj.get("escalacao") or []
except Exception:
    escalacao = []

# liderId aparece nas obras escaladas hoje. Se não está em ids_cadastrados → oculto
lideres_hoje = {}      # liderId -> set(obraId)
membros_hoje = {}      # membroId -> list(obraId)
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

ocultos = {lid: len(obras) for lid, obras in lideres_hoje.items()
           if lid and lid not in ids_cadastrados}

# Conflito: aplicador (não-líder) escalado em ≥2 obras distintas hoje
conflitos = {}
for mid, obras in membros_hoje.items():
    obras_unicas = list(set(o for o in obras if o))
    if len(obras_unicas) >= 2 and mid not in lideres_hoje:
        # busca nome em /api/equipes
        nome = None
        for eq in (equipes or []):
            for m in (eq.get("membros") or []):
                if m.get("id") == mid:
                    nome = m.get("nome")
                    break
            if nome: break
        conflitos[mid] = {"nome": nome or mid[:8], "obras": obras_unicas}

# ============================================================
# Monta entrada de hoje
# ============================================================
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

# ============================================================
# Carrega histórico anterior
# ============================================================
hist = []
if os.path.exists(HIST_F):
    try:
        with open(HIST_F, encoding="utf-8") as f:
            hist = json.load(f)
    except Exception:
        hist = []

# Se a última entrada é de hoje, sobrescreve (re-run no mesmo dia)
if hist and hist[-1].get("date") == TODAY:
    hist = hist[:-1]

prev = hist[-1] if hist else None

# ============================================================
# Detecta mudanças
# ============================================================
def detectar_mudancas(prev, atual):
    if not prev: return None
    p = prev["indices"]
    a = atual["indices"]
    out = {}

    # zumbi: IDs ontem mas não hoje
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

    # órfãs: IDs ontem que ganharam consultor (não estão hoje)
    p_orf = set(p.get("orfas", {}).get("ids", []))
    a_orf = set(a.get("orfas", {}).get("ids", []))
    atrib = p_orf - a_orf
    if atrib:
        # tenta achar consultor atual no painel
        panel_by_short = {o["id"][:8]: o for o in panel}
        out["orfas_atribuida"] = []
        for sid in sorted(atrib):
            cli  = p.get("orfas", {}).get("clientes", {}).get(sid, sid)
            cons = (panel_by_short.get(sid, {}).get("consultorNome") or "").strip()
            cons_short = cons.split()[0] if cons else "(?)"
            out["orfas_atribuida"].append({
                "id": sid, "cliente": cli,
                "novo_consultor": cons_short
            })

    # líderes ocultos: IDs ontem mas não hoje (= cadastrados em /api/equipes)
    p_lid = set(p.get("lideres_ocultos", {}).get("ids", []))
    a_lid = set(a.get("lideres_ocultos", {}).get("ids", []))
    formaliz = p_lid - a_lid
    if formaliz:
        out["lideres_formalizado"] = [
            {"id": sid, "motivo": "agora aparece em /api/equipes"}
            for sid in sorted(formaliz)
        ]

    # conflitos: nomes ontem mas não hoje
    p_conf = set(p.get("conflitos", {}).get("nomes", []))
    a_conf = set(a.get("conflitos", {}).get("nomes", []))
    resolv = p_conf - a_conf
    if resolv:
        out["conflitos_resolvido"] = [
            {"nome": n, "motivo": "não está mais escalado em ≥2 obras"}
            for n in sorted(resolv)
        ]

    # lote VT: IDs ontem mas não hoje (=mudaram de fase)
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

# ============================================================
# Anexa, aplica janela 90d e salva
# ============================================================
hist.append(entrada_hoje)

# rolling window 90d
if len(hist) > 90:
    hist = hist[-90:]

with open(HIST_F, "w", encoding="utf-8") as f:
    json.dump(hist, f, ensure_ascii=False, indent=2)

n_mud = sum(len(v) for v in (entrada_hoje["mudancas_vs_anterior"] or {}).values())
print(f"  backlog-historico.json: {len(hist)} entradas | hoje: zumbi={len(zumbi_ids)} ocultos={len(ocultos)} orfas={len(orfas_ids)} conf={len(conflitos)} vt={len(lote_ids)} | mudancas={n_mud}")
PYEOF

echo "[done] Refresh PESADO concluído em $NOW_UTC"
