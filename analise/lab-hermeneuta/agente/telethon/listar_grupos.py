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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows console default é cp1252 · força utf-8 pra suportar acentos/emoji
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

try:
    from dotenv import load_dotenv
    from telethon import TelegramClient
    from telethon.errors import SessionPasswordNeededError
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
CODE = os.getenv("TELEGRAM_CODE")
PASSWORD = os.getenv("TELEGRAM_PASSWORD")

if not (API_ID and API_HASH and PHONE):
    print("ERRO: variáveis ausentes no .env")
    print("Copie .env.example para .env e preencha TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
    print("Obtenha API_ID e API_HASH em: https://my.telegram.org/apps")
    sys.exit(1)

SESSION = ROOT / "session"
HASH_FILE = ROOT / ".phone_code_hash"


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


# UFs brasileiros — padrão de nomenclatura de obra: "MMAA - UF - NOME"
UFS_BR = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
    "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
    "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}

# Padrão estrito MMAA + UF · aceita "0925 - SP", "0925- SP", "07/24 - SP", "07-24 - SP"
_RE_OBRA_UF = re.compile(
    r"^\s*\d{2}[/\-]?\d{2}\s*[/\-]?\s*([A-Z]{2})\b",
    re.IGNORECASE,
)
# Padrão data sem UF: "0124 - NOME" (formato legado)
_RE_OBRA_DATA = re.compile(r"^\s*\d{2}[/\-]?\d{2}\s*[-/]")
# Padrão prefixo "Obra"/"OBRA" sem MMAA: "Obra - NOME" (formato muito antigo)
_RE_OBRA_PREF = re.compile(r"^\s*OBRA\s*-", re.IGNORECASE)
# Grupo de alinhamento com cliente: "UF - 1 ALINHAMENTO - NOME" ou "1 ALINHAMENTO - NOME"
_RE_ALINHAMENTO = re.compile(r"1\s*ALINHAMENTO", re.IGNORECASE)


def classificar(nome: str) -> tuple[str, str]:
    """
    Retorna (eh_obra, tipo_canal) para o nome do grupo.

    eh_obra: 's' se for grupo técnico de obra · 'n' caso contrário
    tipo_canal: 'obra' (técnico) · 'alinhamento' (cliente) · 'outro'
    """
    if not nome:
        return "n", "outro"

    # Alinhamento com cliente tem prioridade · pode aparecer com UF antes do "1 ALINHAMENTO"
    if _RE_ALINHAMENTO.search(nome):
        return "n", "alinhamento"

    # Tier 1: MMAA + UF (regra estrita · maioria dos grupos atuais)
    m = _RE_OBRA_UF.match(nome)
    if m and m.group(1).upper() in UFS_BR:
        return "s", "obra"

    # Tier 2: MMAA + NOME (sem UF · formato legado)
    if _RE_OBRA_DATA.match(nome):
        return "s", "obra"

    # Tier 3: prefixo "Obra -" sem MMAA (formato muito antigo)
    if _RE_OBRA_PREF.match(nome):
        return "s", "obra"

    return "n", "outro"


async def authenticate(client):
    """Login não-interativo: usa session salva, ou code/password do .env."""
    await client.connect()
    if await client.is_user_authorized():
        return

    # Não autorizado · precisa de code
    if not CODE:
        print(f"Enviando code de login pro Telegram do {PHONE}...")
        sent = await client.send_code_request(PHONE)
        HASH_FILE.write_text(sent.phone_code_hash, encoding="utf-8")
        print()
        print("=" * 60)
        print("[OK] CODE ENVIADO")
        print("=" * 60)
        print()
        print("1. Abra o Telegram no celular ou desktop")
        print("2. Vai ter uma mensagem do 'Telegram' com código de 5-6 dígitos")
        print("3. Adicione no .env:  TELEGRAM_CODE=12345")
        print("4. Se você tem 2FA, adicione também:  TELEGRAM_PASSWORD=sua_senha")
        print("5. Rode de novo: python listar_grupos.py")
        print()
        print("(code expira em ~2min · hash salvo em .phone_code_hash)")
        sys.exit(0)

    if not HASH_FILE.exists():
        print("ERRO: TELEGRAM_CODE preenchido mas .phone_code_hash não existe.")
        print("Apague TELEGRAM_CODE do .env e rode de novo pra disparar um code novo.")
        sys.exit(1)

    phone_hash = HASH_FILE.read_text(encoding="utf-8").strip()

    try:
        await client.sign_in(PHONE, CODE, phone_code_hash=phone_hash)
    except SessionPasswordNeededError:
        if not PASSWORD:
            print("ERRO: sua conta tem 2FA. Adicione TELEGRAM_PASSWORD ao .env e rode de novo.")
            sys.exit(1)
        await client.sign_in(password=PASSWORD)

    # Login OK · limpa o hash usado
    HASH_FILE.unlink(missing_ok=True)


async def main():
    print(f"Conectando como {PHONE}...")
    client = TelegramClient(str(SESSION), int(API_ID), API_HASH)
    try:
        await authenticate(client)
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

            nome = entity.title or ""
            flag_obra, tipo_canal = classificar(nome)
            grupos.append({
                "id": entity.id,
                "nome": nome,
                "tipo": tipo,
                "eh_obra": flag_obra,
                "tipo_canal": tipo_canal,
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

        fieldnames = [
            "id", "nome", "tipo", "eh_obra", "tipo_canal", "membros",
            "ultima_mensagem_data", "dias_inativo", "ultima_mensagem_preview"
        ]

        # Salva CSV completo (todos os 800+ grupos, com flags eh_obra + tipo_canal)
        csv_path = ROOT / "grupos.csv"
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(grupos)

        # Salva CSV filtrado só com obras técnicas (foco principal da HERMENEUTA)
        obras = [g for g in grupos if g["tipo_canal"] == "obra"]
        obras_path = ROOT / "grupos-obra.csv"
        with open(obras_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(obras)

        # Salva CSV de alinhamento com cliente (fonte secundária · feedback do cliente)
        alinhamentos = [g for g in grupos if g["tipo_canal"] == "alinhamento"]
        alinha_path = ROOT / "grupos-alinhamento.csv"
        with open(alinha_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(alinhamentos)

        # Salva JSON com metadata
        json_path = ROOT / "grupos.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "total": len(grupos),
                "total_obras": len(obras),
                "total_alinhamentos": len(alinhamentos),
                "grupos": grupos,
            }, f, ensure_ascii=False, indent=2)

        print(f"Obras técnicas:        {len(obras):4d}")
        print(f"Alinhamento c/ cliente: {len(alinhamentos):4d}")
        print(f"Outros (ignorados):    {len(grupos) - len(obras) - len(alinhamentos):4d}")
        print(f"Total:                 {len(grupos):4d}")
        print()
        print(f"[OK] {csv_path}  (todos)")
        print(f"[OK] {obras_path}  (obras técnicas)")
        print(f"[OK] {alinha_path}  (cliente)")
        print(f"[OK] {json_path}")
        print()
        print("Próximo passo: abrir grupos-obra.csv no Excel · ordenado por última msg desc")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
