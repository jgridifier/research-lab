## ebnm 1.1.42 black-box oracle fixtures (SYNTHETIC Q2 mock ZBB data, 2026-11-13 generator seed 20261113)
## Reproduces the A1 level fit of runs/2026-11-13/m1_ebnm.R (ash = normal_scale_mixture, mode 0) and writes
## inputs + outputs to JSON for a separate Python parity program. Not committed (per-program rows); summaries only.
suppressMessages({library(ebnm); library(jsonlite)})
D <- "/workspace/scout/1113/data/"
out <- list(); out$smngrid <- list(KL=ebnm:::smngrid$KL, m=ebnm:::smngrid$m)
for (firm in c("Corning_mock","MorganStanley_mock")) {
  F <- read.csv(paste0(D, firm, "_features.csv"), check.names=FALSE)
  yrs <- as.integer(sub("^y","",grep("^y[0-9]{4}$",names(F),value=TRUE))); T1 <- max(yrs)
  y <- F[[paste0("y",T1)]]; ok <- !is.na(y)
  d <- data.frame(id=F$program_id[ok], group=F$group[ok], x=y[ok] + F$sigma[ok]^2/2, s=F$sigma[ok])
  gm <- ave(d$x, d$group, FUN=mean); gn <- ave(d$x, d$group, FUN=length)
  gm[gn < 3] <- NA; d$m <- ifelse(is.na(gm), mean(d$x), gm)
  x <- d$x - d$m; s <- d$s
  res <- list(x=x, s=s)
  for (fam in c("normal_scale_mixture","point_normal","normal")) {
    t0 <- Sys.time()
    f <- ebnm(x, s, prior_family=fam, mode=0, output=ebnm_output_all())
    sec <- as.numeric(difftime(Sys.time(), t0, units="secs"))
    res[[fam]] <- list(loglik=as.numeric(logLik(f)), pi=f$fitted_g$pi, sd=f$fitted_g$sd, mean=f$fitted_g$mean,
      post_mean=f$posterior$mean, post_sd=f$posterior$sd, lfsr=f$posterior$lfsr, sec=sec)
  }
  ## timing: median of 20 ash fits
  tt <- replicate(20, system.time(ebnm(x, s, prior_family="normal_scale_mixture", mode=0))[["elapsed"]])
  res$ash_sec_median20 <- median(tt)
  out[[firm]] <- res
}
write_json(out, "oracle/fixtures.json", digits=NA, auto_unbox=TRUE)
cat("done\n")
