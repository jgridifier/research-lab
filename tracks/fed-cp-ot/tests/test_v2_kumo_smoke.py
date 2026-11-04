"""Smoke guards are checked without network or OOS data."""
import hashlib
import json
from pathlib import Path
import pandas as pd
import pytest
from fed_cp_ot import kumo_smoke, kumo
from fed_cp_ot.errors import ScoringWallError
from synth_vol import make_vol


@pytest.mark.parametrize('target', ['2009-01-02', '2026-10-02', '2008-12-27',
                                    '2001-01-05', 'NaT', '2008-12-26T12:00',
                                    '2008-12-26T00:00Z'])
def test_smoke_rejects_invalid_target_before_io(target, monkeypatch, tmp_path):
    def forbidden(*a, **kw): raise AssertionError('I/O reached')
    monkeypatch.setattr(kumo_smoke, 'preflight', forbidden)
    monkeypatch.setattr(kumo, 'api_key', forbidden)
    with pytest.raises(ScoringWallError):
        kumo_smoke.run('missing.zip', tmp_path / 'evidence.json', target, forbidden)
    assert not (tmp_path / 'evidence.json').exists()


@pytest.mark.parametrize('status', [200, 429, 500, 'timeout'])
def test_smoke_one_request_no_retry_and_no_secret(status, monkeypatch, tmp_path):
    secret = 'test-secret-do-not-save'
    monkeypatch.setenv('NVIDIA_API_KEY', secret)
    monkeypatch.setattr(kumo_smoke, 'sha256', lambda _: 'synthetic')
    vol = make_vol('2005-01-03', '2008-12-19', seed=3)
    def parse(path, provenance, wall):
        assert provenance.mode == 'burnin' and not provenance.oos_approved
        assert wall == '2008-12-19'
        return vol, {}
    monkeypatch.setattr(kumo_smoke, 'parse_vol', parse)
    calls = []
    def transport(url, body, headers, timeout):
        calls.append(json.loads(body))
        assert headers['Authorization'] == 'Bearer ' + secret
        if status == 'timeout': raise TimeoutError(secret)
        return status, {'secret': secret}, json.dumps({
            'echo': secret, 'predictions': [{'row_index': i, 'prediction': 1/6} for i in range(24)]})
    path = tmp_path / 'evidence.json'
    if status == 200:
        kumo_smoke.run('unused.zip', path, transport=transport)
    else:
        with pytest.raises(kumo.KumoFailure):
            kumo_smoke.run('unused.zip', path, transport=transport)
    assert len(calls) == 1
    assert secret not in path.read_text()
    evidence = json.loads(path.read_text())
    assert evidence['parser_verified'] == (status == 200)
    assert evidence['target'] == '2008-12-26'
    with pytest.raises(FileExistsError):
        kumo_smoke.run('unused.zip', path, transport=transport)
    assert len(calls) == 1


def test_v2_manifest_hashes_and_includes_implementation_choices():
    root = Path(__file__).resolve().parents[3]
    manifest = root / 'tracks/fed-cp-ot/prereg/PIN_v2.txt'
    names = []
    for line in manifest.read_text().splitlines():
        digest, name = line.split()
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
        names.append(Path(name).name)
    assert set(names) == {'PREREG_v2_fed_cp_ot.md', 'GATE_THRESHOLDS_fed_cp_ot.md',
                          'PREREG_fed_cp_ot.md', 'test_design_fed_cp_ot_v1.json',
                          'IMPLEMENTATION_CHOICES_v2.md'}


def test_committed_smoke_evidence_is_burnin_only():
    root = Path(__file__).resolve().parents[3]
    evidence = json.loads((root / 'tracks/fed-cp-ot/artifacts/kumo_burnin_smoke_v2.json').read_text())
    origin = kumo_smoke.burnin_origin(evidence['target'])
    assert evidence['origin'] == str(origin.date())
    assert evidence['request_count'] == 1 and evidence['retries'] == 0
    payload = evidence['request']
    assert evidence['request_sha256'] == kumo.payload_sha256(payload)
    for section in ('context', 'predict'):
        for row in payload[section]['instance_table']['rows']:
            assert pd.Timestamp(row[2]).tz_localize(None) <= origin
        for row in payload[section]['related_tables']['weekly_facts']['rows']:
            assert pd.Timestamp(row[3]).tz_localize(None) <= origin
    assert evidence['parser_verified'] is False and evidence['error'] == 'TimeoutError'
    assert evidence['response'] is None and evidence['status'] is None
