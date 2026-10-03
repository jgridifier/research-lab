"""The combination real-data run is pinned to the committed test_design_combo.json and a clean tree."""
import hashlib
import json
import subprocess

import pytest
from statement_forecast import prereg

RELATIVE = 'tracks/statement-forecast/test_design_combo.json'


def git(repo, *args):
    return subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@example.com', *args],
                          cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    design = tmp_path / RELATIVE
    design.parent.mkdir(parents=True)
    design.write_bytes(prereg.COMBO_DESIGN_PATH.read_bytes())
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-q', '-m', 'pre-register combination')
    return tmp_path, design, git(tmp_path, 'rev-parse', 'HEAD')


def check(repo_root, design, commit):
    return prereg.verify_combo_preregistration(root=repo_root, design_path=design, commit=commit)


def test_pinned_digest_matches_committed_combo_design():
    assert hashlib.sha256(prereg.COMBO_DESIGN_PATH.read_bytes()).hexdigest() == prereg.COMBO_PREREG_SHA256
    pinned = subprocess.run(['git', 'show', f'{prereg.COMBO_PREREG_COMMIT}:{RELATIVE}'], cwd=prereg.ROOT,
                            capture_output=True)
    if pinned.returncode != 0:
        pytest.skip('combination pre-registration commit not in local history')
    assert hashlib.sha256(pinned.stdout).hexdigest() == prereg.COMBO_PREREG_SHA256
    # The pre-registration commit touches the design file and nothing else.
    files = subprocess.run(['git', 'show', '--name-only', '--format=', prereg.COMBO_PREREG_COMMIT],
                           cwd=prereg.ROOT, capture_output=True, text=True, check=True).stdout.split()
    assert files == [RELATIVE]


def test_v1_pins_untouched_by_extension():
    assert prereg.PREREG_COMMIT == '3ea20c8f34e62927ea8b8dac54d19f34e4a17717'
    assert prereg.PREREG_SHA256 == '915d8b220f9dcbdc844d464f7b98db739cc986fa48f9f14e0ed7b73d01ffa68f'
    assert prereg.COMBO_PREREG_SHA256 != prereg.PREREG_SHA256


def test_clean_pinned_design_passes(repo):
    root, design, commit = repo
    result = check(root, design, commit)
    assert result['test_design_sha256'] == prereg.COMBO_PREREG_SHA256
    assert result['prereg_commit'] == commit and result['prereg_commit_available']


def test_later_committed_edit_fails_instead_of_becoming_new_preregistration(repo):
    root, design, commit = repo
    edited = json.loads(design.read_text(encoding='utf-8'))
    edited['method']['min_distinct_target_quarters'] = 4
    design.write_text(json.dumps(edited, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    git(root, 'commit', '-q', '-am', 'edit design after the fact')
    assert git(root, 'status', '--porcelain') == ''
    with pytest.raises(prereg.PreregistrationError, match='pinned pre-registration'):
        check(root, design, commit)


def test_dirty_tree_fails(repo):
    root, design, commit = repo
    (root / 'scratch.txt').write_text('untracked')
    with pytest.raises(prereg.PreregistrationError, match='not clean'):
        check(root, design, commit)
    (root / 'scratch.txt').unlink()
    design.write_text(design.read_text(encoding='utf-8') + ' ', encoding='utf-8')
    with pytest.raises(prereg.PreregistrationError, match='not clean'):
        check(root, design, commit)


def test_pinned_commit_blob_must_match(repo):
    root, design, _ = repo
    design.write_text('{}\n')
    git(root, 'commit', '-q', '-am', 'different design')
    wrong = git(root, 'rev-parse', 'HEAD')
    design.write_bytes(prereg.COMBO_DESIGN_PATH.read_bytes())
    git(root, 'commit', '-q', '-am', 'restore pinned bytes')
    with pytest.raises(prereg.PreregistrationError, match='does not hash'):
        check(root, design, wrong)


def test_v1_design_does_not_satisfy_combo_pin(repo):
    root, design, commit = repo
    v1 = root / 'tracks/statement-forecast/test_design.json'
    v1.write_bytes(prereg.DESIGN_PATH.read_bytes())
    git(root, 'add', '.')
    git(root, 'commit', '-q', '-m', 'add v1 design')
    with pytest.raises(prereg.PreregistrationError):
        prereg.verify_combo_preregistration(root=root, design_path=v1, commit=commit)
