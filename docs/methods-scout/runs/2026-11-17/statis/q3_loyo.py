import pandas as pd,numpy as np,itertools,json
from statis_np import statis
P=pd.read_csv('q3_pim_panel.csv'); V=['drawdown','income_pretax_net_rate','loss_total_loan_rate','cet1_start','payout_rwa','div_rwa','bb_rwa']
years=sorted(P.year.unique()); mats={y:P[P.year==y][V].dropna().rank().corr().values for y in years}; out=[]
for drop in years:
    ys=[y for y in years if y!=drop]; C=statis([mats[y] for y in ys])['C']; K=len(ys)
    def D(post):
        pre=[i for i in range(K) if i not in post]; w=[C[a,b] for g in (pre,list(post)) for a,b in itertools.combinations(g,2)]; return np.mean(w)-np.mean([C[a,b] for a in pre for b in post])
    post=[i for i,y in enumerate(ys) if y>=2020]; d=D(post); allD=np.array([D(c) for c in itertools.combinations(range(K),len(post))])
    out.append(dict(drop=int(drop),D=float(d),p=float(np.mean(allD>=d-1e-12))))
print(pd.DataFrame(out).round(4).to_string()); json.dump(out,open('q3_loyo.json','w'),indent=1)
