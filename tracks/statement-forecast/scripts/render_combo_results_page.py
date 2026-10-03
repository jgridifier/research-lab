"""Render the Statement Forecast v2 (naive / pooled-AR combination) results page.

Every number on the page is read from the exported tables in
docs/tracks/statement-forecast/results-combination/tables/; none is typed here.
"""
import argparse
from datetime import datetime
from html import escape
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / 'docs/tracks/statement-forecast/results-combination'
LABELS = {'combo': 'Combination', 'naive': 'Naive', 'seasonal_naive': 'Seasonal naive',
          'pooled_ar': 'Pooled panel AR'}
ET = ZoneInfo('America/New_York')


def text(value):
    return escape(str(value))


def scroll(table_html):
    """Wide tables scroll horizontally inside their own box on narrow screens."""
    return f'<div class="table-scroll" style="overflow-x:auto;-webkit-overflow-scrolling:touch">{table_html}</div>'


def num(value, spec):
    """Format a statistic; undefined (null/NaN) DM statistics render as 'undefined'."""
    if value is None or pd.isna(value):
        return 'undefined'
    return format(float(value), spec)


def to_et(timestamp):
    try:
        parsed = datetime.fromisoformat(str(timestamp))
    except ValueError:
        return str(timestamp)
    if parsed.tzinfo is None:
        return str(timestamp)
    return parsed.astimezone(ET).strftime('%Y-%m-%d %H:%M:%S ET')


def error_table(frame, dm=None):
    rows = []
    for row in frame.itertuples():
        record = {}
        if hasattr(row, 'target_year'):
            record['Target year'] = row.target_year
        record.update({'Method': LABELS[row.method], 'Forecasts (count)': f'{row.n_forecasts:,}',
                       'MAE (thousands USD)': f'{row.mae:,.0f}', 'RMSE (thousands USD)': f'{row.rmse:,.0f}'})
        if dm is not None:
            for loss, label in [('abs', 'absolute error'), ('squared', 'squared error')]:
                match = dm.loc[dm.baseline.eq(row.method) & dm.loss.eq(loss)]
                record[f'DM t vs combination · {label}'] = num(match.iloc[0].t_stat, '.3f') if len(match) else '—'
                record[f'DM p vs combination · {label}'] = num(match.iloc[0].p_value, '.4f') if len(match) else '—'
        rows.append(record)
    return scroll(pd.DataFrame(rows).to_html(index=False, border=0, escape=True))


def dm_table(frame):
    frame = frame.copy()
    frame['baseline'] = frame.baseline.map(LABELS)
    frame['loss'] = frame.loss.map({'abs': 'Absolute error', 'squared': 'Squared error'})
    frame['t_stat'] = frame.t_stat.map(lambda v: num(v, '.3f'))
    frame['p_value'] = frame.p_value.map(lambda v: num(v, '.4f'))
    columns = ['scope', 'baseline', 'loss', 'n', 'G', 't_stat', 'p_value', 'inference']
    return scroll(frame[columns].rename(columns={
        'scope': 'Target year', 'baseline': 'Baseline', 'loss': 'Loss', 'n': 'Forecasts (count)',
        't_stat': 'DM t', 'p_value': 'Two-sided p', 'inference': 'Inference'}).to_html(
            index=False, border=0, escape=True))


def weight_summary(weights, labels):
    rows = []
    for line, group in weights.groupby('line', sort=False):
        rows.append({'Line': labels[line], 'Origins (count)': len(group),
                     'First origin w': f'{group.w.iloc[0]:.2f}', 'Last origin w': f'{group.w.iloc[-1]:.2f}',
                     'Minimum w': f'{group.w.min():.2f}', 'Median w': f'{group.w.median():.2f}',
                     'Maximum w': f'{group.w.max():.2f}',
                     'Fewer-than-minimum-quarters fallbacks': int(group.weight_rule.eq('min_quarters_fallback').sum())})
    return scroll(pd.DataFrame(rows).to_html(index=False, border=0, escape=True))


