"""Math avenue for #53: is market-partial rho size-correct? Exactly PREREG.md section C. Seed 20261117, R = 1000."""
import json, numpy as np
import proprlite as P
R = 1000; D = 14; SEED = 20261117

def ar1(rng, phi, T, sd=1.0, size=None):
    shape = (T,) if size is None else (T, size)
    x = np.empty(shape); x[0] = rng.normal(0, sd/np.sqrt(1-phi**2), size=shape[1:] or None)
    e = rng.normal(0, sd, size=(T-1,)+shape[1:])
    for t in range(1, T): x[t] = phi*x[t-1] + e[t-1]
    return x

def one(rng, T, scen, variant):
    z = ar1(rng, 0.9, T)
    lam = rng.normal(0, 0.25, D); lam[0], lam[1] = 0.5, -0.5
    v = ar1(rng, 0.8, T, 0.15, D)
    l = z[:, None]*lam[None, :] + v
    if scen == 'S1':
        w = ar1(rng, 0.8, T, 0.15); l[:, 0] += w; l[:, 1] -= w
    S = np.exp(l - l.max(1, keepdims=True)); S /= S.sum(1, keepdims=True)
    nuis = np.column_stack([ar1(rng, 0.9, T) for _ in range(3)])
    zc = z if variant == 'exact' else z + rng.normal(0, 0.5*z.std(ddof=1), T)
    X = np.column_stack([zc, nuis])
    C = P.clr(S)
    out = {}
    out['Raw'] = P.cyclic_shift_pvalue(C[:, 0], C[:, 1])[1]
    Rl = P.partial_level(S, X); out['PL'] = P.cyclic_shift_pvalue(Rl[:, 0], Rl[:, 1])[1]
    Ri = P.partial_increment(S, X); out['PI'] = P.cyclic_shift_pvalue(Ri[:, 0], Ri[:, 1])[1]
    return out

cells = [(s, T, v) for v in ('exact', 'noisy') for s in ('S0', 'S1') for T in (40, 62)]
kids = np.random.SeedSequence(SEED).spawn(len(cells))
res = {}
for (s, T, v), k in zip(cells, kids):
    rng = np.random.default_rng(k)
    ps = [one(rng, T, s, v) for _ in range(R)]
    rates = {m: float(np.mean([p[m] <= 0.05 for p in ps])) for m in ('Raw', 'PL', 'PI')}
    res[f'{s}|T{T}|{v}'] = rates; print(s, T, v, rates, flush=True)
verdict = {}
for m in ('Raw', 'PL', 'PI'):
    size_ok = all(0.02 <= res[f'S0|T{T}|exact'][m] <= 0.08 for T in (40, 62))
    pow_ok = res['S1|T62|exact'][m] >= 0.80
    verdict[m] = dict(size_ok=size_ok, power_ok=pow_ok, passes=size_ok and pow_ok)
res['verdict'] = verdict; print(verdict)
json.dump(res, open('math_results.json', 'w'), indent=1)
