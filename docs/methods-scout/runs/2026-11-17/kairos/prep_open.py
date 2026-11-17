# 2026-11-17 kairos refresh (#60): monthly compositions from the lab's public copies. PREREG.md section B.
import pandas as pd, numpy as np
DD='/workspace/research/drive_inv/data/'
out={}
# O1 venue x tenor: the 11-15 table, unchanged
out['O1_venue_tenor']=pd.read_csv('/workspace/rl-1117/docs/methods-scout/runs/2026-11-15/kairos/mix_monthly.csv',index_col=0)
# O2 tri-party collateral (TRIV1 transaction volume by collateral)
r=pd.read_csv(DD+'cleared_repo_daily.csv.gz',parse_dates=['date']); r['m']=r.mnemonic.str.replace(r'-[FP]$','',regex=True)
r=r.sort_values('vintage').drop_duplicates(['m','date'],keep='last'); P=r.pivot_table(index='date',columns='m',values='value',aggfunc='last')
O2=P[['REPO-TRIV1_TV_T','REPO-TRIV1_TV_AG','REPO-TRIV1_TV_CORD','REPO-TRIV1_TV_O']].resample('ME').mean()
O2.columns=['Treasury','Agency','CorpDebt','Other']; O2.index=O2.index.strftime('%Y-%m'); out['O2_triparty_collateral']=O2.loc[:'2026-09']
# O3 CFTC TFF UST futures positioning mix
t=pd.read_csv(DD+'tff_panel_harmonized.csv.gz',parse_dates=['report_date'])
t=t[t.contract_harmonized.str.startswith('UST ')&(t.FutOnly_or_Combined.str.strip()=='FutOnly')]
cols={'Dealer_L':'Dealer_Positions_Long_All','Dealer_S':'Dealer_Positions_Short_All','AM_L':'Asset_Mgr_Positions_Long_All','AM_S':'Asset_Mgr_Positions_Short_All',
      'Lev_L':'Lev_Money_Positions_Long_All','Lev_S':'Lev_Money_Positions_Short_All','Oth_L':'Other_Rept_Positions_Long_All','Oth_S':'Other_Rept_Positions_Short_All',
      'NonRep_L':'NonRept_Positions_Long_All','NonRep_S':'NonRept_Positions_Short_All'}
w=t.groupby('report_date')[list(cols.values())].sum(); w.columns=list(cols); O3=w.resample('ME').mean(); O3.index=O3.index.strftime('%Y-%m'); out['O3_tff_ust_positioning']=O3.loc[:'2026-09']
print('TFF contracts', sorted(t.contract_harmonized.unique()))
# O4 Fed CP issuance by maturity bucket (all issuers)
c=pd.read_csv(DD+'fed_cp_volume_stats_by_maturity.csv',parse_dates=['date'])
O4=c.pivot_table(index='date',columns='maturity_range_days',values='amount_usd_mm',aggfunc='sum')[['1_4','5_9','10_20','21_40','41_80','GT80']].resample('ME').mean()
O4.index=O4.index.strftime('%Y-%m'); out['O4_cp_maturity']=O4
# O5 MSPD Treasury marketable debt by class
m=pd.read_csv(DD+'MSPD_marketable_securities_2001-2026.zip',low_memory=False)
m['cls']=m['Security Class 1 Description'].str.strip()
mp={'Bills Maturity Value':'Bills','Notes':'Notes','Bonds':'Bonds','Inflation-Protected Securities':'TIPS','Inflation-Indexed Notes':'TIPS','Inflation-Indexed Bonds':'TIPS','Floating Rate Notes':'FRN'}
m=m[m.cls.isin(mp)&m['Security Class 2 Description'].astype(str).isin(['Total Unmatured Treasury Bills','Total Unmatured Treasury Notes','Total Unmatured Treasury Bonds','Total Treasury TIPS','Total Treasury Inflation-Protected Securities','Total Treasury Inflation-Indexed Notes','Total Treasury Inflation-Indexed Bonds','Total Treasury Floating Rate Notes'])]; m['k']=m.cls.map(mp); m['amt']=pd.to_numeric(m['Outstanding Amount (in Millions)'],errors='coerce')
O5=m.groupby(['Record Date','k']).amt.sum().unstack().fillna(0.0); O5.index=pd.to_datetime(O5.index).strftime('%Y-%m'); out['O5_treasury_debt_mix']=O5[['Bills','Notes','Bonds','TIPS','FRN']].sort_index()
# O6 Form PF tab 8.27 borrowing by creditor type (monthly, 2013-01..2025-12)
pf=pd.read_csv('/workspace/ms-1114/q1/monthly.csv').set_index('period')
O6=pf[['Secured_Prime Broker','Secured_Reverse Repo','Secured_Other Secured','Unsecured_Subtotal']]; O6.columns=['PrimeBroker','ReverseRepo','OtherSecured','Unsecured']; out['O6_formpf_creditor']=O6
pf[['Total_Total']].to_csv('formpf_total_monthly.csv')
for k,v in out.items():
    v=v.dropna(); v=v[(v>0).all(axis=1)] if k!='O5_treasury_debt_mix' else v
    v.to_csv(f'{k}.csv'); print(k, v.shape, v.index[0], v.index[-1], (v<=0).sum().to_dict())
