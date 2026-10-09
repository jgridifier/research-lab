from dataclasses import replace
from datetime import datetime
import json
import numpy as np
import pandas as pd
import pytest
from synth import make_zip
from fed_cp_ot.errors import ProvenanceError, ScoringWallError
from fed_cp_ot.parse import load_vol, parse_vol
from fed_cp_ot.weekly import build_weekly, mkt_weekly_total, provisional_partial_week
from fed_cp_ot.forecast import ForwardLog, data_available_at, Persistence, origin_view, walk_forward

def test_provenance_required(provenance,tmp_path):
    with pytest.raises(ProvenanceError): load_vol(None,tmp_path/'not_opened.zip')
    with pytest.raises(ProvenanceError): load_vol(replace(provenance,oos_approved=True),tmp_path/'not_opened.zip')

def test_withheld(provenance,tmp_path):
    path=make_zip(tmp_path/'s.zip')
    df,report=load_vol(provenance,path)
    assert df.loc[df.date>'2008-12-26','value'].isna().all()
    assert 99999 not in df.value.values and '99999' not in json.dumps(report)
    assert report['series_count']==60 and set(report['rates_series_ids'])=={'RATE1','RATE2'}
    with pytest.raises(ProvenanceError): parse_vol(path,provenance,wall=None)
    with pytest.raises(ScoringWallError): build_weekly(df,through='2009-01-02')
    with pytest.raises(ScoringWallError): mkt_weekly_total(df,through='2009-01-02')
    w=build_weekly(df); assert w.week.max()==pd.Timestamp('2008-12-26')
    assert provisional_partial_week(df,'2008-12-24').provisional.all()

def test_forecast_no_future(provenance,tmp_path):
    df,_=load_vol(provenance,make_zip(tmp_path/'s.zip'))
    weekly=build_weekly(df,types=('AAA',)); origin=pd.Timestamp('2004-04-09')
    changed=weekly.copy(deep=True)
    changed.loc[changed.week>origin,'mix']=changed.loc[changed.week>origin,'mix'].map(lambda _:np.ones(6)/6)
    pd.testing.assert_frame_equal(origin_view(weekly,origin),origin_view(changed,origin))
    a=walk_forward(weekly,Persistence(),[origin])[0]; b=walk_forward(changed,Persistence(),[origin])[0]
    np.testing.assert_array_equal(a['mix'],b['mix']); assert a['target']==pd.Timestamp('2004-04-16')

def dt(s): return datetime.fromisoformat(s)

def test_forward_log(tmp_path):
    log=ForwardLog(tmp_path/'f.jsonl',live=False); mix=np.ones(6)/6
    args=dict(origin='2008-12-19',target='2008-12-26',cp_type='AAA',mix=mix,model='P',input_max_date='2008-12-19')
    with pytest.raises(ValueError): log.record_outcome('2008-12-26','AAA',mix,dt('2008-12-29T18:00:00+00:00'))
    with pytest.raises(ValueError): log.record_forecast(**args,issued_at=dt('2008-12-29T18:00:00+00:00'))
    # issued before the origin week's data were published (Mon 2008-12-22 13:00 ET): uses future data
    with pytest.raises(ValueError): log.record_forecast(**args,issued_at=dt('2008-12-18T18:00:00+00:00'))
    with pytest.raises(ValueError): log.record_forecast(**args,issued_at=dt('2008-12-22T17:59:00+00:00'))
    log.record_forecast(**args,issued_at=dt('2008-12-22T18:00:00+00:00'))
    with pytest.raises(ValueError): log.record_outcome('2008-12-26','AAA',mix,dt('2008-12-29T17:59:00+00:00'))
    log.record_outcome('2008-12-26','AAA',mix,dt('2008-12-29T18:00:00+00:00'))
    assert log.verify() and log.score('2008-12-26','AAA','P')==0
    with pytest.raises(ScoringWallError): log.score('2009-01-02','AAA','P')
    with pytest.raises(ValueError): log.record_forecast(**args,issued_at=dt('2008-12-22T18:00:00+00:00'))
    log.path.write_text(log.path.read_text().replace('"model": "P"','"model": "EXP"'))
    with pytest.raises(ValueError,match='tampered'): log.verify()

@pytest.mark.parametrize('friday,expected',[('2008-12-26','2008-12-29T13:00:00-05:00'),('2008-07-04','2008-07-07T13:00:00-04:00')])
def test_release(friday,expected): assert data_available_at(friday).isoformat()==expected

