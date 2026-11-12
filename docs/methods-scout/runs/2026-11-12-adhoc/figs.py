#!/usr/bin/env python3
"""Figures for 2026-11-12 ad hoc methods scout. Colors follow the 11-11 brief style."""
import json, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
from matplotlib.colors import TwoSlopeNorm
import matplotlib.ticker as mticker

plt.rcParams.update({
    'font.size': 9,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi': 140,
    'savefig.bbox': 'tight',
    'savefig.facecolor': 'white',
    'axes.labelcolor': '#1c150d',
    'text.color': '#1c150d',
    'axes.edgecolor': '#1c150d',
    'xtick.color': '#1c150d',
    'ytick.color': '#1c150d',
})
INK = '#1c150d'
AC = ['#e8902e', '#1f9e8e', '#54b441', '#df5236', '#3b6fb6', '#8a5a9e',
      '#c47b2b', '#5a8f7b', '#777777', '#b4536a', '#4a7c9b', '#8b6b3d',
      '#6b7c3a', '#7a5c8e']
F = '/workspace/scout/1112-adhoc/fig/'
os.makedirs(F, exist_ok=True)

m1 = json.load(open('/workspace/scout/1112-adhoc/out/m1_results.json'))
m2 = json.load(open('/workspace/scout/1112-adhoc/out/m2_results.json'))

# patch turnover in a copy used for captions (will also rewrite JSON)
m1['A']['turnover_mean'] = {'total': 0.0, 'appearance': 0.0, 'disappearance': 0.0,
                            'note': 'Closed balanced panel: all dealers present every quarter; turnover is identically 0. An earlier draft averaged the time index (a column-order bug) and is discarded.'}
m1['E4']['turnover_mean'] = dict(m1['A']['turnover_mean'])

def ticks(ax, labels, step=4, rotation=45):
    ax.set_xticks(range(0, len(labels), step))
    ax.set_xticklabels([labels[i] for i in range(0, len(labels), step)],
                       rotation=rotation, ha='right')

def save(fig, name):
    fig.tight_layout()
    fig.savefig(F + name, dpi=140)
    plt.close(fig)
    print('wrote', name)

# =====================================================================
# m1: rank clocks next to standard share lines  (THE visual)
# =====================================================================
def rank_clock(ax, shares, labels, names, colors, title, start_year_label=True):
    """Polar clock: time starts at 12 o'clock, runs clockwise; radius = share %."""
    T = len(labels)
    # start at 12 o'clock, clockwise: theta = pi/2 - 2pi * t/T
    # close the loop with a faint last-to-first? NO — that would invent a wrap.
    # Just draw the path t=0..T-1, and mark start/end.
    theta = 0.5 * np.pi - 2 * np.pi * np.arange(T) / T
    for i, s in enumerate(names):
        r = np.array(shares[s]) * 100
        ax.plot(theta, r, color=colors[i], lw=2.0, label=s, solid_capstyle='round')
        ax.scatter(theta[0], r[0], color=colors[i], s=28, zorder=5, edgecolors=INK, lw=0.5)
        ax.scatter(theta[-1], r[-1], color=colors[i], s=36, zorder=5, marker='s', edgecolors=INK, lw=0.5)
    ax.set_theta_offset(0)
    ax.set_theta_direction(-1)  # we already baked clockwise into theta
    # custom angular ticks: quarter labels at a few dates, at 12, 3, 6, 9
    n_marks = 8
    idxs = [int(round(k * (T - 1) / n_marks)) for k in range(n_marks)]
    idxs = sorted(set(idxs))
    ax.set_thetagrids([np.degrees(theta[i]) % 360 for i in idxs],
                      [labels[i] for i in idxs], fontsize=7)
    ax.set_title(title, fontsize=9, pad=12)
    ax.tick_params(axis='y', labelsize=7)
    ax.set_ylim(0, None)

fig = plt.figure(figsize=(11.4, 7.6))
# top: E4 lines + clock
ax1 = fig.add_subplot(2, 2, 1)
labs = m1['E4']['q']
for i, s in enumerate(m1['E4']['share_names']):
    ax1.plot(np.array(m1['E4']['shares'][s]) * 100, color=AC[i], lw=1.9, label=s)
ticks(ax1, labs, 6)
ax1.set_ylabel('% of big-4 trailing-4Q equity trading revenue')
ax1.set_title('Standard plot · PROXY equity-revenue shares (E4)', fontsize=9)
ax1.legend(fontsize=8, loc='upper right')
ax1.axhline(25, color='#ddd', lw=0.6, zorder=0)

