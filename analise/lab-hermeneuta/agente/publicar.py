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
from _util import setup_utf8, marcar_step_falho

setup_utf8()

LAB_LOCAL = Path(__file__).parent.parent  # analise/lab-hermeneuta
PUB_REPO = Path("C:/Users/vitor/lab-hermeneuta-pub")  # repo separado · privado

ARQUIVOS = [
    ("index.html", "public/index.html"),
    ("jornada.html", "public/jornada.html"),
    ("dados/discordancias-v3.json", "public/dados/discordancias-v3.json"),
    ("dados/jornadas.json", "public/dados/jornadas.json"),
    ("dados/historico-kpis.json", "public/dados/historico-kpis.json"),
    ("dados/status.json", "public/dados/status.json"),
]


def _garantir_pub_repo_saudavel() -> bool:
    """Detecta rebase travado / detached HEAD no pub repo e faz a faxina ANTES de pull/push.
    Aprendizado 2026-05-28: o pub repo entrava em estado caótico quando o pull --rebase --autostash
    conflitava em arquivos auto-gerados (jornadas.json, _jornadas/*.md), deixando detached HEAD
    e rebase travado. Isso quebrava o publicar.py em loop e corrompia o JSON publicado (tela
    branca no site). Retorna True se fez faxina (caller deve forçar cópia ignorando mtime).
    Playbook em [[feedback-deploy-cf-workers]]."""
    def _run(cmd):
        return subprocess.run(cmd, cwd=str(PUB_REPO), capture_output=True, text=True,
                              encoding="utf-8", errors="replace")

    # fetch silencioso pra origin/main estar atualizado
    _run(["git", "fetch", "origin"])

    # detecta sintomas
    rebase_em_andamento = ((PUB_REPO / ".git" / "rebase-merge").exists() or
                           (PUB_REPO / ".git" / "rebase-apply").exists())
    detached = _run(["git", "symbolic-ref", "-q", "HEAD"]).returncode != 0

    if not rebase_em_andamento and not detached:
        return False  # estado saudável · segue o fluxo normal

    motivos = []
    if rebase_em_andamento:
        motivos.append("rebase em andamento")
    if detached:
        motivos.append("detached HEAD")
    print(f"[publicar.py] pub repo em estado inconsistente ({' + '.join(motivos)}) · faxina automática...")

    # 1. aborta rebase, limpa stashes
    _run(["git", "rebase", "--abort"])
    _run(["git", "stash", "clear"])
    # 2. volta pro branch main e sincroniza com origin (descarta commits locais — são "varreduras"
    #    de dado regenerável, sem trabalho humano)
    _run(["git", "checkout", "main"])
    _run(["git", "reset", "--hard", "origin/main"])

    print("[publicar.py] faxina concluída · main resetado pro origin/main · recopia do lab a seguir")
    return True


def main():
    if not PUB_REPO.exists():
        print(f"AVISO: {PUB_REPO} não existe · publicação pulada")
        print("       (esperado nas primeiras rodadas até criar o repo)")
        return 0

    if not (PUB_REPO / ".git").exists():
        print(f"AVISO: {PUB_REPO} não é repo git · `git init` ainda não foi feito · publicação pulada")
        return 0

    # Faxina automática se o pub repo estiver bagunçado (rebase travado/detached HEAD)
    faxina_feita = _garantir_pub_repo_saudavel()

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
        # Compara mtime · evita commits vazios. Se houve faxina, o reset reverteu dst pra
        # versão do origin (pode ser antiga) — FORÇA a recopia do lab pra garantir integridade.
        if not faxina_feita and dst.exists() and src.stat().st_mtime <= dst.stat().st_mtime:
            n_iguais += 1
            continue
        shutil.copy2(src, dst)
        n_copiados += 1

    print(f"Copiados: {n_copiados} · sem mudança: {n_iguais}")

    if n_copiados == 0:
        print("Nada novo pra publicar via git · forçando wrangler deploy mesmo assim (garantia de sync)")
        deploy_ok = _wrangler_deploy()
        if not deploy_ok:
            marcar_step_falho(
                "publicar/wrangler_deploy",
                "wrangler deploy falhou (sem mudanças git, mas tentamos sync)"
            )
            return 1
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
            saida = (r_commit.stdout + r_commit.stderr).lower()
            if "nothing to commit" in saida or "nothing added to commit" in saida:
                # Nada novo no git, mas ainda assim pode ter mudança no public/ que
                # o CF não pegou. Continua pra wrangler deploy garantir sync.
                print("Sem mudanças staged · pulando push, indo direto pro deploy")
                deploy_ok = _wrangler_deploy()
                if not deploy_ok:
                    marcar_step_falho(
                        "publicar/wrangler_deploy",
                        "wrangler deploy falhou após git no-op",
                    )
                    return 1
                return 0
            err = r_commit.stderr.strip()[:200]
            print(f"AVISO: git commit falhou: {err}")
            marcar_step_falho("publicar/commit", f"commit falhou: {err}")
            return 1

        # Pull --rebase pra evitar conflito se outro commit chegou
        r_pull = subprocess.run(
            ["git", "pull", "--rebase", "--autostash"],
            cwd=str(PUB_REPO), capture_output=True, text=True, encoding="utf-8",
        )
        if r_pull.returncode != 0:
            err = r_pull.stderr.strip()[:200]
            print(f"AVISO: git pull --rebase falhou: {err}")
            marcar_step_falho("publicar/pull", f"pull --rebase falhou: {err}")
            # Não aborta · push pode ainda funcionar dependendo do erro

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
            err = r_push.stderr.strip()[:200]
            print(f"AVISO: git push falhou: {err}")
            marcar_step_falho("publicar/push", f"push falhou · CF NÃO atualizado: {err}")
            return 1

        # Validação extra: confere que HEAD local == origin/main
        r_status = subprocess.run(
            ["git", "status", "-sb"],
            cwd=str(PUB_REPO), capture_output=True, text=True, encoding="utf-8",
        )
        if r_status.returncode == 0 and ("ahead" in r_status.stdout or "behind" in r_status.stdout):
            print(f"AVISO: após push, HEAD ainda divergente: {r_status.stdout.strip()[:200]}")
            marcar_step_falho("publicar/sync_check", f"divergência após push: {r_status.stdout.strip()[:200]}")

        print(f"[OK] Git push concluído · {msg}")
    except subprocess.TimeoutExpired:
        print("AVISO: git push timeout (60s) · rede lenta? · próxima rodada tenta de novo")
        marcar_step_falho("publicar/timeout", "git push estourou timeout 60s")
        return 1
    except Exception as e:
        print(f"AVISO: erro inesperado na publicação: {e}")
        marcar_step_falho("publicar/exception", str(e)[:200])
        return 1

    # ============================================================
    # CRÍTICO · DESCOBERTO 2026-05-04: o auto-deploy CF Workers via
    # GitHub NÃO sincroniza assets de public/. Sem `wrangler deploy`
    # explícito, o Worker continua servindo HTML/JSON antigos.
    # ============================================================
    deploy_ok = _wrangler_deploy()
    if not deploy_ok:
        marcar_step_falho(
            "publicar/wrangler_deploy",
            "wrangler deploy falhou · CF NÃO atualizado mesmo com git push OK"
        )
        return 1

    print(f"[OK] Publicado + deployado · {msg}")
    return 0


