"""Render Statement Forecast aggregate outputs in the shared site layout."""
import argparse
from html import escape
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / 'docs/tracks/statement-forecast/results'
LABELS = {'eb_panel': 'EB panel', 'naive': 'Naive', 'seasonal_naive': 'Seasonal naive',
          'pooled_ar': 'Pooled panel AR'}


def text(value):
    return escape(str(value))


def error_table(frame, dm=None):
    rows = []
    for row in frame.itertuples():
        record = {}
        if hasattr(row, 'target_year'):
            record['Target year'] = row.target_year
        record.update({'Method': LABELS[row.method], 'Forecasts (count)': row.n_forecasts,
                       'MAE (thousands USD)': f'{row.mae:,.0f}', 'RMSE (thousands USD)': f'{row.rmse:,.0f}'})
        if dm is not None:
            for loss, label in [('abs', 'absolute error'), ('squared', 'squared error')]:
                match = dm.loc[dm.baseline.eq(row.method) & dm.loss.eq(loss)]
                record[f'DM t · {label}'] = f'{match.iloc[0].t_stat:.3f}' if len(match) else '—'
                record[f'DM p · {label}'] = f'{match.iloc[0].p_value:.4f}' if len(match) else '—'
        rows.append(record)
    return pd.DataFrame(rows).to_html(index=False, border=0, escape=True)


def dm_table(frame):
    frame = frame.copy()
    frame['baseline'] = frame.baseline.map(LABELS)
    frame['loss'] = frame.loss.map({'abs': 'Absolute error', 'squared': 'Squared error'})
    frame['t_stat'] = frame.t_stat.map(lambda v: f'{v:.3f}')
    frame['p_value'] = frame.p_value.map(lambda v: f'{v:.4f}')
    columns = ['scope', 'baseline', 'loss', 'n', 'G', 'df', 't_stat', 'p_value', 'inference']
    return frame[columns].rename(columns={'scope':'Target year', 'baseline':'Baseline', 'loss':'Loss',
        'n':'Forecasts (count)', 't_stat':'DM t', 'p_value':'Two-sided p', 'inference':'Inference'}).to_html(
            index=False, border=0, escape=True)


def parameter_table(parameters, labels):
    rows = []
    for line, group in parameters.groupby('line', sort=False):
        for column in ['rho', 'shrinkage', 'omega2']:
            rows.append({'Line': labels[line], 'Parameter': column, 'Minimum': group[column].min(),
                         'Median': group[column].median(), 'Maximum': group[column].max()})
    return pd.DataFrame(rows).to_html(index=False, border=0, escape=True, float_format=lambda v: f'{v:.4f}')


