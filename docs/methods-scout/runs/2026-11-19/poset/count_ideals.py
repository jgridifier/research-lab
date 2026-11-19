import pandas as pd, numpy as np, time, sys
from prep_lib import load, dom, S
from lattice import exact
P=load()
for y,g in P.groupby('year'):
    t=time.time(); M=dom(g[S].values)
    tot,R,e,ni=exact(M)
    print(y,len(g),'ideals',ni,'linext %.3e'%tot,'sec %.1f'%(time.time()-t),flush=True)
