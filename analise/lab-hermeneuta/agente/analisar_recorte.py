"""
Análise IA por recorte · usa GitHub Models (gratuito · GITHUB_TOKEN)
=====================================================================

Recebe lista de obra_ids · pra cada obra coleta:
  - status painel + fase + dados básicos
  - mensagens recentes Telegram + WhatsApp
  - tag KIRA atualizada

Chama GitHub Models (gpt-4o-mini default) com prompt do HERMENEUTA-v3 simplificado
e atualiza no `discordancias-v3.json`:
  - veredicto, status_sugerido, tipo_demanda
  - flags
  - acao_consultor, prazo_acao
  - urgencia
  - confianca

Failover: se GitHub Models falhar/sem token · degrada graciosamente
(retorna análise determinística simples · não trava pipeline).

Uso (em GitHub Actions ou manual):
    python analisar_recorte.py --obra-ids id1,id2,id3 --recorte "Em execução"
    python analisar_recorte.py --obra-ids-arquivo /tmp/ids.txt
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

# Suporte a urllib (sem dep de `requests` em Action)
import urllib.request
import urllib.error

sys.path.insert(0, str(Path(__file__).parent))
from _util import setup_utf8, write_discord, marcar_step_falho

setup_utf8()

ROOT = Path(__file__).parent.parent
DISCORD_PATH = ROOT / "dados" / "discordancias-v3.json"
TG_SNAPSHOT = ROOT / "agente" / "telethon" / "telegram-snapshot.json"
PAINEL_SNAPSHOT = ROOT / "dados" / "painel-snapshot.json"
ENV_LOCAL = ROOT / ".env"


def _carregar_env_local():
    """Carrega variáveis de `.env` local (não-versionado) sem sobrescrever shell."""
    if not ENV_LOCAL.exists():
        return
    for raw in ENV_LOCAL.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and v and not os.environ.get(k):
            os.environ[k] = v


_carregar_env_local()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_MODEL = os.environ.get("GITHUB_MODEL", "gpt-4o-mini")
GITHUB_MODELS_URL = "https://models.inference.ai.azure.com/chat/completions"


def log(msg: str):
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}", flush=True)


# ============================================================
# Construção de contexto pra cada obra
# ============================================================

def montar_contexto_obra(obra: dict, snapshot_obra: dict | None, painel_obra: dict | None) -> str:
    """
    Monta texto enxuto pra IA com tudo necessário pra gerar veredicto.
    Foca em msgs recentes (15d) · evita poluir contexto com histórico antigo.
    """
    partes = []

    # Identificação
    partes.append(f"Cliente: {obra.get('cliente') or '?'}")
    partes.append(f"Consultor formal: {obra.get('consultor') or '—'}")

    # Painel oficial
    p = obra.get("painel") or {}
    partes.append(
        f"Painel: status={p.get('status_atual')} · fase={p.get('fase_atual')} · "
        f"idade={p.get('idade_dias')}d · metragem={p.get('metragem')}m²"
    )

    # Régua
    r = obra.get("regua") or {}
    if r.get("data_inicio_x"):
        partes.append(
            f"Data início prevista (X): {r.get('data_inicio_x')} · "
            f"dias até X: {r.get('dias_ate_inicio')} · "
            f"alterada: {r.get('data_inicio_alterada')}"
        )
    if r.get("bucket"):
        b = r["bucket"]
        partes.append(f"Bucket atual: {b.get('label')} ({b.get('id')})")

    # Equipe em campo
    e = obra.get("equipe_em_campo") or {}
    if e.get("cadastrados"):
        nomes = [c.get("nome_oficial") for c in e["cadastrados"][:3] if c.get("nome_oficial")]
        if nomes:
            partes.append(f"Equipe em campo (cadastrados): {', '.join(nomes)}")

    # Cores
    c = obra.get("cores") or {}
    cores_atual = c.get("atual") or []
    if cores_atual:
        partes.append(f"Cores escolhidas: {', '.join(cores_atual)}")

    # KIRA WhatsApp (se houver)
    k = obra.get("kira_whatsapp") or {}
    if k.get("tag_kira"):
        partes.append(f"Tag KIRA: {k['tag_kira']}")
    ws = k.get("whatsapp") or {}
    if ws.get("clima_geral"):
        partes.append(f"Clima KIRA: {ws['clima_geral']}")

    partes.append("")

    # Mensagens recentes (do snapshot)
    msgs_tg = (snapshot_obra or {}).get("telegram", {}).get("mensagens", []) if snapshot_obra else []
    msgs_wa = (snapshot_obra or {}).get("whatsapp", {}).get("mensagens", []) if snapshot_obra else []

    if msgs_tg:
        partes.append(f"=== ÚLTIMAS {min(20, len(msgs_tg))} MSGS TELEGRAM (15d) ===")
        for m in msgs_tg[-20:]:
            data = (m.get("data") or "")[:16]
            autor = (m.get("autor_nome") or "?")[:25]
            txt = (m.get("texto") or "[mídia]")[:250].replace("\n", " ")
            partes.append(f"[{data}] {autor}: {txt}")
        partes.append("")

    if msgs_wa:
        partes.append(f"=== ÚLTIMAS {min(10, len(msgs_wa))} MSGS WHATSAPP CLIENTE (15d) ===")
        for m in msgs_wa[-10:]:
            data = (m.get("data") or "")[:16]
            autor = (m.get("autor_nome") or "?")[:25]
            txt = (m.get("texto") or "[mídia]")[:250].replace("\n", " ")
            partes.append(f"[{data}] {autor}: {txt}")
        partes.append("")

    return "\n".join(partes)


# ============================================================
# Prompt
# ============================================================

PROMPT_SISTEMA = """Você é o agente HERMENEUTA do Lab Orion (Monofloor · piso polido).