def render(results_dir):
    results_dir = Path(results_dir)
    tables = results_dir / 'tables'
    def read(name):
        return json.loads((tables / f'{name}.json').read_text())
    design, metadata, vintage, verdicts = (read(n) for n in ['test_design', 'run_metadata', 'vintage', 'verdicts'])
    overall = pd.read_csv(tables / 'overall_errors.csv')
    annual = pd.read_csv(tables / 'by_year_errors.csv')
    dm = pd.read_csv(tables / 'dm_tests.csv', dtype={'scope':str})
    parameters = pd.read_csv(tables / 'eb_parameters.csv')
    line_labels = {line['key']: line['label'] for line in design['lines']}
    sections, yearly = [], []
    for line in design['lines']:
        key = line['key']
        scores = overall.loc[overall.line.eq(key)].set_index('method').reindex(LABELS).reset_index()
        full = dm.loc[dm.line.eq(key) & dm.scope.eq('full')]
        v = verdicts[key]
        audit = metadata['audits'][key]
        fallback = metadata['fallback_counts'][key]
        comparison = '<' if v['eb_mae'] < v['naive_mae'] else '>='
        verdict_text = (f"{v['verdict']}: EB MAE {v['eb_mae']:,.0f} {comparison} naive MAE {v['naive_mae']:,.0f} "
                        f"thousands USD; absolute-error DM p = {v['p_value']:.4f} (bar ≤ {v['alpha']:.2f}).")
        sections.append(f'''<h3>{text(line['label'])} ({text(line['mdrm'])})</h3>
{error_table(scores, full)}
<p><strong>{text(verdict_text)}</strong> Verdicts use unrounded values.</p>
<p>EB fallbacks: {fallback['eb_fallbacks']:,}; pooled AR fallbacks: {fallback['ar_fallbacks']:,}.
Of {audit['selected']:,} selected origin–BHC pairs, {audit['dropped_target_missing']:,} lack targets and
{audit['dropped_history']:,} additional pairs lack current or seasonal history.
Estimation membership precedes these evaluation exclusions.</p>''')
        yearly.append(f'''<h3>{text(line['label'])} · Descriptive only</h3>
{error_table(annual.loc[annual.line.eq(key)])}
<h3>Per-year DM · Descriptive only</h3>
{dm_table(dm.loc[dm.line.eq(key) & dm.scope.ne('full')])}''')
    count = sum(v['passed'] for v in verdicts.values())
    headline = f'{count} of {len(design["lines"])} lines pass the pre-registered bar'
    method_keys = ['transform', 'level_forecast', 'window', 'seasonal_regressors', 'estimation',
                   'correlated_random_effects', 'tweedie', 'estimation_cross_section', 'fallback', 'no_tuning']
    notes = ''.join(f'<li>{text(design["method"][key])}</li>' for key in method_keys)
    download_rows = ''.join(f'<tr><td>{text(info["quarter"])}</td><td>{text(info["downloaded_at_utc"])}</td></tr>'
                            for info in vintage['downloads'].values())
    links = []
    for name in ['overall_errors', 'by_year_errors', 'dm_tests', 'eb_parameters']:
        for ext in ['csv','json']:
            links.append(f'<a href="tables/{name}.{ext}">{text(name)} {ext.upper()}</a>')
    for name in ['verdicts', 'run_metadata', 'test_design', 'vintage']:
        links.append(f'<a href="tables/{name}.json">{text(name)} JSON</a>')
    prereg = str(metadata['prereg_commit'])
    prereg_link = f'https://github.com/jgridifier/research-lab/commit/{prereg}'
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Statement Forecast Results — Research Lab</title>
  <meta name="description" content="Pre-registered empirical-Bayes forecasts of three quarterly Y-9C income-statement lines." />
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
    <div class="page-header__eyebrow">Track 1 · Results</div>
    <h1>Empirical-Bayes statement forecasts</h1>
    <p class="page-header__sub">Next-quarter NII, noninterest income and expense on the top-50 FR Y-9C panel. Research only.</p>
  </div>
