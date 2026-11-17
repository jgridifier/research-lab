# PREREG.md E2, bar Math-1: coverage of the firm-clustered PIM variance at our design. 2026-11-17. Seed 20261117.
import json, sys, time, numpy as np
from multiprocessing import Pool
from pimfast import within_pairs, fit, vcov_sandwich, vcov_firm
F_, T_, R, RB, B = 40, 13, 2000, 500, 199


def panel(rng, beta, nf=F_):
    c = rng.normal(0, np.sqrt(0.6), nf); a = rng.normal(0, 1, nf); firm, year, x = [], [], []
    for t in range(T_):
        k = int(round(rng.integers(18, 36) * nf / F_)); s = np.sort(rng.choice(nf, k, replace=False))
        firm += list(s); year += [t] * k; x += list(c[s] + rng.normal(0, np.sqrt(0.4), k))
    firm, year, x = map(np.array, (firm, year, x)); y = beta * x + a[firm] + rng.normal(0, 1, len(x))
    return firm, year, x, y


def one(args):
    scen, beta, truth, r = args; rng = np.random.default_rng([20261117, scen, r])
    firm, year, x, y = panel(rng, beta); pairs = within_pairs(year); F = fit(x, y, pairs); b = F['beta'][0]
    out = dict(r=r, b=b, se_sw=float(np.sqrt(vcov_sandwich(F, pairs)[0, 0])), se_f=float(np.sqrt(vcov_firm(F, pairs, firm)[0, 0])))
    if r < RB:
        fs = np.unique(firm); bb = []
        for _ in range(B):
            s = rng.choice(fs, len(fs), replace=True); idx = np.concatenate([np.flatnonzero(firm == f) for f in s])
            yb = year[idx]; o = np.argsort(yb, kind='stable'); idx = idx[o]
            bb.append(fit(x[idx], y[idx], within_pairs(year[idx]))['beta'][0])
        out['bt_lo'], out['bt_hi'] = np.quantile(bb, [0.025, 0.975])
    out['truth'] = truth
    return out


if __name__ == '__main__':
    t0 = time.time(); rng = np.random.default_rng([20261117, 99]); tb = []
    for _ in range(20):
        firm, year, x, y = panel(rng, 0.5, nf=400); tb.append(fit(x, y, within_pairs(year))['beta'][0])
    truthB = float(np.mean(tb)); res = dict(truthB=truthB, truthB_sd=float(np.std(tb, ddof=1)))
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 4) as pool:
        for scen, beta, truth in [(0, 0.0, 0.0), (1, 0.5, truthB)]:
            rows = pool.map(one, [(scen, beta, truth, r) for r in range(R)], chunksize=10)
            b = np.array([q['b'] for q in rows]); z = 1.959963984540054
            cov = lambda se: float(np.mean(np.abs(b - truth) <= z * np.array([q[se] for q in rows])))
            bt = [q for q in rows if 'bt_lo' in q]; cbt = float(np.mean([(q['bt_lo'] <= truth <= q['bt_hi']) for q in bt]))
            res['AB'[scen]] = dict(beta=beta, truth=truth, R=R, cov_sandwich=cov('se_sw'), cov_firm=cov('se_f'), R_boot=len(bt), cov_boot=cbt,
                                   sd_b=float(b.std(ddof=1)), mean_se_sw=float(np.mean([q['se_sw'] for q in rows])),
                                   mean_se_f=float(np.mean([q['se_f'] for q in rows])), bias=float(b.mean() - truth))
            print(scen, json.dumps(res['AB'[scen]]), flush=True)
    res['pass_math1'] = all(0.935 <= res[s]['cov_firm'] <= 0.965 for s in 'AB'); res['seconds'] = time.time() - t0
    json.dump(res, open('math_sim.json', 'w'), indent=1); print(json.dumps(res, indent=1))
