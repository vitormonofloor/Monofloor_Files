"""
Extrai cores das mensagens do Telegram + agrega tendências
===========================================================

Pra cada obra:
1. Varre msgs cronologicamente buscando padrão "COR: NOME"
2. Normaliza nome (remove sufixos " - Stelion", "(a definir)", "PERSONALIZADAS", etc)
3. Identifica:
   - cores_definidas (lista de cores reais mencionadas)
   - cor_atual (mais recentemente mencionada nos cards de programação)
   - tem_pendencia (alguma menção a "a definir")

No fim, agrega:
- top_cores (ranking global)
- cores por bucket temporal
- obras com cor pendente

Custo zero.
"""

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import write_json_atomic, setup_utf8

setup_utf8()

ROOT = Path(__file__).parent.parent
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"
SNAPSHOT_PATH = ROOT / "agente" / "telethon" / "telegram-snapshot.json"

HOJE = datetime.now(timezone.utc)

# Padrão "COR: ALGO" até quebra de linha ou pontuação forte
RE_COR = re.compile(r"COR\s*:\s*([^\n\r]{2,80})", re.IGNORECASE | re.MULTILINE)

# Termos que indicam pendência (não são cores reais)
RE_PENDENCIA = re.compile(r"\ba\s*definir\b|\bdefinir\b|\bpersonalizadas?\b\s*\(a\s*definir\)|^\s*-\s*$", re.IGNORECASE)

# Linhas de produto pra remover do nome da cor
LINHAS = ["stelion", "lilit", "stelion - lilit", "lilit - stelion"]


def parse_iso(s: str):
    if not s: return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None


def normalizar_cor(raw: str) -> tuple[str | None, bool]:
    """Retorna (nome_cor_normalizado, eh_pendencia). Se for só pendência, nome_cor=None."""
    if not raw:
        return None, False
    s = raw.strip().rstrip(".,;").strip()

    # Detecta pendência
    eh_pend = bool(RE_PENDENCIA.search(s))

    # Limpa parênteses tipo "(a definir)"
    s = re.sub(r"\s*\([^)]*\)", "", s).strip()

    # Se sobrou só "a definir" ou similar, não é cor
    if not s or RE_PENDENCIA.fullmatch(s):
        return None, eh_pend

    # Pode haver múltiplas cores separadas por " e " ou ","
    # Mas pra MVP pegamos a string completa como uma "cor composta" se tiver várias
    # (separação fica em iteração futura)

    # Remove sufixos de linha (Stelion, Lilit) — mantém a cor real
    parts = re.split(r"\s*-\s*", s)
    parts_filtradas = [p.strip() for p in parts if p.strip().lower() not in LINHAS and p.strip()]

    if not parts_filtradas:
        return None, eh_pend

    # Junta com " - " se sobraram múltiplas (ex: "Personalizada - Creme de abacate")
    nome = " - ".join(parts_filtradas)

    # Title case pra padronizar
    nome_norm = " ".join(p.capitalize() if not p.isupper() or len(p) <= 3 else p.title() for p in nome.split())

    # Casos especiais comuns
    nome_norm = nome_norm.replace("Iii", "III")
    nome_norm = nome_norm.replace("Ii", "II")

    return nome_norm, eh_pend


