"""
Extrai timeline_recente (últimas 4 semanas) de cada obra
=========================================================

Custo zero de API · só lê os dossiês + telegram-snapshot existentes.

Pra cada obra:
1. Pega `evidencias_fortes[]` e `datas_mencionadas[]` do dossiê
2. Filtra eventos >= JANELA_DIAS atrás
3. Pega últimas N mensagens com texto significativo do telegram-snapshot
4. Mescla, deduplica por (data+autor+trecho), ordena cronológico desc
5. Injeta `timeline_recente` em cada obra do discordancias-v3.json
"""

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

ROOT = Path(__file__).parent.parent
DOSSIES_DIR = ROOT / "dados" / "dossies"
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"
SNAPSHOT_PATH = ROOT / "agente" / "telethon" / "telegram-snapshot.json"

JANELA_DIAS = 28
HOJE = datetime(2026, 4, 30, tzinfo=timezone.utc)
LIMITE = HOJE - timedelta(days=JANELA_DIAS)


def parse_data(s: str):
    """Aceita YYYY-MM-DD ou YYYY-MM-DDTHH:MM(:SS)?(+TZ)? · sempre retorna tz-aware UTC."""
    if not s:
        return None
    s = s.strip()
    try:
        if "T" in s:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        else:
            d = datetime.fromisoformat(s + "T00:00:00+00:00")
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d
    except (ValueError, TypeError):
        return None


