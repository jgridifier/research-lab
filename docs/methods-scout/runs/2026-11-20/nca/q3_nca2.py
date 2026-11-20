import numpy as np, pandas as pd, json, sys, warnings
warnings.filterwarnings('ignore'); sys.path.insert(0,'.')
from nca_port import ce_fdh, ceil_at, bottleneck
from q3_nca import perm_within, spurious, d as D
import statsmodels.formula.api as smf, statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
rng=np.random.default_rng(99); out={}
conds=['x_dd','x_pt','x_loss','x_cet1min']
# ---- robustness of the cet1min ceiling
rob={}
for yc in ['payout_rwa','bb_rwa','div_rwa']:
    df=D[['x_cet1min',yc,'year']].dropna()
    cut=df.x_cet1min.quantile(0.98); dft=df[df.x_cet1min<=cut]
    o,pw,_=perm_within(dft,'x_cet1min',yc,1999,rng); rs,sm_,s95,ps=spurious(dft,'x_cet1min',yc,1999,rng)
    rob[f'{yc}|trim_top2pct_x']=dict(n=len(dft),d=o,p_within=pw,spur95=s95,p_spur=ps)
    cuty=df[yc].quantile(0.98); dfy=df[df[yc]<=cuty]
    o,pw,_=perm_within(dfy,'x_cet1min',yc,1999,rng); rs,sm_,s95,ps=spurious(dfy,'x_cet1min',yc,1999,rng)
    rob[f'{yc}|trim_top2pct_y']=dict(n=len(dfy),d=o,p_within=pw,spur95=s95,p_spur=ps)
    loyo=[]
    for yr in sorted(df.year.unique()):
        dl=df[df.year!=yr]; o=ce_fdh(dl.x_cet1min,dl[yc])['d']; rs,sm_,s95,ps=spurious(dl,'x_cet1min',yc,499,rng); loyo.append(dict(drop=int(yr),d=o,spur95=s95,p_spur=ps))
    rob[f'{yc}|loyo']=loyo
    print(yc,{k:v for k,v in rob.items() if k.startswith(yc) and 'loyo' not in k}, 'loyo p_spur max',max(l['p_spur'] for l in loyo),flush=True)
out['robust']=rob
# ---- N3 eras
era={}
for lab,m in {'2013-2019':D.year<=2019,'2020-2025':D.year>=2020}.items():
    for xc in conds:
        df=D.loc[m,[xc,'payout_rwa','year']].dropna(); o,pw,_=perm_within(df,xc,'payout_rwa',1999,rng); rs,sm_,s95,ps=spurious(df,xc,'payout_rwa',999,rng)
        f=ce_fdh(df[xc],df.payout_rwa); med=df.payout_rwa.median()
        era[f'{lab}|{xc}']=dict(n=len(df),d=o,p_within=pw,spearman=rs,spur95=s95,p_spur=ps,bottleneck_at_median_payout=float(bottleneck(f,med)[0]),median_payout=float(med))
        print(lab,xc,{k:round(v,4) if isinstance(v,float) else v for k,v in era[f'{lab}|{xc}'].items()},flush=True)
out['eras']=era
# ---- N2 limiting factor (pooled CE-FDH ceilings per condition)
df=D[conds+['payout_rwa','year','scb','x_scb']].copy()
fits={xc:ce_fdh(df[xc],df.payout_rwa) for xc in conds}
CE=np.column_stack([ceil_at(fits[xc],df[xc].values) for xc in conds])
mn=CE.min(1); lim=[]
for r in range(len(df)):
    w=np.where(np.isclose(CE[r],mn[r]))[0]; lim.append(conds[w[0]] if len(w)==1 else 'tie')
