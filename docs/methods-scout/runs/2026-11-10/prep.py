import pandas as pd, numpy as np
D='/workspace/scout/data/'
def s(name):
    x=pd.read_csv(D+name+'.csv'); x.columns=['date',name]
    x['date']=pd.to_datetime(x['date']); x[name]=pd.to_numeric(x[name],errors='coerce')
    return x.set_index('date')[name].dropna()
ser={n:s(n) for n in ['VIXCLS','T10Y2Y','DGS2','DGS10','MORTGAGE30US','NFCI','STLFSI4']}
ebp=pd.read_csv(D+'ebp_monthly.csv',parse_dates=['date']).set_index('date')
# monthly (month-end mean)
M=pd.DataFrame({k:v.resample('ME').mean() for k,v in ser.items()})
e=ebp[['gz_spread','ebp']].copy(); e.index=e.index+pd.offsets.MonthEnd(0)
M=M.join(e,how='left')
M=M.loc['1990-01-31':]
M['dDGS2_12']=M.DGS2-M.DGS2.shift(12)
M['dMORT_12']=M.MORTGAGE30US-M.MORTGAGE30US.shift(12)
M['dGZ_3']=M.gz_spread-M.gz_spread.shift(3)
M['y_fwd6']=M.gz_spread.shift(-6)-M.gz_spread
M['dGZ']=M.gz_spread.diff(); M['dVIX']=M.VIXCLS.diff(); M['dDGS10']=M.DGS10.diff()
M.index.name='date'
M.to_csv('/workspace/scout/out/monthly_panel.csv')
print(M.dropna(subset=['VIXCLS','gz_spread']).index[[0,-1]], len(M))
# weekly panel for changeforest (Friday)
W=pd.DataFrame({k:v.resample('W-FRI').mean() for k,v in ser.items()}).loc['1994-01-07':]
W=W.ffill(limit=2).dropna()
W.index.name='date'; W.to_csv('/workspace/scout/out/weekly_panel.csv'); print('weekly',W.index[[0,-1]],len(W))
# daily panel
Dd=pd.DataFrame({k:ser[k] for k in ['VIXCLS','T10Y2Y','DGS2','DGS10']}).loc['1990-01-02':].dropna()
Dd.index.name='date'; Dd.to_csv('/workspace/scout/out/daily_panel.csv'); print('daily',Dd.index[[0,-1]],len(Dd))
