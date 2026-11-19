import json, numpy as np, pandas as pd, warnings
from scipy.stats import spearmanr, kendalltau
from prep_lib import load, dom, S
from lattice import exact
warnings.filterwarnings('ignore')
rng=np.random.default_rng(20261119)
P=load(); P=P[P.payout_rwa.notna()].copy()
RJ=json.load(open('parity_real_R.json'))
out={'n_firm_years':int(len(P)),'years':{}}
# ---- per-year structures
Y={}
for y,g in P.groupby('year'):
    g=g.reset_index(drop=True); M=dom(g[S].values); tot,R,e,ni=exact(M)
    Y[y]=dict(g=g,M=M,R=R,e=e)
# parity vs R on real posets (R had all firms incl. 4 rows without payout)
P0=load(); par=[]
for y,g in P0.groupby('year'):
    M=dom(g[S].values); _,_,e,_=exact(M); par.append(float(np.max(np.abs(e-np.array(RJ[str(y)]['expected'])))))
out['parity_expected_rank_max_abs_vs_netrankr']=max(par)
# ---- composites (higher = more stressed)
def zs(x): return (x-x.mean())/x.std(ddof=0)
for y,d in Y.items():
    g=d['g']; Z=np.column_stack([zs(g[c].values) for c in S])
    d['ew']=Z.mean(1)
    u,s,vt=np.linalg.svd(Z,full_matrices=False); pc=Z@vt[0]; d['pc1']=pc*np.sign(np.corrcoef(pc,d['ew'])[0,1])
# pooled OLS composite (in-sample, uses payouts) 
X=np.column_stack([np.ones(len(P))]+[P[c].values for c in S]); b=np.linalg.lstsq(X,P.payout_rwa.values,rcond=None)[0]
out['pooled_ols_coef']=dict(zip(['const']+S,[float(v) for v in b]))
for y,d in Y.items(): d['ols']=-(np.column_stack([np.ones(len(d['g']))]+[d['g'][c].values for c in S])@b)  # higher = more stressed (lower fitted payout)
# ---- A1 dominance concordance
def conc(M,pay):
    i,j=np.nonzero(M)  # i less stressed than j
    if len(i)==0: return np.nan,0
    c=(pay[j]<pay[i]).astype(float)+0.5*(pay[j]==pay[i]); return c.mean(),len(i)
def a1(col):
    obs=[];npairs=0;stats={}
    for y,d in Y.items():
        pay=d['g'][col].values; ok=~np.isnan(pay)
        M=d['M'][np.ix_(ok,ok)]; p=pay[ok]; i,j=np.nonzero(M)
        obs.append(((p[j]<p[i])+0.5*(p[j]==p[i])).sum()); npairs+=len(i)
    C=sum(obs)/npairs
    nulls=[]
    for r in range(4999):
        s=0
        for y,d in Y.items():
            pay=d['g'][col].values; ok=~np.isnan(pay); M=d['M'][np.ix_(ok,ok)]; p=rng.permutation(pay[ok]); i,j=np.nonzero(M)
            s+=((p[j]<p[i])+0.5*(p[j]==p[i])).sum()
        nulls.append(s/npairs)
    nulls=np.array(nulls)
    return dict(C=float(C),pairs=int(npairs),null_mean=float(nulls.mean()),null_q95=float(np.quantile(nulls,.95)),p=float((1+(nulls>=C).sum())/5000))
out['A1_same_year']=a1('payout_rwa'); out['A1_next_year']=a1('payout_rwa_next')
# incomparable share per year and standard composites: Spearman & all-pairs Kendall concordance
rows=[]
for y,d in Y.items():
    g=d['g']; n=len(g); comp=d['M'].sum(); pairs=n*(n-1)/2; pay=g.payout_rwa.values
    r=dict(year=int(y),n=n,comparable_frac=comp/pairs,incomparable_frac=1-comp/pairs)
    for k in ['ew','pc1','ols']: r['spearman_'+k]=spearmanr(d[k],pay).correlation
    r['spearman_expected_rank']=spearmanr(d['e'],pay).correlation
    # among dominance pairs vs incomparable pairs: how often does EW composite order agree with payout (more stressed pays less)
    inc_agree=[];dom_agree=[]
    for i in range(n):
        for j in range(i+1,n):
            hi,lo=(i,j) if d['ew'][i]>d['ew'][j] else (j,i)
            a=float(pay[hi]<pay[lo])+0.5*(pay[hi]==pay[lo])
            (dom_agree if (d['M'][i,j] or d['M'][j,i]) else inc_agree).append(a)
    r['ew_agree_dominance_pairs']=np.mean(dom_agree); r['ew_agree_incomparable_pairs']=np.mean(inc_agree) if inc_agree else np.nan
    r['n_dom']=len(dom_agree); r['n_inc']=len(inc_agree)
    R=d['R']; ks=np.arange(1,n+1); sd=np.sqrt((R*ks**2).sum(1)-d['e']**2)
    lo=np.array([ks[R[u]>1e-12].min() for u in range(n)]); hi=np.array([ks[R[u]>1e-12].max() for u in range(n)])
    r['mean_interval_width_over_n']=float(((hi-lo+1)/n).mean()); r['mean_rank_sd']=float(sd.mean()); r['mean_rank_sd_over_n']=float((sd/n).mean())
    d['lo']=lo;d['hi']=hi;d['sd']=sd
    rows.append(r)
T=pd.DataFrame(rows); T.to_csv('A1_A2_by_year.csv',index=False)
# pooled agree rates
dd=T.n_dom.sum(); ii=T.n_inc.sum()
out['A1_ew_agree_dominance']=float((T.ew_agree_dominance_pairs*T.n_dom).sum()/dd); out['A1_ew_agree_incomparable']=float((T.ew_agree_incomparable_pairs*T.n_inc).sum()/ii)
out['incomparable_frac_mean']=float(T.incomparable_frac.mean()); out['incomparable_frac_range']=[float(T.incomparable_frac.min()),float(T.incomparable_frac.max())]
out['mean_spearman']={k:float(T['spearman_'+k].mean()) for k in ['ew','pc1','ols','expected_rank']}
out['rank_ambiguity']={'mean_interval_width_over_n':float(T.mean_interval_width_over_n.mean()),'mean_rank_sd':float(T.mean_rank_sd.mean()),'mean_rank_sd_over_n':float(T.mean_rank_sd_over_n.mean())}
# permutation test on incomparable vs dominance agreement difference (EW composite) -- descriptive null
json.dump(out,open('q3_poset_A1A2.json','w'),indent=1,default=float)
import pickle; pickle.dump({y:{k:v for k,v in d.items() if k!='g'}|{'ids':d['g'].id_rssd.tolist(),'names':d['g'].disclosure_legal_name.tolist(),'pay':d['g'].payout_rwa.tolist(),'scb':d['g'].scb.tolist(),'X':d['g'][S].values.tolist()} for y,d in Y.items()},open('Y.pkl','wb'))
print(json.dumps(out,indent=1,default=float)); print(T.round(3).to_string())
