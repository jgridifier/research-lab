# Pre-registration: the cross-section of CFPB complaint counts

**For:** Jared (GitHub `jgridifier`)
**Recorded:** 2026-10-08
**Status:** `KILLED_AT_BURNIN`
**Design:** `test_design_cfpb_ot_v1.json` (field `oos_authorized` is false and is not the switch)
**Object id:** primary equal-weighted empirical measure of `log(1 + company total)`, three bureau names pinned out

This pre-registration locks one design for a forecast of how CFPB complaints are spread across companies in a month. The object is the equal-weighted empirical distribution of `x = log(1 + total complaints)` among companies with at least one complaint that month, after dropping three pinned names. The burn-in noise-floor rule fired, so the status is `KILLED_AT_BURNIN`. On the 99-point grid the median next-month squared Wasserstein-2 distance was `0.0063598632` and the median half-sample distance was `0.0268769480` (ratio `0.2366289198`). No replacement object is proposed. Nothing after 2017-12 is scored. `oos_authorized` stays false.

Every figure below is copied from `compute_cfpb_ot_burnin.stdout.txt` unless the sentence says it is reused from `compute_cfpb_facts.stdout.txt`, is a quote from `DATA_FACTS.md`, or is a SHA256 printed in `sha256_inputs.stdout.txt`. Month-level burn-in rows are in the new stdout and are not retyped here. DOIs are the identifiers printed in `/workspace/research/ot_classical/ot_classical_notes.md` sections 3 and 4, not estimates.

## 1. Files

| Role | Path | SHA256 |
|---|---|---|
| This run's script | `/workspace/research/cfpb_ot_prereg/compute_cfpb_ot_burnin.py` | `74d682924a51ead286ad373a2bf417b8e316f7d401082a3ccb075d2e935a6f6b` |
| This run's stdout | `/workspace/research/cfpb_ot_prereg/compute_cfpb_ot_burnin.stdout.txt` | `3edaa56bcf706936a91e5f0fe4a47651831425e1d8d38171a4a00ffbcaa4821d` |
| Product panel | `/workspace/research/cfpb_ot_prereg/raw/cfpb_panel_company_month_product.csv.gz` | `1630a2054886f64d702930e25794362bfb1fe49de16127be5cfe837444ce068f` |
| Facts stdout (reused, not rerun) | `/workspace/research/cfpb_ot_prereg/compute_cfpb_facts.stdout.txt` | `56036095bafb30a004652f08d517d0f94678c49380d601e6522cad808a1ec956` |
| Facts memo | `/workspace/research/cfpb_ot_prereg/DATA_FACTS.md` | `4b9d86a72645060c1a040f9dc13d821e9505d6b1c8f59ddd352144c61b492d28` |

Stdout header: `NUMPY 2.5.3`, `PANDAS 3.0.6`, `SCIPY 1.18.1`. `SHA_MATCH True`.

The bank-products panel was not opened for this pre-registration. It was not checked. It is not an input.

## 2. Object

Each month, among companies other than the three names below, sum `complaints` over that company's product rows. Companies with no row are not in the measure. The law is conditional on at least one complaint. Zeros are not stored in the file and are not filled in.

`x = log(1 + total)`, natural log.

The month's object is the equal-weighted empirical measure of those `x` values.

Pinned exclusions, exact strings, and no others:

- `TRANSUNION INTERMEDIATE HOLDINGS, INC.`
- `EQUIFAX, INC.`
- `EXPERIAN INFORMATION SOLUTIONS INC.`

These three were identified from the full-snapshot lifetime ranking already printed in `compute_cfpb_facts.stdout.txt` `SECTION top10_companies` and copied in `DATA_FACTS.md` section 6. This pre-registration does not recompute that ranking and does not add exclusions from any other ranking. The names are pinned. They are not a rule that gets re-estimated on later volume.

