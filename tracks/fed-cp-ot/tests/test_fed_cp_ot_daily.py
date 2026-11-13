import io
import json
import re
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
import pytest
from synth import make_zip
from fed_cp_ot import daily, gate
from fed_cp_ot.alerts import alert, open_or_update_issue
from fed_cp_ot.burnin_hash import (HashMismatch, STDOUT_SHA256, SCRIPT_SHA256, check_design_pins, check_file,
                                   main as hash_main)
from fed_cp_ot.errors import ProvenanceError, ScoringWallError, ValidationError
from fed_cp_ot.fed_holidays import FED_HOLIDAYS, is_fed_holiday
from fed_cp_ot.fedcal import fed_holidays
from fed_cp_ot.ingest import fetch_vintage
from fed_cp_ot.manifest_chain import ChainError, append_chained, verify_chain
from fed_cp_ot.release_assets import MissingAssetError, download_asset
from fed_cp_ot.wall import wall_guard
from fed_cp_ot.paths import ROOT

ET = ZoneInfo('America/New_York')
def et(y, m, d, h, mi): return datetime(y, m, d, h, mi, tzinfo=ET).astimezone(timezone.utc)

# ---- holidays ----
def test_holiday_list_matches_computed_rules():
    for year in range(2025, 2031):
        assert {d for d in FED_HOLIDAYS if d.year == year} == set(fed_holidays(year))

@pytest.mark.parametrize('d,expected', [
    (date(2027, 7, 5), True), (date(2027, 7, 4), False),     # Sunday holiday observed Monday
    (date(2026, 7, 3), False), (date(2026, 7, 4), False),    # Saturday holiday not moved to Friday
    (date(2027, 12, 24), False), (date(2028, 12, 25), True),
    (date(2029, 11, 12), True), (date(2026, 6, 19), True), (date(2025, 11, 27), True)])
def test_observed_rules(d, expected): assert is_fed_holiday(d) is expected

def test_holiday_out_of_range_raises():
    with pytest.raises(ValueError): is_fed_holiday(date(2031, 1, 1))

# ---- gate ----
@pytest.mark.parametrize('args,run', [
    ((2026, 10, 29, 13, 29), False), ((2026, 10, 29, 13, 30), True), ((2026, 10, 29, 18, 0), True),
    ((2026, 10, 29, 18, 30), False),              # EDT
    ((2026, 12, 15, 13, 30), True), ((2026, 12, 15, 18, 0), True), ((2026, 12, 15, 18, 30), False),  # EST
    ((2026, 10, 31, 14, 0), False),               # Saturday
    ((2026, 11, 26, 14, 0), False),               # Thanksgiving
    ((2026, 12, 24, 14, 0), True)])
def test_gate_window_and_calendar(args, run):
    assert gate.decide(et(*args), [])[0] is run

def test_gate_utc_cron_hours_map_to_et_in_both_zones():
    # 17:30 UTC is 13:30 EDT; 18:30 UTC is 13:30 EST; 22:00 UTC is 18:00 EDT; 23:00 UTC is 18:00 EST
    assert gate.decide(datetime(2026, 10, 29, 17, 30, tzinfo=timezone.utc), [])[0]
    assert gate.decide(datetime(2026, 12, 15, 18, 30, tzinfo=timezone.utc), [])[0]
    assert gate.decide(datetime(2026, 10, 29, 22, 30, tzinfo=timezone.utc), [])[0] is False
    assert gate.decide(datetime(2026, 12, 15, 23, 0, tzinfo=timezone.utc), [])[0]
    assert gate.decide(datetime(2026, 12, 15, 17, 30, tzinfo=timezone.utc), [])[0] is False

def test_gate_requires_aware_clock():
    with pytest.raises(ValueError): gate.decide(datetime(2026, 10, 29, 14, 0), [])

