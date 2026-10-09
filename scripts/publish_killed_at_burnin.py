#!/usr/bin/env python3
"""Publish a pre-registered study that was KILLED AT BURN-IN (negative result). Docs only: nothing is run or scored.

Usage:
    python scripts/publish_killed_at_burnin.py scripts/killed_at_burnin/<slug>.json            # write
    python scripts/publish_killed_at_burnin.py scripts/killed_at_burnin/<slug>.json --check    # dry run + diff
    python scripts/publish_killed_at_burnin.py CONFIG --source-dir /other/dir                 # override source

The JSON config gives: slug, name (label = "<name>: killed at burn-in (negative result)"), source_dir,
files ([{name, sha256}], the expected pins; source files are matched BY HASH, so a renamed file still matches),
design_sha256 (the design JSON; its oos_authorized must be false), learning_sha256 (the teaching page),
verdict_html, what_html, metrics ([[label, value], ...]), rule_html, record_note_html, card_desc_html and
learning_link_text.

Steps (all idempotent):
  1. hash every file in source_dir; every expected sha256 must be present (else exit 2, nothing written);
  2. copy those files byte-for-byte to tracks/<slug>/prereg/ and re-verify the hashes after copying;
  3. check the design JSON: status KILLED_AT_BURNIN and oos_authorized false;
  4. render docs/tracks/<slug>/index.html (navy/black/white, inline CSS, no scripts or external requests);
  5. publish the teaching page verbatim as docs/tracks/<slug>/learning.html;
  6. add the index card "<name>: killed at burn-in (negative result)" and the learning-guides link to docs/index.html
     if absent (an existing card for the slug is left alone).
--check writes nothing: it reports what would change, with a whitespace-normalised comparison of the track page.
"""
import argparse
import hashlib
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'docs' / 'index.html'
TEMPLATE = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>@@LABEL@@</title>\n<style>\n  :root { --navy: #0b2545; --ink: #111; --line: #c9d1dc; }\n  * { box-sizing: border-box; }\n  body { margin: 0; background: #fff; color: var(--ink);\n         font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; line-height: 1.55; }\n  header { background: var(--navy); color: #fff; padding: 1.25rem 1rem; }\n  header a { color: #fff; }\n  .wrap { max-width: 44rem; margin: 0 auto; padding: 0 1rem; }\n  nav { font-size: 0.9rem; margin-bottom: 0.5rem; }\n  h1 { font-size: 1.35rem; line-height: 1.3; margin: 0.25rem 0 0; }\n  h2 { font-size: 1.05rem; color: var(--navy); margin-top: 1.6rem; }\n  main { padding: 1rem 0 3rem; }\n  a { color: var(--navy); }\n  .verdict { border: 2px solid var(--navy); padding: 0.75rem 0.9rem; margin: 1rem 0; }\n  .verdict strong { color: var(--navy); }\n  table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }\n  th, td { border-bottom: 1px solid var(--line); padding: 0.4rem 0.3rem; text-align: left; vertical-align: top; }\n  th { color: var(--navy); }\n  td.num { text-align: right; white-space: nowrap; }\n  code { font-size: 0.85em; overflow-wrap: anywhere; }\n  .scroll { overflow-x: auto; }\n  footer { border-top: 1px solid var(--line); font-size: 0.85rem; padding: 1rem 0 2rem; color: #333; }\n</style>\n</head>\n<body>\n<header>\n  <div class="wrap">\n    <nav><a href="../../index.html">Research Lab</a> › @@NAME@@</nav>\n    <h1>@@NAME@@: Killed at burn-in (negative result)</h1>\n  </div>\n</header>\n<main class="wrap">\n  <div class="verdict">\n    <strong>Status: killed at burn-in. No out-of-sample run.</strong>\n@@VERDICT@@  </div>\n\n  <h2>What was going to be forecast</h2>\n@@WHAT@@\n\n  <h2>The kill rule and the numbers</h2>\n  <div class="scroll"><table>\n    <tbody>\n@@METRICS@@    </tbody>\n  </table></div>\n@@RULE@@\n\n  <h2>Pre-registration record</h2>\n  <div class="scroll"><table>\n    <thead><tr><th>File (tracks/@@SLUG@@/prereg/)</th><th>sha256</th></tr></thead>\n    <tbody>\n@@RECORD@@    </tbody>\n  </table></div>\n@@RECORDNOTE@@\n</main>\n<footer>\n  <div class="wrap">Independent research lab · Not affiliated with any employer or financial institution · Not investment advice.\n  <a href="../../index.html">Home</a></div>\n</footer>\n</body>\n</html>\n'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def label_of(cfg):
    return f"{cfg['name']}: killed at burn-in (negative result)"


def match_sources(cfg, source_dir):
    """{expected sha: source path}; raises SystemExit(2) if any expected hash is missing."""
    by_hash = {}
    for p in sorted(Path(source_dir).iterdir()):
        if p.is_file():
            by_hash.setdefault(sha256(p), p)
    out, missing = {}, []
    for f in cfg['files']:
        p = by_hash.get(f['sha256'])
        if p is None:
            missing.append(f"{f['name']} {f['sha256']}")
        else:
            out[f['sha256']] = p
            if p.name != f['name']:
                print(f"note: {f['name']} matched by hash as {p.name}")
    if missing:
        sys.exit('STOP: expected sha256 not found in ' + str(source_dir) + ':\n  ' + '\n  '.join(missing))
    return out


def render_page(cfg, names):
    """names: {sha: file name as published}."""
    metrics = ''.join(f'      <tr><th>{k}</th><td class="num">{v}</td></tr>\n' for k, v in cfg['metrics'])
    record = ''.join(f'      <tr><td><code>{html.escape(names[f["sha256"]])}</code></td>'
                     f'<td><code>{f["sha256"]}</code></td></tr>\n' for f in cfg['files'])
    out = TEMPLATE
    for key, val in [('@@LABEL@@', label_of(cfg)), ('@@NAME@@', cfg['name']), ('@@SLUG@@', cfg['slug']),
                     ('@@VERDICT@@', cfg['verdict_html']), ('@@WHAT@@', cfg['what_html']),
                     ('@@METRICS@@', metrics), ('@@RULE@@', cfg['rule_html']), ('@@RECORD@@', record),
                     ('@@RECORDNOTE@@', cfg['record_note_html'])]:
        out = out.replace(key, val)
    assert '@@' not in out
    return out


def update_index(text, cfg):
    """Add the track card and learning link if absent. Returns (new_text, list of changes)."""
    slug, changes = cfg['slug'], []
    if f'href="tracks/{slug}/index.html"' not in text:
        n = len(re.findall(r'<a class="track-card" href="tracks/', text)) + 1
        card = (f'    <a class="track-card" href="tracks/{slug}/index.html">\n'
                f'      <div class="track-card__label">Track {n}</div>\n'
                f'      <div class="track-card__title">{label_of(cfg)}</div>\n'
                f'      <p class="track-card__desc">\n{cfg["card_desc_html"]}      </p>\n'
                f'    </a>\n')
        grid = text.index('<div class="track-grid">')
        end = text.index('\n  </div>\n', grid) + 1        # closing tag of the research-track grid
        text = text[:end] + card + text[end:]
        changes.append(f'index: added card Track {n}')
    if f'href="tracks/{slug}/learning.html"' not in text:
        li = f'    <li><a href="tracks/{slug}/learning.html">{cfg["learning_link_text"]}</a></li>\n'
        ul = text.index('<ul class="resource-list">')
        last = [m.end() for m in re.finditer(r'    <li><a href="tracks/[^"]+/learning.html">.*?</a></li>\n', text[ul:])]
        pos = ul + (last[-1] if last else len('<ul class="resource-list">\n'))
        text = text[:pos] + li + text[pos:]
        changes.append('index: added learning link')
    return text, changes


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('config')
    ap.add_argument('--source-dir')
    ap.add_argument('--check', action='store_true', help='write nothing; report differences')
    a = ap.parse_args(argv)
    cfg = json.loads(Path(a.config).read_text(encoding='utf-8'))
    src = Path(a.source_dir or cfg['source_dir'])
    want = {f['sha256'] for f in cfg['files']}
    assert cfg['design_sha256'] in want and cfg['learning_sha256'] in want, 'design/learning must be pinned files'
    sources = match_sources(cfg, src)
    names = {h: p.name for h, p in sources.items()}
    design = json.loads(sources[cfg['design_sha256']].read_text(encoding='utf-8'))
    if design.get('oos_authorized') is not False or design.get('status') != 'KILLED_AT_BURNIN':
        sys.exit(f"STOP: design must have oos_authorized false and status KILLED_AT_BURNIN "
                 f"(got {design.get('oos_authorized')!r}, {design.get('status')!r})")
    prereg = ROOT / 'tracks' / cfg['slug'] / 'prereg'
    docs = ROOT / 'docs' / 'tracks' / cfg['slug']
    page = render_page(cfg, names)
    index_old = INDEX.read_text(encoding='utf-8')
    index_new, index_changes = update_index(index_old, cfg)
    plan = []
    for h, p in sources.items():
        dst = prereg / p.name
        if not dst.exists() or sha256(dst) != h:
            plan.append(f'copy {p.name} -> {dst.relative_to(ROOT)}')
    lp = docs / 'learning.html'
    if not lp.exists() or sha256(lp) != cfg['learning_sha256']:
        plan.append(f'publish {lp.relative_to(ROOT)}')
    tp = docs / 'index.html'
    old_page = tp.read_text(encoding='utf-8') if tp.exists() else None
    if old_page != page:
        same = old_page is not None and norm(old_page) == norm(page)
        plan.append(f'render {tp.relative_to(ROOT)}' + (' (whitespace-only difference)' if same else ''))
    plan += index_changes
    if a.check:
        print('\n'.join(plan) if plan else 'no changes')
        return 0
    prereg.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    for h, p in sources.items():
        shutil.copyfile(p, prereg / p.name)
        if sha256(prereg / p.name) != h:
            sys.exit(f'STOP: copy of {p.name} does not match {h}')
    shutil.copyfile(sources[cfg['learning_sha256']], lp)
    if sha256(lp) != cfg['learning_sha256']:
        sys.exit('STOP: published learning page does not match its pin')
    tp.write_text(page, encoding='utf-8')
    if index_new != index_old:
        INDEX.write_text(index_new, encoding='utf-8')
    print('\n'.join(plan) if plan else 'no changes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
