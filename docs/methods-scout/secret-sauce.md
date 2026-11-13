# Secret sauce plans

*Edition 1 · 2026-11-12 · America/New_York (EST), four already-scouted methods. Edition 2 · same day, ad hoc exotic scout: codyn and Lovell proportionality, grounded in [2026-11-12-adhoc](2026-11-12-adhoc.html). Edition 3 · scheduled 2026-11-12 scout (catch-up published 2026-11-13): ecotraj and lphom, grounded in [2026-11-12](2026-11-12.html). Plans only.*

This is a running file. Each daily methods scout should append plans for that day's methods in the same form. Edition 1 covers the four methods already scouted: changeforest and partykit ([2026-11-10](2026-11-10.html); [RESULTS](https://github.com/jgridifier/analysis-skills/blob/main/methods/changeforest/RESULTS.md) and [RESULTS](https://github.com/jgridifier/analysis-skills/blob/main/methods/partykit/RESULTS.md)) and MARSS and InspectChangepoint ([2026-11-11](2026-11-11.html), aimed at [Q1](QUESTIONS.md)). No new fits were run. Every number below is from those pages, their run JSON, or the RESULTS files. Nothing is being built, nothing is promoted, and no `APPROVAL.md` is written.

**Jared's ask (2026-11-11):** a plan for secret sauce that could make each package truly extraordinary, ranging from engineering (for example a faithful Python or Rust port of an R-only package, validated against the original as oracle for parity, then speed) to a full theoretical math modification.

**Format.** Each method has exactly three avenues, always in this order:

1. **Engineering** — port, speed, or scale (for example a Python or Rust port against an R oracle).
2. **Math** — a theoretical modification: a new estimator, null, or inference procedure.
3. **New use on our data** — a novel application or extension tied to a research question.

For each avenue: what it is in plain math, why it matters on our data (tied to a weakness we actually saw), the closest prior work with a real citation (or a clear statement that none was found), effort (S / M / L), and how we would test that it beats the original (a pre-registered metric plus a null). One avenue per method is the **top pick**. Effort: **S** is days, **M** is one to a few weeks, **L** is a substantial port or a paper-scale theoretical change.

**Forecasting is lower priority.** Jared's own model framework is at v2.1, and it moved past MARSS-style state-space models at v0.1. MARSS is treated here as a v0.1-era tool for *decomposing* sticky versus market-driven share and *visualizing* that split, not as a forecasting upgrade. Its three avenues stay off forecasting improvements. The other methods are also pointed at description, inference, and visualization rather than at beating a forecast baseline.

**Found via.** Each method has a "Found via" line: the channel, the exact link, and the date, taken only from the 11-10 and 11-11 scout pages, their run folders, and the watchlist. If a paper URL was not recorded, that is stated.

## Top picks

| Method | Top pick | One line |
|---|---|---|
| changeforest | **Math** | A block-permutation test of the classifier gain, so weekly breaks have to beat a dependence-aware null, not just an iid shuffle. |
| partykit | **Math** | Conditional-inference and MOB split tests that stay valid under serial dependence and persistent state variables. |
| MARSS | **Math** | A finite-sample test of "sticky vs slow mean reversion" that can label a single firm at 40 quarters, for the decomposition, not for a forecast. |
| InspectChangepoint | **Math** | A sparse-projection "who moved" procedure whose size is right under persistent (near-unit-root) share levels, or under a change in drift. |
| codyn | **Math** | A compositionally valid variance ratio in ilr (or clr) coordinates — official VR on shares is identically 0 — and a rank-shift null that does not wrap trending series. |
| Lovell proportionality (ρ) | **Math** | A formal partial-ρ given market factors, with a persistence-aware null whose size is demonstrated at 40 and 62 quarters. |
| ecotraj | **Math** | An increment-level market/residual trajectory split with a sign-flip test whose size is right — level residualization hid the sticky walk. |
| lphom | **New use** | Form ADV Schedule D filers as the voting units, so the transfer matrix can actually be identified. |

---

## changeforest

