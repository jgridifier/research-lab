"""Pre-registered sensitivities S1-S16, S4b, FB4 (prereg §5.6, addendum v1.1 §4.3/§7). Non-gating.

Each entry of PLAN is one registered execution (logged as its own trial by run.run_all_v1_1 *before* it runs).
kind = 'rerun'   : the full v1.1 walk-forward (annual re-selection, case scale) is repeated with one change;
       'rescore' : the primary's stored forecasts are re-aggregated / re-scored (no refit), because the variation
                   is defined on the evaluation, not the estimation (S5, S7, S10, S13, S14, S15, FB4).
Every result reports, per hypothesis, G, G_U, the raw fixed-b test-C p (M = floor(sqrt(T))), coverage, LOBO-min,
targets and cases, and a descriptive verdict_v1_1 computed with the raw p (labelled descriptive; never gating).
"""
import numpy as np
import pandas as pd

from . import gate, ot_bary, sets
from . import panel as P
from . import secondary_v1_1 as SEC
from . import walkforward_v1_1 as V
from .scoring import U19, U19_IDX, quantile_crps

FB4_EXCLUDE = ('2020Q1', '2020Q2')
S4_EXCLUDE = ('2020Q1', '2020Q2')
S3_THRESHOLDS = {'10m': 1e4, '50m': 5e4, '1bn': 1e6}
S8_TA_MIN = 1e8                     # $100bn in $k
S14_WINDOW = ('2010Q1', '2013Q4')


def summarize(cases):
    ev = SEC.evaluate(cases)
    if ev.get('status') == 'ok':
        c = cases.dropna(subset=['S_ot', 'S_ref'])
        lb = gate.lobo(c) if c.rssd_id.nunique() > 1 else {}
        sp = gate.subperiods(c) if c.rssd_id.nunique() > 1 else {}
        ev['subperiod_G'] = {k: v['G'] for k, v in sp.items()}
        ev['verdict_descriptive'] = (gate.verdict_v1_1(ev['p'], ev['G'], ev['G_U'], ev['coverage90'], lb,
                                                       ev['subperiod_G'], ev['n_targets'])
                                     if c.rssd_id.nunique() > 1 else 'n/a (single series)')
    ev.pop('dm', None)
    return ev


# ── plan ────────────────────────────────────────────────────────────────────
def _p(id_, variant, kind, hyp, **cfg):
    return dict(id=id_, variant=variant, kind=kind, hypotheses=list(hyp), config=cfg)


PLAN = [
    _p('S1', 'balanced_full_10m', 'rerun', ['H1'], set_rule='balanced', thr=1e4,
       note='look-ahead: |A220_q| >= $10m in every quarter 2009Q1..last'),
    _p('S1', 'balanced_full_100m', 'rerun', ['H1'], set_rule='balanced', thr=1e5,
       note='look-ahead: |A220_q| >= $100m in every quarter 2009Q1..last'),
    _p('S1', 'fixed_S2013Q4', 'rerun', ['H1'], set_rule='fixed_first_freeze', note='S_2013Q4 for every epoch'),
    _p('S2', 'total_assets', 'rerun', ['H1'], spec=dict(denom='total_assets')),
    _p('S2', 'raw_usd', 'rerun', ['H1'], spec=dict(denom='unit')),
    *[_p('S3', k, 'rerun', ['H2'], spec=dict(lag_ta_min=v)) for k, v in S3_THRESHOLDS.items()],
    _p('S4', 'exclude_2020Q1Q2_training', 'rerun', ['H1', 'H2'], spec=dict(exclude_train=S4_EXCLUDE)),
    _p('S4b', 'training_from_2010Q1', 'rerun', ['H1', 'H2'], spec=dict(first='2010Q1')),
    _p('S5', 'drop_merger_targets', 'rescore', ['H1', 'H2']),
    _p('S6', 'no_q1_dummy_war_q1_shift', 'rerun', ['H1', 'H2'], spec=dict(use_q1=False, war_q1_shift=True)),
    _p('S7', 'crps_u19', 'rescore', ['H1', 'H2']),
    _p('S8', 'ex_cva_dva_100bn', 'rerun', ['H1', 'H2'], target='A220 - K090 - K094 if TA_t >= $100bn'),
    _p('S9', 'macro_through_Dt', 'rerun', ['H1', 'H2'], macro='asof_rule=Dt'),
    _p('S10', 'leave_one_year_out', 'rescore', ['H1', 'H2']),
    _p('S11', 'entrant_rule_b_T1', 'rerun', ['H1d']),
    _p('S12', 'rolling_w16', 'rerun', ['H1', 'H2'], spec=dict(window=16)),
    _p('S13', 'settings_frozen_2013Q4', 'rescore', ['H1', 'H2']),
    _p('S14', 'frozen_burnin_scale', 'rescore', ['H1', 'H1d']),
    _p('S15', 'test_A_and_WPE', 'rescore', ['H1', 'H2']),
    _p('S16', 'b5_without_baa10y', 'rerun', ['H1', 'H2'], macro='drop baa'),
    _p('FB4', 'exclude_targets_2020Q1Q2', 'rescore', ['H1', 'H2']),
]


