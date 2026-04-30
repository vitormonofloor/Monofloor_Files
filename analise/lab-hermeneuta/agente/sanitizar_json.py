"""
Limpa flags + campos mortos do discordancias-v3.json
=====================================================

(1) Telegram é canal INTERNO Monofloor. Cliente final fica no WhatsApp
    (capturado pelo KIRA). Então 'cliente ausente do Telegram' é design,
    não problema · remove dessa fonte de ruído:
    - obras[].flags · remove 'cliente_ausente'
    - agregados.flags_recorrentes · remove
    - agregados.padroes_cross_obras · remove parágrafos sobre o tema

(2) Campos mortos detectados pela auditoria · escritos por scripts mas
    nunca lidos pela tela. Ocupam espaço sem agregar valor:
    - obras[].evidencia_principal (gerado pelo HERMENEUTA · não consumido)
    - obras[].secretario_concordou (idem)
    - top-level: regua_aplicada_em, regua_buckets, total_msgs_novas_ultima_varredura
    - cores_agregado: por_bucket, top_geral
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import write_json_atomic, setup_utf8

setup_utf8()

ROOT = Path(__file__).parent.parent
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"


def main():
    if not DISCORD_PATH.exists():
        print(f"ERRO: {DISCORD_PATH} não existe")
        sys.exit(1)

    data = json.loads(DISCORD_PATH.read_text(encoding="utf-8"))

    # 1. Remove flag de cada obra
    n_removidas = 0
    for o in data.get("obras", []):
        flags = o.get("flags") or []
        if "cliente_ausente" in flags:
            flags.remove("cliente_ausente")
            o["flags"] = flags
            n_removidas += 1

    # 2. Remove de flags_recorrentes
    ag = data.setdefault("agregados", {})
    fr = ag.get("flags_recorrentes") or []
    fr = [f for f in fr if f.get("flag") != "cliente_ausente"]
    ag["flags_recorrentes"] = fr

    # 3. Remove padrão sobre cliente ausente
    padroes = ag.get("padroes_cross_obras") or []
    padroes_novos = [
        p for p in padroes
        if not re.search(r"cliente.*ausente|cliente.*final.*aus|cliente final.*n[aã]o.*post", p, re.IGNORECASE)
    ]
    ag["padroes_cross_obras"] = padroes_novos

    # 4. Remove campos mortos (auditoria detectou: escritos mas nunca lidos)
    n_evid = 0
    for o in data.get("obras", []):
        if o.pop("evidencia_principal", None) is not None:
            n_evid += 1
        o.pop("secretario_concordou", None)
    n_top = 0
    for k in ["regua_aplicada_em", "regua_buckets", "total_msgs_novas_ultima_varredura"]:
        if data.pop(k, None) is not None:
            n_top += 1
    cores_ag = data.get("cores_agregado") or {}
    n_cores = 0
    for k in ["por_bucket", "top_geral"]:
        if cores_ag.pop(k, None) is not None:
            n_cores += 1
    # Remove veredicto_em_no_calculo (interno antigo · agora usamos só veredicto_em)
    n_rs = 0
    for o in data.get("obras", []):
        rs = o.get("refresh_status")
        if isinstance(rs, dict) and rs.pop("veredicto_em_no_calculo", None) is not None:
            n_rs += 1

    write_json_atomic(DISCORD_PATH, data)

    print(f"[OK] {DISCORD_PATH}")
    print(f"     Flag 'cliente_ausente' removida de {n_removidas} obra(s)")
    print(f"     Padrões cross-obras: {len(padroes)} → {len(padroes_novos)}")
    print(f"     Campos mortos removidos: evidencia_principal × {n_evid} obras · top-level × {n_top} · cores_agregado × {n_cores} · refresh_status × {n_rs}")


if __name__ == "__main__":
    main()
