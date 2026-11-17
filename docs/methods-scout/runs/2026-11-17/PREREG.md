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
