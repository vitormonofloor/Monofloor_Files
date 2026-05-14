"""
E3 — Classificar obras 2026 em perfis de comportamento.
Parte do escopo ESCOPO_TIMELINE.md (E3 Padroes emergentes).
"""
import json
from collections import Counter
from datetime import datetime

data = json.loads(open("lab-hermeneuta/dados/timeline_obras.json", encoding="utf-8").read())
timelines = data["timelines"]

MARCOS_FLUXO = [
    "contrato_assinado", "escopo_em_revisao", "escopo_aprovado", "cor_aprovada",
    "amostra_solicitada", "vt_agendada", "vt_realizada", "material_produzido",
    "material_entregue", "equipe_chegou", "camada_produto", "ultima_camada",
    "finalizacao", "aprovacao_cliente", "vistoria_cliente", "reprovacao_retorno",
]

obras = []
for o in timelines:
    dec = o.get("data_exec_confirmada", "")
    dep = o.get("data_exec_prevista", "")
    marcos_raw = o.get("marcos") or []
    primeiro_exec = None
    for m in sorted(marcos_raw, key=lambda x: x.get("data", "")):
        if m.get("fase") == "2_execucao" and m.get("tipo") not in ("ocorrencia_formal",):
            primeiro_exec = m.get("data", "")[:10]
            break
    inicio = None
    if dec and dec[:4] == "2026":
        inicio = dec[:10]
    elif primeiro_exec and primeiro_exec[:4] == "2026":
        inicio = primeiro_exec
    elif dep and dep[:4] == "2026":
        inicio = dep[:10]
    if not inicio:
        continue

    marcos = sorted(marcos_raw, key=lambda m: m.get("data", ""))
    seq = {}
    for m in marcos:
        t = m.get("tipo")
        if t in MARCOS_FLUXO and t not in seq:
            seq[t] = m.get("data", "")[:10]

    tem = set(seq.keys())
    n_marcos = len(marcos_raw)
    tem_exec = bool(tem & {"equipe_chegou", "camada_produto"})
    tem_final = "finalizacao" in tem
    tem_repro = "reprovacao_retorno" in tem
    tem_vt = bool(tem & {"vt_agendada", "vt_realizada"})
    tem_material = bool(tem & {"material_produzido", "material_entregue"})

    dt_contrato_exec = None
    if "contrato_assinado" in seq and ("equipe_chegou" in seq or "camada_produto" in seq):
        exec_dt = seq.get("equipe_chegou") or seq.get("camada_produto")
        try:
            dt_contrato_exec = (datetime.fromisoformat(exec_dt) - datetime.fromisoformat(seq["contrato_assinado"])).days
        except:
            pass

    if n_marcos == 0:
        perfil = "A_sem_marcos"
    elif not tem_exec and not tem_final:
        perfil = "B_pre_obra_pura"
    elif tem_exec and not tem_final and not tem_repro:
        perfil = "C_em_execucao"
    elif tem_final and not tem_repro:
        perfil = "D_caminho_feliz"
    elif tem_repro and tem_final:
        perfil = "E_final_com_reprovacao"
    elif tem_repro and not tem_final:
        perfil = "F_reprovacao_sem_final"
    elif tem_exec:
        perfil = "C_em_execucao"
    else:
        perfil = "X_indefinido"

    obras.append({
        "cliente": o.get("cliente", "?")[:40],
        "status": o.get("status", "?"),
        "fase": o.get("fase_atual_painel", "?"),
        "perfil": perfil,
        "n_marcos": n_marcos,
        "n_chave": len(seq),
        "tem_vt": tem_vt,
        "tem_material": tem_material,
        "dt_contrato_exec": dt_contrato_exec,
        "tem_repro": tem_repro,
        "seq_keys": sorted(seq.keys(), key=lambda k: seq[k]),
    })

perfis = Counter(o["perfil"] for o in obras)

LABELS = {
    "A_sem_marcos": "Sem marcos (planejamento puro / sem Telegram)",
    "B_pre_obra_pura": "So pre-obra (contrato/escopo/VT, sem execucao)",
    "C_em_execucao": "Em execucao (equipe/camada, sem finalizar)",
    "D_caminho_feliz": "Finalizada SEM reprovacao",
    "E_final_com_reprovacao": "Finalizada COM reprovacao",
    "F_reprovacao_sem_final": "Reprovacao SEM finalizacao registrada",
}

print(f"PERFIS DE COMPORTAMENTO ({len(obras)} obras 2026):")
print()
for p, n in sorted(perfis.items()):
    pct = round(n / len(obras) * 100)
    print(f"  {p}: {n} obras ({pct}%) -- {LABELS.get(p, p)}")

for perfil_nome in sorted(perfis.keys()):
    grupo = [o for o in obras if o["perfil"] == perfil_nome]
    print()
    print(f"--- {perfil_nome} ({len(grupo)} obras) ---")

    st = Counter(o["status"] for o in grupo)
    print(f"  Status: {dict(st.most_common(5))}")

    vt = sum(1 for o in grupo if o["tem_vt"])
    mat = sum(1 for o in grupo if o["tem_material"])
    print(f"  Com VT: {vt}/{len(grupo)} ({round(vt / len(grupo) * 100)}%)"
          f" | Com material: {mat}/{len(grupo)} ({round(mat / len(grupo) * 100)}%)")

    tempos = [o["dt_contrato_exec"] for o in obras if o["perfil"] == perfil_nome and o["dt_contrato_exec"] is not None and o["dt_contrato_exec"] >= 0]
    if tempos:
        tempos.sort()
        print(f"  Contrato->Exec: mediana {tempos[len(tempos) // 2]}d"
              f" | min {min(tempos)}d | max {max(tempos)}d (N={len(tempos)})")

    exemplos = sorted(grupo, key=lambda x: -x["n_marcos"])[:5]
    for e in exemplos:
        seq_resumo = " > ".join(e["seq_keys"][:8])
        cli = e["cliente"]
        sts = e["status"]
        nm = e["n_marcos"]
        print(f"    {cli:<35} {sts:<20} {nm:>3}m | {seq_resumo}")

# Resumo cruzado
print()
print("=" * 80)
print("RESUMO CRUZADO")
print()
total = len(obras)
com_exec = sum(1 for o in obras if o["perfil"] not in ("A_sem_marcos", "B_pre_obra_pura"))
com_final = perfis.get("D_caminho_feliz", 0) + perfis.get("E_final_com_reprovacao", 0)
com_repro = perfis.get("E_final_com_reprovacao", 0) + perfis.get("F_reprovacao_sem_final", 0)
print(f"  Total 2026: {total}")
print(f"  Chegaram a executar: {com_exec} ({round(com_exec/total*100)}%)")
print(f"  Finalizaram: {com_final} ({round(com_final/total*100)}%)")
print(f"  Com reprovacao: {com_repro} ({round(com_repro/total*100)}%)")
if com_final > 0:
    taxa_repro_final = perfis.get("E_final_com_reprovacao", 0)
    print(f"  Taxa reprovacao entre finalizadas: {taxa_repro_final}/{com_final} ({round(taxa_repro_final/com_final*100)}%)")

vt_total = sum(1 for o in obras if o["tem_vt"] and o["perfil"] not in ("A_sem_marcos",))
exec_total = sum(1 for o in obras if o["perfil"] not in ("A_sem_marcos", "B_pre_obra_pura"))
print(f"  Obras com VT registrada (excl. sem marcos): {vt_total}/{len(obras) - perfis.get('A_sem_marcos', 0)} ({round(vt_total/(len(obras) - perfis.get('A_sem_marcos', 0))*100)}%)")
