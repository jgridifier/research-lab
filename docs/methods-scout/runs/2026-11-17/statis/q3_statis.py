import pandas as pd, numpy as np, json, itertools
from statis_np import statis, rv, rv_mod
P=pd.read_csv('q3_pim_panel.csv')
V=['drawdown','income_pretax_net_rate','loss_total_loan_rate','cet1_start','payout_rwa','div_rwa','bb_rwa']
LAB=['CET1 drawdown','SA pre-tax income','SA loan losses','Start CET1','Payout/RWA','Dividends/RWA','Net buybacks/RWA']
years=sorted(P.year.unique()); out={'years':[int(y) for y in years],'vars':LAB}
def corr_y(D): return D[V].dropna().rank().corr().values
mats=[corr_y(P[P.year==y]) for y in years]; nfirm=[int(P[P.year==y][V].dropna().shape[0]) for y in years]
out['n_firms']=nfirm
res=statis(mats)
out['alpha']=res['alpha'].tolist(); out['C']=res['C'].round(4).tolist(); out['C_eig_share']=(res['C_eig']/res['C_eig'].sum()).round(4).tolist()
out['tau']=res['tau'].round(4).tolist()
rvc=[rv(s,res['Splus']) for s in res['S']]; out['rv_to_compromise']=rvc
print('n firms',dict(zip(years,nfirm))); print('alpha',dict(zip(years,res['alpha'].round(3))))
print('RV to compromise',dict(zip(years,np.round(rvc,3)))); print('compromise tau',res['tau'].round(3))
# B1: era split permutation (exact, all C(13,6))
C=res['C']; K=len(years)
def D_stat(post):
    post=np.array(post); pre=np.setdiff1d(np.arange(K),post)
    w=[C[a,b] for g in (pre,post) for a,b in itertools.combinations(g,2)]
    btw=[C[a,b] for a in pre for b in post]; return np.mean(w)-np.mean(btw)
post_obs=[i for i,y in enumerate(years) if y>=2020]; Dobs=D_stat(post_obs)
allD=np.array([D_stat(c) for c in itertools.combinations(range(K),len(post_obs))])
p=float(np.mean(allD>=Dobs-1e-12)); rank_best=int(np.sum(allD>Dobs+1e-12))+1
out['B1']=dict(D=Dobs,p_exact=p,n_assign=len(allD),rank=rank_best)
print('B1 D',round(Dobs,4),'p',p,'rank',rank_best,'of',len(allD))
# same with modified RV and without double-centering
for nm,kw in [('modRV',dict(rvfun=rv_mod)),('nocenter',dict(center=False))]:
    r2=statis(mats,**kw); C2=r2['C']
    def D2(post):
        post=np.array(post); pre=np.setdiff1d(np.arange(K),post)
        w=[C2[a,b] for g in (pre,post) for a,b in itertools.combinations(g,2)]; btw=[C2[a,b] for a in pre for b in post]; return np.mean(w)-np.mean(btw)
    d=D2(post_obs); aD=np.array([D2(c) for c in itertools.combinations(range(K),len(post_obs))])
    out['B1_'+nm]=dict(D=d,p_exact=float(np.mean(aD>=d-1e-12)),rv_to_comp=[ (rv_mod if nm=='modRV' else rv)(s,r2['Splus']) for s in r2['S']])
    print('B1',nm,round(d,4),out['B1_'+nm]['p_exact'])
# best 2-era split among contiguous splits
cont=[]
for cut in range(2,K-1):
    post=list(range(cut,K)); cont.append((int(years[cut]),D_stat(post)))
out['contiguous_splits']=cont; print('contiguous split D by first post year',[(y,round(d,3)) for y,d in cont])
# year interstructure map coords (first two eigvecs of C scaled)
ev,U=np.linalg.eigh(C); o=np.argsort(ev)[::-1]; G=U[:,o[:2]]*np.sqrt(ev[o[:2]]); G[:,0]*=np.sign(G[:,0].sum())
out['year_map']=G.round(4).tolist()
# B2: firm bootstrap within year
rng=np.random.default_rng(20261117); B=299; Sp=res['Splus']
from statis_np import dcenter
boot=np.zeros((K,B))
for k,y in enumerate(years):
    D=P[P.year==y][V].dropna().values; n=len(D)
    for b in range(B):
        idx=rng.integers(0,n,n); Db=pd.DataFrame(D[idx]).rank().corr().values
        if np.isnan(Db).any(): boot[k,b]=np.nan; continue
        s=dcenter(Db); s=s/np.linalg.eigvalsh(s)[-1]; boot[k,b]=rv(s,Sp)
