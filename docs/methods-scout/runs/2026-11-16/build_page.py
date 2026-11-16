import json, pandas as pd, re, html
SC='../../'
E=json.load(open('ecofolio/e1_results.json')); T=pd.read_csv('pim/pim_results.csv'); X=json.load(open('pim/pim_extra.json')); TR=pd.read_csv('pim/pim_trim.csv')
src=open(SC+'2026-11-15.html').read()
head=src[:src.index('</head>')+7]
head=re.sub(r'<title>.*?</title>','<title>Methods scout · 2026-11-16 · research-lab</title>',head)
head=re.sub(r'<meta name="description" content=".*?">','<meta name="description" content="Methods scout 2026-11-16, aimed at Q2 and Q3: mean-variance portfolio effects and Taylor’s power law (fisheries ecology, ecofolio) on the synthetic mock ZBB datasets; probabilistic index models (biostatistics, pim) on public stress-test results and Y-9C payouts.">',head)
head=head.replace('</style>','  .robust { border-left: 8px solid var(--ink); }\n  .finds { border-left: 8px solid var(--amber); }\n  .robust h3, .finds h3 { margin-top: 0; }\n</style>')
f=lambda v,d=2: f"{v:.{d}f}".replace('-','−')
C=E['Corning_mock']; M=E['MorganStanley_mock']
def segtab():
  r=[]
  for tag,F in [('Corning mock',C),('MS mock',M)]:
    for s in sorted(F['A1']['segments'],key=lambda s:s['z']):
      r.append(f"<tr><td>{tag}: {html.escape(s['segment'])}</td><td class='num'>{s['n']}</td><td class='num'>{f(s['z'])}</td><td class='num'>{f(s['pe_cv'])}</td><td class='num'>{f(s['div_ratio'])}</td><td class='num'><strong>{f(s['pe_mv'])}</strong></td><td class='num'>{f(s['pe_mv_true'])}</td></tr>")
  return '\n'.join(r)
def plantab():
  r=[]
  for tag,F in [('Corning mock',C),('MS mock',M)]:
    for p in F['A2']['planted']:
      r.append(f"<tr><td>{tag}: {p['cluster']} ({p['subset']})</td><td>{p['type'].replace('_','-')}</td><td class='num'>{p['n']}</td><td class='num'>{f(p['pe'])}</td><td class='num'>{f(100*p['pe_pct'],0)}</td><td class='num'>{f(p['rho'])}</td><td class='num'>{f(100*p['rho_pct'],0)}</td></tr>")
  return '\n'.join(r)
nice={'drawdown':'SA CET1 drawdown','income_pretax_net_rate':'SA pre-tax income','scb':'SCB','gap_dd':'SA − Adverse drawdown gap','dd_A':'Adverse drawdown','gap_pt':'Adverse − SA pre-tax gap'}
onice={'payout_rwa':'payout/RWA','payout_rwa_next':'next-year payout/RWA','payout_ni':'payout/net income','div_rwa':'dividends/RWA','bb_rwa':'net buybacks/RWA','div_share':'dividend share','div_share_next':'next-year dividend share'}
def pimtab(rows):
  r=[]
  for i in rows:
    t=T.loc[i]; r.append(f"<tr><td>{html.escape(t.analysis[3:])}</td><td>{onice[t.outcome]} ~ {nice[t.covariate]}</td><td class='num'>{t.n}</td><td class='num'>{f(t.PI,3)} [{f(t.PI_lo,3)}, {f(t.PI_hi,3)}]</td><td class='num'><strong>{f(t.PI_iqr,2)}</strong></td><td class='num'>{f(t.p_perm,3)}</td><td class='num'>{f(t.holm_perm,3)}</td><td class='num'>{f(t.ols_b,3)} (t {f(t.ols_t,1)})</td></tr>")
  return '\n'.join(r)
PH="<thead><tr><th>Sample</th><th>Model</th><th class='num'>n</th><th class='num'>PI per 1 unit [firm-bootstrap 95%]</th><th class='num'>PI per IQR</th><th class='num'>p (perm)</th><th class='num'>Holm (family)</th><th class='num'>OLS + year FE (cluster t)</th></tr></thead>"
d20=X['dec2020']; g=[r for r in d20 if r['covariate']=='gap_alt'][0]
fr=X['fragility']
body=open('page_body.html').read()
for k,v in {'{SEGTAB}':segtab(),'{PLANTAB}':plantab(),'{PIMB1}':pimtab([0,1,2,3,4,5,6,7,8,9,10]),'{PIMB2}':pimtab([11,12,13,14,15,16,17,18]),'{PIMB3}':pimtab(list(range(19,29))),'{PH}':PH,
  '{DEC_PI}':f(g['PI'],2),'{DEC_P}':f(g['p_perm'],2)}.items(): body=body.replace(k,v)
open(SC+'2026-11-16.html','w').write(head+'\n'+body)
print('written', len(head+body))
