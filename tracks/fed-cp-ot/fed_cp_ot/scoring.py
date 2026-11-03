"""PREREG v2 2, 7(d), 9 and 12 T5: paired weeks, G, G_s, fixed-b Bartlett HAC with the phi rule, Holm per family."""
import math
import numpy as np
import pandas as pd
from .paths import SEED
from .metric import q_from_p, w2sq, X_LOG

MIN_PAIRS = 800
HURDLE_G = 0.02
PHI_REJECT = 0.99
GRID = np.round(np.arange(-0.98, 0.9801, 0.01), 2)
SUBPERIODS = (('2009-2014', '2009-01-01', '2014-12-31'), ('2015-2020', '2015-01-01', '2020-12-31'),
              ('2021-2026', '2021-01-01', '2026-10-02'))
NON_REJECTION = 'underpowered to detect a 5% gain (planning power ≈0.50); not evidence of no gain.'

def weekly_loss(forecast, outcome):
    """L_t(m) = mean over the 4 types of W2SQ(f, y). Both are dicts {type: 6-mix}; None if either side lacks a type."""
    if set(forecast) != set(outcome) or len(forecast) != 4: return None
    return sum(w2sq(q_from_p(forecast[t], X_LOG), q_from_p(outcome[t], X_LOG)) for t in forecast) / 4

def zstat(d, L):
    """One-sided fixed-b Bartlett HAC t-statistic of the mean of d (rows are independent series)."""
    d = np.atleast_2d(d); T = d.shape[1]; m = d.mean(1, keepdims=True); c = d - m; s2 = (c * c).mean(1)
    for j in range(1, L + 1): s2 = s2 + 2 * (1 - j / (L + 1)) * (c[:, j:] * c[:, :-j]).sum(1) / T
    return np.sqrt(T) * m[:, 0] / np.sqrt(np.maximum(s2, 1e-300))

def ar_paths(rng, n, T, phi, burn=200):
    e = rng.standard_normal((n, T + burn)); x = np.empty_like(e)
    x[:, 0] = e[:, 0] / math.sqrt(max(1 - phi * phi, 1e-12))
    for k in range(1, T + burn): x[:, k] = phi * x[:, k - 1] + e[:, k]
    return x[:, burn:]

def phi_hat(d):
    d = np.asarray(d, float)
    X = np.c_[np.ones(len(d) - 1), d[:-1]]
    return float(np.linalg.lstsq(X, d[1:], rcond=None)[0][1])

def null_z(T, L, phi, draws, seed=SEED, chunk=5000):
    rng = np.random.default_rng(seed)
    return np.concatenate([zstat(ar_paths(rng, min(chunk, draws - i), T, phi), L) for i in range(0, draws, chunk)])

def runtime_p(z, T, L, phi, draws=100000):
    """P(Z_null >= z) from AR(1) null draws at phi_hat (v1 5)."""
    return float((null_z(T, L, phi, draws) >= z).mean())

def cv_grid(T, L, levels=(0.95, 0.975), draws=20000):
    """Critical values on the phi grid (step 0.01 over [-0.98, 0.98])."""
    cv = {lv: [] for lv in levels}
    for ph in GRID:
        z = null_z(T, L, float(ph), draws, chunk=5000)
        for lv in levels: cv[lv].append(float(np.quantile(z, lv)))
    return cv

def grid_cv(cv_for_level, phi):
    """Linear interpolation inside the grid only; outside it there is no value (no extrapolation)."""
    if phi < GRID[0] or phi > GRID[-1]: return None
    return float(np.interp(phi, GRID, cv_for_level))

def paired_weeks(L_cand, L_comp):
    return sorted(set(L_cand) & set(L_comp))

def gain(L_cand, L_comp, weeks):
    if not weeks: return None
    return 1 - sum(L_cand[w] for w in weeks) / sum(L_comp[w] for w in weeks)

