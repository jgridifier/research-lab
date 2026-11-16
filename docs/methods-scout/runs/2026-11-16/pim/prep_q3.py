# Build the Q3 PIM panel from the lab's verified public files (11-14 run): DFAST results (all scenarios), Y-9C HI-A, SCB.
import pandas as pd, numpy as np
P=pd.read_csv('/workspace/ms-1114/q3/q3_panel.csv')
Y=pd.read_csv('/workspace/ms-1114/q3/y9c_payouts.csv')
D=pd.read_csv('/workspace/ms-1114/fed_dfast_2026.csv')
D['year']=D.exercise_name.str.extract(r'(\d{4})').astype(int)
D.loc[D.exercise_name.str.startswith('December 2020'),'year']=2020
D['dd']=D.common_equity_tier1_actual_rat.fillna(D.tier1_common_actual_rat)-D.common_equity_tier1_min_rat.fillna(D.tier1_common_min_rat)
dec=D.exercise_name.str.startswith('December 2020')
A=D[(D.scenario_id==2)][['year','id_rssd','dd','income_pretax_net_rate','loss_total_loan_rate']].rename(columns={'dd':'dd_A','income_pretax_net_rate':'pt_A','loss_total_loan_rate':'loss_A'})
ALT=D[dec&(D.scenario_id==30)][['id_rssd','dd']].rename(columns={'dd':'dd_alt'})
SAdec=D[dec&(D.scenario_id==3)][['id_rssd','dd','income_pretax_net_rate']].rename(columns={'dd':'dd_sa_dec','income_pretax_net_rate':'pt_sa_dec'})
Y['gross_bb']=Y.BHCK4783; Y['div_all']=Y.BHCK4460+Y.BHCK4598
yy=Y[['RSSD9001','year','gross_bb','BHCK4460','rwa','payout_rwa','payout_ni','div','buyback_net']].rename(columns={'RSSD9001':'id_rssd'})
P=P[P.year<=2025].merge(yy[['id_rssd','year','gross_bb','BHCK4460']],on=['id_rssd','year'],how='left')
nxt=yy.copy(); nxt['year']=nxt.year-1
P=P.merge(nxt[['id_rssd','year','payout_rwa','payout_ni','div','gross_bb','rwa']].rename(columns=lambda c: c if c in('id_rssd','year') else c+'_next'),on=['id_rssd','year'],how='left')
P=P.merge(A,on=['year','id_rssd'],how='left')
P['gap_dd']=P.drawdown-P.dd_A          # SA minus Adverse CET1 drawdown (pp)
P['gap_pt']=P.pt_A-P.income_pretax_net_rate  # Adverse minus SA pre-tax income (pp of assets)
P['div_rwa']=100*P['div']/P.rwa; P['bb_rwa']=100*P.buyback_net/P.rwa; P['grossbb_rwa']=100*P.gross_bb/P.rwa
den=P['div']+P.gross_bb; P['div_share']=np.where(den>0,P['div']/den,np.nan)
P['payout_rwa_pct']=P.payout_rwa  # payout_rwa in the 11-14 panel is already in percent of RWA
den2=P.div_next+P.gross_bb_next; P['div_share_next']=np.where(den2>0,P.div_next/den2,np.nan)
P=P.merge(ALT,on='id_rssd',how='left').merge(SAdec,on='id_rssd',how='left')
P.loc[P.year!=2020,['dd_alt','dd_sa_dec','pt_sa_dec']]=np.nan
P.to_csv('q3_pim_panel.csv',index=False)
print(P.shape, P[['payout_rwa','div_rwa','bb_rwa','div_share','gap_dd','payout_rwa_next']].describe().T)
print('Adverse matched rows by year', P.dropna(subset=['dd_A']).groupby('year').size().to_dict())
print('2020 alt rows', P.dd_alt.notna().sum())
print('check payout_rwa = div+bb ratio', np.nanmax(np.abs(P.payout_rwa-(P.div_rwa+P.bb_rwa))))
