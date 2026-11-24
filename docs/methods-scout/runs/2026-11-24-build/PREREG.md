<!-- quant-scout-bot -->
# Pre-registration: picked-methods build steps, 2026-11-24

Written Tuesday 2026-11-24, about 2:27 PM ET, **before** the study below was run. Committed and merged before the run. Anything learned afterwards goes in a dated addendum at the end; the text above it is not edited.

## C2. codyn (#52), build step 2: share-space compensation test

**Why a new statistic.** The official Schluter variance ratio (VR) on shares is identically 0 because shares sum to 1 (the covariance matrix has a zero row-sum; verified 4.07e-17 on 2026-11-23). On raw volumes VR is dominated by a common market factor. The proposal: work on log-volume increments, remove each entity's loading on the cross-sectional mean increment (the market), and test the most negative pairwise residual correlation (the "compensation" statistic, `stat = min_{i<j} r_ij`) against a **no-wrap truncated shift null**: entity j's increment series is taken from rows k_j … k_j+L−1, with k_j uniform on 0…K, K = 8, L = (T−1)−K, so no series is wrapped around a trend. The observed statistic uses rows 0…L−1 (the all-zero shift, which is one member of the null set). p = (1 + #{null ≤ obs}) / (B + 1), B = 199. The min over pairs is a max-statistic, so the p-value already accounts for scanning all pairs.

**Design.** SYNTHETIC panels, T = 40 quarters (39 increments), S = 10 entities. Increment Δ_it = λ_i z_t + e_it; z_t AR(1) φ = 0.9 with innovation sd 0.10; λ_i ~ N(1, 0.3²); e_it AR(1) φ = 0.3 with innovation sd 0.15. S0 (null): as is. S1 (sticky swap): a shared AR(1) w_t, φ = 0.8, innovation sd 0.12, added to entity 0 and subtracted from entity 1. R = 1,000 panels per scenario. Seeds: `SeedSequence(20261124).spawn(2)` (S0 then S1). Reject at p ≤ 0.05.

**Comparators (reported, not scored).** (a) Official VR on shares for one S1 panel (expected ≈ 0). (b) Raw-volume VR (levels = exp of cumulated log increments) with the Hallett wrap null, reject when VR is below the lower 2.5% bound (compensation); its rejection rate under S0 and S1 at B = 199.

**Pass bars (from the build plan).** Size under S0 in [0.02, 0.08] (Monte Carlo 2 SE at R = 1,000 is about ±0.014); power under S1 ≥ 0.80. Official VR on shares ≈ 0 (< 1e-12).

**Kill rule.** If size lands outside the band, drop the share-space statistic from the library and ship raw-volume VR only, with that documented.

## C3. codyn, build step 3: speed by benchmark

Not a study. All metrics with 999-draw nulls on a SYNTHETIC 2,000-entity × 40-period panel: NumPy (the current port), plus Numba and Rust only if NumPy exceeds the bar. Bar: ≤ 5 s on 4 vCPU (the box has 8 vCPU; the run is pinned to 4 threads with `taskset`). Rust is kept only if it is ≥ 5× faster than the best Python path. Median of 3, timings committed.

---

# Pre-registration: scheduled methods scout 2026-11-24 (written about 2:28 PM ET, before any run of the new method on our data)

Rotation: Q1 and Q2 were last targeted 2026-11-22, Q3 on 2026-11-23; Q1 is chosen because its core sub-question (who leads, and does it disconnect in stress) is exactly what the new method answers, and the real public series are on the box. Picked methods exist (feedback-state.json), so today scouts ONE new method. (Clock times in this file were corrected from the box clock before merge.)

## Method — Phase Slope Index (PSI) with segment-jackknife standardisation (Nolte et al. 2008; EEG / neuroscience), Q1
Home field: EEG effective connectivity (Nolte, Ziehe, Nikulin, Schlögl, Krämer, Brismar, Müller, PRL 100:234101, 2008, arXiv:0712.2352). Implementation oracle: `mne-connectivity` 0.9.0 `phase_slope_index`; independent NumPy implementation for our use.
Statistic: Ψ_ij = Im Σ_{f∈F} C*_ij(f) C_ij(f+δf), C = coherency from segment-averaged cross-spectra; z = Ψ / jackknife-sd over segments (|z| > 2 is the paper's rule). Positive Ψ: i leads j.

Data (public aggregates, lab copies on the box, no private rows): weekly 2018-05-09..2025-12-31 (/workspace/ms-1114/q1/weekly.csv): fails to deliver (UST ex-TIPS financing fails, `fails_fin_ust`), DVP outstanding (`dvp_out`), tri-party volume (`tri_tvol`). Monthly 2013-01..2025-12 (/workspace/ms-1114/q1/monthly.csv): Form PF 8.27 prime-broker borrowing (`Secured_Prime Broker`), reverse repo (`Secured_Reverse Repo`), plus monthly means of fails, tri-party volume, DVP outstanding where available. Transform: log first difference (weekly log change; monthly log change), standardised. Segments: weekly 52 weeks, 50% overlap, Hann; monthly 24 months, 50% overlap, Hann. Band F: weekly periods 4–26 weeks; monthly periods 4–12 months (stated before looking).

Pairs: W1 fails × DVP outstanding; W2 fails × tri-party volume; W3 DVP outstanding × tri-party volume; M1 PB × fails; M2 PB × reverse repo; M3 PB × DVP outstanding (2018-05+ only), M4 PB × tri-party volume (2014-08+). Multiplicity: Holm over the 7 pairs on the jackknife-z two-sided normal p.

Analyses (all computed, none run yet):
- A1 Home-field reproduction (SYNTHETIC): (i) our NumPy PSI equals `mne-connectivity` PSI to ≤ 1e-8 on 20 random pairs; (ii) Nolte-style simulation, y2(t) = 0.8 y1(t−τ) + noise, τ = 2 samples, N = 5,000, plus a random mixture of two independent sources: PSI direction correct in ≥ 95% of 200 sims for the coupled case; PSI mixture-of-independent false-significance (|z| > 2) ≤ 10%; statsmodels Granger (lag 4, F-test p < 0.05 either direction) false-significance on the mixture, reported (paper's claim: high).
- A2 Q1 analysis: Ψ, z and Holm p for the 7 pairs, plus the standard toolkit's answer for each pair: Granger F-test p (both directions, lag chosen by AIC ≤ 8) and the cross-correlation peak lag with Bartlett band. Report where they disagree.
- A3 Stability and stress: first vs second half sign and z for each pair; rolling PSI (weekly: 104-week windows, step 13 weeks; monthly: 60-month windows, step 6) drawn as a lead-lag strip chart (our graph) vs the standard rolling correlation line. Stress windows named in advance: 2020-02..2020-05 (weekly pairs only).
- A4 Size on our sampling (matched persistence): for W1 and M2, 1,000 pairs of independent AR(p) series (p by BIC ≤ 4, fitted to each real series' log differences, innovations bootstrapped), and the same with one common instantaneous shock (corr 0.5) added to both. Rejection rate (|z| > 2) of PSI; of Granger (p < 0.05 in the stated direction i→j). Pass for the method: PSI size under both within [0.03, 0.08] (approximate; 1,000 sims; MC 2 SE about ±0.014). A surrogate p-value check: Holm-corrected observed pair results are reported only where the A4 size passes.
- B Benchmark (low priority, walk-forward): target monthly log change of PB borrowing, one step ahead, test 2019-01..2025-12, expanding window refit each month: mean (zero-change), OLS on lag-1 reverse-repo change, ARDL(own lags ≤ 3 by BIC + reverse repo lags 0..3 by BIC), SARIMAX(1,0,1), SARIMAX(1,0,1)+X (reverse repo lag 1), and PSI-gated: use the X model only if training-window PSI z (M2) is significant (|z| > 2) with reverse repo leading, else SARIMAX(1,0,1). Promising = PSI-gated RMSE ≥ 3% lower than the best of the other models with Diebold–Mariano p < 0.10; otherwise reported as not promising. Forecasting is low priority; this is included for the standing benchmark rule.
- E Engineering: NumPy PSI + 1,000-draw segment bootstrap vs `mne-connectivity` loop on 200 channel pairs × 10,000 samples; parity and wall time.

Visual: lead-lag strip chart (PSI by band and window, coloured by sign, hatched where |z| < 2) vs rolling correlation line (standard).
Pass bars: A1 (i)–(ii) as stated; A4 as stated. Kill/limit: if A4 size fails for a pair type, its observed z is reported as descriptive only. Y-9C is not used.

---

## Addendum 2 — written 2026-11-24, about 2:43 PM ET, before the D4 run; the text above is unchanged

## D4. DenseLines (#56), build step 4 input: a branch test with power (the dip test missed the planted clusters at p = 0.99 on 2026-11-23)

**Question.** What is the smallest number of series at which a test on the last-column residuals detects a branch planted in 10% of the series with power ≥ 0.80 while holding size ≤ 0.05, and does the Hartigan dip test or a two-component Gaussian-mixture likelihood-ratio test (LRT) do it?

**Design.** SYNTHETIC. T = 6 yearly points. Each series: yearly log changes iid N(0, 0.15²), series level removed (row-demeaned) and the column median removed as in `d3_truth.py::resid_last`. Branch: a random 10% of series get an extra drift per year after year 3 (years 4–6, three steps) of size d so that the expected separation of the branch mean from the main mean at the last column equals s standard deviations of the last-column residual of the main group (s ∈ {1.5, 2, 3}; d solved from the simulated sd of the null residual, computed once per N). N ∈ {50, 100, 200, 500, 1,000, 2,000}. R = 500 replications per (N, s) cell for power; 2,000 replications for the null (s = 0, no branch) per N. Seeds: `SeedSequence(20261124).spawn` in the order null, then s = 1.5, 2, 3, N outer.

**Tests.** (i) Hartigan dip test with the `diptest` package p-value, reject at p < 0.05. (ii) 2-vs-1 Gaussian mixture LRT (1-d EM, 6 random restarts, variance floor 1e-6 of the sample variance, minimum component weight 0.03), rejected when the LRT exceeds the 95% quantile of its null distribution at that N (the 2,000 null replications; the null is calibrated by simulation, not by the chi-square approximation).

**Pass bars.** Size of each test ≤ 0.07 at every N (null, 2,000 reps; Monte Carlo 2 SE about 0.01). A test is adopted for the library if its size passes and its power ≥ 0.80 at s = 2 for some N ≤ 2,000; the published table gives, per s, the smallest N with power ≥ 0.80. If neither test passes, the branch check ships off by default with the dip test's missing power documented.

**Not claimed.** The null is Gaussian by construction, so size on real heavy-tailed budget residuals is not tested here. The library's diagnostics()/null_test()/HOW_TO_JUDGE.md are engineering and are not part of this study.
