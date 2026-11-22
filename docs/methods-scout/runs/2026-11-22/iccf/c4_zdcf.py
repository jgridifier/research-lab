import numpy as np, pandas as pd, json, os, warnings
from pyzdcf import pyzdcf
from q1_iccf import get, detrend
warnings.filterwarnings('ignore'); os.makedirs('zdcf_in',exist_ok=True); os.makedirs('zdcf_out',exist_ok=True); out={}
for P,(k1,k2) in {'P1':('pb','fails'),'P5':('rr','dvp'),'P2':('pb','tri')}.items():
    d1=get(k1); d2=get(k2); a=max(d1.date.min(),d2.date.min()); b=min(d1.date.max(),d2.date.max())
    d1=d1[(d1.date>=a)&(d1.date<=b)]; d2=d2[(d2.date>=a)&(d2.date<=b)]
    for n,d in [('lc1',d1),('lc2',d2)]:
        y=detrend(d.t.values,d.y.values); pd.DataFrame({'t':d.t.astype(int),'y':y,'e':np.full(len(y),1e-6)}).to_csv(f'zdcf_in/{P}_{n}.csv',header=False,index=False)
    np.random.seed(1)
    r=pyzdcf(input_dir='zdcf_in/',output_dir='zdcf_out/',intr=False,parameters=dict(autocf=False,prefix=P,uniform_sampling=False,omit_zero_lags=True,minpts=0,num_MC=100,lc1_name=f'{P}_lc1.csv',lc2_name=f'{P}_lc2.csv'),sep=',')
    w=r[(r.tau.abs()<=365)]; i=w.dcf.abs().idxmax()
    out[P]=dict(n_bins_in_window=len(w),tau_at_max_abs=float(w.tau[i]),zdcf_at_max=float(w.dcf[i]),tau_sig=[float(w['-sig(tau)'][i]),float(w['+sig(tau)'][i])],dcf_err=[float(w['-err(dcf)'][i]),float(w['+err(dcf)'][i])])
    w.to_csv(f'zdcf_out/{P}_window.csv',index=False)
json.dump(out,open('C4_zdcf.json','w'),indent=1); print(json.dumps(out,indent=1))
