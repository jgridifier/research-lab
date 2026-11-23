"""pim #63 build step 3, exactly runs/2026-11-23-build/PREREG-P3.md. Same datasets as runs/2026-11-17/pim2/math_sim.py."""
import json, sys, time, os, numpy as np
from multiprocessing import Pool
from vcov_small import within_pairs, fit, vcov_firm, vcov_cr2, score_wild, vcov_jack, meat_cr2, _meat, _isqrt_apply
F_, T_, R = 40, 13, 2000; Z = 1.959963984540054

def panel(rng, beta, nf=F_):   # copied unchanged from math_sim.py
    c = rng.normal(0, np.sqrt(0.6), nf); a = rng.normal(0, 1, nf); firm, year, x = [], [], []
    for t in range(T_):
        k = int(round(rng.integers(18, 36) * nf / F_)); s = np.sort(rng.choice(nf, k, replace=False))
        firm += list(s); year += [t] * k; x += list(c[s] + rng.normal(0, np.sqrt(0.4), k))
    firm, year, x = map(np.array, (firm, year, x)); y = beta * x + a[firm] + rng.normal(0, 1, len(x))
    return firm, year, x, y

def one(args):
    scen, beta, truth, r = args; rng = np.random.default_rng([20261117, scen, r])
    firm, year, x, y = panel(rng, beta); pairs = within_pairs(year); F = fit(x, y, pairs); b = F['beta'][0]
    t0 = time.perf_counter(); se_f = float(np.sqrt(vcov_firm(F, pairs, firm)[0, 0]))
    t1 = time.perf_counter(); se_cr2 = float(np.sqrt(vcov_cr2(F, pairs, firm)[0, 0]))
    t2 = time.perf_counter(); q = score_wild(F, pairs, firm, 399, np.random.default_rng([20261123, scen, r]))
    t3 = time.perf_counter(); se_j = float(np.sqrt(vcov_jack(x, y, year, firm)[0, 0])); t4 = time.perf_counter()
    return dict(b=b, se_f=se_f, se_cr2=se_cr2, q_wild=q, se_j=se_j, truth=truth, sec=[t1 - t0, t2 - t1, t3 - t2, t4 - t3])

def identities():
    # Harness fixed 2026-11-23 after the first launch (see PREREG-P3 Addendum 1, deviations): meat check is relative to max|B_F|
    # (B_F entries are ~3.5e4, so an absolute 1e-10 is below round-off); random M is scaled so eig(M'M) < 1 (as for a real
    # cluster block of a projection); plus a check on a real firm cluster's M.
    rng = np.random.default_rng([20261123, 7]); firm, year, x, y = panel(rng, 0.5); pairs = within_pairs(year); F = fit(x, y, pairs)
    _, gid = np.unique(firm, return_inverse=True); Bf = _meat(F['u'], pairs, gid)
    d1 = float(np.abs(meat_cr2(F, pairs, firm, adjust=False) - Bf).max() / np.abs(Bf).max())
    def dense(M, rt):
        ev, EV = np.linalg.eigh(np.eye(len(rt)) - M @ M.T); return EV @ np.diag(ev ** -0.5) @ EV.T @ rt
    M = rng.normal(0, 0.1, (30, 2)); rt = rng.normal(size=30)
    d2 = float(np.abs(_isqrt_apply(M, rt) - dense(M, rt)).max())
    w = F['p'] * (1 - F['p']); sw = np.sqrt(w); ev, EV = np.linalg.eigh(F['A']); Aih = EV @ np.diag(ev ** -0.5) @ EV.T
    ix = np.flatnonzero((gid[pairs[:, 0]] == 0) | (gid[pairs[:, 1]] == 0)); Mr = (sw[ix, None] * F['Z'][ix]) @ Aih; rr = rng.normal(size=len(ix))
    d3 = float(np.abs(_isqrt_apply(Mr, rr) - dense(Mr, rr)).max()); lmax = float(np.linalg.eigvalsh(Mr.T @ Mr).max())
    return {'meat_cr2_off_vs_firm_meat_max_rel': d1, 'rank_k_isqrt_vs_dense_random_max_abs': d2,
            'rank_k_isqrt_vs_dense_real_firm0_max_abs': d3, 'real_firm0_max_eig_H': lmax, 'n_pairs_firm0': int(len(ix)),
            'pass': d1 <= 1e-10 and d2 <= 1e-10 and d3 <= 1e-10}

if __name__ == '__main__':
    t0 = time.time(); res = {'prereg': 'runs/2026-11-23-build/PREREG-P3.md', 'identities': identities()}
    print(res['identities'], flush=True)
    assert res['identities']['pass']
    rng = np.random.default_rng([20261117, 99]); tb = []
    for _ in range(20):
        firm, year, x, y = panel(rng, 0.5, nf=400); tb.append(fit(x, y, within_pairs(year))['beta'][0])
    truthB = float(np.mean(tb)); res['truthB'] = truthB
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 6) as pool:
        for scen, beta, truth in [(0, 0.0, 0.0), (1, 0.5, truthB)]:
            rows = pool.map(one, [(scen, beta, truth, r) for r in range(R)], chunksize=5)
            b = np.array([q['b'] for q in rows]); sd = float(b.std(ddof=1))
            cov = lambda half: float(np.mean(np.abs(b - truth) <= half))
            se = {k: np.array([q[k] for q in rows]) for k in ['se_f', 'se_cr2', 'se_j']}; qw = np.array([q['q_wild'] for q in rows])
            out = {'beta': beta, 'truth': truth, 'R': R, 'sd_b': sd,
                   'firm': {'coverage': cov(Z * se['se_f']), 'mean_se_over_sd': float(se['se_f'].mean() / sd), 'mean_halfwidth': float((Z * se['se_f']).mean())},
                   'firm_cr2': {'coverage': cov(Z * se['se_cr2']), 'mean_se_over_sd': float(se['se_cr2'].mean() / sd), 'mean_halfwidth': float((Z * se['se_cr2']).mean())},
                   'score_wild': {'coverage': cov(qw * se['se_f']), 'mean_q': float(qw.mean()), 'mean_halfwidth': float((qw * se['se_f']).mean())},
                   'firm_jack': {'coverage': cov(Z * se['se_j']), 'mean_se_over_sd': float(se['se_j'].mean() / sd), 'mean_halfwidth': float((Z * se['se_j']).mean())},
                   'sec_per_rep_median': dict(zip(['firm', 'firm_cr2', 'score_wild', 'firm_jack'], np.median([q['sec'] for q in rows], 0).tolist()))}
            res['AB'[scen]] = out; print(scen, json.dumps(out), flush=True)
    band = lambda c: 0.935 <= c <= 0.965
    passing = [m for m in ['firm_cr2', 'firm_jack', 'score_wild'] if all(band(res[s][m]['coverage']) for s in 'AB')]
    res['passing'] = passing
    res['default'] = (min(passing, key=lambda m: (np.mean([abs(res[s][m]['coverage'] - 0.95) for s in 'AB']), ['firm_cr2', 'firm_jack', 'score_wild'].index(m))) if passing else 'firm (hard warning; kill rule)')
    res['step3_pass'] = bool(passing); res['seconds'] = time.time() - t0
    json.dump(res, open('p3_results.json', 'w'), indent=1); print(json.dumps({k: res[k] for k in ['passing', 'default', 'step3_pass', 'seconds']}))
