import json, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.stats import t as tdist
d = json.load(open('a2_a3.json')); roll = d['rolling']; names = ['W1', 'W2', 'W3', 'M1', 'M2']
lab = {'W1': 'fails, DVP (wk)', 'W2': 'fails, tri-party (wk)', 'W3': 'DVP, tri-party (wk)', 'M1': 'PF prime broker, fails (mo)', 'M2': 'PF prime broker, reverse repo (mo)'}
def tt(s): return pd.to_datetime(s if len(s) > 7 else s + '-28')
for kind in ('std', 'psi'):
    fig, axs = plt.subplots(5, 1, figsize=(6.2, 7.4), sharex=True)
    for ax, nm in zip(axs, names):
        pts = roll[nm]; t = [tt(q['end']) for q in pts]
        if kind == 'std':
            ax.plot(t, [q['corr'] for q in pts], c='#444'); ax.axhline(0, c='k', lw=.4); ax.set_ylim(-1, 1)
        else:
            ps = np.array([q['psi'] for q in pts]); z = np.array([q['z'] for q in pts]); tc = np.array([tdist.ppf(.975, q['K'] - 1) for q in pts])
            col = np.where(np.abs(z) > tc, np.where(z > 0, '#1a73e8', '#e8710a'), '#c8c8c8')
            ax.bar(t, ps, width=60 if nm[0] == 'W' else 120, color=col); ax.axhline(0, c='k', lw=.4)
        ax.set_ylabel(nm, fontsize=8); ax.set_title(lab[nm], fontsize=8, loc='left', pad=2); ax.tick_params(labelsize=7)
    fig.suptitle('Rolling correlation (usual picture)' if kind == 'std' else 'Rolling PSI: blue first leads, orange second leads, grey not significant', fontsize=9)
    plt.tight_layout(); plt.savefig(f'../../../fig/2026-11-24/psi_{kind}.png', dpi=120); plt.close()
