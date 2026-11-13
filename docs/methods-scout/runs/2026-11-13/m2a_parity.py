"""Parity and speed: NumPy port vs authors' Rust reference on the reference's own demo generator
(sine model + N(0,12) noise, clamp to [0,height], u32 cast; width 400, height 300), plus a gap case."""
import numpy as np, subprocess, time, json, sys, os
sys.path.insert(0, '/workspace/scout/1113/runs'); from denselines import density
BIN = '/workspace/scout/1113/ldr/target/release/parity'; T = '/tmp/dl_parity/'; os.makedirs(T, exist_ok=True)
W, H = 400, 300; rng = np.random.default_rng(20261113)
model = H / 4 * np.sin(np.arange(W) / 20) + H / 2
def gen(n): return np.clip(model + rng.normal(0, 12, (n, W)), 0, H).astype(np.int64)
def rust(S, w=W, h=H):
    f = T + 'in.txt'; np.savetxt(f, S, fmt='%d', delimiter=',')
    t = time.time(); p = subprocess.run([BIN, f, T + 'out.txt', str(w), str(h)], capture_output=True, text=True); wall = time.time() - t
    sec = float(p.stderr.split()[-1]); return np.loadtxt(T + 'out.txt', delimiter=','), sec, wall
res = {'reference_commit': '083890c94a4d54d00362d3df0bb5259d30adf5b5', 'parity': [], 'speed': []}
for n in [100, 1000, 5000]:
    S = gen(n); R, rs, _ = rust(S)
    t = time.time(); P = density(list(S), W, H); ps = time.time() - t
    P32 = density(list(S), W, H, dtype=np.float32)
    nzR = R > 0; nzP = P > 0
    res['parity'].append({'n': n, 'same_nonzero_pixels': bool((nzR == nzP).all()), 'max_abs_diff': float(np.abs(R - P).max()),
        'max_rel_diff': float((np.abs(R - P) / np.maximum(R, 1e-12))[nzR].max()), 'column_sums_equal_n': bool(np.allclose(P.sum(0), n)),
        'rust_compute_s': rs, 'numpy_s': ps})
    print(res['parity'][-1])
# gap case: same 50 series, but 10 of them stop at column 300
S = gen(50); S2 = [s if i >= 10 else s[:300] for i, s in enumerate(S)]
f = T + 'in.txt'; open(f, 'w').write('\n'.join(','.join(map(str, s)) for s in S2))
p = subprocess.run([BIN, f, T + 'out.txt', str(W), str(H)], capture_output=True, text=True)
Rg = np.loadtxt(T + 'out.txt', delimiter=',', dtype=str); Rg = np.char.lower(Rg); nan_cols_rust = int(np.any(Rg == 'nan', axis=0).sum())
Pg = density(S2, W, H); Ps = density(S2, W, H, gap_safe=True)
res['gap_case'] = {'series': 50, 'series_stopping_at_col_300': 10, 'rust_nan_columns': nan_cols_rust, 'port_default_nan_columns': int(np.isnan(Pg).any(0).sum()),
                   'gap_safe_nan_columns': int(np.isnan(Ps).any(0).sum()), 'gap_safe_colsum_after_300': float(Ps[:, 350].sum())}
print(res['gap_case'])
for n in [1000, 10000, 50000]:
    S = gen(n); R, rs, wall = rust(S); t = time.time(); density(list(S), W, H); ps = time.time() - t
    res['speed'].append({'n': n, 'rust_compute_s': rs, 'numpy_s': ps}); print(res['speed'][-1])
json.dump(res, open('/workspace/scout/1113/out/m2a_parity.json', 'w'), indent=1)
