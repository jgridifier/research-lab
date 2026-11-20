import numpy as np, pandas as pd, json, sys, time, warnings
warnings.filterwarnings('ignore'); sys.path.insert(0,'.')
from lk_port import lkif, var1_t
from lkhelp import fitvar, sim, V, X
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.api import VAR
from scipy.stats import t as tdist, norm
rng=np.random.default_rng(5); out={}
full=X[V].dropna(); Z=((full-full.mean())/full.std()).values; n=len(Z)
# HC3 size on two edges under the same bootstrap null
A,c,E=fitvar(Z); hc={}
for s_,t_ in [('d_spread','dl_fails'),('dl_fails','d_spread')]:
    i,j=V.index(t_),V.index(s_); A0=A.copy(); A0[i,j]=0; r=[]
    for b in range(400):
        x=sim(A0,c,E,n,rng,Z[0]); x=(x-x.mean(0))/x.std(0)
        ex=sm.add_constant(x[:-1]); m=sm.OLS(x[1:,i],ex).fit(cov_type='HC3'); r.append(m.pvalues[j+1]<0.05)
    hc[f'{s_}->{t_}']=float(np.mean(r)); print('HC3 size',s_,t_,hc[f'{s_}->{t_}'],flush=True)
out['hc3_size']=hc
# B: walk-forward 1-week-ahead dl_fails (log fails change) from 2022-07-06
D=X[V+['l_fails']].dropna(); y=D.dl_fails.values; idx=np.where(D.index>='2022-07-06')[0]
def lagmat(cols,t0,t1):  # rows t in [t0,t1): predictors at t-1 (and t-2 for own)
    pass
pred={k:[] for k in ['ardl_own','ardl_lkif','ardl_granger','sarimax','rw']}; act=[]
Vs=V
for t in idx:
    tr=D.iloc[:t]; Ztr=((tr[Vs]-tr[Vs].mean())/tr[Vs].std()).values
    R=lkif(Ztr); G=VAR(Ztr).fit(1)
    i=0; lk_par=[Vs[j] for j in range(1,6) if R['p'][i,j]<0.05]; gc_par=[Vs[j] for j in range(1,6) if G.test_causality(0,[j],kind='f').pvalue<0.05]
    def ardl(par):
        Y=tr.dl_fails.values[2:]; Xr=np.column_stack([tr.dl_fails.values[1:-1],tr.dl_fails.values[:-2]]+[tr[p].values[1:-1] for p in par]); Xr=sm.add_constant(Xr)
        b=np.linalg.lstsq(Xr,Y,rcond=None)[0]; xn=np.r_[1,tr.dl_fails.values[-1],tr.dl_fails.values[-2],[tr[p].values[-1] for p in par]]; return xn@b
    pred['ardl_own'].append(ardl([])); pred['ardl_lkif'].append(ardl(lk_par)); pred['ardl_granger'].append(ardl(gc_par))
    try:
        sm_=SARIMAX(tr.dl_fails.values,order=(1,0,1),trend='c').fit(disp=False); pred['sarimax'].append(float(sm_.forecast(1)[0]))
    except Exception: pred['sarimax'].append(np.nan)
    pred['rw'].append(0.0); act.append(y[t])
act=np.array(act); rm={k:float(np.sqrt(np.nanmean((np.array(v)-act)**2))) for k,v in pred.items()}
def dm(a,b):
    d=(np.array(pred[a])-act)**2-(np.array(pred[b])-act)**2; d=d[~np.isnan(d)]; s=np.sqrt(np.var(d,ddof=1)/len(d)); return float(2*norm.sf(abs(d.mean()/s)))
out['B']=dict(n_test=len(act),start=str(D.index[idx[0]].date()),end=str(D.index[idx[-1]].date()),rmse=rm,dm_lkif_vs_own=dm('ardl_lkif','ardl_own'),dm_granger_vs_own=dm('ardl_granger','ardl_own'),gain_lkif_pct=100*(1-rm['ardl_lkif']/rm['ardl_own']))
print(out['B'],flush=True)
# timing
tim=[]
for d in [6,30,100]:
    for nn in [400,3000]:
        x=rng.standard_normal((nn,d))
        t0=time.perf_counter(); lkif(x); t1=time.perf_counter()
        t2=time.perf_counter(); m=VAR(x).fit(1)
        if d<=30:
            for i in range(d):
                for j in range(d):
                    if i!=j: m.test_causality(i,[j],kind='f')
            t3=time.perf_counter(); g=t3-t2
        else:
            t3=time.perf_counter(); 
            for i in range(3):
                for j in range(d):
                    if i!=j: m.test_causality(i,[j],kind='f')
            g=(time.perf_counter()-t2)/ (3*(d-1)) * d*(d-1)  # extrapolated from 3 rows
        tim.append(dict(d=d,n=nn,lkif_s=t1-t0,granger_loop_s=g,extrapolated=d>30)); print(tim[-1],flush=True)
out['timing']=tim
json.dump(out,open('B_timing.json','w'),indent=1)
