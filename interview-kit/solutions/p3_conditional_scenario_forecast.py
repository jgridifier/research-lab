"""
Problem 3 (main event, ~15-20 min): conditional scenario forecast.

Part A (core). Estimate an ARX for quarterly deposit growth g_t (%):
    g_t = c + a g_{t-1} + b1 dUR_t + b2 dY10_t + e_t
Impose a 9-quarter path for the unemployment rate (UR) and 10y yield (Y10)
(CCAR-style Baseline and Severely Adverse), iterate g forward, cumulate to a
deposit LEVEL path, and give 5/95% bands by residual bootstrap.
Part B (stress). Severely Adverse paths plus an idiosyncratic outflow overlay.
Part C (extension). VAR(1) in (UR, Y10, g) treating the paths as conditions on
endogenous variables: Waggoner-Zha / conditional-mean shocks via min-norm.

Scenario paths below are ILLUSTRATIVE, shaped like a Fed Severely Adverse path,
not the published numbers. Needs numpy + pandas only.
"""
import numpy as np
import pandas as pd

H = 9  # CCAR horizon in quarters


# ----------------------------------------------------------------------------
# Synthetic history and scenarios
# ----------------------------------------------------------------------------
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


# ----------------------------------------------------------------------------
# Part A: ARX estimated by OLS, path forecast with bootstrap bands
# ----------------------------------------------------------------------------
def fit_arx(hist: pd.DataFrame):
    d = pd.DataFrame({"g": hist.g, "g_l1": hist.g.shift(1),
                      "dur": hist.ur.diff(), "dy10": hist.y10.diff()}).dropna()
    X = np.column_stack([np.ones(len(d)), d.g_l1, d.dur, d.dy10])
    beta, *_ = np.linalg.lstsq(X, d.g.to_numpy(), rcond=None)
    resid = d.g.to_numpy() - X @ beta
    return beta, resid


def project(beta, hist: pd.DataFrame, path: pd.DataFrame, shocks=None,
            overlay=None) -> pd.DataFrame:
    """Iterate the ARX over the imposed path. shocks: (n_sims, H) residual
    draws, or None for the mean path. overlay: (H,) add-on to growth (pp)."""
    c, a, b1, b2 = beta
    dur = np.diff(np.r_[hist.ur.iloc[-1], path.ur.to_numpy()])     # first diff vs jump-off
    dy10 = np.diff(np.r_[hist.y10.iloc[-1], path.y10.to_numpy()])
    eps = np.zeros((1, H)) if shocks is None else shocks
    ov = np.zeros(H) if overlay is None else np.asarray(overlay)
    g = np.empty_like(eps)
    g_prev = np.full(eps.shape[0], hist.g.iloc[-1])
    for h in range(H):                                             # recursion in g
        g[:, h] = c + a * g_prev + b1 * dur[h] + b2 * dy10[h] + ov[h] + eps[:, h]
        g_prev = g[:, h]
    level = hist.deposits.iloc[-1] * np.cumprod(1 + g / 100, axis=1)
    return g, level


def scenario_forecast(hist, path, n_sims=4000, seed=0, overlay=None):
    beta, resid = fit_arx(hist)
    g_mean, lvl_mean = project(beta, hist, path, overlay=overlay)
    rng = np.random.default_rng(seed)
    draws = rng.choice(resid, size=(n_sims, H), replace=True)      # residual bootstrap
    _, lvl_sims = project(beta, hist, path, shocks=draws, overlay=overlay)
    out = pd.DataFrame({"g": g_mean[0], "deposits": lvl_mean[0],
                        "p05": np.percentile(lvl_sims, 5, axis=0),
                        "p95": np.percentile(lvl_sims, 95, axis=0)}, index=path.index)
    return out, beta


# ----------------------------------------------------------------------------
# Part C: VAR(1) conditional forecast (Waggoner-Zha, hard conditions)
# ----------------------------------------------------------------------------
def fit_var1(Y: np.ndarray):
    X = np.column_stack([np.ones(len(Y) - 1), Y[:-1]])
    B, *_ = np.linalg.lstsq(X, Y[1:], rcond=None)
    U = Y[1:] - X @ B
    Sigma = U.T @ U / (len(U) - X.shape[1])
    return B[0], B[1:].T, Sigma          # c, A (k x k), Sigma


