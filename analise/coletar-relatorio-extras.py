"""
coletar-relatorio-extras.py — Coletor dos endpoints subutilizados
==================================================================

Busca 4 endpoints públicos do Painel de Obras + Planejamento que NÃO
estão no coletor principal mas respondem perguntas-chave do relatório
quinzenal:

1. /api/analise (cliente)            ->atRisk + problemCategories + recentEvents + teamPerformance
2. /api/analytics/alerts (planej)    ->8 alertas estruturados (stage_delay + sem_equipe)
3. /api/analytics/weekly-forecast    ->projeção semanal {starting, inExecution, ending}
4. /api/dashboard (cliente)          ->ocorrencias.byStatus (691 abertas)

Saída: analise/dados/relatorio-extras.json
Uso:   python coletar-relatorio-extras.py
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
DADOS = ROOT / "dados"

ENDPOINTS = [
    ("analise",   "https://cliente.monofloor.cloud/api/analise"),
    ("alerts",    "https://planejamento.monofloor.cloud/api/analytics/alerts"),
    ("forecast",  "https://planejamento.monofloor.cloud/api/analytics/weekly-forecast"),
    ("dashboard", "https://cliente.monofloor.cloud/api/dashboard"),
]


def fetch_json(url, timeout=30):
    """GET + parse JSON. Levanta exceção em caso de falha."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Monofloor-Relatorio-Extras/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if r.status != 200:
            raise ValueError(f"HTTP {r.status}")
        data = r.read()
        return json.loads(data.decode("utf-8"))


def main():
    out = {
        "atualizado_em": datetime.now().isoformat(),
        "fonte": "coletor-relatorio-extras (4 endpoints públicos)",
    }
    falhas = []

    for chave, url in ENDPOINTS:
        try:
            data = fetch_json(url)
            out[chave] = data
            tamanho = len(json.dumps(data))
            print(f"[OK]   {chave:<10} ->{tamanho:>7} bytes")
        except urllib.error.HTTPError as e:
            print(f"[FAIL] {chave:<10} ->HTTP {e.code} {e.reason}")
            out[chave] = None
            falhas.append(chave)
        except urllib.error.URLError as e:
            print(f"[FAIL] {chave:<10} ->URL {e.reason}")
            out[chave] = None
            falhas.append(chave)
        except Exception as e:
            print(f"[FAIL] {chave:<10} ->{type(e).__name__}: {e}")
            out[chave] = None
            falhas.append(chave)

    DADOS.mkdir(exist_ok=True)
    out_path = DADOS / "relatorio-extras.json"
    out_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n[OK] Salvo em: {out_path}")
    print(f"     Tamanho: {out_path.stat().st_size:,} bytes")
    if falhas:
        print(f"     Falhas: {', '.join(falhas)} (relatório gerador trata como ausente)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
