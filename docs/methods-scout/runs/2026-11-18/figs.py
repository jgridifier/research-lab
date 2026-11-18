import json, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, sys
sys.path.insert(0,'hyst'); from hyst import hi_storm
OUT='/workspace/scout/1118/fig/'
AMB,TEAL,INK,MUT,RED='#e8902e','#1f9e8e','#1c150d','#6f5f46','#df5236'
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
PAL=['#1f9e8e','#e8902e','#df5236','#5b6abf','#9c5bb5','#3c8d3c','#b5835a','#c2417a']
# ---------- STEM profile grid (the strongly visual one)
def grid(f,title,fn):
    p=pd.read_csv(f'stem/q2/bout/{f}_actual_c1_profiletable.txt',sep='\t'); g=pd.read_csv(f'stem/q2/bout/{f}_actual_c1_genetable.txt',sep='\t')
    yrs=[c for c in g.columns if c.isdigit()]
    p['sig']=p['Cluster (-1 non-significant)']!=-1; p=p.sort_values(['sig','# Genes Assigned'],ascending=[False,False]).reset_index(drop=True)
    cl={c:i for i,c in enumerate(sorted(p.loc[p.sig,'Cluster (-1 non-significant)'].unique()))}
    fig,axs=plt.subplots(5,10,figsize=(12,6.4)); 
    for ax,(_,r) in zip(axs.flat,p.iterrows()):
        mem=g[g.Profile==r['Profile ID']][yrs].values
        col=PAL[cl[r['Cluster (-1 non-significant)']]%len(PAL)] if r.sig else '#ffffff'
        ax.set_facecolor(col if r.sig else '#ffffff'); ax.patch.set_alpha(0.22 if r.sig else 1)
        for m in mem[:60]: ax.plot(m,color='#8c7b62',lw=.4,alpha=.5)
        mp=np.array([float(x) for x in r['Profile Model'].split(',')]); sc=np.abs(mem).max() if len(mem) else 1
        ax.plot(mp/ (np.abs(mp).max() or 1)*sc*0.8,color=INK if r.sig else '#b8ab92',lw=1.8)
        ax.set_xticks([]); ax.set_yticks([]); 
        for s in ax.spines.values(): s.set_visible(True); s.set_color(INK if r.sig else '#d8cdb8')
        ax.text(0.03,0.97,f"{r['# Genes Assigned']:.0f} vs {r['# Gene Expected']:.0f}",transform=ax.transAxes,fontsize=6.5,va='top',color=INK if r.sig else MUT,fontweight='bold' if r.sig else 'normal')
    fig.suptitle(title,fontsize=11); fig.text(0.5,0.01,'Box = model shape (dark line); grey = programs assigned. "n vs e" = assigned vs expected with years shuffled.\nColoured = significantly over-full (Bonferroni 5%); same colour = merged cluster.',ha='center',fontsize=8,color=MUT)
    fig.tight_layout(rect=(0,0.05,1,0.96)); fig.savefig(OUT+fn); plt.close()
