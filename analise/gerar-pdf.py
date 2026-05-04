"""
gerar-pdf.py — Converte o .md do relatório em .html estilizado pra exportar PDF
==============================================================================

Lê o último relatório .md em analise/relatorios/ e gera .html ao lado, com
CSS Monofloor (cream, Plus Jakarta, header/footer Monofloor) + @page rules
pra impressão.

Uso:
    python gerar-pdf.py                              # último .md da pasta
    python gerar-pdf.py 2026-05-quinzena-1.md        # arquivo específico

Pra exportar PDF: abrir o .html no Chrome → Ctrl+P → "Salvar como PDF" →
"Mais opções" → habilitar "Cabeçalhos e rodapés" se quiser numeração.

Sem dependência externa · conversor markdown→HTML minimal embutido.
"""

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SAIDA = ROOT / "relatorios"


# ═══ Conversor Markdown → HTML (subset que cobre o relatório) ═══

def md_to_html(md):
    """Conversor minimal MD→HTML pro nosso template fixo."""
    out = []
    lines = md.split("\n")
    i = 0
    in_table = False
    table_buf = []
    in_list = False
    in_blockquote = False
    blockquote_buf = []

    def flush_table():
        nonlocal in_table, table_buf
        if not in_table or not table_buf:
            return
        # Primeira linha = header, segunda = separator (ignorar), resto = body
        rows = [r for r in table_buf if r.strip()]
        if len(rows) >= 2:
            header = parse_row(rows[0])
            body_rows = [parse_row(r) for r in rows[2:]]
            tab_html = ['<table>']
            tab_html.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in header) + "</tr></thead>")
            tab_html.append("<tbody>")
            for r in body_rows:
                tab_html.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
            tab_html.append("</tbody></table>")
            out.append("\n".join(tab_html))
        in_table = False
        table_buf = []

    def parse_row(line):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        return [inline_md(c) for c in cells]

    def flush_blockquote():
        nonlocal in_blockquote, blockquote_buf
        if not in_blockquote or not blockquote_buf:
            return
        joined = " ".join(blockquote_buf)
        out.append(f"<blockquote>{inline_md(joined)}</blockquote>")
        in_blockquote = False
        blockquote_buf = []

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Tabela
        if "|" in line and (line.strip().startswith("|") or in_table):
            if not in_table:
                flush_blockquote()
                flush_list()
                in_table = True
            table_buf.append(line)
            i += 1
            continue
        else:
            if in_table:
                flush_table()

        # Blockquote
        if stripped.startswith(">"):
            if not in_blockquote:
                flush_list()
                in_blockquote = True
            blockquote_buf.append(stripped.lstrip(">").strip())
            i += 1
            continue
        else:
            if in_blockquote:
                flush_blockquote()

        # Headers
        if stripped.startswith("####"):
            flush_list()
            out.append(f"<h4>{inline_md(stripped[4:].strip())}</h4>")
            i += 1
            continue
        if stripped.startswith("###"):
            flush_list()
            out.append(f"<h3>{inline_md(stripped[3:].strip())}</h3>")
            i += 1
            continue
        if stripped.startswith("##"):
            flush_list()
            out.append(f"<h2>{inline_md(stripped[2:].strip())}</h2>")
            i += 1
            continue
        if stripped.startswith("# "):
            flush_list()
            out.append(f"<h1>{inline_md(stripped[2:].strip())}</h1>")
            i += 1
            continue

        # HR
        if stripped == "---":
            flush_list()
            out.append("<hr/>")
            i += 1
            continue

        # Lista
        if stripped.startswith("- ") or re.match(r"^\d+\.\s", stripped):
            if not in_list:
                out.append("<ul>")
                in_list = True
            content = re.sub(r"^(\d+\.|\-)\s+", "", stripped)
            out.append(f"<li>{inline_md(content)}</li>")
            i += 1
            continue
        else:
            flush_list()

        # Linha em branco
        if not stripped:
            i += 1
            continue

        # HTML comments → ignore
        if stripped.startswith("<!--"):
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue

        # Parágrafo
        out.append(f"<p>{inline_md(stripped)}</p>")
        i += 1

    flush_table()
    flush_blockquote()
    flush_list()
    return "\n".join(out)


