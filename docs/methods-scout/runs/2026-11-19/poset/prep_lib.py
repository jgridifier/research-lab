import pandas as pd, numpy as np
S=['drawdown','neg_pti','loss_total_loan_rate']
def load():
    P=pd.read_csv('/workspace/methods-scout/2026-11-19/q3_pim_panel.csv')
    P['neg_pti']=-P.income_pretax_net_rate
    return P
def dom(X):
    X=np.asarray(X,float); le=(X[:,None,:]<=X[None,:,:]).all(2); lt=(X[:,None,:]<X[None,:,:]).any(2)
    M=(le&lt).astype(int); np.fill_diagonal(M,0); return M