Sua função: cruzar PAINEL DE OBRAS (oficial) com COMUNICAÇÃO TELEGRAM (técnica) + WHATSAPP (cliente) e gerar veredicto preciso da obra.

Princípio central: quando painel e telegram divergem, a verdade está no telegram. O painel é responsabilidade do consultor atualizar.

DIMENSÕES DO PAINEL (importante · não confunda com contradição):
- `status` = categoria macro do kanban (planejamento, em_execucao, aguardando_execucao, pausado, reparo, marcas_rolo_cera, aguardando_clima, contrato)
- `fase` = estágio específico DENTRO do status (ex: "LOGÍSTICA - MATERIAL ENTREGUE", "CLIENTE FINALIZADO", "OBRA CONCLUÍDA", "RESULTADO VT - ENTRADA")
- Status e fase coexistem · um valor pra cada · NÃO se anulam · um status pode hospedar várias fases

Vocabulário (use exatamente):
- VEREDICTOS: coerente · status_desatualizado · abandono · detrator · inconclusivo
- FLAGS possíveis: detrator_latente · aplicador_indefinido · consultor_divergente · silencio_anomalo · retrabalho_de_retrabalho · escopo_aumentando · risco_tecnico · detrator
- TIPO DEMANDA: patologia · dano_terceiro · retrabalho_acabamento · retorno_servico · execucao_normal · finalizacao · pausa
- URGÊNCIA: alta · media · baixa

REGRAS:
1. **status_desatualizado** SÓ se aplica quando o Telegram mostra a obra em CATEGORIA MACRO diferente do `status` do painel (ex: telegram mostra equipe finalizando, painel diz "planejamento"). NÃO atribua só porque a `fase` parece "estranha" pro `status` · isso é hierarquia legítima do sistema.
2. **`status_sugerido` JAMAIS pode ser igual ao `status` atual do painel.** Se sua leitura do telegram concorda com o `status` atual, retorne veredicto `coerente` e `status_sugerido: null`.
3. **abandono** = obra ATIVA + silêncio 30+d + data prevista passada (mesmo se painel diz ativo)
4. **detrator** = evidência textual de conflito agudo (advogado, Reclame Aqui)
5. **detrator_latente** (flag) = histórico de quase-distrato, sem manifestação aguda
6. **acao_consultor** = frase curta, concreta, com prazo e responsável quando possível

