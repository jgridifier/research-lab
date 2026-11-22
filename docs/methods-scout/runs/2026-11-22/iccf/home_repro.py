import numpy as np, json, time, sys
sys.path.insert(0,'.'); import iccf_core as ic, PYCCF3 as orig
D='PyCCF_orig/PurePython/'; C='PyCCF_orig/CPython/'
t1,y1,e1=np.loadtxt(D+'sample_lc1.dat',unpack=True,usecols=[0,1,2]); t2,y2,e2=np.loadtxt(D+'sample_lc2.dat',unpack=True,usecols=[0,1,2])
ship=np.loadtxt(C+'sample_ccf_yap.dat'); cent_ship=np.loadtxt(C+'sample_centtab_yap.dat'); peak_ship=np.loadtxt(C+'sample_peaktab_yap.dat')
r_o,lag_o,n_o=orig.xcor(t1,y1,t2,y2,-100,100,2.)
r_n,lag_n,n_n=ic.xcor(t1,y1,t2,y2,-100,100,2.)
out=dict(n_lags=len(lag_o), shipped_lags_match=bool(np.allclose(ship[:,0],lag_o)),
 max_abs_orig_vs_shipped=float(np.abs(r_o-ship[:,1]).max()), max_abs_numpy_vs_shipped=float(np.abs(r_n-ship[:,1]).max()),
 max_abs_numpy_vs_orig=float(np.abs(r_n-r_o).max()), lags_identical=bool(np.array_equal(lag_o,lag_n)))
po=orig.peakcent(t1,y1,t2,y2,-100,100,2.); pn=ic.peakcent(t1,y1,t2,y2,-100,100,2.)
out.update(peak_orig=float(po[0]),cent_orig=float(po[2]),peak_numpy=float(pn[0]),cent_numpy=float(pn[1]))
# random uneven pairs parity
rng=np.random.default_rng(7); md=0.0
for k in range(50):
    a=np.sort(rng.uniform(0,300,rng.integers(20,200))); b=np.sort(rng.uniform(0,300,rng.integers(10,80)))
    ya=np.cumsum(rng.normal(size=len(a))); yb=np.cumsum(rng.normal(size=len(b)))
    ro,lo,_=orig.xcor(a,ya,b,yb,-60,60,1.5); rn,ln,_=ic.xcor(a,ya,b,yb,-60,60,1.5)
    md=max(md,float(np.abs(ro-rn).max())) if len(ro)==len(rn) and np.array_equal(lo,ln) else float('inf')
out['max_abs_numpy_vs_orig_random50']=md
# CCCD (FR+RSS, 500 draws) vs shipped
np.random.seed(20261122); t0=time.time()
res=orig.xcor_mc(t1,y1,abs(e1),t2,y2,abs(e2),-100,100,2.,nsim=500,mcmode=0,sigmode=0.2); t_orig=time.time()-t0
t0=time.time(); pk,ce,rm=ic.rss_draws(t1,y1,t2,y2,-100,100,2.,500,np.random.default_rng(20261122),dy1=abs(e1),dy2=abs(e2),fr=True); t_np=time.time()-t0
q=lambda x:[round(float(v),2) for v in np.percentile(x[np.isfinite(x)],[15.87,50,84.13])]
out.update(cccd_shipped=q(cent_ship),cccd_orig_rerun=q(res[1]),cccd_numpy=q(ce),ccpd_shipped=q(peak_ship),ccpd_numpy=q(pk),
  n_ok_shipped=len(cent_ship),n_ok_numpy=int(np.isfinite(ce).sum()),seconds_orig_500=round(t_orig,2),seconds_numpy_500=round(t_np,2))
json.dump(out,open('home_repro.json','w'),indent=1); print(json.dumps(out,indent=1))
