"""
atualizar_universo.py — Automacao diaria do universo de obras
=============================================================

Roda ANTES do gerar_jornada.py. Faz 3 coisas:
  1. Busca TODAS as obras da API (limite 5000)
  2. Identifica obras em fases de execucao que nao estao no _obras_2026_ids.json
  3. Adiciona automaticamente e salva

Resultado: _obras_2026_ids.json sempre atualizado com o universo completo.
O gerar_jornada.py le esse arquivo e processa todas.

Uso:
  python agente/atualizar_universo.py          # atualiza IDs + refaz painel-snapshot
  python agente/atualizar_universo.py --dry    # so mostra o que faria, nao salva

Encadear com pipeline completo:
  python agente/atualizar_universo.py && python agente/gerar_jornada.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import date, datetime, timezone
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))
try:
    from _util import setup_utf8
    setup_utf8()
except ImportError:
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).parent.parent
IDS_PATH = Path(__file__).parent / "_obras_2026_ids.json"
SNAPSHOT_PATH = ROOT / "dados" / "painel-snapshot.json"
LOG_PATH = ROOT / "dados" / "universo-log.json"
BASE_API = "https://cliente.monofloor.cloud/api/projects"

HOJE = date.today()

OBRAS_PILOTO = [
    "a79f00f0-19b1-43d4-b9d7-6ab8d219c205", "3e5c6392-af93-427a-9e29-3a927e6d5dc6",
    "0e4e10b2-9fbe-49a4-9e42-08ae5624b39c", "63623d90-e0c0-48e7-bc9d-eb45cc923af5",
    "e6b38375-4075-4f79-9319-f15566722963", "0f3e836e-8e36-4436-bac8-51ef678b17c9",
    "687fbc05-b847-4c52-8af1-d7833b3a4590", "b055e234-ebef-41d3-b464-54c2102c0895",
    "b8fbadd8-778c-4a3b-9e18-81bba29a6a8e", "9a190357-99d5-4a25-bba2-436ab65542ed",
    "50068c67-3854-49dd-9302-1a8636cf4a6a", "e1fe5106-083e-4958-8af0-2a491c826b5b",
    "c1621370-4f28-4e9b-9f02-10032f9bf7a0", "c3d79452-b378-4d23-895c-3ba5e8a060ea",
    "994a0d5b-e532-44fb-ab3b-19b686d147a6", "edc779fb-2dca-4d1a-864a-6234236cf145",
    "13d9ca18-e5fc-42bc-907c-174a2e02ae9f", "56cd74a9-44ee-40f2-b389-8773ac6df222",
    "0d0c35bd-3b00-4de2-b898-4dfc61e6fdae", "1b292a9b-8c57-47bd-92e1-824fcd0b7fff",
]

# Fases que indicam que a obra passou por execucao ou esta em execucao
FASES_EXECUTOU = {
    'INDÚSTRIA - EM PRODUÇÃO',
    'LOGÍSTICA - EM COLETA', 'LOGÍSTICA - COLETAR',
    'LOGÍSTICA - EM ENTREGA', 'LOGÍSTICA - MATERIAL ENTREGUE',
    'INFORMAÇÕES LOGÍSTICAS',
    'CONFIRMAÇÕES OP 1', 'EQUIPE DE EXECUÇÃO', 'REVISÃO FINAL OP',
    'OBRA EM EXECUÇÃO', 'OBRA PAUSADA',
    'OBRA CONCLUÍDA',
    'PÓS VENDAS ACIONADO', 'RESULTADO VT - QUALIDADE', 'REAPLICAÇÃO TOTAL',
}

# Corte temporal: so incluir obras com previsao >= esta data OU em fase ativa de execucao
CORTE_PREV = "2025-11-01"

FASES_ATIVAS_SEMPRE = {
    'OBRA EM EXECUÇÃO', 'OBRA PAUSADA',
    'LOGÍSTICA - EM ENTREGA', 'LOGÍSTICA - MATERIAL ENTREGUE',
    'LOGÍSTICA - EM COLETA', 'LOGÍSTICA - COLETAR',
    'INDÚSTRIA - EM PRODUÇÃO',
    'CONFIRMAÇÕES OP 1', 'EQUIPE DE EXECUÇÃO', 'REVISÃO FINAL OP',
    'PÓS VENDAS ACIONADO', 'RESULTADO VT - QUALIDADE', 'REAPLICAÇÃO TOTAL',
    'INFORMAÇÕES LOGÍSTICAS',
}


def fetch(url, max_retries=2):
    last_err = None
    for tentativa in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "lab-orion/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.load(r)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            last_err = e
            if tentativa < max_retries:
                time.sleep(2 ** tentativa)
    raise RuntimeError(f"fetch falhou: {last_err}")


def main():
    dry = "--dry" in sys.argv

    print(f"atualizar_universo.py · {HOJE.isoformat()}")
    print(f"{'[DRY RUN]' if dry else ''}")
    print()

    # 1. Buscar todas as obras da API
    print("[1/4] Buscando todas as obras da API...")
    todas = fetch(f"{BASE_API}?limit=5000")
    print(f"      {len(todas)} obras no universo total")

    # 2. Salvar painel-snapshot atualizado
    if not dry:
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(todas, ensure_ascii=False, indent=None), encoding="utf-8")
        print(f"      painel-snapshot.json atualizado ({len(todas)} itens)")
    else:
        print(f"      [DRY] painel-snapshot.json NAO atualizado")

    # 3. Carregar IDs atuais
    if IDS_PATH.exists():
        ids_atual = json.load(open(IDS_PATH, "r"))
    else:
        ids_atual = []

    ids_set = set(ids_atual) | set(OBRAS_PILOTO)
    print(f"\n[2/4] IDs no pipeline atual: {len(ids_set)}")

    # 4. Identificar obras novas em fases de execucao
    print(f"\n[3/4] Identificando obras em fases de execucao...")

    fases = Counter(o.get('faseAtual', '') for o in todas)
    novos = []

    for o in todas:
        oid = o.get('id', '')
        if not oid or oid in ids_set:
            continue

        fase = o.get('faseAtual', '')
        if fase not in FASES_EXECUTOU:
            continue

        prev = (o.get('dataExecucaoPrevista') or '')[:10]
        nome = o.get('clienteNome', '?')

        # Incluir se: fase ativa (sempre) OU obra concluida com prev recente
        incluir = False
        if fase in FASES_ATIVAS_SEMPRE:
            incluir = True
        elif prev >= CORTE_PREV:
            incluir = True

        if incluir:
            novos.append({
                'id': oid,
                'nome': nome,
                'fase': fase,
                'prev': prev,
            })

    print(f"      {len(novos)} obras novas encontradas")

    if novos:
        por_fase = Counter(n['fase'] for n in novos)
        for f, c in por_fase.most_common():
            print(f"        {f}: {c}")

        print(f"\n      Obras novas:")
        for n in sorted(novos, key=lambda x: x['prev'] or 'z'):
            print(f"        + {n['nome'][:45]:45s} | {n['fase']:28s} | prev={n['prev'] or '—'}")

    # 5. Atualizar _obras_2026_ids.json
    print(f"\n[4/4] Atualizando _obras_2026_ids.json...")

    novos_ids = [n['id'] for n in novos]

    if novos_ids:
        if not dry:
            ids_atualizado = ids_atual + novos_ids
            IDS_PATH.write_text(json.dumps(ids_atualizado, indent=None), encoding="utf-8")
            print(f"      +{len(novos_ids)} IDs adicionados. Total: {len(ids_atualizado)}")
        else:
            print(f"      [DRY] +{len(novos_ids)} IDs SERIAM adicionados")
    else:
        print(f"      Nenhum ID novo. Universo esta completo.")

    # 6. Log da execucao
    log_entry = {
        "data": HOJE.isoformat(),
        "hora": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "total_api": len(todas),
        "ids_pipeline": len(ids_set) + len(novos_ids),
        "novos": len(novos_ids),
        "novos_nomes": [n['nome'] for n in novos],
        "dry": dry,
    }

    if not dry:
        log = []
        if LOG_PATH.exists():
            try:
                log = json.loads(LOG_PATH.read_text(encoding="utf-8"))
            except Exception:
                log = []
        log.append(log_entry)
        # Manter ultimos 90 dias
        log = log[-90:]
        LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")

    # Resumo
    print(f"\n{'='*60}")
    print(f"RESUMO")
    print(f"{'='*60}")
    print(f"  API total:          {len(todas)} obras")
    print(f"  Pipeline:           {len(ids_set) + len(novos_ids)} IDs")
    print(f"  Novas hoje:         {len(novos_ids)}")
    print(f"  Snapshot:           {'atualizado' if not dry else 'DRY'}")

    if novos_ids:
        print(f"\n  Proximo passo: python agente/gerar_jornada.py")
    else:
        print(f"\n  Universo completo. Pipeline pode rodar direto.")

    return len(novos_ids)


if __name__ == "__main__":
    main()
