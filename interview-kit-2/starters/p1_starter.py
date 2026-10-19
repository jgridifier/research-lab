"""
Outcomes analysis of a champion forecast. ~11 minutes.

df: quarterly, y = deposit growth (%), x = change in unemployment (pp).
champion_backtest(df) is the business line's backtest of its champion model
    y_{t+1} = c + a*y_t + b*x_{t+1} + d*x_t
It re-fits at every origin and reports a very good RMSE. You are the reviewer.

1. leak_test(backtest_fn, df, k): overwrite every row after position k with
   junk, re-run backtest_fn, and return True if ANY forecast whose origin is
   <= k changed. Run it on champion_backtest. What leaks, and is the
   full-sample z-score also a problem?
2. fixed_backtest(df, first_origin=60): same spec, leak-free. Return a
   DataFrame indexed by target date with columns origin, actual, forecast,
   rw (random walk: y_t) and mean (historical mean of y up to t).
3. RMSE/MAE for forecast, rw, mean; then diebold_mariano(e1, e2) -> (stat, p).
numpy/pandas are enough; scipy and statsmodels are available.
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



def leak_test(backtest_fn, df: pd.DataFrame, k: int, junk: float = 1e3) -> bool:
    raise NotImplementedError


def fixed_backtest(df: pd.DataFrame, first_origin: int = 60) -> pd.DataFrame:
    raise NotImplementedError


def diebold_mariano(e1, e2, h: int = 1):
    """Return (stat, p_value). Negative stat => model 1 more accurate."""
    raise NotImplementedError


def check():
    df = make_data()
    champ = champion_backtest(df)
    print(champ.head(3))
    assert leak_test(champion_backtest, df, k=90), "the champion should fail the leak test"
    bt = fixed_backtest(df)
    assert {"origin", "actual", "forecast", "rw", "mean"} <= set(bt.columns)
    assert not leak_test(fixed_backtest, df, k=90), "your backtest leaks"
    rmse = {c: float(np.sqrt(((bt.actual - bt[c]) ** 2).mean())) for c in ["forecast", "rw", "mean"]}
    print("champion RMSE", round(float(np.sqrt(((champ.actual - champ.forecast) ** 2).mean())), 3), "| honest", rmse)
    assert rmse["forecast"] < rmse["rw"] < rmse["mean"]
    stat, p = diebold_mariano(bt.actual - bt.forecast, bt.actual - bt.rw)
    print("DM", round(stat, 2), round(p, 4))
    assert stat < 0
    print("checks passed")


if __name__ == "__main__":
    check()
