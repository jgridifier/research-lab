# Methods scout 2026-11-19 — run folder

- `PREREG.md` — pre-registration written before any run on our data.
- `found_via.md` — discovery channel, link and time for each pick and watch item.
- `poset/` — Q3, partial-order ranking. `lattice.py` (independent lattice-of-ideals port), `home_repro.R` + `home_repro_R.json` (netrankr examples), `parity_python_vs_R.json`, `parity_real.R` + `parity_real_R.json` (netrankr on the 13 real posets), `q3_poset.py` (A1, A2 rank ambiguity), `q3_poset2.py` (A1b trade-off pairs, A2 walk-forward, A3 SCB vs path, A4 stability), `a1b_twosided.py`, outputs `*.json`/`*.csv`, `figs_poset.py`. Input: `q3_pim_panel.csv` (copy of `runs/2026-11-17/statis/q3_pim_panel.csv`, public data).
- `phylo/` — Q2, phylogenetic signal on SYNTHETIC mocks. `prep_q2.py` (slopes, label and text trees; reads `/workspace/q2-mock-zbb/output`), `home_repro.R`, `q2_signal.R` (phyloSignal, lipaMoran), `score_q2.py`, `extra_q2.py`, figures. Per-program scored CSVs are not committed (regenerate with the scripts); trees (`*.nwk`), LIPA tables and summary JSON are.
Environments: R 4.5 micromamba env `rscout` (netrankr 2.0.0, phylosignal 1.3.1, phytools 2.5.2, ape 5.8.1); Python `/workspace/scout-venv`.
