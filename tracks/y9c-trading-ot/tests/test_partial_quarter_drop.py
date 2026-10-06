"""prereg §6.3 test 3: availability rule D_t = Y-9C due date + 7 calendar days; partial quarters excluded."""
import zipfile

import pandas as pd
import pytest
from trading_ot import panel as tp


def test_due_dates_2026_calendar():
    assert str(tp.due_date('2026Q1')) == '2026-05-11'
    assert str(tp.due_date('2026Q2')) == '2026-08-10'
    assert str(tp.due_date('2026Q3')) == '2026-11-09'
    assert str(tp.due_date('2025Q4')) == '2026-02-17'   # Feb 14 Sat -> Feb 16 Presidents Day -> Feb 17
    assert str(tp.availability_date('2026Q1')) == '2026-05-18'


@pytest.mark.parametrize('as_of,last', [('2026-10-06', '2026Q2'), ('2026-08-18', '2026Q2'),
                                        ('2026-08-17', '2026Q2'), ('2026-08-12', '2026Q1'),
                                        ('2026-08-16', '2026Q1')])
def test_complete_quarters(as_of, last):
    qs = tp.complete_quarters(as_of)
    assert str(qs[-1]) == last and str(qs[0]) == '2018Q1'


def write_zip(path, quarter, rows):
    header = ['RSSD9001', 'RSSD9999', 'RSSD9017', 'BHCK2170', 'BHCK4074', 'BHCKA220', 'BHCK3545']
    lines = ['^'.join(header)]
    for rssd, ytd in rows:
        lines.append('^'.join([str(rssd), f'{quarter.end_time:%Y%m%d}', 'BANK', '1000000', '10', str(ytd), '50000']))
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr(f'BHCF{quarter.end_time:%Y%m%d}.txt', '\n'.join(lines) + '\n')


def test_build_reads_only_available_quarters(tmp_path):
    for q in pd.period_range('2018Q1', '2026Q3', freq='Q'):
        write_zip(tmp_path / f'BHCF{q.end_time:%Y%m%d}.zip', q, [(1, 100 * q.quarter), (2, -5 * q.quarter)])
    p, v = tp.build_trading_panel(tmp_path, '2026-10-06')
    assert str(p.quarter.max()) == '2026Q2' and v['last_complete_quarter'] == '2026Q2'
    assert '2026Q3' not in v['availability_dates']
    p2, _ = tp.build_trading_panel(tmp_path, '2026-08-12')
    assert str(p2.quarter.max()) == '2026Q1'
    p3, _ = tp.build_trading_panel(tmp_path, '2026-08-18')
    assert str(p3.quarter.max()) == '2026Q2'
    assert (p.loc[p.rssd_id.eq(1), 'trading_revenue_q'] == 100).all()
