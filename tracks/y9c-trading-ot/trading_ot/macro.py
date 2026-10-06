"""FRED daily covariates aggregated to quarters (prereg §3 B5, §1.5).

Cached CSVs live under data/fred/ (gitignored; sha256 and fetch time recorded
in fred_manifest.json). Primary rule 'qend': quarter-t aggregates use daily data
inside quarter t (through its last day). Variant 'Dt' (S9) uses data from the
start of quarter t through the availability date D_t.
"""
from datetime import datetime, timezone
import hashlib
import io
import json

import numpy as np
import pandas as pd
import requests

from .panel import availability_date
from .paths import DATA

FRED = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={start}&coed={end}'
SERIES = ['VIXCLS', 'DGS10', 'SP500']
OPTIONAL = 'BAMLC0A0CM'   # included only if FRED history covers 2018+ (decided before the freeze)
CACHE = DATA / 'fred'


def fetch_fred(series, start='2017-01-01', end=None, cache=CACHE, refresh=False):
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f'{series}.csv'
    manifest_path = cache / 'fred_manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if refresh or not path.exists():
        end = end or datetime.now(timezone.utc).date().isoformat()
        r = requests.get(FRED.format(sid=series, start=start, end=end), timeout=60)
        r.raise_for_status()
        if 'html' in r.headers.get('Content-Type', '').lower():
            raise RuntimeError(f'FRED returned HTML for {series}')
        path.write_bytes(r.content)
        manifest[series] = dict(url=FRED.format(sid=series, start=start, end=end),
                                fetched_at_utc=datetime.now(timezone.utc).isoformat(),
                                sha256=hashlib.sha256(r.content).hexdigest())
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    frame = pd.read_csv(path, na_values=['.', ''])
    frame.columns = ['date', series]
    frame['date'] = pd.to_datetime(frame.date)
    return frame.dropna().set_index('date')[series]


def history_covers(series_values, start='2018-01-01'):
    return len(series_values) and series_values.index.min() <= pd.Timestamp(start) + pd.Timedelta(days=7)


def quarter_features(quarters, asof_rule='qend', series=None):
    """DataFrame indexed by quarter: vix (mean), rates_rv (sd of daily d10y), eq_rv (sd of daily log SP500 returns)."""
    series = series or {s: fetch_fred(s) for s in SERIES}
    vix, dgs, spx = series['VIXCLS'], series['DGS10'], series['SP500']
    d10 = dgs.diff().dropna()
    ret = np.log(spx).diff().dropna()
    rows = {}
    for q in quarters:
        q = pd.Period(q, freq='Q')
        lo = q.start_time
        hi = q.end_time if asof_rule == 'qend' else pd.Timestamp(availability_date(q)) + pd.Timedelta(hours=23)
        win = lambda s: s[(s.index >= lo) & (s.index <= hi)]
        rows[q] = dict(vix=float(win(vix).mean()), rates_rv=float(win(d10).std(ddof=1)),
                       eq_rv=float(win(ret).std(ddof=1)))
    return pd.DataFrame.from_dict(rows, orient='index')
