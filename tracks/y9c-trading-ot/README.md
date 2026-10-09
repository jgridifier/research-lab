# Y-9C trading revenue × OT (`tracks/y9c-trading-ot`)

Pre-registered forecasts of FR Y-9C trading revenue (BHCKA220, Schedule HI 5.c):
per-bank probabilistic baselines B0–B6, plus two OT layers from the classical-OT guide:
- **H1 (§4)**: equal-weight W₂ barycenter (quantile average) of the baselines.
- **H2 (§3)**: Wasserstein autoregression of the cross-sectional quantile function, mapped to banks through a Gaussian-copula AR on probit ranks.

**Status: the one authorized OOS run (2026-10-08, commit `5f11ed5`) is INCOMPLETE. Primary verdict: FAIL on H1 and H2.** It logged 24 of the 39 approved trials and stopped in sensitivity S4 (`KeyError` 2020Q1 in WAR-RM); `gate.json` and `secondary.json` were written, `sensitivities.json` and `r1.json` were not. No rerun (Quant ruling). Results: `docs/tracks/y9c-trading-ot/results/`.
- **Primary (v1.1):** `test_design_trading_ot_v1_1.json`, copied verbatim from prereg addendum v1.1 and pinned in its own
  commit `06dbc28` (sha256 `930353641c6a…9694`) via `statement_forecast.prereg.verify_trading_ot_v1_1_preregistration`.
  History runs 2009Q1–2026Q2 (2008 is pre-sample, used only for TA 2008Q4) and the burn-in is 2009Q1–2013Q4. The 50 h=1
  targets are 2014Q1–2026Q2. The bank set is refreshed annually and settings are re-selected each Q4. The test is
  fixed-b Bartlett DM with Holm over {H1, H2}, plus G > 0 in at least 2 of 3 subperiods.
- **R1 (non-gating):** the v1.0 design `test_design_trading_ot.json` (commit `4e33139`, sha256 `dffd1323…4e30`) stays
  byte-identical. It runs on 2018+ data with the YTD-reset guard, with B6 excluded from M0/B* but still reported.
