# 2026-11-17 kairos refresh (#60), PREREG.md section B, tests T1 and T2 (event-model part) on O1-O6.
suppressMessages({library(kairos);library(tabula);library(dimensio);library(jsonlite)})
set.seed(20261117)
res <- list()
for (f in sort(Sys.glob('O*_*.csv'))) {
  nm <- sub('.csv','',f); M <- read.csv(f, row.names=1, check.names=FALSE); M <- M[complete.cases(M),]
  sc <- 10000/median(rowSums(M)); X <- round(as.matrix(M)*sc); X <- X[, colSums(X)>0]
  mon <- rownames(X); yr <- as.numeric(substr(mon,1,4)) + (as.numeric(substr(mon,6,7))-0.5)/12
  ser <- seriate_average(X, margin=c(1,2), axes=1); ro <- order_rows(ser); rk <- integer(nrow(X)); rk[ro] <- seq_along(ro)
  sp <- cor(rk, seq_len(nrow(X)), method='spearman')
  sig <- assess(ser, axes=1, n=1000, progress=FALSE)
  # full-sample clock (as on 11-15)
  ev <- event(X, dates=yr, calendar=NULL, verbose=FALSE); pe <- predict_event(ev, margin=1, calendar=NULL)[,1]
  mixdate <- fitted(lm(yr ~ pe))
  # walk-forward: first 60% of months train
  ntr <- floor(0.6*nrow(X)); tr <- seq_len(nrow(X)) <= ntr
  ev2 <- event(X[tr,], dates=yr[tr], calendar=NULL, verbose=FALSE)
  p2 <- predict_event(ev2, X[!tr,,drop=FALSE], margin=1, calendar=NULL)[,1]
  p2tr <- predict_event(ev2, margin=1, calendar=NULL)[,1]; m2 <- lm(yr[tr] ~ p2tr); p2y <- coef(m2)[1]+coef(m2)[2]*p2
  write.csv(data.frame(month=mon, yr=yr, mix_date=mixdate, train=tr, wf_pred=ifelse(tr, NA, c(rep(NA,ntr), p2y))), paste0('clock_',nm,'.csv'), row.names=FALSE)
  res[[nm]] <- list(n_months=nrow(X), first=mon[1], last=mon[length(mon)], parts=colnames(X), spearman_seriated_vs_calendar=sp,
    porcic_observed=sig$observed, porcic_random_q05=unname(quantile(sig$random,.05)), porcic_p=(1+sum(sig$random<=sig$observed))/(1+length(sig$random)),
    ca_axis1_pct=unname(get_eigenvalues(ca(X))[1,2]), n_train=ntr, n_test=sum(!tr), train_end=mon[ntr],
    wf_mae_clock=mean(abs(p2y-yr[!tr])), wf_mae_naive=mean(abs(max(yr[tr])-yr[!tr])))
  cat(nm, 'done\n')
}
write_json(res, 'kairos_open_results.json', auto_unbox=TRUE, pretty=TRUE, digits=6)
writeLines(capture.output(sessionInfo()), 'sessionInfo.txt')
