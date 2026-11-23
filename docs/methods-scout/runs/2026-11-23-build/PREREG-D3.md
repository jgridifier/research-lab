<!-- quant-scout-bot -->
# Pre-registration: DenseLines (#56) build step 3, "does it show truth better?"

Written Monday 2026-11-23, about 2:55 PM ET, **before** the study was run; committed and merged before the run. Results go in a dated addendum at the end; the text above it is not edited.

**Data.** Both SYNTHETIC Q2 mock ZBB datasets regenerated with seed **20261123** (generator `generate_q2_mock_zbb.py` with only its `SEED` constant overridden; features from the 2026-11-13 `prep.py` logic). These are the same regenerated mocks as the ebnm step-3 test (PREREG.md section E3). The answer key is used only for scoring.

**Charts.** Exactly the 2026-11-13 construction (`runs/2026-11-13/m2_denselines.py`): programs with ≥ 2 observed years; log actuals indexed to each program's own mean; canvas 500 × 300; y-range = 0.5th to 99.5th percentile ± 0.02; vertex x-positions spread evenly over the years; gap-safe DenseLines (normalised) vs the unnormalised chart (binary per-series images summed). The "truth" chart is built the same way from the answer-key true paths on the same observed years and y-range.

**Clusters on (the generator's planted clusters, unchanged).** Metric: mean over columns of the 1-D Wasserstein-1 distance (log units) between each noisy chart's column distribution and the truth chart's column distribution (`emd` in the 11-13 script). **Bar:** DenseLines W1 < unnormalised W1 on **both** mocks.

**Clusters off (years shuffled within program).** For each of 200 shuffles (seeds 20261123 + k, k = 0…199), permute each program's observed log actuals across its own observed years. Compute the residual R = (V − program mean) − column median, as in the 11-13 D2 branch brush, and run the Hartigan dip test (Python `diptest` 0.12.0, `diptest.diptest`, default p-value) on R in the last year for programs observed in that year. A branch is "flagged" when p < 0.05. **Bar:** flagged in ≤ 5% of the 200 shuffles (≤ 10), on each mock.

Reported but not scored: the same dip test on the unshuffled regenerated mocks (whether the planted clusters show as a branch), and the total-variation distance to truth.

**Kill rule (from the build plan).** If DenseLines fails to beat the unnormalised density on both mocks, the library ships it as a plotting utility with no judging claims.

## Addendum 1 — 2026-11-23, about 2:45 PM ET, written after the run; the text above is unchanged

Ran as written (`denselines/d3/d3_truth.py`, 4.6 s). **Clusters on:** W1 to the truth chart, DenseLines 0.0496 vs unnormalised 0.0524 (Corning mock) and 0.0359 vs 0.0370 (MS mock) — DenseLines closer on both: **pass**, by small margins (5% and 3%). **Clusters off:** 0 of 200 shuffles flagged on each mock (rate 0.0 ≤ 0.05): **pass**. Kill rule not triggered.

Read with care: the dip test also does **not** flag the unshuffled mocks with the planted clusters (p = 0.990 Corning, 0.994 MS). So this null has no power to see the planted clusters here; the "≤ 5% false branches" bar is met, but it tells us little. Build step 4 (judging layer) should not ship the last-year dip test as the branch test; its power study must choose a test that detects a branch planted in 10% of series.
