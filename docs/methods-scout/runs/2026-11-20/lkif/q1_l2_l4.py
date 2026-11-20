import numpy as np, pandas as pd, json, sys
sys.path.insert(0,'.'); from lk_port import lkif, var1_t
from lkhelp import fitvar, sim, V, X
rng=np.random.default_rng(11)
def std(D): return ((D-D.mean())/D.std()).values
def bootp(Z,i,j,B,rng):
    A,c,E=fitvar(Z); A0=A.copy(); A0[i,j]=0; T0=abs(lkif(Z)['T'][i,j]); cnt=0
    for b in range(B):
        x=sim(A0,c,E,len(Z),rng,Z[0]); x=(x-x.mean(0))/x.std(0); cnt+=abs(lkif(x)['T'][i,j])>=T0
    return (cnt+1)/(B+1)
out={}
full=X[V].dropna(); Z=std(full); R=lkif(Z); t=var1_t(Z)
out['derivation_check_max_abs_diff']=float(np.max(np.abs(np.abs(R['T']/R['SE'])-np.abs(t))[~np.eye(6,dtype=bool)]))
print('deriv', out['derivation_check_max_abs_diff'])
key=[('d_spread','dl_fails'),('d_spread','dl_dvp'),('dl_fails','d_spread'),('d_lev','dl_fails'),('d_vix','dl_fails')]
halves={'2018-05..2022-02':full[full.index<'2022-03-02'],'2022-03..2025-12':full[full.index>='2022-03-02']}
out['halves']={}
for h,D in halves.items():
    Zh=std(D); Rh=lkif(Zh); out['halves'][h]={}
    for s_,t_ in key:
        i,j=V.index(t_),V.index(s_)
        out['halves'][h][f'{s_}->{t_}']=dict(n=len(Zh),tau=float(Rh['tau'][i,j]),T=float(Rh['T'][i,j]),p_asym=float(Rh['p'][i,j]),p_boot=float(bootp(Zh,i,j,499,rng)))
    print(h,out['halves'][h],flush=True)
# rolling 104-week tau for key edges (5-var without lev to reach 2026-09)
V5=['dl_fails','d_spread','dl_dvp','dl_tri','d_vix']; F5=X[V5].dropna(); roll=[]
for end in range(104,len(F5)+1,4):
    D=F5.iloc[end-104:end]; Rr=lkif(std(D))
    row=dict(end=str(D.index[-1].date()))
    for s_,t_ in [('d_spread','dl_fails'),('dl_fails','d_spread'),('d_spread','dl_dvp')]:
        i,j=V5.index(t_),V5.index(s_); row[f'{s_}->{t_}_tau']=float(Rr['tau'][i,j]); row[f'{s_}->{t_}_p']=float(Rr['p'][i,j])
    roll.append(row)
pd.DataFrame(roll).to_csv('L2_rolling.csv',index=False)
# late 2025: 5-var system on 2024-07..2026-09 vs 2022-03..2024-06
out['late']={}
for lab,D in {'2022-03..2024-06':F5[(F5.index>='2022-03-02')&(F5.index<'2024-07-03')],'2024-07..2026-09':F5[F5.index>='2024-07-03']}.items():
    Zl=std(D); Rl=lkif(Zl); out['late'][lab]={}
    for s_,t_ in [('d_spread','dl_fails'),('dl_fails','d_spread'),('d_spread','dl_dvp')]:
        i,j=V5.index(t_),V5.index(s_); out['late'][lab][f'{s_}->{t_}']=dict(n=len(Zl),tau=float(Rl['tau'][i,j]),p_asym=float(Rl['p'][i,j]),p_boot=float(bootp(Zl,i,j,499,rng)))
    print(lab,out['late'][lab],flush=True)
# L4 monthly
M=pd.read_csv('q1_monthly_lkif.csv').set_index('period'); VM=list(M.columns); Zm=std(M); Rm=lkif(Zm)
from statsmodels.tsa.api import VAR
fit=VAR(Zm).fit(1); rows=[]
for i in range(6):
    for j in range(6):
        if i==j: continue
        rows.append(dict(src=VM[j],tgt=VM[i],tau=Rm['tau'][i,j],T=Rm['T'][i,j],p_asym=Rm['p'][i,j],p_boot=bootp(Zm,i,j,999,rng),p_granger=fit.test_causality(i,[j],kind='f').pvalue))
L4=pd.DataFrame(rows)
def holm(p):
    p=np.asarray(p); o=np.argsort(p); m=len(p); adj=np.empty(m); run=0
    for k,i in enumerate(o): run=max(run,(m-k)*p[i]); adj[i]=min(1,run)
    return adj
L4['holm_boot']=holm(L4.p_boot); L4['holm_asym']=holm(L4.p_asym); L4.to_csv('L4_monthly.csv',index=False)
print(L4.sort_values('p_boot').head(8).round(4).to_string())
# AIC-lag sensitivity via package (multi-lag)
np.mat=np.asmatrix
from LK_Info_Flow import multi_causality_est
try:
    Rp=multi_causality_est(Zm.T,max_lag=-1); out['L4_aic_lag']=int(Rp['max_lag'])
except TypeError as e:
    out['L4_aic_lag']='package error: '+str(e)
json.dump(out,open('L2_L4.json','w'),indent=1)
