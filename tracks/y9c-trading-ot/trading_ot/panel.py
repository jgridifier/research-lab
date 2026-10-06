"""Trading-revenue panel: parse NIC ZIPs, de-cumulate YTD flows, availability rule.

Reuses y9c.panel.read_quarter (item list extended) and y9c.panel.decumulate
unchanged. A quarter is usable only once it is *available*: Y-9C due date
(40 days after Mar/Jun/Sep quarter ends, 45 after Dec 31, rolled forward to the
next business day) plus 7 calendar days (prereg §1.5).
"""
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pandas.tseries.holiday import USFederalHolidayCalendar
from y9c.panel import decumulate, read_quarter

from .paths import PACKAGE

FIRST_QUARTER = pd.Period('2018Q1', freq='Q')
AVAILABILITY_LAG_DAYS = 7
_HOLIDAYS = None


def load_items():
    return yaml.safe_load((PACKAGE / 'items.yaml').read_text())


def _holidays():
    global _HOLIDAYS
    if _HOLIDAYS is None:
        _HOLIDAYS = set(USFederalHolidayCalendar().holidays('2015-01-01', '2035-12-31').date)
    return _HOLIDAYS


def due_date(quarter):
    """FR Y-9C filing deadline for a report quarter, rolled to the next business day."""
    quarter = pd.Period(quarter, freq='Q')
    end = quarter.end_time.date()
    day = end + timedelta(days=45 if quarter.quarter == 4 else 40)
    while day.weekday() >= 5 or day in _holidays():
        day += timedelta(days=1)
    return day


def availability_date(quarter):
    """D_t = due date + 7 calendar days."""
    return due_date(quarter) + timedelta(days=AVAILABILITY_LAG_DAYS)


def complete_quarters(as_of, first=FIRST_QUARTER):
    """Report quarters q >= first with D_q <= as_of (inclusive)."""
    as_of = pd.Timestamp(as_of).date()
    out, q = [], pd.Period(first, freq='Q')
    while availability_date(q) <= as_of:
        out.append(q)
        q += 1
    return out


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_trading_panel(raw_dir, as_of, out_dir=None, first=FIRST_QUARTER):
    """Parse every available quarter's ZIP and de-cumulate the YTD flows.

    Quarters whose availability date is after as_of are never read, so a
    partial (not yet due + 7d) quarter cannot enter. Returns the panel with
    *_ytd and *_q columns for flows and level columns for stocks.
    """
    spec = load_items()
    items = spec['items']
    quarters = complete_quarters(as_of, first)
    if not quarters:
        raise ValueError(f'No complete quarters as of {as_of}')
    raw_dirs = [Path(d) for d in (raw_dir if isinstance(raw_dir, (list, tuple)) else [raw_dir])]
    paths = []
    for q in quarters:
        name = f'BHCF{q.end_time:%Y%m%d}.zip'
        found = [d / name for d in raw_dirs if (d / name).exists()]
        if not found:
            raise FileNotFoundError(f'{name} missing for available quarter {q} in {raw_dirs}; manual NIC drop-in needed')
        paths.append(found[0])
    manifests = {}
    for d in raw_dirs:
        if (d / 'manifest.json').exists():
            manifests.update(json.loads((d / 'manifest.json').read_text()))
    zip_sha = {p.name: _sha256(p) for p in paths}
    bad = [k for k, h in zip_sha.items() if k in manifests and manifests[k].get('sha256') != h]
    if bad:
        raise ValueError(f'ZIP sha256 does not match manifest.json for {bad}; refusing to build the panel')
    codes = list(items) + list(spec.get('parse_guard', []))
    frames = [read_quarter(p, codes) for p in paths]
    raw = pd.concat(frames, ignore_index=True)
    if raw.duplicated(['rssd_id', 'report_date']).any():
        raise ValueError('Duplicate RSSD/report-date keys')
    raw = raw.sort_values(['rssd_id', 'report_date']).reset_index(drop=True)
    panel = raw[['rssd_id', 'report_date', 'name']].copy()
    panel['quarter'] = panel.report_date.dt.to_period('Q')
    for code, meta in items.items():
        if meta['kind'] == 'flow_ytd':
            quarterly, missing = decumulate(raw, code)
            panel[meta['name'] + '_ytd'] = raw[code]
            panel[meta['name'] + '_q'] = quarterly
            panel[meta['name'] + '_missing_prior'] = missing
        else:
            panel[meta['name']] = raw[code]
    vintage = dict(as_of=str(pd.Timestamp(as_of).date()), first_quarter=str(quarters[0]),
                   last_complete_quarter=str(quarters[-1]), n_quarters=len(quarters),
                   availability_rule='Y-9C due date (40d after Mar/Jun/Sep, 45d after Dec; next business day) + 7 calendar days',
                   availability_dates={str(q): str(availability_date(q)) for q in quarters},
                   zips=zip_sha, units='thousands USD',
                   n_rows=len(panel), n_rssd=int(panel.rssd_id.nunique()))
    if manifests:
        vintage['downloaded_at_utc'] = {p.name: manifests.get(p.name, {}).get('downloaded_at_utc') for p in paths}
        vintage['manifest_sha256_match'] = {p.name: manifests.get(p.name, {}).get('sha256') == vintage['zips'][p.name]
                                            for p in paths}
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        panel.to_parquet(out_dir / 'trading_panel.parquet', index=False)
        (out_dir / 'vintage.json').write_text(json.dumps(vintage, indent=2) + '\n')
    return panel, vintage


