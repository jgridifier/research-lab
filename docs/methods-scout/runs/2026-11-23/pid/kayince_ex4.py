# Kay & Ince (2018, arXiv:1803.02030) Example 4: population p=-0.2, q=0.7, r=-0.7 and their sample estimates.
import sys, json, numpy as np
sys.path.insert(0,'pid'); from pidcore import idep_from_corr, mmi_from_cov
res={}
for lab,(p,q,r) in {'ex4_pop':(-0.2,0.7,-0.7),'ex4_sample':(-0.1125,0.6492,-0.6915)}.items():
    C=np.array([[1,q,r],[q,1,p],[r,p,1]]); res[lab]=dict(idep=idep_from_corr(p,q,r),mmi=mmi_from_cov(C))
    print(lab,{k:round(float(v),4) for k,v in res[lab]['idep'].items()},{k:round(float(v),4) for k,v in res[lab]['mmi'].items()})
json.dump(res,open('pid/home_repro_kayince.json','w'),indent=1,default=float)
