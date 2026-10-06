"""Addendum §5.3 test 16: the v1.1 design is pinned in its own commit; a modified v1.1 JSON fails; the v1.0 pin
still verifies; the OOS gate stays closed (oos_authorized=false); the trial log holds the design revision only."""
import hashlib
import json
import subprocess

import pytest
from statement_forecast import prereg
from trading_ot import run
from trading_ot.paths import TRIALS_PATH

RELATIVE = 'tracks/y9c-trading-ot/test_design_trading_ot_v1_1.json'
SHA_V1_1 = '930353641c6af0b4846d6678648a7446a738a579a52b4863726c9edb5a6a9694'
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


def test_v1_1_gate_closed():
    design = json.loads(prereg.TRADING_OT_V1_1_DESIGN_PATH.read_text(encoding='utf-8'))
    assert design['oos_authorized'] is False and design['open_questions'] == []
    with pytest.raises(run.OOSNotAuthorized):
        run.assert_oos_authorized(design)
    with pytest.raises(run.OOSNotAuthorized):
        run.stage_oos('v1_1', '2026-10-06')
    with pytest.raises(run.OOSNotAuthorized):
        run.stage_oos('v1_0', '2026-10-06')     # R1 is authorized only through the v1.1 design


def test_trial_log_design_revision_only():
    lines = [json.loads(x) for x in TRIALS_PATH.read_text(encoding='utf-8').splitlines() if x.strip()]
    assert lines[0] == {"type": "design_revision", "from": f"v1.0 {SHA_V1_0}", "to": f"v1.1 {SHA_V1_1}",
                        "oos_seen": False, "counts_as_trial": False,
                        "reason": "backfill 2008-2017; primary gate moved to 2014Q1-2026Q2 before any OOS score; "
                                  "see ADDENDUM_v1_1"}
    assert run.trial_count() == 0


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
