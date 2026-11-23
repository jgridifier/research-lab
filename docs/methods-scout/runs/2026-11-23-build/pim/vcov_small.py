"""Small-sample variance options for the pim prototype (research code, 2026-11-23, PREREG-P3.md).
Builds on runs/2026-11-17/pim2/pimfast.py (fit, within_pairs, _meat, vcov_firm)."""
import numpy as np, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '2026-11-17', 'pim2'))
from pimfast import within_pairs, fit, vcov_sandwich, vcov_firm, _meat

def _isqrt_apply(M, rt):
    """(I - M M')^{-1/2} rt via the k x k eigenproblem of M'M (exact rank-k update)."""
    G = M.T @ M; lam, Q = np.linalg.eigh(G)
    lam = np.clip(lam, 0, 1 - 1e-12)
    coef = np.where(lam > 1e-15, (1 / np.sqrt(1 - lam) - 1) / np.where(lam > 1e-15, lam, 1), 0.5)
    return rt + M @ (Q @ (coef * (Q.T @ (M.T @ rt))))

def _groups(keys):
    o = np.argsort(keys, kind='stable'); k = keys[o]; cut = np.flatnonzero(np.diff(k)) + 1
    return np.split(o, cut)

def meat_cr2(f, pairs, firm, adjust=True):
    Z = f['Z']; w = f['p'] * (1 - f['p']); r = f['I'] - f['p']; k = Z.shape[1]
    Ai = np.linalg.inv(f['A']); ev, EV = np.linalg.eigh(f['A']); Aih = EV @ np.diag(ev ** -0.5) @ EV.T
    sw = np.sqrt(w); rt = r / sw
    _, gid = np.unique(firm, return_inverse=True); g1, g2 = gid[pairs[:, 0]], gid[pairs[:, 1]]; Gn = gid.max() + 1
    def S(ix):
        if not adjust: return Z[ix].T @ r[ix]
        M = (sw[ix, None] * Z[ix]) @ Aih
        return (Z[ix] * sw[ix, None]).T @ _isqrt_apply(M, rt[ix])
    B = np.zeros((k, k))
    for fidx in range(Gn):
        ix = np.flatnonzero((g1 == fidx) | (g2 == fidx))
        if len(ix): s = S(ix); B += np.outer(s, s)
    lo, hi = np.minimum(g1, g2), np.maximum(g1, g2)
    for ix in _groups(lo * Gn + hi):
        v = S(ix); B -= np.outer(v, v)
    return B

def vcov_cr2(f, pairs, firm):
    Ai = np.linalg.inv(f['A']); return Ai @ meat_cr2(f, pairs, firm) @ Ai

def score_wild(f, pairs, firm, B=399, rng=None, level=0.95):
    """q_{level}(|t*|) for the first coefficient; t* = [A^-1 U*]_1 / se_firm(u*)."""
    _, gid = np.unique(firm, return_inverse=True); G = gid.max() + 1
    g1, g2 = gid[pairs[:, 0]], gid[pairs[:, 1]]; Ai = np.linalg.inv(f['A']); u = f['u']; c = G / (G - 1)
    ts = np.empty(B)
    for b in range(B):
        e = rng.choice([-1.0, 1.0], G); us = (e[g1] + e[g2])[:, None] * u
        bs = Ai @ us.sum(0); V = c * Ai @ _meat(us, pairs, gid) @ Ai
        ts[b] = bs[0] / np.sqrt(V[0, 0])
    return float(np.quantile(np.abs(ts), level))

def vcov_jack(X, Y, year, firm):
    fs = np.unique(firm); bs = []
    for fo in fs:
        keep = firm != fo; yk = year[keep]; o = np.argsort(yk, kind='stable')
        xk = np.asarray(X)[keep][o]; Yk = np.asarray(Y)[keep][o]
        bs.append(fit(xk, Yk, within_pairs(yk[o]))['beta'])
    bs = np.array(bs); G = len(fs)
    d = bs - bs.mean(0); return (G - 1) / G * d.T @ d
