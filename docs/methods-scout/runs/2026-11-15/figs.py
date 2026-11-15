import json, pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
INK='#0F2A23'; C=['#0F766E','#B45309','#7C3AED','#B91C1C','#1D4ED8']
# ---- CCM
R=json.load(open('ccm/ccm_results.json'))
keys=['d_lev -> d_spread','dl_fails -> d_spread','dl_fails -> dl_dvp','d_lev -> dl_dvp','d_lev -> dl_fails','dl_fails -> d_lev']
LAB={'d_lev':'TFF lev-fund net short','dl_fails':'financing fails','dl_dvp':'DVP volume','d_spread':'DVP−tri-party spread'}
def lab(k): a,b=k.split(' -> '); return f'{LAB[a]} → {LAB[b]}'
fig,axs=plt.subplots(2,3,figsize=(12,6.4),sharey=True)
for ax,k,c in zip(axs.flat,keys,C+['#555']):
    cv=R['curves'][k]; r=R['ccm'][k]
    ax.plot(cv['LibSize'],cv['rho'],'-o',color=c,ms=3)
    ax.axhspan(-1,r['null_q95'],color='#ddd',alpha=.6,lw=0)
    ax.axhline(0,color='#999',lw=.6)
    ax.set_title(lab(k)+f"\nρ={r['rho_L350']:.2f}, shift-null p={r['p_shift']:.3f}",fontsize=9)
    ax.set_ylim(-.1,.42); ax.set_xlabel('library size (weeks)')
axs[0,0].set_ylabel('cross-map skill ρ'); axs[1,0].set_ylabel('cross-map skill ρ')
fig.suptitle('Convergent cross mapping, weekly 2019-01 → 2025-12 (n=364). Grey: below 95th pct of 200 circular-shift surrogates of the driver',fontsize=10)
fig.tight_layout(); fig.savefig('fig/ccm_convergence.png',dpi=130); plt.close()
fig,ax=plt.subplots(figsize=(7.5,3.6))
for k,c in zip(keys[:4],C):
    lg=R['ccm'][k]['lag_rho']; xs=sorted(int(x) for x in lg); ax.plot(xs,[lg[str(x)] for x in xs],'-o',color=c,label=lab(k),ms=3)
ax.axvline(0,color='#999',lw=.6); ax.set_xlabel('cross-map lag Tp (weeks; negative = driver’s past)'); ax.set_ylabel('ρ at L=350'); ax.legend(fontsize=8,frameon=False)
ax.set_title('Lag scan (Ye et al. 2015): where cross-map skill peaks',fontsize=10); fig.tight_layout(); fig.savefig('fig/ccm_lag.png',dpi=130); plt.close()
# ---- kairos baseline stacked area
M=pd.read_csv('kairos/mix_monthly.csv',index_col=0); S=M.div(M.sum(1),axis=0); idx=pd.to_datetime(S.index)
order=['DVP_G30','GCF_T30','GCF_G30','TRI_ON','GCF_ON','TRI_G30','TRI_T30','DVP_T30','DVP_ON']
cols=plt.cm.tab10(np.arange(9))
fig,ax=plt.subplots(figsize=(9,4)); ax.stackplot(idx,[S[c] for c in order],labels=order,colors=cols,alpha=.9)
ax.axvline(pd.Timestamp('2025-08-14'),color='k',lw=.8,ls='--'); ax.text(pd.Timestamp('2025-08-20'),0.02,'OFR tenor\nbuckets split',fontsize=7)
ax.set_ylim(0,1); ax.set_ylabel('share of monthly volume'); ax.legend(fontsize=7,ncol=1,bbox_to_anchor=(1.01,1),loc='upper left',frameon=False)
ax.set_title('Standard view: stacked shares of the 9 venue × tenor segments (calendar order)',fontsize=10); fig.tight_layout(); fig.savefig('fig/kairos_stacked_baseline.png',dpi=130); plt.close()
# mix clock
mc=pd.read_csv('kairos/mixclock.csv'); oos=pd.read_csv('kairos/mixclock_oos.csv')
fig,ax=plt.subplots(1,2,figsize=(11,4))
ax[0].plot(mc.yr,mc.yr,color='#999',lw=.8,label='calendar (perfect clock)')
ax[0].plot(mc.yr,mc.mix_date,color=C[0],label='mix date, fit on all months')
ax[0].plot(oos.yr,oos.pred,color=C[1],label='walk-forward: fit ≤2022, predict 2023→')
ax[0].axvline(2025+7.5/12,color='k',lw=.7,ls='--'); ax[0].set_xlabel('calendar year'); ax[0].set_ylabel('event date implied by the mix'); ax[0].legend(fontsize=8,frameon=False)
ax[0].set_title('“Mix clock”: Bellanger–Husi event dates on repo composition',fontsize=10)
pf=pd.read_csv('kairos/formpf_monthly.csv',index_col=0); d=mc.set_index('month').join(pf,how='inner')
d['speed']=d.mix_date.diff(12); d['g']=np.log(d.Total_Total).diff(12).shift(3)
z=d[['g','speed']].dropna()
ax[1].scatter(z.g,z.speed,s=12,c=pd.to_datetime(z.index).year,cmap='viridis'); ax[1].axhline(1,color='#999',lw=.6)
ax[1].set_xlabel('Form PF total borrowing growth, 12-mo log change, 3 months earlier'); ax[1].set_ylabel('mix speed (mix-years per 12 months)')
L=json.load(open('kairos/link_pf.json'))['tests']['g_tot_lead3_vs_mix_speed']
ax[1].set_title(f"Borrowing growth vs mix speed: r={L['r']:.2f}, shift-null p={L['p_shift']:.4f} (n={L['n']})",fontsize=10)
fig.tight_layout(); fig.savefig('fig/kairos_mixclock.png',dpi=130); plt.close()
print('ok')
