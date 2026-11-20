import numpy as np, pandas as pd, json, sys, time
sys.path.insert(0,'.'); from lk_port import lkif, var1_t
from scipy.stats import norm, t as tdist
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import grangercausalitytests
import warnings; warnings.filterwarnings('ignore')
rng=np.random.default_rng(20261120)
X=pd.read_csv('q1_weekly_lkif.csv',parse_dates=['date']).set_index('date')
V=['dl_fails','d_spread','dl_dvp','dl_tri','d_lev','d_vix']
def holm(p):
    p=np.asarray(p); o=np.argsort(p); m=len(p); adj=np.empty(m); run=0
    for k,i in enumerate(o): run=max(run,(m-k)*p[i]); adj[i]=min(1,run)
    return adj
def surrogate(Z,nshift,rng,minshift=26):
    n,d=Z.shape; T0=lkif(Z)['T']; cnt=np.zeros((d,d))
    for j in range(d):
        for s in range(nshift):
            k=rng.integers(minshift,n-minshift); Zs=Z.copy(); Zs[:,j]=np.roll(Z[:,j],k)
            cnt[:,j]+= np.abs(lkif(Zs)['T'][:,j])>=np.abs(T0[:,j])
    return (cnt+1)/(nshift+1)
def analyse(D,V,nshift=4999,label=''):
    Z=((D[V]-D[V].mean())/D[V].std()).values
    R=lkif(Z); ps=surrogate(Z,nshift,rng); tv=var1_t(Z); pt=2*tdist.sf(np.abs(tv),len(Z)-len(V)-2)
    m=VAR(Z); p_bic=m.select_order(8).bic; p_bic=max(int(p_bic),1); fit=m.fit(p_bic)
    rows=[]
    for i in range(len(V)):
        for j in range(len(V)):
            if i==j: continue
            gc=fit.test_causality(i,[j],kind='f').pvalue
            pw=grangercausalitytests(np.column_stack([Z[:,i],Z[:,j]]),[1])[1][0]['ssr_ftest'][1]
            rows.append(dict(src=V[j],tgt=V[i],T=R['T'][i,j],tau=R['tau'][i,j],p_asym=R['p'][i,j],p_surr=ps[i,j],z_lk=R['T'][i,j]/R['SE'][i,j],t_var1=tv[i,j],p_var1=pt[i,j],p_granger_bic=gc,p_pairwise=pw,corr=np.corrcoef(Z[:-1,i],Z[:-1,j])[0,1],a=R['A'][i,j]))
    df=pd.DataFrame(rows); df['holm_surr']=holm(df.p_surr); df['holm_asym']=holm(df.p_asym); df['holm_var1']=holm(df.p_var1); df['holm_gbic']=holm(df.p_granger_bic); df['holm_pw']=holm(df.p_pairwise)
    selfdh=None
    return df,p_bic,len(Z)
t0=time.time()
full=X[V].dropna()
L1,pb,n=analyse(full,V)
L1.to_csv('L1_edges.csv',index=False)
print('L1 n',n,'VAR BIC lag',pb, 'time',round(time.time()-t0,1))
print(L1.sort_values('p_surr').head(12)[['src','tgt','T','tau','p_asym','p_surr','holm_surr','p_var1','p_granger_bic','p_pairwise','holm_gbic','corr']].round(4).to_string())
# derivation check: z_lk vs OLS t (standardized -> zero means)
print('max |z_lk - t_var1|',float(np.max(np.abs(L1.z_lk-L1.t_var1))))
json.dump(dict(n=n,var_bic_lag=pb,max_abs_z_minus_t=float(np.max(np.abs(L1.z_lk-L1.t_var1))),start=str(full.index.min().date()),end=str(full.index.max().date())),open('L1_meta.json','w'))
