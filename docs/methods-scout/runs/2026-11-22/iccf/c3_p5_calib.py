# post hoc: calibrated p for P5 observed r* using independent pairs at the fitted AR(1) persistence (outer loop of C3)
import numpy as np, json, time
import iccf_core as ic
from q1_iccf import get, detrend, ar1, sim_ar1, LMIN, LMAX, STEP
rng=np.random.default_rng(1122); out={}
for P,(k1,k2),obs in [('P5',('rr','dvp'),0.921),('P1',('pb','fails'),0.258)]:
    d1=get(k1); d2=get(k2); a=max(d1.date.min(),d2.date.min()); b=min(d1.date.max(),d2.date.max())
    d1=d1[(d1.date>=a)&(d1.date<=b)]; d2=d2[(d2.date>=a)&(d2.date<=b)]; t1=d1.t.values; t2=d2.t.values
    p1=ar1(detrend(t1,d1.y.values)); p2=ar1(detrend(t2,d2.y.values)); t0=time.time()
    r=np.array([abs(ic.rstar(t1,detrend(t1,sim_ar1(len(t1),*p1,rng)),t2,detrend(t2,sim_ar1(len(t2),*p2,rng)),LMIN,LMAX,STEP)[0]) for _ in range(2000)])
    out[P]=dict(obs_abs_rstar=obs,n=2000,p_calibrated=round(float((1+(r>=obs).sum())/2001),4),q95=round(float(np.quantile(r,.95)),3),q99=round(float(np.quantile(r,.99)),3),secs=round(time.time()-t0,1))
    print(P,out[P],flush=True)
json.dump(out,open('C3_calib.json','w'),indent=1)
