import sys, json, time, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
sys.path.insert(0,'pid'); sys.path.insert(0,'gpid/src')
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
D=pd.read_csv('q3_pim_panel.csv'); D=D[D.payout_rwa.notna()&D.payout_rwa_next.notna()].copy()
out={}
def ols_pred(tr,te,X):
    m=sm.OLS(tr.payout_rwa_next,sm.add_constant(tr[X],has_constant='add')).fit(); return m.predict(sm.add_constant(te[X],has_constant='add'))
rows=[]
for t in range(2016,2025):
    tr=D[D.year<t]; te=D[D.year==t]
    if len(te)==0: continue
    r=dict(year=t,y=te.payout_rwa_next.values,firm=te.id_rssd.values)
    for nm,X in {'ols_pt':['income_pretax_net_rate'],'ols_pt_dd':['income_pretax_net_rate','drawdown'],'ols_dd':['drawdown'],
                 'ardl_pt':['payout_rwa','income_pretax_net_rate'],'ardl_pt_dd':['payout_rwa','income_pretax_net_rate','drawdown'],'ardl_dd':['payout_rwa','drawdown']}.items():
        r[nm]=ols_pred(tr,te,X).values
    for nm,X in {'sarimax_pt':['income_pretax_net_rate'],'sarimax_pt_dd':['income_pretax_net_rate','drawdown']}.items():
        pr=r['ardl_'+nm.split('_',1)[1]].copy(); nsx=0
        for k,(i,row) in enumerate(te.iterrows()):
            h=D[(D.id_rssd==row.id_rssd)&(D.year<t)].sort_values('year')
            # firm series: payout_rwa by year, exog aligned; forecast next value = payout_rwa_next of year t
            hs=pd.concat([h[['year','payout_rwa']+X],pd.DataFrame([row[['year','payout_rwa']+X]])]).sort_values('year')
            if len(hs)>=7:
                try:
                    yv=hs.payout_rwa.values.astype(float); ex=hs[X].values.astype(float)
                    m=SARIMAX(yv[1:],exog=ex[:-1],order=(1,0,0),trend='c').fit(disp=False)
                    pr[k]=m.get_forecast(1,exog=ex[-1:]).predicted_mean[0]; nsx+=1
                except Exception: pass
        r[nm]=pr; r[nm+'_n']=nsx
    rows.append(r)
models=['ols_dd','ols_pt','ols_pt_dd','ardl_dd','ardl_pt','ardl_pt_dd','sarimax_pt','sarimax_pt_dd']
y=np.concatenate([r['y'] for r in rows])
res={m:float(np.sqrt(np.mean((np.concatenate([r[m] for r in rows])-y)**2))) for m in models}
res['n']=int(len(y)); res['n_sarimax_firm_fits']=int(sum(r['sarimax_pt_n'] for r in rows))
res['climatology_prev_mean']=float(np.sqrt(np.mean((np.concatenate([np.full(len(r['y']),D[D.year<r['year']].payout_rwa_next.mean()) for r in rows])-y)**2)))
for fam in ['ols','ardl','sarimax']:
    res[f'{fam}_dd_added_pct']=100*(res[f'{fam}_pt_dd']/res[f'{fam}_pt']-1)
if 'ols_dd' in res: res['ols_pt_added_to_dd_pct']=100*(res['ols_pt_dd']/res['ols_dd']-1); res['ardl_pt_added_to_dd_pct']=100*(res['ardl_pt_dd']/res['ardl_dd']-1)
out['B']=res; print(json.dumps(res,indent=1))
# SCB short walk-forward (not scored)
S=D[D.year>=2021]; sres={}
for t in [2023,2024]:
    tr=S[S.year<t]; te=S[S.year==t]
    for nm,X in {'ols_dd':['drawdown'],'ols_dd_scb':['drawdown','scb'],'ardl_dd':['payout_rwa','drawdown'],'ardl_dd_scb':['payout_rwa','drawdown','scb']}.items():
        sres.setdefault(nm,[]).extend(list(ols_pred(tr,te,X).values-te.payout_rwa_next.values))
out['B_scb_unscored']={k:dict(n=len(v),rmse=float(np.sqrt(np.mean(np.square(v))))) for k,v in sres.items()}
print(out['B_scb_unscored'])
# timing
from pidcore import mmi_from_cov, idep_from_corr, copnorm
from gpid.mmi_pid import mmi_pid
import dit
from dit.pid import PID_BROJA, PID_CCS
z=np.random.default_rng(0).standard_normal((360,3)); C=np.cov(z.T)
def tm(f,reps):
    t0=time.perf_counter()
    for _ in range(reps): f()
    return (time.perf_counter()-t0)/reps
R=np.corrcoef(z.T)
tim=dict(ours_mmi_us=1e6*tm(lambda: mmi_from_cov(C,360),2000),ours_idep_us=1e6*tm(lambda: idep_from_corr(R[1,2],R[0,1],R[0,2]),2000),
         gpid_mmi_us=1e6*tm(lambda: mmi_pid(C,1,1,1),500),copnorm_360x3_us=1e6*tm(lambda: [copnorm(z[:,i]) for i in range(3)],500))
# dit on tercile-discretized data
q=np.column_stack([np.digitize(z[:,i],np.quantile(z[:,i],[1/3,2/3])) for i in range(3)])
from collections import Counter
cnt=Counter(''.join(map(str,r)) for r in q[:,[1,2,0]]); dd=dit.Distribution(list(cnt),[v/360 for v in cnt.values()])
tim['dit_broja_terciles_ms']=1e3*tm(lambda: PID_BROJA(dd,[[0],[1]],[2]),3); tim['dit_ccs_terciles_ms']=1e3*tm(lambda: PID_CCS(dd,[[0],[1]],[2]),3)
out['timing']=tim; print(tim)
json.dump(out,open('pid/bench.json','w'),indent=1,default=float)
