"""Pre-registered secondary family (prereg §4.1/§4.2 secondary variants, addendum v1.1 §4.3/§7), F1-F5 and
secondary metrics, on the v1.1 extended window. Non-gating: nothing here can change a primary verdict.

Family (Holm within family on the raw fixed-b test-C p-values; reported as "secondary"):
  H1b  CRPS-shrunk-weight barycenter of the epoch's trimmed members, widened by the epoch's s, vs B*      (T2)
  H1c  equal-weight linear pool of the epoch's trimmed members (no widening) vs B*                          (T2)
  H1d  BARY-EW on the industry total T1 (members B0, B1, B3, B4 on the level) vs B*_T1                      (T1)
  H1e  BARY-EW at h = 2, 3, 4 (three tests), settings re-selected per horizon, vs B*_h                       (T2)
  H2b  WAR-RM mapped to the T2 bank set in $ (q_tau x TA_(i,t)) vs B*                                       (T2)
  H2c  trimmed W2^2 on U19 of the WAR cross-section forecast vs persistence and vs climatology (two tests)  (T3)
  H2d  global Frechet regression of Q_(s+1) on (VIX, rates vol) + the WAR rank map vs B*_CS                  (T3)
  H2e  OT quantile-map recalibration of B* (PIT pool >= 100) vs B*                                          (T2)
  H2f  autoregressive OT map (scalar) + the WAR rank map vs B*_CS; N/A if it cannot run at the first origin (T3)
Every forecast is causal (data <= its origin); the reused primary forecasts come from walkforward_v1_1.primary
(store=True). Interpretations are listed in README "IMPLEMENTATION_NOTES (Phase B)".
"""
import numpy as np
import pandas as pd
from statement_forecast.combo import truncate

from . import baselines as B
from . import gate, ot_bary, ot_war, select, sets
from . import walkforward as W10
from . import walkforward_v1_1 as V
from .scoring import (U19, U19_IDX, U99, coverage, pinball, pit, quantile_crps, raw_case_scale, trimmed_w2sq)

FAMILY = ['H1b', 'H1c', 'H1d', 'H1e_h2', 'H1e_h3', 'H1e_h4', 'H2b', 'H2c_persistence', 'H2c_climatology', 'H2d',
          'H2e', 'H2f']
T1_MEMBERS = ['B0', 'B1', 'B3', 'B4']
T1_MIN_OWN = 2
H1B_N0 = 200
H2D_COVARIATES = ('vix', 'rates_rv')
H2E_MIN_PIT = 100
HORIZONS = (2, 3, 4)
F3_PERMS = 200
F3_SEED = 20261006
FROZEN_SCALE_WINDOW = ('2010Q1', '2013Q4')


# ── common evaluation ───────────────────────────────────────────────────────
def evaluate(cases, seed=gate.DM_SEED, R=gate.DM_R):
    """Matched cases (target_quarter, rssd_id, S_ot, S_ref[, cov_ot, cov_ref]) -> G, G_U, raw test-C p (fixed-b,
    M = floor(sqrt(T))), coverage, LOBO-min, counts. Fewer than 3 target quarters -> p NaN."""
    cases = cases.dropna(subset=['S_ot', 'S_ref'])
    if cases.empty:
        return dict(status='N/A', reason='no matched cases', n_targets=0, n_cases=0, p=np.nan, G=np.nan)
    pq = gate.per_quarter(cases)
    T = len(pq)
    G = float(pq.dbar.sum() / pq.Sbar_ref.sum())
    if T >= 3:
        g = gate.gain_v1_1(pq, seed, R)
        dm, G_U, p = g, g['G_U'], g['p']
    else:
        dm, G_U, p = None, np.nan, np.nan
    lb = gate.lobo(cases) if cases.rssd_id.nunique() > 1 else {}
    return dict(status='ok', n_targets=int(T), n_cases=int(len(cases)), G=G, G_U=float(G_U), p=float(p), dm=dm,
                coverage90=float(cases.cov_ot.mean()) if 'cov_ot' in cases else np.nan,
                coverage90_ref=float(cases.cov_ref.mean()) if 'cov_ref' in cases else np.nan,
                lobo_min=float(min(lb.values())) if lb else np.nan,
                first_target=str(pq.index.min()), last_target=str(pq.index.max()))


