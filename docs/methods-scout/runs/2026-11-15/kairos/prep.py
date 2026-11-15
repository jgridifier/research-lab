import pandas as pd, numpy as np
r=pd.read_csv('/workspace/research/drive_inv/data/cleared_repo_daily.csv.gz',parse_dates=['date'])
r['m']=r.mnemonic.str.replace(r'-[FP]$','',regex=True)
r=r.sort_values('vintage').drop_duplicates(['m','date'],keep='last')  # same rule as prep_q1: last vintage wins
P=r.pivot_table(index='date',columns='m',values='value',aggfunc='last')
seg={}
for v,pre,kind in [('DVP','REPO-DVP','OV'),('GCF','REPO-GCF','OV'),('TRI','REPO-TRIV1','TV')]:
    oo=P[f'{pre}_{kind}_OO']; g30=P[f'{pre}_{kind}_G30']
    le=P[f'{pre}_{kind}_LE30']
    parts=[c for c in [f'{pre}_{kind}_B27',f'{pre}_{kind}_B830'] if c in P]
    after=P[parts].sum(axis=1,min_count=1) if parts else np.nan
    le30=le.combine_first(after)
    seg[f'{v}_ON']=oo; seg[f'{v}_T30']=le30; seg[f'{v}_G30']=g30
S=pd.DataFrame(seg)
S=S[(S.index>='2018-05-07')]
M=S.resample('ME').mean()
print(M.notna().sum()); print(M.isna().sum().sum())
M=M.loc[:'2026-09']
M.index=M.index.strftime('%Y-%m')
print(M.round(0).iloc[[0,30,60,-14,-13,-1]].to_string())
M.to_csv('mix_monthly.csv')
# Form PF monthly (tab 8.27) from the 11-14 panel
pf=pd.read_csv('/workspace/ms-1114/q1/monthly.csv').set_index('period')[['Secured_Prime Broker','Secured_Reverse Repo','Secured_Other Secured','Total_Total']]
pf.to_csv('formpf_monthly.csv')
