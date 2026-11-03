import pandas as pd, html, re
K=open('rl/docs/learn/kumo_rfm_nim.html').read()
css=K[K.index('<style>'):K.index('</style>')+8]
def tbl(df,num=()):
    h='<div class="wrap"><table><tr>'+''.join(f'<th>{html.escape(str(c))}</th>' for c in df.columns)+'</tr>'
    for r in df.itertuples(index=False):
        h+='<tr>'+''.join(f'<td class="{"n" if c in num else ""}">{html.escape("" if pd.isna(v) else str(v))}</td>' for c,v in zip(df.columns,r))+'</tr>'
    return h+'</table></div>'
def md_tables(path):
    out=[];cur=[]
    for l in open(path):
        if l.startswith('|'): cur.append(l)
        elif cur: out.append(cur);cur=[]
    if cur: out.append(cur)
    res=[]
    for t in out:
        rows=[[c.strip() for c in l.strip().strip('|').split('|')] for l in t if not re.match(r'^\|[-| ]+\|$',l.strip())]
        res.append(pd.DataFrame(rows[1:],columns=rows[0]))
    return res
B=md_tables('BENCHMARK.md'); schema,tasks,splits,vb=B[0],B[1],B[2],B[3]
D=md_tables('DATA_TO_COLLECT.md')[0]
D['URL']=D['URL'].map(lambda s:s)
jc=pd.read_csv('reports/join_coverage.csv'); jc['share']=(jc.share*100).round(1).astype(str)+'%'
jc=jc[['source','target','key','matched','total','share','note']]
v=pd.read_csv('reports/baselines_val.csv')
v['val (95% CI)']=v.apply(lambda r:f"{r.val:.3f} [{r.ci_lo:.3f}, {r.ci_hi:.3f}]",axis=1)
piv=v[v.metric!='delta rel-single'].pivot(index='task',columns='model',values='val (95% CI)').fillna('–')
piv=piv[[c for c in ['naive','naive_last_growth','train_median','linear_single','lgbm_single','lgbm_relational'] if c in piv]].reset_index()
dl=v[v.metric=='delta rel-single'][['task','val (95% CI)','top_rel_features']].rename(columns={'val (95% CI)':'lgbm_relational − lgbm_single','top_rel_features':'top features (gain)'})
def link(t):
    return re.sub(r'(https?://[^\s;]+)',lambda m:f'<a href="{m.group(1)}">{m.group(1)}</a>',html.escape(t))
drows=''.join('<tr>'+''.join(f'<td>{link(x)}</td>' for x in r)+'</tr>' for r in D.itertuples(index=False))
dtab='<div class="wrap"><table><tr>'+''.join(f'<th>{c}</th>' for c in D.columns)+'</tr>'+drows+'</table></div>'
P=f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>BankGraph: our own relational benchmark from the Drive data</title>
{css}</head><body>
<h1>BankGraph: our own relational benchmark</h1>
<div class="meta">Learning note + benchmark spec · Nov 3, 2026 · Prepared for Jared · Data: "Bank forecasting datasets" and "BHCF 2008-2017" Drive folders, plus FFIEC HMDA reporter panels · Companion to <a href="kumo_rfm_nim.html">KumoRFM on NVIDIA NIM</a> · Not investment advice.</div>
<div class="callout"><b>Summary.</b> We built five temporal prediction tasks over a linked database of banks, branches, holding companies, mortgage lenders, and complaint companies, using only data from our Drive. Every join was measured. Train/val/test splits are fixed by date, and a sealed holdout is never written to disk by default. On validation, relational aggregates clearly helped one task (branch closure, +0.068 AUC, CI excludes 0) and gave a small gain on holdco-state deposit growth (MAE −0.0011). On bank-deposit decline and complaint spikes, relational features did not help single-table LightGBM. The mortgage-share task is near chance for every baseline. No Kumo or TRACE run has been made on this benchmark; test and holdout labels are untouched.</div>

<h2>1. Why our own benchmark</h2>
<p>Public benchmarks such as RelBench are used in model development, so headline numbers on them may not transfer. A benchmark built from our own data, with tasks and comparison bars fixed before any challenger runs, gives a fairer test of KumoRFM, and later TRACE, against simple baselines.</p>

<h2>2. Schema</h2>
<p>Primary keys, foreign keys, and the time column each table uses for as-of filtering. Publication lags are applied: call report +45 days, SOD June 30 +120 days, HMDA year Y on April 1 of Y+1.</p>
{tbl(schema)}

<h2>3. Join coverage (measured)</h2>
<p>Coverage is computed in <code>scripts/build.py</code>. Low shares are mostly expected scope gaps: the call report panel holds the top 100 banks only, HMDA includes nonbanks and credit unions, and CFPB companies include fintechs and servicers. These gaps shape what each task can use.</p>
{tbl(jc,num=('matched','total','share'))}

<h2>4. Tasks and splits</h2>
{tbl(tasks)}
{tbl(splits)}
<h3>Leakage rules</h3>
<ol>
<li>Features use only rows whose availability date (time column + publication lag) is on or before the cutoff.</li>
<li>Labels look strictly after the cutoff.</li>
<li>Peer aggregates are leave-one-out.</li>
<li>Bank→holdco, LEI↔RSSD, and the complaint-company name map are treated as time-invariant in v0.1. This is a documented approximation; the FFIEC NIC relationships file would remove it.</li>
<li>Test labels are stored in a separate file. Holdout rows are written only with <code>RELBENCH_UNSEAL=1</code>, for one final, announced run.</li>
<li>LightGBM hyperparameters are fixed in advance (400 trees, lr 0.03, 31 leaves, min_child 50, subsample/colsample 0.8, seed 0; L1 loss for regression).</li>
</ol>

<h2>5. Metrics and pre-registered comparison bars</h2>
<p>AUC for classification and MAE for regression, each with a 95% entity-cluster bootstrap CI (B=500, or 200 when validation has more than 50k rows).</p>
<div class="verdict"><ul>
<li>A challenger beats a task only if, on test, challenger − lgbm_relational has a paired 95% CI that excludes 0 in its favor. It ties if the CI covers 0 and loses if the CI excludes 0 against it.</li>
<li>The headline is a count of wins, ties, and losses across T1–T5, with no averaging across metrics.</li>
<li>Challengers get the same tables and cutoffs, with no test or holdout labels in context.</li>
<li>T4 is reported with low weight, because all baselines are near AUC 0.5 on validation.</li>
<li>The holdout is opened once, after test results are recorded.</li>
</ul></div>

<h2>6. Validation baselines (train → val only)</h2>
{tbl(piv)}
<p>Relational vs single-table LightGBM (paired bootstrap):</p>
{tbl(dl)}
<p class="small">Source: <code>reports/baselines_val.csv</code>. Test and holdout have not been scored.</p>

<h2>7. Data worth collecting next</h2>
<p>Ranked by how much each source fixes a measured join gap or adds a task. All URLs were checked on Nov 3, 2026. "Page read" means the site blocks scripted downloads but opened in a browser fetch.</p>
{dtab}

<h2>8. Reproduce</h2>
<pre>python scripts/build.py      # raw Drive files -> parquet + bankgraph.duckdb + join coverage
python scripts/tasks.py      # task tables; holdout only if RELBENCH_UNSEAL=1
python scripts/baselines.py  # train -> val baselines with bootstrap CIs</pre>
<p class="small">Scripts and the spec are in <code>bankgraph/</code> in this repository. Raw data stays in Drive and is not committed.</p>
</body></html>'''
open('rl/docs/learn/bankgraph_benchmark.html','w').write(P)
