"""prereg §6.3 test 11: the run is pinned to the committed test_design_trading_ot.json and a clean tree;
a modified design JSON makes the run fail; the OOS stop-gate holds while v1.1 is pending."""
import hashlib
import json
import subprocess

import pytest
from statement_forecast import prereg
from trading_ot import run

RELATIVE = 'tracks/y9c-trading-ot/test_design_trading_ot.json'


def git(repo, *args):
    return subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@example.com', *args],
                          cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    design = tmp_path / RELATIVE
    design.parent.mkdir(parents=True)
    design.write_bytes(prereg.TRADING_OT_DESIGN_PATH.read_bytes())
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-q', '-m', 'pre-register trading OT')
    return tmp_path, design, git(tmp_path, 'rev-parse', 'HEAD')


def check(root, design, commit):
    return prereg.verify_trading_ot_preregistration(root=root, design_path=design, commit=commit)


def test_pinned_digest_matches_committed_design():
    assert hashlib.sha256(prereg.TRADING_OT_DESIGN_PATH.read_bytes()).hexdigest() == prereg.TRADING_OT_PREREG_SHA256
    pinned = subprocess.run(['git', 'show', f'{prereg.TRADING_OT_PREREG_COMMIT}:{RELATIVE}'], cwd=prereg.ROOT,
                            capture_output=True)
    if pinned.returncode != 0:
        pytest.skip('pre-registration commit not in local history')
    assert hashlib.sha256(pinned.stdout).hexdigest() == prereg.TRADING_OT_PREREG_SHA256
    files = subprocess.run(['git', 'show', '--name-only', '--format=', prereg.TRADING_OT_PREREG_COMMIT],
                           cwd=prereg.ROOT, capture_output=True, text=True, check=True).stdout.split()
    assert files == [RELATIVE]


def test_earlier_pins_untouched():
    assert prereg.PREREG_SHA256 == '915d8b220f9dcbdc844d464f7b98db739cc986fa48f9f14e0ed7b73d01ffa68f'
    assert prereg.COMBO_PREREG_SHA256 == 'b16c1a129cc7b9320c40716694c6d39b5a3c6277eaf1511dea7eeeebc70d49e6'


def test_clean_pinned_design_passes(repo):
    root, design, commit = repo
    assert check(root, design, commit)['test_design_sha256'] == prereg.TRADING_OT_PREREG_SHA256


def test_modified_design_fails(repo):
    root, design, commit = repo
    edited = json.loads(design.read_text(encoding='utf-8'))
    edited['primary']['H1']['widening_grid'] = [1.0, 2.0]
    design.write_text(json.dumps(edited, indent=2) + '\n', encoding='utf-8')
    with pytest.raises(prereg.PreregistrationError, match='not clean'):
        check(root, design, commit)
    git(root, 'commit', '-q', '-am', 'edit design after the fact')
    with pytest.raises(prereg.PreregistrationError, match='pinned pre-registration'):
        check(root, design, commit)


def test_oos_gate_closed_while_v11_pending():
    design = json.loads(prereg.TRADING_OT_DESIGN_PATH.read_text(encoding='utf-8'))
    with pytest.raises(run.OOSNotAuthorized):
        run.assert_oos_authorized(design)
    ok = dict(design, oos_authorized=False, open_questions=[dict(q, resolution='x') for q in design['open_questions']])
    run.assert_oos_authorized(ok)                  # design side: flag false + questions resolved
    with pytest.raises(run.OOSNotAuthorized):
        run.assert_oos_authorized(dict(ok, oos_authorized=True))    # a true flag is a failure (option (c))
