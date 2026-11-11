# Methods scout: watchlist

One row per method or package seen by the daily scout. Status: `trialed` (run on our data, with an edition link),
`watch` (worth a run later), `skip` (reason given). Newest first within each date.

| Name | Ecosystem | Link | Date seen | Status | Reason |
|---|---|---|---|---|---|
| partykit (ctree, mob/lmtree) | R (C core via libcoin) | https://cran.r-project.org/package=partykit | 2026-11-10 | trialed: adopt-candidate | Readable regime trees and a test-based split rule; MOB found an NFCI-driven change in the VIX→credit-spread link. Didn't forecast 6-month spread changes OOS. [Edition](2026-11-10.html) |
| changeforest | Rust crate + Python/R bindings | https://github.com/mlondschien/changeforest | 2026-11-10 | trialed: interesting | Finds volatility and correlation breaks that mean methods miss; 0 false breaks on shuffled data; near-linear time. Seed-sensitive break counts, and artifacts on persistent levels. [Edition](2026-11-10.html) |
| fastcpd | R / C++ | https://cran.r-project.org/package=fastcpd | 2026-11-10 | watch | Sequential-gradient change points with GLM/ARMA/GARCH costs (v1.0.0, 2026-06). Parametric counterpart to changeforest. |
| stablelearner | R | https://cran.r-project.org/package=stablelearner | 2026-11-10 | watch | Formal stability assessment for trees (v0.1-9, 2026-08). Replaces the hand-rolled bootstrap tables. |
| glmertree | R | https://cran.r-project.org/package=glmertree | 2026-11-10 | watch | MOB with random effects (v0.2-7, 2026-08). Right tool for county/state clustered panels. |
| evtree | R | https://cran.r-project.org/package=evtree | 2026-11-10 | watch | Globally optimal trees by evolutionary search (JSS 2014; v1.0-8, last release 2019). Checks whether greedy splits miss a better regime. Old but stable. |
| augurs | Rust | https://crates.io/crates/augurs | 2026-11-10 | watch | Time-series toolkit (changepoint, outlier, DTW clustering, MSTL), v0.10.3. Rust building block to check against changeforest. |
