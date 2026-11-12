"""Render docs/methods-scout/2026-11-11.html from out/m1_results.json and out/m2_results.json."""
import json, html, shutil, os, sys
B='/workspace/scout/1111/'; DOCS=sys.argv[1] if len(sys.argv)>1 else B+'site/'
os.makedirs(DOCS+'fig/2026-11-11',exist_ok=True)
for f in os.listdir(B+'fig'): shutil.copy(B+'fig/'+f, DOCS+'fig/2026-11-11/'+f)
a=json.load(open(B+'out/m1_results.json')); b=json.load(open(B+'out/m2_results.json')); ps=json.load(open(B+'data/panel_summary.json'))
e=html.escape; FIG='fig/2026-11-11/'
def f(x,n=2):
    return 'n/a' if x is None or x=='NA' else f'{float(x):.{n}f}'
def tbl(head, rows, num=()):
    h=''.join(f'<th class="num">{e(c)}</th>' if i in num else f'<th>{e(c)}</th>' for i,c in enumerate(head))
    r=''.join('<tr>'+''.join(f'<td class="num">{c}</td>' if i in num else f'<td>{c}</td>' for i,c in enumerate(row))+'</tr>' for row in rows)
    return f'<div class="table-wrap"><table><thead><tr>{h}</tr></thead><tbody>{r}</tbody></table></div>'
nm=lambda k: k.replace('UBS.CS','UBS+CS')
LAB={'M0':'M0 market+noise (no sticky)','M1':'M1 sticky RW + market','M1n':'M1n sticky RW, no market','M2':'M2 mean-reverting + market'}
def a1table(pn):
    rows=[]
    for k,r in a['A1_'+pn].items():
        ai=r['AICc']; best=r['best']
        rows.append([nm(k),best,f(ai['M0'],1),f(ai['M1'],1),f(ai['M1n'],1),f(ai['M2'],1),f(r['M2_b'],3),(f(r['M2_halflife_q'],1) if r['M2_halflife_q'] not in (None,'NA') else '∞'),
                     f"{100*r['var_frac']['sticky']:.0f}% / {100*r['var_frac']['market']:.0f}% / {100*r['var_frac']['transient']:.0f}%",
                     f"{f(list(r['net_change_clr'].values())[0])} = {f(r['net_change_clr']['sticky'])} + {f(r['net_change_clr']['market'])} + {f(list(r['net_change_clr'].values())[3])}"])
    return tbl(['Dealer','Best (AICc)','M0','M1','M1n','M2','M2 b','Half-life (q)','Var. of Δ: sticky / market / transient','Net clr change = sticky + market + transient'],rows,num=(2,3,4,5,6,7))
def pairs(pn,k=6):
    return tbl(['Pair','Corr. of sticky increments','one-sided p (circular shift, 1,000)','BH q'],
        [[f"{nm(p['a'])} ↔ {nm(p['b'])}",f(p['corr'],3),f(p['p_neg'],3),f(p['q_BH'],3)] for p in a[f'A1_{pn}_pairs'][:k]],num=(1,2,3))
def a2table(pn,early,late):
    rows=[]
    for k in a['A2'][f'{pn}_early']:
        E_,L_=a['A2'][f'{pn}_early'][k],a['A2'][f'{pn}_late'][k]
        rows.append([nm(k),E_['best'],L_['best'],f"{100*E_['var_frac']['sticky']:.0f}% / {100*E_['var_frac']['market']:.0f}%",f"{100*L_['var_frac']['sticky']:.0f}% / {100*L_['var_frac']['market']:.0f}%",f(E_['M2_b'],2),f(L_['M2_b'],2)])
    return tbl(['Dealer',f'Best {early}',f'Best {late}',f'Sticky / market var. {early}',f'Sticky / market var. {late}',f'M2 b {early}',f'M2 b {late}'],rows,num=(5,6))
def a3table(pn):
    o=a['A3'][pn]; ks=['RW','MEAN','AR1','MARSS_M0','MARSS_M1']; lab={'RW':'Random walk (last share)','MEAN':'Expanding mean','AR1':'AR(1) to window mean','MARSS_M0':'MARSS M0 (market only, no sticky state)','MARSS_M1':'MARSS M1 (sticky + market)'}
    return tbl(['Forecast','RMSE, clr units','RMSE, share pp'],[[lab[k],f(o['rmse_clr'][k],4),f(o['rmse_share_pp'][k],3)] for k in ks],num=(1,2))
def a4table():
    rows=[]
    for pn in ['E4','A']:
        for k,r in a['A4'][pn].items():
            rows.append([pn,nm(k),f(r['phi_used'],2),f"{100*r['AR_null_frac_M1_selected']:.0f}%",f"{100*r['RW_power_frac_M1_selected']:.0f}%",a['A1_'+pn][k]['best']])
    return tbl(['Panel','Dealer','AR(1) φ matched','False "sticky" (M1 picked on stationary AR)','Power (M1 picked on a true random walk)','Real-data pick'],rows,num=(2,3,4))
