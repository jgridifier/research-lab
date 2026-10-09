# Pre-registration: state distributions of FDIC branch deposits, Wasserstein forecasting

**For:** Jared (GitHub `jgridifier`)
**Recorded:** 2026-10-09
**Status:** `KILLED_AT_BURNIN`
**Design:** `test_design_fdic_sod_ot_v1.json` (`oos_authorized` is false, and that flag is not the switch)
**Object id:** primary. For each state and year, the equal-weighted empirical law of `ln(DEPSUMBR) - ln(M_t)` over non-main-office branches with positive deposits.

This pre-registration fixes one design for forecasting how branch deposits are spread inside each US state, one year ahead. It also records that the burn-in gate killed that design. Two of the three pre-stated kill rules fired. **K1 (noise floor):** the median next-year squared Wasserstein-2 distance was `0.0078208250`, below the median half-sample distance of `0.0195766804` (ratio `0.3994969939`). **K3 (shape noise floor):** the median next-year shape term was `0.0036937468`, below the median half-sample shape term of `0.0093507007` (ratio `0.3950235363`). **K2 did not fire:** the pooled shape share of the next-year move was `0.4199810024`, above the pre-stated 0.15. Planning power was also hopeless: the pre-registered primary test has simulated power `0.0705` at a 5% relative gain at the Holm 2.5% level. No replacement object is proposed. No year after 2003 was scored or summarized distributionally. `oos_authorized` stays false.

Every figure below is copied from `compute_sod_ot_burnin.stdout.txt` unless the sentence says it comes from `compute_sod_facts.stdout.txt` / `DATA_FACTS.md`. DOIs and arXiv ids come from `/workspace/research/ot_classical/ot_classical_notes.md` §3–§4. That list was verified earlier. No new paper is cited.

## 1. Files

| Role | Path | SHA256 |
|---|---|---|
| Kill thresholds (written and hashed **before** any W2 computation) | `GATE_THRESHOLDS_fdic_sod_ot.md` | `14018b0c4f44de33f30e276134ddfa42334f64044333db19d5a924ae4f9af4a8` |
| Burn-in script | `compute_sod_ot_burnin.py` | `664c590390583a059893984d77d08a1c3724962e610fe394634267797e1162f4` |
| Burn-in stdout | `compute_sod_ot_burnin.stdout.txt` | `b07b9f7264be386e584970b785b0b8456151b8eb004ac57bb475415a68213528` |
| Facts script | `compute_sod_facts.py` | `99bd140d5a4c4284a976f86b46c3d2288432c4e53dd7c886f84aa4220375e859` |
| Facts stdout | `compute_sod_facts.stdout.txt` | `91f575bb71bb354b574dce279fdb75f096abb061c3fc97d9278c49399b782aa8` |
| Units probe (1994, 2003 only) | `units_probe_burnin.py` / `.stdout.txt` | `43e934046d3e8237d4609136967c0acfdc70c73a6c1bd015cca0086a469bc0ad` / `52b92055eb07f7fe71a56cba82f5d91dca68cebe84096dfac74912d0c17b8261` |
| Facts memo | `DATA_FACTS.md` | `2abdaab23751f0afc6b02d71c1b67f4f9b75f1ba8e9b178956605c544d46a94d` |
| Drive manifest (ids, modified times) | `drive_manifest.json` | `fc3f4c6c52a678730026b06e88511720ef286ff3f0c2fb1ea7c250ce805b6592` |

All paths are under `/workspace/research/fdic_sod_ot_prereg/`. Raw inputs are under `raw/`. Their per-file sha256, Drive id and Drive modified time are printed in `compute_sod_facts.stdout.txt` `SECTION files` and tabulated in `DATA_FACTS.md` §1. Stdout header: `NUMPY 2.5.3`, `PANDAS 3.0.6`. `THRESHOLDS_SHA256 … MATCH True`. `INPUT_SHA_MATCH_ALL_BURNIN_FILES True`. `NO_YEAR_AFTER_2003_READ True`. SciPy is not installed in the box Python. No SciPy function is used: the t quantile comes from simulation, and the AR(1) fits use NumPy least squares.

