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
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from statement_forecast.combo import truncate

from . import baselines as B
from . import ot_bary, select, sets
from . import walkforward as W10
from .panel import presample_mask
from .scoring import case_scale, coverage, quantile_crps

FIRST = pd.Period('2009Q1', freq='Q')
FIRST_R = '2009Q1'
FIRST_FREEZE = pd.Period('2013Q4', freq='Q')
TARGETS_H1 = pd.period_range('2014Q1', '2026Q2', freq='Q')
ORIGINS_H1 = TARGETS_H1 - 1
EPOCH0_TARGETS = pd.period_range('2012Q3', '2013Q4', freq='Q')
MEMBERS = list(B.MEMBERS)
DENOM_COLUMNS = {'trading_assets': 'trading_assets', 'total_assets': 'total_assets', 'unit': 'unit_denom'}


@dataclass(frozen=True)
class Spec:
    """Estimation variant. The default is the pre-registered primary; sensitivities change one field each.

    first        first training quarter (S4b: 2010Q1); rows before it are masked at every origin except the
                 denominator one quarter earlier (same rule as the 2008 pre-sample mask).
    denom        bank-level modelling scale for T2 (S2): 'trading_assets' (primary), 'total_assets', 'unit' (raw $:
                 a constant 1e4 denominator, so the ratio equals the level).
    lag_ta_min   T3 threshold on lagged trading assets in $k (S3).
    use_q1       Q1 dummy in B4/B5 (S6 off).
    war_q1_shift WAR with a Q1 tangent shift (S6).
    window       rolling estimation window in quarters (S12: 16); None = expanding from `first`.
    exclude_train quarters whose A220_q is masked in every training window (S4: 2020Q1-Q2); scores still use
                 the unmasked truth panel.
    """
    first: str = '2009Q1'
    denom: str = 'trading_assets'
    lag_ta_min: float = W10.CS_LAG_TA_MIN
    use_q1: bool = True
    war_q1_shift: bool = False
    window: int = None
    exclude_train: tuple = field(default_factory=tuple)

    @property
    def denom_col(self):
        return DENOM_COLUMNS[self.denom]

    def first_at(self, origin):
        f = pd.Period(self.first, freq='Q')
        if self.window:
            f = max(f, pd.Period(origin, freq='Q') - self.window + 1)
        return f

    def is_primary_data(self, origin):
        return self.first_at(origin) == FIRST and not self.exclude_train and self.denom != 'unit'

    def as_config(self):
        return dict(first=self.first, denom=self.denom, lag_ta_min=self.lag_ta_min, use_q1=self.use_q1,
                    war_q1_shift=self.war_q1_shift, window=self.window, exclude_train=list(self.exclude_train))


PRIMARY = Spec()


def forecast_panel(panel, origin, spec=PRIMARY):
    """truncate(panel, origin) plus the spec's training restrictions (no-op copy-free for the primary)."""
    trunc = truncate(panel, origin)
    if spec.is_primary_data(origin):
        return trunc
    out = trunc.copy()
    f = spec.first_at(origin)
    if f > FIRST:
        out = presample_mask(out, f - 1, keep=tuple({'trading_assets', 'total_assets'}))
    if spec.exclude_train:
        out.loc[out.quarter.isin(pd.PeriodIndex(list(spec.exclude_train), freq='Q')), 'trading_revenue_q'] = np.nan
    if spec.denom == 'unit':
        out['unit_denom'] = 1e4
    return out


def _score(Q, y, scale):
    ok = np.isfinite(y) & np.all(np.isfinite(Q), axis=1) & np.isfinite(scale)
    S = np.full(len(y), np.nan)
    S[ok] = quantile_crps(Q[ok], y[ok]) / scale[ok]
    cov = np.full(len(y), np.nan)
    cov[ok] = coverage(Q[ok], y[ok], 0.9)
    return S, cov


# ── T2 ─────────────────────────────────────────────────────────────────────
def t2_forecasts(panel, population, origin, h, macro, members=MEMBERS, spec=PRIMARY, truth=None):
    """Member forecasts (USD) for `population` at origin; returns (fc, scale, floor).

    The case scale always comes from the truth panel (= panel unless a sensitivity masks training data)."""
    origin = pd.Period(origin, freq='Q')
    fp = forecast_panel(panel, origin, spec)
    population = list(population)
    W = B.Wide(fp, population, denom=spec.denom_col, first=str(spec.first_at(origin)))
    W.use_q1 = spec.use_q1
    t = W.idx(origin)
    sp = fp if (truth is None and spec.is_primary_data(origin)) else truncate(panel if truth is None else truth, origin)
    scale, floor = case_scale(sp, population, origin, set_=population)
    fc = B.run_members(W, t, h, 'usd', scale, macro, members=members)
    return fc, scale, floor


