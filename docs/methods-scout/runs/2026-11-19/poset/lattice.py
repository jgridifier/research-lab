"""Exact rank probabilities of a finite poset by dynamic programming over its lattice of ideals
(downsets), the idea in De Loof, De Meyer & De Baets (2006). Independent re-implementation for parity
against netrankr::exact_rank_prob. P[i,j]=1 means i is ranked below j (i <= j). Ranks 1..n, 1 = lowest."""
import numpy as np, itertools, json, sys
from functools import lru_cache

def exact(P):
    P=np.asarray(P); n=len(P)
    pred=[0]*n
    for i in range(n):
        for j in range(n):
            if P[i,j] and i!=j: pred[j]|=1<<i     # i must come before j
    full=(1<<n)-1
    # forward: number of ways to build downset D from empty (count of linear extensions of D)
    fwd={0:1}; layers=[[0]]
    for k in range(n):
        nxt={}
        for D in layers[-1]:
            c=fwd[D]
            for u in range(n):
                if not (D>>u)&1 and (pred[u]&~D)==0:
                    E=D|(1<<u); nxt[E]=nxt.get(E,0)+c
        fwd.update(nxt); layers.append(list(nxt.keys()))
    bwd={full:1}
    for k in range(n,0,-1):
        for D in layers[k-1]:
            s=0
            for u in range(n):
                if not (D>>u)&1 and (pred[u]&~D)==0: s+=bwd[D|(1<<u)]
            bwd[D]=s
    total=fwd[full]
    R=np.zeros((n,n))
    for k in range(n):
        for D in layers[k]:
            for u in range(n):
                if not (D>>u)&1 and (pred[u]&~D)==0:
                    R[u,k]+=fwd[D]*bwd[D|(1<<u)]
    R/=total
    exp=R@np.arange(1,n+1)
    return total,R,exp,sum(len(l) for l in layers)

def brute(P):
    P=np.asarray(P); n=len(P); cnt=0; R=np.zeros((n,n))
    for perm in itertools.permutations(range(n)):
        pos={u:k for k,u in enumerate(perm)}
        if all(pos[i]<pos[j] for i in range(n) for j in range(n) if P[i,j] and i!=j):
            cnt+=1
            for u,k in pos.items(): R[u,k]+=1
    return cnt,R/cnt

if __name__=='__main__':
    J=json.load(open('home_repro_R.json'))
    out={}
    def chk(name,P,lin,expR,RR=None):
        t,R,e,ni=exact(P); b,Rb=brute(P) if len(P)<=9 else (None,None)
        d={'lin_ext_R':lin,'lin_ext_dp':int(t),'lin_ext_brute':b,'max_abs_expected_vs_R':float(np.max(np.abs(e-np.array(expR)))),
           'max_abs_rankprob_dp_vs_brute':None if Rb is None else float(np.max(np.abs(R-Rb)))}
        if RR is not None: d['max_abs_rankprob_vs_R']=float(np.max(np.abs(R-np.array(RR))))
        out[name]=d
    e5=J['ex5']; chk('ex5',np.array(e5['P']),e5['lin_ext'],e5['expected'],e5['rank_prob'])
    for k,r in enumerate(J['random']): chk(f'random{k}',np.array(r['P']),r['lin_ext'],r['expected'],r['rank_prob'])
    worst={'max_expected':max(v['max_abs_expected_vs_R'] for v in out.values()),
           'max_rankprob_R':max(v.get('max_abs_rankprob_vs_R',0) for v in out.values()),
           'max_rankprob_brute':max(v['max_abs_rankprob_dp_vs_brute'] or 0 for v in out.values()),
           'all_counts_equal':all(v['lin_ext_R']==v['lin_ext_dp'] and (v['lin_ext_brute'] in (None,v['lin_ext_dp'])) for v in out.values())}
    out['worst']=worst; print(worst)
    json.dump(out,open('parity_python_vs_R.json','w'),indent=1)
