"""Deterministic static burn-in placeholder; no scripts or live forecasts."""
import argparse
from html import escape
from pathlib import Path
import numpy as np
import pandas as pd
from .paths import ROOT, SCORING_WALL, SOURCE_URL
from .preflight import preflight, sha256
from .parse import load_vol, EXPECTED_VOL_SERIES
from .weekly import build_weekly
from .ingest import latest_vintage

BANNER = 'PLACEHOLDER — burn-in data only (weeks ending on or before 2008-12-26). Not live data. No forecast has been scored.'

def build_app(out=ROOT/'docs/tracks/fed-cp-ot/app/index.html', zip_path=None):
    if zip_path is None:
        try: zip_path = latest_vintage()
        except FileNotFoundError: pass
    if zip_path is not None:
        provenance = preflight('burnin')
        vol,_ = load_vol(provenance,zip_path)
        label = 'Pinned/cached data vintage SHA256: ' + sha256(zip_path)
    else:
        rows = [(s,*attrs,pd.Timestamp(d),True,float((i%6+1)*100))
                for i,(s,attrs) in enumerate(EXPECTED_VOL_SERIES.items())
                for d in ('2008-12-22','2008-12-23','2008-12-24')]
        vol = pd.DataFrame(rows,columns=['series','cp_type','mat','vt','date','valid','value'])
        label = 'SYNTHETIC PLACEHOLDER DATA — illustrative shares, not Fed observations.'
    weekly = build_weekly(vol)
    sections = []
    for typ,g in weekly[weekly.usable & (weekly.week == pd.Timestamp(SCORING_WALL))].groupby('cp_type',sort=False):
        row = g.sort_values('week').iloc[-1]
        bars = ''.join(f'<li><span>{escape(bucket)} days: {share:.2%}</span><svg viewBox="0 0 100 4" role="img" aria-label="{share:.2%}"><rect width="{share*100:.6f}" height="4" fill="#0b2545"/></svg></li>'
                       for bucket,share in zip(('1–4','5–9','10–20','21–40','41–80','81–270'),row['mix']))
        table = ''.join(f'<tr><th scope="row">{bucket}</th><td>{share:.2%}</td></tr>' for bucket,share in zip(('1–4','5–9','10–20','21–40','41–80','81–270'),row['mix']))
        sections.append(f'<section><h2>{escape(typ)} dollar mix</h2><p>Week ending {row.week:%Y-%m-%d}</p><p>Valid days: {row.valid_days}; issues: {row.N.sum():,.0f}. Usable week: yes.</p><ul>{bars}</ul><table><caption>Six maturity bucket shares</caption><thead><tr><th scope="col">Days</th><th scope="col">Dollar share</th></tr></thead><tbody>{table}</tbody></table></section>')
    learning = '<p><a href="../learning.html">Pinned learning page</a> · <a href="../index.html">Preregistration</a></p>'
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Fed CP maturity mix — placeholder</title>
<style>body{{margin:0;background:white;color:black;font:17px/1.6 system-ui,sans-serif}}main{{max-width:850px;margin:auto;padding:12px}}h1,h2,a{{color:#0b2545}}.banner{{background:#0b2545;color:white;padding:20px;font-weight:700}}section{{margin:24px 0;padding:16px;border:1px solid #0b2545}}ul{{list-style:none;padding:0}}li{{margin:12px 0}}svg{{display:block;width:100%;height:14px}}.vintage{{overflow-wrap:anywhere}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;padding:6px;border-bottom:1px solid #0b2545}}caption{{text-align:left}}@media (min-width:700px){{main{{padding:32px}}section{{padding:24px}}}}</style></head>
<body><main><h1>Commercial paper maturity mix</h1><p class="banner">{escape(BANNER)}</p><p class="vintage">{escape(label)}</p>
{''.join(sections)}<section><h2>This week (provisional)</h2><p>The partial-week view will show observations available so far, flagged provisional. Missing days are never filled. Forecasts use completed weeks only.</p></section>
<section><h2>Forecast</h2><p>OOS not authorized. The headline will be the SEL forecast, with persistence as the fallback if Family B fails after the single approved OOS run.</p></section>
<section><h2>Data source and cadence</h2><p><a href="{escape(SOURCE_URL,quote=True)}">Federal Reserve CP XML</a>. Daily, typically a one-day lag, about 1:00 pm ET; timing is not guaranteed. Planned pull: 13:30 ET with retries until 18:00 ET. A completed Friday week is normally available Monday at about 13:00 ET. Missing days are not filled.</p><p>Volumes cover rate-eligible issues. Rating criteria changed during the burn-in. MKT is a separate comparator, never a sum of the four types.</p></section>
<p><a href="../../../index.html">Back to research lab</a></p>{learning}</main></body></html>'''
    out = Path(out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(html)
    return out

def main():
    p=argparse.ArgumentParser(); p.add_argument('--zip'); args=p.parse_args(); print(build_app(zip_path=args.zip))
if __name__ == '__main__': main()
