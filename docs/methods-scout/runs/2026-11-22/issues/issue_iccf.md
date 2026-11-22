<!-- quant-scout-bot -->

Interpolated cross-correlation with RSS centroid distributions (astrostatistics: reverberation mapping, where a quasar's emission-line light curve echoes its continuum days later and the delay measures the black hole's size; PyCCF, plus ZDCF as the home-field cross-check) on monthly SEC Form PF tab 8.27 borrowing against weekly public repo and fails series (2013–2025), with no regridding. One pair passes Holm under both a matched-persistence AR(1) null and a phase-randomized null: OFR DVP repo volume lags Form PF reverse-repo borrowing by about 6 weeks (centroid +39 d, 68% interval [+31, +54] d, r = 0.92, p = 0.001; ZDCF +46 d). Prime-broker borrowing × fails (r −0.26 at −113 d) is not significant (p 0.12 / 0.50). Method lesson: the home-field rule (the 68% interval excludes zero) calls a lag on all five pairs, and on independent series with our persistence it raises false lags 54–60% of the time; Bartlett bands on monthly levels 75–99%. Our AR(1) null is right-sized at P1 persistence (4.7%) but too loose near a unit root (14%), and P5 still passes when persistence is pushed to 0.995/0.999 (p ≤ 0.001). The DVP lag holds in 2018–21 (centroid +28 d) and changes sign in 2022–25. Misses: as a forecast input it does not beat ARDL or SARIMAX (pre-registered −0.24% RMSE, DM p 0.47). All computed, descriptive only.

**Found via.** Web search 2026-11-22 14:19 ET -> https://www.ascl.net/1805.032 (PyCCF, Sun, Grier & Peterson; Peterson et al. 1998 PASP 110:660, arXiv:astro-ph/9802103); ZDCF port https://github.com/LSST-sersag/pyzdcf

**Home-field robustness.** Established, with caveats. ICCF+FR/RSS is the reverberation-mapping workhorse. Yu et al. (2020, MNRAS 491:6045) find the centroid distribution overstates lag errors by about 3× (JAVELIN about 1.1×), and SDSS-RM simulations (Li et al. 2019, ApJ 884:119) rank ICCF above ZDCF. It reproduces: our NumPy port matches PyCCF to 2×10⁻¹³ and runs 10× faster; overstated errors on the sample cadence (η 1.21); slightly too tight on ours (η 0.90, 68% coverage 0.61). Its "lag > 0" confidence (Peterson et al. 1998) comes from resampling the points, not from a null of unrelated series.

**Secret-sauce cards.**
- **Engineering.** Effort S. Batched NumPy-then-Rust ICCF engine, PyCCF as oracle, with RSS and surrogate nulls in one pass. Test: r(τ) within 10⁻¹² of PyCCF on the sample and 50 random pairs; 2,000 RSS + 2,000 null draws for P1 in < 2 s; null size in [0.03, 0.07] at P1 persistence.
- **Math.** Effort M. A calibrated lag confidence set by inverting a null-calibrated peak test (a profile set over τ), replacing the 68% centroid rule. Test: on planted-lag series at our cadence, 68% and 95% coverage in [0.63, 0.73] and [0.92, 0.97]; independent series: false "lag found" ≤ 5%. **Top pick.**
- **New use.** Effort S. Rolling 36-month ICCF of Form PF reverse repo → DVP (Q1.3) to date when the 6-week lead broke. Test: break date where the rolling r* leaves its first-half null band for ≥ 6 consecutive months, block-shift p < 0.05.

**Research card.** https://jgridifier.github.io/research-lab/methods-scout/m/iccf-lag.html

👍 go ahead · 👎 drop · or just comment what you think.
