# Descriptive extra (PREREG.md A): ARDL long-run multiplier of drawdown on payout/NI, full vs the 11-16 2% trim.
import json, numpy as np, pandas as pd, statsmodels.formula.api as smf
B=pd.read_csv('bench_panel.csv').dropna(subset=['payout_ni','drawdown','payout_ni_prev'])
cut=np.quantile(np.abs(B.payout_ni),.98); out={}
for k,D in [('full',B),('trim2pct',B[np.abs(B.payout_ni)<=cut])]:
    m=smf.ols('payout_ni ~ payout_ni_prev + drawdown + C(year)',D).fit(); phi=m.params['payout_ni_prev']; b=m.params['drawdown']
    o=smf.ols('payout_ni ~ drawdown + C(year)',D).fit().params['drawdown']
    out[k]=dict(n=len(D),phi=phi,beta=b,long_run=b/(1-phi),ols_static=o)
out['ardl_lr_change_pct']=100*(out['trim2pct']['long_run']/out['full']['long_run']-1)
out['ols_change_pct']=100*(out['trim2pct']['ols_static']/out['full']['ols_static']-1)
json.dump(out,open('bench_trim.json','w'),indent=1); print(json.dumps(out,indent=1))
