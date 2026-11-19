import json, pickle, numpy as np, pandas as pd, warnings
from scipy.stats import spearmanr, kendalltau
from prep_lib import load, dom, S
warnings.filterwarnings('ignore'); rng=np.random.default_rng(201911)
Y=pickle.load(open('Y.pkl','rb')); out={}
# ---- A1b: incomparable pairs. Agreement of EW composite & per-indicator, with within-year permutation null
def inc_stats(perm=False):
    agg={'ew':[0,0],'ols':[0,0],'drawdown':[0,0],'neg_pti':[0,0],'loss_total_loan_rate':[0,0]}
    for y,d in Y.items():
        pay=np.array(d['pay']); pay=rng.permutation(pay) if perm else pay
        X=np.array(d['X']); n=len(pay); M=d['M']
        iu,ju=np.triu_indices(n,1); inc=~(M[iu,ju].astype(bool)|M[ju,iu].astype(bool)); i=iu[inc]; j=ju[inc]
        for k in agg:
            s=d[k] if k in ('ew','ols') else X[:,S.index(k)]
            hi=np.where(s[i]>s[j],i,j); lo=np.where(s[i]>s[j],j,i); tie=s[i]==s[j]
            a=(pay[hi]<pay[lo])+0.5*(pay[hi]==pay[lo]); a=np.where(tie,0.5,a)
            agg[k][0]+=a.sum(); agg[k][1]+=len(a)
    return {k:v[0]/v[1] for k,v in agg.items()}, agg['ew'][1]
obs,ninc=inc_stats(); nul=[inc_stats(True)[0] for _ in range(1999)]
out['A1b_incomparable']={'n_pairs':int(ninc),'obs':obs,'null_q95':{k:float(np.quantile([z[k] for z in nul],.95)) for k in obs},
   'p':{k:float((1+sum(z[k]>=obs[k] for z in nul))/2000) for k in obs}}
# ---- A2 walk-forward: predict year y cross-section of payout_rwa using info up to y (stress of year y known at results; payouts realized in calendar y)
P=load(); P=P[P.payout_rwa.notna()].copy().sort_values(['id_rssd','year'])
P['lag_pay']=P.groupby('id_rssd').payout_rwa.shift(1); P['lag_year']=P.groupby('id_rssd').year.shift(1)
yrs=sorted(Y); res=[]
import statsmodels.api as sm
from statsmodels.tsa.statespace.sarimax import SARIMAX
for y in yrs:
    if y<2015: continue
    tr=P[P.year<y]; te=P[P.year==y].copy()
    d=Y[y]; e=pd.Series(-np.array(d['e']),index=d['ids'])   # expected stress rank; higher stress -> lower payout => use negative
    te['pred_poset']=te.id_rssd.map(e)
    Xtr=sm.add_constant(tr[S]); ols=sm.OLS(tr.payout_rwa,Xtr).fit(); te['pred_ols']=ols.predict(sm.add_constant(te[S],has_constant='add'))
    trA=tr.dropna(subset=['lag_pay']); ardl=sm.OLS(trA.payout_rwa,sm.add_constant(trA[['lag_pay']+S])).fit()
    teA=te.copy(); teA['lag_pay']=teA.lag_pay.fillna(tr.payout_rwa.median())
    te['pred_ardl']=ardl.predict(sm.add_constant(teA[['lag_pay']+S],has_constant='add'))
    ps=[]
    for _,r in te.iterrows():
        h=P[(P.id_rssd==r.id_rssd)&(P.year<y)]
        if len(h)>=8:
            try:
                m=SARIMAX(h.payout_rwa.values,exog=h[S].values,order=(1,0,0),trend='c').fit(disp=False)
                ps.append(float(m.forecast(1,exog=r[S].values.reshape(1,-1).astype(float))[0]))
            except Exception: ps.append(h.payout_rwa.values[-1])
        elif len(h)>0: ps.append(h.payout_rwa.values[-1])
        else: ps.append(tr.payout_rwa.median())
    te['pred_sarimax']=ps
    row={'year':y,'n':len(te)}
    for k in ['poset','ols','ardl','sarimax']: row[k]=spearmanr(te['pred_'+k],te.payout_rwa).correlation
    row['n_sarimax_fit']=int(sum(len(P[(P.id_rssd==i)&(P.year<y)])>=8 for i in te.id_rssd))
    res.append(row)
