import pandas as pd, numpy as np, json
from eca import circ_null, binarize
M=pd.read_csv('/workspace/ms-1114/q1/monthly.csv'); M['period']=pd.PeriodIndex(M.period,freq='M'); M=M.set_index('period')
X=pd.DataFrame(index=M.index)
X['g_pb']=np.log(M['Secured_Prime Broker']).diff(); X['g_tot']=np.log(M['Total_Total']).diff(); X['dl_fails']=np.log(M.fails_fin_ust).diff()
X=X.dropna(); print(len(X),X.index.min(),X.index.max())
E=pd.DataFrame({'fails':binarize(X.dl_fails,0.8),'pb':binarize(X.g_pb,0.8),'tot':binarize(X.g_tot,0.8)},index=X.index)
rows=[]
for b in ['pb','tot']:
    for tau in [0,3,6]:
        o=circ_null(E.fails.values,E[b].values,2,tau,4999,minshift=6,seed=tau)
        rows.append(dict(A='fails',B=b,tau=tau,kind='precursor',rate=o['rp'],null95=o['null_rp_95'],p=o['p_prec_circ']))
        rows.append(dict(A='fails',B=b,tau=tau,kind='trigger',rate=o['rt'],null95=o['null_rt_95'],p=o['p_trig_circ']))
# reverse at tau 0: PF spike preceded by fails spike
for b in ['pb','tot']:
    o=circ_null(E[b].values,E.fails.values,2,0,4999,minshift=6,seed=99)
    rows.append(dict(A=b,B='fails',tau=0,kind='precursor',rate=o['rp'],null95=o['null_rp_95'],p=o['p_prec_circ']))
    rows.append(dict(A=b,B='fails',tau=0,kind='trigger',rate=o['rt'],null95=o['null_rt_95'],p=o['p_trig_circ']))
R=pd.DataFrame(rows); m=len(R); o=np.argsort(R.p.values); adj=np.empty(m); run=0
for k,i in enumerate(o): run=max(run,(m-k)*R.p.values[i]); adj[i]=min(1,run)
R['p_holm']=adj; print(R.round(4).to_string()); R.to_csv('F2_results.csv',index=False)
json.dump(dict(n=len(X),start=str(X.index.min()),end=str(X.index.max()),NA=int(E.fails.sum()),NB_pb=int(E.pb.sum()),NB_tot=int(E.tot.sum())),open('F2_meta.json','w'))
