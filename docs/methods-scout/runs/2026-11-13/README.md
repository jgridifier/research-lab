# Methods scout run 2026-11-13 (scheduled edition)

Scripts and aggregate outputs behind `../../2026-11-13.html`. No input data is committed.

**SYNTHETIC data only.** Both methods were run on the Q2 mock zero-based-budgeting datasets built on 2026-11-13
(Drive folder "Q2 mock ZBB datasets (synthetic, 2026-11-13)"; box copy `/workspace/q2-mock-zbb/output/`, generator
`generate_q2_mock_zbb.py`, RNG seed 20261113). They are modeled on publicly reported totals for a manufacturer like
Corning Incorporated and a financial firm like Morgan Stanley. **They are not either firm's budgets and contain no private data.**
`Corning_mock`: 1,079 programs, FY2020–2025. `MorganStanley_mock`: 1,840 programs, FY2021–2025.

The answer key (`ground_truth.json`) is used **only to score** results (true levels, pooling families, planted
mismatches, latent clusters). No chart input or model input uses it. `prep.py` writes observable features and,
separately, `*_KEY_*` scoring files.

Per-program noise SD is estimated from the spread of budget-minus-actual gaps (an observable), using the dataset
README's statement that budget noise is 0.70 × actual noise, and shrunk toward the group median (4 pseudo-observations).

Order:
1. `prep.py` (Python 3.13, pandas)
2. `m1_ebnm.R`, then `m1c_relative.R` (R 4.5.3; ebnm 1.1.42, ashr 2.2.63, mixsqp 0.3.54)
3. `m2a_parity.py`: NumPy port `denselines.py` against the authors' Rust reference (github.com/domoritz/line-density-rust
   @ 083890c). The harness `parity_harness.rs` was placed in that repo's `src/bin/`. It copies `run_series` / `sum_images`
   from upstream `src/main.rs` unchanged and only adds file I/O. Built with rustc 1.99.0. The 50,000-series speed step was
   killed by the box's 15.6 GB memory limit, so `m2a_parity.json` was transcribed from the run log; that is noted inside the file.
4. `m2_denselines.py`, then `m2b_brush_sensitivity.py`
5. `figs.py`

Seeds: 20261113. Everything is descriptive. No forecasts.
