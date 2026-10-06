"""Synthetic fixtures only; no test reads the processed real-data cache unless marked `realdata` (skipped if absent)."""
import numpy as np
import pandas as pd
import pytest
from y9c.panel import decumulate

QUARTERS = pd.period_range('2018Q1', '2026Q2', freq='Q')


def synthetic_ytd(seed=20261006, n_banks=26):
    """Bank x quarter frame with YTD trading revenue and stocks, in $k."""
    rng = np.random.default_rng(seed)
    rows = []
    for b in range(1, n_banks + 1):
        ta = float(np.exp(rng.uniform(np.log(3e4), np.log(5e8))))
        assets = ta * rng.uniform(5, 40)
        r_mean = rng.normal(80, 30)
        r = r_mean
        ytd = 0.0
        prev_ta = ta
        for j, q in enumerate(QUARTERS):
            r = r_mean + 0.3 * (r - r_mean) + rng.standard_t(4) * 40 + (15 if q.quarter == 1 else 0)
            flow = r * prev_ta / 1e4
            ytd = flow if q.quarter == 1 else ytd + flow
            rows.append(dict(rssd_id=1000 + b, report_date=q.end_time.normalize(), name=f'Synthetic {b}',
                             trading_revenue_ytd=ytd, trading_assets=ta, total_assets=assets))
            prev_ta = ta
            ta *= float(np.exp(rng.normal(0.01, 0.08)))
            assets *= float(np.exp(rng.normal(0.01, 0.03)))
    return pd.DataFrame(rows)


def to_panel(ytd):
    """Same columns the real pipeline produces (de-cumulation via y9c.panel.decumulate)."""
    frame = ytd.sort_values(['rssd_id', 'report_date']).reset_index(drop=True)
    q, missing = decumulate(frame, 'trading_revenue_ytd')
    frame['trading_revenue_q'] = q
    frame['trading_revenue_missing_prior'] = missing
    frame['quarter'] = frame.report_date.dt.to_period('Q')
    return frame


def synthetic_macro(seed=7):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({'vix': rng.uniform(12, 35, len(QUARTERS)), 'rates_rv': rng.uniform(.02, .1, len(QUARTERS)),
                         'eq_rv': rng.uniform(.005, .03, len(QUARTERS))}, index=QUARTERS)


@pytest.fixture(scope='session')
def ytd():
    return synthetic_ytd()


@pytest.fixture(scope='session')
def panel(ytd):
    return to_panel(ytd)


@pytest.fixture(scope='session')
def macro():
    return synthetic_macro()
