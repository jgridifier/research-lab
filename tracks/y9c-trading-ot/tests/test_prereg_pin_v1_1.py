"""Addendum §5.3 test 16: the v1.1 design is pinned in its own commit; a modified v1.1 JSON fails; the v1.0 pin
still verifies; the design flag stays false (the pinned approval file is the switch); the trial log holds the design
revision followed by the 24 trials the one authorized run logged before it stopped in S4 (INCOMPLETE; no rerun)."""
import hashlib
import json
import subprocess

import pytest
from statement_forecast import prereg
from trading_ot import run
from trading_ot.paths import TRIALS_PATH

RELATIVE = 'tracks/y9c-trading-ot/test_design_trading_ot_v1_1.json'
SHA_V1_1 = '930353641c6af0b4846d6678648a7446a738a579a52b4863726c9edb5a6a9694'
RUN_HEAD = '5f11ed5618ec3bc9bd5b28c273aaaa942c808c2c'      # approval/preflight commit the OOS run used
RECORDED_TRIALS = 24                                           # the run stopped in S4 (INCOMPLETE; no rerun)
SHA_V1_0 = 'dffd1323883cb04e198853d95d4078fb67b4e0c8af4c8d19ef17d7f8f6234e30'
QUANT_SOURCE = '/workspace/research/y9c_ot_prereg/v1_1/test_design_trading_ot_v1_1.json'


def git(repo, *args):
    return subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@example.com', *args],
                          cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    design = tmp_path / RELATIVE
    design.parent.mkdir(parents=True)
    design.write_bytes(prereg.TRADING_OT_V1_1_DESIGN_PATH.read_bytes())
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-q', '-m', 'pre-register trading OT v1.1')
    return tmp_path, design, git(tmp_path, 'rev-parse', 'HEAD')


def test_v1_1_constants_and_own_commit():
    assert prereg.TRADING_OT_V1_1_PREREG_SHA256 == SHA_V1_1
    assert hashlib.sha256(prereg.TRADING_OT_V1_1_DESIGN_PATH.read_bytes()).hexdigest() == SHA_V1_1
    pinned = subprocess.run(['git', 'show', f'{prereg.TRADING_OT_V1_1_PREREG_COMMIT}:{RELATIVE}'], cwd=prereg.ROOT,
                            capture_output=True)
    if pinned.returncode != 0:
        pytest.skip('v1.1 pre-registration commit not in local history')
    assert hashlib.sha256(pinned.stdout).hexdigest() == SHA_V1_1
    files = subprocess.run(['git', 'show', '--name-only', '--format=', prereg.TRADING_OT_V1_1_PREREG_COMMIT],
                           cwd=prereg.ROOT, capture_output=True, text=True, check=True).stdout.split()
    assert files == [RELATIVE]


def test_verbatim_copy_of_quant_source():
    try:
        src = open(QUANT_SOURCE, 'rb').read()
    except FileNotFoundError:
        pytest.skip('prereg source folder not on this machine')
    assert src == prereg.TRADING_OT_V1_1_DESIGN_PATH.read_bytes()


def test_v1_0_pin_unchanged_and_still_verifies():
    assert prereg.TRADING_OT_PREREG_SHA256 == SHA_V1_0
    assert hashlib.sha256(prereg.TRADING_OT_DESIGN_PATH.read_bytes()).hexdigest() == SHA_V1_0
    design = json.loads(prereg.TRADING_OT_V1_1_DESIGN_PATH.read_text(encoding='utf-8'))
    assert design['supersedes_for_primary_gate']['sha256'] == SHA_V1_0


def test_clean_pinned_v1_1_passes(repo):
    root, design, commit = repo
    out = prereg.verify_trading_ot_v1_1_preregistration(root=root, design_path=design, commit=commit)
    assert out['test_design_sha256'] == SHA_V1_1


def test_modified_v1_1_fails(repo):
    root, design, commit = repo
    edited = json.loads(design.read_text(encoding='utf-8'))
    edited['window']['targets_h1'] = ['2018Q1', '2026Q2']
    design.write_text(json.dumps(edited, indent=1) + '\n', encoding='utf-8')
    with pytest.raises(prereg.PreregistrationError, match='not clean'):
        prereg.verify_trading_ot_v1_1_preregistration(root=root, design_path=design, commit=commit)
    git(root, 'commit', '-q', '-am', 'edit design after the fact')
    with pytest.raises(prereg.PreregistrationError, match='pinned pre-registration'):
        prereg.verify_trading_ot_v1_1_preregistration(root=root, design_path=design, commit=commit)


def test_v1_1_design_flag_stays_false(tmp_path, monkeypatch):
    """Quant option (c): the design's oos_authorized stays false; a true flag fails; without the approval file the
    gate is closed (stage_oos refuses before loading anything)."""
    design = json.loads(prereg.TRADING_OT_V1_1_DESIGN_PATH.read_text(encoding='utf-8'))
    assert design['oos_authorized'] is False and design['open_questions'] == []
    run.assert_oos_authorized(design)                              # design side passes only with the flag false
    with pytest.raises(run.OOSNotAuthorized):
        run.assert_oos_authorized(dict(design, oos_authorized=True))
    monkeypatch.setattr(run, 'OOS_APPROVAL_PATH', tmp_path / 'absent.json')
    with pytest.raises(run.OOSNotAuthorized):
        run.stage_oos('v1_1', '2026-10-06')
    with pytest.raises(run.OOSNotAuthorized):
        run.stage_oos('v1_0', '2026-10-06')     # R1 is authorized only through the v1.1 approval


