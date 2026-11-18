import json,pandas as pd,numpy as np; from eca import eca
R=json.load(open('home_repro.json')); out={}
for k,f,a,b in [('ex1','home_ex1_bin.csv','Fl','TT'),('ex2','home_ex2_bin.csv','carb','sorghum')]:
    D=pd.read_csv(f); o=eca(D[a].values,D[b].values)
    r=R[k]; out[k]=dict(py=o, R={kk:r[kk] for kk in r})
    print(k,o['rp'],r['precursor coincidence rate'],o['rt'],r['trigger coincidence rate'],o['p_prec_pois'],r['p-value precursor'],o['p_trig_pois'],r['p-value trigger'])
json.dump(out,open('parity_home.json','w'),indent=1,default=float)
