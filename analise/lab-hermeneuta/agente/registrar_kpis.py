"""
Registra KPIs da varredura atual em historico-kpis.json
========================================================

Roda no fim de cada varredura (12h/18h). Acumula série temporal pra
gerar sparklines e delta vs período anterior na tela.

Saída: dados/historico-kpis.json
{
  "kpis": [
    {"data": "2026-04-30T17:51Z", "obras": 10, "precisam_atencao": 4, ...},
    ...
  ]
}

Mantém histórico curto (rolling · últimos 200 pontos = ~3 meses 2x/dia).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import write_json_atomic, setup_utf8

setup_utf8()

ROOT = Path(__file__).parent.parent
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"
HISTORICO_PATH = ROOT / "dados" / "historico-kpis.json"

LIMITE_PONTOS = 200


def calcular_kpis(data: dict) -> dict:
    obras = data.get("obras", []) or []
    ag = data.get("agregados", {}) or {}
    flags_rec = ag.get("flags_recorrentes") or []

    def flag_count(nome):
        m = next((f for f in flags_rec if f.get("flag") == nome), None)
        return m.get("ocorrencias", 0) if m else 0

    # Precisam atenção (mesmo cálculo da tela)
    atencao = set()
    for o in obras:
        flags = o.get("flags") or []
        if o.get("veredicto") == "status_desatualizado": atencao.add(o["obra_id"])
        if (o.get("regua") or {}).get("data_inicio_alterada"): atencao.add(o["obra_id"])
        if "detrator_latente" in flags: atencao.add(o["obra_id"])
        if o.get("veredicto") in ("detrator", "abandono"): atencao.add(o["obra_id"])

    # Saúde (mesmo cálculo)
    n_ok, n_atencao, n_crit = 0, 0, 0
    for o in obras:
        flags = o.get("flags") or []
        r = o.get("regua") or {}
        clima = ((o.get("kira_whatsapp") or {}).get("whatsapp") or {}).get("clima_geral", "") or ""
        clima = clima.lower()
        remarc_n = len((r.get("data_inicio_historico") or []))

        eh_crit = ("detrator" in flags or o.get("veredicto") in ("detrator", "abandono")
                   or "risco_tecnico" in flags
                   or "crit" in clima
                   or ("aplicador_indefinido" in flags and r.get("dias_ate_inicio") is not None and r.get("dias_ate_inicio") <= 7)
                   or remarc_n >= 4)
        eh_atencao = (not eh_crit and (
                    o.get("veredicto") == "status_desatualizado"
                    or "detrator_latente" in flags
                    or r.get("data_inicio_alterada")
                    or "consultor_divergente" in flags
                    or "aplicador_indefinido" in flags
                    or "tens" in clima))
        if eh_crit: n_crit += 1
        elif eh_atencao: n_atencao += 1
        else: n_ok += 1

    saude_pct = round(n_ok * 100 / len(obras)) if obras else 0

    return {
        "data": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "obras": len(obras),
        "precisam_atencao": len(atencao),
        "urgencia_alta": sum(1 for o in obras if o.get("urgencia") == "alta"),
        "cliente_em_risco": flag_count("detrator_latente"),
        "datas_remarcadas": sum(1 for o in obras if (o.get("regua") or {}).get("data_inicio_alterada")),
        "saude_pct": saude_pct,
    }


def main():
    if not DISCORD_PATH.exists():
        print(f"ERRO: {DISCORD_PATH} não existe")
        sys.exit(1)

    discord = json.loads(DISCORD_PATH.read_text(encoding="utf-8"))
    novo_ponto = calcular_kpis(discord)

    historico = {"kpis": []}
    if HISTORICO_PATH.exists():
        try:
            historico = json.loads(HISTORICO_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            historico = {"kpis": []}

    pontos = historico.get("kpis") or []

    # Dedup: se o último ponto é da mesma hora (mesmo minuto), substitui em vez de duplicar
    if pontos and pontos[-1].get("data", "")[:13] == novo_ponto["data"][:13]:
        pontos[-1] = novo_ponto
    else:
        pontos.append(novo_ponto)

    # Mantém últimos LIMITE_PONTOS
    if len(pontos) > LIMITE_PONTOS:
        pontos = pontos[-LIMITE_PONTOS:]

    historico["kpis"] = pontos
    write_json_atomic(HISTORICO_PATH, historico)

    print(f"[OK] {HISTORICO_PATH}")
    print(f"     {len(pontos)} pontos no histórico")
    print(f"     último: {novo_ponto}")


if __name__ == "__main__":
    main()
