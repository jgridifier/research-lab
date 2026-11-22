# SYNTHETIC Q2 mock ZBB -> budget-miss ratios x = actual/budget per program-year + region labels. Answer key only in *_truth.csv (scoring).
import pandas as pd, numpy as np, json, re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
SRC='/workspace/q2-mock-zbb/output/'
leak=re.compile(r'(\$|\d|actual|budget|since|first year|running|miss|percent|million|billion|risen|fallen|grown|declined|shrunk|history)',re.I)
rng=np.random.default_rng(20261122); meta={}
def merge_small(lab,size,minn=5):
    lab=lab.copy()
    while True:
        vc=lab.value_counts(); small=vc[vc<minn]
        if small.empty or len(vc)==1: return lab
        g=small.index[0]; ms=size.groupby(lab).mean(); others=ms.drop(g)
        lab[lab==g]=(others-ms[g]).abs().idxmin()
for f in ['Corning_mock','MorganStanley_mock']:
    h=pd.read_csv(SRC+f+'/history.csv'); pr=pd.read_csv(SRC+f+'/programs.csv').set_index('program_id'); g=json.load(open(SRC+f+'/ground_truth.json'))
    h['x']=h.actual_usd/h.budget_usd
    n=h.groupby('program_id').size(); keep=n[n>=4].index
    h=h[h.program_id.isin(keep)].sort_values(['program_id','fiscal_year'])
    h[['program_id','fiscal_year','x']].to_csv(f'{f}_x.csv',index=False)
    P=pd.DataFrame(index=keep); P['n']=n[keep]
    P['size_m']=h.groupby('program_id').actual_usd.mean()/1e6
    P['band']=pd.cut(P.size_m,[0,3,8,np.inf],right=False,labels=['lt3m','3to8m','ge8m']).astype(str)
    for c in ['function','segment','stated_discretionary','stated_cost_type','stated_intent']: P[c]=pr.loc[keep,c].values
    P['reg_A']=merge_small(P.function.astype(str),np.log(P.size_m))
    P['reg_B']=P.stated_discretionary+'|'+P.band
    P['reg_B']=merge_small(P.reg_B,np.log(P.size_m))
    docs=[' '.join(s for s in re.split(r'(?<=[.!?])\s+',pr.loc[p,'description']) if not leak.search(s)) for p in keep]
    X=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True).fit_transform(docs)
    P['reg_C']=['T%02d'%k for k in KMeans(30,n_init=10,random_state=20261122).fit_predict(X)]
    P['reg_C']=merge_small(P.reg_C,np.log(P.size_m))
    P['reg_D']=rng.permutation(P.reg_B.values)
    sig=pd.read_csv(f'{f}_true_sigma.csv',index_col=0).sigma
    T=pd.DataFrame(index=keep); T['sigma']=sig[keep]; T['reg_O']=['s%.3f'%v for v in T.sigma]
    T['logq90_true']=0.02-0.255*T.sigma**2+1.2816*1.22066*T.sigma
    T['sd_true']=1.22066*T.sigma
    mm={m['program_id']:m['mismatch_type'] for m in g['mismatch_text_vs_numbers']}; T['mismatch']=pd.Series(mm).reindex(keep).fillna('').values
    P.to_csv(f'{f}_programs_regions.csv'); T.to_csv(f'{f}_truth.csv')
    meta[f]=dict(n_programs=len(keep),n_dropped_lt4=int((n<4).sum()),rows=len(h),years=[int(h.fiscal_year.min()),int(h.fiscal_year.max())],
      n_regions={c:int(P[c].nunique()) for c in ['reg_A','reg_B','reg_C','reg_D']}, n_oracle=int(T.reg_O.nunique()),
      reg_B_sizes=P.reg_B.value_counts().to_dict(), mismatch_counts=T.mismatch.value_counts().to_dict())
json.dump(meta,open('prep_meta.json','w'),indent=1); print(json.dumps(meta,indent=1))