def plan_ids():
    return [f"{p['id']}:{p['variant']}" for p in PLAN]


# ── reruns ──────────────────────────────────────────────────────────────────
def s8_panel(panel, ta_min=S8_TA_MIN):
    """Target ex-CVA/DVA: A220_q - K090_q - K094_q where TA_t >= $100bn; missing K090/K094 count as 0 (memo
    items are blank before 2011Q1 and when not applicable). Sign convention as written in the prereg (UNVERIFIED
    against the form, per prereg §5.6)."""
    out = panel.copy()
    big = out.total_assets.ge(ta_min) & out.trading_revenue_q.notna()
    adj = out.trd_cva_counterparty_q.fillna(0) + out.trd_dva_own_q.fillna(0)
    out.loc[big, 'trading_revenue_q'] = out.loc[big, 'trading_revenue_q'] - adj[big]
    return out


def _sets(panel, epochs, rule, thr=1e4):
    if rule == 'balanced':
        s = sets.balanced_set(panel, thr=thr, first=str(V.FIRST))
        return {e: s for e in epochs}
    if rule == 'fixed_first_freeze':
        s = V.rolling_set_by_epoch(panel, [V.FIRST_FREEZE])[V.FIRST_FREEZE]
        return {e: s for e in epochs}
    return None


def run_rerun(item, ctx):
    cfg, hyp = item['config'], item['hypotheses']
    panel, macro, kw = ctx['panel'], ctx['macro'], ctx['engine_kw']
    epochs = kw.get('epochs', V.select.EPOCH_ORIGINS)
    if hyp == ['H1d']:                                            # S11
        cases, info = SEC.h1d(ctx['panel_rule_b'], epochs=epochs, targets=kw.get('targets', V.TARGETS_H1))
        return {'H1d': summarize(cases)}, dict(selection=info['selection'])
    spec = V.Spec(**{k: (tuple(v) if isinstance(v, (list, tuple)) else v) for k, v in cfg.get('spec', {}).items()})
    truth, set_by_epoch = None, None
    if 'set_rule' in cfg:
        set_by_epoch = _sets(panel, epochs, cfg['set_rule'], cfg.get('thr', 1e4))
        if set_by_epoch is not None and not len(next(iter(set_by_epoch.values()))):
            return {h: dict(status='N/A', reason='empty bank set') for h in hyp}, dict(set=[])
    run_panel = panel
    if item['id'] == 'S8':
        run_panel = s8_panel(panel)
        set_by_epoch = ctx['primary']['sets_periods']             # population unchanged; only the target changes
    if spec.exclude_train or spec.first != V.Spec().first:
        truth = panel                                              # training restricted; scores on the full truth
    if item['id'] == 'S9':
        macro = ctx['macro_dt']
    if item['id'] == 'S16':
        macro = macro.drop(columns=['baa'])
    res = V.primary(run_panel, macro, epochs=epochs, targets=kw.get('targets', V.TARGETS_H1), spec=spec,
                    truth=truth, set_by_epoch=set_by_epoch, hypotheses=tuple(hyp))
    out = {h: summarize(res[h.lower()]) for h in hyp}
    extra = dict(set_sizes={k: len(v) for k, v in res['sets'].items()},
                 selection=[{k: v for k, v in e.items() if k in ('epoch', 'set_size')} |
                            {h: {kk: e[h][kk] for kk in ('b_star', 'trimmed', 's', 'inherited')}
                             for h in ('t2', 'cs') if h in e and e[h]} for e in res['selection_log']])
    if set_by_epoch is not None and item['id'] == 'S1':
        extra['set'] = [int(x) for x in next(iter(set_by_epoch.values()))]
    return out, extra


