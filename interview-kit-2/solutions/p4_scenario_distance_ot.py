"""
Problem 4 (swap-in, ~10 min): how far is a stress scenario from history?
Optimal transport three ways.

  1. wasserstein_1d(x, y): W_p between two equal-size 1-D samples (sorted
     samples = quantile coupling).
  2. ot_lp(a, b, C): discrete OT between histograms a, b with cost matrix C,
     solved as a linear program with scipy.optimize.linprog. Return the cost
     and the transport plan; check it against the 1-D closed form.
  3. sliced_wasserstein(X, Y, n_proj): vectorized sliced W2 between 2-D
     samples (e.g. joint quarterly changes in unemployment and the 10y yield).
Application: compare the joint (dUR, dY10) distribution implied by a
scenario generator with the historical one.
numpy required; scipy needed only for part 2 (skipped otherwise).
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


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def wasserstein_1d(x, y, p: int = 1):
    x, y = np.sort(np.asarray(x, float)), np.sort(np.asarray(y, float))
    assert len(x) == len(y), "equal sizes for the sorted-sample formula"
    return float(np.mean(np.abs(x - y) ** p) ** (1 / p))


def wasserstein_1d_hist(a, b, grid):
    """W1 between histograms on a common sorted grid: integral of |F_a - F_b|."""
    Fa, Fb = np.cumsum(a), np.cumsum(b)
    return float(np.sum(np.abs(Fa - Fb)[:-1] * np.diff(grid)))


def ot_lp(a, b, C):
    """min <C, P>  s.t.  P 1 = a,  P' 1 = b,  P >= 0.   Variables: vec(P) row-major."""
    n, m = C.shape
    A_eq = np.zeros((n + m, n * m))
    for i in range(n):
        A_eq[i, i * m:(i + 1) * m] = 1.0          # row sums
    for j in range(m):
        A_eq[n + j, j::m] = 1.0                   # column sums
    res = linprog(C.ravel(), A_eq=A_eq, b_eq=np.r_[a, b], bounds=(0, None), method="highs")
    assert res.status == 0, res.message
    return float(res.fun), res.x.reshape(n, m)


def sliced_wasserstein(X, Y, n_proj: int = 500, seed: int = 0):
    """SW2: average over random unit directions of W2^2 of the 1-D projections."""
    rng = np.random.default_rng(seed)
    theta = rng.standard_normal((n_proj, X.shape[1]))
    theta /= np.linalg.norm(theta, axis=1, keepdims=True)
    px = np.sort(X @ theta.T, axis=0)             # (n, n_proj), sorted per direction
    py = np.sort(Y @ theta.T, axis=0)
    return float(np.sqrt(np.mean((px - py) ** 2)))


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    hist, stress = make_samples()
    # 1. 1-D: W is a metric-like quantity; a pure shift moves W1 by exactly the shift
    x = hist[:, 0]
    assert wasserstein_1d(x, x) == 0.0
    assert np.isclose(wasserstein_1d(x, x + 0.7), 0.7)
    assert np.isclose(wasserstein_1d(x, stress[:, 0]), wasserstein_1d(stress[:, 0], x))
    # 2. LP agrees with the 1-D CDF formula on a histogram grid
    lp_ok = linprog is not None
    if lp_ok:
        grid = np.linspace(-2, 3, 26)
        bins = np.r_[grid - 0.1, grid[-1] + 0.1]
        a = np.histogram(np.clip(hist[:, 0], -2, 3), bins=bins)[0].astype(float); a /= a.sum()
        b = np.histogram(np.clip(stress[:, 0], -2, 3), bins=bins)[0].astype(float); b /= b.sum()
        C = np.abs(grid[:, None] - grid[None, :])
        cost, P = ot_lp(a, b, C)
        assert np.allclose(P.sum(1), a, atol=1e-9) and np.allclose(P.sum(0), b, atol=1e-9)
        assert np.isclose(cost, wasserstein_1d_hist(a, b, grid), atol=1e-8)
    # 3. sliced W2: zero on identical samples; a shift a gives SW2^2 ~ |a|^2 / d
    assert sliced_wasserstein(hist, hist) == 0.0
    shift = np.array([0.6, -0.4])
    sw_shift = sliced_wasserstein(hist, hist + shift, n_proj=4000)
    assert abs(sw_shift ** 2 - shift @ shift / 2) < 0.01, sw_shift
    sw_stress = sliced_wasserstein(hist, stress)
    sw_null = sliced_wasserstein(hist[:200], hist[200:])       # sampling noise level
    assert sw_stress > 4 * sw_null
    print("p4 OK  | W1(dUR hist, stress) = %.3f | LP check: %s | SW2 stress %.3f vs noise %.3f"
          % (wasserstein_1d(x, stress[:, 0]), lp_ok, sw_stress, sw_null))


if __name__ == "__main__":
    _tests()
