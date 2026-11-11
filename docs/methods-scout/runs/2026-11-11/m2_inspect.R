# Method 2: InspectChangepoint (Wang & Samworth 2018, JRSS-B): sparse-projection change points in the
# multivariate log-ratio share panel. The projection vector says WHICH dealers moved at each break.
suppressMessages({library(InspectChangepoint); library(strucchange); library(jsonlite); library(MASS)})
set.seed(20261111)
M=read.csv('data/market_q.csv',row.names=1)
clr=function(X){L=log(as.matrix(X)); L-rowMeans(L)}
covs=list(A=c('vix','nasdaq_ret4','ta_ind_g1'),E4=c('vix','nasdaq_ret4','eq_rev_ind_g4'))
sc=function(Y){ s=apply(Y,2,function(y) mad(diff(y))/sqrt(2)); s[s<=0]=sd(diff(Y))/sqrt(2); list(z=t(t(Y)/s),s=s)}  # rows=time
thr=list()
TH=function(n,p){k=paste(n,p); if(is.null(thr[[k]])) thr[[k]]<<-suppressMessages(compute.threshold(n,p,nrep=200)); thr[[k]]}
run=function(Y){ z=sc(Y); x=t(z$z); r=suppressMessages(inspect(x,threshold=TH(ncol(x),nrow(x)))); cp=r$changepoints
  if(is.null(cp)||nrow(cp)==0||all(is.na(cp))) return(list(loc=integer(0),cusum=numeric(0)))
  cp=cp[order(cp[,'location']),,drop=FALSE]; list(loc=as.integer(cp[,'location']),cusum=round(cp[,'max.proj.cusum'],2))}
describe=function(X,Y,res){
  q=rownames(X); S=as.matrix(X/rowSums(X)); n=nrow(Y); b=c(0,res$loc,n); out=list()
  for(k in seq_along(res$loc)){ lo=b[k]+1; mid=res$loc[k]; hi=b[k+2]
    seg=t(sc(Y[lo:hi,,drop=FALSE])$z); lc=suppressMessages(locate.change(seg))
    dsh=colMeans(S[(mid+1):hi,,drop=FALSE])-colMeans(S[lo:mid,,drop=FALSE])
    v=lc$vector.proj; names(v)=colnames(Y); if(sum(v*dsh)<0) v=-v
    o=order(-abs(v))[1:min(4,length(v))]
    out[[k]]=list(break_after=q[mid],first_new_quarter=q[mid+1],cusum=res$cusum[k],segment=c(q[lo],q[hi]),
      top_projection=as.list(round(v[o],3)),share_change_pp=as.list(round(100*dsh,2)))}
  out}
resid_mkt=function(Y,pn,rows){ D=as.matrix(M[rows,covs[[pn]]]); apply(Y,2,function(y) resid(lm(y~D))+mean(y))}
out=list()
for(pn in c('A','E4')){
  X=read.csv(sprintf('data/panel_%s.csv',pn),row.names=1); Y=clr(X); n=nrow(Y); p=ncol(Y)
  r_raw=run(Y); Yr=resid_mkt(Y,pn,rownames(X)); r_adj=run(Yr)
  out[[paste0('B1_',pn)]]=list(n=n,p=p,threshold=round(TH(n,p),3),raw=describe(X,Y,r_raw),market_adjusted=describe(X,Yr,r_adj),
     n_cp_raw=length(r_raw$loc),n_cp_adj=length(r_adj$loc))
  # ---- B2 nulls
  E=apply(Yr,2,function(y){ l=lm(y[-1]~0+y[-n]); c(phi=unname(coef(l)),s=sd(resid(l)))})
  Rc=cor(apply(Yr,2,function(y){l=lm(y[-1]~0+y[-n]); resid(l)}))
  nsim=200
  sim_ar=function(phiv){ Z=mvrnorm(n,rep(0,p),Rc)%*%diag(E['s',]); Ys=matrix(0,n,p)
    Ys[1,]=Z[1,]; for(t in 2:n) Ys[t,]=phiv*Ys[t-1,]+Z[t,]; Ys}
  cnt=function(gen) sapply(1:nsim,function(i) length(run(gen())$loc))
  shuf=cnt(function() Yr[sample(n),])
  arc=cnt(function() sim_ar(pmin(pmax(E['phi',],0),0.95)))
  rwc=cnt(function() sim_ar(rep(1,p)))
  out[[paste0('B2_',pn)]]=list(observed_adj=length(r_adj$loc),observed_raw=length(r_raw$loc),nsim=nsim,
     phi_hat=as.list(round(E['phi',],3)),
     shuffle=list(mean=mean(shuf),p_ge_obs=mean(shuf>=length(r_adj$loc)),frac_zero=mean(shuf==0)),
     ar1_matched=list(mean=mean(arc),p_ge_obs=mean(arc>=length(r_adj$loc)),frac_zero=mean(arc==0)),
     random_walk=list(mean=mean(rwc),p_ge_obs=mean(rwc>=length(r_adj$loc)),frac_zero=mean(rwc==0)))
  # ---- B3 baseline (univariate strucchange::breakpoints, BIC) + real-time detection delay
  uni=lapply(colnames(Yr),function(f){ bp=breakpoints(Yr[,f]~1,h=max(3,floor(0.1*n))); b=bp$breakpoints
    if(all(is.na(b))) character(0) else rownames(X)[b]}); names(uni)=colnames(Yr)
  allu=unlist(uni)
  agree=sapply(r_adj$loc,function(l) sum(sapply(uni,function(u) any(abs(match(u,rownames(X))-l)<=1))))
  delay=sapply(r_adj$loc,function(l){ for(e in (l+2):n){ rr=run(Yr[1:e,]); if(any(abs(rr$loc-l)<=1)) return(e-l)}; NA})
  out[[paste0('B3_',pn)]]=list(univariate_breaks=uni,n_univariate_total=length(allu),
     inspect_breaks=rownames(X)[r_adj$loc],n_firms_with_univariate_break_within_1q=as.list(setNames(agree,rownames(X)[r_adj$loc])),
     realtime_delay_quarters=as.list(setNames(delay,rownames(X)[r_adj$loc])))
}

