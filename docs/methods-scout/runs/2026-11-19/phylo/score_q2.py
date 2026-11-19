import pandas as pd, numpy as np, json, sys, warnings
from sklearn.metrics import roc_auc_score
import statsmodels.api as sm, statsmodels.formula.api as smf
from statsmodels.tsa.statespace.sarimax import SARIMAX
warnings.filterwarnings('ignore')
out={}
FS=sys.argv[1:] or ['Corning_mock','MorganStanley_mock']
for f in FS:
    d=pd.read_csv(f+'_q2.csv',keep_default_na=False,na_values=['']); L=pd.read_csv(f+'_lipa.csv'); d=d.merge(L,on='tip')
    for c in ['mismatch','drift','cluster']: d[c]=d[c].fillna('').astype(str)
    sig=json.load(open(f+'_signal.json')); o={}
    # standard tool for P1: ANOVA R^2 of slope on categories
    for y in ['slope','slope_true']:
        o['anova_r2_function_'+y]=smf.ols(f'{y}~C(function)',d).fit().rsquared
        o['anova_r2_seg_fun_intent_'+y]=smf.ols(f'{y}~C(segment)+C(function)+C(stated_intent)',d).fit().rsquared
        o['anova_r2_fun_x_intent_'+y]=smf.ols(f'{y}~C(function):C(stated_intent)',d).fit().rsquared
    o['signal']={tn:{'stat':sig[tn]['stat'],'p':sig[tn]['pvalue']} for tn in ['label','text']}
    # peer z within function x stated_intent (standard peer comparison)
    grp=d.groupby(['function','stated_intent']).slope
    d['peer_z']=(d.slope-grp.transform('mean'))/grp.transform('std').replace(0,np.nan)
    d['peer_z']=d.peer_z.fillna(0)
    d['nb_gap']=d.slope-d.nb_slope    # program minus patristic-weighted relatives
    # P2 mismatch scoring
    P2={}
    for mt,sign in [('stated_growth_actually_declining',-1),('stated_run_actually_transform',+1),('stated_transform_actually_run',-1),('stated_mandatory_actually_discretionary',0),('stated_people_actually_vendor',0)]:
        yv=(d.mismatch==mt).astype(int)
        if yv.sum()==0: continue
        r={'n':int(yv.sum())}
        # LIPA-based: negative LIPA = unlike relatives; signed: direction relative to relatives
        r['auc_neg_lipa']=roc_auc_score(yv,-d.lipa)
        if sign!=0:
            r['auc_signed_lipa']=roc_auc_score(yv,-d.lipa*np.sign(sign*(d.slope-d.slope.mean()))) # unlike relatives AND moving in mismatch direction
            r['auc_nb_gap']=roc_auc_score(yv,sign*d.nb_gap); r['auc_peer_z']=roc_auc_score(yv,sign*d.peer_z); r['auc_ols_slope']=roc_auc_score(yv,sign*d.slope)
        else:
            r['auc_abs_nb_gap']=roc_auc_score(yv,np.abs(d.nb_gap)); r['auc_abs_peer_z']=roc_auc_score(yv,np.abs(d.peer_z))
        P2[mt]=r
    o['P2']=P2
    # P3 drift: LIPA early minus late; comparator |delta peer z|
    for w in ['early','late']:
        g=d.groupby(['function','stated_intent'])['slope_'+w]; d['pz_'+w]=((d['slope_'+w]-g.transform('mean'))/g.transform('std').replace(0,np.nan)).fillna(0)
    d['drift_lipa']=d.lipa_early-d.lipa_late; d['drift_pz']=np.abs(d.pz_late-d.pz_early)
    d['drift_nb']=np.abs((d.slope_late-d.nb_late)-(d.slope_early-d.nb_early))
    P3={}
    for lab,mask in [('any',d.drift!=''),('intent',d.drift.str.contains('intent')),('discretionary',d.drift.str.contains('discretionary')),('cost_type',d.drift.str.contains('cost_type'))]:
        yv=mask.astype(int)
        if yv.sum()<3: continue
        P3[lab]={'n':int(yv.sum()),'auc_drift_lipa':roc_auc_score(yv,d.drift_lipa),'auc_abs_drift_lipa':roc_auc_score(yv,np.abs(d.drift_lipa)),'auc_abs_dpeer_z':roc_auc_score(yv,d.drift_pz),'auc_abs_dnb_gap':roc_auc_score(yv,d.drift_nb)}
    o['P3']=P3
    # P4 walk-forward one step: predict last-year growth g_last using data to previous year
    ytrue=d.g_last.values
    preds={'ols_trend':d.slope_tr.values,'phylo_nb':d.nb_gprev.values,'blend':0.5*d.slope_tr.values+0.5*d.nb_gprev.values}
    # pooled ARDL(1): g_t = a + b g_{t-1}, fit on previous transition
    m=sm.OLS(d.g_prev,sm.add_constant(d.g_prev2)).fit(); preds['ardl1']=m.params.iloc[0]+m.params.iloc[1]*d.g_prev.values
    # SARIMAX(1,0,0) per program on log actual levels up to previous year -> forecast growth
    h=pd.read_csv(f'/workspace/q2-mock-zbb/output/{f}/history.csv'); A=h.pivot(index='program_id',columns='fiscal_year',values='actual_usd')
    ids=d.program_id.values; LA=np.log(A.loc[ids].values); sp=[]
    for row in LA:
        s=row[:-1]
        try:
            r=SARIMAX(s,order=(1,0,0),trend='ct').fit(disp=False); sp.append(float(r.forecast(1)[0])-s[-1])
        except Exception: sp.append(s[-1]-s[-2])
    preds['sarimax100']=np.array(sp)
    preds['zero']=np.zeros(len(d))
    rm={k:float(np.sqrt(np.nanmean((v-ytrue)**2))) for k,v in preds.items()}
    rmt={k:float(np.sqrt(np.nanmean((v-d.g_last_true.values)**2))) for k,v in preds.items()}
    o['P4_rmse_vs_observed']=rm; o['P4_rmse_vs_true']=rmt
    o['P4_blend_vs_ols_pct']=100*(rm['blend']/rm['ols_trend']-1); o['P4_nb_vs_ols_pct']=100*(rm['phylo_nb']/rm['ols_trend']-1)
    # LIPA significance counts
    o['lipa_sig_p05']=int((d.p<0.05).sum()); o['lipa_sig_neg_p05']=int(((d.p<0.05)&(d.lipa<0)).sum()); o['lipa_sig_pos_p05']=int(((d.p<0.05)&(d.lipa>0)).sum())
    # planted clusters: share of members with significant positive LIPA vs non-members
    o['cluster_pos_lipa_share']={c:float(((d.cluster==c)&(d.p<0.05)&(d.lipa>0)).sum()/max((d.cluster==c).sum(),1)) for c in d.cluster.unique() if c}
    o['noncluster_pos_lipa_share']=float(((d.cluster=='')&(d.p<0.05)&(d.lipa>0)).sum()/(d.cluster=='').sum())
    d.to_csv(f+'_scored.csv',index=False)
    out[f]=o
json.dump(out,open('q2_scores_'+'_'.join(FS)+'.json','w'),indent=1,default=float)
print(json.dumps(out,indent=1,default=float))
