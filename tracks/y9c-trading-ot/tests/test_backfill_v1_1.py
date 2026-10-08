"""Addendum §5.3 tests 1, 4-10 on the real 2008Q1-2026Q2 panel (marked realdata; skipped when the gitignored
panel is absent) plus synthetic checks of the same rules. No forecast here is made at an origin >= 2013Q4
(those would be OOS forecasts); the 72/72 check uses burn-in pseudo-origins 2012Q2-2013Q3 only."""
import hashlib
import json
import zipfile

import numpy as np
import pandas as pd
import pytest
from trading_ot import panel as P, sets as S
from trading_ot.paths import DATA, RAW_DIRS_V1_1
from conftest import real_panel_v1_1

Q = lambda s: pd.Period(s, freq='Q')
GUARD_ROWS = [(1029884, '2010Q3'), (1199992, '2010Q3'), (1245741, '2010Q3'), (2857691, '2010Q3'),
              (4400336, '2012Q2'), (3023466, '2012Q3'), (1562859, '2012Q4'), (1204627, '2013Q2'),
              (3866373, '2014Q2'), (2858951, '2014Q3'), (3762457, '2015Q4'), (1025608, '2016Q2'),
              (1035157, '2017Q4'), (1378434, '2021Q3'), (1575569, '2021Q4'), (1378434, '2022Q4')]
V1_EXANTE_19 = [1039502, 1069778, 1070345, 1073757, 1074156, 1094640, 1111435, 1119794, 1120754, 1199611, 1199844,
                1275216, 1574834, 1951350, 2162966, 2380443, 3587146, 4846998, 5006575]
EXPECTED_COUNTS = {'2013Q4': 12, '2014Q4': 16, '2015Q4': 17, '2016Q4': 18, '2017Q4': 18, '2018Q4': 19,
                   '2019Q4': 17, '2020Q4': 19, '2021Q4': 19, '2022Q4': 21, '2023Q4': 22, '2024Q4': 19, '2025Q4': 21}
GS, MS = 2380443, 2162966
realdata = pytest.mark.realdata


@pytest.fixture(scope='module')
def raw():
    return real_panel_v1_1()


@pytest.fixture(scope='module')
def v11(raw):
    return P.prepare_v1_1(raw)


# 1 ─ vintage
@realdata
def test_backfill_vintage(raw):
    v = json.loads((DATA / 'processed_v1_1' / 'vintage.json').read_text())
    assert v['n_quarters'] == 74 and v['first_quarter'] == '2008Q1' and v['last_complete_quarter'] == '2026Q2'
    assert len(v['zips']) == 74 and all(v['manifest_sha256_match'].values())
    manifests = {}
    for d in RAW_DIRS_V1_1:
        manifests.update(json.loads((d / 'manifest.json').read_text()))
    assert all(manifests[k]['sha256'] == h for k, h in v['zips'].items())


def test_modified_zip_fails(tmp_path):
    from test_partial_quarter_drop import write_zip     # fake-ZIP helper of the v1.0 suite
    q = pd.Period('2018Q1', freq='Q')
    path = tmp_path / f'BHCF{q.end_time:%Y%m%d}.zip'
    write_zip(path, q, [(1, 100), (2, -5)])
    (tmp_path / 'manifest.json').write_text(json.dumps({path.name: {'sha256': hashlib.sha256(path.read_bytes())
                                                                    .hexdigest()}}))
    P.build_trading_panel(tmp_path, '2018-06-01')
    with zipfile.ZipFile(path, 'a') as z:
        z.writestr('extra.dat', 'tampered')
    with pytest.raises(ValueError, match='manifest'):
        P.build_trading_panel(tmp_path, '2018-06-01')


# 4 ─ entry before BHC status
@realdata
def test_entry_before_bhc_status(v11):
    from trading_ot import walkforward as W10
    for b in (GS, MS):
        rows = v11[v11.rssd_id.eq(b)]
        assert rows.quarter.min() == Q('2009Q1')
        r = S.add_ratio(v11)
        first_r = r[r.rssd_id.eq(b) & r.r.notna()].quarter.min()
        assert first_r == Q('2009Q2')
        assert b not in S.cross_section(r, '2009Q1').rssd_id.values
        assert b in S.cross_section(r, '2009Q2').rssd_id.values
        assert b not in S.exante_bank_set_rolling(v11, '2011Q4')     # needs 16 own quarters (2009Q1-2012Q4)
        assert b in S.exante_bank_set_rolling(v11, '2013Q4')


# 5 ─ partial-quarter entrants
@realdata
def test_partial_quarter_entrants(raw, v11):
    for b, q in [(1562859, '2009Q2'), (1562176, '2013Q2'), (3226762, '2010Q4'), (3226762, '2015Q4'),
                 (5280254, '2018Q2'), (3606542, '2015Q3'), (2816906, '2016Q3')]:
        row = v11[v11.rssd_id.eq(b) & v11.quarter.eq(Q(q))]
        assert len(row) == 1 and row.trading_revenue_ytd.notna().all() and row.trading_revenue_q.isna().all(), (b, q)
    t1 = lambda p, q: p[p.quarter.eq(Q(q))].trading_revenue_q.sum() / 1e6
    vb = P.prepare_v1_1(raw, entrant_rule='b')
    assert round(t1(v11, '2016Q3'), 3) == 16.094 and round(t1(v11, '2013Q2'), 3) == 14.167
    assert round(t1(vb, '2013Q2'), 3) == 15.551
    # Quant's 14.906 counts BancWest's 2016Q3 first-filing YTD (+$0.027bn); with the pre-registered
    # tiered-duplicate exclusion applied to T1 the rule-(b) value is 14.879. Both are asserted.
    assert round(t1(vb, '2016Q3'), 3) == 14.879
    no_tier = P.presample_mask(P.ytd_reset_guard(raw[raw.total_assets.notna()].reset_index(drop=True)))
    no_tier = no_tier.assign(trading_revenue_q=P.entrant_rule_b(no_tier).where(~no_tier.ytd_reset_flag))
    assert round(t1(no_tier, '2016Q3'), 3) == 14.906


