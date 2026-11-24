"""A2 (Q1 pairs, PSI vs standard toolkit) + A3 (stability, rolling) + figure. Public aggregates only."""
import json, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from scipy.stats import norm
from statsmodels.tsa.api import VAR
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from psi_core import psi
import data_psi as D
res = {}; rows = []
def ccf_peak(x, y, maxlag):
    n = len(x); bands = 2 / np.sqrt(n); best = (0, 0.)
    out = {}
    for k in range(-maxlag, maxlag + 1):
        if k >= 0: r = np.corrcoef(x[:n - k], y[k:])[0, 1]     # x leads y by k when y_{t+k}~x_t
        else: r = np.corrcoef(x[-k:], y[:n + k])[0, 1]
        out[k] = r
        if abs(r) > abs(best[1]): best = (k, r)
    return best, bands
def granger(x, y, maxlags=8):
    v = VAR(np.column_stack([x, y])).fit(maxlags=maxlags, ic='aic')
    if v.k_ar == 0: return dict(lag=0, p_x_to_y=1., p_y_to_x=1.)
    return dict(lag=int(v.k_ar), p_x_to_y=float(v.test_causality(1, 0, kind='f').pvalue), p_y_to_x=float(v.test_causality(0, 1, kind='f').pvalue))
for name, freq, a, b in D.PAIRS:
    d = D.pair(freq, a, b); P = D.PARAM[freq]; x, y = d[a].values, d[b].values
    r = psi(x, y, **P); p = 2 * (1 - norm.cdf(abs(r['z'])))
    g = granger(x, y); (k, rk), bands = ccf_peak(x, y, 8 if freq == 'weekly' else 6)
    h = len(x) // 2; r1 = psi(x[:h], y[:h], **P); r2 = psi(x[h:], y[h:], **P)
    rows.append(dict(pair=name, freq=freq, x=a, y=b, n=len(x), start=str(d.index[0]), end=str(d.index[-1]), K=r['K'], psi=r['psi'], z=r['z'], p=p,
                     gc=g, ccf_peak_lag=k, ccf_peak_r=rk, ccf_band95=bands, z_first=r1.get('z', float('nan')), z_second=r2.get('z', float('nan')), K_half=r1['K']))
# Holm
ps = np.array([r['p'] for r in rows]); o = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0
for i, j in enumerate(o): run = max(run, (m - i) * ps[j]); adj[j] = min(1, run)
for r, a in zip(rows, adj): r['p_holm'] = float(a)
res['pairs'] = rows
# A3 rolling PSI
roll = {}
for name, freq, a, b in D.PAIRS:
    if name not in ('W1', 'W2', 'W3', 'M1', 'M2'): continue
    d = D.pair(freq, a, b); P = D.PARAM[freq]; x, y = d[a].values, d[b].values
    win, step = (104, 13) if freq == 'weekly' else (60, 6); pts = []
    for s in range(0, len(x) - win + 1, step):
        r = psi(x[s:s + win], y[s:s + win], **P); c = np.corrcoef(x[s:s + win], y[s:s + win])[0, 1]
        pts.append(dict(end=str(d.index[s + win - 1]), z=r['z'], psi=r['psi'], K=r['K'], corr=float(c)))
    roll[name] = pts
res['rolling'] = roll
json.dump(res, open('a2_a3.json', 'w'), indent=1, default=float)
for r in rows: print(r['pair'], r['x'], r['y'], 'K', r['K'], 'psi %.3f z %.2f p %.3f holm %.3f' % (r['psi'], r['z'], r['p'], r['p_holm']), 'GC', r['gc'], 'ccf', r['ccf_peak_lag'], round(r['ccf_peak_r'], 2), 'halves z', round(r['z_first'], 2), round(r['z_second'], 2))
# figure: lead-lag strip chart (PSI z) vs rolling correlation
fig, axs = plt.subplots(5, 2, figsize=(11, 9), sharex='col', gridspec_kw=dict(width_ratios=[1.4, 1]))
for i, nm in enumerate(['W1', 'W2', 'W3', 'M1', 'M2']):
    pts = roll[nm]; t = pd.to_datetime([q['end'] if len(q['end']) > 7 else q['end'] + '-28' for q in pts]); z = np.array([q['z'] for q in pts]); ps_ = np.array([q['psi'] for q in pts]); tc = np.array([__import__('scipy.stats').stats.t.ppf(.975, q['K'] - 1) for q in pts]); c = np.array([q['corr'] for q in pts])
    pr = [p_ for p_ in D.PAIRS if p_[0] == nm][0]
    ax = axs[i, 0]; col = np.where(np.abs(z) > tc, np.where(z > 0, '#1a73e8', '#e8710a'), '#c8c8c8')
    ax.bar(t, ps_, width=60 if nm[0] == 'W' else 120, color=col); ax.axhline(0, c='k', lw=.4)
    ax.set_ylabel(f'{nm}\n{pr[2]}→{pr[3]}', fontsize=8); ax.tick_params(labelsize=7)
    ax2 = axs[i, 1]; ax2.plot(t, c, c='#555'); ax2.axhline(0, c='k', lw=.4); ax2.set_ylim(-1, 1); ax2.tick_params(labelsize=7)
axs[0, 0].set_title('PSI, rolling window: blue first leads, orange second leads, grey not significant (t crit, df=K-1)', fontsize=9)
axs[0, 1].set_title('Standard: rolling correlation of the same windows', fontsize=9)
plt.tight_layout(); plt.savefig('psi_strip.png', dpi=130)