def holm_family(results):
    """Holm within the secondary family over members with a finite raw p; N/A members do not count."""
    pv = {k: v['p'] for k, v in results.items() if v.get('status') == 'ok' and np.isfinite(v.get('p', np.nan))}
    adj = gate.holm(pv)
    for k, v in results.items():
        v['p_holm_secondary'] = adj.get(k, np.nan)
    return dict(members=sorted(pv), m=len(pv))


def _frame(tq, ids, y, S_ot, cov_ot, S_ref, cov_ref, **extra):
    d = pd.DataFrame({'target_quarter': tq, 'rssd_id': list(ids), 'y': np.asarray(y, float),
                      'S_ot': S_ot, 'cov_ot': cov_ot, 'S_ref': np.asarray(S_ref, float),
                      'cov_ref': np.asarray(cov_ref, float)})
    for k, v in extra.items():
        d[k] = v
    return d


def _concat(rows):
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(
        columns=['target_quarter', 'rssd_id', 'y', 'S_ot', 'cov_ot', 'S_ref', 'cov_ref'])


def _rows_ok(Qs):
    return np.all([np.all(np.isfinite(Q), axis=1) for Q in Qs], axis=0)


# ── pseudo-OOS pool on T2 (H1b weights, H2e PITs) ───────────────────────────
def t2_pool(store):
    """One walk-forward forecast per (target, bank): the epoch-0 selection cases (targets 2012Q3-2013Q4, set
    S_2013Q4) followed by the scored primary cases (target 2014Q1+, set in force). Returns (meta frame, {m: Q})."""
    metas, Qs = [], {}
    sel = store.get('t2_sel0')
    members = None
    if sel is not None:
        c = sel['cases']
        members = sorted({m for (_, m) in sel['Q']})
        metas.append(c[['target_quarter', 'rssd_id', 'y', 'scale']].reset_index(drop=True))
        for m in members:
            Qs.setdefault(m, []).append(np.vstack([sel['Q'][(tq, m)][r] for tq, r in zip(c.target_quarter, c.row)]))
    for tq in sorted(store['t2']):
        e = store['t2'][tq]
        members = members or sorted(e['Q'])
        metas.append(e['cases'][['target_quarter', 'rssd_id', 'y', 'scale']].reset_index(drop=True))
        for m in members:
            Qs.setdefault(m, []).append(e['Q'][m])
    meta = pd.concat(metas, ignore_index=True)
    return meta, {m: np.vstack(v) for m, v in Qs.items()}


# ── H1b / H1c / H2e (reuse the primary T2 forecasts) ────────────────────────
def h1b(store, n0=H1B_N0):
    meta, PQ = t2_pool(store)
    rows, log = [], []
    for tq in sorted(store['t2']):
        e = store['t2'][tq]
        st = store['settings'][e['epoch']]['t2']
        K = st['trimmed']
        ok = (meta.target_quarter < tq).to_numpy() & np.isfinite(meta.y.to_numpy(float)) \
            & np.isfinite(meta.scale.to_numpy(float)) & _rows_ok([PQ[m] for m in K])
        pool = np.stack([PQ[m][ok] for m in K])
        lam, info = ot_bary.shrunk_weights(pool, meta.y.to_numpy(float)[ok], meta.scale.to_numpy(float)[ok], n0)
        c = e['cases']
        Q = ot_bary.widen(ot_bary.barycenter_1d([e['Q'][m] for m in K], lam), st['s'])
        S, cov = V._score(Q, c.y.to_numpy(float), c.scale.to_numpy(float))
        rows.append(_frame(tq, c.rssd_id, c.y, S, cov, c[f"S_{st['b_star']}"], c[f"cov_{st['b_star']}"]))
        log.append(dict(target=str(tq), members=K, weights=[float(x) for x in lam], kappa=info['kappa'], n=info['n']))
    return _concat(rows), dict(weights=log)


