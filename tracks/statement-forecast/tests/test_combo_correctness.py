"""Combination arithmetic, weight fit rules, parity with imported baselines, verdict logic."""
import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from y9c import forecast as y9c
from statement_forecast import combo


def cases_frame(naive, pooled, actual, quarters=None):
    n = len(actual)
    quarters = quarters if quarters is not None else pd.period_range('2015Q1', periods=n, freq='Q')
    return pd.DataFrame({'naive': np.asarray(naive, float), 'pooled_ar': np.asarray(pooled, float),
                         'actual': np.asarray(actual, float), 'target_quarter': quarters,
                         'ar_fallback': np.zeros(n, bool)})


def test_design_encodes_ticket_rules(combo_spec):
    grid = combo.weight_grid(combo_spec)
    assert len(grid) == 21 and grid[0] == 0 and grid[-1] == 1
    np.testing.assert_allclose(np.diff(grid), .05)
    assert combo_spec['method']['min_distinct_target_quarters'] == 8
    assert combo_spec['method']['fallback_weight'] == .5
    assert combo_spec['pass_bar']['alpha'] == .05 and combo_spec['pass_bar']['comparator'] == 'naive'
    assert combo_spec['test_window']['expected_cases_per_line'] == 893
    text = ' '.join(c['text'] for c in combo_spec['citations'])
    assert '10.3982/QE2589' in text and '10.1016/j.ijforecast.2022.11.005' in text


def test_w0_is_naive_and_w1_is_pooled_exactly(panel, combo_spec):
    rng = np.random.default_rng(1)
    n, p = rng.lognormal(10, 2, 1000), rng.lognormal(10, 2, 1000)
    np.testing.assert_array_equal(combo.combine(n, p, 0.0), n)
    np.testing.assert_array_equal(combo.combine(n, p, 1.0), p)
    line = combo_spec['lines'][1]
    origins = pd.period_range('2021Q4', '2022Q2', freq='Q')
    forecasts, _, _ = combo.combo_forecasts(panel, line, combo_spec, origins)
    np.testing.assert_array_equal(combo.combine(forecasts.naive, forecasts.pooled_ar, 0.0), forecasts.naive)
    np.testing.assert_array_equal(combo.combine(forecasts.naive, forecasts.pooled_ar, 1.0), forecasts.pooled_ar)


def test_informative_pooled_drives_w_to_one(combo_spec):
    rng = np.random.default_rng(2)
    actual = rng.lognormal(10, 1, 400)
    cases = cases_frame(actual + rng.normal(0, 5000, 400), actual + rng.normal(0, 50, 400), actual)
    w, info = combo.fit_weight(cases, combo_spec)
    assert w >= .95 and info['weight_rule'] == 'fit'


def test_noise_pooled_drives_w_to_zero(combo_spec):
    rng = np.random.default_rng(3)
    actual = rng.lognormal(10, 1, 400)
    naive = actual + rng.normal(0, 50, 400)
    cases = cases_frame(naive, naive + rng.normal(0, 5000, 400), actual)
    w, _ = combo.fit_weight(cases, combo_spec)
    assert w <= .05


def test_ties_go_to_smallest_w(combo_spec, monkeypatch):
    actual = np.arange(1., 21.)
    same = cases_frame(actual + 3, actual + 3, actual)  # P == N: every w ties
    assert combo.fit_weight(same, combo_spec)[0] == 0.0
    original = combo.combine
    def flat_between(naive, pooled, w):
        # Exact tie at w = 0.6 and 0.65 (both zero loss); all other weights are worse.
        return pooled if round(w, 2) in (0.6, 0.65) else original(naive, pooled, w) + 1
    monkeypatch.setattr(combo, 'combine', flat_between)
    w, _ = combo.fit_weight(cases_frame(actual + 7, actual, actual), combo_spec)
    assert w == 0.6


