import pandas as pd, numpy as np
D='/workspace/research/drive_inv/data/'
W=pd.read_csv('/workspace/ms-1114/q1/weekly.csv',parse_dates=['date']).set_index('date').asfreq('W-WED')
t=pd.read_csv(D+'tff_panel_harmonized.csv.gz',usecols=['contract_harmonized','FutOnly_or_Combined','report_date','Lev_Money_Positions_Long_All','Lev_Money_Positions_Short_All','Open_Interest_All'])
print(t.FutOnly_or_Combined.unique())
t=t[t.FutOnly_or_Combined=='FutOnly']
core=['UST 2Y NOTE - CHICAGO BOARD OF TRADE','UST 5Y NOTE - CHICAGO BOARD OF TRADE','UST 10Y NOTE - CHICAGO BOARD OF TRADE']
t=t[t.contract_harmonized.isin(core)].copy()
t['net_short']=t.Lev_Money_Positions_Short_All-t.Lev_Money_Positions_Long_All
p=t.pivot_table(index='report_date',columns='contract_harmonized',values='net_short',aggfunc='sum')
print(p.notna().sum())
lev=p.sum(axis=1,min_count=3)/1e3  # thousand contracts, 2Y+5Y+10Y unweighted
lev.index=pd.to_datetime(lev.index)
# Tuesday report -> following Wednesday week label
lev.index=lev.index+pd.offsets.Week(weekday=2)
lev=lev.groupby(level=0).last()
W=W.join(lev.rename('lev_net_k'),how='left')
W=W.interpolate(limit=1,limit_area='inside')
X=pd.DataFrame(index=W.index)
X['d_lev']=W.lev_net_k.diff()            # weekly change in lev-fund net short (k contracts)
X['dl_fails']=np.log(W.fails_fin_ust).diff()
X['dl_dvp']=np.log(W.dvp_out).diff()
X['d_spread']=W.spread_bp.diff()
X['lev']=W.lev_net_k; X['l_fails']=np.log(W.fails_fin_ust); X['spread']=W.spread_bp
X=X.dropna(); X=X[X.index>='2019-01-16']
print(len(X),X.index.min().date(),X.index.max().date())
print(X.describe().T.round(3))
X.to_csv('panel.csv')
