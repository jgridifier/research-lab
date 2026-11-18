# Minimal NumPy port of STEM's assignment + permutation test (Ernst, Nau & Bar-Joseph 2005), used for parity
# against stem.jar 1.3.15 and for custom nulls. Model profiles are taken from the jar's profile table.
import numpy as np, itertools, math
from scipy.stats import binom
def corr_rows(A,B):
    A=A-A.mean(1,keepdims=True); B=B-B.mean(1,keepdims=True)
    na=np.linalg.norm(A,axis=1,keepdims=True); nb=np.linalg.norm(B,axis=1,keepdims=True)
    with np.errstate(invalid='ignore',divide='ignore'): C=(A@B.T)/(na*nb.T)
    return np.nan_to_num(C,nan=-2)
def assign_counts(V,P,eps=1e-9):
    """V: genes x T (already v - v0), P: profiles x T. Ties split equally (as in tallyassignments)."""
    C=corr_rows(V,P); mx=C.max(1,keepdims=True); W=(C>=mx-eps).astype(float); W/=W.sum(1,keepdims=True)
    return W.sum(0), C.argmax(1)
def stem(X,P,permute0=True,alpha=0.05):
    X=np.asarray(X,float); P=np.asarray(P,float); n,T=X.shape
    cnt,lab=assign_counts(X-X[:,[0]],P)
    perms=list(itertools.permutations(range(T))) if permute0 else [(0,)+q for q in itertools.permutations(range(1,T))]
    exp=np.zeros(len(P))
    for q in perms:
        Y=X[:,list(q)]; c,_=assign_counts(Y-Y[:,[0]],P); exp+=c
    exp/=len(perms)
    p=np.array([binom.sf(math.ceil(cnt[i]-1),n,exp[i]/n) for i in range(len(P))])
    sig=p<alpha/len(P)
    return dict(count=cnt,expected=exp,p=p,sig=sig,label=lab)
