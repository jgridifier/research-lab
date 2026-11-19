import pandas as pd,numpy as np,json
out={}
for f in ['Corning_mock','MorganStanley_mock']:
    d=pd.read_csv(f+'_scored.csv',keep_default_na=False,na_values=['']); d['cluster']=d.cluster.fillna('')
    flag=(d.p<0.05)&(d.lipa>0); k=int(flag.sum())
    fm=d.groupby(['function','stated_intent']).slope.transform('mean')
    top=d.index.isin(fm.sort_values(ascending=False).index[:k])
    tz=d.index.isin(d.slope.sort_values(ascending=False).index[:k])
    ta=d.index.isin((fm-d.slope.mean()).abs().sort_values(ascending=False).index[:k])
    sa=d.index.isin((d.slope-d.slope.mean()).abs().sort_values(ascending=False).index[:k])
    o={'k':k}
    for c in [c for c in d.cluster.unique() if c]:
        m=d.cluster==c
        o[c]={'n':int(m.sum()),'recall_lipa':float((flag&m).sum()/m.sum()),'recall_cell_mean':float((top&m).sum()/m.sum()),'recall_own_slope':float((tz&m).sum()/m.sum()),'recall_abs_cell_mean':float((ta&m).sum()/m.sum()),'recall_abs_own':float((sa&m).sum()/m.sum())}
    o['co_move_precision']={'lipa':float((flag&d.cluster.str.len().gt(0)).sum()/k),'cell_mean':float((top&d.cluster.str.len().gt(0)).sum()/k),'own_slope':float((tz&d.cluster.str.len().gt(0)).sum()/k),'abs_cell_mean':float((ta&d.cluster.str.len().gt(0)).sum()/k),'abs_own':float((sa&d.cluster.str.len().gt(0)).sum()/k)}
    # sarimax failure
    h=pd.read_csv(f'/workspace/q2-mock-zbb/output/{f}/history.csv')
    out[f]=o
print(json.dumps(out,indent=1)); json.dump(out,open('cluster_localisation.json','w'),indent=1)
