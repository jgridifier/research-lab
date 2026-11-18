import json,numpy as np,pandas as pd
from statis_np import rv
out={}
for nm in ['w1','w2']:
    D=pd.read_csv(f'bal_{nm}.csv',index_col=0); n=len(D); K=D.shape[1]//7
    names=pd.read_csv(f'bal_{nm}_names.csv').set_index('id_rssd').disclosure_legal_name
    W=[]
    for k in range(K):
        X=D.iloc[:,7*k:7*k+7].values; X=(X-X.mean(0))/X.std(0); Wk=X@X.T/n; W.append(Wk/np.sqrt(np.trace(Wk@Wk)))
    C=np.array([[rv(a,b) for b in W] for a in W]); ev,U=np.linalg.eigh(C); u=U[:,-1]*np.sign(U[:,-1].sum()); a=u/u.sum()
    Wc=sum(x*w for x,w in zip(a,W)); lam,Q=np.linalg.eigh(Wc); o=np.argsort(lam)[::-1]; lam=lam[o][:2]; Q=Q[:,o][:,:2]
    F=Q*np.sqrt(lam); Fk=np.stack([w@Q/np.sqrt(lam) for w in W])
    step=np.linalg.norm(np.diff(Fk,axis=0),axis=2).sum(0)  # path length per firm
    # standard: total absolute change in payout/RWA rank across years
    pr=np.stack([D.iloc[:,7*k+4].values for k in range(K)]); rk=np.abs(np.diff(pr,axis=0)).sum(0)
    from scipy.stats import spearmanr
    r=spearmanr(step,rk).correlation
    df=pd.DataFrame({'firm':[names.get(int(i),str(i)) for i in D.index],'path':step,'payout_rank_change':rk}).sort_values('path',ascending=False)
    out[nm]=dict(n=n,years=list(D.columns[::7].str[-4:]),RV=C.round(4).tolist(),tau2=(lam/np.linalg.eigvalsh(Wc).clip(0).sum()).round(4).tolist(),
                 top=df.head(5).round(3).to_dict('records'),spearman_path_vs_payoutrank=float(r),F=F.round(4).tolist(),Fk=Fk.round(4).tolist(),
                 firms=[names.get(int(i),str(i)) for i in D.index])
    print(nm,n,'tau12',out[nm]['tau2'],'rho(path, payout-rank change)',round(r,3)); print(df.head(6).round(3).to_string())
json.dump(out,open('q3_firms.json','w'),indent=1,default=float)