Inside the analysis frame only, the script counted stored rows for those strings: `BUREAU_ROWS` 202, 226, and 255, in the order printed. `ROWS_BEFORE_EXCLUSION 86080`. `ROWS_AFTER_EXCLUSION 85397`. `ROWS_EXCLUDED 683`.

## 3. Windows and usability

The snapshot pull date is 2026-10-06, as stated in the facts memo's README note. `2026-10` is an in-progress month and is dropped. The drop is the pull date. The ratio in the facts memo is not a tuned rule and is not used.

Sample months, by calendar: `2013-01` through `2026-09`. Burn-in target months: `2013-01` through `2017-12` (`BURNIN_MONTHS_CALENDAR 60`). Out-of-sample target months: `2018-01` through `2026-09`. `OOS_MONTHS_CALENDAR 105`. `T_OOS 105`. That count is the calendar. Those rows were not read for statistics.

`SQRT_T 10.2469507660`. `LAG_FLOOR_SQRT_T 10`. `B_FIXED 0.0952380952`.

A month is usable only if it has at least `MIN_COMPANIES 100` non-bureau companies (or, in the two trials that put the names back, at least 100 companies in that trial's measure). The check was applied to the burn-in. The same rule is pre-registered for out-of-sample months at runtime. `INCOMPLETE_IF_OOS_FAILS_GT_FRACTION 0.10`. `OOS_FAIL_COUNT_THRESHOLD_EXCLUSIVE 10.5000000000`. If the number of failed out-of-sample months is greater than that threshold, the run is `INCOMPLETE`. Those months were not counted now.

Subperiod lengths, calendar only: `SUBPERIOD 2018-01 2021-12 48`, `SUBPERIOD 2022-01 2024-12 36`, `SUBPERIOD 2025-01 2026-09 21`.

Month labels after 2017-12 already appear as the `yyyymm` column of `compute_cfpb_facts.stdout.txt` `SECTION monthly`. This design does not re-aggregate them. Stdout lines: `ANALYSIS_FRAME_MIN 2013-01`, `ANALYSIS_FRAME_MAX 2017-12`, `NO_MONTH_AFTER_2017_12_AGGREGATED True`, `OOS_ROWS_NOT_AGGREGATED True`.

## 4. Burn-in summaries

Definitions printed by the script:

- `SD_DEFINITION numpy.std ddof=0 (second moment of the empirical measure)`
- `MAD_DEFINITION unscaled median(|x - median(x)|); median is numpy.median`
- `QUANTILE_METHOD linear` on `u = k/100` for `k = 1..99` (`N_GRID 99`)
- `W2SQ_FORMULA mean_{k=1}^{99} (Q1(u_k)-Q2(u_k))**2`
- `CRPS_FORMULA (2/99)*sum_{k=1}^{99} (1{y<q_k}-u_k)*(q_k-y) with u_k=k/100`
- `AR_PAIRS calendar-adjacent usable months only; a gap is not lag 1`
- `RESIDUAL_SD sqrt(SSE/(n_pairs-2))`
- `HALF_SPLIT permutation of companies; first n//2 vs the rest; odd n -> second half larger by 1`

`N_TARGET_MONTHS 60`. `N_MONTHS_PRESENT 60`. `N_USABLE 60`. `N_UNUSABLE 0`. Every burn-in month clears the floor of 100.

`COMPANY_COUNT_MIN 218` in `COMPANY_COUNT_MIN_MONTH 2013-05`. `COMPANY_COUNT_MAX 1374` in `COMPANY_COUNT_MAX_MONTH 2017-03`.

Across the 60 usable months: `USABLE_MEAN_OF_MEAN_X 1.4154610730`, `USABLE_MEAN_OF_SD_X 1.0325601745`, `USABLE_MEAN_OF_MAD_X 0.4102598093`. `N_USABLE_SD_EQ_0 0`. `N_USABLE_SD_GT_0 60`.

### Persistence, burn-in only

AR(1) with intercept, OLS, on the monthly mean of `x`. Series `2013-01` through `2017-12`, `SERIES_N 60`, `ADJACENT_PAIRS 59`, `GAPS_SKIPPED_NOT_USED_AS_LAG1 0`.

- `AR1_MEAN_COEFFICIENT 0.8316994457`
- `AR1_MEAN_INTERCEPT 0.2322962145`
- `AR1_MEAN_RESIDUAL_SD 0.0449416661`
- `AR1_MEAN_N_PAIRS 59`

The same regression on `log(sd)` for months with `sd > 0` (all 60):

- `AR1_LOGSD_COEFFICIENT 0.8826149263`
- `AR1_LOGSD_INTERCEPT -0.0026692645`
- `AR1_LOGSD_RESIDUAL_SD 0.0258960254`
- `AR1_LOGSD_N_PAIRS 59`

These coefficients are descriptions of the burn-in. They are not the B3 coefficients used at a future origin. B3, if it were ever fit, re-estimates at each origin. It was not fit.

### Noise floor

`SEED 20261008`. One `numpy.random.default_rng` stream, usable months in chronological order. For each usable month the companies are permuted and split into `n//2` and the rest. Squared grid distance between the two half-sample quantile functions, and between month `t` and month `t+1` for consecutive usable burn-in months.

`N_MONTHS_HALF_SPLIT 60`. `N_PAIRS_NEXT_MONTH 59`.

- `MEDIAN_HALF_W2SQ 0.0268769480`
- `MEDIAN_NEXT_W2SQ 0.0063598632`
- `RATIO_NEXT_OVER_HALF 0.2366289198`
- `KILL_IF_MEDIAN_NEXT_LEQ_MEDIAN_HALF True`
- `NOISE_FLOOR_STATUS KILLED_AT_BURNIN`

The rule was: kill if the median next-month distance is less than or equal to the median half-sample distance. It fired. The month-to-month quantile function moved less, on this grid, than two random halves of the same month. No other object is substituted.

### B0 on the burn-in, for scale only

**Label: BURN-IN. Not an out-of-sample result.**

B0's forecast of month `t` is the empirical quantile function of calendar month `t-1`, and only if `t-1` is usable. The score is the mean, over companies in month `t`, of the 99-grid CRPS printed above. `N_B0_SCORES 59`, from `B0_SCORE_FIRST_MONTH 2013-02` through `B0_SCORE_LAST_MONTH 2017-12`. `B0_SCORE_GAPS 0`.

- `B0_MEAN_SCORE 0.4881777450`
- `B0_SCORE_SD_DDOF1 0.0630861719` (`numpy.std` with `ddof=1` of the monthly scores)

AR(1) with intercept on that monthly score:

- `AR1_B0_COEFFICIENT 0.8520187511`
- `AR1_B0_INTERCEPT 0.0685685922`
- `AR1_B0_RESIDUAL_SD 0.0195693433`
- `AR1_B0_N_PAIRS 58`
- `AR1_B0_PHI_INSIDE_OPEN_INTERVAL_-0.99_0.99 True`

Formula check, not CFPB data. The same 99-grid CRPS applied to standard-normal quantiles, scored at 0, printed `CRPS_NORMAL_GRID_AT_0 0.2359119878`. The closed form at the mean, `(sqrt(2)-1)/sqrt(pi)`, printed `CRPS_NORMAL_AT_MEAN_CLOSED_FORM 0.2336949773`. Difference `CRPS_NORMAL_GRID_MINUS_CLOSED 0.0022170106`. The 99-point CRPS is an approximation. The same approximation is used for every method, so a comparison is a comparison of that approximation, not of the integral.

## 5. Methods, specified so they can be coded, not fit

Nothing in this section was estimated. H1, H2, H1s, H2m, and the product-mix barycenter were not fit. `s` for H1s was not chosen.

Quantile grid `u_k = k/100`, `k = 1..99`, `numpy` quantile `method=linear` for empirical quantile functions. Any forecast quantile function is projected to be nondecreasing with isotonic regression (pool-adjacent-violators, equal weights on the 99 points, increasing in `u`) before scoring.

Baselines use only months strictly before the target. A pair is a lag only if the two months are usable and one calendar month apart. A gap is not lag 1.

- **B0.** Empirical quantile function of calendar month `t-1`, defined only if `t-1` is usable. If `t-1` is unusable, B0 is undefined. Do not substitute `t-2`.
- **B1.** Expanding Fréchet mean: the average of the empirical quantile functions of all usable months strictly before `t`. Undefined if there is none. In one dimension that average is the equal-weight Wasserstein-2 barycenter of those months.
- **B2.** Average of the empirical quantile functions of the same calendar month in earlier years, using usable months only. If fewer than 2 such months exist, B2's forecast equals B1's forecast, and B2 is then defined only if B1 is defined. If at least 2 such months exist, B2 is that same-calendar average.
- **B3.** Gaussian location-scale. At each origin, OLS with intercept of the monthly mean of `x` on its own lag, and OLS with intercept of `log(sd)` on its own lag, using calendar-adjacent usable pairs strictly before `t`. The log-sd regression uses only months with `sd > 0`. Each autoregressive coefficient is clipped to the printed interval `B3_AR_CLIP -0.99 0.99`. The intercept is not clipped. The lag input is month `t-1`: if `t-1` is not usable, or its sd is not finite and positive, B3 is undefined. Need at least two pairs in each regression. Forecast mean `a_m + b_m * mean_{t-1}`, forecast log-sd `a_s + b_s * log(sd_{t-1})`, forecast sd `exp` of that. If the forecast sd is not finite and positive, B3 is undefined. Quantile function `mean + sd * Phi^{-1}(u_k)`, then isotonic.

**B-star.** Among B0, B1, B2, B3 that are defined for the target, the one with the lowest mean score on the trailing past scored months. A past scored month is a month `s < t` at which B0 is defined. `BSTAR_MIN_PAST 12`. `BSTAR_TRAILING 24`. If fewer than 12 past scored months exist, B-star is undefined. Otherwise use the most recent `min(24, n)` of them. A candidate is eligible only if it is defined on the target and on every month in that window. Ties break in the order B0, B1, B2, B3. Re-selected at every origin. Past scores only.

If B2 is only the B1 fallback, its quantile function equals B1's. H1, defined next, averages each distinct quantile function once, so a fallback B2 is not a second copy of B1 inside H1. B2 may still be selected by B-star; on a tie with B1 the tie-break keeps B1.

**H1 (primary).** Equal-weight Wasserstein-2 barycenter of the defined members of {B0, B1, B2, B3}, with the distinct-function rule in the previous paragraph. In one dimension that barycenter is the average of their quantile functions, then isotonic. If fewer than 2 baselines are defined, H1 is undefined.

Citation, from `/workspace/research/ot_classical/ot_classical_notes.md` section 4, not re-derived here: *Probability forecast combination via entropy regularized Wasserstein distance*, Entropy 22(9):929, 2020, DOI `10.3390/e22090929`. The notes say that in one dimension the barycenter equals quantile averaging. H1 is that unregularized average. It is not the paper's entropic barycenter. Section 3 of the same notes is the geometry used for H2: the quantile function is the coordinate, and a forecast is mapped back onto nondecreasing functions.

**H2 (primary).** Wasserstein autoregression of order 1. The origin for target `t` is month `t-1`, which must be usable; otherwise H2 is undefined. `Q-bar` is the average of the empirical quantile functions of all usable months at or before the origin. The origin's own realized measure is included. Log-map `L_s = Q_s - Q-bar`, using that one `Q-bar` for every `s` in the estimation sample (centering is at the origin, not causal inside the sample, and it does not use a month after the origin). OLS without an intercept of `L_s` on `L_{s-1}`, one slope, pooled by stacking the 99 grid points, over calendar-adjacent usable pairs with `s` at or before the origin. Slope `sum(L_s * L_{s-1}) / sum(L_{s-1}^2)`. Undefined if there is no pair or the denominator is 0. Clip the slope to `H2_SLOPE_CLIP 0 1`. Forecast quantile `Q-bar + slope * L_origin`, then isotonic.

Citation, notes section 3: *Wasserstein autoregressive models for density time series*, Journal of Time Series Analysis 43(1), 2022, DOI `10.1111/jtsa.12590`, arXiv `2006.12640`. *Fréchet regression for random objects with Euclidean predictors*, Annals of Statistics 47(2), 2019, DOI `10.1214/17-AOS1624`, arXiv `1608.03012`, is background (before 2020). It is not the estimator.

## 6. Score, gain, and the gate

The score of a method in a target month is the mean, over companies in that month's measure, of the 99-grid CRPS of the forecast quantile function. The approximation in section 4 is the score. It is the same approximation for every method.

Loss differential `d_t = score(B-star)_t - score(method)_t`. Positive means the method has the lower score.

Relative gain on a set of paired months:

`G = 1 - mean(score(method)) / mean(score(B-star))`

using the same months in both means. `HURDLE_G 0.0200000000`.

**Statistic.** This is the statistic. It is not a textbook Kiefer–Vogelsang critical value. Those tables were not used.

`Z = sqrt(T) * mean(d) / s_b`

`s_b^2` is the Bartlett HAC variance with lag `L = floor(sqrt(T))`, Newey–West weights `w_j = 1 - j/(L+1)` for `j = 1..L`:

`gamma_j = (1/T) * sum_{t=j+1}^{T} (d_t - dbar) * (d_{t-j} - dbar)`

`s_b^2 = gamma_0 + 2 * sum_{j=1}^{L} w_j * gamma_j`

`T` is the number of out-of-sample months where both scores exist, not a padded 105 if some months are missing from the pair. One-sided, upper tail: the alternative is a positive mean of `d_t`.

**Runtime p-value.** Fixed-b test with simulated p-values under a mean-zero AR(1) that uses the dependence estimated on that same `d_t` series. OLS AR(1) with intercept on `d_t`. If that coefficient is not inside the open interval `(-0.99, 0.99)`, the comparison is `INCOMPLETE` and the coefficient is not clipped to force a p-value. If it is inside, simulate `N_DRAWS 100000` mean-zero Gaussian AR(1) series of length `T`, innovation scale 1 (the studentized statistic does not depend on scale), 500 draws discarded at the start, stationary draw for the first state, `numpy.random.default_rng` seed `SEED 20261008`, restarted for that comparison. `p = (1 + count(Z_sim >= Z_obs)) / (N_DRAWS + 1)`. Also compute the p-value at `phi = 0` the same way. The `phi = 0` p-value is reported and does not gate. The planning critical values in section 7 are not substituted for this runtime simulation. Runtime `phi` is the coefficient of `d_t`, which has not been computed, because the out-of-sample scores do not exist.

**Primary family.** `PRIMARY_FAMILY_SIZE 2`: H1 against B-star, and H2 against B-star. Holm, familywise `HOLM_FAMILYWISE 0.05`, one-sided. Order the two runtime p-values `p_(1) <= p_(2)`. Reject the smaller comparison if `p_(1) <= HOLM_FIRST_THRESHOLD 0.025`. Reject the larger only if the smaller was rejected and `p_(2) <= HOLM_SECOND_THRESHOLD 0.05`.

**PASS**, for one primary method, requires all of the following:

1. Holm rejects that method's comparison.
2. `G > 0.0200000000` on the paired out-of-sample months in that comparison.
3. `G > 0` in at least 2 of the 3 subperiods (same `G`, computed inside the subperiod on the paired months that fall in it). A subperiod with no paired month does not count as `G > 0`.
4. At least `MIN_PAIRED_OOS_MONTHS 80` months in the paired comparison.
5. The out-of-sample usability rule in section 3 does not trip.

A statistical rejection with `G <= 0.0200000000` is `INCOMPLETE`, not a pass. Failure of Holm, or of the subperiod count, is not a pass. It is not a license to change the design and rerun.

## 7. Planning critical values and power

**Label: PLANNING.** From the burn-in B0 scale. Not a result about 2018–2026.

Null simulations: `T 105`, `L 10`, `N_DRAWS 100000`, seed restarted per block at `20261008`, `IID_N_FINITE 100000`, `IID_N_NONPOSITIVE_HAC 0`, and the same finite count and zero nonpositive HAC under the burn-in phi. Upper quantiles, `numpy.quantile` `method=linear`. The reported critical values are the 4-decimal lines.

| Null | 5% critical value | 2.5% critical value |
|---|---|---|
| mean-zero iid (`phi = 0`) | `CV_IID_95_4DP 1.8579` | `CV_IID_975_4DP 2.2585` |
| mean-zero AR(1) at `AR_PHI_USED 0.8520187511` | `CV_AR_95_4DP 2.7900` | `CV_AR_975_4DP 3.4417` |

Power simulation. `DGP d_t - mu = phi*(d_{t-1}-mu) + eps_t`. `POWER_SIGMA 0.0195693433`, the burn-in residual sd of the monthly B0 score. `MU = gain * B0_MEAN_SCORE`, and `POWER_MEAN_B0 0.4881777450`. `N_REPS 2000`. Seed `20261008` restarted per phi. Shocks shared across gains within a phi. Reject when the statistic is strictly greater than the critical value from the matching null. Every power row printed `N_FINITE 2000` and `N_NONPOSITIVE_HAC 0`.

| Block | Gain | Mu | Power at 5% | Power at 2.5% |
|---|---|---|---|---|
| `PHI 0.0000000000` | `0.0100000000` | `0.0048817775` | `0.7960` | `0.6670` |
| `PHI 0.0000000000` | `0.0200000000` | `0.0097635549` | `0.9990` | `0.9975` |
| `PHI 0.0000000000` | `0.0500000000` | `0.0244088873` | `1.0000` | `1.0000` |
| `PHI 0.0000000000` | `0.1000000000` | `0.0488177745` | `1.0000` | `1.0000` |
| `PHI 0.8520187511` | `0.0100000000` | `0.0048817775` | `0.0940` | `0.0510` |
| `PHI 0.8520187511` | `0.0200000000` | `0.0097635549` | `0.1670` | `0.0990` |
| `PHI 0.8520187511` | `0.0500000000` | `0.0244088873` | `0.5620` | `0.4130` |
| `PHI 0.8520187511` | `0.1000000000` | `0.0488177745` | `0.9665` | `0.9240` |

`SMALLEST_GAIN_POWER80_AT_5PCT PHI0 0.0200000000`. `SMALLEST_GAIN_POWER80_AT_2_5PCT PHI0 0.0200000000`. `SMALLEST_GAIN_POWER80_AT_5PCT PHIBURNIN 0.1000000000`. `SMALLEST_GAIN_POWER80_AT_2_5PCT PHIBURNIN 0.1000000000`.

The 2.5% column is the per-comparison bar after the Holm factor for two tests. The 5% column is the unadjusted one-sided test.

At a relative gain of `0.0200000000` and at the burn-in coefficient `0.8520187511`, simulated power is `0.1670` at the 5% critical value and `0.0990` at the 2.5% critical value. Both are below one half. The dependence in the burn-in B0 scores, not the calendar length under independence, is what makes a 2% gain hard to detect: under `phi = 0` the same 2% gain has power `0.9990` and `0.9975`. The hurdle stays `0.0200000000`. It is not raised to the smallest gain named by the stdout labels `SMALLEST_GAIN_POWER80_AT_5PCT` and `SMALLEST_GAIN_POWER80_AT_2_5PCT`.

## 8. Kill, and what incomplete means

The burn-in noise floor fired. Status `KILLED_AT_BURNIN`. The design is recorded so the negative result is pinned. There is no out-of-sample run. There is no replacement object.

If this kill were ignored, the runtime incomplete rules would still be: fewer than 80 paired out-of-sample months, or more than 10% of the 105 out-of-sample months under 100 companies, or a Holm rejection with `G <= 0.0200000000`. Those checks are not performed now, because the months are off limits and the kill already stopped the run.

## 9. Nine trials

`TRIAL_COUNT 9`. One run would log all nine before any score. One run only. If the output looked odd, stop and show the raw output. Do not rerun. The kill means that run does not start. The nine are still specified.

They are not one Holm family. The only gating Holm family is the primary pair, trials 1 and 2. Trials 3 through 9 are each one trial. Each gets the same fixed-b statistic and the same simulated one-sided p-value, reported raw. None of them can gate. There is no second Holm family.

1. Primary H1 against B-star.
2. Primary H2 against B-star.
3. **H1s.** Take H1's quantile function after isotonic. Let `m` be the grid point at `u = 0.50`. Replace `Q(u)` by `m + s * (Q(u) - m)`, then isotonic. `s` is chosen on the primary burn-in only, before any out-of-sample month is touched, by minimizing the mean burn-in score over `S_GRID 1.0 1.1 1.2 1.35 1.5`. Ties take the smallest `s`. Then `s` is frozen. Compared with the same B-star rule. This is a dispersion widening. The Entropy 2020 paper discusses a dispersion knob. That paper's entropic barycenter is not what is computed, and H1s is not a Sinkhorn barycenter. `s` was not computed in this pre-registration.
4. **H2m.** Transport-map autoregression in one dimension. Forecast quantile `a + b * Q_previous`, where `a` and `b` are OLS of the stacked grid of `Q_s` on `Q_{s-1}` and a constant, over calendar-adjacent usable pairs at or before the origin. `b` is clipped to `H2M_B_CLIP 0 2`. `a` is not clipped. Then isotonic. Undefined if the origin month is unusable, if there is no pair, or if `b` is not identified. Citation, notes section 3: *Autoregressive optimal transport models*, arXiv `2105.05439` (the notes say arXiv 2021, v4, journal not confirmed). This is a restricted one-dimensional linear specification of that family. It is not a reproduction of that paper's estimator.
5. Primary H1 with the three bureau names included. The log stays. No other change.
6. Primary H2 with the three bureau names included. The log stays. No other change.
7. Primary H1 on raw complaint totals, no log. The three names stay excluded. No other change. `x` is the company total. B3's log-sd regression uses the sd of that raw cross-section.
8. Primary H2 on raw complaint totals, no log. The three names stay excluded. No other change.
9. Product-mix trial, section 10. Not part of a Holm family that can gate.

Trials 7 and 8 change the transform and do not also add the bureaus back. Trials 5 and 6 add the names back and do not also drop the log. One change each, so the two changes are not confounded.

## 10. Product-mix trial, specified, not computed

Not gating. Not computed. No share, no W1, and no barycenter was calculated.

Window where the facts memo says the product strings are a stable set of 9: target months `2017-05` through `2023-07`. `PRODUCT_MIX_WINDOW_MONTHS 75`. Its own burn-in `2017-05` through `2019-12`: `PRODUCT_MIX_BURNIN_MONTHS 32`. Its own out-of-sample `2020-01` through `2023-07`: `PRODUCT_MIX_OOS_MONTHS 43`. The primary minimum of 80 paired months is a primary-gate rule. This trial's calendar out-of-sample length is 43, so it could not meet 80. It would be reported anyway, and it still cannot gate. The kill stops it from being run.

The nine strings, exact:

- Checking or savings account
- Credit card or prepaid card
- Credit reporting, credit repair services, or other personal consumer reports
- Debt collection
- Money transfer, virtual currency, or money service
- Mortgage
- Payday loan, title loan, or personal loan
- Student loan
- Vehicle loan or lease

Industry mix: complaint-weighted shares over these strings, non-bureau companies only. If any other product string has positive complaints among those non-bureau companies that month, the month is dropped. Bureau rows are not used to build the share and are not used to drop the month.

Ground distance for W1: `W1_COST_DIAGONAL 0`, `W1_COST_SAME_GROUP 1`, `W1_COST_OTHER 2`.

Groups:

- deposits: Checking or savings account
- revolving: Credit card or prepaid card
- info: Credit reporting, credit repair services, or other personal consumer reports; Debt collection
- housing: Mortgage
- installment: Student loan; Vehicle loan or lease; Payday loan, title loan, or personal loan
- payments: Money transfer, virtual currency, or money service

The monthly loss is W1 between the realized share and the forecast share under that cost. It is one number per month, not a mean over companies.

Baselines, using only earlier kept months: B0 is the previous calendar month's mix if that month was kept, else undefined. B1 is the average of share vectors of all earlier kept months. B2 is the average of the same calendar month in earlier years; if fewer than 2, use B1. Hmix is the equal-weight W1 barycenter of the defined members of {B0, B1, B2}, at least 2, a linear program on the 9-simplex with that cost. Not an entropic barycenter. If the LP has several optima, take the barycenter masses with smallest Euclidean norm, then the lexicographic minimum, so the solver does not choose. B-star is among B0, B1, and B2 by the same trailing-24 rule (`24`, minimum `12`), tie-break B0 then B1 then B2. One comparison, Hmix against B-star. The p-value is reported. It is not part of a Holm family that can gate.

## 11. Leakage and the snapshot

No parameter is chosen using a month after the origin. The frozen `s` for H1s is the exception that is fixed before the first out-of-sample origin, and it is chosen on the primary burn-in only (`2013-01` through `2017-12`). It does not use a later month. It was not chosen in this file.

The bureau list is pinned names, not a volume rule re-estimated later.

The file is one snapshot pulled 2026-10-06, not point-in-time vintages. The facts memo, section 8, attributes this sentence to one fetch of the CFPB consumer-complaints page: "Only complaints sent to companies for response are eligible to be published and are only published after the company responds, confirming a commercial relationship or after 15 days, whichever comes first. The database generally updates daily." That sentence is not strengthened here. A later edit to an old complaint can change a past month. The backtest is pseudo-real-time. That can leak. It is a limitation, not a kill, because vintages are not in the file. The kill that did fire is the burn-in noise floor, which is a different fact.

Full-snapshot exposure already taken is listed in `DATA_FACTS.md`: lifetime shares, the October 2026 size comparison, the product timeline, and the 2014 company-month percentiles. This pre-registration adds burn-in distributional summaries: company counts, means, sds, MADs, grid Wasserstein distances, and B0 CRPS, for `2013-01` through `2017-12` only. No 2018–2026 distributional summary has been computed. No company count, mean, quantile, Wasserstein distance, or complaint sum for a month after 2017-12 was printed by this script.

## 12. Authorization

`OOS_AUTHORIZED false` is printed in the stdout and stored in the design JSON.

The Y-9C lesson, as written in `/workspace/research/y9c_ot_prereg/OOS_APPROVAL_v1_1.json`, is that a separate approval file is what authorizes a run, and that `oos_authorized` in the design JSON stays false and is not the switch. This design copies that lesson. If Jared authorizes something later, the authorization will be a separate file. It will not be a flip of this flag. Because the noise floor killed this object, an authorization file still would not start an out-of-sample run of this design. A different object would need its own pre-registration.

## 13. Constraints

Classical statistics only. No pretrained model. No neural net.

The out-of-sample window stays closed. The negative burn-in result is the result this file pins.