lo=np.nanquantile(boot,0.025,axis=1); hi=np.nanquantile(boot,0.975,axis=1)
dep=[]
for k in range(K):
    others=np.median([rvc[j] for j in range(K) if j!=k]); dep.append(bool(hi[k]<others))
out['B2']=dict(lo=lo.tolist(),hi=hi.tolist(),departs=dep)
print('B2 95% band RV->comp',[(y,round(a,3),round(b,3),d) for y,a,b,d in zip(years,lo,hi,dep)])
# B3: which variable moves most (partial points vs compromise, dims 1-2)
F=res['F'][:,:2]; Fk=res['Fk'][:,:,:2]
mv=np.linalg.norm(Fk-F[None],axis=2)  # K x I
out['var_move']=dict(zip(LAB,mv.sum(0).round(4).tolist())); print('var move',out['var_move'])
out['F']=F.round(4).tolist(); out['Fk']=Fk.round(4).tolist()
# era partial configurations and cosine between payout and drawdown etc.
a=res['alpha']; pre=[k for k,y in enumerate(years) if y<2020]; post=[k for k,y in enumerate(years) if y>=2020]
Fk3=res['Fk'][:,:,:3]
def era(ix): w=a[ix]/a[ix].sum(); return np.tensordot(w,Fk3[ix],1)
Epre,Epost=era(pre),era(post)
def cos(M,i,j): return float(M[i]@M[j]/np.linalg.norm(M[i])/np.linalg.norm(M[j]))
pairs={}
for i,j in itertools.combinations(range(len(V)),2):
    pairs[f'{LAB[i]} ~ {LAB[j]}']=(cos(Epre,i,j),cos(Epost,i,j))
chg=sorted(pairs.items(),key=lambda kv:-abs(kv[1][1]-kv[1][0]))
out['pair_cos_change']=[(k,round(v[0],3),round(v[1],3)) for k,v in chg]
print('largest era changes in compromise-space cosine'); [print(' ',x) for x in out['pair_cos_change'][:8]]
# raw era-mean Spearman for the same pairs (for comparison)
rawpre=np.mean([mats[k] for k in pre],0); rawpost=np.mean([mats[k] for k in post],0)
out['raw_pair_change']=[(f'{LAB[i]} ~ {LAB[j]}',round(rawpre[i,j],3),round(rawpost[i,j],3)) for i,j in itertools.combinations(range(len(V)),2)]
# standard comparator: year-by-year Spearman payout/RWA vs drawdown with firm bootstrap band
std=[]
for y in years:
    D=P[P.year==y][['payout_rwa','drawdown']].dropna(); r=D.rank().corr().iloc[0,1]; bs=[]
    for b in range(999):
        Db=D.sample(len(D),replace=True,random_state=int(rng.integers(1e9))); bs.append(Db.rank().corr().iloc[0,1])
    std.append(dict(year=int(y),rho=float(r),lo=float(np.nanquantile(bs,0.025)),hi=float(np.nanquantile(bs,0.975))))
out['std_rho_payout_drawdown']=std; print(pd.DataFrame(std).round(3).to_string())
# standard pooled test: era difference in Spearman payout~drawdown (pooled firm-years)
pre_r=P[P.year<2020][['payout_rwa','drawdown']].dropna().rank().corr().iloc[0,1]; post_r=P[P.year>=2020][['payout_rwa','drawdown']].dropna().rank().corr().iloc[0,1]
out['std_pooled_era']=(float(pre_r),float(post_r)); print('pooled era rho',pre_r,post_r)
json.dump(out,open('q3_statis.json','w'),indent=1,default=float)
