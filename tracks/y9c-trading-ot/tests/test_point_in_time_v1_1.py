"""Addendum §5.3 tests 2, 3, 12 and 15.

Deviation from the addendum's literal test 3 (reported in the PR): on REAL data, forecasts are checked
only at pseudo-origins <= 2013Q3, because a forecast made at an origin >= 2013Q4 is an OOS forecast and
the build is not authorized to compute any. At the addendum's origins {2013Q4, 2016Q2, 2016Q3}, sets,
case scales and the CS population are checked on real data (no forecasts); forecasts, selection and
scales at those origins are checked on the synthetic 2008-2026 panel.
"""
import numpy as np
import pandas as pd
import pytest
from trading_ot import panel as P, sets as S, walkforward_v1_1 as V, walkforward as W10
from trading_ot.scoring import case_scale
from conftest import prepared_v1_1, real_panel_v1_1, to_panel

Q = lambda s: pd.Period(s, freq='Q')
ORIGINS = ['2013Q4', '2016Q2', '2016Q3']


def perturb_raw_after(raw, o, seed):
    """Real-panel perturbation of every value dated after o (YTDs re-de-cumulated) - and an entrant after o."""
    rng = np.random.default_rng(seed)
    p = raw.copy()
    later = p.quarter.gt(o)
    for c in [c for c in p.columns if c.endswith('_ytd')] + ['trading_assets', 'total_assets']:
        p.loc[later, c] = p.loc[later, c] * rng.uniform(-3, 10, later.sum())
    from y9c.panel import decumulate
    p = p.sort_values(['rssd_id', 'report_date']).reset_index(drop=True)
    for c in [c[:-4] for c in p.columns if c.endswith('_ytd')]:
        p[f'{c}_q'], p[f'{c}_missing_prior'] = decumulate(p, f'{c}_ytd')
    fake = p[p.quarter.eq(o + 1)].head(1).assign(rssd_id=99999999, trading_revenue_ytd=5e6, trading_revenue_q=5e6)
    return pd.concat([p, fake], ignore_index=True)


@pytest.mark.realdata
@pytest.mark.parametrize('origin', ORIGINS)
def test_point_in_time_backfill_real_sets_scales(origin):
    raw = real_panel_v1_1()
    o = Q(origin)
    a = P.prepare_v1_1(raw)
    b = P.prepare_v1_1(perturb_raw_after(raw, o, o.ordinal))
    c = P.prepare_v1_1(raw[raw.quarter.le(o)])
    q4 = S.set_origin(o)
    s_a = S.exante_bank_set_rolling(a, q4)
    assert S.exante_bank_set_rolling(b, q4) == s_a == S.exante_bank_set_rolling(c, q4)
    for p in (b, c):
        np.testing.assert_array_equal(case_scale(a, s_a, o, s_a)[0], case_scale(p, s_a, o, s_a)[0])
        assert W10.cs_population(p[p.quarter.le(o)], o) == W10.cs_population(a[a.quarter.le(o)], o)


@pytest.mark.realdata
def test_point_in_time_backfill_real_forecasts_burnin():
    """Real-data forecasts at the last burn-in pseudo-origin (2013Q3) ignore every row dated later."""
    from trading_ot import macro as M
    raw = real_panel_v1_1()
    o = Q('2013Q3')
    try:
        mac = M.quarter_features_v1_1(pd.period_range('2009Q1', '2013Q3', freq='Q'),
                                      series={k: M.fetch_fred(k, start=M.START_V1_1, cache=M.CACHE_V1_1)
                                              for k in M.SERIES_V1_1})
    except Exception as e:  # pragma: no cover
        pytest.skip(f'FRED cache unavailable: {e}')
    a = P.prepare_v1_1(raw)
    b = P.prepare_v1_1(perturb_raw_after(raw, o, 7))
    s0 = S.exante_bank_set_rolling(a[a.quarter.le(Q('2013Q4'))], '2013Q4')   # epoch-0 population
    fa, sa, _ = V.t2_forecasts(a, s0, o, 1, mac)
    fb, sb, _ = V.t2_forecasts(b, s0, o, 1, mac)
    np.testing.assert_array_equal(sa, sb)
    for m in V.MEMBERS:
        np.testing.assert_array_equal(fa[m][0], fb[m][0], err_msg=m)


def _perturb_syn(ytd, mask, cols, seed):
    rng = np.random.default_rng(seed)
    y = ytd.copy()
    for c in cols:
        y.loc[mask, c] = y.loc[mask, c] * rng.uniform(-3, 10, mask.sum())
    return prepared_v1_1(y)


