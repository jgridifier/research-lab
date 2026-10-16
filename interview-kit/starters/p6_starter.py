"""
Monte Carlo credit losses, then make it fast. ~12 minutes.

One-factor Gaussian (Vasicek) model, rho = 0.15. Loan i defaults in sim s if
    sqrt(rho) * Z_s + sqrt(1 - rho) * eps_{s,i} < Phi^{-1}(PD_i)
Loss_s = sum_i EAD_i * LGD_i * 1{default}.
1. Simulate 20,000 scenarios; report expected loss, 99.9% VaR and ES.
   Check EL against the analytic value sum(EAD * LGD * PD).
2. Make it fast: vectorize with numpy and/or use numba (if available).
   Show both versions give the same answer on the same random draws.
"""
import math
import time
import numpy as np
from scipy.stats import norm


def make_portfolio(n_loans: int = 500, seed: int = 5):
    rng = np.random.default_rng(seed)
    ead = rng.lognormal(mean=0.0, sigma=1.0, size=n_loans)   # exposures
    pd_ = rng.uniform(0.005, 0.05, size=n_loans)              # default probs
    lgd = rng.uniform(0.3, 0.6, size=n_loans)
    return ead, pd_, lgd


def simulate_losses(n_sims, ead, pd_, lgd, rho, seed=0):
    raise NotImplementedError


def check():
    ead, pd_, lgd = make_portfolio()
    L = simulate_losses(20_000, ead, pd_, lgd, 0.15)
    print("EL MC", L.mean(), "EL analytic", np.sum(ead * lgd * pd_))
    print("checks passed")


if __name__ == "__main__":
    check()
