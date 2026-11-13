#!/usr/bin/env Rscript
# Methods scout 2026-11-12 (scheduled) — Method 2: lphom (ecological inference of RxC transfer matrices by LP)
# Pavia & Romero 2022/2024 Sociol Methods Res 53(3):1491-1533; Romero et al. 2020 J Appl Stat 47:2711-2736.
# Transfer: "voting units" = consecutive quarter pairs; "election 1/2" = dealer shares at t-1 / t (x 1e4).
# Under homogeneity, one share-transfer matrix P (rows sum to 1) moves composition t-1 -> t.
# 2a Q1: retention / flow matrix on E4 (4 dealers) and A-6 blocs; split halves; annual non-overlapping steps;
#        baseline = constrained least squares (Lee-Judge-Zellner style) via the same LP-free QP-like solver.
# 2b Q1: market vs sticky — fit P separately on high-VIX vs low-VIX quarter pairs; permutation null on the split.
# 2c Q1: planted-truth recovery (lphom vs least squares) and a persistence-matched no-migration null.
suppressPackageStartupMessages({library(lphom); library(jsonlite); library(MASS)})
set.seed(20261112)
D <- "/workspace/scout/1112/data/"; O <- "/workspace/scout/1112/out/"
SC <- 1e5   # shares -> integer "votes" per unit (1 vote = 0.001 pp); totals forced equal (closed panel, no net entry/exit)
intv <- function(M) { V <- round(M * SC); V[, which.max(colMeans(V))] <- V[, which.max(colMeans(V))] + (SC - rowSums(V)); rownames(V) <- NULL; as.data.frame(V) }
units <- function(S, idx = 2:nrow(S)) list(x = intv(S[idx - 1, , drop = FALSE]), y = intv(S[idx, , drop = FALSE]))
fitP <- function(S, idx = 2:nrow(S)) {
  u <- units(S, idx); r <- lphom(u$x, u$y, new_and_exit_voters = "raw", verbose = FALSE)
  P <- r$VTM.complete; P <- P[colnames(S), colnames(S)]; list(P = P, HETe = r$HETe, lo = r$deterministic.bounds$lower, hi = r$deterministic.bounds$upper) }
# Baseline: constrained least squares Markov estimator (Lee, Judge & Zellner 1970) by projected gradient on rows of simplex
proj_simplex <- function(v) { u <- sort(v, decreasing = TRUE); cs <- cumsum(u); r <- max(which(u - (cs - 1) / seq_along(u) > 0)); pmax(v - (cs[r] - 1) / r, 0) }
fitLS <- function(S, idx = 2:nrow(S), iters = 20000) {
  X <- S[idx - 1, , drop = FALSE]; Y <- S[idx, , drop = FALSE]; K <- ncol(S); P <- diag(K)
  L <- max(eigen(crossprod(X), only.values = TRUE)$values); step <- 1 / L
  for (it in 1:iters) { G <- crossprod(X, X %*% P - Y); P <- P - step * G; P <- t(apply(P, 1, proj_simplex)) }
  dimnames(P) <- list(colnames(S), colnames(S)); P }
migr <- function(P, s) sum(s * (1 - diag(P)))   # share-weighted migration per quarter (fraction of total share moving)
halflife <- function(p) ifelse(p >= 1 - 1e-12, Inf, log(0.5) / log(p))
rd <- function(P) round(P, 5)

load_panel <- function(name, blocs = NULL) {
  W <- read.csv(paste0(D, "panel_", name, ".csv"), check.names = FALSE); q <- W$q; M <- as.matrix(W[,-1])
  if (!is.null(blocs)) M <- sapply(blocs, function(b) rowSums(M[, b, drop = FALSE]))
  S <- M / rowSums(M); rownames(S) <- q; S }
E <- load_panel("E4")
A6 <- load_panel("A", list(JPM = "JPM", GS = "GS", MS = "MS", BAC = "BAC", `C+WFC` = c("C", "WFC"),
                             `Foreign IHCs` = c("Barclays", "UBS+CS", "DB", "BNP", "HSBC", "Mizuho", "RBC", "TD")))
