# Methods scout: watchlist

One row per method or package seen by the daily scout. Status: `trialed` (run on our data, with an edition link),
`watch` (worth a run later), `skip` (reason given). Newest first within each date.

| Name | Ecosystem | Link | Date seen | Status | Reason |
|---|---|---|---|---|---|
| MARSS | R (CRAN) | https://cran.r-project.org/package=MARSS | 2026-11-11 | trialed: recommend for promote workflow | Q1. State-space split of log-ratio shares into market, sticky (random walk) and transient parts, with AICc model comparison (R Journal 2012; v3.11.10; ~1.5k dl/mo; niche, from ecology). GS's revenue-share loss is sticky and mirrors JPM's gain; market factors drive most other swings. Labels need ≥ ~60 quarters (matched-persistence null). [Edition](2026-11-11.html) |
| InspectChangepoint | R (CRAN) | https://cran.r-project.org/package=InspectChangepoint | 2026-11-11 | trialed: interesting | Q1. Sparse-projection change points that say which dealers moved (JRSS-B 2018; v1.2, 2022; ~450 dl/mo; obscure). Fast (10 ms), but level breaks on persistent shares fail a persistence-matched null and drift breaks were not significant. [Edition](2026-11-11.html) |
| not | R (CRAN) | https://cran.r-project.org/package=not | 2026-11-11 | watch | Narrowest-Over-Threshold (JRSS-B 2019; v1.6; ~390 dl/mo). Piecewise-linear change points: when a share-migration trend starts or stops. |
| mosum | R (CRAN) | https://cran.r-project.org/package=mosum | 2026-11-11 | watch | Moving-sum change points with multiscale merge (JSS 2021; v1.2.7; ~570 dl/mo). Theory-backed fast mean-change baseline. |
| coda.base | R (CRAN) | https://cran.r-project.org/package=coda.base | 2026-11-11 | watch | ilr bases and principal balances for shares (v1.0.6, 2026-05; ~870 dl/mo). Interpretable "IHCs vs US big-6" coordinates instead of clr. |
| DirichletReg | R (CRAN) | https://cran.r-project.org/package=DirichletReg | 2026-11-11 | watch | Dirichlet regression of the whole share vector on covariates (v0.7-4, 2026-10; ~5.7k dl/mo). Cross-checks MARSS market loadings. |
| KFAS | R (CRAN) | https://cran.r-project.org/package=KFAS | 2026-11-11 | watch | Exact-diffuse Kalman filter/smoother (JSS 2017; v1.6.0; ~7k dl/mo; well-known). Faster engine for a joint multivariate share model. |
| partykit (ctree, mob/lmtree) | R (C core via libcoin) | https://cran.r-project.org/package=partykit | 2026-11-10 | trialed: adopt-candidate | Readable regime trees and a test-based split rule; MOB found an NFCI-driven change in the VIX→credit-spread link. Didn't forecast 6-month spread changes OOS. [Edition](2026-11-10.html) |
| changeforest | Rust crate + Python/R bindings | https://github.com/mlondschien/changeforest | 2026-11-10 | trialed: interesting | Finds volatility and correlation breaks that mean methods miss; 0 false breaks on shuffled data; near-linear time. Seed-sensitive break counts, and artifacts on persistent levels. [Edition](2026-11-10.html) |
| fastcpd | R / C++ | https://cran.r-project.org/package=fastcpd | 2026-11-10 | watch | Sequential-gradient change points with GLM/ARMA/GARCH costs (v1.0.0, 2026-06). Parametric counterpart to changeforest. |
| stablelearner | R | https://cran.r-project.org/package=stablelearner | 2026-11-10 | watch | Formal stability assessment for trees (v0.1-9, 2026-08). Replaces the hand-rolled bootstrap tables. |
| glmertree | R | https://cran.r-project.org/package=glmertree | 2026-11-10 | watch | MOB with random effects (v0.2-7, 2026-08). Right tool for county/state clustered panels. |
| evtree | R | https://cran.r-project.org/package=evtree | 2026-11-10 | watch | Globally optimal trees by evolutionary search (JSS 2014; v1.0-8, last release 2019). Checks whether greedy splits miss a better regime. Old but stable. |
| augurs | Rust | https://crates.io/crates/augurs | 2026-11-10 | watch | Time-series toolkit (changepoint, outlier, DTW clustering, MSTL), v0.10.3. Rust building block to check against changeforest. |
