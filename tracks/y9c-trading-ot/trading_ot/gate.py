"""Evaluation gate (prereg §5.3-5.4): panel DM on per-target-quarter mean differentials, Holm, verdicts."""
import numpy as np
import pandas as pd
from scipy.stats import t as student_t

MIN_TARGETS = 16
G_MIN = 0.03
COVERAGE_BAND = (0.80, 0.97)
ALPHA = 0.05


def newey_west_lrv(x, lag):
    """Bartlett-kernel long-run variance of a demeaned series with `lag` autocovariances."""
    x = np.asarray(x, float) - np.mean(x)
    T = len(x)
    lrv = float(np.dot(x, x) / T)
    for k in range(1, lag + 1):
        lrv += 2 * (1 - k / (lag + 1)) * float(np.dot(x[k:], x[:-k]) / T)
    return lrv


def hln_factor(T, h):
    return float(np.sqrt((T + 1 - 2 * h + h * (h - 1) / T) / T))


def panel_dm(dbar, h=1):
    """One-sided DM on dbar_t (positive favours the OT method): HLN factor, NW lag h-1, t_(T-1).

    Returns dict with mean, se (of the mean, before HLN), stat (HLN-adjusted), p (one-sided), df.
    """
    d = np.asarray(dbar, float)
    T = len(d)
    lrv = newey_west_lrv(d, h - 1)
    se = float(np.sqrt(lrv / T)) if lrv > 0 else np.nan
    mean = float(d.mean())
    if not np.isfinite(se) or se == 0:
        return dict(T=T, mean=mean, se=se, stat=np.nan, p=np.nan, df=T - 1, hln=hln_factor(T, h))
    stat = mean / se * hln_factor(T, h)
    return dict(T=T, mean=mean, se=se, stat=float(stat), p=float(student_t.sf(stat, T - 1)), df=T - 1,
                hln=hln_factor(T, h))


def fixed_m_dm(dbar, m=None):
    """Fixed-smoothing DM (Coroneo & Iacone 2020), weighted-periodogram LRV with Daniell kernel.

    sigma2 = (1/m) sum_(j=1..m) 2 pi I(lambda_j), lambda_j = 2 pi j / T; stat = sqrt(T) dbar / sigma ~ t_(2m).
    Default m = floor(T^(1/3)). One-sided p (positive favours the OT method). Reported only, not gating.
    """
    d = np.asarray(dbar, float)
    T = len(d)
    m = int(np.floor(T ** (1 / 3))) if m is None else int(m)
    x = d - d.mean()
    tt = np.arange(1, T + 1)
    lam = 2 * np.pi * np.arange(1, m + 1) / T
    I = np.abs(np.exp(1j * np.outer(lam, tt)) @ x) ** 2 / (2 * np.pi * T)
    sigma2 = float(np.mean(2 * np.pi * I))
    stat = float(np.sqrt(T) * d.mean() / np.sqrt(sigma2)) if sigma2 > 0 else np.nan
    return dict(T=T, m=m, df=2 * m, stat=stat, p=float(student_t.sf(stat, 2 * m)) if np.isfinite(stat) else np.nan)


def holm(pvals):
    """Holm step-down adjusted p-values for a dict {name: p}; NaN p stays NaN (treated as non-rejection)."""
    names = [k for k in pvals if np.isfinite(pvals[k])]
    order = sorted(names, key=lambda k: pvals[k])
    m = len(pvals)
    adj, running = {}, 0.0
    for rank, k in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[k]))
        adj[k] = running
    for k in pvals:
        adj.setdefault(k, np.nan)
    return adj


def per_quarter(cases, ref='ref', alt='ot'):
    """cases: DataFrame with target_quarter, rssd_id, S_ref, S_ot (scaled CRPS). Returns per-quarter means."""
    g = cases.groupby('target_quarter')
    out = pd.DataFrame({'Sbar_ref': g[f'S_{ref}'].mean(), 'Sbar_ot': g[f'S_{alt}'].mean(), 'n': g.size()})
    out['dbar'] = out.Sbar_ref - out.Sbar_ot
    return out


