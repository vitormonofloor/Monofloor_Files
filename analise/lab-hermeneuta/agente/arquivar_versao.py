"""
Arquiva versão atual do discordancias-v3.json em dados/historico/
=================================================================

Roda ANTES de qualquer consolidação que sobrescreva o JSON.
Mantém histórico completo pra ver evolução de veredictos por obra.

Saída: dados/historico/discordancias-v3-{YYYY-MM-DD-HHMM}.json + atualiza index.

Uso:
    python agente/arquivar_versao.py             # arquiva versão atual
    python agente/arquivar_versao.py --evolucao OBRA_ID   # mostra evolução de uma obra
"""

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

ROOT = Path(__file__).parent.parent
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"
HISTORICO_DIR = ROOT / "dados" / "historico"
INDEX_PATH = HISTORICO_DIR / "index.json"


def arquivar() -> Path:
    """Copia discordancias-v3.json atual pra historico/ com timestamp."""
    if not DISCORD_PATH.exists():
        print("ERRO: discordancias-v3.json não existe · nada pra arquivar")
        sys.exit(1)

    HISTORICO_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(DISCORD_PATH.read_text(encoding="utf-8"))
    gerado = data.get("gerado_em") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Sanitiza pra nome de arquivo
    ts = gerado.replace(":", "").replace("-", "").replace("T", "-").split("+")[0].split(".")[0][:13]
    dest = HISTORICO_DIR / f"discordancias-v3-{ts}.json"

    # Se já existe (mesmo timestamp), adiciona sufixo
    i = 1
    while dest.exists():
        dest = HISTORICO_DIR / f"discordancias-v3-{ts}-{i}.json"
        i += 1

    shutil.copy2(DISCORD_PATH, dest)
    atualizar_index(dest, data)
    print(f"[OK] arquivado em {dest.name}")
    return dest


def atualizar_index(arquivo: Path, data: dict):
    """Mantém index.json com lista de versões + metadados leves de cada uma."""
    index = []
    if INDEX_PATH.exists():
        try:
            index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            index = []

    # Resumo enxuto de cada obra: id + cliente + veredicto + status_sugerido + flags
    obras_resumo = []
    for o in data.get("obras", []):
        obras_resumo.append({
            "obra_id": o.get("obra_id"),
            "cliente": o.get("cliente"),
            "veredicto": o.get("veredicto"),
            "status_sugerido": o.get("status_sugerido"),
            "consultor_inferido": (o.get("consultor_inferido") or {}).get("nome"),
            "flags": o.get("flags", []),
            "urgencia": o.get("urgencia"),
            "confianca": o.get("confianca"),
        })

    entry = {
        "arquivo": arquivo.name,
        "gerado_em": data.get("gerado_em"),
        "total_obras": data.get("total_obras"),
        "veredictos": (data.get("agregados") or {}).get("veredictos"),
        "obras": obras_resumo,
    }
    index.append(entry)
    # Mantém ordem cronológica (mais antigo primeiro)
    index.sort(key=lambda e: e.get("gerado_em") or "")

    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def mostrar_evolucao(obra_id: str):
    """Mostra como veredicto/status/flags mudaram ao longo do tempo pra uma obra."""
    if not INDEX_PATH.exists():
        print("Sem histórico ainda")
        return

    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    versoes = []
    for e in index:
        for o in e.get("obras", []):
            if o.get("obra_id") == obra_id:
                versoes.append({
                    "data": (e.get("gerado_em") or "")[:16],
                    "veredicto": o.get("veredicto"),
                    "status": o.get("status_sugerido"),
                    "consultor": o.get("consultor_inferido"),
                    "urgencia": o.get("urgencia"),
                    "flags": o.get("flags", []),
                })
                break

    if not versoes:
        print(f"Obra {obra_id} não encontrada no histórico")
        return

    # Pega cliente do mais recente
    cliente = next((o["cliente"] for e in index for o in e["obras"] if o["obra_id"] == obra_id), obra_id)
    print(f"=== EVOLUÇÃO · {cliente} ({obra_id[:8]}) ===")
    print(f"{len(versoes)} versão(ões) no histórico\n")

    for i, v in enumerate(versoes):
        print(f"{i+1}. [{v['data']}]")
        print(f"   veredicto: {v['veredicto']} · status: {v['status']} · urg: {v['urgencia']}")
        print(f"   consultor: {v['consultor']}")
        print(f"   flags: {', '.join(v['flags']) if v['flags'] else '—'}")
        if i > 0:
            ant = versoes[i-1]
            mudancas = []
            if ant['veredicto'] != v['veredicto']:
                mudancas.append(f"veredicto {ant['veredicto']} → {v['veredicto']}")
            if ant['status'] != v['status']:
                mudancas.append(f"status {ant['status']} → {v['status']}")
            if ant['urgencia'] != v['urgencia']:
                mudancas.append(f"urg {ant['urgencia']} → {v['urgencia']}")
            adicionadas = set(v['flags']) - set(ant['flags'])
            removidas = set(ant['flags']) - set(v['flags'])
            if adicionadas:
                mudancas.append(f"+ flags: {', '.join(adicionadas)}")
            if removidas:
                mudancas.append(f"- flags: {', '.join(removidas)}")
            if mudancas:
                print(f"   MUDANÇAS desde versão anterior: {' · '.join(mudancas)}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--evolucao", help="UUID da obra · mostra evolução cronológica")
    args = parser.parse_args()

    if args.evolucao:
        mostrar_evolucao(args.evolucao)
    else:
        arquivar()
