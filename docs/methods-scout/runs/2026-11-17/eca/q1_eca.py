import pandas as pd, numpy as np, json, time
from eca import eca, circ_null, binarize, rates, poisson_p
t0=time.time()
X=pd.read_csv('q1_weekly.csv',parse_dates=['date'],index_col='date')
def ev(X,q=0.9):
    E=pd.DataFrame(index=X.index)
    E['fails']=binarize(X.dl_fails,q); E['spread']=binarize(X.d_spread,q); E['dvp']=binarize(X.dl_dvp,q)
    E['levbuild']=binarize(X.d_lev,q); E['levunwind']=binarize(X.d_lev,1-q,upper=False)
    return E
E=ev(X)
pairs=[('fails','spread'),('spread','fails'),('fails','levbuild'),('fails','levunwind'),('spread','levbuild'),('spread','levunwind'),('dvp','fails'),('fails','dvp')]
taus=[0,2,4]; REPS=4999
def sub(E,a,b):
    S=E[[a,b]]
    if 'lev' in a or 'lev' in b: S=S[S.index<='2025-12-31']
    S=S.dropna(); return S[a].values,S[b].values
rows=[]
for a,b in pairs:
    A,B=sub(E,a,b)
    for tau in taus:
        o=circ_null(A,B,1,tau,REPS,seed=17+tau)
        rows.append(dict(A=a,B=b,tau=tau,n=len(A),**o))
R=pd.DataFrame(rows)
# Holm over 48 (precursor + trigger)
long=pd.concat([R.assign(kind='precursor',rate=R.rp,p=R.p_prec_circ,p_pois=R.p_prec_pois,null_med=R.null_rp_med,null95=R.null_rp_95),
                R.assign(kind='trigger',rate=R.rt,p=R.p_trig_circ,p_pois=R.p_trig_pois,null_med=R.null_rt_med,null95=R.null_rt_95)])
long=long[['A','B','tau','kind','n','NA','NB','rate','null_med','null95','p','p_pois']].reset_index(drop=True)
m=len(long); o=np.argsort(long.p.values); adj=np.empty(m); run=0
for k,i in enumerate(o): run=max(run,(m-k)*long.p.values[i]); adj[i]=min(1,run)
long['p_holm']=adj
long.to_csv('F1_results.csv',index=False)
print(long.sort_values('p').head(14).round(4).to_string())
print('Poisson p<0.05:',int((long.p_pois<0.05).sum()),' circ p<0.05:',int((long.p<0.05).sum()),' Holm<0.05:',int((long.p_holm<0.05).sum()))
print('time',round(time.time()-t0,1))
