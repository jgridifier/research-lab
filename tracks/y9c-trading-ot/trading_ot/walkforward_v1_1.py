"""Walk-forward engine for the v1.1 primary gate (prereg addendum v1.1, test_design_trading_ot_v1_1.json).

Conventions (all causal; every forecast at origin t is computed from truncate(panel, t)):
- History: expanding from 2009Q1; 2008 is masked by panel.presample_mask (TA 2008Q4 is the 2009Q1 denominator).
- T2 forecasting population. A forecast made at origin t for a case that belongs to epoch e uses
  population S_e, the set chosen at the epoch origin e (Q4). For scored h = 1 cases e = last Q4 <= t, so
  S_e uses data <= t. For selection cases of epoch e (targets <= e) the population is also S_e: this is
  the "bank in the set in force at the epoch origin" rule of the design's selection.cases, and it uses
  data <= e, the moment the selection is made. Pooled components (pooled errors, B5 training, B6 EB
  universe) therefore pool over S_e.
- Case scale s_i(o): trailing-16 MAD of A220_q at the case's own origin o, >= 12 values, floored at the
  10th percentile over the population S_e (= the set in force at o for scored cases). The same s_i(o) is
  the pooled-error scale inside the baselines.
- T3 population at origin t: banks with TA(i,t) >= $100m and >= 8 prior r values in [2009Q1, t].
- Selection for epoch e reads only cases with target <= e (select.select_settings enforces this).

Nothing in this module checks OOS authorization; run.stage_oos does that before calling it.
"""
import numpy as np
import pandas as pd
from statement_forecast.combo import truncate

from . import baselines as B
from . import ot_bary, select, sets
from . import walkforward as W10
from .scoring import case_scale, coverage, quantile_crps

FIRST = pd.Period('2009Q1', freq='Q')
FIRST_R = '2009Q1'
FIRST_FREEZE = pd.Period('2013Q4', freq='Q')
TARGETS_H1 = pd.period_range('2014Q1', '2026Q2', freq='Q')
ORIGINS_H1 = TARGETS_H1 - 1
EPOCH0_TARGETS = pd.period_range('2012Q3', '2013Q4', freq='Q')
MEMBERS = list(B.MEMBERS)


def _score(Q, y, scale):
    ok = np.isfinite(y) & np.all(np.isfinite(Q), axis=1) & np.isfinite(scale)
    S = np.full(len(y), np.nan)
    S[ok] = quantile_crps(Q[ok], y[ok]) / scale[ok]
    cov = np.full(len(y), np.nan)
    cov[ok] = coverage(Q[ok], y[ok], 0.9)
    return S, cov


# ── T2 ─────────────────────────────────────────────────────────────────────
def t2_forecasts(panel, population, origin, h, macro, members=MEMBERS):
    """Member forecasts (USD) for `population` at origin; returns (fc, scale, floor)."""
    origin = pd.Period(origin, freq='Q')
    trunc = truncate(panel, origin)
    population = list(population)
    W = B.Wide(trunc, population, first=str(FIRST))
    t = W.idx(origin)
    scale, floor = case_scale(trunc, population, origin, set_=population)
    fc = B.run_members(W, t, h, 'usd', scale, macro, members=members)
    return fc, scale, floor


def t2_cases(panel, population, targets, macro, members=MEMBERS, h=1, keep_quantiles=False):
    """Long table of (target, bank) cases for the given population: S_<m>, cov_<m> per member, scale, y."""
    rows, Qstore = [], {}
    for tq in targets:
        o = tq - h
        fc, scale, floor = t2_forecasts(panel, population, o, h, macro, members)
        y = W10.actual(panel, population, tq)
        rec = pd.DataFrame({'target_quarter': tq, 'origin': o, 'rssd_id': population, 'y': y, 'scale': scale,
                            'has_actual': np.isfinite(y), 'row': np.arange(len(population))})
        for m in members:
            Q = fc[m][0]
            rec[f'S_{m}'], rec[f'cov_{m}'] = _score(Q, y, scale)
            rec[f'def_{m}'] = np.all(np.isfinite(Q), axis=1)
            if keep_quantiles:
                Qstore[(tq, m)] = Q
        rec['b4_fallback'] = fc['B4'][1].get('fallback', np.zeros(len(population), bool)) if 'B4' in fc else False
        rows.append(rec)
    df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    return (df, Qstore) if keep_quantiles else df


def member_coverage(cases, members=MEMBERS):
    """{member: (n defined with actual, n cases with actual)} - the 72/72 first-freeze check."""
    base = cases[cases.has_actual]
    return {m: (int(base[f'def_{m}'].sum()), int(len(base))) for m in members}


def _bary_callable(cases, Qstore):
    """callable(kept, idx) -> (equal-weight barycenter of `kept` members, y, scale) on cases.loc[idx]."""
    def f(kept, idx):
        sub = cases.loc[idx]
        Qs = [np.vstack([Qstore[(tq, m)][r] for tq, r in zip(sub.target_quarter, sub.row)]) for m in kept]
        return ot_bary.barycenter_1d(Qs), sub.y.to_numpy(float), sub.scale.to_numpy(float)
    return f


def t2_epoch(panel, macro, epoch_origin, set_e, members=MEMBERS, previous=None):
    """Selection for one epoch on T2: walk-forward cases for S_e at the epoch's targets; settings."""
    lo, hi = select.selection_epochs()[pd.Period(epoch_origin, freq='Q')]
    targets = pd.period_range(lo, hi, freq='Q')
    base = truncate(panel, epoch_origin)          # outcomes after the epoch origin cannot enter
    cases, Qstore = t2_cases(base, set_e, targets, macro, members, keep_quantiles=True)
    settings = select.select_settings(cases, members, epoch_origin, previous=previous,
                                      bary_quantiles=_bary_callable(cases, Qstore))
    return settings, cases


