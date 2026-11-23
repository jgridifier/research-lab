<!-- quant-scout-bot -->
# Pre-registration: pim (#63) build step 3, small-sample SEs that hold coverage

Written Monday 2026-11-23, about 3:00 PM ET, **before** any code for this step ran; committed and merged before the run. Results go in a dated addendum at the end; the text above it is not edited.

**Design (unchanged from `runs/2026-11-17/pim2/math_sim.py`, PREREG 2026-11-17 section E2).** 40 firms × 13 years, a random 18–35 firms observed per year; \(x_{ft}=c_f+u_{ft}\), \(c_f\sim N(0,0.6)\), \(u_{ft}\sim N(0,0.4)\); \(y_{ft}=\beta x_{ft}+a_f+e_{ft}\), \(a_f\sim N(0,1)\), \(e_{ft}\sim N(0,1)\). Logit difference PIM on within-year pairs. Scenario A: β = 0 (truth 0). Scenario B: β = 0.5 (pseudo-truth = mean PIM coefficient over 20 fits on 400 firms × 13 years, same seed stream as 11-17). R = 2,000 replications per scenario, seed 20261117 with the same per-replication streams, so the datasets are the 11-17 datasets (firm SE coverage should reproduce 91.65% / 91.75%).

**Candidates (all nominal 95%, two-sided).** Notation: pair scores \(u_p=z_p r_p\), \(r_p=I_p-\hat\mu_p\), \(w_p=\hat\mu_p(1-\hat\mu_p)\), \(A=\sum_p w_p z_pz_p^\top\); \(P_f\) = pairs involving firm f; \(P_{ab}\) = pairs (any year) made of firms a and b.

1. `firm` (reference, 11-17): \(c\,A^{-1}B_FA^{-1}\), \(B_F=\sum_f S_fS_f^\top-\sum_{a<b}V_{ab}V_{ab}^\top\), \(c=G/(G-1)\). Wald, z = 1.96.
2. `firm_cr2` (new dyadic bias-reduced linearisation). For any cluster \(g\) (a firm's pair set \(P_f\) or a dyad's pair set \(P_{ab}\)): standardised residuals \(\tilde r_g=W_g^{-1/2}r_g\), \(M_g=W_g^{1/2}Z_gA^{-1/2}\), \(H_{gg}=M_gM_g^\top\), adjusted score \(S^{*}_g=Z_g^\top W_g^{1/2}(I-H_{gg})^{-1/2}\tilde r_g\) (Kauermann–Carroll / Bell–McCaffrey form for estimating equations; Mancl–DeRouen use the full inverse instead). Then \(B^{*}=\sum_f S^{*}_{f}S^{*\top}_{f}-\sum_{a<b}V^{*}_{ab}V^{*\top}_{ab}\) and \(\hat V=A^{-1}B^{*}A^{-1}\), **no** G/(G−1) factor. \((I-H)^{-1/2}\) is computed exactly through the k × k eigenproblem of \(M_g^\top M_g\) (rank-k update). Why: the linearisation \(r\approx(I-WZA^{-1}Z^\top)\varepsilon\) makes the raw residuals of cluster g shrink by \(I-H_{gg}\) on average; inverting that square root removes the leading downward bias in each cluster's outer product. The dyadic step (applying it to the inclusion–exclusion terms separately) is our own adaptation and is not from a paper. Code identity checks before use: with the adjustment switched off, \(B^{*}=B_F\) to ≤ 1e-10; the rank-k formula equals a dense inverse square root on random clusters to ≤ 1e-10. Wald, z = 1.96.
3. `score_wild` (firm-level wild score bootstrap, after Kline & Santos 2012). B = 399 Rademacher draws \(\varepsilon_f\) per replication; perturbed pair scores \(u^{*}_p=(\varepsilon_{a(p)}+\varepsilon_{b(p)})u_p\); \(t^{*}=[A^{-1}\sum_pu^{*}_p]_1/\mathrm{se}_{\text{firm}}(u^{*})\), where \(\mathrm{se}_{\text{firm}}(u^{*})\) is candidate 1 computed on the perturbed scores. Interval \(\hat\beta\pm q_{0.95}(|t^{*}|)\,\mathrm{se}_{\text{firm}}\). No refits.
4. `firm_jack` (leave-one-firm-out jackknife, the CR3 analogue): refit without each firm's pairs; \(\hat V_J=\tfrac{G-1}{G}\sum_f(\hat\beta_{(f)}-\bar\beta_{(\cdot)})^2\). Wald, z = 1.96. Added as a third candidate because it needs no new theory.

**Bar (build plan).** The **default's** coverage in [93.5%, 96.5%] in **both** scenarios. Monte Carlo SE at R = 2,000 near 95% is 0.49 points (computed).

**Selection rule.** Among candidates 2–4 that are in the band in both scenarios, the default is the one with the smallest mean |coverage − 95%| over A and B; ties go to the cheaper one (CR2, then jackknife, then wild). Three candidates are tried, so a pass by one of them is reported with that multiplicity stated.

**Kill rule (build plan).** If no candidate reaches the band in both scenarios, `firm` stays the default with a hard warning below the power-study minimum, and the miss is recorded. It is not called fixed.

Also reported (no bar): mean SE / SD of β̂ for each candidate, interval width, run time per replication.
