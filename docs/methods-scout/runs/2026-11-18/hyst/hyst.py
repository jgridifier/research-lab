# Storm C-Q hysteresis (Lloyd et al. 2016 HInew; Vaughan et al. 2017 FI) on public Q1 aggregates. Pre-registered in ../PREREG.md.
import numpy as np, pandas as pd, json
rng=np.random.default_rng(20261118)
def hi_storm(q,c,inc=0.05):
    """q,c arrays over the storm (start..end); peak = argmax q. Returns HI (mean HI_j), FI, n_j, per-j values."""
    q=np.asarray(q,float); c=np.asarray(c,float); k=int(np.argmax(q))
    if np.ptp(q)==0 or np.ptp(c)==0: return np.nan,np.nan,0,[]
    qn=(q-q.min())/np.ptp(q); cn=(c-c.min())/np.ptp(c)
    def interp_limb(qs,cs,level):
        for i in range(len(qs)-1):
            a,b=qs[i],qs[i+1]
            if (a-level)*(b-level)<=0 and a!=b: return cs[i]+(cs[i+1]-cs[i])*(level-a)/(b-a)
        return np.nan
    rq,rc=qn[:k+1],cn[:k+1]; fq,fc=qn[k:],cn[k:]
    vals=[]
    for lev in np.arange(inc,1.0-1e-9,inc):
        r=interp_limb(rq,rc,lev); f=interp_limb(fq,fc,lev)
        if np.isfinite(r) and np.isfinite(f): vals.append(r-f)
    hi=float(np.mean(vals)) if vals else np.nan
    fi=float(cn[k]-cn[0])
    return hi,fi,len(vals),vals
if __name__=='__main__':
    # ---- home-field: Lloyd 2016 Fig. 1c idealised normalised storm (TRL/TFL at 25% and 75% discharge)
    home={'fig1c_25pct':{'HILA':0.6/0.1-1,'HInew':0.6-0.1},'fig1c_75pct':{'HILA':0.9/0.4-1,'HInew':0.9-0.4},
          'fig1a_HIL':{'(5,1)':5/1-1,'(10,6)':10/6-1},'fig1b_HIL':{'(8,6)':8/6-1,'(3,5) anticlockwise':-1/(3/5)+1}}
    # a perfect loop: c leads q by a quarter cycle -> clockwise (HI>0); lags -> anticlockwise
    t=np.linspace(0,np.pi,41); q=np.sin(t)
    home['synthetic_lead']=hi_storm(q,np.sin(t+0.6))[0]; home['synthetic_lag']=hi_storm(q,np.sin(t-0.6))[0]
    json.dump({k:(round(v,4) if isinstance(v,float) else {kk:round(vv,4) for kk,vv in v.items()}) for k,v in home.items()},open('home_lloyd.json','w'),indent=1)
    print('home',json.load(open('home_lloyd.json')))
