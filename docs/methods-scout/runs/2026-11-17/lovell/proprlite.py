"""proprlite: proportionality (Lovell et al. 2015; Quinn et al. 2017 formulas) with a persistence-aware null.

Engineering avenue for scout issue #53 (2026-11-17). Pure NumPy, no neural nets. Functions:
  clr, vlr, phi, rho, pairwise_rho (vectorised), partial_level, partial_increment,
  cyclic_shift_pvalue (exact, all relative shifts in [smin, T-smin]), bh.
rho on any log-ratio-like vectors u, v:  rho = 1 - var(u - v) / (var u + var v) = 2 cov(u, v) / (var u + var v).
"""
import numpy as np


def clr(M):
    L = np.log(np.asarray(M, float))
    return L - L.mean(axis=1, keepdims=True)


def _svar(x):
    return np.var(x, ddof=1)


def vlr(x, y):
    return _svar(np.log(x) - np.log(y))


def phi(x, y):
    return vlr(x, y) / _svar(np.log(x))


def rho(x, y):
    """Lovell rho on two positive vectors (log taken here)."""
    lx, ly = np.log(x), np.log(y)
    return 1.0 - _svar(lx - ly) / (_svar(lx) + _svar(ly))


def rho_vec(u, v):
    """rho on vectors already on the log scale (clr coordinates, residuals, increments)."""
    return 1.0 - _svar(u - v) / (_svar(u) + _svar(v))


def pairwise_rho(L):
    """All pairwise rho for a T x D matrix of log-scale columns, vectorised: 2 cov_ij / (v_i + v_j)."""
    L = np.asarray(L, float)
    C = np.cov(L, rowvar=False, ddof=1)
    v = np.diag(C)
    R = 2.0 * C / (v[:, None] + v[None, :])
    np.fill_diagonal(R, 1.0)
    return R


def _resid(Y, Z):
    b, *_ = np.linalg.lstsq(Z, Y, rcond=None)
    return Y - Z @ b


def partial_level(S, X):
    """Residualise clr levels on [1, X] (the 2026-11-12 prototype '2c'). Returns T x D residuals."""
    C = clr(S)
    Z = np.column_stack([np.ones(len(C)), X])
    return _resid(C, Z)


def partial_increment(S, X):
    """Residualise clr increments on [1, dX]. Returns (T-1) x D residual increments."""
    dC = np.diff(clr(S), axis=0)
    dX = np.diff(np.asarray(X, float), axis=0)
    Z = np.column_stack([np.ones(len(dC)), dX])
    return _resid(dC, Z)


def cyclic_shift_pvalue(u, v, smin=4):
    """Two-sided exact cyclic-shift p for rho_vec(u, v): shift v by every s in [smin, n - smin]."""
    obs = rho_vec(u, v)
    n = len(u)
    shifts = range(smin, n - smin + 1)
    null = np.array([rho_vec(u, np.roll(v, s)) for s in shifts])
    p = (1 + np.sum(np.abs(null) >= abs(obs))) / (1 + len(null))
    return obs, float(p), null


def bh(p):
    p = np.asarray(p, float)
    n = len(p)
    o = np.argsort(p)
    q = p[o] * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty(n)
    out[o] = np.minimum(q, 1)
    return out
