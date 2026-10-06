"""§3 layer: Wasserstein autoregression of the cross-sectional quantile function + rank map (prereg §4.2).

In 1-D the log map at the Frechet mean is isometric to V_s = Q_s - Qbar in
L2(0,1), so a scalar WAR(1) V_(s+h) = beta V_s is a W2 geodesic step:
Qhat_(t+h) = (1 - beta) Qbar_t + beta Q_t (McCann interpolant at time beta).
"""
import numpy as np
import pandas as pd
from scipy.stats import norm

from .scoring import U19_IDX, U99


def cs_quantiles(r_values, taus=U99):
    """Empirical (type 7) quantile function of a cross-section of ratios."""
    return np.quantile(np.asarray(r_values, float), taus, method='linear')


def frechet_mean(Qs):
    """W2 Frechet mean of 1-D distributions = average of quantile functions."""
    return np.mean(np.asarray(Qs, float), axis=0)


def war_beta(Qs, h=1, grid_idx=U19_IDX):
    """beta_hat_h = clip(sum <V_(s+h), V_s> / sum <V_s, V_s>, 0, 1) over pairs inside the window.

    Qs: (S, L) quantile functions of consecutive quarters S_t (oldest first). Inner
    products use the trimmed grid U19. Returns (beta_clipped, beta_raw, n_pairs).
    """
    Qs = np.asarray(Qs, float)
    V = (Qs - frechet_mean(Qs))[:, grid_idx]
    if len(V) <= h:
        return np.nan, np.nan, 0
    num = float(np.sum(V[h:] * V[:-h]))
    den = float(np.sum(V[:-h] * V[:-h]))
    raw = num / den if den > 0 else np.nan
    return float(np.clip(raw, 0.0, 1.0)), raw, len(V) - h


def war_forecast(Qbar, Qt, beta):
    """Point at fraction beta along the W2 geodesic from Qbar to Q_t."""
    return (1 - beta) * np.asarray(Qbar, float) + beta * np.asarray(Qt, float)


def probit_ranks(values):
    """z = Phi^-1((rank - 0.5) / n) with average ranks for ties."""
    v = pd.Series(np.asarray(values, float))
    p = (v.rank(method='average').to_numpy() - 0.5) / len(v)
    return norm.ppf(p)


def rank_rho(pairs_now, pairs_next):
    """Pooled Pearson correlation of (z_(j,s+h), z_(j,s)), clipped to [0, 0.99]; returns (rho, raw, n)."""
    a, b = np.asarray(pairs_now, float), np.asarray(pairs_next, float)
    if len(a) < 3:
        return np.nan, np.nan, len(a)
    raw = float(np.corrcoef(a, b)[0, 1])
    return float(np.clip(raw, 0.0, 0.99)), raw, len(a)


def interp_quantile(Qhat, u, taus=U99):
    """Qhat interpolated linearly on U99 and held flat beyond [0.01, 0.99]."""
    return np.interp(u, taus, Qhat)


def rankmap_quantiles(Qhat, z, rho, taus=U99):
    """q_tau(r_i) = Qhat(Phi(rho z_i + sqrt(1 - rho^2) Phi^-1(tau))) for each bank; returns (n, L)."""
    z = np.atleast_1d(np.asarray(z, float))
    u = norm.cdf(rho * z[:, None] + np.sqrt(1 - rho ** 2) * norm.ppf(np.asarray(taus))[None, :])
    return interp_quantile(Qhat, u, taus)


def frechet_regression(Qnext, X, x_new):
    """Global Frechet (Wasserstein) regression in 1-D (Petersen & Muller 2019): weighted quantile average + isotonic projection.

    Qnext: (S, L) responses Q_(s+1); X: (S, p) predictors x_s; x_new: (p,).
    """
    from scipy.optimize import isotonic_regression
    X, Qnext = np.asarray(X, float), np.asarray(Qnext, float)
    xbar = X.mean(axis=0)
    Sig = np.atleast_2d(np.cov(X, rowvar=False, ddof=0))
    w = (1 + (X - xbar) @ np.linalg.solve(Sig, np.asarray(x_new, float) - xbar)) / len(X)
    q = w @ Qnext
    return isotonic_regression(q).x


