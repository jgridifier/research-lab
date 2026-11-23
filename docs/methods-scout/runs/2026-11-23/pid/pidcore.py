"""Gaussian-copula MMI partial information decomposition (NumPy port, 2026-11-23 scout)."""
import numpy as np
from scipy.stats import rankdata, norm
from scipy.special import psi
LN2=np.log(2)

def copnorm(x):
    r=rankdata(x); return norm.ppf(r/(len(x)+1))

def copnorm_by(x, groups):
    x=np.asarray(x,float); out=np.empty_like(x)
    for g in np.unique(groups):
        m=groups==g; out[m]=copnorm(x[m])
    return out

def ent_g(C, n=None):
    """Gaussian entropy (nats) from covariance; optional Cai et al./gcmi analytic bias correction."""
    C=np.atleast_2d(C); d=C.shape[0]
    h=0.5*np.linalg.slogdet(C)[1] + 0.5*d*np.log(2*np.pi*np.e)
    if n is not None:
        # gcmi: H_bc = H - [d/2*log(2/(n-1)) + 1/2*sum psi((n-k)/2)] correction of log det term
        dterm=(np.log(2.0/(n-1))*d + psi((n-np.arange(1,d+1))/2.0).sum())/2.0
        h=h-dterm
    return h

def mi(C, ia, ib, n=None):
    ia=list(ia); ib=list(ib); ab=ia+ib
    return (ent_g(C[np.ix_(ia,ia)],n)+ent_g(C[np.ix_(ib,ib)],n)-ent_g(C[np.ix_(ab,ab)],n))/LN2

def mmi_from_cov(C, n=None):
    """C: 3x3 covariance/correlation of (T, X1, X2). Returns dict in bits."""
    i1=mi(C,[0],[1],n); i2=mi(C,[0],[2],n); i12=mi(C,[0],[1,2],n)
    R=min(i1,i2)
    return dict(I1=i1,I2=i2,I12=i12,R=R,U1=i1-R,U2=i2-R,S=i12-max(i1,i2))

def pid_data(t,x1,x2,groups=None,bias=True):
    if groups is None: z=np.c_[copnorm(t),copnorm(x1),copnorm(x2)]
    else: z=np.c_[copnorm_by(t,groups),copnorm_by(x1,groups),copnorm_by(x2,groups)]
    C=np.cov(z.T)
    return mmi_from_cov(C, len(t) if bias else None)

def barrett_closed(a,b,c):
    """Barrett 2015 eqs (64)-(67): corr(T,X1)=a, corr(X1,X2)=b, corr(T,X2)=c, |a|<=|c|. bits."""
    R=0.5*np.log(1/(1-a*a))/LN2
    U2=0.5*np.log((1-a*a)/(1-c*c))/LN2
    S=0.5*np.log((1-b*b)*(1-c*c)/(1-(a*a+b*b+c*c)+2*a*b*c))/LN2
    return dict(R=R,U1=0.0,U2=U2,S=S)

def idep_from_corr(p,q,r):
    """Kay & Ince (2018) Idep PID, univariate Gaussian, Table 5 + eqs (8)-(11).
    p=corr(X0,X1), q=corr(X0,Y), r=corr(X1,Y). Returns bits; X0 -> '0', X1 -> '1'."""
    L=lambda v: 0.5*np.log2(v)
    I0=L(1/(1-q*q)); I1=L(1/(1-r*r)); det=1-p*p-q*q-r*r+2*p*q*r
    I01=L((1-p*p)/det)
    t7=L((1-q*q*r*r)/((1-q*q)*(1-r*r)))
    b=d=I0; i=t7-I1; k=I01-I1
    c=f=I1; h=t7-I0; j=I01-I0
    u0=min(b,d,i,k); u1=min(c,f,h,j)
    red=I0-u0; syn=I01-u0-u1-red
    return dict(I1=I0,I2=I1,I12=I01,U1=u0,U2=u1,R=red,S=syn,red_check=I1-u1)

def idep_data(t,x1,x2,groups):
    z=np.c_[copnorm_by(t,groups),copnorm_by(x1,groups),copnorm_by(x2,groups)]
    C=np.corrcoef(z.T); return idep_from_corr(C[1,2],C[0,1],C[0,2])
