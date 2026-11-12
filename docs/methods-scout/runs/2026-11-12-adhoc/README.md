# Methods scout run 2026-11-12 (ad hoc, exotic mandate, aimed at Q1)

Scripts and aggregate outputs behind `../../2026-11-12-adhoc.html`. No raw data is committed.

**Ad hoc edition**, requested 2026-11-12, not the 2 PM daily run. Part B only (no TRACE nightly).
**Exotic mandate** (Jared's Managing Director, 2026-11-12): "you got to go more exotic to find the good stuff."
**PROXY data, not prime brokerage.** Same FR Y-9C panels as 2026-11-11, built by that day's `prep.py`
from the public FFIEC/NIC BHCF trading panel (box copy at `/workspace/rl_check/tracks/y9c-trading-ot/data/processed_v1_1/`).
- `A`: trading assets (BHCK3545) of 14 dealer holding companies, 2016Q3–2026Q2;
- `E4`: trailing-4-quarter equity trading revenue (HI Memo 9.c, BHCK8759) of JPM, GS, MS, BAC, 2011Q1–2026Q2.

Order: `m1_codyn.R` (R 4.5.3, codyn 2.0.6) → `m2_propr.py` (Lovell 2015 / Quinn 2017 formulas, identity-tested;
the CRAN propr package is archived) → `figs.py`. Seeds: 20261112. Cyclic-shift nulls use 999 draws.

Pre-registration note: the same Y-9C panel feeds the pre-registered `tracks/y9c-trading-ot` forecast study
(OOS not authorized). This run is descriptive share and community-dynamics analysis and runs none of that
study's forecasts. MaxLIPO (the MD's calibration example) is on the watchlist only; it is not one of the two picks.
