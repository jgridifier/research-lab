"""prereg §6.3 test 1: YTD -> quarterly de-cumulation of A220 (y9c.panel.decumulate reused unchanged)."""
import numpy as np
import pandas as pd
import pytest
import y9c.panel
from trading_ot import panel as tp
from conftest import to_panel

ROWS = [(1, '2020-03-31', 10.0), (1, '2020-06-30', 25.0), (1, '2020-09-30', 20.0), (1, '2020-12-31', 40.0),
        (1, '2021-03-31', 7.0), (1, '2021-09-30', 30.0), (1, '2021-12-31', 33.0),
        (2, '2020-06-30', 5.0), (2, '2020-09-30', 9.0), (2, '2021-03-31', -4.0)]


def frame():
    return pd.DataFrame([dict(rssd_id=i, report_date=pd.Timestamp(d), trading_revenue_ytd=v) for i, d, v in ROWS])


def test_reused_unchanged():
    assert tp.decumulate is y9c.panel.decumulate


def test_q1_reset_and_negative_kept():
    out = to_panel(frame()).set_index(['rssd_id', 'quarter']).trading_revenue_q
    assert out[(1, pd.Period('2020Q1'))] == 10.0
    assert out[(1, pd.Period('2021Q1'))] == 7.0           # Q1 as reported, not 7 - 40
    assert out[(2, pd.Period('2021Q1'))] == -4.0          # negative values kept
    assert out[(1, pd.Period('2020Q3'))] == -5.0          # negative de-cumulation kept, no log/clip


def test_telescoping():
    out = to_panel(frame())
    y2020 = out[(out.rssd_id == 1) & (out.quarter.dt.year == 2020)]
    assert y2020.trading_revenue_q.sum() == y2020.trading_revenue_ytd.iloc[-1]


def test_missing_predecessor_is_nan_no_bridging():
    out = to_panel(frame()).set_index(['rssd_id', 'quarter']).trading_revenue_q
    assert np.isnan(out[(1, pd.Period('2021Q3'))])        # 2021Q2 missing: no bridge to Q1
    assert out[(1, pd.Period('2021Q4'))] == 3.0
    assert np.isnan(out[(2, pd.Period('2020Q2'))])        # first filing in Q2: no predecessor
    assert out[(2, pd.Period('2020Q3'))] == 4.0


def test_no_subtraction_across_years():
    f = frame()
    f.loc[(f.rssd_id == 1) & (f.report_date == '2020-12-31'), 'trading_revenue_ytd'] = 1e9
    out = to_panel(f).set_index(['rssd_id', 'quarter']).trading_revenue_q
    assert out[(1, pd.Period('2021Q1'))] == 7.0


@pytest.mark.realdata
def test_real_panel_telescopes():
    from trading_ot.paths import DATA
    path = DATA / 'processed/trading_panel.parquet'
    if not path.exists():
        pytest.skip('real panel not built')
    p = pd.read_parquet(path)
    p['year'] = p.quarter.dt.year
    g = p.dropna(subset=['trading_revenue_q']).groupby(['rssd_id', 'year'])
    full = g.filter(lambda x: len(x) == 4)
    sums = full.groupby(['rssd_id', 'year']).trading_revenue_q.sum()
    q4 = full[full.quarter.dt.quarter == 4].set_index(['rssd_id', 'year']).trading_revenue_ytd
    assert len(sums) > 1000 and float((sums - q4.reindex(sums.index)).abs().max()) == 0.0
