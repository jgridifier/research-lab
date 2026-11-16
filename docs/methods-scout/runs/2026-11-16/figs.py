import json, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT='/workspace/rl-1116/docs/methods-scout/fig/2026-11-16/'
INK='#0F2A23'; AMB='#E8A33D'; TEAL='#1F7A6D'; GRN='#3C8D3F'; MUT='#6B7570'; RED='#B5473A'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':INK})
E=json.load(open('ecofolio/e1_results.json'))
SRC='/workspace/q2-mock-zbb/output/'
def detr(X):
  t=np.arange(X.shape[0]); Z=np.c_[np.ones_like(t),t]; M=np.eye(len(t))-Z@np.linalg.solve(Z.T@Z,Z.T); return M@X
# ---- fig 1: Taylor / mean-variance extrapolation plot
fig,axs=plt.subplots(1,2,figsize=(12,5))
for ax,f,lab in zip(axs,['Corning_mock','MorganStanley_mock'],['Corning mock (778 programs, FY2020–25)','Morgan Stanley mock (1,404 programs, FY2021–25)']):
  h=pd.read_csv(SRC+f+'/history.csv'); w=h.pivot(index='fiscal_year',columns='program_id',values='actual_usd').dropna(axis=1)/1e6
  X=w.values; m=X.mean(0); v=detr(X).var(0,ddof=1); tot=X.sum(1); mt=tot.mean(); vt=detr(tot[:,None]).var(ddof=1)
  A=E[f]['A1']; a=A['taylor_detr']['a']; z=A['taylor_detr']['z']
  ax.scatter(np.log10(m),np.log10(v),s=6,alpha=.35,color=TEAL,lw=0,label='one program (mean, detrended variance)')
  xs=np.linspace(np.log10(m.min()),np.log10(mt)+.1,50); ax.plot(xs,(a+z*xs*np.log(10))/np.log(10),color=INK,lw=2,label=f'Taylor fit, z = {z:.2f}, extrapolated')
  # avg-CV implicit z=2 line: CV fixed at the average program CV
  cvbar=np.mean(np.sqrt(v)/m); ax.plot(xs,np.log10((cvbar*10**xs)**2),color=AMB,lw=2,ls='--',label='average-CV assumption (z = 2)')
  ax.scatter([np.log10(mt)],[np.log10(vt)],s=90,color=RED,edgecolor=INK,zorder=5,label='actual portfolio total')
  ax.axvline(np.log10(mt),color=MUT,lw=.8,ls=':')
  ax.set_title(lab,fontsize=11,color=INK,loc='left'); ax.set_xlabel('log10 mean annual spend ($M)'); ax.set_ylabel('log10 detrended variance ($M²)')
  pe_mv=A['pe_mv_detr']['pe']; pe_cv=A['pe_cv_detr']
  ax.text(.02,.97,f"mean-variance PE = {pe_mv:.2f}\naverage-CV PE = {pe_cv:.2f}",transform=ax.transAxes,va='top',fontsize=10,family='monospace',bbox=dict(fc='white',ec=INK))
axs[0].legend(loc='lower right',fontsize=8,frameon=False)
fig.suptitle('Taylor’s power law on SYNTHETIC mock program budgets: the portfolio sits near the z < 2 line, far below the z = 2 line',fontsize=11,x=.01,ha='left',color=INK)
fig.tight_layout(); fig.savefig(OUT+'eco_taylor.png',dpi=130); plt.close()
# ---- fig 2: segment PE comparison
rows=[]
for f,tag in [('Corning_mock','Corning mock'),('MorganStanley_mock','MS mock')]:
  for s in E[f]['A1']['segments']: rows.append(dict(firm=tag,**s))
