suppressMessages({library(partykit); library(rpart); library(jsonlite); library(strucchange)})
set.seed(20261110)
O <- "/workspace/scout/out/"; F <- "/workspace/scout/fig/"
res <- list()
M <- read.csv(paste0(O,"monthly_panel.csv")); M$date <- as.Date(M$date)
feats <- c("VIXCLS","T10Y2Y","NFCI","DGS2","dDGS2_12","ebp","dMORT_12","dGZ_3")
fm <- as.formula(paste("y_fwd6 ~", paste(feats, collapse="+")))
d <- M[complete.cases(M[,c("y_fwd6",feats)]),]
res$A1_sample <- list(n=nrow(d), start=as.character(min(d$date)), end=as.character(max(d$date)))
ctl <- ctree_control(alpha=0.05, minbucket=24, maxdepth=3)
t0 <- Sys.time(); ct <- ctree(fm, data=d, control=ctl); t_ct <- as.numeric(Sys.time()-t0, units="secs")
png(paste0(F,"m1_ctree_regimes.png"), width=1500, height=750, res=110)
plot(ct, terminal_panel=node_boxplot, gp=gpar(fontsize=9)); dev.off()
d$leaf <- predict(ct, type="node")
leaf_tab <- do.call(rbind, lapply(split(d, d$leaf), function(z) data.frame(
  leaf=z$leaf[1], n=nrow(z), mean_fwd6=mean(z$y_fwd6), sd_fwd6=sd(z$y_fwd6),
  p_widen_gt50bp=mean(z$y_fwd6>0.5), first=as.character(min(z$date)), last=as.character(max(z$date)))))
# rule text per leaf
rules <- partykit:::.list.rules.party(ct)
leaf_tab$rule <- rules[as.character(leaf_tab$leaf)]
res$A1_leaves <- leaf_tab; res$A1_fit_secs <- t_ct
write.csv(data.frame(date=d$date, leaf=d$leaf), paste0(O,"m1_leaf_timeline.csv"), row.names=FALSE)
# walk-forward
refits <- seq(as.Date("2004-01-31"), max(d$date), by="12 months")
pred <- data.frame()
for (i in seq_along(refits)) {
  r <- refits[i]; nxt <- if (i<length(refits)) refits[i+1] else max(d$date)+1
  tr <- d[d$date <= seq(r, by="-6 months", length.out=2)[2],]   # gap: target fully observed
  te <- d[d$date > r - 0 & d$date <= nxt & d$date > r,]
  te <- d[d$date >= r & d$date < nxt,]
  if (nrow(te)==0) next
  c1 <- ctree(fm, data=tr, control=ctl)
  rp <- rpart(fm, data=tr, control=rpart.control(cp=0.001, minbucket=24, xval=10))
  cpb <- rp$cptable[which.min(rp$cptable[,"xerror"]),"CP"]; rp <- prune(rp, cp=cpb)
  ol <- lm(fm, data=tr)
  pred <- rbind(pred, data.frame(date=te$date, y=te$y_fwd6, mean=mean(tr$y_fwd6),
     ctree=predict(c1,te), cart=predict(rp,te), ols=predict(ol,te), ctree_leaves=length(nodeids(c1,terminal=TRUE))))
}
oos <- function(p) c(R2_vs_hist_mean=1-sum((pred$y-p)^2)/sum((pred$y-pred$mean)^2), MAE=mean(abs(pred$y-p)), corr=cor(pred$y,p))
res$A1_walkforward <- list(n_oos=nrow(pred), period=c(as.character(min(pred$date)),as.character(max(pred$date))),
  ctree=oos(pred$ctree), cart=oos(pred$cart), ols=oos(pred$ols), hist_mean=oos(pred$mean),
  ctree_leaves_range=range(pred$ctree_leaves))
# by sub-period
pred$era <- ifelse(pred$date < as.Date("2010-01-01"),"2004-09", ifelse(pred$date<as.Date("2020-01-01"),"2010-19","2020-26"))
res$A1_by_era <- do.call(rbind, lapply(split(pred,pred$era), function(z) data.frame(era=z$era[1], n=nrow(z),
  ctree=1-sum((z$y-z$ctree)^2)/sum((z$y-z$mean)^2), cart=1-sum((z$y-z$cart)^2)/sum((z$y-z$mean)^2), ols=1-sum((z$y-z$ols)^2)/sum((z$y-z$mean)^2))))
write.csv(pred, paste0(O,"m1_walkforward.csv"), row.names=FALSE)

