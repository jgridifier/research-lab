"""Vectorized NumPy ICCF (interpolated cross-correlation, Gaskell & Peterson 1987; Peterson et al. 1998 FR/RSS),
written to reproduce PyCCF V2.2 (Sun, Grier & Peterson) xcor/peakcent exactly, imode=0 (average of both interpolations)."""
import numpy as np
def tau_grid(tlagmin, tlagmax, tunit):
    # PyCCF accumulates tau += tunit in floating point; emulate it so lag values match bit-for-bit
    safe=tunit*0.1; taus=[]; tau=tlagmin+0.0
    while tau < tlagmax+safe: taus.append(tau); tau+=tunit
    return np.array(taus)
def _half(ta, ya, tb, yb, taus, sign):
    # correlate ya(ta) with yb interpolated at ta + sign*tau, over points inside tb's span
    T=ta[None,:]+sign*taus[:,None]
    M=(T>=tb.min())&(T<=tb.max())
    Yb=np.interp(T.ravel(),tb,yb).reshape(T.shape)*M
    Ya=ya[None,:]*M
    n=M.sum(1).astype(float)
    sa=Ya.sum(1); sb=Yb.sum(1); saa=(Ya*Ya).sum(1); sbb=(Yb*Yb).sum(1); sab=(Ya*Yb).sum(1)
    rd1sq=n*sbb-sb*sb; rd2sq=n*saa-sa*sa
    rd1=np.sqrt(np.where(rd1sq>0,rd1sq,0.0)); rd2=np.sqrt(np.where(rd2sq>0,rd2sq,0.0))
    with np.errstate(invalid='ignore',divide='ignore'):
        r=np.where(rd1*rd2==0,0.0,(n*sab-sb*sa)/(rd1*rd2))
    return r, n
def xcor(t1,y1,t2,y2,tlagmin,tlagmax,tunit):
    taus=tau_grid(tlagmin,tlagmax,tunit)
    r12,n12=_half(t1,y1,t2,y2,taus,+1.0)   # interpolate lc2 at t1+tau
    r21,n21=_half(t2,y2,t1,y1,taus,-1.0)   # interpolate lc1 at t2-tau
    ok=(n12>0)&(n21>0)
    return 0.5*(r12[ok]+r21[ok]), taus[ok], 0.5*(n12[ok]+n21[ok])
def peakcent(t1,y1,t2,y2,tlagmin,tlagmax,tunit,thres=0.8,sigmode=0.2):
    r,lag,npts=xcor(t1,y1,t2,y2,tlagmin,tlagmax,tunit)
    i=int(np.argmax(r)); rmax=r[i]; tp=lag[i]
    if not (rmax>=sigmode and tlagmin<tp<tlagmax): return np.nan,np.nan,rmax,(r,lag)
    rc=thres*rmax; neg=r-rc<0; d=lag[neg]-tp
    L=np.abs(d[d<0]); R=d[d>0]
    if len(L)==0 or len(R)==0: return np.nan,np.nan,rmax,(r,lag)
    tl=tp-L.min(); tr=tp+R.min()
    if not (tl>=lag.min() and tr<=lag.max()): return np.nan,np.nan,rmax,(r,lag)
    sel=(lag>tl)&(lag<tr)
    if sel.sum()==0: return np.nan,np.nan,rmax,(r,lag)
    return tp, float(np.sum(r[sel]*lag[sel])/np.sum(r[sel])), rmax, (r,lag)
def rss_draws(t1,y1,t2,y2,tlagmin,tlagmax,tunit,nsim,rng,dy1=None,dy2=None,fr=False,thres=0.8,sigmode=0.2):
    """RSS (and optionally FR) Monte Carlo: returns arrays of peak and centroid lags (NaN = failed)."""
    pk=np.full(nsim,np.nan); ce=np.full(nsim,np.nan); rm=np.full(nsim,np.nan)
    for k in range(nsim):
        while True:
            i1,c1=np.unique(rng.integers(0,len(t1),len(t1)),return_counts=True)
            if len(i1)>1: break
        while True:
            i2,c2=np.unique(rng.integers(0,len(t2),len(t2)),return_counts=True)
            if len(i2)>1: break
        a1=y1[i1]; a2=y2[i2]
        if fr: a1=rng.normal(a1,dy1[i1]/np.sqrt(c1)); a2=rng.normal(a2,dy2[i2]/np.sqrt(c2))
        p,c,r,_=peakcent(t1[i1],a1,t2[i2],a2,tlagmin,tlagmax,tunit,thres,sigmode)
        pk[k]=p; ce[k]=c; rm[k]=r
    return pk,ce,rm
def rstar(t1,y1,t2,y2,tlagmin,tlagmax,tunit):
    r,lag,_=xcor(t1,y1,t2,y2,tlagmin,tlagmax,tunit); i=int(np.argmax(np.abs(r))); return r[i],lag[i]
