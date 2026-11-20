"""Independent NumPy port of Liang (2021) multivariate LKIF, lag 1 (eq. 14-20), for parity with LK_Info_flow."""
import numpy as np
from scipy.stats import norm
def lkif(X, dt=1.0):
    # X: (n_time, d)
    X = np.asarray(X, float); n, d = X.shape
    X0, X1 = X[:-1], X[1:]
    Z = np.column_stack([X0, np.ones(n-1)])
    B, *_ = np.linalg.lstsq(Z, X1, rcond=None)      # X1 = Z B
    A = (B[:d].T - np.eye(d)) / dt                   # drift matrix, A[i,j] effect of j on i
    C = np.cov(X0.T)
    T = A * (C / np.diag(C)[:, None])                # T[i,j] = a_ij C_ij / C_ii  (flow j->i)
    E = X1 - Z @ B
    SIG = E.T @ E / (n - 1 - d - 1)              # package uses (n - np - m - 1) with n=time length
    dHnoise = np.diag(np.abs(SIG)/dt) / (2*np.diag(C))   # placeholder, recomputed below as package
    Bm = np.sqrt(np.abs(SIG)/dt)
    dHnoise = (Bm**2).sum(axis=0) / (2*np.diag(C))
    Zn = np.abs(T).sum(axis=1) + np.abs(dHnoise)
    tau = T / Zn[:, None]
    XtX_inv = np.linalg.inv(X0.T @ X0)               # package uses uncentered X1 (no constant) here
    se_a = np.sqrt(np.outer(np.diag(SIG), np.diag(XtX_inv)))  # se of a_ij
    SE = se_a * np.abs(C / np.diag(C)[:, None]) / dt
    p = 2*(1-norm.cdf(np.abs(T/SE)))
    return dict(T=T, tau=tau, SE=SE, p=p, A=A, C=C, se_a=se_a)

def var1_t(X):
    """Correct OLS t-statistics of a_ij in X_{t+1} = c + B X_t (constant included, proper (Z'Z)^-1)."""
    X = np.asarray(X, float); n, d = X.shape
    X0, X1 = X[:-1], X[1:]; Z = np.column_stack([X0, np.ones(n-1)])
    B, *_ = np.linalg.lstsq(Z, X1, rcond=None); E = X1 - Z @ B
    s2 = (E**2).sum(0) / (n-1-d-1); V = np.linalg.inv(Z.T @ Z)
    se = np.sqrt(np.outer(s2, np.diag(V)[:d]))
    return B[:d].T / se
