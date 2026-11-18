import json, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, sys
sys.path.insert(0,'eca'); from eca import rates
OUT='/workspace/rl-scout-1117/docs/methods-scout/fig/2026-11-17/'
AMB,TEAL,INK,MUT,RED='#e8902e','#1f9e8e','#1c150d','#6f5f46','#df5236'
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
X=pd.read_csv('eca/q1_weekly.csv',parse_dates=['date'],index_col='date'); M=json.load(open('eca/q1_more.json'))
# 1 standard: Pearson cross-correlation
S=pd.DataFrame(M['pearson']); s=S[S.pair=='dl_fails~d_lev']
Xl=X[X.index<='2025-12-31']; v=pd.concat([Xl.dl_fails,Xl.d_lev],axis=1).dropna().values; rng=np.random.default_rng(1)
null=[abs(np.corrcoef(v[:,0],np.roll(v[:,1],k))[0,1]) for k in rng.integers(8,len(v)-8,1999)]; b=np.quantile(null,0.95)
fig,ax=plt.subplots(figsize=(5,3.2)); ax.bar(s.lag,s.r,color=[AMB if p<0.05 else '#cbbd9f' for p in s.p],edgecolor=INK)
ax.axhspan(-b,b,color='#eee4cf',zorder=0,label='95% circular-shift null'); ax.axhline(0,color=INK,lw=.8)
ax.set_xlabel('lag (weeks): positioning change leads fails change'); ax.set_ylabel('Pearson r'); ax.set_title('Usual tool: cross-correlation of weekly changes',fontsize=10)
ax.legend(frameon=False,fontsize=8,loc='upper right'); ax.set_ylim(-.3,.3); fig.tight_layout(); fig.savefig(OUT+'eca_std_xcorr.png'); plt.close()
# 2 ECA: precursor rate by exact lag, unwind vs build
D=pd.DataFrame(M['lag_decomp']); fig,ax=plt.subplots(figsize=(5,3.2))
for nm,col,off in [('levunwind',TEAL,-0.18),('levbuild',AMB,0.18)]:
    d=D[(D.A=='fails')&(D.B==nm)]; ax.bar(d.tau+off,d.rp,width=.34,color=col,edgecolor=INK,label={'levunwind':'big unwind week (bottom 10%)','levbuild':'big build week (top 10%)'}[nm])
    for t,r,p in zip(d.tau,d.rp,d.p): ax.text(t+off,r+.008,f'p={p:.3f}',ha='center',fontsize=7)