def weight_path(weights, labels):
    path = weights.pivot(index='origin', columns='line', values='w')
    path = path[[key for key in labels if key in path.columns]].rename(columns=labels)
    pseudo = weights.groupby('origin', sort=True).agg(first=('first_pseudo_target', 'first'),
                                                      last=('last_pseudo_target', 'first'),
                                                      quarters=('n_pseudo_target_quarters', 'max'))
    frame = path.map(lambda v: f'{v:.2f}')
    frame.insert(0, 'Pseudo-OOS targets', [f"{pseudo.loc[o, 'first']}–{pseudo.loc[o, 'last']} "
                                           f"({pseudo.loc[o, 'quarters']} quarters)" for o in frame.index])
    frame.index.name = 'Origin'
    return scroll(frame.reset_index().to_html(index=False, border=0, escape=True))


def render(results_dir):
    results_dir = Path(results_dir)
    tables = results_dir / 'tables'

    def read(name):
        return json.loads((tables / f'{name}.json').read_text(encoding='utf-8'))
    design, metadata, vintage, verdicts = (read(n) for n in ['test_design_combo', 'run_metadata', 'vintage',
                                                             'verdicts'])
    overall = pd.read_csv(tables / 'overall_errors.csv')
    annual = pd.read_csv(tables / 'by_year_errors.csv')
    dm = pd.read_csv(tables / 'dm_tests.csv', dtype={'scope': str})
    weights = pd.read_csv(tables / 'weights.csv', dtype={'origin': str, 'target': str,
                                                         'first_pseudo_target': str, 'last_pseudo_target': str})
    labels = {line['key']: line['label'] for line in design['lines']}
    sections, yearly = [], []
    for line in design['lines']:
        key = line['key']
        scores = overall.loc[overall.line.eq(key)].set_index('method').reindex(LABELS).reset_index()
        full = dm.loc[dm.line.eq(key) & dm.scope.eq('full')]
        v = verdicts[key]
        audit = metadata['audits'][key]
        fallback = metadata['fallback_counts'][key]
        comparison = '<' if v['combo_mae'] < v['naive_mae'] else '≥'
        verdict_text = (f"{v['verdict']}: combination MAE {v['combo_mae']:,.0f} {comparison} naive MAE "
                        f"{v['naive_mae']:,.0f} thousands USD; absolute-error DM t = {num(v['t_stat'], '.3f')}, "
                        f"two-sided p = {num(v['p_value'], '.4f')} (bar ≤ {v['alpha']:.2f}).")
        sections.append(f'''<h3>{text(line['label'])} ({text(line['mdrm'])})</h3>
{error_table(scores, full)}
<p><strong>{text(verdict_text)}</strong> The verdict uses unrounded values.</p>
<p>Pooled AR naive fallbacks among evaluated cases: {fallback['ar_fallbacks']:,} (for these, the combination equals naive).
Origins using the fewer-than-minimum-quarters weight: {fallback['weight_min_quarters_fallbacks']:,}.
Of {audit['selected']:,} selected origin–BHC pairs, {audit['dropped_target_missing']:,} lack targets and
{audit['dropped_history']:,} more lack current or seasonal history; {audit['n_forecasts_per_method']:,} cases are scored.</p>''')
        yearly.append(f'''<h3>{text(line['label'])} · Descriptive only</h3>
{error_table(annual.loc[annual.line.eq(key)])}
<h4>Per-year DM vs the combination · Descriptive only</h4>
{dm_table(dm.loc[dm.line.eq(key) & dm.scope.ne('full')])}''')
    count = sum(v['passed'] for v in verdicts.values())
    headline = f'{count} of {len(design["lines"])} lines pass the pre-registered bar'
    disclosures = ''.join(f'<li>{text(item)}</li>' for item in design['required_disclosures'])
    method_items = ''.join(f'<li>{text(item)}</li>' for item in design['method_verbatim'])
    notes = ''.join(f'<li>{text(item)}</li>' for item in design['method']['implementation_notes'])
    citations = ''.join(f'<li>{text(c["text"])} <a href="{escape(c["url"], quote=True)}">{text(c["url"])}</a></li>'
                        for c in design['citations'])
    download_rows = ''.join(f'<tr><td>{text(info["quarter"])}</td><td>{text(info["downloaded_at_utc"])}</td></tr>'
                            for info in vintage['downloads'].values())
    links = []
    for name in ['overall_errors', 'by_year_errors', 'dm_tests', 'weights']:
        for ext in ['csv', 'json']:
            links.append(f'<a href="tables/{name}.{ext}">{text(name)} {ext.upper()}</a>')
    for name in ['verdicts', 'run_metadata', 'test_design_combo', 'vintage']:
        links.append(f'<a href="tables/{name}.json">{text(name)} JSON</a>')
    prereg = str(metadata['prereg_commit'])
    prereg_link = f'https://github.com/jgridifier/research-lab/commit/{prereg}'
    window = design['test_window']
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Statement Forecast v2 Results: Naive / Pooled-AR Combination — Research Lab</title>
  <meta name="description" content="Pre-registered walk-forward combination of naive and pooled-AR forecasts of three quarterly Y-9C income-statement lines." />
  <link rel="stylesheet" href="../../../assets/site.css" />
