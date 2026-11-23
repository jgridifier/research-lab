import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'pid')
from pidcore import copnorm_by, mmi_from_cov, pid_data
import statsmodels.api as sm
rng=np.random.default_rng(20261123)
D=pd.read_csv('q3_pim_panel.csv')
D=D[D.payout_rwa.notna()].copy()
NB=2000; NP=4999

def zmat(df,t,x1,x2):
    g=df.year.values
    return np.c_[copnorm_by(df[t].values,g),copnorm_by(df[x1].values,g),copnorm_by(df[x2].values,g)]

def atoms_z(z,bias=True):
    return mmi_from_cov(np.cov(z.T), len(z) if bias else None)

def r2(y,X):
    X=sm.add_constant(X); return sm.OLS(y,X).fit().rsquared

def analyse(df,t,x1,x2,label):
    df=df.dropna(subset=[t,x1,x2]).copy(); n=len(df); g=df.year.values
    z=zmat(df,t,x1,x2)
    obs=atoms_z(z); plug=atoms_z(z,bias=False)
    strong = 1 if obs['I1']>=obs['I2'] else 2
    corr=np.corrcoef(z.T)
    # (a) joint I permutation within year
    cnt=0
    for _ in range(NP):
        zp=z.copy()
        for yv in np.unique(g):
            m=np.where(g==yv)[0]; zp[m,0]=z[rng.permutation(m),0]
        if atoms_z(zp)['I12']>=obs['I12']: cnt+=1
    p_joint=(cnt+1)/(NP+1)
    # (b) Freedman-Lane for S: residualize weak on strong, permute residual within year
    si,wi=(1,2) if strong==1 else (2,1)
    beta=np.polyfit(z[:,si],z[:,wi],1); res=z[:,wi]-np.polyval(beta,z[:,si])
    cnt=0; Snull=[]
    for _ in range(NP):
        zp=z.copy(); e=res.copy()
        for yv in np.unique(g):
            m=np.where(g==yv)[0]; e[m]=res[rng.permutation(m)]
        zp[:,wi]=np.polyval(beta,z[:,si])+e
        s=atoms_z(zp)['S']; Snull.append(s)
        if s>=obs['S']: cnt+=1
    p_S=(cnt+1)/(NP+1)
    # (c) firm-block bootstrap
    firms=df.id_rssd.unique(); B=[]
    groups={f:df.index[df.id_rssd==f] for f in firms}
    for _ in range(NB):
        pick=rng.choice(firms,len(firms),replace=True)
        idx=np.concatenate([groups[f] for f in pick]); bd=df.loc[idx]
        try:
            zb=zmat(bd,t,x1,x2); a=atoms_z(zb); a['dI']=a['I1']-a['I2']; B.append(a)
        except Exception: pass
    B=pd.DataFrame(B)
    ci={k:[float(B[k].quantile(.025)),float(B[k].quantile(.975))] for k in ['I1','I2','I12','R','U1','U2','S','dI']}
    # standard tools on raw data: OLS both, VIF, commonality; and on z
    y=df[t].values; X=df[[x1,x2]].values
    fit=sm.OLS(y,sm.add_constant(X)).fit(cov_type='cluster',cov_kwds={'groups':df.id_rssd.values})
    rb=np.corrcoef(X.T)[0,1]; vif=1/(1-rb**2)
    R1,R2_,R12=r2(y,X[:,0]),r2(y,X[:,1]),r2(y,X)
    comm=dict(R2_1=R1,R2_2=R2_,R2_12=R12,unique1=R12-R2_,unique2=R12-R1,common=R1+R2_-R12)
    R1z,R2z,R12z=r2(z[:,0],z[:,1]),r2(z[:,0],z[:,2]),r2(z[:,0],z[:,1:])
    commz=dict(R2_1=R1z,R2_2=R2z,R2_12=R12z,unique1=R12z-R2z,unique2=R12z-R1z,common=R1z+R2z-R12z)
    # Fit with year FE on z? z already within-year. OLS both on z:
    fz=sm.OLS(z[:,0],sm.add_constant(z[:,1:])).fit(cov_type='cluster',cov_kwds={'groups':df.id_rssd.values})
    out=dict(label=label,t=t,x1=x1,x2=x2,n=n,firms=int(len(firms)),corr_z=corr.tolist(),obs=obs,plugin=plug,strong=f'x{strong}',
             p_joint=p_joint,p_S_freedman_lane=p_S,S_null_95=float(np.quantile(Snull,.95)),boot_ci=ci,
             ols_raw=dict(coef=fit.params.tolist(),t=fit.tvalues.tolist(),p=fit.pvalues.tolist(),r_sources=rb,vif=vif),
             commonality_raw=comm,commonality_z=commz,
             ols_z=dict(coef=fz.params.tolist(),t=fz.tvalues.tolist(),p=fz.pvalues.tolist()))
    print(label,n,{k:round(v,4) for k,v in obs.items()},'pj',p_joint,'pS',p_S,'CI S',[round(c,4) for c in ci['S']],'CI dI',[round(c,4) for c in ci['dI']])
    print('   OLS raw t',[round(v,2) for v in fit.tvalues],'vif',round(vif,2),'comm',{k:round(v,3) for k,v in comm.items()})
    return out

R={}
S21=D[D.year>=2021]
R['P1_scb_dd']=analyse(S21,'payout_rwa','scb','drawdown','P1 SCB vs drawdown 2021-25')
R['P1_scb_pt']=analyse(S21,'payout_rwa','scb','income_pretax_net_rate','P1 SCB vs pretax 2021-25')
R['P1_scb_dd_next']=analyse(S21,'payout_rwa_next','scb','drawdown','P1 SCB vs drawdown next-year 2021-24')
R['P1_scb_dd_div']=analyse(S21,'div_rwa','scb','drawdown','P1 SCB vs dd, dividends')
R['P1_scb_dd_bb']=analyse(S21,'bb_rwa','scb','drawdown','P1 SCB vs dd, net buybacks')
A=D[(D.year>=2014)&(D.year<=2019)]
R['P2_sa_adv']=analyse(A,'payout_rwa','drawdown','dd_A','P2 SA vs Adverse drawdown 2014-19')
R['P2_sa_adv_next']=analyse(A,'payout_rwa_next','drawdown','dd_A','P2 next-year')
for era,(lo,hi) in {'e1':(2013,2019),'e2':(2020,2025)}.items():
    E=D[(D.year>=lo)&(D.year<=hi)]
    for tg in ['payout_rwa','div_rwa','bb_rwa']:
        R[f'P3_{era}_{tg}']=analyse(E,tg,'drawdown','income_pretax_net_rate',f'P3 {era} {tg} dd vs pretax')
R['P3_all_payout']=analyse(D,'payout_rwa','drawdown','income_pretax_net_rate','P3 all years dd vs pretax')
json.dump(R,open('pid/q3_pid.json','w'),indent=1,default=float)
