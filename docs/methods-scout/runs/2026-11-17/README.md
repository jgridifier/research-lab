# 2026-11-17 — follow-ups to Jared's comments on scout issues #63, #60, #53, #50

Pre-registration first: [PREREG.md](PREREG.md) (merged in PR #67 before the runs; see its Addendum 1 for timing).
Public data or SYNTHETIC mocks only. No firm-level predictions, firm-year rows or per-program scores are committed
(files ending `_LOCAL_ONLY` stay on the box). R 4.5 (conda env `rscout`: pim 2.0.4, kairos 2.3.0, tabula 3.3.2,
dimensio 0.14.2); Python 3.13 (statsmodels 0.15.0, scikit-learn); ecotrajpy at jgridifier/ecotraj-py main.

- `pim/` (#63, Q3): `bench_prep.py` (adds previous-year payouts to the 11-16 panel) → `bench_pim.R` (PIM scores, held-out
  years) → `bench_ts.py` (OLS, pooled ARDL(1,0), per-firm SARIMAX(1,0,0)+exog, concordance, firm-block bootstrap,
  the pre-stated "promising" rule) → `bench_results.json`.
- `kairos/` (#60, Q1 + Q2): `prep_open.py` builds six public monthly compositions (O1–O6, committed as aggregate CSVs);
  `kairos_open.R` (Porčić test, event-model clock, walk-forward) → `tests_open.py` (naive and ridge baselines, Form PF
  lead test with Holm) → `tests_open.json`. Mocks: `prep_mock.py` → `kairos_mock.R` → `tests_mock.py` → `tests_mock.json`.
- `lovell/` (#53): `proprlite.py` (the engineering deliverable), `test_proprlite.py` → `eng_results.json`;
  `sim_partial.py` → `math_results.json`.
- `ecotraj/` (#50): `ext3_newuse.py` (Extension-2 procedure unchanged on O1 and O2) → `ext3_results.json`. The P2 power
  curve lives in jgridifier/ecotraj-py (`prereg/P2_PREREG.md`, `sims/run_p2.py`, `results/p2/`).