def h1c(store):
    rows = []
    for tq in sorted(store['t2']):
        e = store['t2'][tq]
        st = store['settings'][e['epoch']]['t2']
        K, c = st['trimmed'], e['cases']
        Qk = [e['Q'][m] for m in K]
        ok = _rows_ok(Qk)
        Q = np.full_like(Qk[0], np.nan)
        if ok.any():
            Q[ok] = ot_bary.linear_pool_quantiles_fast(np.stack([q[ok] for q in Qk]))
        S, cov = V._score(Q, c.y.to_numpy(float), c.scale.to_numpy(float))
        rows.append(_frame(tq, c.rssd_id, c.y, S, cov, c[f"S_{st['b_star']}"], c[f"cov_{st['b_star']}"]))
    return _concat(rows), {}


def h2e(store, min_pit=H2E_MIN_PIT):
    meta, PQ = t2_pool(store)
    rows, log = [], []
    for tq in sorted(store['t2']):
        e = store['t2'][tq]
        st = store['settings'][e['epoch']]['t2']
        b = st['b_star']
        ok = (meta.target_quarter < tq).to_numpy() & np.isfinite(meta.y.to_numpy(float)) & _rows_ok([PQ[b]])
        pits = pit(PQ[b][ok], meta.y.to_numpy(float)[ok]) if ok.any() else np.array([])
        c = e['cases']
        Qb = e['Q'][b]
        active = len(pits) >= min_pit
        Q = np.full_like(Qb, np.nan)
        rok = _rows_ok([Qb])
        if active and rok.any():
            Q[rok] = ot_war.ot_recalibrate(Qb[rok], pits)
        S, cov = V._score(Q, c.y.to_numpy(float), c.scale.to_numpy(float))
        rows.append(_frame(tq, c.rssd_id, c.y, S, cov, c[f'S_{b}'], c[f'cov_{b}']))
        log.append(dict(target=str(tq), b_star=b, n_pit=int(len(pits)), active=bool(active)))
    return _concat(rows), dict(activation=log)


# ── H2b / H2c / H2d / H2f (reuse the primary WAR fits) ──────────────────────
def h2b(store, panel):
    """WAR-RM ratio quantiles for each T2 bank with a rank at the origin, x TA_(i,t) / 1e4 ($k), vs B* in $."""
    ta = panel.set_index(['rssd_id', 'quarter']).trading_assets
    rows = []
    for tq in sorted(store['t2']):
        if tq not in store['cs']:
            continue
        e = store['t2'][tq]
        st = store['settings'][e['epoch']]['t2']
        info = store['cs'][tq]['info']
        c = e['cases']
        o = tq - 1
        z = info['z_all'].reindex(c.rssd_id).to_numpy(float)
        D = ta.reindex(pd.MultiIndex.from_arrays([c.rssd_id, [o] * len(c)])).to_numpy(float)
        Q = np.full((len(c), len(U99)), np.nan)
        ok = np.isfinite(z) & (D > 0)
        if ok.any():
            Q[ok] = ot_war.rankmap_quantiles(info['Qhat'], z[ok], info['rho']) * D[ok, None] / 1e4
        S, cov = V._score(Q, c.y.to_numpy(float), c.scale.to_numpy(float))
        rows.append(_frame(tq, c.rssd_id, c.y, S, cov, c[f"S_{st['b_star']}"], c[f"cov_{st['b_star']}"]))
    return _concat(rows), {}


def realized_cs_quantiles(truth, tq, lag_ta_min=W10.CS_LAG_TA_MIN):
    pr = sets.add_ratio(truth[truth.quarter.between(tq - 1, tq)])
    cs = sets.cross_section(pr, tq, lag_ta_min)
    return ot_war.cs_quantiles(cs.r) if len(cs) else None


def h2c(store, truth):
    """One loss per target quarter (the cross-section is the unit): L = trimmed W2^2 on U19 to the realised
    Q_(t+1). Returns {'persistence': cases, 'climatology': cases}; S_ref = comparator loss, S_ot = WAR loss."""
    out = {'persistence': [], 'climatology': []}
    for tq in sorted(store['cs']):
        info = store['cs'][tq]['info']
        Qr = realized_cs_quantiles(truth, tq)
        if Qr is None:
            continue
        L_war = trimmed_w2sq(info['Qhat'], Qr)
        for name, Qc in [('persistence', info['Qt']), ('climatology', info['Qbar'])]:
            out[name].append(dict(target_quarter=tq, rssd_id=0, S_ot=L_war, S_ref=trimmed_w2sq(Qc, Qr),
                                  cov_ot=np.nan, cov_ref=np.nan))
    return {k: pd.DataFrame(v) for k, v in out.items()}


