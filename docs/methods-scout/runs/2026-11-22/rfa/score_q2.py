import pandas as pd, numpy as np, json
from scipy import stats
from sklearn.metrics import roc_auc_score
Z90=stats.norm.ppf(0.9); out={}
def eb_logsd(ls,n,grp):
    # normal-theory EB: log s_i ~ N(theta_i, v_i), v_i ~ 1/(2(n_i-1)); shrink to group mean, tau^2 by moments
    res=pd.Series(index=ls.index,dtype=float)
    for g,idx in ls.groupby(grp).groups.items():
        y=ls[idx]; v=1/(2*(n[idx]-1)); mu=np.average(y,weights=1/v); tau2=max(np.var(y,ddof=1)-v.mean(),1e-6)
        res[idx]=mu+tau2/(tau2+v)*(y-mu)
    return res
for f in ['Corning_mock','MorganStanley_mock']:
    X=pd.read_csv(f'{f}_x.csv'); X['lx']=np.log(X.x); P=pd.read_csv(f'{f}_programs_regions.csv',index_col=0); T=pd.read_csv(f'{f}_truth.csv',index_col=0)
    S=pd.read_csv(f'{f}_site.csv').set_index('program_id'); R=pd.read_csv(f'{f}_regions.csv')
    g=X.groupby('program_id').lx; m=g.mean(); s=g.std(ddof=1); n=g.size()
    est=pd.DataFrame(index=P.index)
    est['at-site empirical']=np.log(X.groupby('program_id').x.quantile(0.9))
    est['at-site lognormal']=m+Z90*s
    for sch,lab in [('reg_B','RFA regions B (disc x size)'),('reg_A','RFA regions A (function)'),('reg_C','RFA regions C (text)'),('reg_D','RFA random regions'),('reg_O','RFA oracle regions (answer key)')]:
        est[lab]=np.log(S.loc[P.index,'q90_'+sch])
    # pooled SD by stated function (standard category pooling)
    dev=X.lx-X.program_id.map(m); X['A']=X.program_id.map(P.reg_A)
    sp=np.sqrt((dev**2).groupby(X.A).sum()/(X.groupby('A').size()-X.groupby('A').program_id.nunique()))
    est['category-pooled lognormal (function)']=m+Z90*P.reg_A.map(sp)
    ls=np.log(s); est['EB-shrunk sd (to region B)']=m+Z90*np.exp(eb_logsd(ls,n,P.reg_B)+0.0)
    est['EB-shrunk sd (to function)']=m+Z90*np.exp(eb_logsd(ls,n,P.reg_A))
    truth=T.loc[P.index,'logq90_true']
    rmse=((est.sub(truth,axis=0))**2).mean()**0.5
    # bootstrap CI for the key ratio
    rng=np.random.default_rng(1); ids=np.arange(len(P)); E=est.sub(truth,axis=0).values**2; cols=list(est.columns)
    def ratio(a,b,i): return np.sqrt(E[i,cols.index(a)].mean()/E[i,cols.index(b)].mean())
    bs={}
    for a in ['RFA regions B (disc x size)','RFA regions A (function)','category-pooled lognormal (function)']:
        r=[ratio(a,'at-site lognormal',rng.choice(ids,len(ids))) for _ in range(2000)]; bs[a+' / at-site lognormal']=[round(ratio(a,'at-site lognormal',ids),4),round(np.percentile(r,2.5),4),round(np.percentile(r,97.5),4)]
    # sd RMSE
    sd_true=T.loc[P.index,'sd_true']
    # Q1 homogeneity: Levene per region vs H1
    lev={}
    for sch in ['reg_A','reg_B','reg_C','reg_D','reg_O']:
        lab=P[sch] if sch!='reg_O' else T.loc[P.index,'reg_O']; ps=[]
        for gname,idx in lab.groupby(lab).groups.items():
            if len(idx)<2: continue
            grp=[X.lx[X.program_id==i].values for i in idx]
            ps.append(stats.levene(*grp,center='median').pvalue)
        Rs=R[R.scheme==sch]; Rs=Rs[Rs.N>=2]
        lev[sch]=dict(n_regions=len(ps),share_levene_p05=round(float(np.mean(np.array(ps)<0.05)),3),share_H1ge2=round(float((Rs.H1>=2).mean()),3),share_H1ge1=round(float((Rs.H1>=1).mean()),3),median_H1=round(float(Rs.H1.median()),2),
                      siteweighted_H1ge2=round(float((Rs.N*(Rs.H1>=2)).sum()/Rs.N.sum()),3))
    # Q3 discordancy vs planted mandatory->discretionary
    man=P.stated_discretionary=='mandatory'; y=(T.loc[P.index,'mismatch']=='stated_mandatory_actually_discretionary')[man].astype(int)
    Pm=P[man]
    zsd=(ls-ls.groupby(P.reg_B).transform('mean'))/ls.groupby(P.reg_B).transform('std')
    St=S.loc[P.index]; zt=(St.t-St.t.groupby(P.reg_B).transform('mean'))/St.t.groupby(P.reg_B).transform('std')
    # chi-square variance ratio vs region pooled variance
    spB=((dev**2).groupby(X.program_id.map(P.reg_B)).sum()/(X.groupby(X.program_id.map(P.reg_B)).size()-X.groupby(X.program_id.map(P.reg_B)).program_id.nunique()))
    chi=(n-1)*s**2/P.reg_B.map(spB); chip=-np.log(stats.chi2.sf(chi,n-1))
    auc={k:round(roc_auc_score(y,v[man]),3) for k,v in [('D_i (region B)',St.D_reg_B),('D_i (function)',St.D_reg_A),('L-CV z within region B',zt),('z of at-site log sd within region B',zsd),('chi-square variance ratio vs region B',chip)]}
    flags=St.D_reg_B[man]>=3; prec=float(y[flags].mean()) if flags.sum() else None
    # power check of D_i: planted count & ranks
    out[f]=dict(rmse_logq90={k:round(v,4) for k,v in rmse.items()}, ratio_ci=bs, rmse_sd_at_site=round(float(((s-sd_true)**2).mean()**0.5),4),
                rmse_sd_rfa_A=None, homogeneity=lev, q3=dict(n_mandatory=int(man.sum()),n_planted=int(y.sum()),auc=auc,n_flag_D3=int(flags.sum()),precision_D3=prec,recall_D3=round(float(y[flags].sum()/y.sum()),3)))
    est.join(truth).to_csv(f'{f}_q90_estimates.csv')
json.dump(out,open('q2_scores.json','w'),indent=1); print(json.dumps(out,indent=1))
