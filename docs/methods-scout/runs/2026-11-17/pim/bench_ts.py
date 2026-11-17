# 2026-11-17: OLS, pooled ARDL(1,0) and per-firm SARIMAX(1,0,0)+exog, held-out years 2016-2025; concordance metric
# and firm-block bootstrap; "promising" rule exactly as in PREREG.md section A. Aggregates only are saved for publishing.
import warnings, json, numpy as np, pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
warnings.filterwarnings('ignore')
B=pd.read_csv('bench_panel.csv').sort_values(['id_rssd','year'])
X=['drawdown','income_pretax_net_rate']
rows=[]
def ols(Xtr,ytr,Xte):
    A=np.column_stack([np.ones(len(Xtr)),Xtr]); b=np.linalg.lstsq(A,ytr,rcond=None)[0]
    return np.column_stack([np.ones(len(Xte)),Xte])@b, b
for y in ['payout_rwa','payout_ni']:
    yp=y+'_prev'
    D=B.dropna(subset=[y]+X+[yp])
    for T in range(2016,2026):
        tr=D[D.year<T]; te=D[D.year==T]
        if len(te)<2: continue
        p,_=ols(tr[X].values,tr[y].values,te[X].values)
        rows+= [dict(model='OLS',outcome=y,year=T,id_rssd=i,y=v,score=s) for i,v,s in zip(te.id_rssd,te[y],p)]
        p,_=ols(tr[[yp]+X].values,tr[y].values,te[[yp]+X].values)
        rows+= [dict(model='ARDL',outcome=y,year=T,id_rssd=i,y=v,score=s) for i,v,s in zip(te.id_rssd,te[y],p)]
        for _,r in te.iterrows():
            h=tr[tr.id_rssd==r.id_rssd]
            if len(h)<5: continue
            try:
                m=SARIMAX(h[y].values,exog=h[X].values,order=(1,0,0),trend='c').fit(disp=False)
                f=float(m.forecast(1,exog=r[X].values.reshape(1,-1).astype(float))[0])
            except Exception as e:
                continue
            rows.append(dict(model='SARIMAX',outcome=y,year=T,id_rssd=r.id_rssd,y=r[y],score=f))
R=pd.concat([pd.DataFrame(rows),pd.read_csv('pred_pim.csv')])
R.to_csv('pred_all_LOCAL_ONLY.csv',index=False)

def conc(df):
    num=den=0.0
    for _,g in df.groupby('year'):
        yv=g.y.values; s=g.score.values
        dy=np.sign(yv[:,None]-yv[None,:]); ds=np.sign(s[:,None]-s[None,:])
        iu=np.triu_indices(len(yv),1); dy=dy[iu]; ds=ds[iu]; k=dy!=0
        num+=np.sum((dy[k]==ds[k]))+0.5*np.sum(ds[k]==0); den+=k.sum()
    return num/den if den else np.nan, int(den)
rng=np.random.default_rng(20261117)
out={'models':{}, 'diffs':{}}
for y in ['payout_rwa','payout_ni']:
    sub=R[R.outcome==y]
    sar_keys=set(map(tuple,sub[sub.model=='SARIMAX'][['year','id_rssd']].values))
    for mdl in ['OLS','PIM_static','ARDL','PIM_dyn','SARIMAX']:
        g=sub[sub.model==mdl]
        c,n=conc(g); gs=g[[ (a,b) in sar_keys for a,b in zip(g.year,g.id_rssd)]]; cs,ns=conc(gs)
        mae=float(np.mean(np.abs(g.y-g.score))) if not mdl.startswith('PIM') else None
        py={int(t):round(conc(gg)[0],4) for t,gg in g.groupby('year')}
        out['models'][f'{y}|{mdl}']=dict(C_all=c,pairs_all=n,n_rows=len(g),C_sarimax_subset=cs,pairs_subset=ns,n_rows_subset=len(gs),mae=mae,C_by_year=py)
    firms=sub.id_rssd.unique()
    def diff(a,b,subset):
        ga=sub[sub.model==a]; gb=sub[sub.model==b]
        if subset: ga=ga[[ (x,z) in sar_keys for x,z in zip(ga.year,ga.id_rssd)]]; gb=gb[[ (x,z) in sar_keys for x,z in zip(gb.year,gb.id_rssd)]]
        d0=conc(ga)[0]-conc(gb)[0]; bs=[]
        for _ in range(999):
            s=rng.choice(firms,len(firms),replace=True)
            def rs(g):
                parts=[]
                for k,f in enumerate(s):
                    q=g[g.id_rssd==f].copy(); q['id_rssd']=k; parts.append(q)
                return pd.concat(parts)
            bs.append(conc(rs(ga))[0]-conc(rs(gb))[0])
        return dict(diff=d0,lo90=float(np.nanpercentile(bs,5)),hi90=float(np.nanpercentile(bs,95)))
    out['diffs'][f'{y}|PIM_dyn-ARDL']=diff('PIM_dyn','ARDL',False)
    out['diffs'][f'{y}|PIM_dyn-SARIMAX(subset)']=diff('PIM_dyn','SARIMAX',True)
    out['diffs'][f'{y}|PIM_static-OLS']=diff('PIM_static','OLS',False)
d=out['diffs']; M=out['models']
a=(d['payout_rwa|PIM_dyn-ARDL']['diff']>=-0.02) and (d['payout_rwa|PIM_dyn-SARIMAX(subset)']['diff']>=-0.02)
b=(M['payout_ni|PIM_dyn']['C_all']>=M['payout_ni|ARDL']['C_all']) and (M['payout_ni|PIM_dyn']['C_sarimax_subset']>=M['payout_ni|SARIMAX']['C_sarimax_subset'])
out['promising']=dict(a=bool(a),b=bool(b),promising=bool(a and b))
json.dump(out,open('bench_results.json','w'),indent=1,default=float)
for k,v in M.items(): print(k, {kk:(round(vv,4) if isinstance(vv,float) else vv) for kk,vv in v.items() if kk!='C_by_year'})
for k,v in d.items(): print(k,{kk:round(vv,4) for kk,vv in v.items()})
print(out['promising'])
