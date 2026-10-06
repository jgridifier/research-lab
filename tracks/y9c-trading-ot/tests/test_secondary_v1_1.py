"""Phase B secondary family (H1b-H1e, H2b-H2f), F1-F5 helpers and secondary metrics, on SYNTHETIC data only."""
import copy

import numpy as np
import pandas as pd
import pytest
from trading_ot import baselines as B
from trading_ot import ot_bary, ot_war, select, walkforward as W10, walkforward_v1_1 as V
from trading_ot import secondary_v1_1 as SEC
from trading_ot.scoring import U99, trimmed_w2sq

EPOCHS = select.EPOCH_ORIGINS[:2]
TARGETS = pd.period_range('2014Q1', '2015Q4', freq='Q')


@pytest.fixture(scope='module')
def prim(panel11, macro11):
    return V.primary(panel11, macro11, epochs=EPOCHS, targets=TARGETS, store=True)


def test_store_does_not_change_primary(prim, panel11, macro11):
    plain = V.primary(panel11, macro11, epochs=EPOCHS, targets=TARGETS)
    for k in ('h1', 'h2'):
        pd.testing.assert_frame_equal(plain[k].reset_index(drop=True), prim[k].reset_index(drop=True))
    assert plain['selection_log'] == prim['selection_log']


def test_store_contents(prim):
    st = prim['store']
    assert sorted(st['t2']) == list(TARGETS) and sorted(st['cs']) == list(TARGETS)
    assert st['t2_sel0']['cases'].target_quarter.max() == pd.Period('2013Q4', freq='Q')
    for tq, e in st['t2'].items():
        assert set(e['Q']) == set(V.MEMBERS) and e['bary'].shape == e['Q']['B0'].shape
    info = st['cs'][TARGETS[0]]['info']
    assert max(info['Qd']) == TARGETS[0] - 1                  # cross-sections only up to the origin


# ── OT helpers ──
def test_war_beta_pairs_matches_war_beta_when_complete():
    rng = np.random.default_rng(0)
    qs = pd.period_range('2009Q1', '2013Q4', freq='Q')
    Qd = {q: np.sort(rng.normal(size=99)) + 0.1 * k for k, q in enumerate(qs)}
    Qs = np.stack([Qd[q] for q in qs])
    b0 = ot_war.war_beta(Qs, 1)
    b1 = ot_war.war_beta_pairs(Qd, ot_war.frechet_mean(Qs), 1)
    assert b1[2] == b0[2] and b1[0] == pytest.approx(b0[0], abs=1e-12) and b1[3] is None


def test_war_beta_pairs_skips_missing_quarters_and_q1_shift():
    rng = np.random.default_rng(1)
    qs = pd.period_range('2009Q1', '2016Q4', freq='Q')
    base = np.sort(rng.normal(size=99))
    v, Qd = 0.0, {}
    for q in qs:
        v = 0.5 * v + rng.normal(0, 0.05) + (0.8 if q.quarter == 1 else 0.0)
        Qd[q] = base + v
    full = ot_war.war_beta_pairs(Qd, np.mean(list(Qd.values()), axis=0), 1)
    gap = {q: Q for q, Q in Qd.items() if q not in pd.PeriodIndex(['2012Q1', '2012Q2'], freq='Q')}
    part = ot_war.war_beta_pairs(gap, np.mean(list(gap.values()), axis=0), 1)
    assert part[2] == full[2] - 3                             # pairs touching the two missing quarters dropped
    shift = ot_war.war_beta_pairs(Qd, np.mean(list(Qd.values()), axis=0), 1, q1_shift=True)
    assert shift[3] is not None and np.mean(shift[3]) > 0.3   # the Q1 tangent shift is picked up


