"""T6: Kumo NIM client, mock-tested only. No live call, no secret."""
import json
import numpy as np
import pandas as pd
import pytest
from fed_cp_ot import kumo
from fed_cp_ot.weekly import build_weekly, TYPES
from synth_vol import make_vol

KEY = 'nvapi-SECRET-TEST-KEY'

@pytest.fixture(scope='module')
def frame():
    return build_weekly(make_vol('2002-01-07', '2006-12-29', seed=3), through='2006-12-29')

class Transport:
    def __init__(self, *script): self.script, self.calls = list(script), []
    def __call__(self, url, body, headers, timeout):
        self.calls.append((url, body, dict(headers), timeout))
        step = self.script.pop(0)
        if isinstance(step, Exception): raise step
        return step

def ok_body(vals=None):
    vals = np.full(24, 1 / 6) if vals is None else vals
    return json.dumps({'predictions': [{'row_index': i, 'prediction': float(v)} for i, v in reversed(list(enumerate(vals)))]})

def client(tmp_path, *script, sleeps=None):
    t = Transport(*script); sleeps = [] if sleeps is None else sleeps
    return kumo.KumoClient(tmp_path / 'attempts.jsonl', transport=t, sleep=sleeps.append, key=KEY), t, sleeps

def test_payload_has_24_entities_and_156_usable_weeks_each(frame):
    o = pd.Timestamp('2006-12-29')
    p = kumo.build_payload(frame, o, 'best')
    ctx, pre = p['context']['related_tables'], p['predict']['related_tables']
    n_ctx = 24 * 155
    assert len(p['predict']['instance_table']['rows']) == 24 and len(p['context']['instance_table']['rows']) == n_ctx
    # Entity attribute rows are instance-scoped and declare instance_id (live NIM requirement).
    assert ctx['entities']['columns'][0] == 'instance_id'
    assert len(ctx['entities']['rows']) == n_ctx and len(pre['entities']['rows']) == 24
    assert all(r[0] == inst[0] and r[1] == inst[1]
               for r, inst in zip(ctx['entities']['rows'], p['context']['instance_table']['rows']))
    assert 'instance_id' in p['schema']['related_tables']['entities']['columns']
    assert len(ctx['weekly_facts']['rows']) + len(pre['weekly_facts']['rows']) == 24 * 156 == 3744
    assert p['inference'] == {'run_mode': 'best'} and p['task']['kind'] == 'regression'

def test_payload_is_anchored_at_o_and_never_looks_past_it(frame):
    o = pd.Timestamp('2006-06-30')
    p = kumo.build_payload(frame[frame.week <= o], o, 'fast')
    stamps = [r[2] for r in p['context']['instance_table']['rows']] + [r[2] for r in p['predict']['instance_table']['rows']]
    assert max(stamps) == o.strftime('%Y-%m-%dT%H:%M:%S.000000Z')
    assert all(r[3] <= o.strftime('%Y-%m-%dT%H:%M:%S.000000Z') for r in p['context']['related_tables']['weekly_facts']['rows'])
    with pytest.raises(ValueError): kumo.build_payload(frame, o, 'best')    # frame extends past the origin
    with pytest.raises(ValueError): kumo.build_payload(frame[frame.week <= o], o, 'turbo')

def test_labels_are_next_week_shares(frame):
    o = pd.Timestamp('2006-12-29'); p = kumo.build_payload(frame, o)
    inst = p['context']['instance_table']['rows'][0]      # entity 0 = (AAA, bucket 0); anchor and label from consecutive weeks
    h = frame[(frame.cp_type == 'AAA') & frame.usable].sort_values('week').tail(156)
    assert inst[2] == h.week.iloc[0].strftime('%Y-%m-%dT%H:%M:%S.000000Z') and inst[3] == pytest.approx(h.mix.iloc[1][0])

def test_payload_is_deterministic(frame):
    o = pd.Timestamp('2006-12-29')
    assert kumo.payload_sha256(kumo.build_payload(frame, o)) == kumo.payload_sha256(kumo.build_payload(frame.copy(), o))

def test_key_from_environment_only(tmp_path, monkeypatch):
    monkeypatch.delenv('NVIDIA_API_KEY', raising=False)
    with pytest.raises(kumo.KumoKeyMissing): kumo.KumoClient(tmp_path / 'a.jsonl')
    monkeypatch.setenv('NVIDIA_API_KEY', KEY)
    assert kumo.KumoClient(tmp_path / 'a.jsonl', transport=lambda *a: None)._key == KEY

def test_success_first_try_logs_one_attempt_without_the_key(tmp_path, frame):
    c, t, sleeps = client(tmp_path, (200, {'x-model-version': '1.1.0', 'other': 'y'}, ok_body()))
    p = kumo.build_payload(frame, pd.Timestamp('2006-12-29'))
    vals = c.predict(p, '2006-12-29', 'best')
    assert vals.shape == (24,) and sleeps == [] and len(t.calls) == 1
    assert t.calls[0][0] == kumo.URL and t.calls[0][2]['Authorization'] == 'Bearer ' + KEY
    log = (tmp_path / 'attempts.jsonl').read_text()
    row = json.loads(log)
    assert row['status'] == 200 and row['payload_sha256'] == kumo.payload_sha256(p) and row['model_headers'] == {'x-model-version': '1.1.0'}
    assert KEY not in log and 'latency_s' in row

