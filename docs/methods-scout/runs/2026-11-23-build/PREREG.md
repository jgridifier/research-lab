<!-- quant-scout-bot -->
# Pre-registration: picked-methods build steps, 2026-11-23

Written Monday 2026-11-23, about 2:35 PM ET, **before** any of the studies below were run. Committed and merged before the runs. Anything learned afterwards goes in a dated addendum at the end; the text above it is not edited.

Scope: build-plan steps that are studies (they can fail). Parity and benchmark steps are not studies; their pass bars are already fixed in `feedback-state.json` and are reported as measured.

## L3. Lovell proportionality (#53), build step 3: size, power and proxy-noise study

**Question.** Is the market-partial increment ρ (`partial_increment`, the proposed library default) size-correct with an exact market proxy, how short can the panel be, and how much proxy noise can it take?

**Design.** Reuse `runs/2026-11-17/lovell/sim_partial.py` unchanged in its data-generating process: D = 14 parts, market factor z ~ AR(1) φ = 0.9, loadings λ ~ N(0, 0.25²) with λ₀ = 0.5, λ₁ = −0.5, idiosyncratic AR(1) φ = 0.8 sd 0.15, three AR(1) nuisance regressors. S0 = no extra link between parts 0 and 1 (null). S1 = shared AR(1) shock w (sd 0.15) added to part 0 and subtracted from part 1 (alternative). Test: exact two-sided cyclic-shift p (smin = 4), reject at p ≤ 0.05. Methods reported: Raw clr ρ, partial_level (PL), partial_increment (PI).

Grid: T ∈ {20, 30, 40, 62} × proxy ∈ {exact, noise 0.10, 0.25, 0.50 × sd(z)} × {S0, S1}. 32 cells, R = 1,000 replications each. Seeds: `SeedSequence(20261123).spawn(32)` in that cell order (T outer, then proxy, then scenario).

**Known before running.** At T = 20 the cyclic null has 13 shifts, so the smallest attainable p is 1/14 = 0.071 > 0.05: rejection rate is exactly 0 at T = 20 by construction (computed). At T = 30 the smallest p is 1/24 = 0.042.

**Pass bars (from the build plan).**
- With an exact proxy, PI size in [0.02, 0.08] at T = 40 and at T = 62, and PI power ≥ 0.80 at T = 62.
- Published: a **minimum-T table** = the smallest T in the grid where exact-proxy PI size is in [0.02, 0.08] **and** power ≥ 0.80; and, for each T, the **largest proxy noise** in {0, 0.10, 0.25, 0.50} whose PI size is ≤ 0.08.
- Monte Carlo error at R = 1,000 near 0.05 is about ±0.014 (2 SE, computed); no re-runs to chase a band edge.

**Kill rule.** If exact-proxy PI size is outside [0.02, 0.08] at T = 40 or T = 62, `partial_increment` stops being the default and the README says why.

## E3. ebnm (#55), build step 3: the "is this move real?" flag test

**Data.** Both SYNTHETIC Q2 mock ZBB datasets regenerated with a **new seed, 20261123**, by importing `generate_q2_mock_zbb.py` and overriding its `SEED` constant only (no other change), then building observable features with the 2026-11-13 `prep.py` logic. Ground truth is used only for scoring.

**Procedure.** For programs with actuals in both of the last two fiscal years: x = Δlog actual (last year minus the year before), s = √2·σ̂ (σ̂ = the shrunk per-program noise SD from prep). Fit ebnm with the ash prior (scale mixture of normals, mode fixed at 0) with the research port `ebnmport.py` (exact KL-bound grid); cross-check the fit against R ebnm 1.1.42 on the same inputs and report the log-likelihood gap. Flag a program when lfsr < 0.05. Comparator: two-sided z-test p = 2Φ(−|x/s|) with Benjamini–Hochberg at q = 0.05.

**Metrics.** Wrong-sign rate among flags = share of flagged programs where sign(posterior mean) ≠ sign(true Δlog). BH calls = number of BH rejections. Calibration: bins of lfsr (0, 0.01], (0.01, 0.05], (0.05, 0.2], (0.2, 0.5]; in each bin with ≥ 20 programs, |realised wrong-sign rate − mean lfsr| (bins with fewer than 20 programs are reported, not scored). All-zero-effect mock: keep each mock's x-generating noise but set every true change to zero, i.e. x = s·ε with ε ~ N(0, 1), seed 20261123; false-flag rate = share of programs flagged.

**Pass bars (from the build plan).** On both mocks: wrong-sign rate ≤ 5% among flags; flags ≥ 3 × BH calls; calibration within ±5 points in every scored bin. On the all-zero-effect version of each mock: false flags ≤ 5%.

**Kill rule.** If the wrong-sign rate is > 5% on either mock, the flag ships off by default with a warning; shrinkage still ships.
