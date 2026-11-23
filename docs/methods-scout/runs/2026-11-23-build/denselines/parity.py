"""Step-1 parity: denselines_core (gap-safe weighted streaming Rust core) vs the authors' Rust reference
(line-density-rust @083890c, run_series/sum_images unchanged via runs/2026-11-13/parity_harness.rs).
SYNTHETIC inputs: the reference's own demo generator (sine + N(0,12), clamp, u32), width 400, height 300, seed 20261123."""
import numpy as np, subprocess, json, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
REF = HERE + "/ldr-ref/target/release/parity"; CORE = HERE + "/core/target/release/dl"; T = "/tmp/dl_parity_1123/"; os.makedirs(T, exist_ok=True)
W, H = 400, 300; rng = np.random.default_rng(20261123)
model = H / 4 * np.sin(np.arange(W) / 20) + H / 2
gen = lambda n: np.clip(model + rng.normal(0, 12, (n, W)), 0, H).astype(np.int64)
def write(S, f): open(f, "w").write("\n".join(",".join(map(str, s)) for s in S))
def ref(S):
    write(S, T + "in.txt"); p = subprocess.run([REF, T + "in.txt", T + "ref.txt", str(W), str(H)], capture_output=True, text=True, check=True)
    return np.loadtxt(T + "ref.txt", delimiter=",", dtype=str), float(p.stderr.split()[-1])
def core(S, wts=None):
    write(S, T + "in.txt"); args = [CORE, T + "in.txt", T + "core.txt", str(W), str(H)]
    if wts is not None: np.savetxt(T + "w.txt", wts); args.append(T + "w.txt")
    p = subprocess.run(args, capture_output=True, text=True, check=True)
    L = open(T + "core.txt").read().splitlines()
    live = np.array(L[0].split(","), float); wm = np.array(L[1].split(","), float)
    G = np.array([r.split(",") for r in L[2:]], float); return G, live, wm, float(p.stderr.split()[-1])
res = {"reference_commit": "083890c94a4d54d00362d3df0bb5259d30adf5b5", "data": "SYNTHETIC (reference demo generator, seed 20261123)",
       "metric": "max_rel = max|core-ref| / max|ref| over the grid; also max per-pixel rel diff on ref>0", "full_span": []}
for n in [100, 1000, 5000]:
    S = gen(n); Rs, rs = ref(S); R = Rs.astype(float); G, live, wm, cs = core(S)
    e = {"n": n, "same_nonzero_pixels": bool(((R > 0) == (G > 0)).all()), "max_abs_diff": float(np.abs(R - G).max()),
         "max_rel": float(np.abs(R - G).max() / np.abs(R).max()),
         "max_pixel_rel": float((np.abs(R - G) / np.maximum(R, 1e-300))[R > 0].max()),
         "colsum_max_abs_dev_from_n": float(np.abs(G.sum(0) - n).max()), "live_all_n": bool((live == n).all()),
         "ref_s": rs, "core_s": cs}
    e["pass"] = e["max_rel"] <= 1e-6 and e["colsum_max_abs_dev_from_n"] <= 1e-6 * n
    res["full_span"].append(e); print(e)
S = gen(50); S2 = [s if i >= 10 else s[:300] for i, s in enumerate(S)]
Rs, _ = ref(S2); nan_ref = int((np.char.lower(Rs) == "nan").any(0).sum())
G, live, wm, _ = core(S2)
res["gap_case"] = {"series": 50, "stopping_at_col_300": 10, "ref_nan_columns": nan_ref, "core_nan_columns": int(np.isnan(G).any(0).sum()),
    "core_colsum_cols_300_399_min": float(G[:, 300:].sum(0).min()), "core_colsum_cols_300_399_max": float(G[:, 300:].sum(0).max()),
    "core_colsum_cols_0_298": [float(G[:, :299].sum(0).min()), float(G[:, :299].sum(0).max())],
    "live_col_299_and_300": [float(live[299]), float(live[300])],
    "gap_match_ref_on_cols_0_298_max_abs": float(np.abs(Rs[:, :299].astype(float) - G[:, :299]).max())}
g = res["gap_case"]; g["pass"] = g["core_nan_columns"] == 0 and abs(g["core_colsum_cols_300_399_min"] - 40) < 1e-9 and abs(g["core_colsum_cols_300_399_max"] - 40) < 1e-9
print(g)
# NaN-in-the-middle gap + weights: 20 series, series 0-4 absent in cols 100-149; weights 1..20
S = gen(20).astype(float); S[:5, 100:150] = np.nan; wts = np.arange(1, 21, dtype=float)
G, live, wm, _ = core([["" if np.isnan(v) else str(int(v)) for v in s] for s in S], wts)
res["weighted_nan_gap"] = {"nan_columns": int(np.isnan(G).any(0).sum()),
    "colsum_equals_W_max_abs": float(np.abs(G.sum(0) - wm).max()), "W_in_gap_cols": float(wm[120]), "W_expected": float(wts[5:].sum()),
    "live_in_gap": float(live[120])}
print(res["weighted_nan_gap"])
res["step1_pass"] = all(e["pass"] for e in res["full_span"]) and g["pass"]
json.dump(res, open(HERE + "/parity.json", "w"), indent=1); print("step1_pass", res["step1_pass"])
