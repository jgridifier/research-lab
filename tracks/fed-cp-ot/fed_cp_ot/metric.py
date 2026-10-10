"""Exact step-quantile arithmetic ported unchanged from the pinned burn-in script."""
import math
import numpy as np
EDGES = [(1,4), (5,9), (10,20), (21,40), (41,80), (81,270)]
X_LOG = np.array([math.log(math.sqrt(a*b)) for a,b in EDGES])
X_RANK = np.arange(6, dtype=float)
def q_from_p(p, x):
    p = np.asarray(p, float); k = p > 0; c = np.cumsum(p[k]) / p[k].sum(); c[-1] = 1.0
    return (c, x[k].astype(float))
def _merge(*qs):
    c = np.unique(np.concatenate([q[0] for q in qs])); c = c[c > 0]
    lens = np.diff(np.r_[0.0, c]); mids = c - lens / 2
    vals = [q[1][np.minimum(np.searchsorted(q[0], mids, side="left"), len(q[1]) - 1)] for q in qs]
    return c, lens, vals
def w2sq(q1, q2):
    _, l, (v1, v2) = _merge(q1, q2); return float(np.sum(l * (v1 - v2) ** 2))
def decomp(q1, q2):
    _, l, (v1, v2) = _merge(q1, q2)
    m1, m2 = np.sum(l * v1), np.sum(l * v2)
    s1, s2 = math.sqrt(max(np.sum(l * (v1 - m1) ** 2), 0)), math.sqrt(max(np.sum(l * (v2 - m2) ** 2), 0))
    cov = np.sum(l * (v1 - m1) * (v2 - m2))
    shape = s1 * s1 + s2 * s2 - 2 * cov - (s1 - s2) ** 2
    return (m1 - m2) ** 2, (s1 - s2) ** 2, shape
def barycenter(qs, w=None):
    c, l, vals = _merge(*qs); w = np.ones(len(qs)) / len(qs) if w is None else np.asarray(w) / np.sum(w)
    return (c, np.sum([wi * v for wi, v in zip(w, vals)], axis=0))
def qmix(q1, q2, a):  # a*q1 + (1-a)*q2
    return barycenter([q1, q2], [a, 1 - a])

def alr(p, ref=0):
    p = np.asarray(p, dtype=float).copy()
    if p.shape != (6,) or not np.isfinite(p).all() or (p < 0).any() or p.sum() <= 0:
        raise ValueError('Expected six nonnegative shares')
    p[p == 0] = 1e-4
    p /= p.sum()
    return np.log(np.delete(p, ref) / p[ref])
