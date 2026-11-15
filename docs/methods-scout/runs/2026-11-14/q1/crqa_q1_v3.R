suppressPackageStartupMessages({library(crqa); library(jsonlite); library(parallel)})
RNGkind("L'Ecuyer-CMRG"); set.seed(20261114)
cl <- makeCluster(8); invisible(clusterEvalQ(cl, suppressPackageStartupMessages(library(crqa)))); clusterSetRNGStream(cl, 20261114)
pl <- function(X, FUN) parLapply(cl, X, FUN)
setwd('/workspace/ms-1114/q1')
q5 <- function(x) as.integer(cut(rank(x, ties.method='first'), breaks=quantile(rank(x,ties.method='first'), 0:5/5), include.lowest=TRUE))
drp <- function(a,b,ws) drpfromts(a, b, windowsize=ws, radius=0.001, datatype='categorical', method='crqa')$profile
null_drp <- function(a,b,ws,nperm=999,minshift=26){
  n <- length(b); obs <- drp(a,b,ws); L <- 2*ws+1
  shifts <- sample(minshift:(n-minshift), nperm, replace=TRUE)
  clusterExport(cl, c('drp','a','b','ws'), envir=environment()); M <- do.call(rbind, pl(shifts, function(s) drp(a, c(tail(b,-s), head(b,s)), ws)))
  lead1 <- function(m) mean(m[(ws+2):L]) - mean(m[1:ws])
  list(obs=obs, p_lag=sapply(1:L, function(j) (1+sum(M[,j]>=obs[j]))/(nperm+1)),
       p_max=(1+sum(apply(M,1,max)>=max(obs)))/(nperm+1), null_mean=colMeans(M), null_q95=apply(M,2,quantile,0.95),
       peak_lag=(-ws:ws)[which.max(obs)], asym=lead1(obs), p_asym=(1+sum(abs(apply(M,1,lead1))>=abs(lead1(obs))))/(nperm+1))
}
sccf <- function(x,y,ws) sapply(-ws:ws, function(k){ n<-length(x); if(k>=0) cor(x[1:(n-k)], y[(1+k):n], method='spearman') else cor(x[(1-k):n], y[1:(n+k)], method='spearman')})
res <- list()
W <- read.csv('weekly.csv'); W <- W[complete.cases(W[,c('l_fails_fin','spread_bp','dl_dvp_out','l_fails_otr')]),]
pairs <- list(fin_vs_spread=c('l_fails_fin','spread_bp'), otr_vs_spread=c('l_fails_otr','spread_bp'), fin_vs_dvpgrowth=c('l_fails_fin','dl_dvp_out'), otr_vs_fin=c('l_fails_otr','l_fails_fin'))
t0 <- Sys.time()
res$A1 <- lapply(pairs, function(p){ a<-q5(W[[p[1]]]); b<-q5(W[[p[2]]])
  list(co=null_drp(a,b,13), anti=null_drp(a,6L-b,13), ccf=sccf(W[[p[1]]],W[[p[2]]],13)) })
