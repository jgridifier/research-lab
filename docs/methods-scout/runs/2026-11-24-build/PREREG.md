<!-- quant-scout-bot -->
# Pre-registration: picked-methods build steps, 2026-11-24

Written Tuesday 2026-11-24, about 2:50 PM ET, **before** the study below was run. Committed and merged before the run. Anything learned afterwards goes in a dated addendum at the end; the text above it is not edited.

## C2. codyn (#52), build step 2: share-space compensation test

**Why a new statistic.** The official Schluter variance ratio (VR) on shares is identically 0 because shares sum to 1 (the covariance matrix has a zero row-sum; verified 4.07e-17 on 2026-11-23). On raw volumes VR is dominated by a common market factor. The proposal: work on log-volume increments, remove each entity's loading on the cross-sectional mean increment (the market), and test the most negative pairwise residual correlation (the "compensation" statistic, `stat = min_{i<j} r_ij`) against a **no-wrap truncated shift null**: entity j's increment series is taken from rows k_j … k_j+L−1, with k_j uniform on 0…K, K = 8, L = (T−1)−K, so no series is wrapped around a trend. The observed statistic uses rows 0…L−1 (the all-zero shift, which is one member of the null set). p = (1 + #{null ≤ obs}) / (B + 1), B = 199. The min over pairs is a max-statistic, so the p-value already accounts for scanning all pairs.

**Design.** SYNTHETIC panels, T = 40 quarters (39 increments), S = 10 entities. Increment Δ_it = λ_i z_t + e_it; z_t AR(1) φ = 0.9 with innovation sd 0.10; λ_i ~ N(1, 0.3²); e_it AR(1) φ = 0.3 with innovation sd 0.15. S0 (null): as is. S1 (sticky swap): a shared AR(1) w_t, φ = 0.8, innovation sd 0.12, added to entity 0 and subtracted from entity 1. R = 1,000 panels per scenario. Seeds: `SeedSequence(20261124).spawn(2)` (S0 then S1). Reject at p ≤ 0.05.

**Comparators (reported, not scored).** (a) Official VR on shares for one S1 panel (expected ≈ 0). (b) Raw-volume VR (levels = exp of cumulated log increments) with the Hallett wrap null, reject when VR is below the lower 2.5% bound (compensation); its rejection rate under S0 and S1 at B = 199.

**Pass bars (from the build plan).** Size under S0 in [0.02, 0.08] (Monte Carlo 2 SE at R = 1,000 is about ±0.014); power under S1 ≥ 0.80. Official VR on shares ≈ 0 (< 1e-12).

**Kill rule.** If size lands outside the band, drop the share-space statistic from the library and ship raw-volume VR only, with that documented.

## C3. codyn, build step 3: speed by benchmark

Not a study. All metrics with 999-draw nulls on a SYNTHETIC 2,000-entity × 40-period panel: NumPy (the current port), plus Numba and Rust only if NumPy exceeds the bar. Bar: ≤ 5 s on 4 vCPU (the box has 8 vCPU; the run is pinned to 4 threads with `taskset`). Rust is kept only if it is ≥ 5× faster than the best Python path. Median of 3, timings committed.
