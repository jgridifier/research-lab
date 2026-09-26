import json
import os
import subprocess

import pandas as pd
from pandas.testing import assert_frame_equal
import pytest
from y9c import forecast as y9c
from statement_forecast.evaluate import evaluate_line
from statement_forecast.paths import ROOT, PANEL_PATH

# Last main commit before the shared-baseline refactor (Y-9C PR #3 merge).
PRE_REFACTOR = 'b8925c198081168e5c5ee8c26b55a2264fe7d368'


@pytest.mark.parametrize('line', ['nii', 'noninterest_income', 'noninterest_expense'])
def test_imported_baselines_and_nii_evaluate_parity(panel, spec, line):
    result = evaluate_line(panel, line, spec)[0]
    column = next(item['column'] for item in spec['lines'] if item['key'] == line)
    origins = pd.period_range('2021Q4', '2026Q1', freq='Q')
    direct, _ = y9c.baseline_forecasts(y9c.design(panel, column), origins, column)
    assert_frame_equal(result[direct.columns], direct, check_exact=True)
    if line == 'nii':
        legacy = y9c.evaluate(panel)[0]
        assert_frame_equal(result[legacy.columns], legacy, check_exact=True)
        # Also exercise the pre-refactor code from main (PR #3 merge) on synthetic inputs.
        namespace = {}
        exec(subprocess.check_output(['git', 'show', f'{PRE_REFACTOR}:tracks/y9c-panel/y9c/forecast.py'], cwd=ROOT), namespace)
        old = namespace['evaluate'](panel)
        new = y9c.evaluate(panel)
        for a, b in zip(old[:3], new[:3], strict=True):
            assert_frame_equal(a, b, check_exact=True)
        assert json.dumps(old[3], indent=2) == json.dumps(new[3], indent=2)
        assert_frame_equal(namespace['dm_tests'](old[0]), y9c.dm_tests(new[0]), check_exact=True)


@pytest.mark.skipif(os.environ.get('SF_RUN_REAL_PARITY') != '1',
                    reason='Real data parity is opt-in; default CI never inspects processed data')
def test_real_data_published_serialization(tmp_path):
    # The existence check is deliberately inside this opt-in test: even stat is
    # avoided during synthetic-only work. Requires explicit real-data permission.
    if not PANEL_PATH.exists():
        pytest.skip('Shared panel is absent')
    cases, overall, annual, summary = y9c.evaluate(pd.read_parquet(PANEL_PATH))
    for name, frame in [('overall_errors', overall), ('by_year_errors', annual)]:
        (tmp_path / f'{name}.csv').write_text(frame.to_csv(index=False))
        (tmp_path / f'{name}.json').write_text(frame.to_json(orient='records', indent=2) + '\n')
    (tmp_path / 'test_design.json').write_text(json.dumps(summary, indent=2) + '\n')
    dm = y9c.dm_tests(cases)
    (tmp_path / 'dm_tests.csv').write_text(dm.to_csv(index=False))
    (tmp_path / 'dm_tests.json').write_text(json.dumps(dm.to_dict(orient='records'), indent=2) + '\n')
    for path in tmp_path.iterdir():
        committed = subprocess.check_output(['git', 'show', f'HEAD:docs/tracks/y9c-panel/results/tables/{path.name}'], cwd=ROOT)
        assert path.read_bytes() == committed
