# FR Y-9C panel: next-quarter net interest income

Independent research lab · Not affiliated with any employer or financial institution · Not investment advice.

Run from the repository root with Python 3.13, venv/pip, GNU make, and network access:

```sh
make y9c
```

`make y9c-data` is the standalone one command for download + build, including environment setup in a fresh clone. A `.venv/.y9c-requirements.stamp` dependency installs packages once and refreshes them when `requirements.txt` changes. Data, notebook, page and test targets all depend on it.

`make y9c` runs dependency installation, NIC downloads and panel construction, notebook execution, and static results rendering in order. Individual steps:

```sh
make y9c-venv
make y9c-data
make y9c-test
make y9c-notebook
make y9c-page
```

Dependencies (including transitives) are pinned to the versions installed in the repository `.venv`. The notebook kernel is registered under `.venv` and execution uses `.venv/bin/jupyter`. Paths resolve relative to the repository, so execution works from either its root or the notebook directory. No reference-workspace imports are needed.

## Source and reproducibility

[NIC Financial Data Download](https://www.ffiec.gov/npw/FinancialReport/FinancialDataDownload) provides `BHCFYYYYMMDD.zip` at:

```
https://www.ffiec.gov/npw/FinancialReport/ReturnBHCFZipFiles?zipfilename=BHCF{YYYYMMDD}.zip
```

`make y9c-data` requests every quarter from 2018Q1 through the latest quarter-end on or before the execution date. ZIPs with PK magic, a text member, and valid CRCs are reused. Real downloads use a `.partial` file and atomic rename, one-second spacing, and up to three attempts for transient failures. Redirects are not followed. Required-quarter failures stop the command with status, content type, first bytes, URL, and manual fallback instructions. Only the single most recent quarter-end can be unavailable, and only when less than 100 days old. No data are fabricated. To unblock a failed quarter, download the named ZIP using the NIC page and put it in `tracks/y9c-panel/data/raw/`, then rerun `make y9c-data`.

`data/raw/manifest.json` records quarter, URL, bytes, SHA-256 and download time. Pre-existing cache files have a first-seen timestamp, not an invented download date; unchanged files retain their provenance on rerun. Filings can be revised: cached bytes give a reproducible local vintage, but a fresh download later may differ. Delete a specific cached ZIP only when intentionally requesting a new vintage. The page records build time and all download/cache dates. Build timestamps change on each rerun; cached inputs and numerical results stay the same.

## Panel and units

Each ZIP contains one Latin-1, caret-delimited text file. Parsing uses `QUOTE_NONE`; empty strings and `--------` are missing. An optional second description row is skipped only when its RSSD field is not numeric. Malformed rows, inconsistent report dates, or duplicate RSSD/date keys fail clearly.

The small `core_items.yaml` corrects the reference's mislabeled income fields: **BHCK4074 is net interest income**, BHCK4107 is total interest income, and BHCK4073 is total interest expense. Other unused income codes are omitted. All monetary values are **thousands of USD**. For example 25,000,000 thousand USD equals $25 billion.

YTD flow de-cumulation is by RSSD ID and calendar year: Q1 equals reported YTD; Q2–Q4 equal current YTD minus immediately prior-quarter YTD. Both the prior row and its value must exist. Missing predecessors produce NaN, never imputation or subtraction over gaps. Negative quarterly changes are retained. Coverage and vintage metadata count negative Q2–Q4 NII de-cumulations (`negative_nii_decumulations`) and the subset where every earlier quarter in the same year is observed and positive (`negative_nii_after_positive`). For the 2018Q1–2026Q2 vintage, there are 36 negative Q2–Q4 de-cumulations, including 6 after all earlier quarters that year were observed and positive. These checks do not change or exclude observations. For BNP Paribas USA, reported YTD NII falls from 1,910,303 in 2021Q3 to 192,866 in 2021Q4, implying −1,717,437 thousand USD quarterly NII. This is consistent with a within-year consolidation-scope change or restated YTD; the diagnostic alone does not establish the cause. We retain reported values as-is. The builder prints JPMorgan RSSD 1039502 NII, verifies complete-year quarterly sums against Q4 YTD, and checks 4107−4073=4074 across comparable records (tolerance one thousand USD). The notebook repeats these checks.

Runtime outputs under `data/processed/`:

- `panel_long.parquet`: RSSD/date/item, reported value and quarterly value for flows (stocks have no quarterly-flow value).
- `panel_wide.parquet`: one RSSD/date row with name, assets, NII YTD/quarterly and other mapped values.
- `coverage.csv`: raw records, consolidated-asset filers, NII availability, missing-prior de-cumulation counts and top-50 asset cutoff by quarter.
- `vintage.json`: quarter range/list, manifest provenance, build timestamp, filer counts and sanity checks.

Bulk files contain other records with empty consolidated Y-9C fields. All raw RSSD/date rows remain in the panel; coverage's `n_bhcs` counts records with BHCK2170 assets, and `n_raw_records` includes all records. Flow-drop counts describe unavailable quarterly values; they do not delete entire panel rows.

## One fixed forecasting exercise

Target: next-quarter de-cumulated BHCK4074 NII. At each origin t, rank reported assets at t and select the top 50 (RSSD ID breaks ties). Historical training rows use the same top-50 rule at their own origin. Test targets are fixed a priori at **2022Q1 through the latest available quarter**, with roughly 3.5 initial years reserved for burn-in. No tuning on test data.

Methods: naive y(t), seasonal naive y(t−3), and expanding pooled OLS on log growth:

```
g(s) = log y(s) - log y(s-1)
g(s+1) = a + b1*g(s) + b4*g(s-3)
yhat(t+1) = y(t) * exp(ghat(t+1))
```

At each origin t, historical training targets obey s+1≤t, and all required log inputs must be positive. The model uses `numpy.linalg.lstsq` with an intercept and no weights, clipping or regularization. Nonpositive or missing prediction inputs cause a naive fallback, counted among evaluated cases. Calendar-key lookups prevent lag calculations from bridging gaps.

Evaluation intersects the cases available to all methods: observed target, current NII and seasonal NII. Report disjoint missing-target and then missing-history drops, plus AR fallbacks. Missing targets include exit/merger cases but do not establish their cause. MAE and RMSE use thousands USD; MAPE is mean absolute error divided by absolute actual NII, multiplied by 100. Zero actuals are excluded from MAPE and supplementary MdAPE and counted. Negative NII is retained in level metrics but cannot enter log-growth training. Losses are equally weighted by BHC-quarter. Output overall and by-target-year results and metric winners exactly as observed, including baseline wins. The final year can be partial.

**MdAPE (median absolute percentage error, %): supplementary, added after observing MAPE outliers; does not replace MAPE.** It uses the same percentage-error cases and absolute-actual denominator as MAPE, with winners reported separately overall and by year. MAE, RMSE, MAPE, their winners, the models and evaluation cases remain unchanged. A few foreign-bank IHCs with near-zero/negative NII dominate MAPE; there are 10 nonpositive actuals among the current 893 cases. The notebook displays the ten largest naive absolute-percentage-error cases with bank name, target quarter, actual and forecast (thousands USD), and APE (%). That per-bank diagnostic is not exported to the results page or tables.

This is a report-quarter backtest, not a real-time release-date/vintage backtest: period-t filings are treated as available at t, and downloaded filings may include revisions. Timing and revision limitations remain even though universe selection and model fitting use no future report-quarter observations.

## Entry, exit, mergers and coverage

The panel follows RSSD IDs as reported, without pro-forma merger adjustment. Entrants appear when they start filing and require history for evaluation. Exiters' history stays in training, but they are not forecast after their last filing. A forecast at their final filing is dropped if the next-quarter target is unavailable. Acquirers' NII jumps remain and appear as forecast errors.

The 2018Q3 reporting threshold increased from $1 billion to $3 billion, mostly affecting small filers. Foreign-bank intermediate holding companies file Y-9C and can be in the top 50. Parent/subsidiary filers are not consolidated across RSSD IDs. The aggregate figure sums the evaluated sample, not a non-overlapping sector total; sample composition changes by quarter.

Only PNG figures, aggregate error tables (CSV and JSON), test design metadata, vintage metadata and generated HTML go to `docs/tracks/y9c-panel/results/`. No per-BHC data, forecasts or panels are exported there. The executed notebook includes the JPMorgan sanity output and ten-case naive percentage-error diagnostic; other institution-level forecast rows stay in memory. ZIPs, TXT files, parquet panels and all runtime data are gitignored.