def relative_gain_ci(pq, h=1, level=0.95):
    """G = sum dbar / sum Sbar_ref; one-sided upper bound from the HLN/NW SE scaled by sum Sbar_ref / T."""
    dm = panel_dm(pq.dbar.to_numpy(), h)
    T = dm['T']
    denom = pq.Sbar_ref.sum() / T
    G = float(pq.dbar.sum() / pq.Sbar_ref.sum())
    se_adj = dm['se'] / dm['hln'] if np.isfinite(dm['se']) else np.nan
    q = student_t.ppf(level, T - 1)
    return dict(G=G, G_upper=float((dm['mean'] + q * se_adj) / denom) if np.isfinite(se_adj) else np.nan,
                G_lower=float((dm['mean'] - q * se_adj) / denom) if np.isfinite(se_adj) else np.nan, **dm)


def lobo(cases):
    """Relative gain after dropping each bank in turn (re-aggregated by quarter)."""
    out = {}
    for b in sorted(cases.rssd_id.unique()):
        pq = per_quarter(cases[cases.rssd_id.ne(b)])
        out[int(b)] = float(pq.dbar.sum() / pq.Sbar_ref.sum())
    return out


def loyo(cases):
    out = {}
    years = cases.target_quarter.map(lambda q: q.year)
    for y in sorted(years.unique()):
        pq = per_quarter(cases[years.ne(y)])
        out[int(y)] = float(pq.dbar.sum() / pq.Sbar_ref.sum())
    return out


def verdict(p_holm, G, G_upper, coverage90, lobo_gains, n_targets):
    """PASS / PASS-fragile / FAIL / INCOMPLETE per prereg §5.4."""
    if n_targets < MIN_TARGETS:
        return 'INCOMPLETE'
    if G <= 0 or (np.isfinite(G_upper) and G_upper < G_MIN):
        return 'FAIL'
    c1 = np.isfinite(p_holm) and p_holm < ALPHA
    c2 = G >= G_MIN
    c3 = COVERAGE_BAND[0] <= coverage90 <= COVERAGE_BAND[1]
    c4 = min(lobo_gains.values()) > 0
    if c1 and c2 and c3 and c4:
        return 'PASS'
    if c1 and c2 and c3 and not c4:
        return 'PASS-fragile'
    return 'INCOMPLETE'


# ── v1.1 (addendum §2.6, §4.3, §5.4) ────────────────────────────────────────
from functools import lru_cache

from scipy.stats import norm

MIN_TARGETS_V1_1 = 40
DM_SEED = 20261006
DM_R = 200_000
SUBPERIODS = {'P1': ('2014Q1', '2017Q4'), 'P2': ('2018Q1', '2021Q4'), 'P3': ('2022Q1', '2026Q2')}
FB2_BREAKS = ('2015Q3', '2016Q3', '2020Q1', '2022Q1')


def bartlett_bandwidth(T):
    return int(np.floor(np.sqrt(T)))


def bartlett_omega(x, M):
    """Omega = g0 + 2 sum_{l=1..M} (1 - l/(M+1)) g_l with g_l = T^-1 sum (x_t - xbar)(x_{t-l} - xbar).

    x may be (T,) or (R, T) (rows are independent series)."""
    x = np.atleast_2d(np.asarray(x, float))
    x = x - x.mean(axis=1, keepdims=True)
    T = x.shape[1]
    om = np.einsum('ij,ij->i', x, x) / T
    for l in range(1, M + 1):
        om = om + 2 * (1 - l / (M + 1)) * np.einsum('ij,ij->i', x[:, l:], x[:, :-l]) / T
    return om


def _dm_c_stat(x, M):
    x = np.atleast_2d(np.asarray(x, float))
    T = x.shape[1]
    om = bartlett_omega(x, M)
    with np.errstate(invalid='ignore', divide='ignore'):
        return x.mean(axis=1) / np.sqrt(om / T)


@lru_cache(maxsize=16)
def fixedb_null(T, M=None, R=DM_R, seed=DM_SEED):
    """Sorted null statistics of DM_C on R iid N(0,1) series of length T (deterministic under the seed)."""
    M = bartlett_bandwidth(T) if M is None else M
    rng = np.random.default_rng(seed)
    out = np.empty(R)
    chunk = 20_000
    for a in range(0, R, chunk):
        out[a:a + chunk] = _dm_c_stat(rng.standard_normal((min(chunk, R - a), T)), M)
    out = out[np.isfinite(out)]
    out.sort()
    return out


