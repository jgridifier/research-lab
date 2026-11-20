import numpy as np, pandas as pd, json, sys
sys.path.insert(0,'.'); from lk_port import lkif, var1_t
from scipy.stats import t as tdist
X=pd.read_csv('q1_weekly_lkif.csv',parse_dates=['date']).set_index('date')
V=['dl_fails','d_spread','dl_dvp','dl_tri','d_lev','d_vix']
def fitvar(Z):
    n,d=Z.shape; Zr=np.column_stack([Z[:-1],np.ones(n-1)]); B,*_=np.linalg.lstsq(Zr,Z[1:],rcond=None)
    return B[:d].T,B[d],Z[1:]-Zr@B
def blockboot(E,n,rng,mb=8):
    idx=[]; m=len(E)
    while len(idx)<n:
        s=rng.integers(m); L=rng.geometric(1/mb); idx+= [(s+k)%m for k in range(L)]
    return E[np.array(idx[:n])]
def sim(A,c,E,n,rng,Z0):
    e=blockboot(E,n+50,rng); x=np.zeros((n+50,A.shape[0])); x[0]=Z0
    for t in range(n+49): x[t+1]=c+A@x[t]+e[t]
    return x[50:]
def shiftp(Z,i,j,ns,rng):
    T0=abs(lkif(Z)['T'][i,j]); n=len(Z); c=0
    for s in range(ns):
        Zs=Z.copy(); Zs[:,j]=np.roll(Z[:,j],rng.integers(26,n-26)); c+= abs(lkif(Zs)['T'][i,j])>=T0
    return (c+1)/(ns+1)