def test_postwall_nonnumeric_is_not_converted(provenance,tmp_path):
    def mutate(attrs,obs):
        for row in obs:
            if row['TIME_PERIOD']>'2008-12-26': row['OBS_VALUE']='NOT A NUMBER'
    df,_=load_vol(provenance,make_zip(tmp_path/'s.zip',mutate))
    assert df.loc[df.date>'2008-12-26','valid'].all()
    assert df.loc[df.date>'2008-12-26','value'].isna().all()

def test_forward_input_timing(tmp_path):
    log=ForwardLog(tmp_path/'f.jsonl',live=False); mix=np.ones(6)/6
    with pytest.raises(ValueError):
        log.record_forecast('2008-12-19','2008-12-26','AAA',mix,'P',dt('2008-12-22T18:00:00+00:00'),'2008-12-20')
    with pytest.raises(ValueError):
        log.record_forecast('2008-12-19','2008-12-19','AAA',mix,'P',dt('2008-12-22T18:00:00+00:00'),'2008-12-19')
    assert not log.path.exists()

def test_models_share_one_outcome(tmp_path, provenance):
    log = ForwardLog(tmp_path/'forward.jsonl',live=False)
    mix = np.ones(6)/6
    args = dict(origin='2008-12-19', target='2008-12-26', cp_type='AAA',
                issued_at='2008-12-22T18:00:00+00:00', input_max_date='2008-12-19')
    log.record_forecast(**args, model='P', mix=mix)
    log.record_forecast(**args, model='EXP', mix=[1,0,0,0,0,0])
    with pytest.raises(ValueError): log.record_forecast(**args, model='EXP', mix=mix)
    log.record_outcome('2008-12-26','AAA',mix,'2008-12-29T18:00:00+00:00',provenance)
    assert log.score('2008-12-26','AAA','P') == 0
    assert log.score('2008-12-26','AAA','EXP') > 0
    with pytest.raises(ValueError): log.record_outcome('2008-12-26','AAA',mix,'2008-12-29T18:00:00+00:00',provenance)
    with pytest.raises(ValueError): log.record_forecast(**args, model='MA4', mix=mix)

@pytest.mark.parametrize('origin,target',[('2008-12-18','2008-12-26'),('2008-12-12','2008-12-26')])
def test_friday_seven_day_horizon(tmp_path,origin,target):
    log = ForwardLog(tmp_path/'forward.jsonl',live=False)
    with pytest.raises(ValueError):
        log.record_forecast(origin,target,'AAA',np.ones(6)/6,'P','2008-12-22T18:00:00+00:00',origin)
    assert not log.path.exists()

def test_outcome_wall_before_storage(tmp_path,provenance,approved):
    log = ForwardLog(tmp_path/'forward.jsonl',live=False)
    mix = np.ones(6)/6
    log.record_forecast('2008-12-26','2009-01-02','AAA',mix,'P','2008-12-29T18:00:00+00:00','2008-12-26')
    before = log.path.read_bytes()
    for permission in (None, provenance):
        with pytest.raises(ScoringWallError):
            log.record_outcome('2009-01-02','AAA',mix,'2009-01-05T18:00:00+00:00',permission)
        assert log.path.read_bytes() == before
    # Synthetic outcome only; no held-out source observations are loaded.
    log.record_outcome('2009-01-02','AAA',mix,'2009-01-05T18:00:00+00:00',approved)
    assert log.score('2009-01-02','AAA','P',approved) == 0

def test_hash_before_load(pins,monkeypatch,tmp_path):
    from fed_cp_ot import app
    (pins.PREREG_DIR/'PIN.txt').write_text('tampered')
    calls = []
    monkeypatch.setattr(app,'load_vol',lambda *a: calls.append('load'))
    with pytest.raises(ProvenanceError): app.build_app(tmp_path/'app.html',tmp_path/'unopened.zip')
    assert not calls


# --- Fed holiday calendar: availability = 13:00 ET on the next Fed business day ---
from fed_cp_ot.fedcal import fed_holidays, is_fed_business_day, next_fed_business_day
from datetime import date

