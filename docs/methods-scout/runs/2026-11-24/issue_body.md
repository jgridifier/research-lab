<!-- quant-scout-bot -->
**Phase slope index (PSI)** is a lead-lag test borrowed from EEG brain-connectivity work (Nolte et al. 2008). It reads direction from how the phase of the cross-spectrum changes with frequency, and it is blind to anything that moves both series at the same instant. On our public Q1 series (fails, DVP and tri-party volume weekly; Form PF prime-broker borrowing and reverse repo monthly) no pair shows a significant lead-lag after Holm. The usual Granger test flags two pairs (fails → tri-party, p = 0.023; reverse repo → prime-broker, p = 0.042), and on matched-persistence simulations Granger's either-direction false-alarm rate is 13% (weekly fails × DVP) against PSI's 0.6%. PSI is itself too conservative at our short sample sizes (size 0.6–4.1%), so "no lead-lag found" is weak evidence.

**Found via:** web search 2026-11-24 ~2:35 PM ET → https://arxiv.org/abs/0712.2352 (Nolte et al., PRL 100:234101), Haufe et al. 2013 https://pubmed.ncbi.nlm.nih.gov/23006806/

**Home-field robustness:** well established as a linear lead-lag direction measure in EEG (independent simulation study; ~600 citations). Limits: linear only, cannot show two-way interaction, and lead-lag is not the same as causal direction in nonlinear systems.

**Three avenues (top pick: Math)**
- **Engineering** (S): vectorised PSI + segment jackknife for thousands of pairs; 6.1× faster than a per-pair loop in our test; parity with mne-connectivity not yet reached. Test: parity ≤ 1e-8 after tracing its estimator.
- **Math ★ top pick** (M): a small-sample-calibrated test (delta-method variance or time-reversal surrogates) to replace the jackknife, which is too conservative at 6–15 segments. Test: size in [0.03, 0.07] at K = 11–15 on matched-persistence simulations, power ≥ 0.80 on a planted 2-week delay.
- **New use** (M): band-resolved lead-lag map of the funding stack with pre-registered stress windows (Q1). Test: share of band × pair cells beating a matched-persistence null after Holm.

Research card: https://jgridifier.github.io/research-lab/methods-scout/m/phase-slope-index.html
Edition: https://jgridifier.github.io/research-lab/methods-scout/2026-11-24.html#phase-slope-index

## How to respond

👍 go ahead · 👎 drop · or just comment what you think.

A daily scanner reads this issue; you do not need to @-mention anyone.
