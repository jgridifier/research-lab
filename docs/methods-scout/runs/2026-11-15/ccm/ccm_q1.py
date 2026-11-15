"""Methods scout 2026-11-15, pick 1: convergent cross mapping (pyEDM) on Q1 public aggregates.
Weekly (Wed) 2019-01-16..2025-12-31, n=364: CFTC TFF leveraged-fund net short (UST 2Y+5Y+10Y futures, unweighted contracts),
NY Fed primary-dealer financing fails (UST ex-TIPS), OFR DVP outstanding, OFR DVP-overnight minus tri-party rate spread."""
import pandas as pd, numpy as np, pyEDM, time, json
from statsmodels.tsa.stattools import grangercausalitytests
rng=np.random.default_rng(20261115)
X=pd.read_csv('panel.csv',parse_dates=['date'])
V=['d_lev','dl_fails','dl_dvp','d_spread']
LAB={'d_lev':'TFF lev-fund net short (Δ)','dl_fails':'financing fails (Δlog)','dl_dvp':'DVP volume (Δlog)','d_spread':'DVP−tri-party spread (Δ)'}
def frame(sub):
    df=pd.DataFrame({'time':np.arange(len(sub))+1})
    for c in V: df[c]=((sub[c]-sub[c].mean())/sub[c].std()).values
    return df
df=frame(X); n=len(df); half=n//2
out={'n':n,'start':str(X.date.min().date()),'end':str(X.date.max().date())}
T0=time.time()
# 1) embedding dimension and nonlinearity per series (first half lib, second half pred)
emb={}
for c in V:
    e=pyEDM.EmbedDimension(dataFrame=df,columns=c,target=c,lib=[1,half],pred=[half+1,n],maxE=8,showPlot=False)
    E=int(e.loc[e.rho.idxmax(),'E'])
    th=pyEDM.PredictNonlinear(dataFrame=df,columns=c,target=c,lib=[1,half],pred=[half+1,n],E=E,showPlot=False)
    emb[c]={'E':E,'rho_simplex':float(e.rho.max()),'rho_theta0':float(th.rho.iloc[0]),'rho_best':float(th.rho.max()),'theta_best':float(th.iloc[th.rho.idxmax(),0])}
out['embedding']=emb
# 2) CCM pairs with convergence, surrogate null, lag scan
pairs=[('d_lev','dl_fails'),('d_lev','dl_dvp'),('d_lev','d_spread'),('dl_fails','d_spread'),('dl_dvp','dl_fails')]
libs=[20,40,80,120,160,200,240,280,320,350]
def ccm(d,a,b,E,libsizes,seed=1,Tp=0,sample=100):
    return pyEDM.CCM(dataFrame=d,columns=a,target=b,E=E,Tp=Tp,libSizes=libsizes,sample=sample,seed=seed,exclusionRadius=4,parallel=False)
def surr_shift(x):
    k=rng.integers(26,len(x)-26); return np.roll(x,k)
res={}; curves={}
for a,b in pairs:
    # column a's manifold cross-maps b  => evidence "b drives a" (Sugihara 2012 convention); reverse for a drives b
    Ea=emb[a]['E']; Eb=emb[b]['E']
    r1=ccm(df,a,b,Ea,libs); r2=ccm(df,b,a,Eb,libs)
    k1=f'{a}:{b}'; k2=f'{b}:{a}'
    curves[f'{b} -> {a}']=r1[['LibSize',k1]].rename(columns={k1:'rho'}).to_dict('list')
    curves[f'{a} -> {b}']=r2[['LibSize',k2]].rename(columns={k2:'rho'}).to_dict('list')
    for drv,resp,r,k,E in [(b,a,r1,k1,Ea),(a,b,r2,k2,Eb)]:
        rho_max=float(r[k].iloc[-1]); rho_min=float(r[k].iloc[0])
        # null: circularly shift the putative driver, cross map from responder manifold
        null=[]
        for s in range(200):
            d2=df.copy(); d2[drv]=surr_shift(df[drv].values)
            rr=ccm(d2,resp,drv,E,[350],seed=s+11,sample=20); null.append(float(rr.iloc[0,1]))
        null=np.array(null); p=(1+np.sum(null>=rho_max))/(1+len(null))
        # lag scan (Ye et al. 2015): cross map responder -> driver at Tp=-4..4
        lag={}
        for Tp in range(-4,5):
            rr=ccm(df,resp,drv,E,[350],Tp=Tp,sample=20); lag[int(Tp)]=float(rr.iloc[0,1])
        # Granger baseline driver -> responder (lags 1..4, min p over lags, ssr F)
        g=grangercausalitytests(df[[resp,drv]].values,maxlag=4)
        gp={int(L):float(g[L][0]['ssr_ftest'][1]) for L in g}
        # stability: two halves
        halves=[]
        for sub in (X.iloc[:half],X.iloc[half:]):
            dh=frame(sub.reset_index(drop=True)); rr=ccm(dh,resp,drv,E,[20,len(dh)-10],sample=50)
            halves.append([float(rr.iloc[0,1]),float(rr.iloc[-1,1])])
        res[f'{drv} -> {resp}']={'E':E,'rho_L20':rho_min,'rho_L350':rho_max,'converges':rho_max-rho_min,
            'null_mean':float(null.mean()),'null_q95':float(np.quantile(null,0.95)),'p_shift':float(p),
            'lag_rho':lag,'best_lag':int(max(lag,key=lag.get)),'granger_p':gp,'granger_minp':min(gp.values()),
            'half1_L20_Lmax':halves[0],'half2_L20_Lmax':halves[1]}
        print(drv,'->',resp,{k:(round(v,3) if isinstance(v,float) else v) for k,v in res[f'{drv} -> {resp}'].items() if k not in('lag_rho','granger_p')},flush=True)
out['ccm']=res; out['curves']=curves
out['runtime_s']=time.time()-T0
# timing: one CCM curve
t=time.time(); ccm(df,'d_lev','dl_fails',3,libs); out['one_curve_s']=time.time()-t
json.dump(out,open('ccm_results.json','w'),indent=1,default=float)
print(json.dumps(emb,indent=1)); print('runtime',out['runtime_s'])
