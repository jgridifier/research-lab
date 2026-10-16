"""
Challenger vs naive: expanding-window backtest with no look-ahead. ~13 minutes.

df: quarterly, columns y (deposit growth, %) and x (change in unemployment, pp).
Challenger ARX(1):   y_{t+1} = c + phi * y_t + beta * x_t + e
Benchmarks:          random walk (forecast y_{t+1} = y_t), historical mean.

1. backtest(df, first_origin=60, h=1): for each origin t >= first_origin,
   fit the ARX using ONLY data dated <= t, forecast y_{t+1}, store
   actual / arx / rw / mean. Return a DataFrame indexed by target date.
2. Report RMSE and MAE for each model.
3. diebold_mariano(e1, e2, h): DM statistic and p-value (squared-error loss).
Use numpy for OLS if you like; statsmodels is available.
"""
import numpy as np
import pandas as pd


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


def backtest(df: pd.DataFrame, first_origin: int = 60, h: int = 1) -> pd.DataFrame:
    raise NotImplementedError


def diebold_mariano(e1, e2, h: int = 1):
    """Return (stat, p_value). Negative stat => model 1 more accurate."""
    raise NotImplementedError


def check():
    df = make_data()
    bt = backtest(df, first_origin=60, h=1)
    assert {"actual", "arx", "rw", "mean"} <= set(bt.columns)
    # look-ahead guard: overwrite the future; forecasts made before it must not move
    df_bad = df.copy(); df_bad.iloc[81:] = 999.0
    bt_bad = backtest(df_bad.iloc[:82], first_origin=60, h=1)
    assert np.allclose(bt_bad.arx.to_numpy(), bt.arx.iloc[:len(bt_bad)].to_numpy()), "look-ahead!"
    rmse = {m: np.sqrt(((bt.actual - bt[m]) ** 2).mean()) for m in ["arx", "rw", "mean"]}
    print(rmse)
    print(diebold_mariano(bt.actual - bt.arx, bt.actual - bt.rw, h=1))
    print("checks passed")


if __name__ == "__main__":
    check()