ax2 = fig.add_subplot(2, 2, 2, projection='polar')
rank_clock(ax2, m1['E4']['shares'], labs, m1['E4']['share_names'], AC,
           'Rank clock · same data (radius = share %; ● start, ■ end)')
ax2.legend(loc='upper left', bbox_to_anchor=(1.05, 1.05), fontsize=8, frameon=False)
# annotate the GS inward / JPM outward story is visible without text on the clock

# bottom: A lines (selected) + clock of same
ax3 = fig.add_subplot(2, 2, 3)
labsA = m1['A']['q']
# highlight a readable subset, gray the rest
focus = ['JPM', 'GS', 'MS', 'BAC', 'C', 'UBS+CS', 'Mizuho']
# foreign sum
foreign = ['Barclays', 'UBS+CS', 'DB', 'BNP', 'HSBC', 'Mizuho', 'RBC', 'TD']
fsum = np.sum([np.array(m1['A']['shares'][s]) for s in foreign], axis=0) * 100
for i, s in enumerate(m1['A']['share_names']):
    y = np.array(m1['A']['shares'][s]) * 100
    if s in focus:
        ax3.plot(y, color=AC[i], lw=1.7, label=s)
    else:
        ax3.plot(y, color='#cccccc', lw=0.8, zorder=0)
ax3.plot(fsum, color=INK, lw=1.6, ls='--', label='8 foreign IHCs (sum)')
ticks(ax3, labsA, 4)
ax3.set_ylabel('% of 14-dealer trading assets')
ax3.set_title('Standard plot · PROXY trading-asset shares (A); foreign sum dashed', fontsize=9)
ax3.legend(fontsize=6.5, ncol=2, loc='upper right')

ax4 = fig.add_subplot(2, 2, 4, projection='polar')
# clock of the focus dealers plus maybe too crowded; use focus only
focus_colors = [AC[m1['A']['share_names'].index(s)] for s in focus]
rank_clock(ax4, m1['A']['shares'], labsA, focus, focus_colors,
           'Rank clock · selected dealers (radius = share %)')
ax4.legend(loc='upper left', bbox_to_anchor=(1.05, 1.05), fontsize=7, frameon=False)

fig.suptitle('codyn rank clocks (Collins et al. 2008; Hallett et al. 2016) next to the usual line plot  ·  PROXY, not prime brokerage',
             fontsize=10, fontweight='bold', y=1.01)
save(fig, 'm1_rankclocks.png')

# =====================================================================
# m1: rate-of-change (distance vs lag) + VR bars
# =====================================================================
fig, axs = plt.subplots(1, 3, figsize=(11.6, 3.6))

def lag_plot(ax, d, title, color):
    iv = np.array(d['rate_change_interval']['interval'])
    di = np.array(d['rate_change_interval']['distance'])
    lags = np.unique(iv)
    mu = np.array([di[iv == L].mean() for L in lags])
    q25 = np.array([np.quantile(di[iv == L], 0.25) for L in lags])
    q75 = np.array([np.quantile(di[iv == L], 0.75) for L in lags])
    ax.fill_between(lags, q25, q75, color=color, alpha=0.22, lw=0)
    ax.plot(lags, mu, color=color, lw=2.0, label='mean distance at lag')
    # linear fit on all pairs (the official rate_change is this slope)
    # reconstruct intercept from earlier: A 0.0291, E4 0.1164 — compute
    X = np.column_stack([np.ones(len(iv)), iv])
    from numpy.linalg import lstsq
    b, _, _, _ = lstsq(X, di, rcond=None)
    ax.plot(lags, b[0] + b[1] * lags, color=INK, lw=1.2, ls='--',
            label=f'linear (slope {b[1]:.4f}, the official rate)')
    Xs = np.column_stack([np.ones(len(iv)), np.sqrt(iv)])
    bs, _, _, _ = lstsq(Xs, di, rcond=None)
    ax.plot(lags, bs[0] + bs[1] * np.sqrt(lags), color='#777', lw=1.2, ls=':',
            label='√lag (random-walk shape)')
    ax.set_xlabel('time lag (quarters)')
    ax.set_ylabel('Euclidean distance of share vectors')
    ax.set_title(title, fontsize=8.5)
    ax.legend(fontsize=6.2, loc='upper left')

lag_plot(axs[0], m1['A'],
         f"A · rate of community change = {m1['A']['rate_change']:.4f}\n(cyclic-shift null mean {m1['A']['rate_null']['null_mean']:.4f}, p = {m1['A']['rate_null']['p_ge']:.3f})",
         AC[1])
