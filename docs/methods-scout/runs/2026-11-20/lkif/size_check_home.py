import numpy as np, json, sys
sys.path.insert(0,'.'); from lk_port import lkif, var1_t
np.mat=np.asmatrix
from LK_Info_Flow import multi_causality_est
from scipy.stats import norm
A=np.array([[0,0,-0.6,0,0,0],[-0.5,0,0,0,0,0.8],[0,0.7,0,0,0,0],[0,0,0,0.7,0.4,0],[0,0,0,0.2,0,0.7],[0,0,0,0,0,-0.5]])
alpha=np.array([0.1,0.7,0.5,0.2,0.8,0.3]); null=(A==0)&~np.eye(6,dtype=bool)
def sim(n,b,seed,al):
    r=np.random.default_rng(seed); x=np.zeros((n+500,6))
    for t in range(n+499): x[t+1]=al+A@x[t]+b*r.standard_normal(6)
    return x[500:]
out={}
for lab,al in [('alpha_as_paper',alpha),('alpha_x10',alpha*10),('alpha_zero',alpha*0)]:
    rp=[];rt=[];par=[]
    for s in range(300):
        x=sim(400,1,1000+s,al); R=multi_causality_est(x.T); p=np.squeeze(R['p'])
        P=lkif(x); par.append(np.max(np.abs(P['p']-p)))
        t=var1_t(x); pt=2*(1-norm.cdf(np.abs(t)))
        rp.append((p[null]<0.05).mean()); rt.append((pt[null]<0.05).mean())
    out[lab]=dict(size_package=float(np.mean(rp)),size_ols_t=float(np.mean(rt)),port_parity_p=float(max(par)))
    print(lab,out[lab])
json.dump(out,open('size_check_home.json','w'),indent=1)
