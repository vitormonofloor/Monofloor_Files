"""
Fase A — Descoberta de grupos
=============================

Lista TODOS os grupos do Telegram da conta logada e gera CSV pra você revisar.
NÃO captura mensagens. NÃO altera nada. Só LISTA.

Saída: grupos.csv + grupos.json no mesmo diretório.

Uso:
    python listar_grupos.py

Primeira execução pede:
    - número de telefone (formato +5511999999999)
    - código de 6 dígitos que o Telegram manda no app
    - senha 2FA (se você tiver ativada)

Depois disso salva session.session local (gitignored). Próximas execuções não pedem nada.
"""

import asyncio
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    from telethon import TelegramClient
    from telethon.tl.types import Channel, Chat
except ImportError:
    print("ERRO: dependências não instaladas.")
    print("Execute: pip install -r requirements.txt")
    sys.exit(1)

# Carrega .env do mesmo diretório
ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

if not (API_ID and API_HASH and PHONE):
    print("ERRO: variáveis ausentes no .env")
    print("Copie .env.example para .env e preencha TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
    print("Obtenha API_ID e API_HASH em: https://my.telegram.org/apps")
    sys.exit(1)

SESSION = ROOT / "session"


def truncate(s: str, max_len: int = 80) -> str:
    s = (s or "").replace("\n", " ").replace("\r", " ").strip()
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


def kind(entity) -> str:
    """Classifica: grupo simples / supergrupo / canal."""
    if isinstance(entity, Chat):
        return "grupo"
    if isinstance(entity, Channel):
        if entity.broadcast:
            return "canal"
        return "supergrupo"
    return "outro"


async def main():
    print(f"Conectando como {PHONE}...")
    async with TelegramClient(str(SESSION), int(API_ID), API_HASH) as client:
        await client.start(phone=PHONE)
        me = await client.get_me()
        print(f"Logado: {me.first_name} (@{me.username or '—'})\n")

        print("Coletando diálogos (pode demorar 30s-2min em conta com 400+ grupos)...\n")

        grupos = []
        total = 0
        async for dialog in client.iter_dialogs():
            total += 1
            entity = dialog.entity
            tipo = kind(entity)
            if tipo not in ("grupo", "supergrupo"):
                continue

            # Última mensagem
            last_msg = dialog.message
            last_date = last_msg.date if last_msg else None
            last_text = truncate(last_msg.message if last_msg else "", 80)

            # Membros
            try:
                participants_count = entity.participants_count or 0
            except AttributeError:
                participants_count = 0

            # Idade da última mensagem em dias
            now = datetime.now(timezone.utc)
            dias_inativo = (now - last_date).days if last_date else None

            grupos.append({
                "id": entity.id,
                "nome": entity.title or "",
                "tipo": tipo,
                "membros": participants_count,
                "ultima_mensagem_data": last_date.strftime("%Y-%m-%d %H:%M") if last_date else None,
                "dias_inativo": dias_inativo,
                "ultima_mensagem_preview": last_text,
            })

            if len(grupos) % 50 == 0:
                print(f"  {len(grupos)} grupos coletados...")

        print(f"\nTotal de diálogos varridos: {total}")
        print(f"Grupos/supergrupos encontrados: {len(grupos)}\n")

        # Ordena por última mensagem (mais recentes primeiro)
        grupos.sort(key=lambda g: g["ultima_mensagem_data"] or "", reverse=True)

        # Salva CSV
        csv_path = ROOT / "grupos.csv"
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "id", "nome", "tipo", "membros", "ultima_mensagem_data", "dias_inativo", "ultima_mensagem_preview"
            ])
            writer.writeheader()
            writer.writerows(grupos)

        # Salva JSON
        json_path = ROOT / "grupos.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "total": len(grupos),
                "grupos": grupos,
            }, f, ensure_ascii=False, indent=2)

        print(f"✓ {csv_path}")
        print(f"✓ {json_path}")
        print()
        print("Próximo passo: abrir grupos.csv no Excel/Notepad e marcar quais são de obra")
        print("(planilha já vem ordenada por última mensagem · ativos no topo · zumbis no fundo)")


if __name__ == "__main__":
    asyncio.run(main())
