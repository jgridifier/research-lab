"""Prep for 2026-11-13 scout. SYNTHETIC mock ZBB data only (q2-mock-zbb, seed 20261113).
Writes per-program observable features (no ground-truth columns) and, separately, an answer-key file
used ONLY for scoring. Noise SD per program is estimated from budget-vs-actual gaps, an observable."""
import json, numpy as np, pandas as pd, sys
SRC='/workspace/q2-mock-zbb/output/'; OUT='/workspace/scout/1113/data/'
ETA=0.70  # budget noise / actual noise ratio, stated in the dataset README ("How the numbers were made")
summ={}
for firm in ['Corning_mock','MorganStanley_mock']:
    P=pd.read_csv(SRC+firm+'/programs.csv'); H=pd.read_csv(SRC+firm+'/history.csv'); G=json.load(open(SRC+firm+'/ground_truth.json'))
    H=H.sort_values(['program_id','fiscal_year'])
    H['y']=np.log(H.actual_usd); H['b']=np.log(H.budget_usd); H['d']=H.b-H.y
    P['group']=P.segment+' | '+P['function']
    # per-program sd of budget-actual gap -> sigma_hat, shrunk toward group pooled value (4 pseudo-obs)
    g=H.groupby('program_id').agg(k=('d','size'),sdd=('d','std'))
    g=g.join(P.set_index('program_id')['group'])
    g['s2']=(g.sdd**2)/(1+ETA**2)
    pooled=g[g.k>=3].groupby('group').s2.median(); allmed=g[g.k>=3].s2.median()
    g['s2g']=g.group.map(pooled).fillna(allmed)
    kk=(g.k-1).clip(lower=0); g['s2']=g.s2.fillna(0)
    g['sigma']=np.sqrt((kk*g.s2+4*g.s2g)/(kk+4))
    yrs=sorted(H.fiscal_year.unique()); last=yrs[-1]; prev=yrs[-2]
    W=H.pivot(index='program_id',columns='fiscal_year',values='y')
    feat=P[['program_id','segment','function','group','stated_cost_type','stated_discretionary','stated_intent','status','start_year','end_year']].set_index('program_id').join(g[['k','sigma']])
    for t in yrs: feat[f'y{t}']=W[t]
    # OLS slope of log actual on year (k>=3)
    def slope(r):
        v=r.dropna();
        if len(v)<3: return pd.Series({'slope':np.nan,'sxx':np.nan})
        x=np.array(v.index,float); x=x-x.mean(); return pd.Series({'slope':float((x*v.values).sum()/(x*x).sum()),'sxx':float((x*x).sum())})
    feat=feat.join(W.apply(slope,axis=1))
    feat.reset_index().to_csv(OUT+f'{firm}_features.csv',index=False)
    # answer key (scoring only)
    T=G['true_levels_by_program_year']
    key=pd.DataFrame([{'program_id':p,'fiscal_year':int(t),'true_usd':v['true_usd'],'true_intent':v['intent']} for p,d in T.items() for t,v in d.items()])
    key.to_csv(OUT+f'{firm}_KEY_true_levels.csv',index=False)
    fam={p:f['family_id'] for f in G['pooling_families'] for p in f['program_ids']}
    mm={m['program_id']:m['mismatch_type'] for m in G['mismatch_text_vs_numbers']}
    cl={}; 
    for c in G['latent_clusters']:
        for m in c['members']: cl[m['program_id']]=(c['cluster_id'],m['loading'],m['text_reveals_cluster'])
    K=pd.DataFrame({'program_id':P.program_id})
    K['family']=K.program_id.map(fam); K['mismatch']=K.program_id.map(mm)
    K['cluster']=K.program_id.map(lambda p:cl.get(p,(None,None,None))[0]); K['loading']=K.program_id.map(lambda p:cl.get(p,(None,None,None))[1]); K['text_reveals']=K.program_id.map(lambda p:cl.get(p,(None,None,None))[2])
    K.to_csv(OUT+f'{firm}_KEY_labels.csv',index=False)
    json.dump({'mix_vs_behavior':G['mix_vs_behavior'],'clusters':[{k:c[k] for k in c if k!='members'} for c in G['latent_clusters']],'noise_model':G['noise_model']},open(OUT+f'{firm}_KEY_summary.json','w'),indent=1)
    summ[firm]={'programs':len(P),'history_rows':len(H),'years':[int(y) for y in yrs],'groups':int(P.group.nunique()),'median_sigma_hat':float(g.sigma.median())}
json.dump(summ,open(OUT+'panel_summary.json','w'),indent=1); print(json.dumps(summ,indent=1))
