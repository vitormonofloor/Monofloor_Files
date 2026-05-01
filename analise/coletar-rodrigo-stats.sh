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
# /api/prestadores do cliente (180 cadastrados, 115 ativos = fonte da aba Aplicadores)
fetch "$API_CLI/prestadores?limit=500" "$TMP/prestadores.json"; sleep 1
# /api/escalacao-diaria — quem está escalado em qual obra hoje (lider + membros)
# NOTA 2026-04-30: parâmetro ?date=YYYY-MM-DD é ACEITO mas IGNORADO pelo backend —
# sempre retorna escalação do dia atual. Não dá pra prever obras futuras por esse
# endpoint. "Agenda futura" precisa de outra fonte (ainda não mapeada).
fetch "$API_CLI/escalacao-diaria"      "$TMP/escalacao.json"; sleep 1
# /api/equipes — 6 equipes operacionais (Wiguens, João, Gilmar, Júlio, Egberto, Michael)
fetch "$API_CLI/equipes"               "$TMP/equipes.json"; sleep 1
# Endpoints de operação/capacidade/alertas continuam no planejamento
fetch "$API_PLN/orchestrator/status"   "$TMP/orch.json";     sleep 1
fetch "$API_PLN/analytics/capacity"    "$TMP/cap.json";      sleep 1
fetch "$API_PLN/analytics/alerts"      "$TMP/alerts.json";   sleep 1
fetch "$API_PLN/analytics/weekly-forecast" "$TMP/fcast.json"; sleep 1

