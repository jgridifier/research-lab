"""Baseline ladder on TRAIN -> VALIDATION only. Never reads test_labels or holdout.
Metrics: AUC (classification) / MAE (regression), 95% entity-cluster bootstrap CI (B=500; 200 for val sets >50k rows)."""
import pandas as pd, numpy as np, json, lightgbm as lgb, warnings; warnings.filterwarnings('ignore')
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline; from sklearn.impute import SimpleImputer; from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, mean_absolute_error
TASKS={'bank-deposit-decline':('CERT','clf',lambda d:-d.s_dep_g.fillna(0)),
 'branch-closure':('CERT','clf',lambda d:-d.s_dep_g1.fillna(0)),
 'complaint-spike':('company','clf',lambda d:d.s_ratio_med6.fillna(1)),
 'hmda-share-drop':('lei','clf',lambda d:-d.s_share_g.fillna(0)),
 'hc-state-deposit-growth':('RSSDHCR','reg',lambda d:np.zeros(len(d)))}
P=dict(n_estimators=400,learning_rate=0.03,num_leaves=31,min_child_samples=50,subsample=0.8,subsample_freq=1,colsample_bytree=0.8,random_state=0,verbose=-1)
def metric(kind,y,p): return roc_auc_score(y,p) if kind=='clf' else mean_absolute_error(y,p)
def boot(kind,y,preds,grp,B=None,seed=0):
    B=B or (200 if len(y)>50000 else 500)
    rng=np.random.default_rng(seed); u=np.unique(grp); idx={g:np.where(grp==g)[0] for g in u}; out={k:[] for k in preds}
    for _ in range(B):
        s=np.concatenate([idx[g] for g in rng.choice(u,len(u))])
        if kind=='clf' and y[s].min()==y[s].max(): continue
        for k,p in preds.items(): out[k].append(metric(kind,y[s],p[s]))
    return {k:np.array(v) for k,v in out.items()}
res=[]
for t,(ent,kind,naive) in TASKS.items():
    d=pd.read_parquet(f'tasks/{t}/trainval.parquet'); tr=d[d.split=='train']; va=d[d.split=='val']
    S=[c for c in d if c.startswith('s_')]; A=S+[c for c in d if c.startswith('r_')]
    ytr=tr.label.values; yva=va.label.values; preds={}
    preds['naive']=np.nan_to_num(np.asarray(naive(va),float).clip(-1e6,1e6))
    if kind=='reg': preds['naive_last_growth']=va.s_g1.fillna(0).clip(-1,1).values
    lin=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=2000,C=1.0) if kind=='clf' else Ridge(1.0))
    Xtr=tr[S].replace([np.inf,-np.inf],np.nan); Xva=va[S].replace([np.inf,-np.inf],np.nan)
    lin.fit(Xtr,ytr); preds['linear_single']=lin.predict_proba(Xva)[:,1] if kind=='clf' else lin.predict(Xva)
    for name,cols in [('lgbm_single',S),('lgbm_relational',A)]:
        m=(lgb.LGBMClassifier if kind=='clf' else lgb.LGBMRegressor)(**P,**({} if kind=='clf' else {'objective':'l1'}))
        m.fit(tr[cols].replace([np.inf,-np.inf],np.nan),ytr)
        preds[name]=m.predict_proba(va[cols].replace([np.inf,-np.inf],np.nan))[:,1] if kind=='clf' else m.predict(va[cols].replace([np.inf,-np.inf],np.nan))
        if name=='lgbm_relational':
            imp=pd.Series(m.booster_.feature_importance('gain'),cols).sort_values(ascending=False); top=list(imp.index[:6])
    if kind=='reg': preds['train_median']=np.full(len(va),np.median(ytr))
    bs=boot(kind,yva,preds,va[ent].astype(str).values)
    dlt=bs['lgbm_relational']-bs['lgbm_single']
    for k,p in preds.items():
        res.append(dict(task=t,metric='AUC' if kind=='clf' else 'MAE',model=k,val=round(metric(kind,yva,p),4),ci_lo=round(np.percentile(bs[k],2.5),4),ci_hi=round(np.percentile(bs[k],97.5),4),n_train=len(tr),n_val=len(va),val_pos_rate=round(yva.mean(),4) if kind=='clf' else None,n_single_feats=len(S),n_rel_feats=len(A)-len(S)))
    res.append(dict(task=t,metric='delta rel-single',model='lgbm_relational - lgbm_single',val=round(metric(kind,yva,preds['lgbm_relational'])-metric(kind,yva,preds['lgbm_single']),4),ci_lo=round(np.percentile(dlt,2.5),4),ci_hi=round(np.percentile(dlt,97.5),4),top_rel_features=','.join(top)))
    print(t,'done')
r=pd.DataFrame(res); r.to_csv('reports/baselines_val.csv',index=False); print(r.drop(columns=['n_single_feats','n_rel_feats'],errors='ignore').to_string())
