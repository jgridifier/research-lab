"""Dry run on the real pinned zip: burn-in only. Needs the zip (realdata); takes a few minutes."""
import json
import pandas as pd
import pytest
from fed_cp_ot import harness
from fed_cp_ot.paths import SCORING_WALL

pytestmark = pytest.mark.realdata

def test_dry_run_burnin_end_to_end_on_burnin_targets_only(real_zip, tmp_path):
    result = harness.dry_run_burnin(real_zip, tmp_path)
    assert result['max_target'] <= SCORING_WALL and result['label'].startswith('DRY RUN')
    fc = [json.loads(s) for s in (tmp_path / 'forecasts.jsonl').read_text().splitlines()]
    assert len(fc) > 1000 and max(r['target'] for r in fc) <= SCORING_WALL and max(r['input_max_date'] for r in fc) <= SCORING_WALL
    assert all(r['incomplete'] for r in result['families'].values())           # <800 paired weeks in the burn-in
    assert result['kumo_payload_smoke']['fact_rows'] == 3744 and result['kumo_payload_smoke']['live_call'] is False
    assert (tmp_path / 'sel_schedule.json').exists() and (tmp_path / 'bstar_schedule.json').exists()
    sel = json.loads((tmp_path / 'sel_schedule.json').read_text())
    assert sel and all(r['n_weeks'] <= 156 and r['window_last_week'] <= r['origin'] for r in sel)
    assert not (tmp_path / 'oos_result.json').exists() and not harness.RESULT_PATH.exists() and not harness.LOCK_PATH.exists()