def brk(lst,drift=False):
    rows=[]
    for c in lst:
        tp=', '.join(f"{nm(k)} {v:+.2f}" for k,v in c['top_projection'].items())
        if drift: rows.append([c['break_after'],f(c['cusum'],2),' → '.join(c['segment']),tp])
        else:
            mv=sorted(c['share_change_pp'].items(),key=lambda kv:-abs(kv[1]))[:3]
            rows.append([c['break_after'],f(c['cusum'],2),tp,', '.join(f"{nm(k)} {v:+.2f}pp" for k,v in mv)])
    return tbl(['Break after','Projected CUSUM','Projection direction (top 4 loadings)','Biggest share moves (adjacent segments)'] if not drift else ['Break after','Projected CUSUM','Segment','Projection direction'],rows,num=(1,))
b2=lambda pn: b['B2_'+pn]
NULLT=tbl(['Panel / test','Observed breaks','iid shuffle (mean, P≥obs)','AR(1)-matched (mean, P≥obs)','Random walk (mean, P≥obs)'],[
 [f"A · levels, market-adjusted (n={b['B1_A']['n']}, p={b['B1_A']['p']})",b2('A')['observed_adj'],f"{f(b2('A')['shuffle']['mean'])}, {f(b2('A')['shuffle']['p_ge_obs'],3)}",f"{f(b2('A')['ar1_matched']['mean'])}, {f(b2('A')['ar1_matched']['p_ge_obs'],3)}",f"{f(b2('A')['random_walk']['mean'])}, {f(b2('A')['random_walk']['p_ge_obs'],3)}"],
 [f"E4 · levels, market-adjusted (n={b['B1_E4']['n']}, p={b['B1_E4']['p']})",b2('E4')['observed_adj'],f"{f(b2('E4')['shuffle']['mean'])}, {f(b2('E4')['shuffle']['p_ge_obs'],3)}",f"{f(b2('E4')['ar1_matched']['mean'])}, {f(b2('E4')['ar1_matched']['p_ge_obs'],3)}",f"{f(b2('E4')['random_walk']['mean'])}, {f(b2('E4')['random_walk']['p_ge_obs'],3)}"],
],num=(1,))
D4=tbl(['Panel / drift test (first differences)','Observed','iid shuffle (mean, P≥obs)','Block-4 shuffle (mean, P≥obs)','AR(1)-matched (mean, P≥obs)'],[
 [f"{pn}",b['B4_'+pn]['observed'],f"{f(b['B4_'+pn]['null_shuffle']['mean'])}, {f(b['B4_'+pn]['null_shuffle']['p_ge_obs'],3)}",f"{f(b['B4_'+pn]['null_block4']['mean'])}, {f(b['B4_'+pn]['null_block4']['p_ge_obs'],3)}",f"{f(b['B4_'+pn]['null_ar1']['mean'])}, {f(b['B4_'+pn]['null_ar1']['p_ge_obs'],3)}"] for pn in ['A','E4']],num=(1,))
B3T=tbl(['Inspect break (A, market-adjusted)','Firms with a univariate strucchange break within ±1q (of 14)','Real-time delay (quarters of extra data needed)'],
 [[k,v,b['B3_A']['realtime_delay_quarters'][k]] for k,v in b['B3_A']['n_firms_with_univariate_break_within_1q'].items()],num=(1,2))
ihc0=sum(ps['A_first'][k] for k in ['Barclays','UBS+CS','DB','BNP','HSBC','Mizuho','RBC','TD']); ihc1=sum(ps['A_last'][k] for k in ['Barclays','UBS+CS','DB','BNP','HSBC','Mizuho','RBC','TD'])
r=a['A1_E4']; rA=a['A1_A']; o3=a['A3']
jg=a['A1_E4_pairs'][0]
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
mkt=lambda k: f"{100*r[k]['var_frac']['market']:.0f}%"
page=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Methods scout · 2026-11-11 · research-lab</title>
<meta name="description" content="Daily methods scout, aimed at Q1 (dealer share dynamics: market-driven vs sticky): MARSS state-space decomposition and InspectChangepoint sparse-projection change points, on a PROXY Y-9C dealer panel.">
{FONTS}
<link rel="stylesheet" href="../assets/brief.css">
{KATEX}
{ICONS}</head><body><main>
<header class="mast">
  <div class="date">Wednesday · November 11, 2026 · edition 2 · aimed at Q1</div>
  <h1>Methods scout</h1>
  <p class="dek">Two lesser-known, fast, interpretable methods for one question: when a dealer's share moves, is it the market or a sticky migration? Run on a clearly labelled PROXY panel, because top-25 prime-broker data isn't in Drive.</p>
  <nav><a href="index.html">All editions</a><a href="https://github.com/jgridifier/research-lab/blob/main/docs/methods-scout/QUESTIONS.md">Research questions</a><a href="https://github.com/jgridifier/research-lab/blob/main/docs/methods-scout/watchlist.md">Watchlist</a><a href="../index.html">Research lab home</a></nav>
