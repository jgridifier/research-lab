# Standard tools on the same weekly data: cross-correlation, ARDL (BIC), SARIMAX(1,0,1)+X, walk-forward 1-step
# with and without the pre-registered limb-asymmetry term. Low priority (forecasting); reported either way.
import numpy as np, pandas as pd, json, warnings
warnings.filterwarnings('ignore')
from statsmodels.tsa.ardl import ARDL, ardl_select_order
from statsmodels.tsa.statespace.sarimax import SARIMAX
import statsmodels.api as sm
from scipy import stats
W=pd.read_csv('q1_weekly_hyst.csv',parse_dates=['date']).set_index('date')
W=W[['fails_fin_ust','spread_bp']].dropna(); W.index.freq='W-WED'
y=np.log(W.fails_fin_ust); x=W.spread_bp
out={}
# cross-correlation of weekly changes, lags -4..4 (positive k: spread change leads fails change by k weeks)
dy=y.diff(); dx=x.diff(); out['xcorr']={k:round(float(dy.corr(dx.shift(k))),3) for k in range(-4,5)}
out['xcorr_levels']={k:round(float(y.corr(x.shift(k))),3) for k in range(-4,5)}
# ARDL full sample, both directions
sel=ardl_select_order(y,4,pd.DataFrame({'spread':x}),4,ic='bic',trend='c')
r=sel.model.fit(); out['ardl_fails_on_spread']={'order':str(sel.model.ardl_order),'params':{k:round(float(v),4) for k,v in r.params.items()},'pvalues':{k:round(float(v),4) for k,v in r.pvalues.items()}}
sel2=ardl_select_order(x,4,pd.DataFrame({'lfails':y}),4,ic='bic',trend='c')
r2=sel2.model.fit(); out['ardl_spread_on_fails']={'order':str(sel2.model.ardl_order),'params':{k:round(float(v),4) for k,v in r2.params.items()},'pvalues':{k:round(float(v),4) for k,v in r2.pvalues.items()}}
# walk-forward: train to 2022-06-29, 1-step forecasts of log fails
split=W.index.get_loc(pd.Timestamp('2022-06-29'))+1
med8=y.shift(1).rolling(8).median()
rising=((y.shift(1)>med8) & (y.shift(1)>y.shift(2))).astype(float)   # causal: known at t-1
def design(i,limb):
    d=pd.DataFrame({'c':1.0,'y1':y.shift(1),'y2':y.shift(2),'x1':x.shift(1),'x2':x.shift(2)},index=y.index)
    if limb: d['x1r']=x.shift(1)*rising; d['r']=rising
    return d
res={}
for nm,limb in [('ardl_lag1',False),('ardl_lag1_plus_limb',True)]:
    d=design(0,limb); errs=[]
    for t in range(split,len(y)):
        tr=d.iloc[:t].dropna(); yt=y.loc[tr.index]
        b=np.linalg.lstsq(tr.values,yt.values,rcond=None)[0]
        errs.append(float(y.iloc[t]-d.iloc[t].values@b))
    res[nm]=np.array(errs)
# SARIMAX(1,0,1) with exog spread_{t-1}, refit every 13 weeks, 1-step with filtering
e=[]; X1=x.shift(1).bfill()
for t in range(split,len(y)):
    if (t-split)%13==0:
        m=SARIMAX(y.iloc[:t],exog=X1.iloc[:t],order=(1,0,1),trend='c').fit(disp=False); prm=m.params
    mm=SARIMAX(y.iloc[:t+1],exog=X1.iloc[:t+1],order=(1,0,1),trend='c').filter(prm)
    e.append(float(y.iloc[t]-mm.predict(start=t,end=t).iloc[0]))
res['sarimax101_x']=np.array(e)
# naive random walk
res['random_walk']=(y-y.shift(1)).iloc[split:].values
rm={k:round(float(np.sqrt(np.mean(v**2))),4) for k,v in res.items()}
def dm(e1,e2,h=1):
    d=e1**2-e2**2; n=len(d); g0=np.var(d,ddof=0); st=d.mean()/np.sqrt(g0/n); return float(2*(1-stats.norm.cdf(abs(st)))),float(st)
out['walk_forward']={'train_end':'2022-06-29','n_test':int(len(y)-split),'test_start':str(y.index[split].date()),'test_end':str(y.index[-1].date()),'rmse':rm,
  'limb_vs_ardl_rmse_change_pct':round(100*(rm['ardl_lag1_plus_limb']/rm['ardl_lag1']-1),2),'dm_limb_vs_ardl':dm(res['ardl_lag1_plus_limb'],res['ardl_lag1']),
  'sarimax_vs_ardl_rmse_change_pct':round(100*(rm['sarimax101_x']/rm['ardl_lag1']-1),2)}
# full-sample OLS of the limb term (descriptive): does the fails-spread relation differ on rising vs other weeks?
d=design(0,True).dropna(); o=sm.OLS(y.loc[d.index],d).fit(cov_type='HAC',cov_kwds={'maxlags':4})
out['ols_limb_full']={'x1r':round(float(o.params['x1r']),4),'p':round(float(o.pvalues['x1r']),4)}
json.dump(out,open('q1_baselines.json','w'),indent=1); print(json.dumps(out,indent=1))
