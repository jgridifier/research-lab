"""prereg §6.3 tests 5-8: barycenter = POT LP barycenter in 1-D; WAR geodesic; rank map; CRPS approximation."""
import numpy as np
import ot
import pytest
from scipy.stats import norm
from trading_ot import ot_bary, ot_war
from trading_ot.scoring import U99, quantile_crps, coverage, pit


def test_barycenter_equals_pot():
    """Quantile averaging vs POT's exact LP W2 barycenter on a common 1-D grid."""
    x = np.linspace(-6, 10, 321)
    a = norm.pdf(x, 0, 1)
    b = 0.6 * norm.pdf(x, 4, 0.7) + 0.4 * norm.pdf(x, 1, 1.5)
    a, b = a / a.sum(), b / b.sum()
    M = ot.dist(x.reshape(-1, 1), x.reshape(-1, 1), metric='sqeuclidean')
    M /= M.max()
    bary = ot.lp.barycenter(np.vstack([a, b]).T, M, np.array([0.5, 0.5]))
    cdf = np.cumsum(bary) / bary.sum()
    q_pot = np.interp(U99, cdf, x)
    qa = np.interp(U99, np.cumsum(a), x)
    qb = np.interp(U99, np.cumsum(b), x)
    q_avg = ot_bary.barycenter_1d(np.stack([qa[None], qb[None]]))[0]
    grid = x[1] - x[0]
    assert np.max(np.abs(q_pot - q_avg)) <= 2 * grid
    assert np.all(np.diff(q_avg) >= 0)


def test_widen_monotone_and_median_fixed():
    Q = np.sort(np.random.default_rng(1).normal(size=(5, 99)), axis=1)
    for s in ot_bary.S_GRID:
        W = ot_bary.widen(Q, s)
        assert np.all(np.diff(W, axis=1) >= -1e-12)
        np.testing.assert_allclose(W[:, 49], Q[:, 49])


def test_trim_and_select_s():
    assert ot_bary.trim_members({'B0': 1.0, 'B1': 1.2, 'B2': 1.3}) == ['B0', 'B1']
    assert ot_bary.trim_members({'B0': 1.0, 'B1': 2.0, 'B2': 3.0}) == ['B0', 'B1']    # keep >= 2
    rng = np.random.default_rng(0)
    y = rng.normal(0, 2, 500)
    Q = np.tile(norm.ppf(U99), (500, 1))                 # under-dispersed N(0,1) for N(0,4) data
    s, scores = ot_bary.select_s(Q, y, np.ones(500))
    assert s == 1.5


def test_linear_pool_quantiles_matches_mixture():
    Qa = norm.ppf(U99, 0, 1)[None]
    Qb = norm.ppf(U99, 3, 1)[None]
    lp = ot_bary.linear_pool_quantiles(np.stack([Qa, Qb]))[0]
    assert abs(lp[49] - 1.5) < 0.05                      # symmetric mixture median
    assert lp[89] - lp[9] > (Qa[0, 89] - Qa[0, 9]) * 1.5  # pool wider than the barycenter


def test_war_geodesic():
    rng = np.random.default_rng(2)
    Qs = np.sort(rng.normal(size=(12, 99)) * 50 + 80, axis=1)
    Qbar = ot_war.frechet_mean(Qs)
    np.testing.assert_allclose(ot_war.war_forecast(Qbar, Qs[-1], 0.0), Qbar)
    np.testing.assert_allclose(ot_war.war_forecast(Qbar, Qs[-1], 1.0), Qs[-1])
    for beta in [0.1, 0.5, 0.9]:
        assert np.all(np.diff(ot_war.war_forecast(Qbar, Qs[-1], beta)) >= 0)
    beta, raw, n = ot_war.war_beta(Qs, 1)
    assert 0 <= beta <= 1 and n == 11


def test_war_beta_recovers_ar_coefficient():
    rng = np.random.default_rng(3)
    base = np.sort(rng.normal(size=99))
    shape = np.linspace(-1, 1, 99)
    a, Qs = 0.0, []
    for _ in range(400):
        a = 0.6 * a + rng.normal(0, 1)
        Qs.append(base + a * 0.1 * (1 + shape))
    beta, raw, n = ot_war.war_beta(np.array(Qs), 1)
    assert abs(beta - 0.6) < 0.1


def test_rankmap():
    Qhat = norm.ppf(U99, 80, 40)
    z = np.array([-1.5, 0.0, 2.0])
    for rho in [0.0, 0.3, 0.9]:
        q = ot_war.rankmap_quantiles(Qhat, z, rho)
        assert np.all(np.diff(q, axis=1) >= -1e-12)
    np.testing.assert_allclose(ot_war.rankmap_quantiles(Qhat, z, 0.0), np.tile(Qhat, (3, 1)), atol=1e-9)
    q = ot_war.rankmap_quantiles(Qhat, z, 0.999999)
    target = np.interp(norm.cdf(z), U99, Qhat)
    assert np.max(np.abs(q - target[:, None])) < 0.5
    assert np.ptp(q, axis=1).max() < 1.0


def test_crps_quantile_approx():
    """The U99 approximation over-states N(0,1) CRPS by a near-constant ~1% (it cancels in relative gains).

    Expected CRPS over y ~ N(0,1) and pointwise values for |y| <= 1 are within 1%;
    pointwise out to |y| = 3 the gap is at most 1.1% (1.01% at |y| = 2, 1.03% at 2.5).
    """
    exact = lambda y: y * (2 * norm.cdf(y) - 1) + 2 * norm.pdf(y) - 1 / np.sqrt(np.pi)
    Q = norm.ppf(U99)[None]
    for y in [-1.0, -0.5, 0.0, 0.7, 1.0]:
        assert abs(quantile_crps(Q, np.array([y]))[0] / exact(y) - 1) < 0.01, y
    for y in [-3.0, -2.0, -1.5, 1.5, 1.75, 2.5, 3.0]:
        assert abs(quantile_crps(Q, np.array([y]))[0] / exact(y) - 1) < 0.011, y
    ys = norm.rvs(size=100000, random_state=1)
    ratio = quantile_crps(np.tile(Q, (len(ys), 1)), ys).mean() / exact(ys).mean()
    assert abs(ratio - 1) < 0.01


def test_coverage_and_pit():
    Q = np.tile(norm.ppf(U99), (3, 1))
    cov = coverage(Q, np.array([0.0, 1.7, -1.6]))
    assert cov.tolist() == [True, False, True]
    assert abs(pit(Q, np.array([0.0]))[0] - 0.5) < 1e-9