Londschien, Bühlmann & Kovács (2023), "Random Forests for Change Point Detection", *JMLR* 24(216):1–45. Rust core with Python and R bindings, v1.2.1. Scouted on [11-10](2026-11-10.html); three applications reproduced in analysis-skills, [RESULTS](https://github.com/jgridifier/analysis-skills/blob/main/methods/changeforest/RESULTS.md). Novelty: niche. Status: recommended, awaiting approval — not promoted.

**Found via.** PyPI and crates.io, seen 2026-11-10. Recorded links: [https://pypi.org/project/changeforest/](https://pypi.org/project/changeforest/), [https://crates.io/crates/changeforest](https://crates.io/crates/changeforest), and [https://github.com/mlondschien/changeforest](https://github.com/mlondschien/changeforest) (the watchlist's link). The 11-10 footer also records scanning the JMLR (2023) paper; an exact paper URL was not recorded. An X search that day is recorded as turning up only noise (the collision was with the name "partykit").

**What our runs showed.** The method finds volatility and correlation breaks that a mean-change test misses (0 mean breaks vs 35 distributional breaks on weekly changes; 28 daily breaks, including the 2022 stock–rate correlation flip). It scales well (9,174 × 4 daily rows in 1.2 s; 16,000 synthetic rows in 0.70 s) and returns 0 breaks on iid-shuffled data. The weakness is the independence assumption. On weekly *levels* it produced 63 breaks spaced about 27 weeks apart (an artifact). On weekly *changes*, a stationary VAR(1) null fitted to the data (spectral radius 0.957, no breaks by construction) still produced 20–37 breaks in 5 simulations — as many as the real data (35; 32–47 across seeds). A VAR(1) prewhitening remedy, already tested in RESULTS, left 22 breaks, 12 of which recurred in at least 8 of 10 seeds (including 2007-07, 2008-10, 2019-12, 2020-06, 2022-01), and 0–2 breaks on the same VAR null applied to residuals. Daily changes already pass that null (radius 0.50, 0 breaks in 3 simulations). Break counts are seed-sensitive; the skill lesson is to report only the multi-seed core. The package already has a Rust core, so the engineering avenue is not a port.

### Three avenues

| # | Avenue | Pitch | Effort | Headline test | Pick |
|---|---|---|---|---|---|
| 1 | Engineering | Bake persistence check, VAR(1) prewhitening, 10-seed consensus, and the VAR null into the crate as a first-class time-series mode. | M | Parity with the hand-rolled RESULTS (12 stable prewhitened breaks; 0–2 on the VAR null), then speed of that whole pipeline. | |
| 2 | Math | Replace the iid permutation test of the classifier gain with a block-permutation (dependence-aware) test, so a break has to beat residual autocorrelation, not just a shuffle. | L | On VAR(1) surrogates with radius 0.957 and no breaks, the false-break rate is near a pre-registered α (original: 20–37 breaks, as many as the real weekly series). | **Top** |
| 3 | New use on our data | Use the stable market-regime dates (including the 2022 correlation flip) to ask whether Q1 sticky-share increments cluster at those dates. | S | Mean absolute MARSS sticky increment in a window around those dates, versus a circular-shift null of the sticky series. | |

### 1 · Engineering: a first-class time-series mode in the crate

**What it is.** The original procedure, for a segment \((u,v]\) and a candidate split \(s\), fits a classifier labelling rows as left or right of \(s\) and keeps the split if a permutation test of the classifier log-likelihood-ratio gain \(G(s)\) rejects. The engineering sauce does not change \(G\). It makes mandatory, inside the crate, the pipeline we already had to hand-roll: (i) refuse to run on persistent levels; (ii) estimate a VAR(1) and, if the spectral radius is high, prewhiten; (iii) run 10 seeds and return only breaks that recur in at least 8 of 10; (iv) always report a stationary VAR(1) null (because the iid shuffle passed on weekly changes even where the VAR null failed). Meinshausen & Bühlmann (2010), *JRSS-B* 72(4):417–473, is the closest formal frame for the multi-seed core (stability selection); applying it to changeforest breaks is engineering, not new theory.

**Why it matters on our data.** Weekly changes failed the VAR null until we prewhitened by hand. Daily changes did not need it. A default that checks persistence and reports the consensus set would have stopped us from reading the raw 35 weekly breaks as a result. Seed sensitivity (32–47) was the reason the 11-10 verdict was "interesting" rather than adopt.

**Closest prior work.** Londschien, Bühlmann & Kovács (2023) already implement the forest, the gain, and an (iid) permutation step, in Rust. We did not find a first-class time-series mode that bundles prewhitening, multi-seed consensus, and a VAR null. Meinshausen & Bühlmann (2010) is the closest work on selection frequencies.

**Effort.** M.

**How we would test it.** Pre-registered parity, then speed. On the same weekly and daily panels (no new data), the pipeline must recover the RESULTS numbers: 12 prewhitened weekly breaks that recur in at least 8 of 10 seeds, 0–2 breaks on the VAR(1) residual null, and the same 28 daily default-seed dates with 0 VAR-null breaks. Timings are compared only after parity, on a stated machine, for "10 seeds + VAR null" versus the same steps in Python around the existing crate. The null is the same fitted VAR(1) (radius 0.957 weekly, 0.50 daily). This beats the original *package* by making the passing analysis the default, not by changing the estimator.

### 2 · Math: a block-permutation test of the gain (top pick)

**What it is.** The original permutation shuffles rows, which is valid only if rows are exchangeable. On weekly changes they are not (VAR radius 0.957). Prewhitening fixes the size empirically, but it changes the series: it looks for breaks in innovations, and can miss or move a break that is a change in the autoregressive structure itself. The math sauce keeps \(G(s)\) on the original (differenced) series and changes the *test*: split the series into blocks of length \(L\) long enough to cover the short-run dependence, permute whole blocks, and keep a split only if \(G(s)\) exceeds the \((1-\alpha)\) quantile of the block-permuted gains. That is Kirch's (2007) block-permutation idea, applied to the classifier gain rather than to a CUSUM. We would still not run on undifferenced near-unit-root levels (radius 0.997); block permutation is a short-range device, not a unit-root device.

**Why it matters on our data.** This is the headline weekly failure: 20–37 breaks on a no-break VAR(1) null, against 35 on the real data. The iid shuffle gave 0, and was the wrong null. A valid test on the original weekly changes would let us date volatility and correlation regimes without first stripping a VAR, and without taking 20–37 false breaks as the price.

**Closest prior work.** Kirch (2007), "Block permutation principles for the change analysis of dependent data", *Journal of Statistical Planning and Inference* 137:2453–2474, proves that block permutation yields the right critical values for CUSUM-type change-point statistics under linear-process dependence. Zeileis & Hothorn (2013), "A toolbox of permutation tests for structural change", *Statistical Papers* 54(4):931–954, discuss block permutations for structural-change tests and point to Kirch. We did not find a paper that applies block permutation to Londschien, Bühlmann & Kovács's classifier gain. Their 2023 theory is for (consistent) classifiers under the paper's assumptions, with a permutation step that, as they note, is not a fully exact permutation test.

**Effort.** L (the empirical wrapper is closer to M; a consistency proof for the block-permuted gain is L).

**How we would test it.** Pre-registered size and power, on the panels we already have, plus the same VAR(1) generator used in RESULTS. **Null (size):** 200 simulated weekly series from the fitted VAR(1) (radius 0.957, no breaks). The original method's break counts were 20–37 in 5 draws. The new test passes if the fraction of series with at least one break is at most a pre-registered \(\alpha\) (for example 0.10, Bonferroni-aware if we also look at daily). **Power:** on the real weekly changes, the test should still recover a pre-registered fraction (for example at least 8 of 12) of the stable prewhitened dates that RESULTS already trusts (2007-07, 2008-10, 2019-12, 2020-06, 2022-01, and the rest of that 12), at a stated tolerance (the 11-10 weekly tolerance was ±13 weeks). **Sanity:** on daily changes, where the original already has 0 VAR-null breaks, the new test must not invent a crop of breaks, and must keep a pre-registered fraction of the 23 daily breaks that recurred in at least 8 of 10 seeds.

### 3 · New use on our data: regime-timed sticky-share attribution, for Q1

**What it is.** changeforest says *when* a market distribution changed, not *what* share did. The 11-10 page already suggested pairing it with a MOB tree or with per-segment summaries. The new use, aimed at [Q1](QUESTIONS.md), is: take the stable daily and weekly market-regime dates (including the 2022 VIX–rate correlation flip, which both frequencies recovered) and test whether MARSS sticky-state increments from the 11-11 PROXY dealer-share panels cluster at those dates more than under a circular shift of the sticky series. In plain terms: if \(S_t\) is a dealer's smoothed sticky increment and \(\mathcal{B}\) is the set of market-break dates, compare \(\frac{1}{|\mathcal{B}|}\sum_{b\in\mathcal{B}} |S|\) in a small window around each \(b\) to the same statistic after circularly shifting \(S\). This uses only fitted structure already published (break dates and sticky-state paths). It is descriptive. The 11-11 panel overlaps a pre-registered Y-9C forecast window; this application would run none of that track's forecasts.

**Why it matters on our data.** Q1 asks whether share moves are market-driven or sticky. MARSS decomposed the PROXY shares; Inspect found no share *break* that cleared a persistence null (gradual drift, not shocks). The open question is whether the gradual sticky moves (foreign-IHC retreat; GS→JPM on equity revenue) line up with market-regime changes that changeforest *does* date cleanly, especially at daily frequency where the VAR null already passes. If they do not, that is evidence the sticky migration is not just "the market regime changed."

**Closest prior work.** We did not find a paper that uses classifier-based distributional regimes as event times for a compositional share decomposition. The two ingredients are the 2023 changeforest paper and the 11-11 MARSS decomposition (Holmes, Ward & Wills 2012, as used there). Circular-shift nulls for the sticky-increment correlations were already used on 11-11.

**Effort.** S (no new estimator; a short script on published aggregates and already-fitted states).

**How we would test it.** Pre-registered metric: for GS and JPM equity-revenue sticky increments (and, separately, for the foreign-IHC trading-asset group), the mean absolute increment in a ±1-quarter window around market-regime dates, versus 1,000 circular shifts of the sticky series (the same null family as 11-11). The result "beats a null of no alignment" if the real statistic is beyond a pre-registered tail (for example, one-sided \(p < 0.05\), BH-adjusted across the pre-registered pairs). A negative result is also a result, and would be reported as such. No forecast metric.

**Why Math is the top pick.** The package is already fast and already in Rust. The thing that changed what we believed on our weekly data was a failed dependence null. Making that null the *test*, not a post-hoc patch, is the extraordinary step.

---

## partykit (ctree and MOB)

Hothorn, Hornik & Zeileis (2006), "Unbiased Recursive Partitioning: A Conditional Inference Framework", *JCGS* 15(3):651–674; Zeileis, Hothorn & Hornik (2008), "Model-Based Recursive Partitioning", *JCGS* 17(2):492–514; Hothorn & Zeileis (2015), "partykit: A Modular Toolkit for Recursive Partytioning in R", *JMLR* 16:3905–3909. R package partykit 1.2-29, C core via libcoin. Scouted on [11-10](2026-11-10.html); three applications reproduced in analysis-skills, [RESULTS](https://github.com/jgridifier/analysis-skills/blob/main/methods/partykit/RESULTS.md). Novelty: well-known (less of a scout "diamond"). Status: recommended with a scoped skill, awaiting approval — not promoted. R-only.

**Found via.** CRAN, [https://cran.r-project.org/package=partykit](https://cran.r-project.org/package=partykit), seen 2026-11-10. The 11-10 footer records scanning "CRAN (partykit and Zeileis-group packages)" and the JCGS (2006, 2008) and JMLR (2015) papers; exact paper URLs were not recorded. An X search the same day "turned up only noise… because 'partykit' collides with an unrelated web framework."

**What our runs showed.** The trees are readable and fast (full-sample ctree in 25 ms; 300 block-bootstrap refits in 3.6 s; ctree 0.07 s on a 30,740-row replicated county table, lmtree 13.5 s). MOB is the best 11-10 result: one NFCI split at 0.057, the VIX→credit-spread slope roughly doubles (0.0293 → 0.0587), calendar time does not split (\(p = 0.83\)), and BIC improves from −350.5 (pooled) to −513.6. As a *forecaster* of 6-month spread changes, ctree lost to the historical mean (OOS \(R^2 = -0.31\)); we are not proposing to fix that, and forecasting is lower priority. The weakness that matters is inference on time series. ctree's permutation tests assume exchangeable rows. A circularly shifted response (keeps autocorrelation) still produced a tree split in 60% of 100 shifts. For MOB, circularly shifting the partitioning variables still produced a split in 53% of 100 shifts: the instability test is picking up volatility clustering that any persistent state variable can flag. The county cross-section is fine (iid-permuted response split in 0% and 4% of 50 permutations; the right null there).

### Three avenues

| # | Avenue | Pitch | Effort | Headline test | Pick |
|---|---|---|---|---|---|
| 1 | Engineering | A faithful Python or Rust port of ctree and MOB, with R partykit 1.2-29 as the oracle for parity, then speed. | L | Split variables, thresholds, leaf counts and MOB coefficients match the three 11-10 applications; then speed versus 3.6 s / 13.5 s in R. | |
| 2 | Math | Dependence-aware split tests: block-permutation linear statistics for ctree, and a fluctuation test for MOB that stays size-correct when the state variable is persistent. | L | Circular-shift false-split rate near a pre-registered α (original: 60% for ctree, 53% for MOB), while the county trees and the real NFCI MOB split still appear. | **Top** |
| 3 | New use on our data | MOB of Q1 dealer share–market loadings, partitioned by financial conditions, to see whether the market part of the share decomposition itself changes with NFCI or VIX. | S | A split that clears a circular-shift null of the partitioning variables, with a better description (for example BIC) than constant loadings. | |

### 1 · Engineering: a faithful Python or Rust port, R as oracle

**What it is.** The same estimators as the R package. For ctree, the linear association statistic \(T_j\) and the Strasser–Weber permutation moments \((\mu_j, \Sigma_j)\) that produce the quadratic form \(c_j\), computed today in C via libcoin; then a cut-point search on the selected variable. For MOB, a parametric model in each node and an M-fluctuation test of parameter instability along each partitioning variable (Zeileis 2005). The port is faithful if, on a frozen oracle (partykit 1.2-29, the 11-10 version), it reproduces splits, thresholds, leaf membership, and node coefficients to a pre-registered tolerance. Speed comes after parity. This is Jared's example of engineering sauce, and it is the right one here: partykit is R-only, and our TRACE-style stack is Rust with thin bindings.

**Why it matters on our data.** We already want 300-bootstrap stability tables as a matter of course (3.6 s in R, cheap enough nightly). A Rust libcoin-equivalent would make that, and MOB on larger panels, native in the same stack as changeforest. It also makes a future dependence-aware test (avenue 2) shippable in one place.

**Closest prior work.** The R package and libcoin are the oracle, not a prior port. A search for a Python or Rust implementation turned up packages that implement *related* permutation-based trees; we did not find a port with a documented parity suite against partykit on real panels. We are not treating any of those as a faithful oracle-tested port. Zeileis (2005) and Hothorn, Hornik & Zeileis (2006) are the math being ported.

**Effort.** L.

**How we would test it.** Pre-registered parity against R partykit 1.2-29 on the three 11-10 applications, using the same panels (byte-identical inputs were already used in analysis-skills). **Metric:** the same comparison used in RESULTS (default absolute tolerance \(10^{-4}\) on coefficients and p-values; exact match on split variable, threshold to the published rounding, leaf \(n\), and rules). Application 3's CV scores are allowed the same documented exception (fold assignment depends on the RNG stream). **Then speed:** 300 block-bootstrap refits of application 1, and lmtree on the 30,740-row replicated county table, on a stated machine, versus the recorded R times (3.6 s and 13.5 s). The port "beats" the original on speed only after parity is exact. The circular-shift null is not this avenue's test.

### 2 · Math: dependence-aware ctree and MOB split tests (top pick)

**What it is.** Two related changes, one per algorithm.

For ctree, replace the exchangeable-row Strasser–Weber permutation moments with a *block* permutation of the influence functions \(h(Y_i)\) (and, if needed, of the pairs \((X_i, Y_i)\)). The linear statistic \(T_j\) is unchanged; its null distribution is taken from block permutations that keep serial dependence inside blocks, in the sense of Kirch (2007) and of the structural-change permutation toolbox in Zeileis & Hothorn (2013). A split is declared only if this dependence-aware p-value clears \(\alpha\).

For MOB, there are two layers, and we should not pretend they are the same. (i) Serially correlated *scores*: partykit can take a sandwich / clustered covariance for the M-fluctuation test (Zeileis 2005; the package suggests `sandwich`). We did not use that on 11-10. The first, small experiment is to rerun application 2 with a HAC covariance and repeat the 100 circular shifts of the partitioning variables. (ii) If that shifted-Z false-split rate stays near 53%, the gap is not just HAC: it is a persistent partitioning variable lining up with volatility clustering. Hansen (2000), "Testing for structural change in conditional models", *Journal of Econometrics* 97(1):93–115, shows that standard break tests have the wrong distribution when regressors (or, here, state variables) are persistent or have their own breaks. The sauce is a split test whose critical values are taken from circular shifts (or a fixed-regressor bootstrap in Hansen's sense) of the partitioning variables, so that "NFCI is persistent and volatility clusters" is in the null, and a split has to beat it.

**Why it matters on our data.** Time-series trees failed the shifted null: 60% (ctree, shifted response) and 53% (MOB, shifted Z). Those are the RESULTS gates that failed, and they are why the recommended skill is scoped to cross-sections, with time-series use only behind a dependence-aware null. Making that null the *split rule*, not a post-hoc veto, is what would make the package extraordinary on panels like ours. The county application should be essentially unchanged (exchangeability is plausible there).

**Closest prior work.** Kirch (2007) and Zeileis & Hothorn (2013) for block-permutation structural-change tests; Zeileis (2005), "A Unified Approach to Structural Change Tests Based on ML Scores, F Statistics, and OLS Residuals", *Econometric Reviews* 24(4):445–466, for the M-fluctuation test MOB already uses; Hansen (2000) for break tests with persistent covariates. We did not find a paper that puts a circular-shift or Hansen-style calibration *inside* partykit's variable-selection step for time-series panels.

**Effort.** L (the HAC rerun is S; a calibrated split rule with theory is L).

**How we would test it.** Pre-registered size and retention of real structure, on the 11-10 panels, no new fits beyond the same circular-shift experiments already defined. **Null (size):** 100 circular shifts of the response (ctree, application 1) and of the partitioning variables (MOB, application 2). The original false-split rates were 60% and 53%. The new tests pass if those rates are at most a pre-registered \(\alpha\) (for example 0.10). **Retention:** on the unshifted data, MOB should still split on NFCI (the published threshold was 0.057; we would pre-register a tolerance, and still require Bonferroni time-split \(p\) not to beat NFCI). ctree's root need not stay "VIX ≈ 32" — that split may itself have been optimism — but the county trees (application 3) must match the original root variables and, up to the documented CV exception, the published leaf counts, under the same iid null that already passed (0% and 4%). **Sanity:** iid-permuted monthly responses, which already split in only 3% for ctree, must not become anti-conservative.

### 3 · New use on our data: MOB of Q1 market loadings

**What it is.** The 11-11 MARSS decomposition assumed constant market loadings \(D\) in \(y_t = x_t + D^\top d_t + v_t\). Window splits already showed that this is not a fixed property of a firm: JPM's equity-revenue share was 88% sticky / 12% market in 2011–17 and 2% sticky / 78% market in 2018–26. The new use is a MOB tree for the PROXY revenue and trading-asset panels: \(\Delta y_t = \beta_0 + \beta^\top d_t + \varepsilon_t\), partitioned by NFCI, VIX, and calendar time, with a circular-shift null of the partitioning variables (the 11-10 lesson, applied from the start). This is a description of *when the market part of the share decomposition changes*, and a visualization of leaf-wise loadings. It is not a forecast.

**Why it matters on our data.** It ties partykit to Q1, and it asks a question MARSS with constant \(D\) cannot. If MOB splits on NFCI and that split *clears* the shifted-Z null, the market-versus-sticky picture should be drawn state by state, not as one variance share for the whole sample. If it does not clear the null, that is also an answer: the window instability in 11-11 1b may be the same persistent-Z artifact we saw on credit spreads.

**Closest prior work.** Zeileis, Hothorn & Hornik (2008) is the MOB method. We did not find an application of MOB to a market-versus-sticky share decomposition, or to these Y-9C PROXY panels. Hansen (2000) is the caution on persistent partitioners.

**Effort.** S–M (an application, plus the mandatory shifted null; smaller if avenue 2 already supplies the test).

**How we would test it.** Pre-registered: (i) whether a split is declared, and on which variable; (ii) the circular-shift false-split rate of the same procedure, which must be at most a pre-registered \(\alpha\) before we read the real split; (iii) a descriptive comparison (BIC, or a full-sample variance split that is allowed to differ by leaf) against the constant-\(D\) MARSS M1 already published. No out-of-sample forecast RMSE, and none of the Y-9C trading-OT forecast trials. PROXY labelling stays on the page.

**Why Math is the top pick.** A port would be valuable (R-only, well-known package), but the thing that failed on our time-series data was the split test. Until that is fixed, a faster port would reproduce the 60% and 53% false-split rates more quickly.

---

## MARSS

Holmes, E. E., Ward, E. J. & Wills, K. (2012), "MARSS: Multivariate Autoregressive State-space Models for Analyzing Time-series Data", *The R Journal* 4(1):11–19. R package MARSS 3.11.10. Scouted on [11-11](2026-11-11.html), aimed at Q1, on a clearly labelled PROXY (FR Y-9C dealer shares, not prime brokerage). Novelty: niche (ecology package, rarely used in this setting). Scout verdict: recommend for the promote workflow — not started, not promoted, awaiting Jared's pick.

**Found via.** CRAN, [https://cran.r-project.org/package=MARSS](https://cran.r-project.org/package=MARSS), seen 2026-11-11 (watchlist "Date seen", and the 11-11 citation). The 11-11 page cites the R Journal (2012) article; an exact journal URL was not recorded. An X search that day is recorded as finding "no method leads and no data." A "sources scanned" list like the 11-10 footer was not recorded for 11-11.

**v0.1-era, not a forecasting upgrade.** Jared's own model framework is at v2.1, and it moved past MARSS-style state-space models at v0.1. The three avenues below treat MARSS as a v0.1-era tool for decomposing sticky versus market-driven share and for visualizing that split. They are deliberately not forecasting improvements (no new nowcast, no walk-forward RMSE target, no claim to beat a random walk). The 11-11 page already reported a mixed one-step comparison and made "no forecasting claim"; we leave that as is.

**What our runs showed.** On the equity-revenue PROXY (E4: JPM, GS, MS, BAC, 62 quarters), market covariates explain 74% (BAC), 62% (MS) and 59% (JPM) of quarterly share-change variance, but only 22% for GS. GS's fall from 52.3% to 23.1% of big-4 equity trading revenue sits almost entirely in the sticky state, and GS's sticky increments mirror JPM's (correlation −0.79, BH \(q = 0.038\)). On trading assets (14 dealers, 40 quarters), net shifts are almost all sticky: foreign-bank IHCs' share fell from 13.8% to 5.9%, with JPM +6.1 points and GS +3.8. The weakness is sample length for *labels*: a matched-persistence null shows that AICc can tell sticky from slow mean reversion at 62 quarters (false "sticky" on stationary AR(1) surrogates 0–18%; power on a true random walk 57–65%) but not reliably at 40 quarters (false "sticky" 15–65%). Decompositions also shift across windows (JPM revenue: 88% sticky in 2011–17, 78% market in 2018–26). Univariate clr fits ignore the sum-to-zero link between dealers. The model is fast enough to use (about 0.2–1 s per univariate fit; the whole 11-11 edition, about 4,000 model selections including nulls and a walk-forward, ran in 11 minutes) and R-only.

### Three avenues

| # | Avenue | Pitch | Effort | Headline test | Pick |
|---|---|---|---|---|---|
| 1 | Engineering | A faithful Python or Rust port of the MARSS Kalman path, with R MARSS 3.11.10 as the oracle, aimed at fast decompositions, persistence nulls, and visualization. | L | Smoothed sticky/market/transient paths, variance splits, AICc choices and net-change attributions match the 11-11 panels; then speed. | |
| 2 | Math | Replace AICc as the sticky-versus-mean-reverting *label* with a finite-sample bootstrap likelihood-ratio test that is calibrated at 40 quarters. | M | At \(T=40\), the false "sticky" rate on stationary AR(1) surrogates drops from 15–65% into the \(T=62\) range (0–18%), with power on true random walks still at least 50%. | **Top** |
| 3 | New use on our data | A joint, compositional model with a structured process covariance, so "who took share from whom" is a parameter, with a visualization of the joint sticky paths. | M | For GS↔JPM, the estimated sticky-increment association has an interval that excludes the clr built-in −0.333, against a circular-shift null; plus a readable joint chart. | |

### 1 · Engineering: a faithful port for decomposition and visualization

**What it is.** The 11-11 model for dealer \(i\) is the centred log-ratio share
\[
x_t = b\, x_{t-1} + w_t,\qquad y_t = x_t + D^\top d_t + v_t,
\]
with AICc comparison of no-sticky, random-walk sticky, no-market, and mean-reverting versions, and a smoothed split of each path into sticky, market and transient parts. The port implements the same Kalman likelihood, the same model set, and the same smoothed states, with R MARSS 3.11.10 as oracle. After parity, speed is used to make the matched-persistence null (40+40 surrogates per dealer) and the charts cheap, including a joint visualization (avenue 3). It is not a forecasting library and would not be tested as one. Closest existing software, not a port: KFAS in R (Helske 2017) was already on the 11-11 watchlist as a faster engine and a cross-check; Python `statsmodels` UnobservedComponents implements Harvey-style structural models. Neither was oracle-tested against MARSS on our panels.

**Why it matters on our data.** The decomposition and the persistence null are the parts we trust and want to reuse on every new share panel (and on real prime-broker data if it arrives). R-only is a friction; 11 minutes for 4,000 selections is acceptable but tight for a more careful short-\(T\) test (avenue 2) or a joint model (avenue 3). A validated port is the engineering path that makes those two avenues practical.

**Closest prior work.** Holmes, Ward & Wills (2012) is the oracle package. Helske (2017), "KFAS: Exponential Family State Space Models in R", *Journal of Statistical Software* 78(10):1–39, is the closest alternative R engine. We did not find a faithful Python or Rust port of MARSS with an oracle parity suite.

**Effort.** L.

**How we would test it.** Pre-registered parity on the published 11-11 aggregates and fitted structure (no raw private rows; the PROXY Y-9C panel is public). **Metric:** AICc for M0/M1/M1n/M2, estimated \(b\) and half-lives, variance splits (sticky / market / transient), net-change attributions, and the published sticky-increment correlations, within a tight tolerance (for example the \(10^{-4}\) style used in analysis-skills, or exact match at the published rounding). **Then speed** of the decomposition-plus-null workload (the matched-persistence simulations of 11-11 1d) on a stated machine, versus the recorded R time. Walk-forward RMSE is not a success criterion.

### 2 · Math: a short-sample test for the sticky label (top pick)

**What it is.** AICc picked "sticky" (M1 or M1n) or "slow mean reversion" (M2) as if that label were reliable. At 40 quarters it is not. The math sauce replaces the AICc decision with a finite-sample test of the hypothesis that matters for the decomposition: is the sticky state a random walk (\(b = 1\), or process variance \(q > 0\) against a stationary alternative) at this \(T\)? Concretely, a parametric bootstrap likelihood-ratio: fit the stationary model (M2, or the matched AR(1) used in 11-11 1d), simulate many series of the same length with the same covariates, recompute the LR against the random-walk sticky model, and label a dealer "sticky" only if the real LR exceeds a pre-registered quantile of that bootstrap. This is the testing idea in Morley, Panovska & Sinclair (2017), who found that a bootstrap LR test of stationarity in unobserved-components models has much better small-sample behaviour than standard LM stationarity tests. Nyblom & Harvey (2000) is the classical LM ancestor for stochastic trends in this kind of model. A possible second step, if the single-firm test is still weak at \(T=40\), is to share information on \(b\) across the 14 dealers (a hierarchical or pooled persistence), still as a labelling device for the decomposition, not as a forecast.

**Why it matters on our data.** This is the stated caveat Jared already heard: "below about 60 quarters, sticky vs slow mean reversion can't be told apart." The 14-dealer trading-asset panel is 40 quarters, and that is where the large sticky net shifts (UBS+CS, Mizuho, RBC, JPM) were labelled. The variance split and the net-change *attribution* can still be reported; the *word* "sticky" for a single firm at \(T=40\) cannot, until the test is calibrated. At 62 quarters the current AICc rule is already informative (false-sticky 0–18%). The sauce is to get the 40-quarter panel into that reliability band.

**Closest prior work.** Morley, J., Panovska, I. B. & Sinclair, T. M. (2017), "Testing Stationarity with Unobserved-Components Models", *Macroeconomic Dynamics* 21(1):160–182. Nyblom, J. & Harvey, A. (2000), "Tests of Common Stochastic Trends", *Econometric Theory* 16(2):176–199. Our 11-11 analysis 1d is already a Monte Carlo of AICc's error rate; the contribution is to make a calibrated test the formal rule. We did not find a paper that does this inside MARSS for compositional share panels.

**Effort.** M (the bootstrap LR is a known procedure to adapt and pre-register; a hierarchical \(b\) would push it toward L).

**How we would test it.** The same matched-persistence design as 11-11 1d, which already exists: for each dealer, 40 stationary AR(1) series with the real lag-1 and noise, and 40 true random walks, at both \(T=40\) (panel A) and \(T=62\) (panel E4), with the real covariates. **Metric (size):** at \(T=40\), the false "sticky" rate must fall into the band we already treat as acceptable at \(T=62\), namely 0–18% (or, pre-registered, at most 0.20) for the dealers in that table. **Metric (power):** the rate of labelling a true random walk as sticky stays at least 0.50 (the 11-11 powers were 50–80% at \(T=40\) and 57–65% at \(T=62\); we will not claim an improvement on power if size is the binding constraint). **Sanity:** at \(T=62\), size must not get worse than the 0–18% AICc already achieved. No forecast RMSE.

### 3 · New use on our data: joint "who took from whom", and a picture of it

**What it is.** Univariate clr fits "ignore the sum-to-zero link between dealers. A joint MARSS with a structured \(Q\) is the next step" — that is a quote from the 11-11 limitations, and it is the new use. Estimate a joint state \(x_t \in \mathbb{R}^{N}\) for the clr (or ilr) vector, with a process covariance \(Q\) that is the "who took share from whom" parameter, under a sum-to-zero constraint. The GS↔JPM sticky-increment correlation (−0.79, BH \(q = 0.038\)) was computed post-hoc on univariate states; here it is estimated with uncertainty, and plotted as a pair of sticky paths (and, on panel A, as the foreign-IHC versus US-dealer contrast). Visualization is part of the sauce: a single chart that shows, for each dealer or group, the sticky path, the market path, and the off-diagonal associations. Not a forecast.

**Why it matters on our data.** Q1 is about migration between brokers, which is a joint fact. The only pair that survived BH correction on 11-11 was GS↔JPM on equity revenue; no pair survived on the 14-dealer asset panel (best \(q = 0.31\)). A joint model can change both the estimate and the uncertainty, and a visualization is what makes the decomposition usable. This stays on the PROXY until real prime-broker data exists.

**Closest prior work.** Snyder, R. D., Ord, J. K., Koehler, A. B., McLaren, K. R. & Beaumont, A. N. (2017), "Forecasting compositional time series: A state space approach", *International Journal of Forecasting* 33(2):502–512, put Gaussian innovations state-space models on log-ratio market shares and proved invariance to the base series. Their aim was forecasting shares (US automobiles). We would use the same compositional state-space idea for decomposition and visualization only, with the 11-11 circular-shift null retained as the test of association. Holmes, Ward & Wills (2012) already support multivariate MARSS in R; the 11-11 run did not use a structured \(Q\) on shares.

**Effort.** M.

**How we would test it.** Pre-registered, on the E4 PROXY panel first (62 quarters, where labels are more trustworthy). **Metric:** the estimated GS↔JPM association (a correlation or a \(Q\) entry, stated in the plan) has a confidence or bootstrap interval that excludes the clr built-in level of about −0.333, and a circular-shift (or parametric) one-sided p-value that still survives BH among the pre-registered pairs. **Visualization:** a chart of the joint sticky paths whose plotted end-points match the published net sticky changes (GS −0.99, JPM +0.79 in clr, as already reported) to a stated rounding. **Sanity:** a joint model that drops the off-diagonal of \(Q\) should recover the univariate variance splits within a stated tolerance. No forecast comparison. If the interval does *not* exclude −0.333, that is a reported failure of the "GS losses went to JPM" reading, not a reason to change the metric.

**Why Math is the top pick.** The port and the joint picture are worth doing, but the sentence we cannot yet stand behind on the 40-quarter panel is a single-firm "sticky" label. That is what a calibrated short-\(T\) test would buy, and it is what the decomposition is for.

---

## InspectChangepoint

Wang, T. & Samworth, R. J. (2018), "High dimensional change point estimation via sparse projection", *Journal of the Royal Statistical Society: Series B* 80(1):57–83. R package InspectChangepoint 1.2 (last CRAN release recorded on 11-11 as 2022-05), pure R, imports only MASS. Scouted on [11-11](2026-11-11.html), aimed at Q1, same PROXY. Novelty: obscure. Scout verdict: interesting, not recommended for the promote workflow on that day's evidence.

**Found via.** CRAN, [https://cran.r-project.org/package=InspectChangepoint](https://cran.r-project.org/package=InspectChangepoint), seen 2026-11-11 (watchlist "Date seen", and the 11-11 citation). The 11-11 page cites the JRSS-B (2018) article; an exact journal URL was not recorded. An X search that day is recorded as finding "no method leads and no data." A "sources scanned" list like the 11-10 footer was not recorded for 11-11.

**What our runs showed.** The selling point is the "who moved" vector, and the method is very fast (9.6 ms per 14 × 40 panel). On market-adjusted log-ratio *levels* it found 8 breaks in the trading-asset panel, while AR(1)-matched and random-walk surrogates with the same persistence averaged 12.39 and 13.28 breaks (\(P(\ge \text{observed}) = 1.000\)). Those level breaks are what a persistent series does under a test that assumes (too little) dependence; they are not evidence of discrete events. On revenue shares, 12 observed breaks were more than AR(1) surrogates (\(p = 0.005\)) but not more than random walks (\(p = 0.075\)). On first differences (a change in *drift*, the right test for a migration that starts or stops), there were 0 breaks in trading assets and 1 non-significant break in revenue shares (after 2011Q3, GS-loaded; iid and block-of-4 nulls produced that often, \(p = 0.24\) and \(0.22\)). Read with MARSS: gradual persistent drift, not a handful of shocks. Quarterly differences in trading-asset shares are negatively autocorrelated (lag-1 between −0.10 and −0.55, median about −0.43), which the 11-11 page read as quarter-end window dressing. The 11-10 changeforest levels artifact is the same lesson.

### Three avenues

| # | Avenue | Pitch | Effort | Headline test | Pick |
|---|---|---|---|---|---|
| 1 | Engineering | A faithful Python or Rust port, with R InspectChangepoint 1.2 as the oracle, and a built-in persistence-matched null as default output. | M | Break dates and projection vectors match the 11-11 panels; the persistence null is reported on every run. | |
| 2 | Math | A sparse-projection procedure whose critical values are valid under near-unit-root persistence, and that can look for a change in drift (slope), not only a change in mean. | L | Size near a pre-registered α on the same AR(1)/RW surrogates of panel A (original: those surrogates produce *more* breaks than the data); power on a planted sparse shift or slope change. | **Top** |
| 3 | New use on our data | Use the "who moved" vector as a readout at *trend-change* dates for Q1 (start or end of the foreign-IHC retreat and the GS→JPM shift), after a persistence null is passed. | M | Dates and named dealers for those two migrations, clearing a persistence null, compared to Narrowest-Over-Threshold as a baseline. | |

### 1 · Engineering: a faithful port, with the persistence null built in

**What it is.** The published procedure stacks the \(p\) series into \(X\), forms a CUSUM matrix \(T\), estimates a sparse projection by a nuclear-norm / \(\ell_1\) relaxation, and runs a univariate CUSUM on the projected series, recursing with wild binary segmentation. The port reproduces that, with R 1.2 as oracle, then (after parity) can be faster on larger \(p\) or \(n\). The 14 × 40 panel is already 9.6 ms in pure R, so speed is not the 11-11 pain point; maintainability, a default persistence-matched null (the 11-11 2b/2c surrogates), and a place to hang avenue 2 are. Last recorded CRAN release was 2022-05; the 11-11 page noted a small user base.

**Why it matters on our data.** Without the persistence null as a default, the face-value 8 breaks (2018Q4 and the rest) are easy to over-read; 11-11 2a told those stories and 2b took them back. A port that always prints "observed vs AR(1) vs RW vs iid" would have made 2b the headline. The R-only, quietly maintained package is a natural oracle-and-port job, but only useful if the null travels with it.

**Closest prior work.** Wang & Samworth (2018) and their R package are the oracle. We did not find a faithful Python or Rust port with an oracle parity suite.

**Effort.** M (the algorithm is small; the null is already written in the 11-11 scripts).

**How we would test it.** Pre-registered parity: on panels A and E4, break dates and the published top projection loadings (and projected CUSUM values, at the published rounding) match InspectChangepoint 1.2. **Then** the default output of a single call must include the 11-11 2b comparison (observed break count vs iid, AR(1)-matched and random-walk surrogates), and those means must match the published 0.76 / 12.39 / 13.28 (panel A levels) to a stated Monte-Carlo tolerance at the same seed. Speed is secondary at this panel size.

### 2 · Math: Inspect that is valid under persistence, including a change in drift (top pick)

**What it is.** Two closely related modifications, because our levels failed one assumption and our scientific question wanted the other.

(i) *Size under persistence.* The 11-11 page said noise is assumed independent over time, and that is what we tested. Wang & Samworth (2018) also discuss an extension to short-range dependent Gaussian processes. Our share *levels* have lag-1 persistence of about 1 (a unit root), which is not short-range dependence, and that is where the test broke (8 observed vs 12.4–13.3 on persistence-matched surrogates). The sauce is a sparse-projection CUSUM whose critical values (or whose prewhitened / long-run-variance studentization) are valid for local-to-unity or unit-root panels of this shape — or, equivalently, a theorem plus a default that refuses to report level breaks unless they beat the persistence-matched surrogate distribution we already computed. Block permutation (Kirch 2007) is a candidate for short-range errors; it is not, by itself, a solution at a unit root.

(ii) *A change in drift.* Sticky migration is a change in *slope* (a trend that starts or stops), not a jump in the mean of the level. The 11-11 run already applied Inspect to first differences and found nothing significant. The math improvement is to put a piecewise-linear (slope-change) model inside the sparse-projection step, so the "who moved" vector \(\hat v\) is the direction of a *drift* change, with a test that has the right size under the observed negative autocorrelation of differences (median lag-1 about −0.43). Closest existing method for the "when" of a slope change, without a "who" vector, is Narrowest-Over-Threshold (Baranowski, Chen & Fryzlewicz 2019), already on the 11-11 watchlist.

**Why it matters on our data.** Every face-value level break failed a persistence-matched null. The drift test that is the right Q1 question found 0 significant breaks. A method that can say "these dealers started or stopped a migration at this date," with a test that does not light up on a random walk, is what Inspect was supposed to be for Q1 and is not, yet, on this PROXY.

**Closest prior work.** Wang & Samworth (2018), including their short-range-dependence extension, which does not cover unit-root levels. Baranowski, R., Chen, Y. & Fryzlewicz, P. (2019), "Narrowest-over-threshold detection of multiple change points and change-point-like features", *JRSS-B* 81(3):649–672, for piecewise-linear features. Kirch (2007) for block-permutation critical values under short-range dependence. We did not find a sparse-projection "who moved" method with proven size at near-unit-root persistence, or a published Inspect extension to slope changes.

**Effort.** L.

**How we would test it.** Reuse the 11-11 surrogate design (200 level surrogates, 300 drift surrogates). **Size:** on AR(1)-matched and random-walk surrogates of panel A, the fraction of series with at least as many breaks as a pre-registered threshold (or the false-discovery of "significant" breaks at a stated \(\alpha\)) is at most 0.10. The original levels test is badly off in the other direction (surrogates have *more* breaks, \(p = 1.000\)). **Power:** plant a sparse mean shift or a sparse slope change of a stated size (we would pre-register a magnitude on the order of the face-value 2018Q4 share moves — JPM +1.82 pp, MS −1.23 pp, GS +1.02 pp — as a *planted* alternative, not as a claimed real break) in otherwise persistence-matched series, and require a pre-registered power (for example at least 0.80) to flag a break within ±1 quarter and to load on the planted dealers. **Sanity:** on the real first-differenced panels, if no planted break is present, we do not require a discovery; a calibrated non-rejection is an acceptable and already-suggested reading (gradual drift).

### 3 · New use on our data: "who moved" at Q1 trend-change dates

**What it is.** Once a dependence-valid trend-change procedure exists (avenue 2, or NOT for the dates plus Inspect only as a projection readout), apply it to the Q1 PROXY to date the *start or end* of two already-described gradual migrations — the foreign-IHC retreat on trading assets (13.8% → 5.9%) and the GS→JPM equity-revenue shift (52.3% → 23.1% and the sticky correlation −0.79) — and to name the dealers in the projection. This is a visualization and a "who" label on a trend, not a forecast, and not a claim of a mean jump. Compare dates to Narrowest-Over-Threshold (Baranowski, Chen & Fryzlewicz 2019) as the "when only" baseline already on the watchlist.

**Why it matters on our data.** MARSS told us the migrations were sticky and gradual; Inspect-on-levels told us stories about 2018Q4 and other dates that the null took back; Inspect-on-differences did not significantly date a start. Q1 still wants a date and a "who" if a calibrated trend-change test can provide them. If it cannot, the honest picture remains "gradual, no discrete start," which is worth locking in.

**Closest prior work.** Baranowski, Chen & Fryzlewicz (2019) for dating piecewise-linear changes; Wang & Samworth (2018) for the projection. We did not find an application that combines the two on a compositional dealer-share panel.

**Effort.** M (S if it is only a script around avenue 2 or around `not`).

**How we would test it.** Pre-registered: (i) the persistence or slope-change null of avenue 2 (or a stated NOT-based null) must pass before dates are read; (ii) if a date is declared, the projection's top loadings should include the dealers the 11-11 MARSS net-change already named (foreign IHCs and JPM/GS on assets; GS and JPM on E4), as a concordance metric (for example, at least two of the top four loadings match the pre-registered set); (iii) NOT's dates, if any, are a baseline for "when," not a "who." A calibrated "no date" is a pass of the *procedure*, and would be reported as agreeing with 11-11 2c. No forecast metric.

**Why Math is the top pick.** A port of a test that is invalid on our share levels would only reproduce the 8-versus-12.4 artifact more conveniently. The extraordinary step is a "who moved" procedure we can believe under the persistence we actually have.

---



---

## codyn

Hallett, Jones, MacDonald, Jones, Flynn, Ripplinger, Slaughter, Gries & Collins (2016), "codyn: An r package of community dynamics metrics", *Methods in Ecology and Evolution* 7(10):1146–1151, doi:10.1111/2041-210X.12569. Package v2.0.6 (2026-09-18, Apache-2.0). Scouted on the [2026-11-12 ad hoc](2026-11-12-adhoc.html) exotic run, aimed at [Q1](QUESTIONS.md). Novelty: niche, from community ecology. Status: recommended for the promote workflow — not promoted, no `APPROVAL.md`.

**Found via.** Journal, *Methods in Ecology and Evolution* (named in the exotic-mandate venue list), 2026-11-12, field: community ecology. Paper: <https://besjournals.onlinelibrary.wiley.com/doi/10.1111/2041-210X.12569>. Also used: <https://cran.r-project.org/package=codyn>, the temporal-diversity vignette, and the NCEAS news note <https://www.nceas.ucsb.edu/news/new-r-code-helps-understand-community-dynamics>. An SSRN search did not surface this package. X was not searched for this edition.

**What our runs showed.** On the PROXY Y-9C panels (same as 11-11; no raw private data), US dealer *volumes* co-move: Schluter VR = 4.45 on 14-dealer trading assets against a 999-draw cyclic-shift null of 0.44–2.00, and 2.36 on big-4 equity trading revenue against 0.57–1.66. The eight foreign IHCs, alone, do not (VR = 0.73, inside 0.29–2.19). Share composition walks in one direction (Collins rate of change 0.00138 and 0.00473, both p = 0.001 vs cyclic-shift). Incidence turnover is identically 0 (closed balanced panel). Mean rank shift is modest (0.385 and 0.238) and is *not* larger than the cyclic-shift null; on E4 it is significantly smaller (p≤ = 0.002), which we treat as a description of gradual change because the Hallett 2014 cyclic shift wraps a trending series and inflates that null. VR on shares is a numerical zero (4.07×10⁻¹⁷ on panel A), as the identity requires. Rank clocks make the GS→JPM equity-revenue swap (52.3% → 23.1% vs 14.5% → 43.4%) and the UBS+CS collapse (rank 7 → 14) visible next to the usual line plot.

### Three avenues

| # | Avenue | Pitch | Effort | Headline test | Pick |
|---|---|---|---|---|---|
| 1 | Engineering | A faithful Python or Rust port of rank clocks, VR with cyclic-shift, and rate-of-change, with codyn 2.0.6 as oracle, then speed for a Form ADV-scale panel. | M | Parity on today’s numbers (VR 4.4537 on A; rates 0.001379 and 0.004727; MRS 0.3846 and 0.2377), then 10×–100× wall time on a larger panel. | |
| 2 | Math | A compositionally valid variance ratio in ilr (or clr) coordinates — official VR on shares is 0 — and a rank-shift null that does not wrap trending series. | L | On simulated 40-quarter panels, correct size under a market factor and power ≥ 0.80 on a planted sticky swap (official VR-on-shares stays 0; official cyclic-shift MRS is inflated by the wrap). | **Top** |
| 3 | New use on our data | Rerun the same clocks, VR and rate-of-change on Form ADV Schedule D prime-broker client counts, once built, and colour the clock by market regime. | S | Whether the GS→JPM clock and a rate-of-change that beats the same null recur on actual prime-broker relationships. | |

### 1 · Engineering: a port with the R package as oracle

**What it is.** A faithful Python or Rust implementation of the metrics we actually ran — rank clocks (Collins et al. 2008), Schluter VR with the Hallett 2014 cyclic-shift null, Collins rate of change, mean rank shift, and turnover — with codyn 2.0.6 as the oracle, then a speed pass for a Form ADV-scale panel. The R package is maintained and small; the work is parity and scale, not a new statistic.

**Why it matters on our data.** Today’s 14×40 and 4×62 panels ran in 129 seconds, mostly in 999-draw nulls. A Form ADV panel (many funds × brokers, longer histories) would feel that. We did not find a Python port of these exact temporal metrics with an oracle suite.

**Closest prior.** Hallett et al. (2016) and the package itself. We did not find a published Python or Rust port with oracle parity on these functions.

**Effort.** M.

**How we would test it.** Pre-registered parity on this proxy: VR 4.453678 on panel A raw amounts (null interval 0.4376–2.0026 at seed 20261112, 999 draws); rate of change 0.001378931 and 0.004726503; mean rank shift 0.3846154 and 0.2377049; turnover identically 0. Then a wall-time comparison on a stated larger panel, 10×–100× as a target, not as a Q1 claim. No forecast metric.

### 2 · Math, in detail (top pick)

**What it is.** Two related gaps we actually hit. (i) Official VR on shares is identically zero, because the share total is 1. A Schluter-style ratio (or a related compensatory metric) in an ilr basis would be compositionally valid and would answer Q1 in share space, which is where the question lives. (ii) The Hallett 2014 cyclic shift is the right null for VR, but on a trending series it wraps the end onto the start and creates an artificial rank jump, so the MRS null is too high. A null that does not wrap — for example a stationary bootstrap of increments — is needed before MRS can be tested fairly.

**Why it matters on our data.** We verified VR-on-shares = 4.07×10⁻¹⁷ on panel A, and we could not use the official tool to test compensatory *share* dynamics, only raw-volume synchrony. On E4, observed MRS 0.238 vs wrap-around null 0.367 (p≤ = 0.002) cannot be read as a formal rejection.

**Closest prior.** Lovell et al. (2015) already refuse raw covariance on the simplex (that is method 2 of the same edition). We did not find a published Schluter-style VR in ilr coordinates with a cyclic-shift null, or a published rank-shift null that avoids wrap-around on trending series. Hallett et al. (2014) is the official VR null we would keep for volumes.

**Effort.** L.

**How we would test it.** Simulate 40-quarter share panels under a common market factor (no sticky swap) and under a planted GS→JPM-style swap. The new share-space metric has a false-positive rate in a pre-registered band around α, and power of at least 0.80 on the planted swap. Official VR-on-shares remains 0 and is reported as a negative control. Official cyclic-shift MRS is a baseline we already know is conservative in the wrap direction. No forecast metric.

### 3 · New use, in detail

**What it is.** The method is already pointed at Q1; the next data is the constraint. Rerun unchanged on Form ADV Schedule D §7.B.(1) prime-broker relationship counts, and colour clock rays by a VIX (or NFCI) high/low split.

**Why it matters.** Zero turnover and a 14-firm closed panel are by construction. Real entry and exit, and real prime-broker relationships, are what Q1 asked for.

**Closest prior.** Today’s 1a–1c pipeline, unchanged.

**Effort.** S, once the panel exists; the data build is separate.

**How we would test it.** The GS–JPM reordering and a rate-of-change above the cyclic-shift null, or an honest non-recurrence, on that panel. Plans only.

**Why Math is the top pick.** A port of a VR that cannot be used on shares would only make today’s identity more convenient. The extraordinary step is a compensatory-share metric we can actually apply to Q1.

---

## Lovell proportionality (ρ)

Lovell, Pawlowsky-Glahn, Egozcue, Marguerat & Bähler (2015), "Proportionality: A Valid Alternative to Correlation for Relative Data", *PLoS Computational Biology* 11(3):e1004075, doi:10.1371/journal.pcbi.1004075. Package paper: Quinn, Richardson, Lovell & Crowley (2017), "propr: An R-package for Identifying Proportionally Abundant Features Using Compositional Data Analysis", *Scientific Reports* 7:16520, doi:10.1038/s41598-017-16520-0. The CRAN package was archived on 2022-11-10 (last version 4.2.6); today’s numbers are from a from-paper implementation, identity-tested, not from propr as an oracle. Scouted on the [2026-11-12 ad hoc](2026-11-12-adhoc.html) exotic run, aimed at [Q1](QUESTIONS.md). Novelty: obscure, from compositional data analysis / genomics. Status: recommended for the promote workflow — not promoted, no `APPROVAL.md`.

**Found via.** Journal, *PLoS Computational Biology*, 2026-11-12, field: compositional data analysis / genomics. Paper: <https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004075>. Found while looking for a compositional alternative to correlation, after the exotic mandate named chemometrics and compositional geochemistry and after `coda.base` was already on the 11-11 watchlist. Also used: Quinn et al. 2017, <https://www.nature.com/articles/s41598-017-16520-0>, and the CRAN archive record. An SSRN search turned up Greenacre’s compositional-data review (SSRN 3800686) but not this method. X was not searched for this edition.

**What our runs showed.** Algebraic identity tests all passed (exact proportionality gives ρ = 1 and VLR = 0; VLR is identical on a composition and on the same amounts times a varying total; ρ is symmetric). On the four-firm equity-revenue proxy, JPM–GS ρ = −0.698 (cyclic-shift p = 0.007, BH q = 0.021) and JPM–MS ρ = −0.554 (p = 0.001, q = 0.006). After residualizing clr on VIX, 4-quarter Nasdaq return, the BAA–Treasury spread and industry growth, JPM–GS becomes *more* anti-proportional (−0.882, p = 0.006, q = 0.036), the only partial pair that survives BH; JPM–MS shrinks to −0.253 and is no longer significant (p = 0.172). JPM–GS is stable across windows (−0.63, −0.68, −0.64); JPM–MS flips from +0.62 in 2011–15 to about −0.52 later. On the 14-dealer panel, Pearson on raw shares often overstates association (Citi–UBS+CS −0.673 vs ρ −0.071; MS–RBC +0.745 vs +0.163); 28 of 91 pairs have raw cyclic-shift p ≤ 0.05 and none survive BH at 0.05. Clr R² on the market is 67% (MS), 62% (BAC), 52% (JPM), 29% (GS), in the same direction as the 11-11 MARSS split, under a different model.

### Three avenues

| # | Avenue | Pitch | Effort | Headline test | Pick |
|---|---|---|---|---|---|
| 1 | Engineering | A maintained Python or Rust library with identity tests, a cyclic-shift (not iid) permutation, and BH, validated against the published formulas. CRAN propr is archived. | M | The identity suite already run, plus parity on E4 JPM–GS ρ = −0.6976, then speed on a wider panel. | |
| 2 | Math | A formal partial-ρ given market factors, with a persistence-aware null whose size is demonstrated at T = 40 and T = 62. Today’s 2c is the prototype. | L | On simulated panels, partial ρ is near 0 when a pair only co-moves through the market, and stays negative when they swap independently of it; raw ρ does not make that cut. | **Top** |
| 3 | New use on our data | Once prime-broker or Form ADV shares exist, run market-partial ρ on a short, pre-registered pair list (JPM–GS, foreign vs US), not on all 91 pairs after the fact. | S | Recurrence of today’s signed, BH-surviving JPM–GS partial ρ, or an honest non-recurrence. | |

### 1 · Engineering: a maintained library with the right null

**What it is.** The formulas are a few lines; the product is a maintained Python or Rust package with identity tests, a cyclic-shift default null, and BH. Closest prior: Quinn et al. 2017 and the archived propr, which had an iid permutation and FDR. We did not find a maintained port whose default null is a cyclic shift.

**Why it matters.** CRAN propr has been archived since 2022-11-10. Today’s numbers depend on a one-off implementation. A Form ADV panel would also want speed and a correct null, not an iid shuffle.

**Effort.** M.

**How we would test it.** The identity suite already in `m2_propr.py` must pass. Parity on this proxy: E4 JPM–GS ρ = −0.697629 (seed 20261112). Then a wall-time comparison on a stated wider panel. No forecast metric.

### 2 · Math, in detail (top pick)

**What it is.** Analysis 2c already draws the Q1 distinction — JPM–GS gets more anti-proportional after the market is removed (−0.698 → −0.882), JPM–MS less so (−0.554 → −0.253) — but it is a prototype, not a theorem. The sauce is a partial-ρ given market factors, with a cyclic-shift (or block) null whose size is demonstrated at T = 40 and T = 62.

**Why it matters.** That distinction is the Q1 payoff of the edition. Without a size result, 2c is a pattern on one proxy.

**Closest prior.** propr’s `pcor.bshrink` (partial correlation with basis shrinkage, recommended in the propr documentation for p ≫ n), which is partial *correlation* after a log-ratio, not partial ρ, and is not aimed at a short, persistent time series with a named covariate set. We did not find a formal “partial ρ given covariates” with a time-series null.

**Effort.** L.

**How we would test it.** Simulate share panels (i) with a common market factor and no residual swap, (ii) with a residual GS→JPM-style swap orthogonal to the market. At a pre-registered α, partial ρ’s false-positive rate on (i) is in a stated band, and power on (ii) is at least 0.80 at T = 62 and is reported honestly at T = 40. Raw ρ must not be allowed to pass (i). No forecast metric.

### 3 · New use, in detail

**What it is.** A short, pre-registered pair list on real prime-broker or Form ADV shares, using market-partial ρ and a cyclic-shift null.

**Why it matters.** The 91-pair FDR on panel A already left no pair standing. Q1 is about named brokers, not a fishing expedition. The limiting ingredient is the data.

**Closest prior.** Today’s 2c pipeline, with BH replaced by a pre-registered list.

**Effort.** S, once the panel exists.

**How we would test it.** JPM–GS partial ρ negative and BH-significant (or significant on the pre-registered list) on the real PB series, or a clear miss, reported as such. Plans only.

**Why Math is the top pick.** A maintained port of raw ρ would still leave “is this the market or a sticky swap” as a prototype. The extraordinary step is a size-correct partial-ρ, which is what turned today’s JPM–GS and JPM–MS into opposite answers.



## ecotraj

De Cáceres, Coll, Legendre, Allen, Wiser, Fortin, Condit & Hubbell (2019), "Trajectory analysis in community ecology", *Ecological Monographs* 89:e01350. Sturbois et al. (2021), *Ecological Modelling* 440:109400. Djeghri et al. (2026), *Ecological Monographs* 96(2):e70058. CRAN ecotraj 1.2.2. Scouted on the [2026-11-12 scheduled edition](2026-11-12.html). Novelty: niche. Status: recommended for the promote workflow — not promoted. Plans only; grounded in that run; no further fits were run to write these plans.

**Found via.** Journal, *Ecological Monographs* / the ecotraj package documentation, 2026-11-12 scheduled exotic scout, field: community ecology. Paper: [https://doi.org/10.1002/ecm.1350](https://doi.org/10.1002/ecm.1350). Also used: [https://emf-creaf.github.io/ecotraj/](https://emf-creaf.github.io/ecotraj/), [https://cran.r-project.org/package=ecotraj](https://cran.r-project.org/package=ecotraj), Sturbois et al. 2021 ([doi:10.1016/j.ecolmodel.2020.109400](https://doi.org/10.1016/j.ecolmodel.2020.109400)), Djeghri et al. 2026 ([doi:10.1002/ecm.70058](https://doi.org/10.1002/ecm.70058)). Not codyn. X and SSRN were not the discovery path.

**What our runs showed.** On 14-dealer trading-asset shares, directionality 0.577 beats a sign-flip null (p = 0.027) and a persistence-matched AR(1) (p = 0.001). Residualizing clr *levels* on market covariates hid the sticky walk (residual sign-flip p = 0.994). Residualizing *increments* finds it: residual dir 0.595, p = 0.008; residual net 3.81 vs market 0.54; market steps explain 16% of step energy. On equity revenue, residual net is a GS→JPM swap (GS −1.16, JPM +1.03 clr) but residual directionality is not significant (p = 0.365) and the overall path fails a sign-flip null (p = 0.664). The built-in random-order null is too weak (p = 0.001 on both panels). DSPD clusters of 13 stress episodes put Lehman in a class of its own; 9- vs 15-month window Spearman 0.96.

### 1 · Engineering (effort M)

A faithful Python or Rust port of `trajectoryDirectionality`, the increment sign-flip null, and DSPD, with ecotraj 1.2.2 as oracle, then a speed pass for a Form ADV-scale panel. We did not find a published Python port with an oracle suite. **Test:** parity on A dir 0.577301, E4 dir 0.431413, A residual-increment dir 0.595092 (seed 20261112, 999 draws), then a wall-time comparison on a stated larger panel. No forecast metric.

### 2 · Math (top pick, effort L)

An increment-level market/residual trajectory split that is compositionally valid and whose sign-flip test has the right size. Closest prior: De Cáceres et al. (2019) define directionality on a single trajectory; they do not split steps into covariate and residual sub-trajectories. We did not find a published increment-level market/residual ETA procedure with a demonstrated size at T = 40 and 62. **Test:** simulate share panels (i) with a common market factor and no residual walk, (ii) with a planted sticky swap orthogonal to the market. Residual directionality’s false-positive rate on (i) is in a pre-registered band around α; power on (ii) is at least 0.80 at T = 62 and is reported honestly at T = 40. The level-residualization procedure must not be allowed to pass (ii) if it fails (i) the way it did today. No forecast metric.

**Why Math is the top pick.** A port of today’s tool would still leave the increment vs level split as a prototype, and that split is what made the sticky walk visible.

### 3 · New use on our data (effort S)

Keep the stress-episode DSPD map as a recurring graph, and rerun the increment split unchanged on Form ADV prime-broker counts. **Test:** recurrence of a directional residual path on activity-like counts, and of a wiggly-but-sticky GS→JPM residual net on revenue-like counts, or an honest miss. Plans only.

## lphom

Pavía & Romero (2024), "Improving Estimates Accuracy of Voter Transitions. Two New Algorithms for Ecological Inference Based on Linear Programming", *Sociological Methods & Research* 53(3):1491–1533 (online 2022), doi:10.1177/00491241221092725. Romero, Pavía, Martín & Romero (2020), *Journal of Applied Statistics* 47:2711–2736. CRAN lphom 0.3.5.7. Scouted on the [2026-11-12 scheduled edition](2026-11-12.html). Novelty: obscure. Status: interesting — not promoted. Plans only; grounded in that run; no further fits were run to write these plans.

**Found via.** Journal, *Sociological Methods & Research*, 2026-11-12 scheduled exotic scout, field: ecological inference. Paper: [https://doi.org/10.1177/00491241221092725](https://doi.org/10.1177/00491241221092725). Also used: [https://cran.r-project.org/package=lphom](https://cran.r-project.org/package=lphom), Romero et al. 2020 ([doi:10.1080/02664763.2020.1804842](https://doi.org/10.1080/02664763.2020.1804842)). This run used baseline `lphom()`, not the 2024 tslphom/nslphom estimators. X and SSRN were not the discovery path.

**What our runs showed.** On a single closed panel of consecutive quarters the transfer matrix is not identified: deterministic bounds have median width 0.88 on the big-4 equity-revenue panel (63% of cells wider than 0.80). The implied GS→JPM cell is 0, which contradicts MARSS, residual Lovell ρ, and ecotraj’s residual net. A no-migration AR(1) already looks like ~20% quarterly churn (observed migration 10.3% is *lower* than that null, p = 0.992). A planted 1% GS→JPM flow is not recovered (499 sims, n = 200 steps, median L1 error 0.68; lphom better than least squares in 60% of draws). Product-year units (54) are a better design but homogeneity error stays high (HETe 28) and the GS→JPM cell is not significant against a shuffle (p = 0.116). High- vs low-VIX splits of P are not significant.

### 1 · Engineering (effort M)

Wrap tslphom and nslphom, the deterministic bounds, and a planted-truth harness so an unidentified run fails loudly instead of returning a tidy heatmap. **Test:** replicate today’s vacuous E4 bounds (median width 0.88) and planted L1 error (median 0.68), then show tighter bounds once real units are supplied. No forecast metric.

### 2 · Math (effort L)

A transfer estimator whose null accounts for persistence, and whose interval is not [0, 1] on a single compositional path. Closest prior: Romero et al. (2020) give deterministic bounds; Pavía & Romero (2024) improve accuracy when many units exist. We did not find a published LP (or Bayesian) transfer estimator designed for one persistent compositional time series. **Test:** on simulated persistent panels with no true flow, coverage of a pre-registered interval for off-diagonal cells; power on a planted 1% GS→JPM flow at T = 62. No forecast metric.

### 3 · New use on our data (top pick, effort M once the panel exists)

Form ADV Schedule D filers as the voting units: each fund’s prime-broker affiliation is a real unit, which is the design lphom is built for and the free route to Q1’s missing data. The blocker is the panel build, not a new statistic. **Test:** informative bounds (median width clearly below 0.5) and a pre-registered GS→JPM (or foreign vs US) flow that either recurs or honestly does not. Plans only.

**Why New use is the top pick.** Today’s failure is a missing-units problem. A better estimator on the same single path will still be weakly identified. The extraordinary step is to give the method the data it was designed for.


## Citations used (verified)

Only papers we located with venue, year, and pages, plus the four method papers already cited on the scout pages. "Found via" links are only those recorded on the 11-10 and 11-11 pages or in the watchlist.

- Baranowski, R., Chen, Y. & Fryzlewicz, P. (2019). Narrowest-over-threshold detection of multiple change points and change-point-like features. *Journal of the Royal Statistical Society: Series B*, 81(3):649–672.
- Hansen, B. E. (2000). Testing for structural change in conditional models. *Journal of Econometrics*, 97(1):93–115.
- Helske, J. (2017). KFAS: Exponential Family State Space Models in R. *Journal of Statistical Software*, 78(10):1–39.
- Holmes, E. E., Ward, E. J. & Wills, K. (2012). MARSS: Multivariate Autoregressive State-space Models for Analyzing Time-series Data. *The R Journal*, 4(1):11–19.
- Hothorn, T., Hornik, K. & Zeileis, A. (2006). Unbiased Recursive Partitioning: A Conditional Inference Framework. *Journal of Computational and Graphical Statistics*, 15(3):651–674.
- Hothorn, T. & Zeileis, A. (2015). partykit: A Modular Toolkit for Recursive Partytioning in R. *Journal of Machine Learning Research*, 16:3905–3909.
- Kirch, C. (2007). Block permutation principles for the change analysis of dependent data. *Journal of Statistical Planning and Inference*, 137:2453–2474.
- Londschien, M., Bühlmann, P. & Kovács, S. (2023). Random Forests for Change Point Detection. *Journal of Machine Learning Research*, 24(216):1–45.
- Meinshausen, N. & Bühlmann, P. (2010). Stability selection. *Journal of the Royal Statistical Society: Series B*, 72(4):417–473.
- Morley, J., Panovska, I. B. & Sinclair, T. M. (2017). Testing Stationarity with Unobserved-Components Models. *Macroeconomic Dynamics*, 21(1):160–182.
- Nyblom, J. & Harvey, A. (2000). Tests of Common Stochastic Trends. *Econometric Theory*, 16(2):176–199.
- Snyder, R. D., Ord, J. K., Koehler, A. B., McLaren, K. R. & Beaumont, A. N. (2017). Forecasting compositional time series: A state space approach. *International Journal of Forecasting*, 33(2):502–512.
- Wang, T. & Samworth, R. J. (2018). High dimensional change point estimation via sparse projection. *Journal of the Royal Statistical Society: Series B*, 80(1):57–83.
- Zeileis, A. (2005). A Unified Approach to Structural Change Tests Based on ML Scores, F Statistics, and OLS Residuals. *Econometric Reviews*, 24(4):445–466.
- Zeileis, A. & Hothorn, T. (2013). A toolbox of permutation tests for structural change. *Statistical Papers*, 54(4):931–954.
- Zeileis, A., Hothorn, T. & Hornik, K. (2008). Model-Based Recursive Partitioning. *Journal of Computational and Graphical Statistics*, 17(2):492–514.

## What this is not

Plans only. Nothing here is being built. Edition 3’s plans are grounded in the 11-12 scheduled scout runs already published on that edition’s page; no further fits were run to write these plans. Nothing is promoted into analysis-skills. No `APPROVAL.md` is written. No raw private Drive rows are published. This file and its page live in research-lab, not in traceot. Research-lab PRs #25 and #21 are not touched.

- Baselga, A. & Orme, C. D. L. (2012). betapart: an R package for the study of beta diversity. *Methods in Ecology and Evolution*, 3(5):808–812.
- Collins, S. L., Micheli, F. & Hartt, L. (2000). A method to determine rates and patterns of variability in ecological communities. *Oikos*, 91(2):285–293.
- Collins, S. L., Suding, K. N., Cleland, E. E., Batty, M., Pennings, S. C., Gross, K. L., Grace, J. B., Gough, L., Fargione, J. E. & Clark, C. M. (2008). Rank clocks and plant community dynamics. *Ecology*, 89(12):3534–3541.
- Hallett, L. M., Hsu, J. S., Cleland, E. E., Collins, S. L., Dickson, T. L., Farrer, E. C., Gherardi, L., Gross, K. L., Hobbs, R. J., Turnbull, L. & Suding, K. N. (2014). Biotic mechanisms of community stability shift along a precipitation gradient. *Ecology*, 95(6):1693–1700.
- Hallett, L. M., Jones, S. K., MacDonald, A. A. M., Jones, M. B., Flynn, D. F. B., Ripplinger, J., Slaughter, P., Gries, C. & Collins, S. L. (2016). codyn: An r package of community dynamics metrics. *Methods in Ecology and Evolution*, 7(10):1146–1151.
- Lovell, D. R., Pawlowsky-Glahn, V., Egozcue, J. J., Marguerat, S. & Bähler, J. (2015). Proportionality: A Valid Alternative to Correlation for Relative Data. *PLoS Computational Biology*, 11(3):e1004075.
- Malherbe, C. & Vayatis, N. (2017). Global optimization of Lipschitz functions. *Proceedings of the 34th International Conference on Machine Learning*, PMLR 70:2314–2323.
- Quinn, T. P., Richardson, M. F., Lovell, D. R. & Crowley, T. M. (2017). propr: An R-package for Identifying Proportionally Abundant Features Using Compositional Data Analysis. *Scientific Reports*, 7:16520.
- Schluter, D. (1984). A Variance Test for Detecting Species Associations, with Some Example Applications. *Ecology*, 65(3):998–1005.
- De Cáceres, M., Coll, L., Legendre, P., Allen, R. B., Wiser, S. K., Fortin, M.-J., Condit, R. & Hubbell, S. (2019). Trajectory analysis in community ecology. *Ecological Monographs*, 89:e01350.
- Djeghri, N., Sturbois, A., Hélaouët, P., Geissmann, Q., Rimmelin-Maury, P., Boyé, A., Gauthier, O. & De Cáceres, M. (2026). Going round in cycles but going somewhere: Deciphering cyclical dynamics using Ecological Trajectory Analysis. *Ecological Monographs*, 96(2):e70058.
- Pavía, J. M. & Romero, R. (2024). Improving estimates accuracy of voter transitions. Two new algorithms for ecological inference based on linear programming. *Sociological Methods & Research*, 53(3):1491–1533.
- Romero, R., Pavía, J. M., Martín, J. & Romero, G. (2020). Assessing uncertainty of voter transitions estimated from aggregated data. Application to the 2017 French presidential election. *Journal of Applied Statistics*, 47:2711–2736.
- Sturbois, A., De Cáceres, M., Sánchez-Pinillos, M., Schaal, G., Gauthier, O., Le Mao, P., Ponsero, A. & Desroy, N. (2021). Extending community trajectory analysis: New metrics and representation. *Ecological Modelling*, 440:109400.
