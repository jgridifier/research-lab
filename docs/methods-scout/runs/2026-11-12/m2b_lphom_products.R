#!/usr/bin/env Rscript
# Methods scout 2026-11-12 — Method 2, analysis 2a': lphom with PRODUCT LINES as voting units (PROXY, Y-9C).
# Unit = (risk type p, year y -> y+1); origin/destination = big-4 dealer shares of that risk type's annual trading
# revenue (Q4 YTD, HI Memo 9.a-e), kept only when all four dealers are positive in both years (54 units).
# Homogeneity = one franchise-wide transfer matrix shared across product lines and years.
# Q1 reading: flows common to all product lines look like franchise/relationship (sticky) migration;
# product-specific deviations (EHet) look like product-cycle (market) moves.
suppressPackageStartupMessages({library(lphom); library(jsonlite)})
set.seed(20261112)
D <- "/workspace/scout/1112/data/"; O <- "/workspace/scout/1112/out/"; SC <- 1e5
DL <- c("JPM", "GS", "MS", "BAC")
df <- read.csv(paste0(D, "products_annual_raw.csv"))
df$ok <- apply(df[, DL] > 0, 1, function(z) isTRUE(all(z)))
U <- do.call(rbind, lapply(split(df, df$product), function(g) { g <- g[order(g$year), ]
  do.call(rbind, lapply(seq_len(nrow(g) - 1), function(i) if (g$year[i + 1] == g$year[i] + 1 && g$ok[i] && g$ok[i + 1])
    data.frame(product = g$product[i], y0 = g$year[i], o = g[i, DL] / sum(g[i, DL]), d = g[i + 1, DL] / sum(g[i + 1, DL]))))}))
O1 <- as.matrix(U[, paste0("o.", DL)]); D1 <- as.matrix(U[, paste0("d.", DL)]); colnames(O1) <- colnames(D1) <- DL
intv <- function(M) { V <- round(M * SC); V[, 1] <- V[, 1] + (SC - rowSums(V)); rownames(V) <- NULL; as.data.frame(V) }
fit <- function(idx, Oi = O1, Di = D1) { r <- lphom(intv(Oi[idx, , drop = FALSE]), intv(Di[idx, , drop = FALSE]), "raw", verbose = FALSE)
  list(P = r$VTM.complete[DL, DL], HETe = r$HETe, EHet = r$EHet) }
all <- seq_len(nrow(U)); f <- fit(all)
eq <- which(U$product == "equity"); ne <- which(U$product != "equity")
fe <- fit(eq); fn <- fit(ne)
lopo <- lapply(unique(U$product), function(p) fit(which(U$product != p))$P); names(lopo) <- unique(U$product)
early <- which(U$y0 <= 2016); late <- which(U$y0 >= 2017); f_early <- fit(early); f_late <- fit(late)
# null: within each unit apply one random dealer relabelling to origin and destination (unit's own dynamics kept,
# cross-unit identity scrambled) -> distribution of pooled off-diagonal flows
nperm <- 999
nul <- replicate(nperm, { Op <- O1; Dp <- D1; for (i in all) { pm <- sample(4); Op[i, ] <- O1[i, pm]; Dp[i, ] <- D1[i, pm] }
  P <- fit(all, Op, Dp)$P; c(gsjpm = P["GS", "JPM"], offmax = max(P - diag(diag(P))), ret_mean = mean(diag(P))) })
P <- f$P; offd <- P; diag(offd) <- NA
pv <- function(v, o) (1 + sum(v >= o)) / (1 + length(v))
# per-product mean absolute residual from the homogeneous fit (share pp): which product lines deviate (product-specific moves)
eh <- abs(f$EHet); eh_prod <- tapply(rowSums(eh) / SC * 100 / 2, U$product, mean)
# naive baseline: average annual net share change per dealer (pp) pooled across units, and equity only
naive <- colMeans(D1 - O1) * 100; naive_eq <- colMeans(D1[eq, ] - O1[eq, ]) * 100
res <- list(n_units = nrow(U), units_per_product = as.list(table(U$product)), years = range(U$y0),
            P = round(P, 5), HETe = f$HETe, P_equity = round(fe$P, 5), P_nonequity = round(fn$P, 5),
            HETe_equity = fe$HETe, HETe_nonequity = fn$HETe, P_lopo = lapply(lopo, round, 5),
            P_early = round(f_early$P, 5), P_late = round(f_late$P, 5), n_early = length(early), n_late = length(late),
            gsjpm = c(all = P["GS", "JPM"], equity = fe$P["GS", "JPM"], nonequity = fn$P["GS", "JPM"], early = f_early$P["GS", "JPM"], late = f_late$P["GS", "JPM"],
                      sapply(lopo, function(m) m["GS", "JPM"])),
            null = list(gsjpm_q = unname(quantile(nul["gsjpm", ], c(.025, .5, .975))), p_gsjpm = pv(nul["gsjpm", ], P["GS", "JPM"]),
                        offmax_q = unname(quantile(nul["offmax", ], c(.025, .5, .975))), p_offmax = pv(nul["offmax", ], max(offd, na.rm = TRUE)),
                        ret_mean_q = unname(quantile(nul["ret_mean", ], c(.025, .5, .975))), p_ret_low = (1 + sum(nul["ret_mean", ] <= mean(diag(P)))) / (1 + nperm), nperm = nperm),
            ehet_pp_by_product = as.list(round(eh_prod, 3)), naive_pp = round(naive, 3), naive_eq_pp = round(naive_eq, 3),
            versions = list(lphom = as.character(packageVersion("lphom"))))
write_json(res, paste0(O, "m2b_products.json"), auto_unbox = TRUE, digits = 6, pretty = TRUE)
print(res[c("n_units", "units_per_product", "P", "HETe", "P_equity", "P_nonequity", "gsjpm", "null", "ehet_pp_by_product", "naive_pp", "naive_eq_pp", "P_early", "P_late")])