def test_war_rm_q1_shift_only_for_q1_targets(panel11):
    pop = W10.cs_population(panel11[panel11.quarter.le(pd.Period('2014Q3', freq='Q'))], pd.Period('2014Q3', freq='Q'))
    Qa, ia = W10.war_rm(panel11, '2014Q3', pop, first_r='2009Q1')
    Qb, ib = W10.war_rm(panel11, '2014Q3', pop, first_r='2009Q1', q1_shift=True)   # target 2014Q4: no shift
    assert ib['q1_delta'] is not None and np.allclose(ia['Qhat'], ib['Qhat'], atol=0.5 * np.abs(ia['Qhat']).max())
    Qc, ic = W10.war_rm(panel11, '2014Q4', pop, first_r='2009Q1', q1_shift=True)   # target 2015Q1: shifted
    assert np.all(np.diff(ic['Qhat']) >= -1e-9)


def test_ar_map_recovers_alpha_for_location_shifts():
    qs = pd.period_range('2009Q1', '2012Q4', freq='Q')
    base = np.sort(np.random.default_rng(2).normal(size=99))
    alpha, m, dm, Qd = 0.6, 0.0, 1.0, {}
    for q in qs:
        Qd[q] = base + m
        m, dm = m + dm, alpha * dm
    Qhat, fit = ot_war.ar_map_forecast(Qd, qs[-1])
    assert fit['alpha'] == pytest.approx(alpha, abs=1e-9)
    last_disp = Qd[qs[-1]] - Qd[qs[-2]]
    assert np.allclose(Qhat, Qd[qs[-1]] + alpha * last_disp)
    with pytest.raises(ValueError):
        ot_war.ar_map_forecast({qs[0]: base}, qs[0])


def test_linear_pool_fast_matches_bisection():
    rng = np.random.default_rng(3)
    Qs = np.sort(rng.normal(size=(3, 4, 99)) * rng.uniform(.5, 3, (3, 4, 1)) + rng.normal(size=(3, 4, 1)), axis=2)
    Qs[0, 1, 30:40] = Qs[0, 1, 30]
    assert np.abs(ot_bary.linear_pool_quantiles(Qs) - ot_bary.linear_pool_quantiles_fast(Qs)).max() < 1e-7


# ── family members ──
def test_h1b_kappa_and_causality(prim):
    cases, info = SEC.h1b(prim['store'])
    w = info['weights']
    assert [x['target'] for x in w] == [str(t) for t in TARGETS]
    for x in w:
        assert x['kappa'] == pytest.approx(x['n'] / (x['n'] + SEC.H1B_N0))
        assert sum(x['weights']) == pytest.approx(1.0) and min(x['weights']) >= 0
    assert w[1]['n'] > w[0]['n']                                  # the pool grows with the origin
    st = copy.deepcopy(prim['store'])
    last = TARGETS[-1]
    st['t2'][last]['cases'] = st['t2'][last]['cases'].assign(y=lambda d: d.y * 50)   # perturb the last target
    _, info2 = SEC.h1b(st)
    assert info2['weights'][:-1] == w[:-1]                       # earlier weights cannot see it


def test_h1c_is_linear_pool_of_trimmed(prim):
    st = prim['store']
    cases, _ = SEC.h1c(st)
    tq = TARGETS[0]
    e = st['t2'][tq]
    K = st['settings'][e['epoch']]['t2']['trimmed']
    ok = SEC._rows_ok([e['Q'][m] for m in K])
    Q = ot_bary.linear_pool_quantiles(np.stack([e['Q'][m][ok] for m in K]))
    S, _ = V._score(Q, e['cases'].y.to_numpy(float)[ok], e['cases'].scale.to_numpy(float)[ok])
    got = cases[cases.target_quarter.eq(tq)].S_ot.to_numpy()[ok]
    assert np.allclose(np.nan_to_num(got), np.nan_to_num(S), atol=1e-6)


def test_h2e_activation_threshold(prim):
    off, info_off = SEC.h2e(prim['store'], min_pit=10 ** 9)
    assert off.S_ot.isna().all() and not any(a['active'] for a in info_off['activation'])
    on, info_on = SEC.h2e(prim['store'], min_pit=1)
    assert on.S_ot.notna().any() and all(a['active'] for a in info_on['activation'])
    assert info_on['activation'][1]['n_pit'] > info_on['activation'][0]['n_pit']


