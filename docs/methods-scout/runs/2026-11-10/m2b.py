import pandas as pd, numpy as np, json, time
from changeforest import changeforest, Control
import ruptures as rpt
from sklearn.cluster import KMeans
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
O='/workspace/scout/out/'; F='/workspace/scout/fig/'
res=json.load(open(O+'m2_results.json'))
lev_cps=res['B1_rf_cps']; gaps=np.diff(pd.to_datetime(lev_cps)).astype('timedelta64[D]').astype(int)/7
res['B0_levels_artifact']={'n_cps':len(lev_cps),'median_gap_weeks':float(np.median(gaps)),'min_gap_weeks':float(gaps.min()),'max_gap_weeks':float(gaps.max())}
W=pd.read_csv(O+'weekly_panel.csv',parse_dates=['date']).set_index('date')
cols=['VIXCLS','T10Y2Y','DGS2','MORTGAGE30US','NFCI','STLFSI4']
X=W[cols].copy(); X['VIXCLS']=np.log(X['VIXCLS']); X=X.diff().dropna()
X.columns=['dlogVIX','dT10Y2Y','dDGS2','dMORT','dNFCI','dSTLFSI4']
Z=((X-X.mean())/X.std()).values; dates=X.index
def cf(Z,m='random_forest',ctl=None):
    t=time.perf_counter(); r=changeforest(Z,m,'bs',ctl) if ctl else changeforest(Z,m,'bs'); return r,time.perf_counter()-t
r,t=cf(Z); cps=r.split_points()
res['B1_n']=len(Z); res['B1_period']=[str(dates[0].date()),str(dates[-1].date())]; res['B1_rf_secs']=t
res['B1_rf_cps']=[str(dates[i].date()) for i in cps]
b=[0]+cps+[len(Z)]
res['B1_segments']=[dict(start=str(dates[a].date()),end=str(dates[c-1].date()),weeks=c-a,
   **{('sd_'+k):round(float(X.iloc[a:c][k].std()),3) for k in X.columns},
   NFCI_level=round(float(W.loc[dates[a]:dates[c-1],'NFCI'].mean()),2), VIX_level=round(float(W.loc[dates[a]:dates[c-1],'VIXCLS'].mean()),1),
   corr_dVIX_dDGS2=round(float(X.iloc[a:c][['dlogVIX','dDGS2']].corr().iloc[0,1]),2)) for a,c in zip(b[:-1],b[1:])]
rk,tk=cf(Z,'knn'); rm,tm=cf(Z,'change_in_mean')
res['B2_knn_cps']=[str(dates[i].date()) for i in rk.split_points()]; res['B2_cim_cps']=[str(dates[i].date()) for i in rm.split_points()]
res['B2_secs']={'random_forest':t,'knn':tk,'change_in_mean':tm}
def match(ref,others,tol=13): return [float(np.mean([any(abs(c-o)<=tol for o in oc) for oc in others])) for c in ref]
seeds=[cf(Z,'random_forest',Control(seed=s))[0].split_points() for s in range(10)]
res['B2_seed_reproduce']={str(dates[c].date()):round(m,2) for c,m in zip(cps,match(cps,seeds))}; res['B2_seed_ncp']=[len(s) for s in seeds]
drop={cn:cf(np.delete(Z,j,axis=1))[0].split_points() for j,cn in enumerate(X.columns)}
res['B2_dropone_match']={str(dates[c].date()):round(m,2) for c,m in zip(cps,match(cps,list(drop.values())))}; res['B2_dropone_ncp']={k:len(v) for k,v in drop.items()}
# subsample stability: fit on first 70% only, check CPs reproduced there
cut=int(.7*len(Z)); sub=cf(Z[:cut])[0].split_points()
ref_in=[c for c in cps if c<cut-26]
res['B2_first70_ncp']=len(sub); res['B2_first70_match']=round(float(np.mean(match(ref_in,[sub]))),2) if ref_in else None
K=max(len(cps),1)
rb=rpt.Binseg(model='rbf').fit(Z).predict(n_bkps=K)[:-1]; bl=rpt.Binseg(model='l2').fit(Z).predict(n_bkps=K)[:-1]
res['B2_binseg_rbf_cps']=[str(dates[i].date()) for i in rb]; res['B2_binseg_l2_cps']=[str(dates[i].date()) for i in bl]
res['B2_rf_vs_binseg_rbf_match']=round(float(np.mean(match(cps,[rb]))),2); res['B2_rf_vs_binseg_l2_match']=round(float(np.mean(match(cps,[bl]))),2)
km=KMeans(n_clusters=K+1,n_init=10,random_state=0).fit(Z).labels_; res['B2_kmeans_label_switches']=int((np.diff(km)!=0).sum()); res['B2_cf_switches']=len(cps)
# false-positive checks: row-shuffled data should give 0 change points
rng=np.random.default_rng(1)
res['B2_shuffled_weekly_ncp']=[len(cf(Z[rng.permutation(len(Z))])[0].split_points()) for _ in range(5)]
Dd=pd.read_csv(O+'daily_panel.csv',parse_dates=['date']).set_index('date')
DX=pd.DataFrame({'dlogVIX':np.log(Dd.VIXCLS).diff(),'dT10Y2Y':Dd.T10Y2Y.diff(),'dDGS2':Dd.DGS2.diff(),'dDGS10':Dd.DGS10.diff()}).dropna()
DX=DX[(DX.abs()<DX.abs().quantile(0.9999)).all(axis=1)]; DZ=((DX-DX.mean())/DX.std()).values
res['B3_shuffled_daily_ncp']=[len(cf(DZ[rng.permutation(len(DZ))])[0].split_points()) for _ in range(3)]
json.dump(res,open(O+'m2_results.json','w'),indent=1,default=lambda o: o.tolist() if hasattr(o,'tolist') else int(o))
fig,ax=plt.subplots(3,1,figsize=(12,7),sharex=True)
for a,(c,lab) in zip(ax,[('VIXCLS','VIX (weekly avg)'),('NFCI','NFCI'),('DGS2','2y yield')]):
    a.plot(W.index,W[c],lw=.8,color='#1f2937'); a.set_ylabel(lab,fontsize=9)
    for i in cps: a.axvline(dates[i],color='#e11d48',lw=1.2)
ax[0].set_title('changeforest (random forest) on weekly CHANGES of 6 series: detected breaks in red',fontsize=10)
plt.tight_layout(); plt.savefig(F+'m2_weekly_breaks.png',dpi=120); plt.close()
fig,ax=plt.subplots(figsize=(12,2.6)); ax.plot(W.index,W.VIXCLS,lw=.7,color='#1f2937')
for c in lev_cps: ax.axvline(pd.Timestamp(c),color='#f59e0b',lw=.8)
ax.set_title(f'Failure mode: on persistent LEVELS changeforest returns {len(lev_cps)} breaks spaced ~{np.median(gaps):.0f} weeks apart (artifact)',fontsize=10)
plt.tight_layout(); plt.savefig(F+'m2_levels_artifact.png',dpi=120); plt.close()
print(len(cps), res['B1_rf_cps'], res['B2_seed_ncp'], res['B2_shuffled_weekly_ncp'], res['B3_shuffled_daily_ncp'])