def test_retries_429_5xx_and_network_errors_with_the_same_payload(tmp_path, frame):
    c, t, sleeps = client(tmp_path, (429, {}, ''), (503, {}, ''), TimeoutError('t'), (200, {}, ok_body()))
    p = kumo.build_payload(frame, pd.Timestamp('2006-12-29'))
    assert c.predict(p, '2006-12-29', 'best').shape == (24,)
    assert len(t.calls) == 4 and sleeps == [30, 30, 30] and len({call[1] for call in t.calls}) == 1
    rows = [json.loads(s) for s in (tmp_path / 'attempts.jsonl').read_text().splitlines()]
    assert [r['status'] for r in rows] == [429, 503, None, 200] and rows[2]['error'] == 'TimeoutError'
    assert len({r['payload_sha256'] for r in rows}) == 1

def test_gives_up_after_three_retries(tmp_path, frame):
    c, t, sleeps = client(tmp_path, *[(500, {}, '')] * 4)
    with pytest.raises(kumo.KumoFailure): c.predict(kumo.build_payload(frame, pd.Timestamp('2006-12-29')), '2006-12-29', 'best')
    assert len(t.calls) == 4 and sleeps == [30, 30, 30]

def test_other_client_errors_are_not_retried(tmp_path, frame):
    c, t, sleeps = client(tmp_path, (400, {}, 'bad'))
    with pytest.raises(kumo.KumoFailure): c.predict(kumo.build_payload(frame, pd.Timestamp('2006-12-29')), '2006-12-29', 'best')
    assert len(t.calls) == 1 and sleeps == []

@pytest.mark.parametrize('body', ['not json', json.dumps({'predictions': []}), ok_body(np.r_[np.full(23, .1), np.nan]).replace('NaN', 'null')])
def test_unusable_responses_fail(tmp_path, frame, body):
    c, _, _ = client(tmp_path, (200, {}, body))
    with pytest.raises(kumo.KumoFailure): c.predict(kumo.build_payload(frame, pd.Timestamp('2006-12-29')), '2006-12-29', 'best')

def test_predictions_come_back_in_row_order(tmp_path, frame):
    c, _, _ = client(tmp_path, (200, {}, ok_body(np.arange(24) / 100)))
    assert np.allclose(c.predict(kumo.build_payload(frame, pd.Timestamp('2006-12-29')), '2006-12-29', 'best'), np.arange(24) / 100)

def test_to_mixes_clips_and_renormalises_per_type():
    P = {t: np.full(6, 1 / 6) for t in TYPES}
    v = np.r_[[-0.2, 0.2, 0.2, 0.2, 0.2, 0.2], np.full(18, 1 / 6)]
    mix, failed = kumo.to_mixes(v, P)
    assert not failed and mix['AAA'][0] == 0 and mix['AAA'].sum() == pytest.approx(1) and mix['AAA'][1] == pytest.approx(0.2)

def test_all_nonpositive_type_falls_back_to_p_and_counts_as_failure():
    P = {t: np.eye(6)[2] for t in TYPES}
    v = np.r_[np.full(6, -0.1), np.full(18, 1 / 6)]
    mix, failed = kumo.to_mixes(v, P)
    assert failed and np.array_equal(mix['AAA'], P['AAA'])

def test_origin_failure_drops_the_origin_only(tmp_path, frame):
    c, _, _ = client(tmp_path, *[(500, {}, '')] * 4)
    P = {t: np.full(6, 1 / 6) for t in TYPES}
    assert kumo.kumo_forecast(c, frame, pd.Timestamp('2006-12-29'), 'best', P) == (None, True)

def test_family_k_incomplete_when_more_than_five_percent_fail():
    assert not kumo.family_k_incomplete(46, 927) and kumo.family_k_incomplete(47, 927)
    assert not kumo.family_k_incomplete(5, 100) and kumo.family_k_incomplete(6, 100) and kumo.family_k_incomplete(0, 0)

def test_modes_and_constants_are_pinned():
    assert kumo.MODES == ('best', 'fast') and kumo.MAX_RETRIES == 3 and kumo.BACKOFF_S == 30 and kumo.CONTEXT_WEEKS == 156
    assert kumo.URL == 'https://ai.api.nvidia.com/v1/structured-data/nvidia/kumo-relational/predictions'

def test_module_makes_no_network_call_on_import_or_build(frame, monkeypatch):
    import urllib.request
    monkeypatch.setattr(urllib.request, 'urlopen', lambda *a, **k: (_ for _ in ()).throw(AssertionError('network')))
    kumo.build_payload(frame, pd.Timestamp('2006-12-29'))
