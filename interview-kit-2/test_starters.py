"""Plug the reference functions into each starter and run the starter's check().
Also confirms each untouched starter fails cleanly (stubs raise, nothing else breaks)."""
import importlib.util, sys, pathlib, io, contextlib
D = pathlib.Path(__file__).resolve().parent
SOL = D / "solutions" if (D / "solutions").is_dir() else D
sys.path.insert(0, str(SOL))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


import p1_champion_outcomes as r1, p2_deposit_runoff_scenarios as r2, p3_frozen_champion_overlay as r3
import p4_scenario_distance_ot as r4, p5_planning_allocation_milp as r5, p6_gl_sql_pipeline as r6
import p7_variance_explainer_guardrail as r7

patch = {
    1: dict(leak_test=r1.leak_test, fixed_backtest=r1.fixed_backtest, diebold_mariano=r1.diebold_mariano),
    2: dict(simulate=r2.simulate, trough_grid=r2.trough_grid),
    3: dict(hinge_basis=r3.hinge_basis, fit_overlay=r3.fit_overlay, build_challenger=r3.build_challenger),
    4: dict(wasserstein_1d=r4.wasserstein_1d, ot_lp=r4.ot_lp, sliced_wasserstein=r4.sliced_wasserstein),
    5: dict(solve_lp=r5.solve_lp, solve_milp=r5.solve_milp),
    6: dict(SQL=r6.SQL),
    7: dict(pvm=r7.pvm, check_narrative=r7.check_narrative),
}
fails = 0
for i in range(1, 8):
    path = D / "starters" / f"p{i}_starter.py"
    # (a) untouched starter: check() must fail on a stub (NotImplementedError / AssertionError)
    m0 = load(path, f"s{i}_raw")
    note = "stubs fail cleanly"
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            m0.check()
        if i == 5 and r5.linprog is None:
            note = "scipy missing, so check() skips the solver parts (expected)"
        else:
            print(f"starter p{i}: UNEXPECTED pass with stubs"); fails += 1
    except (NotImplementedError, AssertionError):
        pass
    # (b) with reference functions: check() must pass
    m = load(path, f"s{i}")
    for k, v in patch[i].items():
        setattr(m, k, v)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m.check()
    last = buf.getvalue().strip().splitlines()[-1]
    assert last == "checks passed", last
    print(f"starter p{i}: {note}; check() passes with reference functions")
sys.exit(1 if fails else 0)
