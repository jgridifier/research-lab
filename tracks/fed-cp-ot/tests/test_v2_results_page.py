"""T8: result schema and the Pages results page."""
import json
import subprocess
import sys
from pathlib import Path
import pytest
from fed_cp_ot import harness

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / 'scripts/render_fed_cp_results.py'

def run(*args):
    return subprocess.run([sys.executable, '-I', str(SCRIPT), *args], capture_output=True, text=True)

def test_committed_page_is_the_no_result_placeholder_and_regenerates():
    assert not harness.RESULT_PATH.exists()
    out = run('--check')
    assert out.returncode == 0 and out.stdout.strip() == 'no changes', out.stdout + out.stderr
    assert 'No out-of-sample result exists' in (ROOT / 'docs/tracks/fed-cp-ot/results.html').read_text()

def test_page_renders_a_result_with_wording_and_flags(tmp_path):
    fam = {'family': 'A', 'G': 0.01, 'G_s': {'2009-2014': 0.1, '2015-2020': None, '2021-2026': -0.2}, 'p': None, 'n_pairs': 700,
           'phi': None, 'incomplete': True, 'incomplete_reason': 'n_pairs 700 < 800', 'claim': False,
           'wording': 'underpowered to detect a 5% gain (planning power ≈0.50); not evidence of no gain.'}
    res = {'label': 'OOS <b>result</b>', 'lock_sha256': 'a' * 64, 'manifest': {'zip_sha256': 'b' * 64}, 'families': {'WAR vs B*': fam},
           'family_K': {'failed_origins': 0, 'origins': 927, 'incomplete': False},
           'disclosures': {'revised_pre_wall_values_across_archived_vintages': 3, 'faa_gt80_floored_input_share_fraction': 0.0048, 'pseudo_real_time': 'x'}}
    (tmp_path / 'r.json').write_text(json.dumps(res))
    out = run('--result', str(tmp_path / 'r.json'), '--out', str(tmp_path / 'p.html'))
    assert out.returncode == 0
    page = (tmp_path / 'p.html').read_text()
    assert 'not evidence of no gain' in page and 'INCOMPLETE: n_pairs 700 &lt; 800' in page and '&lt;b&gt;result' in page and '<b>result' not in page

def test_result_json_schema_keys_come_from_finalize(tmp_path):
    """oos_result.json is written from finalize(): every test carries G, G_s, p, n_pairs, phi, the INCOMPLETE flag, family and claim."""
    from fed_cp_ot.scoring import score_all
    out = score_all({})
    assert len(out['families']) == 5
    for r in out['families'].values():
        assert {'G', 'G_s', 'p', 'n_pairs', 'phi', 'incomplete', 'incomplete_reason', 'family', 'claim', 'holm_reject', 'hurdles'} <= set(r)
    assert out['families']['WAR vs B*']['wording'].startswith('underpowered')
