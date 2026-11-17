# Ext 3 (New use) for #50, PREREG.md section D: Extension-2 procedure P1 unchanged (increment split, re-projected
# sign flip) with B = 999, on live-Q1 public compositions O1 (venue x tenor) and O2 (tri-party collateral), monthly.
# Market covariates k = 3: monthly mean VIX, monthly mean 10y Treasury yield, log total panel volume. Seed 20261117.
import json, numpy as np, pandas as pd
from scipy.spatial.distance import pdist, squareform
from ecotrajpy.ext2 import clr, split_increments, path_test, draw_signs
from ecotrajpy.core import define_trajectories
from ecotrajpy.comparison import trajectory_distances
DD='/workspace/research/drive_inv/data/'; KD='/workspace/ms-1117/kairos/'
def monthly(f,c):
    s=pd.read_csv(DD+f,parse_dates=['observation_date']).set_index('observation_date')[c]; s=pd.to_numeric(s,errors='coerce')
    m=s.resample('ME').mean(); m.index=m.index.strftime('%Y-%m'); return m
vix=monthly('VIXCLS.csv','VIXCLS'); y10=monthly('DGS10.csv','DGS10')
rng=np.random.default_rng(20261117); out={}
EP={'2020-03 Covid dash':('2020-01','2020-06'),'2023-03 bank stress':('2023-01','2023-06'),'2025-08 onward':('2025-06','2025-12'),
    'quiet 2019':('2019-01','2019-06'),'quiet 2024':('2024-01','2024-06')}
for nm in ['O1_venue_tenor','O2_triparty_collateral']:
    M=pd.read_csv(KD+nm+'.csv',index_col=0).dropna(); M=M[(M>0).all(1)]
    X=pd.DataFrame({'vix':vix,'y10':y10}).reindex(M.index); X['logvol']=np.log(M.sum(1)); X=X.dropna(); M=M.loc[X.index]
    S=(M.values/M.values.sum(1,keepdims=True)); C=clr(S); sp=split_increments(C,X.values)
    signs=draw_signs(rng,999,len(C)-1)
    p1=path_test(C[0]+sp['r'],signs,Mmat=sp['Mmat'],inc=sp['E'])
    w=path_test(C,signs)
    fit=sp['fit']; share=float(np.sum(fit**2)/np.sum(sp['dC']**2))
    net=(sp['r'][-1]); parts=list(M.columns); top=sorted(zip(parts,net),key=lambda t:-abs(t[1]))[:3]
    # episode map: DSPD between residual sub-paths (descriptive)
    R=pd.DataFrame(C[0]+sp['r'],index=M.index); coords=[];sites=[];times=[]
    for k,(a,b) in EP.items():
        seg=R.loc[a:b]
        if len(seg)<3: continue
        coords.append(seg.values); sites+= [k]*len(seg); times+= list(range(1,len(seg)+1))
    Z=np.vstack(coords); tr=define_trajectories(squareform(pdist(Z)),sites=sites,times=times)
    Dm=trajectory_distances(tr,distance_type='DSPD')
    out[nm]=dict(n_months=len(M),first=M.index[0],last=M.index[-1],k=3,market_step_energy_share=share,
                 P1_residual_dir=p1['stat'],P1_p=p1['p'],W_whole_path_dir=w['stat'],W_p=w['p'],
                 residual_net_top3={a:float(b) for a,b in top},episode_dspd=Dm.round(4).to_dict())
ps=[out[k]['P1_p'] for k in out]; o=np.argsort(ps); h=[0,0]; run=0
for r_,i in enumerate(o): run=max(run,(2-r_)*ps[i]); h[i]=min(1,run)
for k,hh in zip(out,h): out[k]['P1_holm']=hh
out['recurrence']=bool(min(h)<=0.05)
json.dump(out,open('ext3_results.json','w'),indent=1,default=float); print(json.dumps(out,indent=1,default=float))
