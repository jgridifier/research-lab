"""Phase B sensitivities (S1-S16, S4b, FB4) on SYNTHETIC data only."""
import numpy as np
import pandas as pd
import pytest
from trading_ot import baselines as B, panel as P, select, walkforward_v1_1 as V
from trading_ot import sensitivity_v1_1 as SENS
from trading_ot.scoring import U19, U19_IDX, quantile_crps

EPOCHS = select.EPOCH_ORIGINS[:2]
TARGETS = pd.period_range('2014Q1', '2015Q4', freq='Q')


@pytest.fixture(scope='module')
def prim(panel11, macro11):
    return V.primary(panel11, macro11, epochs=EPOCHS, targets=TARGETS, store=True)


def test_plan_covers_registered_ids():
    ids = {p['id'] for p in SENS.PLAN}
    want = {f'S{k}' for k in range(1, 17)} | {'S4b', 'FB4'}
    assert want <= ids
    s1 = [p['variant'] for p in SENS.PLAN if p['id'] == 'S1']
    assert 'fixed_S2013Q4' in s1 and len(s1) == 3
    assert [p['hypotheses'] for p in SENS.PLAN if p['id'] == 'S11'] == [['H1d']]     # rule (b): T1 only
    assert len(set(SENS.plan_ids())) == len(SENS.PLAN)


def test_primary_spec_is_identity(panel11):
    o = pd.Period('2014Q2', freq='Q')
    fp = V.forecast_panel(panel11, o)
    pd.testing.assert_frame_equal(fp, panel11[panel11.quarter.le(o)])


def test_forecast_panel_masks(panel11):
    o = pd.Period('2021Q2', freq='Q')
    s4 = V.forecast_panel(panel11, o, V.Spec(exclude_train=('2020Q1', '2020Q2')))
    m = s4.quarter.isin(pd.PeriodIndex(['2020Q1', '2020Q2'], freq='Q'))
    assert s4.loc[m, 'trading_revenue_q'].isna().all() and s4.loc[~m, 'trading_revenue_q'].notna().any()
    s4b = V.forecast_panel(panel11, o, V.Spec(first='2010Q1'))
    pre = s4b.quarter.le(pd.Period('2009Q4', freq='Q'))
    assert s4b.loc[pre, 'trading_revenue_q'].isna().all()
    assert s4b.loc[s4b.quarter.eq(pd.Period('2009Q4', freq='Q')), 'trading_assets'].notna().all()
    s12 = V.forecast_panel(panel11, o, V.Spec(window=16))
    assert V.Spec(window=16).first_at(o) == o - 15
    assert s12.loc[s12.quarter.lt(o - 15), 'trading_revenue_q'].isna().all()
    assert s12.loc[s12.quarter.eq(o - 16), 'trading_assets'].notna().all()
    raw = V.forecast_panel(panel11, o, V.Spec(denom='unit'))
    assert (raw.unit_denom == 1e4).all()


def test_masked_training_keeps_truth_and_scale(panel11, macro11):
    pop = V.rolling_set_by_epoch(panel11, [EPOCHS[1]])[EPOCHS[1]]
    tq = [pd.Period('2015Q2', freq='Q')]
    base = V.t2_cases(panel11, pop, tq, macro11)
    s4 = V.t2_cases(panel11, pop, tq, macro11, spec=V.Spec(first='2010Q1'), truth=panel11)
    assert np.allclose(base.y, s4.y, equal_nan=True) and np.allclose(base.scale, s4.scale, equal_nan=True)
    assert not np.allclose(base.S_B4, s4.S_B4, equal_nan=True)           # training changed


def test_q1_dummy_off(panel11):
    pop = V.rolling_set_by_epoch(panel11, [EPOCHS[0]])[EPOCHS[0]]
    tr = panel11[panel11.quarter.le(pd.Period('2014Q4', freq='Q'))]
    W = B.Wide(tr, pop, first='2009Q1')
    t = W.idx('2014Q4')
    on, _ = B.b4_ar1q1(W, t, 1, 'ratio', np.ones(len(pop)))
    W.use_q1 = False
    off, _ = B.b4_ar1q1(W, t, 1, 'ratio', np.ones(len(pop)))
    i = 0
    s = np.arange(0, t)
    x, y = W.R[i, s], W.R[i, s + 1]
    ok = np.isfinite(x) & np.isfinite(y)
    coef = np.polyfit(x[ok], y[ok], 1)
    assert off[i, 49] == pytest.approx(coef[0] * W.R[i, t] + coef[1] + np.median(y[ok] - np.polyval(coef, x[ok])),
                                       rel=1e-6)
    assert not np.allclose(on, off)