def memo9_check(panel, tol=1.0):
    """Share of rows where A220 YTD equals the Memo 9.a-e sum within tol ($k)."""
    cols = ['trd_interest_rate_ytd', 'trd_fx_ytd', 'trd_equity_ytd', 'trd_commodity_ytd', 'trd_credit_ytd']
    both = panel.dropna(subset=['trading_revenue_ytd', *cols])
    gap = (both[cols].sum(axis=1) - both.trading_revenue_ytd).abs()
    return dict(n_rows=len(both), n_within_tol=int(gap.le(tol).sum()),
                share_within_tol=float(gap.le(tol).mean()) if len(both) else float('nan'),
                max_gap_thousands=float(gap.max()) if len(both) else float('nan'))


# Known structural events (prereg §5.6 S5; DATA_CHECK §7; Developer list).
# Quarters are the report quarter at which the series is affected.
EVENTS = [
    dict(rssd_id=1074156, quarter='2019Q4', label='Truist (BB&T + SunTrust) merger, total assets +100%'),
    dict(rssd_id=1131787, quarter='2019Q3', label='SunTrust last filing (exit into Truist)'),
    dict(rssd_id=1094640, quarter='2020Q3', label='First Horizon / IBKC merger, +71%'),
    dict(rssd_id=1069778, quarter='2021Q2', label='PNC acquires BBVA USA, +16.9%'),
    dict(rssd_id=1378434, quarter='2022Q4', label='MUFG Americas Union Bank sale, -68%'),
    dict(rssd_id=1378434, quarter='2023Q3', label='MUFG Americas last filing'),
    dict(rssd_id=1119794, quarter='2022Q4', label='U.S. Bancorp acquires Union Bank, +12.3%'),
    dict(rssd_id=1574834, quarter='2022Q4', label='Credit Suisse USA -27%'),
    dict(rssd_id=1574834, quarter='2023Q2', label='Credit Suisse USA -24%'),
    dict(rssd_id=1574834, quarter='2024Q1', label='Credit Suisse USA last filing'),
    dict(rssd_id=1245415, quarter='2023Q1', label='BMO Financial (Bank of the West), +44%'),
    dict(rssd_id=1575569, quarter='2023Q1', label='BNP Paribas USA -50% (Bank of the West sale)'),
    dict(rssd_id=1575569, quarter='2023Q2', label='BNP Paribas USA -27%'),
    dict(rssd_id=2277860, quarter='2025Q2', label='Capital One +34%'),
    dict(rssd_id=1199844, quarter='2025Q4', label='Comerica last filing'),
    dict(rssd_id=1070345, quarter='2026Q1', label='Fifth Third +39% (Comerica link inferred from filings, UNVERIFIED)'),
    dict(rssd_id=3226762, quarter='2018Q1', label='RBC USA Holdco last filing (RSSD change)'),
    dict(rssd_id=5280254, quarter='2018Q2', label='RBC US Group Holdings first filing (splice candidate)'),
    dict(rssd_id=1026632, quarter='2020Q1', label='Schwab +26%'),
    dict(rssd_id=1026632, quarter='2020Q4', label='Schwab (TD Ameritrade) +31%'),
    # v1.1 additions (addendum §2.5, S5)
    dict(rssd_id=1120754, quarter='2008Q4', label='Wells Fargo / Wachovia, +110%'),
    dict(rssd_id=1069778, quarter='2008Q4', label='PNC / National City, +100%'),
    dict(rssd_id=1073757, quarter='2009Q1', label='Bank of America / Merrill Lynch, +27.5%'),
    dict(rssd_id=1039502, quarter='2008Q3', label='JPMorgan / WaMu, +26.8%'),
    dict(rssd_id=1245415, quarter='2011Q3', label='BMO (Harris / M&I), +57%'),
    dict(rssd_id=1068025, quarter='2016Q3', label='KeyCorp / First Niagara, +34%'),
    dict(rssd_id=1378434, quarter='2016Q3', label='MUFG Americas IHC, +29%'),
    dict(rssd_id=1094640, quarter='2017Q4', label='First Horizon / Capital Bank, +40%'),
    dict(rssd_id=2277860, quarter='2010Q1', label='Capital One +19%'),
]
IHC_WAVE = '2016Q3'
TD_RETIER = '2015Q3'


