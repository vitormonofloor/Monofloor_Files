"""
Sentinela · equipe de prevenção e risco
========================================

Roda APÓS cada varredura · faz N validações de saúde · gera dados/status.json.

A tela lê esse JSON e mostra badge discreto no canto:
- 🟢 verde · tudo OK
- 🟡 âmbar · há warnings (não bloqueia uso, mas vale conferir)
- 🔴 vermelho · há problemas críticos (sinaliza que precisa atenção urgente)

Cada check retorna {nome, status: ok|warn|crit, detalhe, sugestao}.

Custo zero · roda local em ~1s.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import write_json_atomic, setup_utf8, validar_discord, now_utc

setup_utf8()

ROOT = Path(__file__).parent.parent
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"
SNAPSHOT_PATH = ROOT / "agente" / "telethon" / "telegram-snapshot.json"
HISTORICO_KPI = ROOT / "dados" / "historico-kpis.json"
BACKUPS_DIR = ROOT / "dados" / "backups"
LOG_PATH = ROOT / "agente" / "varredura.log"
LOCK_PATH = ROOT / "agente" / ".varredura.lock"
STATUS_PATH = ROOT / "dados" / "status.json"


def parse_iso(s):
    if not s: return None
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None


# ============================================================
# Cada check é uma função que retorna dict com {nome, status, detalhe, sugestao}
# Status: ok | warn | crit
# ============================================================

def check_schema_discord(data):
    nome = "Schema do JSON principal"
    if not data:
        return {"nome": nome, "status": "crit", "detalhe": "discordancias-v3.json não carregou", "sugestao": "Restaurar de dados/backups/"}
    problemas = validar_discord(data)
    if not problemas:
        return {"nome": nome, "status": "ok", "detalhe": f"{len(data.get('obras', []))} obras válidas"}
    return {
        "nome": nome,
        "status": "crit",
        "detalhe": "; ".join(problemas[:3]) + (f" (+{len(problemas)-3} outros)" if len(problemas) > 3 else ""),
        "sugestao": "Restaurar JSON do backup mais recente",
    }


def check_obras_completas(data):
    nome = "Completude das obras"
    obras = data.get("obras", []) or []
    if not obras:
        return {"nome": nome, "status": "crit", "detalhe": "0 obras no JSON", "sugestao": "Rodar pipeline IA"}
    incompletas = []
    for o in obras:
        faltam = []
        for c in ("painel", "telegram", "veredicto", "regua", "cores", "kira_whatsapp", "equipe_em_campo"):
            if c not in o:
                faltam.append(c)
        if faltam:
            incompletas.append((o.get("cliente", "?")[:25], faltam))
    if not incompletas:
        return {"nome": nome, "status": "ok", "detalhe": f"{len(obras)} obras com todos campos"}
    if len(incompletas) <= 2:
        return {"nome": nome, "status": "warn", "detalhe": f"{len(incompletas)} obras com campos faltando: {incompletas[0][0]}", "sugestao": "Rodar varredura completa"}
    return {"nome": nome, "status": "crit", "detalhe": f"{len(incompletas)}/{len(obras)} obras com campos faltando", "sugestao": "Rodar pipeline IA"}


def check_telegram_session(snapshot):
    nome = "Sessão Telegram"
    if not snapshot:
        return {"nome": nome, "status": "crit", "detalhe": "telegram-snapshot.json não existe", "sugestao": "Rodar monitorar.py manualmente · pode ser sessão expirada"}
    obras_snap = snapshot.get("obras", []) or []
    com_erro = sum(1 for o in obras_snap if o.get("telegram", {}).get("erro"))
    if com_erro == 0:
        return {"nome": nome, "status": "ok", "detalhe": f"{len(obras_snap)} obras coletadas"}
    pct = com_erro / max(len(obras_snap), 1)
    if pct >= 0.30:
        return {"nome": nome, "status": "crit", "detalhe": f"{com_erro}/{len(obras_snap)} obras com erro Telegram (≥30%)", "sugestao": "Sessão Telegram pode ter expirado · refazer login"}
    return {"nome": nome, "status": "warn", "detalhe": f"{com_erro} obra(s) com erro Telegram", "sugestao": "Investigar grupos com erro"}


def check_freshness_varredura(data):
    nome = "Frescor da varredura"
    ultima = parse_iso(data.get("ultima_varredura") or data.get("gerado_em"))
    if not ultima:
        return {"nome": nome, "status": "warn", "detalhe": "sem timestamp de varredura", "sugestao": "Rodar varredura.py"}
    horas = (now_utc() - ultima).total_seconds() / 3600
    if horas < 8:
        return {"nome": nome, "status": "ok", "detalhe": f"última varredura há {round(horas, 1)}h"}
    if horas < 24:
        return {"nome": nome, "status": "warn", "detalhe": f"varredura há {round(horas, 1)}h (sem 12h/18h hoje)", "sugestao": "Verificar Task Scheduler"}
    return {"nome": nome, "status": "crit", "detalhe": f"varredura há {round(horas, 1)}h", "sugestao": "Task Scheduler parou · rodar varredura.py manualmente"}


def check_kira_freshness(data):
    nome = "KIRA WhatsApp"
    obras = data.get("obras", []) or []
    com_kira = [o for o in obras if (o.get("kira_whatsapp") or {}).get("whatsapp")]
    if not com_kira:
        return {"nome": nome, "status": "warn", "detalhe": "nenhuma obra tem dados do KIRA", "sugestao": "Verificar refresh.sh do dashboard principal"}
    # Pega tag mais recente entre as obras (sinal de KIRA ativo)
    tags_dias = [(o.get("kira_whatsapp") or {}).get("tag_dias_atras") for o in com_kira]
    tags_dias = [d for d in tags_dias if d is not None]
    if not tags_dias:
        return {"nome": nome, "status": "warn", "detalhe": "sem tag_kira atualizada", "sugestao": "KIRA pode estar parado · checar refresh.sh"}
    minimo = min(tags_dias)
    if minimo <= 7:
        return {"nome": nome, "status": "ok", "detalhe": f"tag KIRA mais recente há {minimo}d"}
    if minimo <= 21:
        return {"nome": nome, "status": "warn", "detalhe": f"tag KIRA mais recente há {minimo}d (>1 semana)", "sugestao": "Verificar se KIRA está rodando no dashboard principal"}
    return {"nome": nome, "status": "crit", "detalhe": f"tag KIRA mais recente há {minimo}d", "sugestao": "KIRA parado há tempo · checar refresh.sh + jobs do dashboard"}


def check_lock_orfao():
    nome = "Lock de execução"
    if not LOCK_PATH.exists():
        return {"nome": nome, "status": "ok", "detalhe": "sem lock pendente"}
    try:
        idade = datetime.now().timestamp() - LOCK_PATH.stat().st_mtime
        pid = int(LOCK_PATH.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return {"nome": nome, "status": "warn", "detalhe": "lock corrompido", "sugestao": "Apagar agente/.varredura.lock"}
    try:
        os.kill(pid, 0)
        if idade < 60:
            return {"nome": nome, "status": "ok", "detalhe": f"varredura em curso · PID {pid}"}
        return {"nome": nome, "status": "warn", "detalhe": f"varredura há {int(idade)}s · PID {pid} ainda vivo", "sugestao": "Aguardar ou matar processo"}
    except (OSError, ProcessLookupError):
        return {"nome": nome, "status": "warn", "detalhe": f"lock fantasma · PID {pid} morto", "sugestao": "Próxima varredura limpa automaticamente"}


def check_backups():
    nome = "Backups disponíveis"
    if not BACKUPS_DIR.exists():
        return {"nome": nome, "status": "warn", "detalhe": "pasta de backups não existe ainda", "sugestao": "1ª varredura cria"}
    bkps = [p for p in BACKUPS_DIR.iterdir() if p.is_file() and p.suffix == ".json"]
    if not bkps:
        return {"nome": nome, "status": "warn", "detalhe": "0 backups · sem segurança", "sugestao": "Rodar varredura"}
    mais_recente = max(bkps, key=lambda p: p.stat().st_mtime)
    idade_h = (datetime.now().timestamp() - mais_recente.stat().st_mtime) / 3600
    if idade_h <= 12:
        return {"nome": nome, "status": "ok", "detalhe": f"{len(bkps)} backups · mais recente {round(idade_h, 1)}h"}
    if idade_h <= 36:
        return {"nome": nome, "status": "warn", "detalhe": f"{len(bkps)} backups · último há {round(idade_h, 1)}h"}
    return {"nome": nome, "status": "warn", "detalhe": f"backup mais recente há {round(idade_h, 1)}h", "sugestao": "Pipeline talvez não tenha rodado"}


def check_drift_obras(data):
    """
    Detecta REGRESSÃO no número de obras (perda silenciosa = sinal de pipeline quebrado).

    Lógica: usa máximo recente como baseline (expansão consciente é absorvida em 1 varredura).
    Só alerta quando a contagem CAI vs o pico recente.
    Crescimento NUNCA é crit (geralmente é piloto expandindo).
    """
    nome = "Drift de quantidade de obras"
    obras = data.get("obras", []) or []
    atual = len(obras)
    if not HISTORICO_KPI.exists():
        return {"nome": nome, "status": "ok", "detalhe": f"{atual} obras · sem histórico ainda"}
    try:
        h = json.loads(HISTORICO_KPI.read_text(encoding="utf-8"))
        pontos = h.get("kpis", []) or []
    except Exception:
        return {"nome": nome, "status": "warn", "detalhe": "histórico-kpis ilegível"}
    if len(pontos) < 2:
        return {"nome": nome, "status": "ok", "detalhe": f"{atual} obras · histórico curto"}

    # Baseline = MÁXIMO dos últimos 6 pontos (absorve expansão imediatamente)
    recentes = pontos[-6:]
    if not recentes:
        return {"nome": nome, "status": "ok", "detalhe": "sem amostras suficientes"}
    baseline = max(p.get("obras", 0) for p in recentes)
    if baseline == 0:
        return {"nome": nome, "status": "ok"}

    # Crescimento ou estável · sempre OK (expansão = sinal positivo)
    if atual >= baseline:
        if atual > baseline:
            return {"nome": nome, "status": "ok", "detalhe": f"{atual} obras · expansão (+{atual-baseline} vs pico recente {baseline})"}
        return {"nome": nome, "status": "ok", "detalhe": f"{atual} obras · estável vs pico recente"}

    # Regressão (atual < baseline) · alerta proporcional à perda
    perda = baseline - atual
    perda_pct = perda / baseline
    if perda_pct < 0.10:
        return {"nome": nome, "status": "ok", "detalhe": f"{atual} obras · variação dentro do normal (-{perda} de {baseline})"}
    if perda_pct < 0.30:
        return {"nome": nome, "status": "warn", "detalhe": f"{atual} obras · perda de {perda} ({round(perda_pct*100)}%) vs pico {baseline}", "sugestao": "Investigar obras que sumiram"}
    return {"nome": nome, "status": "crit", "detalhe": f"{atual} obras · REGRESSÃO grave -{perda} ({round(perda_pct*100)}%) vs pico {baseline}", "sugestao": "Pipeline pode estar quebrado · investigar URGENTE"}


def check_pipeline_errors_flag():
    """Lê dados/pipeline-errors.json (gerado por varredura.py se algum step falha)."""
    nome = "Erros de pipeline (flag)"
    erros_path = ROOT / "dados" / "pipeline-errors.json"
    if not erros_path.exists():
        return {"nome": nome, "status": "ok", "detalhe": "nenhuma falha registrada"}
    try:
        data = json.loads(erros_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {"nome": nome, "status": "warn", "detalhe": "arquivo de erros corrompido"}
    erros = data.get("erros") or []
    if not erros:
        return {"nome": nome, "status": "ok", "detalhe": "varredura limpa"}
    # Pega só os erros da última varredura (mesmo timestamp)
    steps = [e.get("step") for e in erros]
    nivel = "crit" if "publicar" in steps or "sanitizar_json" in steps else "warn"
    detalhe = f"{len(erros)} step(s) falharam: {', '.join(set(steps))}"
    return {
        "nome": nome,
        "status": nivel,
        "detalhe": detalhe,
        "sugestao": "Ver dados/pipeline-errors.json · re-rodar steps falhos manualmente",
    }


def check_passos_pipeline_ok():
    """Olha o varredura.log das últimas 24h pra ver se algum passo falhou."""
    nome = "Saúde do pipeline"
    if not LOG_PATH.exists():
        return {"nome": nome, "status": "warn", "detalhe": "sem log · varredura nunca rodou"}
    try:
        # Lê últimas 200 linhas (varredura típica gera ~30 linhas)
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            linhas = f.readlines()[-200:]
    except OSError:
        return {"nome": nome, "status": "warn", "detalhe": "log inacessível"}

    falhas = [l for l in linhas if "FALHOU" in l or "ABORT" in l or "ERRO (exit" in l]
    if not falhas:
        return {"nome": nome, "status": "ok", "detalhe": "sem falhas nas últimas runs"}
    if len(falhas) <= 2:
        return {"nome": nome, "status": "warn", "detalhe": f"{len(falhas)} falha(s) no log recente", "sugestao": "Conferir varredura.log"}
    return {"nome": nome, "status": "crit", "detalhe": f"{len(falhas)} falhas no log recente", "sugestao": "Pipeline degradado · ver log"}


def main():
    discord = None
    snapshot = None
    try:
        if DISCORD_PATH.exists():
            discord = json.loads(DISCORD_PATH.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"AVISO: falha ao ler discord: {e}", file=sys.stderr)
    try:
        if SNAPSHOT_PATH.exists():
            snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8-sig"))
    except Exception as e:
        print(f"AVISO: falha ao ler snapshot: {e}", file=sys.stderr)

    checks = [
        check_schema_discord(discord),
        check_obras_completas(discord or {}),
        check_telegram_session(snapshot),
        check_freshness_varredura(discord or {}),
        check_kira_freshness(discord or {}),
        check_lock_orfao(),
        check_backups(),
        check_drift_obras(discord or {}),
        check_pipeline_errors_flag(),
        check_passos_pipeline_ok(),
    ]

    # Status geral = pior dentre todos
    contagem = {"ok": 0, "warn": 0, "crit": 0}
    for c in checks:
        contagem[c.get("status", "warn")] = contagem.get(c.get("status", "warn"), 0) + 1
    if contagem["crit"]:
        geral = "crit"
    elif contagem["warn"]:
        geral = "warn"
    else:
        geral = "ok"

    status = {
        "geral": geral,
        "checked_at": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "contagem": contagem,
        "checks": checks,
    }

    write_json_atomic(STATUS_PATH, status)

    print(f"Sentinela: {geral.upper()} · {contagem}")
    for c in checks:
        ico = {"ok": "✓", "warn": "⚠", "crit": "✗"}.get(c["status"], "?")
        print(f"  {ico} {c['nome']:<35} {c.get('detalhe', '')}")
        if c.get("sugestao") and c["status"] != "ok":
            print(f"     → {c['sugestao']}")


if __name__ == "__main__":
    main()
