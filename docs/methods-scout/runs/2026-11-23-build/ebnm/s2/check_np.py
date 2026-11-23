import json, time, numpy as np, sqp_np as S
fx = json.load(open('../oracle/fixtures.json'))
for firm in ['Corning_mock', 'MorganStanley_mock']:
    r = fx[firm]; x = np.array(r['x']); s = np.array(r['s']); o = r['normal_scale_mixture']; sc = np.array(o['sd'])
    m = S.ash_fit(x, s, sc); ts = []
    for _ in range(50): t = time.perf_counter(); S.ash_fit(x, s, sc); ts.append(time.perf_counter() - t)
    print(firm, 'iters', m['iters'], 'dLL', abs(m['loglik'] - o['loglik']), 'dmean', np.abs(m['post_mean'] - o['post_mean']).max(), 'dlfsr', np.abs(m['lfsr'] - o['lfsr']).max(), 'ms', 1000 * np.median(ts))
