"""Walk-forward engine for the primary hypotheses (prereg §3-§5).

Every forecast made at origin t is computed from `truncate(panel, t)` (hard
truncation, statement_forecast.combo.truncate); target actuals are looked up
separately and only for scoring. Frozen decisions (trim set, s, B*) are taken
once at FREEZE_ORIGIN from burn-in pseudo-OOS cases whose forecasts each use data
<= their own pseudo-origin.
"""
import numpy as np
import pandas as pd
from statement_forecast.combo import truncate

from . import baselines as B
from . import ot_bary, ot_war, sets
from .scoring import U99, coverage, quantile_crps

FREEZE_ORIGIN = pd.Period('2021Q4', freq='Q')
BURN_END = pd.Period('2021Q4', freq='Q')
PSEUDO_TARGETS = pd.period_range('2020Q2', '2021Q4', freq='Q')
OOS_ORIGINS = pd.period_range('2021Q4', '2026Q1', freq='Q')
CS_MIN_PRIOR_R = 8
CS_LAG_TA_MIN = 1e5


# ── data helpers ────────────────────────────────────────────────────────────
def actual(panel, rssd_ids, quarter, column='trading_revenue_q'):
    s = panel[panel.quarter.eq(quarter)].set_index('rssd_id')[column]
    return s.reindex(list(rssd_ids)).to_numpy(float)


def bank_scales(panel, banks, burn_end=BURN_END):
    """s_i = 1.4826 MAD(A220_q, 2018Q1..burn_end), frozen; uses rows <= burn_end only."""
    b = truncate(panel, burn_end)
    return np.array([B.mad(b.loc[b.rssd_id.eq(i), 'trading_revenue_q']) for i in banks])


def pool_scales_usd(trunc, banks, origin):
    """Pooling scale for pooled errors at an origin: MAD over 2018Q1..min(origin, burn-in end) (no look-ahead)."""
    return bank_scales(trunc, banks, min(origin, BURN_END))


# ── T2: ex-ante bank set, $ space ──────────────────────────────────────────
def t2_member_forecasts(panel, banks, origin, h, macro, members=B.MEMBERS):
    origin = pd.Period(origin, freq='Q')
    trunc = truncate(panel, origin)
    W = B.Wide(trunc, banks)
    t = W.idx(origin)
    pool = pool_scales_usd(trunc, banks, origin)
    return B.run_members(W, t, h, 'usd', pool, macro, members=members)


# ── T3: cross-section, ratio space ─────────────────────────────────────────
def cs_population(trunc, origin, lag_ta_min=CS_LAG_TA_MIN, min_prior=CS_MIN_PRIOR_R):
    """Banks eligible for an h=1 target at origin+1: TA(i, origin) >= threshold and >= min_prior r values <= origin.

    Membership of C_(t+1) also needs non-null A220 at t+1; that is the target's
    availability and is checked only at scoring time.
    """
    pr = sets.add_ratio(trunc)
    now = pr[pr.quarter.eq(origin) & pr.trading_assets.ge(lag_ta_min)]
    counts = pr[pr.quarter.le(origin)].groupby('rssd_id').r.count()
    return sorted([i for i in now.rssd_id if counts.get(i, 0) >= min_prior])


def cs_scales(W, t, banks_idx, floor_q=0.10):
    """s_i^r = 1.4826 MAD of the last 8 r values <= origin, floored at the 10th pct across these banks."""
    raw = np.array([B.mad(W.R[i, :t + 1][np.isfinite(W.R[i, :t + 1])][-8:]) for i in banks_idx])
    floor = np.nanquantile(raw, floor_q)
    return np.maximum(raw, floor), raw


def cs_membership(W, lag_ta_min=CS_LAG_TA_MIN):
    """(n, T) bool: bank in C_s (lagged TA >= threshold and non-null A220_q at s)."""
    return (W.Dlag >= lag_ta_min) & np.isfinite(W.Y)