def inline_md(text):
    """Aplica formatação inline: bold, italic, code, links."""
    if not text:
        return ""
    # Não escapar HTML aqui pra preservar entidades já escapadas
    # Code inline `...`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Bold ***
    text = re.sub(r"\*\*\*([^*]+)\*\*\*", r"<strong><em>\1</em></strong>", text)
    # Bold **
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # Italic *...*
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    # Italic _..._
    text = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"<em>\1</em>", text)
    # Links [texto](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


# ═══ Template HTML + CSS Monofloor ═══

TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>{titulo}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@200;300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box}}

@page {{
  size: A4;
  margin: 25mm 20mm 20mm 20mm;
  @top-right {{
    content: "Relatório Quinzenal de Qualidade · Monofloor";
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 9px;
    color: #a89e92;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }}
  @bottom-center {{
    content: "página " counter(page) " de " counter(pages);
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #a89e92;
  }}
  @bottom-right {{
    content: "monofloor.com.br";
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #c8bfb4;
  }}
}}

body {{
  font-family: 'Plus Jakarta Sans', sans-serif;
  background: #fefcf8;
  color: #2a2520;
  line-height: 1.65;
  font-size: 11pt;
  margin: 0;
  padding: 0;
}}

.wrap {{
  max-width: 720px;
  margin: 0 auto;
  padding: 40px 32px 60px;
}}

.brand-bar {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2px solid #b8a080;
  padding-bottom: 14px;
  margin-bottom: 28px;
}}
.brand-bar .logo {{
  font-size: 18px;
  font-weight: 200;
  letter-spacing: 8px;
  text-transform: lowercase;
  color: #2a2520;
}}
.brand-bar .meta {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #8a7e72;
}}

h1 {{
  font-size: 28pt;
  font-weight: 200;
  letter-spacing: -0.02em;
  color: #2a2520;
  margin: 0 0 8px;
  line-height: 1.2;
}}

h2 {{
  font-size: 17pt;
  font-weight: 600;
  color: #2a2520;
  margin: 32px 0 14px;
  padding-top: 18px;
  border-top: 1px solid #e8e0d4;
  page-break-after: avoid;
  break-after: avoid;
}}
h2:first-of-type {{ border-top: none; padding-top: 0; }}