res$A1_runtime_s <- as.numeric(difftime(Sys.time(), t0, units='secs')); res$n_weeks <- nrow(W); res$weeks <- c(W$date[1], tail(W$date,1))
# single-call timing of one DRP and one full CRQA on weekly data
a <- q5(W$l_fails_fin); b <- q5(W$spread_bp)
res$time_one_drp_s <- system.time(drp(a,b,13))[['elapsed']]
res$time_one_crqa_s <- system.time(cr <- crqa(a,6L-b,delay=1,embed=1,radius=0.001,datatype='categorical',method='crqa'))[['elapsed']]
res$full_crqa_anti <- cr[c('RR','DET','NRLINE','maxL','L','ENTR','rENTR','LAM','TT')]
crc <- crqa(a,b,delay=1,embed=1,radius=0.001,datatype='categorical',method='crqa'); res$full_crqa_co <- crc[c('RR','DET','L','LAM','TT')]
RP <- as.matrix(cr$RP); idx <- which(RP!=0, arr.ind=TRUE)
write.csv(data.frame(i=idx[,1], j=idx[,2], sa=a[idx[,1]]), 'out/crp_anti_points.csv', row.names=FALSE)
# A2 (v3 fix): windowed CRQA, LOCAL quintiles in each 52-week window, 4-week step.
# v1/v2 used full-matrix RR, which for categorical data depends only on the marginal counts and is therefore
# identical under any circular shift (degenerate null). v3 uses order-dependent statistics instead:
# rr0 = same-week recurrence (main diagonal), DET = share of recurrent points on diagonal lines >= 2.
res$rr_shift_invariance_check <- { a<-q5(W$l_fails_fin); b<-q5(W$spread_bp); c(crqa(a,b,delay=1,embed=1,radius=0.001,datatype='categorical',method='crqa')$RR, crqa(a,c(tail(b,-50),head(b,50)),delay=1,embed=1,radius=0.001,datatype='categorical',method='crqa')$RR) }
starts <- seq(1, nrow(W)-51, by=4)
clusterExport(cl, c('W','q5'), envir=environment())
win <- do.call(rbind, pl(starts, function(i){ j <- i:(i+51)
  one <- function(x,y){ aa<-q5(x[j]); bb<-q5(y[j])
    st <- function(b2){ o<-crqa(aa,b2,delay=1,embed=1,radius=0.001,datatype='categorical',method='crqa'); c(mean(aa==b2), o$DET) }
    obs <- st(bb); nl <- t(replicate(199,{s<-sample(8:44,1); st(c(tail(bb,-s),head(bb,s)))}))
    c(obs[1], obs[2], (1+sum(nl[,1]>=obs[1]))/200, mean(nl[,1]), (1+sum(nl[,2]>=obs[2]))/200, mean(nl[,2])) }
  r1 <- one(W$l_fails_fin, -W$spread_bp); r2 <- one(W$l_fails_fin, W$dl_dvp_out)
  data.frame(start=W$date[i], end=W$date[i+51], rr0_anti=r1[1], p_rr0_anti=r1[3], null_rr0_anti=r1[4], DET_anti=r1[2], p_DET_anti=r1[5], null_DET_anti=r1[6],
             rr0_dvp=r2[1], p_rr0_dvp=r2[3], null_rr0_dvp=r2[4], DET_dvp=r2[2], p_DET_dvp=r2[5], null_DET_dvp=r2[6],
             rho_spread=cor(W$l_fails_fin[j], W$spread_bp[j], method='spearman'), rho_dvp=cor(W$l_fails_fin[j], W$dl_dvp_out[j], method='spearman')) }))
write.csv(win, 'out/wincrqa_v3.csv', row.names=FALSE)
# A3 monthly
M <- read.csv('monthly.csv'); M$pb <- M$Secured_Prime.Broker; M$rr <- M$Secured_Reverse.Repo
lg <- function(x,k=3) c(rep(NA,k), diff(log(x), lag=k))
M$g_pb <- lg(M$pb); M$g_rr <- lg(M$rr); M$g_tri <- lg(M$tri_tvol); M$g_dvp <- lg(M$dvp_out); M$l_fin <- log(M$fails_fin_ust)
mp <- list(pb_vs_trivol=c('g_pb','g_tri'), pb_vs_dvpout=c('g_pb','g_dvp'), pb_vs_failsfin=c('g_pb','l_fin'), pb_vs_spread=c('g_pb','spread_bp'), revrepo_vs_dvpout=c('g_rr','g_dvp'), revrepo_vs_failsfin=c('g_rr','l_fin'))
res$A3 <- lapply(mp, function(p){ d <- M[complete.cases(M[,p]),]; a<-q5(d[[p[1]]]); b<-q5(d[[p[2]]])
  list(n=nrow(d), span=c(d$period[1], tail(d$period,1)), co=null_drp(a,b,6,minshift=12), anti=null_drp(a,6L-b,6,minshift=12), ccf=sccf(d[[p[1]]],d[[p[2]]],6)) })
res$pb_level <- list(first=c(M$period[1], M$pb[1]), last=c(tail(M$period,1), tail(M$pb,1)), rr_first=M$rr[1], rr_last=tail(M$rr,1))
tm <- sapply(c(500,1000,2000,4000), function(n){ x<-sample(1:5,n,TRUE); y<-sample(1:5,n,TRUE); system.time(crqa(x,y,delay=1,embed=1,radius=0.001,datatype='categorical',method='crqa'))[['elapsed']] })
res$timing <- data.frame(n=c(500,1000,2000,4000), sec=tm)
write_json(res, 'out/crqa_results_v3.json', auto_unbox=TRUE, digits=6, pretty=TRUE); stopCluster(cl); cat('done\n'); writeLines(capture.output(sessionInfo()), 'out/sessionInfo_v3.txt')
