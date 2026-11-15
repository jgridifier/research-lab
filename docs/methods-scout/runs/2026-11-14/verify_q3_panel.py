"""Verify the 2026-11-14 Q3 panel (q3_panel.csv) against its public inputs.
dfast.csv: Fed public_results_DFAST_2026.csv rows (exact match checked against a fresh download on 2026-11-15).
y9c_payouts.csv: BHCF Q4 zips, items checked by verify_y9c.py. scb_panel.csv: LBCR PDFs, checked below."""
import pandas as pd, subprocess, re
B='/workspace/ms-1114/'
d=pd.read_csv(B+'q3/dfast.csv'); P=pd.read_csv(B+'q3/q3_panel.csv'); y=pd.read_csv(B+'q3/y9c_payouts.csv')
a=pd.read_csv(B+'fed_dfast_2026.csv',encoding='latin1'); a=a[a.id_rssd.notna()].copy(); a['id_rssd']=a.id_rssd.astype(int)
m=d.merge(a,on=['exercise_name','id_rssd','scenario_id'],suffixes=('','_f'))
print('dfast rows matched to Fed CSV:',len(m),'of',len(d))
for c in ['common_equity_tier1_actual_rat','common_equity_tier1_min_rat','tier1_common_actual_rat','tier1_common_min_rat','income_pretax_net_rate']:
    print(' ',c,'max abs diff',float((pd.to_numeric(m[c],errors='coerce')-pd.to_numeric(m[c+'_f'],errors='coerce')).abs().max()))
s=d[(d.scenario_name=='Supervisory Severely Adverse')&~d.exercise_name.str.startswith('December')].copy()
s['year']=s.exercise_name.str.extract(r'(\d{4})').astype(int)
s['dd']=s.common_equity_tier1_actual_rat.fillna(s.tier1_common_actual_rat)-s.common_equity_tier1_min_rat.fillna(s.tier1_common_min_rat)
j=P.merge(s[['year','id_rssd','dd','income_pretax_net_rate']],on=['year','id_rssd'],suffixes=('','_r'))
print('panel drawdown rebuilt:',len(j),'of',len(P),'max diff',float((j.drawdown-j.dd).abs().max()),'pretax max diff',float((j.income_pretax_net_rate-j.income_pretax_net_rate_r).abs().max()))
j2=P.merge(y[['year','RSSD9001','payout_rwa']].rename(columns={'RSSD9001':'id_rssd'}),on=['year','id_rssd'],suffixes=('','_y'))
print('payout/RWA matched:',len(j2),'max diff',float((j2.payout_rwa-j2.payout_rwa_y).abs().max()))
sc=pd.read_csv(B+'scb/scb_panel.csv'); files={2021:'lbcr_2021.pdf',2022:'lbcr_20220804.pdf',2023:'lbcr_20230727.pdf',2024:'lbcr_20240828.pdf',2025:'lbcr_20250829.pdf',2026:'lbcr_20260624.pdf'}
bad=0
for yr,f in files.items():
    t=subprocess.run(['pdftotext','-layout',B+'scb/'+f,'-'],capture_output=True,text=True).stdout
    for _,r in sc[sc.year_effective==yr].iterrows():
        L=[l for l in t.splitlines() if l.strip().startswith(r['name'][:25])]
        if not L or f"{r.scb:.1f}" not in re.findall(r'\d+\.\d',L[0]): bad+=1
print('SCB rows checked vs LBCR PDFs:',len(sc),'mismatches',bad)
