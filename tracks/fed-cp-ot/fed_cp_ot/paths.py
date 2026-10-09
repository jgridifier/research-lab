from pathlib import Path
TRACK = Path(__file__).resolve().parents[1]
ROOT = TRACK.parents[1]
PREREG_DIR = TRACK / 'prereg'
DATA_DIR = TRACK / 'data'
TRIALS_PATH = TRACK / 'trials.jsonl'
FORWARD_LOG_PATH = DATA_DIR / 'forward_log.jsonl'
SCORING_WALL = '2008-12-26'
BURNIN = ('2001-01-05', SCORING_WALL)
OOS = ('2009-01-02', '2026-10-02')
SEED = 20261009
EXPECTED_TRIALS = 3
SOURCE_URL = 'https://www.federalreserve.gov/releases/cp/data/FRB_CP_xml.zip'
PINNED_RESEARCH_ZIP_SHA256 = '16805f2ce102d5b6703de6393e89f345e9e68e15381ab457fb58f3830cff22d2'
PINNED_CSV_SHA256 = 'aeab7b0941af5e2b492e42dbe4fe05c6752efd6bc9eff3fa9b620b5545596d7a'
