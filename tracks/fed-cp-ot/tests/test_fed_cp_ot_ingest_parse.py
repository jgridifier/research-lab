import zipfile
import csv
import io
import json
import pandas as pd
import pytest
from synth import make_zip
from fed_cp_ot import preflight as pf
from fed_cp_ot.errors import ValidationError
from fed_cp_ot.parse import load_vol, KNOWN_GAPS
from fed_cp_ot.weekly import build_weekly

@pytest.mark.parametrize('kind',['missing','extra','attribute','negative','fraction','partial'])
def test_validation(provenance,tmp_path,kind):
    def mutate(a,obs):
        if a['SERIES_NAME']!='AB.1_4.AA.AMT': return
        if kind=='missing': a['skip']='yes'
        elif kind=='extra': a['SERIES_NAME']='EXTRA'
        elif kind=='attribute': a['CP_TYPE']='NAA'
        elif kind=='negative': obs[0]['OBS_VALUE']='-1'
        elif kind=='fraction': obs[0]['OBS_VALUE']='1.5'
        else: obs[0]['OBS_STATUS']='ND'
    with pytest.raises(ValidationError): load_vol(provenance,make_zip(tmp_path/'s.zip',mutate))

def test_known_gaps(provenance,tmp_path):
    df,report=load_vol(provenance,make_zip(tmp_path/'s.zip',gaps=True))
    assert {k:v for k,v in report['known_gaps'].items() if v}==KNOWN_GAPS
    assert not any(report['anomalies'].values())
    w=build_weekly(df).set_index(['cp_type','week'])
    assert w.loc[('NA2',pd.Timestamp('2004-04-09')),'valid_days']==4
    assert w.loc[('AAA',pd.Timestamp('2004-04-09')),'valid_days']==5
    assert w.loc[('NAA',pd.Timestamp('2004-12-24')),'valid_days']==4

def test_csv(provenance,tmp_path):
    from fed_cp_ot.csv_check import cross_check_csv
    from fed_cp_ot.parse import MAT_MAP
    df,_=load_vol(provenance,make_zip(tmp_path/'s.zip'))
    reverse={v:k for k,v in MAT_MAP.items()}; cats={'AAA':'AB','FAA':'FIN','M':'MKT','NAA':'NONFIN','NA2':'NONFIN'}
    rows=[[r.date.strftime('%Y-%m-%d'),cats[r.cp_type],reverse[r.mat],r.value] for r in df[(df.vt=='D') & df.valid & (df.date<='2008-12-26')].itertuples()]
    # Post-wall nonnumeric sentinel must never be converted.
    rows.append(['2009-01-02','AB','1_4','DO NOT PARSE'])
    path=tmp_path/'check.csv'
    def save():
        with path.open('w') as f:
            writer=csv.writer(f); writer.writerow(['date','issuer_category','maturity_range_days','amount_usd_mm']); writer.writerows(rows)
    save(); result=cross_check_csv(path,df,'2008-12-26'); assert result['NONFIN_pair_fraction']==1
    next(r for r in rows if r[1]=='NONFIN')[3]+=1
    save()
    with pytest.raises(ValidationError): cross_check_csv(path,df,'2008-12-26')

def test_ingest(tmp_path):
    from fed_cp_ot.ingest import fetch_vintage,latest_vintage,register_local_vintage
    blob=make_zip(tmp_path/'s.zip').read_bytes()
    class Response(io.BytesIO):
        status=200
        headers={'ETag':'abc','Last-Modified':'Monday','Content-Length':str(len(blob))}
    seen=[]
    def opener(req, timeout=None): assert timeout and timeout > 0; seen.append(req); return Response(blob)
    cache=tmp_path/'cache'
    a=fetch_vintage(cache,opener=opener); b=fetch_vintage(cache,opener=opener)
    assert a['sha256']==b['sha256'] and b['unchanged_from_previous']
    assert len(list((cache/'vintages').glob('*.zip')))==1 and latest_vintage(cache).exists()
    assert a['http_status']==200 and a['xml_prepared']=='2026-10-05' and a['fetched_at_et']
    assert seen[0].get_header('User-agent')=='research-lab fed-cp-ot (jgridifier)'
    assert len((cache/'manifest.jsonl').read_text().splitlines())==2
    with pytest.raises(ValueError): register_local_vintage(tmp_path/'s.zip','bad',cache,pinned=True)
    bad=lambda req, timeout=None: Response(b'not a zip')
    with pytest.raises(zipfile.BadZipFile): fetch_vintage(cache,opener=bad,retries=1)

def test_vintage_diff(provenance,tmp_path):
    from fed_cp_ot.vintages import diff_vintages,append_diff
    df,_=load_vol(provenance,make_zip(tmp_path/'s.zip')); new=df.copy()
    new.loc[0,'value']+=1
    new.loc[new.date>'2008-12-26','value']=99999
    result=diff_vintages(df,new)
    assert len(result['value_changes'])==1 and '99999' not in json.dumps(result)
    append_diff(result,tmp_path/'diff.jsonl'); assert (tmp_path/'diff.jsonl').exists()

@pytest.mark.parametrize('marker',['status','value'])
def test_missing_markers_independently(provenance,tmp_path,marker):
    def mutate(attrs,obs):
        for row in obs:
            if row['TIME_PERIOD']=='2008-12-25':
                if marker=='status': row['OBS_VALUE']='123'
                else: row['OBS_STATUS']='A'
    df,_=load_vol(provenance,make_zip(tmp_path/'s.zip',mutate))
    assert not df.loc[df.date=='2008-12-25','valid'].any()
    assert df.loc[df.date=='2008-12-25','value'].isna().all()

