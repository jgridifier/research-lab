# Statement Forecast: empirical-Bayes dynamic panel

Independent research lab. Not affiliated with any employer or financial institution. Not investment advice.

Run from the repository root with Python 3.13, venv/pip and make:

```sh
make statement-forecast-test
make statement-forecast
```

The pipeline installs the shared pinned environment, downloads/builds the shared Y-9C panel,
executes this track's notebook and renders this track's page. It does not execute the Y-9C notebook
or render its page. Network access is needed for dependency installation and uncached data.
Tests use synthetic data and need no panel cache. `make y9c-test` also guards the published
Y-9C results with committed SHA-256 hashes.

## Fixed specification

[`test_design.json`](test_design.json) is the fixed pre-registration; do not edit it to fit results.
Commit it separately before the first real-data run. The notebook checks its exact SHA-256 against
`git show HEAD:tracks/statement-forecast/test_design.json`, records the most recent commit touching
that file and its commit time, and refuses an uncommitted or changed specification. The committed
notebook holds the single real-data run (pre-registration commit `3ea20c8`, 2026-09-26 17:14:22 ET;
run start 2026-09-26 17:15:34 ET). The result was published whatever the verdict.

## Result (first run)

**0 of 3 lines pass the pre-registered bar.** On the same 893 matched cases per line, naive beats the
EB panel on MAE for NII (117,823 vs 150,011 thousand USD; abs-error DM p = 0.0026, favoring naive),
noninterest income (294,201 vs 394,099; p = 0.0002) and noninterest expense (230,601 vs 277,329;
p = 0.0158). See the [results page](../../docs/tracks/statement-forecast/results/index.html).

Liu, Moon & Schorfheide, *Forecasting with Dynamic Panel Data Models*, NBER Working Paper 25102
(2018); Econometrica 88(1), 171–201 (2020), [paper](https://www.nber.org/papers/w25102).
The first method forecasts BHCK4074 NII, BHCK4079 noninterest income and BHCK4093 noninterest expense
one quarter ahead, with targets **2022Q1–2026Q2** (18 origins, 2021Q4–2026Q1).

Transform quarterly flow X to `400 * X / lagged assets`, using the previous calendar quarter.
Fit 12 rolling equations and their initial condition (13 observed ratios), with common persistence,
three centered seasonal dummies and a Gaussian correlated-random-effects prior conditional on the
initial ratio. Profile the integrated likelihood (LMS eq. 24), including the zero prior-variance
boundary, from within and pooled OLS starts. Use the parametric Tweedie posterior mean
`lambda_hat + (sigma2/T) * score` (eqs. 17/20/30), and scale next-quarter predictions by origin assets.
Failed/nonfinite fits raise; missing complete windows receive counted naive fallbacks.
No tuning, trimming, winsorizing or outlier elimination.

Each line passes only if EB MAE is strictly below naive MAE and the full-sample absolute-error
clustered DM two-sided p is ≤ 0.05. Undefined p fails. The headline counts passes out of three.
No multiplicity adjustment. Seasonal-naive/pooled-AR comparisons, RMSE/squared-error DM,
per-year results and parameter summaries are descriptive only.

## Point-in-time design and reuse

`statement_forecast` imports `y9c.panel.PROCESSED` and `y9c.forecast` directly. There are no copies
of the panel builder, baselines, metrics, or clustered DM. Use
`PYTHONPATH=tracks/y9c-panel:tracks/statement-forecast` for standalone imports.

At each origin, the shared design ranks reported origin assets, RSSD breaking ties, and selects
50 banks. EB hard-truncates the panel before transforming it; estimation includes all selected
banks with complete ratio windows regardless of target availability. Only evaluation applies
the shared target/current/seasonal-history case rule. Calendar-key joins never bridge gaps.
Tests perturb future flows/assets/ranks, delete future observations and individual targets,
compare the exact estimation arrays, and verify lagged-asset level scaling and baseline parity.
The optional real-data serialization parity test requires `SF_RUN_REAL_PARITY=1` and skips if the
panel is absent. It is disabled by default so synthetic-only runs never inspect processed data.

These safeguards address report-quarter leakage, not filing lags or later revisions. Merger jumps
remain; no pro-forma histories or cross-RSSD consolidation are constructed.

## Outputs and synthetic smoke runs

Aggregate tables and figures go to `docs/tracks/statement-forecast/results/`: overall/by-year errors,
DM tests and origin-level EB parameters (CSV/JSON), verdicts, run metadata with audits and fallback
counts, an exact design copy and shared vintage copy. Only aggregate outputs are exported, never
per-bank forecasts. The renderer uses these outputs and the shared site CSS.

For a synthetic notebook run, set `SF_PANEL_PATH` to a synthetic parquet and `SF_RESULTS_DIR` to a
temporary output directory. Vintage defaults to `vintage.json` beside the supplied panel;
`SF_VINTAGE_PATH` can override it. The committed-spec check still applies. Execute a **copy** of the
notebook to leave the source unexecuted, then render with:

```sh
.venv/bin/python tracks/statement-forecast/scripts/render_results_page.py /tmp/sf_smoke/results
```

`write_outputs(results, out_dir, vintage_path, run_meta)` also accepts explicit paths. Metadata
includes UTC run start, git HEAD, pre-registration SHA and time, design hash, audits and fallback
counts. The notebook prints the three 2024+ quarterly lines for RSSD 1039502 as a sanity check.