def test_gate_skips_when_todays_vintage_ingested():
    now = et(2026, 10, 29, 14, 0)
    ok = {'fetched_at_et': '2026-10-29T13:31:00-04:00', 'last_modified': 'Thu, 29 Oct 2026 17:05:00 GMT'}
    stale = {'fetched_at_et': '2026-10-29T13:31:00-04:00', 'last_modified': 'Wed, 28 Oct 2026 17:05:00 GMT'}
    assert gate.decide(now, [ok])[0] is False
    assert gate.decide(now, [stale])[0] is True            # still yesterday's file: keep retrying
    assert gate.decide(now, [{'fetched_at_et': '2026-10-29T13:31:00-04:00', 'last_modified': None}])[0] is True
    assert gate.decide(now, [dict(ok, fetched_at_et='2026-10-28T13:31:00-04:00')])[0] is True

def test_gate_workflow_cron_covers_window():
    text = (ROOT/'.github/workflows/fed-cp-ot-daily.yml').read_text()
    crons = re.findall(r"- cron: '(\S+) (\S+) \* \* 1-5'", text)
    assert crons
    fires = set()
    for minutes, hours in crons:
        hs = range(int(hours.split('-')[0]), int(hours.split('-')[-1]) + 1) if '-' in hours else [int(hours)]
        fires |= {(h, int(m)) for h in hs for m in minutes.split(',')}
    for offset in (4, 5):  # EDT, EST
        t = datetime(2026, 1, 1, 13, 30)
        while t <= datetime(2026, 1, 1, 18, 0):
            assert ((t.hour + offset), t.minute) in fires, (offset, t)
            t += timedelta(minutes=30)

# ---- manifest chain ----
def _mk(path, n=3):
    for i in range(n): append_chained(path, {'i': i})

def test_chain_ok_and_tamper_detection(tmp_path):
    p = tmp_path/'m.jsonl'; _mk(p)
    assert verify_chain(p) == 3
    lines = p.read_text().splitlines()
    edited = json.loads(lines[1]); edited['i'] = 99
    for bad in ([lines[0], json.dumps(edited), lines[2]], [lines[0], lines[2]], [lines[1], lines[0], lines[2]],
                [lines[0], lines[1]][:1] + ['{not json']):
        p.write_text('\n'.join(bad) + '\n')
        with pytest.raises(ChainError): verify_chain(p)

def test_chain_edit_with_recomputed_own_hash_still_fails(tmp_path):
    from fed_cp_ot.manifest_chain import entry_hash
    p = tmp_path/'m.jsonl'; _mk(p)
    rows = [json.loads(l) for l in p.read_text().splitlines()]
    rows[0]['i'] = 7; rows[0]['entry_hash'] = entry_hash(rows[0])
    p.write_text('\n'.join(json.dumps(r) for r in rows) + '\n')
    with pytest.raises(ChainError): verify_chain(p)

def test_append_refuses_broken_chain(tmp_path):
    p = tmp_path/'m.jsonl'; _mk(p)
    p.write_text(p.read_text().replace('"i": 1', '"i": 5'))
    with pytest.raises(ChainError): append_chained(p, {'i': 9})

def _opener(blob, lm='Thu, 29 Oct 2026 17:05:00 GMT'):
    class R(io.BytesIO):
        status = 200
        headers = {'ETag': 'e', 'Last-Modified': lm, 'Content-Length': str(len(blob))}
    return lambda req, timeout=None: R(blob)

def test_fetch_manifest_is_chained_with_required_fields(tmp_path):
    blob = make_zip(tmp_path/'s.zip').read_bytes()
    row = fetch_vintage(tmp_path/'c', opener=_opener(blob)); fetch_vintage(tmp_path/'c', opener=_opener(blob))
    assert row['sha256'] and row['fetched_at_utc'].endswith('+00:00') and row['last_modified'].startswith('Thu')
    assert verify_chain(tmp_path/'c'/'manifest.jsonl') == 2

