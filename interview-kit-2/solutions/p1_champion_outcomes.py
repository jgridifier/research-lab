"""
Problem 1 (core, ~11 min): outcomes analysis of a "champion" forecast.

A business line hands you its champion deposit-growth model and the backtest
that "proves" it works. As the independent reviewer you must:
  1. Write a generic leak test: perturb every observation after origin k and
     check that no forecast made at an origin <= k moves.
  2. Find the leak in champion_backtest (it uses the realized x_{t+1}: an
     oracle regressor) and write a leak-free backtest of the same spec.
  3. Benchmark against a random walk and the historical mean (RMSE/MAE) and
     run a Diebold-Mariano test (HLN-corrected) vs the random walk.

DGP: x_t = 0.6 x_{t-1} + eta_t (change in unemployment, pp)
     y_t = 0.5 + 0.4 y_{t-1} - 1.5 x_t - 0.6 x_{t-1} + e_t (deposit growth, %)
Only numpy + pandas required; scipy (t CDF) and statsmodels (OLS
cross-check) are used when available.
"""
import math
import numpy as np
import pandas as pd

try:
    from scipy import stats
except ImportError:          # numpy-only fallback: normal CDF via math.erf
    stats = None


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def make_data(T: int = 140, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x = np.zeros(T)
    y = np.zeros(T)
    for t in range(1, T):
        x[t] = 0.6 * x[t - 1] + rng.normal(0, 0.35)
        y[t] = 0.5 + 0.4 * y[t - 1] - 1.5 * x[t] - 0.6 * x[t - 1] + rng.normal(0, 0.4)
    idx = pd.period_range("1991Q1", periods=T, freq="Q")
    return pd.DataFrame({"y": y, "x": x}, index=idx)


# ----------------------------------------------------------------------------
# The champion's backtest, as handed over (contains a leak; do not "fix" here)
# ----------------------------------------------------------------------------
def champion_backtest(df: pd.DataFrame, first_origin: int = 60) -> pd.DataFrame:
    """Champion spec: y_{t+1} = c + a*y_t + b*x_{t+1} + d*x_t.
    Re-fits at every origin (looks careful) but plugs in the REALIZED x_{t+1}."""
    xs = (df["x"] - df["x"].mean()) / df["x"].std()   # full-sample z-score (harmless: affine)
    recs = []
    for t in range(first_origin, len(df) - 1):
        yy = df["y"].iloc[1:t + 1].to_numpy()
        X = np.column_stack([np.ones(t), df["y"].iloc[:t].to_numpy(),
                             xs.iloc[1:t + 1].to_numpy(), xs.iloc[:t].to_numpy()])
        b = np.linalg.lstsq(X, yy, rcond=None)[0]
        xrow = np.array([1.0, df["y"].iloc[t], xs.iloc[t + 1], xs.iloc[t]])   # <- x_{t+1}: oracle
        recs.append(dict(origin=t, target=df.index[t + 1], actual=df["y"].iloc[t + 1],
                         forecast=float(xrow @ b)))
    return pd.DataFrame(recs).set_index("target")


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def leak_test(backtest_fn, df: pd.DataFrame, k: int, junk: float = 1e3) -> bool:
    """True if a leak is detected: some forecast with origin <= k changes when
    every observation dated after k is overwritten."""
    base = backtest_fn(df)
    bad = df.copy()
    bad.iloc[k + 1:] = junk
    pert = backtest_fn(bad)
    keep = base["origin"] <= k
    a = base.loc[keep, "forecast"].to_numpy()
    b = pert.loc[pert["origin"] <= k, "forecast"].to_numpy()
    return not (len(a) == len(b) and np.allclose(a, b, rtol=0, atol=1e-10))


def ols(X, y):
    return np.linalg.lstsq(X, y, rcond=None)[0]


def fixed_backtest(df: pd.DataFrame, first_origin: int = 60) -> pd.DataFrame:
    """Same champion spec, but x_{t+1} is replaced by its own AR(1) forecast
    fitted on data <= t. Also returns the two naive benchmarks."""
    recs = []
    for t in range(first_origin, len(df) - 1):
        hist = df.iloc[: t + 1]                       # <- the no-look-ahead line
        y, x = hist["y"].to_numpy(), hist["x"].to_numpy()
        # 1) forecast x_{t+1} with an AR(1) on x (data <= t only)
        ax = ols(np.column_stack([np.ones(t), x[:-1]]), x[1:])
        x_next = ax[0] + ax[1] * x[-1]
        # 2) champion regression on rows s = 1..t: y_s on (1, y_{s-1}, x_s, x_{s-1})
        X = np.column_stack([np.ones(t), y[:-1], x[1:], x[:-1]])
        b = ols(X, y[1:])
        f = float(np.array([1.0, y[-1], x_next, x[-1]]) @ b)
        recs.append(dict(origin=t, target=df.index[t + 1], actual=df["y"].iloc[t + 1],
                         forecast=f, rw=y[-1], mean=y.mean()))
    return pd.DataFrame(recs).set_index("target")


def error_table(bt: pd.DataFrame, cols=("forecast", "rw", "mean")) -> pd.DataFrame:
    out = {}
    for c in cols:
        e = bt["actual"] - bt[c]
        out[c] = {"RMSE": float(np.sqrt(np.mean(e ** 2))), "MAE": float(np.mean(np.abs(e)))}
    return pd.DataFrame(out).T


def _norm_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def diebold_mariano(e1, e2, h: int = 1):
    """DM with squared-error loss, rectangular LRV to lag h-1, HLN correction.
    Negative stat => model 1 more accurate. Returns (stat, two-sided p)."""
    e1, e2 = np.asarray(e1, float), np.asarray(e2, float)
    d = e1 ** 2 - e2 ** 2
    n = len(d)
    dc = d - d.mean()
    gam = [dc @ dc / n] + [dc[k:] @ dc[:-k] / n for k in range(1, h)]
    lrv = gam[0] + 2 * sum(gam[1:])
    if lrv <= 0:
        lrv = gam[0] + 2 * sum((1 - k / h) * gam[k] for k in range(1, h))
    stat = d.mean() / math.sqrt(lrv / n)
    stat *= math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    p = 2 * (1 - stats.t.cdf(abs(stat), df=n - 1)) if stats else 2 * (1 - _norm_cdf(abs(stat)))
    return float(stat), float(p)


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    df = make_data()
    champ = champion_backtest(df)
    fixed = fixed_backtest(df)
    # 1. the leak test flags the champion and clears the fixed version
    assert leak_test(champion_backtest, df, k=90), "champion should leak"
    assert not leak_test(fixed_backtest, df, k=90), "fixed version must not leak"
    # 2. the leak flatters the champion: oracle RMSE is far below the honest one
    rm_champ = float(np.sqrt(np.mean((champ.actual - champ.forecast) ** 2)))
    tab = error_table(fixed)
    assert rm_champ < 0.75 * tab.loc["forecast", "RMSE"], (rm_champ, tab)
    # 3. the honest model still beats both naive benchmarks
    assert tab.loc["forecast", "RMSE"] < tab.loc["rw", "RMSE"]
    assert tab.loc["forecast", "RMSE"] < tab.loc["mean", "RMSE"]
    dm = diebold_mariano(fixed.actual - fixed.forecast, fixed.actual - fixed.rw)
    assert dm[0] < 0 and dm[1] < 0.05, dm
    # 4. DM is antisymmetric
    assert np.isclose(dm[0], -diebold_mariano(fixed.actual - fixed.rw, fixed.actual - fixed.forecast)[0])
    # 5. the full-sample z-score alone is NOT a leak (OLS with intercept is affine-invariant)
    #    (the AR(1) forecast of x is affine-equivariant too, so y forecasts are unchanged)
    d2 = df.copy()
    d2["x"] = (df["x"] - df["x"].mean()) / df["x"].std()
    a = fixed_backtest(df)["forecast"].to_numpy()
    b = fixed_backtest(d2)["forecast"].to_numpy()
    assert np.allclose(a, b, atol=1e-8), "affine rescaling of x should not change forecasts"
    # 5b. a champion variant that keeps the full-sample z-score but drops x_{t+1}
    #     passes the leak test: the z-score is not a material leak for OLS
    def champion_lagged_only(d):
        xs = (d["x"] - d["x"].mean()) / d["x"].std()
        recs = []
        for t in range(60, len(d) - 1):
            X = np.column_stack([np.ones(t), d["y"].iloc[:t].to_numpy(), xs.iloc[:t].to_numpy()])
            b = ols(X, d["y"].iloc[1:t + 1].to_numpy())
            f = float(np.array([1.0, d["y"].iloc[t], xs.iloc[t]]) @ b)
            recs.append(dict(origin=t, target=d.index[t + 1], forecast=f))
        return pd.DataFrame(recs).set_index("target")
    assert not leak_test(champion_lagged_only, df, k=90, junk=5.0)
    # 6. statsmodels cross-check of the regression, if installed
    try:
        import statsmodels.api as sm
        y, x = df.y.to_numpy(), df.x.to_numpy()
        X = np.column_stack([np.ones(len(y) - 1), y[:-1], x[1:], x[:-1]])
        assert np.allclose(sm.OLS(y[1:], X).fit().params, ols(X, y[1:]))
        sm_ok = True
    except ImportError:
        sm_ok = False
    print("p1 OK  | n_oos =", len(fixed), "| statsmodels cross-check:", sm_ok)
    print("champion (oracle x) RMSE = %.3f" % rm_champ)
    print(tab.round(3).to_string())
    print("DM fixed vs rw: stat=%.2f p=%.4f" % dm)


if __name__ == "__main__":
    _tests()
