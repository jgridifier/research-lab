import json, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':160,'savefig.bbox':'tight',
 'savefig.facecolor':'white','axes.labelcolor':'#1c150d','text.color':'#1c150d','axes.edgecolor':'#1c150d','xtick.color':'#1c150d','ytick.color':'#1c150d'})
INK='#1c150d'; AMB='#e8902e'; TEAL='#1f9e8e'; RED='#df5236'; BLUE='#3b6fb6'; GREY='#9a9389'
O='/workspace/ms-1114/q1/out/'; F='/workspace/ms-1114/fig/'
R=json.load(open(O+'crqa_results_v3.json'))
srcW='Sources: NY Fed primary-dealer fails (weekly); OFR U.S. Repo Markets Data Release (daily → Thu–Wed means). Public aggregates, 2018-06 to 2026-09.'
def prof(a,x,lags,title,col):
    o=np.array(x['obs']); m=np.array(x['null_mean']); q=np.array(x['null_q95'])
    a.fill_between(lags,m,q,color=GREY,alpha=.25,label='circular-shift null: mean to 95th pct'); a.plot(lags,m,color=GREY,lw=1)
    a.plot(lags,o,'o-',color=col,ms=3,lw=1.5,label='observed'); a.axvline(0,color=INK,lw=.5,ls=':')
    a.set_title(title,fontsize=9,loc='left'); a.set_xlabel('lag (positive = first series leads)')
fig,ax=plt.subplots(1,3,figsize=(12,3.4),sharey=True); L=np.arange(-13,14)
prof(ax[0],R['A1']['fin_vs_spread']['anti'],L,'Dealer financing fails vs DVP−tri-party spread\nANTI-recurrence (high fails ↔ low spread)',RED)
prof(ax[1],R['A1']['fin_vs_dvpgrowth']['co'],L,'Dealer financing fails vs DVP volume growth (4-wk)\nco-recurrence',TEAL)
prof(ax[2],R['A1']['otr_vs_fin']['co'],L,'On-the-run 5y+10y fails vs financing fails\nco-recurrence (sanity check)',BLUE)
ax[0].set_ylabel('share of weeks in the same quintile'); ax[0].legend(fontsize=7,frameon=False,loc='lower left')
fig.text(0,-.08,srcW,fontsize=7,color=GREY); fig.savefig(F+'q1_drp_weekly.png'); plt.close()
w=pd.read_csv(O+'wincrqa_v3.csv',parse_dates=['start','end']); mid=w.start+(w.end-w.start)/2
fig,ax=plt.subplots(2,1,figsize=(11,4.6),sharex=True)
a=ax[0]; a.plot(mid,w.rr0_anti,'-',color=RED,lw=1.6,label='same-week anti-recurrence (fails ↔ spread), local quintiles'); a.plot(mid,w.null_rr0_anti,color=GREY,lw=1,label='circular-shift null mean')
s=w.p_rr0_anti<.05; a.scatter(mid[s],w.rr0_anti[s],s=12,color=RED,zorder=3,label='window p < 0.05 (199 shifts)'); a.set_ylabel('rr₀'); a.legend(fontsize=7,frameon=False,ncol=3,loc='upper left'); a.set_ylim(0,.65)
a=ax[1]; a.plot(mid,w.rho_spread,color=INK,lw=1.4,label='Spearman ρ, fails vs spread'); a.plot(mid,w.rho_dvp,color=TEAL,lw=1.2,label='Spearman ρ, fails vs DVP growth'); a.axhline(0,color=GREY,lw=.6); a.legend(fontsize=7,frameon=False,ncol=2); a.set_ylabel('52-week ρ')
fig.text(0,-.04,srcW+' 52-week windows, 4-week step, plotted at window midpoint.',fontsize=7,color=GREY); fig.savefig(F+'q1_windows.png'); plt.close()
M=pd.read_csv('/workspace/ms-1114/q1/monthly.csv'); M['d']=pd.to_datetime(M.period)
fig,ax=plt.subplots(1,3,figsize=(12,3.4)); a=ax[0]
a.plot(M.d,M['Secured_Prime Broker'],color=INK,lw=1.6,label='prime-broker borrowings'); a.plot(M.d,M['Secured_Reverse Repo'],color=AMB,lw=1.6,label='"reverse repo" borrowings'); a.plot(M.d,M['Secured_Other Secured'],color=GREY,lw=1.2,label='other secured')
a.set_ylabel('$ billions'); a.set_title('Form PF tab 8.27: qualifying hedge fund\nborrowings by creditor type (monthly)',fontsize=9,loc='left'); a.legend(fontsize=7,frameon=False)
L6=np.arange(-6,7)
prof(ax[1],R['A3']['pb_vs_failsfin']['anti'],L6,'PB borrowing growth (3-mo) vs financing fails\nanti-recurrence, best of 8 PB tests',INK)
prof(ax[2],R['A3']['revrepo_vs_dvpout']['co'],L6,'Form PF "reverse repo" borrowing growth vs DVP\noutstanding growth (3-mo), co-recurrence',AMB)
ax[1].set_ylabel('share of months in the same quintile'); ax[1].legend(fontsize=7,frameon=False,loc='upper left')
fig.text(0,-.08,'Sources: SEC Private Funds Statistics (Form PF tab 8.27); OFR repo; NY Fed fails. Public aggregates. Lag in months.',fontsize=7,color=GREY); fig.savefig(F+'q1_monthly.png'); plt.close()
print('ok')
