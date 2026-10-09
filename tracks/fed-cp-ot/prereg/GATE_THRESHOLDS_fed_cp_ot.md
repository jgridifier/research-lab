# Gate thresholds and pinned rules: Fed CP issuance maturity mix (applied lab)

**Written:** 2026-10-09, before any weekly mix, Wasserstein distance, split, loss, baseline forecast or
power simulation of this object was computed, and before any RATES (spread) value was parsed.
**Already seen when this was written (disclosed):** `compute_cp_facts.stdout.txt` contains:
- structure for all dates: series ids, observation and zero counts per series over 2001–2026,
  missing dates, consistency match fractions;
- burn-in-only (2001–2008) weekly issue counts, mean bucket shares and issue sizes.

It also contains the inventory memo of 2026-10-08, which noted sparse FIN buckets on 2026-10-01.
Nothing else was seen.

**Mandate (2026-10-09 steering):** applied lab, meaning a working paper plus a daily app. OT is one
candidate among several. A burn-in kill ends the **OT claim only**. Three separate verdicts are printed.

## 0. Data and object
- **Source:** the VOL dataset of `CP_data.xml` inside `FRB_CP_xml.zip` (Drive id
  `1kIy2Z8EuYz85CokrZpBZR_WqNHKI-Mio`). The derived CSV is NOT used, because its NONFIN rows drop the
  AA/A2P2 tier.
- **Missing values:** `OBS_STATUS="ND"` or `OBS_VALUE=-9999` is treated as missing.
- **Primary issuer types (4):** AAA (AA asset-backed), FAA (AA financial), NAA (AA nonfinancial),
  NA2 (A2/P2 nonfinancial). MKT (`M`) is excluded from the primary object, because it is not the sum of
  the four. It is used only as a stress comparator.
- **Week:** Monday–Friday, labelled by its Friday (`W-FRI`). For type τ and week w:
  `D_b` = sum of the daily `*.AMT` values; `N_b` = sum of the daily `*.VOL` values (number of issues),
  over the valid days of that type in that week.
- **Usable type-week:** at least 3 valid days, `sum N_b >= 100`, and `sum D_b > 0`.
- **Object:** the dollar mix `p_b = D_b / sum D`, a discrete law on 6 ordered points.
- **Ground metric (primary):** `x_b = ln(sqrt(lo_b*hi_b))` days, with `(lo,hi)` = (1,4), (5,9),
  (10,20), (21,40), (41,80), (81,270). The 270-day cap comes from the Fed CP "About" page: "The Federal
  Reserve Board only considers maturities of 270 days or less." The reason for log-days: a location
  shift is then a proportional change in maturity, so "duration" has a meaning.
- **Sensitivity metric:** rank, `x_b = 0..5`.
- **Distance:** `W2SQ` is the exact squared 2-Wasserstein distance between step quantile functions
  (breakpoints merged).

## 1. Windows
- Burn-in: weeks ending 2001-01-05 through 2008-12-26.
- OOS: weeks ending 2009-01-02 through 2026-10-02.
- A calm sub-burn-in (weeks ending 2001–2006) is printed but never gates.
- Why the burn-in includes 2007–08: the gates and the model-selection warm-up then see both a calm
  market and the ABCP/Lehman stress. Otherwise the first OOS stress would be out of distribution. The
  cost is that two of the stress events fall inside the burn-in (see §6).

## 2. OT-claim kill rules (any one fires => OT_CLAIM = KILLED)
- **K1 (issue-level half split; gating).** For each usable type-week:
  - counts `c_b = N_b`, average issue size `a_b = D_b/N_b` (0 where `N_b = 0`);
  - draw `c1 ~ multivariate hypergeometric(c, floor(N/2))`, `c2 = c - c1`;
  - half mixes `∝ c1*a` and `∝ c2*a`;
  - `numpy.random.default_rng(20261009)`, one stream, in (type, week) order.

  `MEDIAN_HALF` = the median W2SQ between the two halves. `MEDIAN_NEXT` = the median W2SQ between
  usable type-weeks w and w+1 (consecutive weeks). Kill if `MEDIAN_NEXT <= MEDIAN_HALF`. This floor
  ignores the spread of issue sizes within a bucket, so it **understates** sampling noise. That makes it
  lenient toward the OT claim. Disclosed.
