# Pre-registration, scheduled methods scout 2026-11-23 (written 14:27 ET, before any run on our data)

Rotation: Q1 and Q2 last targeted 2026-11-22; Q3 last targeted 2026-11-20 -> Q3 (longest untargeted). One method today.
Steering: #46 "Not exotic enough"; #63 ARDL/SARIMAX next to OLS. Prior Q3 picks: IDR, pim, STATIS, poset-ranking, NCA. pim 11-16 found "SCB + drawdown jointly unidentified (collinear)" -> today's method is built for exactly that: shared vs unique vs synergistic information.

## Method — Partial information decomposition (PID), Gaussian-copula MMI form
Home field: computational neuroscience / information theory (Williams & Beer 2010 arXiv:1004.2515; Barrett 2015 PRE 91:052802 MMI for Gaussians; Ince et al. 2017 Hum Brain Mapp Gaussian-copula MI; Venkatesh et al. 2023 NeurIPS bias correction, code praveenv253/gpid). Implementations: dit 2.4 (discrete PIDs), gpid (mmi_pid), gcmi (copnorm, mi_gg); plus our own NumPy port.

Estimator: within each test year, copula-normalize every variable (average ranks -> Phi^-1(r/(n_y+1))); pool firm-years; Gaussian MI in bits from the correlation matrix; atoms R = min(I1,I2), U_strong = |I1-I2|, U_weak = 0, S = I12 - max(I1,I2). Bias: analytic Gaussian (Cai et al.) correction on each MI (gcmi biascorrect) reported next to plug-in. Primary = bias-corrected.

Home-field reproduction (before our data):
- H1: Williams-Beer I_min on XOR (S = 1 bit, R = U = 0) and AND (R ~ 0.311, S = 0.5, U = 0) with dit PID_WB; and dit's BROJA/MMI/CCS on AND to show the measures disagree (known critique).
- H2: Barrett eqs (64)-(67): closed form vs gpid mmi_pid vs our port on 3 covariance settings, agreement < 1e-9; synergy = 0 at b = a/c.
- H3: bias: our estimator at n = 132 and n = 360 on a known Gaussian (a = 0.35, c = 0.30, b = 0.85, close to our SCB/drawdown case), 2,000 draws: mean bias of each atom plug-in vs corrected.

Data (public, lab's verified panel runs/2026-11-17/statis/q3_pim_panel.csv, sha256 6aa2f52a...; 364 firm-years, 360 with payouts; 43 firms; 13 SA exercises 2013-2025). Outcome T = Y-9C payout/RWA (%) calendar year of test; sensitivity next-year payout. Sources oriented as published.

- P1 (Q3.2 buffer vs path, aimed directly at the open question): 2021-2025 (n = 132): sources SCB and SA CET1 drawdown; also SCB vs SA pre-tax income. Report I(T;SCB), I(T;dd), I(T;SCB,dd), atoms, firm-block bootstrap 95% CI (2,000 resamples of firms), and nulls: (a) joint I vs within-year permutation of T (4,999); (b) synergy S vs a Freedman-Lane null that permutes, within year, the residual of the weaker source on the stronger (keeps a, c-structure; 4,999); (c) U_strong: bootstrap CI of I1 - I2 excludes 0. Standard tools shown side by side: OLS with both (t-stats, VIF), commonality analysis (unique and common R^2). Finding = joint I permutation p < 0.05; atom "present" only if its bootstrap 95% CI excludes 0 AND its null p < 0.05.
- P2 (Q3.4 easier vs severe, 2014-2019, n = 181): sources SA drawdown and Adverse drawdown (dd_A); same outputs. Expectation from pim 11-16: Adverse adds nothing -> S and U_A ~ 0.
- P3 (Q3.3 stability + Q3.5 composition): sources SA drawdown and SA pre-tax income; eras 2013-2019 (n = 215 with payouts) vs 2020-2025 (n = 145); targets payout/RWA, dividends/RWA, net buybacks/RWA. Era difference of each atom: permutation of era labels by test year (exact over all 1,716 7/6 year splits); leave-one-year-out atoms.
- P4 (size/power on our shape): Gaussian sims at n = 132 and 360 with S = 0 (b = a/c) and with S = 0.05 bits: false-positive rate of the S rule and power. Pass for the method on our data: size <= 0.07.
- B (benchmark, walk-forward, time-indexed; descriptive): next-year payout/RWA (pooled firm-years), test years 2016-2024 expanding window (train on test years < t). Models: OLS(dd), OLS(dd + pre-tax), ARDL(1,0)(lag payout + dd), ARDL(1,0)(lag + dd + pre-tax), SARIMAX(1,0,0)+exog (per firm with >= 6 prior years, else ARDL). PID consistency claim pre-stated: the weaker source's added OOS value (RMSE change when added) should be <= 1% when its S CI includes 0, and >= 2% better when S is present. Promising for the method = the sign of that prediction holds in both pooled OLS and ARDL. SCB walk-forward only 2023-2024 tests (too short: reported, not scored).
- Timing: our port vs gpid mmi_pid vs dit discrete PIDs per call.
Visual: (1) standard: OLS coefficient/VIF and commonality bar (unique + common, common can go negative); (2) method: PID atom stacked bars (R, U, S) with CIs; (3) "Barrett plane": synergy as a function of source correlation b for the observed a, c, with our estimate marked.
Descriptive only: no claim about how a firm should set its dividend; no trading signal; no Y-9C trading forecast.

## Addendum 14:33 ET (after the home-field reproduction, before any result on our data was seen)
Kay & Ince (2018, arXiv:1803.02030) derive a closed-form Gaussian Idep PID and prove Immi gives redundancy and synergy >= Idep. Added as a pre-stated sensitivity: every P1-P3 atom is also reported under Idep (same copula data, same bootstrap). An atom is called "robust" only if it is present under both Immi and Idep. MMI stays the pre-registered primary.