def _state(panel, macro, o):
    q4 = S.set_origin(o)
    s_e = S.exante_bank_set_rolling(panel, q4)
    fc, scale, _ = V.t2_forecasts(panel, s_e, o, 1, macro)
    pop, cscale, cfc = W10.cs_member_forecasts(panel, o, macro, first=V.FIRST_R)
    Qw, info = W10.war_rm(panel, o, pop, first_r=V.FIRST_R)
    out = {f'T2_{m}': fc[m][0] for m in fc}
    out.update({f'CS_{m}': cfc[m][0] for m in cfc})
    out.update(WAR=Qw, scale=scale, cscale=cscale, pop=np.array(pop, float), set=np.array(s_e, float),
               br=np.array([info['beta'], info['rho']]))
    if o.quarter == 4:
        st, _ = V.t2_epoch(panel, macro, o, s_e)
        out['settings'] = np.array([hash(repr(st))], float)
    return out


@pytest.mark.parametrize('origin', ORIGINS)
def test_point_in_time_synthetic(ytd11, panel11, macro11, origin):
    o = Q(origin)
    base = _state(panel11, macro11, o)
    later = ytd11.report_date.dt.to_period('Q').gt(o)
    p2 = _perturb_syn(ytd11, later, ['trading_revenue_ytd', 'trading_assets', 'total_assets',
                                     'total_interest_income_ytd'], o.ordinal)
    m2 = macro11.copy()
    m2.loc[m2.index > o] *= 5
    p3 = prepared_v1_1(ytd11[~later])
    for alt, mac in [(p2, m2), (p3, macro11[macro11.index <= o])]:
        st = _state(alt, mac, o)
        for k in base:
            np.testing.assert_array_equal(base[k], st[k], err_msg=f'{k} at {o}')


def test_presample_mask_synthetic(ytd11, panel11, macro11):
    """Perturbing any 2008 value except TA(2008Q4) is inert; perturbing TA(2008Q4) changes only 2009Q1 r."""
    q = ytd11.report_date.dt.to_period('Q')
    o = Q('2013Q4')
    base = _state(panel11, macro11, o)
    p2 = _perturb_syn(ytd11, q.le(Q('2008Q4')), ['trading_revenue_ytd', 'total_assets', 'total_interest_income_ytd'], 1)
    p2b = _perturb_syn(ytd11, q.lt(Q('2008Q4')), ['trading_assets'], 2)
    for alt in (p2, p2b):
        st = _state(alt, macro11, o)
        for k in base:
            np.testing.assert_array_equal(base[k], st[k], err_msg=k)
    p3 = _perturb_syn(ytd11, q.eq(Q('2008Q4')), ['trading_assets'], 3)
    ra, rb = S.add_ratio(panel11), S.add_ratio(p3)
    diff = ~np.isclose(ra.r.to_numpy(), rb.r.to_numpy(), equal_nan=True)
    assert diff.any() and set(ra.quarter[diff]) == {Q('2009Q1')}


def test_due_dates_backfill_era():
    from trading_ot.panel import availability_date, complete_quarters, due_date
    assert str(due_date('2012Q2')) == '2012-08-09'      # "the June 30 report must be received by August 9"
    assert str(due_date('2012Q4')) == '2013-02-14'      # "... and the December 31 report by February 14"
    assert str(due_date('2008Q2')) == '2008-08-11'      # Aug 9 2008 is a Saturday -> next business day
    assert str(availability_date('2012Q2')) == '2012-08-16'
    assert str(complete_quarters('2009-02-20', first='2008Q1')[-1]) == '2008Q3'
    assert str(complete_quarters('2009-02-24', first='2008Q1')[-1]) == '2008Q4'


@pytest.mark.realdata
def test_macro_history():
    from trading_ot import macro as M
    if not (M.CACHE_V1_1 / 'fred_manifest.json').exists():
        pytest.skip('v1.1 FRED cache absent')
    series = {k: M.fetch_fred(k, start=M.START_V1_1, cache=M.CACHE_V1_1) for k in M.SERIES_V1_1}
    for k, s in series.items():
        assert s.index.min() <= pd.Timestamp('2008-01-02') and s.index.max() >= pd.Timestamp('2026-06-30'), k
        assert M.max_gap_days(s, '2008-01-01', '2026-10-06') <= 7, k
    f = M.quarter_features_v1_1(['2012Q2'], series=series)
    later = {k: s.where(s.index <= pd.Timestamp('2012-06-30'), s * 9) for k, s in series.items()}
    pd.testing.assert_frame_equal(f, M.quarter_features_v1_1(['2012Q2'], series=later))
    assert list(f.columns) == ['vix', 'rates_rv', 'eq_rv', 'baa']