Retorne APENAS JSON válido (sem markdown, sem texto antes/depois)."""

PROMPT_USUARIO_TEMPLATE = """HOJE: {hoje}

Analise esta obra e retorne JSON com este schema EXATO:

{{
  "veredicto": "coerente|status_desatualizado|abandono|detrator|inconclusivo",
  "status_sugerido": "string ou null",
  "tipo_demanda": "patologia|dano_terceiro|retrabalho_acabamento|retorno_servico|execucao_normal|finalizacao|pausa|null",
  "flags": ["lista", "das", "flags"],
  "acao_consultor": "Frase curta com próxima ação concreta",
  "prazo_acao": "YYYY-MM-DD ou null (sempre >= HOJE · não inventar prazo passado)",
  "urgencia": "alta|media|baixa",
  "confianca": 0.0-1.0
}}

DADOS DA OBRA:
{contexto}
"""


# ============================================================
# Chamada GitHub Models
# ============================================================

def chamar_github_models(prompt_usuario: str, max_retries: int = 2) -> dict | None:
    """
    Chama GitHub Models (gpt-4o-mini default).
    Retorna dict parseado do JSON OU None se falhar.
    """
    if not GITHUB_TOKEN:
        log("AVISO: GITHUB_TOKEN ausente · pulando análise IA")
        return None

    payload = {
        "model": GITHUB_MODEL,
        "messages": [
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": prompt_usuario},
        ],
        "max_tokens": 800,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    last_err = None
    for tentativa in range(max_retries + 1):
        try:
            req = urllib.request.Request(GITHUB_MODELS_URL, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read().decode("utf-8"))
            content = resp["choices"][0]["message"]["content"].strip()
            # Tenta parsear JSON
            return json.loads(content)
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}"
            if e.code == 429 and tentativa < max_retries:
                time.sleep(2 ** tentativa * 5)  # rate limit · espera
                continue
        except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
            last_err = str(e)[:200]
        if tentativa < max_retries:
            time.sleep(2 ** tentativa)

    log(f"AVISO: GitHub Models falhou após {max_retries+1} tentativas · {last_err}")
    return None


# ============================================================
# Aplicação dos resultados
# ============================================================

def aplicar_analise(obra: dict, analise: dict) -> bool:
    """Atualiza obra com resultado da IA. Retorna True se aplicou."""
    if not analise or not isinstance(analise, dict):
        return False

    # Campos diretos
    for campo in ("veredicto", "status_sugerido", "tipo_demanda", "acao_consultor", "prazo_acao", "urgencia"):
        if campo in analise and analise[campo] not in (None, ""):
            obra[campo] = analise[campo]

    # Flags · sobrescreve
    if isinstance(analise.get("flags"), list):
        obra["flags"] = [str(f) for f in analise["flags"] if f]

    # Confiança
    try:
        c = float(analise.get("confianca") or 0)
        obra["confianca"] = max(0.0, min(1.0, c))
    except (TypeError, ValueError):
        pass

    # Atualiza refresh_status
    agora_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rs = obra.setdefault("refresh_status", {})
    rs["veredicto_em"] = agora_iso
    rs["msgs_novas_desde_veredicto"] = 0
    rs["stale"] = False
    rs["horas_desde_veredicto"] = 0.0

    return True


# ============================================================
# Main
# ============================================================

def main():
    ap = argparse.ArgumentParser(description="Análise IA por recorte usando GitHub Models")
    ap.add_argument("--obra-ids", help="IDs separados por vírgula")
    ap.add_argument("--obra-ids-arquivo", help="Arquivo com 1 ID por linha")
    ap.add_argument("--todas-ativas", action="store_true", help="Varre TODAS obras ativas do discord-v3 (status != concluido/finalizado)")
    ap.add_argument("--recorte", default="manual", help="Nome do recorte (apenas pra log)")
    ap.add_argument("--max-obras", type=int, default=500, help="Limite de obras por execução (default: 500)")
    args = ap.parse_args()

    # Carrega discord cedo · precisa pra modo --todas-ativas
    if not DISCORD_PATH.exists():
        log(f"ERRO: {DISCORD_PATH} não encontrado")
        sys.exit(1)
    discord = json.loads(DISCORD_PATH.read_text(encoding="utf-8"))

    # Coleta IDs
    ids: list[str] = []
    if args.todas_ativas:
        ids = [
            o["obra_id"] for o in discord.get("obras", [])
            if (o.get("painel") or {}).get("status_atual") not in ("concluido", "finalizado")
            and o.get("obra_id")
        ]
        log(f"Modo --todas-ativas · {len(ids)} obras (filtradas das {len(discord.get('obras', []))} totais)")
    if args.obra_ids:
        ids.extend([s.strip() for s in args.obra_ids.split(",") if s.strip()])
    if args.obra_ids_arquivo:
        path = Path(args.obra_ids_arquivo)
        if path.exists():
            ids.extend([l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()])
    # Dedup mantendo ordem
    seen = set()
    ids = [x for x in ids if not (x in seen or seen.add(x))]
    if not ids:
        log("ERRO: nenhum ID informado · use --obra-ids, --obra-ids-arquivo ou --todas-ativas")
        sys.exit(1)

    if len(ids) > args.max_obras:
        log(f"AVISO: {len(ids)} IDs > limite {args.max_obras} · cortando")
        ids = ids[:args.max_obras]

    log(f"Recorte: '{args.recorte}' · {len(ids)} obras · modelo {GITHUB_MODEL}")
    log(f"GITHUB_TOKEN: {'OK' if GITHUB_TOKEN else 'AUSENTE'}")

    snapshot = {}
    if TG_SNAPSHOT.exists():
        try:
            tg = json.loads(TG_SNAPSHOT.read_text(encoding="utf-8"))
            snapshot = {o["obra_id"]: o for o in tg.get("obras", [])}
        except Exception as e:
            log(f"AVISO: snapshot Telegram ilegível: {e}")

    painel_idx = {}
    if PAINEL_SNAPSHOT.exists():
        try:
            painel = json.loads(PAINEL_SNAPSHOT.read_text(encoding="utf-8"))
            painel_idx = {o.get("id"): o for o in painel}
        except Exception as e:
            log(f"AVISO: painel-snapshot ilegível: {e}")

    obras_idx = {o["obra_id"]: o for o in discord.get("obras", [])}

    # Processa cada obra
    sucesso = 0
    falha = 0
    inicio = time.time()
    for i, obra_id in enumerate(ids, 1):
        obra = obras_idx.get(obra_id)
        if not obra:
            log(f"  [{i}/{len(ids)}] {obra_id[:8]} · NÃO encontrada · pulando")
            falha += 1
            continue

        cliente_curto = (obra.get("cliente") or "?")[:35]
        log(f"  [{i}/{len(ids)}] {cliente_curto:<37} · analisando...")

        contexto = montar_contexto_obra(obra, snapshot.get(obra_id), painel_idx.get(obra_id))
        hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        prompt = PROMPT_USUARIO_TEMPLATE.format(contexto=contexto, hoje=hoje)

        analise = chamar_github_models(prompt)
        if not analise:
            falha += 1
            log(f"      ✗ análise vazia · obra mantida sem alteração")
            continue

        if aplicar_analise(obra, analise):
            sucesso += 1
            v = obra.get("veredicto", "?")
            u = obra.get("urgencia", "?")
            log(f"      ✓ veredicto={v} · urgência={u}")
        else:
            falha += 1

    elapsed = time.time() - inicio
    log(f"\nResumo · {sucesso}/{len(ids)} sucesso · {falha} falha · {elapsed:.1f}s total")

    # Salva sempre que houve pelo menos 1 sucesso
    if sucesso > 0:
        write_discord(DISCORD_PATH, discord)
        log(f"[OK] {DISCORD_PATH} atualizado")
    else:
        log("Nenhuma análise aplicada · JSON não modificado")
        marcar_step_falho(
            "analisar_recorte/sem_resultados",
            f"Nenhuma análise IA bem-sucedida em {len(ids)} obras (recorte: {args.recorte})",
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
