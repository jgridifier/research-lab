# Method 1: MARSS state-space decomposition of log-ratio (clr) dealer shares into
# market-driven (covariates in observation eq.), sticky (random-walk state) and transient parts.
suppressMessages({library(MARSS); library(jsonlite); library(parallel)})
set.seed(20261111)
M=read.csv('data/market_q.csv',row.names=1)
clr=function(X){L=log(as.matrix(X)); L-rowMeans(L)}
softmax=function(v){e=exp(v-max(v)); e/sum(e)}
mk=function(type,d){
  base=list(Z=matrix(1),U='zero',A='zero',R=matrix('r'),x0=matrix('x0'),tinitx=0)
  if(type=='M0') {base$B=matrix(1);base$Q=matrix(0)}
  if(type=='M1') {base$B=matrix(1);base$Q=matrix('q')}
  if(type=='M1n'){base$B=matrix(1);base$Q=matrix('q')}
  if(type=='M2') {base$B=matrix('b');base$Q=matrix('q')}
  if(type!='M1n'){base$D='unconstrained';base$d=d} else {base$D='zero'}
  base}
# Fitting: BFGS (quasi-Newton on the Kalman-filter likelihood) after a short EM warm start; EM alone crawls when R -> 0.
fit=function(y,type,d){
  w=try(MARSS(matrix(y,1),model=mk(type,d),silent=TRUE,control=list(maxit=100)),silent=TRUE)
  f=try(MARSS(matrix(y,1),model=mk(type,d),silent=TRUE,method='BFGS',inits=if(inherits(w,'try-error')) NULL else w),silent=TRUE)
  if(inherits(f,'try-error')||is.null(f$AICc)) { if(inherits(w,'try-error')) NULL else w } else f }
covs=list(A=c('vix','nasdaq_ret4','ta_ind_g1'),E4=c('vix','nasdaq_ret4','eq_rev_ind_g4'))
zs=function(D,mu=NULL,sd=NULL){ if(is.null(mu)){mu=colMeans(D);sd=apply(D,2,sd)}; list(z=t((t(D)-mu)/sd),mu=mu,sd=sd)}

analyse=function(pn,rows=NULL){
  X=read.csv(sprintf('data/panel_%s.csv',pn),row.names=1); if(!is.null(rows)) X=X[rows,,drop=FALSE]
  Y=clr(X); D=as.matrix(M[rownames(X),covs[[pn]]]); dz=t(zs(D)$z)
  res=list()
  for(f in colnames(Y)){
    y=Y[,f]-mean(Y[,f])
    fs=lapply(c(M0='M0',M1='M1',M1n='M1n',M2='M2'),function(t) fit(y,t,dz))
    aic=sapply(fs,function(o) if(is.null(o)) NA else o$AICc)
    f1=fs$M1; cf=coef(f1,type='vector')
    xs=as.numeric(f1$states); mkt=as.numeric(matrix(cf[grep('^D',names(cf))],1)%*%dz); rs=y-xs-mkt
    v=c(sticky=var(diff(xs)),market=var(diff(mkt)),transient=var(diff(rs)))
    b=if(!is.null(fs$M2)) coef(fs$M2,type='vector')['B.b'] else NA
    res[[f]]=list(AICc=as.list(round(aic,2)),best=names(which.min(aic)),
      dAICc_M1_vs_M0=round(unname(aic['M1']-aic['M0']),2), dAICc_M1_vs_M1n=round(unname(aic['M1']-aic['M1n']),2),
      M2_b=round(unname(b),3), M2_halflife_q=if(!is.na(b)&&b>0&&b<1) round(log(.5)/log(unname(b)),1) else NA,
      D=as.list(round(cf[grep('^D',names(cf))],4)), var_frac=as.list(round(v/sum(v),3)),
      net_change_clr=as.list(round(c(total=y[length(y)]-y[1],sticky=xs[length(xs)]-xs[1],market=mkt[length(mkt)]-mkt[1],transient=rs[length(rs)]-rs[1]),3)),
      series=list(q=rownames(X),y=round(y,4),sticky=round(xs,4),market=round(mkt,4)))
    res[[f]]$dxs=diff(xs)
  }
  res}

out=list()
# ---------- A1: Q1-directed decomposition on both proxy panels
for(pn in c('E4','A')){ r=analyse(pn); out[[paste0('A1_',pn)]]=lapply(r,function(z){z$dxs=NULL;z})
  # who-from-whom: correlation of sticky increments, circular-shift null
  S=sapply(r,function(z) z$dxs); C=cor(S); n=ncol(S); B=1000
  sh=replicate(B,{Ss=apply(S,2,function(s){k=sample(length(s),1);c(s[-(1:k)],s[1:k])}); cor(Ss)})
  pv=matrix(NA,n,n,dimnames=dimnames(C))
  for(i in 1:n) for(j in 1:n) if(i!=j) pv[i,j]=(1+sum(sh[i,j,]<=C[i,j]))/(B+1)   # one-sided: more negative than null
  pairs=data.frame()
  for(i in 1:(n-1)) for(j in (i+1):n) pairs=rbind(pairs,data.frame(a=colnames(S)[i],b=colnames(S)[j],corr=round(C[i,j],3),p_neg=round(pv[i,j],4)))
  pairs$q_BH=round(p.adjust(pairs$p_neg,'BH'),4); pairs=pairs[order(pairs$corr),]
  out[[paste0('A1_',pn,'_pairs')]]=pairs; out[[paste0('A1_',pn,'_clr_baseline_corr')]]=round(-1/(n-1),3)
}
# ---------- A2: stability across windows
qE=rownames(read.csv('data/panel_E4.csv',row.names=1)); qA=rownames(read.csv('data/panel_A.csv',row.names=1))
sumz=function(r) lapply(r,function(z) list(best=z$best,dAICc_M1_vs_M0=z$dAICc_M1_vs_M0,D=z$D,var_frac=z$var_frac,M2_b=z$M2_b))
out$A2=list(E4_early=sumz(analyse('E4',qE[qE<='2017Q4'])),E4_late=sumz(analyse('E4',qE[qE>='2018Q1'])),
            A_early=sumz(analyse('A',qA[qA<='2021Q2'])),A_late=sumz(analyse('A',qA[qA>='2021Q3'])))
