"""Steps of the daily-ingest workflow: gate, verify, fetch, validate, diff, build, upload.

Each subcommand fails hard with an ::error annotation; with --issue it also opens/updates a GitHub issue.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
from . import vintages
from .alerts import alert
from .errors import ProvenanceError, ValidationError
from .gate import decide, write_github_output
from .ingest import fetch_vintage
from .manifest_chain import ChainError, read_rows, verify_chain
from .paths import DATA_DIR
from .release_assets import MissingAssetError, VINTAGE_TAG, download_asset, upload_asset

MANIFEST = DATA_DIR / 'manifest.jsonl'
DIFFS = DATA_DIR / 'vintage_diffs.jsonl'
ALERTING = (ChainError, MissingAssetError, ValidationError, ProvenanceError)


def _zip_path(row, data_dir):
    return Path(data_dir) / row['path']


def _load_walled(zip_path):
    from .parse import load_vol
    from .preflight import preflight
    frame, _ = load_vol(preflight('burnin'), zip_path)  # burn-in provenance: wall_guard applies
    return frame


def previous_distinct(rows):
    """(previous, current) manifest rows, where previous is the newest earlier row with a different sha256."""
    if not rows:
        raise FileNotFoundError('empty manifest')
    cur = rows[-1]
    prev = next((r for r in reversed(rows[:-1]) if r['sha256'] != cur['sha256']), None)
    return prev, cur


def step_gate(now=None, manifest=MANIFEST):
    if manifest.exists():
        verify_chain(manifest)
    run, reason = decide(now or datetime.now(timezone.utc), read_rows(manifest))
    print(f'run={run}: {reason}')
    write_github_output(run, reason)


def step_fetch(data_dir=DATA_DIR):
    verify_chain(Path(data_dir) / 'manifest.jsonl')
    row = fetch_vintage(data_dir)
    print(f"vintage {row['sha256']} fetched {row['fetched_at_utc']} Last-Modified {row['last_modified']}")


def step_validate(data_dir=DATA_DIR):
    rows = read_rows(Path(data_dir) / 'manifest.jsonl')
    verify_chain(Path(data_dir) / 'manifest.jsonl')
    frame = _load_walled(_zip_path(rows[-1], data_dir))
    print(f'schema ok: {len(frame)} rows, latest vintage {rows[-1]["sha256"]}')


def step_diff(data_dir=DATA_DIR, download=download_asset):
    data_dir = Path(data_dir)
    rows = read_rows(data_dir / 'manifest.jsonl')
    prev, cur = previous_distinct(rows)
    if rows[-1].get('unchanged_from_previous'):
        print('vintage unchanged from previous: no diff recorded')
        return None
    if prev is None:
        print('no earlier distinct vintage: nothing to diff')
        return None
    prev_zip = _zip_path(prev, data_dir)
    if not prev_zip.exists():
        download(VINTAGE_TAG, Path(prev['path']).name, prev_zip.parent)
    diff = vintages.diff_vintages(_load_walled(prev_zip), _load_walled(_zip_path(cur, data_dir)))
    diff.update(prev_sha256=prev['sha256'], cur_sha256=cur['sha256'], cur_fetched_at_utc=cur['fetched_at_utc'])
    vintages.append_diff(diff, data_dir / 'vintage_diffs.jsonl')
    print(f"diff recorded: {len(diff['value_changes'])} burn-in value changes")
    return diff


def step_upload(data_dir=DATA_DIR):
    row = read_rows(Path(data_dir) / 'manifest.jsonl')[-1]
    print('uploaded', upload_asset(VINTAGE_TAG, _zip_path(row, data_dir)))


def step_build_app(data_dir=DATA_DIR):
    from .app import build_app
    row = read_rows(Path(data_dir) / 'manifest.jsonl')[-1]
    print(build_app(zip_path=_zip_path(row, data_dir)))


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('step', choices=['gate', 'fetch', 'validate', 'diff', 'upload', 'build-app', 'verify'])
    p.add_argument('--issue', action='store_true', help='open/update a GitHub issue on alerting failures')
    args = p.parse_args(argv)
    steps = {'gate': step_gate, 'fetch': step_fetch, 'validate': step_validate, 'diff': step_diff,
             'upload': step_upload, 'build-app': step_build_app, 'verify': lambda: verify_chain(MANIFEST)}
    try:
        steps[args.step]()
    except Exception as exc:
        alert(f'fed-cp-ot daily: {args.step} failed', f'{type(exc).__name__}: {exc}',
              issue=args.issue and isinstance(exc, ALERTING))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
