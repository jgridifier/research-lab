<!-- quant-scout-bot -->
# 2026-11-17 feedback follow-ups: what we will run, and what counts as a pass (written before any run)

Written 2026-11-17 (ET) by the lab agent in response to Jared's comments on scout issues #63, #60, #53 and #50.
This file is merged **before** any of the analyses below is run. Changes after merge go in a dated addendum at the
bottom; the text above it is never edited. Self-written; not independently reviewed before merge (stated honestly).

Common rules: public data or SYNTHETIC mocks only; no raw private rows published; Y-9C work is descriptive model
comparison only (no firm-level predicted payouts are published, nothing touches the pre-registered Y-9C trading study);
no neural nets; nothing is promoted into analysis-skills.

---

## A. pim (#63, Q3): ARDL and SARIMAX benchmarks beside OLS

Jared: "can you add an ARDL/Sarimax Benchmark?" … "If the benchmark with ARDL/Sarimax looks promising, then let's do
it with the Eng and Math enhancements."

**Data.** `q3_pim_panel.csv` rebuilt unchanged by `runs/2026-11-16/pim/prep_q3.py` (360 firm-years, 40 firms,
2013–2025). Previous-year payout y_{i,t−1} is taken from the same lab Y-9C payout file for year t−1 (it exists whether or
not the firm was tested in t−1). Stress metrics: severely adverse CET1 drawdown and pre-tax income (year-t test).

**Outcomes.** Y1 = payout/RWA (primary). Y2 = payout/net income (secondary; the heavy-tailed ratio where OLS was fragile).

**Held-out-year design (no leakage).** Test years 2016–2025. For test year T, every model is fitted on rows with
year < T only, then scores the firms tested in year T. Scaling, if any, is fitted on training rows only.
This is a model-comparison check, not a forecast; no predicted value for any firm is published.

**Models.**
1. OLS (static): pooled OLS of y on {drawdown, pre-tax}.
2. PIM (static): pim 2.0.4, within-year pairs, logit link, difference model, same two covariates (as on 11-16).
3. ARDL(1,0), pooled panel: y_t = a + φ y_{t−1} + β′x_t + e, OLS on training rows.
4. SARIMAX, per firm: statsmodels SARIMAX(y, exog = {drawdown, pre-tax}, order (1,0,0), trend 'c'); no seasonal part
   (annual data). Fitted on the firm's own tested years before T in time order (gaps for biennial testers are skipped,
   stated). Feasible only when the firm has ≥ 5 training years; it is evaluated on that feasible subset.
5. PIM-dyn: PIM on {y_{t−1}, drawdown, pre-tax} (the same information as ARDL).

**Metric.** Within-year concordance C: over all test years, over all pairs of firms in the same test year with
different realized y, the share where the model orders the pair the same way (a predicted tie counts 0.5). Per-year C
and, for level models, MAE are reported too. Uncertainty: 999 firm-block bootstrap resamples of the fixed predictions,
90% interval for each difference in C.

**"Promising" (decided now).** Both must hold:
- (a) On Y1: C(PIM-dyn) − C(ARDL) ≥ −0.02 on all rows, **and** C(PIM-dyn) − C(SARIMAX) ≥ −0.02 on SARIMAX's subset.
- (b) On Y2: C(PIM-dyn) ≥ C(ARDL) and C(PIM-dyn) ≥ C(SARIMAX) (same subsets).

If promising: start the Engineering (streaming within-block PIM fitter, pim as oracle) and Math (firm × year clustered
variance, coverage simulation) avenues as written on the issue. If not: stop and say so.

Descriptive extra (no pass/fail): ARDL long-run multiplier of drawdown on Y2, β/(1−φ), with and without the same 2% trim
used on 11-16, beside the OLS (−43%) and PIM (<2%) shifts.

---

## B. kairos/tabula (#60, Q1 + Q2): refresh, mock datasets, more open datasets, worth-building verdict

Jared: "refresh the page with the tests/questions we have now, want to see it on our mock datasets and more of the open
datasets to tell if it's worth building."

**Open datasets (Q1.4 / Q1.5 family; public lab copies).** Monthly compositions, each treated like a pottery count table:
- O1 OFR venue × tenor volumes (the 11-15 reference, rerun unchanged).
- O2 OFR tri-party collateral mix (Treasury, agency, corporate debt, other), transaction volume, 2014-08 onward.
- O3 CFTC TFF Treasury-futures positioning mix: open interest by trader type × side (dealer, asset manager, leveraged
  funds, other reportables, non-reportables; long and short) summed over the 2Y/5Y/10Y/bond/ultra contracts.
