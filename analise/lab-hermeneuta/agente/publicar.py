"""
Publica versão atual do lab pra repo privado lab-hermeneuta-pub
================================================================

Copia HTML + 3 JSONs essenciais pro repo separado e faz git push.
Cloudflare Pages detecta o commit e rebuilda lab.monofloor.cloud em ~30s.

Roda no FIM de cada varredura (12h e 18h via Task Scheduler).

Falha silenciosa: se git push der erro (rede, conflito, repo não inicializado),
loga aviso mas NÃO aborta a varredura · publicação é best-effort.
"""

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import setup_utf8

setup_utf8()

LAB_LOCAL = Path(__file__).parent.parent  # analise/lab-hermeneuta
PUB_REPO = Path("C:/Users/vitor/lab-hermeneuta-pub")  # repo separado · privado

ARQUIVOS = [
    ("index.html", "public/index.html"),
    ("dados/discordancias-v3.json", "public/dados/discordancias-v3.json"),
    ("dados/historico-kpis.json", "public/dados/historico-kpis.json"),
    ("dados/status.json", "public/dados/status.json"),
]


def main():
    if not PUB_REPO.exists():
        print(f"AVISO: {PUB_REPO} não existe · publicação pulada")
        print("       (esperado nas primeiras rodadas até criar o repo)")
        return 0

    if not (PUB_REPO / ".git").exists():
        print(f"AVISO: {PUB_REPO} não é repo git · `git init` ainda não foi feito · publicação pulada")
        return 0

    # Copia arquivos atualizados
    n_copiados = 0
    n_iguais = 0
    for src_rel, dst_rel in ARQUIVOS:
        src = LAB_LOCAL / src_rel
        dst = PUB_REPO / dst_rel
        if not src.exists():
            print(f"AVISO: {src_rel} não existe local · pulando")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Compara mtime · evita commits vazios
        if dst.exists() and src.stat().st_mtime <= dst.stat().st_mtime:
            n_iguais += 1
            continue
        shutil.copy2(src, dst)
        n_copiados += 1

    print(f"Copiados: {n_copiados} · sem mudança: {n_iguais}")

    if n_copiados == 0:
        print("Nada novo pra publicar")
        return 0

    # Git add + commit + push
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"varredura · {ts}"

    try:
        # Add só os arquivos públicos (não pega .DS_Store etc)
        for _, dst_rel in ARQUIVOS:
            subprocess.run(["git", "add", dst_rel], cwd=str(PUB_REPO), check=False, capture_output=True)

        # Commit (--allow-empty=false default · se nada staged, falha sem ruído)
        r_commit = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=str(PUB_REPO),
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if r_commit.returncode != 0:
            if "nothing to commit" in (r_commit.stdout + r_commit.stderr).lower():
                print("Sem mudanças staged · nada a commitar")
                return 0
            print(f"AVISO: git commit falhou: {r_commit.stderr.strip()[:200]}")
            return 0

        # Pull --rebase pra evitar conflito se outro commit chegou
        subprocess.run(
            ["git", "pull", "--rebase", "--autostash"],
            cwd=str(PUB_REPO), capture_output=True, text=True, encoding="utf-8",
        )

        # Push
        r_push = subprocess.run(
            ["git", "push"],
            cwd=str(PUB_REPO),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        if r_push.returncode != 0:
            print(f"AVISO: git push falhou: {r_push.stderr.strip()[:200]}")
            return 0

        print(f"[OK] Publicado · {msg}")
    except subprocess.TimeoutExpired:
        print("AVISO: git push timeout (60s) · rede lenta? · próxima rodada tenta de novo")
        return 0
    except Exception as e:
        print(f"AVISO: erro inesperado na publicação: {e}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