def evaluate_pair(L_cand, L_comp, test=True, min_pairs=MIN_PAIRS, p_draws=100000, grid_draws=20000):
    weeks = paired_weeks(L_cand, L_comp)
    res = {'n_pairs': len(weeks), 'G': gain(L_cand, L_comp, weeks), 'G_s': {}, 'phi': None, 'z': None, 'p': None,
           'incomplete': False, 'incomplete_reason': None}
    for name, a, b in SUBPERIODS:
        sub = [w for w in weeks if pd.Timestamp(a) <= w <= pd.Timestamp(b)]
        res['G_s'][name] = gain(L_cand, L_comp, sub)
    if not test: return res
    if len(weeks) < min_pairs:
        return {**res, 'incomplete': True, 'incomplete_reason': f'n_pairs {len(weeks)} < {min_pairs}'}
    d = np.array([L_comp[w] - L_cand[w] for w in weeks])  # gaps closed up; the HAC treats d as consecutive
    T = len(d); L = int(math.floor(math.sqrt(T)))
    ph = phi_hat(d); res['phi'] = ph
    if abs(ph) >= PHI_REJECT:
        return {**res, 'incomplete': True, 'incomplete_reason': f'|phi_hat| {abs(ph):.4f} >= {PHI_REJECT}'}
    z = float(zstat(d, L)[0]); res['z'] = z; res['L'] = L
    res['p'] = runtime_p(z, T, L, ph, p_draws)
    if grid_draws:
        cv = cv_grid(T, L, draws=grid_draws)
        res['grid_cv'] = {str(lv): grid_cv(v, ph) for lv, v in cv.items()}  # diagnostic; the p-value decides
    return res

def holm(pvalues, alpha=0.05):
    """Holm step-down on a family; a test without a p-value (INCOMPLETE) counts as p=1 but keeps the family size."""
    m = len(pvalues); order = sorted(range(m), key=lambda i: (1.0 if pvalues[i] is None else pvalues[i], i))
    out = [False] * m
    for rank, i in enumerate(order):
        if pvalues[i] is None or pvalues[i] > alpha / (m - rank): break
        out[i] = True
    return out

def hurdles(res):
    return {'G_gt_0.02': res['G'] is not None and res['G'] > HURDLE_G,
            'G_s_pos_in_2_of_3': sum(1 for v in res['G_s'].values() if v is not None and v > 0) >= 2,
            'pairs_ge_800': res['n_pairs'] >= MIN_PAIRS}

def run_family(name, pairs, losses, **kw):
    """pairs: [(cand, comp)]. Returns {test_label: result} with Holm rejection and the claim flag per test."""
    res = {f'{c} vs {k}': evaluate_pair(losses.get(c, {}), losses.get(k, {}), **kw) for c, k in pairs}
    rej = holm([r['p'] for r in res.values()])
    for (label, r), reject in zip(res.items(), rej):
        h = hurdles(r)
        r.update(family=name, holm_reject=reject, hurdles=h, claim=bool(reject and all(h.values()) and not r['incomplete']))
        if name == 'A' and not r['claim']: r['wording'] = NON_REJECTION
    return res

FAMILIES = (('A', [('WAR', 'B*'), ('TMAR', 'B*')]), ('B', [('SEL', 'P')]), ('K', [('KUMO_best', 'SEL'), ('KUMO_best', 'P')]))
DESCRIPTIVE = (('KUMO_best', 'B*'), ('KUMO_best', 'WAR'), ('KUMO_best', 'TMAR'), ('KUMO_fast', 'SEL'), ('KUMO_fast', 'P'))

def score_all(losses, **kw):
    out = {'families': {}, 'descriptive': {}}
    for name, pairs in FAMILIES: out['families'].update(run_family(name, pairs, losses, **kw))
    for c, k in DESCRIPTIVE: out['descriptive'][f'{c} vs {k}'] = evaluate_pair(losses.get(c, {}), losses.get(k, {}), test=False)
    return out