def merger_flags(panel, thr=0.15, events=None):
    """Flag bank-quarters with |dTotal assets|/TA_(t-1) > thr (calendar-adjacent only) or a listed event.

    Returns a frame (rssd_id, quarter, asset_change, flag_threshold, flag_event, event_label, flag).
    """
    events = EVENTS if events is None else events
    data = panel[['rssd_id', 'quarter', 'total_assets']].copy().set_index(['rssd_id', 'quarter']).sort_index()
    ids, qs = data.index.get_level_values(0), data.index.get_level_values(1)
    prev = data.total_assets.reindex(pd.MultiIndex.from_arrays([ids, qs - 1])).to_numpy()
    change = data.total_assets.to_numpy() / np.where(prev > 0, prev, np.nan) - 1
    out = pd.DataFrame({'rssd_id': ids, 'quarter': qs, 'asset_change': change})
    out['flag_threshold'] = np.abs(out.asset_change) > thr
    ev = {(e['rssd_id'], pd.Period(e['quarter'], freq='Q')): e['label'] for e in events}
    out['event_label'] = [ev.get((i, q), '') for i, q in zip(out.rssd_id, out.quarter)]
    out['flag_event'] = out.event_label.ne('')
    out['flag'] = out.flag_threshold | out.flag_event
    return out


# ── v1.1 data rules (prereg addendum §2.5) ──────────────────────────────────
PRESAMPLE_END = pd.Period('2008Q4', freq='Q')
TIERED_DUPLICATES = [dict(rssd_id=5005998, name='BancWest Corporation', quarters=['2016Q3', '2016Q4']),
                     dict(rssd_id=1032473, name='Deutsche Bank Trust Corporation', quarters=['2016Q3', '2016Q4'])]


def flow_columns(panel):
    return [c for c in panel.columns if c.endswith('_q') and c[:-2] + '_ytd' in panel.columns]


