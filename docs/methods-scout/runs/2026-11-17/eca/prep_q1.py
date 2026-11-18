# Weekly Q1 panel for ECA: lab copies of public NY Fed fails, OFR repo (11-14 weekly.csv) + CFTC TFF (harmonized panel).
import pandas as pd, numpy as np
D='/workspace/research/drive_inv/data/'
W=pd.read_csv('/workspace/ms-1114/q1/weekly.csv',parse_dates=['date']).set_index('date').asfreq('W-WED')
t=pd.read_csv(D+'tff_panel_harmonized.csv.gz',usecols=['contract_harmonized','FutOnly_or_Combined','report_date','Lev_Money_Positions_Long_All','Lev_Money_Positions_Short_All'])
t=t[t.FutOnly_or_Combined=='FutOnly']
core=['UST 2Y NOTE - CHICAGO BOARD OF TRADE','UST 5Y NOTE - CHICAGO BOARD OF TRADE','UST 10Y NOTE - CHICAGO BOARD OF TRADE']
t=t[t.contract_harmonized.isin(core)].copy(); t['net_short']=t.Lev_Money_Positions_Short_All-t.Lev_Money_Positions_Long_All
p=t.pivot_table(index='report_date',columns='contract_harmonized',values='net_short',aggfunc='sum')
lev=p.sum(axis=1,min_count=3)/1e3; lev.index=pd.to_datetime(lev.index)+pd.offsets.Week(weekday=2); lev=lev.groupby(level=0).last()
lev=lev[lev.index<='2025-12-31']
W=W.join(lev.rename('lev_net_k'),how='left')
gaps={c:int(W[c].isna().sum()) for c in ['fails_fin_ust','dvp_out','spread_bp']}
W[['fails_fin_ust','dvp_out','spread_bp']]=W[['fails_fin_ust','dvp_out','spread_bp']].interpolate(limit=1,limit_area='inside')
W['lev_net_k']=W.lev_net_k.interpolate(limit=1,limit_area='inside')
X=pd.DataFrame(index=W.index)
X['dl_fails']=np.log(W.fails_fin_ust).diff(); X['d_spread']=W.spread_bp.diff(); X['dl_dvp']=np.log(W.dvp_out).diff(); X['d_lev']=W.lev_net_k.diff()
X['fails']=W.fails_fin_ust; X['spread']=W.spread_bp
X=X[X.index>='2018-05-16']
X.to_csv('q1_weekly.csv')
print(len(X),X.index.min().date(),X.index.max().date(),'missing before interp',gaps)
print(X.notna().sum().to_dict()); print(X.describe().T.round(4))
