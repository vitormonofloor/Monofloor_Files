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
fetch "$API_PLN/analytics/weekly-forecast" "$TMP/fcast.json"

# Compor JSON canônico via Python (heredoc com env vars)
NOW="$NOW" TMP="$TMP" DADOS="$DADOS" python3 << 'PYEOF'
import json, os, sys
from collections import Counter
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

# Contagem por status (regra confirmada via reverse-engineer da tela do Rodrigo 2026-04-30)
if not isinstance(projects, list):
    projects = []
status_count = Counter(p.get("status") or "sem_status" for p in projects if isinstance(p, dict))

total = len(projects)
finalizados = status_count.get("finalizado", 0) + status_count.get("concluido", 0)
ativas = total - finalizados  # tudo que NÃO é finalizado/concluido (regra do frontend)
em_exec = status_count.get("em_execucao", 0)
pausadas = status_count.get("pausado", 0)

current_load = cap.get("currentLoad", {}) or {}
capacity_obj = cap.get("capacity", {}) or {}
active_proj = cap.get("activeProjects", {}) or {}
recom = cap.get("recommendations", {}) or {}

canon = {
    "atualizado_em": NOW,
    "fonte": "cliente.monofloor.cloud/api/projects (contagens) + planejamento.monofloor.cloud/api/{orchestrator,analytics}/* (capacidade/alertas)",
    "totais": {
        "total": total,
        "ativas": ativas,
        "finalizados": finalizados,
        "em_execucao": em_exec,
        "pausados": pausadas,
    },
    "por_status": dict(status_count),
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
        "obras_ativas_capacity": active_proj.get("count", 0),
        "m2_em_obra": active_proj.get("totalM2", 0),
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
    "agenda_hoje": {
        "visitas": stats.get("visitasHoje", 0),
        "entregas": stats.get("entregasHoje", 0),
    },
    "weekly_forecast": fcast,
}

out = f"{DADOS}/rodrigo-stats.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(canon, f, ensure_ascii=False, indent=2)
print(f"  rodrigo-stats.json: ativas={ativas} total={stats.get('totalProjetos',0)} cap={current_load.get('utilizationPercent',0)}%")
PYEOF

rm -rf "$TMP"
echo "[done] Coletor Rodrigo concluído."
