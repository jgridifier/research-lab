#!/usr/bin/env python3
"""Prep for methods scout 2026-11-12 (scheduled). Q1 PROXY panels are reused unchanged from the
2026-11-12 ad hoc run (built by 2026-11-11 prep.py from public FR Y-9C). This script only builds the
monthly macro-financial stress-state panel used by the ecotraj episode analysis (1c)."""
import pandas as pd, numpy as np, json
D = '/workspace/scout/data/'
O = '/workspace/scout/1112/data/'
def m(f, col, how='mean'):
    s = pd.read_csv(D + f, parse_dates=['observation_date'], index_col=0)[col]
    s = pd.to_numeric(s, errors='coerce').dropna()
    return s.resample('MS').mean()
vix = np.log(m('VIXCLS.csv', 'VIXCLS')).rename('log_vix')
nfci = m('NFCI.csv', 'NFCI').rename('nfci')
stl = m('STLFSI4.csv', 'STLFSI4').rename('stlfsi4')
curve = m('T10Y2Y.csv', 'T10Y2Y').rename('t10y2y')
e = pd.read_csv(D + 'ebp_monthly.csv', parse_dates=['date'], index_col=0)
X = pd.concat([vix, nfci, stl, curve, e['gz_spread'], e['ebp']], axis=1).dropna()
X = X.loc['1994-01-01':]
Z = (X - X.mean()) / X.std()
Z.to_csv(O + 'stress_monthly_z.csv')
json.dump({'start': str(X.index[0].date()), 'end': str(X.index[-1].date()), 'n': len(X),
           'mean': X.mean().round(4).to_dict(), 'sd': X.std().round(4).to_dict()},
          open(O + 'stress_summary.json', 'w'), indent=1)
print(X.index[0], X.index[-1], len(X))
