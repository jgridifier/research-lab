#!/usr/bin/env Rscript
# Methods scout 2026-11-12 ad hoc, method 1: codyn (Hallett et al. 2016 MEE)
# PROXY FR Y-9C dealer panels. Descriptive only. Seed 20261112.
# No raw data is written besides aggregates in the JSON.

suppressPackageStartupMessages({
  library(codyn)
  library(jsonlite)
})

SEED <- 20261112
set.seed(SEED)
BOOT <- 999
t0 <- proc.time()[3]
cat("codyn version", as.character(packageVersion("codyn")), "\n")

A <- read.csv("/workspace/scout/1112-adhoc/data/panel_A.csv", check.names = FALSE)
E <- read.csv("/workspace/scout/1112-adhoc/data/panel_E4.csv", check.names = FALSE)
stopifnot("q" %in% names(A), "q" %in% names(E))

to_tidy <- function(wide, value = "abundance") {
  sp <- setdiff(names(wide), "q")
  out <- do.call(rbind, lapply(sp, function(s) {
    data.frame(q = wide$q, t = seq_len(nrow(wide)), species = s,
               abundance = wide[[s]], stringsAsFactors = FALSE)
  }))
  rownames(out) <- NULL
  out
}

shares_wide <- function(wide) {
  sp <- setdiff(names(wide), "q")
  tot <- rowSums(wide[sp])
  out <- wide
  out[sp] <- wide[sp] / tot
  out
}

first_last_ranks <- function(sh) {
  sp <- setdiff(names(sh), "q")
  r1 <- rank(-as.numeric(sh[1, sp]), ties.method = "average")
  r2 <- rank(-as.numeric(sh[nrow(sh), sp]), ties.method = "average")
  s1 <- as.numeric(sh[1, sp]); s2 <- as.numeric(sh[nrow(sh), sp])
  data.frame(species = sp, rank_first = as.numeric(r1), rank_last = as.numeric(r2),
             d_rank = as.numeric(r2 - r1),
             share_first = s1, share_last = s2, d_share = s2 - s1,
             stringsAsFactors = FALSE)
}

# ---- official package metrics on one panel ----
run_panel <- function(wide, pname, raw_for_vr = TRUE) {
  sh <- shares_wide(wide)
  td_raw <- to_tidy(wide)
  td_sh  <- to_tidy(sh)
  sp <- setdiff(names(wide), "q")
  qs <- wide$q
  nT <- length(qs)

  # 1. ranks first/last (on shares)
  fl <- first_last_ranks(sh)

  # 2. turnover on raw (and on shares) -- presence is abundance > 0
  turn_total <- turnover(td_raw, time.var = "t", species.var = "species",
                         abundance.var = "abundance", metric = "total")
  turn_app <- turnover(td_raw, time.var = "t", species.var = "species",
                       abundance.var = "abundance", metric = "appearance")
  turn_dis <- turnover(td_raw, time.var = "t", species.var = "species",
                       abundance.var = "abundance", metric = "disappearance")

  # 3. rank_shift on SHARES (relative abundance ranks)
  rs <- rank_shift(td_sh, time.var = "t", species.var = "species",
                   abundance.var = "abundance")
  # column names: year_pair / MRS or similar — inspect
  rs_cols <- names(rs)

  # 4. rate_change on SHARES
  rc <- rate_change(td_sh, time.var = "t", species.var = "species",
                    abundance.var = "abundance")
  rci <- rate_change_interval(td_sh, time.var = "t", species.var = "species",
                              abundance.var = "abundance")

  # 5. variance_ratio on RAW amounts (shares would make var(sum)=0)
  vr <- variance_ratio(td_raw, time.var = "t", species.var = "species",
                       abundance.var = "abundance", bootnumber = BOOT, level = 0.95)
  # sanity: VR on shares ~ 0
  vr_sh <- variance_ratio(td_sh, time.var = "t", species.var = "species",
                          abundance.var = "abundance", bootnumber = 20, level = 0.95)

  # 6. Loreau synchrony on RAW (not shares)
  syn_L <- synchrony(td_raw, time.var = "t", species.var = "species",
                     abundance.var = "abundance", metric = "Loreau")
  syn_G <- synchrony(td_raw, time.var = "t", species.var = "species",
                     abundance.var = "abundance", metric = "Gross")

  list(panel = pname, nT = nT, n_species = length(sp), species = sp,
       q_first = qs[1], q_last = qs[nT],
       first_last = fl,
       turnover = list(total_mean = mean(turn_total[[ncol(turn_total)]]),
                       appearance_mean = mean(turn_app[[ncol(turn_app)]]),
                       disappearance_mean = mean(turn_dis[[ncol(turn_dis)]]),
                       total = turn_total, appearance = turn_app, disappearance = turn_dis),
       rank_shift = rs, rank_shift_cols = rs_cols,
       rank_shift_mean = mean(rs[[ncol(rs)]]),
       rate_change = as.numeric(rc),
       rate_change_interval = rci,
       variance_ratio = vr, variance_ratio_on_shares = vr_sh,
       synchrony_Loreau = as.numeric(syn_L),
       synchrony_Gross = as.numeric(syn_G))
}

