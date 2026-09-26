"""The real-data run is pinned to the 3ea20c8 design bytes and a clean tree."""
import hashlib
import subprocess

import pytest
from statement_forecast import prereg
from statement_forecast.paths import DESIGN_PATH, ROOT

RELATIVE = 'tracks/statement-forecast/test_design.json'


def git(repo, *args):
    return subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@example.com', *args],
                          cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    design = tmp_path / RELATIVE
    design.parent.mkdir(parents=True)
    design.write_bytes(DESIGN_PATH.read_bytes())
    git(tmp_path, 'init', '-q')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-q', '-m', 'pre-register')
    return tmp_path, design, git(tmp_path, 'rev-parse', 'HEAD')


def check(repo_root, design, commit):
    return prereg.verify_preregistration(root=repo_root, design_path=design, commit=commit)


def test_pinned_digest_matches_committed_design():
    assert hashlib.sha256(DESIGN_PATH.read_bytes()).hexdigest() == prereg.PREREG_SHA256
    pinned = subprocess.run(['git', 'show', f'{prereg.PREREG_COMMIT}:{RELATIVE}'], cwd=ROOT, capture_output=True)
    if pinned.returncode != 0:
        pytest.skip('pre-registration commit not in local history')
    assert hashlib.sha256(pinned.stdout).hexdigest() == prereg.PREREG_SHA256


def test_clean_pinned_design_passes(repo):
    root, design, commit = repo
    result = check(root, design, commit)
    assert result['test_design_sha256'] == prereg.PREREG_SHA256
    assert result['prereg_commit'] == commit and result['prereg_commit_available']


def test_later_committed_edit_fails_instead_of_becoming_new_preregistration(repo):
    root, design, commit = repo
    design.write_text(design.read_text().replace('"window_T": 12', '"window_T": 8'))
    git(root, 'commit', '-q', '-am', 'edit design after the fact')
    # Clean tree, HEAD == disk, and the latest commit touching the file is the
    # edit: the old "match HEAD" check would pass; the pinned check must not.
    assert git(root, 'status', '--porcelain') == ''
    with pytest.raises(prereg.PreregistrationError, match='pinned pre-registration'):
        check(root, design, commit)


def test_dirty_tree_fails(repo):
    root, design, commit = repo
    (root / 'scratch.txt').write_text('untracked')
    with pytest.raises(prereg.PreregistrationError, match='not clean'):
        check(root, design, commit)
    (root / 'scratch.txt').unlink()
    design.write_text(design.read_text() + ' ')
    with pytest.raises(prereg.PreregistrationError, match='not clean'):
        check(root, design, commit)


def test_pinned_commit_blob_must_match(repo):
    root, design, _ = repo
    other = root / RELATIVE
    other.write_text('{}\n')
    git(root, 'commit', '-q', '-am', 'different design')
    wrong = git(root, 'rev-parse', 'HEAD')
    other.write_bytes(DESIGN_PATH.read_bytes())
    git(root, 'commit', '-q', '-am', 'restore pinned bytes')
    with pytest.raises(prereg.PreregistrationError, match='does not hash'):
        check(root, design, wrong)


def test_missing_pinned_commit_still_requires_pinned_digest(repo):
    root, design, _ = repo
    result = check(root, design, '0' * 40)
    assert result['prereg_commit_available'] is False