S=pd.DataFrame(rows).sort_values(['firm','z']); y=np.arange(len(S))
fig,ax=plt.subplots(figsize=(10,6))
ax.hlines(y,S.pe_mv,S.pe_cv,color=MUT,lw=1.5)
ax.scatter(S.pe_cv,y,color=AMB,edgecolor=INK,s=60,zorder=3,label='average-CV PE (assumes z = 2)')
ax.scatter(S.pe_mv,y,color=TEAL,edgecolor=INK,s=60,zorder=3,label='mean-variance PE (uses fitted z)')
ax.scatter(S.pe_mv_true,y,marker='x',color=RED,s=40,zorder=4,label='mean-variance PE on noise-free true levels')
ax.set_yticks(y); ax.set_yticklabels([f"{r.firm}: {r.segment[:30]}  (z = {r.z:.2f}, n = {r.n})" for r in S.itertuples()],fontsize=8.5)
ax.axvline(1,color=INK,lw=.8,ls=':'); ax.set_xscale('log'); ax.set_xlabel('portfolio effect (×; 1 = no stabilisation beyond one equal-sized program)')
ax.legend(fontsize=8.5,frameon=False,loc='lower right'); ax.set_title('Segment portfolio effects: the two measures agree only where z ≈ 2',loc='left',fontsize=11,color=INK)
fig.tight_layout(); fig.savefig(OUT+'eco_segments.png',dpi=130); plt.close()
# ---- fig 3: planted clusters, PE percentile vs mean pairwise-correlation percentile
fig,axs=plt.subplots(1,2,figsize=(12,4.6))
for f,c in [('Corning_mock',TEAL),('MorganStanley_mock',AMB)]:
  sc=pd.DataFrame(E[f]['A2']['screen']); axs[0].scatter(sc.rho_pct,sc.pe_pct,s=14+40*sc.share_cluster,color=c,alpha=.6,edgecolor=INK,lw=.3,label=f.replace('_mock',' mock')+' label groups')
  pl=pd.DataFrame(E[f]['A2']['planted'])
  for r in pl.itertuples(): axs[0].scatter(r.rho_pct,r.pe_pct,marker='*',s=220,color=RED,edgecolor=INK,zorder=5); axs[0].annotate(f"{r.cluster} ({r.subset})",(r.rho_pct,r.pe_pct),fontsize=7,xytext=(-150,0),textcoords='offset points',arrowprops=dict(arrowstyle='-',color=MUT,lw=.5))
axs[0].set_xlabel('mean pairwise YoY correlation, percentile vs random same-size sets'); axs[0].set_ylabel('mean-variance PE, percentile vs random sets'); axs[0].legend(fontsize=8,frameon=False,loc='center left')
axs[0].set_title('Screen: planted clusters (★) all sit at the far right (correlation),\nbut spread out vertically (PE)',loc='left',fontsize=10,color=INK)
for f,c in [('Corning_mock',TEAL),('MorganStanley_mock',AMB)]:
  s=E[f]['A2']['shuffle_null']; axs[1].errorbar([s['null_median']],[f.replace('_mock','')],xerr=[[s['null_median']-s['null_q05']],[s['null_q95']-s['null_median']]],fmt='o',color=c,capsize=5,label='year-shuffle null (median, 5–95%)' if c==TEAL else None)
  axs[1].scatter([s['obs']],[f.replace('_mock','')],marker='D',s=70,color=RED,edgecolor=INK,zorder=5,label='observed' if c==TEAL else None)
axs[1].set_xscale('log'); axs[1].set_xlabel('mean-variance PE (log scale)'); axs[1].legend(fontsize=8,frameon=False); axs[1].set_title('Whole portfolio vs a null that keeps each program’s\nmean and variance but breaks co-movement (999 shuffles)',loc='left',fontsize=10,color=INK)
fig.tight_layout(); fig.savefig(OUT+'eco_screen.png',dpi=130); plt.close()
# ---- PIM figures
T=pd.read_csv('pim/pim_results.csv')
nice={'drawdown':'SA CET1 drawdown','income_pretax_net_rate':'SA pre-tax income','scb':'SCB','gap_dd':'SA − Adverse drawdown gap','dd_A':'Adverse drawdown','gap_pt':'Adverse − SA pre-tax gap'}
sel=[0,1,2,3,4,5,6,9,10,11,12,13,14,17,18]
D=T.loc[sel].copy(); D['lab']=[f"{r.analysis[3:]} · {r.outcome} ~ {nice.get(r.covariate,r.covariate)}" for r in D.itertuples()]
D['lo']=1/(1+np.exp(-np.log(D.PI_lo/(1-D.PI_lo))*D.iqr)); D['hi']=1/(1+np.exp(-np.log(D.PI_hi/(1-D.PI_hi))*D.iqr))
fig,ax=plt.subplots(figsize=(11,6.4)); y=np.arange(len(D))[::-1]
for yy,r in zip(y,D.itertuples()):
  c=TEAL if r.analysis.startswith('B1') else AMB
  ax.plot([r.lo,r.hi],[yy,yy],color=c,lw=2.5); ax.scatter([r.PI_iqr],[yy],color=c,edgecolor=INK,s=55,zorder=3)
  ax.text(1.0,yy,f"p={r.p_perm:.3f}",fontsize=7.5,va='center',family='monospace',transform=ax.get_yaxis_transform())