def cs_member_forecasts(panel, origin, macro, members=B.MEMBERS, lag_ta_min=CS_LAG_TA_MIN):
    """Ratio-space baselines for the cross-section population at origin (h = 1)."""
    origin = pd.Period(origin, freq='Q')
    trunc = truncate(panel, origin)
    pop = cs_population(trunc, origin, lag_ta_min)
    pr = sets.add_ratio(trunc)
    ever = sorted(set(pr.loc[pr.trading_assets_lag.ge(lag_ta_min) & pr.trading_revenue_q.notna(), 'rssd_id']) | set(pop))
    W = B.Wide(trunc, ever)
    t = W.idx(origin)
    pos = [W.banks.index(i) for i in pop]
    scale, _ = cs_scales(W, t, pos)
    pool = np.full(len(W.banks), np.nan)
    pool[pos] = scale
    mask = cs_membership(W, lag_ta_min)
    out = {}
    for m in members:
        if m == 'B5':
            Q, info = B.b5_panel_qr(W, t, 1, 'ratio', pool, macro, train_mask=np.pad(mask, ((0, 0), (0, 1))))
        elif m == 'B6':
            Wp = B.Wide(trunc, pop)
            Q, info = B.b6_eb(Wp, Wp.idx(origin), 1, 'ratio', scale)
            out[m] = (Q, info)
            continue
        else:
            Q, info = B.run_members(_subset(W, pos), t, 1, 'ratio', scale, macro, members=[m])[m]
            out[m] = (Q, info)
            continue
        out[m] = (Q[pos], info)
    return pop, scale, out


def _subset(W, pos):
    """A shallow Wide restricted to rows `pos` (pooled-error pools then cover the population only)."""
    import copy
    S = copy.copy(W)
    S.banks = [W.banks[i] for i in pos]
    for a in ['Y', 'D', 'A', 'Dlag', 'R']:
        setattr(S, a, getattr(W, a)[pos])
    return S


def war_rm(panel, origin, pop, lag_ta_min=CS_LAG_TA_MIN, h=1):
    """H2 WAR-RM ratio quantiles for `pop` at origin; NaN rows for banks without a rank at the origin."""
    origin = pd.Period(origin, freq='Q')
    trunc = truncate(panel, origin)
    pr = sets.add_ratio(trunc)
    quarters = pd.period_range('2018Q2', origin, freq='Q')
    css = {s: sets.cross_section(pr, s, lag_ta_min) for s in quarters}
    Qs = np.stack([ot_war.cs_quantiles(css[s].r) for s in quarters])
    Qbar = ot_war.frechet_mean(Qs)
    beta, beta_raw, n_pairs = ot_war.war_beta(Qs, h)
    Qhat = ot_war.war_forecast(Qbar, Qs[-1], beta)
    zs = {s: pd.Series(ot_war.probit_ranks(css[s].r.to_numpy()), index=css[s].rssd_id.to_numpy()) for s in quarters}
    a, b = [], []
    for s in quarters:
        if s + h > origin:
            break
        common = zs[s].index.intersection(zs[s + h].index)
        a += list(zs[s][common])
        b += list(zs[s + h][common])
    rho, rho_raw, n_tr = ot_war.rank_rho(a, b)
    z_now = zs[origin].reindex(pop).to_numpy(float)
    Q = np.full((len(pop), len(U99)), np.nan)
    ok = np.isfinite(z_now)
    Q[ok] = ot_war.rankmap_quantiles(Qhat, z_now[ok], rho)
    return Q, dict(beta=beta, beta_raw=beta_raw, beta_pairs=n_pairs, rho=rho, rho_raw=rho_raw,
                   rho_transitions=n_tr, Qhat=Qhat, Qbar=Qbar, Qt=Qs[-1])


# ── scoring helpers ────────────────────────────────────────────────────────
def score_rows(Q, y, scale):
    ok = np.isfinite(y) & np.all(np.isfinite(Q), axis=1)
    S = np.full(len(y), np.nan)
    S[ok] = quantile_crps(Q[ok], y[ok]) / scale[ok]
    cov = np.full(len(y), np.nan)
    cov[ok] = coverage(Q[ok], y[ok], 0.9)
    return S, cov


