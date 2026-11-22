import pandas as pd, numpy as np, json, warnings
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
warnings.filterwarnings('ignore'); Z90=stats.norm.ppf(0.9); out={}
def pinball(y,q,tau=0.9): d=y-q; return float(np.mean(np.maximum(tau*d,(tau-1)*d)))
for f in ['Corning_mock','MorganStanley_mock']:
    X=pd.read_csv(f'{f}_x.csv'); X['lx']=np.log(X.x); P=pd.read_csv(f'{f}_programs_regions.csv',index_col=0)
    S=pd.read_csv(f'{f}_site_wf.csv').set_index('program_id'); ly=X.fiscal_year.max()
    tr=X[X.fiscal_year<ly]; te=X[X.fiscal_year==ly].set_index('program_id').lx
    ids=[i for i in S.index if i in te.index]; y=te[ids]
    g=tr.groupby('program_id').lx; m=g.mean(); s=g.std(ddof=1)
    B=pd.DataFrame(index=ids)
    B['at-site lognormal']=(m+Z90*s)[ids]
    B['RFA index-flood, regions B']=np.log(S.loc[ids,'q90_reg_B'])
    B['RFA index-flood, regions A (function)']=np.log(S.loc[ids,'q90_reg_A'])
    dev=tr.lx-tr.program_id.map(m); A=tr.program_id.map(P.reg_A)
    sp=np.sqrt((dev**2).groupby(A).sum()/(tr.groupby(A).size()-tr.groupby(A).program_id.nunique()))
    B['category-pooled lognormal (function)']=(m+Z90*P.reg_A.map(sp))[ids]
    # OLS pooled on stated features
    F=pd.get_dummies(P[['stated_discretionary','band','stated_cost_type','stated_intent']].astype(str),drop_first=True).astype(float)
    Xtr=sm.add_constant(F.loc[tr.program_id].values); ols=sm.OLS(tr.lx.values,Xtr).fit(); res=pd.Series(tr.lx.values-ols.predict(Xtr),index=tr.index)
    rq=res.groupby(tr.program_id.map(P.reg_B)).quantile(0.9)
    B['OLS on stated features']=ols.predict(sm.add_constant(F.loc[ids].values,has_constant='add'))+P.loc[ids,'reg_B'].map(rq).values
    # pooled ARDL(1) by region B
    tr2=tr.sort_values(['program_id','fiscal_year']).copy(); tr2['lag']=tr2.groupby('program_id').lx.shift(); tr2=tr2.dropna(); tr2['reg']=tr2.program_id.map(P.reg_B)
    last=tr.sort_values('fiscal_year').groupby('program_id').lx.last()
    ard=pd.Series(index=ids,dtype=float)
    for rname,d in tr2.groupby('reg'):
        fit=sm.OLS(d.lx.values,sm.add_constant(d.lag.values)).fit(); q=np.quantile(fit.resid,0.9)
        sel=[i for i in ids if P.loc[i,'reg_B']==rname]; ard[sel]=fit.params[0]+fit.params[1]*last[sel].values+q
    B['pooled ARDL(1), regions B']=ard
    # per-program SARIMAX(1,0,0)
    sar=pd.Series(index=ids,dtype=float); nfb=0
    for i in ids:
        v=tr.lx[tr.program_id==i].values
        try:
            r=SARIMAX(v,order=(1,0,0),trend='c').fit(disp=False); fc=r.get_forecast(1); u=fc.conf_int(alpha=0.2)[0,1]
            if not np.isfinite(u) or not r.mle_retvals.get('converged',True): raise ValueError
            sar[i]=u
        except Exception:
            sar[i]=m[i]+Z90*s[i]; nfb+=1
    B['SARIMAX(1,0,0) per program']=sar
    out[f]=dict(n=len(ids),test_year=int(ly),sarimax_fallbacks=nfb,
                coverage={k:round(float((y<=B[k]).mean()),3) for k in B},pinball={k:round(pinball(y.values,B[k].values),5) for k in B})
    out[f]['pinball_ratio_vs_at_site']={k:round(out[f]['pinball'][k]/out[f]['pinball']['at-site lognormal'],3) for k in B}
json.dump(out,open('wf_q2.json','w'),indent=1); print(json.dumps(out,indent=1))
