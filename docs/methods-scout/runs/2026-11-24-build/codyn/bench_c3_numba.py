"""C3 Numba path for the cyclic-shift VR null (same draws as codynport.variance_ratio_null)."""
import time, json, numpy as np, numba as nb, codynport as C
@nb.njit(cache=True)
def null_vr(X, shifts):
    T, S = X.shape; B = shifts.shape[0]; out = np.empty(B)
    mu = np.empty(S)
    for j in range(S):
        s = 0.0
        for t in range(T): s += X[t, j]
        mu[j] = s / T
    den = 0.0
    for j in range(S):
        for t in range(T): den += (X[t, j] - mu[j]) ** 2
    # cyclic shifts preserve each column's mean and sum of squares, so den is constant
    for b in range(B):
        num = 0.0
        for t in range(T):
            r = 0.0
            for j in range(S):
                k = t + shifts[b, j]
                if k >= T: k -= T
                r += X[k, j] - mu[j]
            num += r * r
        out[b] = num / den
    return out
rng = np.random.default_rng(20261124); T, S = 40, 2000
X = np.exp(rng.normal(0, 1, (1, S)) + np.cumsum(rng.normal(0, .1, (T, S)), 0)) * 100
sh = np.random.default_rng(1).integers(0, T, (999, S)); null_vr(X, sh[:2])
ts = []
for _ in range(3): t = time.perf_counter(); n = null_vr(X, sh); ts.append(time.perf_counter() - t)
# NumPy reference with same shifts
idx = (np.arange(T)[None, :, None] + sh[:, None, :]) % T
def np_null():
    out = np.empty(999)
    for c in range(0, 999, 111):
        B = X[idx[c:c + 111], np.arange(S)[None, None, :]]; B = B - B.mean(1, keepdims=True)
        out[c:c + 111] = (B.sum(2) ** 2).sum(1) / (B ** 2).sum((1, 2))
    return out
tn = []
for _ in range(3): t = time.perf_counter(); r = np_null(); tn.append(time.perf_counter() - t)
res = dict(numba_null_sec=float(np.median(ts)), numpy_chunked_null_sec=float(np.median(tn)), port_original_null_sec=4.56, speedup_vs_numpy_chunked=float(np.median(tn) / np.median(ts)),
           speedup_vs_port_original=float(4.56 / np.median(ts)), max_abs_diff=float(np.abs(n - r).max()), threads=1)
res['rust_decision'] = 'Rust not built: best Python path (Numba) is %.0fx faster than the NumPy port; bar for keeping Rust is >=5x over the best Python path, and Numba already puts the full null at %.3f s' % (res['speedup_vs_port_original'], res['numba_null_sec'])
json.dump(res, open('c3_numba.json', 'w'), indent=1); print(json.dumps(res, indent=1))
