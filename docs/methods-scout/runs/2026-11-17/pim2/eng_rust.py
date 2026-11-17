# Post-hoc engineering extra (not pre-registered): Rust/rayon permutation fitter vs the numpy scalar fitter. 2026-11-17.
import json, os, subprocess, sys, time, numpy as np, pandas as pd
from pimfast import within_pairs, fit
P0 = pd.read_csv('q3_pim_panel.csv'); O = json.load(open('oracle.json')); D = P0.iloc[O['perm_rows']]
D = D.iloc[np.argsort(D.year.values, kind='stable')]; X = D[['drawdown', 'income_pretax_net_rate']].values; Y = D.payout_rwa.values; yr = D.year.values
inp = f"{len(Y)} 2 10000 20261117 50\n" + "\n".join(f"{int(a)} {float(b)!r} {float(c)!r} {float(d)!r}" for a, b, c, d in zip(yr, Y, X[:, 0], X[:, 1]))
runs = []
for r in range(3):
    t0 = time.perf_counter(); p = subprocess.run(['pimperm-rs/target/release/pimperm'], input=inp, capture_output=True, text=True, check=True)
    runs.append(dict(wall_s=time.perf_counter() - t0, inner=p.stderr.strip()))
L = p.stdout.strip().split('\n'); B = np.array([list(map(float, l.split())) for l in L[:10000]]); YP = [np.array(list(map(float, l.split()))) for l in L[10000:]]
pairs = within_pairs(yr); d = max(np.max(np.abs(fit(X, yp, pairs)['beta'] - B[i])) for i, yp in enumerate(YP))
ok_perm = all(np.allclose(np.sort(yp[yr == y]), np.sort(Y[yr == y])) for yp in YP for y in np.unique(yr))
res = dict(label=sys.argv[1] if len(sys.argv) > 1 else 'run', load1=os.getloadavg()[0], runs=runs, parity50_max_dbeta=d, perms_are_within_year=ok_perm,
           perm_sd_beta=B.std(0, ddof=1).tolist())
print(json.dumps(res, indent=1)); json.dump(res, open(f"eng_rust_{res['label']}.json", 'w'), indent=1)
