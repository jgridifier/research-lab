#!/usr/bin/env python3
"""Figures for methods scout 2026-11-12 (scheduled): ecotraj + lphom on PROXY Y-9C panels and FRED stress states."""
import json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 140,
                     'savefig.bbox': 'tight', 'savefig.facecolor': 'white', 'axes.labelcolor': '#1c150d', 'text.color': '#1c150d',
                     'axes.edgecolor': '#1c150d', 'xtick.color': '#1c150d', 'ytick.color': '#1c150d'})
INK = '#1c150d'; AMB = '#e8902e'; TEAL = '#1f9e8e'; RED = '#df5236'; BLUE = '#3b6fb6'; GRN = '#54b441'; GREY = '#9a9389'
AC = ['#e8902e', '#1f9e8e', '#54b441', '#df5236', '#3b6fb6', '#8a5a9e', '#c47b2b', '#5a8f7b', '#777777', '#b4536a', '#4a7c9b', '#8b6b3d', '#6b7c3a', '#7a5c8e']
B = '/workspace/scout/1112/'; F = B + 'fig/'
m1 = json.load(open(B + 'out/m1_results.json')); m1b = json.load(open(B + 'out/m1b_increments.json'))
m2 = json.load(open(B + 'out/m2_results.json')); m2p = json.load(open(B + 'out/m2b_products.json'))
mk = pd.read_csv(B + 'data/market_q.csv', index_col=0)

def shares(p):
    W = pd.read_csv(B + f'data/panel_{p}.csv', index_col=0); return W.div(W.sum(1), axis=0)

