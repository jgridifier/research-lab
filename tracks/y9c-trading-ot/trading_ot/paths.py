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


def load_design(path=DESIGN_PATH):
    return json.loads(Path(path).read_text(encoding='utf-8'))