def _cs_mapped(store, tq, Qhat):
    """Rank-map a cross-section forecast Qhat to the T3 population of target tq with the primary's z and rho."""
    e = store['cs'][tq]
    info, c = e['info'], e['cases']
    z = info['z_all'].reindex(c.rssd_id).to_numpy(float)
    Q = np.full((len(c), len(U99)), np.nan)
    ok = np.isfinite(z)
    if ok.any():
        Q[ok] = ot_war.rankmap_quantiles(Qhat, z[ok], info['rho'])
    S, cov = V._score(Q, c.y.to_numpy(float), c.scale.to_numpy(float))
    ref = store['settings'][e['epoch']]['cs']['b_star']
    return _frame(tq, c.rssd_id, c.y, S, cov, c[f'S_{ref}'], c[f'cov_{ref}'])


def h2d(store, macro, covariates=H2D_COVARIATES):
    rows, log = [], []
    for tq in sorted(store['cs']):
        info = store['cs'][tq]['info']
        o = tq - 1
        Qd = info['Qd']
        pairs = [s for s in Qd if (s + 1) in Qd and (s + 1) <= o and s in macro.index]
        if o not in macro.index or len(pairs) < len(covariates) + 2:
            log.append(dict(target=str(tq), status='N/A', n_pairs=len(pairs)))
            continue
        X = macro.loc[pairs, list(covariates)].to_numpy(float)
        Qn = np.stack([Qd[s + 1] for s in pairs])
        Qhat = ot_war.frechet_regression(Qn, X, macro.loc[o, list(covariates)].to_numpy(float))
        rows.append(_cs_mapped(store, tq, Qhat))
        log.append(dict(target=str(tq), status='ok', n_pairs=len(pairs)))
    return _concat(rows), dict(fits=log)


def h2f(store):
    tqs = sorted(store['cs'])
    if not tqs:
        return pd.DataFrame(), dict(status='N/A', reason='no targets')
    rows, log = [], []
    for k, tq in enumerate(tqs):
        info = store['cs'][tq]['info']
        try:
            Qhat, fit = ot_war.ar_map_forecast(info['Qd'], tq - 1)
        except (ValueError, np.linalg.LinAlgError) as err:
            if k == 0:
                return pd.DataFrame(), dict(status='N/A', reason=f'does not run at the first origin: {err}')
            log.append(dict(target=str(tq), status='failed', reason=str(err)))
            continue
        rows.append(_cs_mapped(store, tq, Qhat))
        log.append(dict(target=str(tq), status='ok', **fit))
    return _concat(rows), dict(status='ok', fits=log)


# ── H1d: industry total T1 ──────────────────────────────────────────────────
def t1_series(panel):
    """T1 as a one-'bank' panel (rssd_id 0): sum of A220_q over filers with non-null A220_q at t (after the guard,
    tiered exclusion and the pre-sample mask already applied to `panel`). trading_assets is a constant 1e4 so
    that the ratio-space members (B2-B4) operate on the level itself."""
    s = panel.groupby('quarter').trading_revenue_q.sum(min_count=1)
    qs = pd.period_range(panel.quarter.min(), panel.quarter.max(), freq='Q')
    return pd.DataFrame({'rssd_id': 0, 'quarter': qs, 'report_date': qs.end_time.normalize(),
                         'trading_revenue_q': s.reindex(qs).to_numpy(float),
                         'trading_assets': 1e4, 'total_assets': 1e4})


