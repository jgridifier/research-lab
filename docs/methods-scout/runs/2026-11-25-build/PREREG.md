<!-- quant-scout-bot -->
# Pre-registration: picked-methods build steps and scheduled scout, 2026-11-25

Written Wednesday 2026-11-25, about 2:25 PM ET, **before** any study below was run. Committed and merged before the runs. Anything learned afterwards goes in a dated addendum at the end; the text above it is not edited.

Picked methods exist (feedback-state.json: codyn #52, ebnm #55, DenseLines #56 approved; Lovell #53, pim #63 in progress; ecotraj #50 excluded), so today scouts ONE new method and spends the rest on build plans, oldest-approved first. Remaining steps for codyn (4–5), DenseLines (4 remainder, 5) need the library repos (engineering tickets #96, #95 open, repos not created), so today runs the parts that can be finished and verified without a repo. ebnm #55 step 3 (flag test) missed one calibration bin on 2026-11-23 with the kill rule not triggered; it is not re-run today (no re-run to chase a bar).

All build-step data are SYNTHETIC unless stated. Timings are pinned to 4 vCPU with `taskset -c 0-3` (the box has 8), median of 3, thread pools set to 4.

## C4. codyn (#52), build step 4 input: minimum T for the raw-volume variance ratio (VR) test, and the trend warning

**Why.** Step 2 dropped the share-space VR (kill rule), so the library ships raw-volume VR with the Hallett cyclic-shift (wrap) null. Step 4's judging layer needs (a) the minimum number of periods T for useful power and (b) evidence for the "trending series under a wrapping null" warning.

**Design.** S = 10 entities, T ∈ {10, 15, 20, 30, 40, 62}. Levels X_it = 10 + e_it + c_i a w_t, with e_it AR(1) φ = 0.3, unit stationary sd; w_t AR(1) φ = 0.3, unit stationary sd, shared within each of 5 fixed pairs (entities 2k, 2k+1), c = +1 for the first and −1 for the second member (compensation). Scenarios: S0 null a = 0; S1 compensation a ∈ {0.5, 1.0}; S2 null plus a linear trend b_i t/T with b_i ~ N(0, 1.5²) (random-sign trends, no compensation); S3 null plus a common trend 1.5 t/T for all entities (synchrony by trend). Test: VR from `codynport.variance_ratio`; null from `codynport.variance_ratio_null`, B = 199. Compensation is declared when VR < the null's 2.5% quantile; synchrony when VR > the 97.5% quantile. R = 500 panels per (scenario, T). Seeds: `SeedSequence(20261125).spawn` in the order S0, S1(0.5), S1(1.0), S2, S3, T inner.

**Outputs and bars.** Size (either tail) under S0 in [0.02, 0.08] at each T; minimum T with power ≥ 0.80 for compensation at a = 1.0 and a = 0.5 (the published minimum-T table). Trend warning: if the either-tail rejection rate under S2 or S3 exceeds 0.10 at any T ≥ 20, the library's `diagnostics()` must warn when a linear trend explains ≥ 50% of the variance of the median entity (rule written now; the R² threshold is checked by reporting the median trend R² in S2/S3). Kill: if S0 size is outside the band at T ≥ 20, the VR test ships with "descriptive only" in HOW_TO_JUDGE.md.

## L2. Lovell proportionality (#53), build step 2: pick the backend by benchmark

**What is timed.** The full default pipeline of `proprlite` on a SYNTHETIC composition: `partial_increment(S, X)` (exact market proxy), then ρ for all pairs, the exact two-sided cyclic-shift p for every pair (shifts 4 … n−4 of the 61 increments, as `cyclic_shift_pvalue`), and BH q over all pairs. Sizes D = 500 (124,750 pairs) and D = 5,000 (12,497,500 pairs), T = 62. Data: log-normal compositions, one market factor, seed 20261125.

**Backends.** (a) NumPy: every shift as one matrix product over all pairs (BLAS), counts accumulated in place; (b) Numba `prange` over pairs. Rust is built only if neither Python path meets the bars, or if (b) is more than 2× faster than (a) at 5,000 parts (then a Rust loop could plausibly reach 5×); otherwise the reason it is not built is recorded.

**Bars (from the build plan).** < 0.1 s at 500 × 62 and < 3 s at 5,000 × 62, peak RSS < 4 GB. Parity: on 200 random pairs at D = 500, ρ within 1e-12 of `proprlite.rho_vec` and p identical to `cyclic_shift_pvalue`. Timings committed.

## P2. pim (#63), build step 2: pick the backend by benchmark

**What is timed.** 10,000 within-year permutation refits of the joint logit PIM (difference model) on the 2026-11-17 panel (360 rows, 5,017 pairs; `q3_pim_panel.csv` rows from `oracle.json['perm_rows']`, covariates drawdown and pre-tax income rate). Backends: (a) NumPy batched Newton (`pimfast.perm_fit`); (b) Numba: per-permutation Newton, closed-form 2 × 2 solve, `prange` over permutations, permutations supplied as index arrays so the draws equal (a)'s; (c) the existing Rust/rayon binary (`pimperm-rs`, `RAYON_NUM_THREADS=4`).

**Bars (from the build plan).** ≤ 2.0 s median of 3 on 4 vCPU. Keep Rust only if it is ≥ 5× faster than the best Python path. Parity: (b) vs (a) on the same permutations max |Δβ| ≤ 1e-10; (c) vs the scalar `fit` on its own first 50 permutations ≤ 1e-10. Timings written to `pim/bench_results.json` beside pim's ~75 s extrapolation.

---

# New method: extreme deconvolution (XD; Bovy, Hogg & Roweis 2011, astrophysics), Q2

**Rotation.** Q2 was last targeted on 2026-11-22 (Q3 on 11-23, Q1 on 11-24), so today targets Q2.

**Method.** A Gaussian mixture for the *underlying* (noise-free) distribution, fitted to points that each carry their own known noise covariance S_i and their own missing dimensions (projection R_i): x_i ~ Σ_j α_j N(R_i m_j, R_i V_j R_iᵀ + S_i), by EM (Bovy et al. 2011, AOAS 5(2B):1657–1677). Oracle: Bovy's C library (github.com/jobovy/extreme-deconvolution, BSD-3, built on the box against GSL). Our implementation: independent NumPy.

**Data (SYNTHETIC only).** The Q2 mock ZBB books, seed 20261113 (published mocks; observable features from the 2026-11-13 prep, `/workspace/scout/1113/data`) and the seed-20261123 regeneration (`/workspace/scout/1123-build/data`) as a replicate. Answer-key files are used only for scoring. x_i = year-on-year changes in log actual spend (Corning-like: FY2021–25, 5 dims; MS-like: FY2022–25, 4 dims); a missing year makes its adjacent changes missing dims (projection). Programs need ≥ 2 observed changes. Noise: actual = true × exp(ε), so each change has variance 2σ̂_i² and adjacent changes covariance −σ̂_i² (MA(1)); σ̂_i is the 2026-11-13 observable estimate from budget–actual gaps (README noise ratio 0.70, shrunk to the segment × function median). No program row is published.

**Fitting.** K ∈ 1…10, 5 starts (k-means++ on complete cases, seeds 20261125+r), EM to relative log-likelihood change < 1e-7 or 2,000 iterations, covariance floor w = 1e-6 · I; K by BIC (p = K−1 + K·D + K·D(D+1)/2). The standard comparator is a plain Gaussian mixture (sklearn `GaussianMixture`, full covariance, same starts, K by BIC) on complete-case programs, plus k-means with XD's K.

**A1 Home-field reproduction (SYNTHETIC).** (i) Parity: our EM vs Bovy's C from identical initial parameters on a 2-D, 3-component SYNTHETIC set (n = 2,000, heteroscedastic noise, 20% of points missing one dimension): final average log-likelihood within 1e-8 and parameters within 1e-6 after the same number of iterations (fixed 500 iterations, no tolerance stop). Also run the C package's own `tests/` with our build. (ii) The paper's central claim — the fit recovers the underlying distribution, while a mixture fitted to the noisy points is broadened by noise — on 20 SYNTHETIC replicates (3 components in 2-D, per-point noise sd uniform in [0.2, 1.0] × component scale): Monte-Carlo KL(truth ‖ fit) for XD vs GaussianMixture with the same K; pass if XD's KL is lower in ≥ 18 of 20.

**A2 Q2.4 structure (the question analysis).** Planted groups: each co-moving cluster, and each sign side of each trade-off cluster, with ≥ 15 members among the scored programs. Score: best F1 over components (MAP assignment) per group. Primary comparison on the common complete-case set; secondary on all programs XD can score (GMM's excluded programs count as unassigned). Promising if XD's best-F1 beats the GMM's by ≥ 0.05 on at least half of the groups pooled over both books (seed 20261113), with the same direction on most groups in the replicate.

**A3 Q2.3 real change vs noise.** (a) Noise share of the spread in program growth: 1 − tr(Σ̂_underlying) / tr(Cov(x)) on complete cases, against the answer key's 1 − tr(Cov(true changes)) / tr(Cov(x)). Pass: within ±5 points on both books. (b) Per-program denoised last-year change (XD posterior mean of the last dimension) vs true last-year change: RMSE for raw x, ebnm ash (1-D, s = √2σ̂, mode at the cross-sectional median; `ebnmport`), and XD. XD counts as better only if its RMSE is ≥ 3% below ebnm's on both books.

**A4 Nulls.** (i) Clusters off: each program's years shuffled within program (levels permuted, changes recomputed), 20 shuffles: BIC K and best-F1 for the planted groups; observed must exceed the 95th percentile of the shuffle best-F1 for a group to count as found. (ii) Noise only: x_i replaced by pure simulated noise with each program's S_i and the observed missing pattern: XD must report tr(Σ̂_underlying) < 10% of the mean tr(S_i) and BIC K = 1; the GMM's answer is reported.

**A5 Stability.** Corning-like book, early window FY2021–23 changes vs late window FY2023–25 (3 dims each): ARI between the two windows' component assignments on common programs, for XD and the GMM; and replicate-seed agreement of the A2/A3 numbers.

**B Walk-forward benchmark (low priority, standing rule).** Target: each program's FY2025 change in log actual, using data through FY2024 only. Models: no change; per-program OLS trend; pooled ARDL(1) (Δy_t on Δy_{t−1}, pooled, OLS); per-program SARIMAX(1,0,0) with constant on the changes (fallback to the pooled ARDL forecast if it fails); SARIMAX(1,0,0)+X with X = the prior-year mean change of the program's stated function; XD: fit on all stacked 3-change windows observable through FY2024, then the conditional mean of the third change given the two latest observed (FY2023, FY2024), using the noisy-data mixture (V_j + S_i). Scored against the observed FY2025 change and against the true change. Promising if XD's RMSE is ≥ 3% below the best other model with a paired test on squared-error differences p < 0.10, on both books.

**E Speed.** Our NumPy EM vs Bovy's C (OpenMP, 4 threads) vs astroML `XDGMM`, n = 1,800, D = 5, K = 6, 200 fixed iterations, and n = 100,000 (our implementation and C only). Median of 3. Parity of final log-likelihood reported.

**Visual.** Standard: GaussianMixture ellipses on the noisy FY2024 × FY2025 changes. Method: XD underlying ellipses with the deconvolved posterior means, same axes.

No neural nets. No real budgets exist; nothing here is a real firm's data.
