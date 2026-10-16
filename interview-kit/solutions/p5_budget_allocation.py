"""
Problem 5 (swap-in, ~12 min): allocate a budget B across n business lines.

    max_x  sum_i a_i (1 - exp(-b_i x_i))   s.t.  sum_i x_i = B,  0 <= x_i <= u_i

Concave, separable. KKT: a_i b_i exp(-b_i x_i) = lam for interior x_i, so
    x_i(lam) = clip( ln(a_i b_i / lam) / b_i , 0, u_i ),
and sum_i x_i(lam) is decreasing in lam -> bisection on lam.
Cross-checks: scipy.optimize.minimize (SLSQP), a piecewise-linear LP with
scipy.optimize.linprog (dual of the budget row ~ lam), and an extension MILP
with "minimum spend if funded" (scipy.optimize.milp).
"""
import numpy as np

try:
    from scipy.optimize import minimize, linprog
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False
try:                                    # milp needs scipy >= 1.9
    from scipy.optimize import milp, LinearConstraint, Bounds
    HAVE_MILP = True
except ImportError:
    HAVE_MILP = False


# ----------------------------------------------------------------------------
# Synthetic problem
# ----------------------------------------------------------------------------
def make_problem(n: int = 8, seed: int = 4):
    rng = np.random.default_rng(seed)
    a = rng.uniform(5, 20, n)        # saturation level of each line's payoff
    b = rng.uniform(0.05, 0.4, n)    # how fast payoff saturates
    u = rng.uniform(8, 25, n)        # caps
    B = 0.45 * u.sum()
    return a, b, u, B


def objective(x, a, b):
    return np.sum(a * (1 - np.exp(-b * x)))


# ----------------------------------------------------------------------------
# Reference solution 1: bisection on the multiplier
# ----------------------------------------------------------------------------
def x_of_lam(lam, a, b, u):
    return np.clip(np.log(a * b / lam) / b, 0.0, u)


def allocate_bisection(a, b, u, B, tol=1e-12, max_iter=200):
    if B >= u.sum():
        return u.copy(), 0.0                     # budget not binding
    lo, hi = 1e-12, np.max(a * b)                # at lam = max(a b) every x_i = 0
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        if x_of_lam(mid, a, b, u).sum() > B:     # spending too much -> raise price
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    lam = 0.5 * (lo + hi)
    return x_of_lam(lam, a, b, u), lam


# ----------------------------------------------------------------------------
# Reference solution 2: general NLP solver
# ----------------------------------------------------------------------------
def allocate_slsqp(a, b, u, B):
    x0 = np.full(len(a), B / len(a))
    res = minimize(lambda x: -objective(x, a, b), x0,
                   jac=lambda x: -(a * b * np.exp(-b * x)),
                   bounds=list(zip(np.zeros_like(u), u)),
                   constraints=[{"type": "eq", "fun": lambda x: x.sum() - B,
                                 "jac": lambda x: np.ones_like(x)}],
                   method="SLSQP", options={"ftol": 1e-12, "maxiter": 500})
    assert res.success, res.message
    return res.x


# ----------------------------------------------------------------------------
# Reference solution 3: piecewise-linear LP (outer approximation by segments)
# ----------------------------------------------------------------------------
def allocate_lp(a, b, u, B, K=200):
    """Split [0,u_i] into K equal segments; segment k of line i pays its average
    slope. Concavity => slopes decrease, so the LP fills segments in order
    without needing binaries."""
    n = len(a)
    w = u / K                                            # segment widths
    edges = np.linspace(0, 1, K + 1)[None, :] * u[:, None]
    f = a[:, None] * (1 - np.exp(-b[:, None] * edges))
    slope = np.diff(f, axis=1) / w[:, None]              # n x K
    c = -slope.ravel()                                   # linprog minimizes
    A_eq = np.ones((1, n * K)); b_eq = [B]
    bounds = [(0, w[i]) for i in range(n) for _ in range(K)]
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    assert res.status == 0, res.message
    x = res.x.reshape(n, K).sum(axis=1)
    try:                                                 # scipy >= 1.7 (HiGHS duals)
        lam_lp = -res.eqlin.marginals[0]                 # shadow price of budget
    except AttributeError:
        lam_lp = float("nan")
    return x, lam_lp


