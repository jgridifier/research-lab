#!/usr/bin/env python3
"""Render a pinned lab-plan Markdown file to a static Pages HTML page (inline CSS, no scripts, no external requests).

Usage:
    python scripts/render_lab_plan.py SOURCE.md OUT.html --title "..." --nav "CP funding" [--sha256 HEX]
                                      [--source-label path/in/repo.md] [--extra-link href "text"]...
                                      [--status "label"] [--note "text"] [--pin NAME SHA256]... [--check]

Supported Markdown subset (what Quant's plans use): # / ## / ### headings, paragraphs (consecutive lines kept as
line breaks), nested "-" and "1." lists by indentation, pipe tables, **bold**, *italic*, `code`.
--status puts an exact status label at the top of the page; --note replaces the default "A plan, not a result" note;
each --pin adds a row to a "Pinned files" sha256 table above the body (the script does not hash those files; the
track's pin test does). --sha256 makes the script refuse to render if the source does not hash to the pin. --check writes nothing and
exits 1 if OUT.html would change.
"""
import argparse
import hashlib
import html
import re
import sys
from pathlib import Path

CSS = """  :root { --navy: #0b2545; --ink: #111; --line: #c9d1dc; }
  * { box-sizing: border-box; }
  body { margin: 0; background: #fff; color: var(--ink);
         font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.55; }
  header { background: var(--navy); color: #fff; padding: 1.25rem 1rem; }
  header a { color: #fff; }
  .wrap { max-width: 44rem; margin: 0 auto; padding: 0 1rem; }
  nav { font-size: 0.9rem; margin-bottom: 0.5rem; }
  h1 { font-size: 1.35rem; line-height: 1.3; margin: 0.25rem 0 0; }
  h2 { font-size: 1.05rem; color: var(--navy); margin-top: 1.6rem; }
  h3 { font-size: 0.98rem; color: var(--navy); }
  main { padding: 1rem 0 3rem; overflow-wrap: break-word; }
  a { color: var(--navy); }
  ul, ol { padding-left: 1.3rem; }
  li { margin: 0.2rem 0; }
  .status { color: var(--navy); font-size: 1.05rem; }
  .note { border: 2px solid var(--navy); padding: 0.75rem 0.9rem; margin: 1rem 0; }
  table { border-collapse: collapse; width: 100%; font-size: 0.88rem; }
  th, td { border-bottom: 1px solid var(--line); padding: 0.4rem 0.3rem; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
  th { color: var(--navy); }
  code { font-size: 0.85em; overflow-wrap: anywhere; }
  .scroll { overflow-x: auto; }
  footer { border-top: 1px solid var(--line); font-size: 0.85rem; padding: 1rem 0 2rem; color: #333; }"""


def inline(s):
    parts = re.split(r'(`[^`]+`)', s)
    out = []
    for p in parts:
        if p.startswith('`') and p.endswith('`') and len(p) > 1:
            out.append('<code>' + html.escape(p[1:-1], quote=False) + '</code>')
            continue
        p = html.escape(p, quote=False)
        p = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', p)
        p = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', p)
        out.append(p)
    return ''.join(out)


LIST = re.compile(r'^( *)(-|\d+\.) (.*)$')


def render_list(lines, i):
    """Render the list starting at lines[i]; returns (html, next index)."""
    indent = len(LIST.match(lines[i]).group(1))
    ordered = LIST.match(lines[i]).group(2) != '-'
    tag = 'ol' if ordered else 'ul'
    start = LIST.match(lines[i]).group(2)[:-1] if ordered else None
    out = [f'<{tag}' + (f' start="{start}"' if ordered and start != '1' else '') + '>']
    while i < len(lines):
        m = LIST.match(lines[i])
        if not m or len(m.group(1)) < indent:
            break
        if len(m.group(1)) > indent:                         # nested list belongs to the previous item
            sub, i = render_list(lines, i)
            out[-1] = out[-1][:-len('</li>')] + sub + '</li>'
            continue
        if (m.group(2) == '-') == ordered:                    # list type changes at the same level
            break
        out.append('<li>' + inline(m.group(3)) + '</li>')
        i += 1
    out.append(f'</{tag}>')
    return '\n'.join(out), i