def pooled_member_scores(records, members, matched=True):
    """records: list of dicts with 'S' {member: (n,) scaled CRPS}. Pooled mean per member.

    matched=True: only cases where every member has a score (intersection)."""
    S = {m: np.concatenate([r['S'][m] for r in records]) for m in members}
    if matched:
        ok = np.all([np.isfinite(S[m]) for m in members], axis=0)
        return {m: float(np.mean(S[m][ok])) for m in members}, int(ok.sum())
    return {m: float(np.nanmean(S[m])) for m in members}, {m: int(np.isfinite(S[m]).sum()) for m in members}


# ── frozen burn-in decisions (taken once, at FREEZE_ORIGIN) ─────────────────
POLICIES = ('matched', 'available', 'exclude_b6')


def _pooled(S_by_member, members, policy):
    """Pooled mean scaled CRPS per member under the burn-in policy (see design json)."""
    if policy == 'available':
        return ({m: float(np.nanmean(S_by_member[m])) for m in members},
                {m: int(np.isfinite(S_by_member[m]).sum()) for m in members})
    ok = np.all([np.isfinite(S_by_member[m]) for m in members], axis=0)
    return {m: float(np.mean(S_by_member[m][ok])) for m in members}, {m: int(ok.sum()) for m in members}


def freeze_decisions(panel, macro, policy, members=B.MEMBERS, lag_ta_min=CS_LAG_TA_MIN):
    """Trim set, widening s and B* (bank set) and B*_CS, from burn-in pseudo-OOS only.

    The panel is hard-truncated to FREEZE_ORIGIN before anything else, so the
    decisions cannot depend on later data. Each pseudo-forecast for target s+1
    uses truncate(panel, s).
    """
    if policy not in POLICIES:
        raise ValueError(f'burn-in policy {policy!r} not pre-registered; one of {POLICIES}')
    base = truncate(panel, FREEZE_ORIGIN)
    members = [m for m in members if not (policy == 'exclude_b6' and m == 'B6')]
    banks = sets.exante_bank_set(base)
    s_i = bank_scales(base, banks)
    S2 = {m: [] for m in members}
    Q2 = {m: [] for m in members}
    y2, sc2 = [], []
    S3 = {m: [] for m in members}
    for target in PSEUDO_TARGETS:
        o = target - 1
        fc = t2_member_forecasts(base, banks, o, 1, macro, members)
        y = actual(base, banks, target)
        for m in members:
            S, _ = score_rows(fc[m][0], y, s_i)
            S2[m].append(S)
            Q2[m].append(fc[m][0])
        y2.append(y)
        sc2.append(s_i)
        pop, scale, cfc = cs_member_forecasts(base, o, macro, members, lag_ta_min)
        pr = sets.add_ratio(base)
        yr = pr[pr.quarter.eq(target)].set_index('rssd_id').r.reindex(pop).to_numpy(float)
        for m in members:
            S, _ = score_rows(cfc[m][0], yr, scale)
            S3[m].append(S)
    S2 = {m: np.concatenate(v) for m, v in S2.items()}
    S3 = {m: np.concatenate(v) for m, v in S3.items()}
    Q2 = {m: np.concatenate(v) for m, v in Q2.items()}
    y2, sc2 = np.concatenate(y2), np.concatenate(sc2)
    t2_scores, t2_n = _pooled(S2, members, policy)
    kept = ot_bary.trim_members(t2_scores)
    ok = np.isfinite(y2) & np.all([np.all(np.isfinite(Q2[m]), axis=1) for m in kept], axis=0)
    Qbar = ot_bary.barycenter_1d([Q2[m][ok] for m in kept])
    s_best, s_scores = ot_bary.select_s(Qbar, y2[ok], sc2[ok])
    cs_scores, cs_n = _pooled(S3, members, policy)
    b_star = min(t2_scores, key=t2_scores.get)
    b_star_cs = min(cs_scores, key=cs_scores.get)
    return dict(freeze_origin=str(FREEZE_ORIGIN), policy=policy, members=members, bank_set=[int(b) for b in banks],
                bank_scales={int(b): float(v) for b, v in zip(banks, s_i)},
                t2_burnin_scores=t2_scores, t2_burnin_n=t2_n, trimmed_members=kept,
                bary_burnin_cases=int(ok.sum()), s=float(s_best), s_scores={str(k): v for k, v in s_scores.items()},
                b_star=b_star, cs_burnin_scores=cs_scores, cs_burnin_n=cs_n, b_star_cs=b_star_cs,
                pseudo_targets=[str(q) for q in PSEUDO_TARGETS])


