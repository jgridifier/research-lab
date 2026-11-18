import pandas as pd, numpy as np
P=pd.read_csv('q3_pim_panel.csv')
V=['drawdown','income_pretax_net_rate','loss_total_loan_rate','cet1_start','payout_rwa','div_rwa','bb_rwa']
for nm,yrs in [('w1',range(2015,2019)),('w2',range(2022,2026))]:
    yrs=list(yrs); S=P[P.year.isin(yrs)].dropna(subset=V); c=S.groupby('id_rssd').year.nunique(); ids=sorted(c[c==len(yrs)].index)
    T=[]
    for y in yrs:
        D=S[(S.year==y)&S.id_rssd.isin(ids)].set_index('id_rssd').loc[ids,V].rank()  # ranks within year (Spearman-type)
        D.columns=[f'{v}_{y}' for v in V]; T.append(D)
    pd.concat(T,axis=1).to_csv(f'bal_{nm}.csv'); print(nm,len(ids),yrs)
    S[S.id_rssd.isin(ids)][['id_rssd','disclosure_legal_name']].drop_duplicates('id_rssd').to_csv(f'bal_{nm}_names.csv',index=False)
