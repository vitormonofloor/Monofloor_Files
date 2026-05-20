"""Snapshot semanal da Qualidade Monofloor.

Salva copia datada do analise-unificada.json e calcula delta vs snapshot anterior.
Habilita: radar de trajetoria, tendencia temporal, relatorio semanal.

Uso:
  python analise/dados/snapshot_semanal.py          # salva snapshot de hoje
  python analise/dados/snapshot_semanal.py --delta   # salva + mostra delta vs anterior
  python analise/dados/snapshot_semanal.py --force   # sobrescreve se ja existe

Pre-requisito: rodar pipeline_unificado.py antes (gera analise-unificada.json).
"""
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent
UNIFICADA = BASE / "analise-unificada.json"
SNAP_DIR = BASE / "snapshots-unificados"


def snapshot_mais_recente(excluir=None):
    """Retorna path do snapshot mais recente, excluindo um especifico."""
    if not SNAP_DIR.exists():
        return None
    snaps = sorted(SNAP_DIR.glob("*.json"), reverse=True)
    for s in snaps:
        if excluir and s.name == excluir:
            continue
        return s
    return None


def calcular_delta(atual, anterior):
    """Compara indicadores entre 2 snapshots. Retorna dict de deltas."""
    ia = atual["indicadores"]
    ip = anterior["indicadores"]
    deltas = {}

    # radar
    for eixo in ["tempo", "fluxo", "qualidade", "risco"]:
        va = ia["radar"][eixo]["pct"]
        vp = ip["radar"][eixo]["pct"]
        deltas[f"radar_{eixo}"] = {
            "atual": va,
            "anterior": vp,
            "delta": round(va - vp, 1),
        }

    # portfolio
    for campo in ["total", "idade_media"]:
        va = ia["portfolio"][campo]
        vp = ip["portfolio"][campo]
        deltas[f"portfolio_{campo}"] = {
            "atual": va,
            "anterior": vp,
            "delta": round(va - vp, 1) if isinstance(va, (int, float)) else 0,
        }

    # gargalo
    deltas["gargalo"] = {
        "atual": f"{ia['gargalo']['fase']} ({ia['gargalo']['n_obras']})",
        "anterior": f"{ip['gargalo']['fase']} ({ip['gargalo']['n_obras']})",
        "delta": ia["gargalo"]["n_obras"] - ip["gargalo"]["n_obras"],
    }

    # retrabalho
    deltas["retrabalho_total"] = {
        "atual": ia["retrabalho"]["total"],
        "anterior": ip["retrabalho"]["total"],
        "delta": ia["retrabalho"]["total"] - ip["retrabalho"]["total"],
    }

    # alertas
    deltas["alertas_total"] = {
        "atual": ia["alertas"]["total"],
        "anterior": ip["alertas"]["total"],
        "delta": ia["alertas"]["total"] - ip["alertas"]["total"],
    }

    # risco critico+alto
    dist_a = ia["distribuicao_risco"]
    dist_p = ip["distribuicao_risco"]
    crit_a = dist_a.get("critico", 0) + dist_a.get("alto", 0)
    crit_p = dist_p.get("critico", 0) + dist_p.get("alto", 0)
    deltas["risco_critico_alto"] = {
        "atual": crit_a,
        "anterior": crit_p,
        "delta": crit_a - crit_p,
    }

    # consultor: delta retrabalho por consultor
    cons_a = ia.get("consultor", {})
    cons_p = ip.get("consultor", {})
    todos = set(list(cons_a.keys()) + list(cons_p.keys()))
    deltas_cons = {}
    for c in todos:
        ra = cons_a.get(c, {}).get("retrabalho", 0)
        rp = cons_p.get(c, {}).get("retrabalho", 0)
        if ra != rp:
            deltas_cons[c] = {"atual": ra, "anterior": rp, "delta": ra - rp}
    if deltas_cons:
        deltas["retrabalho_por_consultor"] = deltas_cons

    return deltas


def sinal_delta(d):
    if d > 0:
        return f"+{d}"
    return str(d)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    force = "--force" in sys.argv
    show_delta = "--delta" in sys.argv

    if not UNIFICADA.exists():
        print("ERRO: analise-unificada.json nao existe. Rode pipeline_unificado.py primeiro.")
        sys.exit(1)

    SNAP_DIR.mkdir(exist_ok=True)

    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    destino = SNAP_DIR / f"{hoje}.json"

    if destino.exists() and not force:
        print(f"Snapshot {hoje} ja existe. Use --force pra sobrescrever.")
        sys.exit(0)

    shutil.copy2(UNIFICADA, destino)
    print(f"Snapshot salvo: {destino.name} ({destino.stat().st_size // 1024} KB)")

    # listar snapshots
    snaps = sorted(SNAP_DIR.glob("*.json"))
    print(f"Total snapshots: {len(snaps)}")
    for s in snaps:
        print(f"  {s.name}")

    # delta vs anterior
    anterior_path = snapshot_mais_recente(excluir=f"{hoje}.json")
    if anterior_path and show_delta:
        print(f"\n--- DELTA vs {anterior_path.name} ---")
        atual = json.loads(destino.read_text(encoding="utf-8"))
        anterior = json.loads(anterior_path.read_text(encoding="utf-8"))

        deltas = calcular_delta(atual, anterior)

        for k, v in deltas.items():
            if k == "retrabalho_por_consultor":
                print(f"  Retrabalho por consultor:")
                for c, dv in v.items():
                    print(f"    {c}: {dv['anterior']} -> {dv['atual']} ({sinal_delta(dv['delta'])})")
                continue
            d = v["delta"]
            if d == 0:
                continue
            print(f"  {k}: {v['anterior']} -> {v['atual']} ({sinal_delta(d)})")

        # salvar delta junto
        delta_path = SNAP_DIR / f"{hoje}-delta.json"
        delta_out = {
            "data": hoje,
            "comparado_com": anterior_path.name.replace(".json", ""),
            "deltas": deltas,
        }
        delta_path.write_text(
            json.dumps(delta_out, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\nDelta salvo: {delta_path.name}")
    elif not anterior_path:
        print("\nPrimeiro snapshot — sem delta pra comparar.")
    else:
        print(f"\nSnapshot anterior: {anterior_path.name} (use --delta pra comparar)")


if __name__ == "__main__":
    main()