# ── primary OOS walk-forward ───────────────────────────────────────────────
def h1_oos(panel, macro, frozen, origins=OOS_ORIGINS):
    """Bank-set cases for H1: every member, BARY-EW (trimmed, widened) and B*, scaled CRPS and 90% coverage."""
    banks, s_i = frozen['bank_set'], np.array([frozen['bank_scales'][b] for b in frozen['bank_set']])
    rows = []
    for o in origins:
        fc = t2_member_forecasts(panel, banks, o, 1, macro, frozen['members'])
        y = actual(panel, banks, o + 1)
        kept = frozen['trimmed_members']
        Qk = [fc[m][0] for m in kept]
        Qbar = ot_bary.widen(ot_bary.barycenter_1d(Qk), frozen['s'])
        Qpool = None
        res = {'BARY': Qbar, **{m: fc[m][0] for m in frozen['members']}}
        for name, Q in res.items():
            S, cov = score_rows(Q, y, s_i)
            for k, b in enumerate(banks):
                rows.append(dict(origin=o, target_quarter=o + 1, rssd_id=b, method=name, S=S[k], cov90=cov[k],
                                 y=y[k], fallback=bool(fc['B4'][1].get('fallback', np.zeros(len(banks), bool))[k])
                                 if name == 'B4' else False))
    return pd.DataFrame(rows)


def h2_oos(panel, macro, frozen, origins=OOS_ORIGINS, lag_ta_min=CS_LAG_TA_MIN):
    """Cross-section cases for H2: WAR-RM and every ratio-space member, scaled by s_i^r."""
    rows, params = [], []
    for o in origins:
        pop, scale, cfc = cs_member_forecasts(panel, o, macro, frozen['members'], lag_ta_min)
        Qw, info = war_rm(panel, o, pop, lag_ta_min)
        pr = sets.add_ratio(panel)
        tgt = pr[pr.quarter.eq(o + 1) & pr.trading_assets_lag.ge(lag_ta_min) & pr.trading_revenue_q.notna()]
        y = tgt.set_index('rssd_id').r.reindex(pop).to_numpy(float)
        params.append(dict(origin=str(o), beta=info['beta'], beta_raw=info['beta_raw'], beta_pairs=info['beta_pairs'],
                           rho=info['rho'], rho_raw=info['rho_raw'], rho_transitions=info['rho_transitions'],
                           n_population=len(pop)))
        for name, Q in {'WAR': Qw, **{m: cfc[m][0] for m in frozen['members']}}.items():
            S, cov = score_rows(Q, y, scale)
            for k, b in enumerate(pop):
                rows.append(dict(origin=o, target_quarter=o + 1, rssd_id=b, method=name, S=S[k], cov90=cov[k], y=y[k]))
    return pd.DataFrame(rows), pd.DataFrame(params)


def matched_cases(long, ot='BARY', ref='B0'):
    """Wide (target_quarter, rssd_id, S_ref, S_ot, cov_ot) on the intersection where both methods and the actual exist."""
    a = long[long.method.eq(ot)].set_index(['target_quarter', 'rssd_id'])
    b = long[long.method.eq(ref)].set_index(['target_quarter', 'rssd_id'])
    df = pd.DataFrame({'S_ot': a.S, 'S_ref': b.S.reindex(a.index), 'cov_ot': a.cov90,
                       'cov_ref': b.cov90.reindex(a.index), 'y': a.y}).reset_index()
    total = len(df)
    drops = dict(missing_target=int(df.y.isna().sum()),
                 missing_history=int((df.y.notna() & (df.S_ot.isna() | df.S_ref.isna())).sum()))
    df = df.dropna(subset=['S_ot', 'S_ref'])
    return df, dict(candidates=total, matched=len(df), **drops)