</head>
<body>
<nav class="site-nav" aria-label="Site navigation">
  <div class="site-nav__inner">
    <a class="site-nav__logo" href="../../../index.html">Research Lab</a>
    <ul class="site-nav__links">
      <li><a href="../../../index.html">Home</a></li>
      <li><a href="../index.html" class="active">Statement Forecast</a></li>
      <li><a href="../../y9c-panel/index.html">Y-9C Panel</a></li>
      <li><a href="../../dfm-sinkhorn/index.html">DFM × Sinkhorn</a></li>
    </ul>
  </div>
</nav>
<header class="page-header">
  <div class="page-header__inner">
    <div class="page-header__eyebrow">Track 1 · Results · Method v2</div>
    <h1>Naive / pooled-AR forecast combination</h1>
    <p class="page-header__sub">Next-quarter NII, noninterest income and expense on the top-50 FR Y-9C panel, one walk-forward weight per line. Research only.</p>
  </div>
</header>
<main class="page-content prose">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="../../../index.html">Home</a><span aria-hidden="true"> › </span>
    <a href="../index.html">Statement Forecast</a><span aria-hidden="true"> › </span>Results: combination
  </nav>
  <div class="callout"><strong>Selection disclosure.</strong><ul>{disclosures}</ul>
  A pass here is weaker evidence than a pass on fresh data. See the <a href="../combination-teaching.html">teaching note</a>
  and the <a href="../results/index.html">v1 results</a>.</div>
  <h2>{text(headline)}</h2>
  <p>{text(design['multiple_testing'])} Comparisons with pooled AR and seasonal naive, RMSE, squared-error DM,
  by-year results, the weight path and fallback counts are descriptive only.</p>
  <p>DM differential = L(baseline) − L(combination), error = forecast − actual.
  Positive t favors the combination. CR1 standard errors cluster by target quarter; two-sided p uses Student t(G−1).
  There is no correction for dependence between quarters. An undefined p is a FAIL.</p>
  {''.join(sections)}
  <h2>The pre-registered bar</h2>
  <blockquote>{text(design['pass_bar_verbatim'])}</blockquote>
  <p><a href="tables/test_design_combo.json">Fixed pre-registration</a> ·
  Commit <a href="{escape(prereg_link, quote=True)}"><code>{text(prereg)}</code></a> ·
  Commit time: {text(to_et(metadata['prereg_commit_time']))}.
  SHA-256: <code>{text(metadata['test_design_sha256'])}</code>.
  Run start: {text(to_et(metadata['run_start_time_utc']))} (recorded as {text(metadata['run_start_time_utc'])} UTC)
  at git HEAD <code>{text(metadata['git_head'])}</code>.</p>
  <h2>Question and design</h2>
  <p>{text(design['question'])}</p>
  <p>{text(design['universe'])} Targets: {text(window['first_target'])}–{text(window['last_target'])};
  origins: {text(window['first_origin'])}–{text(window['last_origin'])}. {text(design['evaluation_cases'])}</p>
  <p>{text(design['units'])}. Errors receive equal weight per BHC-quarter.</p>
  <h3>Method (pre-registered text)</h3>
  <ul>{method_items}</ul>
  <h3>Implementation notes (pre-registered)</h3>
  <ul>{notes}</ul>
  <p>{text(design['baselines']['source'])}</p>
  <h2>Weight path · Descriptive only</h2>
  <p>w is the weight on pooled AR (w = 0 is naive, w = 1 is pooled AR). Each origin's weight is fit only on
  pseudo-out-of-sample cases whose targets were already observed at that origin.</p>
  {weight_summary(weights, labels)}
  <details><summary>Weight by origin and line</summary>{weight_path(weights, labels)}</details>
  <h2>Per-year errors and DM · Descriptive only</h2>
  <p>Per-year breakdowns have few target-quarter clusters each and do not change the full-sample verdicts.</p>
  {''.join(yearly)}
  <h2>Figures</h2>
  <figure><img src="figures/mae_by_line.png" alt="MAE by method and statement line" style="max-width:100%;height:auto" />
    <figcaption>Equal-weight BHC-quarter MAE, thousands USD; matched cases within each line.</figcaption></figure>
  <figure><img src="figures/weight_path.png" alt="Combination weight on pooled AR by origin and line" style="max-width:100%;height:auto" />
    <figcaption>Walk-forward weight on pooled AR by origin; descriptive only.</figcaption></figure>
  <h2>Data vintage</h2>
  <p>Coverage: <strong>{text(vintage['first_quarter'])}–{text(vintage['last_quarter'])}</strong>,
  {text(vintage['n_quarters'])} quarters. Build time (UTC): {text(vintage['build_time_utc'])}.
  Source: <a href="https://www.ffiec.gov/npw/FinancialReport/FinancialDataDownload">FFIEC NIC Financial Data Download</a>.</p>
  <details><summary>NIC download dates and cache provenance (UTC)</summary>
    {scroll(f'<table><thead><tr><th>Quarter</th><th>Downloaded / first seen (UTC)</th></tr></thead><tbody>{download_rows}</tbody></table>')}
  </details>
  <h2>Tables and reproduction</h2>
  <p>{' · '.join(links)}</p>
  <pre><code>make statement-forecast-combo-test
