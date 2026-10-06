"""Quantile-based scores (prereg §5.2). Quantile arrays have shape (n, K) on a grid of levels."""
import numpy as np

U99 = np.round(np.arange(1, 100) / 100, 2)
U19 = np.round(np.arange(1, 20) / 20, 2)
U19_IDX = np.array([int(round(u * 100)) - 1 for u in U19])   # positions of U19 inside U99


def pinball(Q, y, taus):
    """rho_tau(y - Q(tau)) for each level; returns (n, K)."""
    Q, y, taus = np.atleast_2d(np.asarray(Q, float)), np.asarray(y, float).reshape(-1, 1), np.asarray(taus, float)
    u = y - Q
    return u * (taus - (u < 0))


def quantile_crps(Q, y, taus=U99):
    """CRPS(F, y) ~= (2/K) sum_tau rho_tau(y - Q(tau)); (n,) array."""
    return 2.0 * pinball(Q, y, taus).mean(axis=1)


def coverage(Q, y, level=0.9, taus=U99):
    """Indicator that y lies in the central `level` interval [Q((1-l)/2), Q((1+l)/2)]."""
    taus = np.round(np.asarray(taus), 4)
    lo, hi = np.round((1 - level) / 2, 4), np.round((1 + level) / 2, 4)
    i, j = int(np.flatnonzero(taus == lo)[0]), int(np.flatnonzero(taus == hi)[0])
    Q, y = np.atleast_2d(Q), np.asarray(y, float)
    return (y >= Q[:, i]) & (y <= Q[:, j])


def pit(Q, y, taus=U99):
    """Randomisation-free PIT: interpolated CDF value of y under the quantile function (0..1, flat tails)."""
    Q, y = np.atleast_2d(Q), np.asarray(y, float)
    out = np.empty(len(y))
    for k, (q, v) in enumerate(zip(Q, y)):
        if v <= q[0]:
            out[k] = 0.0 if v < q[0] else taus[0]
        elif v >= q[-1]:
            out[k] = 1.0 if v > q[-1] else taus[-1]
        else:
            qq, idx = np.unique(q, return_index=True)
            out[k] = float(np.interp(v, qq, np.asarray(taus)[idx]))
    return out


def energy_score(samples, y):
    """Energy score ES = E||X - y|| - 0.5 E||X - X'|| from an (M, d) sample (Gneiting & Raftery 2007)."""
    X, y = np.asarray(samples, float), np.asarray(y, float)
    t1 = np.linalg.norm(X - y, axis=1).mean()
    # unbiased-enough pairing: compare with a shifted copy (M pairs) for O(M) cost
    t2 = np.linalg.norm(X - np.roll(X, 1, axis=0), axis=1).mean()
    return float(t1 - 0.5 * t2)


def trimmed_w2sq(Qa, Qb, idx=U19_IDX):
    """Trimmed W2^2 on U19: mean over the 19 inner levels of (Qa - Qb)^2."""
    Qa, Qb = np.asarray(Qa, float), np.asarray(Qb, float)
    return float(np.mean((Qa[..., idx] - Qb[..., idx]) ** 2))


# ── v1.1 case scale (addendum §2.4) ─────────────────────────────────────────
MAD_K = 1.4826


def raw_case_scale(panel, banks, origin, window=16, min_obs=12, column='trading_revenue_q'):
    """1.4826 x MAD of each bank's A220_q over the `window` quarters ending at origin; NaN if < min_obs values.

    Uses only rows with origin-window < quarter <= origin (pre-sample rows are NaN after the mask).
    """
    import pandas as pd
    o = pd.Period(origin, freq='Q')
    w = panel[panel.quarter.between(o - (window - 1), o) & panel.rssd_id.isin(list(banks))]
    out = np.full(len(banks), np.nan)
    groups = {k: g[column].to_numpy(float) for k, g in w.groupby('rssd_id')}
    for k, b in enumerate(banks):
        x = groups.get(b, np.array([]))
        x = x[np.isfinite(x)]
        if len(x) >= min_obs:
            out[k] = MAD_K * np.median(np.abs(x - np.median(x)))
    return out


def case_scale(panel, banks, origin, set_, window=16, min_obs=12, floor_q=0.10, column='trading_revenue_q'):
    """s_i(o): raw trailing-window MAD floored at the floor_q quantile of raw s_j(o) over `set_` (the set in force).

    Banks with fewer than min_obs values get NaN (not scored at that origin; counted by the caller).
    """
    banks, set_ = list(banks), list(set_)
    raw_set = raw_case_scale(panel, set_, origin, window, min_obs, column)
    raw_set = raw_set[np.isfinite(raw_set)]
    floor = float(np.quantile(raw_set, floor_q)) if len(raw_set) else np.nan
    raw = raw_case_scale(panel, banks, origin, window, min_obs, column)
    return np.where(np.isfinite(raw), np.fmax(raw, floor), np.nan), floor
