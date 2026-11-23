import sys, json, itertools, time, numpy as np, pandas as pd
sys.path.insert(0,'pid')
from pidcore import copnorm_by, mmi_from_cov, idep_from_corr
import statsmodels.api as sm
rng=np.random.default_rng(1123)
D=pd.read_csv('q3_pim_panel.csv'); D=D[D.payout_rwa.notna()].copy()
out={}
def zmat(df,cols):
    g=df.year.values; return np.column_stack([copnorm_by(df[c].values,g) for c in cols])
def both(z):
    C=np.cov(z.T); m=mmi_from_cov(C,len(z)); R=np.corrcoef(z.T)
    d=idep_from_corr(R[1,2],R[0,1],R[0,2]); return m,d
def idep_boot(df,cols,NB=2000):
    df=df.dropna(subset=cols); firms=df.id_rssd.unique(); G={f:df.index[df.id_rssd==f] for f in firms}
    m,d=both(zmat(df,cols)); B=[]
    for _ in range(NB):
        idx=np.concatenate([G[f] for f in rng.choice(firms,len(firms))]); bd=df.loc[idx]
        mb,db=both(zmat(bd,cols)); B.append({**{'m_'+k:v for k,v in mb.items()},**{'d_'+k:v for k,v in db.items()}})
    B=pd.DataFrame(B); ci={k:[float(B[k].quantile(.025)),float(B[k].quantile(.975))] for k in B.columns}
    return dict(n=len(df),mmi=m,idep=d,ci=ci)
S21=D[D.year>=2021]; A=D[(D.year>=2014)&(D.year<=2019)]
specs={'P1_scb_dd':(S21,['payout_rwa','scb','drawdown']),'P1_scb_dd_div':(S21,['div_rwa','scb','drawdown']),
 'P1_scb_dd_next':(S21,['payout_rwa_next','scb','drawdown']),'P1_scb_dd_bb':(S21,['bb_rwa','scb','drawdown']),
 'P1_scb_pt':(S21,['payout_rwa','scb','income_pretax_net_rate']),
 'P2_sa_adv':(A,['payout_rwa','drawdown','dd_A']),
 'P3_e1_payout':(D[D.year<=2019],['payout_rwa','drawdown','income_pretax_net_rate']),
 'P3_e2_payout':(D[D.year>=2020],['payout_rwa','drawdown','income_pretax_net_rate']),
 'P3_e1_div':(D[D.year<=2019],['div_rwa','drawdown','income_pretax_net_rate']),
 'P3_e2_div':(D[D.year>=2020],['div_rwa','drawdown','income_pretax_net_rate']),
 'P3_all_next':(D,['payout_rwa_next','drawdown','income_pretax_net_rate'])}
for k,(df,cols) in specs.items():
    r=idep_boot(df.copy(),cols); out[k]=r
    print(k,r['n'],'IDEP',{a:round(v,4) for a,v in r['idep'].items()},'CI S',[round(x,4) for x in r['ci']['d_S']],'CI U1',[round(x,4) for x in r['ci']['d_U1']],'CI U2',[round(x,4) for x in r['ci']['d_U2']],'CI R',[round(x,4) for x in r['ci']['d_R']],flush=True)
# ---- post-hoc mechanism check (labelled post hoc): SCB minus drawdown = dividend add-on (12 CFR 225.8(f)(2)) when above the floor
S=S21.dropna(subset=['scb','drawdown','div_rwa']).copy(); S['addon']=S.scb-S.drawdown; S['floor']=S.scb<=2.5+1e-9
nf=S[~S.floor]
from scipy.stats import spearmanr
mech=dict(n=len(S),n_floor=int(S.floor.sum()),spearman_addon_div_nonfloor=float(spearmanr(nf.addon,nf.div_rwa)[0]),n_nonfloor=len(nf),
          median_addon_nonfloor=float(nf.addon.median()),median_div_rwa_nonfloor=float(nf.div_rwa.median()))
z=zmat(S,['payout_rwa','addon','drawdown']); m,d=both(z); mech['pid_addon_dd_payout']=dict(mmi=m,idep=d)
z=zmat(S,['div_rwa','addon','drawdown']); m,d=both(z); mech['pid_addon_dd_div']=dict(mmi=m,idep=d)
z=zmat(nf.assign(year=nf.year),['payout_rwa','scb','drawdown']); m,d=both(z); mech['pid_scb_dd_payout_nonfloor']=dict(n=len(nf),mmi=m,idep=d)
z=zmat(S,['bb_rwa','addon','drawdown']); m,d=both(z); mech['pid_addon_dd_bb']=dict(mmi=m,idep=d)
out['mechanism_posthoc']=mech; print('MECH',json.dumps(mech,default=float)[:1500],flush=True)
# ---- P3 era permutation, exact over all 7/6 splits of 13 test years
years=sorted(D.year.unique()); Z={}
for y in years:
    Z[y]=D[D.year==y]
def atoms_years(ys,cols):
    df=pd.concat([Z[y] for y in ys]).dropna(subset=cols); return both(zmat(df,cols))
for tg in ['payout_rwa','div_rwa']:
    cols=[tg,'drawdown','income_pretax_net_rate']
    def diff(e1):
        e2=[y for y in years if y not in e1]; m1,d1=atoms_years(e1,cols); m2,d2=atoms_years(e2,cols)
        return dict(mR=m2['R']-m1['R'],mU=m2['U2']-m1['U2'],dR=d2['R']-d1['R'],dU2=d2['U2']-d1['U2'],dU1=d2['U1']-d1['U1'])
    obs=diff([y for y in years if y<=2019]); allv=[]
    for e1 in itertools.combinations(years,7): allv.append(diff(list(e1)))
    A_=pd.DataFrame(allv)
    p={k:float((np.abs(A_[k])>=abs(obs[k])-1e-12).mean()) for k in obs}
    out[f'P3_era_{tg}']=dict(obs=obs,p_two_sided=p,n_splits=len(A_)); print('ERA',tg,obs,p,flush=True)
    # leave-one-year-out within each era
    loyo=[]
    for y in years:
        e1=[v for v in years if v<=2019 and v!=y]; e2=[v for v in years if v>=2020 and v!=y]
        m1,d1=atoms_years(e1,cols); m2,d2=atoms_years(e2,cols); loyo.append(dict(drop=int(y),mR1=m1['R'],mR2=m2['R'],mU1=m1['U2'],mU2=m2['U2']))
    out[f'P3_loyo_{tg}']=loyo
json.dump(out,open('pid/q3_pid2.json','w'),indent=1,default=float)
