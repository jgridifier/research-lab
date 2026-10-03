"""Leakage: the origin-t weight and every forecast for targets <= t ignore later data.

Timing convention (as in v1's test_leakage.py): a forecast for target t is made at
origin t-1 with weight w_l,t-1, so perturbing or deleting data dated >= t must
leave it unchanged. The weight w_l,t fit at origin t uses outcomes dated t by
construction (pseudo-OOS targets s+1 <= t), so it is checked against data dated
> t; the test also shows w_l,t does respond to data dated t (it is not vacuous).
"""
import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from y9c import forecast as y9c
from statement_forecast import combo

COLUMNS = ['rssd_id', 'quarter', 'target_quarter', 'actual', 'naive', 'seasonal_naive', 'pooled_ar',
           'combo', 'w', 'ar_fallback']
FLOWS = ['nii_q', 'noninterest_income_q', 'noninterest_expense_q']
FIRST = pd.Period('2021Q4')


def quarter(panel):
    return panel.report_date.dt.to_period('Q')


def perturbed(panel, start, seed):
    """Scale flows and assets dated >= start and permute assets (reshuffles top-50 ranks)."""
    changed = panel.copy()
    future = quarter(changed).ge(start)
    rng = np.random.default_rng(seed)
    for col in [*FLOWS, 'total_assets']:
        changed.loc[future, col] *= rng.uniform(.1, 10, future.sum())
    changed.loc[future, 'total_assets'] = rng.permutation(changed.loc[future, 'total_assets'].to_numpy())
    return changed


def run(panel, line, spec, last_origin):
    forecasts, _, weights = combo.combo_forecasts(panel, line, spec, pd.period_range(FIRST, last_origin, freq='Q'))
    return forecasts[COLUMNS].reset_index(drop=True), weights.reset_index(drop=True)


@pytest.mark.parametrize('target', ['2022Q2', '2024Q1', '2025Q3'])
def test_data_dated_ge_t_leaves_forecasts_through_t_unchanged(panel, combo_spec, target):
    t = pd.Period(target)
    changed = perturbed(panel, t, seed=int(t.ordinal))
    deleted = panel.loc[quarter(panel).lt(t)]
    forecast_columns = [c for c in COLUMNS if c != 'actual']  # the actual for target t is data dated t
    for line in combo_spec['lines']:
        before, w_before = run(panel, line, combo_spec, t)
        after, w_after = run(changed, line, combo_spec, t)
        cut, w_cut = run(deleted, line, combo_spec, t - 1)
        keep = lambda f, last=t: f.loc[f.target_quarter.le(last)].reset_index(drop=True)
        assert len(keep(before)) > 0
        # Perturbing flows, assets and ranks dated >= t.
        assert_frame_equal(keep(before)[forecast_columns], keep(after)[forecast_columns], check_exact=True)
        upto = lambda w: w.loc[pd.PeriodIndex(w.origin, freq='Q') <= t - 1].reset_index(drop=True)
        assert_frame_equal(upto(w_before), upto(w_after), check_exact=True)
        # Deleting every row dated >= t: cases for targets <= t-1 and every weight through
        # origin t-1 (including w_l,t-1, the weight applied to target t) are identical.
        assert_frame_equal(keep(before, t - 1), cut, check_exact=True)
        assert_frame_equal(upto(w_before), w_cut, check_exact=True)
        # Target-t N and P after the deletion (keeping only the target value as the actual).
        column = line['column']
        rebuilt, _ = y9c.baseline_forecasts(y9c.design(truncated_plus_target(deleted, t - 1, column, panel), column),
                                            [t - 1], column)
        at_t = before.loc[before.target_quarter.eq(t)].reset_index(drop=True)
        assert len(at_t)
        assert_frame_equal(at_t[rebuilt.columns], rebuilt.reset_index(drop=True), check_exact=True)
        recombined = combo.combine(rebuilt.naive, rebuilt.pooled_ar, w_cut.w.iloc[-1])
        np.testing.assert_array_equal(at_t.combo.to_numpy(), recombined)
        # Non-vacuity: target t+1 forecasts move when data dated t change.
        nxt = lambda f: f.loc[f.target_quarter.eq(t + 1), 'combo'].to_numpy()
        assert len(nxt(before)) and not np.array_equal(nxt(before), nxt(after))


