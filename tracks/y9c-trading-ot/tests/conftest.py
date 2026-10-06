"""Synthetic fixtures only; no test reads the processed real-data cache unless marked `realdata` (skipped if absent)."""
import numpy as np
import pandas as pd
import pytest
from y9c.panel import decumulate

QUARTERS = pd.period_range('2018Q1', '2026Q2', freq='Q')


QUARTERS_V1_1 = pd.period_range('2008Q1', '2026Q2', freq='Q')


def synthetic_ytd(seed=20261006, n_banks=26, quarters=None, entries=None):
    """Bank x quarter frame with YTD trading revenue and stocks, in $k.

    quarters: defaults to 2018Q1-2026Q2 (v1.0); entries: {bank_index: first quarter} for late entrants (v1.1).
    Also writes a positive cumulative total_interest_income_ytd (for the v1.1 YTD-reset guard).
    """
    rng = np.random.default_rng(seed)
    QUARTERS_ = QUARTERS if quarters is None else quarters
    entries = entries or {}
    rows = []
    for b in range(1, n_banks + 1):
        ta = float(np.exp(rng.uniform(np.log(3e4), np.log(5e8))))
        assets = ta * rng.uniform(5, 40)
        r_mean = rng.normal(80, 30)
        r = r_mean
        ytd = 0.0
        prev_ta = ta
        nii = 0.0
        first = pd.Period(entries[b], freq='Q') if b in entries else None
        for j, q in enumerate(QUARTERS_):
            r = r_mean + 0.3 * (r - r_mean) + rng.standard_t(4) * 40 + (15 if q.quarter == 1 else 0)
            flow = r * prev_ta / 1e4
            ytd = flow if q.quarter == 1 else ytd + flow
            nii = assets * 0.01 if q.quarter == 1 else nii + assets * 0.01
            if first is None or q >= first:
                rows.append(dict(rssd_id=1000 + b, report_date=q.end_time.normalize(), name=f'Synthetic {b}',
                                 trading_revenue_ytd=ytd, trading_assets=ta, total_assets=assets,
                                 total_interest_income_ytd=nii))
            prev_ta = ta
            ta *= float(np.exp(rng.normal(0.01, 0.08)))
            assets *= float(np.exp(rng.normal(0.01, 0.03)))
    return pd.DataFrame(rows)


def to_panel(ytd):
    """Same columns the real pipeline produces (de-cumulation via y9c.panel.decumulate)."""
    frame = ytd.sort_values(['rssd_id', 'report_date']).reset_index(drop=True)
    for name in ['trading_revenue', 'total_interest_income']:
        if f'{name}_ytd' in frame:
            q, missing = decumulate(frame, f'{name}_ytd')
            frame[f'{name}_q'] = q
            frame[f'{name}_missing_prior'] = missing
    frame['quarter'] = frame.report_date.dt.to_period('Q')
    return frame


V1_1_ENTRIES = {3: '2009Q1', 4: '2009Q1', 5: '2009Q3', 6: '2016Q3'}


def synthetic_ytd_v1_1(seed=20261006, n_banks=22):
    return synthetic_ytd(seed, n_banks, quarters=QUARTERS_V1_1, entries=V1_1_ENTRIES)


def synthetic_macro_v1_1(seed=11):
    rng = np.random.default_rng(seed)
    Q = QUARTERS_V1_1
    return pd.DataFrame({'vix': rng.uniform(12, 35, len(Q)), 'rates_rv': rng.uniform(.02, .1, len(Q)),
                         'eq_rv': rng.uniform(.005, .03, len(Q)), 'baa': rng.uniform(1.5, 4, len(Q))}, index=Q)


def prepared_v1_1(ytd):
    from trading_ot.panel import prepare_v1_1
    return prepare_v1_1(to_panel(ytd))


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


@pytest.fixture(scope='session')
def ytd11():
    return synthetic_ytd_v1_1()


@pytest.fixture(scope='session')
def panel11(ytd11):
    return prepared_v1_1(ytd11)


@pytest.fixture(scope='session')
def macro11():
    return synthetic_macro_v1_1()


REAL_V1_1 = None


def real_panel_v1_1():
    """Locally built v1.1 panel (data/processed_v1_1, gitignored) prepared with the v1.1 rules; skip if absent."""
    global REAL_V1_1
    from trading_ot.paths import DATA
    path = DATA / 'processed_v1_1' / 'trading_panel.parquet'
    if not path.exists():
        pytest.skip('real v1.1 panel not built (make trading-ot-panel)')
    if REAL_V1_1 is None:
        REAL_V1_1 = pd.read_parquet(path)
    return REAL_V1_1
