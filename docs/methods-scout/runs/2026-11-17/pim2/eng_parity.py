# PREREG.md E1, bar Eng-1 (parity) + E2 identity check. 2026-11-17.
import json, numpy as np, pandas as pd
from pimfast import within_pairs, fit, vcov_sandwich, vcov_firm, _meat
P0 = pd.read_csv('q3_pim_panel.csv'); O = json.load(open('oracle.json'))
db = ds = 0; rows = []; ident = 0
for f in O['fits']:
    D = P0.iloc[f['rows']]; pairs = within_pairs(D.year.values)
    F = fit(D[f['xs']].values, D[f['y'][0]].values, pairs); se = np.sqrt(np.diag(vcov_sandwich(F, pairs)))
    d1 = np.max(np.abs(F['beta'] - np.array(f['beta']))); d2 = np.max(np.abs(se - np.array(f['se'])))
    # identity: firm-cluster estimator with firm-year ids and c=1 == pim sandwich
    Vi = vcov_firm(F, pairs, np.arange(len(D)), small=False); ident = max(ident, np.max(np.abs(Vi - vcov_sandwich(F, pairs))))
    db, ds = max(db, d1), max(ds, d2); rows.append(dict(label=f['label'][0], y=f['y'][0], xs=f['xs'], npairs=len(pairs), max_dbeta=d1, max_dse=d2))
# permutations
D = P0.iloc[O['perm_rows']]; pairs = within_pairs(D.year.values); X = D[['drawdown', 'income_pretax_net_rate']].values
dp = max(np.max(np.abs(fit(X, np.array(p['y'], float), pairs)['beta'] - np.array(p['beta']))) for p in O['perms'])
res = dict(n_fits=len(O['fits']), n_coefs=sum(len(f['beta']) for f in O['fits']), max_dbeta=db, max_dse=ds, perm50_max_dbeta=dp,
           identity_firmyear_vs_sandwich=ident, pass_eng1=bool(db <= 1e-8 and ds <= 1e-8 and dp <= 1e-8), oracle=f"pim {O['pim_version'][0]}")
json.dump(dict(summary=res, fits=rows), open('eng_parity.json', 'w'), indent=1); print(json.dumps(res, indent=1))
