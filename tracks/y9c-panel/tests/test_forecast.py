import numpy as np
import pandas as pd
from y9c.forecast import design, evaluate, METHODS


def fixture():
    dates = pd.period_range('2018Q1', '2023Q4', freq='Q').to_timestamp(how='end').normalize()
    rows = []
    for bank in range(1, 53):
        for j, date in enumerate(dates):
            rows.append(dict(rssd_id=bank, report_date=date, total_assets=bank*1000,
                             nii_q=100 + bank + 3*j + np.sin(j + bank)))
    return pd.DataFrame(rows)


def test_calendar_lags_do_not_bridge_missing_rows():
    panel = fixture()
    panel = panel[~(panel.rssd_id.eq(52) & panel.report_date.eq('2021-09-30'))]
    data = design(panel)
    row = data[data.rssd_id.eq(52) & data.quarter.eq(pd.Period('2021Q4'))].iloc[0]
    assert np.isnan(row.y_lag1)
    assert np.isnan(row.g_now)


def test_predictions_do_not_use_future_values_or_assets():
    panel = fixture()
    before = evaluate(panel)[0]
    future = panel.report_date.gt('2021-12-31')
    panel.loc[future, 'nii_q'] *= 7
    panel.loc[future, 'total_assets'] = 100000 - panel.loc[future, 'total_assets']
    after = evaluate(panel)[0]
    first_before = before[before.target_quarter.eq(pd.Period('2022Q1'))]
    first_after = after[after.target_quarter.eq(pd.Period('2022Q1'))]
    assert set(first_before.rssd_id) == set(range(3, 53))
    np.testing.assert_allclose(first_before[METHODS], first_after[METHODS])


def test_common_cases_and_ar_fallback_are_counted():
    panel = fixture()
    panel.loc[panel.rssd_id.eq(52) & panel.report_date.eq('2021-12-31'), 'nii_q'] = -1
    panel = panel[~(panel.rssd_id.eq(51) & panel.report_date.eq('2022-03-31'))]
    forecasts, overall, _, summary = evaluate(panel)
    assert overall.n_forecasts.nunique() == 1
    row = forecasts[forecasts.rssd_id.eq(52) & forecasts.target_quarter.eq(pd.Period('2022Q1'))].iloc[0]
    assert row.ar_fallback and row.pooled_ar == row.naive == -1
    assert summary['origin_audit'][0]['dropped_target_missing'] == 1
    assert summary['ar_fallbacks'] > 0


def test_supplementary_mdape_uses_same_nonzero_cases():
    from y9c.forecast import metrics
    cases = pd.DataFrame({'actual': [0., -1., 10., 100.]})
    for method in METHODS:
        cases[method] = [999., 0., 11., 120.]
    result = metrics(cases)
    assert result.n_forecasts.eq(4).all()
    assert result.n_mape.eq(3).all()
    np.testing.assert_allclose(result.mape, (100 + 10 + 20) / 3)
    np.testing.assert_allclose(result.mdape, 20)
