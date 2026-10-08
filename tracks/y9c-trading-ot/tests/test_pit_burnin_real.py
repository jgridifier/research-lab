"""Extra real-data point-in-time checks, BURN-IN ONLY (every forecast origin <= 2013Q3; selection at 2013Q4).

Adopted as-is from Quant's `/workspace/research/y9c_ot_prereg/v1_1/review_pr10/pit_burnin_real.py` (228 assertions);
only imports, the data path and the pytest wrapping are adapted.
For each epoch-0 pseudo-origin o: T2 member forecasts + scales, CS member forecasts + population, WAR-RM quantiles
must be bit-identical when (i) every row dated after o is perturbed (YTD re-de-cumulated, plus a fake entrant at o+1)
and (ii) the panel is hard-cut at o before the v1.1 rules are applied. Then epoch-0 selection (T2 and CS) at 2013Q4
must be identical when every row after 2013Q4 is perturbed / removed."""
import numpy as np, pandas as pd
import pytest
from trading_ot import panel as P, sets as S, walkforward_v1_1 as V, walkforward as W10, macro as M
from test_point_in_time_v1_1 import perturb_raw_after
from conftest import real_panel_v1_1

pytestmark = pytest.mark.realdata
Q = lambda s: pd.Period(s, freq='Q')


def test_pit_burnin_real():
    if not (M.CACHE_V1_1 / 'fred_manifest.json').exists():
        pytest.skip('v1.1 FRED cache absent')
    raw = real_panel_v1_1()
    mac = M.quarter_features_v1_1(pd.period_range('2009Q1', '2013Q4', freq='Q'))
    a = P.prepare_v1_1(raw)
    s0 = S.exante_bank_set_rolling(a[a.quarter.le(Q('2013Q4'))], '2013Q4')

    def state(p, o):
        fc, sc, _ = V.t2_forecasts(p, s0, o, 1, mac)
        pop, cs, cfc = W10.cs_member_forecasts(p, o, mac, first=V.FIRST_R)
        Qw, info = W10.war_rm(p, o, pop, first_r=V.FIRST_R)
        out = {f'T2_{m}': fc[m][0] for m in fc}; out.update({f'CS_{m}': cfc[m][0] for m in cfc})
        out.update(T2scale=sc, CSscale=cs, pop=np.array(pop, float), WAR=Qw, br=np.array([info['beta'], info['rho']]))
        return out
    n_ok = 0
    for o in pd.period_range('2012Q2', '2013Q3', freq='Q'):
        base = state(a, o)
        for lab, alt in [('perturbed', P.prepare_v1_1(perturb_raw_after(raw, o, o.ordinal))), ('cut', P.prepare_v1_1(raw[raw.quarter.le(o)]))]:
            st = state(alt, o)
            for k in base:
                np.testing.assert_array_equal(base[k], st[k], err_msg=f'{k} {o} {lab}'); n_ok += 1
    e = Q('2013Q4')
    t2a, _ = V.t2_epoch(a, mac, e, s0); csa, _ = V.cs_epoch(a, mac, e)
    for lab, alt in [('perturbed', P.prepare_v1_1(perturb_raw_after(raw, e, 11))), ('cut', P.prepare_v1_1(raw[raw.quarter.le(e)]))]:
        t2b, _ = V.t2_epoch(alt, mac, e, s0); csb, _ = V.cs_epoch(alt, mac, e)
        assert t2a == t2b and csa == csb, lab
    assert t2a['b_star'] == 'B0' and t2a['trimmed'] == ['B0', 'B4'] and t2a['s'] == 1.0
    assert csa['b_star'] == 'B0' and csa['n_cases'] == 230 and csa['n_matched'] == 221
    assert n_ok == 228
