"""Render the static results page using aggregate tables and vintage metadata."""
from html import escape
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / 'docs/tracks/y9c-panel/results'
TABLES = RESULTS / 'tables'
LABELS = {'naive': 'Naive', 'seasonal_naive': 'Seasonal naive', 'pooled_ar': 'Pooled panel AR'}


def table(frame):
    frame = frame.copy()
    frame['method'] = frame.method.map(LABELS)
    for column in ['mae', 'rmse']:
        frame[column] = frame[column].map(lambda value: f'{value:,.0f}')
    columns = ['target_year'] if 'target_year' in frame else []
    columns += ['method', 'n_forecasts', 'mae', 'rmse', 'mape', 'n_mape', 'mdape']
    frame = frame[columns].rename(columns={'target_year': 'Target year', 'method': 'Method',
        'n_forecasts': 'Forecasts (count)', 'mae': 'MAE (thousands USD)',
        'rmse': 'RMSE (thousands USD)', 'mape': 'MAPE (%)', 'n_mape': 'Percentage-error cases (count)', 'mdape': 'MdAPE (%, supplementary)' })
    return frame.to_html(index=False, border=0, float_format=lambda v: f'{v:,.3f}', escape=True)


def dm_table(frame):
    frame = frame.copy()
    frame['loss'] = frame.loss.map({'abs': 'Absolute error (thousands USD)',
                                  'squared': 'Squared error ((thousands USD)²)'})
    for column in ['mean_diff', 'se']:
        frame[column] = frame[column].map(lambda value: f'{value:,.0f}')
    frame['favored'] = frame.favored.map({**LABELS, 'tie': 'Tie'})
    columns = ['scope', 'loss', 'n', 'G', 'mean_diff', 'se', 't_stat', 'df', 'p_value', 'favored', 'inference']
    return frame[columns].rename(columns={'scope': 'Scope', 'loss': 'Loss / differential units',
        'mean_diff': 'Mean loss differential', 'se': 'Cluster-robust SE',
        't_stat': 'Cluster-robust t', 'p_value': 'Two-sided p', 'favored': 'Favored method',
        'inference': 'Inference'}).to_html(index=False, border=0, float_format=lambda v: f'{v:.4f}')


def dm_headline(frame):
    """One plain sentence on the mean loss difference (naive minus pooled AR) at a fixed 5% level."""
    sentences = []
    for i, row in enumerate(frame.itertuples()):
        loss = 'absolute error' if row.loss == 'abs' else 'squared error'
        favored = 'naive' if row.mean_diff < 0 else 'pooled AR' if row.mean_diff > 0 else 'neither method'
        stats = f"t = {row.t_stat:.2f}, df = {row.df}, p = {row.p_value:.2g}"
        if row.p_value < 0.05 and row.p_value >= 0.04:
            sentences.append(f"For {loss} it is borderline ({stats}).")
        elif row.p_value < 0.05:
            sentences.append(f"the mean loss difference favors {favored} for {loss} ({stats}).")
        else:
            sentences.append(f"For {loss} the mean loss difference is not distinguishable from zero ({stats}).")
    text = ' '.join(sentences)
    if text.startswith('the mean loss difference'):
        text = 'At the 5% level, ' + text
    else:
        text = 'At the 5% level: ' + text
    return text + ' Neither p-value is adjusted for testing two loss functions.'


def winners(values):
    return '; '.join(f'{metric.upper()}: {", ".join(LABELS[m] for m in methods)}'
                     for metric, methods in values.items())


