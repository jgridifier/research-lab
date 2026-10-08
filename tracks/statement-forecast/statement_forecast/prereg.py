"""Pinned pre-registration check for the real-data run.

The pre-registration is the exact bytes of test_design.json as committed on
its own in PREREG_COMMIT (before the first real-data run). The check pins that
digest rather than trusting whatever the latest commit touching the file says,
so a later committed edit to test_design.json fails instead of silently
becoming the new pre-registration. The working tree must also be clean, so the
run is attributable to a single commit.
"""
import hashlib
import subprocess

from .paths import DESIGN_PATH, ROOT

PREREG_COMMIT = '3ea20c8f34e62927ea8b8dac54d19f34e4a17717'
PREREG_COMMIT_TIME = '2026-09-26T17:14:22-04:00'
# sha256 of `git show 3ea20c8:tracks/statement-forecast/test_design.json`
PREREG_SHA256 = '915d8b220f9dcbdc844d464f7b98db739cc986fa48f9f14e0ed7b73d01ffa68f'


class PreregistrationError(RuntimeError):
    pass


def _git(root, *args):
    return subprocess.run(['git', *args], cwd=root, capture_output=True, check=False)


def verify_preregistration(root=ROOT, design_path=DESIGN_PATH, commit=PREREG_COMMIT,
                           sha256=PREREG_SHA256, commit_time=PREREG_COMMIT_TIME):
    """Raise PreregistrationError unless the run is tied to the pinned design.

    Requires: a clean working tree (no staged, unstaged or untracked changes);
    the design file on disk and at HEAD both hash to the pinned digest; and, when
    the pinned commit is present locally, its blob hashes to the same digest.
    Returns provenance for run metadata.
    """
    relative = design_path.relative_to(root).as_posix()
    status = _git(root, 'status', '--porcelain')
    if status.returncode != 0:
        raise PreregistrationError(f'git status failed: {status.stderr.decode().strip()}')
    if status.stdout.strip():
        raise PreregistrationError('Working tree is not clean; commit or remove changes before the real-data run:\n'
                                   + status.stdout.decode())
    on_disk = hashlib.sha256(design_path.read_bytes()).hexdigest()
    if on_disk != sha256:
        raise PreregistrationError(f'{relative} sha256 {on_disk} != pinned pre-registration {sha256} '
                                   f'(commit {commit}); a changed design is not a new pre-registration')
    head = _git(root, 'show', f'HEAD:{relative}')
    if head.returncode != 0 or hashlib.sha256(head.stdout).hexdigest() != sha256:
        raise PreregistrationError(f'{relative} at HEAD does not match the pinned pre-registration {sha256}')
    pinned = _git(root, 'show', f'{commit}:{relative}')
    commit_available = pinned.returncode == 0
    if commit_available and hashlib.sha256(pinned.stdout).hexdigest() != sha256:
        raise PreregistrationError(f'{relative} in {commit} does not hash to the pinned {sha256}')
    return dict(prereg_commit=commit, prereg_commit_time=commit_time, test_design_sha256=sha256,
                prereg_commit_available=commit_available)


# ── Statement Forecast v2 (naive / pooled-AR combination) ──────────────────
# Extension only: the v1 constants and verify_preregistration above are
# unchanged. The combination pre-registration is test_design_combo.json as
# committed on its own in COMBO_PREREG_COMMIT, before its single real run.
COMBO_DESIGN_PATH = DESIGN_PATH.parent / 'test_design_combo.json'
COMBO_PREREG_COMMIT = '288d4b85af9526666715ac265aa715aaab059194'
COMBO_PREREG_COMMIT_TIME = '2026-10-03T08:01:24-04:00'
# sha256 of `git show 288d4b8:tracks/statement-forecast/test_design_combo.json`
COMBO_PREREG_SHA256 = 'b16c1a129cc7b9320c40716694c6d39b5a3c6277eaf1511dea7eeeebc70d49e6'


def verify_combo_preregistration(root=ROOT, design_path=COMBO_DESIGN_PATH, commit=COMBO_PREREG_COMMIT,
                                 sha256=COMBO_PREREG_SHA256, commit_time=COMBO_PREREG_COMMIT_TIME):
    """Same checks as verify_preregistration, pinned to the combination design."""
    return verify_preregistration(root=root, design_path=design_path, commit=commit,
                                  sha256=sha256, commit_time=commit_time)


# ── Y-9C trading revenue + OT layers (tracks/y9c-trading-ot) ───────────────
# Extension only: earlier constants are unchanged. The trading-OT design is
# test_design_trading_ot.json as committed on its own in TRADING_OT_PREREG_COMMIT.
TRADING_OT_DESIGN_PATH = ROOT / 'tracks/y9c-trading-ot/test_design_trading_ot.json'
TRADING_OT_PREREG_COMMIT = '4e331390f6230970531203fcf73ba369703a328c'
TRADING_OT_PREREG_COMMIT_TIME = '2026-10-06T06:01:04-04:00'
# sha256 of `git show 4e33139:tracks/y9c-trading-ot/test_design_trading_ot.json`
TRADING_OT_PREREG_SHA256 = 'dffd1323883cb04e198853d95d4078fb67b4e0c8af4c8d19ef17d7f8f6234e30'


def verify_trading_ot_preregistration(root=ROOT, design_path=TRADING_OT_DESIGN_PATH,
                                      commit=TRADING_OT_PREREG_COMMIT, sha256=TRADING_OT_PREREG_SHA256,
                                      commit_time=TRADING_OT_PREREG_COMMIT_TIME):
    """Same checks as verify_preregistration, pinned to the trading-OT design."""
    return verify_preregistration(root=root, design_path=design_path, commit=commit,
                                  sha256=sha256, commit_time=commit_time)


# ── Y-9C trading revenue + OT, design v1.1 (prereg addendum: extended history) ──
# Extension only: the v1.0 trading-OT pin above is unchanged and still verifies (R1).
TRADING_OT_V1_1_DESIGN_PATH = ROOT / 'tracks/y9c-trading-ot/test_design_trading_ot_v1_1.json'
TRADING_OT_V1_1_PREREG_COMMIT = '06dbc28bed1609684efc664048e33178d0875af1'
TRADING_OT_V1_1_PREREG_COMMIT_TIME = '2026-10-06T06:17:43-04:00'
# sha256 of `git show 06dbc28:tracks/y9c-trading-ot/test_design_trading_ot_v1_1.json`
TRADING_OT_V1_1_PREREG_SHA256 = '930353641c6af0b4846d6678648a7446a738a579a52b4863726c9edb5a6a9694'


def verify_trading_ot_v1_1_preregistration(root=ROOT, design_path=TRADING_OT_V1_1_DESIGN_PATH,
                                           commit=TRADING_OT_V1_1_PREREG_COMMIT,
                                           sha256=TRADING_OT_V1_1_PREREG_SHA256,
                                           commit_time=TRADING_OT_V1_1_PREREG_COMMIT_TIME):
    """Same checks as verify_preregistration, pinned to the trading-OT v1.1 design."""
    return verify_preregistration(root=root, design_path=design_path, commit=commit,
                                  sha256=sha256, commit_time=commit_time)
