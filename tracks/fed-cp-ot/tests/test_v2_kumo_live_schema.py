"""B3: committed live NIM regression response parses with the harness schema."""
import json
from pathlib import Path
import pandas as pd
import pytest
from fed_cp_ot import kumo, kumo_smoke

FIXTURE = Path(__file__).resolve().parents[1] / 'artifacts' / 'kumo_burnin_smoke_v2_live.json'


def test_live_fixture_metadata_is_burnin_only_with_endpoint_and_date():
    evidence = json.loads(FIXTURE.read_text())
    assert evidence['endpoint'] == kumo.URL
    assert evidence['status'] == 200 and evidence['parser_verified'] is True
    assert evidence['recorded_utc'] and evidence['recorded_date_america_new_york']
    origin = kumo_smoke.burnin_origin(evidence['target'])
    assert evidence['origin'] == str(origin.date())
    assert evidence['input_max_date'] <= evidence['origin']
    # Request never looks past the burn-in origin.
    payload = evidence['request']
    for section in ('context', 'predict'):
        for row in payload[section]['instance_table']['rows']:
            assert pd.Timestamp(row[2]).tz_localize(None) <= origin
        for row in payload[section]['related_tables']['weekly_facts']['rows']:
            assert pd.Timestamp(row[3]).tz_localize(None) <= origin
    assert 'instance_id' in payload['schema']['related_tables']['entities']['columns']
    assert payload['context']['related_tables']['entities']['columns'][0] == 'instance_id'


def test_live_fixture_parses_with_harness_schema_parser():
    evidence = json.loads(FIXTURE.read_text())
    n = evidence['n_entities']
    values = kumo.KumoClient._parse(json.dumps(evidence['response']), n=n)
    assert values.shape == (n,) and values.tolist() == pytest.approx(evidence['predictions'])
    assert evidence['finite_prediction_count'] == n
