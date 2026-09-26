import hashlib
import importlib.util
from pathlib import Path
import json
import numpy as np
import pandas as pd
import pytest
from statement_forecast.evaluate import verdict, evaluate_line, run_all, write_outputs
from statement_forecast.paths import DESIGN_PATH, load_design
from y9c.forecast import dm_tests


@pytest.mark.parametrize('eb_mae,p,expected', [(9,.01,'PASS'),(10,.01,'FAIL'),(11,.01,'FAIL'),
                                               (9,.06,'FAIL'),(9,np.nan,'FAIL'),(9,.05,'PASS')])
def test_verdict(spec, eb_mae, p, expected):
    overall = pd.DataFrame({'method':['naive','eb_panel'], 'mae':[10.,eb_mae]})
    dm = pd.DataFrame([dict(scope='full',baseline='naive',loss='abs',p_value=p,t_stat=2.)])
    assert verdict(overall, dm, spec)['verdict'] == expected


def test_fallback_counting_and_fixed_origins(panel, spec):
    damaged = panel.copy()
    damaged.loc[damaged.rssd_id.eq(56) & damaged.report_date.eq('2021-06-30'), 'nii_q'] = np.nan
    cases, _, _, _, parameters, audit = evaluate_line(damaged, 'nii', spec)
    row = cases.loc[cases.rssd_id.eq(56) & cases.quarter.eq(pd.Period('2021Q4'))].iloc[0]
    assert row.eb_fallback and row.eb_panel == row.naive
    assert audit['eb_fallbacks'] == int(cases.eb_fallback.sum()) > 0
    assert sum(a['eb_fallbacks'] for a in audit['origin_audit']) == audit['eb_fallbacks']
    assert parameters.origin.tolist() == pd.period_range('2021Q4','2026Q1',freq='Q').astype(str).tolist()
    assert parameters.iloc[0].N == 49
    assert parameters.iloc[0].n_excluded_incomplete_window == 1
    assert load_design() == spec


def test_missing_final_target_raises(panel, spec):
    with pytest.raises(ValueError, match='2026Q2'):
        evaluate_line(panel.loc[panel.report_date.lt('2026-04-01')], 'nii', spec)


def test_dm_positive_favors_eb():
    cases = pd.DataFrame({'actual':[0.]*6, 'naive':[1.,2.,3.,4.,5.,6.], 'eb_panel':[0.]*6,
                          'target_quarter':pd.period_range('2022Q1',periods=6,freq='Q'),
                          'target_year':[2022]*4+[2023]*2})
    dm = dm_tests(cases, first='naive', second='eb_panel')
    assert dm.favored.eq('eb_panel').all()
    assert dm.t_stat.gt(0).all()
    assert dm.loc[dm.scope.ne('full'), 'inference'].str.startswith('descriptive only').all()


def test_aggregate_outputs_only(panel, spec, tmp_path):
    results = run_all(panel, spec)
    vintage = tmp_path / 'vintage.json'
    vintage.write_text(json.dumps(dict(synthetic=True, first_quarter='2018Q1', last_quarter='2026Q2',
                                       n_quarters=34, build_time_utc='synthetic', downloads={})) + '\n')
    write_outputs(results, tmp_path / 'results', vintage, {'run_start_time_utc':'synthetic start',
                  'prereg_commit':'synthetic', 'prereg_commit_time':'<untrusted timestamp>'})
    tables = tmp_path / 'results/tables'
    expected = {f'{name}.{ext}' for name in ['overall_errors','by_year_errors','dm_tests','eb_parameters']
                for ext in ['csv','json']} | {'verdicts.json','run_metadata.json','test_design.json','vintage.json'}
    assert {p.name for p in tables.iterdir()} == expected
    for path in tables.iterdir():
        assert 'rssd_id' not in path.read_text()
        if path.suffix == '.json':
            assert path.read_bytes().endswith(b'\n')
    assert (tables / 'test_design.json').read_bytes() == DESIGN_PATH.read_bytes()
    assert (tables / 'vintage.json').read_bytes() == vintage.read_bytes()
    meta = json.loads((tables / 'run_metadata.json').read_text())
    assert meta['test_design_sha256'] == hashlib.sha256(DESIGN_PATH.read_bytes()).hexdigest()
    assert len(meta['git_head']) == 40
    assert meta['run_start_time_utc'] == 'synthetic start'
    assert len(meta['fallback_counts']) == 3
    assert len(results['eb_parameters']) == 54
    assert results['headline'].endswith('of 3 lines pass')

    # Render the exact aggregate exports, including escaping of metadata strings.
    path = Path(__file__).resolve().parents[1] / 'scripts/render_results_page.py'
    module_spec = importlib.util.spec_from_file_location('sf_renderer', path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    rendered = module.render(tmp_path / 'results').read_text()
    assert 'of 3 lines pass the pre-registered bar' in rendered
    assert '&lt;untrusted timestamp&gt;' in rendered
    assert '<untrusted timestamp>' not in rendered
    assert 'href="../../../assets/site.css"' in rendered
    assert 'class="active">Statement Forecast</a>' in rendered
    assert 'Descriptive only' in rendered
    assert 'Positive t favors EB' in rendered
    assert 'DM p · absolute error' in rendered
    for line in spec['lines']:
        eb = results['overall_errors'].loc[results['overall_errors'].line.eq(line['key'])]
        assert f"{eb.iloc[0].mae:,.0f}" in rendered