- O4 Fed commercial-paper issuance by maturity bucket (all issuers), 2001 onward.
- O5 Treasury marketable debt by security type (bills, notes, bonds, TIPS, FRN; MSPD), 2001 onward. FRNs start in 2014: a
  real taxonomy addition.
- O6 Form PF (tab 8.27) borrowing by creditor type, monthly.

**Tests per open dataset (decided now).**
- T1 seriation exists: Porčić (2013) `assess`, 1,000 random orders, p < 0.05.
- T2 the clock dates unseen months: walk-forward, train on the first 60% of months, date the rest with the Bellanger–Husi
  event model. Baselines: naive (last training date) and the usual tool (ridge regression of date on clr shares, penalty
  chosen by leave-one-out on training rows). Pass iff clock MAE ≤ 0.75 × naive MAE **and** clock MAE ≤ ridge MAE.
- T3 Q1.4 link: Form PF total borrowing growth (12-month log change) leads clock speed (12-month change in mix date) at
  leads 3 and 6, circular-shift null (2,000 shifts, ≥ 12 months), Holm across every (dataset × lead) test run here.
  O6 is excluded from T3 (it is Form PF itself).

**SYNTHETIC mock datasets (Q2; Corning- and Morgan Stanley-modeled ZBB mocks, generator seed 20261113).** Rows =
programs, columns = fiscal years 2020–2025, cells = actual spend: each program's spend profile over time.
- M1 seriation exists (Porčić p < 0.05).
- M2 Q2.4 structure: for each planted latent cluster with ≥ 20 members, AUC of the program's CA axis-1 score for cluster
  membership (reported as max(AUC, 1−AUC), the same for both methods, since the sign of a CA axis is arbitrary),
  against the usual tool, the OLS slope of log actual on year. Pass on a mock iff mean AUC over its clusters ≥ baseline
  mean + 0.03. The answer key (`ground_truth.json`) is used only for scoring.
- M3 (descriptive) Q2.5 "seeing it": a battleship (EPPM) chart of all programs ordered by seriation.

**Worth-building verdict (decided now).**
- **Worth building** (Python port + taxonomy-robust clock) iff T2 passes on ≥ 3 of O2–O6 **and** (M2 passes on both mocks
  **or** at least one T3 test survives Holm).
- **Chart tool only, don't build** iff T2 passes on 1–2 of O2–O6, or on ≥ 3 without the second condition.
- **Not worth building** iff T2 passes on none of O2–O6.

---

## C. Lovell proportionality (#53): Math + Engineering

Jared: "Math + Eng". Read as: go ahead with the Math and Engineering avenues (not New use).

**Math: is market-partial ρ size-correct?** Simulation; seed 20261117; R = 1,000 replications per cell.
- D = 14 parts, T ∈ {40, 62}. Log-abundance of part j: l_tj = λ_j z_t + v_tj (+ swap). Market z: AR(1) φ = 0.9, unit
  innovations. Idiosyncratic v: AR(1) φ = 0.8, innovation sd 0.15, independent across parts. Loadings λ_1 = +0.5,
  λ_2 = −0.5, others N(0, 0.25²). Shares = softmax(l); every procedure starts from the shares.
- Observed market covariates: k = 4 columns, z itself plus three independent AR(1) φ = 0.9 nuisance series
  (variant "exact"); and the same with z replaced by z + N(0, (0.5·sd z)²) (variant "noisy proxy", a stress test).
- S0 (null): parts 1 and 2 co-move only through the market. S1 (swap): add w_t to part 1 and −w_t to part 2,
  w AR(1) φ = 0.8 with innovation sd 0.15.
- Procedures on pair (1, 2), two-sided on |ρ|, α = 0.05, null = relative cyclic shift of part 2 by s ∈ {4, …, T−4}
  (all such shifts, exact):
  Raw = ρ on clr levels; PL = residualize clr levels on [1, X] then ρ (the 11-12 prototype "2c");
  PI = residualize clr increments on ΔX, then ρ on residual increments.
- **Pass (decided now), per procedure:** size in S0/exact within [0.02, 0.08] at T = 40 and 62, and power in S1/exact
  ≥ 0.80 at T = 62. Prediction: Raw fails size. The noisy-proxy cells and T = 40 power are reported without a bar.

