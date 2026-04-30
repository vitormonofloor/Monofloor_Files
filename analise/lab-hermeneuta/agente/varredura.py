"""
Varredura automática · sem IA · custo zero
==========================================

Pipeline pra rodar via Task Scheduler 2x/dia (12h e 18h):

1. Backup do snapshot anterior
2. monitorar.py → puxa msgs novas via Telethon
3. Compara com snapshot anterior · conta msgs novas por obra
4. extrair_timeline.py → atualiza timeline 4 semanas no discordancias-v3.json
5. Marca em cada obra: msgs_novas_desde_veredicto + horas_desde_veredicto

Saída: discordancias-v3.json sempre fresco · log em varredura.log

Uso manual: python agente/varredura.py
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

ROOT = Path(__file__).parent.parent
AGENTE = Path(__file__).parent
TELETHON = AGENTE / "telethon"
DADOS = ROOT / "dados"

SNAPSHOT_PATH = TELETHON / "telegram-snapshot.json"
SNAPSHOT_PREV = TELETHON / "telegram-snapshot-prev.json"
DISCORD_PATH = DADOS / "discordancias-v3.json"
LOG_PATH = AGENTE / "varredura.log"

PYTHON = sys.executable


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(cmd: list, cwd: Path) -> bool:
    """Roda subprocesso · retorna True se exit 0."""
    log(f"  → {' '.join(str(c) for c in cmd)}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env=env)
    if r.returncode != 0:
        log(f"  ERRO (exit {r.returncode}): {r.stderr.strip()[:200]}")
        return False
    return True


def calcular_diff_msgs() -> dict:
    """Retorna {obra_id: qtd_msgs_novas} comparando snapshot atual com prev."""
    if not SNAPSHOT_PREV.exists():
        return {}

    prev = json.loads(SNAPSHOT_PREV.read_text(encoding="utf-8"))
    curr = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    prev_by_id = {o["obra_id"]: o for o in prev.get("obras", [])}
    diff = {}
    for o in curr.get("obras", []):
        oid = o["obra_id"]
        p = prev_by_id.get(oid, {"telegram": {"mensagens": []}})
        p_ids = {m["id"] for m in p.get("telegram", {}).get("mensagens", [])}
        c_msgs = o.get("telegram", {}).get("mensagens", [])
        novas = [m for m in c_msgs if m["id"] not in p_ids]
        diff[oid] = len(novas)
    return diff


def parse_iso(s: str):
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except (ValueError, TypeError):
        return None


def marcar_refresh_status(diff_msgs: dict):
    """Adiciona refresh_status em cada obra: msgs_novas + horas_desde_veredicto."""
    if not DISCORD_PATH.exists():
        log("  AVISO: discordancias-v3.json não existe · pulando marcação")
        return

    data = json.loads(DISCORD_PATH.read_text(encoding="utf-8"))
    veredicto_data = parse_iso(data.get("gerado_em"))
    agora = datetime.now(timezone.utc)
    horas = None
    if veredicto_data:
        horas = round((agora - veredicto_data).total_seconds() / 3600, 1)

    # Acumula msgs_novas_desde_veredicto · soma a varreduras anteriores se já existe
    for o in data.get("obras", []):
        oid = o.get("obra_id")
        novas_agora = diff_msgs.get(oid, 0)
        rs = o.get("refresh_status") or {}
        ja_acumuladas = rs.get("msgs_novas_desde_veredicto", 0)

        # Se gerado_em mudou (rodou novo veredicto), zera contador
        rs_veredicto = rs.get("veredicto_em_no_calculo")
        if rs_veredicto != data.get("gerado_em"):
            ja_acumuladas = 0

        o["refresh_status"] = {
            "ultima_varredura": agora.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "msgs_novas_desde_veredicto": ja_acumuladas + novas_agora,
            "msgs_novas_ultima_varredura": novas_agora,
            "veredicto_em": data.get("gerado_em"),
            "veredicto_em_no_calculo": data.get("gerado_em"),
            "horas_desde_veredicto": horas,
            "stale": (horas or 0) > 24 and (ja_acumuladas + novas_agora) > 0,
        }

    # Metadata global
    data["ultima_varredura"] = agora.strftime("%Y-%m-%dT%H:%M:%SZ")
    data["total_msgs_novas_ultima_varredura"] = sum(diff_msgs.values())

    DISCORD_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    log("=" * 60)
    log("VARREDURA INICIADA")

    # 1. Backup snapshot atual (se existe)
    if SNAPSHOT_PATH.exists():
        shutil.copy2(SNAPSHOT_PATH, SNAPSHOT_PREV)
        log("Backup do snapshot anterior salvo")

    # 2. Puxa msgs novas via Telethon
    log("Rodando monitorar.py...")
    if not run([PYTHON, "monitorar.py", "--limit", "50"], TELETHON):
        log("FALHOU em monitorar.py · abortando varredura")
        sys.exit(1)

    # 3. Calcula diff
    diff = calcular_diff_msgs()
    total = sum(diff.values())
    obras_com_diff = sum(1 for v in diff.values() if v > 0)
    log(f"Diff: {total} msgs novas em {obras_com_diff} obras")
    for oid, n in diff.items():
        if n > 0:
            log(f"  + {n} msgs · {oid[:8]}")

    # 4. Atualiza timeline
    log("Rodando extrair_timeline.py...")
    if not run([PYTHON, "extrair_timeline.py"], AGENTE):
        log("FALHOU em extrair_timeline.py")
        sys.exit(1)

    # 5. Recalcula régua temporal (bucket + marcos SLA)
    log("Rodando aplicar_regua.py...")
    if not run([PYTHON, "aplicar_regua.py"], AGENTE):
        log("FALHOU em aplicar_regua.py")
        sys.exit(1)

    # 6. Recalcula equipe em campo (cruza com cadastro /equipes)
    log("Rodando extrair_equipe.py...")
    if not run([PYTHON, "extrair_equipe.py"], AGENTE):
        log("FALHOU em extrair_equipe.py")
        sys.exit(1)

    # 7. Recalcula cores e tendência
    log("Rodando extrair_cores.py...")
    if not run([PYTHON, "extrair_cores.py"], AGENTE):
        log("FALHOU em extrair_cores.py")
        sys.exit(1)

    # 8. Espelha KIRA WhatsApp summary do detail
    log("Rodando extrair_kira_whatsapp.py...")
    if not run([PYTHON, "extrair_kira_whatsapp.py"], AGENTE):
        log("FALHOU em extrair_kira_whatsapp.py (continua)")

    # 9. Registra KPIs no histórico (pra sparkline / delta semanal)
    log("Rodando registrar_kpis.py...")
    if not run([PYTHON, "registrar_kpis.py"], AGENTE):
        log("FALHOU em registrar_kpis.py (continua)")

    # 10. Marca refresh_status nas obras
    marcar_refresh_status(diff)
    log("refresh_status injetado em cada obra")

    log("VARREDURA OK")
    log("=" * 60)


if __name__ == "__main__":
    main()
