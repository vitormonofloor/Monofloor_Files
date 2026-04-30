#!/usr/bin/env bash
# Coletor Rodrigo — fonte canônica de números do painel do Rodrigo.
# Saída: analise/dados/rodrigo-stats.json
# Chamado pelo refresh.yml a cada 30 min.
#
# DESCOBERTA 2026-04-30: o frontend planejamento.monofloor.cloud usa
# cliente.monofloor.cloud como BACKEND DE DADOS. Os números visíveis na tela
# (261 ativos, 34 em execução, 5 pausados, 774 finalizados) são derivados
# diretamente do /api/projects do cliente. /api/stats do planejamento é
# uma view limitada DIFERENTE — não usar pra contagens.
#
# Endpoints cobertos:
#   cliente.monofloor.cloud/api/projects?limit=2000  — 1035 obras (fonte das contagens)
#   planejamento.monofloor.cloud/api/orchestrator/status         — operação viva
#   planejamento.monofloor.cloud/api/analytics/capacity          — capacidade real (utilizationPercent)
#   planejamento.monofloor.cloud/api/analytics/alerts            — alertas estruturados
#   planejamento.monofloor.cloud/api/analytics/weekly-forecast   — projeção semanal

API_CLI="https://cliente.monofloor.cloud/api"
API_PLN="https://planejamento.monofloor.cloud/api"
DIR="$(cd "$(dirname "$0")" && pwd)"
DADOS="$DIR/dados"
TMP="$DADOS/.tmp-rodrigo"
mkdir -p "$TMP"

NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "=== Coletor Rodrigo === $NOW"

fetch() {
  local url="$1" out="$2"
  curl -sf --max-time 30 "$url" -o "$out" \
    && echo "  $url OK ($(wc -c < "$out") bytes)" \
    || { echo "  $url FAILED"; echo '{}' > "$out"; }
}

# /api/projects do cliente (1035 obras = fonte das contagens reais)
fetch "$API_CLI/projects?limit=2000"   "$TMP/projects.json"; sleep 1
# Endpoints de operação/capacidade/alertas continuam no planejamento
fetch "$API_PLN/orchestrator/status"   "$TMP/orch.json";     sleep 1
fetch "$API_PLN/analytics/capacity"    "$TMP/cap.json";      sleep 1
fetch "$API_PLN/analytics/alerts"      "$TMP/alerts.json";   sleep 1
fetch "$API_PLN/analytics/weekly-forecast" "$TMP/fcast.json"; sleep 1

