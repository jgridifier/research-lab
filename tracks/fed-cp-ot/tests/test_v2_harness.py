"""T1/T3/T4/T8: vintage injection, entry gate, run-once lock, schedules written before scoring, dry run on burn-in only."""
import json
import numpy as np
import pandas as pd
import pytest
from fed_cp_ot import harness, trials, kumo
from fed_cp_ot import preflight as pf
from fed_cp_ot.candidates import ENTRIES, forecast_all
from fed_cp_ot.weekly import TYPES, build_weekly
from fed_cp_ot.errors import OOSNotAuthorized, RunOnceError, ScoringWallError
from fed_cp_ot import schedule as sched
from synth_vol import make_vol

def bits(fc): return {k: v.tobytes() for k, v in fc.items()}

def _inject_case(start, end, origin, prov):
    clean = make_vol(start, end, seed=11)
    o = pd.Timestamp(origin)
    dirty = pd.concat([clean, make_vol(start, end, seed=11, extra=(pd.date_range(o + pd.Timedelta(days=1), o + pd.Timedelta(days=7)), 1e6)).query('date > @o')],
                      ignore_index=True)
    assert (dirty.date > o).sum() > (clean.date > o).sum()  # the injection is really there
    h0, imd0 = harness.origin_frame(clean, o, prov)
    h1, imd1 = harness.origin_frame(dirty, o, prov)
    assert imd0 == imd1 <= o and h1.week.max() <= o
    f0, n0 = forecast_all(h0, o, TYPES); f1, n1 = forecast_all(h1, o, TYPES)
    assert bits(f0) == bits(f1) and set(f0) == {(e, t) for e in ENTRIES for t in TYPES}
    assert {k: (v[0].tobytes(), v[1].tobytes()) for k, v in n0.items()} == {k: (v[0].tobytes(), v[1].tobytes()) for k, v in n1.items()}

def test_v2_vintage_injection(provenance):
    """PREREG v2 4: extreme synthetic rows dated o+1..o+7 change no model's forecast, bit for bit."""
    _inject_case('2005-03-01', '2006-11-17', '2006-10-27', provenance)

def test_v2_vintage_injection_across_the_wall(approved):
    _inject_case('2007-10-01', '2009-03-27', '2009-01-16', approved)

def test_frame_input_max_date_comes_from_the_frame_not_the_caller():
    h = pd.DataFrame({'week': pd.to_datetime(['2006-10-20', '2006-10-27', '2006-11-03'])})
    with pytest.raises(ScoringWallError): harness.frame_input_max_date(h, '2006-10-27')
    assert harness.frame_input_max_date(h, '2006-11-03') == pd.Timestamp('2006-11-03')

def test_origin_frame_beyond_wall_needs_oos_provenance(provenance):
    vol = make_vol('2008-11-03', '2009-02-27', seed=1)
    with pytest.raises(ScoringWallError): harness.origin_frame(vol, '2009-01-16', provenance)

# ---------------- T1 entry ----------------
def test_run_oos_raises_not_authorized_on_main_before_reading_anything(monkeypatch):
    calls = []
    for name in ('load_vol', 'build_weekly', 'acquire_lock'):
        monkeypatch.setattr(harness, name, lambda *a, **k: calls.append(name))
    with pytest.raises(OOSNotAuthorized): harness.run_oos()
    assert calls == [] and pf.APPROVAL_SHA256 is None and not pf.APPROVAL_PATH.exists()
    with pytest.raises(OOSNotAuthorized): trials.run_oos()

def test_run_oos_refuses_a_zip_the_approval_does_not_name(approved, tmp_path):
    z = tmp_path / 'x.zip'; z.write_bytes(b'not the vintage')
    with pytest.raises(OOSNotAuthorized, match='vintage'): harness.run_oos(zip_path=z, out_dir=tmp_path, lock_path=tmp_path / 'lock',
                                                                         trials_path=tmp_path / 't.jsonl', kumo_client=object())
    assert not (tmp_path / 'lock').exists() and not (tmp_path / 't.jsonl').exists()

