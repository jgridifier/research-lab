"""
Budget allocation across n business lines. ~12 minutes.

    max_x  sum_i a_i (1 - exp(-b_i x_i))   s.t.  sum_i x_i = B,  0 <= x_i <= u_i

1. Solve it with the first-order conditions + bisection on the Lagrange
   multiplier. Return (x, lam).
2. Solve it again with scipy (scipy.optimize.minimize or linprog) and compare
   allocations, objective values, and lam vs the solver's dual if you get one.
3. Talk: what changes if each line needs a minimum spend of 6 when funded,
   and at most 5 lines can be funded?
"""
import numpy as np


def make_problem(n: int = 8, seed: int = 4):
    rng = np.random.default_rng(seed)
    a = rng.uniform(5, 20, n)        # saturation level of each line's payoff
    b = rng.uniform(0.05, 0.4, n)    # how fast payoff saturates
    u = rng.uniform(8, 25, n)        # caps
    B = 0.45 * u.sum()
    return a, b, u, B


def objective(x, a, b):
    return np.sum(a * (1 - np.exp(-b * x)))


def allocate_bisection(a, b, u, B):
    raise NotImplementedError


def check():
    a, b, u, B = make_problem()
    x, lam = allocate_bisection(a, b, u, B)
    print(np.round(x, 3), lam, objective(x, a, b))
    assert np.isclose(x.sum(), B) and np.all(x >= -1e-12) and np.all(x <= u + 1e-12)
    print("checks passed")


if __name__ == "__main__":
    check()