def test_h2c_losses(prim, panel11):
    out = SEC.h2c(prim['store'], panel11)
    tq = TARGETS[2]
    info = prim['store']['cs'][tq]['info']
    Qr = SEC.realized_cs_quantiles(panel11, tq)
    row = out['persistence'].set_index('target_quarter').loc[tq]
    assert row.S_ot == pytest.approx(trimmed_w2sq(info['Qhat'], Qr))
    assert row.S_ref == pytest.approx(trimmed_w2sq(info['Qt'], Qr))
    assert out['climatology'].set_index('target_quarter').loc[tq].S_ref == pytest.approx(trimmed_w2sq(info['Qbar'], Qr))


def test_h2b_dollar_mapping(prim, panel11):
    cases, _ = SEC.h2b(prim['store'], panel11)
    assert len(cases) == sum(len(prim['store']['t2'][t]['cases']) for t in TARGETS)
    assert cases.S_ot.notna().any()


def test_h2d_and_h2f_run(prim, macro11):
    d, info = SEC.h2d(prim['store'], macro11)
    assert all(f['status'] == 'ok' for f in info['fits']) and d.S_ot.notna().any()
    f, finfo = SEC.h2f(prim['store'])
    assert finfo['status'] == 'ok' and all(-1 <= x['alpha'] <= 1 for x in finfo['fits'])


def test_h2f_na_when_first_origin_fails(prim):
    st = copy.deepcopy(prim['store'])
    first = min(st['cs'])
    st['cs'][first]['info']['Qd'] = {first - 1: st['cs'][first]['info']['Qd'][first - 1]}
    cases, info = SEC.h2f(st)
    assert info['status'] == 'N/A' and cases.empty


def test_t1_series_and_min_own(panel11):
    t1 = SEC.t1_series(panel11)
    q = pd.Period('2012Q2', freq='Q')
    want = panel11.loc[panel11.quarter.eq(q), 'trading_revenue_q'].sum()
    assert t1.set_index('quarter').trading_revenue_q[q] == pytest.approx(want)
    assert t1.set_index('quarter').trading_revenue_q.loc[:'2008Q4'].isna().all()   # pre-sample mask
    short = t1[t1.quarter.le(pd.Period('2010Q3', freq='Q'))]
    W = B.Wide(short, [0], first='2009Q1')
    o = W.idx('2010Q3')
    Q8, _ = B.b1_snaive(W, o, 1, 'usd', np.array([np.nan]))
    W.min_own = SEC.T1_MIN_OWN
    Q2, _ = B.b1_snaive(W, o, 1, 'usd', np.array([np.nan]))
    assert np.isnan(Q8).all() and np.isfinite(Q2).all()          # 3 own errors: < 8 but >= 2, no pooling


def test_h1d_runs_and_selects_causally(panel11):
    cases, info = SEC.h1d(panel11, epochs=EPOCHS, targets=TARGETS)
    assert list(cases.target_quarter) == list(TARGETS) and (cases.rssd_id == 0).all()
    assert [s['epoch'] for s in info['selection']] == ['2013Q4', '2014Q4']
    assert set(info['settings'][EPOCHS[0]]['m0']) <= set(SEC.T1_MEMBERS)
    raw = info['raw']
    assert np.allclose(cases.S_ot, raw.crps_ot / raw.scale)


def test_h1e_targets_and_b6_dropped(panel11, macro11):
    assert [len(SEC.h1e_targets(h)) for h in (2, 3, 4)] == [49, 48, 47]
    assert SEC.h1e_targets(2)[0] == pd.Period('2014Q2', freq='Q')
    cases, info = SEC.h1e(panel11, macro11, 3, epochs=EPOCHS[:1],
                          targets=pd.PeriodIndex(['2014Q3', '2014Q4', '2015Q1'], freq='Q'))
    assert all('B6' in s['excluded_low_coverage'] for s in info['selection'])
    assert list(cases.target_quarter.unique()) == [pd.Period(x, freq='Q') for x in ['2014Q3', '2014Q4', '2015Q1']]