Mk <- read.csv(paste0(D, "market_q.csv")); rownames(Mk) <- Mk$observation_date
t0 <- Sys.time()
analysis_2a <- function(S) {
  Tn <- nrow(S); f <- fitP(S); ls <- fitLS(S); h <- floor(Tn / 2)
  f1 <- fitP(S, 2:h); f2 <- fitP(S, (h + 1):Tn)
  ann <- seq(5, Tn, by = 4); fa <- fitP(S, ann)  # non-overlapping 4-quarter steps (t-4 -> t)
  ua <- list(x = S[ann - 4, ], y = S[ann, ]); fa <- { r <- lphom(intv(ua$x), intv(ua$y), "raw", verbose = FALSE); r$VTM.complete[colnames(S), colnames(S)] }
  sbar <- colMeans(S)
  # in-sample fit: mean absolute share error (pp) of one-step composition, P vs identity (no-change) vs LS
  X <- S[-Tn, ]; Y <- S[-1, ]
  mae <- function(P) mean(abs(X %*% P - Y)) * 100
  # simple accounting baseline: net share change first -> last (pp)
  list(quarters = c(rownames(S)[1], rownames(S)[Tn], Tn), P = rd(f$P), HETe = f$HETe, bounds_lo = rd(f$lo), bounds_hi = rd(f$hi),
       P_ls = rd(ls), P_half1 = rd(f1$P), P_half2 = rd(f2$P), half_split = rownames(S)[h], P_annual = rd(fa),
       retention = round(diag(f$P), 5), halflife_q = round(halflife(diag(f$P)), 1), retention_ls = round(diag(ls), 5),
       migration_per_q = migr(f$P, sbar), migration_ls = migr(ls, sbar), migration_half = c(migr(f1$P, sbar), migr(f2$P, sbar)),
       mae_pp = c(lphom = mae(f$P), ls = mae(ls), identity = mae(diag(ncol(S)))),
       net_change_pp = round((S[Tn, ] - S[1, ]) * 100, 2), first = round(S[1, ] * 100, 2), last = round(S[Tn, ] * 100, 2))
}
R2a <- list(E4 = analysis_2a(E), A6 = analysis_2a(A6))
cat("2a", format(Sys.time() - t0), "\n")

# 2b: market vs sticky — split transitions t-1 -> t by VIX at t (above / below the window median)
analysis_2b <- function(S, nperm = 999) {
  q <- rownames(S); Tn <- nrow(S); idx <- 2:Tn; v <- Mk[q[idx], "vix"]; hi <- idx[v > median(v)]; lo <- idx[v <= median(v)]
  sbar <- colMeans(S); fh <- fitP(S, hi); fl <- fitP(S, lo); obs <- migr(fh$P, sbar) - migr(fl$P, sbar)
  nul <- replicate(nperm, { o <- sample(idx); h <- sort(o[seq_along(hi)]); l <- sort(o[-seq_along(hi)]); migr(fitP(S, h)$P, sbar) - migr(fitP(S, l)$P, sbar) })
  # per-unit (time-varying) matrices via tslphom (nslphom errored on this input): total off-diagonal flow per quarter, vs VIX
  u <- units(S); ns <- tslphom(u$x, u$y, new_and_exit_voters = "raw", verbose = FALSE)
  arr <- ns$VTM.prop.units
  flow <- sapply(seq_along(idx), function(i) { P <- arr[colnames(S), colnames(S), i]; sum(S[idx[i] - 1, ] * (1 - diag(P))) })
  pair <- function(a, b) sapply(seq_along(idx), function(i) { P <- arr[colnames(S), colnames(S), i]; S[idx[i] - 1, a] * P[a, b] })
  ct <- suppressWarnings(cor.test(flow, v, method = "spearman"))
  list(n_hi = length(hi), n_lo = length(lo), vix_median = median(v), P_hi = rd(fh$P), P_lo = rd(fl$P),
       migr_hi = migr(fh$P, sbar), migr_lo = migr(fl$P, sbar), diff = obs,
       p_two_sided = (1 + sum(abs(nul) >= abs(obs))) / (1 + nperm), null_q = unname(quantile(nul, c(.025, .5, .975))),
       unit_quarters = q[idx], unit_flow = flow, unit_vix = v, flow_vix_spearman = unname(ct$estimate), flow_vix_p = ct$p.value,
       HETe_ts = ns$HETe, unit_pairs = if ("GS" %in% colnames(S)) list(GS_JPM = pair("GS", "JPM"), JPM_GS = pair("JPM", "GS"), GS_MS = pair("GS", "MS"), MS_JPM = pair("MS", "JPM")) else NULL)
}
R2b <- list(E4 = analysis_2b(E), A6 = analysis_2b(A6))
cat("2b", format(Sys.time() - t0), "\n")

# 2c: planted truth + persistence-matched no-migration null (E4)
clr <- function(M) { L <- log(M); L - rowMeans(L) }
inv_clr <- function(C) { E <- exp(C); E / rowSums(E) }
fit_ar1 <- function(C) { k <- ncol(C); phi <- numeric(k); mu <- colMeans(C); R <- matrix(0, nrow(C) - 1, k)
  for (j in 1:k) { y <- C[-1, j]; x <- C[-nrow(C), j]; f <- lm(y ~ x); phi[j] <- min(coef(f)[2], 0.99); R[, j] <- y - (coef(f)[1] + coef(f)[2] * x) }
  list(phi = phi, mu = mu, S = cov(R)) }
