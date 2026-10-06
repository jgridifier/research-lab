"""Addendum §5.3 tests 13-14 and the §5.4 decision rules."""
import numpy as np
import pandas as pd
import pytest
from trading_ot import gate


def test_dm_fixedb_critical_values_T50():
    r = gate.dm_fixedb(np.random.default_rng(0).normal(size=50))
    assert r['M'] == 7 and r['R'] == 200_000 and r['seed'] == 20261006
    assert abs(r['cv_975'] - 2.417) <= 0.03
    assert abs(r['cv_95'] - 1.976) <= 0.03
    # ERRATA_v1_1 E3: authoritative values from a fresh default_rng(20261006), R = 200,000
    assert round(r['cv_975'], 4) == 2.4101
    assert round(r['cv_95'], 4) == 1.9658


def test_dm_fixedb_hand_example():
    d = np.array([0.3, -0.1, 0.4, 0.2, 0.0, 0.5, -0.2, 0.1, 0.3, 0.2])
    T, M = 10, 3
    x = d - d.mean()
    g = [np.dot(x[l:], x[:T - l]) / T for l in range(M + 1)]
    omega = g[0] + 2 * sum((1 - l / (M + 1)) * g[l] for l in range(1, M + 1))
    r = gate.dm_fixedb(d, R=20_000)
    assert r['M'] == M
    assert r['omega'] == pytest.approx(omega, rel=1e-12)
    assert r['stat'] == pytest.approx(d.mean() / np.sqrt(omega / T), rel=1e-12)
    null = gate.fixedb_null(T, M, 20_000, 20261006)
    assert r['p'] == pytest.approx(np.mean(null >= r['stat']))


def test_dm_fixedb_p_monotone_and_deterministic():
    base = np.random.default_rng(5).normal(size=50)
    ps = [gate.dm_fixedb(base + shift)['p'] for shift in np.linspace(-1, 1, 9)]
    assert all(a >= b for a, b in zip(ps, ps[1:]))
    assert gate.dm_fixedb(base)['p'] == gate.dm_fixedb(base)['p']


def test_fluctuation_cv_deterministic():
    d = np.random.default_rng(3).normal(size=50)
    a, b = gate.fluctuation_test(d), gate.fluctuation_test(d)
    assert a['m'] == 15 and a['cv'] == b['cv'] and a['stat'] == b['stat']
    assert 2.0 < a['cv'] < 4.5


def test_mean_shift_detects_shift():
    dates = pd.period_range('2014Q1', '2026Q2', freq='Q')
    d = np.where(dates >= pd.Period('2020Q1'), 1.0, 0.0) + np.random.default_rng(1).normal(0, .2, 50)
    out = gate.mean_shift_tests(d, dates)
    assert out['2020Q1']['p_holm'] < 0.01 and out['2020Q1']['shift'] > 0.5


def _verdict(**kw):
    base = dict(p_holm=0.01, G=0.06, G_U=0.10, coverage90=0.9, lobo_gains={1: .02, 2: .03},
                subperiod_gains={'P1': .05, 'P2': .04, 'P3': -.01}, n_targets=50)
    base.update(kw)
    return gate.verdict_v1_1(**base)


def test_verdict_v1_1_rules():
    assert _verdict() == 'PASS'
    assert _verdict(subperiod_gains={'P1': .05, 'P2': -.01, 'P3': -.01}) == 'PASS-fragile'
    assert _verdict(lobo_gains={1: -.01, 2: .03}) == 'PASS-fragile'
    assert _verdict(n_targets=39) == 'INCOMPLETE'
    assert _verdict(integrity_ok=False) == 'INCOMPLETE'
    assert _verdict(G=-0.01) == 'FAIL'
    assert _verdict(G_U=0.029) == 'FAIL'
    assert _verdict(p_holm=0.2) == 'INCOMPLETE'
    assert _verdict(coverage90=0.75) == 'INCOMPLETE'


def test_gain_v1_1_upper_bound():
    pq = pd.DataFrame({'Sbar_ref': np.full(50, 1.0), 'dbar': np.random.default_rng(2).normal(.05, .1, 50)})
    g = gate.gain_v1_1(pq)
    assert g['G'] == pytest.approx(pq.dbar.sum() / 50)
    assert g['G_U'] == pytest.approx(g['G'] + g['cv_95'] * g['se'] / 1.0)
