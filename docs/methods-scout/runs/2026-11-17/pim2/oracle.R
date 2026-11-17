# 2026-11-17 pim oracle for PREREG.md E1 (parity): pim 2.0.4, tight nleqslv tolerance. Same fits as runs/2026-11-16/pim/pim_q3.R.
suppressPackageStartupMessages({library(pim); library(jsonlite)}); set.seed(20261117)
P0 <- read.csv('q3_pim_panel.csv'); P0$row0 <- seq_len(nrow(P0)) - 1
within_pairs <- function(yr){ do.call(rbind, lapply(split(seq_along(yr), yr), function(ix) if (length(ix)>1) t(combn(ix,2)) else NULL)) }
ctl <- list(xtol=1e-13, ftol=1e-13, maxit=500)
fit1 <- function(D, y, xs){ m <- pim(as.formula(paste(y,'~',paste(xs,collapse='+'))), data=D, compare=within_pairs(D$year), link='logit', model='difference', control=ctl)
  list(coef=unname(coef(m)), se=unname(sqrt(diag(vcov(m))))) }
prep <- function(D,y,xs){ D <- D[complete.cases(D[,c(y,xs,'year','id_rssd')]),]; D[D$year %in% names(which(table(D$year)>1)),] }
E1 <- P0[P0$year<=2019,]; E2 <- P0[P0$year>=2021,]; G <- P0[P0$year>=2014 & P0$year<=2019,]
S <- list(list('B1 all years',P0,'payout_rwa','drawdown'), list('B1 all years',P0,'payout_rwa','income_pretax_net_rate'),
 list('B1 all years joint',P0,'payout_rwa',c('drawdown','income_pretax_net_rate')), list('B1 2013-2019',E1,'payout_rwa','drawdown'),
 list('B1 2021-2025',E2,'payout_rwa','drawdown'), list('B1 SCB era',E2,'payout_rwa','scb'), list('B1 SCB era joint',E2,'payout_rwa',c('scb','drawdown')),
 list('B1 timing: next-year payouts',P0[P0$year<=2024,],'payout_rwa_next','drawdown'), list('B1 payout/NI (unstable ratio)',P0,'payout_ni','drawdown'),
 list('B2 SA drawdown + SA-A gap',G,'payout_rwa',c('drawdown','gap_dd')), list('B2 Adverse drawdown only',G,'payout_rwa','dd_A'),
 list('B2 SA drawdown only (same rows)',G[!is.na(G$dd_A),],'payout_rwa','drawdown'), list('B2 gap, next-year payouts',G,'payout_rwa_next',c('drawdown','gap_dd')),
 list('B2 pre-tax SA + A-SA gap',G,'payout_rwa',c('income_pretax_net_rate','gap_pt')))
for (nm in c('div_rwa','bb_rwa','div_share')) { S[[length(S)+1]] <- list('B3 2013-2019',E1,nm,'drawdown'); S[[length(S)+1]] <- list('B3 2021-2025',E2,nm,'drawdown'); S[[length(S)+1]] <- list('B3 SCB era',E2,nm,'scb') }
S[[length(S)+1]] <- list('B3 timing: next-year div share',P0[P0$year<=2024,],'div_share_next','drawdown')
out <- lapply(S, function(s){ D <- prep(s[[2]],s[[3]],s[[4]]); t0 <- Sys.time(); F <- fit1(D,s[[3]],s[[4]])
  list(label=s[[1]], y=s[[3]], xs=s[[4]], rows=D$row0, beta=F$coef, se=F$se, sec=as.numeric(difftime(Sys.time(),t0,units='secs'))) })
# 50 within-year permutations of the B1 joint model
D <- prep(P0,'payout_rwa',c('drawdown','income_pretax_net_rate')); perms <- list(); t0 <- Sys.time()
for (r in 1:50) { Dp <- D; for (ix in split(seq_len(nrow(D)), D$year)) Dp$payout_rwa[ix] <- D$payout_rwa[ix][sample.int(length(ix))]
  F <- fit1(Dp,'payout_rwa',c('drawdown','income_pretax_net_rate')); perms[[r]] <- list(y=Dp$payout_rwa, beta=F$coef)
  if (r==20) t20 <- as.numeric(difftime(Sys.time(),t0,units='secs')) }
write_json(list(fits=out, perm_rows=D$row0, perms=perms, pim_sec_20perm=t20, pim_version=as.character(packageVersion('pim'))), 'oracle.json', digits=NA, auto_unbox=FALSE)
cat('fits', length(out), 'coefs', sum(sapply(out, function(o) length(o$beta))), 't20', t20, '\n')
