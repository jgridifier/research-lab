# Score STEM (stem.jar 1.3.15 batch output) against the planted answer key of the SYNTHETIC Q2 mocks,
# with k-means and OLS-slope comparators. Answer key used only for scoring.
import pandas as pd, numpy as np, json, glob
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, roc_auc_score
SRC='/workspace/q2-mock-zbb/output/'; R={}
def load(f,nm,c):
    p=pd.read_csv(f'bout/{f}_{nm}_c{c}_profiletable.txt',sep='\t'); g=pd.read_csv(f'bout/{f}_{nm}_c{c}_genetable.txt',sep='\t')
    return p,g
def f1(pred,truth):
    tp=len(pred&truth); 
    if tp==0: return 0,0,0
    pr=tp/len(pred); rc=tp/len(truth); return 2*pr*rc/(pr+rc),pr,rc
for f in ['Corning_mock','MorganStanley_mock']:
    gt=json.load(open(SRC+f+'/ground_truth.json')); progs=pd.read_csv(SRC+f+'/programs.csv').set_index('program_id')
    out={}
    for nm in ['actual','true','shuffled','budget','actrep']:
        for c in ([1,2] if nm!='actrep' else [1]):
            p,g=load(f,nm,c); sig=p[p['Cluster (-1 non-significant)']!=-1]
            gs=g.set_index('Gene Symbol')
            out[f'{nm}_c{c}']={'n_sig_profiles':int(len(sig)),'n_clusters':int(sig['Cluster (-1 non-significant)'].nunique()),
                'programs_in_sig':float(sig['# Genes Assigned'].sum()),'n':int(len(g)),
                'sig_profiles':[[int(r['Profile ID']),r['Profile Model'],float(r['# Genes Assigned']),float(r['# Gene Expected']),float(r['p-value']),int(r['Cluster (-1 non-significant)'])] for _,r in sig.sort_values('# Genes Assigned',ascending=False).iterrows()]}
    # ---- S1 structure: planted clusters split by loading sign
    p,g=load(f,'actual',1); sigp=p[p['Cluster (-1 non-significant)']!=-1]
    g=g.set_index('Gene Symbol'); X=pd.read_csv(f'{f}_actual.txt',sep='\t').set_index('Gene Symbol'); ids=set(X.index)
    prof_members={int(k):set(v.index) for k,v in g.groupby('Profile')}
    clus={}
    for _,r in sigp.iterrows(): clus.setdefault(int(r['Cluster (-1 non-significant)']),set()).update(prof_members.get(int(r['Profile ID']),set()))
    units={('P',k):v for k,v in prof_members.items() if k in set(sigp['Profile ID'])}; units.update({('C',k):v for k,v in clus.items()})
    # k-means comparator on z-scored log series, k by silhouette 2..10
    Z=X.sub(X.mean(1),axis=0).div(X.std(1)+1e-12,axis=0).values
    best=None
    for k in range(2,11):
        km=KMeans(k,n_init=20,random_state=1).fit(Z); s=silhouette_score(Z,km.labels_)
        if best is None or s>best[0]: best=(s,k,km.labels_)
    km_units={k:set(X.index[best[2]==k]) for k in range(best[1])}
    # k-means with k forced to the number of STEM significant profiles (fairness check)
    ks=max(2,len(sigp)); km2=KMeans(ks,n_init=20,random_state=1).fit(Z); km2_units={k:set(X.index[km2.labels_==k]) for k in range(ks)}
    # category mix comparator: segment x function cells
    cat=progs.loc[list(ids)]; cat_units={k:set(v.index) for k,v in cat.groupby(['segment','function'])}
    S1=[]
    for cl in gt['latent_clusters']:
        for sgn in [1,-1]:
            tr={m['program_id'] for m in cl['members'] if np.sign(m['loading'])==sgn}&ids
            if len(tr)<10: continue
            def bestf(U): 
                b=max(((f1(v,tr),k) for k,v in U.items()),key=lambda z:z[0][0]); return {'f1':round(b[0][0],3),'prec':round(b[0][1],3),'rec':round(b[0][2],3),'unit':str(b[1])}
            S1.append({'cluster':cl['cluster_id'],'sign':sgn,'n_true_balanced':len(tr),'stem':bestf(units),'kmeans_sil':bestf(km_units),'kmeans_kSTEM':bestf(km2_units),'category':bestf(cat_units)})
    out['S1']=S1; out['kmeans_k']=int(best[1]); out['kmeans_sil']=round(float(best[0]),3); out['kmeans_k_forced']=ks
    # ---- S3 text vs numbers: stated grow/transform programs that are planted 'growth actually declining'
    mm={m['program_id'] for m in gt['mismatch_text_vs_numbers'] if m['mismatch_type']=='stated_growth_actually_declining'}&ids
    sub=progs.loc[list(ids)]; sub=sub[sub.stated_intent.isin(['grow','transform'])].index
    y=np.array([1 if i in mm else 0 for i in sub])
    t=np.array(X.columns,dtype=float); slopes=pd.Series({i:np.polyfit(t,X.loc[i].values,1)[0] for i in sub})
    falling={int(r['Profile ID']) for _,r in sigp.iterrows() if float(r['Profile Model'].split(',')[-1])<0}
    stemflag=pd.Series({i:1 if int(g.loc[i,'Profile']) in falling else 0 for i in sub})
    nflag=int(stemflag.sum()); top=set(slopes.sort_values().index[:nflag]) if nflag>0 else set()
    out['S3']={'n_stated_grow_transform':int(len(sub)),'n_planted_mismatch':int(y.sum()),'stem_flagged':nflag,
        'stem_hits':int(sum(1 for i in sub if stemflag[i] and i in mm)),'ols_hits_matched':int(len(top&mm)),
        'auc_ols_slope':round(float(roc_auc_score(y,-slopes.values)),3) if y.sum()>0 else None}
    R[f]=out
json.dump(R,open('stem_q2_results.json','w'),indent=1)
for f,o in R.items():
    print('==',f); 
    for k,v in o.items():
        if k.endswith(('c1','c2')): print(k,{kk:vv for kk,vv in v.items() if kk!='sig_profiles'})
    print('kmeans k',o['kmeans_k'],'sil',o['kmeans_sil'])
    for s in o['S1']: print(s)
    print('S3',o['S3'])
