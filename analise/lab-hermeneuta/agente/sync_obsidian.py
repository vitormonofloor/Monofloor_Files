"""
sync_obsidian.py · Espelha o estado do projeto Orion no vault Obsidian
========================================================================

Copia os MDs do _projeto/, RETOMAR, ROADMAP, _storytelling/, _jornadas/ e
memórias relevantes do Orion pra
   C:\\Users\\vitor\\Downloads\\monofloor-vault\\obsidian-vault\\ORION\\

NÃO é automático · trigger manual quando Vitor pedir "sync orion" ou
"sincroniza obsidian" no chat. Pra rodar standalone:

    python agente/sync_obsidian.py

CUIDADOS:
- Vault não é git · alterações definitivas
- Só toca dentro de ORION/ · nunca mexe em outras notas
- Backup .bak preservado se sobrescrever versão anterior
"""

import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import setup_utf8

setup_utf8()

ROOT = Path(__file__).parent.parent
PROJETO_DIR = ROOT / "_projeto"
STORYTELLING_DIR = ROOT / "_storytelling"
JORNADAS_DIR = ROOT / "_jornadas"
MEMORY_DIR = Path("C:/Users/vitor/.claude/projects/C--Users-vitor/memory")

VAULT_BASE = Path("C:/Users/vitor/Downloads/monofloor-vault/obsidian-vault")
ORION_DIR = VAULT_BASE / "ORION"

HOJE = datetime.now(timezone.utc)
HOJE_BR = HOJE.strftime("%Y-%m-%d %H:%M UTC")


def add_frontmatter(conteudo: str, source: str, tags: list[str]) -> str:
    """Adiciona ou atualiza frontmatter Obsidian no início do markdown."""
    fm = "---\n"
    fm += f"tags: [{', '.join(tags)}]\n"
    fm += f"sincronizado_em: {HOJE_BR}\n"
    fm += f"fonte: {source}\n"
    fm += "---\n\n"
    # Se já tem frontmatter (---...---), substitui
    if conteudo.startswith("---\n"):
        try:
            fim_fm = conteudo.index("\n---\n", 4) + 5
            corpo = conteudo[fim_fm:].lstrip()
            return fm + corpo
        except ValueError:
            pass
    return fm + conteudo


def copiar_com_backup(src: Path, dst: Path, source_label: str, tags: list[str]):
    """Copia src → dst com frontmatter. Faz .bak se dst já existir e é diferente."""
    if not src.exists():
        return False, "src_inexistente"
    conteudo = src.read_text(encoding="utf-8")
    novo = add_frontmatter(conteudo, source_label, tags)

    if dst.exists():
        atual = dst.read_text(encoding="utf-8")
        if atual == novo:
            return True, "sem_mudanca"
        # Backup do anterior
        bak = dst.with_suffix(dst.suffix + ".bak")
        bak.write_text(atual, encoding="utf-8")

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(novo, encoding="utf-8")
    return True, "atualizado"


def listar_memorias_orion():
    """Lista memórias relacionadas ao Orion (project_orion_*, feedback_kira_*, feedback_verificar_*)."""
    if not MEMORY_DIR.exists():
        return []
    candidatos = []
    padroes = [
        "project_orion_*.md",
        "project_hermeneuta*.md",
        "feedback_kira_*.md",
        "feedback_verificar_consumidor*.md",
    ]
    for pad in padroes:
        candidatos.extend(MEMORY_DIR.glob(pad))
    return sorted(set(candidatos))