make statement-forecast-combo</code></pre>
  <p>The shared y9c package supplies de-cumulation, the naive, seasonal-naive and pooled-AR baselines, metrics and
  the clustered DM test; the combination imports them unchanged. Only aggregate tables and figures are exported.</p>
  <h2>Limitations</h2>
  <p>{text(design['timing_limitation'])}</p>
  <p>RSSD identities are used as reported, without pro-forma merger adjustments; acquisition jumps remain.
  Missing predecessor quarters are never bridged or imputed. Dollar losses emphasize large institutions.
  The weight is a single scalar per line shared across banks. Research only.</p>
  <h2>Citations</h2>
  <ul>{citations}</ul>
</main>
<footer class="site-footer">
  <div class="site-footer__inner">
    <p class="site-footer__disclaimer"><strong>Independent research lab</strong> ·
      Not affiliated with any employer or financial institution · Not investment advice.</p>
    <div class="site-footer__links">
      <a href="../../../index.html">Home</a>
      <a href="../index.html">Statement Forecast</a>
      <a href="../combination-teaching.html">Teaching note</a>
      <a href="https://github.com/jgridifier/research-lab">GitHub</a>
    </div>
  </div>
</footer>
</body>
</html>
'''
    destination = results_dir / 'index.html'
    destination.write_text(html, encoding='utf-8')
    print(f'Rendered {destination}')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results_dir', nargs='?', type=Path, default=RESULTS)
    args = parser.parse_args()
    render(args.results_dir)
