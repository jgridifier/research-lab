"""Aggregate-only exports, provenance, rendered page and the teaching-note copy."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from statement_forecast import combo
from statement_forecast.paths import ROOT

TEACHING = ROOT / 'docs/tracks/statement-forecast/combination-teaching.html'
TEACHING_SHA256 = 'a89bd418ebb23d7d353e9cfc2058b8a74871e89fb36a79969ad8d84caed0768c'


def test_teaching_note_is_the_verbatim_copy():
    assert hashlib.sha256(TEACHING.read_bytes()).hexdigest() == TEACHING_SHA256
    html = TEACHING.read_text(encoding='utf-8')
    assert 'href="results-combination/index.html"' in html


def test_track_index_links_teaching_note_and_results():
    html = (ROOT / 'docs/tracks/statement-forecast/index.html').read_text(encoding='utf-8')
    assert 'href="combination-teaching.html"' in html and 'href="results-combination/index.html"' in html


def load_renderer():
    path = Path(__file__).resolve().parents[1] / 'scripts/render_combo_results_page.py'
    spec = importlib.util.spec_from_file_location('combo_renderer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_aggregate_outputs_and_rendered_page(panel, combo_spec, tmp_path):
    results = combo.run_all(panel, combo_spec)
    with pytest.raises(ValueError, match='expected 893'):
        combo.run_all(panel, combo_spec, expected_cases=893)
    vintage = tmp_path / 'vintage.json'
    vintage.write_text(json.dumps(dict(synthetic=True, first_quarter='2018Q1', last_quarter='2026Q2',
                                       n_quarters=34, build_time_utc='synthetic', downloads={})) + '\n')
    for incomplete in [{}, {'run_start_time_utc': 'x'}, {'git_head': '0' * 40},
                       {'run_start_time_utc': '', 'git_head': '0' * 40}]:
        with pytest.raises(ValueError, match='run_meta must supply'):
            combo.write_outputs(results, tmp_path / 'rejected', vintage, incomplete)
    assert not (tmp_path / 'rejected').exists()
    meta = {'run_start_time_utc': '2026-10-03T16:00:00+00:00', 'git_head': '0' * 40,
            'prereg_commit': '<script>', 'prereg_commit_time': '2026-10-03T11:00:00-04:00'}
    combo.write_outputs(results, tmp_path / 'out', vintage, meta)
    tables = tmp_path / 'out/tables'
    expected = {f'{n}.{e}' for n in combo.TABLES for e in ['csv', 'json']} | {
        'verdicts.json', 'run_metadata.json', 'test_design_combo.json', 'vintage.json'}
    assert {p.name for p in tables.iterdir()} == expected
    for path in tables.iterdir():
        assert 'rssd_id' not in path.read_text(encoding='utf-8')
    assert (tables / 'test_design_combo.json').read_bytes() == combo.COMBO_DESIGN_PATH.read_bytes()
    saved = json.loads((tables / 'run_metadata.json').read_text())
    assert saved['test_design_sha256'] == hashlib.sha256(combo.COMBO_DESIGN_PATH.read_bytes()).hexdigest()
    assert set(saved['fallback_counts']) == {'nii', 'noninterest_income', 'noninterest_expense'}
    assert results['weights'].shape[0] == 54 and results['headline'].endswith('of 3 lines pass')

    figures = tmp_path / 'out/figures'
    figures.mkdir()
    rendered = load_renderer().render(tmp_path / 'out').read_text(encoding='utf-8')
    assert 'of 3 lines pass the pre-registered bar' in rendered
    assert '&lt;script&gt;' in rendered and '<script>' not in rendered
    assert 'href="../../../assets/site.css"' in rendered
    assert 'name="viewport"' in rendered and 'overflow-x:auto' in rendered
    assert 'class="active">Statement Forecast</a>' in rendered
    assert 'href="../combination-teaching.html"' in rendered
    assert '2026-10-03 12:00:00 ET' in rendered  # run start converted to ET
    for disclosure in combo_spec['required_disclosures']:
        assert disclosure in rendered or disclosure.replace("'", '&#x27;') in rendered
    lowered = rendered.lower()
    for banned in ['gold', 'amber', '<img src="logo', 'goldman']:
        assert banned not in lowered
    for v in results['verdicts'].values():
        assert f"{v['combo_mae']:,.0f}" in rendered and f"{v['naive_mae']:,.0f}" in rendered