def test_run_oos_order_lock_then_trials_then_parse_and_second_run_refused(approved, tmp_path, monkeypatch):
    z = tmp_path / 'x.zip'; z.write_bytes(b'vintage')
    pf.APPROVAL_PATH.write_text('Jared approves ' + pf.PINS['PIN.txt'] + ' vintage ' + pf.sha256(z))
    monkeypatch.setattr(pf, 'APPROVAL_SHA256', pf.sha256(pf.APPROVAL_PATH))
    calls = []
    class Stop(Exception): pass
    monkeypatch.setattr(trials, 'git_head', lambda: 'a' * 40)
    real_log = trials.log_trial
    monkeypatch.setattr(trials, 'log_trial', lambda *a, **k: (calls.append('trial'), real_log(*a, **k))[1])
    def load(*a, **k): calls.append('load'); raise Stop
    monkeypatch.setattr(harness, 'load_vol', load)
    kw = dict(zip_path=z, out_dir=tmp_path / 'o', lock_path=tmp_path / 'lock', trials_path=tmp_path / 't.jsonl', kumo_client=object())
    with pytest.raises(Stop): harness.run_oos(**kw)
    assert calls == ['trial'] * 5 + ['load']
    rows = [json.loads(s) for s in (tmp_path / 't.jsonl').read_text().splitlines()]
    assert len(rows) == 5 and len({r['config_hash'] for r in rows}) == 5
    lock_sha = pf.hashlib.sha256((tmp_path / 'lock').read_bytes()).hexdigest()
    assert {r['lock_sha256'] for r in rows} == {lock_sha}      # the lock's sha is in the trial log
    assert (tmp_path / 'o' / 'run_manifest.json').exists()          # manifest written before the run
    calls.clear()
    with pytest.raises(RunOnceError): harness.run_oos(**kw)
    assert calls == []

def test_lock_is_exclusive(tmp_path):
    harness.acquire_lock(tmp_path / 'l', {'a': 1})
    with pytest.raises(RunOnceError): harness.acquire_lock(tmp_path / 'l', {'a': 1})

def test_v2_trial_labels_are_five_with_k_family():
    assert [l for l, _ in trials.CONFIRMATORY_TRIALS_V2] == ['WAR vs B*', 'TMAR vs B*', 'SEL vs P', 'Kumo-best vs SEL', 'Kumo-best vs P']

def test_no_approval_file_and_hash_unset():
    assert pf.APPROVAL_SHA256 is None and not pf.APPROVAL_PATH.exists()

# ---------------- T4 schedules ----------------
def losses_for(n, best, start='2006-01-06'):
    w = pd.date_range(start, periods=n, freq='W-FRI')
    return {e: {x: (1.0 if e == best else 1.5) for x in w} for e in ENTRIES}, w

def test_selection_uses_last_156_weeks_and_logs_span():
    L, w = losses_for(200, 'LS')
    s = sched.select(L, w[-1], ENTRIES)
    assert s['selected'] == 'LS' and s['n_weeks'] == 156 and s['window_first_week'] == str(w[-156].date())
    assert s['calendar_span_weeks'] == 156

def test_selection_span_exceeds_156_weeks_when_weeks_are_missing():
    L, w = losses_for(200, 'LS')
    for e in L:
        for x in w[100:110]: del L[e][x]    # unusable weeks drop out; window still holds 156 usable ones
    s = sched.select(L, w[-1], ENTRIES)
    assert s['n_weeks'] == 156 and s['calendar_span_weeks'] == 166

