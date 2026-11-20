import numpy as np, pandas as pd, json, sys
sys.path.insert(0,'.'); from lk_port import lkif, var1_t
from scipy.stats import t as tdist
rng=np.random.default_rng(7)
X=pd.read_csv('q1_weekly_lkif.csv',parse_dates=['date']).set_index('date')
V=['dl_fails','d_spread','dl_dvp','dl_tri','d_lev','d_vix']
def fitvar(Z):
    n,d=Z.shape; Zr=np.column_stack([Z[:-1],np.ones(n-1)]); B,*_=np.linalg.lstsq(Zr,Z[1:],rcond=None)
    return B[:d].T,B[d],Z[1:]-Zr@B
def blockboot(E,n,rng,mb=8):
    idx=[]; m=len(E)
    while len(idx)<n:
        s=rng.integers(m); L=rng.geometric(1/mb); idx+= [(s+k)%m for k in range(L)]
    return E[np.array(idx[:n])]
def sim(A,c,E,n,rng,Z0):
    e=blockboot(E,n+50,rng); x=np.zeros((n+50,A.shape[0])); x[0]=Z0
    for t in range(n+49): x[t+1]=c+A@x[t]+e[t]
    return x[50:]
def shiftp(Z,i,j,ns,rng):
    T0=abs(lkif(Z)['T'][i,j]); n=len(Z); c=0
    for s in range(ns):
        Zs=Z.copy(); Zs[:,j]=np.roll(Z[:,j],rng.integers(26,n-26)); c+= abs(lkif(Zs)['T'][i,j])>=T0
    return (c+1)/(ns+1)
full=X[V].dropna(); Z=((full-full.mean())/full.std()).values; n=len(Z)
A,c,E=fitvar(Z)
# (a) size study on 4 edges
edges=[('d_spread','dl_fails'),('d_lev','dl_fails'),('dl_fails','d_spread'),('dl_dvp','dl_fails')]
size={}
for src,tgt in edges:
    i,j=V.index(tgt),V.index(src); A0=A.copy(); A0[i,j]=0; ra=[];rs=[];rt=[]
    for s in range(400):
        x=sim(A0,c,E,n,rng,Z[0]); x=(x-x.mean(0))/x.std(0)
        R=lkif(x); ra.append(R['p'][i,j]<0.05)
        tv=var1_t(x)[i,j]; rt.append(2*tdist.sf(abs(tv),n-8)<0.05)
        if s<200: rs.append(shiftp(x,i,j,99,rng)<0.05)
    size[f'{src}->{tgt}']=dict(asym=float(np.mean(ra)),shift_surrogate=float(np.mean(rs)),var1_t=float(np.mean(rt)),n_sims=[400,200,400])
    print(src,tgt,size[f'{src}->{tgt}'],flush=True)
# (b) model-based (edge-zeroed VAR, block residual bootstrap) p for every edge
T0=lkif(Z)['T']; rows=[]
for i in range(6):
    for j in range(6):
        if i==j: continue
        A0=A.copy(); A0[i,j]=0; cnt=0; B=999
        for s in range(B):
            x=sim(A0,c,E,n,rng,Z[0]); x=(x-x.mean(0))/x.std(0); cnt+= abs(lkif(x)['T'][i,j])>=abs(T0[i,j])
        rows.append(dict(src=V[j],tgt=V[i],p_boot=(cnt+1)/(B+1)))
df=pd.DataFrame(rows); df.to_csv('L1_bootp.csv',index=False)
json.dump(size,open('L3_size.json','w'),indent=1)
print(df.sort_values('p_boot').head(8).to_string())
