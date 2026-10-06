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


def test_authorized_synthetic_r1(tmp_path, panel, macro):
    """R1 = v1.0 design with B6 excluded from M0 / B* eligibility but still reported (addendum §6 Q1)."""
    fake = dict(load_design(DESIGN_PATH_V1_1), oos_authorized=True)
    out = run.run_oos_v1_0(panel, macro, fake, tmp_path, trials_path=tmp_path / 'trials.jsonl')
    fr = out['frozen']
    assert 'B6' not in fr['members'] and 'B6' in fr['report_members'] and fr['b_star'] != 'B6'
    assert 'B6' not in fr['trimmed_members'] and fr['b_star_cs'] != 'B6'
    assert set(out['hypotheses']) == {'H1', 'H2'} and (tmp_path / 'r1.json').exists()
