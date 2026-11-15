suppressPackageStartupMessages({library(crqa); library(jsonlite)})
set.seed(20261114)
setwd('/workspace/ms-1114/q1')
q5 <- function(x) as.integer(cut(rank(x, ties.method='first'), breaks=quantile(rank(x,ties.method='first'), 0:5/5), include.lowest=TRUE))
drp <- function(a,b,ws) { r <- drpfromts(a, b, windowsize=ws, radius=0.001, delay=1, embed=1, rescale=0, normalize=0, mindiagline=2, minvertline=2, tw=0, whiteline=FALSE, recpt=FALSE, side='both', method='crqa', metric='euclidean', datatype='categorical'); r$profile }
# sign convention check: b = a shifted so that a leads b by 3
x <- sample(1:5, 400, TRUE); y <- c(sample(1:5,3,TRUE), head(x,-3))
pr <- drp(x,y,6); conv <- data.frame(lag=-6:6, rr=pr)
cat('convention: a leads b by 3 -> peak at index lag', conv$lag[which.max(conv$rr)], '\n')
res <- list(convention_peak_lag_when_ts1_leads_by_3 = conv$lag[which.max(conv$rr)])
W <- read.csv('weekly.csv'); W <- W[complete.cases(W[,c('l_fails_fin','spread_bp','dl_dvp_out','l_fails_otr')]),]
ws <- 13
pairs <- list(fin_vs_spread=c('l_fails_fin','spread_bp'), otr_vs_spread=c('l_fails_otr','spread_bp'), fin_vs_dvpgrowth=c('l_fails_fin','dl_dvp_out'), otr_vs_fin=c('l_fails_otr','l_fails_fin'))
null_drp <- function(a,b,ws,nperm=999,minshift=26){
  n <- length(b); obs <- drp(a,b,ws)
  shifts <- sample(minshift:(n-minshift), nperm, replace=TRUE)
  M <- t(sapply(shifts, function(s) drp(a, c(tail(b,-s), head(b,s)), ws)))
  list(obs=obs, p_lag = sapply(seq_along(obs), function(j) (1+sum(M[,j]>=obs[j]))/(nperm+1)),
       p_max = (1+sum(apply(M,1,max) >= max(obs)))/(nperm+1), null_mean=colMeans(M), null_q95=apply(M,2,quantile,0.95),
       asym_obs = mean(obs[(ws+2):(2*ws+1)]) - mean(obs[1:ws]),
       p_asym = (1+sum(abs(apply(M,1,function(m) mean(m[(ws+2):(2*ws+1)])-mean(m[1:ws]))) >= abs(mean(obs[(ws+2):(2*ws+1)]) - mean(obs[1:ws]))))/(nperm+1))
}
t0 <- Sys.time()
A1 <- lapply(pairs, function(p){ a<-q5(W[[p[1]]]); b<-q5(W[[p[2]]]); r<-null_drp(a,b,ws); 
  cc <- sapply(-ws:ws, function(k){ n<-length(a); if(k>=0) cor(W[[p[1]]][1:(n-k)], W[[p[2]]][(1+k):n], method='spearman') else cor(W[[p[1]]][(1-k):n], W[[p[2]]][1:(n+k)], method='spearman')})
  r$ccf_spearman <- cc; r$peak_lag <- (-ws:ws)[which.max(r$obs)]; r$ccf_peak_lag <- (-ws:ws)[which.max(abs(cc))]; r })
res$A1_runtime_s <- as.numeric(difftime(Sys.time(), t0, units='secs'))
res$A1 <- A1; res$n_weeks <- nrow(W); res$weeks <- c(W$date[1], tail(W$date,1))
# --- A2 windowed CRQA (52-week window, 4-week step), fails_fin vs spread, categorical quintiles
a <- q5(W$l_fails_fin); b <- q5(W$spread_bp)
t0 <- Sys.time()
wc <- wincrqa(a, b, windowstep=4, windowsize=52, delay=1, embed=1, radius=0.001, datatype='categorical', method='crqa')
res$A2_runtime_s <- as.numeric(difftime(Sys.time(), t0, units='secs'))
wc <- as.data.frame(wc)
wc$start <- W$date[seq(1, by=4, length.out=nrow(wc))]; wc$end <- W$date[pmin(nrow(W), seq(1,by=4,length.out=nrow(wc))+51)]
roll <- sapply(seq(1,by=4,length.out=nrow(wc)), function(i){ j<-i:min(nrow(W),i+51); cor(W$l_fails_fin[j], W$spread_bp[j], method='spearman')})
wc$roll_spearman <- roll
# window-level null: per-window circular shift of b within window, 199 shifts -> RR exceedance
wnull <- sapply(seq(1,by=4,length.out=nrow(wc)), function(i){ j<-i:min(nrow(W),i+51); aa<-a[j]; bb<-b[j]; n<-length(j)
   obs <- crqa(aa,bb,delay=1,embed=1,radius=0.001,datatype='categorical',method='crqa')$RR
   nl <- replicate(199, { s<-sample(8:(n-8),1); crqa(aa,c(tail(bb,-s),head(bb,s)),delay=1,embed=1,radius=0.001,datatype='categorical',method='crqa')$RR })
   c(obs=obs, q95=quantile(nl,0.95), p=(1+sum(nl>=obs))/200) })
