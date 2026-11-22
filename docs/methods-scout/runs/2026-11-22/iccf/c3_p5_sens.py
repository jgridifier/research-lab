# post hoc sensitivity: P5 calibrated p if the true persistence is higher than fitted
import numpy as np, json
import iccf_core as ic
from q1_iccf import get, detrend, ar1, sim_ar1, LMIN, LMAX, STEP
rng=np.random.default_rng(11221); d1=get('rr'); d2=get('dvp'); a=max(d1.date.min(),d2.date.min()); b=min(d1.date.max(),d2.date.max())
d1=d1[(d1.date>=a)&(d1.date<=b)]; d2=d2[(d2.date>=a)&(d2.date<=b)]; t1=d1.t.values; t2=d2.t.values
p1=ar1(detrend(t1,d1.y.values)); p2=ar1(detrend(t2,d2.y.values)); out=[]
for f1,f2 in [(p1[0],p2[0]),(0.98,0.995),(0.99,0.998),(0.995,0.999)]:
    r=np.array([abs(ic.rstar(t1,detrend(t1,sim_ar1(len(t1),f1,p1[1],rng)),t2,detrend(t2,sim_ar1(len(t2),f2,p2[1],rng)),LMIN,LMAX,STEP)[0]) for _ in range(1000)])
    out.append(dict(phi_month=round(float(f1),4),phi_week=round(float(f2),4),p=round(float((1+(r>=0.921).sum())/1001),4),q95=round(float(np.quantile(r,.95)),3)))
    print(out[-1],flush=True)
json.dump(out,open('C3_p5_sens.json','w'),indent=1)