ax.axvline(.5,color=INK,lw=.8,ls=':'); ax.set_yticks(y); ax.set_yticklabels(D.lab,fontsize=8); ax.set_xlim(0,1)
ax.set_xlabel('probabilistic index for a one-IQR difference: P(the firm higher on the covariate has the higher payout)')
ax.set_title('Within-test-year PIM effects, firm-block bootstrap 95% CIs (B1 teal, B2 amber)\np = within-year permutation (499)',loc='left',fontsize=10,color=INK)
fig.tight_layout(); fig.savefig(OUT+'pim_forest.png',dpi=130); plt.close()
# composition
fig,axs=plt.subplots(1,2,figsize=(12,4.2))
for ax,cov in zip(axs,['drawdown','scb']):
  B=T[(T.analysis.str.startswith('B3'))&(T.covariate==cov)&(T.outcome.isin(['div_rwa','bb_rwa','div_share']))]
  lab=[f"{r.outcome.replace('div_rwa','dividends/RWA').replace('bb_rwa','net buybacks/RWA').replace('div_share','dividend share')} · {r.analysis[3:]}" for r in B.itertuples()]
  y=np.arange(len(B))[::-1]
  lo=1/(1+np.exp(-np.log(B.PI_lo/(1-B.PI_lo))*B.iqr)); hi=1/(1+np.exp(-np.log(B.PI_hi/(1-B.PI_hi))*B.iqr))
  cols=[TEAL if 'div_rwa' in o else (AMB if 'bb' in o else GRN) for o in B.outcome]
  ax.hlines(y,lo,hi,color=cols,lw=2.5); ax.scatter(B.PI_iqr,y,c=cols,edgecolor=INK,s=55,zorder=3); ax.axvline(.5,color=INK,lw=.8,ls=':')
  for yy,r in zip(y,B.itertuples()): ax.text(1.0,yy,f"p={r.p_perm:.3f} Holm {r.holm_perm:.2f}",fontsize=7,va='center',family='monospace',transform=ax.get_yaxis_transform())
  ax.set_yticks(y); ax.set_yticklabels(lab,fontsize=8); ax.set_xlim(.2,.8); ax.set_xlabel(f'PI for a one-IQR difference in {nice[cov]}')
axs[0].set_title('Q3.5: which leg of payouts lines up with the stress ranking?',loc='left',fontsize=10,color=INK)
fig.tight_layout(); fig.savefig(OUT+'pim_mix.png',dpi=130); plt.close()
tr=pd.read_csv('pim/pim_trim.csv')
fig,ax=plt.subplots(figsize=(7.5,4))
ax.plot(100*tr.trim,100*tr.ols/tr.ols.iloc[0],'o-',color=AMB,label='OLS slope (year FE), % of untrimmed')
ax.plot(100*tr.trim,100*(tr.pim_PI-.5)/(tr.pim_PI.iloc[0]-.5),'s-',color=TEAL,label='PIM effect (PI − 0.5), % of untrimmed')
ax.set_xlabel('% of most extreme payout/net-income ratios removed'); ax.set_ylabel('% of full-sample effect'); ax.set_ylim(0,120); ax.legend(frameon=False,fontsize=9)
ax.set_title('Payout / net income ~ SA drawdown: OLS loses 43% of its slope\nwhen 8 of 360 firm-years are trimmed; PIM moves < 2%',loc='left',fontsize=10,color=INK)
fig.tight_layout(); fig.savefig(OUT+'pim_trim.png',dpi=130); plt.close()
print('ok')
