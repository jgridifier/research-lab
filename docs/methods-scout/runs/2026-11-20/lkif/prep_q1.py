import pandas as pd, numpy as np, json
W=pd.read_csv('/workspace/ms-1114/q1/weekly.csv',parse_dates=['date']).set_index('date').asfreq('W-WED')
E=pd.read_csv('/workspace/rl-scout-1120/docs/methods-scout/runs/2026-11-17/eca/q1_weekly.csv',parse_dates=['date']).set_index('date')
v=pd.read_csv('/workspace/research/drive_inv/data/VIXCLS.csv'); v.columns=['date','vix']; v['date']=pd.to_datetime(v.date); v['vix']=pd.to_numeric(v.vix,errors='coerce')
v=v.set_index('date').vix.dropna().resample('W-WED').last()
gaps={c:int(W[c].isna().sum()) for c in ['fails_fin_ust','dvp_out','tri_tvol','spread_bp']}
for c in ['fails_fin_ust','dvp_out','tri_tvol','spread_bp']: W[c]=W[c].interpolate(limit=1,limit_area='inside')
X=pd.DataFrame(index=W.index)
X['dl_fails']=np.log(W.fails_fin_ust).diff(); X['d_spread']=W.spread_bp.diff(); X['dl_dvp']=np.log(W.dvp_out).diff()
X['dl_tri']=np.log(W.tri_tvol).diff(); X['d_vix']=v.reindex(X.index).diff()
X=X.join(E[['d_lev']],how='left')
X['l_fails']=np.log(W.fails_fin_ust)
X=X[X.index>='2018-05-16']
X.to_csv('q1_weekly_lkif.csv')
full=X.drop(columns='l_fails').dropna()
print(len(full),full.index.min().date(),full.index.max().date(),gaps)
nolev=X.drop(columns=['d_lev','l_fails']).dropna(); print('nolev',len(nolev),nolev.index.min().date(),nolev.index.max().date())
json.dump(dict(n_full=len(full),start=str(full.index.min().date()),end=str(full.index.max().date()),n_nolev=len(nolev),end_nolev=str(nolev.index.max().date()),gaps_before_interp=gaps),open('prep_meta.json','w'))
# monthly
M=pd.read_csv('/workspace/ms-1114/q1/monthly.csv'); M['period']=pd.PeriodIndex(M.period,freq='M'); M=M.set_index('period')
Mm=pd.DataFrame(index=M.index)
Mm['dl_pb']=np.log(M['Secured_Prime Broker']).diff(); Mm['dl_rr']=np.log(M['Secured_Reverse Repo']).diff(); Mm['dl_tot']=np.log(M['Total_Total']).diff()
Mm['dl_fails']=np.log(M.fails_fin_ust).diff(); Mm['d_spread']=M.spread_bp.diff(); Mm['dl_dvp']=np.log(M.dvp_out).diff()
Mm=Mm.dropna(); Mm.to_csv('q1_monthly_lkif.csv'); print('monthly',len(Mm),Mm.index.min(),Mm.index.max())