h3 {{
  font-size: 13pt;
  font-weight: 600;
  color: #3a3530;
  margin: 22px 0 10px;
  page-break-after: avoid;
  break-after: avoid;
}}
h4 {{
  font-size: 11pt;
  font-weight: 600;
  color: #5a5048;
  margin: 16px 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}

p {{ margin: 8px 0 12px; }}

strong {{ color: #2a2520; font-weight: 600; }}
em {{ color: #5a5048; font-style: italic; }}

code {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5pt;
  background: #f4f0e8;
  border: 1px solid #e8e0d4;
  border-radius: 3px;
  padding: 1px 5px;
  color: #5a4a2a;
}}

ul {{
  margin: 6px 0 14px;
  padding-left: 22px;
}}
li {{ margin: 4px 0; }}
li strong:first-child {{ color: #b8884a; }}

blockquote {{
  border-left: 3px solid #b8a080;
  background: #faf6ed;
  margin: 12px 0;
  padding: 10px 16px;
  color: #5a5048;
  font-size: 10.5pt;
  page-break-inside: avoid;
  break-inside: avoid;
  border-radius: 0 4px 4px 0;
}}
blockquote em {{ color: #6b6156; }}
blockquote strong {{ color: #5a4a2a; }}

table {{
  width: 100%;
  border-collapse: collapse;
  margin: 14px 0 18px;
  font-size: 10pt;
  page-break-inside: avoid;
  break-inside: avoid;
}}
thead th {{
  background: #f0e9da;
  border-bottom: 2px solid #b8a080;
  padding: 8px 10px;
  text-align: left;
  font-weight: 600;
  color: #2a2520;
  font-size: 9.5pt;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}
tbody td {{
  border-bottom: 1px solid #ede6dc;
  padding: 7px 10px;
  vertical-align: top;
}}
tbody tr:last-child td {{ border-bottom: none; }}
tbody tr:nth-child(even) {{ background: #faf7f2; }}

hr {{
  border: none;
  border-top: 1px dashed #d8c8a8;
  margin: 24px 0;
}}

a {{ color: #6b8e3d; text-decoration: none; border-bottom: 1px dotted #6b8e3d; }}

/* Bloco de receita / caminho na seção 10 */
h3 + p strong:first-child,
p strong:first-child {{ color: #5a4a2a; }}

/* Quebra de página entre seções principais */
h2 {{ page-break-before: auto; }}

/* Não quebrar páginas dentro de blocos-chave */
table, blockquote, h2 + p, h3 + p {{ page-break-inside: avoid; break-inside: avoid; }}

/* Botão flutuante de ajuda na visualização */
.help-banner {{
  position: fixed;
  top: 12px;
  right: 12px;
  background: #fdf5e3;
  border: 1px solid #e6d4a8;
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 11px;
  color: #5a4a2a;
  box-shadow: 0 4px 12px rgba(42,37,32,0.1);
  z-index: 1000;
  font-family: 'Plus Jakarta Sans', sans-serif;
  max-width: 280px;
  line-height: 1.5;
}}
.help-banner strong {{ color: #b8884a; }}
@media print {{ .help-banner {{ display: none; }} }}
</style>
</head>
<body>
<div class="help-banner">
  <strong>📄 Pra exportar PDF</strong><br>
  Pressione <strong>Ctrl+P</strong> · destino <strong>"Salvar como PDF"</strong> · papel A4 · margens padrão. Esse aviso some na impressão.
</div>

<div class="wrap">
  <div class="brand-bar">
    <span class="logo">monofloor</span>
    <span class="meta">Setor de Qualidade · {versao}</span>
  </div>

{conteudo}

</div>
</body>
</html>
"""


# ═══ Main ═══

def main():
    p = argparse.ArgumentParser()
    p.add_argument("arquivo", nargs="?", help="Nome do .md em analise/relatorios/ (default: último)")
    args = p.parse_args()

    if args.arquivo:
        md_path = SAIDA / args.arquivo
    else:
        # Pega o .md mais recente
        candidatos = sorted(SAIDA.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
        candidatos = [c for c in candidatos if c.name not in ("template-quinzenal.md", "README.md")]
        if not candidatos:
            print("ERRO: nenhum .md encontrado em analise/relatorios/", file=sys.stderr)
            sys.exit(1)
        md_path = candidatos[0]

    if not md_path.exists():
        print(f"ERRO: {md_path} não existe", file=sys.stderr)
        sys.exit(1)

    print(f"Lendo: {md_path.name}")
    md = md_path.read_text(encoding="utf-8")

    conteudo = md_to_html(md)

    # Extrai título do H1 pra usar no <title>
    m = re.search(r"<h1>([^<]+)</h1>", conteudo)
    titulo = m.group(1) if m else "Relatório Quinzenal de Qualidade"

    # Versão = nome do arquivo
    versao = md_path.stem

    html_str = TEMPLATE.format(titulo=titulo, conteudo=conteudo, versao=versao)
    html_path = md_path.with_suffix(".html")
    html_path.write_text(html_str, encoding="utf-8")

    print(f"[OK] HTML gerado: {html_path}")
    print(f"     Tamanho: {len(html_str):,} bytes")
    print(f"\nPara exportar PDF:")
    print(f"  1. Abrir no browser: {html_path}")
    print(f"  2. Ctrl+P · destino 'Salvar como PDF' · A4 · margens padrão")


if __name__ == "__main__":
    main()