def test_selection_tie_band_goes_to_earlier_entry():
    L, w = losses_for(100, 'LS')
    for x in w: L['ALR-AR'][x] = 1.005 ; L['EXP'][x] = 1.009; L['LS'][x] = 1.0
    assert sched.select(L, w[-1], ENTRIES)['selected'] == 'EXP'     # EXP is within 1% of LS and earlier in the list
    for x in w: L['EXP'][x] = 1.02
    assert sched.select(L, w[-1], ENTRIES)['selected'] == 'LS'

def test_bstar_excludes_the_ot_candidates():
    L, w = losses_for(100, 'WAR')
    assert sched.select(L, w[-1], ENTRIES)['selected'] == 'WAR'
    assert sched.select(L, w[-1], sched.NON_OT)['selected'] == 'P'  # all non-OT tie at 1.5 -> the simplest

def test_reselection_is_first_origin_of_each_quarter_and_choice_is_held():
    L, w = losses_for(120, 'LS')
    origins = list(w[60:100])
    sel, bstar, rec = sched.build_schedules(L, origins)
    quarters = {(o.year, (o.month - 1) // 3) for o in origins}
    assert len(rec['SEL']) == len(quarters)
    assert all(pd.Timestamp(r['origin']) in origins for r in rec['SEL'])
    firsts = [pd.Timestamp(r['origin']) for r in rec['SEL']]
    assert all(sel[o] == 'LS' for o in origins if o >= firsts[0]) and all(sel[o] is None for o in origins if o < firsts[0])

def test_schedules_are_on_disk_before_any_scoring(tmp_path, monkeypatch):
    L, w = losses_for(130, 'LS')
    st = {'entry_loss': L, 'native_loss': {e: {} for e in ENTRIES}, 'forecasts': {}, 'imd': {},
          'kumo_fc': {}, 'kumo_loss': {m: {} for m in kumo.MODES}, 'kumo_failed': 0, 'kumo_origins': 0}
    seen = []
    real = harness.score_all
    def spy(*a, **k):
        seen.append(sorted(p.name for p in tmp_path.iterdir())); return real(*a, **k)
    monkeypatch.setattr(harness, 'score_all', spy)
    weekly = build_weekly(make_vol('2005-03-01', '2006-11-17', seed=2), through='2006-11-17')
    harness.finalize(st, list(w[60:120]), tmp_path, ('2006-01-06', '2008-12-26'), 'test', weekly)
    assert 'sel_schedule.json' in seen[0] and 'bstar_schedule.json' in seen[0]

# ---------------- dry run (synthetic, burn-in only) ----------------
def test_walk_forward_and_finalize_on_synthetic_burnin(provenance, tmp_path, monkeypatch):
    vol = make_vol('2005-01-03', '2006-09-29', seed=5)
    origins = harness.origin_list('2006-06-02', '2006-09-29')
    st = harness.walk_forward(vol, origins, provenance)
    assert set(st['entry_loss']['P']) == {o + harness.DAY for o in origins}
    assert max(st['imd'].values()) <= origins[-1]
    full = build_weekly(vol)
    out = harness.finalize(st, origins, tmp_path, ('2006-01-06', '2008-12-26'), harness.LABEL_DRY, full)
    assert all(r['incomplete'] for r in out['families'].values())           # far below 800 pairs
    assert out['families']['WAR vs B*']['wording'].startswith('underpowered to detect a 5% gain')
    assert (tmp_path / 'forecasts.jsonl').exists() and out['family_K']['incomplete']
    json.dumps(harness._jsonable(out), allow_nan=False)

def test_dry_run_refuses_amounts_after_the_wall(monkeypatch, tmp_path):
    vol = make_vol('2008-12-01', '2009-01-30', seed=1)
    monkeypatch.setattr(harness, 'load_vol', lambda *a, **k: (vol, {}))
    with pytest.raises(ScoringWallError): harness.dry_run_burnin(zip_path=tmp_path / 'x', out_dir=tmp_path)

def test_cli_has_exactly_the_two_commands():
    import argparse
    with pytest.raises(SystemExit): harness.main(['bogus'])