## 2. Data facts that shaped the object (from `DATA_FACTS.md`)

- 32 yearly files, 1994–2025. The 15 columns are identical, in the same order, every year. There is no schema drift.
- `DEPSUMBR` is the branch deposit field, in $000s. It is integer every year, with no nulls and no negatives. `DEPSUM` (the bank total) switches to float in 2023–2025 and has one null in each of those years. `DEPSUM` is not used.
- There is no main-office flag column. `BRNUM == 0` marks the main office, and the FDIC reporting instructions say so: "The office number "0" is always the Main Office of the institution".
- There is no date column. The README and the instructions both give the as-of date as June 30, with publication by September 30.
- The data first exist in 1994, so the burn-in is 1994–2003 as requested. No adjustment was needed.

## 3. Object and the main-office trim

Year `t`, state `s` in the 51 jurisdictions (50 states + DC). Rows with `BRNUM != 0` and `DEPSUMBR > 0`. `x = ln(DEPSUMBR) - ln(M_t)`, where `M_t` is the median `DEPSUMBR` over all such rows nationally in year `t`. A state-year is usable if it has at least 50 rows. The quantile function uses `u_k = k/100`, `k = 1..99`, `numpy` `method=linear`. Loss: `W2SQ = mean_k (Q1(u_k) - Q2(u_k))^2`.

**Trim rule: exclude every main office (`BRNUM == 0`). No other trim.** Reasons:

1. The instructions allow "certain classes of deposits … [to] be assigned to a single office for reasons of convenience or efficiency". Unit banks do not file. Their single row is the bank's whole Call Report deposit total. So a main-office row measures a booking convention or a whole bank, not one branch's deposit franchise.
2. Burn-in facts (`DATA_FACTS.md` §4): main offices hold 0.289791–0.329159 of all deposits in 1994–2003. In multi-office banks, the median main office holds 0.558262–0.629997 of its own bank's deposits. The largest office is the main office in 0.834024–0.871567 of those banks.
3. The alternative of dropping each bank's single largest branch is almost the same set of rows, because the largest office is usually the main office. It is kept only as a sensitivity (trial 5–6). The upper tail of non-main branches, such as internet branches (service level 13, not flagged in the files), is handled by the grid: it stops at the 99th percentile, so no single branch enters beyond `u = 0.99`.

Normalizing by the national median `M_t` removes nominal growth common to all states. That median is known at the origin for the origin year. It is not used for the target year. A forecast is made on the normalized scale of the target year, and the target is normalized by its own year's `M_{t+1}`. So the forecast is of relative shape and position against the national median, not of dollar levels.

The burn-in object (`SECTION object`) has 62,920 rows (1994) to 74,297 rows (2003). `M_t` runs from 22190.0 to 27459.0 ($000s). All 510 state-years are usable (`USABLE 510`). The smallest is `MIN_N 75`, WY 1994.

## 4. Windows and timing

The forecast origin is September of year `t`, when the June-30 `t` SOD is published. The target is June 30 of `t+1`. Burn-in measures run 1994–2003, so next-year targets are 1995–2003. Out-of-sample targets would have been 2004–2025: `T = 22` years × 51 states, an expanding window, with the first origin in 2003. 2025 is included because its file exists and was published in September 2025. These years were never scored.

## 5. Burn-in gate (thresholds fixed in `GATE_THRESHOLDS_fdic_sod_ot.md` before computing)

### K1 noise floor (CFPB rule)
For each usable state-year, the rows were permuted once with `numpy.random.default_rng(20261009)`, one stream, in (year, state) order, then split `n//2` vs the rest.

