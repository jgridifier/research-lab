import pandas as pd, numpy as np, json
from eca import eca, circ_null, binarize, rates
X=pd.read_csv('q1_weekly.csv',parse_dates=['date'],index_col='date')
from q1_eca_helpers import ev, sub
out={}
E=ev(X)
# 1) Poisson calibration on circularly shifted pairs (independent by construction, clustering kept)
rng=np.random.default_rng(5)
cal={}
for (a,b) in [('fails','spread'),('fails','levunwind'),('dvp','fails')]:
    A,B=sub(E,a,b); n=len(A); fp=0; fpc=0; N=2000
    for s in rng.integers(8,n-8,N):
        o=eca(A,np.roll(B,s),1,0); fp+= (o['p_prec_pois']<0.05)
    cal[f'{a}<-{b}']=fp/N
out['poisson_FPR_shifted']=cal; print('Poisson FPR on shifted pairs',cal)
# lag-0 clustering of each event series: P(event at t+1 | event at t)
out['self_cluster']={c:float(np.nanmean(E[c].values[1:][E[c].values[:-1]==1])) for c in E.columns}; print(out['self_cluster'])
# 2) exact-lag decomposition, delT=0
dec=[]
for a,b in [('fails','levunwind'),('dvp','fails'),('fails','levbuild')]:
    A,B=sub(E,a,b)
    for tau in [0,1,2]:
        o=circ_null(A,B,0,tau,4999,seed=3+tau); dec.append(dict(A=a,B=b,tau=tau,rp=o['rp'],p=o['p_prec_circ'],null_med=o['null_rp_med']))
    # reverse: B at t+1 given A at t  (does A lead B?)
    o=circ_null(B,A,0,1,4999,seed=9); dec.append(dict(A=b,B=a,tau=1,rp=o['rp'],p=o['p_prec_circ'],null_med=o['null_rp_med']))
out['lag_decomp']=dec; print(pd.DataFrame(dec).round(4))
# 3) standard comparator: Pearson cross-correlation of continuous changes, circular-shift null
def xc(x,y,lag):  # corr(x_t, y_{t-lag})
    s=pd.concat([x,y.shift(lag)],axis=1).dropna(); return s.iloc[:,0].corr(s.iloc[:,1]),s
std=[]
Xl=X[X.index<='2025-12-31']
for nm,x,y in [('dl_fails~d_lev',Xl.dl_fails,Xl.d_lev),('dl_dvp~dl_fails',X.dl_dvp,X.dl_fails),('dl_fails~d_spread',X.dl_fails,X.d_spread)]:
    for lag in range(0,6):
        r,s=xc(x,y,lag); v=s.values; n=len(v); null=[]
        for sh in rng.integers(8,n-8,1999): null.append(np.corrcoef(v[:,0],np.roll(v[:,1],sh))[0,1])
        null=np.abs(null); p=(1+np.sum(null>=abs(r)))/2000
        std.append(dict(pair=nm,lag=lag,r=r,p=p))
S=pd.DataFrame(std); out['pearson']=std; print(S.round(4).to_string())
# Spearman too for the main pair at lag 0
s=pd.concat([Xl.dl_fails,Xl.d_lev],axis=1).dropna(); out['spearman_fails_lev_lag0']=float(s.corr('spearman').iloc[0,1])
# tail-only correlation: corr within lower decile of d_lev
q=s.d_lev.quantile(0.1); out['mean_dlfails_when_unwind']=float(s.dl_fails[s.d_lev<q].mean()); out['mean_dlfails_other']=float(s.dl_fails[s.d_lev>=q].mean())
qb=s.d_lev.quantile(0.9); out['mean_dlfails_when_build']=float(s.dl_fails[s.d_lev>qb].mean())
print({k:out[k] for k in ['spearman_fails_lev_lag0','mean_dlfails_when_unwind','mean_dlfails_other','mean_dlfails_when_build']})
# 4) stability: halves and thresholds for F1 findings (delT=1, tau=0)
stab=[]
for a,b,kind in [('fails','levunwind','precursor'),('fails','levunwind','trigger'),('dvp','fails','trigger')]:
    for lab,q,lo,hi in [('full q.90',0.9,None,None),('2018-05..2022-06',0.9,None,'2022-06-29'),('2022-07..end',0.9,'2022-07-06',None),('q.80',0.8,None,None),('q.95',0.95,None,None)]:
        Eq=ev(X,q); A,B=sub(Eq,a,b)
        idx=sub_idx=Eq[[a,b]].dropna() if not('lev' in a or 'lev' in b) else Eq[[a,b]][Eq.index<='2025-12-31'].dropna()
        m=np.ones(len(idx),bool)
        if lo: m&=idx.index>=lo
        if hi: m&=idx.index<=hi
        A,B=A[m],B[m]
        o=circ_null(A,B,1,0,1999,seed=11)
        r=o['rp'] if kind=='precursor' else o['rt']; n95=o['null_rp_95'] if kind=='precursor' else o['null_rt_95']; p=o['p_prec_circ'] if kind=='precursor' else o['p_trig_circ']
        stab.append(dict(pair=f'{a}<-{b}',kind=kind,window=lab,n=int(m.sum()),NA=o['NA'],NB=o['NB'],rate=r,null95=n95,p=p,passes=bool(r>n95)))
St=pd.DataFrame(stab); out['stability']=stab; print(St.round(4).to_string())
# 5) rolling 104-week precursor rate fails<-levunwind (delT=1,tau=0), events defined on full sample
A,B=sub(E,'fails','levunwind'); idx=E[['fails','levunwind']][E.index<='2025-12-31'].dropna().index
roll=[]
for st in range(0,len(A)-104+1,4):
    a,b=A[st:st+104],B[st:st+104]
    if a.sum()<3 or b.sum()<3: continue
    kp,kt,NA,NB,T=rates(a,b,1,0); 
    # null expectation for random placement: 1-(1-2/T)^NB
    roll.append(dict(end=str(idx[st+103].date()),rp=kp/NA,NA=NA,NB=NB,exp_random=1-(1-2/T)**NB))
out['rolling']=roll; R=pd.DataFrame(roll); print(R.iloc[::6].round(3).to_string())
# which weeks: list coincident fails & unwind weeks
ev_w=E[['fails','levunwind']][E.index<='2025-12-31'].dropna()
co=[str(d.date()) for i,d in enumerate(ev_w.index) if ev_w.fails.iloc[i]==1 and (ev_w.levunwind.iloc[i]==1 or (i>0 and ev_w.levunwind.iloc[i-1]==1))]
out['coincident_weeks']=co; print('coincident weeks',co)
json.dump(out,open('q1_more.json','w'),indent=1,default=float)
