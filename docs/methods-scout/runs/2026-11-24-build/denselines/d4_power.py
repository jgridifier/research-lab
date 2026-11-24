"""D4 (PREREG.md Addendum 2): branch-test power. SYNTHETIC."""
import json, time, numpy as np, diptest
T = 6; NS = [50, 100, 200, 500, 1000, 2000]; SEPS = [1.5, 2.0, 3.0]; R = 500; RN = 2000
def em2(x, rng, restarts=6):
    n = len(x); v0 = x.var(); floor = 1e-6 * v0
    ll1 = -0.5 * n * (np.log(2 * np.pi * v0) + 1)
    best = -np.inf
    for _ in range(restarts):
        mu = np.sort(rng.choice(x, 2, replace=False)); s2 = np.array([v0, v0]) / 2; w = np.array([.5, .5])
        for _ in range(60):
            d = (x[:, None] - mu[None]) ** 2 / s2; lp = np.log(w) - 0.5 * (np.log(2 * np.pi * s2) + d)
            m = lp.max(1, keepdims=True); r = np.exp(lp - m); tot = r.sum(1, keepdims=True); r /= tot
            nk = r.sum(0)
            if nk.min() < 0.03 * n: break
            w = nk / n; mu = (r * x[:, None]).sum(0) / nk; s2 = np.maximum((r * (x[:, None] - mu) ** 2).sum(0) / nk, floor)
        else:
            d = (x[:, None] - mu[None]) ** 2 / s2; lp = np.log(w) - 0.5 * (np.log(2 * np.pi * s2) + d); m = lp.max(1)
            ll = (m + np.log(np.exp(lp - m[:, None]).sum(1))).sum(); best = max(best, ll)
    return max(0.0, 2 * (best - ll1)) if np.isfinite(best) else 0.0
def sim_resid(N, rng, drift=0.0, frac=0.10):
    Y = np.cumsum(rng.normal(0, .15, (N, T)), 1)
    if drift:
        b = rng.permutation(N)[:max(1, int(round(frac * N)))]; Y[b, 3:] += drift * np.arange(1, 4)
    V = Y - Y.mean(1, keepdims=True); R_ = V - np.median(V, 0, keepdims=True); return R_[:, -1]
def drift_for(N, s, rng):  # separation of branch mean from main mean at last col = s sd of null residual
    sd = np.mean([sim_resid(N, rng).std() for _ in range(50)])
    # branch adds drift*(1+2+3) to last col before demeaning; demeaning shifts all by -mean(add)/T; separation = drift*(3 - mean([0,0,0,1,2,3]) = 3-1)= 2*drift
    return s * sd / 2.0
out = {'seed': 20261124, 'R': R, 'RN': RN, 'T': T}
ss = np.random.SeedSequence(20261124)
for N in NS:
    rng = np.random.default_rng(ss.spawn(1)[0]); t0 = time.time()
    nl = [em2(sim_resid(N, rng), rng) for _ in range(RN)]; crit = float(np.quantile(nl, .95))
    dp = [diptest.diptest(sim_resid(N, rng))[1] for _ in range(RN)]
    cell = {'null': {'lrt_size': float(np.mean(np.array(nl) > crit)), 'lrt_crit95': crit, 'dip_size': float(np.mean(np.array(dp) < .05))}}
    for s in SEPS:
        d = drift_for(N, s, rng); l = []; p = []
        for _ in range(R):
            x = sim_resid(N, rng, d); l.append(em2(x, rng) > crit); p.append(diptest.diptest(x)[1] < .05)
        cell[f's{s}'] = {'drift': float(d), 'lrt_power': float(np.mean(l)), 'dip_power': float(np.mean(p))}
    out[str(N)] = cell; print(N, json.dumps(cell), round(time.time() - t0), 's', flush=True)
tab = {}
for s in SEPS:
    for t in ('lrt', 'dip'):
        ok = [N for N in NS if out[str(N)][f's{s}'][f'{t}_power'] >= .8]; tab[f'{t}_s{s}_min_N_power_ge_0.8'] = min(ok) if ok else None
out['min_N'] = tab
out['size_ok'] = {t: all(out[str(N)]['null'][f'{t}_size'] <= .07 for N in NS) for t in ('lrt', 'dip')}
out['adopt'] = {t: bool(out['size_ok'][t] and tab[f'{t}_s2.0_min_N_power_ge_0.8'] is not None) for t in ('lrt', 'dip')}
json.dump(out, open('d4_results.json', 'w'), indent=1); print(json.dumps({k: out[k] for k in ('min_N', 'size_ok', 'adopt')}, indent=1))
