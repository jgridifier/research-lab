# Post-registration addition (14:42 ET), labelled: measure-free bounds from Van Santen, Rosseel & Marinazzo (arXiv:2611.08131):
# any nonnegative 2-source PID has R in [max(0,coI), min(I1,I2)], so S >= max(0,-coI) (Hi-Fi end); MMI is the other end.
import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'pid'); from pidcore import copnorm_by, mmi_from_cov
rng=np.random.default_rng(5)
D=pd.read_csv('q3_pim_panel.csv'); D=D[D.payout_rwa.notna()]
def zmat(df,cols): g=df.year.values; return np.column_stack([copnorm_by(df[c].values,g) for c in cols])
def seg(z):
    m=mmi_from_cov(np.cov(z.T),len(z)); coI=m['I1']+m['I2']-m['I12']
    return dict(coI=coI,S_lo=max(0,-coI),S_hi=m['S'],R_lo=max(0,coI),R_hi=m['R'],U1_hi=m['I1']-max(0,coI),U2_hi=m['I2']-max(0,coI))
out={}
S21=D[D.year>=2021]
for k,(df,cols) in {'P1_payout':(S21,['payout_rwa','scb','drawdown']),'P1_div':(S21,['div_rwa','scb','drawdown']),'P1_next':(S21,['payout_rwa_next','scb','drawdown']),
                    'P2_sa_adv':(D[(D.year>=2014)&(D.year<=2019)],['payout_rwa','drawdown','dd_A']),'P3_all':(D,['payout_rwa','drawdown','income_pretax_net_rate'])}.items():
    df=df.dropna(subset=cols); o=seg(zmat(df,cols)); firms=df.id_rssd.unique(); G={f:df.index[df.id_rssd==f] for f in firms}; B=[]
    for _ in range(2000):
        bd=df.loc[np.concatenate([G[f] for f in rng.choice(firms,len(firms))])]; B.append(seg(zmat(bd,cols)))
    B=pd.DataFrame(B); o['ci']={c:[float(B[c].quantile(.025)),float(B[c].quantile(.975))] for c in B}; out[k]=o
    print(k,{a:round(v,4) for a,v in o.items() if a!='ci'},'S_lo CI',[round(x,4) for x in o['ci']['S_lo']],'negcoI CI',[round(-x,4) for x in o['ci']['coI'][::-1]])
json.dump(out,open('pid/bounds.json','w'),indent=1,default=float)
