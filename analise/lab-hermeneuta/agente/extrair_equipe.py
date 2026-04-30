"""
Extrai equipe em campo por obra (cadastro oficial × Telegram)
==============================================================

Cruza autor_id das mensagens do Telegram com cadastro em equipes-snapshot.json
(vindo da API /equipes do painel) · identifica:

- LÍDER da obra (função=LIDER no cadastro)
- APLICADORES ativos em campo (APLICADOR_1/2/3, AJUDANTE, ENCARREGADO)
- LÍDER OCULTO: pessoa com função=LIDER posta no grupo mas não é da equipe alocada
- AUTORES NÃO MAPEADOS: pessoas no grupo sem cadastro (pode ser cliente, prestador externo)

Injeta `equipe_em_campo` em cada obra do discordancias-v3.json. Custo zero.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import write_json_atomic, setup_utf8

setup_utf8()

ROOT = Path(__file__).parent.parent
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"
EQUIPES_PATH = ROOT / "dados" / "equipes-snapshot.json"
OVERRIDES_PATH = ROOT / "dados" / "equipe-overrides.json"
SNAPSHOT_PATH = ROOT / "agente" / "telethon" / "telegram-snapshot.json"

HOJE = datetime.now(timezone.utc)
JANELA_DIAS = 28  # janela pra considerar pessoa "ativa em campo"


def montar_indice_pessoas(equipes: list, overrides: dict) -> tuple[dict, set, dict]:
    """
    Retorna (idx_pessoas, bots, internos):
    - idx_pessoas: {telegram_user_id: {nome, funcao, equipe_nome, equipe_id, ...}}
    - bots: set de telegram_user_id que devem ser ignorados nas estatísticas
    - internos: {telegram_user_id: {nome_real, funcao_real}} pra Monofloor interno
    """
    idx = {}
    for eq in equipes:
        nome_eq = eq.get("nome") or "?"
        eq_id = eq.get("id")
        lider = eq.get("lider")
        if lider and lider.get("telegramUserId"):
            idx[lider["telegramUserId"]] = {
                "nome": lider.get("nome"),
                "funcao": "LIDER",
                "equipe_nome": nome_eq,
                "equipe_id": eq_id,
                "telefone": lider.get("telefone"),
                "ativo": lider.get("ativo", True),
                "fonte": "cadastro_oficial",
            }
        for m in eq.get("membros", []) or []:
            if m.get("telegramUserId"):
                idx[m["telegramUserId"]] = {
                    "nome": m.get("nome"),
                    "funcao": m.get("funcao"),
                    "equipe_nome": nome_eq,
                    "equipe_id": eq_id,
                    "telefone": m.get("telefone"),
                    "ativo": m.get("ativo", True),
                    "fonte": "cadastro_oficial",
                }

    # Bots
    bots = set(b["telegram_user_id"] for b in overrides.get("bots", []))

    # Override: telegram_id_corrigido sobrescreve/adiciona ao idx
    for c in overrides.get("telegram_id_corrigido", []):
        idx[c["telegram_user_id"]] = {
            "nome": c["nome_real"],
            "funcao": c["funcao_real"],
            "equipe_nome": c.get("equipe") or "?",
            "equipe_id": None,
            "telefone": None,
            "ativo": True,
            "fonte": "override_manual",
        }

    # Internos Monofloor (sem sufixo no TG)
    internos = {}
    for i in overrides.get("monofloor_interno", []):
        internos[i["telegram_user_id"]] = {
            "nome_real": i["nome_real"],
            "funcao_real": i["funcao_real"],
        }

    return idx, bots, internos


def msg_dentro_janela(data_iso: str) -> bool:
    """Compara só DATAS (ignora hora) pra evitar borda do hoje."""
    if not data_iso:
        return False
    try:
        d = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        delta = (HOJE.date() - d.date()).days
        return 0 <= delta <= JANELA_DIAS
    except Exception:
        return False


def main():
    if not DISCORD_PATH.exists() or not EQUIPES_PATH.exists() or not SNAPSHOT_PATH.exists():
        print("ERRO: arquivos faltando · roda primeiro o pipeline básico")
        sys.exit(1)

    discord = json.loads(DISCORD_PATH.read_text(encoding="utf-8"))
    equipes = json.loads(EQUIPES_PATH.read_text(encoding="utf-8-sig"))
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    overrides = {}
    if OVERRIDES_PATH.exists():
        overrides = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))

    idx_pessoas, bots, internos = montar_indice_pessoas(equipes, overrides)
    snap_by_id = {o["obra_id"]: o for o in snapshot.get("obras", [])}

    print(f"Equipes cadastradas: {len(equipes)}")
    print(f"Pessoas com telegramUserId: {len(idx_pessoas)}")
    print(f"Janela de análise: últimos {JANELA_DIAS} dias")
    print()
    print(f"{'Cliente':<42} {'Líder':<25} {'Membros':<8} {'Não-mapeados'}")
    print("-" * 110)

    for obra in discord.get("obras", []):
        oid = obra.get("obra_id")
        snap = snap_by_id.get(oid)
        if not snap:
            obra["equipe_em_campo"] = {"erro": "sem snapshot"}
            continue

        msgs = snap.get("telegram", {}).get("mensagens", [])
        # Conta msgs por autor na janela · ignora bots
        contagem = {}
        for m in msgs:
            if not msg_dentro_janela(m.get("data") or ""):
                continue
            aid = str(m.get("autor_id") or "")
            if not aid or aid in bots:
                continue
            if aid not in contagem:
                contagem[aid] = {
                    "autor_id": aid,
                    "autor_nome_telegram": m.get("autor_nome"),
                    "msgs": 0,
                    "ultima_msg": None,
                }
            contagem[aid]["msgs"] += 1
            d = m.get("data")
            if d and (not contagem[aid]["ultima_msg"] or d > contagem[aid]["ultima_msg"]):
                contagem[aid]["ultima_msg"] = d

        # Classifica cada autor
        cadastrados = []
        nao_mapeados = []
        for aid, info in contagem.items():
            cad = idx_pessoas.get(aid)
            if cad:
                cadastrados.append({
                    **info,
                    "nome_oficial": cad["nome"],
                    "funcao": cad["funcao"],
                    "equipe": cad["equipe_nome"],
                    "telefone": cad["telefone"],
                    "fonte": cad.get("fonte", "cadastro_oficial"),
                })
            else:
                nome_tg = info["autor_nome_telegram"] or ""
                # Detecta Monofloor interno · prioriza override manual, fallback no nome TG
                interno = internos.get(aid)
                eh_monofloor = bool(interno) or ("monofloor" in nome_tg.lower() or "operacional" in nome_tg.lower())
                entry = {**info, "eh_monofloor_interno": eh_monofloor}
                if interno:
                    entry["nome_oficial"] = interno["nome_real"]
                    entry["funcao_interno"] = interno["funcao_real"]
                nao_mapeados.append(entry)

        # Identifica o líder oficial entre os cadastrados
        lideres = [c for c in cadastrados if c.get("funcao") == "LIDER"]
        aplicadores = [c for c in cadastrados if c.get("funcao", "").startswith("APLICADOR") or c.get("funcao") in ("AJUDANTE", "ENCARREGADO")]

        # Equipes presentes (uma obra deveria ter membros de UMA equipe; se há de várias, sinal de troca/oculto)
        equipes_presentes = sorted(set(c["equipe"] for c in cadastrados))

        # Líder oculto: alguém com função LIDER que NÃO é da mesma equipe dos aplicadores
        lider_oculto = False
        if lideres and aplicadores:
            eqs_lider = set(l["equipe"] for l in lideres)
            eqs_aplic = set(a["equipe"] for a in aplicadores)
            if eqs_lider != eqs_aplic and not (eqs_lider & eqs_aplic):
                lider_oculto = True

        obra["equipe_em_campo"] = {
            "janela_dias": JANELA_DIAS,
            "calculado_em": HOJE.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "lideres": lideres,
            "aplicadores": aplicadores,
            "outros_cadastrados": [c for c in cadastrados if c not in lideres and c not in aplicadores],
            "equipes_presentes": equipes_presentes,
            "lider_oculto_detectado": lider_oculto,
            "nao_mapeados": [n for n in nao_mapeados if not n["eh_monofloor_interno"]],  # filtra Monofloor interno
            "monofloor_interno": [n for n in nao_mapeados if n["eh_monofloor_interno"]],
            "total_cadastrados": len(cadastrados),
            "total_nao_mapeados_externos": len([n for n in nao_mapeados if not n["eh_monofloor_interno"]]),
        }

        # Print resumo
        cliente = (obra.get("cliente") or "")[:40]
        lider_str = lideres[0]["nome_oficial"][:24] if lideres else "—"
        n_aplic = len(aplicadores)
        n_externos = len([n for n in nao_mapeados if not n["eh_monofloor_interno"]])
        print(f"{cliente:<42} {lider_str:<25} {n_aplic:<8} {n_externos}")

    write_json_atomic(DISCORD_PATH, discord)
    print(f"\n[OK] {DISCORD_PATH}")


if __name__ == "__main__":
    main()
