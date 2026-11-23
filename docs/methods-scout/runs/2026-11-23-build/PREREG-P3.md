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


## Addendum 1 — 2026-11-23, about 3:00 PM ET, written after the run; the text above is unchanged

Ran `pim/p3_sim.py` (99 s on 6 processes; results `pim/p3_results.json`). All numbers computed.

**Deviations, disclosed.** (1) The first launch failed on an import path (`vcov_small.py` pointed one folder too shallow); fixed, nothing had run. (2) The identity checks failed on the harness, not the method, before any replication ran: the random test matrix had eig(M'M) ≈ 1.2–1.3, so I − MM' was not positive definite and the dense reference was NaN; and the "≤ 1e-10" meat check was absolute while meat entries are ≈ 3.5e4 (the difference was 1.3e-10 absolute, 3.7e-15 relative). The harness now scales the random M to eig < 1, checks the meat relative to max|B_F|, and adds a check on a real firm cluster (247 pairs, max eig H = 0.051). All three pass: 3.7e-15, 1.8e-15, 5.9e-15. The estimators, design, seeds, bar and selection rule are unchanged.

**Reference reproduces 11-17.** `firm` coverage 91.65% (A) and 91.75% (B), as in 11-17. Pseudo-truth for B = 0.4107.

| Candidate | Coverage A (β = 0) | Coverage B (β = 0.5) | mean SE / SD(β̂) A / B | sec per rep (median) |
|---|---|---|---|---|
| `firm` (reference) | 91.65% | 91.75% | 0.920 / 0.909 | 0.0003 |
| `firm_cr2` | 92.70% | 92.35% | 0.949 / 0.934 | 0.019 |
| `score_wild` | 89.10% | 88.15% | mean critical value 1.77 / 1.77 (vs 1.96) | 0.092 |
| `firm_jack` | **94.20%** | **94.15%** | 1.013 / 1.002 | 0.024 |

**Verdict.** Only `firm_jack` is inside [93.5%, 96.5%] in both scenarios, so by the selection rule it becomes the default: **step 3 passes**, with the multiplicity stated (three candidates tried; one passed). It sits about 0.8 points below 95%, that is about 1.7 Monte Carlo SEs (0.49 points); its SE is calibrated (SE/SD ≈ 1.01 / 1.00), so the remaining shortfall is likely the normal critical value with 40 firms. `firm_cr2` helps only a little (+1.0 / +0.6 points): our dyadic bias reduction is too weak here because each firm's leverage is small (max eig ≈ 0.05), so the shortfall is not mainly leverage. `score_wild` is worse than `firm` (89.1% / 88.2%): its bootstrap critical value averages 1.77, below 1.96. It is not offered as an option. Kill rule not triggered.
