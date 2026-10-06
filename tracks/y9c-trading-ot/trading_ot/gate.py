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
