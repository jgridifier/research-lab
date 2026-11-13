"""Fetch and verify the pinned burn-in inputs where the pinned script expects them.

compute_cp_ot_burnin.py (never edited) hardcodes HERE=/workspace/research/fed_cp_ot_prereg and RAW=HERE/raw,
so CI recreates that tree rather than redirecting the script.
"""
import argparse
import sys
from pathlib import Path
from .alerts import alert
from .burnin_hash import SCRIPT_NAME, SCRIPT_SHA256
from .paths import PINNED_RESEARCH_ZIP_SHA256, PINNED_CSV_SHA256
from .preflight import sha256
from .release_assets import PINNED_TAG, MissingAssetError, download_asset

PINNED_HERE = Path('/workspace/research/fed_cp_ot_prereg')
ZIP_NAME, CSV_NAME = 'FRB_CP_xml.zip', 'fed_cp_volume_stats_by_maturity.csv'
# (asset name, destination subdirectory of HERE, pinned sha256)
ASSETS = ((ZIP_NAME, 'raw', PINNED_RESEARCH_ZIP_SHA256),
          (CSV_NAME, 'raw', PINNED_CSV_SHA256),
          (SCRIPT_NAME, '', SCRIPT_SHA256))


class PinnedAssetMismatch(ValueError):
    pass


def fetch_and_verify(here=PINNED_HERE, tag=PINNED_TAG, download=download_asset):
    for name, sub, want in ASSETS:
        path = download(tag, name, Path(here) / sub if sub else Path(here))
        got = sha256(path)
        if got != want:
            raise PinnedAssetMismatch(f'{name}: sha256 {got} != pinned {want}')


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--issue', action='store_true')
    args = p.parse_args(argv)
    try:
        fetch_and_verify()
    except (MissingAssetError, PinnedAssetMismatch, OSError) as exc:
        alert('fed-cp-ot: pinned burn-in input missing or mismatched', str(exc), issue=args.issue)
        return 1
    print(f'pinned inputs verified under {PINNED_HERE}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