# ---- m1_traj: standard stacked area vs ETA trajectory (panel A and E4)
fig, ax = plt.subplots(2, 2, figsize=(11, 8.2), gridspec_kw={'width_ratios': [1, 1.15]})
for r, p in enumerate(['A', 'E4']):
    S = shares(p); q = S.index.tolist(); a = ax[r, 0]
    a.stackplot(range(len(q)), (S.T.values * 100), labels=S.columns, colors=AC[:S.shape[1]], alpha=.9, linewidth=0)
    a.set_xticks(range(0, len(q), 8)); a.set_xticklabels(q[::8]); a.set_ylabel('share, %'); a.set_ylim(0, 100)
    a.set_title(f'Standard plot: stacked shares ({"14 dealers, trading assets" if p=="A" else "big-4 equity trading revenue"})', loc='left', fontsize=9)
    if p == 'E4': a.legend(loc='upper left', ncol=4, fontsize=7, frameon=False)
    else: a.legend(loc='upper left', ncol=5, fontsize=6, frameon=False, bbox_to_anchor=(0, 1.0))
    a = ax[r, 1]; sc = np.array(m1[p]['pca']['scores']); var = m1[p]['pca']['var']
    cm = plt.cm.viridis(np.linspace(0, 1, len(sc)))
    for i in range(len(sc) - 1):
        a.annotate('', xy=sc[i + 1], xytext=sc[i], arrowprops=dict(arrowstyle='-|>', color=cm[i], lw=1.4, mutation_scale=8))
    a.scatter(sc[:, 0], sc[:, 1], c=range(len(sc)), cmap='viridis', s=10, zorder=3)
    for i in [0, len(sc) // 2, len(sc) - 1]: a.annotate(q[i], sc[i], fontsize=7, xytext=(4, 4), textcoords='offset points')
    rot = np.array(m1[p]['pca']['rot']); names = m1[p]['dealers']; sfac = np.abs(sc).max() / np.abs(rot).max() * .55
    top = np.argsort(-np.hypot(rot[:, 0], rot[:, 1]))[:6]
    for j in top:
        a.annotate('', xy=rot[j] * sfac, xytext=(0, 0), arrowprops=dict(arrowstyle='->', color=GREY, lw=.8))
        a.text(*(rot[j] * sfac * 1.08), names[j], color='#5b544b', fontsize=7)
    o = m1[p]
    a.set_title(f'ETA trajectory in Aitchison space (PC1 {var[0]*100:.0f}%, PC2 {var[1]*100:.0f}%)\n'
                f'directionality {o["obs"]["dir"]:.3f}; sign-flip null 95% {o["signflip_dir_q"][0]:.2f}–{o["signflip_dir_q"][2]:.2f} (p={o["p_signflip"]:.3f})', loc='left', fontsize=9)
    a.set_xlabel('PC1 (clr)'); a.set_ylabel('PC2 (clr)')
fig.text(0, -0.01, 'PROXY: FR Y-9C (public), not prime brokerage. Colour runs from first (purple) to last (yellow) quarter. Grey arrows: dealer clr loadings.', fontsize=7.5, color='#5b544b')
plt.tight_layout(); plt.savefig(F + 'm1_traj.png'); plt.close()

# ---- m1_nulls: observed directionality vs nulls
fig, ax = plt.subplots(1, 2, figsize=(11, 3.3))
for a, p in zip(ax, ['A', 'E4']):
    o = m1[p]; sf = np.array(o['nulls_dir']['signflip']); ar = np.array(o['nulls_dir']['ar1'])
    bins = np.linspace(min(sf.min(), ar.min()) - .01, max(sf.max(), ar.max(), o['obs']['dir']) + .02, 50)
    a.hist(sf, bins=bins, color=TEAL, alpha=.6, label=f'sign-flip increments (p={o["p_signflip"]:.3f})')
    a.hist(ar, bins=bins, color=AMB, alpha=.6, label=f'persistence-matched AR(1) (p={o["p_ar1"]:.3f})')
    a.axvline(o['obs']['dir'], color=INK, lw=2); a.text(o['obs']['dir'], a.get_ylim()[1] * .9, f' observed {o["obs"]["dir"]:.3f}', fontsize=8)
    a.set_title(f'{"Panel A (14 dealers, 40 q)" if p=="A" else "Panel E4 (big-4 equity revenue, 62 q)"}; built-in random-order null p={o["p_perm_builtin"]:.3f}', loc='left', fontsize=9)
    a.set_xlabel('De Cáceres directionality'); a.legend(fontsize=7, frameon=False, loc='upper left')
plt.tight_layout(); plt.savefig(F + 'm1_nulls.png'); plt.close()

# ---- m1_market_resid: increments decomposition
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
for a, p in zip(ax, ['A', 'E4']):
    o = m1b[p]; names = list(o['net_total'].keys()); x = np.arange(len(names)); w = .27
    a.bar(x - w, [o['net_total'][n] for n in names], w, color=INK, label='total net clr change')
    a.bar(x, [o['net_market'][n] for n in names], w, color=AMB, label='market-step part')
    a.bar(x + w, [o['net_resid'][n] for n in names], w, color=TEAL, label='residual (sticky) part')
    a.axhline(0, color=INK, lw=.6); a.set_xticks(x); a.set_xticklabels(names, rotation=60 if p == 'A' else 0, fontsize=7)
    s = o['sub']; a.set_title(f'{p}: market steps explain {o["step_energy_market"]*100:.0f}% of step energy; net |Δ|: market {o["norms"][1]:.2f}, residual {o["norms"][2]:.2f}\n'
                              f'directionality market {s["market"]["dir"]:.3f} (p={s["market"]["p_signflip"]:.2f}), residual {s["residual"]["dir"]:.3f} (p={s["residual"]["p_signflip"]:.2f})', loc='left', fontsize=8.5)
    a.set_ylabel('clr units, first→last quarter'); a.legend(fontsize=7, frameon=False)
plt.tight_layout(); plt.savefig(F + 'm1_market_resid.png'); plt.close()

# ---- m1_rolling: window directionality over time vs VIX
fig, ax = plt.subplots(1, 2, figsize=(11, 3.2))
for a, p in zip(ax, ['A', 'E4']):
    W = pd.DataFrame(m1[p]['window']); S = shares(p); q = S.index.tolist()
    mid = W['midpoint'].astype(int).values - 1
    a.plot(mid, W['directionality'], color=TEAL, lw=2, label='9-quarter window directionality')
    a.set_ylim(0, 1); a.set_ylabel('directionality'); a.set_xticks(range(0, len(q), 8)); a.set_xticklabels(q[::8])
    b = a.twinx(); b.plot(range(len(q)), mk.loc[q, 'vix'].values, color=GREY, lw=1, ls='--', label='VIX (quarter mean)'); b.set_ylabel('VIX', color=GREY)
    b.spines['top'].set_visible(False)
    r = np.corrcoef(W['directionality'], mk.loc[[q[i] for i in mid], 'vix'])[0, 1]
    a.set_title(f'{p}: rolling directionality (corr with VIX {r:+.2f})', loc='left', fontsize=9); a.legend(fontsize=7, frameon=False, loc='lower left')
plt.tight_layout(); plt.savefig(F + 'm1_rolling.png'); plt.close()

# ---- m1_episodes
E = m1['episodes']; names = list(E['episodes'].keys()); sc = np.array(E['pca']['scores']); sites = E['pca']['sites']
cl = dict(zip(names, E['cl_dspd'])); ccol = {1: TEAL, 2: AMB, 3: RED}
fig = plt.figure(figsize=(12, 7.6)); g = fig.add_gridspec(2, 3, height_ratios=[1.25, 1])
a = fig.add_subplot(g[0, :2])
for n in names:
    idx = [i for i, s in enumerate(sites) if s == n]; P = sc[idx]
    a.plot(P[:, 0], P[:, 1], '-', color=ccol[cl[n]], lw=1.4, alpha=.9); a.scatter(P[2, 0], P[2, 1], color=ccol[cl[n]], s=18, zorder=3)
    a.annotate('', xy=P[-1], xytext=P[-2], arrowprops=dict(arrowstyle='-|>', color=ccol[cl[n]], lw=1.2))
    pk = np.argmax(np.hypot(P[:, 0], P[:, 1])); a.text(P[pk, 0], P[pk, 1], ' ' + n[:7], fontsize=7, color=ccol[cl[n]])
rot = np.array(E['pca']['rot']); sf = np.abs(sc).max() / np.abs(rot).max() * .35
for j, v in enumerate(E['vars']):
    a.annotate('', xy=rot[j] * sf, xytext=(0, 0), arrowprops=dict(arrowstyle='->', color=GREY, lw=.8)); a.text(*(rot[j] * sf * 1.1), v, fontsize=7, color='#5b544b')
a.set_title(f'Stress episodes as trajectories (onset−2 to onset+12 months), PCA of z-scored states (PC1 {E["pca"]["var"][0]*100:.0f}%)\n'
            'colour = DSPD cluster (teal: snap-back / short; amber: drift-type; red: Lehman alone). Dot = onset month.', loc='left', fontsize=9)
a.set_xlabel('PC1'); a.set_ylabel('PC2')
a = fig.add_subplot(g[0, 2]); Dm = np.array(E['dspd']); Z = linkage(squareform(Dm, checks=False), 'average')
dendrogram(Z, labels=[n[:7] + ' ' + n[8:20] for n in names], orientation='right', ax=a, color_threshold=0, above_threshold_color=INK, leaf_font_size=7)
a.set_title('DSPD dendrogram (average linkage)', loc='left', fontsize=9)
a = fig.add_subplot(g[1, 0]); Zs = pd.read_csv(B + 'data/stress_monthly_z.csv', index_col=0); Zs.index = Zs.index.str[:7]
for n in names:
    k = Zs.index.get_loc(E['episodes'][n]); a.plot(range(-2, 13), Zs['log_vix'].iloc[k - 2:k + 13].values, color=ccol[cl[n]], lw=1, alpha=.8)
a.axvline(0, color=GREY, lw=.6); a.set_title('Standard plot it replaces: overlaid VIX (z) paths', loc='left', fontsize=9); a.set_xlabel('months from onset')
a = fig.add_subplot(g[1, 1]); R = pd.DataFrame(E['recovery']); rc = [c for c in R.columns if c.startswith('ratio')][0]
R['site'] = names; R = R.sort_values(rc)
a.barh(R['site'].str[:22], R[rc], color=[ccol[cl[s]] for s in R['site']]); a.set_xlim(0, 1.05)
a.set_title('End distance ÷ max excursion (1 = never came back)', loc='left', fontsize=9); a.tick_params(axis='y', labelsize=7)
a = fig.add_subplot(g[1, 2]); M = pd.DataFrame(E['metrics']); M['site'] = names
a.scatter(M['length'], M['directionality'], c=[ccol[cl[s]] for s in M['site']], s=30)
for _, r in M.iterrows(): a.text(r['length'], r['directionality'], ' ' + r['site'][:7], fontsize=6.5)
a.set_xlabel('path length'); a.set_ylabel('directionality'); a.set_title('Length vs directionality per episode', loc='left', fontsize=9)
plt.tight_layout(); plt.savefig(F + 'm1_episodes.png'); plt.close()

# ---- m2_flows: E4 transfer matrices (lphom vs LS, halves, annual)
DL = ['JPM', 'GS', 'MS', 'BAC']; a2 = m2['a2']['E4']
mats = [('lphom, all 61 quarter pairs', a2['P']), ('least squares (Lee–Judge–Zellner)', a2['P_ls']), (f'lphom, first half (to {a2["half_split"]})', a2['P_half1']),
        ('lphom, second half', a2['P_half2']), ('lphom, annual non-overlapping steps', a2['P_annual'])]
fig, ax = plt.subplots(1, 5, figsize=(14, 3.1))
for a, (t, P) in zip(ax, mats):
    P = np.array(P) * 100; a.imshow(P, cmap='YlOrBr', vmin=0, vmax=100)
    for i in range(4):
        for j in range(4): a.text(j, i, f'{P[i, j]:.0f}', ha='center', va='center', fontsize=8, color='white' if P[i, j] > 60 else INK)
    a.set_xticks(range(4)); a.set_xticklabels(DL, fontsize=7); a.set_yticks(range(4)); a.set_yticklabels(DL, fontsize=7); a.set_title(t, fontsize=8, loc='left')
ax[0].set_ylabel('from (t−1)'); fig.text(0.5, -0.03, 'to (t) — % of origin share per step; rows sum to 100. PROXY Y-9C big-4 equity trading revenue (T4Q).', ha='center', fontsize=7.5)
plt.tight_layout(); plt.savefig(F + 'm2_flows.png'); plt.close()

# ---- m2_vix: unit-level churn vs VIX + split-null
fig, ax = plt.subplots(1, 3, figsize=(13, 3.4))
for a, p in zip(ax[:2], ['E4', 'A6']):
    b = m2['b2'][p]; a.scatter(b['unit_vix'], np.array(b['unit_flow']) * 100, color=TEAL, s=16)
    a.set_xlabel('VIX (quarter mean, destination quarter)'); a.set_ylabel('share moving off-diagonal, %')
    a.set_title(f'{p}: per-quarter lphom churn vs VIX (Spearman {b["flow_vix_spearman"]:+.2f}, p={b["flow_vix_p"]:.3f})', loc='left', fontsize=8.5)
a = ax[2]; labels = []; 
for k, p in enumerate(['E4', 'A6']):
    b = m2['b2'][p]; a.errorbar([k], [b['null_q'][1] * 100], yerr=[[(b['null_q'][1] - b['null_q'][0]) * 100], [(b['null_q'][2] - b['null_q'][1]) * 100]], fmt='o', color=GREY, capsize=4)
    a.scatter([k], [b['diff'] * 100], color=RED, s=40, zorder=3); a.text(k + .07, b['diff'] * 100, f'p={b["p_two_sided"]:.2f}', fontsize=8)
a.axhline(0, color=INK, lw=.6); a.set_xticks([0, 1]); a.set_xticklabels(['E4', 'A6']); a.set_xlim(-.5, 1.6)
a.set_title('Pooled migration: high-VIX minus low-VIX pairs\n(red = observed, grey = random-split 95% band)', loc='left', fontsize=8.5); a.set_ylabel('pp of share per quarter')
plt.tight_layout(); plt.savefig(F + 'm2_vix.png'); plt.close()

# ---- m2_products + planted
fig, ax = plt.subplots(1, 4, figsize=(14, 3.3), gridspec_kw={'width_ratios': [1, 1, 1, 1.2]})
for a, (t, P) in zip(ax[:3], [(f'products as units: pooled ({m2p["n_units"]} units)', m2p['P']), ('equity units only', m2p['P_equity']), ('non-equity units', m2p['P_nonequity'])]):
    P = np.array(P) * 100; a.imshow(P, cmap='YlOrBr', vmin=0, vmax=100)
    for i in range(4):
        for j in range(4): a.text(j, i, f'{P[i, j]:.0f}', ha='center', va='center', fontsize=8, color='white' if P[i, j] > 60 else INK)
    a.set_xticks(range(4)); a.set_xticklabels(DL, fontsize=7); a.set_yticks(range(4)); a.set_yticklabels(DL, fontsize=7); a.set_title(t, fontsize=8, loc='left')
a = ax[3]; pl = m2['c2']['E4']['planted']
for k, (lab, qq, col) in enumerate([('lphom GS→JPM', pl['lp_gsjpm_q'], TEAL), ('LS GS→JPM', pl['ls_gsjpm_q'], AMB), ('lphom MS→BAC', pl['lp_msbac_q'], TEAL), ('LS MS→BAC', pl['ls_msbac_q'], AMB)]):
    a.errorbar([k], [qq[1] * 100], yerr=[[(qq[1] - qq[0]) * 100], [(qq[2] - qq[1]) * 100]], fmt='o', color=col, capsize=4)
a.axhline(1.0, color=RED, lw=1, ls='--'); a.axhline(0.3, color=BLUE, lw=1, ls=':'); a.text(3.3, 1.0, 'true 1.0', color=RED, fontsize=7); a.text(3.3, .3, 'true 0.3', color=BLUE, fontsize=7)
a.set_xticks(range(4)); a.set_xticklabels(['lphom\nGS→JPM', 'LS\nGS→JPM', 'lphom\nMS→BAC', 'LS\nMS→BAC'], fontsize=7); a.set_ylabel('% per quarter (median, 90% band)')
a.set_title(f'Planted-truth recovery ({pl["n"]} sims, E4 start)', loc='left', fontsize=8.5)
plt.tight_layout(); plt.savefig(F + 'm2_products_planted.png'); plt.close()
print('figs ok')
