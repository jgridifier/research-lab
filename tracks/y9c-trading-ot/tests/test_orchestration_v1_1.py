"""The gated v1.1 OOS orchestration, exercised on SYNTHETIC data only: the authorization check runs before
anything is computed or logged, and an authorized synthetic run logs one trial and writes gate.json."""
import json

import pandas as pd
import pytest
from trading_ot import run, select, walkforward_v1_1 as V
from trading_ot.paths import DESIGN_PATH_V1_1, load_design


def test_unauthorized_computes_nothing(tmp_path, monkeypatch, panel11, macro11):
    called = []
    monkeypatch.setattr(V, 'primary', lambda *a, **k: called.append(1))
    trials = tmp_path / 'trials.jsonl'
    with pytest.raises(run.OOSNotAuthorized):
        run.run_oos_v1_1(panel11, macro11, load_design(DESIGN_PATH_V1_1), tmp_path, trials_path=trials)
    with pytest.raises(run.OOSNotAuthorized):
        run.run_oos_v1_0(panel11, macro11, load_design(DESIGN_PATH_V1_1), tmp_path, trials_path=trials)
    assert not called and not trials.exists() and not (tmp_path / 'gate.json').exists()


def test_authorized_synthetic_run(tmp_path, panel11, macro11):
    fake = dict(load_design(DESIGN_PATH_V1_1), oos_authorized=True)      # in-memory only; the pinned file is untouched
    trials = tmp_path / 'trials.jsonl'
    out = run.run_oos_v1_1(panel11, macro11, fake, tmp_path, trials_path=trials,
                           epochs=select.EPOCH_ORIGINS[:2], targets=pd.period_range('2014Q1', '2015Q4', freq='Q'))
    assert run.trial_count(trials) == 1
    g = json.loads((tmp_path / 'gate.json').read_text())
    assert set(g['hypotheses']) == {'H1', 'H2'}
    for h in g['hypotheses'].values():
        assert h['verdict'] == 'INCOMPLETE'          # 8 synthetic targets < 40
        assert set(h['subperiods']) == {'P1', 'P2', 'P3'} and h['dm']['M'] == 2
    assert [e['epoch'] for e in g['selection_log']] == ['2013Q4', '2014Q4']
    assert g['provenance']['errata'] == {
        'path': 'tracks/y9c-trading-ot/prereg/ERRATA_v1_1.md',
        'sha256': '68d5128fa3da40d269340afda3862ee89374bd6df59ad108c9e84d8698a17fe9',
        'precedence': 'where a stated value conflicts with an operative rule of the pinned design, the rule governs'}
    assert g['provenance']['design_sha256'] == '930353641c6af0b4846d6678648a7446a738a579a52b4863726c9edb5a6a9694'
    assert g['provenance']['errata_v1_1b'] == {
        'path': 'tracks/y9c-trading-ot/prereg/ERRATA_v1_1b.md',
        'sha256': '2f134632acf4120ba410e7e2eacb352895eb41d9fbe9207cd0ddc6d22fef21bf',
        'precedence': 'where a stated value conflicts with an operative rule of the pinned design, the rule governs'}


def test_authorized_synthetic_r1(tmp_path, panel, macro):
    """R1 = v1.0 design with B6 excluded from M0 / B* eligibility but still reported (addendum §6 Q1)."""
    fake = dict(load_design(DESIGN_PATH_V1_1), oos_authorized=True)
    out = run.run_oos_v1_0(panel, macro, fake, tmp_path, trials_path=tmp_path / 'trials.jsonl')
    fr = out['frozen']
    assert 'B6' not in fr['members'] and 'B6' in fr['report_members'] and fr['b_star'] != 'B6'
    assert 'B6' not in fr['trimmed_members'] and fr['b_star_cs'] != 'B6'
    assert set(out['hypotheses']) == {'H1', 'H2'} and (tmp_path / 'r1.json').exists()
    assert out['provenance']['errata']['sha256'] == '68d5128fa3da40d269340afda3862ee89374bd6df59ad108c9e84d8698a17fe9'
    assert out['provenance']['errata_v1_1b']['sha256'] == '2f134632acf4120ba410e7e2eacb352895eb41d9fbe9207cd0ddc6d22fef21bf'
    assert run.trial_count(tmp_path / 'trials.jsonl') == 1      # R1 counts as a trial (ERRATA C2)
