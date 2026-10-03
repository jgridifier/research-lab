"""Walk-forward naive / pooled-AR forecast combination (Statement Forecast v2).

Pesaran, Pick & Timmermann (2026), Quantitative Economics 17(2):342-393,
doi:10.3982/QE2589; Wang, Hyndman, Li & Kang (2023), IJF 39(4):1518-1547.

The two components, the case rule, the metrics and the clustered DM test are
imported from y9c.forecast unchanged; nothing here re-implements them. For
origin t the weight is fit only on pseudo-out-of-sample cases whose targets are
<= t, computed from the panel hard-truncated to quarters <= t.
"""
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
from y9c import forecast as y9c

from .paths import ROOT
from .prereg import COMBO_DESIGN_PATH

COMBO_RESULTS = ROOT / 'docs/tracks/statement-forecast/results-combination'
METHODS = y9c.METHODS
COMBO = 'combo'
REQUIRED_RUN_META = ('run_start_time_utc', 'git_head')
# baseline_forecasts raises these before pooled AR can be fit (burn-in phase).
UNDEFINED_AR = ('insufficient pooled AR burn-in', 'rank-deficient pooled AR training matrix')
TABLES = ['overall_errors', 'by_year_errors', 'dm_tests', 'weights']


def load_combo_design():
    return json.loads(COMBO_DESIGN_PATH.read_text(encoding='utf-8'))


def weight_grid(design_json):
    grid = design_json['method']['weight_grid']
    values = np.round(np.arange(grid['n_points']) * grid['step'] + grid['start'], 2)
    if values[0] != grid['start'] or values[-1] != grid['stop']:
        raise ValueError('Weight grid does not span the pre-registered range')
    return values


def combine(naive, pooled, w):
    """C = N + w (P - N), the pre-registered formula.

    Where P == N (including pooled AR's naive fallback) C is exactly N for every
    w, so such cases add an identical loss at every grid point and cannot break
    a tie. At w = 1 the formula is P algebraically; P is returned so that w = 1
    reproduces pooled AR exactly in floating point.
    """
    naive, pooled, w = (np.asarray(v, dtype=float) for v in (naive, pooled, w))
    return np.where(w == 1, pooled, naive + w * (pooled - naive))


def truncate(panel, origin):
    """Hard truncation: drop every row dated after the origin quarter."""
    return panel.loc[panel.report_date.dt.to_period('Q').le(origin)]


def first_pooled_ar_origin(data, column, last_origin):
    """Earliest quarter <= last_origin at which y9c pooled AR can be fit."""
    for origin in sorted(q for q in data.quarter.unique() if q <= last_origin):
        try:
            y9c.baseline_forecasts(data, [origin], column)
        except ValueError as error:
            message = str(error)
            if any(token in message for token in UNDEFINED_AR):
                continue
            if message == 'No evaluation cases':
                return origin  # pooled AR is defined; this origin simply has no cases
            raise
        return origin
    return None


def pseudo_oos_cases(panel, origin, column):
    """Pseudo-OOS cases (i, s) with target s+1 <= origin, using data <= origin only.

    Each case's N and P come from y9c.baseline_forecasts at origin s, whose
    selection and pooled-AR fit use rows dated <= s; the target X_s+1 only
    enters as the actual through the shared case rule.
    """
    data = y9c.design(truncate(panel, origin), column)
    start = first_pooled_ar_origin(data, column, origin - 1)
    empty = pd.DataFrame(columns=['rssd_id', 'quarter', 'target_quarter', 'actual', *METHODS, 'ar_fallback'])
    if start is None:
        return empty
    try:
        cases, _ = y9c.baseline_forecasts(data, pd.period_range(start, origin - 1, freq='Q'), column)
    except ValueError as error:
        if str(error) == 'No evaluation cases':
            return empty
        raise
    if not cases.target_quarter.le(origin).all():
        raise AssertionError(f'{origin}: pseudo-OOS case with target after the origin')
    return cases