def t2_cases(panel, population, targets, macro, members=MEMBERS, h=1, keep_quantiles=False, spec=PRIMARY,
             truth=None):
    """Long table of (target, bank) cases for the given population: S_<m>, cov_<m> per member, scale, y."""
    rows, Qstore = [], {}
    truth_panel = panel if truth is None else truth
    for tq in targets:
        o = tq - h
        fc, scale, floor = t2_forecasts(panel, population, o, h, macro, members, spec, truth)
        y = W10.actual(truth_panel, population, tq)
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


def t2_epoch(panel, macro, epoch_origin, set_e, members=MEMBERS, previous=None, spec=PRIMARY, truth=None, h=1,
             keep=False):
    """Selection for one epoch on T2: walk-forward cases for S_e at the epoch's targets; settings.

    h > 1 (H1e): the same rule on h-step cases (origins target - h); keep=True also returns the member quantiles."""
    lo, hi = select.selection_epochs()[pd.Period(epoch_origin, freq='Q')]
    targets = pd.period_range(lo, hi, freq='Q')
    base = truncate(panel, epoch_origin)          # outcomes after the epoch origin cannot enter
    tb = None if truth is None else truncate(truth, epoch_origin)
    cases, Qstore = t2_cases(base, set_e, targets, macro, members, h=h, keep_quantiles=True, spec=spec, truth=tb)
    settings = select.select_settings(cases, members, epoch_origin, previous=previous,
                                      bary_quantiles=_bary_callable(cases, Qstore))
    return (settings, cases, Qstore) if keep else (settings, cases)


# ── T3 ─────────────────────────────────────────────────────────────────────
def cs_cases(panel, targets, macro, members=MEMBERS, with_war=False, spec=PRIMARY, truth=None, keep=False):
    """keep=True returns (cases, {(tq, m): Q}, {tq: (Q_war, war_info)})."""
    rows, Qstore, war = [], {}, {}
    truth_panel = panel if truth is None else truth
    pr = sets.add_ratio(truth_panel)
    for tq in targets:
        o = tq - 1
        fp = forecast_panel(panel, o, spec)
        first = str(spec.first_at(o))
        pop, scale, cfc = W10.cs_member_forecasts(fp, o, macro, members, lag_ta_min=spec.lag_ta_min, first=first,
                                                  use_q1=spec.use_q1)
        tgt = pr[pr.quarter.eq(tq) & pr.trading_assets_lag.ge(spec.lag_ta_min) & pr.trading_revenue_q.notna()]
        y = tgt.set_index('rssd_id').r.reindex(pop).to_numpy(float)
        rec = pd.DataFrame({'target_quarter': tq, 'origin': o, 'rssd_id': pop, 'y': y, 'scale': scale,
                            'has_actual': np.isfinite(y), 'row': np.arange(len(pop))})
        for m in members:
            Q = cfc[m][0]
            rec[f'S_{m}'], rec[f'cov_{m}'] = _score(Q, y, scale)
            rec[f'def_{m}'] = np.all(np.isfinite(Q), axis=1)
            if keep:
                Qstore[(tq, m)] = Q
        if with_war:
            Qw, info = W10.war_rm(fp, o, pop, lag_ta_min=spec.lag_ta_min, first_r=first, q1_shift=spec.war_q1_shift)
            rec['S_WAR'], rec['cov_WAR'] = _score(Qw, y, scale)
            rec['war_beta'], rec['war_rho'] = info['beta'], info['rho']
            if keep:
                war[tq] = (Qw, info)
        rows.append(rec)
    df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    return (df, Qstore, war) if keep else df


def cs_epoch(panel, macro, epoch_origin, members=MEMBERS, previous=None, spec=PRIMARY, truth=None):
    lo, hi = select.selection_epochs()[pd.Period(epoch_origin, freq='Q')]
    base = truncate(panel, epoch_origin)
    tb = None if truth is None else truncate(truth, epoch_origin)
    cases = cs_cases(base, pd.period_range(lo, hi, freq='Q'), macro, members, spec=spec, truth=tb)
    return select.select_settings(cases, members, epoch_origin, previous=previous), cases


# ── first freeze (burn-in only; no OOS target) ─────────────────────────────
def first_freeze(panel, macro, members=MEMBERS):
    """Epoch 0 at 2013Q4: S_2013Q4, member coverage on the 72 pseudo-OOS cases, settings. Burn-in only."""
    base = truncate(panel, FIRST_FREEZE)
    s0 = sets.exante_bank_set_rolling(base, FIRST_FREEZE)
    settings, cases = t2_epoch(base, macro, FIRST_FREEZE, s0, members)
    return dict(set=s0, coverage=member_coverage(cases, members), settings=settings, cases=cases)


def rolling_set_by_epoch(panel, epochs=select.EPOCH_ORIGINS):
    return {e: sets.exante_bank_set_rolling(truncate(panel, e), e) for e in epochs}


