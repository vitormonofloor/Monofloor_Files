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

echo "[done] Refresh PESADO concluído em $NOW_UTC"
