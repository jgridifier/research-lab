#!/usr/bin/env Rscript
# Methods scout 2026-11-12 (scheduled) — Method 1: ecotraj (Ecological Trajectory Analysis)
# De Caceres et al. 2019 Ecol Monogr 89:e01350; Sturbois et al. 2021 Ecol Model 440:109400;
# Djeghri et al. 2026 Ecol Monogr 96:e70058. ecotraj 1.2.2 (CRAN).
# 1a Q1: directionality of dealer share-composition trajectories (Aitchison space) vs three nulls
# 1b Q1: market-fitted vs residual (sticky) sub-trajectories + rolling-window directionality
# 1c non-Q1: macro-financial stress episodes 1998-2025 as trajectories; DSPD dissimilarity + clustering
suppressPackageStartupMessages({library(ecotraj); library(jsonlite)})
set.seed(20261112)
D <- "/workspace/scout/1112/data/"; O <- "/workspace/scout/1112/out/"
NSIM <- 999
clr <- function(M) { L <- log(M); L - rowMeans(L) }
dirn <- function(C) {   # directionality of one trajectory given T x D coordinates
  x <- defineTrajectories(dist(C), sites = rep("s", nrow(C)), surveys = seq_len(nrow(C)))
  as.numeric(trajectoryDirectionality(x))
}
straight <- function(C) { s <- sqrt(rowSums(diff(C)^2)); sqrt(sum((C[nrow(C),]-C[1,])^2)) / sum(s) }
pathlen <- function(C) sum(sqrt(rowSums(diff(C)^2)))
null_signflip <- function(C) { d <- diff(C); s <- sample(c(-1,1), nrow(d), TRUE); rbind(C[1,], sweep(apply(d * s, 2, cumsum), 2, C[1,], "+")) }   # sweep adds the start row-wise (fixes an R recycling bug in the first draft)
null_ar1 <- function(C, phi, mu, S) {   # persistence-matched, no drift, market co-movement kept via residual cov
  Tn <- nrow(C); k <- ncol(C); E <- MASS::mvrnorm(Tn, rep(0,k), S); X <- matrix(0, Tn, k); X[1,] <- C[1,]
  for (t in 2:Tn) X[t,] <- mu + phi * (X[t-1,] - mu) + E[t,]
  X }
fit_ar1 <- function(C) {
  k <- ncol(C); phi <- numeric(k); mu <- colMeans(C); R <- matrix(0, nrow(C)-1, k)
  for (j in 1:k) { y <- C[-1,j]; x <- C[-nrow(C),j]; f <- lm(y ~ x); phi[j] <- min(coef(f)[2], 0.99)
    R[,j] <- y - (coef(f)[1] + coef(f)[2]*x) }
  list(phi = phi, mu = mu, S = cov(R)) }

