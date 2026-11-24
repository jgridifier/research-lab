import time, json, numpy as np
from psi_core import psi, seg_fft, _psi_from
rng = np.random.default_rng(1); n, nch = 10000, 200
X = rng.normal(size=(2 * nch, n)); nper, nover = 256, 128
t = time.perf_counter(); r = [psi(X[2 * i], X[2 * i + 1], nper, nover, (0.02, 0.4), jackknife=True)['z'] for i in range(nch)]; t_loop = time.perf_counter() - t
# vectorised: all pairs from segment FFTs, jackknife by leave-one-out sums
t = time.perf_counter()
F = np.stack([seg_fft(X[i], nper, nover) for i in range(2 * nch)])        # (C, K, Fq)
Xi, Xj = F[0::2], F[1::2]; K = Xi.shape[1]; f = np.fft.rfftfreq(nper); lo = np.searchsorted(f, .02); hi = np.searchsorted(f, .4, 'right')
Xi, Xj = Xi[..., lo:hi], Xj[..., lo:hi]
Sij = Xi * np.conj(Xj); Sii = np.abs(Xi) ** 2; Sjj = np.abs(Xj) ** 2
def psis(Sij_m, Sii_m, Sjj_m):
    C = Sij_m / np.sqrt(Sii_m * Sjj_m); return np.imag(np.sum(np.conj(C[..., :-1]) * C[..., 1:], -1))
tot = [a.sum(1) for a in (Sij, Sii, Sjj)]
ps = np.stack([psis(*[(tt - a[:, k]) / (K - 1) for tt, a in zip(tot, (Sij, Sii, Sjj))]) for k in range(K)], 1)
sd = np.sqrt((K - 1) / K * ((ps - ps.mean(1, keepdims=True)) ** 2).sum(1)); z = psis(*[tt / K for tt in tot]) / sd
t_vec = time.perf_counter() - t
out = dict(channels_pairs=nch, n=n, K=int(K), loop_sec=t_loop, vectorised_sec=t_vec, speedup=t_loop / t_vec, max_abs_z_diff=float(np.abs(z - np.array(r)).max()))
json.dump(out, open('e_speed.json', 'w'), indent=1); print(out)
