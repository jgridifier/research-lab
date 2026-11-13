"""Figures for methods scout 2026-11-13: ebnm + DenseLines on SYNTHETIC mock ZBB data."""
import json, numpy as np, pandas as pd, matplotlib, subprocess, sys
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, PowerNorm
from scipy.ndimage import gaussian_filter1d, gaussian_filter
def bl(D): return gaussian_filter(np.nan_to_num(D), 1.6)  # display-only blur, 1.6 px
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 140, 'savefig.bbox': 'tight',
    'savefig.facecolor': 'white', 'axes.labelcolor': '#1c150d', 'text.color': '#1c150d', 'axes.edgecolor': '#1c150d', 'xtick.color': '#1c150d', 'ytick.color': '#1c150d'})
INK='#1c150d'; AMB='#e8902e'; TEAL='#1f9e8e'; RED='#df5236'; BLUE='#3b6fb6'; GRN='#54b441'; GREY='#9a9389'
CM = LinearSegmentedColormap.from_list('dl', ['#fbf6ec', '#bfe0d6', '#1f9e8e', '#16453c', '#1c150d'])
B='/workspace/scout/1113/'; F=B+'fig/'; SYN='SYNTHETIC mock data (q2-mock-zbb, seed 20261113)'
m1=json.load(open(B+'out/m1_results.json')); m1c=json.load(open(B+'out/m1c_relative.json'))
m2=json.load(open(B+'out/m2_results.json')); par=json.load(open(B+'out/m2a_parity.json')); A=np.load(B+'out/m2_arrays.npy',allow_pickle=True).item()
W,H=500,300
def tag(fig): fig.text(0.995, -0.04, SYN, ha='right', va='bottom', fontsize=7, color=RED)
# ---------- m1_shrink
fig, ax = plt.subplots(1, 3, figsize=(14, 4.4), gridspec_kw={'width_ratios': [1.3, 1, 1], 'wspace': .3})
ex = m1['Corning_mock']['A1']['example']; o = np.argsort(ex['truth']); a = ax[0]
for i, j in enumerate(o):
    a.annotate('', xy=(i, ex['ash'][j]), xytext=(i, ex['raw'][j]), arrowprops=dict(arrowstyle='->', color=GREY, lw=.8))
a.scatter(range(len(o)), np.array(ex['raw'])[o], s=16, color=AMB, label='own 2025 actual (log)', zorder=3)
a.scatter(range(len(o)), np.array(ex['ash'])[o], s=16, color=TEAL, label='ebnm (ash prior), pooled', zorder=3)
a.scatter(range(len(o)), np.array(ex['truth'])[o], s=22, marker='_', color=INK, lw=2, label='true level (answer key)', zorder=4)
a.set_title(f'One group ({len(o)} programs):\n{ex["group"]}', loc='left', fontsize=9); a.set_xlabel('programs, sorted by true level'); a.set_ylabel('log 2025 spend'); a.legend(fontsize=7, frameon=False)
for k, firm in enumerate(['Corning_mock', 'MorganStanley_mock']):
    t = pd.DataFrame(m1[firm]['A1']['table']); a = ax[k + 1]
    lab = [s.replace('ebnm: ', '').replace('Own 2025 actual (no pooling)', 'own actual').replace('Group mean (complete pooling)', 'group mean') for s in t.estimator]
    x = np.arange(len(t)); a.bar(x - .2, t.rmse_family, .4, color=TEAL, label='programs in a pooling family'); a.bar(x + .2, t.rmse_nonfamily, .4, color=AMB, label='programs not in a family')
    a.plot(x, t.rmse_all, 'o', color=INK, ms=4, label='all programs')
    a.set_xticks(x); a.set_xticklabels(lab, rotation=35, ha='right', fontsize=7.5); a.set_ylabel('RMSE vs true log level'); a.set_title(firm.replace('_mock', ' mock') + ':\nerror of the 2025 level', loc='left', fontsize=9)
    if k == 0: a.legend(fontsize=7, frameon=False)
