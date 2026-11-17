# PREREG.md E2 descriptive application: 11-16 table, pim sandwich vs firm-clustered p, Holm over the 29 rows each. 2026-11-17.
import json, numpy as np, pandas as pd
from scipy.stats import norm
from statsmodels.stats.multitest import multipletests
from pimfast import within_pairs, fit, vcov_sandwich, vcov_firm
P0 = pd.read_csv('q3_pim_panel.csv'); O = json.load(open('oracle.json')); rows = []
for f in O['fits']:
    D = P0.iloc[f['rows']]; pairs = within_pairs(D.year.values); F = fit(D[f['xs']].values, D[f['y'][0]].values, pairs)
    s1 = np.sqrt(np.diag(vcov_sandwich(F, pairs))); s2 = np.sqrt(np.diag(vcov_firm(F, pairs, D.id_rssd.values)))
    for k, x in enumerate(f['xs']):
        iqr = P0[x].quantile(.75) - P0[x].quantile(.25)
        rows.append(dict(analysis=f['label'][0], outcome=f['y'][0], covariate=x, n=len(D), firms=D.id_rssd.nunique(), beta=F['beta'][k],
                         PI_iqr=1 / (1 + np.exp(-F['beta'][k] * iqr)), se_sandwich=s1[k], se_firm=s2[k], se_ratio=s2[k] / s1[k],
                         p_sandwich=2 * norm.sf(abs(F['beta'][k] / s1[k])), p_firm=2 * norm.sf(abs(F['beta'][k] / s2[k]))))
T = pd.DataFrame(rows); T['holm_sandwich'] = multipletests(T.p_sandwich, method='holm')[1]; T['holm_firm'] = multipletests(T.p_firm, method='holm')[1]
T.to_csv('math_apply.csv', index=False)
pd.set_option('display.width', 250); print(T[['analysis', 'outcome', 'covariate', 'PI_iqr', 'se_ratio', 'p_sandwich', 'p_firm', 'holm_sandwich', 'holm_firm']].round(4).to_string())
print('se_ratio median', T.se_ratio.median(), 'range', T.se_ratio.min(), T.se_ratio.max())
print('Holm<=.05 sandwich', (T.holm_sandwich <= .05).sum(), 'firm', (T.holm_firm <= .05).sum())
