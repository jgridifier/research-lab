# Parity: our bias-corrected Gaussian MI vs gcmi.mi_gg (robince/gcmi, cloned beside this script), n = 132, simulated data.
import sys, numpy as np, json
sys.path.insert(0,'gcmi/python/src'); sys.path.insert(0,'pid')
import gcmi as g
from pidcore import mi
z=np.random.default_rng(3).standard_normal((132,3)); z[:,2]+=0.8*z[:,1]; z[:,0]+=0.3*z[:,2]
C=np.cov(z.T)
a=g.mi_gg(z[:,[0]].T,z[:,[1,2]].T,biascorrect=True,demeaned=False); b=mi(C,[0],[1,2],132)
a2=g.mi_gg(z[:,[0]].T,z[:,[1]].T,biascorrect=True,demeaned=False); b2=mi(C,[0],[1],132)
print(a,b,a2,b2); json.dump(dict(gcmi_joint=a,ours_joint=b,gcmi_single=a2,ours_single=b2),open('pid/parity_gcmi.json','w'))
