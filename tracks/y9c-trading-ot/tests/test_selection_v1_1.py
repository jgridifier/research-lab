"""Addendum §5.3 test 11 (selection causality) and the select.py rules (epochs, ties, coverage rule)."""
import numpy as np
import pandas as pd
import pytest
from trading_ot import select, sets, walkforward_v1_1 as V
from conftest import QUARTERS_V1_1, prepared_v1_1


def test_epochs():
    ep = select.selection_epochs()
    P = lambda s: pd.Period(s, freq='Q')
    assert ep[P('2013Q4')] == (P('2012Q3'), P('2013Q4'))
    assert ep[P('2014Q4')] == (P('2012Q3'), P('2014Q4'))
    assert ep[P('2015Q4')] == (P('2013Q1'), P('2015Q4'))
    assert ep[P('2025Q4')] == (P('2023Q1'), P('2025Q4'))
    assert len(ep) == 13
    assert select.epoch_for_target('2014Q1') == P('2013Q4') and select.epoch_for_target('2015Q1') == P('2014Q4')
    assert select.epoch_for_target('2026Q2') == P('2025Q4')


def _cases(scores, n=10, t='2013Q4'):
    df = pd.DataFrame({'target_quarter': pd.Period(t, freq='Q'), 'rssd_id': range(n), 'has_actual': True})
    for m, v in scores.items():
        df[f'S_{m}'] = v
    return df


def test_ties_and_trim():
    st = select.select_settings(_cases({'B0': 1.0, 'B1': 1.0, 'B2': 1.3, 'B3': 1.2}), ['B0', 'B1', 'B2', 'B3'], '2013Q4')
    assert st['b_star'] == 'B0' and st['trimmed'] == ['B0', 'B1', 'B3']


def test_coverage_rule_and_inheritance():
    c = _cases({'B0': 1.0, 'B1': 0.9, 'B2': 1.1})
    c.loc[:2, 'S_B1'] = np.nan                       # B1 covers 70% < 80%: excluded, logged
    st = select.select_settings(c, ['B0', 'B1', 'B2'], '2013Q4')
    assert st['excluded_low_coverage'] == ['B1'] and st['b_star'] == 'B0' and st['n_matched'] == 10
    c2 = c.copy()
    c2.loc[:2, 'S_B2'] = np.nan
    inh = select.select_settings(c2, ['B0', 'B1', 'B2'], '2014Q4', previous=st)
    assert inh['inherited'] and inh['b_star'] == 'B0'
    with pytest.raises(ValueError):
        select.select_settings(c2, ['B0', 'B1', 'B2'], '2014Q4')


def test_refuses_future_cases():
    with pytest.raises(ValueError, match='> origin'):
        select.select_settings(_cases({'B0': 1, 'B1': 2}, t='2014Q1'), ['B0', 'B1'], '2013Q4')


def _perturb_after(ytd, o, seed=1):
    rng = np.random.default_rng(seed)
    y = ytd.copy()
    later = y.report_date.dt.to_period('Q').gt(o)
    for c in ['trading_revenue_ytd', 'trading_assets', 'total_assets', 'total_interest_income_ytd']:
        y.loc[later, c] = y.loc[later, c] * rng.uniform(-3, 10, later.sum())
    return prepared_v1_1(y)


@pytest.mark.parametrize('epoch', ['2014Q4'])
def test_selection_causality(ytd11, panel11, macro11, epoch):
    """Settings for epoch o change only through cases with target <= o: perturbing outcomes after o is inert."""
    o = pd.Period(epoch, freq='Q')
    s_e = sets.exante_bank_set_rolling(panel11, o)
    a, ca = V.t2_epoch(panel11, macro11, o, s_e)
    p2 = _perturb_after(ytd11, o)
    assert sets.exante_bank_set_rolling(p2, o) == s_e
    m2 = macro11.copy()
    m2.loc[m2.index > o] *= 7
    b, cb = V.t2_epoch(p2, m2, o, s_e)
    assert a == b
    pd.testing.assert_frame_equal(ca, cb)
    # non-vacuous: perturbing an outcome inside the epoch window changes the scores
    y = ytd11.copy()
    hit = y.report_date.dt.to_period('Q').eq(o) & y.rssd_id.isin(s_e)
    y.loc[hit, 'trading_revenue_ytd'] *= 5
    c, cc = V.t2_epoch(prepared_v1_1(y), macro11, o, s_e)
    assert not np.allclose(ca.S_B0.to_numpy(), cc.S_B0.to_numpy(), equal_nan=True)


def test_case_scale_and_sets_ignore_later_rows(ytd11, panel11):
    from trading_ot.scoring import case_scale
    for o in ['2013Q4', '2016Q2', '2016Q3']:
        o = pd.Period(o, freq='Q')
        q4 = sets.set_origin(o)
        p2 = _perturb_after(ytd11, o, seed=o.ordinal)
        s_a = sets.exante_bank_set_rolling(panel11, q4)
        assert sets.exante_bank_set_rolling(p2, q4) == s_a
        np.testing.assert_array_equal(case_scale(panel11, s_a, o, s_a)[0], case_scale(p2, s_a, o, s_a)[0])