def render_table(rows):
    cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
    head, body = cells[0], cells[2:]
    h = '<div class="scroll"><table>\n<thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead>\n<tbody>\n'
    for r in body:
        h += '<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>\n'
    return h + '</tbody></table></div>'


def render_body(md):
    lines = md.splitlines()
    out, i, title = [], 0, None
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
        elif ln.startswith('# ') and title is None:
            title = ln[2:].strip()
            i += 1
        elif re.match(r'^#{1,3} ', ln):
            n = min(len(ln) - len(ln.lstrip('#')), 3)
            out.append(f'<h{n}>{inline(ln.lstrip("#").strip())}</h{n}>')
            i += 1
        elif LIST.match(ln):
            h, i = render_list(lines, i)
            out.append(h)
        elif ln.lstrip().startswith('|'):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith('|'):
                j += 1
            out.append(render_table(lines[i:j]))
            i = j
        else:
            j = i
            while j < len(lines) and lines[j].strip() and not LIST.match(lines[j]) \
                    and not lines[j].startswith('#') and not lines[j].lstrip().startswith('|'):
                j += 1
            out.append('<p>' + '<br>\n'.join(inline(x.strip()) for x in lines[i:j]) + '</p>')
            i = j
    return title, '\n'.join(out)


def render_page(md, *, title, nav, source_label, sha, extra_links, status=None, note=None, pins=()):
    md_title, body = render_body(md)
    links = ''.join(f' · <a href="{html.escape(h)}">{html.escape(t)}</a>' for h, t in extra_links)
    note = html.escape(note, quote=False) if note else 'A plan, not a result. Nothing in it has been scored.'
    status_html = f'<strong class="status">{html.escape(status, quote=False)}</strong><br>\n  ' if status else ''
    pin_html = ''
    if pins:
        pin_html = ('<h2>Pinned files</h2>\n<div class="scroll"><table>\n<thead><tr><th>file</th><th>sha256</th></tr></thead>\n<tbody>\n'
                    + ''.join(f'<tr><td><code>{html.escape(n)}</code></td><td><code>{s}</code></td></tr>\n' for n, s in pins)
                    + '</tbody></table></div>\n')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
{CSS}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <nav><a href="../../index.html">Research Lab</a> › {html.escape(nav)}</nav>
    <h1>{inline(md_title or title)}</h1>
  </div>
</header>
<main class="wrap">
  <p class="note">{status_html}{note} Rendered from the pinned source
  <code>{html.escape(source_label)}</code>, sha256 <code>{sha}</code>{links}.</p>
{pin_html}{body}
</main>
<footer class="wrap">
  Independent research lab · Not affiliated with any employer or financial institution · Not investment advice.
</footer>
</body>
</html>
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('source')
    ap.add_argument('out')
    ap.add_argument('--title', required=True)
    ap.add_argument('--nav', required=True)
    ap.add_argument('--sha256')
    ap.add_argument('--source-label')
    ap.add_argument('--extra-link', nargs=2, action='append', default=[], metavar=('HREF', 'TEXT'))
    ap.add_argument('--status')
    ap.add_argument('--note')
    ap.add_argument('--pin', nargs=2, action='append', default=[], metavar=('NAME', 'SHA256'))
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args(argv)
    raw = Path(a.source).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if a.sha256 and sha != a.sha256:
        sys.exit(f'STOP: {a.source} sha256 {sha} != pinned {a.sha256}')
    page = render_page(raw.decode('utf-8'), title=a.title, nav=a.nav, source_label=a.source_label or a.source,
                       sha=sha, extra_links=a.extra_link, status=a.status, note=a.note, pins=a.pin)
    out = Path(a.out)
    same = out.exists() and out.read_text(encoding='utf-8') == page
    if a.check:
        print('no changes' if same else f'would write {out}')
        return 0 if same else 1
    if not same:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding='utf-8')
    print('no changes' if same else f'wrote {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
