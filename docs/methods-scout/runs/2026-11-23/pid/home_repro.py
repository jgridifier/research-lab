import sys, json, time, numpy as np
sys.path.insert(0,'gpid/src'); sys.path.insert(0,'pid')
import dit
from dit.pid import PID_WB, PID_BROJA, PID_MMI, PID_CCS, PID_dep
from pidcore import mmi_from_cov, barrett_closed
from gpid.mmi_pid import mmi_pid
out={}
xor=dit.Distribution(['000','011','101','110'],[0.25]*4)
andg=dit.Distribution(['000','010','100','111'],[0.25]*4)
def atoms(p):
    return {str(k):float(p.get_pi(k)) for k in p._lattice}
for name,dd in [('XOR',xor),('AND',andg)]:
    out[name]={}
    for M in [PID_WB,PID_MMI,PID_BROJA,PID_CCS,PID_dep]:
        t0=time.time(); p=M(dd,[[0],[1]],[2]); out[name][M.__name__]=atoms(p); out[name][M.__name__]['_sec']=time.time()-t0
print(json.dumps(out,indent=1))
# H2 Barrett closed form vs gpid vs ours
H2=[]
for (a,b,c) in [(0.3,0.5,0.6),(0.2,0.85,0.35),(0.4,-0.3,0.5),(0.3,0.5,0.6*0+0.3/0.5)]:
    C=np.array([[1,a,c],[a,1,b],[c,b,1.]])
    ours=mmi_from_cov(C); clo=barrett_closed(a,b,c) if abs(a)<=abs(c) else None
    g=mmi_pid(C,1,1,1); gp=dict(I1=g[0],I2=g[1],I12=g[2],U1=g[5],U2=g[6],R=g[7],S=g[8])
    H2.append(dict(abc=[a,b,c],ours=ours,closed=clo,gpid=gp,max_abs_diff_gpid=max(abs(ours[k]-gp[k]) for k in gp),
                   max_abs_diff_closed=max(abs(ours[k]-clo[k]) for k in clo)))
out['H2']=H2
print(json.dumps(H2,indent=1))
json.dump(out,open('pid/home_repro.json','w'),indent=1)
