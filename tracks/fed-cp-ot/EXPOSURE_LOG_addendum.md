# Exposure log addendum: Fed CP maturity mix (pipeline PR #11)

This file adds to PREREG_fed_cp_ot.md §7 without editing it. The pinned prereg files in `prereg/` are never edited.
All times are ET.

| date | what | exposure |
|---|---|---|
| 2026-10-09 | The pipeline executor opened https://www.federalreserve.gov/releases/cp/volumestats.htm to check the release cadence. | Aggregate 2024-26 volumes displayed, not recorded or used. Only the "Data as of October 8, 2026 Posted October 9, 2026" line was noted. |
| 2026-10-09 19:25 | Live vintage fetched from https://www.federalreserve.gov/releases/cp/data/FRB_CP_xml.zip (sha256 02e729949a7b19497eba26ab91d2f9cc25470ca995d8c8c0bc20050eeb1ea224, Last-Modified Fri, 09 Oct 2026 17:00:03 GMT). | Parsed with the 2008-12-26 wall. Post-wall AMT/VOL values withheld; structural counts only. Compared with the pinned zip on burn-in dates only: 0 changes. |
| 2026-10-09 | Pipeline burn-in replication (`fed_cp_ot.burnin_checks`): number-level reproduction of values already printed in `compute_cp_ot_burnin.stdout.txt`. | Burn-in amounts only. No K1 resampling, no power simulation, no trial logged. |
| 2026-10-09 19:50-19:52 | Determinism check requested by Quant. `compute_cp_ot_burnin.py` (sha256 34021c50bf30efbe2541b119816e8ef98c455ab5819ee232a892ca990ab11857) was run unchanged in a scratch directory outside the repo, with the pinned seed 20261009, the pinned zip (16805f2c...) and the pinned thresholds (c15eb60c...). Environment: Python 3.13.5, NumPy 2.5.3, pandas 3.0.6. | **This check is not a second gate run.** No verdict, threshold or pinned file was produced, changed or overwritten. The only output was the stdout sha256, compared with the pin. Its exposure is identical to the original run (burn-in amounts; OOS structural valid-day counts only). Result: stdout sha256 17a0b23936e5b0c56e15a4937830e0f032a55ff20713f45cda7cf2d5adc11e8e equals the pin, so it was **reproduced** byte for byte. |
