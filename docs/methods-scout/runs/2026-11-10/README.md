# Methods scout run 2026-11-10

Scripts and aggregate outputs behind `../../2026-11-10.html`. No raw data is committed.

Inputs (from Google Drive, downloaded to `/workspace/scout/data/` on the research box):
VIXCLS.csv, T10Y2Y.csv, DGS2.csv, DGS10.csv, MORTGAGE30US.csv, NFCI.csv, STLFSI4.csv, BAMLH0A0HYM2.csv (downloaded, not used: it starts in 2023),
ebp_monthly.csv, and the Sheet "County econ panel — GDP, unemployment, population, migration, poverty (FIPS x year)" (exported as xlsx).

Order: `prep.py` (builds the panels) → `m1_partykit.R` (R 4.4.3, partykit 1.2.29) → `m2_changeforest.py` → `m2b.py`
(reruns 2a/2b on weekly changes, after the levels run showed artifacts) → `build.py` (writes the HTML from the two JSON files).
`m2_results.json` keeps the levels-run fields under `B0_levels_artifact`; its `B1_*`/`B2_*` fields are the weekly-changes run.