W=pd.DataFrame(res); W.to_csv('A2_walkforward.csv',index=False)
out['A2_walkforward_mean_spearman']={k:float(W[k].mean()) for k in ['poset','ols','ardl','sarimax']}
out['A2_years']=[int(v) for v in W.year]
# ---- A3 SCB vs path, 2021-2025
A3={'disagree_pairs':0,'path_wins':0.0,'scb_pairs':0,'scb_conc':0.0,'path_pairs':0,'path_conc':0.0,'floor_tied_path_pairs':0}
def a3(perm=False):
    dp=0;pw=0.;sp=0;sc=0.;pp=0;pc=0.;ft=0
    for y in [2021,2022,2023,2024,2025]:
        d=Y[y]; pay=np.array(d['pay']); scb=np.array(d['scb'],float); ok=~np.isnan(scb)
        if perm: pay=rng.permutation(pay)
        M=d['M']; n=len(pay)
        for i in range(n):
            for j in range(n):
                if not(ok[i] and ok[j]) or i==j: continue
                if M[i,j]:   # j more stressed on path
                    pp+=1; pc+=(pay[j]<pay[i])+0.5*(pay[j]==pay[i])
                    if scb[j]<=scb[i]:
                        dp+=1; pw+=(pay[j]<pay[i])+0.5*(pay[j]==pay[i]); ft+=(scb[j]==scb[i]==2.5)
                if scb[j]>scb[i] and i<j or (scb[i]>scb[j] and i<j):
                    hi,lo=(j,i) if scb[j]>scb[i] else (i,j); sp+=1; sc+=(pay[hi]<pay[lo])+0.5*(pay[hi]==pay[lo])
    return dict(disagree_pairs=dp,path_conc_in_disagree=pw/max(dp,1),floor_tied=ft,scb_pairs=sp,scb_conc=sc/sp,path_pairs=pp,path_conc=pc/pp)
o=a3(); nul=[a3(True) for _ in range(999)]
o['p_path_in_disagree']=float((1+sum(z['path_conc_in_disagree']>=o['path_conc_in_disagree'] for z in nul))/1000)
o['p_scb']=float((1+sum(z['scb_conc']>=o['scb_conc'] for z in nul))/1000)
o['p_path']=float((1+sum(z['path_conc']>=o['path_conc'] for z in nul))/1000)
out['A3_scb_vs_path_2021_2025']=o
# ---- A4 year-to-year stability of dominance relations
rows=[]
for a,b in zip(yrs[:-1],yrs[1:]):
    da,db=Y[a],Y[b]; common=[i for i in da['ids'] if i in db['ids']]
    ia=[da['ids'].index(i) for i in common]; ib=[db['ids'].index(i) for i in common]
    Ma=da['M'][np.ix_(ia,ia)]; Mb=db['M'][np.ix_(ib,ib)]; m=len(common)
    keep=flip=lost=gained=0
    for i in range(m):
        for j in range(m):
            if Ma[i,j]:
                if Mb[i,j]: keep+=1
                elif Mb[j,i]: flip+=1
                else: lost+=1
            elif not Ma[j,i] and Mb[i,j]: gained+=1
    ea=np.array(da['ew'])[ia]; eb=np.array(db['ew'])[ib]
    pa=np.array(da['pay'])[ia]; pb=np.array(db['pay'])[ib]
    rows.append(dict(pair=f'{a}-{b}',m=m,dom_a=int(Ma.sum()),kept=keep,flipped=flip,lost=lost,gained=gained,keep_share=keep/max(Ma.sum(),1),
                     tau_ew=kendalltau(ea,eb).correlation,tau_payout=kendalltau(pa,pb).correlation,
                     tau_exprank=kendalltau(np.array(da['e'])[ia],np.array(db['e'])[ib]).correlation))
T4=pd.DataFrame(rows); T4.to_csv('A4_stability.csv',index=False)
out['A4_mean']={k:float(T4[k].mean()) for k in ['keep_share','tau_ew','tau_payout','tau_exprank']}
out['A4_flipped_total']=int(T4.flipped.sum()); out['A4_dom_total']=int(T4.dom_a.sum()); out['A4_kept_total']=int(T4.kept.sum()); out['A4_lost_total']=int(T4.lost.sum())
json.dump(out,open('q3_poset_A1b_A4.json','w'),indent=1,default=float)
print(json.dumps(out,indent=1,default=float)); print(W.round(3).to_string()); print(T4.round(3).to_string())
