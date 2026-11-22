import numpy as np, pandas as pd, json, matplotlib, sys, os; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
TEAL='#0f766e'; AMB='#d97706'; RED='#b91c1c'; BLUE='#1d4ed8'; GREY='#9ca3af'; INK='#1c150d'
os.makedirs('fig',exist_ok=True); which=sys.argv[1] if len(sys.argv)>1 else 'all'
NAMES={'P1':'PF prime broker × fails','P2':'PF prime broker × tri-party vol','P3':'PF prime broker × DVP vol','P4':'PF prime broker × DVP−tri spread','P5':'PF reverse repo × DVP vol'}
if which in ('all','iccf'):
    C1=json.load(open('iccf/C1.json'))
    # standard: monthly CCF bars with Bartlett bands
    fig,axs=plt.subplots(1,2,figsize=(8.4,3.2),sharey=True)
    for ax,p in zip(axs,['P5','P1']):
        s=C1[p]['standard']; ks=np.array([int(k) for k in s['ccf_levels']]); r=np.array(list(s['ccf_levels'].values()))
        ax.bar(ks,r,color=[AMB if abs(v)>s['band'] else GREY for v in r]); ax.axhline(s['band'],ls='--',c=INK,lw=.8); ax.axhline(-s['band'],ls='--',c=INK,lw=.8)
        ax.set_title(f"{NAMES[p]}\n{s['n_lags_outside_band']} of 25 lags 'significant' (amber)",fontsize=9); ax.set_xlabel('lag (months; + = market lags Form PF)')
    axs[0].set_ylabel('CCF of monthly means (detrended)'); fig.tight_layout(); fig.savefig('fig/iccf_standard.png'); plt.close()
    # method: ICCF + phase-null band + CCCD
    fig,axs=plt.subplots(2,2,figsize=(8.4,5.0),gridspec_kw={'height_ratios':[2.2,1]},sharex='col')
    for j,p in enumerate(['P5','P1']):
        c=C1[p]['curve']; lag=np.array(c['lag']); r=np.array(c['r']); nb=np.array(c['null95_phase_pointwise'])
        ax=axs[0,j]; ax.fill_between(lag,-nb,nb,color=GREY,alpha=.35,label='95% band, phase-randomized null')
        ax.plot(lag,r,c=TEAL,lw=2,label='ICCF (sign-adjusted)'); ax.axvline(0,c=INK,lw=.6)
        ax.set_title(f"{NAMES[p]}\nr* = {C1[p]['r_star']:+.2f}, null p = {C1[p]['p_ar1']:.3f} (AR1) / {C1[p]['p_phase']:.3f} (phase)",fontsize=9)
        if j==0: ax.legend(fontsize=7,loc='lower left'); ax.set_ylabel('r(τ)')
        ax=axs[1,j]; ax.hist(c['cccd'],bins=np.arange(-365,366,14),color=TEAL if C1[p]['p_phase']<0.05 else AMB); ax.axvline(0,c=INK,lw=.6)
        q=C1[p]['cccd_q']; ax.set_title(f"RSS centroid distribution: median {q[2]:+.0f} d, 68% [{q[1]:+.0f}, {q[3]:+.0f}]",fontsize=8.5); ax.set_xlabel('lag τ (days; + = market lags Form PF)')
    fig.tight_layout(); fig.savefig('fig/iccf_method.png'); plt.close()
    # all-pairs summary: r* vs null95 and CCCD intervals
    fig,axs=plt.subplots(1,2,figsize=(8.6,3.0))
    ps=list(NAMES); y=np.arange(len(ps))[::-1]
    ax=axs[0]; ax.barh(y,[abs(C1[p]['r_star']) for p in ps],color=[TEAL if max(C1[p]['p_ar1'],C1[p]['p_phase'])*5<0.05 else GREY for p in ps])
    ax.scatter([C1[p]['null95_phase'] for p in ps],y,marker='|',s=200,c=RED,label='phase null 95th pct'); ax.scatter([C1[p]['null95_ar1'] for p in ps],y,marker='|',s=200,c=BLUE,label='AR(1) null 95th pct')
    ax.set_yticks(y); ax.set_yticklabels([NAMES[p] for p in ps],fontsize=8); ax.set_xlabel('|r*| (max over ±365 days)'); ax.legend(fontsize=7,loc='lower right')
    ax=axs[1]
    for yy,p in zip(y,ps):
        q=C1[p]['cccd_q']; col=TEAL if max(C1[p]['p_ar1'],C1[p]['p_phase'])*5<0.05 else AMB
        ax.plot([q[0],q[4]],[yy,yy],c=col,lw=1); ax.plot([q[1],q[3]],[yy,yy],c=col,lw=4); ax.plot(q[2],yy,'o',c=INK,ms=4)
    ax.axvline(0,c=INK,lw=.6); ax.set_yticks(y); ax.set_yticklabels([]); ax.set_xlabel('RSS centroid lag (days): 68% thick, 95% thin')
    ax.set_title('Every pair "excludes zero" — only P5 beats the nulls',fontsize=8.5)
    fig.tight_layout(); fig.savefig('fig/iccf_pairs.png'); plt.close()
    # stability
    C2=json.load(open('iccf/C2.json'))
    fig,ax=plt.subplots(figsize=(7.6,3.0)); off={'half1':-0.2,'half2':0.0,'change_full':0.2}; cols={'half1':BLUE,'half2':RED,'change_full':TEAL}
    labs={'half1':'first half','half2':'second half','change_full':'12-month change, full'}
    for i,p in enumerate(ps):
        for h in off:
            v=C2[p][h]; ax.bar(i+off[h],v['r_star'],0.2,color=cols[h],alpha=1 if max(v['p_ar1'],v['p_phase'])<0.05 else 0.35,label=labs[h] if i==0 else None)
            lagv=v['centroid_lag'] if v['centroid_lag'] is not None else v['lag_at_rstar']; ax.text(i+off[h],v['r_star']+(0.04 if v['r_star']>0 else -0.1),f"{lagv:+.0f}d",ha='center',fontsize=6.5)
    ax.axhline(0,c=INK,lw=.6); ax.set_xticks(range(len(ps))); ax.set_xticklabels([NAMES[p].replace(' × ','\n× ') for p in ps],fontsize=7); ax.set_ylabel('signed r*'); ax.legend(fontsize=7,ncol=3,loc='upper left')
    ax.set_title('Stability: solid = both nulls p < 0.05 (unadjusted); label = lag',fontsize=9); fig.tight_layout(); fig.savefig('fig/iccf_stability.png'); plt.close()
    # home repro
    H=json.load(open('iccf/home_repro.json')); sh=np.loadtxt('iccf/PyCCF_orig/CPython/sample_ccf_yap.dat')
    sys.path.insert(0,'iccf'); import iccf_core as ic
    D='iccf/PyCCF_orig/PurePython/'; t1,y1=np.loadtxt(D+'sample_lc1.dat',unpack=True,usecols=[0,1]); t2,y2=np.loadtxt(D+'sample_lc2.dat',unpack=True,usecols=[0,1])
    r,lag,_=ic.xcor(t1,y1,t2,y2,-100,100,2.)
    fig,axs=plt.subplots(1,2,figsize=(8.2,2.9)); axs[0].plot(sh[:,0],sh[:,1],c=GREY,lw=5,label='shipped sample_ccf_yap.dat'); axs[0].plot(lag,r,c=TEAL,lw=1.4,label='our NumPy ICCF'); axs[0].legend(fontsize=7); axs[0].set_xlabel('lag (days)'); axs[0].set_title('PyCCF sample: CCF (100/101 lags to print precision)',fontsize=8.5)
    cs=np.loadtxt('iccf/PyCCF_orig/CPython/sample_centtab_yap.dat'); axs[1].hist(cs,bins=np.arange(-10,60,2),alpha=.5,color=GREY,label='shipped CCCD (500)')
    axs[1].set_title(f"CCCD median: shipped {H['cccd_shipped'][1]:.1f} d, ours {H['cccd_numpy'][1]:.1f} d",fontsize=8.5); axs[1].set_xlabel('centroid lag (days)'); axs[1].legend(fontsize=7)
    fig.tight_layout(); fig.savefig('fig/iccf_home.png'); plt.close()
    if os.path.exists('iccf/C3_size.json'):
        S=json.load(open('iccf/C3_size.json')); keys=[('bartlett_levels','Bartlett bands, monthly levels'),('bartlett_diff','Bartlett bands, monthly changes'),('granger','Granger (VAR, BIC), either way'),('home68','RSS 68% CCCD excludes 0'),('home95','home rule: r>0.5 & 95% CCCD excl. 0'),('null_ar1','ICCF + AR(1) null'),('null_phase','ICCF + phase null')]
        fig,ax=plt.subplots(figsize=(7.6,3.2)); x=np.arange(len(keys)); w=0.38
        for j,(p,col) in enumerate([('P1',AMB),('P5',TEAL)]):
            ax.bar(x+(j-0.5)*w,[S[p]['rates'][k] for k,_ in keys],w,color=col,label=f"matched to {NAMES[p]}")
        ax.axhline(0.05,ls='--',c=INK,lw=.8); ax.set_xticks(x); ax.set_xticklabels([l for _,l in keys],fontsize=7,rotation=20,ha='right'); ax.set_ylabel('false-alarm rate\n(independent series)'); ax.legend(fontsize=7)
        fig.tight_layout(); fig.savefig('fig/iccf_size.png'); plt.close()
