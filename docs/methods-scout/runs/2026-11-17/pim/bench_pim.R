# 2026-11-17: PIM scores for the held-out-year benchmark (PREREG.md section A). Writes local predictions only.
suppressPackageStartupMessages({library(pim)})
B <- read.csv('bench_panel.csv')
within_pairs <- function(yr){ do.call(rbind, lapply(split(seq_along(yr), yr), function(ix) if (length(ix)>1) t(combn(ix,2)) else NULL)) }
out <- list()
for (y in c('payout_rwa','payout_ni')) for (spec in c('static','dyn')) {
  xs <- c('drawdown','income_pretax_net_rate'); if (spec=='dyn') xs <- c(paste0(y,'_prev'), xs)
  for (Tt in 2016:2025) {
    tr <- B[B$year < Tt & complete.cases(B[,c(y,xs)]),]; te <- B[B$year == Tt & complete.cases(B[,c(y,xs)]),]
    if (nrow(te) < 2) next
    m <- pim(as.formula(paste(y,'~',paste(xs,collapse='+'))), data=tr, compare=within_pairs(tr$year), link='logit', model='difference')
    sc <- as.matrix(te[,xs]) %*% coef(m)
    out[[length(out)+1]] <- data.frame(model=paste0('PIM_',spec), outcome=y, year=Tt, id_rssd=te$id_rssd, y=te[[y]], score=as.numeric(sc))
  } }
write.csv(do.call(rbind,out), 'pred_pim.csv', row.names=FALSE)
cat('done\n')
