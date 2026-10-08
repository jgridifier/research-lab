# ERRATA to prereg addendum v1.1 (recorded before any OOS score)

**Date:** 2026-10-06 (ET). Quant review of PR #10 head `a4ac8c25abd75e4ddfa4a0ba96ed70d7843a15bc`.
**Applies to (none of these files is edited):**
- `ADDENDUM_v1_1_extended_history.md`, sha256 `04e815e89392dcd849679c62243d71fed8d262f2deee62ff19eccddbcbc90651`
- `DATA_CHECK_backfill.md`, sha256 `b3d495346d2d7d49e2c203196d8ebed9ca4199038ea334ba3a1ee3a7ae1e0357`
- `test_design_trading_ot_v1_1.json`, sha256 `930353641c6af0b4846d6678648a7446a738a579a52b4863726c9edb5a6a9694` (pinned in commit 06dbc28)

**Status at recording:** no OOS forecast, CRPS, DM or coverage number exists, and `oos_authorized` is false.
**Evidence:** `v1_1/review_pr10/` (scripts and outputs).

**Precedence rule.** Where a stated expected or descriptive value conflicts with an operative rule of the pinned design, the rule governs. None of the corrections below changes a rule, window, estimator, test, threshold, or verdict condition. **No new design pin is required.**

| # | Where | As written | Corrected | Why | Affects anything else? |
|---|---|---|---|---|---|
| E1 | JSON `bank_set.union_size`; addendum §0 ("32 distinct banks") | 32 | **31** | Over the registered origins 2013Q4..2025Q4 the union is 31. My `design_burnin.py` also looped over 2012Q4, which added MUFG Americas (1378434). Reproduced with Developer's code. | No. Per-origin counts (12/16/17/18/18/19/17/19/19/21/22/19/21) and S_2021Q4 = v1's 19 are confirmed. No estimator, test, κ or MDE uses the union. |
| E2 | Addendum §2.5 and §5.3 test 5; DATA_CHECK §9 table | Rule (b) T1 2016Q3 = 14.906; b − a = −1.188 | **14.879; b − a = −1.215** | 14.906 counted BancWest's first-filing YTD (+$0.027bn). The pre-registered tiered-duplicate exclusion (JSON `target.tiered_duplicates_excluded`, `views.T1`) removes it. Rule (a) 16.094 and the 2013Q2 values (14.167 / 15.551) are unchanged. | No. S11 is a T1 sensitivity only; no power, κ or count uses it. |
| E3 | JSON `test.null_simulation.expected_cv_T50`; addendum §2.6 | 2.417 (0.975) / 1.976 (0.95) | **2.410 / 1.966** (authoritative: `dm_fixedb`, fresh `default_rng(20261006)`, R = 200,000) | My values came from a shared RNG stream partway through `mde_v1_1.py`, not a fresh seed. My own independent statistic with a fresh seed reproduces 2.4101 / 1.9658. Across 40 seeds the Monte Carlo sd is 0.0088 / 0.0065 (`fixedb_check_output.txt`). The JSON tolerance of ±0.03 (about 3.4 sd) is appropriate, and p-values come from the seed-pinned null, so they are exactly reproducible. | MDE multipliers in addendum §4.2 used the old critical values. The shift is ≤ 0.010 in the critical value, so MDEs move by well under 0.1 pp. Not recomputed; planning values only. |
| E4 | Addendum §4.1 | Burn-in WAR β̂ 0.198 | **0.199** (ρ̂ 0.546 on 841 transitions unchanged) | My calibration ran before the YTD-reset guard. The guard drops one 2012Q2 cross-section row (Workers United). | No. β is not used in any MDE. The other burn-in calibrations in `design_burnin.py` are also unguarded, but the guarded 2009–2013 rows have \|q\| ≤ $0.86m, so the effect is negligible (not recomputed). |
| E5 | Addendum §5.3 test 3 | Point-in-time **forecast** checks on real data at origins 2013Q4, 2016Q2, 2016Q3 | Real data: **sets, case scales and the T3 population** at those origins. **Forecasts and selection** on real data only at burn-in origins (2012Q2–2013Q3, plus epoch-0 selection at 2013Q4). Forecasts at later origins are checked on synthetic 2008–2026 data. | A real-data forecast at an origin ≥ 2013Q4 is an OOS forecast, and the literal test would have required one. | No. |

**Clarifications (interpretations accepted; not errata to any value):**
- **C1 (pooling and the scale floor).** For a forecast in epoch e, pooled components (pooled errors, B5 training, the B6 EB universe) and the 10th-percentile scale floor use S_e, the set chosen at the epoch origin. For scored cases this is the set in force at the case's origin, as written. For selection cases it is the set "in force at the epoch origin", per `selection.cases`. All of it uses data ≤ e, so selection stays causal. For epoch 0 no earlier set exists.
- **C2 (R1).** R1 (the v1.0 design) runs only when the v1.1 design authorizes OOS. The v1.0 file stays byte-identical with `oos_authorized: false`, so v1.1 is its only authority. R1 counts as a trial.
- **C3 (H2 rank map).** A bank in C_(t+1) without a probit rank at t (not in C_t) gets no WAR-RM forecast, so it drops out under the matched-case rule (counted), as in v1.0.

**Verified in this review (reproduced):**
- Pins: v1.1 `9303…9694` (commit 06dbc28); v1.0 `dffd…4e30` is byte-identical at 4e33139 and HEAD. The addendum and data-check hashes recorded in the JSON match the files.
- Tests: 91/91 pass in a fresh clone.
- Panel: identical to `v1_1/full_panel.parquet` (51,008 bank-quarters, identical NaN patterns, max \|diff\| = 0 on 12 items). The 16 YTD-reset rows are identical.
- Epoch-0 freeze from burn-in data only, both with Developer's code and with my independent re-implementation:
  - 72/72 cases for every member;
  - pooled scores B0 0.478895, B1 0.706508, B2 0.927682, B3 0.726731, B4 0.675533, B5 0.819913, B6 0.745752 (agree to 6 decimals);
  - B\* = B0; trim {B0, B4} (B4 is kept by the keep-≥2 rule); s = 1.0.
- 228 extra real-data burn-in point-in-time assertions pass (T2, T3 and WAR at 2012Q2–2013Q3; epoch-0 T2 and CS selection invariant to rows after 2013Q4).
