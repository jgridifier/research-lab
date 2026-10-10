import pytest
from fed_cp_ot.parse import KNOWN_GAPS
from fed_cp_ot.weekly import build_weekly
from fed_cp_ot.csv_check import cross_check_csv
from fed_cp_ot.burnin_checks import replicate
pytestmark=pytest.mark.realdata

def test_real_structure(real_vol):
    df,report=real_vol
    assert df.series.nunique()==60
    assert {k:v for k,v in report['known_gaps'].items() if v}==KNOWN_GAPS
    assert not any(report['anomalies'].values())
    assert df.loc[df.date>'2008-12-26','value'].isna().all()

def test_real_csv(real_vol):
    from fed_cp_ot.burnin_checks import csv_source
    try: path = csv_source()
    except FileNotFoundError: pytest.skip('Pinned CSV absent (set FED_CP_OT_RAW_DIR)')
    from fed_cp_ot.paths import PINNED_CSV_SHA256
    from fed_cp_ot.preflight import sha256
    assert sha256(path) == PINNED_CSV_SHA256
    result=cross_check_csv(path,real_vol[0],'2008-12-26')
    assert all(result[c]==1 for c in ('AB','FIN','MKT')) and result['NONFIN_pair_fraction']>=.999

def test_real_replication(real_vol):
    result=replicate(build_weekly(real_vol[0]))
    assert result['identity_error']<1e-12
