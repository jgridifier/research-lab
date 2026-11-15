"""Rebuild the Q1 weekly and monthly aggregate panels from the lab's public-data copies (verification of the 2026-11-14 partial files)."""
import pandas as pd, numpy as np, sys
D='/workspace/research/drive_inv/data/'
f=pd.read_csv(D+'fails_weekly.csv'); f=f[f.metric=='level']
fw=f.pivot_table(index='date',columns='keyid',values='value_usd_mm',aggfunc='first')
r=pd.read_csv(D+'cleared_repo_daily.csv.gz'); r['date']=pd.to_datetime(r.date)
def ser(m):
    s=r[r.mnemonic.isin([m+'-F',m+'-P'])].sort_values('vintage').drop_duplicates('date').set_index('date').value.sort_index()  # final preferred
    return s
daily=pd.DataFrame({'dvp_on':ser('REPO-DVP_AR_OO'),'tri_t':ser('REPO-TRI_AR_T'),'dvp_out':ser('REPO-DVP_OV_TOT'),'tri_tvol':ser('REPO-TRI_TV_T')})
daily['spread_bp']=(daily.dvp_on-daily.tri_t)*100
wk=daily.resample('W-WED').mean()
W=pd.DataFrame({'fails_otr510':fw['PDSI5F-TD']+fw['PDSI10F-TD'],'fails_fin_ust':fw['PDFTD-USTET']}); W.index=pd.to_datetime(W.index)
W=W.join(wk,how='left')
W=W[W.index>='2018-05-09']
W['l_fails_otr']=np.log(W.fails_otr510); W['l_fails_fin']=np.log(W.fails_fin_ust); W['l_dvp_out']=np.log(W.dvp_out)
for k in [1,4,13]:
    W[f'dl{k}']=W.l_dvp_out.diff(k)
old=pd.read_csv('/workspace/ms-1114/q1/weekly.csv',parse_dates=['date']).set_index('date')
j=old.join(W,rsuffix='_new',how='inner')
for c in ['fails_otr510','fails_fin_ust','dvp_on','tri_t','dvp_out','tri_tvol','spread_bp']:
    print(c,'max abs diff',float((j[c]-j[c+'_new']).abs().max()), 'n',len(j))
for k in [1,4,13]: print('dl',k,float((j.dl_dvp_out-j[f'dl{k}']).abs().max()))
print(len(old),len(W), old.index.min(), old.index.max())