# ── T3 ─────────────────────────────────────────────────────────────────────
def cs_cases(panel, targets, macro, members=MEMBERS, with_war=False):
    rows = []
    for tq in targets:
        o = tq - 1
        pop, scale, cfc = W10.cs_member_forecasts(panel, o, macro, members, first=FIRST_R)
        pr = sets.add_ratio(panel)
        tgt = pr[pr.quarter.eq(tq) & pr.trading_assets_lag.ge(W10.CS_LAG_TA_MIN) & pr.trading_revenue_q.notna()]
        y = tgt.set_index('rssd_id').r.reindex(pop).to_numpy(float)
        rec = pd.DataFrame({'target_quarter': tq, 'origin': o, 'rssd_id': pop, 'y': y, 'scale': scale,
                            'has_actual': np.isfinite(y)})
        for m in members:
            Q = cfc[m][0]
            rec[f'S_{m}'], rec[f'cov_{m}'] = _score(Q, y, scale)
            rec[f'def_{m}'] = np.all(np.isfinite(Q), axis=1)
        if with_war:
            Qw, info = W10.war_rm(panel, o, pop, first_r=FIRST_R)
            rec['S_WAR'], rec['cov_WAR'] = _score(Qw, y, scale)
            rec['war_beta'], rec['war_rho'] = info['beta'], info['rho']
        rows.append(rec)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def cs_epoch(panel, macro, epoch_origin, members=MEMBERS, previous=None):
    lo, hi = select.selection_epochs()[pd.Period(epoch_origin, freq='Q')]
    base = truncate(panel, epoch_origin)
    cases = cs_cases(base, pd.period_range(lo, hi, freq='Q'), macro, members)
    return select.select_settings(cases, members, epoch_origin, previous=previous), cases


# ── first freeze (burn-in only; no OOS target) ─────────────────────────────
def first_freeze(panel, macro, members=MEMBERS):
    """Epoch 0 at 2013Q4: S_2013Q4, member coverage on the 72 pseudo-OOS cases, settings. Burn-in only."""
    base = truncate(panel, FIRST_FREEZE)
    s0 = sets.exante_bank_set_rolling(base, FIRST_FREEZE)
    settings, cases = t2_epoch(base, macro, FIRST_FREEZE, s0, members)
    return dict(set=s0, coverage=member_coverage(cases, members), settings=settings, cases=cases)


# ── primary walk-forward (OOS; called only from run.stage_oos after authorization) ───────────────
def primary(panel, macro, members=MEMBERS, epochs=select.EPOCH_ORIGINS, targets=TARGETS_H1):
    """H1 and H2 matched-case tables over `targets` with annual re-selection. Returns dict."""
    set_by_epoch = {e: sets.exante_bank_set_rolling(truncate(panel, e), e) for e in epochs}
    t2_set, cs_set, prev2, prev3, log = {}, {}, None, None, []
    for e in epochs:
        prev2, _ = t2_epoch(panel, macro, e, set_by_epoch[e], members, previous=prev2)
        prev3, _ = cs_epoch(panel, macro, e, members, previous=prev3)
        t2_set[e], cs_set[e] = prev2, prev3
        log.append(dict(epoch=str(e), set_size=len(set_by_epoch[e]), t2=prev2, cs=prev3))
    h1_rows, h2_rows = [], []
    for tq in targets:
        e = select.epoch_for_target(tq, epochs)
        st = t2_set[e]
        cases, Qs = t2_cases(panel, set_by_epoch[e], [tq], macro, members, keep_quantiles=True)
        Qbar = ot_bary.widen(ot_bary.barycenter_1d([Qs[(tq, m)] for m in st['trimmed']]), st['s'])
        S_ot, cov_ot = _score(Qbar, cases.y.to_numpy(float), cases.scale.to_numpy(float))
        h1_rows.append(pd.DataFrame({'target_quarter': tq, 'rssd_id': cases.rssd_id, 'y': cases.y,
                                     'S_ot': S_ot, 'cov_ot': cov_ot, 'S_ref': cases[f"S_{st['b_star']}"],
                                     'cov_ref': cases[f"cov_{st['b_star']}"], 'ref': st['b_star'], 'epoch': str(e),
                                     'scale_missing': ~np.isfinite(cases.scale)}))
        c3 = cs_cases(panel, [tq], macro, members, with_war=True)
        ref3 = cs_set[e]['b_star']
        h2_rows.append(pd.DataFrame({'target_quarter': tq, 'rssd_id': c3.rssd_id, 'y': c3.y, 'S_ot': c3.S_WAR,
                                     'cov_ot': c3.cov_WAR, 'S_ref': c3[f'S_{ref3}'], 'cov_ref': c3[f'cov_{ref3}'],
                                     'ref': ref3, 'epoch': str(e), 'beta': c3.war_beta, 'rho': c3.war_rho}))
    h1, h2 = pd.concat(h1_rows, ignore_index=True), pd.concat(h2_rows, ignore_index=True)
    return dict(h1=h1.dropna(subset=['S_ot', 'S_ref']), h2=h2.dropna(subset=['S_ot', 'S_ref']),
                h1_all=h1, h2_all=h2, selection_log=log, sets={str(k): v for k, v in set_by_epoch.items()})
