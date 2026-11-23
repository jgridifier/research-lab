"""Independent NumPy/SciPy implementation of empirical Bayes normal means (EBNM) for three prior
families: normal, point-normal and the scale mixture of normals ("ash", normal_scale_mixture).
Written from the papers (Stephens 2017 Biostatistics; Willwerscheid, Carbonetto & Stephens, ebnm JSS
2025; Kim et al. 2022 mixsqp JCGS). The R package ebnm 1.1.42 is used only as a black-box oracle.
Research prototype for scout issue #55 (2026-11-23). Not a library yet.
"""
from __future__ import annotations
import numpy as np
from scipy import integrate, optimize, special, stats

LOG2PI = np.log(2 * np.pi)

# ---------------------------------------------------------------- grid (Willwerscheid 2021 KL bound)
_GH_X, _GH_W = np.polynomial.hermite_e.hermegauss(160)
_GH_W = _GH_W / np.sqrt(2 * np.pi)

def _kl_two_comp(s2, omega, m):
    """KL( N(0,s2) || omega N(0,1) + (1-omega) N(0,m) ) = E_f[log f - log g], by 160-node Gauss-Hermite."""
    sd = np.sqrt(s2); x = sd * _GH_X
    lf = -0.5 * np.log(2 * np.pi * s2) - 0.5 * _GH_X ** 2
    lg = np.logaddexp(np.log(omega) - 0.5 * np.log(2 * np.pi) - 0.5 * x ** 2,
                      np.log1p(-omega) - 0.5 * np.log(2 * np.pi * m) - 0.5 * x ** 2 / m)
    return float(np.dot(_GH_W, lf - lg))

def _ub_kl(m):
    """Worst case over s2 in [1, m] of the best two-component approximation."""
    inner = lambda s2: optimize.minimize_scalar(lambda w: _kl_two_comp(s2, w, m), bounds=(1e-12, 1 - 1e-12),
                                                method="bounded", options={"xatol": 1e-10}).fun
    r = optimize.minimize_scalar(lambda s2: -inner(s2), bounds=(1.0, m), method="bounded", options={"xatol": 1e-10})
    return -r.fun

def grid_mult_for(kl_target):
    """Solve ub_kl(m) = kl_target for the grid multiplier m (log-scale root find)."""
    g = lambda lm: np.log(_ub_kl(np.exp(lm))) - np.log(kl_target)
    return float(np.exp(optimize.brentq(g, np.log(1.0001), np.log(100.0), xtol=1e-12)))

def smn_scale_grid(x, s, mode=0.0, min_K=3, max_K=300, kl_target=None, grid_mult=None):
    n = len(x); kl_target = 1.0 / n if kl_target is None else kl_target
    max_x2 = np.max((x - mode) ** 2); min_s2 = np.min(s) ** 2
    ratio = max(max_x2 / min_s2, 1.0)
    max_mult = (ratio + 1) ** (1 / (min_K - 1)) + 1e-8
    min_mult = max_mult ** ((min_K - 1) / (max_K - 1)) - 1e-8
    gm = grid_mult_for(kl_target) if grid_mult is None else grid_mult
    gm = min(max(gm, min_mult), max_mult)
    K = int(np.ceil(np.log(ratio + 1) / np.log(gm))) + 1
    return np.sqrt(min_s2 * (gm ** np.arange(K) - 1))

# ---------------------------------------------------------------- mixture-weight solve
def mix_weights(L, tol=1e-12, max_iter=200):
    """Maximise sum_j log(L_j . pi) over the simplex. Primal-dual interior point on the concave problem
    (same objective as mixsqp; a different, exact-to-tolerance solver)."""
    n, K = L.shape
    w = np.full(K, 1.0 / K)
    # Frank-Wolfe-free approach: Newton on the KKT system with log barrier, decreasing mu.
    # Parametrise pi = w; constraint sum w = 1 handled by Lagrange multiplier.
    mu = 1e-2
    for outer in range(60):
        for it in range(max_iter):
            Lw = L @ w
            g = L.T @ (1.0 / Lw) / n + mu / w            # gradient of f + mu*sum log w
            H = (L / Lw[:, None]).T @ (L / Lw[:, None]) / n + np.diag(mu / w ** 2)
            # solve [H 1;1' 0][d;-lam] = [g;0] for ascent direction with sum d = 0
            Hi_g = np.linalg.solve(H, g); Hi_1 = np.linalg.solve(H, np.ones(K))
            lam = Hi_g.sum() / Hi_1.sum()
            d = Hi_g - lam * Hi_1
            # step to keep w > 0
            neg = d < 0
            a = 1.0 if not neg.any() else min(1.0, 0.99 * np.min(-w[neg] / d[neg]))
            w = w + a * d; w = np.maximum(w, 1e-300); w /= w.sum()
            if np.max(np.abs(a * d)) < 1e-15:
                break
        if mu < tol * 1e-3:
            break
        mu *= 0.1
    w[w < 1e-14] = 0.0
    return w / w.sum()

