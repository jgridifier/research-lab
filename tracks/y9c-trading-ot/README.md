# Y-9C trading revenue × OT (`tracks/y9c-trading-ot`)

Pre-registered forecasts of FR Y-9C trading revenue (BHCKA220, Schedule HI 5.c):
per-bank probabilistic baselines B0–B6, plus two OT layers from the classical-OT guide:
- **H1 (§4)**: equal-weight W₂ barycenter (quantile average) of the baselines.
- **H2 (§3)**: Wasserstein autoregression of the cross-sectional quantile function, mapped to banks through a Gaussian-copula AR on probit ranks.

**Status: OOS not run; design v1.1 pinned and awaiting approval.**
- **Primary (v1.1):** `test_design_trading_ot_v1_1.json`, copied verbatim from prereg addendum v1.1 and pinned in its own
  commit `06dbc28` (sha256 `930353641c6a…9694`) via `statement_forecast.prereg.verify_trading_ot_v1_1_preregistration`.
  History runs 2009Q1–2026Q2 (2008 is pre-sample, used only for TA 2008Q4) and the burn-in is 2009Q1–2013Q4. The 50 h=1
  targets are 2014Q1–2026Q2. The bank set is refreshed annually and settings are re-selected each Q4. The test is
  fixed-b Bartlett DM with Holm over {H1, H2}, plus G > 0 in at least 2 of 3 subperiods.
- **R1 (non-gating):** the v1.0 design `test_design_trading_ot.json` (commit `4e33139`, sha256 `dffd1323…4e30`) stays
  byte-identical. It runs on 2018+ data with the YTD-reset guard, with B6 excluded from M0/B* but still reported.
- The v1.1 JSON ships with `oos_authorized: false`, so `python -m trading_ot.run oos [--design v1_1|v1_0]` refuses
  before loading anything. Approval is a separate commit that flips that flag (which also re-pins, by construction).
- **Errata:** `prereg/ERRATA_v1_1.md` is a verbatim copy of `/workspace/research/y9c_ot_prereg/ERRATA_v1_1.md`,
  sha256 `68d5128fa3da40d269340afda3862ee89374bd6df59ad108c9e84d8698a17fe9`, recorded before any OOS score.
  - E1: the set union is 31. E2: rule (b) T1 2016Q3 is 14.879. E3: fixed-b critical values at T=50 are
    2.4101 / 1.9658. E4: burn-in β̂ is 0.199. E5: the point-in-time test scope. C1–C3 are clarifications.
  - **Where a stated value conflicts with an operative rule of the pinned design, the rule wins.** No new design pin.
  - The path and sha256 are written into the provenance block of `gate.json` / `r1.json`, and the run refuses if
    the copy's hash changes.
- `trials.jsonl` holds one `design_revision` entry (`counts_as_trial: false`). The OOS trial count is 0.

## Layout
| Path | What |
|---|---|
| `trading_ot/items.yaml` | Trading MDRM items defined fresh (A220, Memo 9.a–g, K090/K094, 3545, 3548, 2170, and 4107 for the v1.1 YTD-reset guard). Not the forma_adhoc YAML. |
| `trading_ot/panel.py` | `build_trading_panel` (one or more raw dirs; hashes checked against `manifest.json` before parsing), `availability_date` (due date + 7d), `complete_quarters`, `memo9_check`, `merger_flags` + event list (v1.1 S5 additions). v1.1: `ytd_reset_guard`, `tiered_duplicate_mask`, `entrant_rule_b` (S11), `presample_mask`, `prepare_v1_1` / `prepare_v1_0` (R1) |
| `trading_ot/sets.py` | Ex-ante 19-bank rule (v1.0), `exante_bank_set_rolling` / `set_for_target` (v1.1 annual S_o), balanced-13 sensitivity, cross-section `C_s` |
| `trading_ot/macro.py` | v1.0/R1: FRED VIXCLS / DGS10 / SP500. v1.1: VIXCLS / DGS10 / NASDAQCOM / BAA10Y from 2007-01-01 (`data/fred_v1_1`, sha256 in manifest). Caches gitignored |
| `trading_ot/baselines.py` | B0 SAA-8, B1 seasonal naive, B2 ratio RW, B3 SES(0.3), B4 AR(1)+Q1, B5 pooled QR (LP), B6 EB (`eb_forecast_origin` unchanged) |
| `trading_ot/ot_bary.py`, `ot_war.py` | Barycenter, widening, trim, s selection, linear pool; WAR β, geodesic forecast, probit ranks, ρ, rank map |
| `trading_ot/gate.py` | v1.1: `dm_fixedb` (Bartlett, M=⌊√T⌋, simulated p, R=200,000, seed 20261006), `gain_v1_1` (G, G_U), `verdict_v1_1`, `subperiods`, `fluctuation_test`, `mean_shift_tests`, `evaluate_primary_v1_1`. v1.0: panel DM (HLN), WPE fixed-m, Holm, LOBO |
| `trading_ot/scoring.py`, `select.py` | Quantile CRPS, coverage, v1.1 `case_scale` (trailing-16 MAD at the case origin); annual epochs, matched cases, 80% coverage rule, ties |
| `trading_ot/walkforward.py` | v1.0 / R1 engine (frozen 2021Q4 decisions; `exclude_b6` policy reports B6) |
| `trading_ot/walkforward_v1_1.py` | v1.1 engine: epoch populations, first freeze (2013Q4, burn-in only), annual re-selection, H1/H2 matched cases (not executed on OOS) |
| `trading_ot/run.py` | `--design v1_1|v1_0`. Pin checks run first, then the `panel` stage. The `oos` stage is gated on the v1.1 design (`run_oos_v1_1`, `run_oos_v1_0` for R1). Trials are logged to `trials.jsonl` before scoring |
| `scripts/render_results_page.py` | `docs/tracks/y9c-trading-ot/results/index.html` (renders PENDING until `tables/gate.json` exists) |

## Run
```bash
make trading-ot-test     # synthetic leakage/unit tests + real-data checks if the panel is built
make trading-ot-panel    # parse the 74 cached NIC ZIPs (raw_backfill_2008_2017 + raw) -> data/processed_v1_1/
make trading-ot-page     # re-render the results page
```
Raw ZIPs are not re-downloaded (NIC returns 403 from the box). Point `Y9C_RAW_DIR` / `Y9C_RAW_BACKFILL_DIR` at copies, or
symlink `tracks/y9c-panel/data/raw` and `tracks/y9c-panel/data/raw_backfill_2008_2017`.

Independent research lab · not affiliated with any employer or financial institution · not investment advice.
