# Public aggregates (lab copies on the box) -> irregular "light curves": time in days since 2013-01-01, value = log level (spread: bp).
import pandas as pd, numpy as np, json
D='/workspace/research/drive_inv/data/'; O=pd.Timestamp('2013-01-01'); END='2025-12-31'
M=pd.read_csv('/workspace/ms-1114/q1/monthly.csv'); M['date']=pd.PeriodIndex(M.period,freq='M').to_timestamp(how='end').normalize()
f=pd.read_csv(D+'fails_weekly.csv',parse_dates=['date']); fails=f[f.keyid=='PDFTD-USTET'].set_index('date').value_usd_mm.sort_index()
r=pd.read_csv(D+'cleared_repo_daily.csv.gz',parse_dates=['date'])
tri=r[r.mnemonic.isin(['REPO-TRI_TV_TOT-F','REPO-TRI_TV_TOT-P'])].pivot_table(index='date',columns='mnemonic',values='value')
tri=tri['REPO-TRI_TV_TOT-F'].combine_first(tri['REPO-TRI_TV_TOT-P']); tri_w=tri.resample('W-WED').mean().dropna()
W=pd.read_csv('/workspace/ms-1114/q1/weekly.csv',parse_dates=['date']).set_index('date')
series={'pb':(M.set_index('date')['Secured_Prime Broker'],'log'),'rr':(M.set_index('date')['Secured_Reverse Repo'],'log'),
        'fails':(fails,'log'),'tri':(tri_w,'log'),'dvp':(W.dvp_out.dropna(),'log'),'spread':(W.spread_bp.dropna(),'lev')}
meta={}; out=[]
for k,(s,tr) in series.items():
    s=s[(s.index<=END)].dropna(); s=s[s>0] if tr=='log' else s
    v=np.log(s.values) if tr=='log' else s.values.astype(float)
    t=(s.index-O).days.values.astype(float)
    out.append(pd.DataFrame({'series':k,'date':s.index,'t':t,'y':v}))
    meta[k]=dict(n=len(s),start=str(s.index.min().date()),end=str(s.index.max().date()),transform=tr,median_gap_days=float(np.median(np.diff(t))))
pd.concat(out).to_csv('q1_lightcurves.csv',index=False); json.dump(meta,open('prep_meta.json','w'),indent=1); print(json.dumps(meta,indent=1))
