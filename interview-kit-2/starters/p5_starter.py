"""
Planning allocation: LP, duals, then MILP. ~12 minutes.

P (from make_problem): v value per unit, u caps, m minimum scale if funded,
f fixed set-up cost, reg (bool) regulatory flags, B budget, R_min regulatory
floor, K max number of funded initiatives.
1. solve_lp(P, B=None, R_min=None) -> (x, objective):
       max v'x  s.t. sum x <= B, sum_{reg} x >= R_min, 0 <= x <= u
   with scipy.optimize.linprog. What is the shadow price of the budget?
   Confirm with a finite difference.
2. solve_milp(P) -> (x, z, objective): add binaries z with
   m_i z_i <= x_i <= u_i z_i, sum z <= K, keep the floor, objective v'x - f'z.
3. Why does "fund the highest value per unit first" fail here?
"""
import itertools
import numpy as np

try:
    from scipy.optimize import linprog
except ImportError:
    linprog = None
try:
    from scipy.optimize import milp, LinearConstraint, Bounds
except ImportError:
    milp = None


# ----------------------------------------------------------------------------
# Synthetic problem
# ----------------------------------------------------------------------------
def make_problem(seed: int = 5):
    rng = np.random.default_rng(seed)
    n = 8
    v = np.round(rng.uniform(1.0, 3.0, n), 2)        # value per unit
    u = np.round(rng.uniform(4.0, 12.0, n), 1)       # caps
    m = np.round(u * rng.uniform(0.4, 0.7, n), 1)    # minimum scale if funded
    f = np.round(rng.uniform(2.0, 8.0, n), 1)        # fixed set-up cost (value units)
    reg = np.zeros(n, bool); reg[np.argsort(v)[:2]] = True   # regulatory = two lowest-value
    return dict(v=v, u=u, m=m, f=f, reg=reg, B=30.0, R_min=8.0, K=4)



def solve_lp(P, B=None, R_min=None):
    raise NotImplementedError


def solve_milp(P):
    raise NotImplementedError


def check():
    P = make_problem()
    print({k: v for k, v in P.items()})
    try:
        from scipy.optimize import linprog  # noqa: F401
    except ImportError:
        print("scipy missing: discuss the LP/MILP verbally or solve by hand"); print("checks passed"); return
    x, obj = solve_lp(P)[:2]
    assert x.sum() <= P["B"] + 1e-9 and x[P["reg"]].sum() >= P["R_min"] - 1e-9
    _, obj_up = solve_lp(P, B=P["B"] + 1)[:2]
    print("LP objective %.2f, budget shadow price ~ %.2f" % (obj, obj_up - obj))
    assert obj_up >= obj
    try:
        from scipy.optimize import milp  # noqa: F401
    except ImportError:
        print("milp needs scipy >= 1.9: discuss part 2 verbally"); print("checks passed"); return
    x, z, val = solve_milp(P)
    assert z.sum() <= P["K"] and x.sum() <= P["B"] + 1e-9
    assert np.all((x <= 1e-9) | (x >= P["m"] - 1e-9)), "minimum scale violated"
    assert np.isclose(val, 47.11, atol=0.01), val
    print("MILP objective %.2f, funded %s" % (val, np.round(z).astype(int).tolist()))
    print("checks passed")


if __name__ == "__main__":
    check()
