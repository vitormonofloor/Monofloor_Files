"""
Seleciona 10 obras-piloto pra Fase B
=====================================

Cruza painel-snapshot.json (227 obras ativas com status/fase/consultor)
com grupos.json do Telethon (572 obras técnicas).

Pareamento: fuzzy match por nome do cliente.
   painel.clienteNome  ≈  primeiro nome dentro do título do grupo após "MMAA - UF -"
   ex: painel "TAÍSA MENDONÇA DE OLIVEIRA"  ↔  grupo "0625 - SP - TAÍSA MENDONÇA / Wesley"

Critério das 10 piloto:
- match alto (>= 70% similaridade)
- ativo no painel (ativa=true)
- atividade recente no Telegram (dias_inativo <= 30)
- diversidade de status (pega 1-2 de cada bucket relevante)

Saída: piloto.json com 10 obras estruturadas (id_painel, id_grupo, dados ambos lados)
"""

import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

ROOT = Path(__file__).parent
LAB_DADOS = ROOT.parent.parent / "dados"
PAINEL = LAB_DADOS / "painel-snapshot.json"
GRUPOS = ROOT / "grupos.json"


def normalize(s: str) -> str:
    """Remove acentos, lowercase, só letras e espaços."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_cliente_from_grupo(nome: str) -> str:
    """
    Extrai nome do cliente do título do grupo.
    "0625 - SP - TAÍSA MENDONÇA / Wesley" → "TAÍSA MENDONÇA"
    "0825 - SP - JOAO GALLUCCI RODRIGUES / Mariangela" → "JOAO GALLUCCI RODRIGUES"
    "Obra - LEONARDO FERIANI HERNANDEZ PLANA" → "LEONARDO FERIANI HERNANDEZ PLANA"
    """
    s = nome
    # Remove prefixo "MMAA - UF - " ou variações
    s = re.sub(r"^\s*\d{2}[/\-]?\d{2}\s*[/\-]?\s*[A-Z]{2}\s*[/\-]+\s*", "", s, flags=re.IGNORECASE)
    # Remove prefixo "MMAA - " sem UF
    s = re.sub(r"^\s*\d{2}[/\-]?\d{2}\s*[-/]+\s*", "", s)
    # Remove prefixo "Obra - " ou "OBRA - "
    s = re.sub(r"^\s*OBRA\s*-\s*", "", s, flags=re.IGNORECASE)
    # Remove sufixo " / Consultor" (corta no primeiro / ou //)
    s = re.split(r"\s*[/]+\s*", s)[0]
    return s.strip()


def similarity(a: str, b: str) -> float:
    """Razão de similaridade [0,1] · usa SequenceMatcher do stdlib."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def main():
    if not PAINEL.exists():
        print(f"ERRO: {PAINEL} não encontrado")
        sys.exit(1)
    if not GRUPOS.exists():
        print(f"ERRO: {GRUPOS} não encontrado · rode listar_grupos.py primeiro")
        sys.exit(1)

    painel = json.loads(PAINEL.read_text(encoding="utf-8"))
    grupos_data = json.loads(GRUPOS.read_text(encoding="utf-8"))
    grupos = grupos_data["grupos"]

    obras_painel = [o for o in painel if o.get("ativa")]
    grupos_obra = [g for g in grupos if g["tipo_canal"] == "obra"]
    print(f"Painel ativas: {len(obras_painel)}")
    print(f"Grupos Telegram (obra técnica): {len(grupos_obra)}")
    print()

    # Pra cada obra do painel, acha o melhor match no Telegram
    pareamentos = []
    for obra in obras_painel:
        cliente = obra.get("clienteNome", "")
        if not cliente:
            continue
        melhor = None
        melhor_sim = 0.0
        for g in grupos_obra:
            cand = extract_cliente_from_grupo(g["nome"])
            sim = similarity(cliente, cand)
            if sim > melhor_sim:
                melhor_sim = sim
                melhor = g
        pareamentos.append({
            "obra": obra,
            "grupo": melhor,
            "similaridade": round(melhor_sim, 3),
            "cliente_painel": cliente,
            "cliente_grupo": extract_cliente_from_grupo(melhor["nome"]) if melhor else None,
        })

    # Filtra: similaridade >= 0.70 e Telegram ativo (≤30d)
    candidatos = [
        p for p in pareamentos
        if p["similaridade"] >= 0.70
        and p["grupo"]
        and (p["grupo"].get("dias_inativo") or 9999) <= 30
    ]

    # Ordena por similaridade desc · grupos com match perfeito primeiro
    candidatos.sort(key=lambda p: (-p["similaridade"], p["grupo"].get("dias_inativo") or 9999))

    print(f"Candidatos com sim>=0.70 e Telegram ativo ≤30d: {len(candidatos)}")
    print()

    # Distribui por status pra ter diversidade nas 10 piloto
    by_status = {}
    for c in candidatos:
        st = c["obra"].get("status") or "?"
        by_status.setdefault(st, []).append(c)

    print("Distribuição de candidatos por status:")
    for st, lst in sorted(by_status.items(), key=lambda x: -len(x[1])):
        print(f"  {st:25s} {len(lst):3d}")
    print()

    # Pega round-robin por status até 10
    piloto = []
    visto = set()
    while len(piloto) < 10:
        progresso = False
        for st in sorted(by_status.keys()):
            if len(piloto) >= 10:
                break
            for c in by_status[st]:
                key = c["obra"]["id"]
                if key in visto:
                    continue
                piloto.append(c)
                visto.add(key)
                progresso = True
                break
        if not progresso:
            break

    print(f"=== 10 OBRAS-PILOTO ===\n")
    print(f"{'#':<3}{'sim':<6}{'status':<22}{'fase':<22}{'consultor':<22}{'idade_p':<8}{'tg_d':<5}{'cliente'}")
    for i, c in enumerate(piloto, 1):
        o = c["obra"]
        g = c["grupo"]
        print(f"{i:<3}{c['similaridade']:<6}"
              f"{(o.get('status') or '')[:20]:<22}"
              f"{(o.get('faseAtual') or '')[:20]:<22}"
              f"{(o.get('consultorNome') or '')[:20]:<22}"
              f"{(o.get('idade_dias') or '?'):<8}"
              f"{(g.get('dias_inativo') or '?'):<5}"
              f"{(o.get('clienteNome') or '')[:40]}")

    # Salva piloto.json
    out = {
        "gerado_em": grupos_data.get("gerado_em"),
        "total_piloto": len(piloto),
        "piloto": [
            {
                "obra_id": c["obra"]["id"],
                "cliente": c["obra"]["clienteNome"],
                "consultor": c["obra"].get("consultorNome"),
                "status": c["obra"].get("status"),
                "fase": c["obra"].get("faseAtual"),
                "metragem": c["obra"].get("projetoMetragem"),
                "idade_dias_painel": c["obra"].get("idade_dias"),
                "cidade": c["obra"].get("projetoCidade"),
                "telegram": {
                    "grupo_id": c["grupo"]["id"],
                    "grupo_nome": c["grupo"]["nome"],
                    "ultima_msg": c["grupo"].get("ultima_mensagem_data"),
                    "dias_inativo": c["grupo"].get("dias_inativo"),
                    "membros": c["grupo"].get("membros"),
                },
                "match_similaridade": c["similaridade"],
                "painel_completo": c["obra"],
            }
            for c in piloto
        ],
    }
    out_path = ROOT / "piloto.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] {out_path}")


if __name__ == "__main__":
    main()
