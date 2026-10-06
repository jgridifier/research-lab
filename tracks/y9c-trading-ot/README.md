# Y-9C trading revenue × OT (`tracks/y9c-trading-ot`)

Pre-registered forecasts of FR Y-9C trading revenue (BHCKA220, Schedule HI 5.c):
per-bank probabilistic baselines B0–B6, plus two OT layers from the classical-OT guide:
- **H1 (§4)**: equal-weight W₂ barycenter (quantile average) of the baselines.
- **H2 (§3)**: Wasserstein autoregression of the cross-sectional quantile function, mapped to banks through a Gaussian-copula AR on probit ranks.

**Status: OOS not run.** `test_design_trading_ot.json` v1.0 is pinned (commit `4e33139`, sha256 `dffd1323…4e30`) via
`statement_forecast.prereg.verify_trading_ot_preregistration`. The design has `oos_authorized: false` and open
questions, so `python -m trading_ot.run oos` refuses to score anything. A prereg addendum (v1.1, possibly extending history
to 2008) must fix the primary run first. A v1.1 design goes in a **new** design file with its own pin. Editing the pinned
file makes verification fail by construction.

## Layout
| Path | What |
|---|---|
| `trading_ot/items.yaml` | Trading MDRM items defined fresh (A220, Memo 9.a–g, 3545, 3548, 2170). Not the forma_adhoc YAML. |
| `trading_ot/panel.py` | `build_trading_panel`, `availability_date` (due date + 7d), `complete_quarters`, `memo9_check`, `merger_flags` + event list |
| `trading_ot/sets.py` | Ex-ante 19-bank rule (burn-in only), balanced-13 sensitivity, cross-section `C_s` |
| `trading_ot/macro.py` | FRED VIXCLS / DGS10 / SP500 quarter features (cache gitignored). BAMLC0A0CM excluded: FRED history starts 2023-10-06 |
| `trading_ot/baselines.py` | B0 SAA-8, B1 seasonal naive, B2 ratio RW, B3 SES(0.3), B4 AR(1)+Q1, B5 pooled QR (LP), B6 EB (`eb_forecast_origin` unchanged) |
| `trading_ot/ot_bary.py`, `ot_war.py` | Barycenter, widening, trim, s selection, linear pool; WAR β, geodesic forecast, probit ranks, ρ, rank map |
| `trading_ot/gate.py` | Panel DM (HLN, NW lag h−1, t_{T−1}), Holm, gain CI, leave-one-bank-out, verdicts, fixed-smoothing DM |
| `trading_ot/walkforward.py` | Hard-truncated forecasts per origin, frozen burn-in decisions, OOS case builders (not executed) |
| `trading_ot/run.py` | Pin check first, then the `panel` stage; the `oos` stage is gated. Trial logging goes to `trials.jsonl` |
| `scripts/render_results_page.py` | `docs/tracks/y9c-trading-ot/results/index.html` (renders PENDING until `tables/gate.json` exists) |

## Run
```bash
make trading-ot-test     # synthetic leakage/unit tests + real-data checks if the panel is built
make trading-ot-panel    # parse cached NIC ZIPs (tracks/y9c-panel/data/raw, or Y9C_RAW_DIR) -> data/processed/
make trading-ot-page     # re-render the results page
```
Raw ZIPs are not re-downloaded (NIC returns 403 from the box). Point `Y9C_RAW_DIR` at a copy, or symlink
`tracks/y9c-panel/data/raw`.

Independent research lab · not affiliated with any employer or financial institution · not investment advice.
