# Paper-supplement simulation (ernstlab.github.io/STEM/ISMB2005_Supplement/simulated.html), seeds 1..20.
import numpy as np, pandas as pd
M=[(0,-1,1,1,-1),(0,1,0,0,2),(0,2,1,0,0)]
for seed in range(1,21):
    rng=np.random.default_rng(seed)
    for planted in [0,1]:
        X=rng.uniform(10,100,(5000,5))
        if planted:
            for k,m in enumerate(M):
                for gi in range(4850+50*k,4850+50*(k+1)):
                    v=[rng.uniform(10,100)]
                    for i in range(1,5):
                        f=2.0**(m[i]-m[i-1]); v.append(v[-1]*f+rng.uniform(-.05*f,.05*f))
                    X[gi]=v
        d=pd.DataFrame(X,columns=['t0','t1','t2','t3','t4']); d.insert(0,'Gene Symbol',[f'g{i}' for i in range(5000)])
        d.to_csv(f'sim_s{seed}_p{planted}.txt',sep='\t',index=False,float_format='%.5f')