def var_conditional(c, A, Sigma, y_T, cond_idx, cond_path):
    """Mean of y_{T+1..T+H} given y_T and y_{T+h}[cond_idx] = cond_path[h].
    Shocks eps ~ N(0, I) with u = P eps (Cholesky). Deviations from the
    unconditional forecast are linear in eps: dev = M eps. The conditional
    mean of eps given R eps = r is the min-norm solution R'(RR')^-1 r."""
    k = len(y_T); Hc = cond_path.shape[0]
    P = np.linalg.cholesky(Sigma)
    # unconditional path
    yhat = np.empty((Hc, k)); y = y_T.copy()
    for h in range(Hc):
        y = c + A @ y; yhat[h] = y
    # impulse matrix: block (h, j) = A^{h-j} P for j <= h
    M = np.zeros((Hc * k, Hc * k))
    Apow = [np.linalg.matrix_power(A, n) for n in range(Hc)]
    for h in range(Hc):
        for j in range(h + 1):
            M[h * k:(h + 1) * k, j * k:(j + 1) * k] = Apow[h - j] @ P
    rows = [h * k + i for h in range(Hc) for i in cond_idx]
    R = M[rows]
    r = (cond_path - yhat[:, cond_idx]).ravel()
    eps = R.T @ np.linalg.solve(R @ R.T, r)
    ycond = yhat + (M @ eps).reshape(Hc, k)
    # conditional covariance of the path (for bands)
    V = np.eye(Hc * k) - R.T @ np.linalg.solve(R @ R.T, R)
    cov = M @ V @ M.T
    return ycond, yhat, cov


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    hist = make_history()
    sc = make_scenarios(hist.iloc[-1], hist.index[-1] + 1)
    base, beta = scenario_forecast(hist, sc["baseline"])
    sa, _ = scenario_forecast(hist, sc["severely_adverse"])
    # parameters recovered roughly
    assert np.allclose(beta, [TRUE[k] for k in ("c", "a", "b1", "b2")], atol=0.35), beta
    # rising UR lowers deposits: SA below baseline at every horizon
    assert (sa.deposits < base.deposits).all()
    # bands bracket the mean path and widen with horizon
    assert ((base.p05 < base.deposits) & (base.deposits < base.p95)).all()
    width = base.p95 - base.p05
    assert width.iloc[-1] > width.iloc[0]
    # the mean path is the deterministic recursion: check quarter 1 by hand
    c, a, b1, b2 = beta
    g1 = c + a * hist.g.iloc[-1] + b1 * (sc["baseline"].ur.iloc[0] - hist.ur.iloc[-1]) \
        + b2 * (sc["baseline"].y10.iloc[0] - hist.y10.iloc[-1])
    assert np.isclose(base.g.iloc[0], g1)
    # Part B stress: SA + outflow overlay of -3pp in Q1 decaying by half each quarter
    overlay = -3.0 * 0.5 ** np.arange(H)
    stress, _ = scenario_forecast(hist, sc["severely_adverse"], overlay=overlay)
    assert (stress.deposits < sa.deposits).all()
    # Part C: VAR conditional forecast hits the imposed paths exactly
    Y = hist[["ur", "y10", "g"]].to_numpy()
    cV, AV, SV = fit_var1(Y)
    cond = sc["severely_adverse"][["ur", "y10"]].to_numpy()
    ycond, yhat, cov = var_conditional(cV, AV, SV, Y[-1], [0, 1], cond)
    assert np.allclose(ycond[:, :2], cond, atol=1e-8)
    var_diag = np.diag(cov)
    assert np.allclose(var_diag[0::3], 0, atol=1e-8)   # conditioned vars: no uncertainty
    assert np.all(var_diag[2::3] > 0)                  # deposits still uncertain
    # SA path pushes VAR deposit growth below its unconditional forecast (on average)
    assert ycond[:, 2].mean() < yhat[:, 2].mean()
    print("p3 OK  | beta =", np.round(beta, 3))
    show = pd.DataFrame({"UR_SA": sc["severely_adverse"].ur.round(2),
                         "base": base.deposits.round(1), "SA": sa.deposits.round(1),
                         "SA_p05": sa.p05.round(1), "SA_p95": sa.p95.round(1),
                         "stress": stress.deposits.round(1),
                         "VAR_g_SA": np.round(ycond[:, 2], 2)})
    print(show.to_string())


if __name__ == "__main__":
    _tests()
