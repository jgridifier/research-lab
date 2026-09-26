import numpy as np
import pandas as pd
import pytest
from scipy.optimize import minimize
from statement_forecast.eb import (fit_qmle, profile_loglik, seasonal_regressors,
                                   gaussian_score, tweedie_posterior_mean)


def simulation(N=2000, T=12, omega=.5, seed=123):
    rng = np.random.default_rng(seed)
    rho, alpha = .6, np.array([.5, -.3, .2])
    lam = rng.normal(1, omega, N)
    quarters = pd.period_range('1900Q1', periods=400 + T + 1, freq='Q')
    seasons = seasonal_regressors(quarters)
    y = np.zeros((N, len(quarters)))
    for j in range(1, len(quarters)):
        y[:, j] = lam + rho * y[:, j-1] + seasons[j] @ alpha + rng.normal(size=N)
    block = y[:, -T-1:]
    # Stationary joint Gaussian: random-intercept variance plus AR shock variance.
    vy0 = omega**2 / (1-rho)**2 + 1 / (1-rho**2)
    cov = omega**2 / (1-rho)
    phi1 = cov / vy0
    # Deterministic seasonal mean, including its AR propagation.
    mean = 0.
    for j in range(1, len(quarters)-T):
        mean = 1 + rho * mean + seasons[j] @ alpha
    phi0 = 1 - phi1 * mean
    conditional_var = omega**2 - cov**2 / vy0
    return block[:, 1:], block[:, :-1], seasons[-T:], block[:, 0], lam, (phi0, phi1, conditional_var)


def test_recovery_and_oracle_shrinkage():
    Y, Ylag, S, y0, lam, (phi0, phi1, omega2) = simulation()
    fit = fit_qmle(Y, Ylag, S, y0)
    assert fit['rho'] == pytest.approx(.6, abs=.03)
    np.testing.assert_allclose(fit['alpha'], [.5, -.3, .2], atol=.08)
    assert fit['sigma2'] == pytest.approx(1, abs=.06)
    assert fit['phi0'] == pytest.approx(phi0, abs=.12)
    assert fit['phi1'] == pytest.approx(phi1, abs=.04)
    assert fit['omega2'] == pytest.approx(omega2, abs=.025)
    scale = 1 / Y.shape[1]
    oracle_lam = (Y - .6 * Ylag - S @ [.5, -.3, .2]).mean(axis=1)
    oracle = (omega2 * oracle_lam + scale * (phi0 + phi1 * y0)) / (omega2 + scale)
    assert fit['shrinkage'] == pytest.approx(scale / (omega2 + scale), abs=.05)
    assert np.corrcoef(fit['post_mean'], oracle)[0, 1] > .99
    assert np.mean((fit['post_mean'] - lam)**2) < np.mean((fit['lam_hat'] - lam)**2)


def test_gaussian_tweedie_closed_form():
    x = np.array([-3., 1., 7.]); mu = np.array([1., 2., 3.])
    omega2, scale = .3, .2
    actual = tweedie_posterior_mean(x, scale, gaussian_score(x, mu, omega2 + scale))
    np.testing.assert_allclose(actual, (omega2 * x + scale * mu) / (omega2 + scale))


def test_zero_prior_variance_boundary():
    Y, Ylag, S, y0, _, _ = simulation(omega=0, seed=12)
    fit = fit_qmle(Y, Ylag, S, y0)
    assert fit['shrinkage'] > .95
    assert fit['omega2'] < .005


@pytest.mark.parametrize('spread', [0., .8])
def test_profile_matches_direct_variance_and_phi_optimization(spread):
    rng = np.random.default_rng(84)
    N, T = 40, 5
    y0 = rng.normal(size=N)
    Y = 1 + .3*y0[:, None] + rng.normal(0, spread, (N, 1)) + rng.normal(size=(N, T))
    Ylag = np.zeros_like(Y); S = np.zeros((T, 3))
    prof = profile_loglik(0., np.zeros(3), Y, Ylag, S, y0)
    # Direct integrated Gaussian covariance, independent of the profile formula.
    def direct(theta):
        sigma2, omega2, p0, p1 = theta
        cov = sigma2*np.eye(T) + omega2*np.ones((T, T))
        resid = Y - (p0 + p1*y0)[:, None]
        return .5*N*np.linalg.slogdet(cov)[1] + .5*np.sum(resid*np.linalg.solve(cov, resid.T).T)
    fit = minimize(direct, [1., .1, 0., 0.], bounds=[(1e-8, None), (0., None), (None, None), (None, None)],
                   method='L-BFGS-B', options={'ftol': 1e-13, 'gtol': 1e-8})
    assert fit.success
    # Profile omits the determinant's constant N/2 log(T).
    assert -fit.fun == pytest.approx(prof['loglik'] - N/2*np.log(T), abs=1e-6)
    np.testing.assert_allclose(fit.x, [prof['sigma2'], prof['omega2'], prof['phi0'], prof['phi1']], atol=2e-5)


@pytest.mark.parametrize('N,T', [(2, 12), (5, 1)])
def test_minimum_dimensions(N, T):
    with pytest.raises(ValueError, match='N >= 3'):
        fit_qmle(np.ones((N,T)), np.ones((N,T)), np.zeros((T,3)), np.ones(N))


def test_nonfinite_and_optimizer_failure(monkeypatch):
    import statement_forecast.eb as eb
    Y, lag, S, y0, _, _ = simulation(N=30)
    Y[0, 0] = np.inf
    with pytest.raises(ValueError, match='finite'):
        fit_qmle(Y, lag, S, y0)
    Y[0, 0] = 1
    monkeypatch.setattr(eb, 'minimize', lambda *a, **kw: type('Fit', (), {'success': False})())
    with pytest.raises(ValueError, match='Neither'):
        fit_qmle(Y, lag, S, y0)
