import json
import numpy as np
import pandas as pd
import pytest
from synth import make_zip
from fed_cp_ot.parse import load_vol
from fed_cp_ot.weekly import build_weekly, mkt_weekly_total
from fed_cp_ot.metric import q_from_p,w2sq,decomp,X_LOG,alr

def test_metric():
    q=lambda p:q_from_p(p,np.array([0.,2.]))
    assert w2sq(q([1,0]),q([0,1]))==4
    assert w2sq(q([.5,.5]),q([1,0]))==2
    rng=np.random.default_rng(20261009)
    for _ in range(1000):
        a,b=(q_from_p(rng.dirichlet(np.ones(6)),X_LOG) for _ in range(2))
        assert w2sq(a,a)==0 and w2sq(a,b)==w2sq(b,a)
        assert abs(sum(decomp(a,b))-w2sq(a,b))<1e-12
    for i in range(6):
        for j in range(6):
            assert w2sq(q_from_p(np.eye(6)[i],X_LOG),q_from_p(np.eye(6)[j],X_LOG))==pytest.approx((X_LOG[i]-X_LOG[j])**2)
    assert np.isfinite(alr([1,0,0,0,0,0])).all()

def test_support(pins):
    d=json.loads((pins.PREREG_DIR/'test_design_fed_cp_ot_v1.json').read_text())
    np.testing.assert_allclose(X_LOG,d['object']['support_log_days'],atol=1e-6,rtol=0)

def test_mkt(provenance,tmp_path):
    df,_=load_vol(provenance,make_zip(tmp_path/'s.zip'))
    total=mkt_weekly_total(df)
    changed=df.copy(); changed.loc[changed.cp_type!='M','value']*=1000
    pd.testing.assert_series_equal(total,mkt_weekly_total(changed))
    assert total.loc['2008-12-26']==sum(build_weekly(df,types=('M',)).iloc[-1].D)

def test_weekly_usability(provenance,tmp_path):
    df,_ = load_vol(provenance,make_zip(tmp_path/'s.zip'))
    df = df[df.date.between('2008-12-22','2008-12-26')]
    week = build_weekly(df)
    assert week.usable.all() and (week.valid_days >= 3).all()
    for row in week.itertuples():
        np.testing.assert_allclose(row.mix,row.D/row.D.sum())
    short = df[df.date <= '2008-12-23']
    assert not build_weekly(short).usable.any()
    low = df.copy(); low.loc[low.vt == 'N','value'] = 0
    assert not build_weekly(low).usable.any()
