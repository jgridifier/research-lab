"""pimfast: streaming within-block logit PIM fitter + firm-clustered (dyadic) variance. Prototype (numpy).
2026-11-17, research-lab #63, PREREG.md section E. Oracle: R pim 2.0.4 (link='logit', model='difference')."""
import numpy as np
from scipy.special import expit


def within_pairs(year):
    """Same order as R's within_pairs(): split by sorted year, combn order (i<j)."""
    year = np.asarray(year); out = []
    for y in np.unique(year):
        ix = np.flatnonzero(year == y)
        if len(ix) > 1:
            a, b = np.triu_indices(len(ix), 1); out.append(np.c_[ix[a], ix[b]])
    return np.vstack(out)


def pseudo(Y, pairs):
    yi, yj = Y[pairs[:, 0]], Y[pairs[:, 1]]
    return (yi < yj) + 0.5 * (yi == yj)


def fit(X, Y, pairs, tol=1e-12, maxit=50):
    X = np.asarray(X, float).reshape(len(Y), -1)
    Z = X[pairs[:, 1]] - X[pairs[:, 0]]; I = pseudo(np.asarray(Y, float), pairs)
    b = np.zeros(Z.shape[1])
    for _ in range(maxit):
        p = expit(Z @ b); U = Z.T @ (I - p); H = (Z * (p * (1 - p))[:, None]).T @ Z
        step = np.linalg.solve(H, U); b += step
        if np.max(np.abs(U)) < tol and np.max(np.abs(step)) < 1e-14: break
    p = expit(Z @ b)
    return dict(beta=b, Z=Z, I=I, p=p, A=(Z * (p * (1 - p))[:, None]).T @ Z, u=Z * (I - p)[:, None])


def _meat(u, pairs, gid):
    """sum_g S_g S_g' - sum_{unordered group pairs} V V'. gid maps rows -> cluster id."""
    g1, g2 = gid[pairs[:, 0]], gid[pairs[:, 1]]
    G = int(max(g1.max(), g2.max())) + 1; k = u.shape[1]
    S = np.zeros((G, k)); np.add.at(S, g1, u); np.add.at(S, g2, u)
    lo, hi = np.minimum(g1, g2), np.maximum(g1, g2); key = lo * G + hi
    _, inv = np.unique(key, return_inverse=True); V = np.zeros((inv.max() + 1, k)); np.add.at(V, inv, u)
    return S.T @ S - V.T @ V


def vcov_sandwich(f, pairs):
    """pim's default sandwich: clusters = observations (firm-years)."""
    n = int(pairs.max()) + 1; Ai = np.linalg.inv(f['A'])
    return Ai @ _meat(f['u'], pairs, np.arange(n)) @ Ai


def vcov_firm(f, pairs, firm, small=True):
    _, gid = np.unique(firm, return_inverse=True); G = gid.max() + 1; Ai = np.linalg.inv(f['A'])
    c = G / (G - 1) if small else 1.0
    return c * Ai @ _meat(f['u'], pairs, gid) @ Ai


def perm_fit(X, Y, year, nperm, seed=0, chunk=2000, tol=1e-10, maxit=30):
    """Within-year permutations of Y (equivalently of X rows) solved together by batched Newton. Z fixed."""
    rng = np.random.default_rng(seed); X = np.asarray(X, float).reshape(len(Y), -1); Y = np.asarray(Y, float)
    pairs = within_pairs(year); Z = X[pairs[:, 1]] - X[pairs[:, 0]]; k = Z.shape[1]
    ZZ = (Z[:, :, None] * Z[:, None, :]).reshape(len(Z), k * k)
    blocks = [np.flatnonzero(year == y) for y in np.unique(year)]
    out = np.empty((nperm, k)); iters = 0
    for s in range(0, nperm, chunk):
        m = min(chunk, nperm - s); Yp = np.repeat(Y[None, :], m, 0)
        for ix in blocks:
            Yp[:, ix] = np.take_along_axis(Yp[:, ix], rng.random((m, len(ix))).argsort(1), 1)
        I = (Yp[:, pairs[:, 0]] < Yp[:, pairs[:, 1]]) + 0.5 * (Yp[:, pairs[:, 0]] == Yp[:, pairs[:, 1]])
        b = np.zeros((m, k))
        for it in range(maxit):
            p = expit(b @ Z.T); U = (I - p) @ Z; H = ((p * (1 - p)) @ ZZ).reshape(m, k, k)
            b += np.linalg.solve(H, U[:, :, None])[:, :, 0]; iters += 1
            if np.max(np.abs(U)) < tol: break
        p = expit(b @ Z.T); assert np.max(np.abs((I - p) @ Z)) < tol, 'not converged'
        out[s:s + m] = b
    return out, iters
