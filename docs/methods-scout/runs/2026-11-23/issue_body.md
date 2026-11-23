<!-- quant-scout-bot -->

Partial information decomposition (PID; computational neuroscience: how much two brain areas say about a stimulus *redundantly*, *uniquely*, or only *together* as synergy) in its Gaussian-copula form: Barrett's MMI, plus Kay & Ince's Idep as a check. Public data: Fed stress-test results 2013–2025, FR Y-9C payouts, SCB 2021–2025. Q3.2, buffer vs path, 132 firm-years. The SCB alone carries 0.023 bits about payout/RWA, the CET1 drawdown 0.111, and both together 0.208. The extra 0.097 bits is synergy (firm-bootstrap 95% CI 0.008–0.186; within-year Freedman–Lane null p = 0.0002). OLS on the same data reads "a higher SCB means higher payouts" (t = +5.07, VIF 6.5), and commonality analysis gives a negative "common" share (−0.236). The synergy is the SCB's dividend add-on (SCB − drawdown, by rule): use that contrast as the source and the synergy goes away (−0.006 bits). Misses: under Idep the synergy CI touches 0 (power 32% at our shape), and so does the measure-free lower bound. The SA−Adverse pair (Q3.4) adds nothing robust. After 2020, drawdown and pre-tax income share more information about payouts (0.036 → 0.128 bits, exact era-split p = 0.033). All numbers computed.

**Found via.** Web search 2026-11-23 14:23 ET -> https://github.com/praveenv253/gpid (Venkatesh et al. 2023, NeurIPS, arXiv:2307.10515); X 14:40 ET -> https://x.com/Encoding/status/2118725778070266240 (arXiv:2611.08131)

**Home-field robustness.** Promising but contested. The framework (Williams & Beer 2010) is used in top neuroscience work (Luppi et al. 2022, Nature Neuroscience, Gaussian MMI). But redundancy measures disagree, and Immi gives the largest redundancy and synergy of any nonnegative PID (Kay & Ince 2018; Van Santen et al. 2026). Reproduced: Williams–Beer AND gate (0.311 / 0.5 bits), Barrett's closed form (to 1e-15), and Kay & Ince Example 4 to 4 dp.

**Secret-sauce cards.**
- **Engineering.** Effort S. A batched Gaussian-copula PID engine (MMI, Idep, Hi-Fi–MMI segment, within-group copula, Freedman–Lane and firm-block resampling in one call) with gpid/dit as oracles. Test: atoms within 1e-10 of the closed forms, Kay & Ince Example 4 to 4 dp, and ≥ 50× faster than this run's loop on 4,999 permutations + 2,000 bootstraps.
- **Math.** Effort M. Measure-robust synergy with a named contrast: report the whole Hi-Fi–MMI segment with a design-aware small-n test, and name the source contrast that carries the synergy. Test: false-positive rate ≤ 5% at n = 132 when synergy is 0, power ≥ 60% at 0.08 bits, and the recovered contrast within 15° of the SCB add-on. **Top pick.**
- **New use.** Effort M. Q2.2, text vs numbers on the SYNTHETIC mock ZBB books: the unique information in program descriptions vs tabular features about growth, with multivariate sources. Test: unique(text) CI excludes 0 on planted text-signal programs and is ≤ 0.01 bits with scrubbed text.

**Research card.** https://jgridifier.github.io/research-lab/methods-scout/m/gaussian-pid.html

👍 go ahead · 👎 drop · or just comment what you think.
