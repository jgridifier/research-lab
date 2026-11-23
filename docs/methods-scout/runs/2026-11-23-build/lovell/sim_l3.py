"""Lovell #53 build step 3, exactly PREREG.md section L3 (runs/2026-11-23-build). DGP identical to
runs/2026-11-17/lovell/sim_partial.py; only T and proxy noise vary. Seed 20261123, R = 1000, 32 cells."""
import json, sys, time, numpy as np
from concurrent.futures import ProcessPoolExecutor
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-17", "lovell")); import proprlite as P
R = 1000; D = 14; SEED = 20261123
TS = (20, 30, 40, 62); NOISE = (0.0, 0.10, 0.25, 0.50); SCEN = ('S0', 'S1')

def ar1(rng, phi, T, sd=1.0, size=None):
    shape = (T,) if size is None else (T, size)
    x = np.empty(shape); x[0] = rng.normal(0, sd/np.sqrt(1-phi**2), size=shape[1:] or None)
    e = rng.normal(0, sd, size=(T-1,)+shape[1:])
    for t in range(1, T): x[t] = phi*x[t-1] + e[t-1]
    return x

def one(rng, T, scen, noise):
    z = ar1(rng, 0.9, T)
    lam = rng.normal(0, 0.25, D); lam[0], lam[1] = 0.5, -0.5
    v = ar1(rng, 0.8, T, 0.15, D)
    l = z[:, None]*lam[None, :] + v
    if scen == 'S1':
        w = ar1(rng, 0.8, T, 0.15); l[:, 0] += w; l[:, 1] -= w
    S = np.exp(l - l.max(1, keepdims=True)); S /= S.sum(1, keepdims=True)
    nuis = np.column_stack([ar1(rng, 0.9, T) for _ in range(3)])
    zc = z if noise == 0 else z + rng.normal(0, noise*z.std(ddof=1), T)
    X = np.column_stack([zc, nuis])
    C = P.clr(S)
    out = {}
    out['Raw'] = P.cyclic_shift_pvalue(C[:, 0], C[:, 1])[1]
    Rl = P.partial_level(S, X); out['PL'] = P.cyclic_shift_pvalue(Rl[:, 0], Rl[:, 1])[1]
    Ri = P.partial_increment(S, X); out['PI'] = P.cyclic_shift_pvalue(Ri[:, 0], Ri[:, 1])[1]
    return out

cells = [(T, nz, s) for T in TS for nz in NOISE for s in SCEN]
kids = np.random.SeedSequence(SEED).spawn(len(cells))

def run_cell(i):
    T, nz, s = cells[i]; rng = np.random.default_rng(kids[i])
    ps = [one(rng, T, s, nz) for _ in range(R)]
    return f'{s}|T{T}|noise{nz}', {m: float(np.mean([p[m] <= 0.05 for p in ps])) for m in ('Raw', 'PL', 'PI')}

if __name__ == '__main__':
    t0 = time.time()
    with ProcessPoolExecutor(4) as ex:
        res = dict(ex.map(run_cell, range(len(cells))))
    for k, v in res.items(): print(k, v)
    ex_ = lambda s, T, nz=0.0: res[f'{s}|T{T}|noise{nz}']['PI']
    bars = {'size_T40': ex_('S0', 40), 'size_T62': ex_('S0', 62), 'power_T62': ex_('S1', 62)}
    bars['pass'] = all(0.02 <= bars[k] <= 0.08 for k in ('size_T40', 'size_T62')) and bars['power_T62'] >= 0.80
    min_t = [T for T in TS if 0.02 <= ex_('S0', T) <= 0.08 and ex_('S1', T) >= 0.80]
    tol = {T: max([nz for nz in NOISE if ex_('S0', T, nz) <= 0.08], default=None) for T in TS}
    out = {'prereg': 'runs/2026-11-23-build/PREREG.md section L3', 'seed': SEED, 'R': R, 'cells': res,
           'bars_PI_exact': bars, 'min_T_PI_exact': (min(min_t) if min_t else None),
           'min_T_table': {T: {'size': ex_('S0', T), 'power': ex_('S1', T)} for T in TS},
           'largest_noise_size_le_0.08_PI': tol,
           'kill_triggered': not all(0.02 <= bars[k] <= 0.08 for k in ('size_T40', 'size_T62')),
           'runtime_s': time.time() - t0}
    json.dump(out, open('l3_results.json', 'w'), indent=1); print(json.dumps({k: out[k] for k in out if k != 'cells'}, indent=1))