def t1_cases(t1, targets, members=T1_MEMBERS, frozen_scale=None):
    rows, Qstore = [], {}
    for tq in targets:
        o = tq - 1
        fp = truncate(t1, o)
        W = B.Wide(fp, [0], first=str(V.FIRST))
        W.min_own = T1_MIN_OWN
        scale = raw_case_scale(fp, [0], o)              # trailing-16 MAD of the series at the origin
        fc = B.run_members(W, W.idx(o), 1, 'usd', np.array([np.nan]), None, members=members)
        y = W10.actual(t1, [0], tq)
        rec = pd.DataFrame({'target_quarter': tq, 'origin': o, 'rssd_id': [0], 'y': y, 'scale': scale,
                            'has_actual': np.isfinite(y), 'row': [0]})
        for m in members:
            rec[f'S_{m}'], rec[f'cov_{m}'] = V._score(fc[m][0], y, scale)
            rec[f'def_{m}'] = np.all(np.isfinite(fc[m][0]), axis=1)
            Qstore[(tq, m)] = fc[m][0]
        rec['b4_fallback'] = bool(fc['B4'][1].get('fallback', [False])[0]) if 'B4' in fc else False
        rows.append(rec)
    return pd.concat(rows, ignore_index=True), Qstore


def h1d(panel, epochs=select.EPOCH_ORIGINS, targets=V.TARGETS_H1, members=T1_MEMBERS):
    """BARY-EW on T1 with annual re-selection (same rule as T2) vs B*_T1. Returns (cases, info)."""
    t1 = t1_series(panel)
    settings, prev, log = {}, None, []
    for e in epochs:
        lo, hi = select.selection_epochs()[e]
        cases, Q = t1_cases(truncate(t1, e), pd.period_range(lo, hi, freq='Q'), members)
        prev = select.select_settings(cases, members, e, previous=prev, bary_quantiles=V._bary_callable(cases, Q))
        settings[e] = prev
        log.append(dict(epoch=str(e), **{k: prev[k] for k in ('b_star', 'trimmed', 's', 'inherited')}))
    rows, raw = [], []
    for tq in targets:
        e = select.epoch_for_target(tq, epochs)
        st = settings[e]
        c, Q = t1_cases(t1, [tq], members)
        Qb = ot_bary.widen(ot_bary.barycenter_1d([Q[(tq, m)] for m in st['trimmed']]), st['s'])
        S, cov = V._score(Qb, c.y.to_numpy(float), c.scale.to_numpy(float))
        rows.append(_frame(tq, [0], c.y, S, cov, c[f"S_{st['b_star']}"], c[f"cov_{st['b_star']}"]))
        Qr = Q[(tq, st['b_star'])]
        raw.append(dict(target_quarter=tq, y=float(c.y.iloc[0]), scale=float(c.scale.iloc[0]),
                        crps_ot=float(quantile_crps(Qb, c.y.to_numpy(float))[0]),
                        crps_ref=float(quantile_crps(Qr, c.y.to_numpy(float))[0]),
                        mae_ot_usd=float(abs(c.y.iloc[0] - Qb[0, 49])), mae_ref_usd=float(abs(c.y.iloc[0] - Qr[0, 49])),
                        b4_fallback=bool(c.b4_fallback.iloc[0])))
    return _concat(rows), dict(selection=log, settings=settings, raw=pd.DataFrame(raw),
                                                    b4_fallbacks=int(sum(r['b4_fallback'] for r in raw)))


def t1_frozen_scale(panel, window=FROZEN_SCALE_WINDOW):
    t1 = t1_series(panel)
    w = t1[t1.quarter.between(pd.Period(window[0], freq='Q'), pd.Period(window[1], freq='Q'))]
    return B.mad(w.trading_revenue_q)


# ── H1e: BARY-EW at h = 2, 3, 4 ─────────────────────────────────────────────
def h1e_targets(h, last_target=V.TARGETS_H1[-1]):
    """Origins 2013Q4 .. last_target - h (49/48/47 targets for h = 2/3/4)."""
    origins = pd.period_range(V.FIRST_FREEZE, pd.Period(last_target, freq='Q') - h, freq='Q')
    return origins + h