# ── primary walk-forward (OOS; called only from run.* after preflight) ─────────────────────────────
def primary(panel, macro, members=MEMBERS, epochs=select.EPOCH_ORIGINS, targets=TARGETS_H1, spec=PRIMARY,
            truth=None, set_by_epoch=None, hypotheses=('H1', 'H2'), store=False):
    """H1 and H2 matched-case tables over `targets` with annual re-selection. Returns dict.

    spec / truth / set_by_epoch / hypotheses are used by the sensitivities (defaults = the primary).
    store=True also returns every member's quantiles per scored case (T2 and T3), the epoch-0 T2 selection
    cases with quantiles (the pseudo-OOS pool before the first OOS target), and the WAR fits, so that the
    secondary family and the scoring-only sensitivities reuse the primary forecasts instead of refitting."""
    epochs = list(epochs)
    if set_by_epoch is None:
        set_by_epoch = rolling_set_by_epoch(panel, epochs)
    t2_set, cs_set, prev2, prev3, log = {}, {}, None, None, []
    st = dict(t2={}, cs={}, t2_sel0=None, settings={}) if store else None
    for k, e in enumerate(epochs):
        entry = dict(epoch=str(e), set_size=len(set_by_epoch[e]))
        if 'H1' in hypotheses:
            res = t2_epoch(panel, macro, e, set_by_epoch[e], members, previous=prev2, spec=spec, truth=truth,
                           keep=store)
            prev2 = res[0]
            if store and k == 0:
                st['t2_sel0'] = dict(cases=res[1], Q=res[2])
            entry['t2'] = prev2
        if 'H2' in hypotheses:
            prev3, _ = cs_epoch(panel, macro, e, members, previous=prev3, spec=spec, truth=truth)
            entry['cs'] = prev3
        t2_set[e], cs_set[e] = prev2, prev3
        log.append(entry)
        if store:
            st['settings'][e] = dict(t2=prev2, cs=prev3)
    h1_rows, h2_rows = [], []
    for tq in targets:
        e = select.epoch_for_target(tq, epochs)
        if 'H1' in hypotheses:
            stt = t2_set[e]
            cases, Qs = t2_cases(panel, set_by_epoch[e], [tq], macro, members, keep_quantiles=True, spec=spec,
                                 truth=truth)
            Qbar = ot_bary.widen(ot_bary.barycenter_1d([Qs[(tq, m)] for m in stt['trimmed']]), stt['s'])
            S_ot, cov_ot = _score(Qbar, cases.y.to_numpy(float), cases.scale.to_numpy(float))
            h1_rows.append(pd.DataFrame({'target_quarter': tq, 'rssd_id': cases.rssd_id, 'y': cases.y,
                                         'S_ot': S_ot, 'cov_ot': cov_ot, 'S_ref': cases[f"S_{stt['b_star']}"],
                                         'cov_ref': cases[f"cov_{stt['b_star']}"], 'ref': stt['b_star'],
                                         'epoch': str(e), 'scale_missing': ~np.isfinite(cases.scale)}))
            if store:
                st['t2'][tq] = dict(cases=cases, Q={m: Qs[(tq, m)] for m in members}, bary=Qbar, epoch=e)
        if 'H2' in hypotheses:
            res = cs_cases(panel, [tq], macro, members, with_war=True, spec=spec, truth=truth, keep=store)
            c3 = res[0] if store else res
            ref3 = cs_set[e]['b_star']
            h2_rows.append(pd.DataFrame({'target_quarter': tq, 'rssd_id': c3.rssd_id, 'y': c3.y, 'S_ot': c3.S_WAR,
                                         'cov_ot': c3.cov_WAR, 'S_ref': c3[f'S_{ref3}'], 'cov_ref': c3[f'cov_{ref3}'],
                                         'ref': ref3, 'epoch': str(e), 'beta': c3.war_beta, 'rho': c3.war_rho}))
            if store:
                Qw, info = res[2][tq]
                st['cs'][tq] = dict(cases=c3, Q={m: res[1][(tq, m)] for m in members}, war=Qw, info=info, epoch=e)
    cols = ['target_quarter', 'rssd_id', 'y', 'S_ot', 'cov_ot', 'S_ref', 'cov_ref', 'ref', 'epoch']
    h1 = pd.concat(h1_rows, ignore_index=True) if h1_rows else pd.DataFrame(columns=cols)
    h2 = pd.concat(h2_rows, ignore_index=True) if h2_rows else pd.DataFrame(columns=cols)
    out = dict(h1=h1.dropna(subset=['S_ot', 'S_ref']), h2=h2.dropna(subset=['S_ot', 'S_ref']),
               h1_all=h1, h2_all=h2, selection_log=log, sets={str(k): v for k, v in set_by_epoch.items()})
    if store:
        out['store'] = st
    return out
