"""Hash pins for the CFPB complaints x OT pre-registration (killed at burn-in; no out-of-sample run).

The three prereg files are verbatim copies of /workspace/research/cfpb_ot_prereg/ (recorded 2026-10-08). The design's
oos_authorized stays false and is not the switch; the burn-in noise floor killed the object, so nothing is scored.
"""
import hashlib
import json
from pathlib import Path

import pytest

TRACK = Path(__file__).resolve().parents[1]
ROOT = TRACK.parents[1]
PREREG = TRACK / 'prereg'
SOURCE = Path('/workspace/research/cfpb_ot_prereg')
PINS = {
    'PREREG_cfpb_complaints_ot.md': 'd3e8ac46de75fdd181a99d3fc3519107ff84d704ae37034390cbf9bd8ac24a46',
    'cfpb_ot_learning.html': '9c5d5dc30264673cefe68df15163a6ddae5b89be63cad752843d37801d9f9061',
    'test_design_cfpb_ot_v1.json': 'a5170147070a25163ed3549403ffe48860c749c4ccb4e0243d20aa6befada584',
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
    assert _sha(ROOT / 'docs/tracks/cfpb-complaints-ot/learning.html') == PINS['cfpb_ot_learning.html']


def test_design_killed_and_not_authorized():
    d = json.loads((PREREG / 'test_design_cfpb_ot_v1.json').read_text(encoding='utf-8'))
    assert d['oos_authorized'] is False and d['status'] == 'KILLED_AT_BURNIN'


def test_track_page_states_the_kill():
    html = (ROOT / 'docs/tracks/cfpb-complaints-ot/index.html').read_text(encoding='utf-8')
    for s in ('Killed at burn-in', 'negative result', '0.0064', '0.0269', 'oos_authorized'):
        assert s in html, s
    assert '<script' not in html and 'http://' not in html and 'stylesheet' not in html


def test_publisher_regenerates_with_no_changes():
    import subprocess, sys
    if not SOURCE.exists():
        pytest.skip('source directory not on this machine')
    out = subprocess.run([sys.executable, str(ROOT / 'scripts/publish_killed_at_burnin.py'),
                          str(ROOT / 'scripts/killed_at_burnin/cfpb-complaints-ot.json'), '--check'],
                         capture_output=True, text=True)
    assert out.returncode == 0 and out.stdout.strip() == 'no changes', out.stdout + out.stderr
