# H3 bias + P4 size/power on our shape (Gaussian sims), MMI and Idep
import sys, json, numpy as np
sys.path.insert(0,'pid')
from pidcore import mmi_from_cov, idep_from_corr, copnorm
rng=np.random.default_rng(7)
def sim(n,a,b,c,reps=2000):
    C=np.array([[1,a,c],[a,1,b],[c,b,1.]]); L=np.linalg.cholesky(C)
    out=[]
    for _ in range(reps):
        z=rng.standard_normal((n,3))@L.T
        z=np.c_[copnorm(z[:,0]),copnorm(z[:,1]),copnorm(z[:,2])]
        Ch=np.cov(z.T); m=mmi_from_cov(Ch,n); mp=mmi_from_cov(Ch)
        R=np.corrcoef(z.T); d=idep_from_corr(R[1,2],R[0,1],R[0,2])
        out.append([m['R'],m['U2'],m['S'],mp['R'],mp['U2'],mp['S'],d['R'],d['U1'],d['U2'],d['S']])
    return np.array(out), mmi_from_cov(C), idep_from_corr(b,a,c)
res={}
for n in [132,181,360]:
    # near our SCB/drawdown shape: a=corr(T,X1)=0.30, c=corr(T,X2)=0.35, b=0.85
    for lab,(a,b,c) in {'shape_S>0':(0.30,0.85,0.35),'S=0 (b=a/c)':(0.30,0.30/0.35,0.35),'weak 0.2/0.25 S=0':(0.2,0.2/0.25,0.25)}.items():
        X,truth,tid=sim(n,a,b,c)
        res[f'{n} {lab}']=dict(n=n,abc=[a,b,c],truth_mmi=truth,truth_idep=tid,
            mean_bc=dict(R=X[:,0].mean(),U2=X[:,1].mean(),S=X[:,2].mean()),
            mean_plugin=dict(R=X[:,3].mean(),U2=X[:,4].mean(),S=X[:,5].mean()),
            mean_idep=dict(R=X[:,6].mean(),U1=X[:,7].mean(),U2=X[:,8].mean(),S=X[:,9].mean()),
            sd_bc=dict(R=X[:,0].std(),U2=X[:,1].std(),S=X[:,2].std()))
        print(n,lab,{k:round(v,4) for k,v in truth.items()}, 'bc',{k:round(v,4) for k,v in res[f'{n} {lab}']['mean_bc'].items()},'plug',{k:round(v,4) for k,v in res[f'{n} {lab}']['mean_plugin'].items()})
json.dump(res,open('pid/power_bias.json','w'),indent=1,default=float)