def ot_recalibrate(Q, pits, taus=U99):
    """Q_rec(tau) = Q(G^-1(tau)), G the empirical CDF of past PITs (1-D monotone transport of the PIT law to U(0,1))."""
    g_inv = np.quantile(np.asarray(pits, float), taus, method='linear')
    return np.array([np.interp(g_inv, taus, q) for q in np.atleast_2d(Q)])


# ── v1.1 secondary / sensitivity helpers ────────────────────────────────────
def war_beta_pairs(Qd, Qbar, h=1, grid_idx=U19_IDX, q1_shift=False):
    """beta over pairs (s, s+h) both present in Qd {quarter: Q}; V_s = Q_s - Qbar, inner products on U19.

    q1_shift=True: joint least squares of V_(s+h) = beta V_s + delta 1[Q1(s+h)] (Frisch-Waugh: Q1-target pairs
    demeaned within the Q1 group), beta clipped to [0, 1], delta = mean_Q1(V_(s+h)) - beta mean_Q1(V_s) on U99.
    Returns (beta, beta_raw, n_pairs, delta or None)."""
    pairs = [(s, s + h) for s in Qd if (s + h) in Qd]
    if not pairs:
        return np.nan, np.nan, 0, None
    V = {s: np.asarray(Qd[s], float) - Qbar for s in Qd}
    Vx = np.stack([V[a] for a, _ in pairs])
    Vy = np.stack([V[b] for _, b in pairs])
    isq1 = np.array([b.quarter == 1 for _, b in pairs])
    X, Y = Vx[:, grid_idx].copy(), Vy[:, grid_idx].copy()
    if q1_shift and isq1.any():
        X[isq1] -= X[isq1].mean(axis=0)
        Y[isq1] -= Y[isq1].mean(axis=0)
    den = float(np.sum(X * X))
    raw = float(np.sum(X * Y)) / den if den > 0 else np.nan
    beta = float(np.clip(raw, 0.0, 1.0)) if np.isfinite(raw) else np.nan
    delta = None
    if q1_shift and isq1.any() and np.isfinite(beta):
        delta = Vy[isq1].mean(axis=0) - beta * Vx[isq1].mean(axis=0)
    return beta, raw, len(pairs), delta


def ar_map_forecast(Qd, origin, h=1, grid_idx=U19_IDX):
    """H2f, autoregressive OT-map (Zhu & Muller 2023), 1-D, scalar coefficient.

    T_s = Q_(s+1) o F_s is the optimal map from the quarter-s law to the quarter-(s+1) law; as a function of x its
    displacement is d_s(x) = T_s(x) - x, known at the knots x = Q_s(u) (d_s(Q_s(u)) = Q_(s+1)(u) - Q_s(u)) and
    interpolated linearly in x (held flat outside). Model: d_s(x) = alpha d_(s-1)(x), evaluated at x = Q_s(u),
    u in U19; alpha by least squares over consecutive triples, clipped to [-1, 1]. Forecast:
    Qhat_(t+1)(u) = Q_t(u) + alpha d_(t-1)(Q_t(u)), then isotonic projection. Requires h = 1 and >= 3 consecutive
    quarters ending at the origin; raises ValueError otherwise (the caller logs N/A).
    Returns (Qhat, dict(alpha, alpha_raw, n_pairs))."""
    from scipy.optimize import isotonic_regression
    if h != 1:
        raise ValueError('H2f is defined for h = 1 only')
    origin = pd.Period(origin, freq='Q')

    def disp(s):
        return np.asarray(Qd[s + 1], float) - np.asarray(Qd[s], float)

    def d_at(s, x):
        q = np.asarray(Qd[s], float)
        qq, idx = np.unique(q, return_index=True)
        return np.interp(x, qq, disp(s)[idx])

    num = den = 0.0
    n = 0
    for s in Qd:
        if s + 1 in Qd and s - 1 in Qd and s + 1 <= origin:
            x = np.asarray(Qd[s], float)[grid_idx]
            prev = d_at(s - 1, x)
            num += float(np.sum(disp(s)[grid_idx] * prev))
            den += float(np.sum(prev * prev))
            n += 1
    if origin not in Qd or origin - 1 not in Qd or n < 1 or not den > 0:
        raise ValueError(f'H2f: not enough consecutive cross-sections at {origin} (pairs={n})')
    raw = num / den
    alpha = float(np.clip(raw, -1.0, 1.0))
    Qt = np.asarray(Qd[origin], float)
    Qhat = isotonic_regression(Qt + alpha * d_at(origin - 1, Qt)).x
    return Qhat, dict(alpha=alpha, alpha_raw=float(raw), n_pairs=n)


