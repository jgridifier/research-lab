import pandas as pd, numpy as np, json, sys, warnings
import iccf_core as ic
from q1_iccf import get, detrend, ar1, sim_ar1, aaft, standard, LMIN, LMAX, STEP
warnings.filterwarnings('ignore')
which=sys.argv[1]; rng=np.random.default_rng(20261122 if which=='size' else 7); out={}
if which=='size':
    for P,(k1,k2) in {'P1':('pb','fails'),'P5':('rr','dvp')}.items():
        d1=get(k1); d2=get(k2); a=max(d1.date.min(),d2.date.min()); b=min(d1.date.max(),d2.date.max())
        d1=d1[(d1.date>=a)&(d1.date<=b)].copy(); d2=d2[(d2.date>=a)&(d2.date<=b)].copy(); t1=d1.t.values; t2=d2.t.values
        p1=ar1(detrend(t1,d1.y.values)); p2=ar1(detrend(t2,d2.y.values))
        rec=[]; NS=300; NN=200
        for s in range(NS):
            y1=sim_ar1(len(t1),*p1,rng); y2=sim_ar1(len(t2),*p2,rng); d1['y']=y1; d2['y']=y2
            st=standard(d1,d2); z1=detrend(t1,y1); z2=detrend(t2,y2)
            rs,ls=ic.rstar(t1,z1,t2,z2,LMIN,LMAX,STEP); sg=np.sign(rs)
            _,_,rmax,_=ic.peakcent(t1,z1,t2,sg*z2,LMIN,LMAX,STEP)
            pk,ce,rm=ic.rss_draws(t1,z1,t2,sg*z2,LMIN,LMAX,STEP,200,rng); ok=np.isfinite(ce)
            q=np.percentile(ce[ok],[2.5,15.87,84.13,97.5]) if ok.sum()>20 else [np.nan]*4
            q1a=ar1(z1); q2a=ar1(z2)
            na=np.array([abs(ic.rstar(t1,detrend(t1,sim_ar1(len(t1),*q1a,rng)),t2,detrend(t2,sim_ar1(len(t2),*q2a,rng)),LMIN,LMAX,STEP)[0]) for _ in range(NN)])
            nb=np.array([abs(ic.rstar(t1,detrend(t1,aaft(z1,rng)),t2,detrend(t2,aaft(z2,rng)),LMIN,LMAX,STEP)[0]) for _ in range(NN)])
            rec.append(dict(bartlett_levels=st['n_lags_outside_band']>0,bartlett_diff=st['diff_n_outside']>0,granger=min(st['granger_market_to_pf_p'],st['granger_pf_to_market_p'])<0.05,
                home95=bool(abs(rs)>0.5 and (q[0]>0 or q[3]<0)),home68=bool(q[1]>0 or q[2]<0),
                null_ar1=(1+(na>=abs(rs)).sum())/(1+NN)<0.05,null_phase=(1+(nb>=abs(rs)).sum())/(1+NN)<0.05,abs_rstar=abs(rs)))
            if s%50==0: print(P,s,flush=True)
        R=pd.DataFrame(rec); out[P]=dict(nsim=NS,phi=[p1[0],p2[0]],rates={c:round(float(R[c].mean()),3) for c in R.columns if c!='abs_rstar'},median_abs_rstar=round(float(R.abs_rstar.median()),3))
        print(P,out[P],flush=True)
if which=='planted':
    # planted +119-day lag on P1 cadence: latent weekly AR(1) (phi .95); driver = latent at month ends; response = latent 17 weeks earlier + AR(1) noise, SNR 1
    d1=get('pb'); d2=get('fails'); a=max(d1.date.min(),d2.date.min()); b=min(d1.date.max(),d2.date.max())
    t1=d1[(d1.date>=a)&(d1.date<=b)].t.values; t2=d2[(d2.date>=a)&(d2.date<=b)].t.values
    grid=np.arange(t2.min()-400,t2.max()+8,7.0); rec=[]
    for s in range(200):
        x=sim_ar1(len(grid),0.95,1.0,rng)
        y1=np.interp(t1,grid,x); y2=np.interp(t2-119,grid,x); y2=y2/np.std(y2)+sim_ar1(len(t2),0.7,1.0,rng)*np.sqrt(1/(1/(1-0.49)))
        z1=detrend(t1,y1); z2=detrend(t2,y2)
        _,tc,rmax,_=ic.peakcent(t1,z1,t2,z2,LMIN,LMAX,STEP)
        pk,ce,rm=ic.rss_draws(t1,z1,t2,z2,LMIN,LMAX,STEP,300,rng); ok=np.isfinite(ce)
        q=np.percentile(ce[ok],[15.87,50,84.13]) if ok.sum()>20 else [np.nan]*3
        rec.append(dict(tc=tc,med=q[1],half=(q[2]-q[0])/2,cover68=bool(q[0]<=119<=q[2])))
    R=pd.DataFrame(rec).dropna(); e=R.med-119
    out=dict(nsim=len(R),bias_median=round(float(e.median()),1),sigma_obs=round(float((np.percentile(e,84.13)-np.percentile(e,15.87))/2),1),
             sigma_est_mean=round(float(R.half.mean()),1),eta=round(float(R.half.mean()/((np.percentile(e,84.13)-np.percentile(e,15.87))/2)),2),coverage68=round(float(R.cover68.mean()),3))
    print(out)
if which=='yu':
    D='PyCCF_orig/PurePython/'; t1,y1,e1=np.loadtxt(D+'sample_lc1.dat',unpack=True,usecols=[0,1,2]); t2,y2,e2=np.loadtxt(D+'sample_lc2.dat',unpack=True,usecols=[0,1,2])
    f1=np.median(e1/y1); f2=np.median(e2/y2); grid=np.arange(t1.min()-100,t1.max()+1,0.5); rec=[]
    for s in range(200):
        x=sim_ar1(len(grid),np.exp(-0.5/100),1.0,rng); c=10+np.interp(t1,grid,x); l=10+np.interp(t2-20,grid,x)
        c=c+rng.normal(0,f1*np.abs(c)); l=l+rng.normal(0,f2*np.abs(l))
        pk,ce,rm=ic.rss_draws(t1,c,t2,l,-100,100,2.,300,rng,dy1=f1*np.abs(c),dy2=f2*np.abs(l),fr=True); ok=np.isfinite(ce)
        if ok.sum()<20: continue
        q=np.percentile(ce[ok],[15.87,50,84.13]); rec.append(dict(med=q[1],half=(q[2]-q[0])/2))
    R=pd.DataFrame(rec); e=R.med-20; so=(np.percentile(e,84.13)-np.percentile(e,15.87))/2
    out=dict(nsim=len(R),true_lag=20,bias_median=round(float(e.median()),2),sigma_obs=round(float(so),2),sigma_est=round(float(R.half.mean()),2),eta=round(float(R.half.mean()/so),2),drw_tau_days=100,mode='FR+RSS, sample cadence')
    print(out)
json.dump(out,open(f'C3_{which}.json','w'),indent=1,default=float)