def h1e(panel, macro, h, epochs=select.EPOCH_ORIGINS, targets=None, members=V.MEMBERS, set_by_epoch=None):
    """Per-horizon selection on h-step walk-forward cases of S_e with targets <= e; the target's settings and set
    are those of the epoch e = last Q4 <= origin (= target - h). B6 is one-step only, so the 80% coverage rule
    drops it at every epoch (logged)."""
    epochs = list(epochs)
    targets = h1e_targets(h) if targets is None else targets
    if set_by_epoch is None:
        set_by_epoch = V.rolling_set_by_epoch(panel, epochs)
    settings, prev, log = {}, None, []
    for e in epochs:
        prev, _ = V.t2_epoch(panel, macro, e, set_by_epoch[e], members, previous=prev, h=h)
        settings[e] = prev
        log.append(dict(epoch=str(e), **{k: prev[k] for k in ('b_star', 'trimmed', 's', 'inherited',
                                                               'excluded_low_coverage')}))
    rows = []
    for tq in targets:
        e = sets.set_origin(tq - h)
        if e not in settings:
            continue
        st = settings[e]
        c, Q = V.t2_cases(panel, set_by_epoch[e], [tq], macro, members, h=h, keep_quantiles=True)
        Qb = ot_bary.widen(ot_bary.barycenter_1d([Q[(tq, m)] for m in st['trimmed']]), st['s'])
        S, cov = V._score(Qb, c.y.to_numpy(float), c.scale.to_numpy(float))
        rows.append(_frame(tq, c.rssd_id, c.y, S, cov, c[f"S_{st['b_star']}"], c[f"cov_{st['b_star']}"]))
    return _concat(rows), dict(h=h, selection=log)


# ── F1-F5 and secondary metrics ─────────────────────────────────────────────
def f3_placebo(store, n_perm=F3_PERMS, seed=F3_SEED):
    """Rank-permutation placebo: at every origin the origin ranks z are permuted across the banks of that
    quarter's cross-section; Qhat and rho are the primary's. G_placebo on the primary's matched H2 cases."""
    rng = np.random.default_rng(seed)
    tqs = sorted(store['cs'])
    base = []
    for tq in tqs:
        e = store['cs'][tq]
        c = e['cases']
        ref = store['settings'][e['epoch']]['cs']['b_star']
        base.append((tq, e, c, c[f'S_{ref}'].to_numpy(float), np.isfinite(c.S_WAR.to_numpy(float))))
    real = pd.concat([pd.DataFrame({'target_quarter': tq, 'rssd_id': c.rssd_id, 'S_ot': c.S_WAR, 'S_ref': Sref})
                      for tq, e, c, Sref, _ in base]).dropna()
    pq = gate.per_quarter(real)
    G_real = float(pq.dbar.sum() / pq.Sbar_ref.sum()) if len(pq) else np.nan
    Gs = []
    for _ in range(n_perm):
        parts = []
        for tq, e, c, Sref, okw in base:
            info = e['info']
            z_all = info['z_all']
            zp = pd.Series(rng.permutation(z_all.to_numpy()), index=z_all.index)
            z = zp.reindex(c.rssd_id).to_numpy(float)
            Q = np.full((len(c), len(U99)), np.nan)
            ok = np.isfinite(z) & okw
            if ok.any():
                Q[ok] = ot_war.rankmap_quantiles(info['Qhat'], z[ok], info['rho'])
            S, _ = V._score(Q, c.y.to_numpy(float), c.scale.to_numpy(float))
            parts.append(pd.DataFrame({'target_quarter': tq, 'rssd_id': c.rssd_id, 'S_ot': S, 'S_ref': Sref}))
        d = pd.concat(parts).dropna()
        p = gate.per_quarter(d)
        Gs.append(float(p.dbar.sum() / p.Sbar_ref.sum()) if len(p) else np.nan)
    Gs = np.asarray(Gs)
    ratio = float(np.nanmean(Gs) / G_real) if np.isfinite(G_real) and G_real != 0 else np.nan
    return dict(G_real=G_real, G_placebo_mean=float(np.nanmean(Gs)), G_placebo_p50=float(np.nanmedian(Gs)),
                share_perms_ge_80pct=float(np.mean(Gs >= 0.8 * G_real)) if np.isfinite(G_real) else np.nan,
                ratio_mean=ratio, n_perm=n_perm, seed=seed,
                reading=('rank persistence is not the mechanism' if np.isfinite(ratio) and G_real > 0 and ratio >= 0.8
                         else 'placebo below 80% of the real G' if np.isfinite(ratio) and G_real > 0
                         else 'undefined (real G <= 0)'))