def extrair_cores_obra(snapshot_obra: dict) -> dict:
    """Retorna { atual, historico, definidas, tem_pendencia, total_mencoes, ultima_msg_data }."""
    msgs = snapshot_obra.get("telegram", {}).get("mensagens", [])
    historico = []  # lista de {cor, data, msg_id}
    pendencias = []
    cores_distintas = set()
    ultima_msg_com_cor = None

    for m in msgs:
        txt = m.get("texto") or ""
        for mat in RE_COR.finditer(txt):
            raw = mat.group(1)
            cor, eh_pend = normalizar_cor(raw)
            data = m.get("data") or ""
            if cor:
                historico.append({
                    "cor": cor,
                    "msg_data": data[:16],
                    "msg_id": m.get("id"),
                    "raw": raw.strip()[:60],
                })
                cores_distintas.add(cor)
                if not ultima_msg_com_cor or data > ultima_msg_com_cor["msg_data"]:
                    ultima_msg_com_cor = historico[-1]
            elif eh_pend:
                pendencias.append({
                    "msg_data": data[:16],
                    "msg_id": m.get("id"),
                    "raw": raw.strip()[:60],
                })

    # Cor atual = mais recente nas msgs (em ordem cronológica · pega as últimas)
    historico.sort(key=lambda h: h["msg_data"])
    cores_recentes = []
    if historico:
        # Pega cores das últimas 3 msgs com COR (provavelmente cards de programação recentes)
        ultimas_msgs = historico[-5:] if len(historico) >= 5 else historico
        ultima_data_msg = ultimas_msgs[-1]["msg_data"]
        cores_recentes = list({h["cor"] for h in ultimas_msgs if h["msg_data"] == ultima_data_msg})

    return {
        "definidas": sorted(cores_distintas),
        "atual": cores_recentes,  # cores da menção mais recente
        "historico": historico,
        "tem_pendencia": len(pendencias) > 0,
        "total_mencoes": len(historico) + len(pendencias),
        "ultima_msg_com_cor": ultima_msg_com_cor["msg_data"] if ultima_msg_com_cor else None,
    }


def main():
    if not DISCORD_PATH.exists() or not SNAPSHOT_PATH.exists():
        print("ERRO: arquivos faltando")
        sys.exit(1)

    discord = json.loads(DISCORD_PATH.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    snap_by_id = {o["obra_id"]: o for o in snapshot.get("obras", [])}

    # Por obra: extrai cores
    contador_atual = Counter()  # ranking · usa só "atual"
    pendentes = []  # obras com cor a definir

    print(f"{'Cliente':<42} {'Cor atual':<35} {'Pend?':<6} {'Distintas'}")
    print("-" * 110)

    for obra in discord.get("obras", []):
        oid = obra.get("obra_id")
        snap = snap_by_id.get(oid)
        if not snap:
            obra["cores"] = {"erro": "sem snapshot"}
            continue

        cores = extrair_cores_obra(snap)
        obra["cores"] = cores

        # Atualiza agregados (só os que a tela usa)
        bucket_id = ((obra.get("regua") or {}).get("bucket") or {}).get("id") or "?"
        for c in cores["atual"]:
            contador_atual[c] += 1

        if cores["tem_pendencia"] and not cores["atual"]:
            # Tem pendência E não tem cor definida ainda
            pendentes.append({
                "obra_id": oid,
                "cliente": obra.get("cliente"),
                "bucket": bucket_id,
                "dias_ate_inicio": (obra.get("regua") or {}).get("dias_ate_inicio"),
            })

        # Print resumo
        atual_str = ", ".join(cores["atual"][:2]) or ("a definir" if cores["tem_pendencia"] else "—")
        n_dist = len(cores["definidas"])
        print(f'{(obra.get("cliente") or "")[:40]:<42} {atual_str[:33]:<35} {"sim" if cores["tem_pendencia"] else "não":<6} {n_dist}')

    # Top global · só campos consumidos pela tela
    discord["cores_agregado"] = {
        "calculado_em": HOJE.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "top_atual": contador_atual.most_common(15),
        "obras_pendentes_decisao": pendentes,
    }

    write_json_atomic(DISCORD_PATH, discord)

    print()
    print("=== Top 10 cores · obras ATIVAS (cor atual definida) ===")
    for cor, n in contador_atual.most_common(10):
        print(f"  {n}x  {cor}")
    print()
    print(f"Obras pendentes de decisão de cor: {len(pendentes)}")
    for p in pendentes:
        d = p.get('dias_ate_inicio')
        d_str = f"{d}d" if d is not None else "—"
        print(f"  · {p['cliente'][:40]} · bucket {p['bucket']} · {d_str}")

    print(f"\n[OK] {DISCORD_PATH}")


if __name__ == "__main__":
    main()
