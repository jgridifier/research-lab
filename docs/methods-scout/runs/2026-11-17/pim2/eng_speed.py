# PREREG.md E1, bar Eng-2 (speed): 10,000 within-year permutations of the B1 joint model. 2026-11-17.
import json, os, sys, time, numpy as np, pandas as pd
from pimfast import within_pairs, perm_fit, fit, vcov_sandwich
P0 = pd.read_csv('q3_pim_panel.csv'); O = json.load(open('oracle.json')); D = P0.iloc[O['perm_rows']]
X = D[['drawdown', 'income_pretax_net_rate']].values; Y = D.payout_rwa.values; yr = D.year.values
perm_fit(X, Y, yr, 200, seed=1)  # warm-up
load = os.getloadavg()[0]; ts = []
for r in range(3):
    t0 = time.perf_counter(); B, it = perm_fit(X, Y, yr, 10000, seed=20261117 + r); ts.append(time.perf_counter() - t0)
# check a few against the scalar fitter
pairs = within_pairs(yr); rng = np.random.default_rng(5)
# time incl. sandwich SE per permutation (scalar loop, no bar), on 300 permutations then scaled
t0 = time.perf_counter()
for r in range(300):
    Yp = Y.copy()
    for y in np.unique(yr):
        ix = np.flatnonzero(yr == y); Yp[ix] = Y[ix][rng.permutation(len(ix))]
    F = fit(X, Yp, pairs); vcov_sandwich(F, pairs)
t_se = (time.perf_counter() - t0) / 300 * 10000
res = dict(label=sys.argv[1] if len(sys.argv) > 1 else 'run', load1=load, n=len(Y), pairs=len(pairs), nperm=10000,
           wall_s=ts, median_s=float(np.median(ts)), newton_iters_total=it, with_sandwich_scalar_s_extrap=t_se,
           pim_R_s_extrap=O['pim_sec_20perm'][0] / 20 * 10000, threads=os.environ.get('OMP_NUM_THREADS', 'default'),
           ncpu=os.cpu_count())
print(json.dumps(res, indent=1)); json.dump(res, open(f"eng_speed_{res['label']}.json", 'w'), indent=1)
