# Methods scout 2026-11-15 — run folder

Public aggregate data only (lab copies of public files under `/workspace/research/drive_inv/data/` on the box).

- `ccm/` — convergent cross mapping (pyEDM 2.5.7). `prep.py` builds the weekly (Wednesday) panel 2019-01-16..2025-12-31 (n = 364):
  CFTC TFF leveraged-fund net short (UST 2Y+5Y+10Y futures, unweighted contracts; Tuesday report mapped to the next Wednesday),
  NY Fed primary-dealer financing fails (PDFTD-USTET), OFR DVP outstanding, OFR DVP overnight minus tri-party Treasury rate.
  Two holiday weeks without a fails release (2020-12-30, 2024-08-28) are linearly interpolated. `ccm_q1.py` runs embedding,
  S-map, CCM convergence, 200 circular-shift surrogates per direction, a lag scan, linear Granger and a two-half split. Seed 20261115.
- `kairos/` — CA seriation, Porčić (2013) test and Bellanger–Husi event dates (kairos 2.3.0, tabula 3.3.2, dimensio 0.14.2).
  `prep.py` builds monthly-average volumes for 9 venue × tenor segments, 2018-05..2026-09 (DVP and GCF outstanding,
  tri-party TRIV1 transaction volume). `<=30d` is OFR LE30 before 2025-08-14 and B27+B830 after (a known bucket change).
  `kairos_q1.R` runs seriation, the significance test, Ford/EPPM plots, the event model (full and walk-forward) and the window split.
  `link_pf.py` relates the mix clock to SEC Form PF tab 8.27 monthly borrowing growth with a circular-shift null.
- `figs.py` — Python figures.
