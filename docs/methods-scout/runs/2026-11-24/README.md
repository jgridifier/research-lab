# Methods scout 2026-11-24: phase slope index (Q1)

Pre-registration: `../2026-11-24-build/PREREG.md` (merged in PR #105 before the runs). Public aggregates only (lab copies of NY Fed fails, OFR repo, SEC Form PF); no private rows. Python venv `/workspace/psi-venv` (mne-connectivity 0.9.0, statsmodels 0.15, numba).

| File | What |
|---|---|
| `psi_core.py` | independent NumPy PSI with segment jackknife |
| `data_psi.py` | series, pairs, segment settings |
| `a1_home.py` → `a1_home.json` | home-field reproduction (SYNTHETIC), mne parity (missed) |
| `a2_q1.py` → `a2_a3.json`, `psi_strip.png` | Q1 pairs, Granger and cross-correlation comparison, halves, rolling |
| `a4_size.py` → `a4_size.json` | size on our sampling, 1,000 matched-persistence pairs |
| `b_bench.py` → `b_bench.json` | walk-forward benchmark (OLS, ARDL, SARIMAX, SARIMAX+X, PSI-gated) |
| `e_speed.py` → `e_speed.json` | vectorised vs loop |
| `parity_dbg*.py` | attempts to trace the mne-connectivity coherency difference (unresolved) |
| `figs.py` | card figures |
| `found_via.md`, `issue_body.md` | discovery log; issue text |

Reproduce: `cd runs/2026-11-24/psi && python a1_home.py && python a2_q1.py && python a4_size.py && python b_bench.py && python e_speed.py && python figs.py`.
