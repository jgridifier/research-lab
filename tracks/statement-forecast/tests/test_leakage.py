import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from y9c.forecast import design, baseline_forecasts, METHODS
from statement_forecast.eb import eb_forecast_origin, asset_ratio


def at_origin(panel, origin, column):
    data = design(panel, column)
    universe = data.loc[data.selected & data.quarter.eq(origin), 'rssd_id']
    return eb_forecast_origin(panel, origin, universe, column)


@pytest.mark.parametrize('target', ['2022Q1', '2024Q3', '2026Q2'])
@pytest.mark.parametrize('column', ['nii_q', 'noninterest_income_q', 'noninterest_expense_q'])
def test_future_values_deletions_ranks_and_estimation(panel, target, column, monkeypatch):
    import statement_forecast.eb as module
    target = pd.Period(target); origin = target - 1
    original_fit = module.fit_qmle
    inputs = []
    def spy(*args):
        inputs.append(tuple(a.copy() for a in args))
        return original_fit(*args)
    monkeypatch.setattr(module, 'fit_qmle', spy)
    before, params = at_origin(panel, origin, column)
    changed = panel.copy()
    future = changed.report_date.dt.to_period('Q').ge(target)
    rng = np.random.default_rng(9)
    for col in ['nii_q', 'noninterest_income_q', 'noninterest_expense_q', 'total_assets']:
        changed.loc[future, col] *= rng.uniform(.1, 10, future.sum())
    changed.loc[future, 'total_assets'] = rng.permutation(changed.loc[future, 'total_assets'])
    after, after_params = at_origin(changed, origin, column)
    deleted, _ = at_origin(panel.loc[~future], origin, column)
    assert_frame_equal(before, after, check_exact=True)
    assert_frame_equal(before, deleted, check_exact=True)
    assert params == after_params
    assert pd.Period(params['data_last_quarter']) < target
    for comparison in inputs[1:]:
        for left, right in zip(inputs[0], comparison, strict=True):
            np.testing.assert_array_equal(left, right)
    base1, _ = baseline_forecasts(design(panel, column), [origin], column)
    base2, _ = baseline_forecasts(design(changed, column), [origin], column)
    assert_frame_equal(base1[['rssd_id', *METHODS]], base2[['rssd_id', *METHODS]], check_exact=True)


def test_target_availability_does_not_select_estimation(panel):
    origin = pd.Period('2024Q2')
    before, params = at_origin(panel, origin, 'nii_q')
    bank = before.rssd_id.iloc[0]
    reduced = panel.loc[~(panel.rssd_id.eq(bank) & panel.report_date.dt.to_period('Q').eq(origin+1))]
    after, other_params = at_origin(reduced, origin, 'nii_q')
    assert_frame_equal(before, after, check_exact=True)
    assert params == other_params


def test_target_asset_invariance_and_level_scaling(panel, monkeypatch):
    import statement_forecast.eb as module
    origin = pd.Period('2024Q2')
    before, _ = at_origin(panel, origin, 'nii_q')
    changed = panel.copy()
    changed.loc[changed.report_date.dt.to_period('Q').eq(origin+1), 'total_assets'] *= 999
    after, _ = at_origin(changed, origin, 'nii_q')
    assert_frame_equal(before, after, check_exact=True)
    original = module.fit_qmle
    def fixed(*args):
        result = original(*args)
        result.update(rho=0., alpha=[0.,0.,0.], post_mean=np.ones(len(args[0])))
        return result
    monkeypatch.setattr(module, 'fit_qmle', fixed)
    scaled, _ = at_origin(panel, origin, 'nii_q')
    assets = panel.loc[panel.report_date.dt.to_period('Q').eq(origin)].set_index('rssd_id').total_assets
    np.testing.assert_array_equal(scaled.eb_panel, assets.reindex(scaled.rssd_id).to_numpy()/400)


def test_ratio_calendar_lookup_invalid_assets_and_ratio_input(panel):
    tiny = pd.DataFrame({'rssd_id': [1]*4, 'report_date': pd.to_datetime(['2020-03-31','2020-09-30','2020-12-31','2021-03-31']),
                         'total_assets': [10., 0., -2., 8.], 'nii_q': [1.,2.,3.,4.]})
    assert asset_ratio(tiny, 'nii_q').y.isna().all()
    origin = pd.Period('2024Q2')
    data = design(panel)
    ids = data.loc[data.selected & data.quarter.eq(origin), 'rssd_id']
    a, p = eb_forecast_origin(panel, origin, ids, 'nii_q')
    b, q = eb_forecast_origin(asset_ratio(panel, 'nii_q'), origin, ids, 'nii_q')
    assert_frame_equal(a, b, check_exact=True)
    assert p == q


