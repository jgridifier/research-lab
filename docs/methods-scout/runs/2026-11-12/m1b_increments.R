#!/usr/bin/env Rscript
# 1b (revised): market vs residual sub-trajectories built from INCREMENTS, to avoid spurious levels regression.
# d clr_t = B d m_t + e_t (no intercept) ; market path = C_1 + cumsum(B d m_t) ; residual path = C_1 + cumsum(e_t).
# m = (VIX, 4Q Nasdaq return, BAA-10y spread, industry growth) as in the 11-12 ad hoc run. ecotraj directionality + sign-flip null.
suppressPackageStartupMessages({library(ecotraj); library(jsonlite)})
D <- "/workspace/scout/1112/data/"; O <- "/workspace/scout/1112/out/"; NSIM <- 999
clr <- function(M) { L <- log(M); L - rowMeans(L) }
dirn <- function(C) as.numeric(trajectoryDirectionality(defineTrajectories(dist(C), rep("s", nrow(C)), seq_len(nrow(C)))))
sflip <- function(C) { d <- diff(C); s <- sample(c(-1, 1), nrow(d), TRUE); rbind(C[1, ], sweep(apply(d * s, 2, cumsum), 2, C[1, ], "+")) }
run <- function(name, mcols) { set.seed(20261112)
  W <- read.csv(paste0(D, "panel_", name, ".csv"), check.names = FALSE); q <- W$q; M <- as.matrix(W[, -1]); C <- clr(M / rowSums(M)); Tn <- nrow(C)
  Mk <- read.csv(paste0(D, "market_q.csv")); rownames(Mk) <- Mk$observation_date; X <- as.matrix(Mk[q, mcols])
  dC <- diff(C); dX <- diff(X); Z <- dX; B <- solve(crossprod(Z), crossprod(Z, dC))   # no intercept: any common drift stays in the residual (sticky) part
  mk_inc <- dX %*% B; rs_inc <- dC - mk_inc
  mk <- rbind(C[1, ], sweep(apply(mk_inc, 2, cumsum), 2, C[1, ], "+")); rs <- rbind(C[1, ], sweep(apply(rs_inc, 2, cumsum), 2, C[1, ], "+"))
  r2 <- 1 - colSums((dC - Z %*% B)^2) / colSums(dC^2)   # uncentred step R2
  r2m <- 1 - sum(rs_inc^2 - 0) / sum(dC^2)     # share of total step energy (uncentred) explained by market increments
  out <- list()
  for (nm in c("market", "residual")) { P <- if (nm == "market") mk else rs; nul <- replicate(NSIM, dirn(sflip(P)))
    out[[nm]] <- list(dir = dirn(P), length = sum(sqrt(rowSums(diff(P)^2))), net = sqrt(sum((P[Tn, ] - P[1, ])^2)),
                      p_signflip = (1 + sum(nul >= dirn(P))) / (1 + NSIM), null_q = unname(quantile(nul, c(.025, .5, .975)))) }
  pc <- prcomp(C)
  list(panel = name, mcols = mcols, step_r2 = setNames(as.list(round(r2, 3)), colnames(M)), step_energy_market = r2m, sub = out,
       net_total = setNames(as.list(round(C[Tn, ] - C[1, ], 3)), colnames(M)),
       net_market = setNames(as.list(round(mk[Tn, ] - mk[1, ], 3)), colnames(M)), net_resid = setNames(as.list(round(rs[Tn, ] - rs[1, ], 3)), colnames(M)),
       norms = c(total = sqrt(sum((C[Tn, ] - C[1, ])^2)), market = sqrt(sum((mk[Tn, ] - mk[1, ])^2)), resid = sqrt(sum((rs[Tn, ] - rs[1, ])^2))),
       mk_pc = predict(pc, mk)[, 1:2], rs_pc = predict(pc, rs)[, 1:2]) }
PP <- parallel::mclapply(list(list("A", c("vix", "nasdaq_ret4", "baa10y", "ta_ind_g1")), list("E4", c("vix", "nasdaq_ret4", "baa10y", "eq_rev_ind_g4"))),
                         function(a) run(a[[1]], a[[2]]), mc.cores = 2)
names(PP) <- c("A", "E4")
write_json(PP, paste0(O, "m1b_increments.json"), auto_unbox = TRUE, digits = 6, pretty = TRUE)
for (p in PP) { cat(p$panel, "energy_mkt", p$step_energy_market, "norms", p$norms, "\n"); str(p$sub); print(unlist(p$net_market)); print(unlist(p$net_resid)) }