analysis_2c <- function(S, nsim = 499, nplant = 200) {
  Tn <- nrow(S); C <- clr(S); a <- fit_ar1(C); sbar <- colMeans(S); obsP <- fitP(S)$P; obs <- migr(obsP, sbar)
  sim_null <- function() { X <- matrix(0, Tn, ncol(S)); X[1, ] <- C[1, ]; E <- mvrnorm(Tn, rep(0, ncol(S)), a$S)
    for (t in 2:Tn) X[t, ] <- a$mu + a$phi * (X[t - 1, ] - a$mu) + E[t, ]; Z <- inv_clr(X); colnames(Z) <- colnames(S); Z }
  nul <- replicate(nsim, { Z <- sim_null(); c(migr(fitP(Z)$P, colMeans(Z)), fitP(Z)$P["GS", "JPM"]) })
  # planted truth: GS loses 1.0% of its share to JPM each quarter, MS loses 0.3% to BAC; noise = clr AR(1) innovations x 0.5
  Pt <- diag(ncol(S)); dimnames(Pt) <- list(colnames(S), colnames(S)); Pt["GS", "GS"] <- 0.99; Pt["GS", "JPM"] <- 0.01; Pt["MS", "MS"] <- 0.997; Pt["MS", "BAC"] <- 0.003
  pl <- replicate(nplant, { X <- matrix(0, Tn, ncol(S)); X[1, ] <- S[1, ]
    for (t in 2:Tn) { m <- X[t - 1, ] %*% Pt; X[t, ] <- inv_clr(log(m) + 0.5 * mvrnorm(1, rep(0, ncol(S)), a$S)) }
    colnames(X) <- colnames(S); Pl <- fitP(X)$P; Pq <- fitLS(X, iters = 5000)
    c(lp_gsjpm = Pl["GS", "JPM"], ls_gsjpm = Pq["GS", "JPM"], lp_err = sum(abs(Pl - Pt)), ls_err = sum(abs(Pq - Pt)),
      lp_msbac = Pl["MS", "BAC"], ls_msbac = Pq["MS", "BAC"]) })
  list(obs_migration = obs, obs_GS_JPM = obsP["GS", "JPM"], ar1_phi = round(a$phi, 3),
       null_migration_q = unname(quantile(nul[1, ], c(.025, .5, .975))), p_migration = (1 + sum(nul[1, ] >= obs)) / (1 + nsim),
       null_GSJPM_q = unname(quantile(nul[2, ], c(.025, .5, .975))), p_GSJPM = (1 + sum(nul[2, ] >= obsP["GS", "JPM"])) / (1 + nsim),
       planted = list(P_true = Pt, noise_scale = 0.5, n = nplant,
                      lp_gsjpm_q = unname(quantile(pl["lp_gsjpm", ], c(.05, .5, .95))), ls_gsjpm_q = unname(quantile(pl["ls_gsjpm", ], c(.05, .5, .95))),
                      lp_msbac_q = unname(quantile(pl["lp_msbac", ], c(.05, .5, .95))), ls_msbac_q = unname(quantile(pl["ls_msbac", ], c(.05, .5, .95))),
                      lp_L1err_med = median(pl["lp_err", ]), ls_L1err_med = median(pl["ls_err", ]), lp_better_frac = mean(pl["lp_err", ] < pl["ls_err", ])),
       nsim = nsim)
}
R2c <- list(E4 = analysis_2c(E))
cat("2c", format(Sys.time() - t0), "\n")
# timing of one fit
tt <- system.time(for (i in 1:50) fitP(E))[3] / 50; tt6 <- system.time(for (i in 1:50) fitP(A6))[3] / 50
res <- list(a2 = R2a, b2 = R2b, c2 = R2c, fit_seconds = c(E4 = unname(tt), A6 = unname(tt6)),
            versions = list(R = R.version.string, lphom = as.character(packageVersion("lphom")), lpSolve = as.character(packageVersion("lpSolve"))),
            seed = 20261112, runtime_s = as.numeric(Sys.time() - t0, units = "secs"))
saveRDS(res, paste0(O, "m2_results.rds"))
write_json(res, paste0(O, "m2_results.json"), auto_unbox = TRUE, digits = 6, pretty = TRUE)
cat("done", format(Sys.time() - t0), "\n")
