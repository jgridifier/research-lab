import pandas as pd, numpy as np, json, time
from changeforest import changeforest, Control
import ruptures as rpt
from sklearn.cluster import KMeans
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
O='/workspace/scout/out/'; F='/workspace/scout/fig/'
res={}
W=pd.read_csv(O+'weekly_panel.csv',parse_dates=['date']).set_index('date')
cols=['VIXCLS','T10Y2Y','DGS2','MORTGAGE30US','NFCI','STLFSI4']
X=W[cols].copy()
# transformations: log VIX, levels else; z-score (scale only matters for knn/mean)
X['VIXCLS']=np.log(X['VIXCLS'])
Z=((X-X.mean())/X.std()).values
dates=W.index
def run(Z,method,ctl=None):
    t=time.perf_counter(); r=changeforest(Z,method,'bs',ctl) if ctl else changeforest(Z,method,'bs'); return r, time.perf_counter()-t
def segtab(cps):
    b=[0]+list(cps)+[len(X)]; rows=[]
    for a,c in zip(b[:-1],b[1:]):
        seg=W.iloc[a:c]; rows.append(dict(start=str(seg.index[0].date()),end=str(seg.index[-1].date()),weeks=c-a,
            **{k:round(float(seg[k].mean()),2) for k in cols}))
    return rows
# B1: main segmentation
r_rf,t_rf=run(Z,'random_forest')
cps=r_rf.split_points(); res['B1_n']=len(Z); res['B1_period']=[str(dates[0].date()),str(dates[-1].date())]
res['B1_rf_cps']=[str(dates[i].date()) for i in cps]; res['B1_rf_secs']=t_rf; res['B1_segments']=segtab(cps)
# B2: robustness — methods, seeds, feature drop, subsample
r_knn,t_knn=run(Z,'knn'); r_cim,t_cim=run(Z,'change_in_mean')
res['B2_knn_cps']=[str(dates[i].date()) for i in r_knn.split_points()]; res['B2_cim_cps']=[str(dates[i].date()) for i in r_cim.split_points()]
res['B2_secs']={'random_forest':t_rf,'knn':t_knn,'change_in_mean':t_cim}
seed_cps=[]
for s in range(10):
    r,_=run(Z,'random_forest',Control(seed=s))
    seed_cps.append(r.split_points())
def match_rate(ref, others, tol=13):
    out=[]
    for c in ref: out.append(np.mean([any(abs(c-o)<=tol for o in oc) for oc in others]))
    return out
res['B2_seed_reproduce']={str(dates[c].date()):round(m,2) for c,m in zip(cps,match_rate(cps,seed_cps))}
res['B2_seed_ncp']=[len(s) for s in seed_cps]
drop={}
for j,cn in enumerate(cols):
    r,_=run(np.delete(Z,j,axis=1),'random_forest'); drop[cn]=r.split_points()
res['B2_dropone_match']={str(dates[c].date()):round(m,2) for c,m in zip(cps,match_rate(cps,list(drop.values())))}
res['B2_dropone_ncp']={k:len(v) for k,v in drop.items()}
# baselines: ruptures PELT rbf with penalty chosen to give same # of segments, binseg l2; kmeans fragmentation
K=len(cps)
t=time.perf_counter(); bs=rpt.Binseg(model='l2').fit(Z).predict(n_bkps=K); t_bs=time.perf_counter()-t
t=time.perf_counter(); rb=rpt.Binseg(model='rbf').fit(Z).predict(n_bkps=K); t_rbf=time.perf_counter()-t
res['B2_binseg_l2_cps']=[str(dates[i].date()) for i in bs[:-1]]; res['B2_binseg_rbf_cps']=[str(dates[i].date()) for i in rb[:-1]]
res['B2_baseline_secs']={'binseg_l2':t_bs,'binseg_rbf':t_rbf}
res['B2_rf_vs_binseg_rbf_match']=round(float(np.mean(match_rate(cps,[rb[:-1]]))),2)
res['B2_rf_vs_binseg_l2_match']=round(float(np.mean(match_rate(cps,[bs[:-1]]))),2)
km=KMeans(n_clusters=K+1,n_init=10,random_state=0).fit(Z).labels_
res['B2_kmeans_label_switches']=int((np.diff(km)!=0).sum()); res['B2_cf_switches']=K
# B3: daily panel + timing scaling
Dd=pd.read_csv(O+'daily_panel.csv',parse_dates=['date']).set_index('date')
DX=pd.DataFrame({'dlogVIX':np.log(Dd.VIXCLS).diff(),'dT10Y2Y':Dd.T10Y2Y.diff(),'dDGS2':Dd.DGS2.diff(),'dDGS10':Dd.DGS10.diff()}).dropna()
DX=DX[(DX.abs()<DX.abs().quantile(0.9999)).all(axis=1)]
DZ=((DX-DX.mean())/DX.std()).values; dd=DX.index
r_d,t_d=run(DZ,'random_forest'); dcps=r_d.split_points()
res['B3_n']=len(DZ); res['B3_rf_secs']=t_d; res['B3_cps']=[str(dd[i].date()) for i in dcps]
b=[0]+list(dcps)+[len(DZ)]
res['B3_segments']=[dict(start=str(dd[a].date()),end=str(dd[c-1].date()),days=c-a,
    **{('sd_'+k):round(float(DX.iloc[a:c][k].std()),4) for k in DX.columns},
    corr_dVIX_dDGS10=round(float(DX.iloc[a:c][['dlogVIX','dDGS10']].corr().iloc[0,1]),3)) for a,c in zip(b[:-1],b[1:])]
