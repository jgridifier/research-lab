"""v1.1 annual causal re-selection of B*, the trimmed member set and the widening s (addendum §2.3, §5.2).

Epoch 0 (origin 2013Q4) scores pseudo-OOS targets 2012Q3-2013Q4; epoch k at each Q4 origin
o = 2014Q4..2025Q4 scores targets max(2012Q3, o-11)..o. Settings chosen at o apply to targets
o+1..o+4. Every score used here is a walk-forward forecast from its own origin; this module only
sees cases whose target is <= the epoch origin (enforced).
"""
import numpy as np
import pandas as pd

from . import ot_bary

FIRST_SELECTION_TARGET = pd.Period('2012Q3', freq='Q')
EPOCH_ORIGINS = [pd.Period(f'{y}Q4', freq='Q') for y in range(2013, 2026)]
COVERAGE_MIN = 0.80
S_GRID = (1.0, 1.1, 1.2, 1.35, 1.5)


def selection_epochs(origins=EPOCH_ORIGINS):
    """{origin: (first_target, last_target)}."""
    out = {}
    for k, o in enumerate(origins):
        lo = FIRST_SELECTION_TARGET if k == 0 else max(FIRST_SELECTION_TARGET, o - 11)
        out[o] = (lo, o)
    return out


def epoch_for_target(t, origins=EPOCH_ORIGINS):
    """Epoch origin whose settings apply to target t (h = 1): the last Q4 <= t - 1."""
    t = pd.Period(t, freq='Q')
    cands = [o for o in origins if o <= t - 1]
    return cands[-1] if cands else None


def select_settings(cases, members, epoch_origin, s_grid=S_GRID, coverage_min=COVERAGE_MIN, previous=None,
                    bary_quantiles=None):
    """Settings for one epoch.

    cases: DataFrame with columns target_quarter, rssd_id, and S_<member> (scaled CRPS, NaN if the member
        did not produce a forecast or the actual is missing), plus 'has_actual' (bool).
    bary_quantiles: callable(kept_members, case_index) -> (Q (n,99), y (n,), scale (n,)) for the matched
        cases, used to choose s; None skips the s search (H2 / B*_CS selection).
    members: ordered list of member ids (order = tie-break index).
    Returns dict(b_star, trimmed, s, m0, excluded_low_coverage, n_cases, n_matched, scores, inherited).
    """
    o = pd.Period(epoch_origin, freq='Q')
    if len(cases) and (cases.target_quarter.max() > o):
        raise ValueError(f'selection at {o} was handed a case with target {cases.target_quarter.max()} > origin')
    base = cases[cases.has_actual] if 'has_actual' in cases else cases
    n = len(base)
    cover = {m: (float(np.isfinite(base[f'S_{m}']).mean()) if n else 0.0) for m in members}
    m0 = [m for m in members if cover[m] >= coverage_min]
    excluded = [m for m in members if m not in m0]
    if len(m0) < 2:
        if previous is None:
            raise ValueError(f'epoch {o}: fewer than 2 members cover >= {coverage_min:.0%} and no previous epoch')
        return dict(previous, inherited=True, epoch_origin=str(o), coverage=cover, excluded_low_coverage=excluded)
    ok = np.all([np.isfinite(base[f'S_{m}']) for m in m0], axis=0)
    matched = base[ok]
    scores = {m: float(matched[f'S_{m}'].mean()) for m in m0}
    best = min(scores.values())
    b_star = next(m for m in m0 if scores[m] == best)          # ties -> lowest member index
    trimmed = ot_bary.trim_members(scores)
    trimmed = [m for m in m0 if m in trimmed]
    s_best, s_scores = np.nan, {}
    if bary_quantiles is not None:
        Qbar, y, scale = bary_quantiles(trimmed, matched.index)
        s_best, s_scores = ot_bary.select_s(Qbar, y, scale, s_grid)
    return dict(epoch_origin=str(o), b_star=b_star, trimmed=trimmed, s=float(s_best) if np.isfinite(s_best) else None,
                s_scores={str(k): float(v) for k, v in s_scores.items()}, m0=m0, coverage=cover,
                excluded_low_coverage=excluded, n_cases=int(n), n_matched=int(ok.sum()), scores=scores,
                inherited=False)