def truncar(s: str, n: int = 110) -> str:
    s = (s or "").strip().replace("\n", " ").replace("\r", " ")
    # Remove linhas de separadores (------) no início e fim
    s = re.sub(r"^[\s\-=*_·•♦️♣️♠️🚨⚠]+", "", s)
    s = re.sub(r"[\s\-=*_·•♦️♣️♠️]+$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s if len(s) <= n else s[: n - 1] + "…"


def msg_significativa(texto: str) -> bool:
    """Filtra mensagens lixo: só separadores, muito curtas, ou puro padrão de bot."""
    if not texto:
        return False
    t = texto.strip()
    if len(t) < 15:
        return False
    # Remove separadores pra contar conteúdo real
    sem_sep = re.sub(r"[\-=*_·•\s]+", "", t)
    if len(sem_sep) < 12:
        return False
    # Bots/cards padrão · "Inserido no Pipe", "Atualizado"
    if re.match(r"^[♦️♣️♠️\s]*Atualizado\s*\|\s*Inserido", t, re.IGNORECASE):
        return False
    return True


def normalizar_autor(nome: str) -> str:
    if not nome:
        return "—"
    # Remove "| Monofloor" / "Monofloor" sufixos · padroniza
    s = nome.strip()
    s = re.sub(r"\s*\|?\s*Monofloor\s*$", " · Monofloor", s, flags=re.IGNORECASE)
    s = re.sub(r"^Operacional\s+Monofloor$", "Operacional · Monofloor", s, flags=re.IGNORECASE)
    return s


def extrair_eventos_dossie(dossie: dict) -> list:
    """Tira eventos do dossiê (evidencias_fortes + datas_mencionadas), filtrando por janela."""
    eventos = []
    leitura = dossie.get("leitura_secretario", {})

    for ev in leitura.get("evidencias_fortes", []):
        d = parse_data(ev.get("data"))
        if not d or d < LIMITE:
            continue
        eventos.append({
            "data": d.isoformat(),
            "data_curta": d.strftime("%Y-%m-%d"),
            "autor": normalizar_autor(ev.get("autor")),
            "trecho": truncar(ev.get("trecho_curto") or ev.get("porque_relevante") or "", 140),
            "msg_id": ev.get("msg_id"),
            "tipo": "evidencia",
        })

    for dm in leitura.get("datas_mencionadas", []):
        d = parse_data(dm.get("data"))
        if not d or d < LIMITE:
            continue
        eventos.append({
            "data": d.isoformat(),
            "data_curta": d.strftime("%Y-%m-%d"),
            "autor": "—",
            "trecho": truncar(dm.get("evento") or "", 140),
            "msg_id": None,
            "fonte": dm.get("fonte"),
            "tipo": "marco",
        })

    return eventos


def extrair_ultimas_msgs_snapshot(obra_id: str, snapshot: dict, limite: int = 5) -> list:
    """Pega últimas N mensagens com texto >=15 chars do telegram-snapshot."""
    obra_snap = next((o for o in snapshot.get("obras", []) if o.get("obra_id") == obra_id), None)
    if not obra_snap:
        return []

    msgs = obra_snap.get("telegram", {}).get("mensagens", [])
    # Filtra msgs significativas (não só separadores nem cards de bot)
    com_texto = [m for m in msgs if msg_significativa(m.get("texto") or "")]

    # Pega as últimas `limite` (snapshot já está em ordem cronológica)
    ultimas = com_texto[-limite:]

    eventos = []
    for m in ultimas:
        d = parse_data(m.get("data"))
        if not d or d < LIMITE:
            continue
        eventos.append({
            "data": d.isoformat(),
            "data_curta": d.strftime("%Y-%m-%d"),
            "autor": normalizar_autor(m.get("autor_nome")),
            "trecho": truncar(m.get("texto"), 140),
            "msg_id": m.get("id"),
            "tipo": "msg",
        })
    return eventos


def deduplicar(eventos: list) -> list:
    """Remove duplicatas por (data_curta+autor+início_normalizado_do_trecho)."""
    visto = set()
    out = []
    for e in eventos:
        # Normaliza início do trecho pra matching: lower, remove pontuação/espaços
        inicio = re.sub(r"[^a-z0-9]+", "", e["trecho"][:50].lower())[:30]
        chave = (e["data_curta"], e["autor"], inicio)
        if chave in visto:
            continue
        visto.add(chave)
        out.append(e)
    return out


def main():
    if not DISCORD_PATH.exists():
        print(f"ERRO: {DISCORD_PATH} não encontrado")
        sys.exit(1)
    if not SNAPSHOT_PATH.exists():
        print(f"ERRO: {SNAPSHOT_PATH} não encontrado")
        sys.exit(1)

    discord = json.loads(DISCORD_PATH.read_text(encoding="utf-8"))
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    total_eventos = 0
    for obra in discord.get("obras", []):
        oid = obra.get("obra_id")
        dossie_path = DOSSIES_DIR / f"{oid}.json"
        if not dossie_path.exists():
            obra["timeline_recente"] = {"eventos": [], "janela_dias": JANELA_DIAS}
            continue

        dossie = json.loads(dossie_path.read_text(encoding="utf-8"))
        eventos = []
        eventos += extrair_eventos_dossie(dossie)
        eventos += extrair_ultimas_msgs_snapshot(oid, snapshot, limite=8)

        eventos = deduplicar(eventos)

        # Marca eventos futuros (datas previstas mencionadas nas msgs)
        for e in eventos:
            d = parse_data(e["data"])
            e["eh_futuro"] = bool(d and d > HOJE)

        eventos.sort(key=lambda e: e["data"], reverse=True)  # mais recente primeiro

        # Última data REAL = última mensagem (não datas previstas no futuro)
        tg = dossie.get("telegram", {})
        ultima_msg = tg.get("ultima_msg_data")  # vem do snapshot · só msgs reais
        ultima_dt = parse_data(ultima_msg) if ultima_msg else None
        dias_atras = (HOJE - ultima_dt).days if ultima_dt else None

        obra["timeline_recente"] = {
            "janela_dias": JANELA_DIAS,
            "limite_de": LIMITE.strftime("%Y-%m-%d"),
            "ate": HOJE.strftime("%Y-%m-%d"),
            "ultima_data": ultima_msg,
            "dias_desde_ultima": dias_atras,
            "total_eventos": len(eventos),
            "eventos": eventos,
        }
        total_eventos += len(eventos)

    DISCORD_PATH.write_text(json.dumps(discord, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {DISCORD_PATH}")
    print(f"     {total_eventos} eventos injetados em {len(discord.get('obras', []))} obras")
    print(f"     janela: {LIMITE.strftime('%Y-%m-%d')} → {HOJE.strftime('%Y-%m-%d')} ({JANELA_DIAS}d)")
    print()
    print("Por obra:")
    for o in discord.get("obras", []):
        tl = o.get("timeline_recente", {})
        print(f"  {tl.get('total_eventos', 0):3d} eventos · {(o.get('cliente') or '')[:40]:<40} · última {tl.get('ultima_data') or '—'}")


if __name__ == "__main__":
    main()
