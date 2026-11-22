import pandas as pd, numpy as np, json, sys, warnings
from statsmodels.tsa.api import VAR
import iccf_core as ic
warnings.filterwarnings('ignore')
LC=pd.read_csv('q1_lightcurves.csv',parse_dates=['date']); LMIN,LMAX,STEP=-365.,365.,7.
PAIRS={'P1':('pb','fails'),'P2':('pb','tri'),'P3':('pb','dvp'),'P4':('pb','spread'),'P5':('rr','dvp')}
O=pd.Timestamp('2013-01-01')
def get(k,lo=None,hi=None,transform='level'):
    d=LC[LC.series==k].sort_values('t').copy()
    if transform=='change':
        lagn=12 if k in ('pb','rr') else 52
        d['y']=d.y-d.y.shift(lagn); d=d.dropna()
    if lo is not None: d=d[(d.date>=lo)&(d.date<=hi)]
    return d
def detrend(t,y): b=np.polyfit(t,y,1); return y-np.polyval(b,t)
def ar1(y):
    y=y-y.mean(); phi=np.dot(y[1:],y[:-1])/np.dot(y[:-1],y[:-1]); s=np.std(y[1:]-phi*y[:-1],ddof=1); return phi,s
def sim_ar1(n,phi,s,rng):
    e=rng.normal(0,s,n+200); x=np.zeros(n+200)
    for i in range(1,n+200): x[i]=phi*x[i-1]+e[i]
    return x[200:]
def aaft(y,rng):
    n=len(y); g=np.sort(rng.normal(size=n))[np.argsort(np.argsort(y))]
    F=np.fft.rfft(g); ph=rng.uniform(0,2*np.pi,len(F)); ph[0]=0
    if n%2==0: ph[-1]=0
    s=np.fft.irfft(np.abs(F)*np.exp(1j*ph),n); return np.sort(y)[np.argsort(np.argsort(s))]
def monthly(d):
    m=d.groupby(d.date.dt.to_period('M')).y.mean(); return m
def standard(d1,d2,maxlag=12):
    a=monthly(d1); b=monthly(d2); idx=a.index.intersection(b.index); a=a[idx]; b=b[idx]
    t=np.arange(len(idx)); a=detrend(t,a.values); b=detrend(t,b.values); n=len(idx); band=1.96/np.sqrt(n)
    r={k:np.corrcoef(a[max(0,-k):n-max(0,k)],b[max(0,k):n-max(0,-k)])[0,1] for k in range(-maxlag,maxlag+1)}
    kbest=max(r,key=lambda k:abs(r[k]))
    # differences: monthly log changes
    da=np.diff(monthly(d1)[idx].values); db=np.diff(monthly(d2)[idx].values); nd=len(da); bd=1.96/np.sqrt(nd)
    rd={k:np.corrcoef(da[max(0,-k):nd-max(0,k)],db[max(0,k):nd-max(0,-k)])[0,1] for k in range(-maxlag,maxlag+1)}
    kd=max(rd,key=lambda k:abs(rd[k]))
    v=VAR(np.column_stack([da,db])); sel=v.select_order(6).bic; sel=max(int(sel),1); fit=v.fit(sel)
    g12=fit.test_causality(1,[0],kind='f').pvalue; g21=fit.test_causality(0,[1],kind='f').pvalue
    return dict(n_months=n,band=band,lag_maxabs=kbest,r_maxabs=r[kbest],n_lags_outside_band=int(sum(abs(v)>band for v in r.values())),
                diff_lag_maxabs=kd,diff_r_maxabs=rd[kd],diff_n_outside=int(sum(abs(v)>bd for v in rd.values())),diff_band=bd,
                granger_var_lag=sel,granger_market_to_pf_p=g12,granger_pf_to_market_p=g21,ccf_levels=r,ccf_diff=rd)
