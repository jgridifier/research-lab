import numpy as np
def ce_fdh(x, y, scope=None):
    """CE-FDH ceiling (Dul 2016): c(x) = max{y_k : x_k <= x}. Returns effect size d, zone, scope, step arrays."""
    x=np.asarray(x,float); y=np.asarray(y,float)
    xmin,xmax,ymin,ymax = (x.min(),x.max(),y.min(),y.max()) if scope is None else scope
    o=np.lexsort((-y,x)); xs=x[o]; ys=np.maximum.accumulate(y[o])
    ux=np.unique(xs); cu=np.array([ys[xs<=u].max() for u in ux])
    # area of empty zone between step ceiling and ymax over [xmin,xmax]
    edges=np.append(ux,xmax); zone=np.sum((ymax-cu)*np.diff(edges))
    S=(xmax-xmin)*(ymax-ymin)
    return dict(d=zone/S if S>0 else np.nan, zone=zone, scope=S, ux=ux, cu=cu)
def ceil_at(fit, xq, below='first'):
    ux,cu=fit['ux'],fit['cu']; idx=np.searchsorted(ux,xq,side='right')-1
    out=np.where(idx>=0, cu[np.clip(idx,0,None)], cu[0] if below=='first' else -np.inf)
    return out
def bottleneck(fit, yq):
    ux,cu=fit['ux'],fit['cu']; res=[]
    for v in np.atleast_1d(yq):
        k=np.where(cu>=v)[0]; res.append(ux[k[0]] if len(k) else np.nan)
    return np.array(res)