- **K1b (half-week day split; NON-gating, printed).** Days 1,3,5 vs days 2,4 of each week. Day-of-week
  effects inflate this split, and those effects are averaged out in the weekly object, so it is biased
  against the object and does not gate.
- **K2 (location–scale explains nearly all).** `W2SQ = LOC + SCALE + SHAPE`, using the exact moments
  of the step quantile functions. Kill if the pooled `SHAPE` share of next-week W2SQ is `< 0.15`. The
  LOC-only share is also printed.
- **K3.** Kill if the median next-week `SHAPE` is `<=` the median K1 half-split `SHAPE`.
- **K4 (power).**
  - Proxy: `d_w` = mean over the usable types of `[L(P) - L(MA4)]` on burn-in targets, where
    MA4 = the W2 barycenter of the last 4 usable weeks.
  - Gain scale: `min` of the burn-in mean losses of P, MA4 and EXP.
  - Two DGPs at `T` = the number of calendar OOS weeks:
    - (G) Gaussian AR(1) at the burn-in OLS phi and residual sd of `d`;
    - (B) a stationary block bootstrap (mean block 13 weeks) of the demeaned burn-in `d`.
  - Test: one-sided fixed-b Bartlett HAC with `L = floor(sqrt(T))`. The critical value is simulated
    under a mean-zero AR(1) at the phi estimated on the same series (CFPB rule), interpolated on a
    phi grid.
  - Kill if `min(power_G, power_B)` at relative gain **0.05** and one-sided **2.5%** is `< 0.50`.
  - Seed 20261009. 2000 reps; 20000 null draws per phi grid point.

## 3. DATASET_USABLE (yes iff all hold)
- (a) The XML holds NAA and NA2 as separate series for amounts and counts.
- (b) The CSV NONFIN pairs equal {NAA, NA2} in at least 99.9% of keys. This confirms that the CSV
  defect is tier loss and that the XML repairs it.
- (c) Each of the 4 types has at least 95% usable weeks in the burn-in.
- (d) Each of the 4 types has at least 3 valid days in at least 95% of OOS calendar weeks. This is a
  structural day count only; no amounts are read.
- (e) The public source URL answers HTTP 200: `https://www.federalreserve.gov/releases/cp/data/FRB_CP_xml.zip`
  (checked 2026-10-09).

## 4. FORECASTABLE_SIGNAL (any method; burn-in only)
- Baselines, scored on the cross-type mean weekly W2SQ:
  - P (last usable week);
  - EWMA of the quantile functions, with `alpha` in {0.1, 0.2, 0.3, 0.5}, chosen on targets
    2002–2004 (ties go to the smaller alpha);
  - EXP (expanding barycenter).
- Evaluated on targets 2005–2008.
- **SIGNAL = yes** iff `min(meanL_P, meanL_EWMA) <= 0.90 * meanL_EXP`. Also printed: the P vs EWMA
  ratio, a fixed-b Z (descriptive), and the 2005–2006 subwindow.

## 5. Forecasting design pinned now (fit later, never on OOS before approval)
- **Candidates:**
  - P;
  - EWMA (alpha grid above);
  - EXP;
  - LS: location–scale on log-duration. AR(1) on the mix mean and on the log sd of `x`; forecast law
    = normal on log-days, discretized to the bucket edges `ln(lo)`, `ln(hi)` with tails folded into the
    end buckets;
  - ALR-AR: ALR with the 1–4-day bucket as reference; zero shares replaced by 1e-4, then renormalized;
    AR(1) per coordinate;
  - ALR-VAR(1) by OLS;
  - MNL-AR: fractional multinomial logit on lagged ALR, quasi-ML by Newton in NumPy;
  - RIDGE: lagged ALR (lags 1–4) mapped to next-week ALR, with lambda in {0.1, 1, 10, 100};
  - WAR: WAR(1) on quantile functions around the expanding barycenter, one slope per type clipped to
    [0, 1], then isotonic. JTSA 2022, DOI 10.1111/jtsa.12590;
  - TMAR: transport-map AR `a + b·Q_prev`, with `b` in [0, 2]. arXiv:2105.05439.

  All are fit per type, on an expanding window, using data at or before the origin.
