"""Exact NumPy port (runs/2026-11-13/denselines.py, gap_safe=True) on the same SYNTHETIC random-walk shape, n=1000 x 1000 cols."""
import sys, time, json, numpy as np
sys.path.insert(0, "/workspace/rl-build-1123/docs/methods-scout/runs/2026-11-13"); from denselines import density
rng = np.random.default_rng(20261123); n, W, H = 1000, 1000, 300
S = np.clip(H / 2 + np.cumsum(rng.uniform(-3, 3, (n, W)), 1), 0, H).astype(np.int64)
t = time.perf_counter(); D = density(list(S), W, H, gap_safe=True); s = time.perf_counter() - t
json.dump({"n": n, "width": W, "height": H, "numpy_s": s, "colsum_ok": bool(np.allclose(D.sum(0), n)), "data": "SYNTHETIC random walks, seed 20261123"}, open("bench_numpy.json", "w"), indent=1)
print(s)
