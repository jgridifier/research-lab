"""prereg §6.3 test 9: hand-computed HLN/NW DM, Holm, verdict rules."""
import numpy as np
import pandas as pd
from scipy.stats import t as student_t
from trading_ot import gate


def test_panel_dm_hand_h1():
    d = np.array([1.0, 2.0, 3.0, 4.0])
    r = gate.panel_dm(d, h=1)
    se = np.sqrt(1.25 / 4)                               # population variance / T, lag 0
    hln = np.sqrt((4 + 1 - 2) / 4)
    assert np.isclose(r['se'], se) and np.isclose(r['hln'], hln)
    assert np.isclose(r['stat'], 2.5 / se * hln)
    assert np.isclose(r['p'], student_t.sf(2.5 / se * hln, 3))


def test_panel_dm_hand_h2_newey_west():
    d = np.array([1.0, 3.0, 2.0, 5.0, 4.0])
    x = d - d.mean()
    g0 = x @ x / 5
    g1 = x[1:] @ x[:-1] / 5
    lrv = g0 + 2 * 0.5 * g1                             # Bartlett weight 1 - 1/2 at lag 1
    r = gate.panel_dm(d, h=2)
    hln = np.sqrt((5 + 1 - 4 + 2 * 1 / 5) / 5)
    assert np.isclose(r['se'], np.sqrt(lrv / 5)) and np.isclose(r['hln'], hln)
    assert np.isclose(r['stat'], d.mean() / np.sqrt(lrv / 5) * hln)


def test_holm_toy():
    adj = gate.holm({'H1': 0.01, 'H2': 0.04})
    assert np.isclose(adj['H1'], 0.02) and np.isclose(adj['H2'], 0.04)
    adj = gate.holm({'H1': 0.03, 'H2': 0.02})
    assert np.isclose(adj['H2'], 0.04) and np.isclose(adj['H1'], 0.04)
    adj = gate.holm({'H1': 0.5, 'H2': np.nan})
    assert np.isclose(adj['H1'], 1.0) and np.isnan(adj['H2'])


def test_verdicts():
    lobo_ok, lobo_bad = {1: 0.05, 2: 0.04}, {1: 0.05, 2: -0.01}
    assert gate.verdict(0.01, 0.08, 0.15, 0.9, lobo_ok, 18) == 'PASS'
    assert gate.verdict(0.01, 0.08, 0.15, 0.9, lobo_bad, 18) == 'PASS-fragile'
    assert gate.verdict(0.01, 0.08, 0.15, 0.75, lobo_ok, 18) == 'INCOMPLETE'
    assert gate.verdict(0.30, 0.01, 0.025, 0.9, lobo_ok, 18) == 'FAIL'
    assert gate.verdict(0.30, -0.01, 0.10, 0.9, lobo_ok, 18) == 'FAIL'
    assert gate.verdict(0.30, 0.02, 0.10, 0.9, lobo_ok, 18) == 'INCOMPLETE'
    assert gate.verdict(0.001, 0.2, 0.3, 0.9, lobo_ok, 15) == 'INCOMPLETE'


def test_relative_gain_ci_and_lobo():
    rows = []
    for k, q in enumerate(pd.period_range('2022Q1', periods=6, freq='Q')):
        for b in [1, 2, 3]:
            rows.append(dict(target_quarter=q, rssd_id=b, S_ref=1.0 + 0.1 * k, S_ot=0.9 + 0.1 * k + 0.01 * b))
    cases = pd.DataFrame(rows)
    pq = gate.per_quarter(cases)
    ci = gate.relative_gain_ci(pq)
    assert np.isclose(ci['G'], pq.dbar.sum() / pq.Sbar_ref.sum())
    assert set(gate.lobo(cases)) == {1, 2, 3}


def test_fixed_m_dm_runs():
    r = gate.fixed_m_dm(np.array([0.1, 0.2, -0.05, 0.3, 0.15, 0.05, 0.2, 0.1]))
    assert r['m'] == 2 and r['df'] == 4 and np.isfinite(r['p'])