r_dm,_=run(DZ,'change_in_mean'); res['B3_cim_ncp']=len(r_dm.split_points())
# timing scaling on synthetic data: rf vs knn vs ruptures Pelt rbf
rng=np.random.default_rng(0); sc=[]
for n in [1000,2000,4000,8000,16000]:
    Xs=np.concatenate([rng.normal(0,1,(n//2,5)),rng.normal(0,1.6,(n-n//2,5))])
    row={'n':n}
    for m in ['random_forest','knn']:
        if m=='knn' and n>8000: row[m]=None; continue
        t=time.perf_counter(); rr=changeforest(Xs,m,'bs'); row[m]=round(time.perf_counter()-t,3); row[m+'_cps']=rr.split_points()
    if n<=4000:
        t=time.perf_counter(); pp=rpt.Pelt(model='rbf',min_size=20).fit(Xs).predict(pen=np.log(n)*5*2); row['pelt_rbf']=round(time.perf_counter()-t,3); row['pelt_rbf_cps']=pp[:-1]
    else: row['pelt_rbf']=None
    sc.append(row)
res['B3_scaling']=sc
import changeforest as cfm, ruptures, sklearn
res['versions']={'changeforest':getattr(cfm,'__version__','1.2.1'),'ruptures':ruptures.__version__,'sklearn':sklearn.__version__}
json.dump(res,open(O+'m2_results.json','w'),indent=1,default=lambda o: o.tolist() if hasattr(o,'tolist') else int(o))
# figures
fig,ax=plt.subplots(3,1,figsize=(12,7),sharex=True)
for a,(c,lab) in zip(ax,[('VIXCLS','VIX (weekly avg)'),('NFCI','NFCI'),('T10Y2Y','10y-2y spread')]):
    a.plot(W.index,W[c],lw=.8,color='#1f2937'); a.set_ylabel(lab,fontsize=9)
    for i in cps: a.axvline(dates[i],color='#e11d48',lw=1.2)
    for i in r_knn.split_points(): a.axvline(dates[i],color='#2563eb',lw=.8,ls=':')
ax[0].set_title('changeforest (random forest) breaks in red, kNN breaks dotted blue — weekly panel, 6 series',fontsize=10)
plt.tight_layout(); plt.savefig(F+'m2_weekly_breaks.png',dpi=120); plt.close()
fig,ax=plt.subplots(figsize=(12,3.2))
ax.plot(dd,DX.dDGS10.rolling(63).std(),lw=.8,color='#1f2937',label='63d sd of daily Δ10y')
for i in dcps: ax.axvline(dd[i],color='#e11d48',lw=1)
ax.legend(fontsize=8); ax.set_title('Daily changes panel (n≈9k): changeforest breaks',fontsize=10); plt.tight_layout(); plt.savefig(F+'m2_daily_breaks.png',dpi=120); plt.close()
s=pd.DataFrame(sc); fig,ax=plt.subplots(figsize=(6,3.5))
for m,c in [('random_forest','#e11d48'),('knn','#2563eb'),('pelt_rbf','#6b7280')]:
    q=s.dropna(subset=[m]); ax.loglog(q.n,q[m],'o-',color=c,label=m)
ax.set_xlabel('n'); ax.set_ylabel('seconds'); ax.legend(fontsize=8); ax.set_title('Fit time vs n (5 dims, one variance break)',fontsize=10)
plt.tight_layout(); plt.savefig(F+'m2_scaling.png',dpi=120); plt.close()
print('ok')