panel <- function(name, mcols) {
  W <- read.csv(paste0(D, "panel_", name, ".csv"), check.names = FALSE); q <- W$q; M <- as.matrix(W[,-1])
  S <- M / rowSums(M); C <- clr(S); Tn <- nrow(C)
  obs <- c(dir = dirn(C), straight = straight(C), length = pathlen(C), net = sqrt(sum((C[Tn,]-C[1,])^2)))
  x <- defineTrajectories(dist(C), sites = rep("s", Tn), surveys = 1:Tn)
  t0 <- Sys.time(); perm <- trajectoryDirectionality(x, nperm = NSIM); t_perm <- as.numeric(Sys.time()-t0, units="secs")
  sf <- replicate(NSIM, { Z <- null_signflip(C); c(dirn(Z), straight(Z)) })
  a <- fit_ar1(C)
  ar <- replicate(NSIM, { Z <- null_ar1(C, a$phi, a$mu, a$S); c(dirn(Z), straight(Z)) })
  p <- function(v, o) (1 + sum(v >= o)) / (1 + length(v))
  # 1b market vs residual sub-trajectories
  Mk <- read.csv(paste0(D, "market_q.csv")); rownames(Mk) <- Mk$observation_date
  X <- as.matrix(Mk[q, mcols]); X <- cbind(1, X)
  B <- solve(crossprod(X), crossprod(X, C)); Fit <- X %*% B; Res <- C - Fit
  mk_path <- Fit; st_path <- sweep(Res, 2, colMeans(C), "+")   # residual path re-centred at the mean composition
  r2 <- 1 - colSums(Res^2) / colSums(sweep(C, 2, colMeans(C))^2)
  sub <- list()
  for (nm in c("market", "residual")) { P <- if (nm == "market") mk_path else st_path
    sfP <- replicate(NSIM, dirn(null_signflip(P)))
    sub[[nm]] <- list(dir = dirn(P), straight = straight(P), length = pathlen(P),
                      net = sqrt(sum((P[Tn,]-P[1,])^2)), p_signflip = p(sfP, dirn(P)),
                      signflip_q = unname(quantile(sfP, c(.025,.5,.975)))) }
  # net displacement attribution: (C_T - C_1) = market part + residual part
  dC <- C[Tn,] - C[1,]; dM <- Fit[Tn,] - Fit[1,]; dR <- Res[Tn,] - Res[1,]
  # rolling-window metrics (bandwidth = 4 surveys either side -> 9-quarter windows)
  win <- trajectoryWindowMetrics(x, bandwidth = 4)
  # segment angle vs overall direction: cos between each step and the net displacement
  st <- diff(C); u <- dC / sqrt(sum(dC^2)); cosang <- as.numeric(st %*% u) / sqrt(rowSums(st^2))
  # PCA (= PCoA on Aitchison distance) for plotting
  pc <- prcomp(C, center = TRUE, scale. = FALSE)
  list(panel = name, quarters = c(q[1], q[Tn], Tn), dealers = colnames(M), obs = as.list(obs),
       p_perm_builtin = perm$p.value, t_perm_builtin_s = t_perm,
       p_signflip = p(sf[1,], obs["dir"]), p_ar1 = p(ar[1,], obs["dir"]),
       p_signflip_straight = p(sf[2,], obs["straight"]), p_ar1_straight = p(ar[2,], obs["straight"]),
       signflip_dir_q = unname(quantile(sf[1,], c(.025,.5,.975))), ar1_dir_q = unname(quantile(ar[1,], c(.025,.5,.975))),
       ar1_phi = setNames(as.list(round(a$phi,3)), colnames(M)),
       market_cols = mcols, clr_r2_market = setNames(as.list(round(r2,3)), colnames(M)), sub = sub,
       net_clr = setNames(as.list(round(dC,3)), colnames(M)), net_market = setNames(as.list(round(dM,3)), colnames(M)),
       net_resid = setNames(as.list(round(dR,3)), colnames(M)),
       net_norms = c(total = sqrt(sum(dC^2)), market = sqrt(sum(dM^2)), resid = sqrt(sum(dR^2))),
       window = win, step_cos = cosang, step_len = sqrt(rowSums(st^2)),
       pca = list(scores = pc$x[,1:2], rot = pc$rotation[,1:2], var = (pc$sdev^2/sum(pc$sdev^2))[1:3]),
       mk_pc = predict(pc, mk_path)[,1:2], st_pc = predict(pc, st_path)[,1:2],
       nulls_dir = list(signflip = sf[1,], ar1 = ar[1,]))
}
t0 <- Sys.time()
PP <- parallel::mclapply(list(list("A", c("vix", "nasdaq_ret4", "baa10y", "ta_ind_g1")),
                              list("E4", c("vix", "nasdaq_ret4", "baa10y", "eq_rev_ind_g4"))),
                         function(a) { set.seed(20261112); panel(a[[1]], a[[2]]) }, mc.cores = 2, mc.set.seed = FALSE)
A <- PP[[1]]; E <- PP[[2]]; saveRDS(PP, paste0(O, "m1_panels.rds"))
cat("panels done", format(Sys.time() - t0), "\n")

# ---------- 1c: stress episodes ----------
Z <- read.csv(paste0(D, "stress_monthly_z.csv")); rownames(Z) <- substr(Z[,1], 1, 7); Zm <- as.matrix(Z[,-1])
ep <- c("1998-08 LTCM/Russia" = "1998-08", "2001-09 9/11" = "2001-09", "2002-07 WorldCom" = "2002-07",
        "2007-08 Subprime/quant" = "2007-08", "2008-09 Lehman" = "2008-09", "2010-05 Flash crash/euro" = "2010-05",
        "2011-08 US downgrade/euro" = "2011-08", "2015-08 China deval" = "2015-08", "2018-12 Q4 selloff" = "2018-12",
        "2020-03 COVID" = "2020-03", "2022-02 Rates/Ukraine" = "2022-02", "2023-03 SVB" = "2023-03",
        "2025-04 Tariffs" = "2025-04")