# 6 ─ gap filers
@realdata
def test_gap_filers(v11):
    r = S.add_ratio(v11)
    for b, gap_end, resume in [(2816906, '2016Q2', '2016Q3'), (3226762, '2015Q3', '2015Q4')]:
        rows = r[r.rssd_id.eq(b)].set_index('quarter')
        assert not rows.index.isin(pd.period_range('2012Q1', gap_end, freq='Q')).any()
        assert np.isnan(rows.loc[Q(resume), 'trading_revenue_q']) and np.isnan(rows.loc[Q(resume), 'trading_assets_lag'])
        assert np.isnan(rows.loc[Q(resume), 'r'])


# 7 ─ YTD-reset guard
@realdata
def test_ytd_reset_guard(raw):
    base = raw[raw.total_assets.notna()].reset_index(drop=True)
    flagged = P.ytd_reset_rows(base)
    got = sorted((int(a), str(b)) for a, b in base.loc[flagged, ['rssd_id', 'quarter']].itertuples(index=False))
    assert got == sorted(GUARD_ROWS) and len(got) == 16
    g = P.ytd_reset_guard(base)
    flows = P.flow_columns(base)
    assert g.loc[flagged, flows].isna().all().all()
    for b, q in GUARD_ROWS:                        # neighbours untouched
        for nq in (Q(q) - 1, Q(q) + 1):
            m = base.rssd_id.eq(b) & base.quarter.eq(nq)
            pd.testing.assert_frame_equal(base.loc[m, flows], g.loc[m, flows])
    assert P.prepare_v1_0(raw).ytd_reset_flag.sum() == 3     # R1 (2018+): MUFG 2021Q3, BNP 2021Q4, MUFG 2022Q4


# 8 ─ tiered duplicates
@realdata
def test_tiered_duplicates(raw, v11):
    for b in (5005998, 1032473):
        assert raw[raw.rssd_id.eq(b) & raw.quarter.isin([Q('2016Q3'), Q('2016Q4')])].shape[0] == 2
        assert v11[v11.rssd_id.eq(b) & v11.quarter.isin([Q('2016Q3'), Q('2016Q4')])].empty
    assert not v11[v11.rssd_id.eq(1032473) & v11.quarter.eq(Q('2016Q2'))].empty


def test_tiered_duplicate_mask_synthetic():
    df = pd.DataFrame({'rssd_id': [5005998, 5005998, 1032473, 1], 'quarter': pd.PeriodIndex(
        ['2016Q2', '2016Q3', '2016Q4', '2016Q3'], freq='Q')})
    assert P.tiered_duplicate_mask(df).tolist() == [False, True, True, False]


# 9 ─ rolling set
@realdata
def test_rolling_set_v1_equivalence(v11):
    rs = S.rolling_sets(v11)
    assert sorted(rs[Q('2021Q4')]) == V1_EXANTE_19
    assert {str(k): len(v) for k, v in rs.items()} == EXPECTED_COUNTS
    union = set().union(*rs.values())
    # design JSON says union_size 32: that count includes the 2012Q4 origin (design_burnin.py loops 2012..2025);
    # over the pre-registered origins 2013Q4..2025Q4 the union is 31.
    assert len(union) == 31
    assert len(union | set(S.exante_bank_set_rolling(v11, '2012Q4'))) == 32


# 2 (data part) ─ pre-sample mask
@realdata
def test_presample_mask_real(raw, v11):
    pre = v11[v11.quarter.le(Q('2008Q4'))]
    assert pre.trading_revenue_q.isna().all() and pre.total_assets.isna().all()
    assert pre[pre.quarter.lt(Q('2008Q4'))].trading_assets.isna().all()
    assert pre[pre.quarter.eq(Q('2008Q4'))].trading_assets.notna().sum() > 0
    r = S.add_ratio(v11)
    assert r[r.quarter.le(Q('2008Q4'))].r.isna().all() and r[r.quarter.eq(Q('2009Q1'))].r.notna().sum() > 30


# 10 ─ first freeze coverage (burn-in pseudo-OOS only)
@realdata
def test_member_coverage_first_freeze(v11):
    from trading_ot import macro as M, walkforward_v1_1 as V
    try:
        mac = M.quarter_features_v1_1(pd.period_range('2009Q1', '2013Q4', freq='Q'),
                                      series={k: M.fetch_fred(k, start=M.START_V1_1, cache=M.CACHE_V1_1)
                                              for k in M.SERIES_V1_1})
    except Exception as e:  # pragma: no cover
        pytest.skip(f'FRED cache unavailable: {e}')
    ff = V.first_freeze(v11, mac)
    assert len(ff['set']) == 12
    assert ff['cases'].target_quarter.max() == Q('2013Q4') and ff['cases'].origin.max() == Q('2013Q3')
    assert ff['coverage'] == {m: (72, 72) for m in V.MEMBERS}
    assert ff['settings']['n_matched'] == 72 and not ff['settings']['excluded_low_coverage']
