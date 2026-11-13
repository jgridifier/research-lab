# Methods scout run 2026-11-12 (scheduled edition; catch-up published 2026-11-13 morning ET)

Scripts and aggregate outputs behind `../../2026-11-12.html`. No raw data is committed.

**Scheduled 2:12 PM ET edition**, interrupted after the analyses finished and before the page was published. This folder and the edition page are the Friday 13 November morning catch-up. A separate [ad hoc exotic run](../../2026-11-12-adhoc.html) the same afternoon (codyn + Lovell proportionality) was already published; these two methods are new.

**PROXY data, not prime brokerage.** Same FR Y-9C panels as 2026-11-11, built by `prep.py` from the public FFIEC/NIC BHCF trading panel (box copy at `/workspace/rl_check/tracks/y9c-trading-ot/data/processed_v1_1/`), plus FRED VIXCLS, NASDAQCOM, BAA10Y and stress series:
- `A`: trading assets (BHCK3545) of 14 dealer holding companies, 2016Q3–2026Q2;
- `E4`: trailing-4-quarter equity trading revenue (HI Memo 9.c, BHCK8759) of JPM, GS, MS, BAC, 2011Q1–2026Q2;
- product-year units for lphom analysis 2-extra: annual trading-revenue shares by product line (commodity, credit, equity, fx, rates) where all four dealers are positive.

Order: `prep.py` / `prep_products.py` → `m1_ecotraj.R` (R 4.5.3, ecotraj 1.2.2; 999-draw nulls) → `m1b_increments.R` → `m2_lphom.R` (lphom 0.3.5.7; 2c planted-truth uses 499 draws) → `m2b_lphom_products.R` → `figs.py`. Seeds: 20261112.

Pre-registration note: the same Y-9C panel feeds the pre-registered `tracks/y9c-trading-ot` forecast study (OOS not authorized). This run is descriptive share, trajectory and transfer-matrix analysis and runs none of that study's forecasts.