# ---------- B4 (Q1 main test): change in DRIFT of market-adjusted log-ratio shares (Inspect on first differences).
# A sustained migration regime = a change in the mean quarterly log-ratio change. Nulls on differences:
# iid shuffle, block shuffle (block=4, keeps short autocorrelation incl. the 4Q-sum overlap), AR(1)-matched Gaussian.
describe_d=function(X,dY,res){ q=rownames(X)[-1]; n=nrow(dY); b=c(0,res$loc,n); out=list()
  for(k in seq_along(res$loc)){ lo=b[k]+1; mid=res$loc[k]; hi=b[k+2]
    seg=t(sc(dY[lo:hi,,drop=FALSE])$z); lc=suppressMessages(locate.change(seg))
    dd=colMeans(dY[(mid+1):hi,,drop=FALSE])-colMeans(dY[lo:mid,,drop=FALSE])
    v=lc$vector.proj; names(v)=colnames(dY); if(sum(v*dd)<0) v=-v; o=order(-abs(v))[1:min(4,length(v))]
    out[[k]]=list(break_after=q[mid],cusum=res$cusum[k],segment=c(q[lo],q[hi]),top_projection=as.list(round(v[o],3)),
      drift_change_clr_per_q=as.list(round(dd,4)),drift_before=as.list(round(colMeans(dY[lo:mid,,drop=FALSE]),4)),drift_after=as.list(round(colMeans(dY[(mid+1):hi,,drop=FALSE]),4)))}
  out}
for(pn in c('A','E4')){
  X=read.csv(sprintf('data/panel_%s.csv',pn),row.names=1); Y=clr(X); Yr=resid_mkt(Y,pn,rownames(X)); dY=diff(Yr); n=nrow(dY); p=ncol(dY)
  r=run(dY); nsim=300
  bs=function(){ nb=ceiling(n/4); st=sample(1:(n-3),nb,replace=TRUE); idx=as.vector(sapply(st,function(s) s:(s+3)))[1:n]; dY[idx,]}
  ph=apply(dY,2,function(y) coef(lm(y[-1]~0+y[-n]))[1]); Rc=cor(dY); sdv=apply(dY,2,sd)
  ar=function(){ Z=mvrnorm(n,rep(0,p),Rc)%*%diag(sdv*sqrt(1-pmin(ph^2,0.9))); Ys=matrix(0,n,p); Ys[1,]=Z[1,]
    for(t in 2:n) Ys[t,]=ph*Ys[t-1,]+Z[t,]; Ys}
  cnt=function(gen) sapply(1:nsim,function(i) length(run(gen())$loc))
  c1=cnt(function() dY[sample(n),]); c2=cnt(bs); c3=cnt(ar)
  k=length(r$loc)
  out[[paste0('B4_',pn)]]=list(n=n,p=p,observed=k,breaks=describe_d(X,dY,r),phi_diff=as.list(round(ph,3)),nsim=nsim,
    null_shuffle=list(mean=mean(c1),p_ge_obs=mean(c1>=k)),null_block4=list(mean=mean(c2),p_ge_obs=mean(c2>=k)),null_ar1=list(mean=mean(c3),p_ge_obs=mean(c3>=k)))
}

t0=Sys.time(); X=read.csv('data/panel_A.csv',row.names=1); for(i in 1:20) run(clr(X)); out$timing_ms_per_call_A=round(1000*as.numeric(Sys.time()-t0,units='secs')/20,1)
out$meta=list(InspectChangepoint=as.character(packageVersion('InspectChangepoint')),strucchange=as.character(packageVersion('strucchange')),run=format(Sys.time()))
write_json(out,'out/m2_results.json',auto_unbox=TRUE,digits=NA,pretty=TRUE); cat('done\n')
