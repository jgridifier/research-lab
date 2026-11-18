import pandas as pd, numpy as np
from eca import binarize
def ev(X,q=0.9):
    E=pd.DataFrame(index=X.index)
    E['fails']=binarize(X.dl_fails,q); E['spread']=binarize(X.d_spread,q); E['dvp']=binarize(X.dl_dvp,q)
    E['levbuild']=binarize(X.d_lev,q); E['levunwind']=binarize(X.d_lev,1-q,upper=False)
    return E
def sub(E,a,b):
    S=E[[a,b]]
    if 'lev' in a or 'lev' in b: S=S[S.index<='2025-12-31']
    S=S.dropna(); return S[a].values,S[b].values
