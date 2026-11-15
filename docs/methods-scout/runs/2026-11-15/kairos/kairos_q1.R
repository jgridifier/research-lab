suppressMessages({library(kairos);library(tabula);library(dimensio);library(jsonlite)})
set.seed(20261115)
M <- read.csv("mix_monthly.csv", row.names=1, check.names=FALSE)
X <- round(as.matrix(M)/1000)  # $bn monthly-average volume per segment (counts-like table)
mon <- rownames(X); yr <- as.numeric(substr(mon,1,4)) + (as.numeric(substr(mon,6,7))-0.5)/12
out <- list(n_months=nrow(X), segments=colnames(X), first=mon[1], last=mon[length(mon)])
t0 <- Sys.time()
## A1: CA seriation, order recovery, Porcic significance
ser <- seriate_average(X, margin=c(1,2), axes=1)
ro <- order_rows(ser); co <- order_columns(ser)
rk <- integer(nrow(X)); rk[ro] <- seq_along(ro)
rho_time <- cor(rk, seq_len(nrow(X)), method="spearman")
out$A1 <- list(spearman_seriated_vs_calendar=rho_time, column_order=colnames(X)[co])
cax <- ca(X); eig <- get_eigenvalues(cax); out$A1$ca_inertia_pct <- head(eig[,2],4)
rc <- get_coordinates(cax, margin=1)[,1]; cc <- get_coordinates(cax, margin=2)[,1]
out$A1$row_axis1_spearman_time <- cor(rc, yr, method="spearman")
out$A1$col_axis1 <- setNames(as.list(round(cc,3)), colnames(X))
t1 <- Sys.time(); sig <- assess(ser, axes=1, n=1000, progress=FALSE); out$A1$assess_seconds <- as.numeric(Sys.time()-t1, units="secs")
out$A1$assess <- list(observed=sig$observed, expected=sig$expected, maximum=sig$maximum, coef=sig$coef,
  random_q05=unname(quantile(sig$random,0.05)), p_lower=mean(sig$random<=sig$observed))
Xs <- X[ro, co]
png("../fig/kairos_ford.png", width=1100, height=1400, res=130); plot_ford(Xs); dev.off()
png("../fig/kairos_eppm.png", width=1100, height=1400, res=130); seriograph(Xs); dev.off()
png("../fig/kairos_ford_calendar.png", width=1100, height=1400, res=130); plot_ford(X[, co]); dev.off()
## A2: event-date "mix clock" (Bellanger & Husi 2012)
ev <- event(X, dates=yr, rank=NULL, calendar=NULL, verbose=FALSE)
pe <- predict_event(ev, margin=1, calendar=NULL)
ev_hat <- pe[,1]
# rata die if calendar NULL -> convert back to years relative fit: regress back onto yr
cvt <- lm(yr ~ ev_hat); out$A2 <- list(event_cols=colnames(pe), r2_event_vs_time=summary(cvt)$r.squared)
eyr <- fitted(cvt)  # predicted mix date in calendar years (affine map of event estimate)
resid <- eyr - yr
write.csv(data.frame(month=mon, yr=yr, mix_date=eyr, mix_age_resid=resid, rk_seriated=rk, ca1=rc), "mixclock.csv", row.names=FALSE)
# walk-forward: train through 2022-12, predict 2023-01.. (honest OOS)
tr <- yr < 2023; ev2 <- event(X[tr,], dates=yr[tr], calendar=NULL, verbose=FALSE)
p2 <- predict_event(ev2, X[!tr,,drop=FALSE], margin=1, calendar=NULL)[,1]
p2tr <- predict_event(ev2, margin=1, calendar=NULL)[,1]; m2 <- lm(yr[tr] ~ p2tr)
p2y <- coef(m2)[1] + coef(m2)[2]*p2
out$A2$oos <- list(n_train=sum(tr), n_test=sum(!tr), mae_years=mean(abs(p2y-yr[!tr])),
  mae_naive_last_train=mean(abs(max(yr[tr])-yr[!tr])), cor_pred_actual=cor(p2y, yr[!tr]),
  pred_first_test=unname(p2y[1]), pred_last_test=unname(tail(p2y,1)))
write.csv(data.frame(month=mon[!tr], yr=yr[!tr], pred=p2y), "mixclock_oos.csv", row.names=FALSE)
## A3: stability across windows: segment order along CA axis 1
w1 <- yr < 2022.5; c1 <- setNames(get_coordinates(ca(X[w1,]),margin=2)[,1],colnames(X)); c2 <- setNames(get_coordinates(ca(X[!w1,]),margin=2)[,1],colnames(X))
s1 <- if (cor(get_coordinates(ca(X[w1,]),margin=1)[,1], yr[w1])<0) -1 else 1
s2 <- if (cor(get_coordinates(ca(X[!w1,]),margin=1)[,1], yr[!w1])<0) -1 else 1
out$A3 <- list(w1_order=names(sort(s1*c1)), w2_order=names(sort(s2*c2)), kendall=cor(s1*c1, s2*c2, method="kendall"),
  w1_ser_spearman=cor(order(order(get_coordinates(ca(X[w1,]),margin=1)[,1])), seq_len(sum(w1)), method="spearman"),
  w2_ser_spearman=cor(order(order(get_coordinates(ca(X[!w1,]),margin=1)[,1])), seq_len(sum(!w1)), method="spearman"))
# shuffled-row null for order recovery (should be ~0 by construction)
out$runtime_seconds <- as.numeric(Sys.time()-t0, units="secs")
t2 <- Sys.time(); for(i in 1:50) seriate_average(X, margin=c(1,2), axes=1); out$seriate_ms <- 1000*as.numeric(Sys.time()-t2, units="secs")/50
write_json(out, "kairos_results.json", auto_unbox=TRUE, pretty=TRUE, digits=6)
writeLines(capture.output(sessionInfo()), "sessionInfo.txt")
print(out)
