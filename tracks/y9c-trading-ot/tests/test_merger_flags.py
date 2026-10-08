"""prereg §6.3 test 12: structural events are flagged."""
import pandas as pd
import pytest
from trading_ot import panel as tp

KNOWN = [(1074156, '2019Q4'), (1094640, '2020Q3'), (1378434, '2022Q4'), (1070345, '2026Q1'),
         (2277860, '2025Q2'), (1199844, '2025Q4'), (1574834, '2024Q1'), (1378434, '2023Q3'),
         (1245415, '2023Q1'), (1575569, '2023Q1'), (1119794, '2022Q4'), (1069778, '2021Q2'),
         (1131787, '2019Q3'), (5280254, '2018Q2'), (1026632, '2020Q1')]


def test_event_list_complete():
    listed = {(e['rssd_id'], e['quarter']) for e in tp.EVENTS}
    assert set(KNOWN) <= listed


def test_threshold_flags_synthetic():
    p = pd.DataFrame(dict(rssd_id=[1, 1, 1, 1], quarter=pd.period_range('2022Q1', periods=4, freq='Q'),
                          total_assets=[100.0, 110.0, 160.0, 150.0]))
    f = tp.merger_flags(p, events=[]).set_index('quarter')
    assert f.flag.tolist() == [False, False, True, False]


@pytest.mark.realdata
def test_real_events_flagged():
    from trading_ot.paths import DATA
    path = DATA / 'processed/trading_panel.parquet'
    if not path.exists():
        pytest.skip('real panel not built')
    p = pd.read_parquet(path)
    f = tp.merger_flags(p).set_index(['rssd_id', 'quarter'])
    for rssd, q in [(1074156, '2019Q4'), (1094640, '2020Q3'), (1378434, '2022Q4'), (1070345, '2026Q1')]:
        row = f.loc[(rssd, pd.Period(q))]
        assert row.flag and row.flag_threshold, (rssd, q)       # big moves are caught by the 15% rule too
    assert f.loc[(1070345, pd.Period('2026Q1'))].asset_change > 0.35