def test_s8_panel(panel11):
    adj = SENS.s8_panel(panel11)
    big = panel11.total_assets.ge(SENS.S8_TA_MIN) & panel11.trading_revenue_q.notna()
    pre = panel11.quarter.lt(pd.Period('2011Q1', freq='Q'))
    k = panel11.trd_cva_counterparty_q.fillna(0) + panel11.trd_dva_own_q.fillna(0)
    do = big & ~pre
    assert np.allclose(adj.trading_revenue_q[do], (panel11.trading_revenue_q - k)[do])
    assert np.allclose(adj.trading_revenue_q[~do], panel11.trading_revenue_q[~do], equal_nan=True)
    assert (adj.s8_adjusted == do).all() and (adj.s8_unadjusted_pre2011 == (big & pre)).all()
    assert do.any() and (big & pre).any()                       # pre-2011 big-bank rows exist and stay unadjusted


def test_rescore_labels():
    lab = {p['id']: p['config'].get('label') for p in SENS.PLAN}
    assert lab['S7'] == lab['S14'] == 'rescore, no re-selection'
    s8 = next(p for p in SENS.PLAN if p['id'] == 'S8')['config']
    assert 'before 2011Q1 are unadjusted' in s8['label'] and 'March 2012' in s8['sign']


def test_s14_frozen_scales(panel11):
    s0 = V.rolling_set_by_epoch(panel11, [V.FIRST_FREEZE])[V.FIRST_FREEZE]
    sF, floor = SENS.frozen_scales(panel11, s0, set0=s0)
    b = s0[0]
    x = panel11[(panel11.rssd_id == b) & panel11.quarter.between(pd.Period('2010Q1', freq='Q'),
                                                                   pd.Period('2013Q4', freq='Q'))].trading_revenue_q
    assert sF[b] == pytest.approx(max(B.mad(x), floor))
    assert all(v >= floor for v in sF.values())


def test_s5_drop_keys(panel11):
    keys = SENS._merger_drop(panel11)
    f = P.merger_flags(panel11)
    f = f[f.flag]
    for i, q in zip(f.rssd_id, f.quarter):
        assert (i, q) in keys and (i, q + 1) in keys


def test_rescore_u19_and_frozen_settings(prim):
    st = prim['store']
    u = SENS._rescore_u19(st, 'H1')
    tq = TARGETS[0]
    e = st['t2'][tq]
    c = e['cases']
    ok = np.isfinite(c.y) & np.isfinite(c.scale) & np.all(np.isfinite(e['bary']), axis=1)
    want = quantile_crps(e['bary'][ok][:, U19_IDX], c.y[ok].to_numpy(), U19) / c.scale[ok].to_numpy()
    assert np.allclose(u[u.target_quarter.eq(tq)].S_ot.to_numpy()[ok.to_numpy()], want)
    fz, info = SENS._frozen_settings(st, 'H1')
    assert info['epoch'] == '2013Q4'
    h = fz[fz.target_quarter.eq(TARGETS[-1])]
    b0 = st['settings'][EPOCHS[0]]['t2']['b_star']
    assert np.allclose(h.S_ref, st['t2'][TARGETS[-1]]['cases'][f'S_{b0}'], equal_nan=True)


def test_rescore_items_run(prim, panel11, macro11):
    ctx = dict(panel=panel11, macro=macro11, engine_kw=dict(epochs=EPOCHS, targets=TARGETS), primary=prim,
               h1d_raw=None)
    for item in SENS.PLAN:
        if item['kind'] != 'rescore':
            continue
        out, _ = SENS.run_item(item, ctx)
        assert set(out) == set(item['hypotheses']) - ({'H1d'} if ctx['h1d_raw'] is None else set())
    fb4 = next(p for p in SENS.PLAN if p['id'] == 'FB4')
    out, _ = SENS.run_item(fb4, ctx)
    assert out['H1']['G'] == pytest.approx(SENS.summarize(prim['h1'])['G'])   # no 2020 targets in 2014-15


def test_rerun_s12_and_s3(prim, panel11, macro11):
    ctx = dict(panel=panel11, macro=macro11, engine_kw=dict(epochs=EPOCHS[:1], targets=TARGETS[:3]), primary=prim)
    s12 = next(p for p in SENS.PLAN if p['id'] == 'S12')
    out, extra = SENS.run_item(s12, ctx)
    assert out['H1']['status'] == 'ok' and out['H2']['status'] == 'ok'
    s3 = next(p for p in SENS.PLAN if p['id'] == 'S3' and p['variant'] == '1bn')
    out, _ = SENS.run_item(s3, ctx)
    assert set(out) == {'H2'}