**Engineering: a small maintained implementation with the right null.** A single tested module (Python/NumPy) with
ρ, φ, clr, pairwise ρ, level- and increment-partial ρ, the exact cyclic-shift null and BH.
- Pass (decided now): the 11-12 identity suite passes; E4 JPM–GS ρ = −0.6976291 and level-partial ρ = −0.8820532
  reproduced to ≤ 1e-9; all 124,750 pairwise ρ for 500 parts × 62 quarters in < 1 s on the box.
- Packaging as its own repo is drafted as a ticket, not done here.

---

## D. ecotraj (#50): "All 3 extensions"

Read as the issue's three avenues, which the ecotraj-py roadmap already calls Extension 1 (Engineering: port + speed,
done 2026-11-14), Extension 2 (Math: increment split, passed 2026-11-14) and the New-use plan (P3). So: finish each.
- Ext 1 (Engineering): no new engineering run. Packaging (roadmap P4) drafted as a ticket.
- Ext 2 (Math): the P2 power curve, pre-registered separately in jgridifier/ecotraj-py `prereg/P2_PREREG.md`, merged before
  it runs.
- Ext 3 (New use): rerun the Extension 2 procedure P1 **unchanged** (increment split, re-projected sign flip, B = 999) on
  the live-Q1 public compositions O1 (venue × tenor) and O2 (tri-party collateral), monthly. Market covariates (k = 3):
  monthly mean VIX, monthly mean 10-year Treasury yield, log total volume of the panel. Primary: residual directionality
  p per panel, Holm over the 2 panels. "Recurrence" = Holm p ≤ 0.05 on at least one panel; otherwise an honest miss.
  Descriptive: the DSPD stress-episode map (2020-03, 2023-03, 2025-08 onward) as a recurring chart.

## Addendum 1 — 2026-11-17 (ET), written after the runs; the text above is unchanged

1. **Timing (A, pim).** This file was committed (60526b3, 12:35 PM ET) and pushed in PR #67 before any analysis ran.
   The pim benchmark ran 12:36–12:39 PM ET, i.e. after the commit but **before** PR #67 was merged (12:40 PM ET).
   The text was not changed between commit and merge. All other analyses (B, C, D, and the ecotraj-py P2 run) started
   after the merge.
2. **B, O3.** The lab's harmonized CFTC panel has no Ultra contracts; O3 sums the 2Y, 5Y, 10Y and bond futures only.
3. **B, mocks.** The program × year table keeps programs observed in every fiscal year (Corning mock 778 of 1,079;
   Morgan Stanley mock 1,404 of 1,840), so the CA profile and the slope baseline see the same years. Not stated above.
4. **B, O1.** O1 is the 11-15 table unchanged, but T2 uses this file's 60% split (train to 2023-04), not the 11-15 split
   (train to 2022-12), so its walk-forward error differs from the 1.06 years on the 11-15 page.
5. **B, O5.** Treasury's TIPS label changes (Inflation-Indexed Notes/Bonds → Inflation-Protected Securities → TIPS);
   all three are mapped to one TIPS column. FRNs are zero before 2014 (a real new type); kept as zeros.
6. **D.** P2's runner (`sims/run_p2.py` in ecotraj-py) was written after the P2 pre-registration merged and before the run;
   it only sets D, σ, τ² and a as the pre-registration states.

## E. pim (#63): Engineering and Math avenues — 2026-11-17, 2:25 PM ET, written before either avenue runs

**Go.** Jared, in chat at 2:11 PM ET on 11-17: "Yes move forward with pim". He made this call knowing that the section A
benchmark had missed the "promising" rule. Both avenues follow the issue's secret-sauce tab. This is research only: it is
not a promotion into analysis-skills, and Y-9C use stays descriptive (no forecasts, no new outcomes).

### E1. Engineering: a streaming within-block PIM fitter (prototype in numpy; the production Rust core becomes a ticket)
The fitter solves the logit PIM score equation \(U(\beta)=\sum_y\sum_{i<j\in y} Z_{ij}(I_{ij}-\mathrm{expit}(Z_{ij}^\top\beta))\)
with \(Z_{ij}=X_j-X_i\) and \(I_{ij}=1\{Y_i<Y_j\}+\tfrac12 1\{Y_i=Y_j\}\). It uses the same within-year pairs as the 11-16 run, and it gets
permutations by re-labelling \(I\) within year while \(Z\) stays fixed, solving all permutations together with batched Newton.
- **Oracle:** pim 2.0.4 in the lab rscout env, `link='logit', model='difference'`, same `compare` matrix, nleqslv
  `control=list(xtol=1e-13, ftol=1e-13)` so that the oracle's own stopping rule does not set the error floor.