def _wrangler_deploy() -> bool:
    """
    Roda `wrangler deploy` no PUB_REPO. Retorna True se OK.

    Wrangler precisa estar instalado e autenticado (`wrangler login` 1x).
    No Windows, busca npx.cmd em locais conhecidos.
    """
    import os
    # Garante que C:\Program Files\nodejs está no PATH do subprocess
    # (caso Python tenha sido iniciado antes da instalação do Node)
    nodejs_paths = [r"C:\Program Files\nodejs", r"C:\Program Files (x86)\nodejs"]
    env = os.environ.copy()
    path_atual = env.get("PATH", "")
    for p in nodejs_paths:
        if Path(p).exists() and p not in path_atual:
            env["PATH"] = p + os.pathsep + path_atual
            path_atual = env["PATH"]

    # CRÍTICO · DESCOBERTO 2026-05-27: em ambiente não-interativo (cron/Task Scheduler)
    # o XDG_CONFIG_HOME não é herdado, então o wrangler não acha o cache OAuth
    # (`<APPDATA>/xdg.config/.wrangler/config`) e aborta pedindo CLOUDFLARE_API_TOKEN.
    # Aponta explicitamente pro cache se ele existir e a var não estiver setada.
    if not env.get("XDG_CONFIG_HOME"):
        appdata = env.get("APPDATA") or os.path.expandvars(r"%APPDATA%")
        if appdata:
            xdg_candidato = Path(appdata) / "xdg.config"
            if (xdg_candidato / ".wrangler" / "config").exists():
                env["XDG_CONFIG_HOME"] = str(xdg_candidato)
                print(f"XDG_CONFIG_HOME apontado pro cache wrangler: {xdg_candidato}")

    # Acha wrangler · prioridade: PATH > C:\Program Files\nodejs\npx.cmd
    cmds_a_testar = [
        ["wrangler", "deploy"],
        [r"C:\Program Files\nodejs\npx.cmd", "wrangler", "deploy"],
        [r"C:\Program Files\nodejs\npm.cmd", "exec", "wrangler", "deploy"],
        ["npx", "wrangler", "deploy"],
    ]

    for cmd in cmds_a_testar:
        try:
            print(f"Rodando {' '.join(cmd[:2])} ...")
            r = subprocess.run(
                cmd,
                cwd=str(PUB_REPO),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
            )
            if r.returncode == 0:
                # Sucesso · extrai info útil do output
                out = (r.stdout or "") + (r.stderr or "")
                # Procura linha "Uploaded N of N assets" ou "Deployed orion-pub"
                for linha in out.splitlines():
                    s = linha.strip()
                    if "Success" in s or "Uploaded" in s or "Deployed" in s or "Version ID" in s:
                        print(f"  {s[:150]}")
                return True
            else:
                err_short = (r.stderr or r.stdout or "")[:300]
                # Se for "command not found" tipo erro, tenta próximo
                if "command not found" in err_short.lower() or "não é reconhecido" in err_short.lower():
                    continue
                # Erro real do wrangler · não tenta outros
                print(f"AVISO: wrangler deploy falhou (rc={r.returncode}): {err_short}")
                return False
        except FileNotFoundError:
            continue  # tenta próximo path
        except subprocess.TimeoutExpired:
            print("AVISO: wrangler deploy timeout (180s)")
            return False
        except Exception as e:
            print(f"AVISO: erro inesperado em wrangler deploy: {e}")
            return False

    print("AVISO: wrangler não encontrado · rode `npm install -g wrangler` + `wrangler login`")
    return False


if __name__ == "__main__":
    sys.exit(main())