lag_plot(axs[1], m1['E4'],
         f"E4 · rate of community change = {m1['E4']['rate_change']:.4f}\n(cyclic-shift null mean {m1['E4']['rate_null']['null_mean']:.4f}, p = {m1['E4']['rate_null']['p_ge']:.3f})",
         AC[0])

# VR bars
ax = axs[2]
# groups: A full, A US-6, A foreign, A 16-19, A 20-26, E4 full, E4 windows
items = [
    ('A full', m1['A']['vr'], AC[1]),
    ('A US big-6', m1['A']['leaveout']['US_big6_only'], AC[1]),
    ('A foreign 8', m1['A']['leaveout']['foreign_only'], '#aaa'),
    ('A 2016–19', m1['A']['windows']['2016Q3-2019Q4']['vr'], AC[4]),
    ('A 2020–26', m1['A']['windows']['2020Q1-2026Q2']['vr'], AC[4]),
    ('E4 full', m1['E4']['vr'], AC[0]),
    ('E4 2011–15', m1['E4']['windows']['2011Q1-2015Q4']['vr'], AC[3]),
    ('E4 2016–19', m1['E4']['windows']['2016Q1-2019Q4']['vr'], AC[3]),
    ('E4 2020–26', m1['E4']['windows']['2020Q1-2026Q2']['vr'], AC[3]),
]
xs = np.arange(len(items))
for i, (lab, vr, c) in enumerate(items):
    ax.plot([i, i], [vr['lowerCI'], vr['upperCI']], color='#444', lw=1.4, zorder=2)
    ax.scatter([i, i], [vr['lowerCI'], vr['upperCI']], color='#444', s=8, zorder=2)
    ax.bar(i, vr['VR'], color=c, width=0.7, zorder=1, edgecolor=INK, lw=0.5)
    ax.text(i, vr['VR'] + 0.12, f"{vr['VR']:.2f}", ha='center', va='bottom', fontsize=6.5)
ax.axhline(1, color=INK, lw=0.8, ls='--', label='VR = 1 (independent)')
ax.set_xticks(xs)
ax.set_xticklabels([it[0] for it in items], rotation=40, ha='right', fontsize=7)
ax.set_ylabel('variance ratio (raw amounts)')
ax.set_title('Schluter VR vs cyclic-shift 95% null CI\n(VR>1: volumes co-move; whiskers = null CI)', fontsize=8.5)
ax.set_ylim(0, 5.3)
save(fig, 'm1_rate_vr.png')

# =====================================================================
# m2: Pearson vs rho heatmaps (standard plot next to the method) + scatter
# =====================================================================
def heatmap(ax, mat, names, title, vmin=-1, vmax=1):
    norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
    im = ax.imshow(mat, cmap='RdBu_r', norm=norm, aspect='equal')
    ax.set_xticks(range(len(names)))
    ax.set_yticks(range(len(names)))
    fs = 6 if len(names) > 6 else 8
    ax.set_xticklabels(names, rotation=90, fontsize=fs)
    ax.set_yticklabels(names, fontsize=fs)
    ax.set_title(title, fontsize=8.5)
    ax.tick_params(length=0)
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    for i in range(len(names)):
        for j in range(len(names)):
            if i == j:
                continue
            v = mat[i, j]
            ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                    fontsize=4.6 if len(names) > 6 else 7,
                    color='#111' if abs(v) < 0.55 else '#fff')
    return im

fig, axs = plt.subplots(2, 3, figsize=(11.6, 9.2))

# E4 row
namesE = m2['E4']['_mats']['names']
pe = np.array(m2['E4']['_mats']['pearson_share'])
re = np.array(m2['E4']['_mats']['rho_share'])
pp = np.array(m2['E4']['_mats']['rho_partial'])
im = heatmap(axs[0, 0], pe, namesE, 'E4 · standard: Pearson on raw shares')
heatmap(axs[0, 1], re, namesE, 'E4 · Lovell/Quinn ρ on shares  (the method)')
heatmap(axs[0, 2], pp, namesE, 'E4 · market-partial ρ  (CLR residualized on VIX, Nasdaq, spread, industry growth)')

# A row: 14 is dense; still do it, maybe skip numbers for A or use smaller
namesA = m2['A']['_mats']['names']
pa = np.array(m2['A']['_mats']['pearson_share'])
ra = np.array(m2['A']['_mats']['rho_share'])
da = pa - ra
heatmap(axs[1, 0], pa, namesA, 'A · standard: Pearson on raw shares')
heatmap(axs[1, 1], ra, namesA, 'A · Lovell/Quinn ρ on shares')
im2 = heatmap(axs[1, 2], da, namesA, 'A · Pearson − ρ  (where correlation over/understates)',
              vmin=-0.7, vmax=0.7)

