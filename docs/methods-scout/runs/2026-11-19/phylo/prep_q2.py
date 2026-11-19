# SYNTHETIC Q2 mock ZBB data -> per-program slopes, label tree and text tree (Newick). Answer key read only for scoring columns.
import pandas as pd, numpy as np, json, re
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.cluster.hierarchy import linkage, to_tree
from scipy.spatial.distance import pdist
SRC='/workspace/q2-mock-zbb/output/'
def slope(M,yrs):
    t=np.array(yrs,float); t=t-t.mean(); return (M-M.mean(1,keepdims=True))@t/(t@t)
def newick_from_linkage(Z,labels):
    root=to_tree(Z)
    def rec(node,parent_h):
        bl=max(parent_h-node.dist,0.0)
        if node.is_leaf(): return f"{labels[node.id]}:{bl:.6f}"
        return f"({rec(node.left,node.dist)},{rec(node.right,node.dist)}):{bl:.6f}"
    return rec(root,root.dist)[:-len(':0.000000')]+';'
def clean(s): return re.sub(r'[^A-Za-z0-9_]','_',s)
leak=re.compile(r'(\$|\d|actual|budget|since|first year|running|miss|percent|million|billion|risen|fallen|grown|declined|shrunk|history)',re.I)
meta={}
for f in ['Corning_mock','MorganStanley_mock']:
    h=pd.read_csv(SRC+f+'/history.csv'); g=json.load(open(SRC+f+'/ground_truth.json')); pr=pd.read_csv(SRC+f+'/programs.csv').set_index('program_id')
    yrs=sorted(h.fiscal_year.unique()); A=h.pivot(index='program_id',columns='fiscal_year',values='actual_usd').dropna()
    ids=list(A.index); LA=np.log(A.values)
    T=pd.DataFrame({p:{int(y):v['true_usd'] for y,v in g['true_levels_by_program_year'][p].items()} for p in ids}).T[yrs]
    LT=np.log(T.values.astype(float))
    k=3
    d=pd.DataFrame({'program_id':ids,'slope':slope(LA,yrs),'slope_true':slope(LT,yrs),
                    'slope_early':slope(LA[:,:k],yrs[:k]),'slope_late':slope(LA[:,-k:],yrs[-k:]),
                    'g_last':LA[:,-1]-LA[:,-2],'g_last_true':LT[:,-1]-LT[:,-2]})
    # walk-forward inputs: data to second-to-last year
    d['slope_tr']=slope(LA[:,:-1],yrs[:-1]); d['g_prev']=LA[:,-2]-LA[:,-3]; d['g_prev2']=LA[:,-3]-LA[:,-4]
    for c in ['segment','subsegment','function','stated_intent','stated_discretionary','stated_cost_type']: d[c]=pr.loc[ids,c].values
    # answer key (scoring only)
    mm={m['program_id']:m['mismatch_type'] for m in g['mismatch_text_vs_numbers']}; d['mismatch']=d.program_id.map(mm).fillna('')
    dr={}
    for x in g['category_drift']: dr.setdefault(x['program_id'],[]).append(f"{x['field']}:{x['year']}")
    d['drift']=d.program_id.map(lambda p:';'.join(dr.get(p,[])))
    cl={}
    for c in g['latent_clusters']:
        for m in c['members']: cl[m['program_id']]=c['cluster_id']
    d['cluster']=d.program_id.map(cl).fillna('')
    d['tip']=[clean(p) for p in ids]
    # label tree: firm > segment > subsegment > function > stated_intent > program, unit branch lengths (ultrametric)
    def lab_tree(df):
        def grp(sub,levels):
            if not levels: return ','.join(f"{t}:1" for t in sub.tip)
            parts=[]
            for v,s in sub.groupby(levels[0],sort=True):
                inner=grp(s,levels[1:])
                parts.append(f"({inner}):1" if len(s)>1 or levels[1:] else f"{s.tip.iloc[0]}:{1+len(levels[1:])}")
            return ','.join(parts)
        return '('+grp(df,['segment','subsegment','function','stated_intent'])+');'
    open(f'{f}_label.nwk','w').write(lab_tree(d))
    # text tree: descriptions with numeric-history sentences removed
    docs=[]
    for p in ids:
        sents=re.split(r'(?<=[.!?])\s+',pr.loc[p,'description'])
        docs.append(' '.join(s for s in sents if not leak.search(s)))
    V=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True); X=V.fit_transform(docs)
    Z=linkage(pdist(X.toarray(),'cosine'),'average')
    open(f'{f}_text.nwk','w').write(newick_from_linkage(Z,list(d.tip)))
    d.to_csv(f'{f}_q2.csv',index=False)
    meta[f]={'years':[int(y) for y in yrs],'n_balanced':len(ids),'n_mismatch':int((d.mismatch!='').sum()),'n_drift':int((d.drift!='').sum()),
             'kept_words_mean':float(np.mean([len(x.split()) for x in docs])),'orig_words_mean':float(pr.loc[ids,'description'].str.split().str.len().mean()),'tfidf_terms':int(X.shape[1])}
json.dump(meta,open('prep_meta.json','w'),indent=1); print(json.dumps(meta,indent=1))
