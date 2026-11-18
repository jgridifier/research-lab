# Build STEM input files from the SYNTHETIC Q2 mock ZBB datasets (balanced programs, log actuals).
import pandas as pd, numpy as np, json
SRC='/workspace/q2-mock-zbb/output/'
rng=np.random.default_rng(20261118)
meta={}
for f in ['Corning_mock','MorganStanley_mock']:
    h=pd.read_csv(SRC+f+'/history.csv'); g=json.load(open(SRC+f+'/ground_truth.json'))
    yrs=sorted(h.fiscal_year.unique()); A=h.pivot(index='program_id',columns='fiscal_year',values='actual_usd')
    B=h.pivot(index='program_id',columns='fiscal_year',values='budget_usd')
    bal=A.dropna().index.intersection(B.dropna().index); A=A.loc[bal]; B=B.loc[bal]
    LA=np.log(A); LB=np.log(B)
    T=pd.DataFrame({p:{int(y):v['true_usd'] for y,v in g['true_levels_by_program_year'][p].items()} for p in bal}).T[yrs]
    LT=np.log(T.astype(float))
    # pure-noise version: each program's own values in a random order (destroys any shared time pattern)
    LN=LA.apply(lambda r: pd.Series(rng.permutation(r.values),index=r.index),axis=1)
    for nm,X in [('actual',LA),('budget',LB),('true',LT),('shuffled',LN)]:
        out=X.copy(); out.columns=[str(c) for c in out.columns]; out.insert(0,'Gene Symbol',out.index)
        out.to_csv(f'{f}_{nm}.txt',sep='\t',index=False,float_format='%.6f')
    meta[f]={'years':[int(y) for y in yrs],'n_programs':int(len(h.program_id.unique())),'n_balanced':int(len(bal))}
json.dump(meta,open('prep_meta.json','w'),indent=1); print(meta)