def test_holm_family_ignores_na():
    res = {'H1b': dict(status='ok', p=0.01), 'H1c': dict(status='ok', p=0.04), 'H2f': dict(status='N/A', p=np.nan)}
    h = SEC.holm_family(res)
    assert h['m'] == 2 and res['H1b']['p_holm_secondary'] == pytest.approx(0.02)
    assert np.isnan(res['H2f']['p_holm_secondary'])


def test_f3_placebo_is_seeded(prim):
    a = SEC.f3_placebo(prim['store'], n_perm=5)
    b = SEC.f3_placebo(prim['store'], n_perm=5)
    assert a == b and a['n_perm'] == 5


def test_secondary_metrics_shapes(prim):
    m = SEC.secondary_metrics(prim['store'], 'H1')
    assert sum(m['ot']['pit_hist10']) == m['ot']['n_cases'] == m['ref']['n_cases']
    assert 0 <= m['ot']['cov50'] <= m['ot']['cov90'] <= 1


# ── outside the family: K = 2 FPCA WAR and the ridge point forecast (ERRATA_v1_1b §4) ──
def _rank2_qd(A, n=24, seed=3):
    rng = np.random.default_rng(seed)
    u = np.asarray(U99)
    base = 50 * (u - 0.5) + 200 * (u - 0.5) ** 3
    phi1, phi2 = np.ones_like(u), u - 0.5                 # shift and spread
    xi = np.zeros((n, 2))
    xi[0] = [1.0, -2.0]
    for k in range(1, n):
        xi[k] = A @ xi[k - 1] + (rng.normal(size=2) if k < n - 1 else 0)
    qs = pd.period_range('2009Q1', periods=n, freq='Q')
    Qd = {q: base + 5 * x[0] * phi1 + 40 * x[1] * phi2 for q, x in zip(qs, xi)}
    return Qd, qs


def test_fpca_war_recovers_rank2_dynamics():
    A = np.array([[0.6, 0.1], [-0.2, 0.4]])
    Qd, qs = _rank2_qd(A)
    Qbar = np.mean([Qd[q] for q in qs], axis=0)
    Qhat, fit = ot_war.fpca_war_forecast(Qd, Qbar, qs[-1], K=2)
    assert fit['explained_share'] == pytest.approx(1.0, abs=1e-9)        # V has rank 2 exactly (after centring)
    assert fit['n_pairs'] == len(qs) - 1 and np.all(np.diff(Qhat) >= -1e-12)
    # exact rank-2 data: the forecast lies in Qbar + span(phi) and equals the OLS fit of the dynamics
    V_ = np.stack([Qd[q] - Qbar for q in qs])
    Ast = np.asarray(fit['A'])
    assert np.isfinite(Ast).all() and fit['spectral_radius'] < 1.5
    assert np.allclose(Qhat, np.maximum.accumulate(Qhat))
    assert np.linalg.matrix_rank(np.vstack([V_, Qhat - Qbar]), tol=1e-6) == 2


def test_fpca_war_raises_when_too_short():
    Qd, qs = _rank2_qd(np.eye(2) * 0.5, n=2)
    with pytest.raises(ValueError):
        ot_war.fpca_war_forecast(Qd, np.mean(list(Qd.values()), axis=0), qs[-1])


def test_h2_fpca_on_store(prim):
    cases, info = SEC.h2_fpca(prim['store'])
    assert info['status'] == 'ok' and info['K'] == 2
    assert set(cases.target_quarter) <= set(TARGETS) and cases.S_ot.notna().any()
    ev = SEC.evaluate(cases)
    assert ev['status'] == 'ok' and np.isfinite(ev['G'])