def fpca_war_forecast(Qd, Qbar, origin, h=1, K=2, grid_idx=U19_IDX):
    """Secondary variant of prereg §4.2 Step 3: K = 2 FPCA functional WAR, isotonic projection.

    Tangent vectors V_s = Q_s - Qbar (the primary's Frechet mean and cross-sections, quarters <= origin). FPCA on
    the U19 grid (the inner product of Step 2): SVD of the (quarters x 19) matrix V[:, U19] = U S W'; scores
    xi_s = (U S)_(s, 1..K); eigenfunctions extended to U99 by phi_k = sum_s U_(s,k) V_s / S_k (equal to W_k on U19).
    Score dynamics: xi_(s+h) = A xi_s, A (K x K) by least squares over pairs with s + h <= origin, no intercept,
    unconstrained. Forecast Qhat = isotonic(Qbar + sum_k (A xi_origin)_k phi_k). Raises ValueError if fewer than
    K + 1 quarters, fewer than K pairs, or a singular design.
    Returns (Qhat, dict(A, spectral_radius, explained_share, n_pairs, n_quarters))."""
    from scipy.optimize import isotonic_regression
    origin = pd.Period(origin, freq='Q')
    qs = sorted(s for s in Qd if s <= origin)
    if origin not in Qd or len(qs) < K + 1:
        raise ValueError(f'FPCA-WAR: {len(qs)} cross-sections at {origin}')
    Qbar = np.asarray(Qbar, float)
    V = np.stack([np.asarray(Qd[s], float) - Qbar for s in qs])
    U, S, _ = np.linalg.svd(V[:, grid_idx], full_matrices=False)
    if len(S) < K or not S[K - 1] > 0:
        raise ValueError('FPCA-WAR: rank < K')
    xi = U[:, :K] * S[:K]
    phi = (U[:, :K] / S[:K]).T @ V                                   # (K, 99)
    pos = {s: k for k, s in enumerate(qs)}
    pairs = [(pos[s], pos[s + h]) for s in qs if s + h in pos and s + h <= origin]
    if len(pairs) < K:
        raise ValueError(f'FPCA-WAR: {len(pairs)} pairs < K')
    X = np.stack([xi[a] for a, _ in pairs])
    Y = np.stack([xi[b] for _, b in pairs])
    if np.linalg.matrix_rank(X) < K:
        raise ValueError('FPCA-WAR: singular score design')
    A = np.linalg.lstsq(X, Y, rcond=None)[0].T                        # xi_(s+h) = A xi_s
    xi_hat = A @ xi[pos[origin]]
    Qhat = isotonic_regression(Qbar + xi_hat @ phi).x
    return Qhat, dict(A=A.tolist(), spectral_radius=float(np.max(np.abs(np.linalg.eigvals(A)))),
                      explained_share=float(np.sum(S[:K] ** 2) / np.sum(S ** 2)), n_pairs=len(pairs),
                      n_quarters=len(qs))
