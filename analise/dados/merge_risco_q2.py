"""Merge score_risco + consultor normalizado do timeline_obras.json nos Q2_OBRAS.
Cirurgico: so adiciona/atualiza risco_nivel, risco_valor, alerta_parada, consultor.
Nao mexe em idades, status, nem nada mais."""
import json, sys
from pathlib import Path

DASH = Path(__file__).parent / "dashboard-data.json"
TL = Path(__file__).parent.parent / "lab-hermeneuta" / "dados" / "timeline_obras.json"

dash = json.loads(DASH.read_text(encoding="utf-8"))
tl_data = json.loads(TL.read_text(encoding="utf-8"))

tl_map = {t["obra_id"]: t for t in tl_data["timelines"]}

merged = 0
merged_cons = 0
for obra in dash["Q2_OBRAS"]:
    obra.pop("risco_nivel", None)
    obra.pop("risco_valor", None)
    obra.pop("alerta_parada", None)

    tl = tl_map.get(obra["id"])
    if not tl:
        continue
    sr = tl.get("score_risco")
    if sr:
        obra["risco_nivel"] = sr["nivel"]
        obra["risco_valor"] = sr["valor"]
        merged += 1
    if tl.get("alerta_parada"):
        obra["alerta_parada"] = tl["alerta_parada"]
    if tl.get("consultor"):
        obra["consultor"] = tl["consultor"]
        merged_cons += 1

DASH.write_text(json.dumps(dash, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
sem_cons = sum(1 for o in dash["Q2_OBRAS"] if not o.get("consultor") or o["consultor"] in ("", "[]"))
print(f"Merge risco: {merged}/{len(dash['Q2_OBRAS'])} obras enriquecidas")
print(f"Merge consultor: {merged_cons} normalizados, {sem_cons} sem consultor restantes")
print(f"  snapshot_date mantido: {dash.get('snapshot_date')}")
tops = sorted([o for o in dash["Q2_OBRAS"] if o.get("idade")], key=lambda o: -o["idade"])
print(f"  idade max preservada: {tops[0]['idade']}d ({tops[0]['cliente'][:30]})")
niveis = {}
for o in dash["Q2_OBRAS"]:
    n = o.get("risco_nivel", "sem_score")
    niveis[n] = niveis.get(n, 0) + 1
for k, v in sorted(niveis.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
