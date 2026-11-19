import json, pickle, numpy as np, pandas as pd, warnings
from scipy.stats import spearmanr, kendalltau
from prep_lib import load, dom, S
warnings.filterwarnings('ignore'); rng=np.random.default_rng(201911)
Y=pickle.load(open('Y.pkl','rb')); out={}
# ---- A1b: incomparable pairs. Agreement of EW composite & per-indicator, with within-year permutation null
def inc_stats(perm=False):
    agg={'ew':[0,0],'ols':[0,0],'drawdown':[0,0],'neg_pti':[0,0],'loss_total_loan_rate':[0,0]}
    for y,d in Y.items():
        pay=np.array(d['pay']); pay=rng.permutation(pay) if perm else pay
        X=np.array(d['X']); n=len(pay); M=d['M']
        iu,ju=np.triu_indices(n,1); inc=~(M[iu,ju].astype(bool)|M[ju,iu].astype(bool)); i=iu[inc]; j=ju[inc]
        for k in agg:
            s=d[k] if k in ('ew','ols') else X[:,S.index(k)]
            hi=np.where(s[i]>s[j],i,j); lo=np.where(s[i]>s[j],j,i); tie=s[i]==s[j]
            a=(pay[hi]<pay[lo])+0.5*(pay[hi]==pay[lo]); a=np.where(tie,0.5,a)
            agg[k][0]+=a.sum(); agg[k][1]+=len(a)
    return {k:v[0]/v[1] for k,v in agg.items()}, agg['ew'][1]