for ax in axs.ravel():
    ax.set_anchor('C')
fig.suptitle('Proportionality vs the usual correlation  ·  PROXY shares  ·  ρ is valid on compositions; Pearson is not',
             fontsize=10, fontweight='bold')
fig.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(F + 'm2_heatmaps.png', dpi=140)
plt.close(fig)
print('wrote m2_heatmaps.png')

# scatter Pearson vs rho, plus partial bar for E4
fig, axs = plt.subplots(1, 2, figsize=(11.2, 4.3))
ax = axs[0]
# all A pairs
pts = m2['A']['disagreements']
xs = [d['pearson_share'] for d in pts]
ys = [d['rho_share'] for d in pts]
ax.scatter(xs, ys, s=22, color=AC[1], alpha=0.85, edgecolors=INK, lw=0.3, label='A pairs (14 dealers)', zorder=3)
# E4
ptsE = m2['E4']['disagreements']
xsE = [d['pearson_share'] for d in ptsE]
ysE = [d['rho_share'] for d in ptsE]
ax.scatter(xsE, ysE, s=50, color=AC[0], edgecolors=INK, lw=0.6, label='E4 pairs (big-4 revenue)', zorder=4, marker='D')
ax.plot([-1, 1], [-1, 1], color=INK, lw=0.8, ls='--')
ax.axhline(0, color='#ccc', lw=0.6); ax.axvline(0, color='#ccc', lw=0.6)
# annotate the biggest disagreements
for d in pts:
    if abs(d['delta_pearson_share_minus_rho']) > 0.52:
        ax.annotate(f"{d['a']}–{d['b']}", (d['pearson_share'], d['rho_share']),
                    textcoords='offset points', xytext=(4, 4), fontsize=6)
# JPM-GS
for d in ptsE:
    if {d['a'], d['b']} == {'JPM', 'GS'}:
        ax.annotate('JPM–GS', (d['pearson_share'], d['rho_share']),
                    textcoords='offset points', xytext=(5, -10), fontsize=7, fontweight='bold', color=AC[3])
ax.set_xlabel('Pearson correlation of raw shares (the usual, invalid for compositions)')
ax.set_ylabel('Lovell/Quinn ρ of shares (valid)')
ax.set_xlim(-1.05, 1.05); ax.set_ylim(-1.05, 1.05)
ax.set_aspect('equal')
ax.set_title('Where Pearson overstates association\n(points off the diagonal: same pair, two measures)', fontsize=9)
ax.legend(fontsize=7, loc='upper left')

ax = axs[1]
# E4 raw vs partial, as paired bars
pairs = m2['E4']['pairs_partial']
# keep original order of pairs_rho (sorted by rho) — pairs_partial is sorted by partial
# use a consistent interesting order: by raw rho
pairs = sorted(pairs, key=lambda d: d['rho'])
labs = [f"{d['a']}–{d['b']}" for d in pairs]
x = np.arange(len(pairs))
w = 0.38
ax.bar(x - w/2, [d['rho'] for d in pairs], w, color=AC[1], edgecolor=INK, lw=0.5, label='ρ on shares')
ax.bar(x + w/2, [d['rho_partial'] for d in pairs], w, color=AC[0], edgecolor=INK, lw=0.5,
       label='market-partial ρ')
ax.axhline(0, color=INK, lw=0.7)
for i, d in enumerate(pairs):
    # mark BH-significant partial
    if d['bh_q_part'] <= 0.05:
        ax.scatter([x[i] + w/2], [d['rho_partial'] - 0.06 if d['rho_partial']<0 else d['rho_partial']+0.06],
                   marker='*', s=70, color=AC[3], zorder=5, label='partial survives BH q ≤ 0.05' if i==0 else None)
ax.set_xticks(x)
ax.set_xticklabels(labs, rotation=25, ha='right')
ax.set_ylabel('ρ')
ax.set_ylim(-1.15, 0.4)
ax.set_title('E4 · does anti-proportionality survive removing the market?\nJPM–GS gets stronger (−0.70 → −0.88); JPM–MS shrinks and is no longer significant', fontsize=8.5)
ax.legend(fontsize=7, loc='lower right')
save(fig, 'm2_pearson_partial.png')

print('all figs done', os.listdir(F))