# ── rescoring (primary forecasts reused) ────────────────────────────────────
def _merger_drop(panel):
    f = P.merger_flags(panel)
    f = f[f.flag]
    keys = set(zip(f.rssd_id, f.quarter)) | set(zip(f.rssd_id, f.quarter + 1))
    return keys


def _drop(cases, keys):
    m = np.array([(i, q) not in keys for i, q in zip(cases.rssd_id, cases.target_quarter)], bool)
    return cases[m]


def _rescore_u19(store, which):
    rows = []
    src = store['t2'] if which == 'H1' else store['cs']
    for tq in sorted(src):
        e = src[tq]
        c = e['cases']
        st = store['settings'][e['epoch']]['t2' if which == 'H1' else 'cs']
        Qo = e['bary'] if which == 'H1' else e['war']
        Qr = e['Q'][st['b_star']]
        y, s = c.y.to_numpy(float), c.scale.to_numpy(float)
        ok = np.isfinite(y) & np.isfinite(s) & SEC._rows_ok([Qo, Qr])
        So, Sr = np.full(len(c), np.nan), np.full(len(c), np.nan)
        So[ok] = quantile_crps(Qo[ok][:, U19_IDX], y[ok], U19) / s[ok]
        Sr[ok] = quantile_crps(Qr[ok][:, U19_IDX], y[ok], U19) / s[ok]
        rows.append(SEC._frame(tq, c.rssd_id, y, So, c.cov_WAR if which == 'H2' else V._score(Qo, y, s)[1],
                               Sr, c[f"cov_{st['b_star']}"]))
    return pd.concat(rows, ignore_index=True)


def _frozen_settings(store, which):
    e0 = min(store['settings'])
    st0 = store['settings'][e0]['t2' if which == 'H1' else 'cs']
    rows = []
    src = store['t2'] if which == 'H1' else store['cs']
    for tq in sorted(src):
        e = src[tq]
        c = e['cases']
        y, s = c.y.to_numpy(float), c.scale.to_numpy(float)
        if which == 'H1':
            Qo = ot_bary.widen(ot_bary.barycenter_1d([e['Q'][m] for m in st0['trimmed']]), st0['s'])
            So, co = V._score(Qo, y, s)
        else:
            So, co = c.S_WAR.to_numpy(float), c.cov_WAR.to_numpy(float)
        rows.append(SEC._frame(tq, c.rssd_id, y, So, co, c[f"S_{st0['b_star']}"], c[f"cov_{st0['b_star']}"]))
    return pd.concat(rows, ignore_index=True), dict(epoch=str(e0), b_star=st0['b_star'],
                                                    trimmed=st0.get('trimmed'), s=st0.get('s'))


def frozen_scales(panel, banks, window=S14_WINDOW, set0=None):
    """S14: s_i^F = 1.4826 MAD of A220_q over 2010Q1-2013Q4 (>= 12 values), floored at the 10th percentile over
    S_2013Q4. Banks without 12 values in the window get NaN here; the caller then uses their case scale at the
    first origin at which they are scored (frozen from then on)."""
    lo, hi = (pd.Period(x, freq='Q') for x in window)
    sub = panel[panel.quarter.between(lo, hi)]
    from .scoring import raw_case_scale
    n = len(pd.period_range(lo, hi, freq='Q'))
    raw = dict(zip(banks, raw_case_scale(sub, list(banks), hi, window=n, min_obs=12)))
    s0 = raw_case_scale(sub, list(set0), hi, window=n, min_obs=12) if set0 is not None else np.array(list(raw.values()))
    s0 = s0[np.isfinite(s0)]
    floor = float(np.quantile(s0, 0.10)) if len(s0) else np.nan
    return {b: (max(v, floor) if np.isfinite(v) else np.nan) for b, v in raw.items()}, floor