# A2 stability: split windows + block bootstrap of root split
root_of <- function(t) { n <- node_party(t); if (is.terminal(n)) return(c(var="(none)",thr=NA))
  s <- split_node(n); c(var=names(t$data)[varid_split(s)], thr=if(is.null(breaks_split(s))) NA else round(breaks_split(s),3)) }
win <- list(`1990-2007`=d[d$date<as.Date("2008-01-01"),], `2008-2026`=d[d$date>=as.Date("2008-01-01"),], full=d)
res$A2_windows <- do.call(rbind, lapply(names(win), function(k){ t <- ctree(fm, data=win[[k]], control=ctl)
  r <- root_of(t); data.frame(window=k, n=nrow(win[[k]]), root_var=r[["var"]], root_thr=r[["thr"]], leaves=length(nodeids(t,terminal=TRUE)))}))
B <- 300; L <- 24; nb <- ceiling(nrow(d)/L); roots <- character(B); thr <- numeric(B); lv <- integer(B)
t0 <- Sys.time()
for (b in 1:B) { st <- sample(1:(nrow(d)-L+1), nb, replace=TRUE); idx <- unlist(lapply(st, function(s) s:(s+L-1)))[1:nrow(d)]
  t <- ctree(fm, data=d[idx,], control=ctl); r <- root_of(t); roots[b] <- r[["var"]]; thr[b] <- as.numeric(r[["thr"]]); lv[b] <- length(nodeids(t,terminal=TRUE)) }
res$A2_boot_secs <- as.numeric(Sys.time()-t0, units="secs")
res$A2_boot_root_freq <- as.list(sort(table(roots), decreasing=TRUE)/B)
res$A2_boot_thr_by_var <- lapply(split(thr, roots), function(x) round(quantile(x, c(.1,.5,.9), na.rm=TRUE),3))
res$A2_boot_leaves <- as.list(table(lv)/B)

# A3 MOB: regime-dependent credit-spread sensitivity to VIX shocks
d3 <- M[complete.cases(M[,c("dGZ","dVIX","dDGS10","T10Y2Y","NFCI","DGS2")]),]
d3$time <- as.numeric(format(d3$date,"%Y")) + (as.numeric(format(d3$date,"%m"))-0.5)/12
t0 <- Sys.time()
mb <- lmtree(dGZ ~ dVIX + dDGS10 | T10Y2Y + NFCI + DGS2 + time, data=d3, minsize=36, alpha=0.01, bonferroni=TRUE)
res$A3_fit_secs <- as.numeric(Sys.time()-t0, units="secs")
png(paste0(F,"m1_mob_lmtree.png"), width=1500, height=750, res=110); plot(mb, gp=gpar(fontsize=9)); dev.off()
cf <- coef(mb); cf <- if (is.null(dim(cf))) t(as.matrix(cf)) else cf
r3 <- partykit:::.list.rules.party(mb)
nodes <- nodeids(mb, terminal=TRUE); d3$leaf <- predict(mb, type="node")
res$A3_leaves <- data.frame(leaf=nodes, n=as.integer(table(factor(d3$leaf,levels=nodes))), round(cf,4), rule=r3[as.character(nodes)], row.names=NULL)
pooled <- lm(dGZ ~ dVIX + dDGS10, data=d3)
res$A3_pooled <- round(coef(pooled),4)
res$A3_BIC <- c(pooled=BIC(pooled), mob=BIC(mb))
res$A3_n <- nrow(d3)
# sctest of root node
res$A3_root_tests <- round(sctest.modelparty(mb, node=1), 5)

# A4 county shocks
P <- read.csv(paste0(O,"county_panel.csv")); E <- read.csv(paste0(O,"county_edu.csv"))
w <- function(yr, col) { z <- P[P$year==yr, c("fips",col)]; names(z)[2] <- paste0(col,"_",yr); z }
G <- Reduce(function(a,b) merge(a,b,by="fips"), list(w(2007,"unemp_rate"), w(2010,"unemp_rate"), w(2019,"unemp_rate"), w(2020,"unemp_rate"),
   w(2001,"gdp_.M"), w(2007,"gdp_.M"), w(2014,"gdp_.M"), w(2019,"gdp_.M"), w(2007,"labor_force"), w(2019,"labor_force")))
