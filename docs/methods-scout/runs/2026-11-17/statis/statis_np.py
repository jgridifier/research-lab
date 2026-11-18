"""COVSTATIS / STATIS core in NumPy (Abdi et al. 2012 WIREs CS 4:124-167; Lavit et al. 1994).
Input: list of K symmetric PSD-ish matrices on the same I objects. Steps: optional double-centering, MFA normalisation
(first eigenvalue = 1), RV interstructure, weights = first eigenvector of C (rescaled to sum 1), compromise, eigen-decomposition,
partial factor scores F_k = S_k Q Lambda^{-1/2}."""
import numpy as np
def dcenter(S):
    I=S.shape[0]; J=np.eye(I)-np.ones((I,I))/I; return J@S@J
def rv(A,B): return float(np.trace(A@B)/np.sqrt(np.trace(A@A)*np.trace(B@B)))
def rv_mod(A,B):
    A=A-np.diag(np.diag(A)); B=B-np.diag(np.diag(B)); return float(np.sum(A*B)/np.sqrt(np.sum(A*A)*np.sum(B*B)))
def statis(mats,center=True,norm='MFA',nf=3,rvfun=rv):
    S=[dcenter(M) if center else M.copy() for M in mats]
    if norm=='MFA': S=[s/np.linalg.eigvalsh(s)[-1] for s in S]
    K=len(S); C=np.array([[rvfun(S[a],S[b]) for b in range(K)] for a in range(K)])
    ev,U=np.linalg.eigh(C); u=U[:,-1]; u=u*np.sign(u.sum()); alpha=u/u.sum()
    Sp=sum(a*s for a,s in zip(alpha,S))
    lam,Q=np.linalg.eigh(Sp); o=np.argsort(lam)[::-1]; lam=lam[o]; Q=Q[:,o]
    keep=lam>1e-12; lam=lam[keep]; Q=Q[:,keep]
    F=Q*np.sqrt(lam); P=Q/np.sqrt(lam)
    Fk=np.stack([s@P for s in S])
    return dict(C=C,C_eig=ev[::-1],alpha=alpha,Splus=Sp,lam=lam,tau=lam/lam.sum(),F=F[:,:nf],Fk=Fk[:,:,:nf],S=S,Q=Q,P=P)
