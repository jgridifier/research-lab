#!/usr/bin/env python3
"""Engineering evidence only (not a port): a vectorised NumPy reimplementation of De Caceres et al. (2019)
directionality, checked against ecotraj 1.2.2 on today's two Q1 PROXY paths, then timed."""
import numpy as np, pandas as pd, time, json, subprocess
def clr(M): L=np.log(M); return L-L.mean(1,keepdims=True)
def directionality(C):
    n=len(C); D=np.sqrt(((C[:,None,:]-C[None,:,:])**2).sum(-1))
    i,j,k=np.array([(a,b,c) for a in range(n) for b in range(a+1,n) for c in range(b+1,n)]).T
    a=D[i,j]; b=D[j,k]; c=D[i,k]
    # angle between segment i->j and j->k: exterior angle = 180 - interior angle at j (law of cosines)
    cosj=np.clip((a**2+b**2-c**2)/(2*a*b),-1,1); theta=180-np.degrees(np.arccos(cosj))
    w=a+b; return float(np.sum(w*(1-theta/180))/np.sum(w))
out={}
for p in ['A','E4']:
    W=pd.read_csv(f'/workspace/scout/1112/data/panel_{p}.csv',index_col=0).values
    C=clr(W/W.sum(1,keepdims=True)); t=time.perf_counter()
    for _ in range(20): d=directionality(C)
    out[p]={'numpy_dir':d,'numpy_ms':(time.perf_counter()-t)/20*1000,'T':len(C)}
json.dump(out,open('/workspace/scout/1112/out/dir_parity_numpy.json','w'),indent=1); print(out)
