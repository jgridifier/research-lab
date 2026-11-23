"""ebnm #55 build step 3, exactly PREREG.md section E3 (runs/2026-11-23-build). SYNTHETIC mocks, seed 20261123."""
import sys, json, subprocess, numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, '..'); import ebnmport as E
D = '/workspace/scout/1123-build/data/'; SEED = 20261123
def bh(p, q=0.05):
    n = len(p); o = np.argsort(p); ok = p[o] <= q * np.arange(1, n + 1) / n
    k = np.max(np.nonzero(ok)[0]) + 1 if ok.any() else 0; r = np.zeros(n, bool); r[o[:k]] = True; return r
BINS = [(0, 0.01), (0.01, 0.05), (0.05, 0.2), (0.2, 0.5)]
out = {'prereg': 'runs/2026-11-23-build/PREREG.md section E3', 'data': 'SYNTHETIC Q2 mock ZBB regenerated with seed 20261123', 'mocks': {}}
rng = np.random.default_rng(SEED)
for firm in ['Corning_mock', 'MorganStanley_mock']:
    F = pd.read_csv(D + f'{firm}_features.csv'); K = pd.read_csv(D + f'{firm}_KEY_true_levels.csv')
    yrs = sorted(int(c[1:]) for c in F.columns if c.startswith('y') and c[1:].isdigit()); T1, T0 = yrs[-1], yrs[-2]
    ok = F[f'y{T1}'].notna() & F[f'y{T0}'].notna(); f = F[ok]
    x = (f[f'y{T1}'] - f[f'y{T0}']).to_numpy(); s = np.sqrt(2) * f['sigma'].to_numpy()
    tl = K.pivot(index='program_id', columns='fiscal_year', values='true_usd')
    tg = np.log(tl.loc[f.program_id, T1].to_numpy()) - np.log(tl.loc[f.program_id, T0].to_numpy())
    fit = E.ebnm_ash(x, s, 0.0)
    flag = fit['lfsr'] < 0.05; pm = fit['post_mean']
    wrong = np.sign(pm) != np.sign(tg)
    p = 2 * stats.norm.sf(np.abs(x / s)); bhr = bh(p)
    cal = []
    for lo, hi in BINS:
        b = (fit['lfsr'] > lo) & (fit['lfsr'] <= hi); n = int(b.sum())
        e = {'bin': f'({lo}, {hi}]', 'n': n}
        if n: e.update(mean_lfsr=float(fit['lfsr'][b].mean()), wrong_sign=float(wrong[b].mean()), abs_gap=float(abs(wrong[b].mean() - fit['lfsr'][b].mean())))
        e['scored'] = n >= 20; e['pass'] = (e['abs_gap'] <= 0.05) if e['scored'] else None; cal.append(e)
    # all-zero-effect version: x = s * eps
    x0 = s * rng.standard_normal(len(s)); f0 = E.ebnm_ash(x0, s, 0.0); ff = float(np.mean(f0['lfsr'] < 0.05))
    # R cross-check on the same inputs
    np.savetxt('/tmp/e3_xs.csv', np.column_stack([x, s]), delimiter=',')
    r = subprocess.run([str(__import__('pathlib').Path.home() / 'mamba/envs/rscout/bin/Rscript'), '-e',
        'suppressMessages(library(ebnm)); d<-read.csv("/tmp/e3_xs.csv",header=FALSE); f<-ebnm(d[,1],d[,2],prior_family="normal_scale_mixture",mode=0,output=ebnm_output_all()); cat(sprintf("%.10f %d", as.numeric(logLik(f)), sum(f$posterior$lfsr<0.05)))'],
        capture_output=True, text=True)
    rll, rflags = r.stdout.split(); 
    m = {'n': int(len(x)), 'years': [T0, T1], 'flags': int(flag.sum()), 'bh_calls': int(bhr.sum()),
         'wrong_sign_rate_flags': float(wrong[flag].mean()) if flag.any() else None,
         'bh_wrong_sign_rate': float((np.sign(x) != np.sign(tg))[bhr].mean()) if bhr.any() else None,
         'flags_over_bh': float(flag.sum() / bhr.sum()) if bhr.sum() else None, 'calibration': cal,
         'all_zero_false_flag_rate': ff, 'loglik_port': fit['loglik'], 'loglik_R': float(rll), 'R_flags': int(rflags)}
    m['pass'] = {'wrong_sign_le_5pct': m['wrong_sign_rate_flags'] is not None and m['wrong_sign_rate_flags'] <= 0.05,
                 'flags_ge_3x_bh': m['flags'] >= 3 * m['bh_calls'],
                 'calibration_within_5pts': all(c['pass'] for c in cal if c['scored']),
                 'all_zero_false_flags_le_5pct': ff <= 0.05}
    out['mocks'][firm] = m; print(firm, json.dumps(m, indent=1))
out['step3_pass'] = all(all(v['pass'].values()) for v in out['mocks'].values())
out['kill_triggered'] = any(not v['pass']['wrong_sign_le_5pct'] for v in out['mocks'].values())
json.dump(out, open('e3_results.json', 'w'), indent=1); print('step3_pass', out['step3_pass'], 'kill', out['kill_triggered'])
