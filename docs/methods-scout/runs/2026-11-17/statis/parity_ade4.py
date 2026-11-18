import json,numpy as np,pandas as pd
from statis_np import rv
A=json.load(open('ade4_statis.json')); out={}
for nm in ['w1','w2']:
    D=pd.read_csv(f'bal_{nm}.csv',index_col=0); n=len(D); K=D.shape[1]//7
    W=[]
    for k in range(K):
        X=D.iloc[:,7*k:7*k+7].values; X=(X-X.mean(0))/X.std(0)  # population sd, as ade4 scaling with n
        Wk=X@X.T/n; W.append(Wk/np.sqrt(np.trace(Wk@Wk)))
    C=np.array([[rv(a,b) for b in W] for a in W]); ev,U=np.linalg.eigh(C); u=U[:,-1]*np.sign(U[:,-1].sum())
    Wc=sum(ui*w for ui,w in zip(u,W)); lam=np.sort(np.linalg.eigvalsh(Wc))[::-1]
    a=A[nm]; dRV=np.abs(C-np.array(a['RV'])).max(); dw=np.abs(u-np.array(a['tabw'])).max(); de=np.abs(lam[:4]-np.array(a['C.eig'][:4])).max()
    out[nm]=dict(max_dRV=dRV,max_dweights=dw,max_deig=de); print(nm,out[nm])
json.dump(out,open('parity_ade4.json','w'),indent=1,default=float)
