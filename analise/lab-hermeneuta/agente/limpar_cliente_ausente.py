"""
Limpa flag 'cliente_ausente' do discordancias-v3.json
======================================================

Telegram é canal INTERNO Monofloor. Cliente final fica no WhatsApp
(capturado pelo KIRA). Então 'cliente ausente do Telegram' é design,
não problema · remove dessa fonte de ruído.

Atualiza:
- obras[].flags · remove 'cliente_ausente'
- agregados.flags_recorrentes · remove ou diminui
- agregados.padroes_cross_obras · remove parágrafos sobre o tema
- obras[].score (urgência etc se baseada nessa flag) · não tem hoje, OK
"""

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

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

    DISCORD_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] {DISCORD_PATH}")
    print(f"     Flag 'cliente_ausente' removida de {n_removidas} obra(s)")
    print(f"     Padrões cross-obras: {len(padroes)} → {len(padroes_novos)}")


if __name__ == "__main__":
    main()
