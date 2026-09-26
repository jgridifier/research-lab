"""Liu–Moon–Schorfheide Gaussian CRE QMLE and parametric Tweedie forecasts.

Integrated likelihood: LMS (NBER w25102), eq. 24. Sufficient-statistic
posterior mean and score correction: eqs. 17, 20 and 30. Variance parameters
are profiled with the omega² >= 0 boundary; no clipping of data or forecasts.
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

GRADIENT_TOL = 1e-5


def seasonal_regressors(quarters):
    q = pd.PeriodIndex(quarters, freq='Q').quarter.to_numpy()
    return (q[:, None] == np.arange(1, 4)).astype(float) - 0.25


def profile_loglik(rho, alpha, Y, Ylag, S, y0):
    """Profile LMS eq. 24 (omitting the common Gaussian normalizer)."""
    N, T = Y.shape
    ytil = Y - rho * Ylag - S @ np.asarray(alpha)
    lam_hat = ytil.mean(axis=1)
    W = float(np.sum((ytil - lam_hat[:, None]) ** 2))
    z = np.column_stack([np.ones(N), y0])
    phi = np.linalg.lstsq(z, lam_hat, rcond=None)[0]
    prior_mean = z @ phi
    E = float(np.sum((lam_hat - prior_mean) ** 2))
    sigma2 = W / (N * (T - 1))
    v = E / N
    if v >= sigma2 / T:
        omega2 = v - sigma2 / T
    else:
        omega2 = 0.0
        sigma2 = (W + T * E) / (N * T)
        v = sigma2 / T
    loglik = (-N * (T - 1) / 2 * np.log(sigma2) - W / (2 * sigma2)
              - N / 2 * np.log(v) - E / (2 * v)) if sigma2 > 0 and v > 0 else -np.inf
    return dict(loglik=float(loglik), sigma2=float(sigma2), omega2=float(omega2),
                v=float(v), W=W, E=E, phi=phi, phi0=float(phi[0]), phi1=float(phi[1]),
                lam_hat=lam_hat, prior_mean=prior_mean, N=N, T=T)


def gaussian_score(x, mean, var):
    """Derivative of log N(mean, var) with respect to x."""
    return -(np.asarray(x) - mean) / var


def tweedie_posterior_mean(lam_hat, scale, score):
    """LMS eqs. 17/20/30: scale is the sampling variance sigma²/T."""
    return np.asarray(lam_hat) + scale * score


def fit_qmle(Y, Ylag, S, y0):
    """Maximize the integrated likelihood from within and pooled OLS starts.

    No bounds are imposed on rho or seasonal coefficients. Divide the objective
    by N*T for numerical conditioning; the reported likelihood is unscaled.
    A failed fit is an error, not an additional unregistered fallback rule.
    """
    Y, Ylag, S, y0 = [np.asarray(a, dtype=float) for a in (Y, Ylag, S, y0)]
    if Y.ndim != 2:
        raise ValueError('Y must be N x T')
    N, T = Y.shape
    if N < 3 or T < 2 or Ylag.shape != Y.shape or S.shape != (T, 3) or y0.shape != (N,):
        raise ValueError('Require N >= 3, T >= 2 and aligned Y, Ylag, S, y0')
    if not all(np.isfinite(a).all() for a in (Y, Ylag, S, y0)):
        raise ValueError('QMLE inputs must be finite')
    regressors = np.concatenate([Ylag[..., None], np.broadcast_to(S, (N, T, 3))], axis=2)
    within_x = regressors - regressors.mean(axis=1, keepdims=True)
    within_y = Y - Y.mean(axis=1, keepdims=True)
    within = np.linalg.lstsq(within_x.reshape(-1, 4), within_y.ravel(), rcond=None)[0]
    pooled_x = np.column_stack([np.ones(N * T), regressors.reshape(-1, 4)])
    pooled = np.linalg.lstsq(pooled_x, Y.ravel(), rcond=None)[0][1:]

    def objective(theta):
        return -profile_loglik(theta[0], theta[1:], Y, Ylag, S, y0)['loglik'] / (N * T)

    # BFGS can stop with "precision loss" at an optimum; accept a finite point
    # whose gradient of the (N*T-scaled) objective is numerically zero. The
    # winning start and how it was accepted are recorded with the fit.
    fits = []
    for label, start in (('within', within), ('pooled', pooled)):
        f = minimize(objective, start, method='BFGS', options={'gtol': 1e-7, 'maxiter': 1000})
        if not (np.isfinite(getattr(f, 'fun', np.nan)) and np.isfinite(getattr(f, 'x', np.nan)).all()):
            continue
        max_grad = float(np.max(np.abs(getattr(f, 'jac', np.inf))))
        if f.success or max_grad < GRADIENT_TOL:
            fits.append((label, f, max_grad))
    if not fits:
        raise ValueError('Neither QMLE starting point converged to a finite optimum')
    label, best, max_grad = min(fits, key=lambda item: item[1].fun)
    theta = best.x
    pieces = profile_loglik(theta[0], theta[1:], Y, Ylag, S, y0)
    scale = pieces['sigma2'] / T
    var = pieces['omega2'] + scale
    post = tweedie_posterior_mean(pieces['lam_hat'], scale,
                                gaussian_score(pieces['lam_hat'], pieces['prior_mean'], var))
    result = dict(rho=float(theta[0]), alpha=theta[1:].tolist(),
                  **{k: pieces[k] for k in ['sigma2', 'phi0', 'phi1', 'omega2', 'loglik', 'N', 'T',
                                           'lam_hat', 'prior_mean']},
                  post_mean=post, shrinkage=float(scale / var))
    if not all(np.isfinite(np.asarray(v)).all() for v in result.values()):
        raise ValueError('Nonfinite QMLE result')
    result.update(optimizer_start=label, optimizer_success=bool(best.success),
                  optimizer_message=str(getattr(best, 'message', '')), optimizer_max_abs_grad=max_grad,
                  optimizer_accepted_by='success' if best.success else f'gradient<{GRADIENT_TOL:g}',
                  optimizer_starts_converged=[item[0] for item in fits])
    return result


def asset_ratio(panel, column):
    """Annualized percent of previous calendar-quarter assets; never bridge gaps."""
    data = panel[['rssd_id', 'report_date', 'total_assets', column]].copy()
    data['quarter'] = data.report_date.dt.to_period('Q')
    data = data.set_index(['rssd_id', 'quarter']).sort_index()
    ids, quarters = (data.index.get_level_values(k) for k in ['rssd_id', 'quarter'])
    previous = pd.MultiIndex.from_arrays([ids, quarters - 1], names=data.index.names)
    lag_assets = data.total_assets.reindex(previous).to_numpy()
    lag_assets = np.where(lag_assets > 0, lag_assets, np.nan)
    return pd.DataFrame({'y': 400 * data[column] / lag_assets,
                         'X': data[column], 'A': data.total_assets}, index=data.index)


def eb_forecast_origin(panel_or_ratio, origin, universe_ids, column, T=12):
    """Fit on the origin-selected cross-section, independent of target availability.

    Hard truncation precedes all transformation and estimation. A ratio input
    must be the output of asset_ratio (calendar-keyed, with y, X and current A).
    Only missing-window banks receive no prediction; failed estimation raises.
    """
    origin = pd.Period(origin, freq='Q')
    if 'report_date' in panel_or_ratio:
        history = panel_or_ratio.loc[panel_or_ratio.report_date.dt.to_period('Q').le(origin)]
        ratio = asset_ratio(history, column)
    else:
        ratio = panel_or_ratio.loc[panel_or_ratio.index.get_level_values('quarter') <= origin].copy()
    ids = pd.Index(sorted(set(universe_ids)), name='rssd_id')
    quarters = pd.period_range(origin - T, origin, freq='Q')
    keys = pd.MultiIndex.from_product([ids, quarters], names=['rssd_id', 'quarter'])
    window = ratio.y.reindex(keys).to_numpy().reshape(len(ids), T + 1)
    complete = ~np.isnan(window).any(axis=1)
    used_ids, window = ids[complete], window[complete]
    fit = fit_qmle(window[:, 1:], window[:, :-1], seasonal_regressors(quarters[1:]), window[:, 0])
    next_s = seasonal_regressors([origin + 1])[0]
    yhat = fit['post_mean'] + fit['rho'] * window[:, -1] + next_s @ fit['alpha']
    assets = ratio.A.reindex(pd.MultiIndex.from_arrays([used_ids, [origin] * len(used_ids)],
                                                     names=ratio.index.names)).to_numpy()
    if not (np.isfinite(assets).all() and (assets > 0).all()):
        raise ValueError(f'{origin}: origin assets missing or non-positive for an estimated bank')
    forecast = pd.DataFrame({'rssd_id': used_ids, 'eb_panel': yhat * assets / 400,
                             'shrinkage': fit['shrinkage']})
    if not np.isfinite(forecast.eb_panel).all():
        raise ValueError(f'{origin}: nonfinite EB forecast; no clipping or silent case removal')
    params = {k: fit[k] for k in ['rho', 'alpha', 'sigma2', 'phi0', 'phi1', 'omega2',
                                 'shrinkage', 'N', 'T', 'loglik', 'optimizer_start', 'optimizer_success',
                                 'optimizer_message', 'optimizer_max_abs_grad', 'optimizer_accepted_by']}
    used = ratio.loc[ratio.index.get_level_values('rssd_id').isin(used_ids)
                     & ratio.index.get_level_values('quarter').isin(quarters)]
    # Latest report quarter of any value that entered estimation or scaling
    # (y at the window end uses X_t and A_(t-1); the level forecast uses A_t).
    params.update(n_universe=len(ids), n_excluded_incomplete_window=int((~complete).sum()),
                  data_last_quarter=str(used.index.get_level_values('quarter').max()),
                  history_last_quarter=str(ratio.index.get_level_values('quarter').max()))
    return forecast, params
