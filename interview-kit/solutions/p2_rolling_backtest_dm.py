"""
Problem 2 (core, ~12-15 min): expanding-window (rolling-origin) backtest of an
ARX challenger vs naive benchmarks, with RMSE/MAE and a Diebold-Mariano test.
No look-ahead: at origin t the model only sees data dated <= t.

y_t : quarterly deposit growth (%), x_t : change in the unemployment rate (pp)
Challenger: y_{t+h} = c + sum_j phi_j y_{t+1-j} + beta x_t + e   (direct h-step)
Benchmarks: random walk (y_t) and historical mean (mean of y_1..y_t)

Needs numpy + scipy (for the t/normal CDF). statsmodels used only for a cross-check.
"""
import numpy as np
import pandas as pd

try:
    from scipy import stats
except ImportError:          # fallback: normal CDF via math.erf
    stats = None
import math


# ----------------------------------------------------------------------------
# Synthetic data
# ----------------------------------------------------------------------------
def make_data(T: int = 160, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x = np.zeros(T)
    y = np.zeros(T)
    for t in range(1, T):
        x[t] = 0.5 * x[t - 1] + rng.normal(0, 0.3)
        # unemployment rising today lowers deposit growth next quarter
        y[t] = 0.4 + 0.5 * y[t - 1] - 1.2 * x[t - 1] + rng.normal(0, 0.5)
    idx = pd.period_range("1985Q1", periods=T, freq="Q")
    return pd.DataFrame({"y": y, "x": x}, index=idx)


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """OLS coefficients via least squares (numerically safer than inv(X'X))."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def design(df: pd.DataFrame, p: int, h: int, use_x: bool = True):
    """Rows t with regressors dated <= t and target y_{t+h}.
    Returns (X, target, X_last) where X_last is the regressor row at the last
    date (used for the forecast, its target is unknown)."""
    cols = {"const": np.ones(len(df))}
    for j in range(p):
        cols[f"y_l{j}"] = df["y"].shift(j).to_numpy()
    if use_x:
        cols["x_l0"] = df["x"].to_numpy()
    Z = pd.DataFrame(cols, index=df.index)
    target = df["y"].shift(-h)
    ok = Z.notna().all(axis=1) & target.notna()
    return Z[ok].to_numpy(), target[ok].to_numpy(), Z.iloc[-1].to_numpy()


def forecast_at_origin(hist: pd.DataFrame, p: int, h: int, use_x=True) -> float:
    """hist contains ONLY data up to the forecast origin. Fit and forecast."""
    X, yt, x_last = design(hist, p, h, use_x)
    b = ols(X, yt)
    return float(x_last @ b)


def backtest(df: pd.DataFrame, first_origin: int, h: int = 1, p: int = 1):
    """Expanding window. Origin t uses df.iloc[:t+1]; target is y at t+h."""
    recs = []
    for t in range(first_origin, len(df) - h):
        hist = df.iloc[: t + 1]                      # <- the no-look-ahead line
        recs.append(dict(origin=df.index[t], target_date=df.index[t + h],
                         actual=df["y"].iloc[t + h],
                         arx=forecast_at_origin(hist, p, h, True),
                         ar=forecast_at_origin(hist, p, h, False),
                         rw=hist["y"].iloc[-1],
                         mean=hist["y"].mean()))
    return pd.DataFrame(recs).set_index("target_date")


def error_table(bt: pd.DataFrame, models=("arx", "ar", "rw", "mean")) -> pd.DataFrame:
    out = {}
    for m in models:
        e = bt["actual"] - bt[m]
        out[m] = {"RMSE": np.sqrt(np.mean(e ** 2)), "MAE": np.mean(np.abs(e))}
    return pd.DataFrame(out).T


def _norm_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def diebold_mariano(e1, e2, h: int = 1, loss: str = "se", hln: bool = True):
    """DM test of equal predictive accuracy. d_t = L(e1_t) - L(e2_t).
    Negative stat => model 1 more accurate. Long-run variance uses
    autocovariances up to lag h-1 (rectangular, as in DM 1995), with
    a Bartlett fallback if that is non-positive. HLN (1997) small-sample
    correction and t_{n-1} reference distribution when hln=True."""
    e1, e2 = np.asarray(e1), np.asarray(e2)
    d = e1 ** 2 - e2 ** 2 if loss == "se" else np.abs(e1) - np.abs(e2)
    n = len(d)
    dbar = d.mean()
    dc = d - dbar
    gam = [dc @ dc / n] + [dc[k:] @ dc[:-k] / n for k in range(1, h)]
    lrv = gam[0] + 2 * sum(gam[1:])
    if lrv <= 0:  # Bartlett weights guarantee positivity
        lrv = gam[0] + 2 * sum((1 - k / h) * gam[k] for k in range(1, h))
    stat = dbar / math.sqrt(lrv / n)
    if hln:
        stat *= math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
        p = 2 * (1 - stats.t.cdf(abs(stat), df=n - 1)) if stats else 2 * (1 - _norm_cdf(abs(stat)))
    else:
        p = 2 * (1 - _norm_cdf(abs(stat)))
    return stat, p


def clark_west(actual, f_small, f_big):
    """Clark-West (2007) for nested models: big model nests small one.
    One-sided: H1 big model better. Adjusts for the noise from estimating
    parameters that are zero under the null."""
    actual, f_small, f_big = map(np.asarray, (actual, f_small, f_big))
    f = (actual - f_small) ** 2 - ((actual - f_big) ** 2 - (f_small - f_big) ** 2)
    n = len(f)
    stat = f.mean() / (f.std(ddof=1) / math.sqrt(n))
    p = 1 - (stats.norm.cdf(stat) if stats else _norm_cdf(stat))
    return stat, p


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    df = make_data()
    bt = backtest(df, first_origin=60, h=1, p=1)
    tab = error_table(bt)
    # 1. look-ahead guard: scrambling the future must not change any forecast
    t0 = 80
    f_true = forecast_at_origin(df.iloc[: t0 + 1], 1, 1)
    df_bad = df.copy()
    df_bad.iloc[t0 + 1:] = 999.0
    f_bad = forecast_at_origin(df_bad.iloc[: t0 + 1], 1, 1)
    assert f_true == f_bad
    bt_bad = backtest(df_bad.iloc[: t0 + 2], first_origin=60)  # last target = t0+1
    assert np.allclose(bt_bad["arx"].to_numpy(), bt["arx"].iloc[: len(bt_bad)].to_numpy())
    # 2. the true DGP is ARX, so the challenger should win on RMSE
    assert tab.loc["arx", "RMSE"] < tab.loc["rw", "RMSE"]
    assert tab.loc["arx", "RMSE"] < tab.loc["mean", "RMSE"]
    e = {m: bt["actual"] - bt[m] for m in ["arx", "ar", "rw", "mean"]}
    dm_rw = diebold_mariano(e["arx"], e["rw"], h=1)
    assert dm_rw[0] < 0 and dm_rw[1] < 0.05, dm_rw
    # 3. DM is antisymmetric in the two models
    s1, _ = diebold_mariano(e["arx"], e["rw"], h=2)
    s2, _ = diebold_mariano(e["rw"], e["arx"], h=2)
    assert np.isclose(s1, -s2)
    # 4. OLS cross-check vs statsmodels if available
    X, yt, _ = design(df, 2, 1)
    try:
        import statsmodels.api as sm
        assert np.allclose(sm.OLS(yt, X).fit().params, ols(X, yt))
        sm_ok = True
    except ImportError:
        sm_ok = False
    # 5. Clark-West: ARX nests AR(1); should reject in favour of ARX
    cw = clark_west(bt["actual"], bt["ar"], bt["arx"])
    assert cw[0] > 0 and cw[1] < 0.05, cw
    # 6. h = 4 direct forecasts also run and line up
    bt4 = backtest(df, first_origin=60, h=4)
    assert (bt4["origin"].apply(lambda p: p + 4) == bt4.index).all()
    print("p2 OK  | n_oos =", len(bt), "| statsmodels cross-check:", sm_ok)
    print(tab.round(3).to_string())
    print("DM arx vs rw: stat=%.2f p=%.4f | CW arx vs ar: stat=%.2f p=%.4f" % (*dm_rw, *cw))


if __name__ == "__main__":
    _tests()