- `N_HALF_SPLITS 510`, `N_NEXT_PAIRS 459`
- `MEDIAN_HALF_W2SQ 0.0195766804`
- `MEDIAN_NEXT_W2SQ 0.0078208250`
- `RATIO_NEXT_OVER_HALF 0.3994969939`
- `MEAN_HALF_W2SQ 0.0416537516`, `MEAN_NEXT_W2SQ 0.0208632882`
- `FRAC_PAIRS_NEXT_GT_MEDIAN_HALF 0.1938997821`
- Every one of the nine target years has a median next-year distance below that year's median half-sample distance (`BY_TARGET_YEAR` lines). The closest is 1998, with `0.0134856059` against `0.0180702053`.
- **`K1_MEDIAN_NEXT_LEQ_MEDIAN_HALF True` → kill.**

### K2 / K3 location–scale–shape decomposition
The identity used is `W2SQ = (m1-m2)^2 + (s1-s2)^2 + 2*s1*s2*(1-rho)`, with grid means, grid sds (ddof 0) and the grid correlation. `DECOMP_MAX_ABS_IDENTITY_ERROR 4.344e-15`.

| | LOC share (pooled) | SCALE share | SHAPE share | median LOC | median SCALE | median SHAPE |
|---|---|---|---|---|---|---|
| Next-year pairs | 0.1816440514 | 0.3983749462 | 0.4199810024 | 0.0007485986 | 0.0017652298 | 0.0036937468 |
| Half-sample splits | 0.2351888216 | 0.3021961135 | 0.4626150649 | 0.0022808476 | 0.0031053908 | 0.0093507007 |

- `SHAPE_SHARE_POOLED 0.4199810024`. The threshold was 0.15. **`K2 False`.** Shape is a large share of the year-on-year move, so a location–scale model would not be "all you need" for that reason.
- The median of per-pair shape ratios is `0.5479487535`. Not gating.
- `MEDIAN_NEXT_SHAPE 0.0036937468` ≤ `MEDIAN_HALF_SHAPE 0.0093507007`, ratio `0.3950235363`. **`K3 True` → kill.** The shape part of the move is real as a share, but it is smaller than the shape wobble between two random halves of the same state-year.

`GATE_STATUS KILLED_AT_BURNIN`.

### What the kill means, and one caveat recorded without changing the result
Within a state, a year-on-year change in the deposit distribution is smaller, on this grid, than the difference between two random halves of that state's branches in a single year. On this rule the object is too stable relative to its own sampling noise.

Caveat, recorded honestly. Branches persist from year to year, so consecutive full-sample curves share most of their atoms. The half-split benchmark treats a state's branches as a sample from a "law". It is also roughly twice the sampling variance of one full-sample curve. Someone could argue that the forecast target is the finite realized population, not a law, and that the rule is therefore conservative here. That argument does not reopen the design, for two reasons. First, the rule and the threshold were the ones pre-stated, copied from CFPB, and written before computing. Second, the median next-year distance (`0.0078208250`) is below even half of `MEDIAN_HALF_W2SQ`. That is a qualitative comparison of two printed numbers, and no new statistic was computed for it. Independently, §6 shows the forecast-comparison test has almost no power. A rescue would therefore produce an uninformative test, not a useful one.

## 6. Planning power (label: PLANNING; not an out-of-sample result)

**Calibration proxy (burn-in only).** No forecasting method was fit. A stand-in loss differential was built from two burn-in baselines: `d = L(B0) - L(B1)`. B0 is last year's curve. B1 is the state's expanding mean of earlier years, which needs at least 2 history years. Targets are 1996–2003 (`T_PROXY 8`, N = 51). Results:

