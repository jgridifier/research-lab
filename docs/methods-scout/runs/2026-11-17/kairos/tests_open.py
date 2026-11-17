# T2 baselines (naive, ridge on clr) and T3 Form PF lead test, PREREG.md section B.
import json, numpy as np, pandas as pd
from sklearn.linear_model import RidgeCV
K=json.load(open('kairos_open_results.json')); rng=np.random.default_rng(20261117)
pf=pd.read_csv('formpf_total_monthly.csv').set_index('period'); g=np.log(pf.Total_Total).diff(12)
out={}; T3=[]
for nm,r in K.items():
    M=pd.read_csv(f'{nm}.csv',index_col=0).dropna(); M=M.loc[:, (M>0).any()]
    Z=np.log(M.values+0.5*np.min(M.values[M.values>0])); C=Z-Z.mean(1,keepdims=True)   # clr with a half-min zero fill (FRN pre-2014)
    ck=pd.read_csv(f'clock_{nm}.csv'); yr=ck.yr.values; tr=ck.train.values.astype(bool)
    rd=RidgeCV(alphas=np.logspace(-4,4,33)).fit(C[tr],yr[tr]); pr=rd.predict(C[~tr])   # efficient LOO by default
    mae_r=float(np.mean(np.abs(pr-yr[~tr]))); mc=r['wf_mae_clock']; mn=r['wf_mae_naive']
    t1=r['porcic_p']<0.05; t2=(mc<=0.75*mn) and (mc<=mae_r)
    out[nm]=dict(T1_porcic_p=r['porcic_p'],T1_pass=bool(t1),spearman=r['spearman_seriated_vs_calendar'],mae_clock=mc,mae_naive=mn,mae_ridge=mae_r,
                 clock_vs_naive=mc/mn,T2_pass=bool(t2),n_months=r['n_months'],first=r['first'],last=r['last'],train_end=r['train_end'],ca1_pct=r['ca_axis1_pct'])
    if nm.startswith('O6'): continue
    d=ck.set_index('month'); sp=d.mix_date.diff(12)
    for L in (3,6):
        z=pd.DataFrame({'x':g.shift(L),'y':sp}).dropna()
        x=z.x.values; y=z.y.values; n=len(x); obs=np.corrcoef(x,y)[0,1]
        nul=np.array([np.corrcoef(np.roll(x,rng.integers(12,n-12)),y)[0,1] for _ in range(2000)])
        T3.append(dict(dataset=nm,lead=L,r=float(obs),p=float((1+np.sum(np.abs(nul)>=abs(obs)))/2001),n=n))
ps=np.array([t['p'] for t in T3]); o=np.argsort(ps); m=len(ps); holm=np.empty(m); run=0
for k,i in enumerate(o): run=max(run,(m-k)*ps[i]); holm[i]=min(1,run)
for t,h in zip(T3,holm): t['holm']=float(h)
json.dump(dict(datasets=out,T3=T3),open('tests_open.json','w'),indent=1)
for k,v in out.items(): print(k,{a:(round(b,3) if isinstance(b,float) else b) for a,b in v.items() if a not in('first','last')})
for t in T3: print(t)
