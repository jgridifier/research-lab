suppressPackageStartupMessages({library(isodistrreg); library(jsonlite)})
set.seed(20261114); setwd('.')
P <- read.csv('q3_panel.csv'); P <- P[P$year<=2025 & !is.na(P$payout_rwa) & !is.na(P$drawdown),]
pct <- function(v) (rank(v, ties.method='average')-0.5)/length(v)
P$y_pct <- ave(P$payout_rwa, P$year, FUN=pct); P$dd_pct <- ave(P$drawdown, P$year, FUN=pct); P$pt_pct <- ave(P$income_pretax_net_rate, P$year, FUN=pct)
crps_norm <- function(y,mu,s){ z <- (y-mu)/s; s*(z*(2*pnorm(z)-1)+2*dnorm(z)-1/sqrt(pi)) }
crps_emp <- function(ytr, y) sapply(y, function(v) mean(abs(ytr-v)) - 0.5*mean(abs(outer(ytr,ytr,'-'))))
fit_idr <- function(ytr, Xtr, Xte){ fit <- idr(y=ytr, X=as.data.frame(Xtr), progress=FALSE); predict(fit, data=as.data.frame(Xte)) }
# LOYO evaluation. sign: +1 isotonic, -1 antitonic per covariate (pre-specified)
loyo <- function(D, yv, xv, sgn){
  yrs <- sort(unique(D$year)); out <- NULL
  for (yy in yrs){ tr <- D[D$year!=yy,]; te <- D[D$year==yy,]
    Xtr <- sweep(as.matrix(tr[,xv,drop=FALSE]),2,sgn,'*'); Xte <- sweep(as.matrix(te[,xv,drop=FALSE]),2,sgn,'*')
    colnames(Xtr) <- colnames(Xte) <- xv
    pr <- fit_idr(tr[[yv]], Xtr, Xte); c_idr <- crps(pr, te[[yv]])
    c_cl <- crps_emp(tr[[yv]], te[[yv]])
    lm1 <- lm(as.formula(paste(yv,'~',paste(xv,collapse='+'))), data=tr); c_ols <- crps_norm(te[[yv]], predict(lm1,te), summary(lm1)$sigma)
    out <- rbind(out, data.frame(year=yy, n=nrow(te), idr=mean(c_idr), clim=mean(c_cl), ols=mean(c_ols))) }
  w <- out$n/sum(out$n); list(by_year=out, idr=sum(w*out$idr), clim=sum(w*out$clim), ols=sum(w*out$ols), skill_idr=1-sum(w*out$idr)/sum(w*out$clim), skill_ols=1-sum(w*out$ols)/sum(w*out$clim))
}
perm_null <- function(D, yv, xv, sgn, nperm=299){ obs <- loyo(D,yv,xv,sgn)
  sk <- replicate(nperm, { Dp <- D; for (v in xv) Dp[[v]] <- ave(Dp[[v]], Dp$year, FUN=function(z) z[sample.int(length(z))]); loyo(Dp,yv,xv,sgn)$skill_idr })
  obs$null_mean <- mean(sk); obs$null_q95 <- unname(quantile(sk,.95)); obs$p <- (1+sum(sk>=obs$skill_idr))/(nperm+1); obs }
res <- list(n=nrow(P), years=range(P$year), firms=length(unique(P$id_rssd)))
t0 <- Sys.time()
res$A1 <- list(
  pct_drawdown = perm_null(P,'y_pct','dd_pct',-1),
  pct_pretax   = perm_null(P,'y_pct','pt_pct',+1),
  raw_drawdown = perm_null(P,'payout_rwa','drawdown',-1))
