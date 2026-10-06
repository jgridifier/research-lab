"""Track locations. Raw NIC ZIPs are the y9c-panel cache (gitignored)."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TRACK = ROOT / 'tracks/y9c-trading-ot'
PACKAGE = TRACK / 'trading_ot'
DESIGN_PATH = TRACK / 'test_design_trading_ot.json'
TRIALS_PATH = TRACK / 'trials.jsonl'
DATA = TRACK / 'data'                      # gitignored: processed panel, FRED cache, per-bank outputs
RESULTS = ROOT / 'docs/tracks/y9c-trading-ot/results'
# Default: the y9c-panel cache (tracks/y9c-panel/data/raw, itself gitignored).
# Override with Y9C_RAW_DIR to point at another copy of the same ZIPs.
RAW_DIR = Path(os.environ.get('Y9C_RAW_DIR', ROOT / 'tracks/y9c-panel/data/raw'))
# v1.1: 2008Q1-2017Q4 backfill ZIPs (Jared's manual NIC download; gitignored) + the 2018+ cache.
RAW_BACKFILL_DIR = Path(os.environ.get('Y9C_RAW_BACKFILL_DIR', ROOT / 'tracks/y9c-panel/data/raw_backfill_2008_2017'))
RAW_DIRS_V1_1 = [RAW_BACKFILL_DIR, RAW_DIR]
DESIGN_PATH_V1_1 = TRACK / 'test_design_trading_ot_v1_1.json'
# Errata to addendum v1.1 (Quant review of PR #10; verbatim copy). Where a stated value conflicts with an
# operative rule of the pinned design, the rule governs. No new design pin.
ERRATA_PATH = TRACK / 'prereg' / 'ERRATA_v1_1.md'
ERRATA_SOURCE = '/workspace/research/y9c_ot_prereg/ERRATA_v1_1.md'
ERRATA_SHA256 = '68d5128fa3da40d269340afda3862ee89374bd6df59ad108c9e84d8698a17fe9'
ERRATA_1B_PATH = TRACK / 'prereg' / 'ERRATA_v1_1b.md'
ERRATA_1B_SOURCE = '/workspace/research/y9c_ot_prereg/ERRATA_v1_1b.md'
ERRATA_1B_SHA256 = '2f134632acf4120ba410e7e2eacb352895eb41d9fbe9207cd0ddc6d22fef21bf'


def load_design(path=DESIGN_PATH):
    return json.loads(Path(path).read_text(encoding='utf-8'))
