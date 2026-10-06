# ERRATA v1.1b — rulings on PR #10 head ce9ce39 (Quant, 2026-10-06, before any OOS)

Scope: secondary/sensitivity implementation (commits 35ad75a, 1705d10, ce9ce39). Precedence as ERRATA_v1_1: where a
stated value conflicts with an operative rule of the pinned v1.1 design, the rule governs. No OOS forecast, score,
DM or coverage number was computed for this note; every number below is burn-in or data availability only.
Scripts/outputs: v1_1/review_pr10/ (h1d_epoch0_independent*, scale_missing_share*, s8_memo_coverage*, cmp_synth*).

## 1. Verification (no change)
- Pins unchanged at ce9ce39 (v1.0 JSON dffd1323…4e30, v1.1 JSON 93035364…9694, trials.jsonl 6c774ea4…a732 with the
  single design_revision line, .github/workflows, ERRATA_v1_1 68d5128f…7fe9). Suite 141/141; trials.jsonl untouched.
- Primary path: V.primary on the full 2008–2026 synthetic panel is bit-identical at ce9ce39 vs 40a5353 (h1, h2,
  h1_all, h2_all, selection_log, sets). My epoch-0 freeze and 228-assertion PIT scripts reproduce byte-identical output.
- H1d epoch 0 reproduced independently (own extract, burn-in only): T1 rule (a) 2009Q2/2010Q4/2012Q4/2013Q2 =
  17.990/9.029/13.957/14.167 $bn; scores B0 0.3005, B1 0.5221, B3 0.4037, B4 0.2667 → B*_T1 = B4, trim {B0, B4}
  (B3 > 1.25×0.2667), s = 1.0 (0.2045 vs 0.2121 at 1.1). Identical to Developer's code to 4 dp.
- Trial semantics match addendum §3: one authorized run = 37 trials (primary 1, secondary executions 11 — H2c's two
  comparators are one execution — F3 1, sensitivities 23, R1 1), each logged by config hash before it runs; F1/F2/F4/F5
  and secondary metrics are readings of stored outputs, not executions. preflight precedes every log_trial.

## 2. Clarifications (binding)
- **B1. Coverage base (selection, all horizons, T2/T1/CS).** "Epoch's cases (before matching)" = cases with an actual.
  A case whose case scale is NaN (< 12 of 16 values) is unscored for every member and stays in the denominator (code as
  is). Effect: uniform tightening. h = 4 epoch 0: 12/72 scale-missing → every member ≤ 83.3% (non-binding; B6 excluded
  as one-step only). Primary h = 1: scale-missing share 0 at epoch 0, max 14/228 = 6.1% (2020Q4); h = 4 max 16.7%.
- **B2. S8 sign verified.** FR Y-9C instructions (March 2012, Schedule HI Memo 9(f)/9(g)): "Report in this item the
  amount included in the trading revenue reported in … Memorandum items 9(a) through 9(e) … that resulted from changes
  during the calendar year-to-date in the [BHC's] credit valuation adjustments (CVA)" / "debit valuation adjustment
  (DVA)". Signed YTD components of A220 → ex-CVA/DVA = A220_q − K090_q − K094_q, both de-cumulated (items.yaml
  flow_ytd). Form: completed by HCs with total assets ≥ $100bn (2011), "…that are required to complete Memo 9.a–9.e"
  (2012+). Missing → 0 is safe from 2011Q1: of 2,008 rows with TA_t ≥ $100bn and A220_q non-null, 173 lack both items
  (12 banks, median trading assets $0.0bn, Σ|A220_q| $1.61bn of $1,169.1bn). 2009–2010: not collected (181/181 rows
  missing) → S8 training rows before 2011Q1 are unadjusted; report this label with S8. 5 post-2011 rows have YTD K090
  but NaN quarterly flow (missing predecessor); zero-filled, immaterial.
- **B3. S7, S13, S14 as rescoring.** S13 rescoring is exactly a rerun (member forecasts do not depend on settings).
  S7 and S14 are evaluation sensitivities (grid; aggregation weights, addendum §2.4 rationale): settings stay those
  selected under the primary U99 / case-scale criterion. Label them "rescore, no re-selection".

## 3. Rulings on README IMPLEMENTATION_NOTES 1–31
ACCEPT: 1 (separate 12-member secondary Holm; H1e split h=2/3/4 and H2c split are the honest test count; N/A members
leave m), 2, 3 (prereg H1c = equal-weight linear pool, no widening), 4 (T1 members/min-own 2 match JSON
item_notes; own-error minimum non-binding at every H1d origin; annual re-selection with trimming = the v1.1 H1 recipe),
5 (with B1), 6, 7, 8 (global Fréchet weights are affine-invariant, so standardisation is irrelevant), 9 (H2e on T2 vs
B*, pool of targets < t+1, ≥ 100 PITs), 10, 11 (F3: origin z permuted within C_t, Q̂ and ρ kept, 200 perms, one RNG
seeded 20261006; mean placebo G vs 0.8·G, share also reported), 12, 13–15 (S1/S2 are T2-only by definition; S2 on T3
would change H2's target; S3 is T3-only), 16–20, 22–31.
CHANGE: 21 — replace "sign UNVERIFIED" (README and s8_panel docstring) with B2 citation and the pre-2011 label.
PRE-REG-CONFLICT: none.

## 4. Pre-registered items not implemented (status from prereg v1 / addendum)
| Item | Status | Before the flip |
|---|---|---|
| §4-B scenarios + W₂ reduction, energy score (§4.3, §5.2) | SECONDARY (descriptive) | implement + log trial, or pinned dated deferral → NOT-BLIND |
| K = 2 FPCA functional WAR (§4.2 Step 3) | secondary variant | same |
| (pt) pooled ridge point forecast for secondary MAE (§3 table; λ by GCV once on burn-in 2009–2013, frozen) | secondary-metric comparator | same |
| Entropic barycenter (§4.1), WDRO, drift monitor, Gelbrich (§4.4) | EXPLORATORY | none; later, labelled EXPLORATORY |
| Results-page figures (§6.4 png) | rendering of computed outputs | none |