def _metrics(Q, y, scale):
    ok = np.isfinite(y) & np.isfinite(scale) & np.all(np.isfinite(Q), axis=1)
    Q, y, s = Q[ok], y[ok], scale[ok]
    pb = pinball(Q[:, [4, 49, 94]], y, np.array([0.05, 0.5, 0.95])) / s[:, None]
    return ok, dict(pin05=pb[:, 0], pin50=pb[:, 1], pin95=pb[:, 2], mae=np.abs(y - Q[:, 49]) / s,
                    cov50=coverage(Q, y, 0.5).astype(float), cov90=coverage(Q, y, 0.9).astype(float),
                    pit=pit(Q, y))


def secondary_metrics(store, which):
    """Pinball (0.05, 0.5, 0.95) and MAE of the median (scaled), 50/90% coverage and 10-bin PIT histograms for
    the OT method and its reference on the primary's matched cases; equal weight per bank within a quarter, then
    across quarters (as the primary loss)."""
    out = {'ot': [], 'ref': []}
    src = store['t2'] if which == 'H1' else store['cs']
    for tq in sorted(src):
        e = src[tq]
        c = e['cases']
        if which == 'H1':
            st = store['settings'][e['epoch']]['t2']
            Qo, Qr = e['bary'], e['Q'][st['b_star']]
        else:
            st = store['settings'][e['epoch']]['cs']
            Qo, Qr = e['war'], e['Q'][st['b_star']]
        y, s = c.y.to_numpy(float), c.scale.to_numpy(float)
        both = _rows_ok([Qo, Qr]) & np.isfinite(y) & np.isfinite(s)
        for k, Q in [('ot', Qo), ('ref', Qr)]:
            _, m = _metrics(Q[both], y[both], s[both])
            out[k].append(pd.DataFrame(dict(target_quarter=tq, **m)))
    res = {}
    for k, parts in out.items():
        d = pd.concat(parts, ignore_index=True)
        g = d.groupby('target_quarter').mean()
        res[k] = {col: float(g[col].mean()) for col in ['pin05', 'pin50', 'pin95', 'mae', 'cov50', 'cov90']}
        res[k]['pit_hist10'] = np.histogram(d.pit, bins=10, range=(0, 1))[0].tolist()
        res[k]['n_cases'] = int(len(d))
    g_ot = pd.concat(out['ot']).groupby('target_quarter').mae.mean()
    g_ref = pd.concat(out['ref']).groupby('target_quarter').mae.mean()
    res['median_mae_gain'] = float((g_ref - g_ot).sum() / g_ref.sum()) if g_ref.sum() > 0 else np.nan
    return res


def falsification(primary_ev, results, store, h1_cases, h2_cases, metrics, f3=None):
    G1 = primary_ev['H1']['G']
    out = {}
    lp = results.get('H1c', {})
    out['F1'] = dict(G_linear_pool=lp.get('G', np.nan), G_bary=G1,
                     triggered=bool(np.isfinite(lp.get('G', np.nan)) and lp['G'] >= G1),
                     reading='combination helps; W2 geometry not shown to matter')
    beta = h2_cases.groupby('target_quarter').beta.first() if 'beta' in h2_cases else pd.Series(dtype=float)
    share = float(np.mean((beta <= 0) | (beta >= 1))) if len(beta) else np.nan
    out['F2'] = dict(n_origins=int(len(beta)), share_beta_at_boundary=share,
                     triggered=bool(np.isfinite(share) and share > 0.5),
                     reading='WAR collapsed to climatology/persistence; the §3 claim reduces to the rank map')
    out['F3'] = f3
    out['F4'] = {k: dict(lobo_min=primary_ev[k]['lobo_min'], triggered=bool(primary_ev[k]['G'] > 0 and
                                                                              primary_ev[k]['lobo_min'] <= 0))
                 for k in ('H1', 'H2')}
    cov_ref = float(h1_cases.cov_ref.mean()) if len(h1_cases) else np.nan
    mg = metrics['H1']['median_mae_gain']
    out['F5'] = dict(coverage90_b_star=cov_ref, median_mae_gain=mg,
                     triggered=bool(G1 > 0 and np.isfinite(cov_ref) and cov_ref < 0.75 and np.isfinite(mg) and mg <= 0),
                     reading='a calibration gain, not a location gain')
    return out