def _rescale_h1(store, panel):
    tqs = sorted(store['t2'])
    banks = sorted({int(b) for tq in tqs for b in store['t2'][tq]['cases'].rssd_id})
    set0 = V.rolling_set_by_epoch(panel, [V.FIRST_FREEZE])[V.FIRST_FREEZE]
    sF, floor = frozen_scales(panel, banks, set0=set0)
    fallback = {}
    rows = []
    for tq in tqs:
        e = store['t2'][tq]
        c = e['cases']
        st = store['settings'][e['epoch']]['t2']
        sc = []
        for b, s in zip(c.rssd_id, c.scale):
            v = sF.get(int(b), np.nan)
            if not np.isfinite(v) and np.isfinite(s):
                v = fallback.setdefault(int(b), float(s))
            sc.append(v)
        sc = np.asarray(sc, float)
        factor = c.scale.to_numpy(float) / sc
        So = V._score(e['bary'], c.y.to_numpy(float), c.scale.to_numpy(float))[0] * factor
        Sr = c[f"S_{st['b_star']}"].to_numpy(float) * factor
        rows.append(SEC._frame(tq, c.rssd_id, c.y, So, V._score(e['bary'], c.y.to_numpy(float),
                                                                    c.scale.to_numpy(float))[1],
                               Sr, c[f"cov_{st['b_star']}"]))
    return pd.concat(rows, ignore_index=True), dict(floor=floor, n_banks_frozen=int(np.isfinite(list(sF.values())).sum()),
                                                    n_banks_first_origin_scale=len(fallback))


def run_rescore(item, ctx):
    pr, store, panel = ctx['primary'], ctx['primary']['store'], ctx['panel']
    h1, h2 = pr['h1'], pr['h2']
    i = item['id']
    if i == 'S5':
        keys = _merger_drop(panel)
        return {'H1': summarize(_drop(h1, keys)), 'H2': summarize(_drop(h2, keys))}, dict(n_flagged_keys=len(keys))
    if i == 'S7':
        return {'H1': summarize(_rescore_u19(store, 'H1')), 'H2': summarize(_rescore_u19(store, 'H2'))}, {}
    if i == 'S10':
        out = {}
        for h, c in [('H1', h1), ('H2', h2)]:
            years = c.target_quarter.map(lambda q: q.year)
            out[h] = {int(y): summarize(c[years.ne(y)]) for y in sorted(years.unique())}
        return out, {}
    if i == 'S13':
        a, ia = _frozen_settings(store, 'H1')
        b, ib = _frozen_settings(store, 'H2')
        return {'H1': summarize(a), 'H2': summarize(b)}, dict(H1_settings=ia, H2_settings=ib)
    if i == 'S14':
        a, info = _rescale_h1(store, panel)
        out = {'H1': summarize(a)}
        h1d_raw = ctx.get('h1d_raw')
        if h1d_raw is not None and len(h1d_raw):
            sF = SEC.t1_frozen_scale(panel)
            d = pd.DataFrame(dict(target_quarter=h1d_raw.target_quarter, rssd_id=0, S_ot=h1d_raw.crps_ot / sF,
                                  S_ref=h1d_raw.crps_ref / sF))
            out['H1d'] = summarize(d)
            info['t1_frozen_scale'] = float(sF)
        return out, info
    if i == 'S15':
        from y9c.forecast import clustered_dm
        out = {}
        for h, c in [('H1', h1), ('H2', h2)]:
            pq = gate.per_quarter(c)
            d = pq.dbar.to_numpy()
            cd = clustered_dm((c.S_ref - c.S_ot).to_numpy(float), c.target_quarter.astype(str).to_numpy(),
                              negative='ref', positive='ot')
            out[h] = dict(test_A=gate.panel_dm(d, 1), wpe=gate.fixed_m_dm(d), clustered_dm_cr1=cd)
        return out, {}
    if i == 'FB4':
        ex = pd.PeriodIndex(list(FB4_EXCLUDE), freq='Q')
        return {'H1': summarize(h1[~h1.target_quarter.isin(ex)]), 'H2': summarize(h2[~h2.target_quarter.isin(ex)])}, \
            dict(see_also=['S4b:training_from_2010Q1', 'S10:leave_one_year_out'])
    raise KeyError(i)


def run_item(item, ctx):
    return run_rerun(item, ctx) if item['kind'] == 'rerun' else run_rescore(item, ctx)