nm=D[(D.A=='fails')&(D.B=='levunwind')].null_med.mean(); ax.axhline(nm,color=RED,ls='--',lw=1.2,label=f'random placement ≈ {nm:.2f}')
ax.set_xticks([0,1,2]); ax.set_xticklabels(['same week','1 week before','2 weeks before']); ax.set_ylabel('share of fails spikes')
ax.set_title('ECA: fails spikes preceded by a leveraged-fund move',fontsize=10); ax.legend(frameon=False,fontsize=7.5); ax.set_ylim(0,.33); fig.tight_layout(); fig.savefig(OUT+'eca_rates.png'); plt.close()
# 3 raster
E=pd.read_csv('eca/events_q90.csv',parse_dates=['date'],index_col='date'); E=E[E.index<='2025-12-31']
fig,ax=plt.subplots(figsize=(7,2.4)); f=E.index[E.fails==1]; u=E.index[E.levunwind==1]; co=pd.to_datetime(M['coincident_weeks'])
ax.vlines(f,0.55,0.95,color='#cbbd9f',lw=2); ax.vlines(u,0.05,0.45,color='#cbbd9f',lw=2)
ax.vlines(co,0.55,0.95,color=RED,lw=2.4); 
cu=[d for d in u if any(((c-d).days in (0,7)) for c in co)]; ax.vlines(cu,0.05,0.45,color=TEAL,lw=2.4)
ax.set_yticks([.25,.75]); ax.set_yticklabels(['lev-fund\nunwind','fails\nspike']); ax.set_ylim(0,1); ax.set_title('Event weeks 2018–2025; coloured = coincidence (same or previous week)',fontsize=9.5)
fig.tight_layout(); fig.savefig(OUT+'eca_raster.png'); plt.close()
# 4 rolling
R=pd.DataFrame(M['rolling']); R['end']=pd.to_datetime(R.end); fig,ax=plt.subplots(figsize=(6,2.8))
ax.plot(R.end,R.rp,color=TEAL,lw=2,label='share of fails spikes with an unwind (104-wk window)'); ax.plot(R.end,R.exp_random,color=RED,ls='--',label='expected if placed at random')
ax.set_ylim(0,.7); ax.legend(frameon=False,fontsize=8); ax.set_title('Time-resolved coincidence rate',fontsize=10); fig.tight_layout(); fig.savefig(OUT+'eca_rolling.png'); plt.close()
# STATIS
O=json.load(open('statis/q3_statis.json')); yrs=O['years']
st=pd.DataFrame(O['std_rho_payout_drawdown']); fig,ax=plt.subplots(figsize=(5,3.2))
ax.errorbar(st.year,st.rho,yerr=[st.rho-st.lo,st.hi-st.rho],fmt='o',color=AMB,ecolor='#cbbd9f',mec=INK,capsize=2); ax.axhline(0,color=INK,lw=.8); ax.axvline(2019.5,color=MUT,ls=':')
ax.set_title('Usual tool: one correlation per year\n(payout/RWA vs CET1 drawdown, 95% firm bootstrap)',fontsize=9.5); ax.set_ylabel('Spearman ρ'); fig.tight_layout(); fig.savefig(OUT+'statis_std.png'); plt.close()
G=np.array(O['year_map']); fig,ax=plt.subplots(figsize=(5,3.6))
for k,y in enumerate(yrs): ax.scatter(G[k,0],G[k,1],s=60,color=AMB if y<2020 else TEAL,edgecolor=INK,zorder=3); ax.annotate(str(y),(G[k,0],G[k,1]),xytext=(4,3),textcoords='offset points',fontsize=8)
ax.plot(G[:,0],G[:,1],color='#cbbd9f',lw=.8,zorder=1)
ax.set_xlabel('axis 1 (common structure)'); ax.set_ylabel('axis 2 (how a year differs)'); ax.set_title('STATIS interstructure: each dot = one test year\'s whole\ncorrelation pattern (amber 2013–19, teal 2020–25)',fontsize=9.5)
fig.tight_layout(); fig.savefig(OUT+'statis_years.png'); plt.close()
F=np.array(O['F']); Fk=np.array(O['Fk']); LAB=O['vars']; fig,ax=plt.subplots(figsize=(6.2,4.6))
for i,l in enumerate(LAB):
    ax.plot(Fk[:,i,0],Fk[:,i,1],color='#d9c8a6',lw=.8,zorder=1)
    ax.scatter(Fk[:,i,0],Fk[:,i,1],s=10,c=[AMB if y<2020 else TEAL for y in yrs],zorder=2)
    ax.scatter(F[i,0],F[i,1],s=70,color=INK,zorder=3); ax.annotate(l,(F[i,0],F[i,1]),xytext=(5,4),textcoords='offset points',fontsize=8.5,weight='bold')
ax.axhline(0,color=MUT,lw=.5); ax.axvline(0,color=MUT,lw=.5)
t=O['tau']; ax.set_xlabel(f'compromise axis 1 ({100*t[0]:.0f}%)'); ax.set_ylabel(f'axis 2 ({100*t[1]:.0f}%)')
ax.set_title('Compromise map of the 7 variables; small dots = each year\'s position\n(amber 2013–19, teal 2020–25)',fontsize=9.5); fig.tight_layout(); fig.savefig(OUT+'statis_vars.png'); plt.close()
cs=O['contiguous_splits']; fig,ax=plt.subplots(figsize=(5,3))
ax.plot([c[0] for c in cs],[c[1] for c in cs],'o-',color=TEAL,mec=INK); ax.axhline(0,color=INK,lw=.8)
ax.set_xlabel('first year of the "after" era'); ax.set_ylabel('within − between era RV'); ax.set_title('Where does the structure break? (contiguous cuts)',fontsize=10)
fig.tight_layout(); fig.savefig(OUT+'statis_split.png'); plt.close()
W=json.load(open('statis/q3_firms.json'))['w2']; F2=np.array(W['F']); Fk2=np.array(W['Fk']); top=[d['firm'] for d in W['top'][:4]]
fig,ax=plt.subplots(figsize=(6,4.4))
for i,nm in enumerate(W['firms']):
    hl=nm in top; ax.plot(Fk2[:,i,0],Fk2[:,i,1],color=RED if hl else '#d9c8a6',lw=1.4 if hl else .7,zorder=2 if hl else 1)
    ax.scatter(Fk2[-1,i,0],Fk2[-1,i,1],s=14,color=RED if hl else '#cbbd9f',zorder=3)
    if hl: ax.annotate(nm.replace(' Corporation','').replace(' Holding LLC','').replace(' LLC',''),(Fk2[-1,i,0],Fk2[-1,i,1]),xytext=(4,3),textcoords='offset points',fontsize=8)
ax.set_title('Partial triadic view, 21 firms in every test 2022–25:\npath of each firm 2022→2025 (red = 4 longest)',fontsize=9.5); ax.set_xlabel('compromise axis 1'); ax.set_ylabel('axis 2')
fig.tight_layout(); fig.savefig(OUT+'statis_firms.png'); plt.close()
print('ok')
