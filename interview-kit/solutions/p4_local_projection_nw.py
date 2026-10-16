"""
Problem 4 (swap-in, ~12 min): local projection impulse response
with Newey-West standard errors, coded by hand, cross-checked with statsmodels.

For h = 0..Hmax:
    y_{t+h} - y_{t-1} = a_h + b_h s_t + sum_{l=1..L} (g_l y_{t-l} + d_l s_{t-l}) + u_{t+h}
b_h is the impulse response at horizon h. u_{t+h} is MA(h) by construction,
so use HAC (Newey-West) SEs with at least h+1 lags.
Extension: LP-IV when s_t is observed with noise and z_t is an instrument.
"""
import numpy as np
import pandas as pd


# ----------------------------------------------------------------------------
# Synthetic data with a known IRF
# ----------------------------------------------------------------------------
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


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def newey_west(X: np.ndarray, u: np.ndarray, L: int, small_sample: bool = True):
    """HAC covariance (Bartlett kernel, L lags): (X'X)^-1 S (X'X)^-1,
    S = G0 + sum_{l=1..L} w_l (G_l + G_l'), w_l = 1 - l/(L+1), G_l = sum_t x_t u_t u_{t-l} x_{t-l}'.
    small_sample multiplies by n/(n-k) (statsmodels' default use_correction)."""
    n, k = X.shape
    Xu = X * u[:, None]
    S = Xu.T @ Xu
    for l in range(1, L + 1):
        w = 1 - l / (L + 1)
        G = Xu[l:].T @ Xu[:-l]
        S += w * (G + G.T)
    XtX_inv = np.linalg.inv(X.T @ X)
    V = XtX_inv @ S @ XtX_inv
    return V * (n / (n - k)) if small_sample else V


def lp_design(df: pd.DataFrame, h: int, shock: str = "s", n_lags: int = 2):
    d = pd.DataFrame({"lhs": df.y.shift(-h) - df.y.shift(1),
                      "const": 1.0, "shock": df[shock]})
    for l in range(1, n_lags + 1):
        d[f"y_l{l}"] = df.y.shift(l)
        d[f"s_l{l}"] = df[shock].shift(l)
    d = d.dropna()
    return d.drop(columns="lhs"), d["lhs"]


def local_projection(df, Hmax=8, shock="s", n_lags=2):
    rows = []
    for h in range(Hmax + 1):
        X, y = lp_design(df, h, shock, n_lags)
        Xn, yn = X.to_numpy(), y.to_numpy()
        b, *_ = np.linalg.lstsq(Xn, yn, rcond=None)
        u = yn - Xn @ b
        V = newey_west(Xn, u, L=h + 1)
        j = list(X.columns).index("shock")
        se = np.sqrt(V[j, j])
        rows.append(dict(h=h, irf=b[j], se=se, lo=b[j] - 1.96 * se, hi=b[j] + 1.96 * se))
    return pd.DataFrame(rows).set_index("h")


def lp_iv(df, h, endog="s_noisy", instr="z", n_lags=2):
    """Just-identified 2SLS: beta = (Z'X)^-1 Z'y, with HAC on the 2SLS residuals."""
    X, y = lp_design(df, h, endog, n_lags)
    Z = X.copy()
    Z["shock"] = df.loc[X.index, instr]
    Xn, Zn, yn = X.to_numpy(), Z.to_numpy(), y.to_numpy()
    b = np.linalg.solve(Zn.T @ Xn, Zn.T @ yn)
    u = yn - Xn @ b
    # HAC sandwich for IV: (Z'X)^-1 S_zu (X'Z)^-1
    Zu = Zn * u[:, None]
    S = Zu.T @ Zu
    for l in range(1, h + 2):
        G = Zu[l:].T @ Zu[:-l]
        S += (1 - l / (h + 2)) * (G + G.T)
    A = np.linalg.inv(Zn.T @ Xn)
    V = A @ S @ A.T
    j = list(X.columns).index("shock")
    return b[j], np.sqrt(V[j, j])


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    df, true_irf = make_data()
    irf = local_projection(df, Hmax=8)
    truth = np.array([true_irf(h) for h in irf.index])
    # point estimates close to the truth (large T), and most CIs cover it
    assert np.max(np.abs(irf.irf - truth)) < 0.15, (irf.irf - truth)
    cover = ((irf.lo <= truth) & (truth <= irf.hi)).mean()
    assert cover >= 0.75, cover
    # SEs grow with horizon (overlapping errors)
    assert irf.se.iloc[-1] > irf.se.iloc[0]
    # cross-check NW against statsmodels if available
    try:
        import statsmodels.api as sm
        X, y = lp_design(df, 4)
        res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5, "use_correction": True})
        b, *_ = np.linalg.lstsq(X.to_numpy(), y.to_numpy(), rcond=None)
        V = newey_west(X.to_numpy(), y.to_numpy() - X.to_numpy() @ b, L=5)
        assert np.allclose(res.bse.to_numpy(), np.sqrt(np.diag(V)), rtol=1e-8)
        sm_ok = True
    except ImportError:
        sm_ok = False
    # LP with a mismeasured shock is attenuated; LP-IV fixes it
    b_ols = local_projection(df, Hmax=0, shock="s_noisy").irf.iloc[0]
    b_iv, se_iv = lp_iv(df, 0)
    assert b_ols < 0.7 * true_irf(0)              # attenuation ~ 1/2
    assert abs(b_iv - true_irf(0)) < 3 * se_iv
    print("p4 OK  | statsmodels HAC match:", sm_ok, "| OLS(noisy)=%.2f  IV=%.2f (se %.2f)" % (b_ols, b_iv, se_iv))
    print(pd.concat([irf.round(3), pd.Series(truth.round(3), index=irf.index, name="true")], axis=1).to_string())


if __name__ == "__main__":
    _tests()