# ---------------------------------------------------------------- posterior for normal mixtures
def _mix_posterior(x, s, pi, mean, sd):
    s2 = s[:, None] ** 2; v = sd[None, :] ** 2; sig2 = s2 + v
    ll = -0.5 * (np.log(sig2) + (x[:, None] - mean[None, :]) ** 2 / sig2)
    norms = ll.max(1); Lm = np.exp(ll - norms[:, None])
    loglik = np.sum(np.log(Lm @ pi)) + norms.sum() - len(x) * LOG2PI / 2
    w = Lm * pi[None, :]; w /= w.sum(1, keepdims=True)
    cm = (mean[None, :] * s2 + x[:, None] * v) / sig2
    cv = s2 * v / sig2
    pm = (w * cm).sum(1); pm2 = (w * (cm ** 2 + cv)).sum(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        ppos = np.where(cv > 0, stats.norm.sf(0, cm, np.sqrt(np.where(cv > 0, cv, 1))), (cm > 0) * 1.0)
    probpos = (w * ppos).sum(1)
    probzero = (w * (sd[None, :] == 0)).sum(1)
    probneg = 1 - (probpos + probzero)
    lfsr = probzero + np.minimum(probneg, probpos)
    return dict(loglik=float(loglik), post_mean=pm, post_sd=np.sqrt(np.maximum(0, pm2 - pm ** 2)), lfsr=lfsr)

def ebnm_ash(x, s, mode=0.0, scale=None, grid_mult=None):
    x = np.asarray(x, float); s = np.asarray(s, float)
    scale = smn_scale_grid(x, s, mode, grid_mult=grid_mult) if scale is None else np.asarray(scale, float)
    sig2 = s[:, None] ** 2 + scale[None, :] ** 2
    ll = -0.5 * (np.log(sig2) + (x[:, None] - mode) ** 2 / sig2)
    L = np.exp(ll - ll.max(1, keepdims=True))
    pi = mix_weights(L)
    out = _mix_posterior(x, s, pi, np.full(len(scale), mode), scale)
    out.update(pi=pi, sd=scale); return out

def ebnm_point_normal(x, s, mode=0.0):
    """g = pi0 delta_mode + (1-pi0) N(mode, a^2); MLE over (pi0, a) by bounded quasi-Newton."""
    x = np.asarray(x, float); s = np.asarray(s, float)
    def nll(p):
        pi0 = special.expit(p[0]); a2 = np.exp(p[1])
        l0 = stats.norm.logpdf(x, mode, s); l1 = stats.norm.logpdf(x, mode, np.sqrt(s ** 2 + a2))
        return -np.sum(np.logaddexp(np.log(pi0) + l0, np.log1p(-pi0) + l1))
    best = None
    for p0 in ([0.0, np.log(np.mean(x ** 2) + 1e-8)], [2.0, np.log(np.var(x) + 1e-8)], [-2.0, 0.0]):
        r = optimize.minimize(nll, p0, method="L-BFGS-B", options={"ftol": 1e-15, "gtol": 1e-11, "maxiter": 5000})
        r = optimize.minimize(nll, r.x, method="Nelder-Mead", options={"xatol": 1e-12, "fatol": 1e-14, "maxiter": 20000})
        if best is None or r.fun < best.fun: best = r
    pi0 = special.expit(best.x[0]); a = np.sqrt(np.exp(best.x[1]))
    out = _mix_posterior(x, s, np.array([pi0, 1 - pi0]), np.array([mode, mode]), np.array([0.0, a]))
    out.update(pi=np.array([pi0, 1 - pi0]), sd=np.array([0.0, a])); return out

def ebnm_normal(x, s, mode=0.0):
    x = np.asarray(x, float); s = np.asarray(s, float)
    nll = lambda la: -np.sum(stats.norm.logpdf(x, mode, np.sqrt(s ** 2 + np.exp(la))))
    r = optimize.minimize_scalar(nll, bounds=(-40, 10), method="bounded", options={"xatol": 1e-13})
    a = np.sqrt(np.exp(r.x))
    out = _mix_posterior(x, s, np.array([1.0]), np.array([mode]), np.array([a]))
    out.update(pi=np.array([1.0]), sd=np.array([a])); return out
