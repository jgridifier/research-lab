## 2026-11-13 methods scout, Method 1: ebnm (empirical Bayes normal means; Stephens lab, statistical genetics)
## SYNTHETIC mock ZBB data only. Features are observables; KEY files are used only for scoring.
suppressMessages({library(ebnm); library(jsonlite)})
D <- "/workspace/scout/1113/data/"; set.seed(20261113)
fams <- c(normal="normal", point_normal="point_normal", ash="normal_scale_mixture", unimodal="unimodal", npmle="npmle", deconvolver="deconvolver")
fit_all <- function(x, s, mode=0){
  out <- list()
  for (nm in names(fams)) {
    t0 <- Sys.time()
    f <- tryCatch(ebnm(x, s, prior_family=fams[[nm]], mode=if (fams[[nm]] %in% c("npmle","deconvolver")) 0 else mode), error=function(e) NULL)
    if (is.null(f) && nm=="deconvolver") { # deconvolver needs s==1; run on z-scale? skip honestly
      out[[nm]] <- NULL; next }
    out[[nm]] <- list(fit=f, sec=as.numeric(difftime(Sys.time(), t0, units="secs")))
  }
  out
}
rmse <- function(a,b) sqrt(mean((a-b)^2))
res <- list()
for (firm in c("Corning_mock","MorganStanley_mock")) {
  F <- read.csv(paste0(D, firm, "_features.csv"), check.names=FALSE)
  K <- read.csv(paste0(D, firm, "_KEY_true_levels.csv")); L <- read.csv(paste0(D, firm, "_KEY_labels.csv"))
  yrs <- sort(unique(K$fiscal_year)); T1 <- max(yrs); T0 <- T1-1
  tl <- function(yr) { k <- K[K$fiscal_year==yr,]; setNames(log(k$true_usd), k$program_id) }
  r <- list()
  ## ---------- A1 Borrowing strength: 2025 level
  lev <- function(yr){
    y <- F[[paste0("y",yr)]]; ok <- !is.na(y)
    d <- data.frame(id=F$program_id[ok], group=F$group[ok], x=y[ok] + F$sigma[ok]^2/2, s=F$sigma[ok])
    gm <- ave(d$x, d$group, FUN=mean); gn <- ave(d$x, d$group, FUN=length)
    gm[gn < 3] <- NA; d$m <- ifelse(is.na(gm), mean(d$x), gm)   # tiny groups fall back to the global mean
    fits <- fit_all(d$x - d$m, d$s)
    est <- sapply(names(fits), function(n) d$m + fits[[n]]$fit$posterior$mean)
    psd <- sapply(names(fits), function(n) fits[[n]]$fit$posterior$sd)
    list(d=d, fits=fits, est=est, psd=psd)
  }
  A <- lev(T1); d <- A$d; truth <- tl(T1)[d$id]
  fam <- L$family[match(d$id, L$program_id)]; infam <- !is.na(fam) & fam!=""
  tab <- data.frame(estimator=c("Own 2025 actual (no pooling)","Group mean (complete pooling)", paste0("ebnm: ", colnames(A$est))),
    rmse_all = c(rmse(d$x,truth), rmse(d$m,truth), apply(A$est,2,rmse,b=truth)),
    rmse_family = c(rmse(d$x[infam],truth[infam]), rmse(d$m[infam],truth[infam]), apply(A$est[infam,,drop=FALSE],2,rmse,b=truth[infam])),
    rmse_nonfamily = c(rmse(d$x[!infam],truth[!infam]), rmse(d$m[!infam],truth[!infam]), apply(A$est[!infam,,drop=FALSE],2,rmse,b=truth[!infam])),
    cover90 = c(mean(abs(d$x-truth) <= 1.645*d$s), NA, sapply(colnames(A$est), function(n) mean(abs(A$est[,n]-truth) <= 1.645*A$psd[,n]))),
    seconds = c(NA, NA, sapply(names(A$fits), function(n) A$fits[[n]]$sec)),
    loglik = c(NA, NA, sapply(names(A$fits), function(n) as.numeric(logLik(A$fits[[n]]$fit)))))
  r$A1 <- list(n=nrow(d), n_family=sum(infam), table=tab,
     sigma_check = list(median_sigma_hat=median(d$s), realized_sd_own_error=sd(d$x-truth), corr_abs_err_sigma=cor(abs(d$x-truth), d$s)),
     ash_g = list(pi=A$fits$ash$fit$fitted_g$pi, sd=A$fits$ash$fit$fitted_g$sd), normal_g_sd = A$fits$normal$fit$fitted_g$sd)
  ## per-family example for the figure: largest family
  ex <- names(sort(table(fam[infam]), decreasing=TRUE))[1]; w <- which(fam==ex)
  r$A1$example <- list(family=ex, id=d$id[w], raw=d$x[w], ash=A$est[w,"ash"], truth=unname(truth[w]), s=d$s[w], group=d$group[w][1])
  ## by number of years observed
  kk <- F$k[match(d$id,F$program_id)]
  r$A1$by_k <- do.call(rbind, lapply(sort(unique(kk)), function(k){ i<-kk==k; data.frame(k=k,n=sum(i),raw=rmse(d$x[i],truth[i]),ash=rmse(A$est[i,"ash"],truth[i]),normal=rmse(A$est[i,"normal"],truth[i]))}))
  ## ---------- A2 Real change vs noise: 2024->2025
  y1 <- F[[paste0("y",T1)]]; y0 <- F[[paste0("y",T0)]]; ok <- !is.na(y1) & !is.na(y0)
  g <- (y1-y0)[ok]; s <- sqrt(2)*F$sigma[ok]; id <- F$program_id[ok]
  tg <- tl(T1)[id]-tl(T0)[id]
  fa <- ebnm(g, s, prior_family="normal_scale_mixture", mode=0, output=ebnm_output_all())
  fn <- ebnm(g, s, prior_family="normal", mode="estimate")
  fpn <- ebnm(g, s, prior_family="point_normal", mode=0, output=ebnm_output_all())
  calls <- function(sel, est) { n<-sum(sel); fs <- if(n>0) mean(sign(est[sel])!=sign(tg[sel])) else NA; c(n_calls=n, false_sign_rate=fs, true_pos=sum(sel & sign(est)==sign(tg))) }
  z <- g/s; p <- 2*pnorm(-abs(z))
  ct <- rbind(
    "Naive z-test |z|>1.96" = calls(abs(z)>1.96, g),
    "Naive + BH q<0.05" = calls(p.adjust(p,"BH")<0.05, g),
    "ebnm ash, lfsr<0.05" = calls(fa$posterior$lfsr<0.05, fa$posterior$mean),
    "ebnm point-normal, lfsr<0.05" = calls(fpn$posterior$lfsr<0.05, fpn$posterior$mean),
    "ebnm ash, lfsr<0.01" = calls(fa$posterior$lfsr<0.01, fa$posterior$mean))
  ## relative version: change versus the portfolio-typical change (centre at the estimated mode)
  fm <- ebnm(g, s, prior_family="normal_scale_mixture", mode="estimate"); md <- fm$fitted_g$mean[1]
  fr <- ebnm(g-md, s, prior_family="normal_scale_mixture", mode=0, output=ebnm_output_all())
  tgr <- tg - md; zr <- (g-md)/s
  callsr <- function(sel, est) { n<-sum(sel); c(n_calls=n, false_sign_rate=if(n) mean(sign(est[sel])!=sign(tgr[sel])) else NA) }
  ctr <- rbind("Naive |z|>1.96 (relative)"=callsr(abs(zr)>1.96, g-md), "Naive + BH (relative)"=callsr(p.adjust(2*pnorm(-abs(zr)),"BH")<0.05, g-md), "ebnm ash lfsr<0.05 (relative)"=callsr(fr$posterior$lfsr<0.05, fr$posterior$mean))
  ## calibration: among programs with lfsr in bins, realized wrong-sign rate
  lb <- cut(fa$posterior$lfsr, c(-1,0.01,0.05,0.2,0.5,1.01)); cal <- tapply(sign(fa$posterior$mean)!=sign(tg), lb, mean); calN <- table(lb)
  r$A2 <- list(n=length(g), mode_ash=fa$fitted_g$mean[1], rmse_raw=rmse(g,tg), rmse_ash=rmse(fa$posterior$mean,tg), rmse_normal=rmse(fn$posterior$mean,tg),
    calls=as.data.frame(ct), calls_relative=as.data.frame(ctr), mode_typical=md, calibration=data.frame(bin=names(cal), n=as.integer(calN), wrong_sign=as.numeric(cal)),
    scatter=list(g=g, ash=fa$posterior$mean, truth=unname(tg), lfsr=fa$posterior$lfsr))
  ## portfolio: behaviour of continuing programs, raw vs EB-denoised
  B0 <- lev(T0); ids <- intersect(A$d$id, B0$d$id)
  cont <- F$program_id[F$program_id %in% ids]
  lvl <- function(L, n, ids) { i <- match(ids, L$d$id); exp(L$est[i,n] + L$psd[i,n]^2/2) }
  raw_beh <- sum(exp(A$d$x[match(cont,A$d$id)] - A$d$s[match(cont,A$d$id)]^2/2)) - sum(exp(B0$d$x[match(cont,B0$d$id)] - B0$d$s[match(cont,B0$d$id)]^2/2))
  eb_beh <- sum(lvl(A,"ash",cont)) - sum(lvl(B0,"ash",cont))
  tru_beh <- sum(exp(tl(T1)[cont])) - sum(exp(tl(T0)[cont]))
  S <- fromJSON(paste0(D, firm, "_KEY_summary.json"))
  r$A2$portfolio <- list(n_continuing=length(cont), raw_behavior=raw_beh, eb_behavior=eb_beh, true_behavior=tru_beh, key_actual_behavior=S$mix_vs_behavior$actual$behavior_continuing, key_true_behavior=S$mix_vs_behavior$true$behavior_continuing)
  ## ---------- A3 Text vs numbers: stated grow/transform, numbers say declining
  ok <- !is.na(F$slope) & F$stated_intent %in% c("grow","transform")
  x <- F$slope[ok]; s <- F$sigma[ok]/sqrt(F$sxx[ok]); id <- F$program_id[ok]
  lab <- L$mismatch[match(id, L$program_id)]; pos <- !is.na(lab) & lab=="stated_growth_actually_declining"
  f3 <- ebnm(x, s, prior_family="normal_scale_mixture", mode=0, output=ebnm_output_all())
  pneg <- 1 - pnorm(0, f3$posterior$mean, f3$posterior$sd) # approx; use lfsr with sign instead below
  flag_eb <- f3$posterior$mean < 0 & f3$posterior$lfsr < 0.05
  zt <- x/s; flag_naive <- pnorm(zt) < 0.05; flag_bh <- p.adjust(pnorm(zt),"BH") < 0.05
  flag_raw <- x < 0
  pr <- function(fl) c(flagged=sum(fl), hits=sum(fl&pos), precision=if(sum(fl)) sum(fl&pos)/sum(fl) else NA, recall=sum(fl&pos)/sum(pos))
  auc <- function(score) { r <- rank(score); (sum(r[pos]) - sum(pos)*(sum(pos)+1)/2)/(sum(pos)*sum(!pos)) }
  ## ranking score: posterior mean (lower = more declining) vs naive z
  r$A3 <- list(n=sum(ok), n_planted=sum(pos), mode=f3$fitted_g$mean[1],
     table=as.data.frame(rbind("Raw slope < 0"=pr(flag_raw), "Naive one-sided t, p<0.05"=pr(flag_naive), "Naive + BH q<0.05"=pr(flag_bh), "ebnm ash: post. mean<0, lfsr<0.05"=pr(flag_eb))),
     auc=list(raw_slope=auc(-x), naive_z=auc(-zt), ebnm_postmean=auc(-f3$posterior$mean)),
     planted=data.frame(id=id[pos], slope=x[pos], s=s[pos], post=f3$posterior$mean[pos], lfsr=f3$posterior$lfsr[pos]),
     top_flags=data.frame(id=id[flag_eb], post=f3$posterior$mean[flag_eb], lfsr=f3$posterior$lfsr[flag_eb], planted=pos[flag_eb], keylab=lab[flag_eb]))
  res[[firm]] <- r
  cat("==", firm, "\n"); print(tab); print(r$A1$sigma_check); print(ct); print(ctr); cat("typical change", md, "\n"); print(r$A2$portfolio |> unlist()); print(r$A3$table); print(unlist(r$A3$auc))
}
res$versions <- list(ebnm=as.character(packageVersion("ebnm")), ashr=as.character(packageVersion("ashr")), mixsqp=as.character(packageVersion("mixsqp")), R=R.version.string)
write_json(res, "/workspace/scout/1113/out/m1_results.json", auto_unbox=TRUE, digits=NA, pretty=FALSE)
