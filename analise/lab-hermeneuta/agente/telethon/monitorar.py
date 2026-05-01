"""
Fase B — Monitor de mensagens
=============================

Lê piloto.json (10 obras) e puxa últimas N mensagens de cada grupo Telegram
correspondente. Gera telegram-snapshot.json com schema rico.

Uso:
    python monitorar.py [--limit 50]

Saída: telegram-snapshot.json no mesmo diretório.

NÃO escreve no Telegram. NÃO entra em grupos. Só LÊ as mensagens já visíveis
na conta logada (session.session salva pela Fase A).
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

try:
    from dotenv import load_dotenv
    from telethon import TelegramClient
except ImportError:
    print("ERRO: dependências não instaladas. Execute: pip install -r requirements.txt")
    sys.exit(1)

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")
SESSION = ROOT / "session"
PILOTO = ROOT / "piloto.json"

if not (API_ID and API_HASH and PHONE):
    print("ERRO: variáveis ausentes no .env")
    sys.exit(1)


def serialize_message(msg, sender_cache: dict) -> dict:
    """Extrai campos relevantes de uma mensagem · ignora system/service."""
    if not msg or not getattr(msg, "id", None):
        return None

    text = (msg.message or "").strip()
    has_media = bool(getattr(msg, "media", None))

    # Tipo de mídia (sem baixar nada)
    media_tipo = None
    if has_media:
        media = msg.media
        media_tipo = type(media).__name__.replace("MessageMedia", "").lower()

    sender_id = getattr(msg, "sender_id", None) or 0
    autor = sender_cache.get(sender_id, {})

    return {
        "id": msg.id,
        "data": msg.date.isoformat() if msg.date else None,
        "autor_id": sender_id,
        "autor_nome": autor.get("nome"),
        "autor_username": autor.get("username"),
        "texto": text,
        "tem_midia": has_media,
        "midia_tipo": media_tipo,
        "reply_to_msg_id": getattr(msg, "reply_to_msg_id", None),
        "via_bot_id": getattr(msg, "via_bot_id", None),
        "edit_date": msg.edit_date.isoformat() if getattr(msg, "edit_date", None) else None,
    }


async def coletar_grupo(client: TelegramClient, grupo_id: int, limit: int, cutoff_date=None, max_retries: int = 2) -> dict:
    """Pega mensagens do grupo até `cutoff_date` (cronológico antiga→nova) · cap em `limit` mensagens · retry em erro de rede."""
    entity = None
    last_err = None
    for tentativa in range(max_retries + 1):
        try:
            entity = await client.get_entity(grupo_id)
            break
        except Exception as e:
            last_err = e
            if tentativa < max_retries:
                await asyncio.sleep(2 ** tentativa)  # backoff: 1s, 2s
    if entity is None:
        return {"erro": f"get_entity falhou após {max_retries+1} tentativas: {last_err}", "mensagens": []}

    messages = []
    sender_cache = {}

    # iter_messages itera da mais NOVA pra mais antiga · break quando passar do cutoff
    async for msg in client.iter_messages(entity, limit=limit):
        if cutoff_date and msg.date and msg.date < cutoff_date:
            break
        # Resolve autor uma vez por sender_id
        sid = getattr(msg, "sender_id", None) or 0
        if sid and sid not in sender_cache:
            try:
                sender = await msg.get_sender()
                if sender:
                    nome_partes = []
                    if getattr(sender, "first_name", None):
                        nome_partes.append(sender.first_name)
                    if getattr(sender, "last_name", None):
                        nome_partes.append(sender.last_name)
                    if not nome_partes and getattr(sender, "title", None):
                        nome_partes.append(sender.title)
                    sender_cache[sid] = {
                        "nome": " ".join(nome_partes).strip() or None,
                        "username": getattr(sender, "username", None),
                    }
                else:
                    sender_cache[sid] = {"nome": None, "username": None}
            except Exception:
                sender_cache[sid] = {"nome": None, "username": None}

        s = serialize_message(msg, sender_cache)
        if s:
            messages.append(s)

    # Inverte: cronológico (mais antiga primeiro)
    messages.reverse()

    # Estatísticas resumo
    autores_distintos = {m["autor_id"]: m["autor_nome"] for m in messages if m["autor_id"]}
    com_texto = [m for m in messages if m["texto"]]
    com_midia = [m for m in messages if m["tem_midia"]]

    return {
        "titulo": getattr(entity, "title", None),
        "membros": getattr(entity, "participants_count", None),
        "mensagens": messages,
        "stats": {
            "total": len(messages),
            "com_texto": len(com_texto),
            "com_midia": len(com_midia),
            "autores_distintos": len(autores_distintos),
            "primeira_msg_data": messages[0]["data"] if messages else None,
            "ultima_msg_data": messages[-1]["data"] if messages else None,
        },
    }


async def main(limit: int, dias: int):
    if not PILOTO.exists():
        print(f"ERRO: {PILOTO} não encontrado · rode selecionar_piloto.py primeiro")
        sys.exit(1)

    piloto_data = json.loads(PILOTO.read_text(encoding="utf-8"))
    piloto = piloto_data["piloto"]
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=dias)
    print(f"Piloto: {len(piloto)} obras · janela últimos {dias}d (cap {limit} msgs) · cutoff {cutoff_date.strftime('%Y-%m-%d %H:%M UTC')}\n")

    print(f"Conectando como {PHONE}...")
    client = TelegramClient(str(SESSION), int(API_ID), API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("ERRO: não autorizado · rode listar_grupos.py primeiro pra fazer login")
        sys.exit(1)

    me = await client.get_me()
    print(f"Logado: {me.first_name}\n")

    out = {
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit_msgs_por_grupo": limit,
        "janela_dias": dias,
        "cutoff_date": cutoff_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "obras": [],
    }

    try:
        for i, p in enumerate(piloto, 1):
            cliente = p["cliente"]
            grupo_id = p["telegram"]["grupo_id"]
            grupo_nome = p["telegram"]["grupo_nome"]
            print(f"  [{i}/{len(piloto)}] {cliente[:40]:<40}  ", end="", flush=True)

            try:
                coletado = await coletar_grupo(client, grupo_id, limit, cutoff_date=cutoff_date)
                stats = coletado["stats"]
                print(f"{stats['total']:3d} msgs · {stats['autores_distintos']} autores · {stats['com_midia']} c/mídia")
            except Exception as e:
                coletado = {"erro": str(e), "mensagens": [], "stats": {}}
                print(f"ERRO: {e}")

            out["obras"].append({
                "obra_id": p["obra_id"],
                "cliente": cliente,
                "consultor": p.get("consultor"),
                "telegram": {
                    "grupo_id": grupo_id,
                    "grupo_nome": grupo_nome,
                    "titulo_atual": coletado.get("titulo"),
                    "membros": coletado.get("membros"),
                    "stats": coletado.get("stats", {}),
                    "mensagens": coletado.get("mensagens", []),
                    "erro": coletado.get("erro"),
                },
            })

        # Aborta se ≥30% das obras falharam (sinal de Telegram/sessão derrubada)
        com_erro = sum(1 for o in out["obras"] if o["telegram"].get("erro"))
        total_obras = len(out["obras"])
        if total_obras > 0 and com_erro / total_obras >= 0.30:
            print(f"\nABORT: {com_erro}/{total_obras} obras com erro Telegram (≥30%) · NÃO sobrescrevendo snapshot")
            print(f"       isso evita perda silenciosa de mensagens · revise sessão Telegram (.session)")
            sys.exit(2)  # exit 2 = erro recuperável · varredura.py aborta sem corromper

        out_path = ROOT / "telegram-snapshot.json"
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[OK] {out_path}")

        total_msgs = sum(len(o["telegram"]["mensagens"]) for o in out["obras"])
        print(f"     {len(out['obras'])} obras · {total_msgs} mensagens totais"
              + (f" · {com_erro} obras c/ erro" if com_erro else ""))
    finally:
        await client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coleta mensagens dos grupos Telegram pareados")
    parser.add_argument("--dias", type=int, default=15,
                        help="Janela de N dias (default: 15)")
    parser.add_argument("--limit", type=int, default=80,
                        help="Cap máximo de msgs por grupo · proteção contra grupos super ativos (default: 80)")
    args = parser.parse_args()
    asyncio.run(main(args.limit, args.dias))