res$A1_runtime_s <- as.numeric(difftime(Sys.time(),t0,units='secs'))
saveRDS(res,"out/partial.rds"); cat("A1 done\n")
# full-sample IDR fit for figure: conditional quantiles of payout pct vs drawdown pct
fitA <- idr(y=P$y_pct, X=data.frame(dd=-P$dd_pct), progress=FALSE)
grid <- data.frame(dd=-seq(0.02,0.98,by=0.02)); pq <- qpred(predict(fitA, grid), quantiles=c(.1,.25,.5,.75,.9))
write.csv(data.frame(dd_pct=-grid$dd, pq), 'out/idr_A1_quantiles.csv', row.names=FALSE)
fitR <- idr(y=P$payout_rwa, X=data.frame(dd=-P$drawdown), progress=FALSE)
gR <- data.frame(dd=-seq(0,10,by=0.25)); pR <- qpred(predict(fitR, gR), quantiles=c(.1,.25,.5,.75,.9))
write.csv(data.frame(drawdown=-gR$dd, pR), 'out/idr_A1raw_quantiles.csv', row.names=FALSE)
write.csv(P[,c('year','drawdown','dd_pct','y_pct','payout_rwa')], 'out/q3_points_aggregate_safe.csv', row.names=FALSE)
# A2: SCB era 2021-2025
S <- P[P$year>=2021 & !is.na(P$scb),]; S$scb_pct <- ave(S$scb, S$year, FUN=pct)
res$A2 <- list(n=nrow(S),
  pct_scb = perm_null(S,'y_pct','scb_pct',-1), pct_drawdown=perm_null(S,'y_pct','dd_pct',-1), pct_pretax=perm_null(S,'y_pct','pt_pct',+1),
  pct_scb_dd = perm_null(S,'y_pct',c('scb_pct','dd_pct'),c(-1,-1)),
  raw_scb = perm_null(S,'payout_rwa','scb',-1), raw_drawdown=perm_null(S,'payout_rwa','drawdown',-1))
res$A2_cor <- list(spearman_scb_dd = cor(S$scb, S$drawdown, method='spearman'), share_at_floor = mean(S$scb<=2.5))
# A3: era stability and transfer
pre <- P[P$year<=2019,]; post <- P[P$year>=2021,]
fpre <- idr(y=pre$y_pct, X=data.frame(dd=-pre$dd_pct), progress=FALSE); fpost <- idr(y=post$y_pct, X=data.frame(dd=-post$dd_pct), progress=FALSE)
g <- data.frame(dd=-c(.1,.3,.5,.7,.9))
res$A3 <- list(pre_median=qpred(predict(fpre,g),quantiles=.5), post_median=qpred(predict(fpost,g),quantiles=.5), grid=-g$dd,
  transfer_pre_to_post = { pr <- predict(fpre, data.frame(dd=-post$dd_pct)); c1 <- mean(crps(pr, post$y_pct)); c0 <- mean(crps_emp(pre$y_pct, post$y_pct)); list(idr=c1, clim=c0, skill=1-c1/c0) },
  transfer_post_to_pre = { pr <- predict(fpost, data.frame(dd=-pre$dd_pct)); c1 <- mean(crps(pr, pre$y_pct)); c0 <- mean(crps_emp(post$y_pct, pre$y_pct)); list(idr=c1, clim=c0, skill=1-c1/c0) },
  y2020 = { tr <- P[P$year!=2020,]; te <- P[P$year==2020,]; pr <- predict(idr(y=tr$y_pct, X=data.frame(dd=-tr$dd_pct), progress=FALSE), data.frame(dd=-te$dd_pct)); list(n=nrow(te), idr=mean(crps(pr,te$y_pct)), clim=mean(crps_emp(tr$y_pct, te$y_pct))) })
# year-to-year rank stability of payouts (descriptive)
ky <- sapply(2014:2025, function(yy){ a <- P[P$year==yy-1,c('id_rssd','payout_rwa')]; b <- P[P$year==yy,c('id_rssd','payout_rwa')]; m <- merge(a,b,by='id_rssd'); if(nrow(m)<6) NA else cor(m$payout_rwa.x, m$payout_rwa.y, method='kendall') })
res$A3$kendall_payout_rank_yoy <- data.frame(year=2014:2025, tau=ky)
# timing: Rust-core IDR vs n (synthetic, labelled)
tm <- sapply(c(1000,3000,6000), function(n){ x <- runif(n); y <- x + rnorm(n); system.time(idr(y=y, X=data.frame(x=x), progress=FALSE))[['elapsed']] })
res$timing <- data.frame(n=c(1000,3000,6000), sec=tm)
tm2 <- sapply(c(300,1000), function(n){ X <- data.frame(a=runif(n), b=runif(n)); y <- X$a+X$b+rnorm(n); system.time(idr(y=y, X=X, progress=FALSE))[['elapsed']] })
res$timing_2d <- data.frame(n=c(300,1000), sec=tm2)
write_json(res, 'out/idr_results.json', auto_unbox=TRUE, digits=6, pretty=TRUE); cat('done\n'); writeLines(capture.output(sessionInfo()),'out/sessionInfo.txt')
