"""Population rules. Every function uses only the (possibly truncated) panel it is given."""
import numpy as np
import pandas as pd

BURN_START, BURN_END = pd.Period('2018Q1', freq='Q'), pd.Period('2021Q4', freq='Q')


def exante_bank_set(panel, burn_end=BURN_END, thr=1e4, burn_start=BURN_START):
    """Banks with |A220_q| >= thr ($k) in every burn-in quarter; uses rows <= burn_end only."""
    burn_end, burn_start = pd.Period(burn_end, freq='Q'), pd.Period(burn_start, freq='Q')
    need = len(pd.period_range(burn_start, burn_end, freq='Q'))
    b = panel.loc[panel.quarter.between(burn_start, burn_end), ['rssd_id', 'quarter', 'trading_revenue_q']]
    ok = b.trading_revenue_q.abs().ge(thr)
    counts = b.assign(ok=ok).groupby('rssd_id').agg(n=('quarter', 'nunique'), n_ok=('ok', 'sum'))
    return sorted(counts.index[(counts.n == need) & (counts.n_ok == need)].tolist())


def balanced_set(panel, thr=1e4, first='2018Q1', last=None):
    """Sensitivity only (uses the full sample): |A220_q| >= thr in every quarter first..last."""
    last = panel.quarter.max() if last is None else pd.Period(last, freq='Q')
    return exante_bank_set(panel, burn_end=last, thr=thr, burn_start=first)


def lagged(panel, column, lag=1):
    """Calendar-key lag (never a row shift across gaps)."""
    s = panel.set_index(['rssd_id', 'quarter'])[column]
    keys = pd.MultiIndex.from_arrays([panel.rssd_id, panel.quarter - lag])
    return s.reindex(keys).to_numpy()


def add_ratio(panel, denom='trading_assets', name='r'):
    """r_(i,t) = A220_q(i,t) / denom(i,t-1) in bp; NaN when the lagged denominator is missing or <= 0."""
    out = panel.copy()
    lag = lagged(out, denom)
    out[f'{denom}_lag'] = lag
    out[name] = 1e4 * out.trading_revenue_q / np.where(lag > 0, lag, np.nan)
    return out


def cross_section(panel, s, lag_ta_min=1e5):
    """C_s: banks with TA(i,s-1) >= lag_ta_min ($k) and non-null A220_q(i,s). Returns frame with r."""
    s = pd.Period(s, freq='Q')
    if 'trading_assets_lag' not in panel or 'r' not in panel:
        panel = add_ratio(panel)
    rows = panel[panel.quarter.eq(s) & panel.trading_assets_lag.ge(lag_ta_min) & panel.trading_revenue_q.notna()]
    return rows


# ── v1.1: annually refreshed ex-ante bank set (addendum §2.5) ──────────────
SET_ORIGINS_V1_1 = [pd.Period(f'{y}Q4', freq='Q') for y in range(2013, 2026)]
SET_WINDOW = 16


def exante_bank_set_rolling(panel, origin_q4, window=SET_WINDOW, thr=1e4):
    """S_o: banks with non-null |A220_q| >= thr in all `window` quarters o-window+1..o; rows <= o only.

    NaN from the YTD-reset guard, rule (a) or the pre-sample mask counts as missing.
    """
    o = pd.Period(origin_q4, freq='Q')
    if o.quarter != 4:
        raise ValueError(f'bank-set origins are Q4 quarters, got {o}')
    return exante_bank_set(panel[panel.quarter.le(o)], burn_end=o, thr=thr, burn_start=o - (window - 1))


def set_origin(origin):
    """Last Q4 <= origin: the set in force for forecasts made at `origin` (any horizon)."""
    o = pd.Period(origin, freq='Q')
    return o - (o.quarter % 4)


def set_for_target(t, h=1):
    """Set origin for target t at horizon h: S_o with o = last Q4 <= t - h."""
    return set_origin(pd.Period(t, freq='Q') - h)


def rolling_sets(panel, origins=SET_ORIGINS_V1_1, window=SET_WINDOW, thr=1e4):
    """{origin: S_o}; each S_o is computed from rows <= o only."""
    return {o: exante_bank_set_rolling(panel, o, window, thr) for o in origins}
