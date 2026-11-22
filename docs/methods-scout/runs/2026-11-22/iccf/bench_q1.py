import pandas as pd, numpy as np, json, warnings
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
from scipy import stats
import iccf_core as ic
from q1_iccf import get, detrend, LMIN, LMAX, STEP
warnings.filterwarnings('ignore')
def monthly(k):
    d=get(k); return d.groupby(d.date.dt.to_period('M')).y.mean()
def run(target,driver,start='2019-01',tag=''):
    yl=monthly(target); xl=monthly(driver); idx=yl.index.intersection(xl.index); y=yl[idx].diff(); x=xl[idx].diff()
    df=pd.DataFrame({'y':y,'x':x}).dropna(); test=df.index[df.index>=pd.Period(start,'M')]
    preds={m:[] for m in ['zero change','OLS on lagged market','ARDL own lags','ARDL + ICCF-lag market','SARIMAX(1,0,1)','SARIMAX(1,0,1)+X ICCF lag']}; ks=[]; k=1; p_own=1
    dT=get(target); dD=get(driver)
    for t in test:
        tr=df[df.index<t]
        if t.month==1 or t==test[0]:
            cut=t.to_timestamp()
            a=dT[dT.date<cut]; b=dD[dD.date<cut]; lo=max(a.date.min(),b.date.min()); a=a[a.date>=lo]; b=b[b.date>=lo]
            # ICCF of driver (lc1) vs target (lc2): positive tau = target lags driver
            _,tc,_,_=ic.peakcent(b.t.values,detrend(b.t.values,b.y.values),a.t.values,detrend(a.t.values,a.y.values)*np.sign(ic.rstar(b.t.values,detrend(b.t.values,b.y.values),a.t.values,detrend(a.t.values,a.y.values),LMIN,LMAX,STEP)[0]),LMIN,LMAX,STEP)
            k=max(1,int(round(tc/30.4))) if np.isfinite(tc) else 1
            bics=[]
            for p in (1,2,3):
                Z=pd.concat([tr.y.shift(i) for i in range(1,p+1)],axis=1).iloc[3:]; bics.append(sm.OLS(tr.y.iloc[3:],sm.add_constant(Z)).fit().bic)
            p_own=int(np.argmin(bics))+1
        ks.append(k)
        full=df[df.index<=t]
        L=pd.concat([full.y.shift(i).rename(f'y{i}') for i in range(1,p_own+1)]+[full.x.shift(k).rename('xk')],axis=1)
        Ltr=L[L.index<t].dropna(); ytr=full.y[Ltr.index]; Lt=L.loc[[t]]
        preds['zero change'].append(0.0)
        preds['OLS on lagged market'].append(float(sm.OLS(ytr,sm.add_constant(Ltr[['xk']])).fit().predict(sm.add_constant(Lt[['xk']],has_constant="add")).iloc[0]))
        own=[c for c in L.columns if c!='xk']
        preds['ARDL own lags'].append(float(sm.OLS(ytr,sm.add_constant(Ltr[own])).fit().predict(sm.add_constant(Lt[own],has_constant="add")).iloc[0]))
        preds['ARDL + ICCF-lag market'].append(float(sm.OLS(ytr,sm.add_constant(Ltr)).fit().predict(sm.add_constant(Lt,has_constant="add")).iloc[0]))
        preds['SARIMAX(1,0,1)'].append(float(SARIMAX(tr.y.values,order=(1,0,1),trend='c').fit(disp=False).forecast(1)[0]))
        ex=full.x.shift(k); m=ex.notna()&(ex.index<t)
        r=SARIMAX(tr.y[m[m].index].values,exog=ex[m].values,order=(1,0,1),trend='c').fit(disp=False)
        preds['SARIMAX(1,0,1)+X ICCF lag'].append(float(r.forecast(1,exog=[[ex[t]]])[0]))
    yt=df.y[test].values; E={m:yt-np.array(v) for m,v in preds.items()}
    rmse={m:round(float(np.sqrt(np.mean(e**2))),5) for m,e in E.items()}
    d=E['ARDL + ICCF-lag market']**2-E['ARDL own lags']**2; dm=float(d.mean()/(d.std(ddof=1)/np.sqrt(len(d)))); p=float(2*stats.t.sf(abs(dm),len(d)-1))
    return dict(target=target,driver=driver,n_test=len(test),first=str(test[0]),last=str(test[-1]),rmse=rmse,gain_vs_ardl_pct=round(100*(1-rmse['ARDL + ICCF-lag market']/rmse['ARDL own lags']),2),dm_stat=round(dm,3),dm_p=round(p,3),k_used=sorted(set(ks)))
out={'B_prereg (PB target, fails driver)':run('pb','fails'),'B_exploratory (DVP target, PF reverse repo driver; post hoc; test from 2021-01 so training has >= 31 months)':run('dvp','rr',start='2021-01')}
json.dump(out,open('B_bench.json','w'),indent=1); print(json.dumps(out,indent=1))
