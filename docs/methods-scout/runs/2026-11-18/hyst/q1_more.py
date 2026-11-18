import numpy as np, pandas as pd, json
from hyst import hi_storm
rng=np.random.default_rng(1118); out={}
R=json.load(open('q1_hyst.json'))
# leave-one-storm-out for the spread mean HI
h=np.array([v for v in R['tests']['spread']['per_storm']],float)
loo=[float(np.nanmean(np.delete(h,i))) for i in range(len(h))]
out['spread_loo_mean_HI']={'min':round(min(loo),3),'max':round(max(loo),3),'all_negative':bool(max(loo)<0)}
# H4 daily: storms on DVP - tri-party overnight spread spikes (20 business-day windows), C = DVP outstanding volume (overnight/open)
d=pd.read_csv('/workspace/research/drive_inv/data/cleared_repo_daily.csv.gz')
d=d[d.mnemonic.isin(['REPO-DVP_AR_OO-F','REPO-TRI_AR_OO-F','REPO-DVP_OV_OO-F'])]
P=d.pivot_table(index='date',columns='mnemonic',values='value',aggfunc='last').dropna(); P.index=pd.to_datetime(P.index)
sp=(P['REPO-DVP_AR_OO-F']-P['REPO-TRI_AR_OO-F'])*100; vol=P['REPO-DVP_OV_OO-F']
ratio=(sp-sp.shift(1).rolling(130,min_periods=100).median())  # spread can be <=0: use excess over trailing median (bp)
thr=ratio.quantile(0.90); Q=sp.values; storms=[]
for i in range(len(Q)):
    lo,hi=max(0,i-20),min(len(Q),i+21)
    if Q[i]==Q[lo:hi].max() and ratio.iloc[i]>=thr:
        s=max(0,i-20)+int(np.argmin(Q[max(0,i-20):i+1])); e=i+int(np.argmin(Q[i:min(len(Q),i+21)]))
        if i-s>=2 and e-i>=2: storms.append([s,i,e])
m=[]
for st in sorted(storms):
    if m and st[0]<=m[-1][2]:
        if Q[st[1]]>Q[m[-1][1]]: m[-1]=[min(st[0],m[-1][0]),st[1],max(st[2],m[-1][2])]
        else: m[-1][2]=max(st[2],m[-1][2])
    else: m.append(st)
storms=m
def his(c): return np.array([hi_storm(Q[s:e+1],c[s:e+1])[0] for s,k,e in storms])
obs=his(vol.values); mo=float(np.nanmean(obs)); L=len(Q)
null=np.array([np.nanmean(his(np.roll(vol.values,int(rng.integers(40,L-40))))) for _ in range(1999)])
out['daily_spread_storms_vs_dvp_volume']={'note':'pre-registered rule adapted: spread can be <= 0, so the storm trigger is spread minus its trailing 130-day median in its top 10% (1.5x ratio not defined)',
  'n_days':int(L),'start':str(P.index[0].date()),'end':str(P.index[-1].date()),'n_storms':len(storms),'mean_HI':round(mo,3),'share_cw_ge0.2':round(float(np.mean(obs>=0.2)),3),'share_acw_le-0.2':round(float(np.mean(obs<=-0.2)),3),
  'null_q025':round(float(np.quantile(null,.025)),3),'null_q975':round(float(np.quantile(null,.975)),3),'p_two_sided':round(float((1+np.sum(np.abs(null)>=abs(mo)))/2000),4),
  'storms':[[str(P.index[s].date()),str(P.index[k].date()),str(P.index[e].date()),round(float(Q[k]),1),None if not np.isfinite(x) else round(float(x),3)] for (s,k,e),x in zip(storms,obs)]}
# power: weekly storms shaped like ours (rise 3 wks, fall 5 wks), C = Q shifted by lag weeks + noise
pw={}
for lag in [0,1,2]:
    for noise in [0.1,0.3]:
        rej=0
        for rep in range(200):
            hs=[]
            for s in range(13):
                tt=np.arange(-6,12); q=np.exp(-0.5*((tt)/2.0)**2)+rng.normal(0,0.05,len(tt))
                c=np.exp(-0.5*((tt-lag)/2.0)**2)+rng.normal(0,noise,len(tt))
                k=int(np.argmax(q)); s0=max(0,k-3); e0=min(len(tt)-1,k+5); hs.append(hi_storm(q[s0:e0+1],c[s0:e0+1])[0])
            hs=np.array(hs); se=np.nanstd(hs,ddof=1)/np.sqrt(np.isfinite(hs).sum())
            rej+=int(abs(np.nanmean(hs))/se>1.96)
        pw[f'lag{lag}_noise{noise}']={'reject_rate':rej/200}
out['power_13_weekly_storms']=pw
json.dump(out,open('q1_more.json','w'),indent=1); print(json.dumps(out,indent=1))
