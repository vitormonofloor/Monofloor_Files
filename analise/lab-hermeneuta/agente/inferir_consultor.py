"""
Adiciona consultor_inferido em discordancias-v3.json
====================================================

Inferência baseada em quem TOMA DECISÃO no grupo Telegram (não quem só fala mais):
- REPULLO       → Luana Monofloor (alta) · declara problema, define escopo, mobiliza equipe
- PAULA CORREA  → Luana Monofloor (alta) · fio condutor em todos os momentos críticos
- MARIA HEYDI   → Juliana Monofloor (media-alta) · reunião com cliente é c/ Juliana · relatórios enviados pra ela
- MAYARA        → MÚLTIPLOS sem dono (baixa) · Wesley formal não posta · operam Pedro/Jonathan/Luana/Vinícius

Realocação dos agregados.consultores:
- Luana PA: ganha REPULLO + PAULA CORREA
- Juliana Santos: ganha MARIA HEYDI
- SEM CONSULTOR: removido
- Wesley: nota MAYARA como "consultor formal não atua"
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import write_json_atomic, setup_utf8

setup_utf8()

ROOT = Path(__file__).parent.parent
JSON_PATH = ROOT / "dados" / "discordancias-v3.json"

INFERENCIAS = {
    # obra_id (uuid) → consultor_inferido
    "2369c899-509f-4deb-a767-03f244854492": {  # REPULLO
        "nome": "Luana Monofloor",
        "confianca": "alta",
        "evidencia": "Declara o problema do José Mário (msg 1310 · 24/03), pede escopo do reparo de parede (msg 1322 · 28/04), mobiliza Kettlyn pra medição (msg 1323). Braiam apenas intermedia com arquiteta Débora; Kettlyn é apoio técnico."
    },
    "c6908776-f200-4b20-87eb-0e9d9a80eda7": {  # PAULA CORREA
        "nome": "Luana Monofloor",
        "confianca": "alta",
        "evidencia": "Único nome em todos os momentos críticos: registra patologia inicial (msg 1173), documenta quase-distrato (msg 1175 · 23/09), registra falha de cor pós-retoque (msg 1193), justifica adiamento por chuva (msg 1202), publica reaplicação para 06/05 (msg 1207)."
    },
    "db76891b-3385-45fe-8899-550517789ae1": {  # MARIA HEYDI
        "nome": "Juliana Monofloor",
        "confianca": "media",
        "evidencia": "Reunião online com cliente foi 'cliente × Juliana 16h' (msg 6 · 31/03). Pedro envia relatório de VT pra ela: 'Relatório enviado 17/04 Juliana' (msg 25). Juliana é destinatária dos entregáveis; Pedro/Kettlyn/Vinícius são apoio."
    },
    # obra_id de MAYARA · consultor formal Wesley não atua
    "c99144e7-a27f-4e49-9ffa-5399d97bafce": {  # MAYARA
        "nome": "MULTIPLOS · consultor formal ausente",
        "confianca": "baixa",
        "evidencia": "Wesley Matheus (formal no painel) não posta em nenhuma das 39 mensagens. Operam Pedro, Jonathan, Kettlyn, Luana, Rodrigo e Vinícius — sem dono único. A 'voz' da cliente (15/12 e 19/12) vem repassada pelo consultor Pedro."
    },
}


def main():
    if not JSON_PATH.exists():
        print(f"ERRO: {JSON_PATH} não encontrado")
        sys.exit(1)

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    # 1. Adiciona consultor_inferido em cada obra · marca flag também
    realocacoes = {}  # consultor_real → list de obras realocadas
    for o in data.get("obras", []):
        oid = o.get("obra_id")
        if oid in INFERENCIAS:
            inf = INFERENCIAS[oid]
            o["consultor_formal"] = o.get("consultor")  # preserva o original
            o["consultor_inferido"] = inf

            # Adiciona flag · merge sem duplicar
            flags = o.get("flags") or []
            if "consultor_divergente" not in flags:
                flags.append("consultor_divergente")
            o["flags"] = flags

            # Track realocação
            real = inf["nome"]
            realocacoes.setdefault(real, []).append({
                "cliente": o.get("cliente"),
                "obra_id": oid,
                "urgencia": o.get("urgencia"),
                "acao": o.get("acao_consultor"),
            })

    # 2. Atualiza agregados.consultores
    ag = data.setdefault("agregados", {})
    cs = ag.get("consultores", [])

    # Remove SEM CONSULTOR · suas obras voltam pros consultores reais
    cs_novo = [c for c in cs if c.get("nome") != "SEM CONSULTOR"]

    # Adiciona obras realocadas aos consultores reais existentes ou cria novos
    for nome_real, obras in realocacoes.items():
        # Pula MAYARA (consultor formal Wesley · só adiciona nota, não realoca)
        if nome_real.startswith("MULTIPLOS"):
            # Acha o card do Wesley e adiciona nota
            for c in cs_novo:
                if "Wesley" in c.get("nome", ""):
                    c.setdefault("nota", "Em MAYARA, Wesley é consultor formal mas não posta no grupo · operam Pedro/Jonathan/Luana/Vinícius")
            continue

        # Acha card existente
        encontrado = None
        for c in cs_novo:
            # Match por primeiro nome (Luana, Juliana, etc)
            primeiro_real = nome_real.split()[0].lower()
            primeiro_existente = c.get("nome", "").split()[0].lower()
            if primeiro_real == primeiro_existente:
                encontrado = c
                break

        if encontrado:
            encontrado["obras_analisadas"] = encontrado.get("obras_analisadas", 0) + len(obras)
            encontrado["obras_com_acao"] = encontrado.get("obras_com_acao", 0) + len(obras)
            for o in obras:
                acao_str = f"{o['cliente']} · {o['urgencia']} · {o['acao']} [INFERIDO · sem atribuição formal no painel]"
                encontrado.setdefault("acoes_priorizadas", []).append(acao_str)
        else:
            cs_novo.append({
                "nome": nome_real + " (inferido)",
                "obras_analisadas": len(obras),
                "obras_com_acao": len(obras),
                "acoes_priorizadas": [
                    f"{o['cliente']} · {o['urgencia']} · {o['acao']} [INFERIDO · sem atribuição formal no painel]"
                    for o in obras
                ],
            })

    # Ordena: maior número de obras primeiro
    cs_novo.sort(key=lambda c: -c.get("obras_analisadas", 0))
    ag["consultores"] = cs_novo

    # 3. Atualiza flags_recorrentes (consultor_divergente sobe)
    fr = ag.get("flags_recorrentes", [])
    obras_div = [o.get("cliente") for o in data["obras"] if "consultor_divergente" in (o.get("flags") or [])]

    cd = next((f for f in fr if f.get("flag") == "consultor_divergente"), None)
    if cd:
        cd["ocorrencias"] = len(obras_div)
        cd["obras"] = obras_div
    else:
        fr.append({
            "flag": "consultor_divergente",
            "ocorrencias": len(obras_div),
            "obras": obras_div,
        })
    fr.sort(key=lambda f: -f.get("ocorrencias", 0))
    ag["flags_recorrentes"] = fr

    # 4. Adiciona nota no resumo executivo (append)
    resumo = data.get("resumo_executivo", "")
    nota = (" Atualização 2026-04-29 pós-revisão: as 3 obras sem consultor formal foram realocadas — "
            "Luana conduz REPULLO e PAULA CORREA, Juliana conduz MARIA HEYDI · em MAYARA o consultor formal "
            "(Wesley) não atua no grupo, operação distribuída entre Pedro/Jonathan/Luana/Vinícius.")
    if "Atualização 2026-04-29" not in resumo:
        data["resumo_executivo"] = resumo + nota

    # Salva
    write_json_atomic(JSON_PATH, data)
    print(f"[OK] {JSON_PATH} atualizado")
    print()
    print("Realocações:")
    for nome, obras in realocacoes.items():
        print(f"  → {nome} · {len(obras)} obra(s):")
        for o in obras:
            print(f"     - {o['cliente']}")


if __name__ == "__main__":
    main()