def fit_weight(cases, design_json):
    """Grid argmin of summed absolute error; ties -> smallest w; <8 target quarters -> 0.5."""
    method = design_json['method']
    grid = weight_grid(design_json)
    n_quarters = int(cases.target_quarter.nunique()) if len(cases) else 0
    info = dict(n_pseudo_cases=int(len(cases)), n_pseudo_target_quarters=n_quarters,
                first_pseudo_target=str(cases.target_quarter.min()) if len(cases) else '',
                last_pseudo_target=str(cases.target_quarter.max()) if len(cases) else '',
                pseudo_ar_fallbacks=int(cases.ar_fallback.sum()) if len(cases) else 0)
    if n_quarters < method['min_distinct_target_quarters']:
        return float(method['fallback_weight']), dict(info, weight_rule='min_quarters_fallback',
                                                      pseudo_sae=float('nan'))
    naive = cases.naive.to_numpy(dtype=float)
    pooled = cases.pooled_ar.to_numpy(dtype=float)
    actual = cases.actual.to_numpy(dtype=float)
    if not (np.isfinite(naive).all() and np.isfinite(pooled).all() and np.isfinite(actual).all()):
        raise ValueError('Nonfinite pseudo-OOS input; no clipping or silent case removal')
    losses = np.array([np.abs(combine(naive, pooled, w) - actual).sum() for w in grid])
    if not np.isfinite(losses).all():
        raise ValueError('Nonfinite pseudo-OOS loss')
    best = int(np.flatnonzero(losses == losses.min())[0])  # grid ascends: first = smallest w
    return float(grid[best]), dict(info, weight_rule='fit', pseudo_sae=float(losses[best]))


def combo_weights(panel, column, origins, design_json, line_key=''):
    rows = []
    for origin in origins:
        w, info = fit_weight(pseudo_oos_cases(panel, origin, column), design_json)
        rows.append(dict(line=line_key, origin=str(origin), target=str(origin + 1), w=w, **info))
    return pd.DataFrame(rows)


def combo_forecasts(panel, line, design_json, origins):
    """Imported baseline cases at the given origins plus the origin-specific combination."""
    column = line['column']
    forecasts, audit = y9c.baseline_forecasts(y9c.design(panel, column), origins, column)
    weights = combo_weights(panel, column, origins, design_json, line['key'])
    by_origin = dict(zip(pd.PeriodIndex(weights.origin, freq='Q'), weights.w, strict=True))
    w = forecasts.quarter.map(by_origin).to_numpy(dtype=float)
    forecasts[COMBO] = combine(forecasts.naive.to_numpy(dtype=float), forecasts.pooled_ar.to_numpy(dtype=float), w)
    forecasts['w'] = w
    if not np.isfinite(forecasts[[*METHODS, COMBO, 'actual']].to_numpy(dtype=float)).all():
        raise ValueError('Nonfinite forecast; no clipping or silent case removal')
    return forecasts, audit, weights


def evaluate_combo_line(panel, line, design_json):
    """Cases, overall, by-year, DM, weight path and aggregate audit for one line."""
    if isinstance(line, str):
        line = next(item for item in design_json['lines'] if item['key'] == line)
    data_quarters = set(panel.report_date.dt.to_period('Q'))
    window = design_json['test_window']
    if pd.Period(window['last_target'], freq='Q') not in data_quarters:
        raise ValueError(f"Panel lacks required last target {window['last_target']}")
    origins = pd.period_range(window['first_origin'], window['last_origin'], freq='Q')
    forecasts, audit, weights = combo_forecasts(panel, line, design_json, origins)
    forecasts['target_year'] = forecasts.target_quarter.dt.year
    methods = [*METHODS, COMBO]
    overall = y9c.metrics(forecasts, methods=methods).assign(line=line['key'])
    by_year = pd.concat([y9c.metrics(group, methods=methods).assign(target_year=int(year), line=line['key'])
                         for year, group in forecasts.groupby('target_year')], ignore_index=True)
    dm = pd.concat([y9c.dm_tests(forecasts, first=b, second=COMBO).assign(line=line['key'], baseline=b)
                    for b in METHODS], ignore_index=True)
    summary = dict(n_forecasts_per_method=len(forecasts), n_target_quarters=len(origins),
                   **{key: sum(a[key] for a in audit) for key in
                      ['selected', 'dropped_target_missing', 'dropped_history', 'ar_fallbacks']},
                   weight_min_quarters_fallbacks=int(weights.weight_rule.eq('min_quarters_fallback').sum()),
                   origin_audit=audit)
    return forecasts, overall, by_year, dm, weights, summary