pre <- 2; post <- 12; rows <- c(); sites <- c(); surv <- c()
for (i in seq_along(ep)) { k <- which(rownames(Zm) == ep[i]); idx <- (k - pre):(k + post)
  rows <- c(rows, idx); sites <- c(sites, rep(names(ep)[i], length(idx))); surv <- c(surv, seq_along(idx)) }
S <- Zm[rows, ]
xe <- defineTrajectories(dist(S), sites = sites, surveys = surv)
t1 <- Sys.time()
met <- trajectoryMetrics(xe)
dspd <- trajectoryDistances(xe, distance.type = "DSPD")
t_dspd <- as.numeric(Sys.time() - t1, units = "secs")
# baseline: plain Euclidean distance between aligned state sequences (lock-step), and peak-VIX only
lock <- as.matrix(dist(t(sapply(names(ep), function(s) as.vector(S[sites == s, ])))))
peak <- sapply(names(ep), function(s) max(S[sites == s, "log_vix"]))
hc <- hclust(as.dist(dspd), method = "average"); hl <- hclust(as.dist(lock), method = "average")
cl_d <- cutree(hc, k = 3); cl_l <- cutree(hl, k = 3)
# recovery: distance from start state (survey 1) to last state, relative to the maximum excursion
rec <- t(sapply(names(ep), function(s) { P <- S[sites == s, ]; d0 <- sqrt(rowSums(sweep(P, 2, P[1,])^2))
  c(max_exc = max(d0), end_dist = d0[nrow(P)], ratio = d0[nrow(P)] / max(d0), peak_month = which.max(d0) - pre - 1) }))
pcs <- prcomp(S, center = TRUE)
# stability: DSPD on a 9-month window (onset-2..onset+6) vs 15-month
keep <- surv <= 9
xe9 <- defineTrajectories(dist(S[keep,]), sites = sites[keep], surveys = surv[keep])
d9 <- as.matrix(trajectoryDistances(xe9, distance.type = "DSPD"))
stab_r <- cor(as.dist(d9), as.dist(as.matrix(dspd)), method = "spearman")
# Mantel-style permutation p for that correlation
mp <- mean(replicate(999, { o <- sample(nrow(d9)); cor(as.dist(d9[o,o]), as.dist(as.matrix(dspd)), method="spearman") }) >= stab_r)
dspd_lock_r <- cor(as.dist(as.matrix(dspd)), as.dist(lock), method = "spearman")
met <- as.data.frame(lapply(met, function(c) if (is.list(c)) sapply(c, function(z) z[1]) else c)); met$site <- names(ep)
rec <- as.data.frame(rec); rec$site <- rownames(rec)
EP <- list(episodes = as.list(ep), window = c(pre = pre, post = post), metrics = met, dspd = as.matrix(dspd), lockstep = lock,
           hc_order = hc$labels[hc$order], hc_merge = hc$merge, hc_height = hc$height, cl_dspd = cl_d, cl_lock = cl_l,
           peak_logvix_z = peak, recovery = rec, t_dspd_s = t_dspd, stab_spearman_9v15 = stab_r, stab_mantel_p = mp,
           dspd_vs_lockstep_spearman = dspd_lock_r,
           pca = list(scores = pcs$x[,1:2], rot = pcs$rotation[,1:2], var = (pcs$sdev^2/sum(pcs$sdev^2))[1:3], sites = sites, surv = surv),
           vars = colnames(Zm))
res <- list(A = A, E4 = E, episodes = EP, versions = list(R = R.version.string, ecotraj = as.character(packageVersion("ecotraj"))),
            seed = 20261112, nsim = NSIM, runtime_s = as.numeric(Sys.time() - t0, units = "secs"))
saveRDS(res, paste0(O, "m1_results.rds"))
write_json(res, paste0(O, "m1_results.json"), auto_unbox = TRUE, digits = 6, pretty = TRUE)
cat("done", format(Sys.time() - t0), "\n")
