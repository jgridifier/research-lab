# Post hoc (labelled): on the real (mock) category regions, does H1 rank truly mixed regions above pure ones better than Brown-Forsythe?
import pandas as pd, numpy as np, json
from scipy import stats
from sklearn.metrics import roc_auc_score
out={}
for f in ['Corning_mock','MorganStanley_mock']:
    X=pd.read_csv(f'{f}_x.csv'); X['lx']=np.log(X.x); P=pd.read_csv(f'{f}_programs_regions.csv',index_col=0); T=pd.read_csv(f'{f}_truth.csv',index_col=0); R=pd.read_csv(f'{f}_regions.csv')
    rows=[]
    for sch in ['reg_A','reg_C']:
        for g,idx in P.groupby(sch).groups.items():
            sg=T.loc[idx,'sigma']; top=sg.value_counts(normalize=True).iloc[0]; cv=sg.std()/sg.mean()
            p=stats.levene(*[X.lx[X.program_id==i].values for i in idx],center='median').pvalue
            h=R[(R.scheme==sch)&(R.region==g)].H1.iloc[0]
            rows.append(dict(scheme=sch,region=g,N=len(idx),top_share=top,sigma_cv=cv,mixed=int(top<0.9),H1=h,BF_p=p))
    D=pd.DataFrame(rows); D.to_csv(f'{f}_realregions.csv',index=False)
    out[f]=dict(n_regions=len(D),n_mixed=int(D.mixed.sum()),auc_H1=round(roc_auc_score(D.mixed,D.H1),3),auc_BF=round(roc_auc_score(D.mixed,-np.log(D.BF_p)),3),
        spearman_H1_sigmacv=round(stats.spearmanr(D.H1,D.sigma_cv)[0],3),spearman_BF_sigmacv=round(stats.spearmanr(-np.log(D.BF_p),D.sigma_cv)[0],3),
        H1ge2_in_mixed=round(float((D.H1[D.mixed==1]>=2).mean()),3),H1ge2_in_pure=round(float((D.H1[D.mixed==0]>=2).mean()),3),
        BF05_in_mixed=round(float((D.BF_p[D.mixed==1]<0.05).mean()),3),BF05_in_pure=round(float((D.BF_p[D.mixed==0]<0.05).mean()),3))
json.dump(out,open('realregions_q2.json','w'),indent=1); print(json.dumps(out,indent=1))
