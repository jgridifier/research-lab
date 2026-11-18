import pandas as pd, numpy as np, json, sys
sys.path.insert(0,'..'); from stem_port import stem, assign_counts
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
SRC='/workspace/q2-mock-zbb/output/'; out={}
def Zs(X): return ((X.T-X.mean(1))/(X.std(1)+1e-12)).T
for f in ['Corning_mock','MorganStanley_mock']:
    o={}
    A=pd.read_csv(f'{f}_actual.txt',sep='\t').set_index('Gene Symbol'); S=pd.read_csv(f'{f}_shuffled.txt',sep='\t').set_index('Gene Symbol')
    # (a) k-means always finds clusters: best silhouette k and value on actual vs shuffled
    for nm,X in [('actual',A),('shuffled',S)]:
        Z=Zs(X.values); best=max(((silhouette_score(Z,KMeans(k,n_init=20,random_state=1).fit(Z).labels_),k) for k in range(2,11)))
        o[f'kmeans_{nm}']={'k':best[1],'silhouette':round(float(best[0]),3)}
    # (b) does the assigned profile match the noise-free (true-level) profile?
    gt=pd.read_csv(f'bout/{f}_true_c1_genetable.txt',sep='\t').set_index('Gene Symbol')['Profile']
    for nm in ['actual','actrep','budget']:
        g=pd.read_csv(f'bout/{f}_{nm}_c1_genetable.txt',sep='\t').set_index('Gene Symbol')['Profile']
        p=pd.read_csv(f'bout/{f}_{nm}_c1_profiletable.txt',sep='\t'); sig=set(p.loc[p['Cluster (-1 non-significant)']!=-1,'Profile ID'])
        pt=pd.read_csv(f'bout/{f}_true_c1_profiletable.txt',sep='\t')
        # same profile set? (model profiles are data-independent given T and c)
        same=(p['Profile Model'].values==pt['Profile Model'].values).all()
        ins=g[g.isin(sig)]; agree=(ins==gt.loc[ins.index]).mean()
        o[f'agree_{nm}']={'profiles_identical':bool(same),'n_in_sig':int(len(ins)),'share_same_profile_as_true':round(float(agree),3),'all_programs_agree':round(float((g==gt.loc[g.index]).mean()),3)}
    out[f]=o
# (c) power: plant n programs following the AI-cluster factor (Corning years) into the Corning shuffled background
S=pd.read_csv('Corning_mock_shuffled.txt',sep='\t').set_index('Gene Symbol').values
P=np.array([[float(x) for x in s.split(',')] for s in pd.read_csv('bout/Corning_mock_actual_c1_profiletable.txt',sep='\t')['Profile Model']])
F=np.log1p(0.8*np.array([0,0.03,-0.05,0.12,0.28,0.52]))
rng=np.random.default_rng(7); pw={}
for sig_ in [0.05,0.10,0.15]:
    for n in [10,20,40,80]:
        hit=0
        for rep in range(20):
            X=S.copy(); idx=rng.choice(len(X),n,replace=False)
            X[idx]=X[idx,:1]+F+rng.normal(0,sig_,(n,6))
            r=stem(X,P); lab_planted=np.bincount(r['label'][idx],minlength=len(P)).argmax()
            hit+=int(r['sig'][lab_planted])
        pw[f'sigma{sig_}_n{n}']=hit/20
out['power_corning_ai_shape']=pw
json.dump(out,open('stem_q2_extra.json','w'),indent=1); print(json.dumps(out,indent=1))