def dm_fixedb(dbar, seed=DM_SEED, R=DM_R, M=None):
    """Primary v1.1 test C: one-sided Bartlett-NW DM with M = floor(sqrt(T)) and simulated fixed-b p-value.

    p = share of the R null statistics >= DM_C. Positive dbar favours the OT method.
    """
    d = np.asarray(dbar, float)
    T = len(d)
    M = bartlett_bandwidth(T) if M is None else int(M)
    null = fixedb_null(T, M, R, seed)
    omega = float(bartlett_omega(d, M)[0])
    stat = float(_dm_c_stat(d, M)[0]) if omega > 0 else np.nan
    p = float((len(null) - np.searchsorted(null, stat, side='left')) / len(null)) if np.isfinite(stat) else np.nan
    return dict(T=T, M=M, mean=float(d.mean()), omega=omega, se=float(np.sqrt(omega / T)) if omega > 0 else np.nan,
                stat=stat, p=p, cv_95=float(np.quantile(null, 0.95)), cv_975=float(np.quantile(null, 0.975)),
                R=R, seed=seed)


def gain_v1_1(pq, seed=DM_SEED, R=DM_R):
    """G = sum dbar / sum Sbar_ref; G_U = G + c_0.95 sqrt(Omega/T) / mean(Sbar_ref) (fixed-b, §5.4)."""
    dm = dm_fixedb(pq.dbar.to_numpy(), seed, R)
    G = float(pq.dbar.sum() / pq.Sbar_ref.sum())
    G_U = G + dm['cv_95'] * dm['se'] / float(pq.Sbar_ref.mean()) if np.isfinite(dm['se']) else np.nan
    return dict(G=G, G_U=float(G_U), **dm)


def verdict_v1_1(p_holm, G, G_U, coverage90, lobo_gains, subperiod_gains, n_targets, integrity_ok=True):
    """PASS / PASS-fragile / FAIL / INCOMPLETE per addendum §5.4."""
    if not integrity_ok or n_targets < MIN_TARGETS_V1_1:
        return 'INCOMPLETE'
    if G <= 0 or (np.isfinite(G_U) and G_U < G_MIN):
        return 'FAIL'
    c1 = bool(np.isfinite(p_holm) and p_holm < ALPHA)
    c2 = G >= G_MIN
    c3 = COVERAGE_BAND[0] <= coverage90 <= COVERAGE_BAND[1]
    c4 = len(lobo_gains) > 0 and min(lobo_gains.values()) > 0
    c5 = sum(1 for g in subperiod_gains.values() if np.isfinite(g) and g > 0) >= 2
    if c1 and c2 and c3:
        return 'PASS' if (c4 and c5) else 'PASS-fragile'
    return 'INCOMPLETE'


def subperiods(cases, periods=SUBPERIODS, seed=DM_SEED, R=DM_R):
    """Per subperiod: G, raw test-C p, OT 90% coverage, LOBO-min, number of target quarters (descriptive)."""
    out = {}
    for name, (a, b) in periods.items():
        lo, hi = pd.Period(a, freq='Q'), pd.Period(b, freq='Q')
        c = cases[cases.target_quarter.between(lo, hi)]
        if c.empty:
            out[name] = dict(G=np.nan, p=np.nan, coverage90=np.nan, lobo_min=np.nan, n_targets=0)
            continue
        pq = per_quarter(c)
        dm = dm_fixedb(pq.dbar.to_numpy(), seed, R) if len(pq) > 2 else dict(p=np.nan)
        lb = lobo(c)
        out[name] = dict(G=float(pq.dbar.sum() / pq.Sbar_ref.sum()), p=dm['p'],
                         coverage90=float(c.cov_ot.mean()) if 'cov_ot' in c else np.nan,
                         lobo_min=float(min(lb.values())) if lb else np.nan, n_targets=int(len(pq)))
    return out


@lru_cache(maxsize=16)
def fluctuation_null(T, m, R=DM_R, seed=DM_SEED):
    M = bartlett_bandwidth(T)
    rng = np.random.default_rng(seed)
    out = np.empty(R)
    chunk = 20_000
    k = np.ones(m) / m
    for a in range(0, R, chunk):
        x = rng.standard_normal((min(chunk, R - a), T))
        om = bartlett_omega(x, M)
        roll = np.apply_along_axis(lambda r: np.convolve(r, k, mode='valid'), 1, x)
        out[a:a + chunk] = np.max(np.abs(np.sqrt(m) * roll / np.sqrt(om)[:, None]), axis=1)
    return np.sort(out)


