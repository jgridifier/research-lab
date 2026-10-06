"""Entry point. Verifies the pinned pre-registration first; the OOS stage is gated.

Stages:
  panel  - parse the cached NIC ZIPs (complete quarters only) and write data/processed/ (gitignored)
  oos    - frozen burn-in decisions + walk-forward OOS scoring + gate; REFUSES to run unless the
           pinned design has oos_authorized = true and every open question is resolved.
Every OOS execution (any model/config scored on 2022Q1+ targets) is appended to trials.jsonl
with config hash, timestamp and git head *before* scoring starts, so aborted runs still count.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import subprocess
import sys

from .paths import DATA, DESIGN_PATH, RAW_DIR, ROOT, TRIALS_PATH, load_design


class OOSNotAuthorized(RuntimeError):
    pass


def assert_oos_authorized(design):
    """Stop-gate: no OOS scoring until the design authorizes it and has no unresolved questions."""
    if not design.get('oos_authorized', False):
        raise OOSNotAuthorized('OOS scoring is not authorized by the pinned design (oos_authorized=false; '
                               'prereg addendum v1.1 pending). Nothing was scored.')
    open_q = [q['id'] for q in design.get('open_questions', []) if q.get('resolution') in (None, '')]
    if open_q:
        raise OOSNotAuthorized(f'Unresolved pre-registration questions: {open_q}. Nothing was scored.')


def git_head():
    return subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def config_hash(config):
    return hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest()


def log_trial(config, label, registered=True, path=TRIALS_PATH):
    """Append one trial record (JSON line). Non-registered configs are labelled EXPLORATORY."""
    record = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), git_head=git_head(),
                  config_hash=config_hash(config), label=label,
                  status='registered' if registered else 'EXPLORATORY', config=config)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, sort_keys=True, default=str) + '\n')
    return record


def trial_count(path=TRIALS_PATH):
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding='utf-8').splitlines() if line.strip())


def stage_panel(as_of):
    from .panel import build_trading_panel
    _, vintage = build_trading_panel(RAW_DIR, as_of, DATA / 'processed')
    return vintage


def stage_oos(design):
    assert_oos_authorized(design)
    raise NotImplementedError('OOS orchestration is completed only after prereg v1.1 fixes the primary run')


def main(argv=None):
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['panel', 'oos'])
    parser.add_argument('--as-of', default='2026-10-06')
    args = parser.parse_args(argv)
    from statement_forecast.prereg import verify_trading_ot_preregistration
    provenance = verify_trading_ot_preregistration()
    design = load_design(DESIGN_PATH)
    if args.stage == 'panel':
        vintage = stage_panel(args.as_of)
        print(json.dumps(dict(provenance=provenance, last_complete_quarter=vintage['last_complete_quarter'],
                              n_quarters=vintage['n_quarters']), indent=2))
        return 0
    stage_oos(design)
    return 0


if __name__ == '__main__':
    sys.exit(main())
