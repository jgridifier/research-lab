"""
Local projection impulse response with Newey-West SEs. ~12 minutes.

df: columns y, s (an observed, identified shock). For h = 0..8 estimate
    y_{t+h} - y_{t-1} = a_h + b_h s_t + 2 lags of y and s + u_{t+h}
Return a DataFrame indexed by h with irf (b_h), se, lo, hi (95%).
Write the Newey-West covariance yourself (numpy), then check it against
statsmodels' HAC if you have time. How many lags, and why?
"""
import numpy as np
import pandas as pd


def make_data(T: int = 3000, seed: int = 3):
    """y_t = rho y_{t-1} + theta s_t + e_t, s iid N(0,1).
    The cumulative response of y_{t+h} - y_{t-1} to s_t is theta * rho^h."""
    rng = np.random.default_rng(seed)
    rho, theta = 0.8, 1.0
    s = rng.normal(size=T)
    y = np.zeros(T)
    for t in range(1, T):
        y[t] = rho * y[t - 1] + theta * s[t] + rng.normal(0, 1.0)
    true_irf = lambda h: theta * rho ** h
    z = s + rng.normal(0, 1.0, size=T)          # instrument correlated with s
    s_noisy = s + rng.normal(0, 1.0, size=T)    # mismeasured shock
    df = pd.DataFrame({"y": y, "s": s, "s_noisy": s_noisy, "z": z})
    return df, true_irf


def newey_west(X: np.ndarray, u: np.ndarray, L: int) -> np.ndarray:
    raise NotImplementedError


def local_projection(df: pd.DataFrame, Hmax: int = 8) -> pd.DataFrame:
    raise NotImplementedError


def check():
    df, true_irf = make_data()
    irf = local_projection(df, Hmax=8)
    truth = np.array([true_irf(h) for h in irf.index])
    print(irf.assign(true=truth).round(3))
    assert np.max(np.abs(irf.irf - truth)) < 0.15
    print("checks passed")


if __name__ == "__main__":
    check()