if which in ('all','rfa'):
    S=json.load(open('rfa/q2_scores.json')); W=json.load(open('rfa/wf_q2.json')); F=['Corning_mock','MorganStanley_mock']; FL={'Corning_mock':'Corning-like (SYNTHETIC)','MorganStanley_mock':'Morgan Stanley-like (SYNTHETIC)'}
    # standard: boxplot by function (top 12 functions by count), MS mock
    X=pd.read_csv('rfa/MorganStanley_mock_x.csv'); P=pd.read_csv('rfa/MorganStanley_mock_programs_regions.csv',index_col=0); X['f']=X.program_id.map(P.function)
    top=X.groupby('f').program_id.nunique().sort_values(ascending=False).index[:12]
    fig,ax=plt.subplots(figsize=(7.6,3.4)); ax.boxplot([100*np.log(X.x[X.f==f]) for f in top],vert=False,showfliers=False,patch_artist=True,boxprops=dict(facecolor='#f3f4f6'))
    ax.set_yticks(range(1,13)); ax.set_yticklabels([f[:30] for f in top],fontsize=7); ax.set_xlabel('budget miss, log(actual/budget) × 100'); ax.axvline(0,c=INK,lw=.6)
    ax.set_title('Usual view: budget miss by function (SYNTHETIC Morgan Stanley-like mock)\nsays nothing about which groups can be pooled',fontsize=9); fig.tight_layout(); fig.savefig('fig/rfa_standard.png'); plt.close()
    # method: L-CV vs t3 ratio diagram + H by scheme
    C=pd.read_csv('rfa/lmrd_curves.csv'); St=pd.read_csv('rfa/MorganStanley_mock_site.csv'); T=pd.read_csv('rfa/MorganStanley_mock_truth.csv',index_col=0)
    R=pd.read_csv('rfa/MorganStanley_mock_regions.csv')
    fig,axs=plt.subplots(1,2,figsize=(8.6,3.6))
    ax=axs[0]; sg=T.loc[St.program_id,'sigma'].values
    for s,col in [(0.065,BLUE),(0.085,TEAL),(0.105,AMB),(0.18,RED)]:
        m=np.isclose(sg,s); ax.scatter(St.t3[m],St.t[m],s=4,alpha=.35,color=col,label=f'true σ={s}')
    for sc,mk,col in [('reg_A','s',INK),('reg_B','D',AMB)]:
        r=R[R.scheme==sc]; ax.scatter(r.rt3,r.rt,s=np.clip(r.N/4,8,120),marker=mk,facecolor='none',edgecolor=col,lw=1.2,label=('function' if sc=='reg_A' else 'discretionary×size')+' region means')
    ax.set_xlabel('L-skewness t3'); ax.set_ylabel('L-CV t'); ax.set_xlim(-1,1); ax.set_ylim(0,0.3); ax.legend(fontsize=6,loc='upper left',markerscale=1)
    ax.set_title('Programs in L-moment space (SYNTHETIC MS-like)\ncolour = generator noise class (answer key)',fontsize=8.5)
    ax=axs[1]; schemes=[('reg_O','oracle σ class'),('reg_A','function'),('reg_C','text clusters'),('reg_B','discr. × size'),('reg_D','random')]
    for i,(sc,l) in enumerate(schemes):
        for j,f in enumerate(F):
            r=pd.read_csv(f'rfa/{f}_regions.csv'); r=r[(r.scheme==sc)&(r.N>=5)]
            ax.scatter(np.full(len(r),i+(j-0.5)*0.3)+np.random.default_rng(1).uniform(-.08,.08,len(r)),r.H1.clip(-4,16),s=np.clip(r.N/6,6,80),color=[TEAL,AMB][j],alpha=.7,label=FL[f] if i==0 else None)
    ax.axhline(1,ls=':',c=INK,lw=.8); ax.axhline(2,ls='--',c=INK,lw=.8); ax.set_xticks(range(5)); ax.set_xticklabels([l for _,l in schemes],fontsize=7.5,rotation=15)
    ax.set_ylabel('heterogeneity H1 per region (clipped)'); ax.legend(fontsize=6.5,loc='upper left'); ax.set_title('Which category scheme is a valid pooling unit?\nH1 < 1 homogeneous, ≥ 2 heterogeneous',fontsize=8.5)
    fig.tight_layout(); fig.savefig('fig/rfa_method.png'); plt.close()
    # q90 RMSE
    keys=['at-site empirical','at-site lognormal','EB-shrunk sd (to region B)','RFA regions B (disc x size)','RFA regions C (text)','RFA random regions','EB-shrunk sd (to function)','RFA regions A (function)','category-pooled lognormal (function)','RFA oracle regions (answer key)']
    fig,ax=plt.subplots(figsize=(7.6,3.6)); y=np.arange(len(keys))[::-1]; w=0.38
    for j,f in enumerate(F): ax.barh(y+(j-0.5)*w,[S[f]['rmse_logq90'][k] for k in keys],w,color=[TEAL,AMB][j],label=FL[f])
    ax.set_yticks(y); ax.set_yticklabels(keys,fontsize=7.5); ax.set_xlabel('RMSE of log 90th-percentile budget miss vs generator truth'); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig('fig/rfa_q90.png'); plt.close()
    # power
    Pm=pd.read_csv('rfa/power_q2_matched.csv'); fig,axs=plt.subplots(1,3,figsize=(8.6,2.8),sharey=True)
    for ax,N in zip(axs,[20,50,150]):
        g=Pm[Pm.N==N]; x=np.arange(len(g)); ax.bar(x-0.27,g.H1ge2,0.27,color=TEAL,label='H1 ≥ 2'); ax.bar(x,g.BF05,0.27,color=GREY,label='Brown–Forsythe p<0.05'); ax.bar(x+0.27,g.BF_matched,0.27,color=AMB,label='Brown–Forsythe, same false-alarm rate as H1')
        ax.set_xticks(x); ax.set_xticklabels([p.replace('/','\nvs ') for p in g.pair],fontsize=6.5); ax.set_title(f'{N} programs per region',fontsize=8.5)
    axs[0].set_ylabel('rejection rate'); axs[0].legend(fontsize=6,loc='upper left'); fig.tight_layout(); fig.savefig('fig/rfa_power.png'); plt.close()
    # walk-forward
    keys=['at-site lognormal','SARIMAX(1,0,0) per program','RFA index-flood, regions B','RFA index-flood, regions A (function)','category-pooled lognormal (function)','OLS on stated features','pooled ARDL(1), regions B']
    fig,axs=plt.subplots(1,2,figsize=(8.6,3.0)); y=np.arange(len(keys))[::-1]; w=0.38
    for j,f in enumerate(F):
        axs[0].barh(y+(j-0.5)*w,[W[f]['pinball_ratio_vs_at_site'][k] for k in keys],w,color=[TEAL,AMB][j],label=FL[f]); axs[1].barh(y+(j-0.5)*w,[W[f]['coverage'][k] for k in keys],w,color=[TEAL,AMB][j])
    axs[0].axvline(0.95,ls='--',c=INK,lw=.8); axs[0].set_yticks(y); axs[0].set_yticklabels(keys,fontsize=7); axs[0].set_xlabel('pinball loss at 0.9 ÷ at-site'); axs[0].legend(fontsize=6.5)
    axs[1].axvline(0.9,ls='--',c=INK,lw=.8); axs[1].set_yticks(y); axs[1].set_yticklabels([]); axs[1].set_xlim(0.6,1); axs[1].set_xlabel('coverage of FY2025 (target 0.90)')
    fig.tight_layout(); fig.savefig('fig/rfa_wf.png'); plt.close()
    # home repro
    rows=[l for l in open('rfa/cascades_out_fortran.txt') if l.strip()[:2].strip().isdigit() and len(l.split())==7]
    Df=np.array([float(l.split()[-1]) for l in rows]); Rr=json.load(open('rfa/home_repro_R.json')); Dr=np.array(Rr['D'] if isinstance(Rr['D'],list) else list(Rr['D'].values()))
    fig,axs=plt.subplots(1,2,figsize=(8.2,2.8)); axs[0].scatter(Df,Dr,c=TEAL); axs[0].plot([0,3],[0,3],c=GREY,lw=.8); axs[0].set_xlabel('D_i printed in CASCADES.OUT (Fortran)'); axs[0].set_ylabel('lmomRFA 3.8'); axs[0].set_title('North Cascades: 19 discordancy values, exact',fontsize=8.5)
    ax=axs[1]; lab=['H1','H2','H3']; ax.bar(np.arange(3)-0.2,[0.62,-1.49,-2.37],0.4,color=GREY,label='Fortran (500 sims)'); ax.bar(np.arange(3)+0.2,Rr['HZ_seeds_mean'][:3],0.4,yerr=Rr['HZ_seeds_sd'][:3],color=TEAL,label='lmomRFA, mean of 20 seeds ±sd')
    ax.set_xticks(range(3)); ax.set_xticklabels(lab); ax.axhline(0,c=INK,lw=.6); ax.legend(fontsize=7); ax.set_title('Heterogeneity measures',fontsize=8.5)
    fig.tight_layout(); fig.savefig('fig/rfa_home.png'); plt.close()
print('ok')
