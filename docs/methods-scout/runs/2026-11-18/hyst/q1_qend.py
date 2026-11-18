# POST-HOC (not pre-registered): is the anticlockwise spread loop a quarter-end calendar effect?
import numpy as np, pandas as pd, json
from hyst import hi_storm
W=pd.read_csv('q1_weekly_hyst.csv',parse_dates=['date']).set_index('date'); H=json.load(open('q1_hyst.json'))
qe=pd.Series(W.index,index=W.index).apply(lambda d: any(0<= (d-pd.Timestamp(y,m,1)+pd.Timedelta(days=1)).days <=7 for y in [d.year] for m in [1,4,7,10]) or (d.month==12 and d.day>=25))
sp=W.spread_bp.copy(); sp[qe]=np.nan; sp=sp.interpolate(limit_area='inside')
Q=W.fails_fin_ust; rng=np.random.default_rng(5); idx={d:i for i,d in enumerate(W.index)}
st=[(idx[pd.Timestamp(s['start'])],idx[pd.Timestamp(s['peak'])],idx[pd.Timestamp(s['end'])]) for s in H['storms']]
def his(c): return np.array([hi_storm(Q.values[s:e+1],c[s:e+1])[0] for s,k,e in st])
h=his(sp.values); m=float(np.nanmean(h)); L=len(W)
null=np.array([np.nanmean(his(np.roll(sp.values,int(rng.integers(8,L-8))))) for _ in range(4999)])
out={'quarter_end_weeks_masked':int(qe.sum()),'mean_HI':round(m,3),'p_two_sided':round(float((1+np.sum(np.abs(null)>=abs(m)))/5000),4),'per_storm':[round(float(x),3) for x in h],'share_le-0.2':round(float(np.mean(h<=-0.2)),3)}
json.dump(out,open('q1_qend_posthoc.json','w'),indent=1); print(out)