def test_fewer_than_8_target_quarters_gives_half(combo_spec):
    rng = np.random.default_rng(4)
    actual = rng.lognormal(10, 1, 70)
    quarters7 = np.repeat(pd.period_range('2019Q3', periods=7, freq='Q'), 10)
    cases = cases_frame(actual + 999, actual, actual, quarters7)  # P perfect: would fit w=1
    w, info = combo.fit_weight(cases, combo_spec)
    assert w == .5 and info['weight_rule'] == 'min_quarters_fallback' and info['n_pseudo_target_quarters'] == 7
    quarters8 = np.repeat(pd.period_range('2019Q3', periods=8, freq='Q'), 10)
    actual8 = np.concatenate([actual, actual[:10]])
    w8, info8 = combo.fit_weight(cases_frame(actual8 + 999, actual8, actual8, quarters8), combo_spec)
    assert w8 == 1.0 and info8['weight_rule'] == 'fit'
    empty = combo.fit_weight(cases.iloc[:0], combo_spec)
    assert empty[0] == .5


def test_min_quarter_rule_on_panel_path(panel, combo_spec):
    # Synthetic data start 2018Q1, so pooled AR is first defined at origin 2019Q2 (target 2019Q3).
    w7, info7 = combo.fit_weight(combo.pseudo_oos_cases(panel, pd.Period('2021Q1'), 'nii_q'), combo_spec)
    w8, info8 = combo.fit_weight(combo.pseudo_oos_cases(panel, pd.Period('2021Q2'), 'nii_q'), combo_spec)
    assert info7['first_pseudo_target'] == '2019Q3' and info7['n_pseudo_target_quarters'] == 7 and w7 == .5
    assert info8['n_pseudo_target_quarters'] == 8 and info8['weight_rule'] == 'fit'


def test_nonfinite_raises(combo_spec):
    actual = np.arange(1., 41.)
    cases = cases_frame(actual, actual, actual)
    cases.loc[3, 'pooled_ar'] = np.nan
    with pytest.raises(ValueError, match='Nonfinite'):
        combo.fit_weight(cases, combo_spec)


@pytest.mark.parametrize('line', ['nii', 'noninterest_income', 'noninterest_expense'])
def test_baseline_columns_are_the_imported_v1_cases(panel, combo_spec, line):
    spec_line = next(item for item in combo_spec['lines'] if item['key'] == line)
    origins = pd.period_range('2021Q4', '2026Q1', freq='Q')
    forecasts, _, weights = combo.combo_forecasts(panel, spec_line, combo_spec, origins)
    direct, _ = y9c.baseline_forecasts(y9c.design(panel, spec_line['column']), origins, spec_line['column'])
    assert_frame_equal(forecasts[direct.columns], direct, check_exact=True)
    grid = set(combo.weight_grid(combo_spec))
    assert weights.w.map(lambda v: v in grid).all() and len(weights) == len(origins)


@pytest.mark.parametrize('combo_mae,p,expected', [(9, .01, 'PASS'), (10, .01, 'FAIL'), (11, .01, 'FAIL'),
                                                  (9, .06, 'FAIL'), (9, np.nan, 'FAIL'), (9, .05, 'PASS'),
                                                  (10 - 1e-9, .05, 'PASS')])
def test_verdict(combo_spec, combo_mae, p, expected):
    overall = pd.DataFrame({'method': ['naive', 'combo'], 'mae': [10., combo_mae]})
    dm = pd.DataFrame([dict(scope='full', baseline='naive', loss='abs', p_value=p, t_stat=2.)])
    assert combo.verdict(overall, dm, combo_spec)['verdict'] == expected


def test_dm_sign_positive_favors_combo():
    cases = pd.DataFrame({'actual': [0.] * 6, 'naive': [1., 2., 3., 4., 5., 6.], 'combo': [0.] * 6,
                          'target_quarter': pd.period_range('2022Q1', periods=6, freq='Q'),
                          'target_year': [2022] * 4 + [2023] * 2})
    dm = y9c.dm_tests(cases, first='naive', second='combo')
    assert dm.favored.eq('combo').all() and dm.t_stat.gt(0).all()
