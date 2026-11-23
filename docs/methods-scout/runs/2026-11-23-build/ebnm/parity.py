"""Parity of ebnmport.py against ebnm 1.1.42 fixtures (separate program; oracle = R)."""
import json, time, numpy as np, ebnmport as E
fx = json.load(open("oracle/fixtures.json")); rep = {"oracle": "ebnm 1.1.42 / mixsqp 0.3.54 (R 4.5.3)", "data": "SYNTHETIC Q2 mock ZBB (2026-11-13, seed 20261113)", "mocks": {}}
for firm in ["Corning_mock", "MorganStanley_mock"]:
    r = fx[firm]; x = np.array(r["x"]); s = np.array(r["s"]); R = {}
    t = time.perf_counter(); gm = E.grid_mult_for(1 / len(x)); tg = time.perf_counter() - t
    oracle_sd = np.array(r["normal_scale_mixture"]["sd"])
    mine_sd = E.smn_scale_grid(x, s, 0.0, grid_mult=gm)
    R["grid"] = {"K_oracle": len(oracle_sd), "K_port": len(mine_sd), "grid_mult_port": gm,
                 "max_abs_scale_diff": float(np.max(np.abs(mine_sd - oracle_sd))) if len(mine_sd) == len(oracle_sd) else None,
                 "grid_solve_sec": tg}
    for fam, fn, kw in [("normal_scale_mixture", E.ebnm_ash, {"grid_mult": gm}),
                        ("normal_scale_mixture_oracle_grid", E.ebnm_ash, {"scale": oracle_sd}),
                        ("point_normal", E.ebnm_point_normal, {}), ("normal", E.ebnm_normal, {})]:
        o = r[fam.replace("_oracle_grid", "")]
        ts = []
        for _ in range(5):
            t = time.perf_counter(); m = fn(x, s, 0.0, **kw); ts.append(time.perf_counter() - t)
        R[fam] = {"loglik_oracle": o["loglik"], "loglik_port": m["loglik"], "abs_d_loglik": abs(o["loglik"] - m["loglik"]),
                  "max_abs_d_post_mean": float(np.max(np.abs(m["post_mean"] - np.array(o["post_mean"])))),
                  "max_abs_d_post_sd": float(np.max(np.abs(m["post_sd"] - np.array(o["post_sd"])))),
                  "max_abs_d_lfsr": float(np.max(np.abs(m["lfsr"] - np.array(o["lfsr"])))),
                  "port_sec_median5": float(np.median(ts))}
        R[fam]["pass"] = bool(R[fam]["abs_d_loglik"] <= 1e-4 and R[fam]["max_abs_d_post_mean"] <= 1e-6 and R[fam]["max_abs_d_lfsr"] <= 1e-6)
    R["oracle_ash_sec_median20"] = r["ash_sec_median20"]
    rep["mocks"][firm] = R
rep["accept"] = "ash loglik to <=1e-4 (-145.7808 Corning, -238.8506 MS) and posterior means + lfsr within 1e-6 on both mocks"
rep["step1_pass"] = all(rep["mocks"][f]["normal_scale_mixture"]["pass"] for f in rep["mocks"])
json.dump(rep, open("parity.json", "w"), indent=1); print(json.dumps(rep, indent=1))
