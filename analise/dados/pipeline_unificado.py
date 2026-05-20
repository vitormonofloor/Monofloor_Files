"""Pipeline unificado da Qualidade Monofloor.

Le 3 fontes (dashboard-data.json, timeline_obras.json, jornadas.json),
cruza por obra_id, calcula indicadores com formulas declaraveis,
gera analise-unificada.json.

Todas as ferramentas (Central, Timeline, Jornada) consomem deste arquivo.
Elimina divergencias entre fontes.

Uso: python analise/dados/pipeline_unificado.py
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

BASE = Path(__file__).parent
DASH_PATH = BASE / "dashboard-data.json"
TL_PATH = BASE.parent / "lab-hermeneuta" / "dados" / "timeline_obras.json"
JORN_PATH = BASE.parent / "lab-hermeneuta" / "dados" / "jornadas.json"
OUT_PATH = BASE / "analise-unificada.json"

FAIXAS = [
    ("PP", 0, 60),
    ("P", 60, 100),
    ("M", 100, 150),
    ("G", 150, 220),
    ("GG", 220, 300),
    ("XG", 300, 99999),
]

CONSULTOR_ALIAS = {
    "luana": "Luana Lima",
    "luana ": "Luana Lima",
    "luana patricia de andrade lima": "Luana Lima",
    "luana lima": "Luana Lima",
    "wesley": "Wesley Carvalho",
    "wesley matheus de carvalho": "Wesley Carvalho",
    "wesley carvalho": "Wesley Carvalho",
    "pedro": "Pedro Santana",
    "pedro alexandre santana": "Pedro Santana",
    "pedro santana": "Pedro Santana",
    "pedro marçal": "Pedro Santana",
    "pedro marcal": "Pedro Santana",
    "juliana santos": "Juliana Santos",
    "juliana": "Juliana Santos",
    "mayara": "Mayara",
    "caroline": "Caroline",
}


def normalizar_consultor(nome):
    if not nome or nome in ("", "[]", "None"):
        return ""
    nome = nome.strip()
    lookup = nome.lower().strip()
    return CONSULTOR_ALIAS.get(lookup, nome)


def carregar_fontes():
    dash = json.loads(DASH_PATH.read_text(encoding="utf-8"))
    tl = json.loads(TL_PATH.read_text(encoding="utf-8"))
    jorn = json.loads(JORN_PATH.read_text(encoding="utf-8"))
    return dash, tl, jorn


def calcular_faixa(m2):
    if not m2 or m2 <= 0:
        return None
    for nome, lo, hi in FAIXAS:
        if lo <= m2 < hi:
            return nome
    return None


def merge_obras(dash, tl, jorn):
    tl_map = {o["obra_id"]: o for o in tl["timelines"]}
    jorn_map = {o["obra_id"]: o for o in jorn["obras"]}

    obras = []
    for d in dash["Q2_OBRAS"]:
        oid = d["id"]
        t = tl_map.get(oid, {})
        j = jorn_map.get(oid, {})

        m2 = d.get("m2") or j.get("metragem") or t.get("metragem") or 0
        if isinstance(m2, str):
            try:
                m2 = float(m2)
            except ValueError:
                m2 = 0

        consultor_raw = t.get("consultor") or d.get("consultor") or ""
        consultor = normalizar_consultor(consultor_raw)

        sr_tl = t.get("score_risco") or {}
        sr_jorn = j.get("score_risco") or {}
        friccao = j.get("friccao") or {}

        veredito = j.get("veredito", "")
        veredito_resumo = ""
        if veredito:
            ponto = veredito.find(".")
            if ponto > 0 and ponto < 150:
                veredito_resumo = veredito[: ponto + 1]
            else:
                veredito_resumo = veredito[:120]

        alerta = t.get("alerta_parada")
        fontes = ["dashboard"]
        if t:
            fontes.append("timeline")
        if j:
            fontes.append("jornadas")

        obra = {
            "id": oid,
            "cliente": d.get("cliente", ""),
            "cidade": d.get("cidade", ""),
            "fase": d.get("fase", ""),
            "status": d.get("status", ""),
            "consultor": consultor,
            "idade": d.get("idade", 0),
            "m2": round(m2, 2) if m2 else 0,
            "faixa_metragem": j.get("faixa_metragem") or calcular_faixa(m2),
            "risco_nivel": sr_tl.get("nivel"),
            "risco_valor": sr_tl.get("valor"),
            "risco_sinais": sr_tl.get("sinais", []),
            "alerta_parada": alerta,
            "estagio": t.get("estagio"),
            "classificacao_origem": (
                t.get("origem_obra", {}).get("origem")
                if isinstance(t.get("origem_obra"), dict)
                else t.get("origem_obra")
            ),
            "classificacao": j.get("classificacao"),
            "friccao_nivel": friccao.get("nivel") if friccao else None,
            "tempo_total_dias": j.get("tempo_total_dias"),
            "tempo_execucao_dias": j.get("tempo_execucao_dias"),
            "tempo_hibernacao_dias": j.get("tempo_hibernacao_dias"),
            "veredito_resumo": veredito_resumo,
            "dias_inativo": t.get("dias_inativo"),
            "fontes": fontes,
        }
        obras.append(obra)

    return obras


def indicador(nome, formula, numerador, denominador):
    valor = round(numerador / denominador, 4) if denominador > 0 else 0
    return {
        "valor": valor,
        "pct": round(valor * 100, 1),
        "formula": formula,
        "numerador": numerador,
        "denominador": denominador,
    }


def calcular_indicadores(obras):
    total = len(obras)

    # --- RADAR (4 eixos, formulas declaraveis) ---
    obras_150 = sum(1 for o in obras if o["idade"] and o["idade"] <= 150)
    sem_alerta = sum(1 for o in obras if not o["alerta_parada"])
    sem_retrab = sum(
        1
        for o in obras
        if o["classificacao"] not in ("entrega_com_retrabalho",) or not o["classificacao"]
    )
    com_score = sum(1 for o in obras if o["risco_nivel"])
    risco_ok = sum(
        1 for o in obras if o["risco_nivel"] in ("baixo", "moderado")
    )

    # retrabalho: contar classificacao = entrega_com_retrabalho
    n_retrab = sum(1 for o in obras if o["classificacao"] == "entrega_com_retrabalho")

    radar = {
        "tempo": indicador("tempo", "obras_idade<=150d / total", obras_150, total),
        "fluxo": indicador("fluxo", "sem_alerta_parada / total", sem_alerta, total),
        "qualidade": indicador(
            "qualidade", "sem_retrabalho / total", total - n_retrab, total
        ),
        "risco": indicador("risco", "(baixo+moderado) / com_score", risco_ok, com_score),
    }

    # --- DISTRIBUICOES ---
    dist_fase = Counter(o["status"] for o in obras)
    dist_risco = Counter(o["risco_nivel"] or "sem_score" for o in obras)
    dist_classificacao = Counter(o["classificacao"] or "sem_dado" for o in obras)

    # faixa metragem com idade media
    faixas = {}
    for o in obras:
        fx = o["faixa_metragem"]
        if not fx:
            fx = "?"
        if fx not in faixas:
            faixas[fx] = {"n": 0, "idades": []}
        faixas[fx]["n"] += 1
        if o["idade"]:
            faixas[fx]["idades"].append(o["idade"])

    dist_faixa = {}
    for fx, data in sorted(faixas.items()):
        idades = data["idades"]
        dist_faixa[fx] = {
            "n_obras": data["n"],
            "idade_media": round(sum(idades) / len(idades), 1) if idades else 0,
        }

    # benchmark: faixa PP como referencia, desvio %
    ref_faixa = "PP"
    ref_idade = dist_faixa.get(ref_faixa, {}).get("idade_media", 0)
    benchmark = {}
    for fx, info in dist_faixa.items():
        desvio = (
            round((info["idade_media"] - ref_idade) / ref_idade * 100, 1)
            if ref_idade > 0 and info["idade_media"] > 0
            else 0
        )
        benchmark[fx] = {
            "n_obras": info["n_obras"],
            "idade_media": info["idade_media"],
            "desvio_pct_vs_PP": desvio,
        }

    acima_bench = 0
    total_bench = 0
    for o in obras:
        fx = o["faixa_metragem"]
        if not fx or fx == "?":
            continue
        ref = dist_faixa.get(fx, {}).get("idade_media", 0)
        if ref > 0 and o["idade"]:
            total_bench += 1
            if o["idade"] > ref:
                acima_bench += 1

    benchmark["_acima_media"] = indicador(
        "acima_benchmark",
        "obras_idade>media_faixa / obras_com_faixa",
        acima_bench,
        total_bench,
    )

    # --- RETRABALHO ---
    retrab_obras = [o for o in obras if o["classificacao"] == "entrega_com_retrabalho"]
    retrab_por_consultor = Counter(
        o["consultor"] or "sem_consultor" for o in retrab_obras
    )

    retrabalho = {
        "total": len(retrab_obras),
        "pct": round(len(retrab_obras) / total * 100, 1) if total > 0 else 0,
        "por_consultor": dict(
            sorted(retrab_por_consultor.items(), key=lambda x: -x[1])
        ),
    }

    # --- CONSULTOR ---
    cons_stats = {}
    for o in obras:
        c = o["consultor"] or "sem_consultor"
        if c not in cons_stats:
            cons_stats[c] = {"n_obras": 0, "idades": [], "retrabalho": 0, "alertas": 0}
        cons_stats[c]["n_obras"] += 1
        if o["idade"]:
            cons_stats[c]["idades"].append(o["idade"])
        if o["classificacao"] == "entrega_com_retrabalho":
            cons_stats[c]["retrabalho"] += 1
        if o["alerta_parada"]:
            cons_stats[c]["alertas"] += 1

    consultor = {}
    for c, s in sorted(cons_stats.items(), key=lambda x: -x[1]["n_obras"]):
        idades = s["idades"]
        consultor[c] = {
            "n_obras": s["n_obras"],
            "idade_media": round(sum(idades) / len(idades), 1) if idades else 0,
            "retrabalho": s["retrabalho"],
            "pct_retrabalho": (
                round(s["retrabalho"] / s["n_obras"] * 100, 1) if s["n_obras"] > 0 else 0
            ),
            "alertas_parada": s["alertas"],
        }

    # --- ALERTAS ---
    alertas_list = [o for o in obras if o["alerta_parada"]]
    alertas_tipo = Counter()
    for o in alertas_list:
        ap = o["alerta_parada"]
        if isinstance(ap, dict):
            alertas_tipo[ap.get("tipo", "desconhecido")] += 1
        else:
            alertas_tipo["desconhecido"] += 1

    alertas = {
        "total": len(alertas_list),
        "por_tipo": dict(sorted(alertas_tipo.items(), key=lambda x: -x[1])),
    }

    # --- GARGALO (fase com mais obras) ---
    fase_top = dist_fase.most_common(1)
    gargalo = {
        "fase": fase_top[0][0] if fase_top else "",
        "n_obras": fase_top[0][1] if fase_top else 0,
        "pct": round(fase_top[0][1] / total * 100, 1) if fase_top and total > 0 else 0,
    }

    return {
        "radar": radar,
        "distribuicao_fase": dict(sorted(dist_fase.items(), key=lambda x: -x[1])),
        "distribuicao_risco": dict(sorted(dist_risco.items(), key=lambda x: -x[1])),
        "distribuicao_classificacao": dict(
            sorted(dist_classificacao.items(), key=lambda x: -x[1])
        ),
        "benchmark_faixa": benchmark,
        "retrabalho": retrabalho,
        "consultor": consultor,
        "alertas": alertas,
        "gargalo": gargalo,
        "portfolio": {
            "total": total,
            "idade_media": round(sum(o["idade"] for o in obras if o["idade"]) / total, 1)
            if total > 0
            else 0,
            "idade_mediana": sorted(o["idade"] for o in obras if o["idade"])[
                len([o for o in obras if o["idade"]]) // 2
            ]
            if obras
            else 0,
        },
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("Pipeline unificado Qualidade Monofloor")
    print("=" * 50)

    dash, tl, jorn = carregar_fontes()
    print(f"Fontes: dashboard {len(dash['Q2_OBRAS'])} | timeline {len(tl['timelines'])} | jornadas {len(jorn['obras'])}")

    obras = merge_obras(dash, tl, jorn)
    print(f"Obras mergeadas: {len(obras)}")

    n3 = sum(1 for o in obras if len(o["fontes"]) == 3)
    n2 = sum(1 for o in obras if len(o["fontes"]) == 2)
    n1 = sum(1 for o in obras if len(o["fontes"]) == 1)
    print(f"Cobertura: 3 fontes={n3} | 2 fontes={n2} | 1 fonte={n1}")

    indicadores = calcular_indicadores(obras)

    resultado = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "fontes": {
            "dashboard": {
                "arquivo": "dashboard-data.json",
                "snapshot_date": dash.get("snapshot_date"),
                "n_obras": len(dash["Q2_OBRAS"]),
            },
            "timeline": {
                "arquivo": "timeline_obras.json",
                "gerado_em": tl.get("gerado_em"),
                "n_obras": len(tl["timelines"]),
            },
            "jornadas": {
                "arquivo": "jornadas.json",
                "gerado_em": jorn.get("gerado_em"),
                "n_obras": len(jorn["obras"]),
            },
        },
        "universo": {
            "ativas": len(obras),
            "com_timeline": sum(1 for o in obras if "timeline" in o["fontes"]),
            "com_jornada": sum(1 for o in obras if "jornadas" in o["fontes"]),
            "intersecao_3": n3,
        },
        "obras": obras,
        "indicadores": indicadores,
        "tendencia_mensal": jorn.get("tendencia_mensal", []),
        "capacidade": jorn.get("capacidade"),
    }

    OUT_PATH.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nOutput: {OUT_PATH}")
    print(f"Tamanho: {OUT_PATH.stat().st_size / 1024:.0f} KB")

    # resumo indicadores
    r = indicadores["radar"]
    print(f"\n--- RADAR (formulas declaraveis) ---")
    for eixo in ["tempo", "fluxo", "qualidade", "risco"]:
        i = r[eixo]
        print(f"  {eixo}: {i['pct']}% = {i['formula']} = {i['numerador']}/{i['denominador']}")

    p = indicadores["portfolio"]
    print(f"\n--- PORTFOLIO ---")
    print(f"  Total: {p['total']} obras | Media: {p['idade_media']}d | Mediana: {p['idade_mediana']}d")

    g = indicadores["gargalo"]
    print(f"  Gargalo: {g['fase']} ({g['n_obras']} obras, {g['pct']}%)")

    rt = indicadores["retrabalho"]
    print(f"  Retrabalho: {rt['total']} obras ({rt['pct']}%)")
    for c, n in list(rt["por_consultor"].items())[:3]:
        print(f"    {c}: {n}")

    a = indicadores["alertas"]
    print(f"  Alertas parada: {a['total']}")

    print(f"\n--- BENCHMARK FAIXA ---")
    for fx, info in indicadores["benchmark_faixa"].items():
        if fx == "_acima_media":
            continue
        print(f"  {fx}: {info['n_obras']} obras, {info['idade_media']}d, desvio {info['desvio_pct_vs_PP']:+.1f}%")
    am = indicadores["benchmark_faixa"]["_acima_media"]
    print(f"  Acima media faixa: {am['pct']}% ({am['numerador']}/{am['denominador']})")

    # validacao
    erros = validar_sanidade(resultado)
    if erros:
        print(f"\n!!! SANIDADE FALHOU ({len(erros)} erros) !!!")
        for e in erros:
            print(f"  ERRO: {e}")
        sys.exit(1)
    else:
        print("\nSanidade OK (0 erros).")

    print("Pipeline OK.")


def validar_sanidade(resultado):
    """Guardrail: bugs devem gritar, nao patinar."""
    erros = []
    obras = resultado["obras"]
    ind = resultado["indicadores"]
    total = len(obras)

    if total < 180 or total > 280:
        erros.append(f"Total obras {total} fora do range esperado (180-280)")

    ids = [o["id"] for o in obras]
    if len(ids) != len(set(ids)):
        erros.append(f"IDs duplicados: {len(ids) - len(set(ids))}")

    for eixo in ["tempo", "fluxo", "qualidade", "risco"]:
        v = ind["radar"][eixo]["valor"]
        if v < 0 or v > 1:
            erros.append(f"Radar {eixo} = {v} fora de [0,1]")
        n = ind["radar"][eixo]["numerador"]
        d = ind["radar"][eixo]["denominador"]
        if n > d:
            erros.append(f"Radar {eixo}: numerador {n} > denominador {d}")

    rt = ind["retrabalho"]["total"]
    if rt > total:
        erros.append(f"Retrabalho {rt} > total {total}")

    dist_risco = ind["distribuicao_risco"]
    soma_risco = sum(dist_risco.values())
    if soma_risco != total:
        erros.append(f"Dist risco soma {soma_risco} != total {total}")

    sem_cons = sum(1 for o in obras if not o["consultor"])
    if sem_cons > total * 0.3:
        erros.append(f"Sem consultor: {sem_cons}/{total} (>30%)")

    return erros


if __name__ == "__main__":
    main()
