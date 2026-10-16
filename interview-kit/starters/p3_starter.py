"""
Conditional scenario forecast (CCAR-style). ~17 minutes. The main event.

hist: quarterly ur (unemployment %), y10 (10y yield %), g (deposit growth, % QoQ),
deposits (level). scenarios: {"baseline", "severely_adverse"} -> 9-quarter
DataFrames with imposed paths for ur and y10 (first row = first forecast quarter).

1. fit_arx(hist): OLS of  g_t = c + a g_{t-1} + b1 dUR_t + b2 dY10_t + e_t.
   Return (beta, residuals).
2. project(beta, hist, path): iterate g over the 9 quarters given the imposed
   paths (careful with the first difference at the jump-off quarter) and turn
   it into a deposit LEVEL path.
3. Run baseline and severely adverse; add 5%/95% bands (your choice of method).
4. Stress version: on top of severely adverse, add a deposit outflow of -3pp
   of growth in quarter 1, halving each quarter after.
"""
import numpy as np
import pandas as pd


H = 9


TRUE = dict(c=1.0, a=0.4, b1=-1.5, b2=0.8, sigma=0.4)


def make_history(T: int = 120, seed: int = 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ur = np.empty(T); y10 = np.empty(T); g = np.empty(T)
    ur[0], y10[0], g[0] = 5.0, 4.0, 1.5
    for t in range(1, T):
        ur[t] = 0.3 + 0.95 * ur[t - 1] + rng.normal(0, 0.25)
        y10[t] = 0.1 + 0.97 * y10[t - 1] + rng.normal(0, 0.25)
        g[t] = (TRUE["c"] + TRUE["a"] * g[t - 1] + TRUE["b1"] * (ur[t] - ur[t - 1])
                + TRUE["b2"] * (y10[t] - y10[t - 1]) + rng.normal(0, TRUE["sigma"]))
    idx = pd.period_range("1996Q1", periods=T, freq="Q")
    dep = 1000 * np.cumprod(1 + g / 100)
    return pd.DataFrame({"ur": ur, "y10": y10, "g": g, "deposits": dep}, index=idx)


def make_scenarios(last: pd.Series, start: pd.Period) -> dict:
    """Return {'baseline': df, 'severely_adverse': df} with UR and Y10 paths."""
    q = pd.period_range(start, periods=H, freq="Q")
    base = pd.DataFrame({"ur": np.linspace(last.ur, last.ur + 0.2, H),
                         "y10": np.linspace(last.y10, last.y10 - 0.1, H)}, index=q)
    # UR jumps ~5.5pp to a peak in quarter 6 then eases; Y10 falls ~2.5pp fast
    peak = last.ur + 5.5
    ur_sa = np.concatenate([np.linspace(last.ur, peak, 7)[1:], np.linspace(peak, peak - 1.0, 4)[1:]])
    y10_sa = np.maximum(last.y10 - 2.5 * (1 - np.exp(-0.8 * np.arange(1, H + 1))), 0.5)
    sa = pd.DataFrame({"ur": ur_sa, "y10": y10_sa}, index=q)
    return {"baseline": base, "severely_adverse": sa}


def fit_arx(hist: pd.DataFrame):
    raise NotImplementedError


def project(beta, hist: pd.DataFrame, path: pd.DataFrame):
    """Return a DataFrame indexed like path with columns g and deposits."""
    raise NotImplementedError


def check():
    hist = make_history()
    sc = make_scenarios(hist.iloc[-1], hist.index[-1] + 1)
    print(hist.tail(3)); print(sc["severely_adverse"].round(2))
    beta, resid = fit_arx(hist)
    print("beta", np.round(beta, 3))           # truth: c=1.0, a=0.4, b1=-1.5, b2=0.8
    base = project(beta, hist, sc["baseline"])
    sa = project(beta, hist, sc["severely_adverse"])
    assert len(sa) == H and (sa.deposits < base.deposits).all()
    print(pd.DataFrame({"base": base.deposits, "SA": sa.deposits}).round(1))
    print("checks passed")


if __name__ == "__main__":
    check()
