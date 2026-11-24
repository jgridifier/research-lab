"""C3: speed of all codyn-port metrics with a 999-draw null on SYNTHETIC 2,000 entities x 40 periods. Run under `taskset -c 0-3`."""
import time, json, os, numpy as np
import codynport as C
rng = np.random.default_rng(20261124); T, S = 40, 2000
X = np.exp(rng.normal(0, 1, (1, S)) + np.cumsum(rng.normal(0, .1, (T, S)), 0)) * 100
def med3(f):
    ts = []
    for _ in range(3): t = time.perf_counter(); f(); ts.append(time.perf_counter() - t)
    return float(np.median(ts))
res = {'threads': len(os.sched_getaffinity(0)), 'panel': [T, S]}
res['variance_ratio'] = med3(lambda: C.variance_ratio(X))
res['variance_ratio_null_999'] = med3(lambda: C.variance_ratio_null(X, 999, seed=1))
res['rate_change'] = med3(lambda: C.rate_change(X))
res['mean_rank_shift'] = med3(lambda: C.mean_rank_shift(X))
res['rank_clocks'] = med3(lambda: C.rank_clocks(X))
res['all_numpy_total'] = sum(res[k] for k in ['variance_ratio_null_999', 'rate_change', 'mean_rank_shift', 'rank_clocks'])
res['bar_sec'] = 5.0; res['pass_numpy'] = res['all_numpy_total'] <= 5.0
json.dump(res, open('c3_bench.json', 'w'), indent=1); print(json.dumps(res, indent=1))