- `MEAN_LOSS_B0 0.0218412883`, `MEAN_LOSS_B1 0.0341400439`
- `SD_YEAR 0.0080504647` (net of sampling), `SD_IDIO 0.0377645926`, `YEAR_SHARE_OF_VAR 0.0434682043`
- `DESIGN_EFFECT_ratio_var_of_yearmean_vs_iid 3.1734102131`
- `AR1_YEAR_MEAN_SERIES_PHI 0.2305120954` (8 points), `AR1_POOLED_WITHIN_STATE_PHI_IDIO 0.4503791505`, `AR1_B0_YEARLY_MEAN_LOSS_PHI 0.6052004214`

**Simulated DGP.** `d_{s,t} = mu + g_t + e_{s,t}`. `g` is a common year shock, AR(1). `e` is an idiosyncratic state term, AR(1) within state. Both are Gaussian, `T = 22`, `N = 51`, with the calibrated sds and phis (each phi clipped to [0, 0.9]). `mu = gain × 0.0218412883`; the burn-in mean B0 loss stands in for the B-star mean loss. `REPS 4000`, seed 20261009.

**Tests.**
- **A (pre-registered primary):** the CFPB statistic on the yearly cross-state mean `dbar_t`. Fixed-b Bartlett HAC with `L = 4`. Critical values come from a simulated null at the AR(1) coefficient estimated on that same `dbar_t`, interpolated on a phi grid (20,000 null draws per grid point, printed `NULL_CV_TABLE`). With a balanced panel and equal weights, this is the Driscoll–Kraay test.
- **B:** the pooled state-year mean with state-clustered SE against `t_50` (`CV95 1.6748`, `CV975 2.0092`). A state-block bootstrap targets the same variance and is not simulated separately.

| Block | gain 0.00 A@5% / B@5% | 0.02 A@2.5% | 0.05 A@2.5% | 0.10 A@2.5% | 0.20 A@2.5% | 0.30 A@2.5% |
|---|---|---|---|---|---|---|
| CALIBRATED | 0.0643 / 0.1403 | 0.0498 | 0.0705 | 0.1288 | 0.3015 | 0.5327 |
| PHIY 0.0 | 0.0658 / 0.1110 | 0.0527 | 0.0840 | 0.1545 | 0.3800 | 0.6488 |
| PHIY 0.5 | 0.0675 / 0.1847 | 0.0512 | 0.0683 | 0.1115 | 0.2313 | 0.4065 |
| PHIY 0.85 | 0.1212 / 0.2908 | 0.0985 | 0.1180 | 0.1537 | 0.2417 | 0.3518 |
| SDYEAR ×2 | 0.0597 / 0.2567 | 0.0418 | 0.0535 | 0.0785 | 0.1505 | 0.2532 |
| SDYEAR ×0.5 | 0.0665 / 0.0770 | 0.0545 | 0.0950 | 0.1800 | 0.4725 | 0.7372 |

- `POWER_PRIMARY_A_AT_GAIN_0.05_2.5PCT 0.0705` → **`UNDERPOWERED True`** under the pre-stated power rule (threshold 0.50).
- `SMALLEST_GAIN_IN_GRID_POWER80_A_2.5PCT NONE_UP_TO_0.30`. Even a 30% gain has power `0.5327`.
- **The state-clustered panel test is not valid as primary.** Its size at 5% nominal is `0.1403` under the calibrated year shocks (`B_ELIGIBLE_AS_PRIMARY False`, pre-stated limit 0.075), and `0.2908` when the year shock is persistent (phi 0.85). The year component is only `0.0434682043` of the differential's variance. But with 51 states, the year shock still triples the variance of the yearly mean (design effect `3.1734102131`), and a state-clustered SE cannot see it. Breadth across states does not replace years: the effective sample size for an unconditional claim is still about 22 years. Test B answers a narrower question, conditional on 2004–2025, and even there it over-rejects in the simulation. Its power at 2.5% (0.1855 at a 5% gain) is mostly that over-rejection.
- Test A is close to its nominal size (0.0643 at 5% calibrated). Its size rises to 0.1212 at phi_year 0.85: at T = 22, the estimated AR coefficient is biased toward zero.

