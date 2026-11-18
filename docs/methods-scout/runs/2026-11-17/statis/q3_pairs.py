import pandas as pd, numpy as np, json, itertools
P=pd.read_csv('q3_pim_panel.csv')
V=['drawdown','income_pretax_net_rate','loss_total_loan_rate','cet1_start','payout_rwa','div_rwa','bb_rwa']
LAB=['CET1 drawdown','SA pre-tax income','SA loan losses','Start CET1','Payout/RWA','Dividends/RWA','Net buybacks/RWA']
years=sorted(P.year.unique()); K=len(years)
M=np.stack([P[P.year==y][V].dropna().rank().corr().values for y in years])
iu=np.triu_indices(7,1); X=M[:,iu[0],iu[1]]  # K x 21
def delta(post): post=np.array(post); pre=np.setdiff1d(np.arange(K),post); return X[post].mean(0)-X[pre].mean(0)
obs_post=[k for k,y in enumerate(years) if y>=2020]
d_obs=delta(obs_post); allc=list(itertools.combinations(range(K),len(obs_post)))
D=np.array([delta(c) for c in allc])
p_each=[(np.sum(np.abs(D[:,j])>=abs(d_obs[j])-1e-12))/len(allc) for j in range(21)]
mx=np.abs(D).max(1); p_maxT=[(np.sum(mx>=abs(d_obs[j])-1e-12))/len(allc) for j in range(21)]
rows=[dict(pair=f'{LAB[i]} ~ {LAB[j]}',pre=X[[k for k in range(K) if k not in obs_post],n].mean(),post=X[obs_post,n].mean(),delta=d_obs[n],p_exact=p_each[n],p_maxT=p_maxT[n]) for n,(i,j) in enumerate(zip(*iu))]
R=pd.DataFrame(rows).sort_values('p_exact'); print(R.round(3).to_string()); R.to_csv('pair_changes.csv',index=False)
# year-to-year: which consecutive transitions have lowest RV (from statis json)
o=json.load(open('q3_statis.json')); C=np.array(o['C'])
cons=[(int(years[k]),int(years[k+1]),float(C[k,k+1])) for k in range(K-1)]; print('consecutive RV',[(a,b,round(c,3)) for a,b,c in cons])
json.dump(dict(pairs=R.to_dict('records'),consecutive_rv=cons),open('q3_pairs.json','w'),indent=1,default=float)
