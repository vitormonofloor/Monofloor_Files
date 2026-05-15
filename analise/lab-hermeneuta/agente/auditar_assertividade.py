"""Audita assertividade das jornadas de abril/2026 — 10 critérios."""
import json, sys, io
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ARQUIVO = "dados/jornadas.json"
MES = "2026-04"

CRITERIOS = [
    "status",
    "classificacao",
    "consultor",
    "lider",
    "metragem",
    "tempo_total",
    "produto",
    "andamento_cruzado",
    "status_x_fase",
    "friccao",
]

def auditar(obra):
    r = {}
    cross = obra.get("resumo_cross", {})

    r["status"] = bool(obra.get("status"))
    r["classificacao"] = obra.get("classificacao") not in (None, "desconhecido")
    r["consultor"] = bool(cross.get("consultor"))
    r["lider"] = bool(cross.get("lider_campo"))
    r["metragem"] = isinstance(obra.get("metragem"), (int, float)) and obra["metragem"] > 0
    r["tempo_total"] = isinstance(obra.get("tempo_total_dias"), (int, float)) and obra["tempo_total_dias"] > 0
    r["produto"] = bool(obra.get("produtos")) and len(obra["produtos"]) > 0

    and_cruz = obra.get("andamento_cruzado", {})
    resumo = and_cruz.get("resumo", {})
    r["andamento_cruzado"] = (resumo.get("confirmado", 0) + resumo.get("detectado_sem_painel", 0)) > 0

    # classificar_obra já usa fase como override, então classificação absorve a discrepância
    classif = obra.get("classificacao", "")
    fase = (obra.get("fase_atual_painel") or "").upper()
    st = (obra.get("status") or "").lower()
    if ("FINALIZADO" in fase or "CONCLU" in fase) and st in (
        "em_execucao", "planejamento", "aguardando_execucao", "contrato",
    ):
        # OK se classificar_obra absorveu (retornou entrega_*)
        r["status_x_fase"] = classif.startswith("entrega_")
    else:
        r["status_x_fase"] = True

    r["friccao"] = obra.get("friccao", {}).get("nivel") is not None

    return r

def main():
    with open(ARQUIVO, encoding="utf-8") as f:
        dados = json.load(f)

    def data_inicio_obra(o):
        return o.get("data_exec_confirmada") or o.get("data_exec_prevista") or o.get("data_criacao_painel")

    def obra_no_periodo(o):
        d = data_inicio_obra(o)
        if not d:
            return False
        return d[:7] == MES

    obras = [o for o in dados.get("obras", []) if obra_no_periodo(o)]

    print(f"Obras no período {MES}: {len(obras)}\n")

    totais = {c: 0 for c in CRITERIOS}
    falhas_detalhe = {c: [] for c in CRITERIOS}

    for o in obras:
        r = auditar(o)
        for c in CRITERIOS:
            if r.get(c):
                totais[c] += 1
            else:
                falhas_detalhe[c].append(o.get("cliente", "?"))

    n = len(obras)
    print(f"{'CRITÉRIO':<25} {'OK':>4} / {n:<4}  {'%':>6}")
    print("-" * 50)
    score_total = 0
    for c in CRITERIOS:
        pct = totais[c] / n * 100 if n else 0
        score_total += pct
        flag = " ✓" if pct == 100 else ""
        print(f"  {c:<23} {totais[c]:>4} / {n:<4}  {pct:>5.1f}%{flag}")

    media = score_total / len(CRITERIOS)
    print(f"\n{'ASSERTIVIDADE GERAL':>25}: {media:.1f}%")

    # Critérios que controlamos vs externos
    ctrl = ["status", "classificacao", "metragem", "tempo_total", "produto", "friccao"]
    ext = ["consultor", "lider", "andamento_cruzado", "status_x_fase"]
    pct_ctrl = sum(totais[c] / n * 100 for c in ctrl) / len(ctrl) if n else 0
    pct_ext = sum(totais[c] / n * 100 for c in ext) / len(ext) if n else 0
    print(f"  Campos controlados:   {pct_ctrl:.1f}%")
    print(f"  Campos externos:      {pct_ext:.1f}%")

    # Detalhe das falhas
    print(f"\n{'='*50}")
    print("FALHAS POR CRITÉRIO")
    print(f"{'='*50}")
    for c in CRITERIOS:
        if falhas_detalhe[c]:
            print(f"\n  {c} ({len(falhas_detalhe[c])} falhas):")
            for nome in falhas_detalhe[c][:10]:
                print(f"    - {nome}")
            if len(falhas_detalhe[c]) > 10:
                print(f"    ... +{len(falhas_detalhe[c]) - 10} mais")

if __name__ == "__main__":
    main()
