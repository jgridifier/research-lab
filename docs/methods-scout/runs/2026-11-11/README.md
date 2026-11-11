# Methods scout run 2026-11-11 (aimed at Q1)

Scripts and aggregate outputs behind `../../2026-11-11.html`. No raw data is committed.

**PROXY data, not prime brokerage.** Input: the FR Y-9C trading panel (public FFIEC/NIC BHCF bulk files, 2008Q1–2026Q2),
box copy at `/workspace/rl_check/tracks/y9c-trading-ot/data/processed_v1_1/trading_panel.parquet`, plus FRED VIXCLS and
NASDAQCOM from `.../data/fred_v1_1/`. Panels built by `prep.py`:
- `A`: trading assets (BHCK3545) of 14 dealer holding companies (JPM, GS, MS, BAC, C, WFC, Barclays US, UBS Americas + Credit Suisse USA,
  DB USA, BNP Paribas USA, HSBC North America, Mizuho Americas, RBC US, TD Group US), 2016Q3–2026Q2;
- `E4`: trailing-4-quarter equity trading revenue (HI Memo 9.c, BHCK8759) of JPM, GS, MS, BAC, 2011Q1–2026Q2 (Citi excluded: negative 4Q sums).

Order: `prep.py` → `m1_marss.R` (R 4.4.3, MARSS 3.11.10) → `m2_inspect.R` (InspectChangepoint 1.2, strucchange 1.6.0)
→ `figs.py` → `build.py`. Seeds: 20261111. `panel_summary.json` holds first/last shares only.

Pre-registration note: the same Y-9C panel feeds the pre-registered `tracks/y9c-trading-ot` forecast study (OOS not authorized).
This run is descriptive share analysis and runs none of that study's forecasts.
