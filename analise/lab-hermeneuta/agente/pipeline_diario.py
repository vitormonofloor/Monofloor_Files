"""
pipeline_diario.py — Automacao completa do Lab Orion
====================================================

Roda tudo na ordem certa:
  1. atualizar_universo.py  (busca obras novas no Painel, atualiza snapshot + IDs)
  2. gerar_jornada.py       (processa todas as obras, 4 camadas de data inicio)
  3. Relatorio de cobertura (mostra o que mudou)

Uso:
  python agente/pipeline_diario.py              # execucao completa
  python agente/pipeline_diario.py --dry        # so mostra o que faria
  python agente/pipeline_diario.py --skip-fetch  # pula API, so roda pipeline

Tempo estimado: ~5-6 min (fetch API ~10s + pipeline ~287s para ~300 obras)
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timezone, date
from pathlib import Path

ROOT = Path(__file__).parent.parent
AGENTE = Path(__file__).parent
JORNADAS_PATH = ROOT / "dados" / "jornadas.json"

sys.stdout.reconfigure(encoding='utf-8')


def rodar(cmd, descricao):
    print(f"\n{'━'*70}")
    print(f"  {descricao}")
    print(f"{'━'*70}\n")
    inicio = time.time()
    result = subprocess.run(
        [sys.executable] + cmd,
        cwd=str(ROOT),
        capture_output=False,
    )
    elapsed = time.time() - inicio
    if result.returncode != 0:
        print(f"\n[ERRO] {descricao} falhou (exit {result.returncode}) em {elapsed:.1f}s")
        return False
    print(f"\n[OK] {descricao} concluido em {elapsed:.1f}s")
    return True


def relatorio_cobertura():
    print(f"\n{'━'*70}")
    print(f"  RELATORIO DE COBERTURA")
    print(f"{'━'*70}\n")

    if not JORNADAS_PATH.exists():
        print("  jornadas.json nao encontrado!")
        return

    j = json.loads(JORNADAS_PATH.read_text(encoding="utf-8"))
    obras = j['obras']
    total = len(obras)
    com_dir = sum(1 for o in obras if o.get('data_inicio_real'))

    from collections import Counter
    origens = Counter(o.get('data_inicio_real_origem', '—') for o in obras if o.get('data_inicio_real'))

    STATUS_NAO_INICIOU = {'planejamento', 'contrato', 'aguardando_execucao', 'cancelado'}
    STATUS_EXEC = {'em_execucao', 'finalizado', 'concluido', 'reparo', 'marcas_rolo_cera', 'aguardando_clima', 'pausado'}

    sem = [o for o in obras if not o.get('data_inicio_real')]
    nao_iniciou = sum(1 for o in sem if o.get('status') in STATUS_NAO_INICIOU)
    exec_sem_data = sum(1 for o in sem if o.get('status') in STATUS_EXEC)

    obras_executaram = total - nao_iniciou
    cobertura_efetiva = com_dir / obras_executaram * 100 if obras_executaram else 0

    print(f"  Universo total:       {total} obras")
    print(f"  Com data_inicio_real: {com_dir} ({100*com_dir/total:.0f}%)")
    print(f"  Nao iniciaram:        {nao_iniciou}")
    print(f"  Exec sem data:        {exec_sem_data}")
    print(f"  Cobertura efetiva:    {com_dir}/{obras_executaram} = {cobertura_efetiva:.1f}%")
    print()
    print(f"  Fontes:")
    for k, v in origens.most_common():
        print(f"    {k:20s}: {v:3d}")

    # Material
    print()
    por_mes = {}
    for o in obras:
        d = o.get('data_inicio_real', '')
        if d and d[:7] >= '2026-01' and d[:7] <= '2026-12':
            mes = d[:7]
            if mes not in por_mes:
                por_mes[mes] = {'n': 0, 'os': 0, 'solic': 0, 'consumo': 0}
            por_mes[mes]['n'] += 1
            if len(o.get('materiais_enviados') or []) > 0:
                por_mes[mes]['os'] += 1
            if len(o.get('solicitacoes_material') or []) > 0:
                por_mes[mes]['solic'] += 1
            if len(o.get('consumos') or []) > 0:
                por_mes[mes]['consumo'] += 1

    print(f"  Material por mes:")
    print(f"  {'Mes':8s} | {'Obras':>5s} | {'c/OS':>5s} | {'c/Solic':>7s} | {'c/Consumo':>9s}")
    for m in sorted(por_mes.keys()):
        d = por_mes[m]
        print(f"  {m:8s} | {d['n']:5d} | {d['os']:5d} | {d['solic']:7d} | {d['consumo']:9d}")

    print(f"\n  Gerado em: {j.get('gerado_em', '?')}")


def main():
    dry = "--dry" in sys.argv
    skip_fetch = "--skip-fetch" in sys.argv

    print(f"{'='*70}")
    print(f"  PIPELINE DIARIO LAB ORION · {date.today().isoformat()}")
    print(f"  {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC")
    if dry:
        print(f"  MODO DRY RUN")
    print(f"{'='*70}")

    inicio_total = time.time()

    # Passo 1: Atualizar universo
    if not skip_fetch:
        args = [str(AGENTE / "atualizar_universo.py")]
        if dry:
            args.append("--dry")
        ok = rodar(args, "PASSO 1: Atualizar universo (API + snapshot + IDs)")
        if not ok and not dry:
            print("\n[ABORTANDO] Falha ao atualizar universo.")
            sys.exit(1)
    else:
        print(f"\n  [SKIP] Passo 1 pulado (--skip-fetch)")

    # Passo 2: Rodar pipeline
    if not dry:
        ok = rodar(
            [str(AGENTE / "gerar_jornada.py")],
            "PASSO 2: Pipeline gerar_jornada.py"
        )
        if not ok:
            print("\n[AVISO] Pipeline falhou, mas snapshot foi atualizado.")
    else:
        print(f"\n  [DRY] Passo 2 pulado (pipeline nao roda em dry run)")

    # Passo 3: Publicar no Cloudflare
    if not dry:
        rodar(
            [str(AGENTE / "publicar.py")],
            "PASSO 3: Publicar no Cloudflare (wrangler deploy)"
        )

    # Passo 4: Relatorio
    if not dry:
        relatorio_cobertura()

    elapsed_total = time.time() - inicio_total
    print(f"\n{'='*70}")
    print(f"  Pipeline concluido em {elapsed_total:.0f}s ({elapsed_total/60:.1f} min)")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
