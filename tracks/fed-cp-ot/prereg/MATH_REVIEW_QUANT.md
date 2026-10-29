# Quant math review: Fed CP funding OT track (PR #11, commit dce8b33)

Reviewed 2026-10-29 (ET). Scope: PREREG, GATE_THRESHOLDS (sha256 c15eb60c… verified against the research copy), DATA_SPEC, ENGINEERING_TICKET, PIN.txt, and `fed_cp_ot/*.py`. Test suite: 129 passed, 4 skipped (data-dependent). Not done: OOS was not unsealed or run, no gate was rerun, and no APPROVAL file was written.

**Verdict: CHANGES REQUIRED before OOS approval.** The burn-in gate math and the leakage wall are sound. The changes are to the specification of the forecasting/test stage (§5). They have to be pinned in a PREREG v2 **before** the harness is built, not discovered while it is being built.

## What checks out
- **W2² on step quantile functions** (`metric.py`). Merging the breakpoints and evaluating each quantile function at segment midpoints gives the exact integral ∫(Q1−Q2)². `c[-1]=1` removes float drift at the top of the cumsum.
- **Decomposition.** `SHAPE = s1²+s2²−2cov−(s1−s2)² = 2·s1·s2·(1−ρ) ≥ 0`, so LOC+SCALE+SHAPE = (m1−m2)² + Var(Q1−Q2) = W2² exactly. The reported identity error is 2.2e-15.
- **Barycenters.** The 1-D W2 barycenter is the weighted average of quantile functions, which is correct. The EWMA/EXP recursions in `burnin_checks.replicate` (`qmix(q,ew,.2)`, `qmix(q,exp,1/n)`) are the correct recursive weights.
- **K1 half split.** A multivariate hypergeometric draw on bucket counts with mean-size reweighting is a valid (lenient, disclosed) sampling-noise floor.
- **K4.** L = floor(√927) = 30 matches. The fixed-b critical value is simulated at the estimated φ, which is appropriate for a Bartlett HAC with b = L/T ≈ 0.032.
- **Citations verified** (Crossref/arXiv):
  - Zhang, Kokoszka, Petersen, "Wasserstein autoregressive models for density time series", JTSA, 10.1111/jtsa.12590 (online 2021, issue 2022);
  - Zhu & Müller, "Autoregressive Optimal Transport Models", arXiv:2105.05439;
  - Petersen & Müller, AoS 2019, 10.1214/17-AOS1624;
  - Chen, Lin, Müller, "Wasserstein Regression", JASA 2021, 10.1080/01621459.2021.1956937.
- **Leakage.**
  - `parse_vol` validates post-wall values as text only and never converts them to float.
  - `build_weekly`, `provisional_partial_week`, `record_outcome` and `score` all go through `check_wall`.
  - `origin_view` deep-copies arrays and drops weeks after the origin.
  - The forward log is a hash chain. It enforces Friday origins with target = origin+7, rejects `input_max_date > origin`, and requires issue time ≥ next-Fed-business-day 13:00 ET after the origin and < the same time after the target. An outcome must post after every forecast for its key, and keys cannot be edited.
- **Burn-in reproducibility.** `burnin_checks.replicate` re-derives median_next, LOC/SCALE/SHAPE, P/EXP/MA4/EWMA0.2, N_NEXT = 1664, 417 usable weeks per type, and identity error < 1e-12, all to 10 dp.

## Findings (numbered)
1. **[Blocker] WAR/TMAR forecasts are not 6-share mixes.**
   - WAR and TMAR (`a + b·Q_prev`, isotonic) produce quantile functions whose values lie *off* the 6 support points.
   - `ForwardLog.record_forecast` and `score` accept only a 6-share `mix` (`_mix`, `q_from_p(mix, X_LOG)`).
   - So either OT forecasts must be projected onto the support, which changes the model and needs a pinned projection (e.g. the W2-nearest law on X_LOG, i.e. assigning each quantile mass to the nearest support point), or the log/score must accept a step quantile function `(c, v)`.
   - Pin one in PREREG v2. Otherwise Family A compares unlike objects.
2. **[Blocker] The hurdle `G` is undefined in GATE §5.**
   - Pin the definition, e.g. `G = 1 − mean L(cand)/mean L(comp)` over the paired OOS weeks, and the per-subperiod version.
   - State whether "≥800 paired weeks" counts weeks where all 4 types are usable or weeks with any usable type.
3. **[Major] The LS discretization edges have gaps.** The buckets are integer-day ranges (4→5, 9→10, …), so "edges ln(lo), ln(hi)" leave unassigned mass. Pin the cut points, e.g. ln(4.5), ln(9.5), ln(20.5), ln(40.5), ln(80.5), with tails folded.
4. **[Major] Leakage residual: vintage content vs origin.**
   - `input_max_date` is self-reported. A vintage fetched Mon–Thu of the target week already contains target-week days.
   - The harness should build the history with `build_weekly(vol, through=origin)` from the named vintage, and recompute and assert `input_max_date` from the frame actually passed to `fit_predict`, rather than trusting the caller.
   - Add a test that injects target-week days into the vintage and asserts the forecast is unchanged.
5. **[Major] K4 knife-edge.**
   - Power is 0.5015 against a 0.50 threshold, with MC SE ≈ 0.011. The pinned seed decides the result, which is legitimate, but record it in the paper.
   - The planning power at a 5% gain is about a coin flip. A null Family A result must be reported as "underpowered for 5%", not as "no gain".
6. **[Minor] The gain scale differs between documents.** GATE says min(P, MA4, EXP) and PREREG reports 0.17873 as "the MA4 mean loss". These agree only if MA4 is the minimum over the full burn-in. State that explicitly.
7. **[Minor] K1/K4 are not replicated in-track.** `burnin_checks` reproduces only the deterministic numbers. The ticket's acceptance criterion (byte-for-byte `compute_cp_ot_burnin.stdout.txt`, sha 17a0b239…) needs a CI job that runs the pinned script (seed 20261009, one RNG stream in (type, week) order) on the pinned zip.
8. **[Minor] Numerical edge cases.**
   - (a) `q_from_p` divides by `p[k].sum()`. It is safe only because usable weeks have D > 0. Add a guard and a test for the all-zero and single-atom cases (SCALE = 0, so SHAPE = 0).
   - (b) `decomp` takes sqrt(max(var, 0)), which is fine.
   - (c) For ALR, the 1e-4 replacement is applied to the shares and then the result is renormalized. Pin that the *forecast* is mapped back through softmax and is not clipped. The 1e-4 floor biases GT80 shares for FAA, so report it.
   - (d) The φ grid interpolation must reject |φ| ≥ 0.99 (INCOMPLETE). Assert this in the harness.
   - (e) Holiday weeks with fewer than 3 valid days are unusable. P and MA4 must use the "last usable week", and for SEL, "156 usable weeks" means the window spans more than 156 calendar weeks. Pin it.
9. **[Minor] B\* is time-varying.** B* is re-selected every 13 weeks. Pin that the Family A differential uses the B* chosen at each origin (a forecast-level comparator), not the ex-post best.
10. **[Note] `oos_authorized` / approval.** `check_oos_approval` needs `APPROVAL_SHA256` pinned in code. That requires a code change after the user writes the approval, so state in the ticket which PR sets it.

No finding invalidates the burn-in gate verdicts.
