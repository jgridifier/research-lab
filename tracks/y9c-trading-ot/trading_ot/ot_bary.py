"""§4 layer: 1-D W2 barycenters of predictive distributions (prereg §4.1).

In 1-D, W2^2(F, G) = int_0^1 (F^-1(u) - G^-1(u))^2 du, so the weighted W2
barycenter of quantile functions Q_k is the weighted average sum_k w_k Q_k
(quantile averaging). It differs from the linear pool sum_k w_k F_k.
"""
import numpy as np
from scipy.optimize import minimize

from .scoring import U99, quantile_crps

TRIM_RATIO = 1.25
S_GRID = (1.00, 1.10, 1.20, 1.35, 1.50)


def barycenter_1d(Qs, w=None):
    """Qs: (K, n, L) member quantiles; w: (K,) weights (default equal). Returns (n, L)."""
    Qs = np.asarray(Qs, float)
    w = np.full(Qs.shape[0], 1 / Qs.shape[0]) if w is None else np.asarray(w, float)
    return np.tensordot(w, Qs, axes=1)


def widen(Q, s, taus=U99):
    """Q_s(tau) = Q(0.5) + s (Q(tau) - Q(0.5)); monotone for s > 0."""
    Q = np.asarray(Q, float)
    med = Q[..., int(np.flatnonzero(np.isclose(taus, 0.5))[0])][..., None]
    return med + s * (Q - med)


def trim_members(burnin_scores, ratio=TRIM_RATIO, min_keep=2):
    """Drop members whose pooled scaled CRPS exceeds ratio x the best member's; keep at least min_keep.

    burnin_scores: {member: pooled mean scaled CRPS}. Returns kept members in input order.
    """
    best = min(burnin_scores.values())
    kept = [m for m, v in burnin_scores.items() if v <= ratio * best]
    if len(kept) < min_keep:
        kept = sorted(burnin_scores, key=burnin_scores.get)[:min_keep]
        kept = [m for m in burnin_scores if m in kept]
    return kept


def select_s(Q_bar, y, scale, grid=S_GRID):
    """argmin over grid of pooled mean scaled CRPS of widen(Q_bar, s); ties -> smallest s.

    Returns (s, {s: score})."""
    scores = {s: float(np.mean(quantile_crps(widen(Q_bar, s), y) / scale)) for s in grid}
    best = min(scores.values())
    return next(s for s in grid if scores[s] == best), scores


def mixture_cdf(Qs, w, x, taus=U99):
    """Linear-pool CDF sum_k w_k F_k(x) with each F_k the piecewise-linear CDF of its quantiles (flat tails)."""
    total = 0.0
    for wk, q in zip(w, Qs):
        if x < q[0]:
            Fk = 0.0
        elif x >= q[-1]:
            Fk = 1.0
        else:
            qq, idx = np.unique(q, return_index=True)
            Fk = float(np.interp(x, qq, taus[idx]))
            # map the interior onto [taus[0], taus[-1]]; mass below/above the end quantiles is at the ends
        total += wk * Fk
    return total


def linear_pool_quantiles(Qs, w=None, taus=U99, tol=1e-9, iters=200):
    """Quantiles of the linear pool by bisection on the mixture CDF. Qs: (K, n, L) -> (n, L)."""
    Qs = np.asarray(Qs, float)
    K, n, L = Qs.shape
    w = np.full(K, 1 / K) if w is None else np.asarray(w, float)
    out = np.empty((n, L))
    for i in range(n):
        members = Qs[:, i, :]
        lo0, hi0 = members.min(), members.max()
        for j, tau in enumerate(taus):
            lo, hi = lo0, hi0
            for _ in range(iters):
                mid = 0.5 * (lo + hi)
                if mixture_cdf(members, w, mid, taus) < tau:
                    lo = mid
                else:
                    hi = mid
                if hi - lo <= tol * max(1.0, abs(mid)):
                    break
            out[i, j] = hi
        out[i] = np.maximum.accumulate(out[i])
    return out


def crps_optimal_weights(Qs, y, scale):
    """lambda_hat = argmin_{simplex} pooled mean scaled CRPS of the weighted barycenter (SLSQP)."""
    Qs = np.asarray(Qs, float)
    K = Qs.shape[0]
    f = lambda w: float(np.mean(quantile_crps(barycenter_1d(Qs, w), y) / scale))
    res = minimize(f, np.full(K, 1 / K), method='SLSQP', bounds=[(0, 1)] * K,
                   constraints=[{'type': 'eq', 'fun': lambda w: w.sum() - 1}])
    w = np.clip(res.x, 0, None)
    return w / w.sum()


def shrunk_weights(Qs, y, scale, n0=200):
    """H1b: lambda_t = (1 - kappa) / |M| + kappa lambda_hat, kappa = n / (n + n0)."""
    K = np.asarray(Qs).shape[0]
    n = len(y)
    kappa = n / (n + n0)
    lam_hat = crps_optimal_weights(Qs, y, scale) if n else np.full(K, 1 / K)
    return (1 - kappa) * np.full(K, 1 / K) + kappa * lam_hat, dict(kappa=kappa, lambda_hat=lam_hat.tolist(), n=n)