@pytest.mark.parametrize('target', ['2022Q1', '2023Q4', '2026Q2'])
def test_end_to_end_forecasts_through_target_ignore_target_and_later_data(panel, spec, target):
    """Full pipeline: every forecast for quarters <= t is identical when all data dated >= t change."""
    from statement_forecast.evaluate import evaluate_line
    target = pd.Period(target)
    changed = panel.copy()
    future = changed.report_date.dt.to_period('Q').ge(target)
    rng = np.random.default_rng(11)
    for col in ['nii_q', 'noninterest_income_q', 'noninterest_expense_q', 'total_assets']:
        changed.loc[future, col] *= rng.uniform(.2, 5, future.sum())
    changed.loc[future, 'total_assets'] = rng.permutation(changed.loc[future, 'total_assets'])
    columns = ['rssd_id', 'quarter', 'target_quarter', *METHODS, 'eb_panel', 'ar_fallback', 'eb_fallback']
    for line in spec['lines']:
        before = evaluate_line(panel, line['key'], spec)[0]
        after = evaluate_line(changed, line['key'], spec)[0]
        keep = lambda frame: frame.loc[frame.target_quarter.le(target), columns].reset_index(drop=True)
        assert len(keep(before)) > 0
        assert_frame_equal(keep(before), keep(after), check_exact=True)


YTD = {'nii_q': 'nii_ytd', 'noninterest_income_q': 'noninterest_income_ytd',
       'noninterest_expense_q': 'noninterest_expense_ytd'}


def decumulated(ytd_panel):
    """Quarterly flows from YTD with the shared y9c de-cumulation (no copy)."""
    from y9c.panel import decumulate
    panel = ytd_panel.copy()
    for quarterly, ytd in YTD.items():
        panel[quarterly], _ = decumulate(panel, ytd)
    return panel


@pytest.mark.parametrize('target', ['2023Q2', '2024Q1', '2025Q4'])
def test_decumulation_future_ytd_perturbation_leaves_forecasts_identical(panel, spec, target):
    """Perturb YTD reported at dates >= t, de-cumulate, evaluate: forecasts for targets <= t are identical."""
    from statement_forecast.evaluate import evaluate_line
    target = pd.Period(target)
    ytd_panel = panel.drop(columns=list(YTD)).copy()
    year = [ytd_panel.rssd_id, ytd_panel.report_date.dt.year]
    for quarterly, ytd in YTD.items():
        ytd_panel[ytd] = panel[quarterly].groupby(year).cumsum()
    base = decumulated(ytd_panel)
    np.testing.assert_allclose(base[list(YTD)], panel[list(YTD)], rtol=1e-12)
    changed_ytd = ytd_panel.copy()
    future = changed_ytd.report_date.dt.to_period('Q').ge(target)
    rng = np.random.default_rng(21)
    for ytd in YTD.values():
        changed_ytd.loc[future, ytd] *= rng.uniform(.3, 3, future.sum())
    changed = decumulated(changed_ytd)
    quarter = changed.report_date.dt.to_period('Q')
    # The perturbation reaches the de-cumulated target quarter and later ones only.
    assert not np.allclose(changed.loc[quarter.eq(target), 'nii_q'], base.loc[quarter.eq(target), 'nii_q'])
    np.testing.assert_array_equal(changed.loc[quarter.lt(target), list(YTD)], base.loc[quarter.lt(target), list(YTD)])
    columns = ['rssd_id', 'quarter', 'target_quarter', *METHODS, 'eb_panel', 'ar_fallback', 'eb_fallback']
    for line in spec['lines']:
        before = evaluate_line(base, line['key'], spec)[0]
        after = evaluate_line(changed, line['key'], spec)[0]
        keep = lambda frame: frame.loc[frame.target_quarter.le(target), columns].reset_index(drop=True)
        assert len(keep(before)) > 0
        assert_frame_equal(keep(before), keep(after), check_exact=True)
        # Non-vacuous: the next target's forecasts do move with the perturbed data.
        nxt = lambda frame: frame.loc[frame.target_quarter.eq(target + 1), 'eb_panel'].to_numpy()
        assert not np.allclose(nxt(before), nxt(after))
