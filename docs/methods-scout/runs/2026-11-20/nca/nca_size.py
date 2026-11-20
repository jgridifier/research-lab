# How often does the standard NCA permutation test call "necessity" when data are only correlated (Gaussian copula, no ceiling)?
import numpy as np, json, sys; sys.path.insert(0,'.')
from nca_port import ce_fdh
from q3_nca import d as D
rng=np.random.default_rng(3); out={}
for lab,xc in [('drawdown-like',-D.drawdown.values),('cet1min-like',D.cet1_min.values)]:
    y0=np.sort(D.payout_rwa.values); xs=np.sort(xc); n=len(xs)
    for rs in [0.0,0.1,0.2,0.3]:
        r=2*np.sin(np.pi*rs/6); rej=0; S=200
        for s in range(S):
            z1=rng.standard_normal(n); z2=r*z1+np.sqrt(1-r*r)*rng.standard_normal(n)
            x=xs[np.argsort(np.argsort(z1))]; y=y0[np.argsort(np.argsort(z2))]
            obs=ce_fdh(x,y)['d']; c=sum(ce_fdh(x,rng.permutation(y))['d']>=obs for _ in range(199))
            rej+= (c+1)/200<0.05
        out[f'{lab}|rho_s={rs}']=rej/S; print(lab,rs,rej/S,flush=True)
json.dump(out,open('nca_size.json','w'),indent=1)
