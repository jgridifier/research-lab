"""Plug the reference functions into each starter and run the starter's check()."""
import importlib.util, sys, pathlib, numpy as np, pandas as pd
D = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(D / "solutions"))
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
import p1_bank_panel_cleaning as r1, p2_rolling_backtest_dm as r2, p3_conditional_scenario_forecast as r3
import p4_local_projection_nw as r4, p5_budget_allocation as r5, p6_monte_carlo_numba as r6, p7_sql_window_functions as r7
def p3_project(beta, hist, path):
    g, lvl = r3.project(beta, hist, path); return pd.DataFrame({"g": g[0], "deposits": lvl[0]}, index=path.index)
def p6_sim(n, ead, pd_, lgd, rho, seed=0):
    rng = np.random.default_rng(seed); return r6.losses_vec(rng.standard_normal(n), rng.standard_normal((n, len(ead))), ead, pd_, lgd, rho)
patch = {1: dict(clean_panel=r1.clean_panel), 2: dict(backtest=r2.backtest, diebold_mariano=r2.diebold_mariano),
         3: dict(fit_arx=r3.fit_arx, project=p3_project), 4: dict(newey_west=r4.newey_west, local_projection=r4.local_projection),
         5: dict(allocate_bisection=r5.allocate_bisection), 6: dict(simulate_losses=p6_sim), 7: dict(SQL=r7.SQL_GROWTH)}
import io, contextlib
for i in range(1, 8):
    m = load(D / "starters" / f"p{i}_starter.py", f"s{i}")
    for k, v in patch[i].items(): setattr(m, k, v)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): m.check()
    print(f"starter p{i}: check() passes with reference functions | last line: {buf.getvalue().strip().splitlines()[-1][:60]}")