**Proxy caveat.** Power depends on `sd(d)` relative to the loss scale. B0 − B1 is a large, noisy contrast. A forecaster that sits close to B-star, such as WAR shrinking last year's curve slightly toward the barycenter, would give a less variable `d`. That would mean more power at the same relative gain than shown. The burn-in cannot measure that without fitting the methods, which this file does not do. The power result is therefore a planning statement, not a proof of futility. The kill rests on K1 and K3. Power is a second, independent reason not to proceed.

## 7. Methods, specified so they can be coded, not fit

Nothing in this section was estimated. The grid and isotonic rule are the same as CFPB: every forecast quantile function is made nondecreasing by PAVA (equal weights, 99 points) before scoring. Only years `<= t` are used at origin `t`.

- **B0 (no change):** `Q_{s,t}`.
- **B1 (expanding Fréchet mean):** the average of `Q_{s,τ}` for `τ <= t`. In 1-D this is the W2 barycenter.
- **B2 (quantile-shift location–scale):** `m̂ + ŝ · (Q_{s,t} - m_{s,t}) / s_{s,t}`. `m` and `log s` are the grid mean and grid sd of the state curve. `m̂` and `log ŝ` are forecast by AR(1) with intercept, pooled across states over adjacent year pairs `<= t`, with the AR coefficient clipped to [−0.99, 0.99].
- **B3 (Gaussian location–scale):** the same AR forecasts, with quantiles `m̂ + ŝ Φ^{-1}(u_k)`.
- **B-star:** among the defined baselines, the one with the lowest mean cross-state loss over the trailing 5 scored years (minimum 3). Ties go to B0, then B1, B2, B3. It is re-selected at every origin using past scores only.
- **H1 (primary): pooled Wasserstein AR(1) around the yearly barycenter.** `Q̄_τ` = the average over usable states of `Q_{s,τ}`. Log map `L_{s,τ} = Q_{s,τ} - Q̄_τ`. One slope `β = Σ L_{s,τ} L_{s,τ-1} / Σ L_{s,τ-1}^2`, stacked over states, grid points and adjacent pairs with `τ <= t`, no intercept, clipped to [0, 1]. Forecast `Q̄_t + β L_{s,t}`, which treats the barycenter as a random walk, then isotonic. Citation: *Wasserstein autoregressive models for density time series*, Journal of Time Series Analysis 43(1), 2022, DOI 10.1111/jtsa.12590, arXiv:2006.12640.
- **H2 (primary): Wasserstein (tangent-space) regression on state deposit growth.** `g_{s,t} = ln(total deposits_{s,t}) − ln(total deposits_{s,t−1})`, with all rows including main offices, minus the same national growth. `g` is lagged: it is known at origin `t`. For each grid point `k`, pooled OLS of `Q_{s,τ+1}(u_k) − Q_{s,τ}(u_k)` on `[1, g_{s,τ}]` over pairs with `τ+1 <= t`. Forecast `Q_{s,t} + a_k + b_k g_{s,t}`, then isotonic. Citation: *Wasserstein regression*, Journal of the American Statistical Association, 2021, DOI 10.1080/01621459.2021.1956937, arXiv:2006.09660. Background (before 2020): *Fréchet regression for random objects with Euclidean predictors*, Annals of Statistics 47(2), 2019, DOI 10.1214/17-AOS1624.
- **Gain** `G = 1 − mean(loss_method)/mean(loss_B-star)` on paired state-years. **Hurdle** `G > 0.02`.
- **Statistic:** test A in §6, computed on the yearly cross-state mean of `d = loss(B-star) − loss(method)`. One-sided. Runtime p-value from the AR(1)-simulated null at the estimated phi (100,000 draws, seed 20261009). Phi outside (−0.99, 0.99) means `INCOMPLETE`.
- **Holm:** family {H1, H2} vs B-star, familywise 0.05, thresholds 0.025 then 0.05.
- **PASS** requires all of: a Holm rejection, `G > 0.02`, `G > 0` in at least 2 of 3 subperiods (2004–2010, 2011–2018, 2019–2025), at least 20 paired years, and at least 45 usable states in at least 90% of OOS years.

