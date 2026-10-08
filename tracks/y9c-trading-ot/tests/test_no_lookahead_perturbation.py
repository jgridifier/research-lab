"""prereg §6.3 test 2: forecasts and frozen parameters at origin t ignore every row dated > t,
including later-quarter YTD values (re-de-cumulated) and later macro rows."""
import numpy as np
import pandas as pd
import pytest
from trading_ot import walkforward as WF, sets
from conftest import to_panel


def perturbed(ytd, macro, t, seed):
    rng = np.random.default_rng(seed)
    y = ytd.copy()
    later = y.report_date.dt.to_period('Q').gt(t)
    for c in ['trading_revenue_ytd', 'trading_assets', 'total_assets']:
        y.loc[later, c] = y.loc[later, c] * rng.uniform(-3, 10, later.sum())
    m = macro.copy()
    m.loc[m.index > t] = m.loc[m.index > t] * rng.uniform(0.1, 10, m.loc[m.index > t].shape)
    return to_panel(y), m


def deleted(ytd, t):
    return to_panel(ytd[ytd.report_date.dt.to_period('Q').le(t)])


def forecasts_at(panel, macro, t, banks):
    out = {}
    fc = WF.t2_member_forecasts(panel, banks, t, 1, macro)
    out.update({f'T2_{m}': q for m, (q, _) in fc.items()})
    pop, scale, cfc = WF.cs_member_forecasts(panel, t, macro)
    out.update({f'CS_{m}': q for m, (q, _) in cfc.items()})
    Qw, info = WF.war_rm(panel, t, pop)
    out['WAR'] = Qw
    out['pop'] = np.array(pop, float)
    out['scale'] = scale
    out['beta_rho'] = np.array([info['beta'], info['rho']])
    return out


@pytest.mark.parametrize('origin', ['2022Q2', '2024Q3'])
def test_forecasts_at_origin_ignore_later_rows(ytd, panel, macro, origin):
    t = pd.Period(origin)
    banks = sets.exante_bank_set(panel)
    assert len(banks) >= 5
    base = forecasts_at(panel, macro, t, banks)
    p2, m2 = perturbed(ytd, macro, t, seed=t.ordinal)
    assert not p2[p2.quarter.gt(t)].trading_revenue_q.equals(panel[panel.quarter.gt(t)].trading_revenue_q)
    pert = forecasts_at(p2, m2, t, banks)
    cut = forecasts_at(deleted(ytd, t), macro[macro.index <= t], t, banks)
    for k in base:
        np.testing.assert_array_equal(base[k], pert[k], err_msg=f'{k} changed under perturbation after {t}')
        np.testing.assert_array_equal(base[k], cut[k], err_msg=f'{k} changed when rows after {t} deleted')
    assert np.isfinite(base['T2_B2']).any() and np.isfinite(base['WAR']).any()


def test_forecasts_do_respond_to_data_at_origin(ytd, panel, macro):
    """Non-vacuous: perturbing data dated t itself changes the origin-t forecasts."""
    t = pd.Period('2023Q2')
    banks = sets.exante_bank_set(panel)
    base = WF.t2_member_forecasts(panel, banks, t, 1, macro)
    p2, m2 = perturbed(ytd, macro, t - 1, seed=3)
    pert = WF.t2_member_forecasts(p2, banks, t, 1, m2)
    assert not np.array_equal(base['B2'][0], pert['B2'][0], equal_nan=True)


def test_frozen_parameters_ignore_post_burnin(ytd, panel, macro):
    t = WF.FREEZE_ORIGIN
    p2, m2 = perturbed(ytd, macro, t, seed=11)
    a = WF.freeze_decisions(panel, macro, 'matched')
    b = WF.freeze_decisions(p2, m2, 'matched')
    c = WF.freeze_decisions(deleted(ytd, t), macro[macro.index <= t], 'matched')
    assert a == b == c
