"""ebnm #55 build step 2: NumPy (sqp_np.py) vs Rust (rs/) on one ash fit at ~1,000 programs and 10,000 bootstrap refits.
SYNTHETIC mock inputs (2026-11-13 generator). Parity of each path against ebnm 1.1.42 on the oracle grid."""
import json, os, subprocess, time, numpy as np
from concurrent.futures import ProcessPoolExecutor
import sqp_np as S
HERE = os.path.dirname(os.path.abspath(__file__)); BIN = HERE + '/rs/target/release/ebnm_bench'
fx = json.load(open(HERE + '/../oracle/fixtures.json'))
import ebnmport as E
res = {'data': 'SYNTHETIC Q2 mock ZBB (2026-11-13)', 'host': 'box, 8 vCPU shared; bootstrap with 4 workers/threads', 'mocks': {}}
def np_boot(args):
    x, s, gm, seed, reps = args; rng = np.random.default_rng(seed); out = []
    for _ in range(reps):
        i = rng.integers(0, len(x), len(x)); xb, sb = x[i], s[i]
        out.append(S.ash_fit(xb, sb, E.smn_scale_grid(xb, sb, 0.0, grid_mult=gm))['loglik'])
    return out
for firm in ['Corning_mock', 'MorganStanley_mock']:
    r = fx[firm]; x = np.array(r['x']); s = np.array(r['s']); o = r['normal_scale_mixture']; sc = np.array(o['sd'])
    gm = E.grid_mult_for(1 / len(x))
    np.savetxt('/tmp/s2_xs.csv', np.column_stack([x, s]), delimiter=',', fmt='%.17g'); np.savetxt('/tmp/s2_sc.txt', sc, fmt='%.17g')
    # Rust, oracle grid (parity) and own grid (speed incl. grid), plus 10,000 refits on 4 threads
    env = dict(os.environ, RAYON_NUM_THREADS='4')
    subprocess.run([BIN, '/tmp/s2_xs.csv', '/tmp/s2_sc.txt', str(gm), '/tmp/s2_rs_or.json', '1', '1'], check=True, env=env)
    subprocess.run([BIN, '/tmp/s2_xs.csv', '-', str(gm), '/tmp/s2_rs.json', '10000', '20261123'], check=True, env=env)
    ro = json.load(open('/tmp/s2_rs_or.json')); rr = json.load(open('/tmp/s2_rs.json'))
    m_np = S.ash_fit(x, s, sc); ts = []
    for _ in range(100):
        t = time.perf_counter(); S.ash_fit(x, s, E.smn_scale_grid(x, s, 0.0, grid_mult=gm)); ts.append(time.perf_counter() - t)
    t = time.perf_counter()
    with ProcessPoolExecutor(4) as ex: lls = sum(ex.map(np_boot, [(x, s, gm, 20261123 + w, 250) for w in range(4)]), [])
    np_boot_250x4 = time.perf_counter() - t
    res['mocks'][firm] = {
        'n': int(len(x)),
        'parity_vs_ebnm_oracle_grid': {
            'numpy': {'d_loglik': abs(m_np['loglik'] - o['loglik']), 'max_d_mean': float(np.abs(m_np['post_mean'] - o['post_mean']).max()), 'max_d_lfsr': float(np.abs(m_np['lfsr'] - o['lfsr']).max())},
            'rust': {'d_loglik': abs(ro['loglik'] - o['loglik']), 'max_d_mean': float(np.abs(np.array(ro['post_mean']) - o['post_mean']).max()), 'max_d_lfsr': float(np.abs(np.array(ro['lfsr']) - o['lfsr']).max())}},
        'one_fit_ms': {'numpy_median100': 1000 * float(np.median(ts)), 'rust_median200': rr['fit_ms_median200'], 'R_ebnm_median20': 1000 * r['ash_sec_median20']},
        'refits': {'rust_10000_s_4threads': rr['boot_s'], 'numpy_1000_s_4procs': np_boot_250x4, 'numpy_10000_s_4procs_extrapolated': 10 * np_boot_250x4},
        'speedup_rust_vs_numpy_one_fit': float(np.median(ts)) * 1000 / rr['fit_ms_median200']}
    print(firm, json.dumps(res['mocks'][firm], indent=1), flush=True)
c = res['mocks']['Corning_mock']
res['accept'] = 'one ash fit <= 3 ms at ~1,000 programs; 10,000 refits <= 30 s on 4 vCPU; keep Rust only if >= 5x faster than the best Python path'
res['pass_fit_3ms'] = min(c['one_fit_ms']['rust_median200'], c['one_fit_ms']['numpy_median100']) <= 3
res['pass_10000_refits_30s'] = c['refits']['rust_10000_s_4threads'] <= 30
res['keep_rust'] = all(m['speedup_rust_vs_numpy_one_fit'] >= 5 for m in res['mocks'].values())
json.dump(res, open(HERE + '/s2_results.json', 'w'), indent=1)
print({k: res[k] for k in ['pass_fit_3ms', 'pass_10000_refits_30s', 'keep_rust']})