# DETAILS das ativas — fonte do whatsappSummary KIRA (NÃO vem no /api/projects!)
# Listing trunca tagKira/whatsappGroupId/whatsappSummary; só /api/projects/{id} popula.
# Baixa em paralelo (até 10 simultâneos) — ~30s pra 230 obras ativas.
mkdir -p "$TMP/details"
echo "  Listando IDs ativas pra fetch detail..."
export TMP_ENV="$TMP"
python3 -c '
import json, os
TMP = os.environ["TMP_ENV"]
ps = json.load(open(TMP + "/projects.json", encoding="utf-8"))
SKIP = {"finalizado","concluido","cancelado"}
ids = [p["id"] for p in ps if isinstance(p, dict) and p.get("status") not in SKIP and p.get("id")]
with open(TMP + "/ids-ativas.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(ids))
print(f"  IDs gerados: {len(ids)}")
'
N_ATIVAS=$(wc -l < "$TMP/ids-ativas.txt" 2>/dev/null || echo 0)
echo "  $N_ATIVAS ativas — baixando details em paralelo..."
# Loop sequencial — xargs/parallel no Git Bash Windows tem bugs de subshell.
# 229 obras × ~0.8s = ~3min. Cabe no refresh 30min.
# NÃO usa -f no curl (schannel renegotiation rompe -f mesmo com 200 OK).
COUNT_OK=0
COUNT_FAIL=0
while IFS= read -r oid; do
  oid=$(echo "$oid" | tr -d '\r\n ')
  [ -z "$oid" ] && continue
  out="$TMP/details/$oid.json"
  curl -s --max-time 15 "$API_CLI/projects/$oid" -o "$out" 2>/dev/null
  if [ -f "$out" ]; then
    first=$(head -c 1 "$out" 2>/dev/null)
    if [ "$first" = "{" ]; then
      COUNT_OK=$((COUNT_OK + 1))
    else
      rm -f "$out"
      COUNT_FAIL=$((COUNT_FAIL + 1))
    fi
  else
    COUNT_FAIL=$((COUNT_FAIL + 1))
  fi
done < "$TMP/ids-ativas.txt"
echo "  $COUNT_OK details OK · $COUNT_FAIL falharam"
N_DET_OK=$(ls "$TMP/details"/*.json 2>/dev/null | wc -l)
echo "  Total details no diretório: $N_DET_OK"

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
prestadores = load("prestadores")  # 180 cadastrados (115 ativos)
escalacao = load("escalacao")  # {obraId: {liderId, membrosIds[]}} de hoje
equipes_raw = load("equipes")  # 6 equipes operacionais com líder + membros
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

# ============== APLICADORES (aba Aplicadores do painel) ==============
# Painel mostra "115 prestadores ativos" + breakdown por cargo.
# Mapping cargo→label do painel: LIDER→Encarregado · APLICADOR_3→Líder de Campo
# (resto bate direto). Usar labels do painel pra UI fica natural pro Vitor.
CARGO_LABEL = {
    "LIDER": "Encarregado",
    "APLICADOR_3": "Líder de Campo",
    "APLICADOR_2": "Aplicador 2",
    "APLICADOR_1": "Aplicador 1",
    "PREPARADOR": "Preparador",
    "AJUDANTE": "Ajudante",
}
prest_list = prestadores if isinstance(prestadores, list) else []
prest_ativos = [p for p in prest_list if isinstance(p, dict) and p.get("ativo") == 1]
prest_inativos = [p for p in prest_list if isinstance(p, dict) and p.get("ativo") != 1]
por_cargo = Counter(p.get("funcao") or "?" for p in prest_ativos)
por_cargo_label = { CARGO_LABEL.get(k, k): v for k, v in por_cargo.items() }

# Escalação hoje: dict {obraId: {liderId, membrosIds[]}}
esc = escalacao if isinstance(escalacao, dict) else {}
em_campo_ids = set()
appearance = {}  # id -> [obraId, ...]
for obra_id, eq in esc.items():
    if not isinstance(eq, dict): continue
    lid = eq.get("liderId")
    if lid:
        em_campo_ids.add(lid)
        appearance.setdefault(lid, []).append(obra_id)
    for m in (eq.get("membrosIds") or []):
        if m:
            em_campo_ids.add(m)
            appearance.setdefault(m, []).append(obra_id)

# Lookup de nomes/cargos
prest_by_id = { p.get("id"): p for p in prest_list if isinstance(p, dict) and p.get("id") }
proj_by_id = { p.get("id"): p for p in projects if isinstance(p, dict) and p.get("id") }

# Conflitos: pessoas escaladas em 2+ obras hoje (qualquer cargo)
conflitos_detalhe = []
for pid, obra_ids in appearance.items():
    obras_unicas = list(dict.fromkeys(obra_ids))  # mantém ordem, remove dups
    if len(obras_unicas) >= 2:
        p = prest_by_id.get(pid, {})
        cargo_raw = p.get("funcao") or "?"
        conflitos_detalhe.append({
            "id": pid,
            "nome": p.get("nome") or pid[:8],
            "cargo": CARGO_LABEL.get(cargo_raw, cargo_raw),
            "qtd_obras": len(obras_unicas),
            "obras": [
                {
                    "id": oid,
                    "cliente": (proj_by_id.get(oid, {}) or {}).get("clienteNome") or oid[:8],
                }
                for oid in obras_unicas
            ],
        })
conflitos_detalhe.sort(key=lambda x: (-x["qtd_obras"], x["nome"]))

# Ociosos: prestadores ativos que NÃO aparecem em em_campo_ids hoje
ociosos_detalhe = []
for p in prest_ativos:
    if p.get("id") not in em_campo_ids:
        cargo_raw = p.get("funcao") or "?"
        ociosos_detalhe.append({
            "id": p.get("id"),
            "nome": p.get("nome") or "?",
            "cargo": CARGO_LABEL.get(cargo_raw, cargo_raw),
        })
ociosos_detalhe.sort(key=lambda x: (x["cargo"], x["nome"]))

# Em campo hoje (lista resumida pra eventual drill-down de "Em campo")
em_campo_detalhe = []
for pid in em_campo_ids:
    p = prest_by_id.get(pid, {})
    cargo_raw = p.get("funcao") or "?"
    em_campo_detalhe.append({
        "id": pid,
        "nome": p.get("nome") or pid[:8],
        "cargo": CARGO_LABEL.get(cargo_raw, cargo_raw),
        "qtd_obras": len(set(appearance.get(pid, []))),
    })
em_campo_detalhe.sort(key=lambda x: (-x["qtd_obras"], x["nome"]))

canon["aplicadores"] = {
    "total_cadastrados": len(prest_list),
    "ativos": len(prest_ativos),
    "inativos": len(prest_inativos),
    "por_cargo": dict(por_cargo_label),
    "obras_com_equipe_hoje": len(esc),
    "pessoas_em_campo_hoje": len(em_campo_ids),
    "em_2_ou_mais_obras_hoje": len(conflitos_detalhe),
    "ociosos_hoje": max(0, len(prest_ativos) - len(em_campo_ids)),
    "conflitos_detalhe": conflitos_detalhe,
    "ociosos_detalhe": ociosos_detalhe,
    "em_campo_detalhe": em_campo_detalhe,
    "fonte": "cliente.monofloor.cloud/api/prestadores + /api/escalacao-diaria",
}

# ============== LUANA × WESLEY (consultoras dominantes) ==============
# Calculado a partir de /api/projects fresh — sem isso o card do Q3 mostra
# números congelados de quando o PESADO rodou (1×/dia).
SKIP_STATUS = {"finalizado", "concluido", "cancelado"}
ativas_obras = [p for p in projects if isinstance(p, dict) and p.get("status") not in SKIP_STATUS]
total_ativas = len(ativas_obras)

# Idade real vem do painel-temporal (cruzamento com snapshot Pipefy).
# createdAt do /api/projects é a data de migração no painel do Rodrigo, não a real.
idade_por_id = {}
try:
    with open(f"{DADOS}/painel-temporal.json", encoding="utf-8") as f:
        for o in json.load(f):
            if o.get("id") and o.get("idade_dias") is not None:
                idade_por_id[o["id"]] = o["idade_dias"]
except Exception:
    pass

def idade_de(p):
    pid = p.get("id")
    if pid and pid in idade_por_id:
        return idade_por_id[pid]
    cd = p.get("createdAt") or p.get("created_at")
    d = parse_date(cd)
    if not d: return None
    return (hoje - d).days

def stats_consultor(nome_alvo):
    obras = [p for p in ativas_obras if (p.get("consultorNome") or "").strip().upper().startswith(nome_alvo)]
    idades = [idade_de(p) for p in obras]
    idades_validas = sorted(i for i in idades if i is not None)
    return {
        "n": len(obras),
        "mediana": idades_validas[len(idades_validas)//2] if idades_validas else 0,
        "n180": sum(1 for i in idades_validas if i >= 180),
        "n270": sum(1 for i in idades_validas if i >= 270),
        "zumbi": sum(1 for p in obras if (p.get("faseAtual") or "").strip().upper() == "CLIENTE FINALIZADO" and p.get("status") != "reparo"),
        "reparo": sum(1 for p in obras if p.get("status") in ("reparo", "marcas_rolo_cera")),
        "pausadas": sum(1 for p in obras if p.get("status") == "pausado"),
    }

luana = stats_consultor("LUANA")
wesley = stats_consultor("WESLEY")
n_180_total = sum(1 for p in ativas_obras for i in [idade_de(p)] if i is not None and i >= 180)

# ============== EQUIPES OPERACIONAIS ==============
# 6 equipes oficiais (Wiguens, João, Gilmar, Júlio, Egberto, Michael).
# Pra cada equipe: ativos, escalados hoje, util_pct, obras_hoje.
# Cruza /api/equipes + /api/escalacao-diaria + /api/projects.
#
# BUG DE CADASTRO descoberto 2026-04-30: 3 equipes têm liderId apontando pro
# prestador ANTIGO/INATIVO (Gilmar 74bd45→inativo / Egberto 0f0222→inativo /
# João Victor era inativo). O líder REAL ativo tem outro UUID com mesmo nome.
# Solução: pra cada equipe, identificar o líder ativo via match de nome.

def resolver_lider_real(eq_dict):
    """Retorna (lider_id_efetivo, lider_nome_efetivo, foi_remapeado)."""
    cadastro_id = eq_dict.get("liderId")
    lider = eq_dict.get("lider") or {}
    cadastro_nome = lider.get("nome") or ""
    cadastro_ativo = lider.get("ativo") in (True, 1)
    if cadastro_ativo:
        return cadastro_id, cadastro_nome, False
    # Cadastro inativo: tentar achar prestador ATIVO com mesmo primeiro nome
    if cadastro_nome:
        primeiro = cadastro_nome.strip().split()[0].lower() if cadastro_nome.strip() else ""
        candidatos = [
            p for p in prest_ativos
            if (p.get("nome") or "").strip().lower().startswith(primeiro + " ")
            and (p.get("funcao") or "").startswith(("LIDER", "APLICADOR_3"))
        ]
        if candidatos:
            c = candidatos[0]
            return c.get("id"), c.get("nome"), True
    return cadastro_id, cadastro_nome, False

def proj_label(oid):
    p = proj_by_id.get(oid, {}) or {}
    return {
        "id": oid,
        "cliente": p.get("clienteNome") or oid[:8],
        "cidade": p.get("projetoCidade") or "",
        "fase": p.get("faseAtual") or "",
        "status": p.get("status") or "",
    }

equipes_detalhe = []
eq_list = equipes_raw if isinstance(equipes_raw, list) else []
for eq in eq_list:
    if not isinstance(eq, dict): continue
    membros_all = eq.get("membros") or []
    # Filtro ativo: tolera bool true e int 1 (algumas equipes vêm sem ativo true mesmo)
    membros_ativos = [m for m in membros_all if m and (m.get("ativo") is True or m.get("ativo") == 1)]
    n_ativos = len(membros_ativos)
    n_total = len(membros_all)

    lider_cadastro_id = eq.get("liderId")
    lider_cadastro_nome = (eq.get("lider") or {}).get("nome") or "?"
    lider_real_id, lider_real_nome, foi_remapeado = resolver_lider_real(eq)
    # Lista de UUIDs aceitos como "líder dessa equipe" (cadastro + real)
    lider_ids_aceitos = {lider_cadastro_id, lider_real_id} - {None}

    # Escalados hoje: membros (ativos OU não — escalação é fonte da verdade) + ambos os UUIDs do líder
    membros_ids_set = set((m.get("id") for m in membros_all if m and m.get("id")))
    membros_ids_set |= lider_ids_aceitos
    escalados_ids = membros_ids_set & em_campo_ids
    n_escalados = len(escalados_ids)

    # Obras hoje da equipe = obras onde algum UUID do líder está como liderId OU
    # obras onde algum membro da equipe está escalado
    obras_lideradas = []
    obras_membros = []
    for obra_id, eqd in esc.items():
        if not isinstance(eqd, dict): continue
        if eqd.get("liderId") in lider_ids_aceitos:
            obras_lideradas.append(obra_id)
        elif any(m in membros_ids_set for m in (eqd.get("membrosIds") or [])):
            obras_membros.append(obra_id)
    obras_hoje_ids = list(dict.fromkeys(obras_lideradas + obras_membros))

    util_pct = round(n_escalados / max(1, n_ativos) * 100, 1) if n_ativos else 0
    estado = "fantasma" if n_ativos == 0 else ("parcial" if n_ativos < 5 else "saudavel")

    equipes_detalhe.append({
        "id": (eq.get("nome") or "").lower().replace(" ", "-").replace("equipe-", ""),
        "nome": eq.get("nome") or "?",
        "lider": lider_real_nome,
        "lider_id": lider_real_id,
        "lider_cadastro_id": lider_cadastro_id,
        "lider_cadastro_nome": lider_cadastro_nome,
        "lider_remapeado": foi_remapeado,
        "ativos": n_ativos,
        "total_cadastrados": n_total,
        "escalados_hoje": n_escalados,
        "util_pct": util_pct,
        "obras_hoje": len(obras_hoje_ids),
        "obras_lideradas": [proj_label(o) for o in obras_lideradas],
        "obras_membros": [proj_label(o) for o in obras_membros if o not in obras_lideradas],
        "estado": estado,
    })

canon["equipes"] = equipes_detalhe

# ============== HISTÓRICO DIÁRIO DE APLICADORES ==============
# Acumula por dia: quem foi escalado, em quantas obras, quem ficou ocioso.
# Permite ranking 7d/30d (mais escalado, mais ocioso, mais carga).
# Cresce 1 entry/dia. Só substitui hoje se já existir (idempotente em mesmo dia).
hist_aplic_path = f"{DADOS}/historico-aplicadores.json"
try:
    with open(hist_aplic_path, encoding="utf-8") as f:
        hist_aplic = json.load(f)
except Exception:
    hist_aplic = []

today_str = hoje.isoformat()

# Snapshot do dia: por pessoa ativa, qtd_obras de hoje
snapshot_dia = {
    "date": today_str,
    "atualizado_em": NOW,
    "total_ativos": len(prest_ativos),
    "total_escalados": len(em_campo_ids),
    "total_ociosos": max(0, len(prest_ativos) - len(em_campo_ids)),
    "por_pessoa": {},
}
for p in prest_ativos:
    pid = p.get("id")
    if not pid: continue
    obras_pessoa = appearance.get(pid, [])
    snapshot_dia["por_pessoa"][pid] = {
        "nome": p.get("nome") or pid[:8],
        "cargo": CARGO_LABEL.get(p.get("funcao"), p.get("funcao") or "?"),
        "obras_hoje": len(set(obras_pessoa)),
        "escalado": pid in em_campo_ids,
    }

# Substitui entry de hoje se já existir
hist_aplic = [h for h in hist_aplic if h.get("date") != today_str]
hist_aplic.append(snapshot_dia)
# Mantém últimos 90 dias
hist_aplic = sorted(hist_aplic, key=lambda x: x.get("date", ""))[-90:]

with open(hist_aplic_path, "w", encoding="utf-8") as f:
    json.dump(hist_aplic, f, ensure_ascii=False, indent=2)

# Ranking 7d (com base no histórico). Se só tem 1 dia, mostra hoje.
ultimos_7 = [h for h in hist_aplic if h.get("date") and (hoje - datetime.strptime(h["date"], "%Y-%m-%d").date()).days <= 6]
agg_7d = {}  # pid -> {nome, cargo, dias_escalado, total_obras, dias_ocioso}
for h in ultimos_7:
    for pid, info in (h.get("por_pessoa") or {}).items():
        a = agg_7d.setdefault(pid, {"nome": info["nome"], "cargo": info["cargo"], "dias_escalado": 0, "dias_ocioso": 0, "total_obras": 0})
        if info.get("escalado"):
            a["dias_escalado"] += 1
            a["total_obras"] += info.get("obras_hoje") or 0
        else:
            a["dias_ocioso"] += 1

ranking = sorted(agg_7d.items(), key=lambda x: -x[1]["total_obras"])
ranking_carga = [{"id": pid, **a} for pid, a in ranking[:10]]
ranking_escalado = [{"id": pid, **a} for pid, a in sorted(agg_7d.items(), key=lambda x: -x[1]["dias_escalado"])[:10]]
ranking_ocioso = [{"id": pid, **a} for pid, a in sorted(agg_7d.items(), key=lambda x: (-x[1]["dias_ocioso"], x[1]["nome"]))[:10] if a["dias_ocioso"] > 0]

# ============== KIRA WHATSAPP — fonte fresh por detail ==============
# whatsappSummary só vem em /api/projects/{id} (não no listing). Pra cada ativa,
# extrai clima, totalMensagens, dias_desde_ultimo_evento, alertas. Classifica:
#   silenciosa = sem evento há ≥30 dias (ou whatsappGroupId ausente + idade > 60d)
#   clima_critico = clima Crítico/Tenso
#   saudavel = clima Positivo/Neutro + msgs recentes
import os, glob
RETRAB_K = {"reparo", "marcas_rolo_cera"}
op_obras = []
op_clima_dist = {"Positivo": 0, "Neutro": 0, "Tenso": 0, "Crítico": 0, "?": 0}
op_kira_mais_recente = None
det_dir = f"{TMP}/details"

def parse_iso_kira(s):
    if not s: return None
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None

now_utc = datetime.now(timezone.utc)
for fn in os.listdir(det_dir) if os.path.isdir(det_dir) else []:
    if not fn.endswith(".json"): continue
    try:
        d = json.load(open(f"{det_dir}/{fn}", encoding="utf-8-sig"))
    except Exception:
        continue
    pid = d.get("id")
    if not pid or d.get("status") in ("finalizado", "concluido", "cancelado"):
        continue

    pm = d.get("pendenciaManual") or {}
    ws = pm.get("whatsappSummary") or {}
    clima = ws.get("climaGeral")
    if clima not in op_clima_dist: clima = "?"
    op_clima_dist[clima] += 1

    # tagKiraUpdatedAt: sinal mais recente do KIRA (atualizado quando pipeline rodou)
    tag_dt = parse_iso_kira(d.get("tagKiraUpdatedAt"))
    if tag_dt and (op_kira_mais_recente is None or tag_dt > op_kira_mais_recente):
        op_kira_mais_recente = tag_dt

    # geradoEm do whatsappSummary: quando o KIRA leu/analisou a conversa pela última vez
    summary_dt = parse_iso_kira(ws.get("geradoEm"))
    dias_desde_resumo = (now_utc - summary_dt).days if summary_dt else None

    # Eventos: lista de eventos no whatsappSummary (cada um tem 'data')
    eventos = ws.get("eventos") or []
    ultima_data = None
    for ev in eventos:
        ed = parse_iso_kira(ev.get("data") if isinstance(ev, dict) else None)
        if ed and (ultima_data is None or ed > ultima_data):
            ultima_data = ed
    dias_sem_evento = (now_utc - ultima_data).days if ultima_data else None

    total_msgs = ws.get("totalMensagens") or 0
    alertas = ws.get("alertas") or []
    n_alertas = len(alertas) if isinstance(alertas, list) else 0
    has_grupo = bool(d.get("whatsappGroupId"))

    # Classificação operacional — usa CLIMA do KIRA + idade da leitura:
    #   atencao   = climaGeral Tenso/Crítico E leitura recente (≤60d)
    #   saudavel  = climaGeral Positivo/Neutro
    #   sem_kira  = climaGeral vazio OU leitura antiga (>60d) — KIRA não tá mais acompanhando
    #   retrabalho = status reparo/marcas (pós-entrega, fora do fluxo)
    eh_retrabalho = d.get("status") in RETRAB_K
    is_saudavel = clima in ("Positivo", "Neutro")
    leitura_velha = (dias_desde_resumo is not None and dias_desde_resumo > 60)
    is_atencao = clima in ("Tenso", "Crítico") and not leitura_velha
    is_sem_kira = (clima == "?") or (clima in ("Tenso", "Crítico") and leitura_velha)

    # Texto KIRA pra mostrar inline na lista (resumo do que está crítico)
    alertas_lista = alertas if isinstance(alertas, list) else []
    pendencias = ws.get("pendencias") or []
    pendencias_lista = pendencias if isinstance(pendencias, list) else []
    resumo_exec = (ws.get("resumoExecutivo") or "").strip()
    clima_desc = (ws.get("climaDescricao") or "").strip()
    periodo = (ws.get("periodo") or "").strip()
    tempo_resp = (ws.get("tempoResposta") or "").strip()

    # Timeline: classifica cada evento como bom/neutro/critico por palavras-chave
    # (heurística — KIRA não dá score; texto é livre. ~5-10% erro tolerado)
    KW_CRITICO = ["atras", "atraso", "descumpr", "crítico", "crítica", "critico", "critica",
                  "falha", "lesado", "reclama", "cobr", "recus", "rejeit",
                  "sem resposta", "pendente", "urgent", "extrapola", "risco",
                  "errad", "errou", "problema", "queixa", "ameaç", "ruptura",
                  "rupture", "veemen", "intercorr", "agrava", "insatisf",
                  "frustr", "discord", "contesta", "questiona", "questionou",
                  "não cumpri", "nao cumpri", "não foi", "nao foi", "ausente",
                  "falt", "cancela", "cancelou", "remarc", "adiar", "adiou",
                  "atrasou", "perdeu", "perda", "danific", "danific", "vazam",
                  "infiltra", "trinc", "manch", "defeit", "tom errado",
                  "cor errada", "diverge", "diverg"]
    KW_BOM = ["conclu", "aprovou", "confirmou", "finaliz", "entregue", "resolv",
              "satisfeito", "concord", "agendou com sucesso", "executou"]

    def classificar_evento(txt):
        t = txt.lower()
        # Bom só se NÃO tiver palavra-chave ruim no contexto
        tem_ruim = any(k in t for k in KW_CRITICO)
        tem_bom = any(k in t for k in KW_BOM)
        if tem_ruim:
            return "critico"
        if tem_bom:
            return "bom"
        return "neutro"

    def extrair_iso(data_str, ref_dt):
        # "DD/MM" → "YYYY-MM-DD" (ano = ano do geradoEm; fallback hoje)
        if not data_str: return None
        import re
        m = re.match(r"^(\d{1,2})/(\d{1,2})", data_str.strip())
        if not m: return None
        dia, mes = m.group(1), m.group(2)
        ano = ref_dt.year if ref_dt else now_utc.year
        try:
            return f"{ano}-{int(mes):02d}-{int(dia):02d}"
        except Exception:
            return None

    eventos_estruturados = []
    import re as _re
    DATA_PATTERN = _re.compile(r"^\s*(\d{1,2}/\d{1,2})\s*[\(\s\-:]+(.+)$")
    for ev in (eventos or []):
        if not isinstance(ev, str): continue
        s = ev.strip()
        # KIRA varia: "DD/MM - txt", "DD/MM: txt", "DD/MM (qualquer): txt", "DD/MM txt"
        m = DATA_PATTERN.match(s)
        if m:
            data_str = m.group(1)
            texto = m.group(2).strip().lstrip(":-) ").strip()
        else:
            data_str, texto = "", s
        iso_ev = extrair_iso(data_str, summary_dt)
        eventos_estruturados.append({
            "data": data_str,
            "iso": iso_ev,
            "texto": texto[:280],
            "classe": classificar_evento(s),  # classifica string inteira (mais robusto)
        })

    op_obras.append({
        "id": pid,
        "cliente": (d.get("clienteNome") or "").strip(),
        "consultor": (d.get("consultorNome") or "").strip(),
        "cidade": (d.get("projetoCidade") or "").strip(),
        "status": d.get("status"),
        "fase": d.get("faseAtual"),
        "m2": float(d.get("projetoMetragem") or 0),
        "clima": clima,
        "total_msgs": total_msgs,
        "n_alertas": n_alertas,
        "tag_kira_dias": (now_utc - tag_dt).days if tag_dt else None,
        "dias_desde_resumo": dias_desde_resumo,
        "dias_sem_evento": dias_sem_evento,
        "tem_grupo": has_grupo,
        "is_retrabalho": eh_retrabalho,
        "is_atencao": is_atencao,
        "is_saudavel": is_saudavel,
        "is_sem_kira": is_sem_kira,
        "alertas": alertas_lista[:5],
        "pendencias": pendencias_lista[:5],
        "resumo_exec": resumo_exec[:600],
        "clima_desc": clima_desc[:300],
        "periodo": periodo,
        "tempo_resp": tempo_resp,
        "eventos": eventos_estruturados,
    })

# Agregação (excluindo retrabalho — segue regra Q1/Q4)
op_fluxo = [o for o in op_obras if not o["is_retrabalho"]]
n_total = len(op_fluxo)
n_atencao = sum(1 for o in op_fluxo if o["is_atencao"])
n_saudavel = sum(1 for o in op_fluxo if o["is_saudavel"])
n_sem_kira = sum(1 for o in op_fluxo if o["is_sem_kira"])
# % saudável usa apenas as obras com KIRA ativo (denominador honesto)
n_com_kira = n_saudavel + n_atencao
pct_saudavel = round(n_saudavel / max(1, n_com_kira) * 100, 1)

# Lista das obras em ATENÇÃO ordenadas por gravidade (clima × frescor):
# Crítico recente (≤7d) → Tenso recente → Crítico médio → Tenso médio → ...
def gravidade_atencao(o):
    s = 1000 if o["clima"] == "Crítico" else 500
    dr = o.get("dias_desde_resumo")
    if dr is None:
        s -= 200
    elif dr <= 7:
        s += 100  # leitura recente: prioridade alta
    elif dr <= 30:
        s += 30   # leitura média
    else:
        s -= 50   # leitura > 30d: empurra pra baixo
    s += (o.get("n_alertas") or 0) * 3
    return -s
obras_atencao = sorted(
    [o for o in op_fluxo if o["is_atencao"]],
    key=gravidade_atencao
)

canon["operacional_kira"] = {
    "kira_atualizado_em": op_kira_mais_recente.isoformat() if op_kira_mais_recente else None,
    "total_fluxo": n_total,
    "com_kira": n_com_kira,
    "saudavel": n_saudavel,
    "saudavel_pct_no_monitorado": pct_saudavel,  # % das que o KIRA acompanha
    "atencao": n_atencao,
    "sem_kira": n_sem_kira,
    "clima_dist": op_clima_dist,
    "obras_atencao": [
        {
            "id": o["id"],
            "cliente": o["cliente"],
            "consultor": (o["consultor"].split(" ")[0] if o["consultor"] else "—"),
            "consultor_full": o["consultor"],
            "cidade": o["cidade"],
            "fase": o["fase"],
            "status": o["status"],
            "clima": o["clima"],
            "n_alertas": o["n_alertas"],
            "dias_sem_evento": o["dias_sem_evento"],
            "dias_desde_resumo": o["dias_desde_resumo"],
            "alertas": o["alertas"],
            "pendencias": o["pendencias"],
            "resumo_exec": o["resumo_exec"],
            "clima_desc": o["clima_desc"],
            "periodo": o["periodo"],
            "tempo_resp": o["tempo_resp"],
            "total_msgs": o["total_msgs"],
            "eventos": o["eventos"],
        } for o in obras_atencao
    ],
    "obras_sem_kira": [
        {
            "id": o["id"],
            "cliente": o["cliente"],
            "consultor": (o["consultor"].split(" ")[0] if o["consultor"] else "—"),
            "cidade": o["cidade"],
            "fase": o["fase"],
            "tem_grupo": o["tem_grupo"],
        } for o in op_fluxo if o["is_sem_kira"]
    ],
    "fonte": "/api/projects/{id} pendenciaManual.whatsappSummary (cada detail fresh, ~3min coleta)",
}

canon["historico_aplicadores"] = {
    "dias_acumulados": len(hist_aplic),
    "janela_dias": len(ultimos_7),
    "top_carga_7d": ranking_carga,
    "top_escalado_7d": ranking_escalado,
    "top_ocioso_7d": ranking_ocioso,
    "fonte": "historico-aplicadores.json (acumulado a cada refresh)",
}

canon["lw"] = {
    "luana": luana,
    "wesley": wesley,
    "total_ativas": total_ativas,
    "n_180_total": n_180_total,
    "concentracao_pct": round((luana["n"] + wesley["n"]) / max(1, total_ativas) * 100, 1),
    "concentracao_180_pct": round((luana["n180"] + wesley["n180"]) / max(1, n_180_total) * 100, 1) if n_180_total else 0,
    "fonte": "cliente.monofloor.cloud/api/projects (campo consultorNome)",
}

out = f"{DADOS}/rodrigo-stats.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(canon, f, ensure_ascii=False, indent=2)
print(f"  rodrigo-stats.json: total={total} ativas={ativas} em_exec={em_exec_count} ({round(m2_em_execucao)}m²) prox15d={canon['proximos']['15d']['obras']} prox30d={canon['proximos']['30d']['obras']} prox60d={canon['proximos']['60d']['obras']}")
print(f"  aplicadores: {canon['aplicadores']['ativos']} ativos · {canon['aplicadores']['pessoas_em_campo_hoje']} em campo · {canon['aplicadores']['ociosos_hoje']} ociosos")
print(f"  Luana={luana['n']} obras · Wesley={wesley['n']} obras · concentração={canon['lw']['concentracao_pct']}%")
print(f"  KIRA: {n_total} no fluxo · {n_saudavel} saudáveis · {n_atencao} em atenção · {n_sem_kira} sem KIRA · {pct_saudavel}% saudável (sobre as {n_com_kira} monitoradas)")
PYEOF

rm -rf "$TMP"
echo "[done] Coletor Rodrigo concluído."
