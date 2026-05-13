"""
gerar_jornada_lote.py · roda gerar_jornada.construir_jornada em lote nas 8 obras de calibração
================================================================================================

Script de calibração F3 (sessão 2026-05-08) · NÃO toca no canônico `gerar_jornada.py`.
Reusa `construir_jornada` do canônico via import. Saída separada: `dados/jornadas_calibracao.json`.

Uso: python agente/gerar_jornada_lote.py
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent))
try:
    from _util import setup_utf8
    setup_utf8()
except ImportError:
    pass

# Importa do canônico
from gerar_jornada import construir_jornada, gerar_narrativa_md, JORNADAS_DIR

ROOT = Path(__file__).parent.parent
SAIDA_LOTE = ROOT / "dados" / "jornadas_calibracao.json"
HOJE = datetime.now(timezone.utc)

# 8 obras de calibração F3 · finalizadas/concluídas com sinal Telegram rico (8+ marcos)
# + GUSTAVO DE SOUZA PEREIRA (marcas_rolo_cera · pausada · obra problemática indicada por Vitor)
OBRAS_CALIBRACAO = [
    ("0e4e10b2-9fbe-49a4-9e42-08ae5624b39c", "GETULIO TURATTI OST",                  "2 ciclos · clássico retrabalho"),
    ("63623d90-e0c0-48e7-bc9d-eb45cc923af5", "LUIS FERNANDO DE LIMA CARVALHO",       "3 ciclos · jornada longuíssima"),
    ("e6b38375-4075-4f79-9319-f15566722963", "TALLY FELDMAN SINGAL GROSS",           "91m · sinal mais rico do histórico"),
    ("0f3e836e-8e36-4436-bac8-51ef678b17c9", "P2B ENGENHARIA",                       "entrega direta corporativa · revalida"),
    ("687fbc05-b847-4c52-8af1-d7833b3a4590", "GUSTAVO DE SOUZA PEREIRA",             "PROBLEMÁTICA · 2000 msgs no limite · marcas/pausada"),
    ("b055e234-ebef-41d3-b464-54c2102c0895", "JAQUES AJZENTAL",                      "poucas msgs · processo paralelo"),
    ("b8fbadd8-778c-4a3b-9e18-81bba29a6a8e", "ANDRE KEUNECKE SALERNO",               "2 ciclos · sinal médio"),
    ("9a190357-99d5-4a25-bba2-436ab65542ed", "RODRIGO DE ALMEIDA SCHMIDT",           "entrega direta · jornada longa"),
]


def main():
    print(f"Calibração F3 · construindo jornada em {len(OBRAS_CALIBRACAO)} obras\n")
    JORNADAS_DIR.mkdir(parents=True, exist_ok=True)

    out = {
        "gerado_em": HOJE.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "modo": "calibracao_f3",
        "obras": [],
    }
    inicio = time.time()
    for oid, nome_esperado, motivo in OBRAS_CALIBRACAO:
        print(f"  · {nome_esperado[:45]} ({motivo})")
        try:
            j = construir_jornada(oid)
            out["obras"].append(j)
            md = gerar_narrativa_md(j)
            md_path = JORNADAS_DIR / f"{oid}.md"
            md_path.write_text(md, encoding="utf-8")
            n_marcos = len(j.get("marcos", []))
            n_ciclos = len(j.get("ciclos", []) or [])
            t_total = j.get("tempo_total_dias", "?")
            t_exec = j.get("tempo_execucao_dias", "?")
            print(f"      ✓ {n_marcos} marcos · {n_ciclos} ciclos · {t_total}d total · {t_exec}d exec")
        except Exception as e:
            print(f"      ✗ ERRO: {e}")

    SAIDA_LOTE.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_LOTE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    elapsed = time.time() - inicio
    print(f"\n[OK] {len(out['obras'])} obras em {elapsed:.1f}s · saída: {SAIDA_LOTE}")
    print(f"     MDs em {JORNADAS_DIR}")


if __name__ == "__main__":
    main()