# ----------------------------------------------------------------------------
# Extension: minimum spend if funded (MILP), plus at most m lines funded
# ----------------------------------------------------------------------------
def allocate_milp(a, b, u, B, m_min, max_funded, K=60):
    n = len(a)
    w = u / K
    edges = np.linspace(0, 1, K + 1)[None, :] * u[:, None]
    f = a[:, None] * (1 - np.exp(-b[:, None] * edges))
    slope = (np.diff(f, axis=1) / w[:, None]).ravel()
    nx = n * K
    c = np.r_[-slope, np.zeros(n)]                       # vars: segments, then z_i
    cons = []
    cons.append(LinearConstraint(np.r_[np.ones(nx), np.zeros(n)][None, :], -np.inf, B))
    for i in range(n):
        row = np.zeros(nx + n); row[i * K:(i + 1) * K] = 1; row[nx + i] = -m_min[i]
        cons.append(LinearConstraint(row[None, :], 0, np.inf))       # sum x_i >= m_i z_i
        for k in range(K):
            row = np.zeros(nx + n); row[i * K + k] = 1; row[nx + i] = -w[i]
            cons.append(LinearConstraint(row[None, :], -np.inf, 0))  # x_ik <= w_i z_i
    row = np.r_[np.zeros(nx), np.ones(n)]
    cons.append(LinearConstraint(row[None, :], 0, max_funded))
    integrality = np.r_[np.zeros(nx), np.ones(n)]
    bounds = Bounds(np.zeros(nx + n), np.r_[np.repeat(w, K), np.ones(n)])
    res = milp(c, constraints=cons, integrality=integrality, bounds=bounds)
    assert res.status == 0, res.message
    x = res.x[:nx].reshape(n, K).sum(axis=1)
    z = np.round(res.x[nx:]).astype(int)
    return x, z


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    a, b, u, B = make_problem()
    x_bis, lam = allocate_bisection(a, b, u, B)
    assert np.isclose(x_bis.sum(), B, atol=1e-8)
    assert np.all(x_bis >= 0) and np.all(x_bis <= u + 1e-12)
    # KKT check: interior lines have marginal value = lam; at 0 marginal <= lam; at cap >= lam
    mv = a * b * np.exp(-b * x_bis)
    interior = (x_bis > 1e-9) & (x_bis < u - 1e-9)
    assert np.allclose(mv[interior], lam, rtol=1e-6)
    assert np.all(mv[x_bis <= 1e-9] <= lam + 1e-9)
    assert np.all(mv[x_bis >= u - 1e-9] >= lam - 1e-9)
    # tight budget: some lines get zero (corner), still matches SLSQP below
    x_small, lam_small = allocate_bisection(a, b, u, 5.0)
    assert np.isclose(x_small.sum(), 5.0) and (x_small < 1e-9).any()
    # budget not binding edge case
    xu, l0 = allocate_bisection(a, b, u, u.sum() * 2)
    assert np.allclose(xu, u) and l0 == 0.0
    if not HAVE_SCIPY:
        print("p5 OK (bisection only; scipy missing)")
        return
    x_sl = allocate_slsqp(a, b, u, B)
    assert np.isclose(objective(x_sl, a, b), objective(x_bis, a, b), rtol=1e-6)
    assert np.allclose(x_sl, x_bis, atol=1e-3)
    assert np.allclose(allocate_slsqp(a, b, u, 5.0), x_small, atol=1e-3)
    x_lp, lam_lp = allocate_lp(a, b, u, B)
    assert np.isclose(x_lp.sum(), B)
    assert objective(x_lp, a, b) <= objective(x_bis, a, b) + 1e-9    # bisection is optimal
    assert np.isclose(objective(x_lp, a, b), objective(x_bis, a, b), rtol=1e-4)
    assert np.isnan(lam_lp) or np.isclose(lam_lp, lam, rtol=0.05), (lam_lp, lam)  # dual ~ multiplier
    if not HAVE_MILP:
        print("p5 OK  (no scipy.optimize.milp; MILP extension skipped) lam=%.5f" % lam)
        return
    # MILP extension: min spend 6 if funded, at most 5 lines
    m_min = np.full(len(a), 6.0)
    x_mi, z = allocate_milp(a, b, u, B, m_min, max_funded=5)
    assert z.sum() <= 5 and np.all(x_mi[z == 0] < 1e-9) and np.all(x_mi[z == 1] >= 6 - 1e-6)
    assert objective(x_mi, a, b) <= objective(x_bis, a, b) + 1e-9    # extra constraints cost value
    print("p5 OK  | lam bisection=%.5f  lam LP dual=%.5f" % (lam, lam_lp))
    print("x bisection:", np.round(x_bis, 2))
    print("x SLSQP    :", np.round(x_sl, 2))
    print("x LP(K=200):", np.round(x_lp, 2))
    print("x MILP     :", np.round(x_mi, 2), "funded:", z)
    print("objective  : bis %.4f  slsqp %.4f  lp %.4f  milp %.4f" % (
        objective(x_bis, a, b), objective(x_sl, a, b), objective(x_lp, a, b), objective(x_mi, a, b)))


if __name__ == "__main__":
    _tests()