# Cyclic-shift a tidy share/raw frame: independently rotate each species.
cyclic_one <- function(td, lag_by_species) {
  out <- td
  for (s in unique(td$species)) {
    ix <- which(td$species == s)
    ix <- ix[order(td$t[ix])]
    k <- lag_by_species[[s]]
    out$abundance[ix] <- td$abundance[ix][c((k + 1):length(ix), seq_len(k))]
  }
  out
}

null_rank_and_rate <- function(td_sh, nboot = BOOT, seed = SEED) {
  set.seed(seed)
  spp <- unique(td_sh$species)
  nT <- max(td_sh$t)
  mrs <- numeric(nboot); rch <- numeric(nboot)
  for (b in seq_len(nboot)) {
    lags <- setNames(as.list(sample(0:(nT - 1), length(spp), replace = TRUE)), spp)
    nd <- cyclic_one(td_sh, lags)
    rs <- rank_shift(nd, time.var = "t", species.var = "species",
                     abundance.var = "abundance")
    mrs[b] <- mean(rs[[ncol(rs)]])
    rch[b] <- as.numeric(rate_change(nd, time.var = "t", species.var = "species",
                                     abundance.var = "abundance"))
  }
  list(mrs_null = mrs, rate_null = rch)
}

# Windows
window_vr <- function(wide, q0, q1) {
  sub <- wide[wide$q >= q0 & wide$q <= q1, , drop = FALSE]
  if (nrow(sub) < 8) return(NULL)
  td <- to_tidy(sub)
  vr <- variance_ratio(td, time.var = "t", species.var = "species",
                       abundance.var = "abundance", bootnumber = BOOT, level = 0.95)
  sh <- shares_wide(sub)
  rs <- rank_shift(to_tidy(sh), time.var = "t", species.var = "species",
                   abundance.var = "abundance")
  rc <- rate_change(to_tidy(sh), time.var = "t", species.var = "species",
                    abundance.var = "abundance")
  list(q0 = q0, q1 = q1, n = nrow(sub), vr = vr,
       rank_shift_mean = mean(rs[[ncol(rs)]]), rate_change = as.numeric(rc))
}

# Leave-out VR (raw)
vr_drop <- function(wide, drop) {
  keep <- setdiff(names(wide), c("q", drop))
  sub <- wide[, c("q", keep), drop = FALSE]
  td <- to_tidy(sub)
  variance_ratio(td, time.var = "t", species.var = "species",
                 abundance.var = "abundance", bootnumber = BOOT, level = 0.95)
}

# Rank series for clocks (share ranks, 1 = largest share)
rank_series <- function(sh) {
  sp <- setdiff(names(sh), "q")
  M <- t(apply(as.matrix(sh[sp]), 1, function(x) rank(-x, ties.method = "average")))
  colnames(M) <- sp
  M
}

summarize_vr <- function(vr) {
  # variance_ratio returns a data frame; inspect names at runtime
  if (is.data.frame(vr)) as.list(vr[1, , drop = TRUE]) else as.list(vr)
}

cat("==== running panel A ====\n")
ta <- proc.time()[3]
resA <- run_panel(A, "A")
cat("A package metrics in", round(proc.time()[3] - ta, 2), "s\n")
print(resA$variance_ratio)
print(resA$rank_shift_cols)
print(head(resA$rank_shift))
print(resA$rate_change)
print(resA$first_last)
print(c(synL = resA$synchrony_Loreau, synG = resA$synchrony_Gross,
        mrs = resA$rank_shift_mean, turn = resA$turnover$total_mean))

cat("==== running panel E4 ====\n")
te <- proc.time()[3]
resE <- run_panel(E, "E4")
cat("E4 package metrics in", round(proc.time()[3] - te, 2), "s\n")
print(resE$variance_ratio)
print(resE$first_last)
print(c(synL = resE$synchrony_Loreau, synG = resE$synchrony_Gross,
        mrs = resE$rank_shift_mean, rc = resE$rate_change, turn = resE$turnover$total_mean))