# Snapshot Pipefy mais recente (cargo-assistente roda seg+sex 5h e commita).
# Lista snapshots via API GitHub e baixa o mais novo.
echo "  Listando snapshots Pipefy..."
SNAP_NAME=$(curl -sf --max-time 20 \
  "https://api.github.com/repos/vitormonofloor/cargo-assistente/contents/cerebro_monofloor/snapshots" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(sorted([x['name'] for x in d if x['name'].startswith('pipefy_cards_') and x['name'].endswith('.json')])[-1])" 2>/dev/null)
if [ -n "$SNAP_NAME" ]; then
  fetch "https://raw.githubusercontent.com/vitormonofloor/cargo-assistente/main/cerebro_monofloor/snapshots/$SNAP_NAME" "$TMP/pipefy_snap.json"
  echo "  snapshot Pipefy: $SNAP_NAME"
else
  echo '{}' > "$TMP/pipefy_snap.json"
  echo "  Sem snapshot Pipefy disponível"
fi

# Compor JSON canônico via Python (heredoc com env vars)
NOW="$NOW" TMP="$TMP" DADOS="$DADOS" python3 << 'PYEOF'
import json, os, sys
from collections import Counter
from datetime import datetime, timedelta, timezone
TMP = os.environ['TMP']
DADOS = os.environ['DADOS']
NOW = os.environ['NOW']

def load(name):
    try:
        with open(f"{TMP}/{name}.json", encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

projects = load("projects")  # lista de 1035 obras do cliente
orch = load("orch")
cap = load("cap")
alerts = load("alerts")
fcast = load("fcast")
pipefy = load("pipefy_snap")  # {resumo, cards[]} do agente_historico

# Contagem por status (regra confirmada via reverse-engineer da tela do Rodrigo 2026-04-30)
if not isinstance(projects, list):
    projects = []
status_count = Counter(p.get("status") or "sem_status" for p in projects if isinstance(p, dict))

total = len(projects)
finalizados = status_count.get("finalizado", 0) + status_count.get("concluido", 0)
ativas = total - finalizados
em_exec_count = status_count.get("em_execucao", 0)
pausados_count = status_count.get("pausado", 0)

# m² em execução (canônico — soma de projetoMetragem das em_execucao)
def m2_of(p):
    try: return float(p.get("projetoMetragem") or 0)
    except: return 0.0

em_exec_obras = [p for p in projects if isinstance(p, dict) and p.get("status") == "em_execucao"]
m2_em_execucao = sum(m2_of(p) for p in em_exec_obras)

# Próximos N dias — alinhado com tela do Rodrigo (44 obras pra 15d):
# obras com status IN (aguardando_execucao, planejamento, em_execucao, aguardando_clima)
# E dataExecucaoPrevista entre hoje e hoje+N
PROX_STATUSES = {"aguardando_execucao", "planejamento", "em_execucao", "aguardando_clima"}
hoje = datetime.now(timezone.utc).date()

def parse_date(s):
    if not s: return None
    try:
        return datetime.fromisoformat(str(s).replace("Z","+00:00")).date()
    except Exception:
        try: return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
        except Exception: return None

def proximos(dias):
    limite = hoje + timedelta(days=dias)
    obras = []
    for p in projects:
        if not isinstance(p, dict): continue
        if p.get("status") not in PROX_STATUSES: continue
        d = parse_date(p.get("dataExecucaoPrevista"))
        if d and hoje <= d <= limite:
            obras.append(p)
    m2 = sum(m2_of(p) for p in obras)
    return {"obras": len(obras), "m2": round(m2)}

current_load = cap.get("currentLoad", {}) or {}
capacity_obj = cap.get("capacity", {}) or {}
active_proj = cap.get("activeProjects", {}) or {}
recom = cap.get("recommendations", {}) or {}

canon = {
    "atualizado_em": NOW,
    "fonte": "cliente.monofloor.cloud/api/projects (contagens + m²) + planejamento.monofloor.cloud/api/{orchestrator,analytics}/*",
    "totais": {
        "total": total,
        "ativas": ativas,
        "finalizados": finalizados,
        "em_execucao": em_exec_count,
        "pausados": pausados_count,
        "m2_em_execucao": round(m2_em_execucao),
    },
    "por_status": dict(status_count),
    "proximos": {
        "15d": proximos(15),
        "30d": proximos(30),
        "60d": proximos(60),
    },
    "operacao_viva": {
        "active_journeys": orch.get("activeJourneys", 0),
        "pending_tasks": orch.get("pendingTasks", 0),
        "executing_tasks": orch.get("executingTasks", 0),
    },
    "capacidade": {
        "utilization_percent": current_load.get("utilizationPercent", 0),
        "status": current_load.get("status", "unknown"),
        "aplicadores_total": cap.get("totalApplicators", 0),
        "aplicadores_necessarios": current_load.get("applicatorsNeeded", 0),
        "aplicadores_por_obra": current_load.get("applicatorsPerProject", 0),
        "capacidade_diaria_m2": capacity_obj.get("dailyM2", 0),
        "capacidade_semanal_m2_puro": capacity_obj.get("weeklyPure", 0),
        "capacidade_semanal_m2_misto": capacity_obj.get("weeklyMixed", 0),
        "capacidade_mensal_m2_puro": capacity_obj.get("monthlyPure", 0),
        "capacidade_mensal_m2_misto": capacity_obj.get("monthlyMixed", 0),
        "capacidade_mensal_produtiva": capacity_obj.get("monthlyProductiveM2", 0),
        "max_obras_saudavel": recom.get("maxProjectsHealthy", 0),
        "max_obras_minimo": recom.get("maxProjectsMinimum", 0),
    },
    "alertas": {
        "total": alerts.get("total", 0),
        "por_tipo": alerts.get("byType", {}),
        "por_severidade": alerts.get("bySeverity", {}),
        "detalhes": alerts.get("alerts", []),
    },
    "weekly_forecast": fcast,
}

# ============== TEMPO (do snapshot Pipefy) ==============
# Mediana de tempo das obras finalizadas em 2026 (substitui mediana de
# idade das ativas — que distorce). 3 medidas pra ver onde tá o gargalo.
def mediana(vals):
    s = sorted(v for v in vals if v is not None and v > 0)
    if not s: return 0
    n = len(s)
    return round(s[n // 2] if n % 2 == 1 else (s[n // 2 - 1] + s[n // 2]) / 2)

cards = pipefy.get("cards", []) if isinstance(pipefy, dict) else []
em2026 = [c for c in cards if isinstance(c, dict) and c.get("tf_finished_at") and str(c["tf_finished_at"]).startswith("2026")]

if em2026:
    canon["tempo"] = {
        "ciclo_total_mediana": mediana(c.get("dias_admin") for c in em2026),
        "pre_execucao_mediana": mediana(c.get("dias_contato_inicio") for c in em2026),
        "execucao_mediana": mediana(c.get("dias_execucao") for c in em2026),
        "meta_dias": 150,
        "obras_base": len(em2026),
        "periodo": "2026",
        "fonte": f"Painel de Obras (snapshot {pipefy.get('resumo', {}).get('coletado_em', 'sem data')})",
    }
else:
    canon["tempo"] = {"obras_base": 0, "periodo": "2026", "fonte": "Painel de Obras — snapshot indisponível"}

out = f"{DADOS}/rodrigo-stats.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(canon, f, ensure_ascii=False, indent=2)
print(f"  rodrigo-stats.json: total={total} ativas={ativas} em_exec={em_exec_count} ({round(m2_em_execucao)}m²) prox15d={canon['proximos']['15d']['obras']} prox30d={canon['proximos']['30d']['obras']} prox60d={canon['proximos']['60d']['obras']}")
PYEOF

rm -rf "$TMP"
echo "[done] Coletor Rodrigo concluído."
