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