- **Bar Eng-1 (parity):** across all 24 fits / 29 coefficients of the 11-16 table (`runs/2026-11-16/pim/pim_q3.R`), max |Δβ| ≤ 1e-8
  and max |ΔSE| ≤ 1e-8 (absolute; SE = pim's default sandwich). In addition, 50 random within-year permutations of the B1 joint model refit by the oracle:
  max |Δβ| ≤ 1e-8.
- **Bar Eng-2 (speed):** 10,000 within-year permutations of the B1 joint model (payout/RWA ~ drawdown + pre-tax income,
  360 firm-years, 5,017 pairs), each solved to max |U| ≤ 1e-10, β for every permutation, wall time **< 2 s** on this box.
  If the 1-minute load average is > 4 when it is measured (the ecotraj P2 run is using 6 workers), it is measured again
  after P2 ends and the bar is judged on that unloaded run; both numbers are reported. Time with a sandwich SE for each
  permutation, and the matching pim time (extrapolated from 20 permutations), are reported with no bar.
- Pass = Eng-1 and Eng-2. Anything production-grade (Rust core, bindings, CI parity) goes into an Engineering ticket and is not run here.

### E2. Math: firm-clustered (dyadic) variance for PIMs
pim's sandwich treats two pairs as dependent only if they share a **firm-year**. With firm effects, pairs that share a
**firm** in different years are also dependent. Estimator: \(\hat V_F = c\,A^{-1} B_F A^{-1}\), with \(A=-\partial U/\partial\beta\),
\(B_F=\sum_f S_fS_f^\top-\sum_{\{a,b\}} V_{ab}V_{ab}^\top\), where \(S_f\) is the sum of pair scores \(u_p\) over pairs that involve firm \(f\) and
\(V_{ab}\) is the sum over the pairs (in any year) made of firms \(a\) and \(b\). This counts every pair of pairs that shares at least one firm exactly once.
Small-sample factor \(c=G/(G-1)\) with G = number of firms. Amorim et al.'s bias reduction is **not** part of this run;
it is named as a follow-up. Identity check: with firm-year IDs in place of firm IDs and c = 1, \(\hat V_F\) equals pim's sandwich (≤ 1e-10).
- **Simulation at our design:** 40 firms × 13 years, and in each year a random 18–35 firms (uniform) observed. \(x_{ft}=c_f+u_{ft}\),
  \(c_f\sim N(0,0.6)\), \(u_{ft}\sim N(0,0.4)\); \(y_{ft}=\beta x_{ft}+a_f+e_{ft}\), \(a_f\sim N(0,1)\), \(e_{ft}\sim N(0,1)\).
  Scenario A: β = 0, where the true PIM coefficient is 0. Scenario B: β = 0.5, where the pseudo-truth is the mean PIM coefficient over 20 fits on 400 firms × 13 years
  with the same per-year sampling share. R = 2,000 replications per scenario (seed 20261117). The firm block bootstrap (percentile,
  B = 199) runs on the first 500 replications of each scenario, for comparison.
- **Bar Math-1:** nominal-95% Wald coverage of \(\hat V_F\) within **[93.5%, 96.5%] in both scenarios**. pim's sandwich and the
  block bootstrap are reported beside it, with no bar.
- **Descriptive application (no bar):** recompute the 29-row 11-16 table with \(\hat V_F\) and report, per row, the sandwich p
  versus the firm-clustered p, with Holm over the 29 rows for each. The card says which headline findings survive.

## Addendum 2 — 2026-11-17 (ET), written after the section E runs; the text above is unchanged

1. **Timing (E).** The section E heading says "2:25 PM ET". That is wrong: the section was committed and merged in PR #69 at
   2:13 PM ET (19:13 UTC), before any section E code ran. The oracle, parity, speed and simulation runs started after the merge.
2. **Eng-2 load.** The 1-minute load average stayed above 4 even after the ecotraj P2 run ended (2:35 PM ET), because other
   jobs share the box. So no unloaded measurement was possible. Both numbers are reported: 11.2 s while P2 ran and 9.1 s at load 4.4.
   Each is far over the 2 s bar, so the verdict (miss) does not depend on which one is used.
3. **Post-hoc extra (E1).** After the numpy prototype missed Eng-2, a small Rust/rayon permutation fitter (`pim2/pimperm-rs`)
   was written and timed on the same task. It is reported as a post-hoc extra and does not turn the pre-registered miss into a pass.
4. **E2.** The identity check (firm-year IDs give pim's sandwich) holds by construction in the code, since both go through the
   same meat function. The binding check is SE parity with pim 2.0.4 itself (Eng-1), which passed.
