# M2 (PREREG.md B): AUC for planted-cluster membership, CA axis-1 score vs OLS slope of log actual. Aggregates only.
import json, numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
K=json.load(open('kairos_mock_results.json')); out={}
for f in K:
    X=pd.read_csv(f'mock_{f}.csv',index_col=0); S=pd.read_csv(f'mockscore_{f}_LOCAL_ONLY.csv').set_index('program_id').loc[X.index]
    yrs=X.columns.astype(int).values; L=np.log(X.values.clip(min=1)); yc=yrs-yrs.mean(); slope=(L-L.mean(1,keepdims=True))@yc/np.sum(yc**2)
    key=json.load(open(f'mockkey_{f}_LOCAL_ONLY.json')); rows={}
    for cid,mem in key.items():
        y=X.index.isin(list(mem)).astype(int)
        a=lambda s: float(max(roc_auc_score(y,s),1-roc_auc_score(y,s)))
        pos=X.index.isin([p for p,l in mem.items() if l>0]).astype(int)
        b=lambda s: float(max(roc_auc_score(pos,s),1-roc_auc_score(pos,s)))
        rows[cid]=dict(n_members_full_history=int(y.sum()),auc_ca1=a(S.ca1.values),auc_slope=a(slope),
                       desc_auc_ca1_pos_loading=b(S.ca1.values),desc_auc_slope_pos_loading=b(slope))
    mc=np.mean([r['auc_ca1'] for r in rows.values()]); ms=np.mean([r['auc_slope'] for r in rows.values()])
    out[f]=dict(M1_porcic_p=K[f]['porcic_p'],M1_pass=K[f]['porcic_p']<0.05,ca1_pct=K[f]['ca1_pct'],n_programs=K[f]['n_programs'],clusters=rows,mean_auc_ca1=mc,mean_auc_slope=ms,M2_pass=bool(mc>=ms+0.03))
json.dump(out,open('tests_mock.json','w'),indent=1,default=float); print(json.dumps(out,indent=1,default=float))
