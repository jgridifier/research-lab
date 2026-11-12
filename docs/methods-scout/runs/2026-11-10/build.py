import json, math, html, shutil, os
O='/workspace/scout/out/'; S='/workspace/scout/site/methods-scout/'
os.makedirs(S+'fig/2026-11-10',exist_ok=True)
for f in ['m1_ctree_regimes.png','m1_mob_lmtree.png','m1_county_gr.png','m1_county_cv.png','m2_weekly_breaks.png','m2_daily_breaks.png','m2_scaling.png','m2_levels_artifact.png']:
    shutil.copy('/workspace/scout/fig/'+f, S+'fig/2026-11-10/'+f)
a=json.load(open(O+'m1_results.json')); b=json.load(open(O+'m2_results.json'))
e=html.escape
def f2(x,n=2): return 'n/a' if x is None or x=='NA' else f'{float(x):.{n}f}'
def tbl(head, rows, num=()):
    h=''.join(f'<th class="num">{e(c)}</th>' if i in num else f'<th>{e(c)}</th>' for i,c in enumerate(head))
    r=''.join('<tr>'+''.join(f'<td class="num">{c}</td>' if i in num else f'<td>{c}</td>' for i,c in enumerate(row))+'</tr>' for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{h}</tr></thead><tbody>{r}</tbody></table></div>'
def rule_fmt(r):
    import re
    def rep(m):
        v=float(m.group(2)); var=m.group(1)
        if var.startswith('log_lf'): return f'{"labour force 2007" if var.endswith("07") else "labour force 2019"} {m.group(3)} {math.exp(v):,.0f}'.replace('{','')
        return f'{var} {m.group(3)} {v:.3g}'
    out=[]
    for part in r.split(' & '):
        toks=part.split(' ')
        var,op,val=toks[0],toks[1],float(toks[2])
        if var.startswith('log_lf'): out.append(f'labour force {"2007" if var.endswith("07") else "2019"} {op} {math.exp(val):,.0f}')
        else: out.append(f'{var} {op} {val:.3g}')
    return ' &amp; '.join(e(x).replace('&lt;=','≤').replace('&gt;','>') for x in out)
wf=a['A1_walkforward']
# ---------- Method 1 tables
A1=tbl(['Leaf (regime)','Months','Mean 6-mo change in GZ spread (pp)','SD','Share widening > 50bp','First','Last'],
  [[rule_fmt(l['rule']),l['n'],f2(l['mean_fwd6']),f2(l['sd_fwd6']),f"{100*l['p_widen_gt50bp']:.0f}%",l['first'][:7],l['last'][:7]] for l in sorted(a['A1_leaves'],key=lambda l:l['mean_fwd6'])],num=(1,2,3,4))
WF=tbl(['Model','OOS R² vs expanding mean','MAE (pp)','Corr(pred, actual)'],
  [[m,f2(wf[k][0]),f2(wf[k][1],3),f2(wf[k][2])] for m,k in [('ctree (α=0.05, depth≤3, minbucket 24)','ctree'),('CART (rpart, CV-pruned)','cart'),('OLS, same 8 features','ols'),('Expanding historical mean','hist_mean')]],num=(1,2,3))
ERA=tbl(['Era','Months','ctree','CART','OLS'],[[r['era'],r['n'],f2(r['ctree']),f2(r['cart']),f2(r['ols'])] for r in a['A1_by_era']],num=(1,2,3,4))
WIN=tbl(['Training window','Months','Root split','Threshold','Leaves'],[[w['window'],w['n'],w['root_var'],w['root_thr'],w['leaves']] for w in a['A2_windows']],num=(1,3,4))
bt=a['A2_boot_thr_by_var']
BOOT=tbl(['Root variable','Share of 300 block-bootstrap refits','Threshold p10 / p50 / p90'],
  [[k,f"{100*v:.1f}%",(' / '.join(str(x) for x in bt.get(k,[])) if k!='(none)' else '—')] for k,v in a['A2_boot_root_freq'].items()],num=(1,))
rt=a['A3_root_tests']; pv=['T10Y2Y','NFCI','DGS2','time']
MOBT=tbl(['Partition variable','Fluctuation statistic','p-value (Bonferroni)'],[[pv[i],f2(rt[0][i]),('&lt; 0.00001' if rt[1][i]<1e-5 else f2(rt[1][i],3))] for i in range(4)],num=(1,2))
pl=a['A3_pooled']
MOBL=tbl(['Regime','Months','Intercept','β on ΔVIX','β on Δ10y yield'],
  [['Pooled OLS (no split)',a['A3_n'],f2(pl[0],4),f2(pl[1],4),f2(pl[2],4)]]+[[rule_fmt(l['rule']),l['n'],f2(l['X.Intercept.'],4),f2(l['dVIX'],4),f2(l['dDGS10'],4)] for l in a['A3_leaves']],num=(1,2,3,4))
def cleaves(k): return tbl(['Leaf','Counties','Mean Δ unemployment rate (pp)','SD'],[[rule_fmt(l['rule']),l['n'],f2(l['mean_shock']),f2(l['sd'])] for l in sorted(a[k],key=lambda l:l['mean_shock'])],num=(1,2,3))
def cv(k): c=a[k]; return tbl(['Model','5-fold CV RMSE (pp)','CV R²'],[[m,f2(c['rmse'][i],3),f2(c['R2'][i],3)] for i,m in enumerate(['Mean','ctree','CART','OLS'])],num=(1,2))
tm=a['A4_timing']
# ---------- Method 2 tables
segs=b['B1_segments']
top=sorted(segs,key=lambda s:-s['sd_dlogVIX'])[:5]
SEGT=tbl(['Segment','Weeks','SD Δlog VIX','SD Δ2y (pp)','SD ΔNFCI','Corr(ΔVIX, Δ2y)','Avg VIX','Avg NFCI'],
  [[f"{s['start']} → {s['end']}",s['weeks'],f2(s['sd_dlogVIX'],3),f2(s['sd_dDGS2'],3),f2(s['sd_dNFCI'],3),f2(s['corr_dVIX_dDGS2']),f2(s['VIX_level'],1),f2(s['NFCI_level'])] for s in segs],num=(1,2,3,4,5,6,7))
corrs=[s['corr_dVIX_dDGS2'] for s in segs]
sr=b['B2_seed_reproduce']; core=[k for k,v in sr.items() if v>=0.8]
dm=b['B2_dropone_match']; core2=[k for k in core if dm[k]>=0.8]
ROB=tbl(['Check','Result'],[
 ['Breaks found (random forest, default control)',str(len(b['B1_rf_cps']))],
 ['Break count over 10 seeds',', '.join(map(str,b['B2_seed_ncp']))],
 ['Breaks reproduced (±13 weeks) in ≥ 8 of 10 seeds',f"{len(core)} of {len(sr)}"],
 ['…and in ≥ 5 of 6 drop-one-series refits',f"{len(core2)} of {len(sr)}"],
 ['Fit on first 70% only: breaks found / share of full-sample breaks reproduced',f"{b['B2_first70_ncp']} / {100*b['B2_first70_match']:.0f}%"],
 ['kNN classifier instead of random forest',f"{len(b['B2_knn_cps'])} breaks (mostly 2008–12 and 2022–23)"],
 ['change_in_mean (parametric baseline)',f"{len(b['B2_cim_cps'])} breaks"],
 ['Binary segmentation, RBF kernel, same break count: share of RF breaks matched',f"{100*b['B2_rf_vs_binseg_rbf_match']:.0f}%"],
 ['Binary segmentation, L2 (mean), same break count: share matched',f"{100*b['B2_rf_vs_binseg_l2_match']:.0f}%"],
 ['k-means on rows, k = segments: label switches over time',f"{b['B2_kmeans_label_switches']} (vs {b['B2_cf_switches']} for changeforest)"],
 ['Row-shuffled weekly data (no true break), 5 runs',', '.join(map(str,b['B2_shuffled_weekly_ncp']))+' breaks'],
 ['Row-shuffled daily data, 3 runs',', '.join(map(str,b['B3_shuffled_daily_ncp']))+' breaks'],
])
sc=b['B3_scaling']
SCT=tbl(['n (5 dims)','random_forest (s)','RF breaks','knn (s)','knn breaks','ruptures PELT-RBF (s)'],
  [[r['n'],f2(r['random_forest'],3),', '.join(map(str,r.get('random_forest_cps',[]))),f2(r.get('knn'),3) if r.get('knn') is not None else 'not run',(str(len(r['knn_cps'])) if 'knn_cps' in r else '—'),f2(r.get('pelt_rbf'),1) if r.get('pelt_rbf') is not None else 'not run'] for r in sc],num=(0,1,3,4,5))
dsegs=b['B3_segments']
DS=tbl(['Segment','Days','SD Δ10y (pp)','SD Δlog VIX','Corr(Δlog VIX, Δ10y)'],[[f"{s['start']} → {s['end']}",s['days'],f2(s['sd_dDGS10'],3),f2(s['sd_dlogVIX'],3),f2(s['corr_dVIX_dDGS10'])] for s in dsegs],num=(1,2,3,4))
pos=[s for s in dsegs if s['corr_dVIX_dDGS10']>0.1]
lev=b['B0_levels_artifact']
KATEX='''<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'\\\\(',right:'\\\\)',display:false}]})"></script>'''
FONTS='<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400..500&family=JetBrains+Mono:wght@400;500;700&display=swap">'
ICONS='''<!-- Methods Scout home-screen / PWA tags. Paste into <head> of every methods-scout page.
     Paths are root-absolute so they resolve under https://jgridifier.github.io/research-lab/. -->
<link rel="apple-touch-icon" sizes="180x180" href="/research-lab/methods-scout/icons/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="/research-lab/methods-scout/icons/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="/research-lab/methods-scout/icons/icon-192.png">
<link rel="manifest" href="/research-lab/methods-scout/manifest.webmanifest">
<meta name="apple-mobile-web-app-title" content="Methods Scout">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#0F2A23">
'''
FIG='fig/2026-11-10/'
gr_root=a['A4_gr_root']; cvl=sorted(a['A4_cv_leaves'],key=lambda l:l['mean_shock'])
page=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Methods scout · 2026-11-10 · research-lab</title>
<meta name="description" content="Daily methods scout: partykit conditional-inference and model-based trees, and changeforest random-forest change-point detection, each run on Drive data.">
{FONTS}
<link rel="stylesheet" href="../assets/brief.css">
{KATEX}
{ICONS}</head><body><main>
<header class="mast">
  <div class="date">Tuesday · November 10, 2026 · first edition</div>
  <h1>Methods scout</h1>
  <p class="dek">Two lesser-known, fast, interpretable methods, each run three-plus ways on our own data. No neural nets.</p>
  <nav><a href="index.html">All editions</a><a href="https://github.com/jgridifier/research-lab/blob/main/docs/methods-scout/watchlist.md">Watchlist</a><a href="../index.html">Research lab home</a></nav>
</header>

<div class="ticker"><span><b>●</b> ctree's regime splits did not forecast credit spreads out of sample (OOS R² −0.31)</span><span><b>●</b> MOB: the VIX→spread link roughly doubles when NFCI &gt; 0.06, and calendar time stops mattering (p = 0.83)</span><span><b>●</b> changeforest: 0 mean breaks but {len(b['B1_rf_cps'])} distribution breaks in weekly changes, and zero false breaks on shuffled data</span><span><b>●</b> Rust core: 9,174 × 4 daily panel segmented in {b['B3_rf_secs']:.1f}s</span></div>

<section class="tldr">
<h2>The short version</h2>
<ul>
<li><strong>partykit · ctree + MOB</strong> <span class="verdict adopt">adopt-candidate</span>. The trees are as readable as promised and very fast (300 bootstrap refits in {a['A2_boot_secs']:.1f}s). The best result is the MOB tree: one NFCI split explains the changing sensitivity of credit spreads to VIX shocks better than a calendar break does. As a <em>forecaster</em> of 6-month spread changes, ctree lost to the plain historical mean, but less badly than CART or OLS.</li>
<li><strong>changeforest (Rust, Python and R bindings)</strong> <span class="verdict interesting">interesting</span>. It finds breaks in volatility and correlation that a mean-change method misses entirely, returns zero breaks on shuffled data, and scales close to linearly (16k rows in {sc[-1]['random_forest']:.1f}s). But it assumes independent rows within a segment. On persistent <em>levels</em> it produced {lev['n_cps']} breaks spaced ~{lev['median_gap_weeks']:.0f} weeks apart, which is an artifact, and even on changes the break count moves between {min(b['B2_seed_ncp'])} and {max(b['B2_seed_ncp'])} across seeds.</li>
</ul>
<p class="meta">Data used: Drive FRED series VIXCLS, T10Y2Y, DGS2, DGS10, MORTGAGE30US, NFCI, STLFSI4; ebp_monthly.csv (GZ spread and excess bond premium); and the "County econ panel" Sheet. Only aggregates, fitted structure and charts are shown here, never raw rows. Scripts and full JSON outputs are under <code>docs/methods-scout/runs/2026-11-10/</code>.</p>
</section>

<!-- ================= METHOD 1 ================= -->
<div class="sec-head"><span class="n">Method 01</span><h2>partykit: conditional inference trees + model-based recursive partitioning</h2><span class="line"></span></div>

<div class="card teal">
<div class="card-top"><span class="tag teal">R · CRAN · C core</span><span class="verdict adopt">adopt-candidate</span></div>
<p><strong>Citations.</strong> Hothorn, Hornik &amp; Zeileis (2006), "Unbiased Recursive Partitioning: A Conditional Inference Framework", <em>JCGS</em> 15(3):651–674. Zeileis, Hothorn &amp; Hornik (2008), "Model-Based Recursive Partitioning", <em>JCGS</em> 17(2):492–514. Hothorn &amp; Zeileis (2015), "partykit: A Modular Toolkit for Recursive Partytioning in R", <em>JMLR</em> 16:3905–3909. Package: <a href="https://cran.r-project.org/package=partykit">cran.r-project.org/package=partykit</a> (v{a['versions']['partykit']}; small Innsbruck/Zurich team; linear statistics computed in C via <code>libcoin</code>).</p>
<p><strong>Why it's unusual.</strong> CART picks the split variable by greedy impurity reduction, which favours variables with many possible cut points. ctree separates <em>variable selection</em> from <em>cut-point search</em> and does the selection with a permutation test, so it has a built-in stopping rule (no pruning) and isn't biased toward continuous variables. MOB goes further: every node holds a small parametric model, here a regression, and a node splits only when that model's coefficients are statistically unstable along some partitioning variable. That turns a tree into an interpretable map of <em>where a relationship changes</em>.</p>
</div>

<h3>The math in plain terms</h3>
<p>For each candidate covariate \\(X_j\\), ctree computes a linear association statistic with the response, using influence functions \\(h\\) and transformations \\(g\\):</p>
<div class="math-block">$$T_j=\\operatorname{{vec}}\\Big(\\sum_{{i=1}}^n g_j(X_{{ij}})\\,h(Y_i)^\\top\\Big),\\qquad c_j=(T_j-\\mu_j)^\\top\\Sigma_j^{{+}}(T_j-\\mu_j)\\;\\dot\\sim\\;\\chi^2_{{\\mathrm{{rank}}(\\Sigma_j)}}$$</div>
<p>Here \\(\\mu_j\\) and \\(\\Sigma_j\\) are the exact mean and covariance under permutation (Strasser–Weber). It picks the variable with the smallest Bonferroni-adjusted p-value and stops when none is below \\(\\alpha\\). Only then does it search for the best binary cut in that one variable. MOB fits \\(y=x^\\top\\beta\\) in a node, orders the score contributions \\(\\psi(y_i,x_i,\\hat\\beta)\\) by each partition variable \\(z_j\\), and tests the cumulative score process for parameter instability (an M-fluctuation test). It splits on the most unstable \\(z_j\\).</p>

<h3>Analysis 1a · Credit-stress regime tree, and does it forecast?</h3>
<p>Monthly panel from {a['A1_sample']['start'][:7]} to {a['A1_sample']['end'][:7]} ({a['A1_sample']['n']} months). Target: the change in the Gilchrist–Zakrajšek (GZ) credit spread over the <em>next</em> 6 months. Features observed at month end: VIX, 10y–2y slope, NFCI, 2y yield, 12-month change in the 2y, excess bond premium, 12-month change in the mortgage rate, and the past 3-month GZ change. A full-sample fit takes {a['A1_fit_secs']*1000:.0f} ms.</p>
<figure><img src="{FIG}m1_ctree_regimes.png" alt="ctree regime tree"><figcaption>Full-sample ctree (α = 0.05, minbucket 24, depth ≤ 3). Boxplots show the 6-month-ahead GZ spread change in each regime.</figcaption></figure>
{A1}
<p><strong>What it shows.</strong> The root split is VIX ≈ 32. Above it, spreads <em>tighten</em> by about 1.4pp over the next 6 months: after a panic, they mean-revert. The dangerous regime is calm VIX with NFCI already above about −0.06. That's 25 months, all between 1991 and 2009, with a +0.92pp average widening and a 56% chance of more than 50bp. The ZIRP leaf (2y yield ≤ 0.38) is the steady-tightening era.</p>
<p><strong>Walk-forward test.</strong> Refit every 12 months from 2004 onward, training only on rows whose 6-month target was fully observed at refit time ({wf['n_oos']} out-of-sample months).</p>
{WF}
{ERA}
<p>None of the models beats the expanding mean overall. Overlapping 6-month targets and very few stress episodes make this a hard target, and that is the honest answer. ctree degrades least, and it is the only model with a positive OOS R² in 2020–26 ({f2(a['A1_by_era'][2]['ctree'])}), where CART and OLS overfit badly. The tree is useful as a description of regimes, not as a spread forecaster.</p>

<h3>Analysis 1b · Are the regimes stable?</h3>
{WIN}
{BOOT}
<p>On the full sample and on post-2008 data, VIX is the root. Before 2008 the slope (10y–2y ≤ 2.03) is the root. In 300 moving-block bootstrap refits (24-month blocks), VIX is the root {100*a['A2_boot_root_freq']['VIXCLS']:.0f}% of the time, with the cut between {bt['VIXCLS'][0]} and {bt['VIXCLS'][2]} (p10–p90). So the "VIX ≈ 30" boundary is robust and the deeper splits are not. All 300 refits took {a['A2_boot_secs']:.1f}s, which makes this kind of stability check cheap enough to run every night.</p>

<h3>Analysis 1c · MOB: where does the spread-to-VIX link change?</h3>
<p>Model in each node: \\(\\Delta GZ_t=\\beta_0+\\beta_1\\,\\Delta VIX_t+\\beta_2\\,\\Delta y^{{10}}_t+\\varepsilon_t\\). Candidate partition variables: slope, NFCI, the 2y level, and <em>calendar time</em>, so a plain structural break gets a fair chance. Settings: α = 0.01, min 36 months, {a['A3_n']} months, fitted in {a['A3_fit_secs']*1000:.0f} ms.</p>
<figure><img src="{FIG}m1_mob_lmtree.png" alt="MOB lmtree"><figcaption>lmtree with one split, on NFCI. Each leaf panel shows its own regression.</figcaption></figure>
{MOBL}
{MOBT}
<p><strong>What it shows.</strong> Once financial conditions are tight (NFCI &gt; 0.057, 36 months), credit spreads respond about twice as strongly to VIX shocks (β {f2(a['A3_leaves'][0]['dVIX'],3)} → {f2(a['A3_leaves'][1]['dVIX'],3)}), and about 3.5× as strongly, with negative sign, to 10y yield moves: the flight-to-quality channel. The instability test rejects strongly for NFCI and not for calendar time (p = {f2(rt[1][3],2)}). So the relationship shifts with financial conditions, not with era. BIC improves from {f2(a['A3_BIC'][0],0)} to {f2(a['A3_BIC'][1],0)}. Caveat: this is contemporaneous and descriptive, not a forecast.</p>

<h3>Analysis 1d · Cross-section: which counties took the biggest unemployment shocks?</h3>
<p>County panel (Drive Sheet), {a['A4_gr_cv']['n']:,} counties with complete data. Two shocks: Great Recession (unemployment rate 2010 minus 2007) and COVID (2020 minus 2019). Pre-shock covariates: unemployment rate, 6-year GDP growth, rural–urban code, metro flag, share with a bachelor's degree, and log labour force.</p>
<div class="grid">
<figure><img src="{FIG}m1_county_gr.png" alt="Great Recession county tree"><figcaption>Great Recession shock, ctree (α = 0.01, depth ≤ 3).</figcaption></figure>
<figure><img src="{FIG}m1_county_cv.png" alt="COVID county tree"><figcaption>COVID shock, same settings.</figcaption></figure>
</div>
<h4>Great Recession, 2007→2010</h4>
{cleaves('A4_gr_leaves')}
{cv('A4_gr_cv')}
<h4>COVID, 2019→2020</h4>
{cleaves('A4_cv_leaves')}
{cv('A4_cv_cv')}
<p><strong>What it shows.</strong> The two shocks have different shapes. The Great Recession tree splits first on pre-shock unemployment (≤ {gr_root[1]}%), then on education and size. The worst group is already-weak, low-degree-share counties (+5.5pp). The COVID tree splits <em>only</em> on county size: the largest counties (labour force above about 426k) rose {cvl[-1]['mean_shock']}pp against {cvl[0]['mean_shock']}pp in the smallest low-unemployment ones. In 5-fold CV the tree is within 0.02–0.04 R² of OLS (OLS wins narrowly), so you trade a little accuracy for a breakdown you can read at a glance.</p>
<p><strong>Timing</strong> on {tm['rows']:,} rows (county table replicated 10×): ctree {tm['ctree']:.2f}s, rpart {tm['rpart']:.2f}s, lmtree {tm['lmtree']:.1f}s. Caveat: rpart was grown to cp = 0.001 and ctree to depth 3, so this is not a like-for-like race. MOB is the slow part because it refits a model at every candidate node.</p>

<div class="card dark"><h4>Limitations</h4><ul>
<li>Time-series rows are serially dependent, but the permutation tests assume exchangeable rows, so p-values on monthly data are optimistic. Use the block bootstrap (1b) as the real stability check.</li>
<li>Single trees are high-variance below the root. Report root splits and bootstrap frequencies, not deep leaves.</li>
<li>Regime trees describe the data. They did not forecast 6-month spread changes out of sample.</li>
</ul>
<p><strong>Verdict: adopt-candidate.</strong> Use MOB as the default "where does this relationship change?" tool on our panels, with a block-bootstrap stability table attached. It's also a natural interpretable comparison for any regime claim.</p></div>

<!-- ================= METHOD 2 ================= -->
<div class="sec-head"><span class="n">Method 02</span><h2>changeforest: random-forest change-point detection (Rust core)</h2><span class="line"></span></div>
<div class="card">
<div class="card-top"><span class="tag">Rust crate · PyPI · conda-forge R</span><span class="verdict interesting">interesting</span></div>
<p><strong>Citation.</strong> Londschien, Bühlmann &amp; Kovács (2023), "Random Forests for Change Point Detection", <em>JMLR</em> 24(216):1–45. Code: <a href="https://github.com/mlondschien/changeforest">github.com/mlondschien/changeforest</a>, <a href="https://crates.io/crates/changeforest">crates.io/crates/changeforest</a>, <a href="https://pypi.org/project/changeforest/">PyPI</a> (v{b['versions']['changeforest']}; essentially a single-maintainer Rust crate with thin Python and R bindings, which is the same architecture TRACE uses).</p>
<p><strong>Why it's unusual.</strong> Most change-point tools assume a parametric segment model (a mean or variance shift) or rely on distances and ranks that break down as dimension grows. changeforest turns change-point detection into classification. If a random forest can tell "before \\(s\\)" from "after \\(s\\)" better than chance, there is a break at \\(s\\). Any distributional change counts, including a change in correlation, with no parametric assumption.</p>
</div>
<h3>The math in plain terms</h3>
<p>For a segment \\((u,v]\\) and a candidate split \\(s\\), fit a classifier labelling rows as left or right of \\(s\\), and take the out-of-bag probabilities \\(\\hat p_i\\) that row \\(i\\) is on the left. The classifier log-likelihood-ratio gain is</p>
<div class="math-block">$$G(s)=\\sum_{{i=u+1}}^{{s}}\\log\\frac{{\\hat p_i\\,(v-u)}}{{s-u}}+\\sum_{{i=s+1}}^{{v}}\\log\\frac{{(1-\\hat p_i)\\,(v-u)}}{{v-s}}$$</div>
<p>The gain is about 0 when the forest can't beat the class prior. Rather than refitting at every \\(s\\), it fits at the ¼, ½ and ¾ points, reads approximate gain curves off those three fits, and refits once at the best guess. That's why it's fast: roughly O(n log n) per segment times a constant number of forests. Segments are found by (seeded) binary segmentation, and each split is kept only if a permutation test on the gain passes.</p>

<h3>Analysis 2a · Weekly regime segmentation (6 series, 1994–2026)</h3>
<p>Weekly changes in log VIX, the 10y–2y slope, the 2y yield, the 30y mortgage rate, NFCI and STLFSI4: {b['B1_n']:,} weeks × 6, z-scored, segmented in {b['B1_rf_secs']:.2f}s.</p>
<figure><img src="{FIG}m2_weekly_breaks.png" alt="weekly breaks"><figcaption>Red lines: changeforest breaks found on weekly changes, drawn over the levels for context.</figcaption></figure>
<details><summary>All {len(segs)} segments (volatility, correlation and average level)</summary>{SEGT}</details>
<p><strong>What it shows.</strong> The breaks are in volatility and co-movement, not in means: <code>change_in_mean</code> finds {len(b['B2_cim_cps'])} breaks on the same data. The highest-volatility segments are the ones you'd expect (2007-07 → 2008-12, 2019-12 → 2020-06, 2022-01 → 2023-03), but the stock–rate correlation is the more useful output. The correlation between VIX changes and 2y changes ranges from {min(corrs):+.2f} to {max(corrs):+.2f} across segments. It is strongly negative in risk-off windows (bad news means lower yields) and near zero or positive from 2022-01 onward, when inflation made rates and risk sell off together. That is the textbook stock–bond correlation flip, recovered without supervision from six public series.</p>

<h3>Analysis 2b · How robust are the breaks? Comparison with baselines</h3>
{ROB}
<p><strong>What it shows.</strong> On shuffled data, where no break exists, it finds zero breaks every time, so the permutation test isn't trigger-happy under independence. But the exact break count is seed-dependent ({min(b['B2_seed_ncp'])}–{max(b['B2_seed_ncp'])}). Only {len(core)} of {len(sr)} breaks reproduce in at least 8 of 10 seeds, and {len(core2)} also survive dropping any one series. Those {len(core2)} are the ones to trust. k-means on the same rows flips label {b['B2_kmeans_label_switches']} times, so it produces noise rather than regimes, which is why a segmentation method is the right tool here. Kernel binary segmentation agrees on about {100*b['B2_rf_vs_binseg_rbf_match']:.0f}% of breaks at the same count, but it needs the count supplied, while changeforest chooses it.</p>
<figure><img src="{FIG}m2_levels_artifact.png" alt="levels artifact"><figcaption>Failure mode, kept on purpose: run on persistent <em>levels</em>, changeforest returned {lev['n_cps']} breaks with gaps of {lev['min_gap_weeks']:.0f}–{lev['max_gap_weeks']:.0f} weeks (median {lev['median_gap_weeks']:.0f}). Any slowly drifting series lets a forest tell neighbouring half-years apart. Always difference persistent series first.</figcaption></figure>

<h3>Analysis 2c · Daily scale and speed</h3>
<p>Daily changes in log VIX, the slope, the 2y and the 10y from 1990 to 2026: {b['B3_n']:,} days × 4, segmented in {b['B3_rf_secs']:.2f}s, with {len(b['B3_cps'])} breaks (<code>change_in_mean</code>: {b['B3_cim_ncp']}).</p>
<figure><img src="{FIG}m2_daily_breaks.png" alt="daily breaks"><figcaption>63-day rolling SD of daily Δ10y with the changeforest breaks.</figcaption></figure>
<details><summary>All {len(dsegs)} daily segments</summary>{DS}</details>
<p>At daily frequency the VIX–10y correlation is positive in {len(pos)} segments: {', '.join(s['start'][:7]+'→'+s['end'][:7] for s in pos)}. These are the pre-2000 regime and 2022–24, which matches the weekly result.</p>
<figure><img src="{FIG}m2_scaling.png" alt="scaling"><figcaption>Synthetic scaling test, 5 dimensions, one variance break at n/2.</figcaption></figure>
{SCT}
<p><strong>What it shows.</strong> The random-forest variant is close to linear (n = 16,000 in {sc[-1]['random_forest']:.2f}s) and lands on the true break every time. The kNN variant is fast but over-segmented the synthetic variance break badly at n ≥ 4,000. Exact kernel PELT (ruptures, RBF) took {sc[2]['pelt_rbf']:.0f}s at n = 4,000 and, at the penalty I set (10·log n), missed the break. That penalty is my choice, not a property of PELT, but the quadratic cost is real.</p>

<div class="card dark"><h4>Limitations</h4><ul>
<li>Assumes independent rows within a segment. Persistent series must be differenced, or you get artifacts (see 2b).</li>
<li>Break counts are seed-sensitive. Report the multi-seed core set, not a single run.</li>
<li>It says <em>when</em> the distribution changed, not <em>what</em> changed. Pair it with per-segment summaries, as above, or with a MOB tree using segment ID as a partitioning variable.</li>
<li>The kNN classifier option is unreliable at large n in my test.</li>
</ul>
<p><strong>Verdict: interesting.</strong> It's worth keeping as the unsupervised "when did the regime change" step ahead of MOB or TRACE-style explanations. The Rust core plus thin bindings matches our stack. Not an adopt-candidate yet, because of seed sensitivity. Next step: a multi-seed consensus wrapper.</p></div>

<div class="sec-head"><span class="n">Watch</span><h2>Logged for later</h2><span class="line"></span></div>
<div class="grid">
<div class="card blue"><h4><a href="https://cran.r-project.org/package=fastcpd">fastcpd</a> · R/C++</h4><p>Fast change-point detection via sequential gradient descent (Li &amp; Zhang). v1.0.0, June 2026. Parametric (GLM, ARMA, GARCH) segment costs: the natural parametric counterpart to changeforest.</p></div>
<div class="card blue"><h4><a href="https://cran.r-project.org/package=stablelearner">stablelearner</a> · R</h4><p>Stability assessment for trees and other learners (Philipp, Strobl, Zeileis et al.). Would replace my hand-rolled bootstrap table in 1b.</p></div>
<div class="card blue"><h4><a href="https://cran.r-project.org/package=glmertree">glmertree</a> · R</h4><p>MOB with random effects (Fokkema &amp; Zeileis). The right tool for the county panel, where state-level clustering should not drive the splits.</p></div>
<div class="card blue"><h4><a href="https://cran.r-project.org/package=evtree">evtree</a> · R</h4><p>Globally optimal trees by evolutionary search (Grubinger, Zeileis, Pfeiffer; JSS 2014). Answers whether greedy trees miss a better regime split.</p></div>
<div class="card blue"><h4><a href="https://crates.io/crates/augurs">augurs</a> · Rust</h4><p>Time-series toolkit (changepoints, outliers, DTW clustering, MSTL), v0.10.3. A Rust building block to check against changeforest.</p></div>
</div>

<footer>
<p>Run 2026-11-10, America/New_York (EST). R {a['versions']['R'].split(' ')[2]}, partykit {a['versions']['partykit']}, rpart {a['versions']['rpart']}; changeforest {b['versions']['changeforest']}, ruptures {b['versions']['ruptures']}, scikit-learn {b['versions']['sklearn']}. Sources scanned: CRAN (partykit and Zeileis-group packages), PyPI and crates.io (changeforest, augurs), JMLR and JCGS papers, and an X search. The X search turned up only noise this time, because "partykit" collides with an unrelated web framework. Data: Drive files listed in the summary; only aggregates are published. No neural nets.</p>
</footer>
</main></body></html>'''
open(S+'2026-11-10.html','w').write(page)
idx=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Methods scout · research-lab</title>{FONTS}<link rel="stylesheet" href="../assets/brief.css">{ICONS}</head><body><main>
<header class="mast"><div class="date">Daily · newest first</div><h1>Methods scout</h1>
<p class="dek">Lesser-known, fast, interpretable analytical methods, each run at least three ways on our own data.</p>
<nav><a href="../index.html">Research lab home</a><a href="https://github.com/jgridifier/research-lab/blob/main/docs/methods-scout/watchlist.md">Watchlist</a></nav></header>
<div class="sec-head"><span class="n">Editions</span><h2>All editions</h2><span class="line"></span></div>
<!-- EDITIONS:START -->
<div class="card teal"><div class="card-top"><span class="tag teal">2026-11-10 · Tue</span><span><span class="verdict adopt">adopt-candidate</span> <span class="verdict interesting">interesting</span></span></div>
<h3><a href="2026-11-10.html">partykit trees (ctree + MOB) and changeforest change points</a></h3>
<p>The VIX→credit-spread link roughly doubles when NFCI &gt; 0.06, and calendar time stops mattering. Regime trees did not forecast 6-month spread changes out of sample. changeforest finds volatility and correlation regimes that mean-change methods miss, including the 2022 stock–rate correlation flip, but its break count is seed-sensitive.</p>
<div class="foot">Data: Drive FRED series, GZ/EBP monthly, county econ panel</div></div>
<!-- EDITIONS:END -->
<footer><p>One page per scouting run, at <code>docs/methods-scout/YYYY-MM-DD.html</code>. Theme notes: <code>docs/assets/THEME.md</code>.</p></footer>
</main></body></html>'''
open(S+'index.html','w').write(idx)
print('built', len(page))