meta <- unique(P[P$year==2023, c("fips","rucc","metro")])
G <- merge(G, meta, by="fips")
e00 <- E[E$period=="2000", c("fips","pct_bachelor_plus")]; names(e00)[2] <- "bach_2000"
e08 <- E[grepl("^2008", E$period), c("fips","pct_bachelor_plus")]; names(e08)[2] <- "bach_2008_12"
G <- merge(merge(G, e00, by="fips"), e08, by="fips")
G$gr_shock <- G$unemp_rate_2010 - G$unemp_rate_2007
G$cv_shock <- G$unemp_rate_2020 - G$unemp_rate_2019
G$gdp_g_01_07 <- 100*log(G$gdp_.M_2007/G$gdp_.M_2001)
G$gdp_g_14_19 <- 100*log(G$gdp_.M_2019/G$gdp_.M_2014)
G$log_lf07 <- log(G$labor_force_2007); G$log_lf19 <- log(G$labor_force_2019)
G$metro <- factor(G$metro); G$rucc <- as.numeric(G$rucc)
cvrun <- function(fm, dat, K=5) {
  dat <- dat[complete.cases(dat[,all.vars(fm)]),]; fold <- sample(rep(1:K, length.out=nrow(dat))); e <- matrix(NA,nrow(dat),4)
  colnames(e) <- c("mean","ctree","cart","ols")
  for (k in 1:K) { tr <- dat[fold!=k,]; te <- dat[fold==k,]
    c1 <- ctree(fm, data=tr, control=ctree_control(alpha=0.01, minbucket=50, maxdepth=4))
    rp <- rpart(fm, data=tr, control=rpart.control(cp=0.001, minbucket=50)); rp <- prune(rp, cp=rp$cptable[which.min(rp$cptable[,"xerror"]),"CP"])
    y <- te[[all.vars(fm)[1]]]
    e[fold==k,] <- cbind(mean(tr[[all.vars(fm)[1]]]), predict(c1,te), predict(rp,te), predict(lm(fm,tr),te)) - y }
  rmse <- sqrt(colMeans(e^2)); list(n=nrow(dat), rmse=round(rmse,4), R2=round(1-rmse^2/rmse[["mean"]]^2,4)) }
f_gr <- gr_shock ~ unemp_rate_2007 + gdp_g_01_07 + rucc + metro + bach_2000 + log_lf07
f_cv <- cv_shock ~ unemp_rate_2019 + gdp_g_14_19 + rucc + metro + bach_2008_12 + log_lf19
ctl4 <- ctree_control(alpha=0.01, minbucket=50, maxdepth=3)
for (nm in c("gr","cv")) {
  fm4 <- get(paste0("f_",nm)); dd <- G[complete.cases(G[,all.vars(fm4)]),]
  t4 <- ctree(fm4, data=dd, control=ctl4)
  png(paste0(F,"m1_county_",nm,".png"), width=1500, height=700, res=110); plot(t4, terminal_panel=node_boxplot, gp=gpar(fontsize=9)); dev.off()
  dd$leaf <- predict(t4, type="node"); rr <- partykit:::.list.rules.party(t4); yv <- all.vars(fm4)[1]
  lt <- do.call(rbind, lapply(split(dd, dd$leaf), function(z) data.frame(leaf=z$leaf[1], n=nrow(z), mean_shock=round(mean(z[[yv]]),2), sd=round(sd(z[[yv]]),2))))
  lt$rule <- rr[as.character(lt$leaf)]
  res[[paste0("A4_",nm,"_leaves")]] <- lt; res[[paste0("A4_",nm,"_cv")]] <- cvrun(fm4, G)
  res[[paste0("A4_",nm,"_root")]] <- root_of(t4)
}
# timing on county-sized data (x10 replicate to ~32k rows)
big <- G[rep(seq_len(nrow(G)), 10), ]; big <- big[complete.cases(big[,all.vars(f_gr)]),]
tm <- function(f) { t0 <- Sys.time(); f; as.numeric(Sys.time()-t0, units="secs") }
res$A4_timing <- list(rows=nrow(big),
  ctree=median(replicate(3, tm(ctree(f_gr, data=big, control=ctl4)))),
  rpart=median(replicate(3, tm(rpart(f_gr, data=big, control=rpart.control(cp=0.001, minbucket=50))))),
  lmtree=median(replicate(3, tm(lmtree(gr_shock ~ unemp_rate_2007 | gdp_g_01_07 + rucc + metro + bach_2000 + log_lf07, data=big, maxdepth=3)))))
res$versions <- list(R=R.version.string, partykit=as.character(packageVersion("partykit")), rpart=as.character(packageVersion("rpart")))
writeLines(toJSON(res, auto_unbox=TRUE, pretty=TRUE, digits=5), paste0(O,"m1_results.json"))
cat("done\n")
