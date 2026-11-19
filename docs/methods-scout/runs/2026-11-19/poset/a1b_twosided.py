import json,numpy as np
import q3_poset2_lib as L
L.rng=np.random.default_rng(7)
obs,_=L.inc_stats(); nul=np.array([[z[k] for k in obs] for z in (L.inc_stats(True)[0] for _ in range(1999))])
ks=list(obs); o=np.array([obs[k] for k in ks]); m=nul.mean(0)
p2={k:float((1+(np.abs(nul[:,i]-0.5)>=abs(o[i]-0.5)).sum())/2000) for i,k in enumerate(ks)}
res={'two_sided_p_about_0.5':p2,'null_q025':dict(zip(ks,np.quantile(nul,.025,0).tolist())),'null_q975':dict(zip(ks,np.quantile(nul,.975,0).tolist()))}
json.dump(res,open('A1b_twosided.json','w'),indent=1); print(res)