# ---- wall guard ----
def test_post_wall_values_never_returned(provenance, tmp_path):
    from fed_cp_ot.parse import parse_vol
    z = make_zip(tmp_path/'z.zip')
    frame, report = parse_vol(z, provenance)
    post = frame[frame.date > pd.Timestamp('2008-12-26')]
    assert len(post) > 0 and post.value.isna().all()
    assert (frame.value.dropna() != 99999).all()

def test_post_wall_text_never_converted(provenance, tmp_path, monkeypatch):
    import builtins
    from fed_cp_ot import parse
    seen = []
    def spy(x=0):
        seen.append(x); return builtins.float(x)
    monkeypatch.setattr(parse, 'float', spy, raising=False)
    parse.parse_vol(make_zip(tmp_path/'z.zip'), provenance)
    assert seen and '99999' not in seen

def test_wall_guard_blanks_and_is_idempotent():
    f = pd.DataFrame({'date': pd.to_datetime(['2008-12-26', '2009-01-02']), 'value': [1.0, 2.0]})
    out = wall_guard(f)
    assert out.value.tolist()[0] == 1.0 and pd.isna(out.value.iloc[1]) and f.value.iloc[1] == 2.0
    assert wall_guard(out).equals(out)

def test_load_vol_burnin_provenance_is_guarded_even_if_parser_were_lax(provenance, tmp_path, monkeypatch):
    from fed_cp_ot import parse
    monkeypatch.setattr(parse, 'readable', lambda d, w=None: True)   # simulate a buggy in-loop check
    frame, _ = parse.load_vol(provenance, make_zip(tmp_path/'z.zip'))
    assert frame[frame.date > pd.Timestamp('2008-12-26')].value.isna().all()

def test_app_burnin_only_and_refuses_when_flag_flips(pins, tmp_path, monkeypatch):
    from fed_cp_ot import app, wall
    out = app.build_app(out=tmp_path/'i.html', zip_path=make_zip(tmp_path/'z.zip'))
    html = out.read_text()
    assert '99999' not in html and '2009-01-02' not in html and 'burn-in' in html
    monkeypatch.setattr(app, 'oos_authorized', lambda: True)
    with pytest.raises(ProvenanceError): app.build_app(out=tmp_path/'j.html', zip_path=make_zip(tmp_path/'z.zip'))
    assert wall.oos_authorized() is False

# ---- alerts, release assets ----
class FakeRun:
    def __init__(self, listed='[]', rc=0): self.calls, self.listed, self.rc = [], listed, rc
    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        return subprocess.CompletedProcess(cmd, self.rc, stdout=self.listed if cmd[2] == 'list' else '', stderr='nope')

def test_issue_created_then_updated():
    r = FakeRun(); assert open_or_update_issue('T', 'b', runner=r) == 'created' and r.calls[-1][2] == 'create'
    r = FakeRun(json.dumps([{'number': 7, 'title': 'T other'}, {'number': 9, 'title': 'T'}]))
    assert open_or_update_issue('T', 'b', runner=r) == 'commented' and r.calls[-1][:4] == ['gh', 'issue', 'comment', '9']

def test_alert_annotates_and_survives_gh_failure(capsys):
    def boom(cmd, **kw): raise subprocess.CalledProcessError(1, cmd)
    alert('T', 'line1\nline2', issue=True, runner=boom)
    out = capsys.readouterr().out
    assert '::error title=fed-cp-ot::T: line1%0Aline2' in out and '::warning' in out

def test_missing_release_asset_raises(tmp_path):
    with pytest.raises(MissingAssetError): download_asset('t', 'a.zip', tmp_path, runner=FakeRun(rc=1))
    ok = lambda cmd, **kw: (tmp_path/'a.zip').write_bytes(b'x') and subprocess.CompletedProcess(cmd, 0, '', '')
    assert download_asset('t', 'a.zip', tmp_path, runner=ok).name == 'a.zip'

