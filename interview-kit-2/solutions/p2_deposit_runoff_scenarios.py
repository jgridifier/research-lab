"""
Problem 2 (core, ~13 min): two-segment deposit runoff simulation and a
scenario grid (a stock-flow compartmental model applied to deposits).

Balances: S = stable/core deposits, R = rate-sensitive deposits.
Each quarter h = 1..H the market rate is m_h = m0 + shock * min(h / ramp, 1)
and the bank pays d_h = beta * m_h, so the rate gap is g_h = max(m_h - d_h, 0).
Flows (fractions of the start-of-quarter balance, each capped at 1):
    S -> R  migration   : mu * g_h                 ("force of infection")
    S -> out organic    : s0
    R -> out runoff     : r0 + k * g_h
Tasks
  1. simulate(...) -> arrays S, R of length H + 1 (index 0 = today).
  2. trough_grid(shocks, betas): trough of total deposits as a share of
     today's total, for every (shock, beta). Vectorize (no Python loop over
     the grid) and check it against the loop version.
  3. breach_frontier: for each beta, the smallest shock whose trough falls
     below a limit (e.g. 85% of today = a 15% runoff limit), by bisection.
Only numpy required.
"""
import numpy as np

PARAMS = dict(S0=700.0, R0=300.0, m0=0.5, ramp=2, mu=0.01, s0=0.002, r0=0.005, k=0.025, H=8)


# ----------------------------------------------------------------------------
# Synthetic setup (parameters are illustrative, not calibrated to any bank)
# ----------------------------------------------------------------------------
def make_setup():
    shocks = np.linspace(0.0, 5.0, 21)      # pp of market-rate shock
    betas = np.linspace(0.0, 0.8, 9)        # deposit pass-through
    return dict(PARAMS), shocks, betas


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def rate_path(m0, shock, ramp, H):
    h = np.arange(1, H + 1)
    return m0 + np.multiply.outer(np.asarray(shock, float), np.minimum(h / ramp, 1.0))


def simulate(p: dict, shock: float, beta: float):
    """Loop version: one scenario. Returns (S, R) arrays of length H+1."""
    H = p["H"]
    S = np.empty(H + 1); R = np.empty(H + 1)
    S[0], R[0] = p["S0"], p["R0"]
    m = rate_path(p["m0"], shock, p["ramp"], H)
    for h in range(1, H + 1):
        g = max(m[h - 1] - beta * m[h - 1], 0.0)
        mig = min(p["mu"] * g, 1.0)
        out_s = min(p["s0"], 1.0 - mig)            # total S outflow fraction <= 1
        run_r = min(p["r0"] + p["k"] * g, 1.0)
        S[h] = S[h - 1] * (1 - mig - out_s)
        R[h] = R[h - 1] * (1 - run_r) + S[h - 1] * mig
    return S, R


def trough_loop(p, shocks, betas):
    out = np.empty((len(shocks), len(betas)))
    D0 = p["S0"] + p["R0"]
    for i, sh in enumerate(shocks):
        for j, b in enumerate(betas):
            S, R = simulate(p, sh, b)
            out[i, j] = (S + R).min() / D0
    return out


def trough_grid(p, shocks, betas):
    """Vectorized over the whole grid: arrays of shape (n_shock, n_beta)."""
    shocks = np.asarray(shocks, float); betas = np.asarray(betas, float)
    m = rate_path(p["m0"], shocks, p["ramp"], p["H"])          # (n_shock, H)
    g = np.maximum(m[:, None, :] * (1 - betas[None, :, None]), 0.0)  # (ns, nb, H)
    mig = np.minimum(p["mu"] * g, 1.0)
    out_s = np.minimum(p["s0"], 1.0 - mig)
    run_r = np.minimum(p["r0"] + p["k"] * g, 1.0)
    S = np.full(g.shape[:2], p["S0"]); R = np.full(g.shape[:2], p["R0"])
    trough = S + R
    for h in range(p["H"]):                    # loop over time only (8 steps)
        S, R = S * (1 - mig[..., h] - out_s[..., h]), R * (1 - run_r[..., h]) + S * mig[..., h]
        trough = np.minimum(trough, S + R)
    return trough / (p["S0"] + p["R0"])


def breach_frontier(p, betas, limit=0.85, lo=0.0, hi=20.0, tol=1e-6):
    """Smallest shock with trough <= limit, per beta (np.inf if none in [lo, hi])."""
    out = []
    for b in betas:
        f = lambda sh: trough_grid(p, [sh], [b])[0, 0] - limit
        if f(hi) > 0:
            out.append(np.inf); continue
        if f(lo) <= 0:
            out.append(lo); continue
        a, c = lo, hi
        while c - a > tol:
            mid = 0.5 * (a + c)
            a, c = (mid, c) if f(mid) > 0 else (a, mid)
        out.append(c)
    return np.array(out)


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    p, shocks, betas = make_setup()
    # 1. conservation: no flows out -> total constant; balances never negative
    q = dict(p, s0=0.0, r0=0.0, k=0.0)
    S, R = simulate(q, 3.0, 0.2)
    assert np.allclose(S + R, q["S0"] + q["R0"]) and R[-1] > q["R0"]
    S, R = simulate(dict(p, k=5.0), 5.0, 0.0)          # extreme runoff is capped
    assert (S >= 0).all() and (R >= 0).all()
    # 2. a hand-checked first quarter
    S, R = simulate(p, 2.0, 0.3)
    g1 = (0.5 + 2.0 * 0.5) * 0.7
    assert np.isclose(S[1], 700 * (1 - 0.01 * g1 - 0.002))
    assert np.isclose(R[1], 300 * (1 - 0.005 - 0.025 * g1) + 700 * 0.01 * g1)
    # 3. vectorized grid == loop
    tl, tg = trough_loop(p, shocks, betas), trough_grid(p, shocks, betas)
    assert tg.shape == (len(shocks), len(betas)) and np.allclose(tl, tg)
    # 4. monotone: bigger shock -> deeper trough; higher pass-through -> shallower
    assert (np.diff(tg, axis=0) <= 1e-12).all() and (np.diff(tg, axis=1) >= -1e-12).all()
    # 5. frontier hits the limit and rises with beta
    fr = breach_frontier(p, betas[:6])
    finite = np.isfinite(fr)
    assert finite.all() and (np.diff(fr) > 0).all()
    for b, sh in zip(betas[:6], fr):
        assert abs(trough_grid(p, [sh], [b])[0, 0] - 0.85) < 1e-5
    print("p2 OK  | grid", tg.shape, "| trough at (5pp, beta 0) = %.3f" % tg[-1, 0])
    print("trough share (rows: shock pp 0,1,..,5; cols: beta 0,0.2,..,0.8)")
    sel = tg[::4, ::2]
    print(np.array2string(sel, precision=3, suppress_small=True))
    print("breach frontier (shock pp for 15% runoff) by beta",
          dict(zip(np.round(betas[:6], 1).tolist(), np.round(fr, 2).tolist())))


if __name__ == "__main__":
    _tests()