def _ridge_ref(X, y, lam):
    """Brute force: standardise (population sd), drop constant columns, centre, solve the normal equations."""
    mu, sd = X.mean(0), X.std(0)
    k = sd > 0
    Z = (X[:, k] - mu[k]) / sd[k]
    n = len(y)
    b = np.linalg.solve(Z.T @ Z + n * lam * np.eye(k.sum()), Z.T @ (y - y.mean()))
    H = Z @ np.linalg.solve(Z.T @ Z + n * lam * np.eye(k.sum()), Z.T)
    fitted = y.mean() + Z @ b
    df = 1 + np.trace(H)
    return b, fitted, n * np.sum((y - fitted) ** 2) / (n - df) ** 2


def test_ridge_gcv_matches_brute_force():
    rng = np.random.default_rng(5)
    X = np.column_stack([rng.normal(size=(120, 4)), np.zeros(120)])
    y = X[:, :4] @ [1.0, 0.0, -0.5, 0.2] + rng.normal(size=120)
    grid = 10.0 ** np.arange(-3, 2.01, 0.25)
    lam, info = B.ridge_gcv(X, y, grid)
    ref = [_ridge_ref(X, y, g)[2] for g in grid]
    assert lam == pytest.approx(grid[int(np.argmin(ref))]) and info['gcv_min'] == pytest.approx(min(ref))
    assert info['n_columns'] == 4 and not info['at_grid_boundary']


def test_ridge_point_matches_brute_force(panel11, macro11):
    origin = pd.Period('2013Q4', freq='Q')
    pop = V.rolling_set_by_epoch(panel11, [origin])[origin]
    W, t = SEC._t2_wide(panel11, pop, origin)
    X, y, bank, xrow = B._ridge_design(W, t, 1, macro11)
    assert X.shape[1] == 3 + macro11.shape[1] + len(pop)               # r_t, r_(t-3), Q1, macro, bank dummies
    lam = 0.37
    r_hat, info = B.ridge_point(W, t, 1, macro11, lam)
    b, _, _ = _ridge_ref(X, y, lam)
    mu, sd = X.mean(0), X.std(0)
    k = sd > 0
    for i in range(len(pop)):
        x = xrow(i)
        if np.all(np.isfinite(x)):
            assert r_hat[i] == pytest.approx(y.mean() + ((x[k] - mu[k]) / sd[k]) @ b, rel=1e-8, abs=1e-8)
    assert not info['undefined'] and np.isfinite(r_hat).any()


def test_ridge_lambda_uses_burnin_only(panel11, macro11):
    origin = SEC.RIDGE_BURNIN_END
    pop = V.rolling_set_by_epoch(panel11, [origin])[origin]
    lam, info = SEC.ridge_lambda(panel11, macro11, pop)
    shocked = panel11.copy()
    later = shocked.quarter > origin
    shocked.loc[later, 'trading_revenue_q'] *= -7.0                      # anything after 2013Q4 cannot matter
    lam2, _ = SEC.ridge_lambda(shocked, macro11.assign(vix=np.where(macro11.index > origin, 1e3, macro11.vix)), pop)
    assert lam == lam2 and lam in B.RIDGE_LAMBDA_GRID and info['burnin_end'] == '2013Q4'


def test_ridge_point_mae_on_store(prim, panel11, macro11):
    cases, summ = SEC.ridge_point_mae(prim['store'], panel11, macro11, lam=1.0)
    assert summ['status'] == 'ok' and summ['n_targets'] == len(TARGETS)
    for k in ('mae_ridge', 'mae_bary', 'mae_bstar', 'gain_bary_vs_ridge', 'gain_bstar_vs_ridge'):
        assert np.isfinite(summ[k]), k
    g = cases.groupby('target_quarter')[['mae_ridge', 'mae_bary']].mean().sum()
    assert summ['gain_bary_vs_ridge'] == pytest.approx((g.mae_ridge - g.mae_bary) / g.mae_ridge)