## 8. Trials (pinned count; every run counts)

`TRIAL_COUNT 10`. None will be run, because of the kill.

1. H1 vs B-star (primary, gates).
2. H2 vs B-star (primary, gates).
3. H1 with main offices included (sensitivity).
4. H2 with main offices included (sensitivity).
5. H1 with each CERT's largest-deposit branch in the state excluded instead of `BRNUM == 0` (sensitivity).
6. H2 with that same trim (sensitivity).
7. **F1 falsification (Y-9C F1 analogue):** equal-weight linear pool (CDF mixture) of {B0, B1, B2, B3} vs their W2 barycenter (quantile average). If the linear pool has G ≥ G(barycenter), the reading is "combination helps; W2 geometry not shown to matter". Barycenter citation: Entropy 22(9):929, 2020, DOI 10.3390/e22090929. The quantile average is the unregularized 1-D case, not the paper's entropic barycenter.
8. H2m: transport-map AR, `a + b Q_{s,t}` pooled, `b` clipped to [0, 2]. Restricted 1-D form from *Autoregressive optimal transport models*, arXiv:2105.05439 (arXiv 2021, v4; journal not confirmed per the notes). Not a reproduction of the paper.
9. H1 with test B (state-clustered, conditional on years). Non-gating, labelled invalid for unconditional inference per §6.
10. H2 with test B. Same labels.

Not used: *Distribution-on-distribution regression via optimal transport maps*, arXiv:2104.09418. It is noted only as a possible future estimator. *Short-term forecasting with optimal transport*, JRSS-A 189(2), 2026, DOI 10.1093/jrsssa/qnaf036, is a nowcasting design with a dynamic factor model; it does not fit annual state distributions and is not used.

## 9. Leakage and exposure log

- **Reads.** The gate script read only 1994–2003 (`YEARS_READ`). The facts script read all 32 files, but printed only structural counts for 2004–2025. Those are row counts, CERT counts, `BRNUM == 0` counts, counts of DEPSUMBR = 0 and > 0, the units match fraction, state codes, and null counts. No quantile, median, mean, Wasserstein distance or deposit total for any year after 2003 was computed in this study.
- **Exposure taken in this study:**
  - structural counts for all years (above);
  - first two data rows of the 1994, 2010 and 2025 files, printed to check headers (two named banks' deposits);
  - an unsaved interactive run of the units probe, later saved and rerun verbatim as `units_probe_burnin.py`, on 1994 and 2003 only;
  - one fetch of the FDIC SOD reporting instructions (June 2026 edition) and one web search about them.
- **Exposure taken before this study:** the 2026-10-08 inventory memo printed 1994 and 2024 national median log10 branch deposits (4.39, 4.90), counts, the largest 2024 branch ($641B, 3.7% of deposits), and a 3–6% zero-deposit share. The README quotes 2025 top-holder totals. These are listed in `DATA_FACTS.md` §5.
- **Snapshot.** One API pull dated 2026-10-06. Revisions to past SOD years are unknown. A backtest would have been pseudo-real-time. That is a limitation, not the reason for the kill.

## 10. Authorization

`oos_authorized` is false in the design JSON and is not the switch. Following the Y-9C lesson (`/workspace/research/y9c_ot_prereg/OOS_APPROVAL_v1_1.json`), a separate approval file would authorize a run. Because the gate killed this object, even such a file would not start an out-of-sample run of this design. A different object would need its own pre-registration. No engineering ticket was drafted: the request was conditional on clearing, and it did not clear.

## 11. Constraints

Classical statistics only. No pretrained model and no neural net. The out-of-sample window stays closed. The negative burn-in result is the result this file pins.
