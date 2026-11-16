suppressPackageStartupMessages({library(pim); library(jsonlite)})
P0 <- read.csv('q3_pim_panel.csv'); Q <- P0[complete.cases(P0[,c('payout_ni','drawdown','year')]),]
within_pairs <- function(yr){ do.call(rbind, lapply(split(seq_along(yr), yr), function(ix) if (length(ix)>1) t(combn(ix,2)) else NULL)) }
out <- do.call(rbind, lapply(c(0,.005,.01,.02,.03,.05), function(f){ Qt <- if (f==0) Q else Q[abs(Q$payout_ni)<=quantile(abs(Q$payout_ni),1-f),]
  m <- pim(payout_ni~drawdown, data=Qt, compare=within_pairs(Qt$year)); data.frame(trim=f, n=nrow(Qt), ols=coef(lm(payout_ni~drawdown+factor(year),Qt))[['drawdown']], pim_PI=plogis(coef(m)[[1]])) }))
print(out); write.csv(out,'pim_trim.csv',row.names=FALSE)
