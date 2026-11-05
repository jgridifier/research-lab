#!/usr/bin/env python3
"""Render the Fed CP OT out-of-sample results page (PREREG v2 12 T8) from tracks/fed-cp-ot/oos_result.json.

Without that file the page states that no OOS result exists. Standard library only. --check verifies without writing."""
import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / 'tracks/fed-cp-ot/oos_result.json'
PAGE = ROOT / 'docs/tracks/fed-cp-ot/results.html'
CSS = """:root { --navy: #0b2545; --ink: #111; --line: #c9d1dc; }
  * { box-sizing: border-box; }
  body { margin: 0; background: #fff; color: var(--ink); font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; line-height: 1.55; }
  header { background: var(--navy); color: #fff; padding: 1.25rem 1rem; }
  header a { color: #fff; }
  .wrap { max-width: 60rem; margin: 0 auto; padding: 0 1rem; }
  h1 { font-size: 1.35rem; margin: 0.25rem 0 0; }
  h2 { font-size: 1.05rem; color: var(--navy); margin-top: 1.6rem; }
  main { padding: 1rem 0 3rem; overflow-wrap: break-word; }
  .note { border: 2px solid var(--navy); padding: 0.75rem 0.9rem; margin: 1rem 0; }
  table { border-collapse: collapse; width: 100%; font-size: 0.88rem; }
  th, td { border-bottom: 1px solid var(--line); padding: 0.4rem 0.3rem; text-align: left; vertical-align: top; }
  th { color: var(--navy); }
  .scroll { overflow-x: auto; }"""

def fmt(v, nd=4):
    return '' if v is None else (f'{v:.{nd}f}' if isinstance(v, float) else str(v))

def render(result):
    e = html.escape
    if result is None:
        body = ('<p class="note"><strong>No out-of-sample result exists.</strong> OOS scoring is not authorized: there is no '
                'APPROVAL_fed_cp_ot.txt and APPROVAL_SHA256 is not set. This page is regenerated from <code>tracks/fed-cp-ot/oos_result.json</code> '
                'after the single approved run (PREREG v2 section 10).</p>')
    else:
        rows = []
        for label, r in result['families'].items():
            gs = ', '.join(f'{k}: {fmt(v)}' for k, v in r['G_s'].items())
            flag = 'INCOMPLETE: ' + e(r['incomplete_reason'] or '') if r['incomplete'] else ''
            rows.append(f"<tr><td>{e(r['family'])}</td><td>{e(label)}</td><td>{fmt(r['G'])}</td><td>{e(gs)}</td><td>{fmt(r['p'])}</td>"
                        f"<td>{r['n_pairs']}</td><td>{fmt(r['phi'])}</td><td>{flag}</td><td>{'yes' if r['claim'] else 'no'}</td>"
                        f"<td>{e(r.get('wording', ''))}</td></tr>")
        d = result['disclosures']
        body = (f'<p class="note"><strong>{e(result["label"])}</strong><br>Run once; lock <code>{e(result["lock_sha256"])}</code>. '
                f'Vintage <code>{e(result["manifest"]["zip_sha256"])}</code>.</p>'
                '<h2>Confirmatory tests (5; Holm within each family; no cross-family control is claimed)</h2><div class="scroll"><table>'
                '<tr><th>Family</th><th>Test</th><th>G</th><th>G by subperiod</th><th>p</th><th>Paired weeks</th><th>phi</th><th>Status</th><th>Claim</th><th>Wording</th></tr>'
                + ''.join(rows) + '</table></div>'
                f'<h2>Family K</h2><p>Kumo failed at {result["family_K"]["failed_origins"]} of {result["family_K"]["origins"]} origins; '
                f'incomplete: {result["family_K"]["incomplete"]}.</p>'
                '<h2>Disclosures (non-gating)</h2><ul>'
                f'<li>Revised pre-wall values across archived vintages: {e(str(d["revised_pre_wall_values_across_archived_vintages"]))}</li>'
                f'<li>FAA GT80 input shares floored at 1e-4: {fmt(d["faa_gt80_floored_input_share_fraction"])}</li>'
                f'<li>{e(d["pseudo_real_time"])}</li></ul>')
    return (f'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>Fed CP maturity mix × OT: out-of-sample results</title>\n<style>\n  {CSS}\n</style>\n</head>\n<body>\n<header>\n  <div class="wrap">\n'
            f'    <a href="../../index.html">Research Lab</a> › <a href="index.html">Fed CP maturity mix × OT</a> › Results\n'
            f'    <h1>Fed CP maturity mix × OT: out-of-sample results</h1>\n  </div>\n</header>\n<main class="wrap">\n{body}\n</main>\n</body>\n</html>\n')

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--result', default=str(RESULT)); ap.add_argument('--out', default=str(PAGE))
    args = ap.parse_args(argv)
    path = Path(args.result)
    page = render(json.loads(path.read_text()) if path.exists() else None)
    out = Path(args.out)
    if args.check:
        same = out.exists() and out.read_text() == page
        print('no changes' if same else 'changed'); return 0 if same else 1
    out.write_text(page); print('wrote', out); return 0

if __name__ == '__main__': sys.exit(main())