# ---- daily steps ----
def _vintage_dir(tmp_path, mutate_second=None):
    d = tmp_path/'data'
    fetch_vintage(d, opener=_opener(make_zip(tmp_path/'a.zip').read_bytes()))
    def mut(attrs, obs):
        for o in obs:
            if o['TIME_PERIOD'] == '2008-12-22' and attrs['SERIES_NAME'].startswith('AB.1_4.AA.AMT'): o['OBS_VALUE'] = '12345'
    fetch_vintage(d, opener=_opener(make_zip(tmp_path/'b.zip', mutate=mut).read_bytes()))
    return d

def test_diff_step_records_change_and_chains_shas(pins, tmp_path):
    d = _vintage_dir(tmp_path)
    diff = daily.step_diff(d, download=lambda *a: pytest.fail('previous is local'))
    rec = json.loads((d/'vintage_diffs.jsonl').read_text().splitlines()[-1])
    assert len(rec['value_changes']) == 1 and rec['prev_sha256'] != rec['cur_sha256'] == diff['cur_sha256']

def test_diff_step_downloads_missing_previous(pins, tmp_path):
    d = _vintage_dir(tmp_path)
    rows = [json.loads(l) for l in (d/'manifest.jsonl').read_text().splitlines()]
    prev = d/rows[0]['path']; keep = prev.read_bytes(); prev.unlink()
    def dl(tag, name, dest): (Path(dest)/name).write_bytes(keep); return Path(dest)/name
    assert daily.step_diff(d, download=dl) is not None

def test_diff_step_skips_unchanged(pins, tmp_path):
    d = tmp_path/'data'; blob = make_zip(tmp_path/'a.zip').read_bytes()
    fetch_vintage(d, opener=_opener(blob)); fetch_vintage(d, opener=_opener(blob))
    assert daily.step_diff(d) is None and not (d/'vintage_diffs.jsonl').exists()

def test_validate_fails_hard_on_attribute_change(pins, tmp_path):
    d = tmp_path/'data'
    def mut(attrs, obs):
        if attrs['SERIES_NAME'].startswith('AB.1_4.AA.AMT'): attrs['CP_MAT_RANGE'] = '99'
    fetch_vintage(d, opener=_opener(make_zip(tmp_path/'a.zip', mutate=mut).read_bytes()))
    with pytest.raises(ValidationError): daily.step_validate(d)

def test_main_returns_1_and_opens_issue_on_chain_failure(tmp_path, monkeypatch, capsys):
    p = tmp_path/'manifest.jsonl'; _mk(p)
    p.write_text(p.read_text().replace('"i": 1', '"i": 5'))
    monkeypatch.setattr(daily, 'MANIFEST', p)
    calls = []
    monkeypatch.setattr('fed_cp_ot.alerts.open_or_update_issue', lambda t, b, runner=None: calls.append(t) or 'created')
    assert daily.main(['verify', '--issue']) == 1
    assert calls and '::error' in capsys.readouterr().out

def test_main_no_issue_for_transient_fetch_error(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr('fed_cp_ot.alerts.open_or_update_issue', lambda *a, **k: calls.append(1))
    monkeypatch.setattr(daily, 'step_fetch', lambda: (_ for _ in ()).throw(OSError('timeout')))
    assert daily.main(['fetch', '--issue']) == 1 and not calls

# ---- burn-in hash pin ----
def test_design_pins_and_constants():
    check_design_pins()
    assert STDOUT_SHA256 == '17a0b23936e5b0c56e15a4937830e0f032a55ff20713f45cda7cf2d5adc11e8e'

def test_hash_check_byte_for_byte(tmp_path):
    a = tmp_path/'s.py'; b = tmp_path/'o.txt'; a.write_bytes(b'x'); b.write_bytes(b'y')
    with pytest.raises(HashMismatch): check_file(a, SCRIPT_SHA256)
    assert hash_main(['--script', str(a), '--stdout', str(b)]) == 1
    assert hash_main(['--script', str(tmp_path/'missing'), '--stdout', str(b)]) == 1
