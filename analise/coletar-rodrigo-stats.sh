#!/usr/bin/env bash
# Coletor Rodrigo — fetch dos 5 endpoints REST do planejamento.monofloor.cloud
# Saída: analise/dados/rodrigo-stats.json (fonte canônica de números do painel do Rodrigo)
# Chamado pelo refresh.yml a cada 30 min.
#
# Endpoints cobertos:
#   /api/stats                       — KPIs canônicos (totalProjetos, projetosEm*, obrasPausadas, etc)
#   /api/orchestrator/status         — operação viva (activeJourneys, pendingTasks)
#   /api/analytics/capacity          — capacidade real (utilizationPercent, capacidade semanal/mensal, recomendações)
#   /api/analytics/alerts            — alertas estruturados (stageDelay, noTeam, capacityRisk)
#   /api/analytics/weekly-forecast   — projeção semanal

API="https://planejamento.monofloor.cloud/api"
DIR="$(cd "$(dirname "$0")" && pwd)"
DADOS="$DIR/dados"
TMP="$DADOS/.tmp-rodrigo"
mkdir -p "$TMP"

NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "=== Coletor Rodrigo === $NOW"

fetch() {
  local path="$1" out="$2"
  curl -sf --max-time 30 "$API/$path" -o "$out" \
    && echo "  /api/$path OK ($(wc -c < "$out") bytes)" \
    || { echo "  /api/$path FAILED"; echo '{}' > "$out"; }
}

# Fetch sequencial (1s entre chamadas pra evitar rate limit do Rodrigo)
fetch "stats"                        "$TMP/stats.json";    sleep 1
fetch "orchestrator/status"          "$TMP/orch.json";     sleep 1
fetch "analytics/capacity"           "$TMP/cap.json";      sleep 1
fetch "analytics/alerts"             "$TMP/alerts.json";   sleep 1
fetch "analytics/weekly-forecast"    "$TMP/fcast.json"

# Compor JSON canônico via Python (heredoc com env vars)
NOW="$NOW" TMP="$TMP" DADOS="$DADOS" python3 << 'PYEOF'
import json, os, sys
TMP = os.environ['TMP']
DADOS = os.environ['DADOS']
NOW = os.environ['NOW']

def load(name):
    try:
        with open(f"{TMP}/{name}.json", encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

stats = load("stats")
orch = load("orch")
cap = load("cap")
alerts = load("alerts")
fcast = load("fcast")

# Definição de "ativas" alinhada com Vitor 2026-04-29:
# planejamento + aguardando_execucao + em_execucao + pausadas
# (logística pós-obra fica fora; ela é "obra acabou, retirando material")
em_plan = stats.get("projetosEmPlanejamento", 0)
aguardando = stats.get("projetosAguardando", 0)
em_exec = stats.get("projetosEmExecucao", 0)
pausadas = stats.get("obrasPausadas", 0)
ativas = em_plan + aguardando + em_exec + pausadas

current_load = cap.get("currentLoad", {}) or {}
capacity_obj = cap.get("capacity", {}) or {}
active_proj = cap.get("activeProjects", {}) or {}
recom = cap.get("recommendations", {}) or {}

canon = {
    "atualizado_em": NOW,
    "fonte": "planejamento.monofloor.cloud — 5 endpoints REST agregados",
    "totais": {
        "total": stats.get("totalProjetos", 0),
        "ativas": ativas,
        "logistica_coleta": stats.get("logisticaColeta", 0),
        "concluidas": stats.get("obrasConcluidas", 0),
    },
    "por_status": {
        "em_planejamento": em_plan,
        "aguardando_execucao": aguardando,
        "em_execucao": em_exec,
        "pausadas": pausadas,
        "logistica_coleta": stats.get("logisticaColeta", 0),
        "concluidas": stats.get("obrasConcluidas", 0),
    },
    "operacao_viva": {
        "active_journeys": orch.get("activeJourneys", 0),
        "pending_tasks": orch.get("pendingTasks", 0),
        "executing_tasks": orch.get("executingTasks", 0),
        "atividades_pendentes": stats.get("atividadesPendentes", 0),
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