@pytest.mark.parametrize('friday,expected', [
    ('2008-01-18', '2008-01-22T13:00:00-05:00'),  # Monday 2008-01-21 MLK Day
    ('2008-02-15', '2008-02-19T13:00:00-05:00'),  # Presidents Day
    ('2008-05-23', '2008-05-27T13:00:00-04:00'),  # Memorial Day
    ('2008-08-29', '2008-09-02T13:00:00-04:00'),  # Labor Day
    ('2008-10-10', '2008-10-14T13:00:00-04:00'),  # Columbus Day
    ('2010-07-02', '2010-07-06T13:00:00-04:00'),  # July 4 on Sunday -> observed Monday July 5
    ('2007-11-09', '2007-11-13T13:00:00-05:00'),  # Nov 11 on Sunday -> observed Monday Nov 12
    ('2022-06-17', '2022-06-21T13:00:00-04:00'),  # Juneteenth on Sunday -> observed Monday June 20
    ('2008-12-19', '2008-12-22T13:00:00-05:00'),  # ordinary Monday
])
def test_release_holiday_monday(friday, expected):
    assert data_available_at(friday).isoformat() == expected

def test_fed_holiday_rules():
    assert date(2008, 11, 27) in fed_holidays(2008)                  # Thanksgiving, 4th Thursday
    assert next_fed_business_day('2008-11-26') == date(2008, 11, 28)
    assert date(2008, 12, 25) in fed_holidays(2008) and date(2009, 1, 1) in fed_holidays(2009)
    # Saturday holidays are NOT moved to Friday at the Fed
    assert is_fed_business_day('2010-12-24') and is_fed_business_day('2021-12-31') and is_fed_business_day('2004-07-02')
    # Juneteenth only from 2021
    assert date(2020, 6, 19) not in fed_holidays(2020) and date(2021, 6, 18) not in fed_holidays(2021)
    assert date(2023, 6, 19) in fed_holidays(2023)
    assert all(d.weekday() < 5 for y in range(2001, 2027) for d in fed_holidays(y))
    assert len(fed_holidays(2008)) == 10 and len(fed_holidays(2024)) == 11
    assert len(fed_holidays(2023)) == 10 and is_fed_business_day('2023-11-10')  # Veterans Day 2023 on Saturday: not moved


# --- Live forward log: stores the fetch time and the release Last-Modified; rejects forecasts stamped before either ---
from fed_cp_ot.forecast import vintage_stamps

LIVE = dict(origin='2008-12-19', target='2008-12-26', cp_type='AAA', mix=np.ones(6)/6, model='P', input_max_date='2008-12-19')

def test_live_log_requires_and_stores_stamps(tmp_path):
    log = ForwardLog(tmp_path/'live.jsonl')  # live is the default
    with pytest.raises(ValueError, match='fetch time'):
        log.record_forecast(**LIVE, issued_at=dt('2008-12-22T19:00:00+00:00'))
    row = log.record_forecast(**LIVE, issued_at=dt('2008-12-22T19:00:00+00:00'),
                              fetched_at='2008-12-22T18:40:00+00:00', release_last_modified='Mon, 22 Dec 2008 18:00:03 GMT')
    assert row['fetched_at'] == '2008-12-22T18:40:00+00:00'
    assert row['release_last_modified'] == '2008-12-22T18:00:03+00:00'
    stored = json.loads((tmp_path/'live.jsonl').read_text().splitlines()[0])
    assert stored['fetched_at'] and stored['release_last_modified'] and log.verify()

@pytest.mark.parametrize('fetched,modified', [
    ('2008-12-22T19:30:00+00:00', 'Mon, 22 Dec 2008 18:00:03 GMT'),   # stamped before the fetch
    ('2008-12-22T18:40:00+00:00', 'Mon, 22 Dec 2008 19:10:00 GMT'),   # stamped before the release update
])
def test_live_log_rejects_forecast_before_fetch_or_release(tmp_path, fetched, modified):
    log = ForwardLog(tmp_path/'live.jsonl')
    with pytest.raises(ValueError, match='stamped before'):
        log.record_forecast(**LIVE, issued_at=dt('2008-12-22T19:00:00+00:00'), fetched_at=fetched, release_last_modified=modified)
    assert not (tmp_path/'live.jsonl').exists()

def test_vintage_stamps_from_manifest():
    assert vintage_stamps({'fetched_at_utc': '2026-10-09T23:25:14+00:00', 'last_modified': 'Fri, 09 Oct 2026 17:00:03 GMT'}) == \
        ('2026-10-09T23:25:14+00:00', 'Fri, 09 Oct 2026 17:00:03 GMT')
    with pytest.raises(ValueError): vintage_stamps({'fetched_at_utc': '2026-10-09T23:25:14+00:00', 'last_modified': None})