</header>

<div class="ticker"><span><b>●</b> PROXY: foreign-bank US IHCs' share of 14-dealer trading assets fell from {100*ihc0:.1f}% to {100*ihc1:.1f}% (2016Q3→2026Q2)</span><span><b>●</b> MARSS: market covariates explain {mkt('BAC')} (BAC), {mkt('MS')} (MS), {mkt('JPM')} (JPM) of quarterly equity-revenue-share changes, but only {mkt('GS')} for GS</span><span><b>●</b> GS's sticky losses mirror JPM's sticky gains: corr {f(jg['corr'])} (BH q = {f(jg['q_BH'],3)})</span><span><b>●</b> Inspect: every "break" in share levels is matched by persistence-only nulls; 0 significant drift breaks</span></div>

<section class="tldr">
<h2>The short version</h2>
<ul>
<li><strong>Data first.</strong> Q1 asks about the top 25 prime brokers. There is <em>no</em> per-firm prime-brokerage revenue, balance or market-share data in Drive or on the box (searched below; the Drive README for the hedge-fund leverage folder says the Coalition Greenwich league tables are paywalled). Everything here runs on a <strong>PROXY</strong>: public FR Y-9C filings for the largest US dealer holding companies and foreign-bank IHCs. Trading assets stand in for "activity/balance share" (14 dealers, 2016Q3–2026Q2) and equity trading revenue (HI Memo 9.c) for "revenue share" (JPM, GS, MS, BAC, 2011Q1–2026Q2). Neither is prime brokerage.</li>
<li><strong>MARSS</strong> (state-space, R Journal 2012) <span class="verdict adopt">recommend for promote workflow</span>. It splits each dealer's log-ratio share into a market-driven part (VIX, Nasdaq return, industry growth), a sticky random-walk state and transient noise, and AICc compares "sticky", "mean-reverting" and "no sticky" versions. On the revenue proxy, market factors drive most quarter-to-quarter moves for JPM, MS and BAC. GS is the exception: its fall from {100*ps['E4_first']['GS']:.0f}% to {100*ps['E4_last']['GS']:.0f}% of big-4 equity trading revenue sits almost entirely in the sticky state, and those sticky losses line up with JPM's gains. The caveat is sample length: a matched-persistence null shows AICc can tell sticky from slow mean reversion at 62 quarters, but not reliably at 40.</li>
<li><strong>InspectChangepoint</strong> (sparse-projection change points, JRSS-B 2018) <span class="verdict interesting">interesting</span>. It's fast ({b['timing_ms_per_call_A']} ms per 14×40 panel), and the projection vector says <em>which</em> dealers moved at a break. But on share levels it finds {b2('A')['observed_adj']} breaks while AR(1) and random-walk surrogates with the same persistence average {f(b2('A')['ar1_matched']['mean'],1)}–{f(b2('A')['random_walk']['mean'],1)}. Run on first differences (a change in migration <em>speed</em>), it finds 0 breaks in the trading-asset panel and 1 non-significant break in revenue shares. So there is no evidence of abrupt regime breaks in the proxy, only gradual persistent drift.</li>
</ul>
<p class="meta">Data used (all public regulatory data, aggregated): FR Y-9C trading panel 2008Q1–2026Q2 built from FFIEC/NIC BHCF bulk files (box copy at <code>rl_check/tracks/y9c-trading-ot/data/processed_v1_1/</code>); FRED VIXCLS and NASDAQCOM. Only shares, fitted structure and charts are shown. Scripts and full JSON outputs are under <code>docs/methods-scout/runs/2026-11-11/</code>. <strong>Pre-registration note:</strong> this panel also feeds the pre-registered Y-9C trading-OT forecast track, whose out-of-sample run is not yet authorized. Today's work is descriptive share analysis of trading assets and the equity memo line. It runs none of that track's forecasts, but it does look at 2014–2026 data that sits inside that track's OOS window. Jared should know this before authorizing that run.</p>
</section>