tag(fig); fig.savefig(F + 'm1_shrink.png'); plt.close(fig)
# ---------- m1_lfsr
fig, ax = plt.subplots(1, 3, figsize=(15, 4.6), gridspec_kw={'wspace': .3})
for k, firm in enumerate(['Corning_mock', 'MorganStanley_mock']):
    s = m1[firm]['A2']['scatter']; g = np.array(s['g']); t = np.array(s['truth']); l = np.array(s['lfsr']); e = np.array(s['ash']); a = ax[k]
    c = np.where(l < 0.05, TEAL, '#d9d2c5'); a.scatter(t, g, s=5, c=c, alpha=.8)
    lim = np.percentile(np.abs(np.r_[g, t]), 99.5); a.plot([-lim, lim], [-lim, lim], color=GREY, lw=.7); a.axhline(0, color=GREY, lw=.5); a.axvline(0, color=GREY, lw=.5)
    a.set_xlim(-lim, lim); a.set_ylim(-lim, lim); a.set_xlabel('true 2024→25 change (log, answer key)'); a.set_ylabel('observed change (log)')
    a.set_title(f'{firm.replace("_mock"," mock")}\nteal = ebnm calls the change real (lfsr < 0.05)', loc='left', fontsize=9)
a = ax[2]; rows = []
for firm in ['Corning_mock', 'MorganStanley_mock']:
    C = pd.DataFrame(m1[firm]['A2']['calls'])
    for nm, lb in [('Naive z-test |z|>1.96', 'naive z'), ('Naive + BH q<0.05', 'BH'), ('ebnm ash, lfsr<0.05', 'ebnm')]:
        r = C.set_index('_row').loc[nm]
        rows.append((firm.split('_')[0][:7], lb, r['n_calls'], r['false_sign_rate']))
x = np.arange(len(rows)); cols = [AMB, GREY, TEAL] * 2
a.bar(x, [r[2] for r in rows], color=cols)
for i, r in enumerate(rows): a.text(i, r[2] + 4, f'{100*r[3]:.1f}%', ha='center', fontsize=7.5)
a.set_xticks(x); a.set_xticklabels([f'{r[0]}\n{r[1]}' for r in rows], fontsize=7); a.set_ylabel('programs called "really changed"'); a.set_title('Programs called "really changed",\nlabel = share with the wrong sign', loc='left', fontsize=9)
tag(fig); fig.savefig(F + 'm1_lfsr.png'); plt.close(fig)
# ---------- m1_text
fig, ax = plt.subplots(1, 1, figsize=(7.5, 3.4)); rows = []
for firm in ['Corning_mock', 'MorganStanley_mock']:
    au = m1[firm]['A3']['auc']; ar = m1c[firm]['auc']
    rows += [(firm.split('_')[0], 'absolute slope', au['raw_slope'], au['naive_z'], au['ebnm_postmean']), (firm.split('_')[0], 'slope vs peers', ar['raw'], ar['naive_z'], ar['ebnm'])]