# Nulls for rank_shift and rate_change
cat("==== cyclic-shift nulls for rank_shift / rate_change ====\n")
tn <- proc.time()[3]
nullA <- null_rank_and_rate(to_tidy(shares_wide(A)), BOOT, SEED)
nullE <- null_rank_and_rate(to_tidy(shares_wide(E)), BOOT, SEED + 1)
cat("nulls in", round(proc.time()[3] - tn, 2), "s\n")

p_ge <- function(obs, nul) (1 + sum(nul >= obs)) / (1 + length(nul))
p_le <- function(obs, nul) (1 + sum(nul <= obs)) / (1 + length(nul))

# Windows
winA <- list(
  window_vr(A, "2016Q3", "2019Q4"),
  window_vr(A, "2020Q1", "2026Q2")
)
winE <- list(
  window_vr(E, "2011Q1", "2015Q4"),
  window_vr(E, "2016Q1", "2019Q4"),
  window_vr(E, "2020Q1", "2026Q2")
)
names(winA) <- c("2016Q3-2019Q4", "2020Q1-2026Q2")
names(winE) <- c("2011Q1-2015Q4", "2016Q1-2019Q4", "2020Q1-2026Q2")

# Leave-out on E4: drop GS, drop JPM, drop both (the suspected swap pair)
loE <- list(
  all = summarize_vr(resE$variance_ratio),
  drop_GS = summarize_vr(vr_drop(E, "GS")),
  drop_JPM = summarize_vr(vr_drop(E, "JPM")),
  drop_GS_JPM = summarize_vr(vr_drop(E, c("GS", "JPM"))),
  drop_MS = summarize_vr(vr_drop(E, "MS")),
  drop_BAC = summarize_vr(vr_drop(E, "BAC"))
)
loA_big <- list(
  all = summarize_vr(resA$variance_ratio),
  drop_foreign = summarize_vr(vr_drop(A, c("Barclays","UBS+CS","DB","BNP","HSBC","Mizuho","RBC","TD"))),
  drop_JPM = summarize_vr(vr_drop(A, "JPM")),
  US_big6_only = summarize_vr(vr_drop(A, c("Barclays","UBS+CS","DB","BNP","HSBC","Mizuho","RBC","TD"))),
  foreign_only = summarize_vr(vr_drop(A, c("JPM","GS","MS","BAC","C","WFC")))
)

# Rank and share series for figures
shA <- shares_wide(A); shE <- shares_wide(E)
rkA <- rank_series(shA); rkE <- rank_series(shE)

# Pack JSON-friendly objects
pack_fl <- function(fl) {
  lapply(seq_len(nrow(fl)), function(i) as.list(fl[i, ]))
}
pack_df <- function(d) {
  # data frame to list-of-columns (and list-of-rows)
  cols <- lapply(d, function(x) unname(if (is.factor(x)) as.character(x) else x))
  cols
}
pack_vr <- function(vr) summarize_vr(vr)
pack_win <- function(w) {
  lapply(w, function(x) {
    if (is.null(x)) return(NULL)
    list(q0 = x$q0, q1 = x$q1, n = x$n, vr = pack_vr(x$vr),
         rank_shift_mean = x$rank_shift_mean, rate_change = x$rate_change)
  })
}

null_summary <- function(obs, nul, alternative = "greater") {
  list(observed = unname(obs),
       null_mean = mean(nul), null_sd = sd(nul),
       null_q025 = unname(quantile(nul, 0.025)),
       null_q975 = unname(quantile(nul, 0.975)),
       null_min = min(nul), null_max = max(nul),
       p_ge = p_ge(obs, nul), p_le = p_le(obs, nul),
       nboot = length(nul))
}

