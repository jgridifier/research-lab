"""
Problem 6 (swap-in, performance, ~10-12 min): simulate a portfolio credit-loss
distribution with the one-factor Gaussian (Vasicek) model, three ways:
  (1) plain Python loops, (2) vectorized numpy, (3) Numba @njit (optional).
Report EL, VaR_99.9 and ES_99.9 (expected shortfall).

Loan i defaults in sim s if  sqrt(rho) Z_s + sqrt(1-rho) eps_{s,i} < Phi^{-1}(PD_i).
Loss_s = sum_i EAD_i * LGD_i * 1{default}.
Analytic checks: E[Loss] = sum EAD*LGD*PD;  for a large homogeneous pool the
loss fraction quantile is Phi( (Phi^{-1}(PD) + sqrt(rho) Phi^{-1}(q)) / sqrt(1-rho) ).
Extension in the kit: deposit-runoff paths under a rate shock.
"""
import math
import time
import numpy as np

try:
    from scipy.stats import norm
    ppf, cdf = norm.ppf, norm.cdf
except ImportError:                       # fallback via statistics.NormalDist
    from statistics import NormalDist
    _N = NormalDist()
    ppf = np.vectorize(_N.inv_cdf); cdf = np.vectorize(_N.cdf)

try:
    from numba import njit, prange
    HAVE_NUMBA = True
except ImportError:
    HAVE_NUMBA = False


def make_portfolio(n_loans: int = 500, seed: int = 5):
    rng = np.random.default_rng(seed)
    ead = rng.lognormal(mean=0.0, sigma=1.0, size=n_loans)   # exposures
    pd_ = rng.uniform(0.005, 0.05, size=n_loans)              # default probs
    lgd = rng.uniform(0.3, 0.6, size=n_loans)
    return ead, pd_, lgd


# (1) loops: correct but slow
def losses_loop(Z, eps, ead, pd_, lgd, rho):
    thr = ppf(pd_)
    n_sims, n_loans = eps.shape
    out = np.zeros(n_sims)
    a, b = math.sqrt(rho), math.sqrt(1 - rho)
    for s in range(n_sims):
        tot = 0.0
        for i in range(n_loans):
            if a * Z[s] + b * eps[s, i] < thr[i]:
                tot += ead[i] * lgd[i]
        out[s] = tot
    return out


# (2) vectorized: broadcasting (n_sims x n_loans) boolean matrix
def losses_vec(Z, eps, ead, pd_, lgd, rho):
    thr = ppf(pd_)
    latent = math.sqrt(rho) * Z[:, None] + math.sqrt(1 - rho) * eps
    return (latent < thr[None, :]) @ (ead * lgd)


# (3) Numba: same loops, compiled; draws inside so memory is O(n_loans)
if HAVE_NUMBA:
    @njit(cache=False)
    def _losses_from_draws_nb(Z, eps, thr, el_i, a, b):
        n_sims, n_loans = eps.shape
        out = np.zeros(n_sims)
        for s in range(n_sims):
            tot = 0.0
            for i in range(n_loans):
                if a * Z[s] + b * eps[s, i] < thr[i]:
                    tot += el_i[i]
            out[s] = tot
        return out

    @njit(parallel=True, cache=False)
    def _losses_sim_nb(n_sims, thr, el_i, a, b, seed):
        out = np.zeros(n_sims)
        for s in prange(n_sims):
            np.random.seed(seed + s)        # per-sim seed -> reproducible under prange
            z = np.random.standard_normal()
            tot = 0.0
            for i in range(thr.shape[0]):
                if a * z + b * np.random.standard_normal() < thr[i]:
                    tot += el_i[i]
            out[s] = tot
        return out


def losses_numba(Z, eps, ead, pd_, lgd, rho):
    return _losses_from_draws_nb(Z, eps, ppf(pd_), ead * lgd, math.sqrt(rho), math.sqrt(1 - rho))


def risk_measures(L, q=0.999):
    var = np.quantile(L, q)
    es = L[L >= var].mean()
    return dict(EL=L.mean(), VaR=var, ES=es)


def _tests():
    rho = 0.15
    ead, pd_, lgd = make_portfolio()
    rng = np.random.default_rng(0)
    # exact equivalence on identical draws (small)
    Zs, Es = rng.standard_normal(300), rng.standard_normal((300, len(ead)))
    L1 = losses_loop(Zs, Es, ead, pd_, lgd, rho)
    L2 = losses_vec(Zs, Es, ead, pd_, lgd, rho)
    assert np.allclose(L1, L2)
    # statistical checks (vectorized, 20k sims)
    n = 20_000
    Z, E = rng.standard_normal(n), rng.standard_normal((n, len(ead)))
    t0 = time.perf_counter(); L = losses_vec(Z, E, ead, pd_, lgd, rho); t_vec = time.perf_counter() - t0
    el_true = np.sum(ead * lgd * pd_)
    se = L.std() / math.sqrt(n)
    assert abs(L.mean() - el_true) < 4 * se, (L.mean(), el_true, se)
    rm = risk_measures(L)
    assert rm["ES"] >= rm["VaR"] >= rm["EL"]
    # Vasicek asymptotic check: big homogeneous pool, loss fraction quantile
    nh, p_h = 2000, 0.02
    Zh, Eh = rng.standard_normal(4000), rng.standard_normal((4000, nh))
    Lh = losses_vec(Zh, Eh, np.ones(nh), np.full(nh, p_h), np.ones(nh), rho) / nh
    q = 0.99
    vas = cdf((ppf(p_h) + math.sqrt(rho) * ppf(q)) / math.sqrt(1 - rho))
    assert abs(np.quantile(Lh, q) - vas) < 0.15 * vas, (np.quantile(Lh, q), vas)
    msg = "numba not installed (skipped)"
    if HAVE_NUMBA:
        L3 = losses_numba(Zs, Es, ead, pd_, lgd, rho)          # first call compiles
        assert np.allclose(L1, L3)
        t0 = time.perf_counter(); losses_numba(Z, E, ead, pd_, lgd, rho); t_nb = time.perf_counter() - t0
        thr, eli = ppf(pd_), ead * lgd
        _losses_sim_nb(10, thr, eli, math.sqrt(rho), math.sqrt(1 - rho), 1)   # compile
        t0 = time.perf_counter()
        Lp = _losses_sim_nb(200_000, thr, eli, math.sqrt(rho), math.sqrt(1 - rho), 123)
        t_par = time.perf_counter() - t0
        Lp2 = _losses_sim_nb(200_000, thr, eli, math.sqrt(rho), math.sqrt(1 - rho), 123)
        assert np.array_equal(Lp, Lp2)                           # reproducible
        assert abs(Lp.mean() - el_true) < 4 * Lp.std() / math.sqrt(len(Lp))
        msg = "vec(20k) %.3fs | njit(20k) %.3fs | njit-parallel(200k, draws inside) %.3fs" % (t_vec, t_nb, t_par)
    # time the loop on a small slice to show the gap
    t0 = time.perf_counter(); losses_loop(Z[:1000], E[:1000], ead, pd_, lgd, rho); t_loop = (time.perf_counter() - t0) * n / 1000
    print("p6 OK  | EL true %.3f  MC %.3f | VaR99.9 %.2f  ES99.9 %.2f" % (el_true, rm["EL"], rm["VaR"], rm["ES"]))
    print("timing (20k sims x %d loans): loop ~%.2fs (extrapolated) | %s" % (len(ead), t_loop, msg))


if __name__ == "__main__":
    _tests()
