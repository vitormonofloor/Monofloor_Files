"""
gerar_agregados.py · Recalcula campos top-level a partir das 230 obras
=========================================================================

Após o cruzar_kira atualizar cada obra individualmente, os campos top-level do JSON
(total_obras, resumo_executivo, agregados.*) ainda refletiam a rodada IA antiga de 10
obras. Este script regenera tudo a partir das 230 obras reais.

REGENERA:
  - total_obras (contagem real)
  - total_ativas (novo · obras com status != concluido/finalizado)
  - resumo_executivo (template baseado em contagens · sem narrativa IA)
  - agregados.veredictos (count by veredicto)
  - agregados.tipo_demanda (count quando preenchido)
  - agregados.flags_recorrentes (lista por flag · top obras)
  - agregados.consultores (agrupado · ações priorizadas)

MANTÉM:
  - padroes_cross_obras (texto narrativo · não regenerado · zera se ausente)
  - cores_agregado (gerado por extrair_cores.py)
  - obras (intactas)

Uso: python gerar_agregados.py
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import setup_utf8, write_discord

setup_utf8()

ROOT = Path(__file__).parent.parent
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"

STATUS_FINALIZADO = ("concluido", "finalizado")

# Donos operacionais durante execução · matching parcial case-insensitive.
# Pedro/Mayara/Kettlyn etc são atendimento PRÉ-obra (explicação inicial) · NÃO entram.
# Renata/Thaísa/Juliana Santos · desconsiderar (Juliana demitida em 2026-05-05).
# Atualizar essa lista quando entrar/sair gente do time de operação.
DONOS_OPERACIONAIS = ("luana", "wesley")


def main():
    if not DISCORD_PATH.exists():
        print(f"ERRO: {DISCORD_PATH} não encontrado")
        sys.exit(1)

    data = json.loads(DISCORD_PATH.read_text(encoding="utf-8"))
    obras = data.get("obras", [])
    n_total = len(obras)
    ativas = [o for o in obras if (o.get("painel") or {}).get("status_atual") not in STATUS_FINALIZADO]
    n_ativas = len(ativas)

    # ============ CONTAGENS ============
    veredictos = Counter()
    tipo_demanda = Counter()
    urgencias = Counter()
    flags_count = Counter()
    flags_obras = defaultdict(list)
    by_consultor = defaultdict(list)

    for o in obras:
        v = o.get("veredicto") or "sem_analise"
        veredictos[v] += 1

        td = o.get("tipo_demanda")
        if td:
            tipo_demanda[td] += 1

        u = o.get("urgencia") or "baixa"
        urgencias[u] += 1

        for f in (o.get("flags") or []):
            flags_count[f] += 1
            cliente = (o.get("cliente") or "?").strip()
            if cliente and cliente not in flags_obras[f]:
                flags_obras[f].append(cliente)

        consultor = o.get("consultor") or o.get("consultor_inferido") or o.get("consultor_formal")
        if consultor and isinstance(consultor, str):
            nome_limpo = consultor.strip().strip("[]").strip("'").strip('"').strip("—").strip("?").strip()
            # Agrupa pelo PRIMEIRO NOME canônico (evita duplicar "Wesley" vs "Wesley Matheus de...")
            primeiro = nome_limpo.split()[0].lower() if nome_limpo else ""
            if primeiro in DONOS_OPERACIONAIS:
                # Usa o primeiro nome capitalizado como chave canônica
                chave = primeiro.capitalize()
                by_consultor[chave].append(o)

    # ============ FLAGS RECORRENTES ============
    flags_recorrentes = []
    for flag, n in flags_count.most_common():
        flags_recorrentes.append({
            "flag": flag,
            "ocorrencias": n,
            "obras": flags_obras[flag][:10],
        })

    # ============ CONSULTORES ============
    consultores_lista = []
    for nome, obras_list in sorted(by_consultor.items(), key=lambda kv: -len(kv[1])):
        com_acao = [o for o in obras_list if o.get("acao_consultor")]
        # Top ações por urgência alta
        urgentes = [o for o in com_acao if o.get("urgencia") == "alta"]
        urgentes.sort(key=lambda o: 0 if o.get("urgencia") == "alta" else 1)
        acoes_priorizadas = [
            f"{(o.get('cliente') or '?')[:35]} · {o.get('urgencia') or 'baixa'} · {o.get('acao_consultor')}"
            for o in (urgentes + [x for x in com_acao if x not in urgentes])[:5]
        ]
        consultores_lista.append({
            "nome": nome,
            "obras_analisadas": len(obras_list),
            "obras_com_acao": len(com_acao),
            "acoes_priorizadas": acoes_priorizadas,
        })

    # ============ RESUMO EXECUTIVO (template determinístico) ============
    n_coer = veredictos.get("coerente", 0)
    n_des = veredictos.get("status_desatualizado", 0)
    n_aband = veredictos.get("abandono", 0)
    n_det = veredictos.get("detrator", 0)
    n_sem = veredictos.get("sem_analise", 0)
    n_alta = urgencias.get("alta", 0)

    resumo = (
        f"Das {n_total} obras analisadas ({n_ativas} ativas), {n_coer} coerentes "
        f"({100*n_coer/max(n_total,1):.0f}%), {n_des} com status desatualizado "
        f"e {n_aband} em silêncio prolongado (abandono detectado · ≥30d sem msg em obra ativa). "
        f"{n_alta} obras com urgência alta · ação imediata recomendada. "
        f"Detecção via cruzar_kira · 4 regras determinísticas · trilha auditável em cada obra "
        f"(campo `analise_kira_trilha`)."
    )
    if n_det:
        resumo += f" Atenção: {n_det} obra(s) marcada(s) como detrator manifesto."
    if n_sem:
        resumo += f" {n_sem} obras sem análise (resíduo · finalizadas ou erro de fetch)."

    # ============ ATUALIZA ============
    data["total_obras"] = n_total
    data["total_ativas"] = n_ativas
    data["resumo_executivo"] = resumo
    data.setdefault("agregados", {})
    data["agregados"]["veredictos"] = dict(veredictos)
    data["agregados"]["tipo_demanda"] = dict(tipo_demanda)
    data["agregados"]["flags_recorrentes"] = flags_recorrentes
    data["agregados"]["consultores"] = consultores_lista
    # Mantém padroes_cross_obras se existe · não regenera (texto narrativo)
    data["agregados"].setdefault("padroes_cross_obras", [])

    write_discord(DISCORD_PATH, data)

    # Resumo no console
    print(f"[OK] {DISCORD_PATH}")
    print(f"     total_obras: {n_total} · ativas: {n_ativas}")
    print(f"     veredictos: {dict(veredictos)}")
    print(f"     urgências:  {dict(urgencias)}")
    print(f"     flags top 5: {[f['flag'] + '(' + str(f['ocorrencias']) + ')' for f in flags_recorrentes[:5]]}")
    print(f"     consultores: {len(consultores_lista)} (top 3: {[c['nome'][:25] for c in consultores_lista[:3]]})")


if __name__ == "__main__":
    main()