out <- list(
  meta = list(method = "codyn", version = as.character(packageVersion("codyn")),
              seed = SEED, boot = BOOT, date = "2026-11-12",
              elapsed_s = unname(proc.time()[3] - t0),
              R = paste(R.version$major, R.version$minor, sep = "."),
              note = "PROXY FR Y-9C. VR and Loreau/Gross synchrony use RAW amounts (VR on shares is degenerate because the share total is 1). rank_shift, rate_change, rank clocks use SHARES. Cyclic-shift nulls preserve each series' autocorrelation (Hallett et al. 2014)."),
  A = list(
    q = A$q, species = resA$species, nT = resA$nT,
    first_last = pack_fl(resA$first_last),
    turnover_mean = list(total = resA$turnover$total_mean,
                         appearance = resA$turnover$appearance_mean,
                         disappearance = resA$turnover$disappearance_mean),
    rank_shift_mean = resA$rank_shift_mean,
    rank_shift = pack_df(resA$rank_shift),
    rate_change = resA$rate_change,
    rate_change_interval = pack_df(resA$rate_change_interval),
    vr = pack_vr(resA$variance_ratio),
    vr_on_shares = pack_vr(resA$variance_ratio_on_shares),
    synchrony_Loreau = resA$synchrony_Loreau,
    synchrony_Gross = resA$synchrony_Gross,
    shares = lapply(setdiff(names(shA), "q"), function(s) unname(shA[[s]])),
    ranks = lapply(colnames(rkA), function(s) unname(rkA[, s])),
    share_names = setdiff(names(shA), "q"),
    mrs_null = null_summary(resA$rank_shift_mean, nullA$mrs_null),
    rate_null = null_summary(resA$rate_change, nullA$rate_null),
    windows = pack_win(winA),
    leaveout = lapply(loA_big, function(x) x)
  ),
  E4 = list(
    q = E$q, species = resE$species, nT = resE$nT,
    first_last = pack_fl(resE$first_last),
    turnover_mean = list(total = resE$turnover$total_mean,
                         appearance = resE$turnover$appearance_mean,
                         disappearance = resE$turnover$disappearance_mean),
    rank_shift_mean = resE$rank_shift_mean,
    rank_shift = pack_df(resE$rank_shift),
    rate_change = resE$rate_change,
    rate_change_interval = pack_df(resE$rate_change_interval),
    vr = pack_vr(resE$variance_ratio),
    vr_on_shares = pack_vr(resE$variance_ratio_on_shares),
    synchrony_Loreau = resE$synchrony_Loreau,
    synchrony_Gross = resE$synchrony_Gross,
    shares = lapply(setdiff(names(shE), "q"), function(s) unname(shE[[s]])),
    ranks = lapply(colnames(rkE), function(s) unname(rkE[, s])),
    share_names = setdiff(names(shE), "q"),
    mrs_null = null_summary(resE$rank_shift_mean, nullE$mrs_null),
    rate_null = null_summary(resE$rate_change, nullE$rate_null),
    windows = pack_win(winE),
    leaveout = loE
  )
)
# attach species names to shares/ranks
names(out$A$shares) <- out$A$share_names
names(out$A$ranks)  <- out$A$share_names
names(out$E4$shares) <- out$E4$share_names
names(out$E4$ranks)  <- out$E4$share_names

# also dump raw null vectors for figures (1000 is fine)
out$A$mrs_null$samples_head <- unname(nullA$mrs_null)
out$A$rate_null$samples_head <- unname(nullA$rate_null)
out$E4$mrs_null$samples_head <- unname(nullE$mrs_null)
out$E4$rate_null$samples_head <- unname(nullE$rate_null)
out$meta$elapsed_s <- unname(proc.time()[3] - t0)

write_json(out, "/workspace/scout/1112-adhoc/out/m1_results.json",
           pretty = TRUE, auto_unbox = TRUE, digits = 10, na = "null")
cat("WROTE m1_results.json in", round(out$meta$elapsed_s, 2), "s\n")

cat("\n==== KEY NUMBERS ====\n")
cat("A  VR:", jsonlite::toJSON(out$A$vr, auto_unbox=TRUE), "\n")
cat("E4 VR:", jsonlite::toJSON(out$E4$vr, auto_unbox=TRUE), "\n")
cat("A  MRS obs/null p_ge:", out$A$rank_shift_mean, out$A$mrs_null$null_mean, out$A$mrs_null$p_ge, "\n")
cat("E4 MRS obs/null p_ge:", out$E4$rank_shift_mean, out$E4$mrs_null$null_mean, out$E4$mrs_null$p_ge, "\n")
cat("A  rate obs/null p_ge:", out$A$rate_change, out$A$rate_null$null_mean, out$A$rate_null$p_ge, "\n")
cat("E4 rate obs/null p_ge:", out$E4$rate_change, out$E4$rate_null$null_mean, out$E4$rate_null$p_ge, "\n")
cat("A  turnover mean:", out$A$turnover_mean$total, "\n")
cat("E4 turnover mean:", out$E4$turnover_mean$total, "\n")