def main():
    print(f"[SYNC] Espelhando estado do projeto Orion no vault Obsidian")
    print(f"[SYNC] Destino: {ORION_DIR}")
    print()

    if not VAULT_BASE.exists():
        print(f"ERRO: vault não existe em {VAULT_BASE}")
        sys.exit(1)

    ORION_DIR.mkdir(parents=True, exist_ok=True)

    # Mapeamento src → dst no ORION/
    arquivos_principais = [
        # (src, dst_relative_to_ORION, source_label, tags)
        (PROJETO_DIR / "README.md",         "README.md",                  "_projeto/README.md",         ["orion", "indice"]),
        (PROJETO_DIR / "HISTORIA.md",       "01-HISTORIA.md",             "_projeto/HISTORIA.md",       ["orion", "historia"]),
        (PROJETO_DIR / "ESTADO.md",         "02-ESTADO.md",               "_projeto/ESTADO.md",         ["orion", "estado"]),
        (PROJETO_DIR / "ARQUITETURA.md",    "03-ARQUITETURA.md",          "_projeto/ARQUITETURA.md",    ["orion", "arquitetura"]),
        (PROJETO_DIR / "PENDENCIAS.md",     "04-PENDENCIAS.md",           "_projeto/PENDENCIAS.md",     ["orion", "pendencias"]),
        (PROJETO_DIR / "RUNBOOK.md",        "05-RUNBOOK.md",              "_projeto/RUNBOOK.md",        ["orion", "runbook"]),
        (PROJETO_DIR / "APRENDIZADOS.md",   "06-APRENDIZADOS.md",         "_projeto/APRENDIZADOS.md",   ["orion", "aprendizados"]),
        (PROJETO_DIR / "INVENTARIO.md",     "07-INVENTARIO.md",           "_projeto/INVENTARIO.md",     ["orion", "inventario"]),
        (PROJETO_DIR / "JORNADA_LOGICA.md", "08-JORNADA-LOGICA.md",       "_projeto/JORNADA_LOGICA.md", ["orion", "jornada", "logica"]),
        (ROOT / "RETOMAR.md",               "09-RETOMAR.md",              "RETOMAR.md",                 ["orion", "retomar"]),
        (ROOT / "ROADMAP_CAMINHO_B.md",     "10-ROADMAP-CAMINHO-B.md",    "ROADMAP_CAMINHO_B.md",       ["orion", "roadmap"]),
    ]

    stats = {"atualizado": 0, "sem_mudanca": 0, "src_inexistente": 0}
    arquivos_sincronizados = []

    print("=== Arquivos principais ===")
    for src, rel, source_label, tags in arquivos_principais:
        dst = ORION_DIR / rel
        ok, status = copiar_com_backup(src, dst, source_label, tags)
        stats[status] = stats.get(status, 0) + 1
        marca = {"atualizado": "✓", "sem_mudanca": "·", "src_inexistente": "✗"}.get(status, "?")
        print(f"  {marca} {rel:<30} ({status})")
        if status == "atualizado":
            arquivos_sincronizados.append(rel)

    # Storytellings
    print("\n=== Storytellings ===")
    if STORYTELLING_DIR.exists():
        for src in sorted(STORYTELLING_DIR.glob("*.md")):
            dst = ORION_DIR / "_storytelling" / src.name
            ok, status = copiar_com_backup(src, dst, f"_storytelling/{src.name}", ["orion", "storytelling"])
            stats[status] = stats.get(status, 0) + 1
            marca = {"atualizado": "✓", "sem_mudanca": "·"}.get(status, "?")
            print(f"  {marca} _storytelling/{src.name}  ({status})")
            if status == "atualizado":
                arquivos_sincronizados.append(f"_storytelling/{src.name}")

    # Jornadas
    print("\n=== Jornadas ===")
    if JORNADAS_DIR.exists():
        for src in sorted(JORNADAS_DIR.glob("*.md")):
            dst = ORION_DIR / "_jornadas" / src.name
            ok, status = copiar_com_backup(src, dst, f"_jornadas/{src.name}", ["orion", "jornada"])
            stats[status] = stats.get(status, 0) + 1
            marca = {"atualizado": "✓", "sem_mudanca": "·"}.get(status, "?")
            print(f"  {marca} _jornadas/{src.name[:8]}...  ({status})")
            if status == "atualizado":
                arquivos_sincronizados.append(f"_jornadas/{src.name}")

    # Memórias
    print("\n=== Memórias relacionadas ao Orion ===")
    for src in listar_memorias_orion():
        dst = ORION_DIR / "_memoria" / src.name
        ok, status = copiar_com_backup(src, dst, f"memory/{src.name}", ["orion", "memoria"])
        stats[status] = stats.get(status, 0) + 1
        marca = {"atualizado": "✓", "sem_mudanca": "·"}.get(status, "?")
        print(f"  {marca} _memoria/{src.name}  ({status})")
        if status == "atualizado":
            arquivos_sincronizados.append(f"_memoria/{src.name}")

    # Index master
    print("\n=== Gerando INDEX.md ===")
    index_content = gerar_index(ORION_DIR)
    (ORION_DIR / "INDEX.md").write_text(index_content, encoding="utf-8")
    print("  ✓ INDEX.md")

    # Último sync
    sync_log = gerar_sync_log(arquivos_sincronizados, stats)
    (ORION_DIR / "_ULTIMO_SYNC.md").write_text(sync_log, encoding="utf-8")
    print("  ✓ _ULTIMO_SYNC.md")

    print()
    print(f"[OK] Total: {stats['atualizado']} atualizados · {stats['sem_mudanca']} sem mudança")
    print(f"     Vault: {ORION_DIR}")