df['limit']=lim; df['headroom']=mn-df.payout_rwa
share=df.limit.value_counts(normalize=True).to_dict(); out['N2_share']=share
out['N2_by_year']=pd.crosstab(df.year,df.limit,normalize='index').round(3).to_dict()
out['N2_near_ceiling']=float((df.headroom<=0.25*df.payout_rwa.std()).mean())
print('limit share',share)
# 2021-2025 with SCB
d5=df[df.year>=2021].dropna(subset=['x_scb'])
o,pw,_=perm_within(d5,'x_scb','payout_rwa',1999,rng); rs,sm_,s95,ps=spurious(d5,'x_scb','payout_rwa',1999,rng)
out['N2_scb']=dict(n=len(d5),d=o,p_within=pw,spearman=rs,spur95=s95,p_spur=ps)
c5=conds+['x_scb']; f5={xc:ce_fdh(d5[xc],d5.payout_rwa) for xc in c5}
CE5=np.column_stack([ceil_at(f5[xc],d5[xc].values) for xc in c5]); mn5=CE5.min(1); lim5=[]
for r in range(len(d5)):
    w=np.where(np.isclose(CE5[r],mn5[r]))[0]; lim5.append(c5[w[0]] if len(w)==1 else 'tie')
out['N2_share_2021_25']=pd.Series(lim5).value_counts(normalize=True).to_dict()
for xc in c5:
    o2,pw2,_=perm_within(d5,xc,'payout_rwa',999,rng); rs2,_,s952,ps2=spurious(d5,xc,'payout_rwa',999,rng)
    out[f'N2_2021_25|{xc}']=dict(d=o2,p_within=pw2,spearman=rs2,spur95=s952,p_spur=ps2)
print('scb',out['N2_scb'],out['N2_share_2021_25'],flush=True)
df.to_csv('N2_limits.csv',index=False)
# ---- N4 walk-forward upper envelope on x_cet1min (best N1 condition)
P=D.sort_values(['id_rssd','year']).copy(); P['lag']=P.groupby('id_rssd').payout_rwa.shift(1)
rows=[]
for ty in range(2015,2026):
    tr=P[P.year<ty]; te=P[P.year==ty]
    f=ce_fdh(tr.x_cet1min,tr.payout_rwa); c_te=ceil_at(f,te.x_cet1min.values)
    q=smf.quantreg('payout_rwa~x_cet1min',tr).fit(q=0.95); qb=q.predict(te)
    o=smf.ols('payout_rwa~x_cet1min',tr).fit(); ob=o.predict(te)+1.645*np.sqrt(o.scale)
    trl=tr.dropna(subset=['lag']); a=smf.ols('payout_rwa~lag+x_cet1min',trl).fit()
    tel=te.copy(); ab=np.full(len(te),np.nan); okm=tel.lag.notna().values
    if okm.any():
        pr=a.get_prediction(tel[okm]).summary_frame(alpha=0.10); ab[okm]=pr.obs_ci_upper.values
    sb=ab.copy()
    for k,(rid,row) in enumerate(te.iterrows()):
        h=tr[tr.id_rssd==row.id_rssd].sort_values('year')
        if len(h)>=8:
            try:
                m=SARIMAX(h.payout_rwa.values,exog=h[['x_cet1min']].values,order=(1,0,0),trend='c').fit(disp=False)
                fc=m.get_forecast(1,exog=[[row.x_cet1min]]); sb[k]=fc.conf_int(alpha=0.10)[0,1]
            except Exception: pass
    for k in range(len(te)):
        rows.append(dict(year=ty,y=te.payout_rwa.values[k],ceil=c_te[k],qr95=qb.values[k],ols=ob.values[k],ardl=ab[k],sarimax=sb[k]))
W=pd.DataFrame(rows); W.to_csv('N4_walkforward.csv',index=False)
res={}
for b in ['ceil','qr95','ols','ardl','sarimax']:
    w=W.dropna(subset=[b]); res[b]=dict(n=len(w),viol=float((w.y>w[b]).mean()),headroom_mean=float((w[b]-w.y).mean()),headroom_median=float((w[b]-w.y).median()))
out['N4']=res; print(res)
json.dump(out,open('N2_N3_N4.json','w'),indent=1,default=float)