x = np.arange(len(rows))
for j, (lb, c) in enumerate([('raw slope', AMB), ('naive z', GREY), ('ebnm posterior mean', TEAL)]): ax.bar(x + (j - 1) * .25, [r[2 + j] for r in rows], .25, color=c, label=lb)
ax.axhline(.5, color=GREY, lw=.7, ls=':'); ax.set_ylim(.4, .85); ax.set_xticks(x); ax.set_xticklabels([f'{r[0]}\n{r[1]}' for r in rows], fontsize=7.5)
ax.set_ylabel('AUC: planted "stated grow, actually declining"'); ax.legend(fontsize=7, frameon=False, ncol=3, loc='upper left'); ax.set_title('Text vs numbers: ranking stated-growth programs by how much they decline', loc='left', fontsize=9)
tag(fig); fig.savefig(F + 'm1_text.png'); plt.close(fig)
# ---------- m2_hero: spaghetti vs unnormalised vs DenseLines (Corning)
a0 = A['Corning_mock']; V = a0['V']; yrs = m2['Corning_mock']['years']; lo, hi = a0['lo'], a0['hi']
fig, ax = plt.subplots(1, 3, figsize=(14, 4.6))
for v in V: ax[0].plot(yrs, v, color=INK, lw=.5, alpha=.07)
ax[0].set_ylim(lo, hi); ax[0].set_title(f'Spaghetti: {len(V)} programs, each indexed to its own mean', loc='left', fontsize=9); ax[0].set_ylabel('log spend vs own mean')
ext = [yrs[0], yrs[-1], lo, hi]
for a, Dm, t in [(ax[1], a0['Du'], 'Line count per pixel (no arc-length normalisation)'), (ax[2], a0['Dn'], 'DenseLines (each program weight 1 per column)')]:
    a.imshow(bl(Dm), origin='lower', aspect='auto', extent=ext, cmap=CM, norm=PowerNorm(.6)); a.set_title(t, loc='left', fontsize=9)
med = np.nanmedian(V, 0); ax[2].plot(yrs, med, color=AMB, lw=1.2, ls='--', label='median program'); ax[2].legend(fontsize=7, frameon=False, loc='lower right')
for a in ax: a.set_xticks(yrs)
tag(fig); fig.savefig(F + 'm2_hero.png'); plt.close(fig)
# ---------- m2_residual: residual DenseLines + profile + brush, and small multiples
for firm, cl in [('Corning_mock', 'ai_datacenter_demand'), ('MorganStanley_mock', 'equity_market_activity')]:
    a0 = A[firm]; yrs = m2[firm]['years']; ext = [yrs[0], yrs[-1], a0['rlo'], a0['rhi']]
    sm = a0['sm']; segs = sorted([k for k in sm if k.startswith('segment:')], key=lambda k: -sm[k].sum())[:4]; cls = [k for k in sm if k.startswith('cluster:')][:4]
    fig = plt.figure(figsize=(14, 6.6)); gs = fig.add_gridspec(2, 6, width_ratios=[1.6, .08, 1, 1, 1, 1], hspace=.45, wspace=.25)
    a = fig.add_subplot(gs[:, 0]); a.imshow(bl(a0['DR']), origin='lower', aspect='auto', extent=ext, cmap=CM, norm=PowerNorm(.6))
    if not np.isnan(a0['brush']): a.axhline(a0['brush'], color=AMB, lw=1.4, ls='--'); a.text(yrs[0] + .08, a0['brush'] + .012, 'label-free brush (valley in last column)', color=RED, fontsize=7.5, bbox=dict(facecolor='white', edgecolor='none', alpha=.85, pad=1.5))
    a.set_title(f'{firm.replace("_mock"," mock")}: residual DenseLines\n(each path minus the median path)', loc='left', fontsize=9); a.set_xticks(yrs); a.tick_params(axis='x', labelsize=7); a.set_ylabel('log, relative to median program')
    for r, keys, hdr in [(0, segs, 'Stated segment'), (1, cls, 'ANSWER KEY cluster')]:
        for j, k in enumerate(keys):
            b = fig.add_subplot(gs[r, j + 2]); b.imshow(bl(sm[k]), origin='lower', aspect='auto', extent=ext, cmap=CM, norm=PowerNorm(.6))
            nm = k.split(":",1)[1].replace('_',' '); nm = nm if len(nm) < 26 else nm[:24] + '…'
            b.set_title(f'{hdr}\n{nm}', loc='left', fontsize=7.5); b.set_xticks([yrs[0], yrs[-1]]); b.tick_params(labelsize=6.5)
            if j: b.set_yticklabels([])
    tag(fig); fig.savefig(F + f'm2_residual_{firm.split("_")[0].lower()}.png'); plt.close(fig)
