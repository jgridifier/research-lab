"""Real-data checks for the Phase B code that use BURN-IN data only (rows <= 2013Q4, origins <= 2013Q3).
Skipped when the gitignored processed panel is absent. No OOS forecast or score is computed."""
import numpy as np
import pandas as pd
import pytest
from conftest import real_panel_v1_1
from statement_forecast.combo import truncate
from trading_ot import panel as P, secondary_v1_1 as SEC, sensitivity_v1_1 as SENS, walkforward_v1_1 as V

pytestmark = pytest.mark.realdata
END = V.FIRST_FREEZE


@pytest.fixture(scope='module')
def burn():
    return truncate(P.prepare_v1_1(real_panel_v1_1()), END)      # v1.1 rules, then burn-in rows only


def test_t1_rule_a_b_match_data_check(burn):
    """DATA_CHECK_backfill2 (1): T1 rule (a)/(b) in $bn for the burn-in quarters where they differ."""
    raw = real_panel_v1_1()
    raw = raw[raw.quarter.le(END)]
    a = SEC.t1_series(P.prepare_v1_1(raw)).set_index('quarter').trading_revenue_q / 1e6
    b = SEC.t1_series(P.prepare_v1_1(raw, 'b')).set_index('quarter').trading_revenue_q / 1e6
    want = {'2009Q2': (17.990, 18.041), '2010Q4': (9.029, 9.272), '2012Q4': (13.957, 14.059),
            '2013Q2': (14.167, 15.551)}
    for q, (wa, wb) in want.items():
        assert a[q] == pytest.approx(wa, abs=5e-4) and b[q] == pytest.approx(wb, abs=5e-4), q
    assert np.isnan(a['2008Q4'])


def test_h1d_epoch0_burnin(burn):
    t1 = SEC.t1_series(burn)
    cases, _ = SEC.t1_cases(t1, V.EPOCH0_TARGETS)
    assert cases.origin.max() <= END - 1
    assert all(cases[f'def_{m}'].all() for m in SEC.T1_MEMBERS) and not cases.b4_fallback.any()
    assert cases.scale.notna().all()
    _, info = SEC.h1d(burn, epochs=[END], targets=[])
    sel = info['selection'][0]
    assert sel == dict(epoch='2013Q4', b_star='B4', trimmed=['B0', 'B4'], s=1.0, inherited=False)


@pytest.mark.parametrize('h,trimmed,n_matched', [(2, ['B0', 'B4'], 72), (3, ['B0', 'B3', 'B4', 'B5'], 72),
                                                 (4, ['B0', 'B1', 'B2', 'B3'], 60)])
def test_h1e_epoch0_burnin(burn, h, trimmed, n_matched):
    import trading_ot.macro as M
    mac = M.quarter_features_v1_1(pd.period_range('2009Q1', '2013Q4', freq='Q'))
    s0 = V.rolling_set_by_epoch(burn, [END])[END]
    st, cases = V.t2_epoch(burn, mac, END, s0, h=h)
    assert cases.origin.max() <= END - h
    assert st['excluded_low_coverage'] == ['B6'] and st['b_star'] == 'B0' and st['s'] == 1.0
    assert st['trimmed'] == trimmed and st['n_matched'] == n_matched and not st['inherited']


def test_s14_frozen_scales_cover_first_freeze_set(burn):
    s0 = V.rolling_set_by_epoch(burn, [END])[END]
    sF, floor = SENS.frozen_scales(burn, s0, set0=s0)
    assert len(sF) == 12 and all(np.isfinite(v) and v >= floor for v in sF.values())


def test_s8_memo_items_start_2011(burn):
    big = burn[burn.total_assets.ge(SENS.S8_TA_MIN)]
    by_year = big.groupby(big.quarter.dt.year).trd_cva_counterparty_q.count()
    assert by_year.get(2009, 0) == 0 and by_year.get(2010, 0) == 0 and by_year[2011] > 0