@pytest.mark.parametrize('origin', ['2021Q4', '2023Q2', '2026Q1'])
def test_origin_weight_ignores_data_after_origin(panel, combo_spec, origin):
    t = pd.Period(origin)
    later = perturbed(panel, t + 1, seed=7)
    deleted = panel.loc[quarter(panel).le(t)]
    moved_at_t = perturbed(panel, t, seed=8)
    for line in combo_spec['lines']:
        base = combo.combo_weights(panel, line['column'], [t], combo_spec, line['key'])
        assert_frame_equal(base, combo.combo_weights(later, line['column'], [t], combo_spec, line['key']),
                           check_exact=True)
        assert_frame_equal(base, combo.combo_weights(deleted, line['column'], [t], combo_spec, line['key']),
                           check_exact=True)
        assert base.weight_rule.iloc[0] == 'fit' and base.last_pseudo_target.iloc[0] == str(t)
        # w_l,t legitimately uses outcomes dated t: perturbing them changes the fit set.
        moved = combo.combo_weights(moved_at_t, line['column'], [t], combo_spec, line['key'])
        assert moved.pseudo_sae.iloc[0] != base.pseudo_sae.iloc[0]


def truncated_plus_target(panel, s, column, source=None):
    """Rows dated <= s plus only the target-quarter value of the line (needed as the actual)."""
    source = panel if source is None else source
    past = panel.loc[quarter(panel).le(s)]
    target = source.loc[quarter(source).eq(s + 1), ['rssd_id', 'report_date', column]]
    return pd.concat([past, target], ignore_index=True)


@pytest.mark.parametrize('origin', ['2022Q3', '2025Q2'])
def test_spy_fit_set_targets_le_t_and_pseudo_cases_rebuilt_at_s(panel, combo_spec, origin, monkeypatch):
    t = pd.Period(origin)
    seen = []
    original = combo.fit_weight
    def spy(cases, design_json):
        seen.append(cases.copy())
        return original(cases, design_json)
    monkeypatch.setattr(combo, 'fit_weight', spy)
    for line in combo_spec['lines']:
        column = line['column']
        seen.clear()
        combo.combo_weights(panel, column, [t], combo_spec, line['key'])
        (cases,) = seen
        assert len(cases) and cases.target_quarter.le(t).all() and cases.target_quarter.max() == t
        assert (cases.target_quarter == cases.quarter + 1).all()
        for s, group in cases.groupby('quarter'):
            # baseline_forecasts at origin s, on data truncated to <= s (plus the target actual only).
            reference, _ = y9c.baseline_forecasts(y9c.design(truncated_plus_target(panel, s, column), column),
                                                  [s], column)
            assert_frame_equal(group.reset_index(drop=True), reference.reset_index(drop=True), check_exact=True)


def test_spy_does_not_use_selection_or_assets_after_s(panel, combo_spec):
    s = pd.Period('2020Q3')
    column = 'nii_q'
    base = truncated_plus_target(panel, s, column)
    reference, _ = y9c.baseline_forecasts(y9c.design(base, column), [s], column)
    # Target-quarter assets (would change ranks at s+1) do not affect pseudo-OOS P at s.
    with_assets = pd.concat([panel.loc[quarter(panel).le(s)], perturbed(panel, s + 1, 5).loc[
        quarter(panel).eq(s + 1), ['rssd_id', 'report_date', 'total_assets', column]]], ignore_index=True)
    with_assets[column] = with_assets[column].where(quarter(with_assets).le(s), base[column].to_numpy())
    other, _ = y9c.baseline_forecasts(y9c.design(with_assets, column), [s], column)
    assert_frame_equal(reference[['rssd_id', 'naive', 'pooled_ar']], other[['rssd_id', 'naive', 'pooled_ar']],
                       check_exact=True)
