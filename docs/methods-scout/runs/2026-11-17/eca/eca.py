"""Event coincidence analysis (Donges et al. 2016; CoinCalc CC.eca.ts semantics, sym=FALSE), NumPy port.
A, B: 0/1 arrays (NaN allowed = missing). Precursor rate: share of A events with >=1 B event in [t-tau-delT, t-tau].
Trigger rate: share of B events with >=1 A event in [t+tau, t+tau+delT]. Poisson p-values follow CoinCalc 2.0."""
import numpy as np
from math import comb

def _prep(A,B):
    A=np.asarray(A,float).copy(); B=np.asarray(B,float).copy()
    m=np.isnan(A)|np.isnan(B); A[m]=np.nan; B[m]=np.nan
    return A,B

def rates(A,B,delT=0,tau=0):
    A,B=_prep(A,B); n=len(A)
    Ab=np.nan_to_num(A)==1; Bb=np.nan_to_num(B)==1
    # precursor
    ia=np.where(Ab)[0]; kp=0
    cb=np.concatenate([[0],np.cumsum(Bb)])
    for i in ia:
        s=i-tau-delT; e=i-tau
        if e<0: continue
        s=max(s,0); e=min(e,n-1)
        if s>n-1: continue
        if cb[e+1]-cb[s]>0: kp+=1
    ib=np.where(Bb)[0]; kt=0
    ca=np.concatenate([[0],np.cumsum(Ab)])
    for j in ib:
        s=j+tau; e=j+tau+delT
        if s>n-1: continue
        e=min(e,n-1)
        if ca[e+1]-ca[s]>0: kt+=1
    NA=int(Ab.sum()); NB=int(Bb.sum())
    return kp,kt,NA,NB,int((~np.isnan(A)).sum())

def poisson_p(k,N,Nother,delT,tau,T):
    q=(1-(delT+1)/(T-tau))**Nother
    return sum(comb(N,K)*((1-q)**K)*(q**(N-K)) for K in range(k,N+1))

def eca(A,B,delT=0,tau=0):
    kp,kt,NA,NB,T=rates(A,B,delT,tau)
    return dict(rp=kp/NA if NA else np.nan, rt=kt/NB if NB else np.nan, NA=NA, NB=NB,
                p_prec_pois=poisson_p(kp,NA,NB,delT,tau,T), p_trig_pois=poisson_p(kt,NB,NA,delT,tau,T))

def circ_null(A,B,delT,tau,reps=4999,minshift=8,seed=0):
    """Circular shift of B relative to A (keeps each series' own clustering). Returns obs, null arrays, p-values."""
    rng=np.random.default_rng(seed); A=np.asarray(A,float); B=np.asarray(B,float); n=len(A)
    o=eca(A,B,delT,tau); sh=rng.integers(minshift,n-minshift,size=reps)
    rp=np.empty(reps); rt=np.empty(reps)
    for r,s in enumerate(sh):
        e=eca(A,np.roll(B,s),delT,tau) if False else None
        kp,kt,NA,NB,_=rates(A,np.roll(B,s),delT,tau)
        rp[r]=kp/NA if NA else np.nan; rt[r]=kt/NB if NB else np.nan
    o['p_prec_circ']=(1+np.sum(rp>=o['rp']-1e-12))/(reps+1)
    o['p_trig_circ']=(1+np.sum(rt>=o['rt']-1e-12))/(reps+1)
    o['null_rp_med']=float(np.nanmedian(rp)); o['null_rt_med']=float(np.nanmedian(rt))
    o['null_rp_95']=float(np.nanquantile(rp,0.95)); o['null_rt_95']=float(np.nanquantile(rt,0.95))
    return o

def binarize(x,q,upper=True):
    x=np.asarray(x,float); thr=np.nanquantile(x,q)
    out=(x>thr).astype(float) if upper else (x<thr).astype(float)
    out[np.isnan(x)]=np.nan; return out
