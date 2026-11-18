import numpy as np, pandas as pd, json, sys
from hyst import hi_storm
rng=np.random.default_rng(20261118)
D='/workspace/research/drive_inv/data/'
W=pd.read_csv('/workspace/ms-1114/q1/weekly.csv',parse_dates=['date']).set_index('date').asfreq('W-WED')
# leveraged-fund net short UST 2Y+5Y+10Y (k contracts), same build as the 11-17 ECA run
t=pd.read_csv(D+'tff_panel_harmonized.csv.gz',usecols=['contract_harmonized','FutOnly_or_Combined','report_date','Lev_Money_Positions_Long_All','Lev_Money_Positions_Short_All'])
t=t[t.FutOnly_or_Combined=='FutOnly']
core=['UST 2Y NOTE - CHICAGO BOARD OF TRADE','UST 5Y NOTE - CHICAGO BOARD OF TRADE','UST 10Y NOTE - CHICAGO BOARD OF TRADE']
t=t[t.contract_harmonized.isin(core)].copy(); t['ns']=t.Lev_Money_Positions_Short_All-t.Lev_Money_Positions_Long_All
p=t.pivot_table(index='report_date',columns='contract_harmonized',values='ns',aggfunc='sum')
lev=p.sum(axis=1,min_count=3)/1e3; lev.index=pd.to_datetime(lev.index)+pd.offsets.Week(weekday=2); lev=lev.groupby(level=0).last(); lev=lev[lev.index<='2025-12-31']
W=W.join(lev.rename('lev'),how='left')
for c in ['fails_fin_ust','dvp_out','spread_bp','lev']: W[c]=W[c].interpolate(limit=1,limit_area='inside')
W=W[W.index>='2018-05-09']
Q=W.fails_fin_ust
# ---- storms (pre-registered rule)
ratio=Q/Q.shift(1).rolling(26,min_periods=20).median()
thr=ratio.quantile(0.90)
peaks=[]
for i in range(len(Q)):
    lo,hi=max(0,i-4),min(len(Q),i+5)
    if Q.iloc[i]==Q.iloc[lo:hi].max() and ratio.iloc[i]>=max(1.5,thr): peaks.append(i)
storms=[]
for i in peaks:
    s=max(0,i-8)+int(np.argmin(Q.iloc[max(0,i-8):i+1].values)); e=i+int(np.argmin(Q.iloc[i:min(len(Q),i+9)].values))
    if i-s>=2 and e-i>=2: storms.append([s,i,e])
merged=[]
for st in sorted(storms):
    if merged and st[0]<=merged[-1][2]:
        if Q.iloc[st[1]]>Q.iloc[merged[-1][1]]: merged[-1]=[min(st[0],merged[-1][0]),st[1],max(st[2],merged[-1][2])]
        else: merged[-1][2]=max(st[2],merged[-1][2])
    else: merged.append(st)
storms=merged
print('ratio p90',round(thr,3),'peaks',len(peaks),'storms',len(storms))
Cs={'spread':W.spread_bp,'dvp_out':W.dvp_out,'lev_net_short':W.lev}
def storm_his(C,shift=0):
    c=np.roll(C.values,shift); out=[]
    for s,k,e in storms:
        cc=c[s:e+1]
        if np.isnan(cc).any(): out.append((np.nan,np.nan,0)); continue
        h,f,n,_=hi_storm(Q.values[s:e+1],cc); out.append((h,f,n))
    return out
res={'n_weeks':int(len(W)),'start':str(W.index[0].date()),'end':str(W.index[-1].date()),'ratio_p90':round(float(thr),3),'storms':[],'tests':{}}
for (s,k,e) in storms: res['storms'].append({'start':str(Q.index[s].date()),'peak':str(Q.index[k].date()),'end':str(Q.index[e].date()),'peak_fails_bn':round(float(Q.iloc[k])/1e3,1),'ratio':round(float(ratio.iloc[k]),2)})
N=4999; L=len(W)
for nm,C in Cs.items():
    obs=storm_his(C); his=np.array([o[0] for o in obs]); fis=np.array([o[1] for o in obs])
    ok=np.isfinite(his); m=float(np.nanmean(his))
    null=[]
    for b in range(N):
        sh=int(rng.integers(8,L-8)); hh=np.array([o[0] for o in storm_his(C,sh)]); null.append(np.nanmean(hh))
    null=np.array(null); pv=(1+np.sum(np.abs(null)>=abs(m)))/(N+1)
    res['tests'][nm]={'n_storms':int(ok.sum()),'mean_HI':round(m,3),'median_HI':round(float(np.nanmedian(his)),3),'mean_FI':round(float(np.nanmean(fis)),3),
        'share_clockwise_ge0.2':round(float(np.mean(his[ok]>=0.2)),3),'share_anticlockwise_le-0.2':round(float(np.mean(his[ok]<=-0.2)),3),
        'null_mean':round(float(null.mean()),3),'null_sd':round(float(null.std()),3),'null_q025':round(float(np.quantile(null,.025)),3),'null_q975':round(float(np.quantile(null,.975)),3),'p_two_sided':round(float(pv),4),
        'per_storm':[None if not np.isfinite(h) else round(float(h),3) for h in his],'per_storm_FI':[None if not np.isfinite(f) else round(float(f),3) for f in fis]}
# Holm over the three
ps=sorted(((v['p_two_sided'],k) for k,v in res['tests'].items()))
run=0
for i,(pv,k) in enumerate(ps):
    run=max(run,min(1,pv*(3-i))); res['tests'][k]['p_holm']=round(run,4)
W.to_csv('q1_weekly_hyst.csv'); json.dump(res,open('q1_hyst.json','w'),indent=1)
for k,v in res['tests'].items(): print(k,{kk:vv for kk,vv in v.items() if not kk.startswith('per_')})
for s,h1,h2,h3 in zip(res['storms'],res['tests']['spread']['per_storm'],res['tests']['dvp_out']['per_storm'],res['tests']['lev_net_short']['per_storm']): print(s,h1,h2,h3)