# ---------- A3: honest expanding-window one-step OOS (nowcast: market covariates for t+1 are known at quarter end,
# ~40 days before the Y-9C is published). Covariates standardised with training-window stats only.
oos=function(pn,first){
  X=read.csv(sprintf('data/panel_%s.csv',pn),row.names=1); Y=clr(X); D=as.matrix(M[rownames(X),covs[[pn]]]); Tn=nrow(Y)
  origins=first:(Tn-1)
  rows=mclapply(origins,function(t){
    z=zs(D[1:t,,drop=FALSE]); dtr=t(z$z); dnext=(D[t+1,]-z$mu)/z$sd
    pr=list(RW=Y[t,],MEAN=colMeans(Y[1:t,,drop=FALSE]))
    pr$AR1=sapply(colnames(Y),function(f){y=Y[1:t,f]; m=mean(y); ph=coef(lm(I(y[-1]-m)~0+I(y[-t]-m)))[1]; unname(m+ph*(y[t]-m))})
    for(ty in c('M1','M0')){ pr[[paste0('MARSS_',ty)]]=sapply(colnames(Y),function(f){ fo=fit(Y[1:t,f],ty,dtr)
      if(is.null(fo)) return(Y[t,f]); cf=coef(fo,type='vector'); Dh=cf[grep('^D',names(cf))]
      xtt=if(ty=='M1') MARSSkfss(fo)$xtt[1,t] else cf['x0.x0']; unname(xtt+sum(Dh*dnext))})}
    act=Y[t+1,]; sact=as.numeric(X[t+1,]/sum(X[t+1,]))
    sapply(pr,function(p) c(clr_se=mean((p-act)^2), share_se=mean((softmax(p)-sact)^2)))
  },mc.cores=6)
  arr=simplify2array(rows)
  rm=sqrt(apply(arr,c(1,2),mean))
  list(origins=c(rownames(X)[first+1],rownames(X)[Tn]),n=length(origins),
       rmse_clr=as.list(round(rm['clr_se',],4)), rmse_share_pp=as.list(round(100*rm['share_se',],3)),
       frac_quarters_M1_beats_RW=round(mean(arr['clr_se','MARSS_M1',]<arr['clr_se','RW',]),3),
       frac_quarters_M0_beats_RW=round(mean(arr['clr_se','MARSS_M0',]<arr['clr_se','RW',]),3))
}
out$A3=list(E4=oos('E4',24),A=oos('A',22))
# ---------- A4: matched-persistence null
nullsim=function(pn,firms,nsim=40){
  X=read.csv(sprintf('data/panel_%s.csv',pn),row.names=1); Y=clr(X); D=as.matrix(M[rownames(X),covs[[pn]]]); dz=t(zs(D)$z); Tn=nrow(Y)
  lapply(setNames(firms,firms),function(f){
    y=Y[,f]-mean(Y[,f]); l=lm(y[-1]~0+y[-Tn]); ph=coef(l)[1]; phc=min(max(ph,0),0.95); s=sd(resid(l))
    sel=function(sim){ a=sapply(c('M0','M1','M2'),function(t){o=fit(sim-mean(sim),t,dz); if(is.null(o)) NA else o$AICc}); names(which.min(a))}
    ar=unlist(mclapply(1:nsim,function(i) sel(as.numeric(arima.sim(list(ar=phc),Tn,sd=s))),mc.cores=6,mc.set.seed=TRUE))
    rw=unlist(mclapply(1:nsim,function(i) sel(cumsum(rnorm(Tn,0,s))),mc.cores=6,mc.set.seed=TRUE))
    list(phi_hat=round(unname(ph),3),phi_used=round(unname(phc),3),
         AR_null_frac_M1_selected=round(mean(ar=='M1'),3),AR_null_frac_M2=round(mean(ar=='M2'),3),
         RW_power_frac_M1_selected=round(mean(rw=='M1'),3),nsim=nsim)})
}
out$A4=list(E4=nullsim('E4',c('JPM','GS','MS','BAC')),A=nullsim('A',c('JPM','GS','MS','BAC','C','WFC','UBS.CS','DB','BNP')))
out$meta=list(MARSS=as.character(packageVersion('MARSS')),R=R.version.string,run=format(Sys.time()))
write_json(out,'out/m1_results.json',auto_unbox=TRUE,digits=NA,pretty=TRUE)
cat('done\n')
