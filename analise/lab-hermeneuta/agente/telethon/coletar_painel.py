"""
Coletor via Painel de Obras (substitui monitorar.py / Telethon)
=================================================================

Lê piloto.json (obras com obra_id) e busca mensagens de cada obra
diretamente no painel:
   GET /api/projects/{obra_id}/messages?source=telegram&limit=2000
   GET /api/projects/{obra_id}/messages?source=whatsapp&limit=2000

Vantagens vs Telethon:
- Sem auth (público)
- Sem rate limit Telegram
- Multi-canal (Telegram + WhatsApp na mesma obra)
- Descrições de foto já incluídas pela IA do backend

Saída: telegram-snapshot.json (mesmo schema do monitorar.py · drop-in)
       Ganha campos novos: 'descricao' (em msgs com mídia) e bloco 'whatsapp'

Uso:
    python coletar_painel.py [--dias 15] [--limit 80]
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

ROOT = Path(__file__).parent
PILOTO = ROOT / "piloto.json"
OUT_PATH = ROOT / "telegram-snapshot.json"  # mesmo nome · drop-in pro pipeline
BASE = "https://cliente.monofloor.cloud/api/projects"


def fetch_json(url: str, max_retries: int = 2):
    """GET JSON com retry exponencial."""
    last_err = None
    for tentativa in range(max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "lab-orion/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            last_err = e
            if tentativa < max_retries:
                time.sleep(2 ** tentativa)
    raise RuntimeError(f"fetch falhou após {max_retries+1} tentativas: {last_err}")


def parse_id_msg(s: str) -> int:
    """'tg-178697' → 178697 · 'wa-uuid' → hash int."""
    if not s:
        return 0
    if s.startswith("tg-"):
        try:
            return int(s[3:])
        except ValueError:
            pass
    # WhatsApp ou fallback: hash determinístico
    return abs(hash(s)) & 0x7FFFFFFF


def parse_data(ts: str) -> str:
    """Normaliza timestamp pro ISO usado pelo pipeline."""
    if not ts:
        return ""
    # Painel retorna '2026-05-04 12:53:49+00' ou '2026-05-04 12:53:49'
    s = ts.strip().replace(" ", "T")
    # Adiciona Z se faltar timezone
    if not (s.endswith("Z") or "+" in s[10:] or "-" in s[10:]):
        s += "+00:00"
    elif s.endswith("+00"):
        s = s[:-3] + "+00:00"
    return s


def autor_id_de_nome(nome: str) -> str:
    """ID determinístico baseado no nome normalizado · placeholder até cruzar com cadastro."""
    if not nome:
        return ""
    # Normaliza: lowercase + tira espaços extras
    n = " ".join(str(nome).strip().lower().split())
    return f"name:{n}"


def msg_painel_para_pipeline(m: dict) -> dict:
    """Mapeia 1 msg do painel pro schema do pipeline (compatível Telethon)."""
    raw_type = (m.get("type") or "text").lower()
    is_text = raw_type == "text"
    sender = m.get("sender") or ""
    content = m.get("content") or ""

    return {
        "id": parse_id_msg(m.get("id") or ""),
        "data": parse_data(m.get("timestamp") or ""),
        "autor_id": autor_id_de_nome(sender),
        "autor_nome": sender,
        "texto": content,
        "tem_midia": not is_text,
        "media_tipo": raw_type if not is_text else None,
        "media_url": m.get("mediaUrl"),
        # Painel já dá descrição rica (foto, vídeo, áudio) embutida em content
        "descricao_painel": content if not is_text else None,
        # Metadados do painel pra debug
        "_origem": "painel",
        "_id_painel": m.get("id"),
        "_direction": m.get("direction"),
        "_chat_title": m.get("chatTitle"),
    }


def coletar_obra(obra_id: str, cutoff_date: datetime, limit: int) -> dict:
    """Coleta Telegram + WhatsApp de 1 obra · filtra por janela."""
    out = {"telegram": [], "whatsapp": [], "chat_title": None, "erro": None}

    try:
        # Telegram
        url_tg = f"{BASE}/{obra_id}/messages?source=telegram&limit=2000"
        d_tg = fetch_json(url_tg)
        msgs_tg = d_tg.get("messages") or []

        for m in msgs_tg:
            data_iso = parse_data(m.get("timestamp") or "")
            # Filtro de janela: timestamp >= cutoff
            if data_iso and data_iso >= cutoff_date.strftime("%Y-%m-%dT%H:%M:%S+00:00"):
                out["telegram"].append(msg_painel_para_pipeline(m))
            if len(out["telegram"]) >= limit:
                break

        if msgs_tg and not out["chat_title"]:
            out["chat_title"] = msgs_tg[0].get("chatTitle")

        # WhatsApp (bonus · pipeline pode ignorar por enquanto)
        url_wa = f"{BASE}/{obra_id}/messages?source=whatsapp&limit=500"
        d_wa = fetch_json(url_wa)
        msgs_wa = d_wa.get("messages") or []
        for m in msgs_wa:
            data_iso = parse_data(m.get("timestamp") or "")
            if data_iso and data_iso >= cutoff_date.strftime("%Y-%m-%dT%H:%M:%S+00:00"):
                out["whatsapp"].append(msg_painel_para_pipeline(m))

    except Exception as e:
        out["erro"] = str(e)

    return out


def main(limit: int, dias: int):
    if not PILOTO.exists():
        print(f"ERRO: {PILOTO} não encontrado · rode selecionar_piloto.py primeiro")
        sys.exit(1)

    piloto_data = json.loads(PILOTO.read_text(encoding="utf-8"))
    piloto = piloto_data["piloto"]
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=dias)
    print(f"Piloto: {len(piloto)} obras · janela últimos {dias}d (cap {limit} msgs Telegram) · cutoff {cutoff_date.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Fonte: PAINEL DE OBRAS (cliente.monofloor.cloud) · sem Telethon\n")

    out = {
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fonte": "painel-monofloor-cloud",
        "limit_msgs_por_grupo": limit,
        "janela_dias": dias,
        "cutoff_date": cutoff_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "obras": [],
    }

    com_erro = 0
    for i, p in enumerate(piloto, 1):
        cliente = p["cliente"]
        obra_id = p["obra_id"]
        grupo_id_legado = p["telegram"]["grupo_id"]
        grupo_nome_legado = p["telegram"]["grupo_nome"]
        print(f"  [{i}/{len(piloto)}] {cliente[:40]:<40}  ", end="", flush=True)

        coletado = coletar_obra(obra_id, cutoff_date, limit)
        msgs_tg = coletado["telegram"]
        msgs_wa = coletado["whatsapp"]
        erro = coletado.get("erro")

        if erro:
            com_erro += 1
            print(f"ERRO: {erro[:60]}")
        else:
            print(f"{len(msgs_tg):3d} TG · {len(msgs_wa):3d} WA")

        # Stats compatíveis com schema atual (Telethon)
        autores_tg = {m["autor_id"]: m["autor_nome"] for m in msgs_tg if m["autor_id"]}
        com_midia_tg = sum(1 for m in msgs_tg if m.get("tem_midia"))

        out["obras"].append({
            "obra_id": obra_id,
            "cliente": cliente,
            "consultor": p.get("consultor"),
            "telegram": {
                "grupo_id": grupo_id_legado,  # mantém pra compatibilidade
                "grupo_nome": grupo_nome_legado,
                "titulo_atual": coletado.get("chat_title") or grupo_nome_legado,
                "membros": None,  # painel não expõe
                "stats": {
                    "total": len(msgs_tg),
                    "autores_distintos": len(autores_tg),
                    "com_midia": com_midia_tg,
                    "com_texto": sum(1 for m in msgs_tg if m.get("texto")),
                },
                "mensagens": msgs_tg,
                "erro": erro,
            },
            # NOVO bloco · WhatsApp individual (antes só tinha resumo KIRA)
            "whatsapp": {
                "stats": {
                    "total": len(msgs_wa),
                    "autores_distintos": len({m["autor_id"]: 1 for m in msgs_wa}),
                    "com_midia": sum(1 for m in msgs_wa if m.get("tem_midia")),
                },
                "mensagens": msgs_wa,
            },
        })

    # Aborta se ≥30% das obras falharam
    total_obras = len(out["obras"])
    if total_obras > 0 and com_erro / total_obras >= 0.30:
        print(f"\nABORT: {com_erro}/{total_obras} obras com erro (≥30%) · NÃO sobrescrevendo snapshot")
        sys.exit(2)

    # Atomic write
    tmp = OUT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(OUT_PATH)

    total_tg = sum(len(o["telegram"]["mensagens"]) for o in out["obras"])
    total_wa = sum(len(o["whatsapp"]["mensagens"]) for o in out["obras"])
    print(f"\n[OK] {OUT_PATH}")
    print(f"     {total_obras} obras · {total_tg} msgs Telegram · {total_wa} msgs WhatsApp"
          + (f" · {com_erro} obras c/ erro" if com_erro else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta mensagens via Painel de Obras (substitui Telethon)")
    parser.add_argument("--dias", type=int, default=15, help="Janela de N dias (default: 15)")
    parser.add_argument("--limit", type=int, default=80, help="Cap máx de msgs Telegram por obra (default: 80)")
    args = parser.parse_args()
    main(args.limit, args.dias)
