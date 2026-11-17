# 2026-11-17: add previous-year payouts (from the same lab Y-9C payout file) for the ARDL/SARIMAX benchmark. See ../PREREG.md section A.
import pandas as pd
P=pd.read_csv('q3_pim_panel.csv')
Y=pd.read_csv('/workspace/ms-1114/q3/y9c_payouts.csv')[['RSSD9001','year','payout_rwa','payout_ni']].rename(columns={'RSSD9001':'id_rssd'})
Y['year']=Y.year+1
P=P.merge(Y.rename(columns={'payout_rwa':'payout_rwa_prev','payout_ni':'payout_ni_prev'}),on=['id_rssd','year'],how='left')
B=P[['year','id_rssd','drawdown','income_pretax_net_rate','payout_rwa','payout_ni','payout_rwa_prev','payout_ni_prev']]
print(B.isna().sum().to_dict(), B.shape)
B.to_csv('bench_panel.csv',index=False)
