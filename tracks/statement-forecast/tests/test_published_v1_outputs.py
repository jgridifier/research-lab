"""Freeze: v1 Statement Forecast and Y-9C published files stay byte-identical to main@d1fd375.

Covers every file under docs/tracks/statement-forecast/results/ and
docs/tracks/y9c-panel/, the v1 pre-registration test_design.json (pinned
915d8b22...) and the v1 notebook. Digests were taken from
`git show d1fd375:<path> | sha256sum`.
"""
import hashlib
import subprocess

import pytest
from statement_forecast import prereg
from statement_forecast.paths import ROOT

BASE = 'd1fd375'
FROZEN_DIRS = ['docs/tracks/statement-forecast/results', 'docs/tracks/y9c-panel']
EXPECTED = {
    'docs/tracks/statement-forecast/results/figures/eb_parameters.png': '94a5b7087fe930dcbe5c80fd32594106adddb39d961447f1e6c56cb24adca656',
    'docs/tracks/statement-forecast/results/figures/mae_by_line.png': 'd434491ff3429f555e1b697b44ef4032458007834977ccfc016244a086cd63f8',
    'docs/tracks/statement-forecast/results/index.html': 'd9453bcf141c5d0159b38d0fee11c263c93b788a781c127461dc8b3c03020c3d',
    'docs/tracks/statement-forecast/results/tables/by_year_errors.csv': '5f384480a317ec974ab75059efd0bde06555ed46589b56dd5f1991c1e4fba8cb',
    'docs/tracks/statement-forecast/results/tables/by_year_errors.json': '3bb37097c6841bd3934845547c578499bf840420f4fa1c64937b11950328f0e5',
    'docs/tracks/statement-forecast/results/tables/dm_tests.csv': 'bfe8fd99b434303a5f5279612796531cd97172aea72b13d7b71557dedfdd8b1d',
    'docs/tracks/statement-forecast/results/tables/dm_tests.json': '01a27476a0d9464b0347918db9767b49a043a9a4ff72e074602a4bda6f45bf7b',
    'docs/tracks/statement-forecast/results/tables/eb_parameters.csv': 'c24f782a2230455975e8837c5ccb3daa415aeb0e6afdfadba35fb5f612305a4c',
    'docs/tracks/statement-forecast/results/tables/eb_parameters.json': '0dc5974d7546102c69f283c0c7d674fb58a714eba6755a35093e792a51b07873',
    'docs/tracks/statement-forecast/results/tables/overall_errors.csv': '65798cb2d908ca440303dc4d6ac2201e23d532987198b16004dcf2f57d16bbb6',
    'docs/tracks/statement-forecast/results/tables/overall_errors.json': '297705756bb87b4470074f8cbd1a61f582b0795506a80629479274c443f3ff2a',
    'docs/tracks/statement-forecast/results/tables/run_metadata.json': '9b7f02434449ebff0e304c4283f9a524f0c6e29866b90d74271c1253ddff6719',
    'docs/tracks/statement-forecast/results/tables/test_design.json': '915d8b220f9dcbdc844d464f7b98db739cc986fa48f9f14e0ed7b73d01ffa68f',
    'docs/tracks/statement-forecast/results/tables/verdicts.json': '93ce9ec76eefb10f700350c0f90de80376a8527a3f348456b378528915e09826',
    'docs/tracks/statement-forecast/results/tables/vintage.json': '0c2c4da497f4d8e630b7ef4fec126df17304f1b6fdc8b07de52004c142755c82',
    'docs/tracks/y9c-panel/index.html': '93274bc9653fae08240e560c1e20f3604e4c6bd1f2cd78b055dcf99e732da9e4',
    'docs/tracks/y9c-panel/results/figures/aggregate_nii.png': '8fd4b7266626fb8a13864a7601912188017aebeb5b4095102e7d1ae9364c03bd',
    'docs/tracks/y9c-panel/results/figures/annual_mae.png': 'ecefe4ce98aa5c0e99a0b4ddf4ebb1a0d0e788d7061508fe3c9c97731388ef7c',
    'docs/tracks/y9c-panel/results/figures/coverage.png': 'bf357a81f3f150d016ce3c3bdb0d7b14fd49e8c1a98a6f7747c3e0c1de40cabc',
    'docs/tracks/y9c-panel/results/figures/jpm_nii.png': '1a3040fd414ea7f0df878e3e89c65ff255d2b8b03e9839a04f5f70e2a2dd8893',
    'docs/tracks/y9c-panel/results/index.html': 'faaedd807d0bee2bebb71543bdc9f16db14e669cfaf30f03a1aac3088db9c7cc',
    'docs/tracks/y9c-panel/results/tables/by_year_errors.csv': '7325da199bae73eedc72da9a06948b5a5338b2f16edeecbc887b00f5e7db079d',
    'docs/tracks/y9c-panel/results/tables/by_year_errors.json': '8ff7b9b70c9c075d2a8b5371c6245af5a0051e3f90aa0b1c187814953b25b4ca',
    'docs/tracks/y9c-panel/results/tables/dm_tests.csv': '1b1bc30d520eee8df0a72e6460cc6702a2e5dfb0c9d85e14e9a1c1204f4142f4',
    'docs/tracks/y9c-panel/results/tables/dm_tests.json': 'b6050030fdf75551801ddb6b6cd54c78b8abcb699c744218e00b1e57bc854ee5',
    'docs/tracks/y9c-panel/results/tables/overall_errors.csv': '342ae6bbb809daf831ea4bf5ac5084104cd571896bb1eb7cba57193ef2b27a2d',
    'docs/tracks/y9c-panel/results/tables/overall_errors.json': '8584830080f7797fa1f591a318ec981e02cd2cd875504b380d762344f845682d',
    'docs/tracks/y9c-panel/results/tables/test_design.json': '8a52931a8a07d095dc15dff1d1c83e84ac9ef4964cb2a701c8d3ecd44ed692f4',
    'docs/tracks/y9c-panel/results/tables/vintage.json': '5f430aa25da83d1cebbb2919aa3a361f36b5ffdcd8c48fbba9a28de329e7ba80',
    'tracks/statement-forecast/test_design.json': '915d8b220f9dcbdc844d464f7b98db739cc986fa48f9f14e0ed7b73d01ffa68f',
    'tracks/statement-forecast/notebooks/statement_forecast_eb.ipynb': '9c57fcb1667337acc9838184f924456b143d0b6e94d38646461952688c83f305',
}


