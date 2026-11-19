import json,numpy as np
from prep_lib import load,dom,S
P=load(); out={}
for y,g in P.groupby('year'): out[str(y)]=dom(g[S].values).tolist()
json.dump(out,open('posets_by_year.json','w'))