def ytd_reset_rows(panel, guard='total_interest_income_ytd'):
    """Bank-quarters (Q2-Q4) where the guard YTD is lower than the immediately prior quarter of the same year."""
    s = panel.set_index(['rssd_id', 'quarter'])[guard]
    prev = s.reindex(pd.MultiIndex.from_arrays([panel.rssd_id, panel.quarter - 1])).to_numpy()
    q = panel.quarter.dt.quarter.to_numpy()
    flag = (q > 1) & np.isfinite(prev) & (panel[guard].to_numpy(float) < prev)
    return pd.Series(flag, index=panel.index)


def ytd_reset_guard(panel, guard='total_interest_income_ytd'):
    """Set every de-cumulated flow to NaN in flagged bank-quarters; neighbouring quarters are untouched."""
    out = panel.copy()
    flag = ytd_reset_rows(out, guard)
    for c in flow_columns(out):
        out.loc[flag, c] = np.nan
    out['ytd_reset_flag'] = flag
    return out


def tiered_duplicate_mask(panel, entries=None):
    """True for rows to exclude (tiered subsidiaries filing alongside their parents)."""
    entries = TIERED_DUPLICATES if entries is None else entries
    mask = pd.Series(False, index=panel.index)
    for e in entries:
        qs = pd.PeriodIndex(e['quarters'], freq='Q')
        mask |= panel.rssd_id.eq(e['rssd_id']) & panel.quarter.isin(qs)
    return mask


def entrant_rule_b(panel, column='trading_revenue'):
    """Rule (b) flow: like rule (a) but a first filing with no predecessor counts its YTD as the quarter's flow.

    Applies only to rows with no filing in the prior quarter (entry or resumption after a gap); a
    present-but-null predecessor still gives NaN. Used for sensitivity S11 (T1) only.
    """
    keys = set(zip(panel.rssd_id, panel.quarter))
    has_prev = np.array([(i, q - 1) in keys for i, q in zip(panel.rssd_id, panel.quarter)])
    q1 = panel.quarter.dt.quarter.eq(1).to_numpy()
    out = panel[f'{column}_q'].copy()
    entry = ~q1 & ~has_prev & panel[f'{column}_ytd'].notna().to_numpy()
    out[entry] = panel.loc[entry, f'{column}_ytd']
    return out


def presample_mask(panel, presample_end=PRESAMPLE_END, keep=('trading_assets',)):
    """NaN every value of rows <= presample_end except `keep` columns in the last pre-sample quarter.

    After this, 2008 cannot enter any estimator, scale, set or selection; TA(2008Q4) survives only as
    the lagged denominator of the 2009Q1 ratio.
    """
    out = panel.copy()
    pre = out.quarter.le(presample_end)
    ids = {'rssd_id', 'quarter', 'report_date', 'name', 'entity_type', 'ytd_reset_flag'}
    vals = [c for c in out.columns if c not in ids and pd.api.types.is_numeric_dtype(out[c])
            and not pd.api.types.is_bool_dtype(out[c])]
    for c in vals:
        m = pre if c not in keep else pre & out.quarter.ne(presample_end)
        out.loc[m, c] = np.nan
    return out


def prepare_v1_1(panel, entrant_rule='a'):
    """Apply the v1.1 rules: YTD-reset guard, tiered-duplicate exclusion, entrant rule (a) primary.

    2008 rows are kept (TA 2008Q4 is the 2009Q1 denominator); estimators mask them via PRESAMPLE_END.
    """
    out = ytd_reset_guard(panel[panel.total_assets.notna()].reset_index(drop=True))
    out = out[~tiered_duplicate_mask(out)].copy()
    if entrant_rule == 'b':
        out['trading_revenue_q'] = entrant_rule_b(out).where(~out.ytd_reset_flag)
    elif entrant_rule != 'a':
        raise ValueError("entrant_rule must be 'a' or 'b'")
    return presample_mask(out).reset_index(drop=True)


def prepare_v1_0(panel):
    """R1: v1.0 design on 2018+ data with the YTD-reset guard (addendum §2.5 applies it to R1)."""
    out = ytd_reset_guard(panel[panel.quarter.ge(FIRST_QUARTER) & panel.total_assets.notna()].reset_index(drop=True))
    return out.reset_index(drop=True)
