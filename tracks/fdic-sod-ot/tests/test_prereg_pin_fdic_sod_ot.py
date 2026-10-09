"""Hash pins for the FDIC branch deposits (Summary of Deposits) x OT pre-registration (killed at burn-in; no OOS run).

The five prereg files are verbatim copies of /workspace/research/fdic_sod_ot_prereg/ (recorded 2026-10-09). The design's
oos_authorized stays false and is not the switch; the burn-in noise floor killed the object, so nothing is scored.
"""
import hashlib
import json
from pathlib import Path

import pytest

TRACK = Path(__file__).resolve().parents[1]
ROOT = TRACK.parents[1]
PREREG = TRACK / 'prereg'
SOURCE = Path('/workspace/research/fdic_sod_ot_prereg')
PINS = {
    'PREREG_fdic_sod_ot.md': '2f7f7917e484663ecfc7260345de24e947094b886bdfc7f9ef1ade857aaf988c',
    'fdic_sod_ot_learning.html': 'd1aced8016107f88a81742239fd334ffc0375fb6753aa63c7abe543483fc2ba7',
    'test_design_fdic_sod_ot_v1.json': 'b9c1aef3086b9dc70e00f74fd88890674d2497bd7a58330c36d92be672627db3',
    'GATE_THRESHOLDS_fdic_sod_ot.md': '14018b0c4f44de33f30e276134ddfa42334f64044333db19d5a924ae4f9af4a8',
    'PIN.txt': 'ab4efcd9d6032be439c4585591664fa128db2a1281db9339be1725479c406cc4',
}


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize('name', sorted(PINS))
def test_prereg_file_pinned(name):
    assert _sha(PREREG / name) == PINS[name]


@pytest.mark.parametrize('name', sorted(PINS))
def test_prereg_file_verbatim(name):
    src = SOURCE / name
    if not src.exists():
        pytest.skip('source directory not on this machine')
    assert src.read_bytes() == (PREREG / name).read_bytes()


def test_published_learning_page_is_the_pinned_copy():
    assert _sha(ROOT / 'docs/tracks/fdic-sod-ot/learning.html') == PINS['fdic_sod_ot_learning.html']


def test_design_killed_and_not_authorized():
    d = json.loads((PREREG / 'test_design_fdic_sod_ot_v1.json').read_text(encoding='utf-8'))
    assert d['oos_authorized'] is False and d['status'] == 'KILLED_AT_BURNIN'


def test_track_page_states_the_kill():
    html = (ROOT / 'docs/tracks/fdic-sod-ot/index.html').read_text(encoding='utf-8')
    for s in ('Killed at burn-in', 'negative result', '0.0078208250', '0.0195766804', '9 of 9', '0.0705', 'oos_authorized'):
        assert s in html, s
    assert '<script' not in html and 'http://' not in html and 'stylesheet' not in html


def test_publisher_regenerates_with_no_changes():
    import subprocess, sys
    if not SOURCE.exists():
        pytest.skip('source directory not on this machine')
    out = subprocess.run([sys.executable, str(ROOT / 'scripts/publish_killed_at_burnin.py'),
                          str(ROOT / 'scripts/killed_at_burnin/fdic-sod-ot.json'), '--check'],
                         capture_output=True, text=True)
    assert out.returncode == 0 and out.stdout.strip() == 'no changes', out.stdout + out.stderr
