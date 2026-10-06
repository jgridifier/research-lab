"""run.run_all_v1_1 on SYNTHETIC data with authorization mocked in memory: one run writes gate.json,
secondary.json, sensitivities.json and r1.json, and every execution is a trial logged before it runs."""
import json

import pandas as pd
import pytest
from conftest import to_panel
from trading_ot import panel as P, run, select, sensitivity_v1_1 as SENS
from trading_ot.paths import DESIGN_PATH_V1_1, load_design

KW = dict(epochs=select.EPOCH_ORIGINS[:2], targets=pd.period_range('2014Q1', '2015Q4', freq='Q'))
SENS_SUBSET = ['S5', 'S7', 'S9', 'S10', 'S11', 'S13', 'S14', 'S15', 'FB4']


def _fake():
    return dict(load_design(DESIGN_PATH_V1_1), oos_authorized=True)


def _labels(path):
    return [json.loads(l)['label'] for l in path.read_text().splitlines() if l.strip()]


ERRATA_1B = '2f134632acf4120ba410e7e2eacb352895eb41d9fbe9207cd0ddc6d22fef21bf'


def test_run_all_writes_everything(tmp_path, panel11, macro11, ytd11, panel, macro):
    trials = tmp_path / 'trials.jsonl'
    inputs = dict(macro_dt=macro11.assign(vix=macro11.vix[::-1].to_numpy()),
                  panel_rule_b=P.prepare_v1_1(to_panel(ytd11), 'b'), panel_v1_0=panel, macro_v1_0=macro)
    out = run.run_all_v1_1(panel11, macro11, _fake(), tmp_path, trials_path=trials, inputs=inputs,
                           sensitivities=SENS_SUBSET, **KW)
    for f in ['gate.json', 'secondary.json', 'sensitivities.json', 'r1.json']:
        assert (tmp_path / f).exists(), f
    g = json.loads((tmp_path / 'gate.json').read_text())
    assert g['companions'] == ['secondary.json', 'sensitivities.json', 'r1.json']
    sec = json.loads((tmp_path / 'secondary.json').read_text())
    assert set(sec['results']) == set(['H1b', 'H1c', 'H1d', 'H1e_h2', 'H1e_h3', 'H1e_h4', 'H2b', 'H2c_persistence',
                                        'H2c_climatology', 'H2d', 'H2e', 'H2f'])
    assert set(sec['falsification']) == {'F1', 'F2', 'F3', 'F4', 'F5'}
    assert sec['provenance']['errata']['sha256'].startswith('68d5128f')
    sens_doc = json.loads((tmp_path / 'sensitivities.json').read_text())
    r1 = json.loads((tmp_path / 'r1.json').read_text())
    for doc in (g, sec, sens_doc, r1):
        assert doc['provenance']['errata_v1_1b']['sha256'] == ERRATA_1B
    sens = sens_doc['sensitivities']
    assert [s['id'] for s in sens] == [p['id'] for p in SENS.PLAN if p['id'] in SENS_SUBSET]
    assert all(s['status'] == 'ok' for s in sens)
    labels_out = {s['id']: s['label'] for s in sens}
    assert labels_out['S7'] == labels_out['S14'] == 'rescore, no re-selection'
    labels = _labels(trials)
    n_sec = 11                                   # 12 family tests; H2c's two comparators are one execution
    assert run.trial_count(trials) == 1 + n_sec + 1 + len(sens) + 1
    assert labels[0] == 'v1.1 primary' and labels[-1].startswith('R1')
    hashes = [json.loads(l)['config_hash'] for l in trials.read_text().splitlines()]
    assert len(set(hashes)) == len(hashes)


def test_trial_is_logged_before_execution(tmp_path, panel11, macro11, monkeypatch):
    trials = tmp_path / 'trials.jsonl'

    def boom(item, ctx):
        raise RuntimeError('stop')
    monkeypatch.setattr(SENS, 'run_item', boom)
    with pytest.raises(RuntimeError):
        run.run_all_v1_1(panel11, macro11, _fake(), tmp_path, trials_path=trials, run_r1=False,
                         secondary=['H1c'], sensitivities=['S13'], **KW)
    labels = _labels(trials)
    assert labels[-1] == 'v1.1 sensitivity S13:settings_frozen_2013Q4'
    assert not (tmp_path / 'sensitivities.json').exists()


def test_run_all_unauthorized(tmp_path, panel11, macro11):
    trials = tmp_path / 'trials.jsonl'
    with pytest.raises(run.OOSNotAuthorized):
        run.run_all_v1_1(panel11, macro11, load_design(DESIGN_PATH_V1_1), tmp_path, trials_path=trials, **KW)
    assert not trials.exists() and not any(tmp_path.glob('*.json'))
