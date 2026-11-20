import numpy as np, json, sys
sys.path.insert(0,'.')
from lk_port import lkif
np.mat = np.asmatrix  # LK_Info_flow 3.1.2.1 uses np.mat, removed in NumPy 2.0
from LK_Info_Flow import multi_causality_est
A=np.array([[0,0,-0.6,0,0,0],[-0.5,0,0,0,0,0.8],[0,0.7,0,0,0,0],[0,0,0,0.7,0.4,0],[0,0,0,0.2,0,0.7],[0,0,0,0,0,-0.5]])
alpha=np.array([0.1,0.7,0.5,0.2,0.8,0.3])
true=set([(2,0),(0,1),(5,1),(1,2),(4,3),(3,4),(5,4)])  # (source j, target i) 0-based
def sim(n,b,seed):
    r=np.random.default_rng(seed); x=np.zeros((n+1000,6)); 
    for t in range(n+999): x[t+1]=alpha+A@x[t]+b*r.standard_normal(6)
    return x[1000:]
out={}
for name,n,b in [('b1_n10000',10000,1),('b100_n10000',10000,100),('b100_n500',500,100)]:
    res=[]
    for seed in range(20):
        x=sim(n,b,seed)
        R=multi_causality_est(x.T,max_lag=1,np=1,dt=1,significance_test=1)
        IF=np.squeeze(R['IF']);nIF=np.squeeze(R['nIF']);e90=np.squeeze(R['err_e90'])
        sig=set((j,i) for i in range(6) for j in range(6) if i!=j and abs(IF[i,j])>e90[i,j])
        P=lkif(x)
        res.append(dict(exact=sig==true,fp=len(sig-true),fn=len(true-sig),
          t62=abs(nIF[1,5]),t65=abs(nIF[4,5]),t45=abs(nIF[4,3]),t54=abs(nIF[3,4]),
          parT=float(np.max(np.abs(P['T']-IF))),partau=float(np.max(np.abs(P['tau']-nIF))),parp=float(np.max(np.abs(P['p']-np.squeeze(R['p']))))))
    agg={k:(float(np.mean([r[k] for r in res])) ) for k in res[0]}
    agg['exact_share']=agg.pop('exact'); agg['tau_seed0']={k:res[0][k] for k in ['t62','t65','t45','t54']}
    agg['parity_max']={k:max(r[k] for r in res) for k in ['parT','partau','parp']}
    out[name]=agg; print(name,json.dumps(agg))
out['paper_values']={'t62':0.132,'t65':0.125,'t45':0.024,'t54':0.088}
json.dump(out,open('home_repro.json','w'),indent=1)
