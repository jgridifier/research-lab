"""Byte-for-byte hash checks for the pinned burn-in script and its stdout.

The design pins `compute_cp_ot_burnin.py` (34021c50...) and `compute_cp_ot_burnin.stdout.txt` (17a0b239...).
The hash 17a0b239... belongs to the script's *stdout*, not to the script file.
"""
import argparse
import json
import sys
from .alerts import alert
from .paths import PREREG_DIR
from .preflight import sha256

SCRIPT_NAME, STDOUT_NAME = 'compute_cp_ot_burnin.py', 'compute_cp_ot_burnin.stdout.txt'
SCRIPT_SHA256 = '34021c50bf30efbe2541b119816e8ef98c455ab5819ee232a892ca990ab11857'
STDOUT_SHA256 = '17a0b23936e5b0c56e15a4937830e0f032a55ff20713f45cda7cf2d5adc11e8e'


class HashMismatch(ValueError):
    pass


def check_design_pins(design_path=PREREG_DIR / 'test_design_fed_cp_ot_v1.json'):
    pins = json.loads(design_path.read_text())['file_sha256']
    for name, want in ((SCRIPT_NAME, SCRIPT_SHA256), (STDOUT_NAME, STDOUT_SHA256)):
        if pins.get(name) != want:
            raise HashMismatch(f'design pins {name} as {pins.get(name)}, expected {want}')


def check_file(path, expected):
    got = sha256(path)
    if got != expected:
        raise HashMismatch(f'{path}: sha256 {got} != pinned {expected}')
    return got


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--script', required=True, help='compute_cp_ot_burnin.py as fetched from the release')
    p.add_argument('--stdout', required=True, help='captured stdout of running that script on the pinned zip')
    p.add_argument('--issue', action='store_true')
    args = p.parse_args(argv)
    try:
        check_design_pins()
        check_file(args.script, SCRIPT_SHA256)
        check_file(args.stdout, STDOUT_SHA256)
    except (HashMismatch, OSError) as exc:
        alert('fed-cp-ot: burn-in hash check failed', str(exc), issue=args.issue)
        return 1
    print('burn-in script and stdout hashes match the pins')
    return 0


if __name__ == '__main__':
    sys.exit(main())
