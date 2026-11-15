# Methods scout 2026-11-14 — run folder

Scheduled run of 2026-11-14 (America/New_York), interrupted that afternoon and **completed on 2026-11-15** at Jared's request.
Edition page: [../../2026-11-14.html](../../2026-11-14.html). Seed 20261114. R 4.5.3 (conda env `rscout`), crqa 2.1.0, isodistrreg 0.6.0.

## Q1 — CRQA (cross-recurrence quantification analysis)

- `prep_q1.py` — rebuilds the weekly panel from the lab's copies of the public files (NY Fed primary-dealer fails, OFR repo daily → Thu–Wed weekly means) and diffs it against the 11-14 `weekly.csv`. Fails and volumes match exactly; the DVP overnight rate differs by ≤ 0.6 bp on some days (final vs preliminary vintage).
- `q1/weekly_aggregates.csv`, `q1/monthly_aggregates.csv` — the public aggregate panels used (monthly Form PF columns are SEC Private Funds Statistics tab 8.27, $ billions).
- `q1/crqa_q1.R` — the 11-14 first pass (results kept as `q1/crqa_results_v1_2026-11-14.json`). Its windowed test used full-plot RR, which for categorical states depends only on state counts and is invariant to any shift, so the window null was degenerate (`q1/wincrqa_v1_degenerate_null.csv`, all p = 1). Not used on the page.
- `q1/crqa_q1_v3.R` — the completed run: weekly lag profiles (co and anti, 999 circular shifts), windowed order-dependent statistics (rr0 = same-week recurrence, DET; 199 within-window shifts), monthly Form PF profiles, timing. The 11-14 v2 attempt stalled under forked workers; v3 uses socket workers. Outputs: `q1/crqa_results_v3.json`, `q1/wincrqa_v3.csv`, `q1/sessionInfo_v3.txt`.
- `figs_q1.py` — figures 1–3.

## Q3 — IDR (isotonic distributional regression)

- `verify_y9c.py` — checks the five Y-9C HI-A items in the panel against the BHCF Q4 zips (exact match, 2013–2025).
- `verify_q3_panel.py` — checks stress-test rows against a fresh download of the Fed's `public_results_DFAST_2026.csv` (643/643 exact), rebuilds drawdown and pre-tax income, and checks 165 SCB values against the Large Bank Capital Requirements PDFs (0 mismatches).
- `q3/idr_q3.R` — rerun from scratch on 2026-11-15; every result equals the 11-14 partial output except run time. Outputs: `q3/idr_results.json`, `q3/idr_A1_quantiles.csv`, `q3/idr_A1raw_quantiles.csv`, `q3/sessionInfo.txt`.
- `figs_q3.py` — figures 4–6.
- Firm-year rows are not republished here; rebuild them from the public sources.

Paths inside the scripts point at the box working folder (`/workspace/ms-1114`). Descriptive work only; no forecasts; nothing touches the pre-registered Y-9C trading study.
