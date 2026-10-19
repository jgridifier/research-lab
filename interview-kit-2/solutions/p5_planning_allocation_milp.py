"""
Problem 5 (swap-in, ~12 min): allocate a planning budget across initiatives
(an optimization model that changes a decision).

n initiatives; x_i = units of budget (e.g. $m or FTE) given to initiative i.
value per unit v_i, cap u_i. Budget B. Some initiatives are regulatory and
must together receive at least R_min units.
  1. LP: max v'x  s.t. sum x <= B, sum_{reg} x >= R_min, 0 <= x <= u.
     Solve with linprog; report the shadow price of the budget and check it
     with a finite difference (re-solve with B + 1).
  2. MILP: each initiative also has a fixed set-up cost f_i and a minimum
     scale m_i if funded (x_i = 0 or m_i <= x_i <= u_i), and at most K can be
     funded; the regulatory floor still applies. max v'x - f'z. Solve with scipy.optimize.milp and verify by
     brute force over all 2^n funding sets.
  3. Show that greedy-by-value fails on the MILP.
numpy required; scipy >= 1.9 for milp (the brute-force solver works without it).
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


# ----------------------------------------------------------------------------
# Reference solution 1: LP and its duals
# ----------------------------------------------------------------------------
def solve_lp(P, B=None, R_min=None):
    B = P["B"] if B is None else B
    R_min = P["R_min"] if R_min is None else R_min
    n = len(P["v"])
    A_ub = np.vstack([np.ones(n), -P["reg"].astype(float)])
    b_ub = np.array([B, -R_min])
    res = linprog(-P["v"], A_ub=A_ub, b_ub=b_ub, bounds=list(zip(np.zeros(n), P["u"])), method="highs")
    assert res.status == 0, res.message
    duals = -res.ineqlin.marginals if hasattr(res, "ineqlin") else None   # scipy >= 1.7
    return res.x, -res.fun, duals


# ----------------------------------------------------------------------------
# Reference solution 2: MILP and a brute-force verifier
# ----------------------------------------------------------------------------
def solve_milp(P):
    v, u, m, f, K, B = P["v"], P["u"], P["m"], P["f"], P["K"], P["B"]
    n = len(v)
    c = -np.r_[v, -f]                         # variables [x (n), z (n)]; minimize -(v'x - f'z)
    I = np.eye(n)
    cons = [LinearConstraint(np.r_[np.ones(n), np.zeros(n)][None, :], -np.inf, B),
            LinearConstraint(np.hstack([I, -np.diag(u)]), -np.inf, 0.0),     # x <= u z
            LinearConstraint(np.hstack([I, -np.diag(m)]), 0.0, np.inf),      # x >= m z
            LinearConstraint(np.r_[np.zeros(n), np.ones(n)][None, :], -np.inf, K),
            LinearConstraint(np.r_[P["reg"].astype(float), np.zeros(n)][None, :], P["R_min"], np.inf)]
    integrality = np.r_[np.zeros(n), np.ones(n)]
    res = milp(c, constraints=cons, integrality=integrality,
               bounds=Bounds(np.zeros(2 * n), np.r_[u, np.ones(n)]))
    assert res.status == 0, res.message
    x, z = res.x[:n], np.round(res.x[n:]).astype(int)
    return x, z, -res.fun


def best_given_z(P, z):
    """With the funding set fixed, the problem is a bounded fractional knapsack
    with unit costs: give every funded initiative its minimum, top up the
    regulatory floor with the best regulatory lines, then fill by value."""
    v, u, m, reg = P["v"], P["u"], P["m"], P["reg"]
    x = np.where(z, m, 0.0)
    left = P["B"] - x.sum()
    if left < -1e-12:
        return None, -np.inf
    need = P["R_min"] - x[reg].sum()
    for i in np.argsort(-v):
        if z[i] and reg[i] and need > 0:
            add = min(u[i] - x[i], left, need); x[i] += add; left -= add; need -= add
    if need > 1e-9:
        return None, -np.inf                      # floor cannot be met with this z
    for i in np.argsort(-v):
        if z[i]:
            add = min(u[i] - x[i], left); x[i] += add; left -= add
    return x, float(v @ x - P["f"] @ z)


def brute_force(P):
    n = len(P["v"]); best = (None, None, -np.inf)
    for bits in itertools.product([0, 1], repeat=n):
        z = np.array(bits)
        if z.sum() > P["K"]:
            continue
        x, val = best_given_z(P, z)
        if val > best[2]:
            best = (x, z, val)
    return best


def greedy(P):
    """Fund the best regulatory line (to meet the floor), then initiatives in
    order of value per unit until K or the budget runs out."""
    z = np.zeros(len(P["v"]), int); spent = 0.0
    order = list(np.argsort(-P["v"]))
    regs, cap = [], 0.0
    for i in order:                                  # enough regulatory lines for the floor
        if P["reg"][i] and cap < P["R_min"]:
            regs.append(i); cap += P["u"][i]
    order = regs + [i for i in order if i not in regs]
    for i in order:
        if z.sum() < P["K"] and spent + P["m"][i] <= P["B"]:
            z[i] = 1; spent += P["m"][i]
    return best_given_z(P, z)


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    P = make_problem()
    msg = []
    if linprog is not None:
        x, obj, duals = solve_lp(P)
        assert x.sum() <= P["B"] + 1e-9 and x[P["reg"]].sum() >= P["R_min"] - 1e-9
        assert (x >= -1e-9).all() and (x <= P["u"] + 1e-9).all()
        _, obj_up, _ = solve_lp(P, B=P["B"] + 1.0)
        _, obj_reg, _ = solve_lp(P, R_min=P["R_min"] + 1.0)
        assert obj_reg < obj                       # the floor binds: it costs value
        if duals is not None:
            # duals of the <= rows; the floor is written as -sum_reg x <= -R_min,
            # so raising R_min by 1 changes the objective by -duals[1]
            assert np.isclose(duals[0], obj_up - obj, atol=1e-8), (duals, obj_up - obj)
            assert np.isclose(-duals[1], obj_reg - obj, atol=1e-8), (duals, obj_reg - obj)
        msg.append("LP obj %.2f, budget shadow price %.2f/unit, cost of +1 unit of reg floor %.2f"
                   % (obj, obj_up - obj, obj - obj_reg))
    xb, zb, vb = brute_force(P)
    xg, vg = greedy(P)
    assert vg < vb - 1e-9, "greedy should be suboptimal on this instance"
    if milp is not None:
        x, z, val = solve_milp(P)
        assert np.isclose(val, vb, atol=1e-6), (val, vb)
        assert z.sum() <= P["K"] and x.sum() <= P["B"] + 1e-9
        assert np.all((x <= 1e-9) | ((x >= P["m"] - 1e-9) & (x <= P["u"] + 1e-9)))
        if linprog is not None:
            assert val <= obj + 1e-9      # the LP is a relaxation (no fixed costs, no minimums)
        msg.append("MILP %.2f == brute force %.2f, funded %s" % (val, vb, z.tolist()))
    else:
        msg.append("milp unavailable; brute force %.2f, funded %s" % (vb, zb.tolist()))
    msg.append("greedy %.2f (gap %.2f)" % (vg, vb - vg))
    print("p5 OK  | " + " | ".join(msg))


if __name__ == "__main__":
    _tests()
