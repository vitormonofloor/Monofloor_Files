"""Runner automatico: pipeline --massa + gerar HTML.
Pode ser chamado manualmente ou via Task Scheduler.

Uso:
  python agente/atualizar_timeline.py
"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
LOG_DIR = ROOT / "dados" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def run(cmd, label):
    """Roda comando e retorna (ok, output)."""
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {label}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            [sys.executable] + cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=600,
        )
        output = result.stdout + result.stderr
        print(output)
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {label} excedeu 10 minutos")
        return False, "TIMEOUT"
    except Exception as e:
        print(f"ERRO: {e}")
        return False, str(e)


def main():
    inicio = datetime.now()
    print(f"Timeline Atualizar · {inicio.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Pipeline --massa (fetch + processar + auditoria embutida)
    ok1, out1 = run(["agente/timeline_10obras.py", "--massa"], "Pipeline --massa")

    if not ok1:
        print("\n⚠ Pipeline falhou. HTML nao sera regenerado.")
        log_path = LOG_DIR / f"run_{inicio.strftime('%Y%m%d_%H%M%S')}_ERRO.log"
        log_path.write_text(out1, encoding="utf-8")
        print(f"Log: {log_path}")
        sys.exit(1)

    # 2. Gerar HTML
    ok2, out2 = run(["agente/gerar_html_timelines.py"], "Gerar HTML")

    elapsed = (datetime.now() - inicio).total_seconds()
    status = "OK" if (ok1 and ok2) else "FALHA"

    # Log
    log_name = f"run_{inicio.strftime('%Y%m%d_%H%M%S')}_{status}.log"
    log_path = LOG_DIR / log_name
    log_content = f"Inicio: {inicio}\nDuracao: {elapsed:.1f}s\nStatus: {status}\n\n"
    log_content += "=== PIPELINE ===\n" + out1 + "\n\n=== HTML ===\n" + out2
    log_path.write_text(log_content, encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"[{status}] Concluido em {elapsed:.1f}s · Log: {log_path.name}")
    print(f"{'='*60}")

    # Limpa logs antigos (mantém últimos 30)
    logs = sorted(LOG_DIR.glob("run_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in logs[30:]:
        old.unlink()


if __name__ == "__main__":
    main()
