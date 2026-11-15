import json, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':160,'savefig.bbox':'tight',
 'savefig.facecolor':'white','axes.labelcolor':'#1c150d','text.color':'#1c150d','axes.edgecolor':'#1c150d','xtick.color':'#1c150d','ytick.color':'#1c150d'})
INK='#1c150d'; AMB='#e8902e'; TEAL='#1f9e8e'; RED='#df5236'; BLUE='#3b6fb6'; GREY='#9a9389'
O='/workspace/ms-1114/q3v/out/'; F='/workspace/ms-1114/fig/'
R=json.load(open(O+'idr_results.json')); Q=pd.read_csv(O+'idr_A1_quantiles.csv'); P=pd.read_csv(O+'q3_points_aggregate_safe.csv')
src='Sources: Fed stress-test results 2013–2025 (severely adverse); FR Y-9C HI-A via FFIEC NIC. Public data.'
# fig1: fan
fig,ax=plt.subplots(1,2,figsize=(10,3.8))
a=ax[0]; a.scatter(P.dd_pct,P.y_pct,s=8,color=GREY,alpha=.6,label='firm-years (n=360)')
a.fill_between(Q.dd_pct,Q.X1,Q.X5,color=TEAL,alpha=.15,label='IDR 10–90%'); a.fill_between(Q.dd_pct,Q.X2,Q.X4,color=TEAL,alpha=.3,label='IDR 25–75%'); a.plot(Q.dd_pct,Q.X3,color=INK,lw=1.8,label='IDR median')
a.set_xlabel('CET1 drawdown, percentile within test year (worse →)'); a.set_ylabel('realized payout / RWA, percentile within year'); a.legend(fontsize=7,frameon=False,loc='lower left'); a.set_title('Payout rank vs stress drawdown rank',fontsize=10,loc='left')
Rq=pd.read_csv(O+'idr_A1raw_quantiles.csv'); a=ax[1]; a.scatter(P.drawdown,P.payout_rwa,s=8,color=GREY,alpha=.6)
a.fill_between(Rq.drawdown,Rq.X1,Rq.X5,color=AMB,alpha=.15); a.fill_between(Rq.drawdown,Rq.X2,Rq.X4,color=AMB,alpha=.35); a.plot(Rq.drawdown,Rq.X3,color=INK,lw=1.8)
a.set_xlim(-1,10); a.set_ylim(-1.5,5); a.set_xlabel('CET1 drawdown, start − minimum (pp)'); a.set_ylabel('payout / RWA (%)'); a.set_title('Raw scale (antitonic IDR)',fontsize=10,loc='left')
fig.text(0,-.04,src,fontsize=7,color=GREY); fig.savefig(F+'q3_idr_fan.png'); plt.close()
# fig2: skill bars
rows=[('2013–25: drawdown pct','A1','pct_drawdown'),('2013–25: pre-tax income pct','A1','pct_pretax'),('2013–25: drawdown (raw)','A1','raw_drawdown'),
      ('2021–25: SCB pct','A2','pct_scb'),('2021–25: drawdown pct','A2','pct_drawdown'),('2021–25: pre-tax pct','A2','pct_pretax'),('2021–25: SCB + drawdown','A2','pct_scb_dd'),('2021–25: SCB (raw)','A2','raw_scb'),('2021–25: drawdown (raw)','A2','raw_drawdown')]
fig,a=plt.subplots(figsize=(10,3.6)); x=np.arange(len(rows))
si=[R[g][k]['skill_idr'] for _,g,k in rows]; so=[R[g][k]['skill_ols'] for _,g,k in rows]; q=[R[g][k]['null_q95'] for _,g,k in rows]
a.bar(x-.18,si,.36,color=TEAL,label='IDR (no tuning)'); a.bar(x+.18,so,.36,color=AMB,label='OLS + normal errors')
a.scatter(x-.18,q,marker='_',s=200,color=RED,lw=2,label='IDR permutation null, 95th pct'); a.axhline(0,color=INK,lw=.6)
a.set_xticks(x); a.set_xticklabels([r[0] for r in rows],rotation=25,ha='right',fontsize=7.5); a.set_ylabel('CRPS skill vs climatology\n(leave-one-test-year-out)'); a.legend(fontsize=7.5,frameon=False)
fig.text(0,-.2,src,fontsize=7,color=GREY); fig.savefig(F+'q3_skill.png'); plt.close()
# fig3: era medians + kendall
A3=R['A3']; fig,ax=plt.subplots(1,2,figsize=(10,3.4)); g=A3['grid']
ax[0].plot(g,[v[0] for v in A3['pre_median']],'o-',color=BLUE,label='2013–2019 fit'); ax[0].plot(g,[v[0] for v in A3['post_median']],'o-',color=RED,label='2021–2025 fit')
ax[0].set_xlabel('drawdown percentile'); ax[0].set_ylabel('IDR median payout percentile'); ax[0].legend(frameon=False,fontsize=8); ax[0].set_title('After 2020: flat in the middle, harsher in the worst decile',fontsize=10,loc='left')
k=pd.DataFrame(A3['kendall_payout_rank_yoy']); ax[1].bar(k.year,k.tau,color=[GREY if y==2020 else (RED if y>2020 else BLUE) for y in k.year]); ax[1].set_ylim(0,1); ax[1].set_ylabel('Kendall τ, payout/RWA rank, year vs prior'); ax[1].set_title('Payout ranking stability',fontsize=10,loc='left')
fig.text(0,-.06,src,fontsize=7,color=GREY); fig.savefig(F+'q3_eras.png'); plt.close()
print('ok')