grid('Corning_mock','STEM on the SYNTHETIC Corning-like mock (778 programs, FY2020–25 log actuals): 7 of 50 shapes are real','stem_grid_corning.png')
grid('MorganStanley_mock','STEM on the SYNTHETIC Morgan Stanley-like mock (1,404 programs, FY2021–25): 5 of 50 shapes are real','stem_grid_ms.png')
R=json.load(open('stem/q2/stem_q2_results.json')); E=json.load(open('stem/q2/stem_q2_extra.json'))
# ---------- standard vs STEM: does the tool find structure in pure noise?
fig,axs=plt.subplots(1,2,figsize=(8,3.2))
for ax,f,lab in zip(axs,['Corning_mock','MorganStanley_mock'],['Corning-like mock','MS-like mock']):
    ka,ks=E[f]['kmeans_actual'],E[f]['kmeans_shuffled']; sa,ss=R[f]['actual_c1']['n_sig_profiles'],R[f]['shuffled_c1']['n_sig_profiles']
    x=np.arange(2); ax.bar(x-0.18,[ka['k'],ks['k']],0.34,color='#cbbd9f',edgecolor=INK,label='k-means: clusters returned (best silhouette)')
    ax.bar(x+0.18,[sa,ss],0.34,color=TEAL,edgecolor=INK,label='STEM: significant shapes')
    for xi,v in zip(x-0.18,[ka,ks]): ax.text(xi,v['k']+.2,f"sil {v['silhouette']}",ha='center',fontsize=7)
    for xi,v in zip(x+0.18,[sa,ss]): ax.text(xi,v+.2,str(v),ha='center',fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(['real mock','years shuffled\n(pure noise)']); ax.set_title(lab,fontsize=10); ax.set_ylim(0,12)
axs[0].legend(frameon=False,fontsize=7,loc='upper left'); fig.suptitle('Usual tool always finds clusters; STEM says when shapes are not real',fontsize=10); fig.tight_layout(); fig.savefig(OUT+'stem_vs_kmeans_noise.png'); plt.close()
fig,ax=plt.subplots(figsize=(5,3.2))
ax.bar([0,1],[E['Corning_mock']['kmeans_shuffled']['k'],E['MorganStanley_mock']['kmeans_shuffled']['k']],color='#cbbd9f',edgecolor=INK)
ax.set_xticks([0,1]); ax.set_xticklabels(['Corning-like','MS-like']); ax.set_ylabel('clusters returned'); ax.set_title('Usual tool: k-means on pure noise (years shuffled)',fontsize=10)
for i,f in enumerate(['Corning_mock','MorganStanley_mock']): ax.text(i,E[f]['kmeans_shuffled']['k']+.2,f"silhouette {E[f]['kmeans_shuffled']['silhouette']}",ha='center',fontsize=8)
ax.set_ylim(0,12); fig.tight_layout(); fig.savefig(OUT+'stem_std_kmeans_noise.png'); plt.close()
fig,ax=plt.subplots(figsize=(5,3.2))
ax.bar([0,1],[R['Corning_mock']['shuffled_c1']['n_sig_profiles'],R['MorganStanley_mock']['shuffled_c1']['n_sig_profiles']],color=TEAL,edgecolor=INK)
ax.bar([2.4,3.4],[R['Corning_mock']['actual_c1']['n_sig_profiles'],R['MorganStanley_mock']['actual_c1']['n_sig_profiles']],color=AMB,edgecolor=INK)
ax.set_xticks([0,1,2.4,3.4]); ax.set_xticklabels(['Corning\nnoise','MS\nnoise','Corning\nreal','MS\nreal']); ax.set_ylabel('significant shapes (of 50)'); ax.set_title('STEM: noise gives 0–1 shapes; the mocks give 5–7',fontsize=10); ax.set_ylim(0,12)
fig.tight_layout(); fig.savefig(OUT+'stem_noise_null.png'); plt.close()
# ---------- budget as a replicate
fig,ax=plt.subplots(figsize=(5.6,3.2)); x=np.arange(2)
for i,(nm,lab,col) in enumerate([('actual','actuals only','#cbbd9f'),('actrep','actuals + budget as replicate',TEAL)]):
    v=[E[f][f'agree_{nm}']['share_same_profile_as_true'] for f in ['Corning_mock','MorganStanley_mock']]; n=[E[f][f'agree_{nm}']['n_in_sig'] for f in ['Corning_mock','MorganStanley_mock']]
    ax.bar(x+(i-.5)*0.36,v,0.34,color=col,edgecolor=INK,label=lab)
    for xi,vi,ni in zip(x+(i-.5)*0.36,v,n): ax.text(xi,vi+.015,f'{vi:.2f}\n(n={ni})',ha='center',fontsize=7)
ax.set_xticks(x); ax.set_xticklabels(['Corning-like mock','MS-like mock']); ax.set_ylabel('share on the true shape'); ax.set_ylim(0,1.05)
ax.set_title('Programs in significant shapes that sit on their noise-free shape',fontsize=9.5); ax.legend(frameon=False,fontsize=7.5,loc='upper left'); fig.tight_layout(); fig.savefig(OUT+'stem_replicate.png'); plt.close()
# ---------- power
pw=E['power_corning_ai_shape']; fig,ax=plt.subplots(figsize=(5,3.2))
for s,col in zip([0.05,0.10,0.15],[TEAL,AMB,RED]): ax.plot([10,20,40,80],[pw[f'sigma{s}_n{n}'] for n in [10,20,40,80]],'o-',color=col,label=f'noise σ = {s}')
ax.set_xscale('log'); ax.set_xticks([10,20,40,80]); ax.set_xticklabels(['10','20','40','80']); ax.set_xlabel('programs sharing the planted shape (of 778)'); ax.set_ylabel('share of 20 runs detected'); ax.legend(frameon=False,fontsize=8)
ax.set_title('Power: a shape needs ~80 programs to light up',fontsize=10); fig.tight_layout(); fig.savefig(OUT+'stem_power.png'); plt.close()
# ---------- hysteresis loops (strongly visual)
W=pd.read_csv('hyst/q1_weekly_hyst.csv',parse_dates=['date']).set_index('date'); H=json.load(open('hyst/q1_hyst.json'))
fig,axs=plt.subplots(3,5,figsize=(12,7.4)); Q=W.fails_fin_ust
for ax,(st,h) in zip(axs.flat,zip(H['storms'],H['tests']['spread']['per_storm'])):
    seg=W.loc[st['start']:st['end']]; q=seg.fails_fin_ust.values; c=seg.spread_bp.values
    qn=(q-q.min())/np.ptp(q); cn=(c-c.min())/(np.ptp(c) or 1); k=int(np.argmax(q))
    ax.plot(qn[:k+1],cn[:k+1],'-o',color=AMB,ms=3,lw=1.5); ax.plot(qn[k:],cn[k:],'-o',color=TEAL,ms=3,lw=1.5)
    for i in range(len(qn)-1): ax.annotate('',xy=(qn[i+1],cn[i+1]),xytext=(qn[i],cn[i]),arrowprops=dict(arrowstyle='->',color=INK,lw=.6))
    ax.set_title(f"peak {st['peak']}  HI {h:+.2f}",fontsize=8.5,color=RED if h<=-0.2 else (TEAL if h>=0.2 else INK)); ax.set_xlim(-.05,1.05); ax.set_ylim(-.05,1.05); ax.set_xticks([0,1]); ax.set_yticks([0,1])
for ax in axs.flat[len(H['storms']):]: ax.axis('off')
ax=axs.flat[-1]; ax.text(0,0.8,'x: financing fails (normalised in storm)\ny: DVP − tri-party spread (normalised)\norange = fails rising; teal = fails falling\nHI < 0: anticlockwise, spread higher\non the way down (spread lags fails)\nred title: HI ≤ −0.2',fontsize=8,va='top')
fig.suptitle('Hysteresis loops: 13 fails "storms", 2018–2026, DVP − tri-party overnight spread vs financing fails',fontsize=11); fig.tight_layout(rect=(0,0,1,.96)); fig.savefig(OUT+'hyst_loops.png'); plt.close()
# HI per storm with null band
T=H['tests']; fig,ax=plt.subplots(figsize=(6.4,3.3)); x=np.arange(len(H['storms']))
for off,(nm,col,lab) in zip([-0.27,0,0.27],[('spread',RED,'DVP−TP spread'),('dvp_out',TEAL,'DVP outstanding'),('lev_net_short',AMB,'lev-fund net short')]):
    v=[np.nan if h is None else h for h in T[nm]['per_storm']]; ax.bar(x+off,v,0.26,color=col,edgecolor=INK,lw=.5,label=f"{lab}: mean {T[nm]['mean_HI']:+.2f}, p={T[nm]['p_two_sided']:.3f}")
ax.axhline(0,color=INK,lw=.8); ax.set_xticks(x); ax.set_xticklabels([s['peak'][:7] for s in H['storms']],rotation=60,fontsize=7); ax.set_ylabel('hysteresis index HI')
ax.legend(frameon=False,fontsize=7,loc='lower left'); ax.set_title('HI by storm (positive: series peaks before fails; negative: after)',fontsize=9.5); fig.tight_layout(); fig.savefig(OUT+'hyst_hi_bars.png'); plt.close()
# mean HI vs null
fig,ax=plt.subplots(figsize=(5,3.2))
for i,(nm,lab) in enumerate([('spread','DVP−TP spread'),('dvp_out','DVP outstanding'),('lev_net_short','lev-fund net short')]):
    t=T[nm]; ax.plot([t['null_q025'],t['null_q975']],[i,i],color='#cbbd9f',lw=8,solid_capstyle='butt'); ax.plot(t['mean_HI'],i,'o',color=RED if t['p_two_sided']<0.05 else INK,ms=8)
    ax.text(0.27,i,f"p={t['p_two_sided']:.3f}\nHolm {t['p_holm']:.3f}",fontsize=7.5,va='center')
ax.set_yticks([0,1,2]); ax.set_yticklabels(['DVP−TP spread','DVP outstanding','lev-fund net short']); ax.axvline(0,color=INK,lw=.6); ax.set_xlim(-.3,.42)
ax.set_xlabel('mean HI across storms (band: 95% circular-shift null)'); ax.set_title('Hysteresis: spread lags fails in storms (not Holm-significant)',fontsize=9.5); fig.tight_layout(); fig.savefig(OUT+'hyst_mean_null.png'); plt.close()
# standard tool: ARDL / cross-correlation of levels
B=json.load(open('hyst/q1_baselines.json')); fig,ax=plt.subplots(figsize=(5,3.2)); k=[int(i) for i in B['xcorr_levels']]
ax.bar(k,list(B['xcorr_levels'].values()),color='#cbbd9f',edgecolor=INK); ax.axhline(0,color=INK,lw=.8)
ax.set_xlabel('lag k (weeks): spread k weeks earlier than fails'); ax.set_ylabel('corr(log fails, spread)'); ax.set_title('Usual tool: one symmetric, near-simultaneous link',fontsize=10)
ax.text(-4,-0.05,f"ARDL(1,2) BIC; spread → fails coefs\nL0 {B['ardl_fails_on_spread']['params']['spread.L0']:+.4f}, L1 {B['ardl_fails_on_spread']['params']['spread.L1']:+.4f}, L2 {B['ardl_fails_on_spread']['params']['spread.L2']:+.4f}",fontsize=7,va='top')
fig.tight_layout(); fig.savefig(OUT+'hyst_std_xcorr.png'); plt.close()
# walk-forward
rm=B['walk_forward']['rmse']; fig,ax=plt.subplots(figsize=(5,3.2)); names=['random_walk','ardl_lag1','ardl_lag1_plus_limb','sarimax101_x']; labs=['random walk','ARDL','ARDL + limb term','SARIMAX(1,0,1)+X']
ax.barh(range(4),[rm[n] for n in names],color=['#cbbd9f',AMB,TEAL,AMB],edgecolor=INK)
for i,n in enumerate(names): ax.text(rm[n]+.002,i,f'{rm[n]:.4f}',va='center',fontsize=8)
ax.set_yticks(range(4)); ax.set_yticklabels(labs); ax.set_xlim(0.2,0.31); ax.set_xlabel('walk-forward RMSE, log fails, 221 weeks 2022-07..2026-09'); ax.set_title('Forecasting: the limb term adds nothing (miss)',fontsize=10)
fig.tight_layout(); fig.savefig(OUT+'hyst_walkforward.png'); plt.close()
print('figs ok')