</header>
<main class="page-content prose">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="../../../index.html">Home</a><span aria-hidden="true"> › </span>
    <a href="../index.html">Statement Forecast</a><span aria-hidden="true"> › </span>Results
  </nav>
  <h2>Question and design</h2>
  <p>{text(design['question'])}</p>
  <p>{text(design['universe'])} Targets: {text(design['test_window']['first_target'])}–{text(design['test_window']['last_target'])};
  origins: {text(design['test_window']['first_origin'])}–{text(design['test_window']['last_origin'])}.
  {text(design['evaluation_cases'])}</p>
  <p>{text(design['units'])}. Errors receive equal weight per BHC-quarter.</p>
  <h2>The pre-registered bar</h2>
  <blockquote>{text(design['pass_bar']['rule'])}</blockquote>
  <p><a href="tables/test_design.json">Fixed pre-registration</a> ·
  Commit <a href="{escape(prereg_link, quote=True)}">{text(prereg)}</a> ·
  Commit time: {text(metadata['prereg_commit_time'])}.
  SHA-256: <code>{text(metadata['test_design_sha256'])}</code>.</p>
  <h2>{text(headline)}</h2>
  <p>{text(design['multiple_testing'])} RMSE, squared-error DM, comparisons with seasonal naive and
  pooled AR, and parameter summaries are descriptive only.</p>
  <p>DM differential = L(baseline) − L(EB panel), error = forecast − actual.
  Positive t favors EB. CR1 standard errors cluster by target quarter; two-sided p uses Student t(G−1).
  There is no correction for dependence between quarters. Undefined p means FAIL.</p>
  {''.join(sections)}
  <h2>Specification and paper deviations</h2>
  <p>{text(design['method']['equation'])}</p>
  <ul>{notes}</ul>
  <p>{text(design['baselines']['source'])}</p>
  <p>Deviations from the paper: quarterly rather than annual forecasting; a top-50 cross-section
  (N≈50 before incomplete-window exclusions) rather than all BHCs; seasonal dummies;
  no macro covariates; no outlier elimination. No trimming, winsorization, clipping or case removal.</p>
  <h2>EB parameter summary · Descriptive only</h2>
  <p>Minimum, median and maximum across origin-specific fits; shrinkage is the weight toward the CRE prior mean.</p>
  {parameter_table(parameters, line_labels)}
  <h2>Per-year errors and DM · Descriptive only</h2>
  <p>Four target-quarter clusters per complete year and two in 2026 give weak inference;
  these breakdowns do not change the full-sample verdicts.</p>
  {''.join(yearly)}
  <h2>Figures</h2>
  <figure><img src="figures/mae_by_line.png" alt="MAE by method and statement line" width="100%" />
    <figcaption>Equal-weight BHC-quarter MAE, thousands USD; matched cases within each line.</figcaption></figure>
  <figure><img src="figures/eb_parameters.png" alt="Estimated rho and shrinkage by origin and line" width="100%" />
    <figcaption>Rolling QMLE persistence and Tweedie shrinkage; descriptive only.</figcaption></figure>
  <h2>Data vintage</h2>
  <p>Coverage: <strong>{text(vintage['first_quarter'])}–{text(vintage['last_quarter'])}</strong>,
  {text(vintage['n_quarters'])} quarters. Build time (UTC): {text(vintage['build_time_utc'])}.
  Source: <a href="https://www.ffiec.gov/npw/FinancialReport/FinancialDataDownload">FFIEC NIC Financial Data Download</a>.
  Cached files are reused; first-seen timestamps are not claimed as original download times.</p>
  <details><summary>NIC download dates and cache provenance (UTC)</summary>
    <table><thead><tr><th>Quarter</th><th>Downloaded / first seen (UTC)</th></tr></thead><tbody>{download_rows}</tbody></table>
  </details>
  <p>Run start (UTC): {text(metadata['run_start_time_utc'])}; git HEAD: <code>{text(metadata['git_head'])}</code>.</p>
  <h2>Tables and reproduction</h2>
  <p>{' · '.join(links)}</p>
  <pre><code>make statement-forecast-test
make statement-forecast</code></pre>
  <p>The shared y9c package supplies downloads, calendar-year de-cumulation, baseline forecasts,
  metrics and clustered DM. Only aggregate tables, parameters and figures are exported.</p>
  <h2>Limitations</h2>
  <p>{text(design['timing_limitation'])}</p>
  <p>RSSD identities are used as reported, without pro-forma merger adjustments. Entrants need history;
  exiters retain historical training observations but missing targets are not scored. Acquisition jumps
  and negative de-cumulations remain. Missing predecessor quarters are never bridged or imputed.</p>
  <p>Foreign-bank intermediate holding companies can enter the top 50; parent and subsidiary filers
  are not consolidated across RSSD IDs. The 2018Q3 reporting threshold change mainly affects smaller filers.
  Dollar losses emphasize large institutions; the latest vintage can be incomplete and contain revisions.
  The Gaussian CRE assumption and small estimation cross-section limit generality. Research only.</p>
  <h2>Citation</h2>
  <blockquote>Liu, L., Moon, H. R., &amp; Schorfheide, F. <em>Forecasting with Dynamic Panel Data Models.</em>
  NBER Working Paper 25102 (2018); <em>Econometrica</em> 88(1), 171–201 (2020).
  <a href="https://www.nber.org/papers/w25102">NBER w25102</a>.</blockquote>
</main>
<footer class="site-footer">
  <div class="site-footer__inner">
    <p class="site-footer__disclaimer"><strong>Independent research lab</strong> ·
      Not affiliated with any employer or financial institution · Not investment advice.</p>
    <div class="site-footer__links">
      <a href="../../../index.html">Home</a>
      <a href="../index.html">Statement Forecast</a>
      <a href="../../y9c-panel/index.html">Y-9C Panel</a>
      <a href="https://github.com/jgridifier/research-lab">GitHub</a>
    </div>
  </div>
</footer>
</body>
</html>
'''
    destination = results_dir / 'index.html'
    destination.write_text(html)
    print(f'Rendered {destination}')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results_dir', nargs='?', type=Path, default=RESULTS)
    args = parser.parse_args()
    render(args.results_dir)