<div class="sec-head"><span class="n">Q1</span><h2>Where the question stands</h2><span class="line"></span></div>
<div class="card dark"><p><strong>Q1 (2026-11-10):</strong> “How have prime broker revenue/activity share dynamics changed among the top 25 brokers and how can we gain insight into market based ones vs real sticky share migration?”</p>
<p><strong>Progress (PROXY only).</strong> (1) Method: a state-space split into market, sticky and transient parts, with a persistence-matched null, works and is cheap. The matching change-point tool mainly tells us there are no abrupt breaks. (2) Proxy findings: in the US dealer balance-sheet proxy, share moved steadily from foreign IHCs (−{100*(ihc0-ihc1):.1f}pp) to JPM (+{100*(ps['A_last']['JPM']-ps['A_first']['JPM']):.1f}pp), GS (+{100*(ps['A_last']['GS']-ps['A_first']['GS']):.1f}pp) and C, and market covariates account for almost none of that net shift (market part of net clr change ≤0.05 in absolute value for every dealer). That looks like sticky migration. In the equity-revenue proxy, quarter-to-quarter swings are mostly market-driven, apart from a persistent GS→JPM shift. (3) Missing: real per-firm prime-brokerage revenue and balances for the top 25 (see the data box). Status: <strong>in progress</strong>.</p></div>