- **Authorization (Quant option (c)).** The v1.1 design JSON keeps `oos_authorized: false` permanently, and its pin
  (`93035364…9694`) is unchanged; a `true` flag is a preflight failure, not a path. The switch is the separate pinned
  file `prereg/OOS_APPROVAL_v1_1.json` (verbatim copy of Quant's file, sha256
  `fe473f36b5308a15bc22b80b87fd124ae081e52460c49120d36df4ad442c77d9`). `run.preflight` checks, after the design pin and
  before any trial is logged: the file's raw sha256, and that its `design_sha256`, both errata shas, the DEFERRAL_4B
  sha, `design_commit` (`c38a284`, the PR #10 merge) and `trials` (39) equal the pinned constants. Without the file,
  `python -m trading_ot.run oos` refuses (`OOSNotAuthorized`). Approval and path are written into the provenance of
  all four output JSONs (`provenance.oos_approval`). The one authorized run is `python -m trading_ot.run oos --design
  v1_1`, which includes R1; `--design v1_0` alone would log an extra trial and is not part of the approval.
- **Errata:** `prereg/ERRATA_v1_1.md` is a verbatim copy of `/workspace/research/y9c_ot_prereg/ERRATA_v1_1.md`,
  sha256 `68d5128fa3da40d269340afda3862ee89374bd6df59ad108c9e84d8698a17fe9`, recorded before any OOS score.
  - E1: the set union is 31. E2: rule (b) T1 2016Q3 is 14.879. E3: fixed-b critical values at T=50 are
    2.4101 / 1.9658. E4: burn-in β̂ is 0.199. E5: the point-in-time test scope. C1–C3 are clarifications.
  - **Where a stated value conflicts with an operative rule of the pinned design, the rule wins.** No new design pin.
  - The path and sha256 are written into the provenance block of `gate.json` / `r1.json`, and the run refuses if
    the copy's hash changes.
- **Errata 1b:** `prereg/ERRATA_v1_1b.md` is a verbatim copy of `/workspace/research/y9c_ot_prereg/ERRATA_v1_1b.md`
  (Quant's review of ce9ce39), sha256 `2f134632acf4120ba410e7e2eacb352895eb41d9fbe9207cd0ddc6d22fef21bf`.
  - §1 verification (pins, primary bit-identity, H1d epoch 0, 37-trial semantics). B1: the coverage base is kept as
    coded (no change). B2: S8 sign verified; pre-2011Q1 S8 training rows unadjusted. B3: S13 rescore = rerun; S7/S14
    labelled "rescore, no re-selection". §4: the not-implemented secondary items (see below).
  - Handled exactly like ERRATA_v1_1: `run.preflight` checks its hash right after authorization and before any trial
    is logged, and `provenance.errata_v1_1b` (path, sha256) is written into `gate.json`, `r1.json`, `secondary.json`
    and `sensitivities.json`.
- **§4-B deferral:** `prereg/DEFERRAL_4B.md` is a verbatim copy of `/workspace/research/y9c_ot_prereg/DEFERRAL_4B.md`
  (Quant, 2026-10-08), sha256 `3867ba4f48441cbc0b3745bd67abb0fd9e6ee3940f8e2fdebbdc696e577c05df`. §4-B is not
  implemented, not logged and not scored; the authorized run stays at 39 trials. `run.preflight` checks the hash after
  the ERRATA_v1_1b check, and `provenance.deferral_4b` (path, sha256) is written into the same four JSONs.
- `trials.jsonl` holds one `design_revision` entry (`counts_as_trial: false`). The OOS trial count is 0.
- **Preflight order.** Every OOS entry point (`run_oos_v1_1`, `run_oos_v1_0`, `run_all_v1_1`, `stage_oos`) calls
  `run.preflight` first: authorization → design sha256 vs the pin(s) in `statement_forecast.prereg` → errata sha256
  (ERRATA_v1_1, then ERRATA_v1_1b) → DEFERRAL_4B sha256 → approval file (OOS_APPROVAL_v1_1.json).
  Only then is a trial logged or any data touched. The provenance computed there is reused in every output JSON.
- **One authorized run** (`python -m trading_ot.run oos`, design v1_1) writes `gate.json` (primary),
  `secondary.json` (H1b–H1e, H2b–H2f, Holm within the family; outside the family the K = 2 FPCA WAR variant and the
  ridge point MAE; F1–F5, secondary metrics), `sensitivities.json` (S1–S16, S4b, FB4) and `r1.json`. Each execution
  is logged as its own trial before it runs: 1 primary + 11 secondary (H2c's two comparators are one execution)
  + 2 outside the family (FPCA K = 2, ridge point) + F3 placebo + 23 sensitivity variants + R1 = **39 trials**.
  F1/F2/F4/F5 and the secondary metrics are readings of these executions, not executions (ERRATA_v1_1b §1).
  §4-B scenarios are deferred (note 34), so they add no trial.

## Layout
| Path | What |
|---|---|
| `trading_ot/items.yaml` | Trading MDRM items defined fresh (A220, Memo 9.a–g, K090/K094, 3545, 3548, 2170, and 4107 for the v1.1 YTD-reset guard). Not the forma_adhoc YAML. |
| `trading_ot/panel.py` | `build_trading_panel` (one or more raw dirs; hashes checked against `manifest.json` before parsing), `availability_date` (due date + 7d), `complete_quarters`, `memo9_check`, `merger_flags` + event list (v1.1 S5 additions). v1.1: `ytd_reset_guard`, `tiered_duplicate_mask`, `entrant_rule_b` (S11), `presample_mask`, `prepare_v1_1` / `prepare_v1_0` (R1) |
| `trading_ot/sets.py` | Ex-ante 19-bank rule (v1.0), `exante_bank_set_rolling` / `set_for_target` (v1.1 annual S_o), balanced-13 sensitivity, cross-section `C_s` |
| `trading_ot/macro.py` | v1.0/R1: FRED VIXCLS / DGS10 / SP500. v1.1: VIXCLS / DGS10 / NASDAQCOM / BAA10Y from 2007-01-01 (`data/fred_v1_1`, sha256 in manifest). Caches gitignored |
| `trading_ot/baselines.py` | B0 SAA-8, B1 seasonal naive, B2 ratio RW, B3 SES(0.3), B4 AR(1)+Q1, B5 pooled QR (LP), B6 EB (`eb_forecast_origin` unchanged); `ridge_gcv` / `ridge_gcv_lambda` / `ridge_point` (pooled ridge point forecast, secondary MAE) |
| `trading_ot/ot_bary.py`, `ot_war.py` | Barycenter, widening, trim, s selection, linear pool; WAR β, geodesic forecast, probit ranks, ρ, rank map; `ar_map_forecast` (H2f), `fpca_war_forecast` (K = 2 FPCA WAR variant) |
| `trading_ot/gate.py` | v1.1: `dm_fixedb` (Bartlett, M=⌊√T⌋, simulated p, R=200,000, seed 20261006), `gain_v1_1` (G, G_U), `verdict_v1_1`, `subperiods`, `fluctuation_test`, `mean_shift_tests`, `evaluate_primary_v1_1`. v1.0: panel DM (HLN), WPE fixed-m, Holm, LOBO |
| `trading_ot/scoring.py`, `select.py` | Quantile CRPS, coverage, v1.1 `case_scale` (trailing-16 MAD at the case origin); annual epochs, matched cases, 80% coverage rule, ties |
| `trading_ot/walkforward.py` | v1.0 / R1 engine (frozen 2021Q4 decisions; `exclude_b6` policy reports B6) |
| `trading_ot/walkforward_v1_1.py` | v1.1 engine: epoch populations, first freeze (2013Q4, burn-in only), annual re-selection, H1/H2 matched cases (not executed on OOS) |
| `trading_ot/secondary_v1_1.py` | Secondary family H1b–H1e / H2b–H2f, Holm within family; outside the family `h2_fpca` and `ridge_lambda` / `ridge_point_mae`; F1–F5 (F3 placebo), secondary metrics (pinball, MAE, 50/90% coverage, PIT) |
| `trading_ot/sensitivity_v1_1.py` | `PLAN` of 23 registered sensitivity executions (S1–S16, S4b, FB4): refits through `walkforward_v1_1.Spec`, or rescoring of the stored primary forecasts |
| `trading_ot/run.py` | `--design v1_1|v1_0`. Pin checks run first, then the `panel` stage. The `oos` stage is gated (`preflight`) on the v1.1 design; `run_all_v1_1` = primary + secondary + sensitivities + R1, `run_oos_v1_0` = R1 alone. Trials are logged to `trials.jsonl` before each execution |
| `scripts/render_results_page.py` | `docs/tracks/y9c-trading-ot/results/index.html` (renders PENDING until `tables/gate.json` exists) |

## IMPLEMENTATION_NOTES (Phase B: secondary family and sensitivities; 32–34: ERRATA_v1_1b §4 items)
Each line is an interpretation made where the prereg (v1.0 §4.1/§4.2/§5.6/§5.7), addendum v1.1 (§4.3, §7) or the
pinned v1.1 JSON leave room; the reading most faithful to the text was chosen. None of it has been executed on OOS
data. Common to all: fixed-b test C with M = ⌊√T⌋ (R = 200,000, seed 20261006), G = Σd̄/ΣS̄_ref, matched cases.

Secondary family (`secondary_v1_1.py`)
1. **Holm family = 12 tests:** H1b, H1c, H1d, H1e at h = 2, 3, 4 (three tests), H2b, H2c vs persistence and vs
   climatology (two tests), H2d, H2e, H2f. A member that is N/A or has < 3 target quarters gets no p-value and does
   not count in the Holm m.
2. **H1b.** Members = the epoch's trimmed set. λ̂_t = `crps_optimal_weights` on the unwidened weighted barycenter
   (the prereg formula), then the epoch's s is applied. Pseudo-OOS pool = one walk-forward forecast per
   (target, bank): epoch-0 selection cases (2012Q3–2013Q4, S_2013Q4) plus scored cases with target ≤ t (= origin).
   Rows need y, scale and every trimmed member. n_t = pool size, κ_t = n_t/(n_t + 200).
3. **H1c.** Same trimmed members, equal weights, **no widening** (s is defined about the barycenter's median; the pool
   is the plain non-OT comparator). Quantiles by exact vectorised inversion (matches bisection to 1e-7).
4. **H1d.** T1 = Σ A220_q over filers with non-null A220_q at t (guard, tiered exclusion, rule (a); 2008 = NaN).
   B0, B1, B3, B4 on the level (constant denominator), own errors ≥ 2, no pooling, B4 fallback = level RW (counted).
   Scale = trailing-16 MAD of T1 at the origin (≥ 12 values, never binding from 2012Q2). "s frozen the same way" is
   read under v1.1 as the same **annual** re-selection (coverage rule, B*_T1, trim, s) on T1's own walk-forward cases;
   trimming is applied because BARY-EW is the full H1 recipe. Comparator B*_T1; one case per target (no LOBO).
5. **H1e.** Settings re-selected per horizon with the same rule on h-step walk-forward cases (targets ≤ e, origin =
   target − h). Selection uses S_e; a scored target uses the set and settings of e = last Q4 ≤ t − h. Targets
   49/48/47. B6 (h = 1 only) is dropped by the 80% rule at every epoch (logged). *Open point for Quant:* at h = 4,
   epoch 0, the 12 cases with target 2012Q3 (origin 2011Q3) have < 12 scale values and count against coverage under
   the existing rule (coverage 60/72 = 83% ≥ 80%, so nothing changes). The coverage rule is left as cleared in Phase A.
6. **H2b.** The primary's origin WAR fit (Q̂, ρ, z_t) mapped to banks of the T2 set in force that rank in C_t,
   × TA_(i,t)/1e4, scored with the case scale against the epoch's B*. A bank without a rank at t is not scored.
7. **H2c.** The cross-section is the unit: one loss per target quarter. Realised Q_(t+1) = type-7 U99 quantiles of
   C_(t+1). Persistence = Q_t, climatology = Q̄_t (the Fréchet mean over 2009Q1..t). Trimmed W₂² on U19.
8. **H2d.** Training pairs (x_s, Q_(s+1)) with s ≥ 2009Q1, s + 1 ≤ t; x = (VIX, rates vol) quarter features (qend rule).
   Global Fréchet regression + isotonic projection, then the §3 rank map with the primary's ρ and z_t, scored like
   H2 against B*_CS. Covariates are not standardised (the weights are affine-invariant).
9. **H2e.** Literal "B*" = the bank-set comparator, so H2e runs on T2 against B*. The PIT pool is the H1b pool,
   with randomisation-free PITs of the current epoch's B* member. It is active only with ≥ 100 PITs. Inactive targets
   have no forecast and are not matched; activation is logged per target.
10. **H2f.** The map displacement d_s(x) = T_s(x) − x is known at x = Q_s(u) and interpolated in x (flat outside).
    α is fitted by least squares on U19 over consecutive triples, clipped to [−1, 1]. Q̂ = Q_t + α·d_(t−1)(Q_t), then
    isotonic projection, then the rank map as H2. N/A for the whole run if it fails at the first origin.
11. **F1–F5.**
    - F1: G(H1c) ≥ G(H1).
    - F2: share of H2 targets with β̂ ∈ {0, 1} after clipping, > 0.5.
    - F3: 200 permutations from one generator (seed 20261006, perm-major then target order). The origin
      cross-section's z is permuted across its banks; Q̂ and ρ are kept. G is computed on the primary's H2 cases.
      The reading uses the mean placebo G ≥ 0.8 × real G.
    - F4: LOBO-min ≤ 0 while G > 0.
    - F5: B* 90% coverage < 0.75 and median-MAE gain ≤ 0 (H1; MAE of the U99 median / s_i(o)).
12. **Secondary metrics.** Pinball at 0.05/0.5/0.95, MAE of the median, 50/90% coverage and 10-bin PIT, for
    BARY vs B* and WAR vs B*_CS, on cases where both exist. Equal weight per bank within a quarter, then across quarters.

Sensitivities (`sensitivity_v1_1.py`; "rerun" = full v1.1 walk-forward with one change, "rescore" = stored primary
forecasts re-aggregated, no refit; the descriptive verdict uses the raw p and never gates)

13. **S1.** The full-sample balanced set over 2009Q1..last (|A220_q| ≥ $10m every quarter, NaN fails), the same at
    $100m (v1's "6 banks at ≥ $100m"), and the fixed S_2013Q4. H1 only; settings are still annual. An empty set is N/A.
14. **S2.** H1 only (bank-level modelling scale; H2 is defined in ratio space). Raw $ = constant denominator.
15. **S3.** H2 only.
16. **S4.** A220_q for 2020Q1–Q2 is masked in every training window. Empty WAR cross-sections are skipped: the
    Fréchet mean uses the quarters present, and β uses pairs where both quarters are present. y and the case scale
    come from the unmasked panel. The T3 trailing-8 r scale uses the last 8 observed training r.
17. **S4b.** Rows before 2010Q1 are masked at every origin (TA 2009Q4 is kept as the denominator). Truth and scale
    are unmasked. Sets are unchanged.
18. **S5.** Rescore: drop (bank, target) at {event, event + 1}, where events are `merger_flags` (>15% or EVENTS,
    including the v1.1 additions).
19. **S6.** The Q1 term is removed from B4/B5 (T2 and T3). The WAR Q1 tangent shift is a joint least-squares fit of
    V_(s+h) = βV_s + δ·1[Q1(s+h)] (β on U19, clipped; δ on U99), with δ added for Q1 targets, then isotonic projection.
20. **S7 — rescore, no re-selection.** The primary forecasts are re-scored with the 19-level score; settings stay those
    selected under the primary U99 criterion (ERRATA_v1_1b B3: an evaluation sensitivity).
21. **S8.** A220 − K090 − K094 where TA_t ≥ $100bn. **Sign verified** (ERRATA_v1_1b B2): the FR Y-9C instructions
    (March 2012) for Schedule HI Memo 9(f)/9(g) define both items as signed YTD amounts included in trading revenue
    (changes during the calendar year-to-date in the BHC's CVA / DVA), so the de-cumulated quarterly
    A220 − K090 − K094 is correct. From 2011Q1 a missing memo value counts as 0 (accepted: 173 of 2,008 rows, 12 banks
    with negligible trading). **Before 2011Q1 the items were not collected: S8's training rows before 2011Q1 are
    unadjusted**, flagged in the code (`s8_unadjusted_pre2011`) and reported with S8 in sensitivities.json. The
    primary's sets are kept (the population is unchanged). H1 and H2 are rerun.
22. **S9.** v1.1 macro with `asof_rule='Dt'`.
23. **S10.** LOYO over 2014..2026 on the primary cases (full summary per year).
24. **S11.** H1d on the rule-(b) T1.
25. **S12.** A rolling 16-quarter window for every estimator (members, B5, the B6 universe, WAR β/ρ/Q̄, the T3
    prior-r count), via the pre-sample mask at origin − 16.
26. **S13.** Rescore with epoch-0 trim, s, B* and B*_CS for every target; populations are still refreshed. This
    rescoring is exactly a rerun, because member forecasts do not depend on settings (ERRATA_v1_1b B3).
27. **S14 — rescore, no re-selection.** Rescore H1 with s_i^F = 1.4826·MAD over 2010Q1–2013Q4 (≥ 12 values, p10 floor over S_2013Q4). Banks
    without 12 values use their case scale at their first scored origin, frozen from then on. H2 is unchanged (the
    addendum keeps the trailing-8 MAD of r). H1d uses T1's 2010Q1–2013Q4 MAD. The forecasts are unchanged.
28. **S15.** Test A, WPE and `y9c.forecast.clustered_dm` (CR1, prereg "continuity").
29. **S16.** B5 without `baa`.
30. **FB4.** Drop targets 2020Q1–Q2 from the primary cases. S4b and S10 are cross-referenced.
31. Engine changes are backward compatible and leave the primary unchanged. The epoch-0 golden test, the 228
    point-in-time assertions and a store-on/off equality test all pass. `war_rm` is bit-identical when every quarter
    is present and there is no Q1 shift.

32. **K = 2 FPCA functional WAR (prereg §4.2 Step 3 variant; its own trial; outside the Holm family).**
    - Inputs are the primary's own objects at each origin: the cross-sections Q_s for the quarters present ≤ origin
      (from 2009Q1) and the primary's Fréchet mean Q̄_t. Tangent vectors V_s = Q_s − Q̄_t.
    - FPCA uses the Step 2 inner product (unweighted, trimmed grid U19): SVD of the quarters × 19 matrix V[:, U19].
      Scores ξ_s are the first K = 2 left singular vectors × singular values. The eigenfunctions are extended to U99
      by φ_k = Σ_s U_{s,k} V_s / S_k, which equals the U19 eigenvector on U19.
    - Dynamics: ξ_{s+1} = A ξ_s with a 2 × 2 A (the "K × K operator" that Step 2 contrasts with the scalar β),
      by least squares over consecutive present pairs with s + 1 ≤ origin; no intercept (the scores are centred), no
      clipping or stability constraint. The spectral radius is reported per origin.
    - Forecast: Q̂ = isotonic(Q̄_t + Σ_k (A ξ_t)_k φ_k) with `scipy.optimize.isotonic_regression`; components beyond
      K are dropped (the FPCA truncation).
    - Bank forecasts: the primary WAR rank map with the primary's ρ̂ and origin ranks z, on the primary T3 population;
      scored against the epoch's B*_CS exactly as H2. Reported with G, G_U, the raw fixed-b test-C p, coverage and
      LOBO; it is a secondary variant, not one of H2b–H2f, so it is outside the Holm family (no Holm p). N/A if it
      cannot run at the first origin; later failures are logged per target.
33. **Pooled ridge point forecast (prereg §3 "(pt)"; its own trial; a secondary-metric comparator, no test).**
    - Bank set T2 (the set in force at each target), h = 1, ratio space r = 1e4·A220/TA_{t−1}; the $ point is
      r̂ × TA_t / 1e4 (as B5).
    - Regressors = B5's T2 regressors (r_s, r_{s−3}, the Q1 indicator of the target, the four macro columns at s;
      B5's exact row rule) plus one intercept dummy per bank in the population.
    - glmnet convention: every non-intercept column (including the bank dummies) is standardised on the training
      rows (population sd); zero-variance columns are dropped; the global intercept is unpenalised and the bank
      intercepts are penalised (pooled). Objective (1/n)·RSS + λ‖β‖².
    - λ is chosen **once** by GCV(λ) = n·RSS/(n − df)², df = 1 + Σ d_j²/(d_j² + nλ), over the grid
      λ = 10^(−4 … 4, step 0.05), on burn-in only: rows ≤ 2013Q4, h = 1 pairs with target ≤ 2013Q4, the epoch-0
      bank set S_2013Q4 (12 banks, 190 rows, 19 columns). **Frozen λ = 10^−1.6 = 0.02512** (interior of the grid;
      pinned by `test_burnin_secondary_real.py::test_ridge_lambda_frozen_on_burnin`).
    - At each scored origin the ridge is refitted with the frozen λ on all pairs with target ≤ origin.
    - Reported: scaled MAE |y − ŷ|/s_i(o) (the primary case scale) on the H1 matched cases where BARY-EW, B* and the
      ridge are defined, for the ridge, the BARY-EW median and the B* median; equal weight per bank within a quarter,
      then across quarters; relative MAE gains of BARY-EW and of B* over the ridge. No test.
34. **§4-B scenarios + W₂ scenario reduction + energy score: DEFERRED (underspecified as written; not improvised).**
    Pinned deferral: `prereg/DEFERRAL_4B.md`, sha256 `3867ba4f…05df` (hash-checked in preflight). What the
    prereg/addendum/errata did not pin down:
    - *Historical-simulation benchmark:* "historical simulation from the last 12 quarters of scaled errors" does not
      say which forecast's errors (B*, BARY-EW median?), the centre the errors are added to, the scale used to
      unscale them, or how a joint 4-quarter (bank × horizon) path is drawn (same calendar quarter across banks?
      consecutive blocks? which horizons' errors).
    - *Copula correlation R̂_t over (bank, horizon):* how (bank, h) PITs are aligned into one observation (by origin,
      which needs targets o + 4 ≤ t), the pseudo-OOS window (burn-in only, or expanding), which B* per horizon (B*_h
      from H1e or the h = 1 B*), the equicorrelation target (the mean off-diagonal correlation, or a fixed level), and
      the handling of missing pairs / a non-PSD matrix. At the first origin there are only about three complete
      4-horizon origins for 48 dimensions (12 banks × 4), so the estimator is not determined by the text.
    - *Reduction:* the k-means seed is "fixed" but not given; "standardized path vectors" does not say per-coordinate
      z-scores vs the case scale; k-means++ restarts are not specified.
    - *Evaluation design under v1.1:* v1 assumed about 15 overlapping 4-quarter origins (2018–2021 history); the
      addendum does not say which origins v1.1 uses (every quarter 2013Q4–2025Q2? annual epochs?), nor how the
      ex-ante set is handled when a bank lacks an actual at some horizon (energy score of a partly observed vector),
      nor whether the "industry" path is the bank-set sum or T1.
    `scoring.energy_score` exists from the v1 build but is not wired to any output (and has no dedicated test).

Not implemented (later, labelled EXPLORATORY, per ERRATA_v1_1b §4):
- §4.4 exploratory WDRO, drift monitor and Gelbrich bound.
- The exploratory entropic barycenter.
- The results-page figures, which need OOS outputs (rendering of computed outputs only).

## Run
```bash
make trading-ot-test     # synthetic leakage/unit tests + real-data checks if the panel is built
make trading-ot-panel    # parse the 74 cached NIC ZIPs (raw_backfill_2008_2017 + raw) -> data/processed_v1_1/
make trading-ot-page     # re-render the results page
```
Raw ZIPs are not re-downloaded (NIC returns 403 from the box). Point `Y9C_RAW_DIR` / `Y9C_RAW_BACKFILL_DIR` at copies, or
symlink `tracks/y9c-panel/data/raw` and `tracks/y9c-panel/data/raw_backfill_2008_2017`.

Independent research lab · not affiliated with any employer or financial institution · not investment advice.