def main():
    overall = pd.read_csv(TABLES / 'overall_errors.csv')
    annual = pd.read_csv(TABLES / 'by_year_errors.csv')
    dm = pd.read_csv(TABLES / 'dm_tests.csv', dtype={'scope': str})
    dm_full = dm[dm.scope.eq('full')]
    design = json.loads((TABLES / 'test_design.json').read_text())
    vintage = json.loads((TABLES / 'vintage.json').read_text())
    download_rows = ''.join(f'<tr><td>{escape(info["quarter"])}</td><td>{escape(info["downloaded_at_utc"])}</td></tr>'
                            for info in vintage['downloads'].values())
    year_winners = ''.join(f'<li>{year}: {winners(value)}.</li>' for year, value in design['by_year_winners'].items())
    supplementary_year_winners = ''.join(f'<li>{year}: {", ".join(LABELS[m] for m in value)}.</li>'
                                        for year, value in design['supplementary_by_year_mdape_winners'].items())
    figures = [
        ('jpm_nii.png', 'JPMorgan quarterly and reported YTD net interest income',
         'JPMorgan (RSSD 1039502): quarterly and reported YTD NII, thousands USD. Complete-year quarterly sums equal Q4 YTD.'),
        ('coverage.png', 'Quarterly Y-9C filer count and top-50 asset cutoff',
         'Filers with reported consolidated assets (BHC count) and the 50th-largest asset value (thousands USD). The 2018Q3 threshold change mainly affects small filers.'),
        ('annual_mae.png', 'Mean absolute forecast error by target year and method',
         'MAE by target year, thousands USD. The final year may be partial; every method uses the same evaluated cases.'),
        ('aggregate_nii.png', 'Actual and forecast aggregate NII for evaluated top-50 cases',
         'NII summed over the same evaluated BHCs within each target quarter, thousands USD. Membership changes over time; aggregate cancellation can hide institution-level errors.')]
    figure_html = '\n'.join(f'<figure><img src="figures/{name}" alt="{alt}" width="100%" /><figcaption>{caption}</figcaption></figure>'
                            for name, alt, caption in figures)
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Y-9C NII Forecast Results — Research Lab</title>
  <meta name="description" content="Reproducible next-quarter net interest income forecasts for the largest 50 Y-9C filers at each origin." />
  <link rel="stylesheet" href="../../../assets/site.css" />
</head>
<body>
<nav class="site-nav" aria-label="Site navigation">
  <div class="site-nav__inner">
    <a class="site-nav__logo" href="../../../index.html">Research Lab</a>
    <ul class="site-nav__links">
      <li><a href="../../../index.html">Home</a></li>
      <li><a href="../../../tracks/statement-forecast/index.html">Statement Forecast</a></li>
      <li><a href="../index.html" class="active">Y-9C Panel</a></li>
      <li><a href="../../../tracks/dfm-sinkhorn/index.html">DFM × Sinkhorn</a></li>
    </ul>
  </div>
</nav>
<header class="page-header">
  <div class="page-header__inner">
    <div class="page-header__eyebrow">Track 2 · Results</div>
    <h1>Next-quarter net interest income</h1>
    <p class="page-header__sub">A fixed forecasting comparison on the top-50 FR Y-9C panel. Research only.</p>
  </div>