<div class="card"><div class="card-top"><span class="tag">Data search</span><span class="tag red">Top-25 PB data: missing</span></div>
<p><strong>Searched</strong> (Drive connectors on the main and personal accounts, plus the xai Drive connector): “prime broker”, “prime services”, “prime brokerage”, “securities lending”, “market share”, “financing balances”, “broker revenue”, “equities financing”, “Coalition Greenwich”, “Y-9C”, “trading revenue”, “broker-dealer FOCUS”. Also checked the box for Y-9C, call-report and Form PF panels. X search found no method leads and no data. One post repeats an unsourced “80% share” claim for the top 3, which we did not use.</p>
<p><strong>Found and relevant, but not top-25 per-firm PB data:</strong> GS and MS 10-K/10-Q/supplement markdown (2 firms, 2023–2026; segment text only); SEC Form PF aggregates (README: Tab 8.28 prime-broker borrowings, aggregate, not by broker; the panel CSV wasn't found by exact name on Drive); SCOOS dealer-survey text (qualitative); NY Fed fails and OFR repo (market plumbing, not firm shares); FDIC call-report top-100 (bank charters, no PB items); OCC quarterly derivatives reports 2016–2026 (PDF tables of top holding companies by derivatives; not parsed today).</p>
<p><strong>Used as PROXY:</strong> the FR Y-9C trading panel (BHCK3545 trading assets; BHCK8759 equity trading revenue), aggregated to dealer shares.</p></div>

<!-- ================= METHOD 1 ================= -->
<div class="sec-head" id="m1"><span class="n">Method 01</span><h2>MARSS: market vs sticky vs transient share moves, as a state-space model</h2><span class="line"></span></div>
<div class="card teal">
<div class="card-top"><span class="tag teal">R · CRAN · v{a['meta']['MARSS']} · GPL-2 · novelty: niche</span><span class="verdict adopt">recommend for promote workflow</span></div>
<p><strong>Citation.</strong> Holmes, E. E., Ward, E. J. &amp; Wills, K. (2012), “MARSS: Multivariate Autoregressive State-space Models for Analyzing Time-series Data”, <em>The R Journal</em> 4(1):11–19. Package: <a href="https://cran.r-project.org/package=MARSS">cran.r-project.org/package=MARSS</a> (v{a['meta']['MARSS']}, 2025-09; ~1.5k downloads/month; NOAA fisheries authors; long user guide with worked examples and a test suite). It comes from ecology, where it's used to split population counts into process and observation noise, and it's rarely used in finance.</p>
<p><strong>Target question.</strong> Q1: is a dealer's share move market-driven (it moves with VIX, equity returns or industry size and comes back), sticky (a permanent random-walk shift), or transient noise?</p>
<p><strong>Why it's good and fast.</strong> One model gives a variance split, a net-change attribution and a likelihood test of “sticky vs mean-reverting vs no sticky component”, with covariates in the observation equation so market effects are kept out of the sticky state. Each univariate fit takes about 0.2–1 s (short EM warm start, then BFGS on the Kalman likelihood). The whole edition, about 4,000 model selections including the nulls and walk-forward, ran in 11 minutes on a shared box.</p>
</div>
<h3>The math in plain terms</h3>
<p>For dealer \\(i\\), take the centred log-ratio share \\(y_{{it}}=\\log s_{{it}}-\\tfrac1N\\sum_j\\log s_{{jt}}\\) (shares live on a simplex; clr maps them to ordinary space). Then</p>
<div class="math-block">$$x_{{t}}=b\\,x_{{t-1}}+w_t,\\quad w_t\\sim N(0,q)\\qquad\\qquad y_{{t}}=x_t+D^\\top d_t+v_t,\\quad v_t\\sim N(0,r)$$</div>
<p>\\(x_t\\) is the <em>sticky</em> state. \\(D^\\top d_t\\) is the <em>market</em> part, with \\(d_t\\) = standardized VIX, 4-quarter Nasdaq return and industry growth; it reverts when the market reverts. \\(v_t\\) is <em>transient</em>. We compare four models by AICc: M0 (\\(q=0\\): no sticky state), M1 (\\(b=1\\): random-walk sticky state), M1n (M1 without market covariates) and M2 (\\(b&lt;1\\): mean-reverting, half-life \\(\\log 0.5/\\log b\\) quarters). From the smoothed M1 we report the variance of quarterly changes in each part, and the net change over the sample split as sticky + market + transient.</p>

<h3>Analysis 1a · Q1-directed: decompose each dealer's share (both proxies)</h3>
<p><strong>Revenue proxy E4</strong>: JPM, GS, MS, BAC shares of big-4 trailing-4-quarter equity trading revenue, {ps['E4_quarters'][0]}–{ps['E4_quarters'][1]} ({ps['E4_quarters'][2]} quarters). Citi is excluded because its 4-quarter equity trading revenue is negative in some quarters, and log-ratios need positive parts.</p>
<figure><img src="{FIG}m1_decomp_E4.png" alt="MARSS decomposition, equity revenue shares"><figcaption>Black: clr share (demeaned). Teal: smoothed sticky state. Dashed: sticky + market. The gap between teal and dashed is the market-driven part.</figcaption></figure>
{a1table('E4')}
<p><strong>What it shows.</strong> Adding market covariates improves AICc sharply for BAC, MS and JPM (M1 vs M1n: {f(r['BAC']['dAICc_M1_vs_M1n'],0)}, {f(r['MS']['dAICc_M1_vs_M1n'],0)}, {f(r['JPM']['dAICc_M1_vs_M1n'],0)}), and market moves are {mkt('BAC')}, {mkt('MS')} and {mkt('JPM')} of their quarterly variance. For these three, most revenue-share swings are the market. GS is different: only {mkt('GS')} is market-driven, and nearly all of its net decline ({f(list(r['GS']['net_change_clr'].values())[0])} clr) is in the sticky state. All four prefer M2 (slow mean reversion, half-lives {f(r['GS']['M2_halflife_q'],1)}–{f(r['MS']['M2_halflife_q'],1)} quarters), but only narrowly over M1 (by 0.5–3.6 AICc points), so “permanent” vs “reverts over 1–2 years” isn't settled.</p>
<p><strong>Who took share from whom.</strong> Correlations of the sticky-state increments, with a circular-shift null that keeps each series' autocorrelation. A 4-part clr has a built-in correlation of about {a['A1_E4_clr_baseline_corr']}.</p>
{pairs('E4',4)}
<p>The GS↔JPM correlation ({f(jg['corr'])}) is far below the {a['A1_E4_clr_baseline_corr']} built-in level and survives BH. In this proxy, GS's sticky losses went to JPM.</p>
<p><strong>Balance/activity proxy A</strong>: shares of trading assets across 14 dealer holding companies (6 US, 8 foreign-bank IHCs; UBS and Credit Suisse combined to stay merger-consistent), {ps['A_quarters'][0]}–{ps['A_quarters'][1]} ({ps['A_quarters'][2]} quarters).</p>
<figure><img src="{FIG}m1_decomp_A.png" alt="MARSS decomposition, trading-asset shares"><figcaption>Same decomposition for six dealers in the trading-asset panel.</figcaption></figure>
<details><summary>All 14 dealers: AICc, half-life, variance split and net change</summary>{a1table('A')}</details>
<p><strong>What it shows.</strong> For balances, market covariates mostly <em>don't</em> help: AICc prefers M1n (no market) for {sum(1 for v in rA.values() if v['best']=='M1n')} of 14 dealers. Share moves are sticky plus quarter-end noise. The large net moves are almost all sticky: UBS+CS {f(list(rA['UBS.CS']['net_change_clr'].values())[0])} clr (sticky {f(rA['UBS.CS']['net_change_clr']['sticky'])}), Mizuho {f(list(rA['Mizuho']['net_change_clr'].values())[0])} (sticky {f(rA['Mizuho']['net_change_clr']['sticky'])}), RBC {f(list(rA['RBC']['net_change_clr'].values())[0])}, JPM {f(list(rA['JPM']['net_change_clr'].values())[0])} (sticky {f(rA['JPM']['net_change_clr']['sticky'])}). No firm-to-firm pair survives BH correction here (best q = {f(a['A1_A_pairs'][0]['q_BH'],2)}).</p>
<details><summary>Top sticky-increment pairs, trading-asset panel</summary>{pairs('A',6)}</details>

<h3>Analysis 1b · Stability across windows</h3>
{a2table('E4','2011–17','2018–26')}
{a2table('A','2016Q3–21Q2','2021Q3–26Q2')}
<p><strong>What it shows.</strong> The decomposition is <em>not</em> stable for every dealer. JPM's revenue share was mostly sticky in 2011–17 ({100*a['A2']['E4_early']['JPM']['var_frac']['sticky']:.0f}% of variance) and mostly market-driven in 2018–26 ({100*a['A2']['E4_late']['JPM']['var_frac']['market']:.0f}%). GS's sticky share of variance rose ({100*a['A2']['E4_early']['GS']['var_frac']['sticky']:.0f}% → {100*a['A2']['E4_late']['GS']['var_frac']['sticky']:.0f}%). The 20-quarter halves of the trading-asset panel are too short to compare reliably (see 1d). Read the split as “what happened in this window”, not as a fixed property of a firm.</p>

<h3>Analysis 1c · Versus plain baselines, honest out of sample</h3>
<p>Expanding window, refit each quarter, one quarter ahead. This is a nowcast: market covariates for quarter \\(t+1\\) are known at quarter end, about 40 days before the Y-9C is published. Covariates are standardized with training-window statistics only.</p>
<figure><img src="{FIG}m1_oos.png" alt="OOS RMSE"><figcaption>One-step RMSE in share percentage points; the random walk is red.</figcaption></figure>
<div class="grid"><div>{a3table('E4')}<p class="meta">E4: {o3['E4']['origins'][0]}–{o3['E4']['origins'][1]}, n = {o3['E4']['n']}; M1 beats RW in {100*o3['E4']['frac_quarters_M1_beats_RW']:.0f}% of quarters.</p></div><div>{a3table('A')}<p class="meta">A: {o3['A']['origins'][0]}–{o3['A']['origins'][1]}, n = {o3['A']['n']}; M1 beats RW in {100*o3['A']['frac_quarters_M1_beats_RW']:.0f}% of quarters.</p></div></div>
<p><strong>What it shows.</strong> Mixed, so no forecasting claim. On revenue shares MARSS M1 has a {100*(1-o3['E4']['rmse_clr']['MARSS_M1']/o3['E4']['rmse_clr']['RW']):.0f}% lower clr RMSE than the random walk, but ties it in share points ({f(o3['E4']['rmse_share_pp']['MARSS_M1'])} vs {f(o3['E4']['rmse_share_pp']['RW'])}pp). On trading assets it's {100*(1-o3['A']['rmse_share_pp']['MARSS_M1']/o3['A']['rmse_share_pp']['RW']):.0f}% better in share points but worse in clr units, because it misses the small dealers. The model with <em>no</em> sticky state (M0) is far worse in both panels ({f(o3['E4']['rmse_share_pp']['MARSS_M0'])}pp and {f(o3['A']['rmse_share_pp']['MARSS_M0'])}pp). That is the clearest out-of-sample evidence that a persistent, sticky component is real.</p>

<h3>Analysis 1d · Matched-persistence null: does AICc cry “sticky” on stationary data?</h3>
<p>For each dealer we simulated {a['A4']['E4']['JPM']['nsim']} stationary AR(1) series with the real series' lag-1 persistence and noise, and {a['A4']['E4']['JPM']['nsim']} true random walks, then ran the same M0/M1/M2 selection with the real covariates.</p>
{a4table()}
<p><strong>What it shows.</strong> With 62 quarters (E4), AICc rarely calls a stationary series sticky (0–{100*max(v['AR_null_frac_M1_selected'] for v in a['A4']['E4'].values()):.0f}%) and finds a true random walk 58–65% of the time, so the classification is informative. With 40 quarters (A) it calls stationary series sticky {100*min(v['AR_null_frac_M1_selected'] for v in a['A4']['A'].values()):.0f}–{100*max(v['AR_null_frac_M1_selected'] for v in a['A4']['A'].values()):.0f}% of the time, so per-dealer “sticky vs slow mean reversion” labels on the 2016–26 balance panel are not trustworthy. The net-change attribution and the M0 out-of-sample failure still are.</p>
<div class="card dark"><h4>Limitations</h4><ul>
<li>PROXY data. Y-9C trading assets and the equity trading-revenue memo line are not prime-brokerage revenue or balances. GS and MS book much of their prime revenue as net interest and commissions, not trading revenue.</li>
<li>Univariate fits on clr coordinates ignore the sum-to-zero link between dealers. A joint MARSS with a structured \\(Q\\) is the next step once there's a longer panel.</li>
<li>Below about 60 quarters, sticky vs slow mean reversion can't be told apart (1d). Decompositions shift between windows (1b).</li>
</ul>
<p><strong>Verdict: recommend for promote workflow</strong> (recommendation only; nothing is promoted without Jared's approval). It's the right shape for Q1, fast, readable, and it carries its own falsification test. Required in any skill: the matched-persistence null and a minimum sample length.</p></div>

<!-- ================= METHOD 2 ================= -->
<div class="sec-head" id="m2"><span class="n">Method 02</span><h2>InspectChangepoint: which dealers moved, and when?</h2><span class="line"></span></div>
<div class="card">
<div class="card-top"><span class="tag">R · CRAN · v{b['meta']['InspectChangepoint']} · GPL-3 · novelty: obscure</span><span class="verdict interesting">interesting</span></div>
<p><strong>Citation.</strong> Wang, T. &amp; Samworth, R. J. (2018), “High dimensional change point estimation via sparse projection”, <em>Journal of the Royal Statistical Society: Series B</em> 80(1):57–83. Package: <a href="https://cran.r-project.org/package=InspectChangepoint">cran.r-project.org/package=InspectChangepoint</a> (v1.2, 2022-05; ~450 downloads/month; pure R, imports only MASS; the authors' own implementation).</p>
<p><strong>Target question.</strong> Q1: was there a discrete moment when share migrated between specific dealers (an exit, a blow-up, a client transfer), and who was involved?</p>
<p><strong>Why it's good and fast.</strong> Most multivariate change-point methods tell you <em>when</em>. Inspect also tells you <em>which coordinates</em>: it finds the sparse direction along which the panel's mean shifted, so each break comes with a short list of dealers that gained or lost. It's a convex relaxation solved by SVD, at {b['timing_ms_per_call_A']} ms per 14×40 panel.</p>
</div>
<h3>The math in plain terms</h3>
<p>Stack the \\(p\\) dealers' standardized series into \\(X\\in\\mathbb R^{{p\\times n}}\\) and form its CUSUM transform \\(T\\) (column \\(t\\) compares the mean before and after \\(t\\)). A mean change in a sparse set of coordinates makes \\(T\\approx\\theta\\gamma^\\top\\), rank one with sparse \\(\\theta\\). Inspect estimates the direction by</p>
<div class="math-block">$$\\hat M=\\arg\\max_{{\\|M\\|_*\\le1}}\\;\\langle T,M\\rangle-\\lambda\\|M\\|_1,\\qquad \\hat v=\\text{{leading left singular vector of }}\\hat M$$</div>
<p>It projects the data onto \\(\\hat v\\), runs a univariate CUSUM and recurses with wild binary segmentation. The loadings \\(\\hat v\\) are the “who moved” vector. Noise is assumed independent over time; that assumption is what we test.</p>

<h3>Analysis 2a · Q1-directed: breaks and who moved (trading-asset panel)</h3>
<figure><img src="{FIG}m2_shares_breaks.png" alt="shares with breaks"><figcaption>Left: trading-asset shares, with Inspect breaks on market-adjusted log-ratio levels (dotted). Right: equity-revenue shares, with the one drift break (dashed).</figcaption></figure>
{brk(b['B1_A']['market_adjusted'])}
<figure><img src="{FIG}m2_who_moved.png" alt="who moved"><figcaption>Mean share change across each break (pp), adjacent segments.</figcaption></figure>
<p><strong>What it shows, taken at face value.</strong> The strongest coherent event is after 2018Q4: JPM +1.8pp and GS +1.0pp; MS −1.2pp and RBC −0.7pp; 7 of 14 dealers also have a univariate break within a quarter. The 2017Q1 break loads on DB, UBS+CS and Barclays losing share. The 2024Q1 break is GS +2.2pp and JPM +1.8pp against BAC and MS. These are plausible stories, but analysis 2b says not to trust them as breaks.</p>

<h3>Analysis 2b · Null that keeps the persistence: are these breaks real?</h3>
<figure><img src="{FIG}m2_nulls.png" alt="nulls"><figcaption>Break counts on the real panels vs surrogates ({b['B2_A']['nsim']} each for the levels test, {b['B4_A']['nsim']} for the drift test).</figcaption></figure>
{NULLT}
<p><strong>What it shows.</strong> On trading-asset shares the lag-1 persistence is about 1 (unit root), and persistence-only surrogates produce <em>more</em> breaks ({f(b2('A')['ar1_matched']['mean'],1)} and {f(b2('A')['random_walk']['mean'],1)}) than the real data ({b2('A')['observed_adj']}). The level breaks are what a persistent series does under a test that assumes independent noise; they aren't evidence of discrete events. On revenue shares the real panel has more breaks than AR(1) surrogates (p = {f(b2('E4')['ar1_matched']['p_ge_obs'],3)}) but not more than random walks (p = {f(b2('E4')['random_walk']['p_ge_obs'],3)}). This is the same lesson as yesterday's changeforest levels artifact.</p>
<h3>Analysis 2c · The right test for sticky migration: did the <em>speed</em> of migration change?</h3>
<p>Run on first differences of market-adjusted log-ratio shares, a break is a change in drift: the start or end of a sustained migration. iid, block-of-4 and AR(1) nulls on the differences.</p>
{D4}
{brk(b['B4_E4']['breaks'],drift=True)}
<p><strong>What it shows.</strong> No drift breaks in the trading-asset panel. One in revenue shares (after {b['B4_E4']['breaks'][0]['break_after'] if b['B4_E4']['breaks'] else '—'}, GS-loaded), which the iid and block nulls produce {100*b['B4_E4']['null_shuffle']['p_ge_obs']:.0f}% and {100*b['B4_E4']['null_block4']['p_ge_obs']:.0f}% of the time, so it isn't significant. Read with MARSS, the picture is gradual, persistent drift (the foreign-IHC retreat, GS→JPM), not a handful of discrete shocks. Quarterly differences in trading-asset shares are strongly negatively autocorrelated (lag-1 between −0.10 and −0.55, median about −0.43), which points to quarter-end window dressing: transient noise that a sticky-share analysis must filter.</p>
<h3>Analysis 2d · Versus univariate baseline, and timing</h3>
<p>Baseline: <code>strucchange::breakpoints</code> mean-shift per dealer (BIC). It found {b['B3_A']['n_univariate_total']} breaks across 14 dealers, against {len(b['B3_A']['inspect_breaks'])} panel breaks from Inspect. Real-time: the extra quarters needed before an expanding-window Inspect run flags the same break (±1q).</p>
{B3T}
<p>Inspect gives a much sparser, cross-dealer summary than 14 separate tests, and it flags a break 2–5 quarters after it happens. But the same persistence caveat applies to the baseline.</p>
<div class="card dark"><h4>Limitations</h4><ul>
<li>Assumes independent noise and a piecewise-constant mean. Share levels violate both, so the level breaks fail a persistence-matched null.</li>
<li>Noise scale is estimated from differences (MAD/√2). On smooth trailing-4Q revenue sums this understates noise and over-segments.</li>
<li>Last CRAN release 2022 (stable, not active). Small user base.</li>
</ul>
<p><strong>Verdict: interesting.</strong> Keep it as the “who moved” readout once a break has been shown to clear a persistence null, ideally on monthly balance data where breaks (exits, blow-ups, client transfers) would be sharper. Not recommended for the promote workflow on today's evidence.</p></div>

<div class="sec-head"><span class="n">Watch</span><h2>Watch list (new today)</h2><span class="line"></span></div>
<ul>
<li><strong>not</strong> (Narrowest-Over-Threshold; Baranowski, Chen &amp; Fryzlewicz, JRSS-B 2019; CRAN v1.6, ~390 dl/mo; obscure). Piecewise-<em>linear</em> change points: it detects when a migration trend starts or stops, which is the sticky-share signal.</li>
<li><strong>mosum</strong> (Meier, Kirch &amp; Cho, JSS 2021; CRAN v1.2.7, ~570 dl/mo; niche). Moving-sum change points with bandwidth-driven localisation and a multiscale merge. A fast mean-change baseline with real theory.</li>
<li><strong>coda.base</strong> (Comas-Cufí; CRAN v1.0.6, 2026-05; ~870 dl/mo; niche). ilr bases and principal balances. Would replace hand-rolled clr with interpretable “IHCs vs US big-6” balance coordinates.</li>
<li><strong>DirichletReg</strong> (Maier; CRAN v0.7-4, 2026-10; ~5.7k dl/mo; niche). Regress the whole share vector on market covariates. A direct check of the MARSS market loadings.</li>
<li><strong>KFAS</strong> (Helske, JSS 2017; CRAN v1.6.0; ~7k dl/mo; well-known). Exact-diffuse Kalman filtering. A cross-check of MARSS fits and a faster engine for a joint multivariate model.</li>
</ul>

<div class="sec-head"><span class="n">Ask</span><h2>What data would answer Q1 properly</h2><span class="line"></span></div>
<ul>
<li><strong>Per-firm prime-brokerage revenue</strong> for the top 25 (quarterly, 2010+): Coalition Greenwich or similar league tables (paywalled; not in Drive), or Jared's internal competitor series.</li>
<li><strong>Per-firm client balances</strong>: margin and financing debits, synthetic and swap financing notional, short balances, monthly if possible.</li>
<li><strong>Relationship counts</strong> (the cleanest sticky-migration signal): the number and GAV of hedge funds naming each firm as prime broker. A free route exists: SEC Form ADV Schedule D, Section 7.B.(1) lists each private fund's prime brokers. Building that panel is a separate data task.</li>
<li>With any one of these, both methods rerun unchanged: <code>prep.py</code> only needs a firm × quarter matrix.</li>
</ul>
<footer><p>Scripts: <code>docs/methods-scout/runs/2026-11-11/</code> (prep.py → m1_marss.R → m2_inspect.R → figs.py → build.py). R 4.4.3, MARSS {a['meta']['MARSS']}, InspectChangepoint {b['meta']['InspectChangepoint']}, strucchange {b['meta']['strucchange']}. Seeds fixed (20261111). No raw data is published. Theme notes: <code>docs/assets/THEME.md</code>.</p></footer>
</main></body></html>'''
open(DOCS+'2026-11-11.html','w').write(page); print('wrote', DOCS+'2026-11-11.html', len(page))
