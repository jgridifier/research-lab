<!-- quant-scout-bot -->

L-moment regional frequency analysis (hydrology: estimating the 100-year flood at a river with a short record by pooling "regions" of similar rivers, with a test that the pooling is valid; Hosking & Wallis, R lmomRFA's Fortran core) on the SYNTHETIC Corning-like and Morgan-Stanley-like mock ZBB books: 901 and 1,549 programs with 4–6 years of budget-miss ratios (actual ÷ budget). The heterogeneity statistic H1 picks the valid pooling unit. Regions by stated function are homogeneous (median H1 −0.09 / −0.05), and the generator's answer key agrees. Discretionary × size regions (3.6 / 2.3) and random regions (4.9 / 8.3) are not. Across real category regions, H1 ranks truly mixed regions better than Brown–Forsythe (AUC 0.86 / 0.89 vs 0.81 / 0.85). Pooling within function cuts the q90 error by 23% / 26% vs at-site, but plain category pooling is as good (0.081 vs 0.082 RMSE). Misses: at matched false-alarm rate H1 has no power edge over Brown–Forsythe; its edge is a looser threshold (9% false alarms at H1 ≥ 2). Discordancy finds the planted mandatory→discretionary programs only on the MS-like book (AUC 0.64 vs 0.47), with 5% precision. Walk-forward FY2025 q90: RFA (discretionary × size regions) beats at-site lognormal (pinball ratio 0.95 / 0.93), but pooled OLS/ARDL are better. All computed on synthetic data.

**Found via.** Web search 2026-11-22 14:19 ET -> https://search.r-project.org/CRAN/refmans/lmomRFA/html/regtst.html (lmomRFA 3.8; Hosking & Wallis 1997)

**Home-field robustness.** Established standard in flood and rainfall frequency, with known limits. It reproduces exactly: on the Cascades rainfall data, D_i, weighted L-moments, kappa and GNO match Hosking's Fortran output; H1 0.52 vs 0.62 (simulation noise; 20-seed mean 0.57). Viglione et al. (2007, WRR) find H1 best at low skew and Anderson–Darling better above t3 = 0.23. Its significance needs independent sites. Cross-correlation lowers power (Castellarin et al., via Lilienthal et al. 2018), and power is very low on short records (Wiltshire 1986: 12% at 5 years).

**Secret-sauce cards.**
- **Engineering.** Effort S. NumPy-then-Rust regtst (L-moments, D_i, kappa-simulated H, Z-DIST), lmomRFA as oracle, vectorized so thousands of candidate regions can be scored. Test: D_i and V within 10⁻¹⁰ of lmomRFA on Cascades and both mocks; H within ±0.1 of the 20-seed lmomRFA mean; 1,000 regions × 500 simulations in < 10 s.
- **Math.** Effort M. An H-guided region search: greedily merge or split stated categories (function × segment × text cluster) under an H1 < 1 constraint, with a year-effect (copula) null so correlated programs don't fake homogeneity. Test: on both mocks, q90 RMSE ≤ 0.95 × category pooling and share of oracle-mixed regions ≤ 10%. **Top pick.**
- **New use.** Effort S. A regional growth curve for year-on-year surprises (Q2.3): flag programs whose FY2025 move exceeds the regional 95% curve. Test: AUC ≥ at-site z + 0.03 on the planted growth-reversal programs.

**Research card.** https://jgridifier.github.io/research-lab/methods-scout/m/lmom-rfa.html

👍 go ahead · 👎 drop · or just comment what you think.
