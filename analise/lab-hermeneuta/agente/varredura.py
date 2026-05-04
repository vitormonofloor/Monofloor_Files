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

sys.path.insert(0, str(Path(__file__).parent))
from _util import write_json_atomic, setup_utf8, fazer_backup, marcar_step_falho, limpar_erros_pipeline

setup_utf8()

ROOT = Path(__file__).parent.parent
AGENTE = Path(__file__).parent
TELETHON = AGENTE / "telethon"
DADOS = ROOT / "dados"

SNAPSHOT_PATH = TELETHON / "telegram-snapshot.json"
SNAPSHOT_PREV = TELETHON / "telegram-snapshot-prev.json"
DISCORD_PATH = DADOS / "discordancias-v3.json"
LOG_PATH = AGENTE / "varredura.log"
LOCK_PATH = AGENTE / ".varredura.lock"
LOCK_MAX_IDADE_SEG = 30 * 60  # 30 minutos · uma varredura típica leva ~10s

PYTHON = sys.executable


def _pid_vivo(pid: int) -> bool:
    """True se PID existe e está rodando · False se zombie/morto."""
    try:
        # No Windows e POSIX, kill(pid, 0) testa sem afetar o processo
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False
    except PermissionError:
        # Processo existe mas sem permissão · considera vivo (caso raro)
        return True


def adquirir_lock():
    """
    Lock anti-concorrência · 3 níveis de check:
    1. Sem lock = adquire e segue
    2. Lock com PID vivo = aborta (outra varredura rodando)
    3. Lock com PID morto OU TTL expirado = considera abandonado, reusa
    """
    if LOCK_PATH.exists():
        try:
            pid_str = LOCK_PATH.read_text(encoding="utf-8").strip()
            pid_anterior = int(pid_str) if pid_str.isdigit() else 0
        except (OSError, ValueError):
            pid_anterior = 0

        idade = datetime.now().timestamp() - LOCK_PATH.stat().st_mtime
        pid_vivo = pid_anterior > 0 and _pid_vivo(pid_anterior)

        if pid_vivo and idade < LOCK_MAX_IDADE_SEG:
            log(f"ABORT: outra varredura rodando · PID {pid_anterior} vivo, lock há {int(idade)}s")
            sys.exit(0)

        # Lock fantasma (PID morto OU TTL expirado)
        razao = "PID morto" if pid_anterior > 0 and not pid_vivo else f"TTL expirado ({int(idade)}s)"
        log(f"AVISO: lock fantasma ({razao}) · removendo e prosseguindo")
        LOCK_PATH.unlink(missing_ok=True)

    LOCK_PATH.write_text(str(os.getpid()), encoding="utf-8")
    log(f"Lock adquirido · PID {os.getpid()}")


def liberar_lock():
    """Remove lock no fim (chamado em finally)."""
    LOCK_PATH.unlink(missing_ok=True)


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
        log(f"  ERRO (exit {r.returncode}): {r.stderr.strip()[:2000]}")
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

        # Se gerado_em mudou (rodou novo veredicto IA), zera contador acumulado
        if rs.get("veredicto_em") != data.get("gerado_em"):
            ja_acumuladas = 0

        o["refresh_status"] = {
            "ultima_varredura": agora.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "msgs_novas_desde_veredicto": ja_acumuladas + novas_agora,
            "msgs_novas_ultima_varredura": novas_agora,
            "veredicto_em": data.get("gerado_em"),
            "horas_desde_veredicto": horas,
            "stale": (horas or 0) > 24 and (ja_acumuladas + novas_agora) > 0,
        }

    # Metadata global
    data["ultima_varredura"] = agora.strftime("%Y-%m-%dT%H:%M:%SZ")

    write_json_atomic(DISCORD_PATH, data)


def _executar_pipeline():
    """Pipeline propriamente dito · separado pra envolver em try/finally do lock."""
    # 0. Backup do JSON principal antes de QUALQUER write (rolling 14 dias)
    bkp = fazer_backup(DISCORD_PATH, pasta_backups=DADOS / "backups", manter=14)
    if bkp:
        log(f"Backup salvo · {bkp.name}")
    # Reseta erros do pipeline (varredura limpa começa sem erros antigos)
    limpar_erros_pipeline()

    # 1. Backup snapshot Telegram pra calcular diff
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
        log("FALHOU em extrair_kira_whatsapp.py (continua · marcado em pipeline-errors.json)")
        marcar_step_falho("extrair_kira_whatsapp", "exit não-zero")

    # 9. Aplica overrides de consultor inferido (Repullo, Paula, Maria Heydi, Mayara)
    # Crítico: sem isso os campos consultor_formal/consultor_inferido somem após IA regerar
    log("Rodando inferir_consultor.py...")
    if not run([PYTHON, "inferir_consultor.py"], AGENTE):
        log("FALHOU em inferir_consultor.py (continua · marcado em pipeline-errors.json)")
        marcar_step_falho("inferir_consultor", "exit não-zero")

    # 10. Sanitiza JSON · remove flag cliente_ausente + campos mortos detectados pela auditoria
    log("Rodando sanitizar_json.py...")
    if not run([PYTHON, "sanitizar_json.py"], AGENTE):
        log("FALHOU em sanitizar_json.py (continua · marcado em pipeline-errors.json)")
        marcar_step_falho("sanitizar_json", "exit não-zero")

    # 11. Registra KPIs no histórico (pra sparkline / delta semanal)
    log("Rodando registrar_kpis.py...")
    if not run([PYTHON, "registrar_kpis.py"], AGENTE):
        log("FALHOU em registrar_kpis.py (continua · marcado em pipeline-errors.json)")
        marcar_step_falho("registrar_kpis", "exit não-zero")

    # 12. Marca refresh_status nas obras
    marcar_refresh_status(diff)
    log("refresh_status injetado em cada obra")

    # 13. Sentinela · valida saúde do pipeline e gera dados/status.json
    log("Rodando sentinela.py...")
    if not run([PYTHON, "sentinela.py"], AGENTE):
        log("FALHOU em sentinela.py (continua · marcado em pipeline-errors.json)")
        marcar_step_falho("sentinela", "exit não-zero")

    # 14. Publica no repo lab-hermeneuta-pub (Cloudflare Pages · lab.monofloor.cloud)
    log("Rodando publicar.py...")
    if not run([PYTHON, "publicar.py"], AGENTE):
        log("FALHOU em publicar.py (continua · marcado em pipeline-errors.json)")
        marcar_step_falho("publicar", "exit não-zero · deploy NÃO chegou ao CF")

    log("VARREDURA OK")
    log("=" * 60)


def main():
    log("=" * 60)
    log("VARREDURA INICIADA")
    adquirir_lock()
    try:
        _executar_pipeline()
    finally:
        liberar_lock()


if __name__ == "__main__":
    main()