# ---------- m2_startstop (MS): gap-safe DenseLines + live strip + entrants layer
a0 = A['MorganStanley_mock']; yrs = m2['MorganStanley_mock']['years']; ext = [yrs[0], yrs[-1], a0['lo'], a0['hi']]
fig = plt.figure(figsize=(13, 5.2)); gs = fig.add_gridspec(2, 2, height_ratios=[4, 1])
a = fig.add_subplot(gs[0, 0]); a.imshow(bl(a0['Dn']), origin='lower', aspect='auto', extent=ext, cmap=CM, norm=PowerNorm(.6)); a.set_title('All 1,765 programs, gap-safe DenseLines (reference code: every column NaN)', loc='left', fontsize=9); a.set_xticks(yrs)
b = fig.add_subplot(gs[0, 1]); E = a0['Dent']; b.imshow(a0['Dn'] / a0['Dn'].max(), origin='lower', aspect='auto', extent=ext, cmap=LinearSegmentedColormap.from_list('g', ['#ffffff', '#cfc8bb']), norm=PowerNorm(.45))
Em = np.ma.masked_where(E <= 0, E); b.imshow(Em, origin='lower', aspect='auto', extent=ext, cmap=LinearSegmentedColormap.from_list('e', ['#f6c58f', AMB, RED]), norm=PowerNorm(.45), alpha=.95)
b.set_title(f'Entrants only ({int(a0["ent"].sum())} programs that start after {yrs[0]}), over all programs in grey', loc='left', fontsize=9); b.set_xticks(yrs)
c = fig.add_subplot(gs[1, 0]); xx = np.linspace(yrs[0], yrs[-1], W); c.fill_between(xx, a0['live'], color=TEAL, alpha=.6); c.set_ylabel('live programs'); c.set_ylim(a0['live'].min() * .97, a0['live'].max() * 1.01); c.set_xticks(yrs)
d = fig.add_subplot(gs[1, 1]); d.fill_between(xx, gaussian_filter1d(E.sum(0), 1), color=AMB, alpha=.7); d.set_ylabel('entrant weight'); d.set_xticks(yrs)
tag(fig); fig.savefig(F + 'm2_startstop.png'); plt.close(fig)
# ---------- m2_parity: speed bars
fig, ax = plt.subplots(1, 2, figsize=(10, 3.4)); P = par['parity']
ax[0].bar(range(len(P)), [p['max_rel_diff'] for p in P], color=TEAL); ax[0].set_xticks(range(len(P))); ax[0].set_xticklabels([f'{p["n"]:,} series' for p in P]); ax[0].set_ylabel('max relative difference'); ax[0].set_yscale('log'); ax[0].set_ylim(1e-8, 1e-5)
ax[0].set_title('NumPy port vs authors\u2019 Rust:\nidentical pixels, float32 rounding only', loc='left', fontsize=9)
for i, p in enumerate(P): ax[0].text(i, p['max_rel_diff'] * 1.3, f'{p["max_rel_diff"]:.1e}', ha='center', fontsize=7)
S = [s for s in par['speed'] if 'numpy_s' in s] + [p for p in P]; S = sorted({s['n']: s for s in S}.values(), key=lambda s: s['n'])
x = np.arange(len(S)); ax[1].bar(x - .2, [s['rust_compute_s'] for s in S], .4, color=INK, label='Rust reference (8 threads)'); ax[1].bar(x + .2, [s['numpy_s'] for s in S], .4, color=AMB, label='NumPy port (1 thread)')
ax[1].set_yscale('log'); ax[1].set_xticks(x); ax[1].set_xticklabels([f'{s["n"]:,}' for s in S]); ax[1].set_xlabel('series (400 points each, 400×300 canvas)'); ax[1].set_ylabel('seconds'); ax[1].legend(fontsize=7, frameon=False)
ax[1].set_title('Speed: the port is correct\nbut 10–120× slower', loc='left', fontsize=9)
fig.savefig(F + 'm2_parity.png'); plt.close(fig)
print('ok')