- **Selection rule (SEL, pins the shipped app model):**
  - At each origin, every candidate's trailing one-step pseudo-OOS losses over the last 156 usable
    weeks are compared, and the lowest mean wins.
  - Selection is redone every 13 weeks (the first origin of each calendar quarter).
  - Ties within 1% relative go to the earlier entry in the list above (the simpler model).
  - Hyperparameters are chosen the same way from the pinned grids.
  - The first selection window is weeks ending 2006–2008, inside the burn-in.
- **Family A (OT claim):** WAR and TMAR each vs B*, where B* = the best non-OT candidate under the
  same trailing rule. Holm at 0.05 one-sided (0.025, then 0.05).
- **Family B (app claim):** SEL vs P, one test, alpha 0.05 one-sided.
- **Common rules for both families:**
  - Statistic: the K4 statistic on weekly cross-type mean differentials.
  - Runtime p-value from 100000 AR(1) null draws at the estimated phi; phi outside (−0.99, 0.99)
    makes the test INCOMPLETE.
  - Hurdle `G > 0.02`, and `G > 0` in at least 2 of the 3 OOS subperiods (2009–2014, 2015–2020,
    2021–2026).
  - At least 800 paired OOS weeks.
- **If Family B fails,** the app headline is P and SEL is labelled experimental.
- **If K1–K4 kill the OT claim,** WAR and TMAR stay in the candidate list as ordinary candidates, but
  no OT-superiority claim may be made.

## 6. Stress early-warning study (pinned; DESCRIPTIVE ONLY, never gating)
- **Events, with reference dates from published sources:**
  - E1 2007-08-09: BNP Paribas suspends three funds (St. Louis Fed Financial Crisis Timeline).
  - E2 2008-09-15: Lehman files (same timeline). Reserve Primary breaks the buck 2008-09-16.
  - E3 2020-03-17: Fed announces CPFF (Fed press release monetary20200317a).
  - Sensitivity E4 2023-03-10: SVB closed (FDIC PR-16-2023; DFPI order). E4 is not a CP-market event;
    it is reported separately.
  - E1 and E2 lie inside the burn-in, so only E3 (and E4) are OOS. There are too few events for a
    gated test.
- **Signals, weekly, each on data at or before week w only:**
  - S_OT: W2SQ between the week-w mix and the barycenter of weeks w−13..w−1, averaged over AAA and FAA;
  - S_VOL: minus the log ratio of the week-w MKT total amount (sum of `MKT.*.AMT`) to its trailing
    13-week mean;
  - S_SPR1: the weekly mean of `RIFSPPNA2P2D30_N.B − RIFSPPNAAD30_N.B`;
  - S_SPR2: the weekly mean of `RIFSPPAAAD30_N.B − RIFSPPNAAD30_N.B`.
- **Alarm:** S_w exceeds the expanding 99th percentile of S over weeks ≤ w−1. At least 104 weeks of
  history are needed.
- **Metrics per event e:**
  - window `[e−13w, e+4w]`;
  - hit = any alarm in `[e−13w, e+1w]`;
  - lead time = e week − first alarm week in `[e−13w, e+4w]`, in weeks (negative = late);
  - false-alarm rate = alarm weeks outside every `[e−13w, e+13w]`, per year.
- Reported for all signals. No p-value gates. Nothing is computed in this pre-registration.

## 7. Seeds
20261009 everywhere, restarted per block.
