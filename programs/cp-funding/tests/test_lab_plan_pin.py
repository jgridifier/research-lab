"""Pin for Quant's CP funding lab plan (2026-10-09): verbatim copy of /workspace/research/lab/LAB_PLAN_cp_funding_2026-10-09.md."""
import hashlib
from pathlib import Path

import pytest

PROG = Path(__file__).resolve().parents[1]
ROOT = PROG.parents[1]
NAME = 'LAB_PLAN_cp_funding_2026-10-09.md'
SHA = 'd78c176ef63adeef012f0dcda5768cdd371490918cded1c618f7d47ce091d2d9'
SOURCE = Path('/workspace/research/lab') / NAME


def test_plan_pinned():
    assert hashlib.sha256((PROG / NAME).read_bytes()).hexdigest() == SHA


def test_plan_verbatim():
    if not SOURCE.exists():
        pytest.skip('source not on this machine')
    assert SOURCE.read_bytes() == (PROG / NAME).read_bytes()


def test_rendered_page_names_the_pin():
    page = (ROOT / 'docs/programs/cp-funding/plan.html').read_text(encoding='utf-8')
    assert SHA in page and 'Milestones' in page and 'Jared approves the run' in page
    assert '<script' not in page and 'stylesheet' not in page and 'http' not in page