def verdict(overall, dm, design_json):
    """Strict unrounded MAE improvement and inclusive two-sided p threshold; undefined p fails."""
    comparator = design_json['pass_bar']['comparator']
    scores = overall.set_index('method')
    combo_mae, naive_mae = float(scores.loc[COMBO, 'mae']), float(scores.loc[comparator, 'mae'])
    row = dm.loc[dm.scope.eq('full') & dm.baseline.eq(comparator) & dm.loss.eq('abs')]
    if len(row) != 1:
        raise ValueError('Expected one full-sample absolute-error DM comparison')
    p = float(row.iloc[0].p_value)
    alpha = design_json['pass_bar']['alpha']
    passed = bool(combo_mae < naive_mae and np.isfinite(p) and p <= alpha)
    return dict(verdict='PASS' if passed else 'FAIL', passed=passed, combo_mae=combo_mae,
                naive_mae=naive_mae, p_value=p, alpha=alpha, t_stat=float(row.iloc[0].t_stat),
                comparator=comparator, loss='abs')


def run_all(panel, design_json, expected_cases=None):
    """Score every line; keep only aggregate tables. expected_cases enforces v1's count."""
    tables = {key: [] for key in TABLES}
    verdicts, audits = {}, {}
    for line in design_json['lines']:
        _, overall, annual, dm, weights, audit = evaluate_combo_line(panel, line, design_json)
        if expected_cases is not None and audit['n_forecasts_per_method'] != expected_cases:
            raise ValueError(f"{line['key']}: {audit['n_forecasts_per_method']} cases, expected {expected_cases}")
        for key, frame in zip(TABLES, [overall, annual, dm, weights], strict=True):
            tables[key].append(frame)
        verdicts[line['key']] = verdict(overall, dm, design_json)
        audits[line['key']] = audit
    count = sum(v['passed'] for v in verdicts.values())
    return {**{key: pd.concat(parts, ignore_index=True) for key, parts in tables.items()},
            'verdicts': verdicts, 'audits': audits, 'test_design': design_json,
            'headline': f'{count} of {len(design_json["lines"])} lines pass'}


def write_outputs(results, out_dir, vintage_path, run_meta):
    """Write an explicit allowlist of aggregate tables plus caller-supplied provenance."""
    if results['test_design'] != load_combo_design():
        raise ValueError('Results design differs from the fixed pre-registration')
    missing = [key for key in REQUIRED_RUN_META if not run_meta.get(key)]
    if missing:
        raise ValueError(f'run_meta must supply {missing}; they are not inferred at write time')
    tables = Path(out_dir) / 'tables'
    tables.mkdir(parents=True, exist_ok=True)
    for name in TABLES:
        frame = results[name]
        if any(c in frame for c in ['rssd_id', 'report_date', 'actual', COMBO]):
            raise ValueError('Aggregate exports must not contain per-bank rows')
        frame.to_csv(tables / f'{name}.csv', index=False)
        (tables / f'{name}.json').write_text(json.dumps(frame.to_dict(orient='records'), indent=2) + '\n')
    metadata = dict(run_meta)
    metadata.update(test_design_sha256=hashlib.sha256(COMBO_DESIGN_PATH.read_bytes()).hexdigest(),
                    fallback_counts={key: {name: audit[name] for name in
                                           ['ar_fallbacks', 'weight_min_quarters_fallbacks']}
                                     for key, audit in results['audits'].items()},
                    n_cases={key: audit['n_forecasts_per_method'] for key, audit in results['audits'].items()},
                    audits=results['audits'], headline=results['headline'])
    for name, value in [('verdicts', results['verdicts']), ('run_metadata', metadata)]:
        (tables / f'{name}.json').write_text(json.dumps(value, indent=2) + '\n')
    shutil.copyfile(COMBO_DESIGN_PATH, tables / 'test_design_combo.json')
    shutil.copyfile(vintage_path, tables / 'vintage.json')
