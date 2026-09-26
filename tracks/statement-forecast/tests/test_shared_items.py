"""The extra flow items must not change legacy coverage/vintage counts."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pandas.testing import assert_frame_equal
from y9c import panel as shared


def test_new_flows_preserve_y9c_metadata(tmp_path, monkeypatch):
    items = yaml.safe_load((Path(__file__).resolve().parents[2] / 'y9c-panel/core_items.yaml').read_text())['core_items']
    raw = tmp_path / 'raw'
    raw.mkdir()
    processed = tmp_path / 'processed'
    original = {code: item for code, item in items.items() if item.get('y9c_core', True)}
    frames = {}
    for quarter, date in enumerate(['2020-03-31', '2020-06-30', '2020-09-30'], 1):
        path = raw / ('BHCF' + date.replace('-', '') + '.zip')
        path.touch()
        frame = pd.DataFrame({'rssd_id':[1,2], 'report_date':pd.to_datetime([date]*2), 'name':['A','B']})
        for code, meta in items.items():
            frame[code] = [quarter * 10., quarter * 20.] if meta['kind'] == 'flow_ytd' else [1000.,2000.]
        if quarter == 1:
            frame.loc[0, 'BHCK4079'] = np.nan
        if quarter == 2:
            frame.loc[1, 'BHCK4093'] = np.nan
        frames[path.name] = frame
    (raw / 'manifest.json').write_text(json.dumps({name:{} for name in frames}))
    monkeypatch.setattr(shared, 'ROOT', tmp_path)
    monkeypatch.setattr(shared, 'RAW', raw)
    monkeypatch.setattr(shared, 'PROCESSED', processed)
    monkeypatch.setattr(shared, 'read_quarter', lambda path, items: frames[path.name].copy())
    monkeypatch.setattr(shared, 'sanity', lambda wide: {})
    monkeypatch.setattr(shared, 'utc', lambda: 'fixed synthetic time')
    config = tmp_path / 'core_items.yaml'
    config.write_text(yaml.safe_dump({'core_items':original}, sort_keys=False))
    shared.main()
    coverage = (processed / 'coverage.csv').read_bytes()
    vintage = (processed / 'vintage.json').read_bytes()
    before = pd.read_parquet(processed / 'panel_wide.parquet')
    config.write_text(yaml.safe_dump({'core_items':items}, sort_keys=False))
    shared.main()
    assert (processed / 'coverage.csv').read_bytes() == coverage
    assert (processed / 'vintage.json').read_bytes() == vintage
    after = pd.read_parquet(processed / 'panel_wide.parquet')
    assert_frame_equal(before, after[before.columns], check_exact=True)
    # The new line really has a missing-prior drop, which the legacy count ignores.
    assert after.loc[after.rssd_id.eq(1) & after.report_date.eq('2020-06-30'), 'noninterest_income_q'].isna().all()
    assert json.loads(vintage)['dropped_missing_prior_any_flow'] == 0