def test_vintage_structural_changes(provenance,tmp_path):
    from fed_cp_ot.vintages import diff_vintages
    df,_=load_vol(provenance,make_zip(tmp_path/'s.zip'))
    new=df.drop(index=0).copy()
    new.loc[1,'valid']=False
    new.loc[new.date>'2008-12-26','valid']=False
    result=diff_vintages(df,new)
    assert sum(map(len,result['removed_dates'].values()))==1
    assert len(result['valid_flag_changes'])==1
    assert all(v['current']['valid']==0 for v in result['post_wall_counts'].values())

def test_burnin_csv_search_and_hash(tmp_path,monkeypatch,provenance):
    from fed_cp_ot import burnin_checks as checks
    csv_path = tmp_path/'csv.csv'; csv_path.write_text('bad')
    assert checks.csv_source(csv_path) == csv_path
    calls=[]
    monkeypatch.setattr(checks,'load_vol',lambda *a: calls.append('load'))
    with pytest.raises(ValueError,match='CSV hash mismatch'):
        checks.run(make_zip(tmp_path/'s.zip'),csv_path)
    assert not calls

def test_compare_burnin_only(tmp_path,monkeypatch,provenance):
    from fed_cp_ot import burnin_checks as checks
    baseline=make_zip(tmp_path/'baseline.zip')
    def mutate(attrs,obs):
        for row in obs:
            if row['TIME_PERIOD'] > '2008-12-26': row['OBS_VALUE']='WITHHELD'
        if attrs['SERIES_NAME']=='AB.1_4.AA.AMT': obs[0]['OBS_VALUE']='999'
    newer=make_zip(tmp_path/'newer.zip',mutate)
    csv_path=tmp_path/'check.csv'; csv_path.write_text('synthetic')
    monkeypatch.setattr(checks,'PINNED_CSV_SHA256',pf.sha256(csv_path))
    monkeypatch.setattr(checks,'pinned_zip',lambda:baseline)
    monkeypatch.setattr(checks,'DATA_DIR',tmp_path/'output')
    monkeypatch.setattr(checks,'cross_check_csv',lambda *a: {})
    def replicate(weekly,strict):
        assert not strict and (weekly.week <= '2008-12-26').all()
        return dict(checks.EXPECTED,usable={},N_NEXT=0,identity_error=0,matches_pinned_numbers=False)
    monkeypatch.setattr(checks,'replicate',replicate)
    result=checks.run(newer,csv_path,True)
    assert result['changed_series_dates']==1
    assert not result['matches_pinned_numbers']
    assert 'WITHHELD' not in json.dumps(result)


def test_fetch_timeout_is_finite_and_retried(tmp_path):
    import socket
    from fed_cp_ot.ingest import fetch_vintage
    calls=[]
    def stalled(req, timeout=None):
        calls.append(timeout); raise socket.timeout('stalled')
    with pytest.raises(OSError): fetch_vintage(tmp_path/'c',opener=stalled,retries=3,backoff_s=0,timeout_s=5)
    assert calls==[5,5,5]


# --- Valid day is per type: all 12 of THAT type's series (6 buckets x AMT/VOL), never 48 at once, never filled ---
def _drop(types, day, series_filter=lambda sid: True):
    def mutate(attrs, obs):
        if attrs['CP_TYPE'] in types and series_filter(attrs['SERIES_NAME']):
            for row in obs:
                if row['TIME_PERIOD'] == day: row['OBS_STATUS'] = 'ND'; row['OBS_VALUE'] = '-9999'
    return mutate

def test_valid_day_is_per_type_not_all_48(provenance, tmp_path):
    # 2004-04-07: only AAA reports (FAA, NAA, NA2 and M all ND). A 48-series rule would void AAA's day; per type keeps it.
    df, report = load_vol(provenance, make_zip(tmp_path/'s.zip', _drop({'FAA', 'NAA', 'NA2', 'M'}, '2004-04-07')))
    w = build_weekly(df).set_index(['cp_type', 'week'])
    wk = pd.Timestamp('2004-04-09')
    assert w.loc[('AAA', wk), 'valid_days'] == 5
    for t in ('FAA', 'NAA', 'NA2'):
        assert w.loc[(t, wk), 'valid_days'] == 4
    assert report['anomalies']['AAA'] == [] and report['anomalies']['FAA'] == ['2004-04-07']

def test_valid_day_needs_all_12_of_the_type(provenance, tmp_path):
    # NA2 loses one of its 12 series on 2004-04-07 while the other types are complete -> partial type-day fails the run
    one = _drop({'NA2'}, '2004-04-07', lambda sid: sid == 'NONFIN.GT80.A2P2.VOL')
    with pytest.raises(ValidationError, match='Partial type-day'):
        load_vol(provenance, make_zip(tmp_path/'s.zip', one))

def test_missing_type_day_not_forward_filled(provenance, tmp_path):
    df, _ = load_vol(provenance, make_zip(tmp_path/'s.zip', _drop({'NA2'}, '2004-04-07')))
    na2 = df[(df.cp_type == 'NA2') & (df.date == '2004-04-07')]
    assert len(na2) == 12 and not na2.valid.any() and na2.value.isna().all()
    w = build_weekly(df).set_index(['cp_type', 'week'])
    full = build_weekly(load_vol(provenance, make_zip(tmp_path/'f.zip'))[0]).set_index(['cp_type', 'week'])
    wk = pd.Timestamp('2004-04-09')
    # dropping a day lowers the weekly sums (nothing carried forward from 2004-04-06)
    assert (w.loc[('NA2', wk), 'D'] < full.loc[('NA2', wk), 'D']).all()
