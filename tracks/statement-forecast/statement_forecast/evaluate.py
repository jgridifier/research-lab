"""Fixed-window, matched-case evaluation; export aggregate results only."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
import pandas as pd
from y9c import forecast as y9c

from .eb import eb_forecast_origin
from .paths import DESIGN_PATH, ROOT, load_design

LINES = load_design()['lines']
METHODS = y9c.METHODS


def evaluate_line(panel, line, design_json):
    """Return cases, overall, by-year, DM, parameters, and aggregate audit."""
    if isinstance(line, str):
        line = next(item for item in design_json['lines'] if item['key'] == line)
    column = line['column']
    data = y9c.design(panel, column)
    window = design_json['test_window']
    if pd.Period(window['last_target'], freq='Q') not in set(data.quarter):
        raise ValueError(f"Panel lacks required last target {window['last_target']}")
    origins = pd.period_range(window['first_origin'], window['last_origin'], freq='Q')
    forecasts, audit = y9c.baseline_forecasts(data, origins, column)
    predictions, parameters = [], []
    for origin, origin_audit in zip(origins, audit, strict=True):
        universe = data.loc[data.selected & data.quarter.eq(origin), 'rssd_id']
        eb, params = eb_forecast_origin(panel, origin, universe, column, T=design_json['method']['window_T'])
        cases = forecasts.loc[forecasts.quarter.eq(origin)].merge(
            eb[['rssd_id', 'eb_panel']], on='rssd_id', how='left', validate='one_to_one', indicator=True)
        # Missing prediction means incomplete window; numerical failures already raise.
        cases['eb_fallback'] = cases['_merge'].eq('left_only')
        cases.loc[cases.eb_fallback, 'eb_panel'] = cases.loc[cases.eb_fallback, 'naive']
        cases = cases.drop(columns='_merge')
        if not np.isfinite(cases[[*METHODS, 'eb_panel', 'actual']].to_numpy()).all():
            raise ValueError(f'{origin}: nonfinite forecast; no clipping or silent case removal')
        origin_audit['eb_fallbacks'] = int(cases.eb_fallback.sum())
        predictions.append(cases)
        parameters.append(dict(line=line['key'], origin=str(origin), **params))
    forecasts = pd.concat(predictions, ignore_index=True)
    forecasts['target_year'] = forecasts.target_quarter.dt.year
    methods = [*METHODS, 'eb_panel']
    overall = y9c.metrics(forecasts, methods=methods).assign(line=line['key'])
    by_year = pd.concat([y9c.metrics(group, methods=methods).assign(target_year=int(year), line=line['key'])
                         for year, group in forecasts.groupby('target_year')], ignore_index=True)
    dm = pd.concat([y9c.dm_tests(forecasts, first=b, second='eb_panel').assign(line=line['key'], baseline=b)
                    for b in METHODS], ignore_index=True)
    summary = dict(n_forecasts_per_method=len(forecasts), n_target_quarters=len(origins),
                   **{key: sum(a[key] for a in audit) for key in
                      ['selected', 'dropped_target_missing', 'dropped_history', 'ar_fallbacks', 'eb_fallbacks']},
                   origin_audit=audit)
    return forecasts, overall, by_year, dm, pd.DataFrame(parameters), summary


def verdict(overall, dm, design_json):
    """Strict MAE improvement and inclusive pre-registered two-sided p threshold."""
    comparator = design_json['pass_bar']['comparator']
    scores = overall.set_index('method')
    eb_mae, naive_mae = float(scores.loc['eb_panel', 'mae']), float(scores.loc[comparator, 'mae'])
    row = dm.loc[dm.scope.eq('full') & dm.baseline.eq(comparator) & dm.loss.eq('abs')]
    if len(row) != 1:
        raise ValueError('Expected one full-sample absolute-error DM comparison')
    p = float(row.iloc[0].p_value)
    alpha = design_json['pass_bar']['alpha']
    passed = bool(eb_mae < naive_mae and np.isfinite(p) and p <= alpha)
    return dict(verdict='PASS' if passed else 'FAIL', passed=passed, eb_mae=eb_mae,
                naive_mae=naive_mae, p_value=p, alpha=alpha,
                t_stat=float(row.iloc[0].t_stat), comparator=comparator, loss='abs')


def run_all(panel, design_json):
    """Discard per-bank cases after scoring; retain only aggregate tables."""
    tables = {key: [] for key in ['overall_errors', 'by_year_errors', 'dm_tests', 'eb_parameters']}
    verdicts, audits = {}, {}
    for line in design_json['lines']:
        _, overall, annual, dm, params, audit = evaluate_line(panel, line, design_json)
        for key, frame in zip(tables, [overall, annual, dm, params], strict=True):
            tables[key].append(frame)
        verdicts[line['key']] = verdict(overall, dm, design_json)
        audits[line['key']] = audit
    count = sum(v['passed'] for v in verdicts.values())
    return {**{key: pd.concat(parts, ignore_index=True) for key, parts in tables.items()},
            'verdicts': verdicts, 'audits': audits, 'test_design': design_json,
            'headline': f'{count} of {len(design_json["lines"])} lines pass'}


def write_outputs(results, out_dir, vintage_path, run_meta):
    """Write an explicit allowlist of aggregate tables, plus provenance.

    Callers supply run_start_time_utc at run start. Defaults support standalone
    callers; notebook runs also provide the verified pre-registration provenance.
    """
    if results['test_design'] != load_design():
        raise ValueError('Results design differs from the fixed pre-registration')
    tables = Path(out_dir) / 'tables'
    tables.mkdir(parents=True, exist_ok=True)
    for name in ['overall_errors', 'by_year_errors', 'dm_tests', 'eb_parameters']:
        frame = results[name]
        if any(c in frame for c in ['rssd_id', 'report_date', 'actual', 'eb_panel']):
            raise ValueError('Aggregate exports must not contain per-bank rows')
        frame.to_csv(tables / f'{name}.csv', index=False)
        content = (json.dumps(frame.to_dict(orient='records'), indent=2) if name == 'dm_tests'
                   else frame.to_json(orient='records', indent=2))
        (tables / f'{name}.json').write_text(content + '\n')
    metadata = dict(run_meta)
    metadata.setdefault('run_start_time_utc', datetime.now(timezone.utc).isoformat())
    if 'git_head' not in metadata:
        metadata['git_head'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    metadata.update(test_design_sha256=hashlib.sha256(DESIGN_PATH.read_bytes()).hexdigest(),
                    fallback_counts={key: {name: audit[name] for name in ['ar_fallbacks', 'eb_fallbacks']}
                                     for key, audit in results['audits'].items()},
                    audits=results['audits'], headline=results['headline'])
    for name, value in [('verdicts', results['verdicts']), ('run_metadata', metadata)]:
        (tables / f'{name}.json').write_text(json.dumps(value, indent=2) + '\n')
    shutil.copyfile(DESIGN_PATH, tables / 'test_design.json')
    shutil.copyfile(vintage_path, tables / 'vintage.json')