def fluctuation_test(dbar, m=None, R=DM_R, seed=DM_SEED, level=0.05):
    """FB1 (Giacomini-Rossi type): F_j = sqrt(m) mean_{window j}(dbar) / sqrt(Omega_full), m = floor(0.3 T)."""
    d = np.asarray(dbar, float)
    T = len(d)
    m = int(np.floor(0.3 * T)) if m is None else int(m)
    om = float(bartlett_omega(d, bartlett_bandwidth(T))[0])
    F = np.sqrt(m) * np.convolve(d, np.ones(m) / m, mode='valid') / np.sqrt(om)
    null = fluctuation_null(T, m, R, seed)
    cv = float(np.quantile(null, 1 - level))
    stat = float(np.max(np.abs(F)))
    return dict(T=T, m=m, stat=stat, cv=cv, reject=bool(stat > cv), path=F.tolist())


def mean_shift_tests(dbar, dates, breaks=FB2_BREAKS):
    """FB2: shift in mean(dbar) at each pre-specified date; Bartlett-HAC (M = floor(sqrt(T))) SE; Holm; descriptive."""
    d = np.asarray(dbar, float)
    dates = pd.PeriodIndex(dates, freq='Q')
    T = len(d)
    M = bartlett_bandwidth(T)
    raw = {}
    out = {}
    for b in breaks:
        D = (dates >= pd.Period(b, freq='Q')).astype(float)
        X = np.column_stack([np.ones(T), D])
        XtX_inv = np.linalg.inv(X.T @ X)
        beta = XtX_inv @ X.T @ d
        u = d - X @ beta
        g = X * u[:, None]
        S = g.T @ g / T
        for l in range(1, M + 1):
            G_l = g[l:].T @ g[:-l] / T
            S += (1 - l / (M + 1)) * (G_l + G_l.T)
        V = T * XtX_inv @ S @ XtX_inv
        se = float(np.sqrt(V[1, 1]))
        z = float(beta[1] / se) if se > 0 else np.nan
        raw[b] = float(2 * norm.sf(abs(z))) if np.isfinite(z) else np.nan
        out[b] = dict(shift=float(beta[1]), se=se, z=z, p=raw[b], n_before=int((D == 0).sum()), n_after=int(D.sum()))
    adj = holm(raw)
    for b in breaks:
        out[b]['p_holm'] = adj[b]
    return out


def evaluate_hypothesis_v1_1(cases, seed=DM_SEED, R=DM_R):
    """All gate inputs for one primary hypothesis from its matched cases (target_quarter, rssd_id, S_ref, S_ot,
    cov_ot). Robustness tests (v1 test A, WPE fixed-m, FB1, FB2) are reported, never gating."""
    pq = per_quarter(cases)
    g = gain_v1_1(pq, seed, R)
    lb = lobo(cases)
    d = pq.dbar.to_numpy()
    return dict(n_targets=int(len(pq)), n_cases=int(len(cases)), G=g['G'], G_U=g['G_U'], dm=g,
                coverage90=float(cases.cov_ot.mean()), coverage90_ref=float(cases.cov_ref.mean()),
                lobo=lb, lobo_min=float(min(lb.values())) if lb else np.nan,
                subperiods=subperiods(cases, seed=seed, R=R),
                robustness=dict(test_A=panel_dm(d, 1), wpe=fixed_m_dm(d),
                                FB1=fluctuation_test(d, R=R, seed=seed) if len(d) >= 10 else None,
                                FB2=mean_shift_tests(d, pq.index) if len(d) >= 10 else None),
                per_quarter=pq.reset_index().assign(target_quarter=lambda x: x.target_quarter.astype(str))
                .to_dict(orient='list'))


def evaluate_primary_v1_1(h1_cases, h2_cases, integrity_ok=True, seed=DM_SEED, R=DM_R):
    """Holm over {H1, H2} on the fixed-b p-values, then verdict_v1_1 per hypothesis."""
    ev = {'H1': evaluate_hypothesis_v1_1(h1_cases, seed, R), 'H2': evaluate_hypothesis_v1_1(h2_cases, seed, R)}
    adj = holm({k: v['dm']['p'] for k, v in ev.items()})
    for k, v in ev.items():
        v['p_holm'] = adj[k]
        v['verdict'] = verdict_v1_1(adj[k], v['G'], v['G_U'], v['coverage90'], v['lobo'],
                                    {p: s['G'] for p, s in v['subperiods'].items()}, v['n_targets'], integrity_ok)
    return ev