wc$RR_chk <- wnull[1,]; wc$RR_null95 <- wnull[2,]; wc$RR_p <- wnull[3,]
write.csv(wc, 'out/wincrqa.csv', row.names=FALSE)
# full CRP for figure (continuous z, radius set so RR ~ 5%: fixed rule, not tuned on any outcome)
za <- as.numeric(scale(W$l_fails_fin)); zb <- as.numeric(scale(W$spread_bp))
cr <- crqa(a, b, delay=1, embed=1, radius=0.001, datatype='categorical', method='crqa')
RP <- as.matrix(cr$RP); idx <- which(RP!=0, arr.ind=TRUE)
write.csv(data.frame(i=idx[,1], j=idx[,2], state=a[idx[,1]]), 'out/crp_points.csv', row.names=FALSE)
res$full_crqa <- cr[c('RR','DET','NRLINE','maxL','L','ENTR','rENTR','LAM','TT')]
# top-quintile-only CRP (stress co-occurrence)
res$top_state_cooccur <- list(obs = sum(a==5 & b==5), expected = sum(a==5)*sum(b==5)/length(a))
# --- A3 monthly: Form PF prime-broker borrowings vs repo/fails
M <- read.csv('monthly.csv'); M$pb <- M$Secured_Prime.Broker; M$rr <- M$Secured_Reverse.Repo
lg <- function(x,k=3) c(rep(NA,k), diff(log(x), lag=k))
M$g_pb <- lg(M$pb); M$g_rr <- lg(M$rr); M$g_tri <- lg(M$tri_tvol); M$g_dvp <- lg(M$dvp_out); M$l_fin <- log(M$fails_fin_ust)
mp <- list(pb_vs_trivol=c('g_pb','g_tri'), pb_vs_dvpout=c('g_pb','g_dvp'), pb_vs_failsfin=c('g_pb','l_fin'), pb_vs_spread=c('g_pb','spread_bp'), revrepo_vs_dvpout=c('g_rr','g_dvp'))
A3 <- lapply(mp, function(p){ d <- M[complete.cases(M[,p]),]; a<-q5(d[[p[1]]]); b<-q5(d[[p[2]]]); r <- null_drp(a,b,6,nperm=999,minshift=12); r$n <- nrow(d); r$span <- c(d$period[1], tail(d$period,1)); r$peak_lag <- (-6:6)[which.max(r$obs)]
  cc <- sapply(-6:6, function(k){ x<-d[[p[1]]]; y<-d[[p[2]]]; n<-length(x); if(k>=0) cor(x[1:(n-k)], y[(1+k):n], method='spearman') else cor(x[(1-k):n], y[1:(n+k)], method='spearman')}); r$ccf_spearman <- cc; r})
res$A3 <- A3
# PB level path summary for page
res$pb_level <- list(first=c(M$period[1], M$pb[1]), last=c(tail(M$period,1), tail(M$pb,1)), max=c(M$period[which.max(M$pb)], max(M$pb)))
# --- timing scaling (synthetic categorical series; labelled synthetic)
tm <- sapply(c(500,1000,2000,4000), function(n){ x<-sample(1:5,n,TRUE); y<-sample(1:5,n,TRUE); system.time(crqa(x,y,delay=1,embed=1,radius=0.001,datatype='categorical',method='crqa'))[['elapsed']] })
res$timing <- data.frame(n=c(500,1000,2000,4000), sec=tm)
write_json(res, 'out/crqa_results.json', auto_unbox=TRUE, digits=6, pretty=TRUE)
cat('done\n')