def analyse(k1,k2,lo=None,hi=None,transform='level',nnull=1000,nrss=2000,seed=0,curves=False):
    rng=np.random.default_rng(seed)
    d1=get(k1,transform=transform); d2=get(k2,transform=transform)
    a=max(d1.date.min(),d2.date.min()); b=min(d1.date.max(),d2.date.max())
    if lo is not None: a=max(a,pd.Timestamp(lo)); b=min(b,pd.Timestamp(hi))
    d1=d1[(d1.date>=a)&(d1.date<=b)]; d2=d2[(d2.date>=a)&(d2.date<=b)]
    t1=d1.t.values; t2=d2.t.values; y1=detrend(t1,d1.y.values); y2=detrend(t2,d2.y.values)
    rs,ls=ic.rstar(t1,y1,t2,y2,LMIN,LMAX,STEP); sg=np.sign(rs)
    r,lag,_=ic.xcor(t1,y1,t2,sg*y2,LMIN,LMAX,STEP); tp,tc,rmax,_=ic.peakcent(t1,y1,t2,sg*y2,LMIN,LMAX,STEP)
    pk,ce,rm=ic.rss_draws(t1,y1,t2,sg*y2,LMIN,LMAX,STEP,nrss,rng)
    ok=np.isfinite(ce); q=np.percentile(ce[ok],[2.5,15.87,50,84.13,97.5]) if ok.sum()>10 else [np.nan]*5
    p1=ar1(y1); p2=ar1(y2); na=[]; nb=[]; nullcurves=[]
    for i in range(nnull):
        s1=detrend(t1,sim_ar1(len(t1),*p1,rng)); s2=detrend(t2,sim_ar1(len(t2),*p2,rng)); na.append(abs(ic.rstar(t1,s1,t2,s2,LMIN,LMAX,STEP)[0]))
        u1=detrend(t1,aaft(y1,rng)); u2=detrend(t2,aaft(y2,rng)); rr,_,_=ic.xcor(t1,u1,t2,u2,LMIN,LMAX,STEP); nb.append(np.abs(rr).max())
        if curves and i<1000: nullcurves.append(np.abs(rr))
    na=np.array(na); nb=np.array(nb)
    res=dict(pair=f'{k1} x {k2}',window=[str(a.date()),str(b.date())],transform=transform,n1=len(t1),n2=len(t2),
      r_star=float(rs),lag_at_rstar=float(ls),sign=int(sg),peak_lag=float(tp) if np.isfinite(tp) else None,centroid_lag=float(tc) if np.isfinite(tc) else None,
      cccd_q=[float(x) for x in q],cccd_ok_share=float(ok.mean()),cccd68_excludes0=bool(q[1]>0 or q[3]<0),cccd95_excludes0=bool(q[0]>0 or q[4]<0),
      ar1_phi=[float(p1[0]),float(p2[0])],p_ar1=float((1+(na>=abs(rs)).sum())/(1+nnull)),p_phase=float((1+(nb>=abs(rs)).sum())/(1+nnull)),
      null95_ar1=float(np.percentile(na,95)),null95_phase=float(np.percentile(nb,95)))
    if curves:
        res['curve']=dict(lag=lag.tolist(),r=(sg*r).tolist(),null95_phase_pointwise=np.percentile(np.array(nullcurves),95,axis=0).tolist(),cccd=ce[ok].tolist())
        res['standard']=standard(d1,d2)
    return res
if __name__=='__main__':
    which=sys.argv[1]; out={}
    if which=='C1':
        for i,(p,(a,b)) in enumerate(PAIRS.items()): out[p]=analyse(a,b,seed=i,curves=True); print(p,{k:v for k,v in out[p].items() if k not in('curve','standard')},flush=True)
    if which=='C2':
        splits={'P1':[('2013-01-01','2019-12-31'),('2020-01-01','2025-12-31')],'P2':[('2013-01-01','2019-12-31'),('2020-01-01','2025-12-31')],
                'P3':[('2018-05-01','2021-12-31'),('2022-01-01','2025-12-31')],'P4':[('2018-05-01','2021-12-31'),('2022-01-01','2025-12-31')],'P5':[('2018-05-01','2021-12-31'),('2022-01-01','2025-12-31')]}
        for i,(p,(a,b)) in enumerate(PAIRS.items()):
            out[p]={'half1':analyse(a,b,*splits[p][0],nnull=500,nrss=1000,seed=10+i),'half2':analyse(a,b,*splits[p][1],nnull=500,nrss=1000,seed=20+i),
                    'change_full':analyse(a,b,transform='change',nnull=500,nrss=1000,seed=30+i)}
            print(p,{h:(v['r_star'],v['centroid_lag'],v['cccd_q'][1:4],v['p_ar1'],v['p_phase']) for h,v in out[p].items()},flush=True)
    json.dump(out,open(f'{which}.json','w'),indent=1,default=float)
