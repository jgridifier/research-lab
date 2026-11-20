import numpy as np, pandas as pd, json, sys, warnings
warnings.filterwarnings('ignore'); sys.path.insert(0,'.')
from nca_port import ce_fdh, ceil_at, bottleneck
from scipy.stats import spearmanr, norm
import statsmodels.formula.api as smf
rng=np.random.default_rng(20261120)
d=pd.read_csv('../q3_pim_panel.csv'); d=d[d.payout_rwa.notna()].copy()
d['x_dd']=-d.drawdown; d['x_pt']=d.income_pretax_net_rate; d['x_loss']=-d.loss_total_loan_rate; d['x_cet1min']=d.cet1_min; d['x_scb']=-d.scb
C={'x_dd':'- CET1 drawdown','x_pt':'SA pre-tax income','x_loss':'- loan-loss rate','x_cet1min':'SA minimum CET1','x_scb':'- SCB'}
def perm_within(df,xc,yc,B,rng):
    obs=ce_fdh(df[xc],df[yc])['d']; y=df[yc].values.copy(); g=df.year.values; cnt=0; ds=[]
    groups=[np.where(g==u)[0] for u in np.unique(g)]
    for b in range(B):
        yy=y.copy()
        for ix in groups: yy[ix]=y[rng.permutation(ix)]
        v=ce_fdh(df[xc].values,yy)['d']; ds.append(v); cnt+= v>=obs
    return obs,(cnt+1)/(B+1),np.array(ds)
def perm_pooled(df,xc,yc,B,rng):
    obs=ce_fdh(df[xc],df[yc])['d']; y=df[yc].values; cnt=0
    for b in range(B): cnt+= ce_fdh(df[xc].values,rng.permutation(y))['d']>=obs
    return (cnt+1)/(B+1)
def spurious(df,xc,yc,B,rng):
    x=df[xc].values; y=df[yc].values; n=len(x); rs=spearmanr(x,y)[0]; r=2*np.sin(np.pi*rs/6)
    xs=np.sort(x); ys=np.sort(y); ds=[]
    for b in range(B):
        z1=rng.standard_normal(n); z2=r*z1+np.sqrt(1-r*r)*rng.standard_normal(n)
        xx=xs[np.argsort(np.argsort(z1))]; yy=ys[np.argsort(np.argsort(z2))]
        ds.append(ce_fdh(xx,yy)['d'])
    ds=np.array(ds); obs=ce_fdh(x,y)['d']
    return rs, float(np.mean(ds)), float(np.quantile(ds,0.95)), float((np.sum(ds>=obs)+1)/(B+1))
if __name__=="__main__":
    res={}
    # N1
    for yc in ['payout_rwa','payout_rwa_next','div_rwa','bb_rwa']:
        for xc in ['x_dd','x_pt','x_loss','x_cet1min']:
            df=d[[xc,yc,'year']].dropna()
            obs,pw,_=perm_within(df,xc,yc,4999 if yc=='payout_rwa' else 1999,rng)
            pp=perm_pooled(df,xc,yc,1999,rng)
            rs,sm,s95,ps=spurious(df,xc,yc,1999,rng)
            ols=smf.ols(f'{yc}~{xc}',df).fit(); q90=smf.quantreg(f'{yc}~{xc}',df).fit(q=0.90); q95=smf.quantreg(f'{yc}~{xc}',df).fit(q=0.95)
            f=ce_fdh(df[xc],df[yc]); yr=df[yc].min()+np.array([.25,.5,.75,.9])*(df[yc].max()-df[yc].min())
            bn=bottleneck(f,yr)
            res[f'{yc}|{xc}']=dict(n=len(df),d=obs,p_within=pw,p_pooled=pp,spearman=rs,spur_mean=sm,spur_95=s95,p_spur=ps,
                ols_slope=ols.params[xc],ols_p=ols.pvalues[xc],ols_r2=ols.rsquared,qr90=q90.params[xc],qr90_p=q90.pvalues[xc],qr95=q95.params[xc],qr95_p=q95.pvalues[xc],
                bottleneck_y=yr.tolist(),bottleneck_x=bn.tolist(),
                finding=bool(obs>=0.10 and pw<0.05 and obs>s95))
            print(yc,xc,{k:round(v,4) if isinstance(v,float) else v for k,v in res[f'{yc}|{xc}'].items() if k not in('bottleneck_y','bottleneck_x')},flush=True)
    json.dump(res,open('N1.json','w'),indent=1,default=float)
