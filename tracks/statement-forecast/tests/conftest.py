"""All default tests are synthetic; never inspect the shared processed cache."""
import numpy as np
import pandas as pd
import pytest
from statement_forecast.paths import load_design


def synthetic_panel(seed=20260926):
    rng = np.random.default_rng(seed)
    quarters = pd.period_range('2018Q1', '2026Q2', freq='Q')
    rows = []
    for bank in range(1, 57):
        asset = 1e7 + bank * 2e6
        ratios = np.array([3.5, 2.0, 2.8]) + rng.normal(0, .2, 3)
        for j, quarter in enumerate(quarters):
            previous_asset = asset
            asset *= np.exp(.006 + rng.normal(0, .015))
            ratios = .6 * ratios + .4 * np.array([3.5, 2., 2.8]) + rng.normal(0, .15, 3)
            values = (ratios + .1 * np.sin(j * np.pi / 2)) * previous_asset / 400
            rows.append(dict(rssd_id=bank, report_date=quarter.to_timestamp(how='end').normalize(),
                             name=f'Synthetic {bank}', total_assets=asset, nii_q=values[0],
                             noninterest_income_q=values[1], noninterest_expense_q=values[2]))
    return pd.DataFrame(rows)


@pytest.fixture(scope='session')
def panel():
    return synthetic_panel()


@pytest.fixture(scope='session')
def spec():
    return load_design()
