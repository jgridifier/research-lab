"""Parity of codynport.py vs codyn 2.0.6 fixtures (separate program; oracle = R). SYNTHETIC fixture + real-panel aggregates."""
import json, time, numpy as np, pandas as pd, codynport as C
fx = json.load(open("oracle/fixture.json")); po = json.load(open("oracle/panels_oracle.json"))
X = np.array([[np.nan if v is None else v for v in row] for row in fx["X"]], float)
mine = {"vr": C.variance_ratio(X), "rate_change": C.rate_change(X), "rank_shift": C.rank_shift(X), "mrs_mean": C.mean_rank_shift(X)}
fix = {}
for k in ["vr", "rate_change", "mrs_mean"]:
    fix[k] = {"oracle": fx[k], "port": mine[k], "abs_diff": abs(fx[k] - mine[k])}
d = np.max(np.abs(np.array(fx["rank_shift"]) - mine["rank_shift"]))
fix["rank_shift_per_pair"] = {"n_pairs": len(fx["rank_shift"]), "max_abs_diff": float(d)}
for k in fix: fix[k]["pass"] = bool(fix[k].get("abs_diff", fix[k].get("max_abs_diff")) <= 1e-10)
targets = {("A", "vr_raw"): 4.4537, ("A", "rate_change_shares"): 0.001379, ("E4", "rate_change_shares"): 0.004727,
           ("A", "mrs_shares"): 0.3846, ("E4", "mrs_shares"): 0.2377}
pan = {}; tim = {}
for p in ["A", "E4"]:
    w = pd.read_csv(f"/workspace/scout/1112-adhoc/data/panel_{p}.csv"); sp = [c for c in w.columns if c != "q"]
    Xr = w[sp].to_numpy(float); Xs = Xr / Xr.sum(1, keepdims=True)
    vals = {"vr_raw": C.variance_ratio(Xr), "rate_change_shares": C.rate_change(Xs), "mrs_shares": C.mean_rank_shift(Xs)}
    for k, v in vals.items():
        e = {"port": v, "oracle_rerun": po[p][k], "abs_diff_vs_oracle": abs(v - po[p][k])}
        if (p, k) in targets:
            e["published_11_12"] = targets[(p, k)]; e["abs_diff_vs_published"] = abs(v - targets[(p, k)]); e["pass_1e-4"] = e["abs_diff_vs_published"] <= 1e-4
        pan[f"{p}:{k}"] = e
    if p == "A":
        ts = []
        for _ in range(3):
            t = time.perf_counter(); nl = C.variance_ratio_null(Xr, 999, seed=20261123); ts.append(time.perf_counter() - t)
        tim = {"port_999_null_sec_median3": float(np.median(ts)), "R_codyn_999_null_sec": po["timing_R_A_999"],
               "port_null": {k: nl[k] for k in ["lowerCI", "upperCI", "nullmean"]},
               "R_null": {k: po["A_null_R"][k] for k in ["lowerCI", "upperCI", "nullmean"]},
               "note": "null intervals are random draws (different RNGs); compared loosely, not for parity"}
rep = {"oracle": "codyn 2.0.6 (R 4.5.3)", "fixture": "SYNTHETIC 30 species x 25 periods, seed 20261123, ties, zeros, absences",
       "fixture_parity": fix, "panels_11_12": pan, "timing": tim,
       "step1_numeric_pass": all(v["pass"] for v in fix.values()) and all(v.get("pass_1e-4", True) for v in pan.values())}
json.dump(rep, open("parity.json", "w"), indent=1, default=float); print(json.dumps(rep, indent=1, default=float))