def gerar_index(orion_dir: Path) -> str:
    """Gera INDEX.md listando todos os arquivos da pasta ORION com links."""
    md = ["---"]
    md.append("tags: [orion, indice]")
    md.append(f"sincronizado_em: {HOJE_BR}")
    md.append("---")
    md.append("")
    md.append("# 🛰 ORION · Índice do Vault")
    md.append("")
    md.append(f"> Atualizado em **{HOJE_BR}** via `agente/sync_obsidian.py`")
    md.append("")
    md.append("## Núcleo do projeto")
    md.append("")
    principais = [
        ("README.md", "Visão geral · entrada"),
        ("01-HISTORIA.md", "Linha do tempo + decisões"),
        ("02-ESTADO.md", "O que está bom · com problema · métricas"),
        ("03-ARQUITETURA.md", "Pipeline · scripts · APIs"),
        ("04-PENDENCIAS.md", "Caminho B · Storytelling · Cores · Opção B"),
        ("05-RUNBOOK.md", "Receitas operacionais"),
        ("06-APRENDIZADOS.md", "10+ padrões consolidados"),
        ("07-INVENTARIO.md", "Mapa físico · onde mora cada arquivo"),
        ("08-JORNADA-LOGICA.md", "Como o detector de jornada funciona"),
        ("09-RETOMAR.md", "Overview rápido pra retomada"),
        ("10-ROADMAP-CAMINHO-B.md", "Refactor estrutural pendente"),
    ]
    for nome, desc in principais:
        if (orion_dir / nome).exists():
            md.append(f"- [[{nome[:-3]}]] · {desc}")
    md.append("")

    # Storytellings
    storytellings = sorted((orion_dir / "_storytelling").glob("*.md")) if (orion_dir / "_storytelling").exists() else []
    if storytellings:
        md.append("## Storytellings · obras finalizadas")
        md.append("")
        for s in storytellings:
            md.append(f"- [[_storytelling/{s.stem}]]")
        md.append("")

    # Jornadas
    jornadas = sorted((orion_dir / "_jornadas").glob("*.md")) if (orion_dir / "_jornadas").exists() else []
    if jornadas:
        md.append("## Jornadas · análise retrospectiva automática")
        md.append("")
        for j in jornadas:
            md.append(f"- [[_jornadas/{j.stem}]]")
        md.append("")

    # Memórias
    memorias = sorted((orion_dir / "_memoria").glob("*.md")) if (orion_dir / "_memoria").exists() else []
    if memorias:
        md.append("## Memórias do agente · relacionadas ao Orion")
        md.append("")
        for m in memorias:
            md.append(f"- [[_memoria/{m.stem}]]")
        md.append("")

    md.append("---")
    md.append("")
    md.append(f"_Vault espelha o estado de `Monofloor_Files/analise/lab-hermeneuta/`._")
    md.append(f"_Re-rode `python agente/sync_obsidian.py` ou peça \"sync orion\" no chat pra atualizar._")
    return "\n".join(md)


def gerar_sync_log(arquivos: list[str], stats: dict) -> str:
    md = ["---"]
    md.append("tags: [orion, sync, log]")
    md.append(f"sincronizado_em: {HOJE_BR}")
    md.append("---")
    md.append("")
    md.append(f"# Último sync · {HOJE_BR}")
    md.append("")
    md.append(f"- ✓ **{stats.get('atualizado', 0)}** atualizados")
    md.append(f"- · {stats.get('sem_mudanca', 0)} sem mudança")
    md.append(f"- ✗ {stats.get('src_inexistente', 0)} fonte inexistente")
    md.append("")
    if arquivos:
        md.append("## Arquivos atualizados nesta rodada")
        md.append("")
        for a in arquivos:
            md.append(f"- `{a}`")
    else:
        md.append("_(nenhum arquivo precisava atualização)_")
    return "\n".join(md)


if __name__ == "__main__":
    main()
