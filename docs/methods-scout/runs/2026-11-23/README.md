# Methods scout 2026-11-23 run folder (Q3, Gaussian partial information decomposition)

Input: `../2026-11-17/statis/q3_pim_panel.csv` (sha256 6aa2f52ab24062932948ea4d67d85491686b7cb89c8580a8bbbc547fe25c0bf7), copied to the working directory as `q3_pim_panel.csv` before running.
Environment: Python 3.13 venv with numpy, scipy, pandas, statsmodels 0.15.0, matplotlib, dit 2.4. Oracles cloned beside the scripts: `gpid/` (github.com/praveenv253/gpid, Venkatesh et al. 2023) and `gcmi/` (github.com/robince/gcmi).

| Script | What | Output |
|---|---|---|
| `PREREG.md` | pre-registration (14:27 ET) + Idep addendum (14:33 ET), written before any result on our data | |
| `pid/pidcore.py` | NumPy port: within-year copula normalisation, Gaussian MI (gcmi-style analytic bias correction), MMI PID, Barrett closed form, Kay & Ince Idep | |
| `pid/home_repro.py` | H1 dit PIDs on XOR / AND; H2 Barrett eqs (64)-(67) vs gpid `mmi_pid` vs port | `home_repro.json` |
| `pid/kayince_ex4.py` | Kay & Ince (2018) Example 4 with `idep_from_corr` | `home_repro_kayince.json` |
| `pid/power.py` | H3 bias of plug-in vs corrected atoms at n = 132/181/360 | `power_bias.json` |
| `pid/q3_pid.py` | P1–P3 MMI atoms, within-year permutation (4,999), Freedman–Lane synergy null (4,999), firm-block bootstrap (2,000), OLS/VIF/commonality | `q3_pid.json`, `q3_pid.log` |
| `pid/q3_pid2.py` | Idep atoms + bootstrap CIs; post-hoc add-on mechanism check; P3 exact era permutation (1,716 splits) and leave-one-year-out | `q3_pid2.json`, `q3_pid2.log` |
| `pid/power2.py` | P4 size/power of the synergy rule at the observed P1 shape | `power_P1.json` |
| `pid/bounds.py` | post-registration addition: Hi-Fi–MMI segment bounds (Van Santen et al. 2026) with firm-block bootstrap | `bounds.json` |
| `pid/bench.py` | B walk-forward OLS / ARDL(1,0) / SARIMAX(1,0,0)+exog; SCB short walk-forward (unscored); timing | `bench.json` |
| `figs.py` | figures in `../../fig/2026-11-23/` | |
| `pid/time_loop.py` | wall time of one P1 triplet in this run's loop (4,999 + 4,999 permutations, 2,000 bootstraps) | `time_loop.json` |
| `pid/parity_gcmi.py` | our bias-corrected Gaussian MI vs gcmi `mi_gg` | `parity_gcmi.json` |

All numbers on the card and edition come from these JSON files (computed). Public data only; descriptive.