def test_oos_approval_verbatim_and_hash():
    from trading_ot.paths import (EXPECTED_TRIALS_V1_1, OOS_APPROVAL_DESIGN_COMMIT, OOS_APPROVAL_PATH,
                                  OOS_APPROVAL_SHA256, OOS_APPROVAL_SOURCE)
    assert OOS_APPROVAL_SHA256 == 'fe473f36b5308a15bc22b80b87fd124ae081e52460c49120d36df4ad442c77d9'
    assert hashlib.sha256(OOS_APPROVAL_PATH.read_bytes()).hexdigest() == OOS_APPROVAL_SHA256
    a = json.loads(OOS_APPROVAL_PATH.read_text(encoding='utf-8'))
    assert a['design_sha256'] == SHA_V1_1 and a['design_commit'] == OOS_APPROVAL_DESIGN_COMMIT
    assert a['trials'] == EXPECTED_TRIALS_V1_1 == 39
    try:
        assert open(OOS_APPROVAL_SOURCE, 'rb').read() == OOS_APPROVAL_PATH.read_bytes()
    except FileNotFoundError:
        pass


def test_registered_executions_equal_approved_trials():
    from trading_ot import secondary_v1_1 as SEC, sensitivity_v1_1 as SENS
    from trading_ot.paths import EXPECTED_TRIALS_V1_1
    n = 1 + (len(SEC.FAMILY) - 1) + 2 + 1 + len(SENS.PLAN) + 1     # primary, family (H2c once), FPCA+ridge, F3, S*, R1
    assert n == EXPECTED_TRIALS_V1_1


def test_trial_log_design_revision_then_one_run():
    lines = [json.loads(x) for x in TRIALS_PATH.read_text(encoding='utf-8').splitlines() if x.strip()]
    assert lines[0] == {"type": "design_revision", "from": f"v1.0 {SHA_V1_0}", "to": f"v1.1 {SHA_V1_1}",
                        "oos_seen": False, "counts_as_trial": False,
                        "reason": "backfill 2008-2017; primary gate moved to 2014Q1-2026Q2 before any OOS score; "
                                  "see ADDENDUM_v1_1"}
    # Post-run (deliberate update, Quant ruling option 1): the one authorized run (approved for 39 trials by
    # prereg/OOS_APPROVAL_v1_1.json) logged 24 registered trials and then stopped in S4 (KeyError 2020Q1 in WAR-RM).
    # S4 was logged before it ran and is kept; no rerun, no completion. All from the approval/preflight commit.
    from trading_ot.paths import EXPECTED_TRIALS_V1_1
    trials = lines[1:]
    assert EXPECTED_TRIALS_V1_1 == 39                                # approved count (unchanged)
    assert run.trial_count() == len(trials) == RECORDED_TRIALS == 24
    assert all(t['status'] == 'registered' for t in trials)
    assert all(t['config']['design_sha256'] == SHA_V1_1 for t in trials if 'design_sha256' in t['config'])
    assert {t['git_head'] for t in trials} == {RUN_HEAD}
    assert len({t['config_hash'] for t in trials}) == len(trials)
    assert trials[0]['label'] == 'v1.1 primary'
    assert trials[-1]['label'] == 'v1.1 sensitivity S4:exclude_2020Q1Q2_training'
    assert not any(t['label'].startswith('R1') for t in trials)


def test_trial_count_rule(tmp_path):
    p = tmp_path / 'trials.jsonl'
    p.write_text(json.dumps({'type': 'design_revision', 'counts_as_trial': False}) + '\n')
    assert run.trial_count(p) == 0
    run.log_trial({'x': 1}, 'synthetic', path=p)
    assert run.trial_count(p) == 1


def test_errata_verbatim_and_hash():
    from trading_ot.paths import ERRATA_PATH, ERRATA_SHA256, ERRATA_SOURCE
    assert ERRATA_SHA256 == '68d5128fa3da40d269340afda3862ee89374bd6df59ad108c9e84d8698a17fe9'
    assert hashlib.sha256(ERRATA_PATH.read_bytes()).hexdigest() == ERRATA_SHA256
    assert run.errata_provenance()['sha256'] == ERRATA_SHA256
    try:
        assert open(ERRATA_SOURCE, 'rb').read() == ERRATA_PATH.read_bytes()
    except FileNotFoundError:
        pass


def test_errata_1b_verbatim_and_hash():
    from trading_ot.paths import ERRATA_1B_PATH, ERRATA_1B_SHA256, ERRATA_1B_SOURCE
    assert ERRATA_1B_SHA256 == '2f134632acf4120ba410e7e2eacb352895eb41d9fbe9207cd0ddc6d22fef21bf'
    assert hashlib.sha256(ERRATA_1B_PATH.read_bytes()).hexdigest() == ERRATA_1B_SHA256
    assert run.errata_provenance_1b()['sha256'] == ERRATA_1B_SHA256
    try:
        assert open(ERRATA_1B_SOURCE, 'rb').read() == ERRATA_1B_PATH.read_bytes()
    except FileNotFoundError:
        pass


def test_deferral_4b_verbatim_and_hash():
    from trading_ot.paths import DEFERRAL_4B_PATH, DEFERRAL_4B_SHA256, DEFERRAL_4B_SOURCE
    assert DEFERRAL_4B_SHA256 == '3867ba4f48441cbc0b3745bd67abb0fd9e6ee3940f8e2fdebbdc696e577c05df'
    assert hashlib.sha256(DEFERRAL_4B_PATH.read_bytes()).hexdigest() == DEFERRAL_4B_SHA256
    assert run.deferral_provenance_4b()['sha256'] == DEFERRAL_4B_SHA256
    try:
        assert open(DEFERRAL_4B_SOURCE, 'rb').read() == DEFERRAL_4B_PATH.read_bytes()
    except FileNotFoundError:
        pass
