"""
Espelha o KIRA WhatsApp Summary do detail de cada obra
=======================================================

KIRA já capturou e sumariza WhatsApp das obras · grava em
`pendenciaManual.whatsappSummary` no detail. Este script espelha esse
conteúdo no discordancias-v3.json pra que a tela mostre voz direta do
cliente — resolve o ponto cego "cliente ausente em 10/10 grupos Telegram".

Lê de: ../dados/details/{obra_id}.json (mantido pelo refresh.sh)
Não duplica, só espelha. Custo zero.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import write_discord, setup_utf8, marcar_step_falho

setup_utf8()

ROOT = Path(__file__).parent.parent  # lab-hermeneuta
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"
DETAILS_DIR = ROOT.parent / "dados" / "details"  # analise/dados/details (irmão do lab)

HOJE = datetime.now(timezone.utc)


def parse_iso(s: str):
    if not s: return None
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
        return d
    except Exception:
        return None


_SCHEMA_DIVERGENTES = []  # acumulador pro relatório final


def extrair_obra(detail_path: Path) -> dict:
    """Extrai whatsappSummary + tagKira + situacaoAtual do detail."""
    if not detail_path.exists():
        return {"erro": "detail não encontrado"}

    try:
        d = json.loads(detail_path.read_text(encoding="utf-8-sig"))
    except Exception as e:
        return {"erro": f"falha ao parsear: {e}"}

    # Schema check explícito · era fonte de bug silencioso (Vitor 2026-05-04)
    pm = d.get("pendenciaManual")
    if pm is not None and not isinstance(pm, dict):
        _SCHEMA_DIVERGENTES.append({
            "obra_id": detail_path.stem,
            "campo": "pendenciaManual",
            "tipo_real": type(pm).__name__,
            "tipo_esperado": "dict|null",
        })
        pm = {}
    elif not isinstance(pm, dict):
        pm = {}
    ws = pm.get("whatsappSummary")
    if ws is not None and not isinstance(ws, dict):
        _SCHEMA_DIVERGENTES.append({
            "obra_id": detail_path.stem,
            "campo": "pendenciaManual.whatsappSummary",
            "tipo_real": type(ws).__name__,
            "tipo_esperado": "dict|null",
        })
        ws = {}
    elif not isinstance(ws, dict):
        ws = {}

    gerado = parse_iso(ws.get("geradoEm"))
    dias_desde_resumo = (HOJE - gerado).days if gerado else None

    # tagKiraUpdatedAt é o sinal mais recente de que o KIRA está ativo
    tag_atualizada = parse_iso(d.get("tagKiraUpdatedAt"))
    dias_desde_tag = (HOJE - tag_atualizada).days if tag_atualizada else None

    return {
        "tag_kira": d.get("tagKira"),
        "tag_kira_atualizada_em": d.get("tagKiraUpdatedAt"),
        "tag_dias_atras": dias_desde_tag,
        "situacao_atual": d.get("situacaoAtual"),
        "whatsapp": {
            "periodo": ws.get("periodo"),
            "gerado_em": ws.get("geradoEm"),
            "dias_desde_resumo": dias_desde_resumo,
            "clima_geral": ws.get("climaGeral"),
            "clima_descricao": ws.get("climaDescricao"),
            "tempo_resposta": ws.get("tempoResposta"),
            "tempo_resposta_detalhes": ws.get("tempoRespostaDetalhes"),
            "total_mensagens": ws.get("totalMensagens"),
            "resumo_executivo": ws.get("resumoExecutivo"),
            "alertas": ws.get("alertas") or [],
            "eventos": ws.get("eventos") or [],
            "pendencias": ws.get("pendencias") or [],
            "participantes": ws.get("participantes") or [],
        } if ws else None,
    }


def main():
    if not DISCORD_PATH.exists():
        print(f"ERRO: {DISCORD_PATH} não existe")
        sys.exit(1)
    if not DETAILS_DIR.exists():
        print(f"ERRO: {DETAILS_DIR} não existe · refresh.sh precisa ter rodado")
        sys.exit(1)

    discord = json.loads(DISCORD_PATH.read_text(encoding="utf-8"))

    print(f"{'Cliente':<42} {'Tag KIRA':<35} {'Clima':<10} {'Tag atualiz.':<14} {'Resumo'}")
    print("-" * 120)

    for obra in discord.get("obras", []):
        oid = obra.get("obra_id")
        detail_path = DETAILS_DIR / f"{oid}.json"
        info = extrair_obra(detail_path)
        obra["kira_whatsapp"] = info

        cliente = (obra.get("cliente") or "")[:40]
        if "erro" in info:
            print(f"{cliente:<42} {'(erro: ' + info['erro'][:25] + ')':<35} {'—':<10}")
            continue
        tag = (info.get("tag_kira") or "—")[:33]
        ws = info.get("whatsapp") or {}
        clima = ws.get("clima_geral") or "—"
        dt = info.get("tag_dias_atras")
        dt_str = f"{dt}d" if dt is not None else "—"
        dr = ws.get("dias_desde_resumo")
        dr_str = f"{dr}d" if dr is not None else "—"
        print(f"{cliente:<42} {tag:<35} {clima:<10} {dt_str:<14} {dr_str}")

    write_discord(DISCORD_PATH, discord)
    print(f"\n[OK] {DISCORD_PATH}")

    # Reporta schema divergente · vira flag visível na sentinela
    if _SCHEMA_DIVERGENTES:
        print(f"\n[WARN] {len(_SCHEMA_DIVERGENTES)} obras com schema KIRA divergente:")
        for d in _SCHEMA_DIVERGENTES[:5]:
            print(f"  · {d['obra_id'][:8]} · {d['campo']} é {d['tipo_real']} (esperado {d['tipo_esperado']})")
        if len(_SCHEMA_DIVERGENTES) > 5:
            print(f"  · (+{len(_SCHEMA_DIVERGENTES)-5} mais)")
        marcar_step_falho(
            "extrair_kira_whatsapp/schema_divergente",
            f"{len(_SCHEMA_DIVERGENTES)} obras com tipos inesperados em pendenciaManual ou whatsappSummary",
        )


if __name__ == "__main__":
    main()
