import pandas as pd, numpy as np
P=pd.read_csv('../q3_pim_panel.csv')
P['neg_pti']=-P.income_pretax_net_rate
S=['drawdown','neg_pti','loss_total_loan_rate']
def dom(X):
    n=len(X); M=np.zeros((n,n),int)
    for i in range(n):
        for j in range(n):
            if i!=j and np.all(X[i]<=X[j]) and np.any(X[i]<X[j]): M[i,j]=1   # i less stressed than j
    return M
rows=[]
for y,g in P.groupby('year'):
    X=g[S].values; M=dom(X); n=len(g)
    eq=sum(1 for i in range(n) for j in range(i+1,n) if np.all(X[i]==X[j]))
    comp=(M+M.T).sum()/2
    rows.append((y,n,int(comp),n*(n-1)//2,round(comp/(n*(n-1)/2),3),eq))
print(pd.DataFrame(rows,columns=['year','n','comparable','pairs','frac','ties']))
