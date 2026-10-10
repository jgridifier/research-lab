"""Hash pins for the Fed CP maturity mix x OT pre-registration (passed burn-in, pinned, awaiting Jared's approval).

The seven prereg files are verbatim copies of /workspace/research/fed_cp_ot_prereg/ (recorded 2026-10-09). The design's
oos_authorized stays false; it is a record, not the switch. Out-of-sample scoring needs a separate approval file.
Prereg files, tests and docs only: the pipeline code lives on branch fed-cp-ot-pipeline, not here.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

TRACK = Path(__file__).resolve().parents[1]
ROOT = TRACK.parents[1]
PREREG = TRACK / 'prereg'
# Original research copies; set FED_CP_OT_PREREG_SOURCE to compare against them. Defaults to the vendored pins.
SOURCE = Path(os.environ.get('FED_CP_OT_PREREG_SOURCE') or PREREG)
DOCS = ROOT / 'docs/tracks/fed-cp-ot'
LABEL = "Passed burn-in, pinned, awaiting Jared's approval"
PINS = {
    'PIN.txt': '65032235646fb984f2b0a0b66f100b5257b239f4e66ac7c4a9f2f079aab419da',
    'test_design_fed_cp_ot_v1.json': '6c87f7ab5efe3a220cb1c50497e3a9edd7435de5965aff4a20f8f6f1b2ce7793',
    'PREREG_fed_cp_ot.md': 'e3da87af2da1002b0635959d751dad4b885c59c985edc3b3a23612fa5bee0ecf',
    'fed_cp_ot_learning.html': '44e77a0c51476724947386a4fc9686af9caea4ccba9c37ae4ad61f50374f5fc7',
    'GATE_THRESHOLDS_fed_cp_ot.md': 'c15eb60cbe1467090fcc920b8f4e311dd14f7b3bbfd0437e21809355721a6c8a',
    'DATA_SPEC_for_app.md': '9c50a16e994cdb04e2598b270800e2941d027e314b375e33cbf5caa98f102c6c',
    'ENGINEERING_TICKET.md': '088d9f2e72a162daf25436b2c76c3b4cfe6b93abd0082d480b5f94befa86346d',
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


def test_track_layout():
    """The pipeline now lives with the pinned prereg; ignore local data/cache artifacts."""
    files = {p.relative_to(TRACK).as_posix() for p in TRACK.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.relative_to(TRACK).parts[0] not in {'data', '.pytest_cache'}}
    assert {f for f in files if f.startswith('prereg/')} == {f'prereg/{n}' for n in PINS}
    assert all(f.startswith(('prereg/', 'tests/')) or f in {'README.md', 'pytest.ini', 'requirements.txt', 'EXPOSURE_LOG_addendum.md'} or (Path(f).parent.as_posix() == 'fed_cp_ot' and f.endswith('.py')) for f in files), files
    assert not any(f.endswith('.py') and not f.startswith(('tests/', 'fed_cp_ot/')) for f in files)


def test_pin_txt_names_design_prereg_and_learning_page():
    pin = (PREREG / 'PIN.txt').read_text(encoding='utf-8')
    for key, name in [('design_sha256', 'test_design_fed_cp_ot_v1.json'),
                      ('prereg_sha256', 'PREREG_fed_cp_ot.md'), ('html_sha256', 'fed_cp_ot_learning.html')]:
        assert f'{key}={PINS[name]}' in pin


def test_design_passed_burnin_and_not_authorized():
    d = json.loads((PREREG / 'test_design_fed_cp_ot_v1.json').read_text(encoding='utf-8'))
    assert d['oos_authorized'] is False and d['status'] == 'BURNIN_PASSED'
    for name in ('GATE_THRESHOLDS_fed_cp_ot.md', 'DATA_SPEC_for_app.md', 'ENGINEERING_TICKET.md'):
        assert d['file_sha256'][name] == PINS[name]


def test_no_approval_file_in_repo():
    assert not list(ROOT.glob('**/APPROVAL_fed_cp_ot*'))


def test_published_learning_page_is_the_pinned_copy():
    assert _sha(DOCS / 'learning.html') == PINS['fed_cp_ot_learning.html']


def test_prereg_page_label_and_hashes():
    page = (DOCS / 'index.html').read_text(encoding='utf-8')
    assert LABEL in page
    for sha in PINS.values():
        assert sha in page
    assert '<script' not in page and 'stylesheet' not in page and 'http' not in page


def test_index_cp_card_links_both_pages():
    idx = (ROOT / 'docs/index.html').read_text(encoding='utf-8')
    card = idx[idx.index('<p class="section-heading">Programs</p>'):idx.index('<p class="section-heading">Learning guides</p>')]
    for href in ('programs/cp-funding/plan.html', 'tracks/fed-cp-ot/index.html', 'tracks/fed-cp-ot/learning.html'):
        assert f'href="{href}"' in card


def test_pages_regenerate_with_no_changes():
    out = subprocess.run(['sh', str(ROOT / 'scripts/render_cp_pages.sh'), '--check'], capture_output=True, text=True)
    assert out.returncode == 0 and out.stdout.split() == ['no', 'changes', 'no', 'changes'], out.stdout + out.stderr
