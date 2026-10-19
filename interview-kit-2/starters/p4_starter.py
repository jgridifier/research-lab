"""
How far is a stress scenario from history? Optimal transport. ~10 minutes.

hist, stress: (400, 2) arrays of quarterly (dUR, dY10) changes in pp.
1. wasserstein_1d(x, y, p=1): W_p between two equal-size 1-D samples.
2. ot_lp(a, b, C) -> (cost, plan): discrete OT between histograms a (n,)
   and b (m,) with cost matrix C (n, m), as a linear program with
   scipy.optimize.linprog. Check it against the 1-D answer.
3. sliced_wasserstein(X, Y, n_proj=500, seed=0): sliced W2 between 2-D
   samples, vectorized (no loop over projections).
"""
import numpy as np

try:
    from scipy.optimize import linprog
except ImportError:
    linprog = None


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def make_samples(n: int = 400, seed: int = 11):
    """Historical vs scenario-generator draws of (dUR pp, dY10 pp) per quarter."""
    rng = np.random.default_rng(seed)
    cov_h = np.array([[0.09, -0.03], [-0.03, 0.16]])
    hist = rng.multivariate_normal([0.0, 0.0], cov_h, size=n)
    # stress generator: UR drifts up, yields fall, fatter UR tail
    cov_s = np.array([[0.25, -0.08], [-0.08, 0.20]])
    stress = rng.multivariate_normal([0.6, -0.4], cov_s, size=n)
    return hist, stress



def wasserstein_1d(x, y, p: int = 1):
    raise NotImplementedError


def ot_lp(a, b, C):
    raise NotImplementedError


def sliced_wasserstein(X, Y, n_proj: int = 500, seed: int = 0):
    raise NotImplementedError


def check():
    hist, stress = make_samples()
    x = hist[:, 0]
    assert np.isclose(wasserstein_1d(x, x + 0.7), 0.7)
    print("W1 dUR hist vs stress:", round(wasserstein_1d(x, stress[:, 0]), 3))
    try:
        import scipy  # noqa: F401
        grid = np.array([0.0, 1.0, 2.0])
        cost, P = ot_lp(np.array([0.5, 0.5, 0.0]), np.array([0.0, 0.5, 0.5]),
                        np.abs(grid[:, None] - grid[None, :]))
        assert np.isclose(cost, 1.0) and np.allclose(P.sum(1), [0.5, 0.5, 0.0])
    except ImportError:
        print("scipy missing: skip the LP part")
    assert sliced_wasserstein(hist, hist) == 0.0
    sw = sliced_wasserstein(hist, hist + np.array([0.6, -0.4]), n_proj=4000)
    assert abs(sw ** 2 - 0.52 / 2) < 0.01, sw
    print("SW2 hist vs stress:", round(sliced_wasserstein(hist, stress), 3))
    print("checks passed")


if __name__ == "__main__":
    check()
