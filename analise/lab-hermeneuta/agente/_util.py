"""
Util compartilhado · funções comuns aos scripts do pipeline
============================================================
"""
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def now_utc() -> datetime:
    """Hora atual UTC. Substitui HOJE hardcoded · pipeline para de derivar."""
    return datetime.now(timezone.utc)


def write_json_atomic(path: Path, data, indent: int = 2):
    """
    Escreve JSON de forma atômica · não corrompe se processo morrer mid-write.

    Estratégia: escreve em arquivo .tmp no mesmo diretório, depois os.replace
    (que é atômico no Windows e POSIX). Garante que `path` ou está intacto
    com conteúdo antigo, ou totalmente atualizado · nunca truncado.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # tempfile no MESMO diretório de destino (replace só funciona no mesmo volume)
    fd, tmp_str = tempfile.mkstemp(
        prefix=path.stem + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_str, path)
    except Exception:
        # Cleanup tmp se algo deu errado antes do replace
        try:
            os.unlink(tmp_str)
        except OSError:
            pass
        raise


def read_json_safe(path: Path, default=None):
    """
    Lê JSON tolerante a BOM (utf-8-sig). Retorna default se erro/inexistente.
    Usar como `data = read_json_safe(path, {})` ou `[]`.
    """
    path = Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"AVISO: falha ao ler {path.name}: {e}", file=sys.stderr)
        return default


# Encoding seguro pra stdout/stderr no Windows
def setup_utf8():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


# ============================================================
# Schema validator · valida discordancias-v3.json antes de gravar
# ============================================================

CAMPOS_OBRIGATORIOS_OBRA = {
    "obra_id", "cliente",  # mínimos absolutos
}
CAMPOS_RECOMENDADOS_OBRA = {
    "consultor", "painel", "telegram", "veredicto", "flags", "urgencia",
    "confianca", "timeline_recente", "regua", "equipe_em_campo", "cores",
    "kira_whatsapp", "refresh_status",
}
CAMPOS_OBRIGATORIOS_TOPO = {"obras", "agregados"}


def validar_discord(data: dict) -> list:
    """
    Valida estrutura do discordancias-v3.json.
    Retorna lista de problemas (vazia = OK).
    """
    problemas = []
    if not isinstance(data, dict):
        return ["root não é dict"]

    for campo in CAMPOS_OBRIGATORIOS_TOPO:
        if campo not in data:
            problemas.append(f"top-level: campo obrigatório '{campo}' faltando")

    obras = data.get("obras") or []
    if not isinstance(obras, list):
        problemas.append("obras não é lista")
        return problemas

    for i, o in enumerate(obras):
        if not isinstance(o, dict):
            problemas.append(f"obra[{i}] não é dict")
            continue
        for campo in CAMPOS_OBRIGATORIOS_OBRA:
            if campo not in o:
                problemas.append(f"obra[{i}] ({(o.get('cliente') or 'sem cliente')[:25]}): obrigatório '{campo}' faltando")

    return problemas


def write_json_atomic_validado(path: Path, data, validator=None, indent: int = 2):
    """
    write_json_atomic + validação prévia. Se validator retornar problemas, RAISES.
    Use pra writes críticos do discordancias-v3.json.
    """
    if validator:
        problemas = validator(data)
        if problemas:
            preview = "; ".join(problemas[:3]) + (f" (+{len(problemas)-3} mais)" if len(problemas) > 3 else "")
            raise ValueError(f"Validação de schema falhou · NÃO escrevendo: {preview}")
    write_json_atomic(path, data, indent=indent)


def tocar_timestamps_discord(data: dict) -> dict:
    """
    Atualiza ultima_varredura e gerado_em no dict pra agora UTC.

    DEVE ser chamada antes de QUALQUER write em discordancias-v3.json
    pra evitar timestamp congelado (bug crônico em refresh manual).

    Retorna o dict (encadeável). Mutação in-place.
    """
    if not isinstance(data, dict):
        return data
    agora = now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")
    data["ultima_varredura"] = agora
    data["gerado_em"] = agora
    return data


def write_discord(path: Path, data: dict, indent: int = 2):
    """
    Helper canônico pra escrever discordancias-v3.json:
      1. tocar timestamps (ultima_varredura, gerado_em)
      2. validar schema
      3. write atomic

    SEMPRE use isso em vez de write_json_atomic puro pra discordancias-v3.json.
    """
    tocar_timestamps_discord(data)
    write_json_atomic_validado(path, data, validator=validar_discord, indent=indent)


# ============================================================
# Pipeline error tracking · falhas silenciosas viram visíveis
# ============================================================

def marcar_step_falho(step: str, erro: str = "", pasta_dados: Path = None):
    """
    Registra que um step do pipeline falhou em dados/pipeline-errors.json.
    Sentinela lê esse arquivo e reporta como warn/crit na tela.
    Permite "continue silencioso" virar visibilidade ativa.
    """
    if pasta_dados is None:
        # default: agente/../dados/
        pasta_dados = Path(__file__).parent.parent / "dados"
    pasta_dados.mkdir(parents=True, exist_ok=True)
    path = pasta_dados / "pipeline-errors.json"

    existing = read_json_safe(path, default={})
    if not isinstance(existing, dict):
        existing = {}
    erros = existing.setdefault("erros", [])
    erros.append({
        "step": step,
        "erro": str(erro)[:500],
        "timestamp": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"),
    })
    # Mantém últimos 50 (rolling)
    existing["erros"] = erros[-50:]
    existing["ultima_atualizacao"] = now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")
    write_json_atomic(path, existing)


def limpar_erros_pipeline(pasta_dados: Path = None):
    """
    Reseta o pipeline-errors.json no início de cada varredura.
    Garante que erros antigos não persistam após varredura limpa.
    """
    if pasta_dados is None:
        pasta_dados = Path(__file__).parent.parent / "dados"
    path = pasta_dados / "pipeline-errors.json"
    if path.exists():
        write_json_atomic(path, {
            "erros": [],
            "ultima_atualizacao": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"),
        })


# ============================================================
# Backup automático · rolling window
# ============================================================

def fazer_backup(arquivo: Path, pasta_backups: Path = None, manter: int = 14):
    """
    Copia `arquivo` pra pasta_backups/ com timestamp.
    Mantém últimos `manter` backups, remove os mais antigos.
    Default: 14 backups = 7 dias × 2 varreduras/dia.
    """
    arquivo = Path(arquivo)
    if not arquivo.exists():
        return None
    if pasta_backups is None:
        pasta_backups = arquivo.parent / "backups"
    pasta_backups.mkdir(parents=True, exist_ok=True)

    ts = now_utc().strftime("%Y%m%d-%H%M%S")
    dest = pasta_backups / f"{arquivo.stem}.{ts}{arquivo.suffix}"
    import shutil
    shutil.copy2(arquivo, dest)

    # Limpa antigos · mantém só os `manter` mais recentes do mesmo prefix
    prefix = f"{arquivo.stem}."
    existentes = sorted(
        [p for p in pasta_backups.iterdir() if p.name.startswith(prefix) and p.suffix == arquivo.suffix],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for antigo in existentes[manter:]:
        try:
            antigo.unlink()
        except OSError:
            pass

    return dest
