"""T7 / PREREG v2 6: rerun the pinned burn-in script (seed 20261009) on the pinned zip; stdout must hash to 17a0b239...

The script is vendored byte-identical (sha pinned below); only its hard-coded HERE line is redirected, which the stdout never prints.
Skipped with a reason when the pinned zip is not available. The OOS run is not allowed until this has passed once on main."""
import hashlib
import os
import subprocess
import sys
from pathlib import Path
import pytest

PINNED = Path(__file__).resolve().parent / 'pinned'
SCRIPT_SHA = '34021c50bf30efbe2541b119816e8ef98c455ab5819ee232a892ca990ab11857'
STDOUT_SHA = '17a0b23936e5b0c56e15a4937830e0f032a55ff20713f45cda7cf2d5adc11e8e'
HERE_LINE = 'HERE = Path("/workspace/research/fed_cp_ot_prereg"); RAW = HERE / "raw"'

def sha(b): return hashlib.sha256(b).hexdigest()

def test_vendored_script_and_stdout_are_the_pinned_files():
    assert sha((PINNED / 'compute_cp_ot_burnin.py').read_bytes()) == SCRIPT_SHA
    assert sha((PINNED / 'compute_cp_ot_burnin.stdout.txt').read_bytes()) == STDOUT_SHA

@pytest.mark.realdata
def test_burnin_stdout_replicates_byte_for_byte(real_zip, tmp_path):
    import numpy, pandas
    if (numpy.__version__, pandas.__version__) != ('2.5.3', '3.0.6'):
        pytest.skip(f'stdout prints library versions; needs numpy 2.5.3 / pandas 3.0.6, have {numpy.__version__} / {pandas.__version__}')
    track = Path(__file__).resolve().parents[1]
    here = tmp_path / 'here'; (here / 'raw').mkdir(parents=True)
    (here / 'GATE_THRESHOLDS_fed_cp_ot.md').write_bytes((track / 'prereg' / 'GATE_THRESHOLDS_fed_cp_ot.md').read_bytes())
    (here / 'raw' / 'FRB_CP_xml.zip').symlink_to(real_zip)
    src = (PINNED / 'compute_cp_ot_burnin.py').read_text()
    assert HERE_LINE in src
    script = tmp_path / 'run' / 'compute_cp_ot_burnin.py'; script.parent.mkdir()
    script.write_text(src.replace(HERE_LINE, f'HERE = Path({str(here)!r}); RAW = HERE / "raw"'))
    out = subprocess.run([sys.executable, '-I', str(script)], capture_output=True, cwd=script.parent, timeout=1800, env={'PATH': os.environ.get('PATH', ''), 'OMP_NUM_THREADS': '1'})
    assert out.returncode == 0, out.stderr.decode()[-2000:]
    assert out.stdout == (PINNED / 'compute_cp_ot_burnin.stdout.txt').read_bytes()
    assert sha(out.stdout) == STDOUT_SHA
