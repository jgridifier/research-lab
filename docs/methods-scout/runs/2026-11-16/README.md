# Methods scout 2026-11-16 — run folder

Scheduled run of 2026-11-16 (America/New_York). Edition page: [../../2026-11-16.html](../../2026-11-16.html). Seed 20261116. R 4.5 (conda env `rscout`), ecofolio 0.1.0 (GitHub seananderson/ecofolio), pim 2.0.4 (CRAN).

## Q2 — ecofolio (mean-variance portfolio effect, Taylor's power law), SYNTHETIC mock ZBB data

- Input: `/workspace/q2-mock-zbb/output/{Corning_mock,MorganStanley_mock}/history.csv` and `programs.csv` (generator seed 20261113; same output as the Drive folder "Q2 mock ZBB datasets (synthetic, 2026-11-13)"). `ground_truth.json` used only for scoring.
- `ecofolio/e0_explore.R` — first look. `ecofolio/e1_ecofolio.R` — A1 portfolio effects (mean-variance vs average-CV vs diversification ratio; segments; noise-free true levels), A2 year-shuffle null (999) and group screen vs random same-size sets (299), A3 Taylor-residual vs CV flags scored against the answer key, and the `pinkbr` vignette reproduction. A vectorised `pe_fast` matches `ecofolio::pe_mv(type = "linear_detrended")` to 1e-15 (checked in the script) and is used inside the null loops.
- `ecofolio/e1_results.json` — all numbers on the page. Per-program points are not republished.

## Q3 — pim (probabilistic index models), public filings

- `pim/prep_q3.py` — builds the panel from the lab's verified 11-14 copies (`/workspace/ms-1114`): Fed `public_results_DFAST_2026.csv` (scenarios 2, 3, 30), FR Y-9C HI-A Q4 items, SCB from the LBCR PDFs. Adds the Adverse drawdown (2014–2019), the December 2020 Alternative Severe drawdown, gross buybacks (BHCK4783), the dividend share, and next-year payouts.
- `pim/pim_q3.R` — 29 within-test-year PIMs (custom `compare` matrix of same-year pairs), 499 within-year permutations, 299 firm-block bootstraps, OLS + year FE with firm-clustered t for comparison, the December 2020 cross-section, the payout/NI fragility check, the FEVData Wilcoxon–Mann–Whitney reproduction and timing. `pim/pim_trim.R` — trimming curve. Holm adjustment within families B1/B2/B3 added to `pim_results.csv`.
- Firm-year rows are not republished; rebuild them from the public sources.

## Figures and page

- `figs.py` → `../../fig/2026-11-16/*.png`. `build_page.py` + `page_body.html` → `../../2026-11-16.html`.
- `found_via.md` — where each method was found (written at the start of the run).

Descriptive work only; no forecasts; nothing touches the pre-registered Y-9C trading study.
