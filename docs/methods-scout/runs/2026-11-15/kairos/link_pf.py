import pandas as pd, numpy as np, json
rng=np.random.default_rng(20261115)
mc=pd.read_csv('mixclock.csv').set_index('month')
pf=pd.read_csv('formpf_monthly.csv').set_index('period')
d=mc.join(pf,how='inner')
d['mix_speed']=d.mix_date.diff(12)          # years of "mix time" advanced per 12 calendar months (1.0 = keeps pace)
d['g_pb']=np.log(d['Secured_Prime Broker']).diff(12)
d['g_rr']=np.log(d['Secured_Reverse Repo']).diff(12)
d['g_tot']=np.log(d['Total_Total']).diff(12)
out={'n_joint':int(d.dropna().shape[0]),'first':d.dropna().index[0],'last':d.dropna().index[-1]}
def shiftnull(x,y,B=2000,minsh=12):
    x=np.asarray(x);y=np.asarray(y);obs=np.corrcoef(x,y)[0,1];n=len(x)
    nul=np.array([np.corrcoef(np.roll(x,rng.integers(minsh,n-minsh)),y)[0,1] for _ in range(B)])
    return float(obs),float((1+np.sum(np.abs(nul)>=abs(obs)))/(1+B))
res={}
for g in ['g_pb','g_rr','g_tot']:
    for lag in [0,3,6]:
        z=pd.DataFrame({'x':d[g].shift(lag),'y':d.mix_speed}).dropna()
        r,p=shiftnull(z.x,z.y); res[f'{g}_lead{lag}_vs_mix_speed']={'r':r,'p_shift':p,'n':len(z)}
        z=pd.DataFrame({'x':d[g].shift(lag),'y':d.mix_age_resid}).dropna()
        r,p=shiftnull(z.x,z.y); res[f'{g}_lead{lag}_vs_mix_resid']={'r':r,'p_shift':p,'n':len(z)}
out['tests']=res
ps=sorted(v['p_shift'] for v in res.values()); m=len(ps)
out['n_tests']=m; out['min_p']=ps[0]; out['holm_min_p']=min(1,ps[0]*m)
# yearly mix speed summary
ys=mc.copy(); ys['y']=ys.index.str[:4]; s=ys.groupby('y').agg(mix=('mix_date','mean'),cal=('yr','mean')); s['gap']=s.mix-s.cal
out['yearly_mix_minus_calendar']=s.gap.round(2).to_dict()
# tenor-bucket redefinition check (OFR split <=30d into 2-7 and 8-30 from 2025-08-14)
out['resid_2025_07_to_10']=mc.loc['2025-07':'2025-10','mix_age_resid'].round(2).to_dict()
json.dump(out,open('link_pf.json','w'),indent=1); print(json.dumps(out,indent=1))
