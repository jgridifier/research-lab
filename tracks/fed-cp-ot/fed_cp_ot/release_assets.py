"""Raw zips live as GitHub release assets (never committed). Missing assets are a hard, alerting failure."""
from pathlib import Path
import subprocess

VINTAGE_TAG = 'fed-cp-ot-vintages'
PINNED_TAG = 'fed-cp-ot-pinned'


class MissingAssetError(FileNotFoundError):
    pass


def download_asset(tag, name, dest_dir, runner=subprocess.run):
    dest_dir = Path(dest_dir); dest_dir.mkdir(parents=True, exist_ok=True)
    result = runner(['gh', 'release', 'download', tag, '--pattern', name, '--dir', str(dest_dir), '--clobber'],
                    capture_output=True, text=True)
    path = dest_dir / name
    if result.returncode != 0 or not path.is_file():
        raise MissingAssetError(f'release asset {name!r} missing from release {tag!r}: '
                                f'{(result.stderr or "").strip()}')
    return path


def upload_asset(tag, path, runner=subprocess.run):
    path = Path(path)
    if runner(['gh', 'release', 'view', tag], capture_output=True, text=True).returncode != 0:
        runner(['gh', 'release', 'create', tag, '--title', tag, '--notes',
                'Raw Fed CP zip vintages; not committed to git.'], check=True)
    runner(['gh', 'release', 'upload', tag, str(path), '--clobber'], check=True)
    return path.name
