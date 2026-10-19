"""
Deposit runoff scenarios: a two-segment compartmental model. ~13 minutes.

S = stable deposits, R = rate-sensitive deposits (start: S0, R0 in PARAMS).
Quarter h = 1..H: market rate m_h = m0 + shock * min(h / ramp, 1)
(rate_path gives you this), the bank pays beta * m_h, so the gap is
g_h = max(m_h - beta * m_h, 0). Fractions of start-of-quarter balances:
    S -> R migration : mu * g_h      S -> out : s0      R -> out : r0 + k * g_h
(cap each flow so no balance goes negative).

1. simulate(p, shock, beta) -> (S, R), numpy arrays of length H + 1.
2. trough_grid(p, shocks, betas) -> array (len(shocks), len(betas)) of
   min_h (S_h + R_h) / (S0 + R0). No Python loop over the grid
   (looping over the 8 quarters is fine).
3. If time: for each beta, the smallest shock whose trough is <= 0.85.
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


def rate_path(m0, shock, ramp, H):
    h = np.arange(1, H + 1)
    return m0 + np.multiply.outer(np.asarray(shock, float), np.minimum(h / ramp, 1.0))



def simulate(p: dict, shock: float, beta: float):
    raise NotImplementedError


def trough_grid(p, shocks, betas):
    raise NotImplementedError


def check():
    p, shocks, betas = make_setup()
    S, R = simulate(p, 2.0, 0.3)
    assert len(S) == p["H"] + 1 and S[0] == p["S0"] and R[0] == p["R0"]
    g1 = (0.5 + 2.0 * 0.5) * 0.7
    assert np.isclose(S[1], 700 * (1 - 0.01 * g1 - 0.002)), S[1]
    assert np.isclose(R[1], 300 * (1 - 0.005 - 0.025 * g1) + 700 * 0.01 * g1), R[1]
    q = dict(p, s0=0.0, r0=0.0, k=0.0)
    S, R = simulate(q, 3.0, 0.2)
    assert np.allclose(S + R, 1000.0), "with no outflows total deposits are conserved"
    tg = trough_grid(p, shocks, betas)
    assert tg.shape == (len(shocks), len(betas))
    S, R = simulate(p, shocks[8], betas[3])
    assert np.isclose(tg[8, 3], (S + R).min() / 1000.0), "grid must match simulate()"
    assert (np.diff(tg, axis=0) <= 1e-12).all(), "bigger shock should not help"
    print(np.round(tg[::4, ::2], 3))
    print("checks passed")


if __name__ == "__main__":
    check()
