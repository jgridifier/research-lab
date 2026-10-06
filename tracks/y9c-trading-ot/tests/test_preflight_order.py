"""Provenance checks run before anything is logged or scored (Quant, post-Phase-A fix).

Every OOS entry point calls run.preflight first: authorization, design pin sha256, errata sha256. A corrupted
errata copy or a design sha mismatch must raise with trials.jsonl unchanged and no scoring function called.
Authorization is mocked in memory; the pinned files are never modified (corrupted copies live in tmp_path).
"""
import pytest
from trading_ot import run, walkforward as W10, walkforward_v1_1 as V
from trading_ot.paths import DESIGN_PATH, DESIGN_PATH_V1_1, ERRATA_PATH, load_design

PRIOR = '{"type": "design_revision", "counts_as_trial": false}\n'


def _fake():
    return dict(load_design(DESIGN_PATH_V1_1), oos_authorized=True)       # in memory only


def _no_scoring(monkeypatch):
    called = []
    boom = lambda name: (lambda *a, **k: called.append(name) or (_ for _ in ()).throw(AssertionError(name)))
    monkeypatch.setattr(V, 'primary', boom('V.primary'))
    for f in ['freeze_decisions', 'h1_oos', 'h2_oos']:
        monkeypatch.setattr(W10, f, boom(f'W10.{f}'))
    return called


def _corrupt_copy(src, dst):
    dst.write_bytes(src.read_bytes() + b' ')
    return dst


def _entry_points(tmp_path, trials):
    import pandas as pd
    empty = pd.DataFrame()
    yield 'v1_1', lambda: run.run_oos_v1_1(empty, empty, _fake(), tmp_path, trials_path=trials)
    yield 'R1', lambda: run.run_oos_v1_0(empty, empty, _fake(), tmp_path, trials_path=trials)
    if hasattr(run, 'run_secondary_v1_1'):
        yield 'secondary', lambda: run.run_secondary_v1_1(empty, empty, _fake(), tmp_path, trials_path=trials)
    if hasattr(run, 'run_sensitivities_v1_1'):
        yield 'sensitivities', lambda: run.run_sensitivities_v1_1(empty, empty, _fake(), tmp_path,
                                                                  trials_path=trials)
    if hasattr(run, 'run_all_v1_1'):
        yield 'all', lambda: run.run_all_v1_1(empty, empty, _fake(), tmp_path, trials_path=trials)


@pytest.mark.parametrize('target', ['errata', 'design_v1_1', 'design_v1_0'])
def test_mismatch_raises_before_trial_log(tmp_path, monkeypatch, target):
    called = _no_scoring(monkeypatch)
    trials = tmp_path / 'trials.jsonl'
    trials.write_text(PRIOR)
    if target == 'errata':
        monkeypatch.setattr(run, 'ERRATA_PATH', _corrupt_copy(ERRATA_PATH, tmp_path / 'ERRATA_v1_1.md'))
    elif target == 'design_v1_1':
        monkeypatch.setattr(run, 'DESIGN_PATH_V1_1', _corrupt_copy(DESIGN_PATH_V1_1, tmp_path / 'd11.json'))
    else:
        monkeypatch.setattr(run, 'DESIGN_PATH', _corrupt_copy(DESIGN_PATH, tmp_path / 'd10.json'))
    ran = 0
    for name, call in _entry_points(tmp_path, trials):
        if target == 'design_v1_0' and name not in ('R1', 'all', 'sensitivities'):
            continue                                            # only R1 reads the v1.0 design
        with pytest.raises(run.ProvenanceError):
            call()
        ran += 1
        assert trials.read_text() == PRIOR, name               # nothing appended
        assert not called, (name, called)                      # nothing scored
        assert not any(tmp_path.glob('*.json')) or all(p.name in ('d11.json', 'd10.json')
                                                       for p in tmp_path.glob('*.json'))
    assert ran >= 1


def test_pinned_files_verify_in_preflight():
    pre = run.preflight(_fake(), ('v1_1', 'v1_0'))
    assert pre['designs']['v1_1']['design_sha256'].startswith('93035364')
    assert pre['designs']['v1_0']['design_sha256'].startswith('dffd1323')
    assert pre['errata']['sha256'].startswith('68d5128f')


def test_unauthorized_beats_provenance(tmp_path, monkeypatch):
    """Authorization is still the very first check, even when a file is also corrupted."""
    monkeypatch.setattr(run, 'ERRATA_PATH', _corrupt_copy(ERRATA_PATH, tmp_path / 'E.md'))
    with pytest.raises(run.OOSNotAuthorized):
        run.preflight(load_design(DESIGN_PATH_V1_1))