</header>
<main class="page-content prose">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="../../../index.html">Home</a><span aria-hidden="true"> › </span>
    <a href="../index.html">Y-9C Panel</a><span aria-hidden="true"> › </span>Results
  </nav>
  <h2>Question and design</h2>
  <p>Can pooled historical NII growth improve on simple next-quarter forecasts? The single target is
  net interest income (BHCK4074), the difference between interest income and interest expense,
  de-cumulated from calendar-year YTD to quarterly flows. All monetary values are <strong>thousands of USD</strong>.
  The corrected mapping is BHCK4107 − BHCK4073 = BHCK4074. The identity holds across
  {vintage['sanity']['identity_rows']:,} comparable rows, with maximum discrepancy
  {vintage['sanity']['max_identity_difference_thousands_usd']:,.0f} thousand USD.</p>
  <p>At each origin t, rank BHCs by reported total assets (BHCK2170) at t and take the largest 50;
  break asset ties by RSSD ID. Historical training membership uses this same rule at each historical
  origin. Future assets and membership never select the origin universe. Forecast y(t+1) using only
  report quarters through t. This is a report-quarter backtest with currently downloaded filings,
  not a real-time filing-vintage backtest: reporting lags and later revisions are not modeled.</p>
  <p>The test window was fixed a priori: target quarters <strong>2022Q1–{design['test_end']}</strong>,
  origins 2021Q4–{design['last_origin']}. Roughly 3.5 initial years are reserved for burn-in.
  The models, universe, test window and headline metrics are unchanged; MdAPE is a supplementary post-review diagnostic.</p>
  <h2>Methods</h2>
  <ul>
    <li><strong>Naive:</strong> ŷ(t+1) = y(t).</li>
    <li><strong>Seasonal naive:</strong> ŷ(t+1) = y(t−3), the same quarter last year.</li>
    <li><strong>Pooled panel AR:</strong> g(s) = log y(s) − log y(s−1);
      g(s+1) = a + b1 g(s) + b4 g(s−3). Expanding pooled OLS with an intercept,
      refitted at every origin using historical top-50 rows with s+1 ≤ t and positive required NII values.
      Forecast y(t) × exp(predicted growth). Missing/nonpositive log inputs trigger a naive fallback.
      No clipping, regularization, weighting, or parameter tuning.</li>
  </ul>
  <p>All three methods share <strong>{design['n_forecasts_per_method']:,} evaluated forecasts per method</strong>
  over {design['n_target_quarters']} target quarters. Of {design['selected_origin_bhc_pairs']:,} selected origin–BHC pairs,
  {design['dropped_target_missing']} lack reported/de-cumulated next-quarter NII (including exits/mergers), and
  {design['dropped_history']} additional pairs lack current or seasonal history. These are disjoint drop counts;
  a missing target is not proof of a merger. There are {design['ar_fallbacks']} AR fallbacks among evaluated cases.</p>
  <h2>Forecast errors</h2>
  <p>Equal weight per evaluated BHC-quarter. MAE and RMSE are in thousands USD; MAPE is the mean
  absolute error divided by absolute actual NII, in percent. {design['zero_actuals_excluded_from_mape']} zero actuals
  are excluded from MAPE and supplementary MdAPE. All other comparisons use the same intersection of cases.</p>
  <p><strong>Overall metric winners:</strong> {winners(design['winners'])}. These are the observed results,
  including baseline wins.</p>
  <p><strong>MdAPE (median absolute percentage error, %): supplementary, added after observing MAPE outliers; does not replace MAPE.</strong>
  It uses the same absolute percentage errors and zero-actual exclusion as MAPE.
  Its winner is reported separately: <strong>{', '.join(LABELS[m] for m in design['supplementary_mdape_winners'])}</strong>.</p>
  <p>MAPE is driven by a few foreign-bank IHCs with near-zero or negative NII, including BNP Paribas USA,
  Mizuho Americas and Credit Suisse USA. There are {design['nonpositive_actuals']} nonpositive actuals among
  {design['n_forecasts_per_method']} evaluated cases. BNP Paribas USA's 2022Q1 naive absolute percentage error
  is about 3,350%. The notebook shows the ten largest naive percentage errors; no cases are removed.</p>
  {table(overall)}
  <h3>Is naive's edge over pooled AR distinguishable from noise?</h3>
  <p>{dm_headline(dm_full)}</p>
  <p>Paired Diebold–Mariano loss differential: L(naive) − L(pooled AR), with error = forecast − actual.
  Negative values favor naive. All {design['n_forecasts_per_method']} matched cases are included.
  Standard errors cluster by target quarter to absorb cross-sectional correlation within a quarter,
  using the CR1 correction G/(G−1) and a Student t(G−1) reference distribution.
  One-step forecasts are assumed to have no serial dependence across quarters beyond what is captured;
  this test does not adjust for correlation between quarters. The stated significance threshold is 5%.</p>
  {dm_table(dm_full)}
  <h3>By target year</h3>
  <p>The final year may be partial. <strong>Per-year results (including pooled AR's 2025 and 2026 wins)
  are descriptive only: 4 clusters per year (2 in 2026), so clustered inference is weak (df=3)
  or essentially undefined (df=1).</strong></p>
  {table(annual)}
  <ul>{year_winners}</ul>
  <p>Supplementary MdAPE winners by target year:</p>
  <ul>{supplementary_year_winners}</ul>
  <h3>Per-year DM comparisons — descriptive only</h3>
  {dm_table(dm[dm.scope.ne('full')])}
  <h2>Figures</h2>
  {figure_html}
  <h2>Data vintage</h2>
  <p>Coverage: <strong>{vintage['first_quarter']}–{vintage['last_quarter']}</strong>,
  {vintage['n_quarters']} quarters. Build time (UTC): {escape(vintage['build_time_utc'])}.
  Source: <a href="https://www.ffiec.gov/npw/FinancialReport/FinancialDataDownload">FFIEC NIC Financial Data Download</a>.
  Cached files are reused; first-seen timestamps are not claimed as original download times.</p>
  <details><summary>NIC download dates and cache provenance (UTC)</summary>
    <table><thead><tr><th>Quarter</th><th>Downloaded / first seen (UTC)</th></tr></thead><tbody>{download_rows}</tbody></table>
  </details>
  <p><a href="tables/vintage.json">Vintage and SHA-256 metadata</a> ·
  <a href="tables/test_design.json">Test design and origin-level counts</a> ·
  <a href="tables/overall_errors.csv">Overall errors CSV</a> ·
  <a href="tables/by_year_errors.csv">By-year errors CSV</a> ·
  <a href="tables/dm_tests.csv">DM tests CSV</a> · <a href="tables/dm_tests.json">DM tests JSON</a></p>
  <h2>Reproduce</h2>
  <pre><code>git clone https://github.com/jgridifier/research-lab &amp;&amp; cd research-lab &amp;&amp; make y9c</code></pre>
  <p>Requires Python 3.13, venv/pip, make, and network access to NIC and the package index.
  The in-repository <a href="https://github.com/jgridifier/research-lab/tree/main/tracks/y9c-panel">pipeline and notebook</a>
  download from 2018Q1 through the latest completed quarter, build the panel, execute the notebook,
  and render this page. Runtime raw files and panels are ignored by git; only aggregate outputs are published.</p>
  <h2>Caveats</h2>
  <ul>
    <li>RSSD IDs are used as reported, with no pro-forma merger adjustments. Entrants appear when they start filing;
    exiters retain their historical training rows but are not forecast after their final filing.
    Acquisition-related NII jumps remain in the data and can cause forecast errors.</li>
    <li>Q1 quarterly NII equals Q1 YTD. Q2–Q4 require the immediately previous quarter of the same calendar year,
    with a nonmissing value. {vintage['dropped_missing_prior_nii']} BHC-quarters lose quarterly NII for missing predecessors
    across the full panel. No imputation or subtraction across gaps is performed.</li>
    <li>There are {vintage['negative_nii_decumulations']} negative Q2–Q4 NII de-cumulations across the full panel;
    {vintage['negative_nii_after_positive']} follow a year in which every earlier quarter was observed and positive.
    These are diagnostics, not corrections or exclusions. BNP Paribas USA reported YTD NII of 1,910,303
    in 2021Q3 and 192,866 in 2021Q4, implying quarterly NII of −1,717,437 thousand USD.
    This is consistent with a within-year consolidation-scope change or restated YTD, but the flag alone
    does not establish the cause. Reported data are retained as-is.</li>
    <li>The 2018Q3 reporting threshold increased from $1 billion to $3 billion, mainly affecting small filers.
    The coverage figure counts institutions with reported consolidated assets, not every record in the bulk file.</li>
    <li>Foreign-bank intermediate holding companies file Y-9C and may be in the top 50. Parent and subsidiary
    filers are not consolidated across RSSD IDs; the aggregate is a sample sum, not a non-overlapping sector total.</li>
    <li>Monetary values are thousands of USD. Dollar losses emphasize large institutions. MAPE can be unstable near
    zero or sign changes; nonpositive values cannot enter log-growth training.</li>
    <li>Current downloaded filings can include revisions. The latest cached quarter may be incomplete.
    The final test year may cover fewer than four quarters. Research only; not investment advice.</li>
  </ul>
</main>
<footer class="site-footer">
  <div class="site-footer__inner">
    <p class="site-footer__disclaimer"><strong>Independent research lab</strong> ·
      Not affiliated with any employer or financial institution · Not investment advice.</p>
    <div class="site-footer__links">
      <a href="../../../index.html">Home</a>
      <a href="../../../tracks/statement-forecast/index.html">Statement Forecast</a>
      <a href="../index.html">Y-9C Panel</a>
      <a href="https://github.com/jgridifier/research-lab">GitHub</a>
    </div>
  </div>
</footer>
</body>
</html>
'''
    (RESULTS / 'index.html').write_text(html)
    print(f'Rendered {RESULTS.relative_to(ROOT) / "index.html"}')


if __name__ == '__main__':
    main()
