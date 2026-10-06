"""Golden values for the v1.1 epoch-0 (2013Q4) freeze, burn-in pseudo-OOS 2012Q3-2013Q4 only.

Reproduced independently by Quant (ERRATA_v1_1.md, `v1_1/review_pr10/freeze_independent.py`). Skips if the
gitignored real-data panel or the v1.1 FRED cache is absent.
"""
import pandas as pd
import pytest
from trading_ot import panel as P, sets as S, walkforward_v1_1 as V
from conftest import real_panel_v1_1

pytestmark = pytest.mark.realdata
BANKS_2013Q4 = [1039502, 1073757, 1094640, 1111435, 1120754, 1199611, 1883693, 1951350, 2162966, 2380443, 3232316,
                3587146]
SCORES = {'B0': 0.478895, 'B1': 0.706508, 'B2': 0.927682, 'B3': 0.726731, 'B4': 0.675533, 'B5': 0.819913,
          'B6': 0.745752}
S_SCORES = {'1.0': 0.500147, '1.1': 0.503443, '1.2': 0.508623, '1.35': 0.519130, '1.5': 0.532498}


@pytest.fixture(scope='module')
def freeze():
    from trading_ot import macro as M
    if not (M.CACHE_V1_1 / 'fred_manifest.json').exists():
        pytest.skip('v1.1 FRED cache absent')
    v = P.prepare_v1_1(real_panel_v1_1())
    mac = M.quarter_features_v1_1(pd.period_range('2009Q1', '2013Q4', freq='Q'))
    ff = V.first_freeze(v, mac)
    cs, cases = V.cs_epoch(v, mac, '2013Q4')
    return ff, cs, cases


def test_epoch0_t2_golden(freeze):
    ff, _, _ = freeze
    st = ff['settings']
    assert sorted(ff['set']) == BANKS_2013Q4
    assert st['n_cases'] == 72 and st['n_matched'] == 72 and st['m0'] == list(SCORES)
    for m, v in SCORES.items():
        assert abs(st['scores'][m] - v) <= 1e-6, (m, st['scores'][m])
    assert st['b_star'] == 'B0' and st['trimmed'] == ['B0', 'B4'] and st['s'] == 1.0
    assert set(st['s_scores']) == set(S_SCORES)
    for k, v in S_SCORES.items():
        assert abs(st['s_scores'][k] - v) <= 1e-6, (k, st['s_scores'][k])
    assert not st['inherited'] and not st['excluded_low_coverage']


def test_epoch0_cs_golden(freeze):
    _, cs, cases = freeze
    assert cs['b_star'] == 'B0' and cs['n_cases'] == 230 and cs['n_matched'] == 221
    assert not cs['excluded_low_coverage'] and cases.target_quarter.max() == pd.Period('2013Q4', freq='Q')