def digest(relative):
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def test_frozen_files_byte_identical_to_main_d1fd375():
    actual = {str(p.relative_to(ROOT).as_posix()): hashlib.sha256(p.read_bytes()).hexdigest()
              for d in FROZEN_DIRS for p in (ROOT / d).rglob('*') if p.is_file()}
    actual.update({k: digest(k) for k in EXPECTED if not any(k.startswith(d + '/') for d in FROZEN_DIRS)})
    assert actual == EXPECTED, 'v1 / Y-9C published files changed; they must stay byte-identical to main@d1fd375'


def test_v1_preregistration_constants_unchanged():
    assert EXPECTED['tracks/statement-forecast/test_design.json'] == prereg.PREREG_SHA256
    assert prereg.PREREG_SHA256 == '915d8b220f9dcbdc844d464f7b98db739cc986fa48f9f14e0ed7b73d01ffa68f'
    assert prereg.PREREG_COMMIT.startswith('3ea20c8')


def test_frozen_files_match_git_blobs_at_base_when_available():
    if subprocess.run(['git', 'cat-file', '-e', f'{BASE}^{{commit}}'], cwd=ROOT).returncode != 0:
        pytest.skip('base commit not in local history')
    for relative, expected in EXPECTED.items():
        blob = subprocess.run(['git', 'show', f'{BASE}:{relative}'], cwd=ROOT, capture_output=True, check=True).stdout
        assert hashlib.sha256(blob).hexdigest() == expected, relative
