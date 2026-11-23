"""ebnm #55 build step 2: the fastest Python path we could write for the ash fit.
Mixture weights by an active-set sequential quadratic programme on f(x) = -(1/n) sum_j log(L_j x) + sum_k x_k, x >= 0
(the unconstrained-sum reformulation used by mixsqp, Kim et al. 2020 JCGS; at the optimum sum x = 1). Independent code."""
import numpy as np
from scipy.special import ndtr
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); import ebnmport as E

def nnqp(H, b, x0, tol=1e-12, maxit=100):
    """min 0.5 y'Hy + b'y, y >= 0 (Lawson-Hanson style active set, warm-started at the support of x0)."""
    K = len(b); P = x0 > 0; y = np.zeros(K)
    if P.any():
        z = np.zeros(K); z[P] = np.linalg.solve(H[np.ix_(P, P)], -b[P])
        if (z[P] > 0).all(): y = z
        else: P[:] = False
    for _ in range(maxit):
        w = -(H @ y + b)
        cand = np.where(~P, w, -np.inf)
        if cand.max() <= tol: break
        P[np.argmax(cand)] = True
        while True:
            z = np.zeros(K); z[P] = np.linalg.solve(H[np.ix_(P, P)], -b[P])
            if (z[P] > 0).all(): y = z; break
            neg = P & (z <= 0); a = np.min(y[neg] / (y[neg] - z[neg]))
            y = y + a * (z - y); P &= y > 1e-15; y[~P] = 0.0
    return y

def mix_sqp(L, tol=1e-10, maxit=200):
    n, K = L.shape; x = np.full(K, 1.0 / K)
    f = lambda x: -np.mean(np.log(L @ x)) + x.sum()
    fx = f(x)
    for it in range(maxit):
        u = L @ x; A = L / u[:, None]
        g = -A.mean(0) + 1.0
        H = A.T @ A / n + 1e-10 * np.eye(K)
        y = nnqp(H, g - H @ x, x)
        d = y - x
        if np.max(g[x > 0] if (x > 0).any() else g) - np.min(g) < tol and g.min() >= -tol: break
        a = 1.0
        while True:
            xn = x + a * d; fn = f(xn)
            if fn <= fx + 0.01 * a * (g @ d) or a < 1e-10: break
            a *= 0.5
        x, fx = xn, fn
        if np.max(np.abs(a * d)) < 1e-12: break
    x = np.maximum(x, 0); return x / x.sum(), it + 1

def ash_fit(x, s, scale):
    s2 = s[:, None] ** 2; v = scale[None, :] ** 2; sig2 = s2 + v
    ll = -0.5 * (np.log(sig2) + x[:, None] ** 2 / sig2); norms = ll.max(1); Lm = np.exp(ll - norms[:, None])
    pi, its = mix_sqp(Lm)
    loglik = np.sum(np.log(Lm @ pi)) + norms.sum() - len(x) * np.log(2 * np.pi) / 2
    w = Lm * pi; w /= w.sum(1, keepdims=True)
    cm = x[:, None] * v / sig2; cv = s2 * v / sig2
    pm = (w * cm).sum(1); pm2 = (w * (cm ** 2 + cv)).sum(1)
    with np.errstate(divide='ignore', invalid='ignore'):
        ppos = np.where(cv > 0, ndtr(cm / np.sqrt(np.where(cv > 0, cv, 1))), 0.0)
    probpos = (w * ppos).sum(1); probzero = (w * (scale[None, :] == 0)).sum(1)
    lfsr = probzero + np.minimum(1 - probpos - probzero, probpos)
    return dict(pi=pi, loglik=float(loglik), post_mean=pm, post_sd=np.sqrt(np.maximum(0, pm2 - pm ** 2)), lfsr=lfsr, iters=its)
