"""Shared data location and track-specific aggregate output paths."""
import json
from pathlib import Path

from y9c.panel import PROCESSED

ROOT = Path(__file__).resolve().parents[3]
TRACK = ROOT / 'tracks/statement-forecast'
DESIGN_PATH = TRACK / 'test_design.json'
RESULTS = ROOT / 'docs/tracks/statement-forecast/results'
PANEL_PATH = PROCESSED / 'panel_wide.parquet'


def load_design():
    return json.loads(DESIGN_PATH.read_text())
