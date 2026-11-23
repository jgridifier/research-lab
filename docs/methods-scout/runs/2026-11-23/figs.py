import sys, json, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,'pid'); from pidcore import barrett_closed, idep_from_corr, mmi_from_cov
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
TEAL='#0f766e'; AMB='#d97706'; RED='#b91c1c'; BLUE='#1d4ed8'; GREY='#9ca3af'; PUR='#7c3aed'
R1=json.load(open('pid/q3_pid.json')); R2=json.load(open('pid/q3_pid2.json'))
p=R1['P1_scb_dd']
# 1. standard view: OLS t + commonality
fig,ax=plt.subplots(1,2,figsize=(7.2,3.2))
t=p['ols_raw']['t'][1:]; ax[0].barh(['SCB','SA CET1\ndrawdown'],t,color=[AMB,BLUE]); ax[0].axvline(0,color='k',lw=.8)
for i,v in enumerate(t): ax[0].text(v/2,i,f't = {v:+.2f}',va='center',ha='center',fontsize=8.5,color='white')
ax[0].set_xlim(-8,8); ax[0].set_title(f"OLS, both together (firm-clustered)\nsource corr {p['ols_raw']['r_sources']:.2f}, VIF {p['ols_raw']['vif']:.1f}",fontsize=9)
c=p['commonality_raw']; vals=[c['unique1'],c['unique2'],c['common']]
ax[1].bar(['unique\nSCB','unique\ndrawdown','common'],vals,color=[AMB,BLUE,RED]); ax[1].axhline(0,color='k',lw=.8)
for i,v in enumerate(vals): ax[1].text(i,v+(0.01 if v>0 else -0.03),f'{v:+.3f}',ha='center',fontsize=8.5)
ax[1].set_title(f"Commonality of R² (total {c['R2_12']:.3f})\n'common' is negative: unreadable",fontsize=9); ax[1].set_ylabel('share of payout/RWA variance')
fig.suptitle('Usual tools, 2021–2025 (132 firm-years): payout/RWA on SCB and drawdown',fontsize=9.5); fig.tight_layout(); fig.savefig('fig/pid_ols.png'); plt.close()
# 2. PID atoms: MMI vs Idep for P1, plus add-on reparam
mech=R2['mechanism_posthoc']
rows=[('SCB + drawdown\n(MMI)',p['obs'],'m'),('SCB + drawdown\n(Idep)',R2['P1_scb_dd']['idep'],'d'),('add-on + drawdown\n(MMI, post hoc)',mech['pid_addon_dd_payout']['mmi'],'m')]
fig,ax=plt.subplots(figsize=(7.2,3.4))
for i,(lab,a,_) in enumerate(rows):
    left=0
    for k,col,nm in [('R',GREY,'shared (redundant)'),('U1',AMB,'unique to 1st (SCB / add-on)'),('U2',BLUE,'unique to drawdown'),('S',PUR,'synergy (only together)')]:
        v=max(a[k],0); ax.barh(i,v,left=left,color=col,label=nm if i==0 else None,edgecolor='white'); 
        if v>0.012: ax.text(left+v/2,i,f'{v:.3f}',ha='center',va='center',fontsize=7.5,color='white')
        left+=v
ax.set_yticks(range(3)); ax.set_yticklabels([r[0] for r in rows],fontsize=8.5); ax.invert_yaxis(); ax.set_xlabel('bits of information about payout/RWA (within-year ranks)')
ci=p['boot_ci']['S']; ax.set_title(f"PID: SCB alone {p['obs']['I1']:.3f} bits, drawdown {p['obs']['I2']:.3f}, together {p['obs']['I12']:.3f}\nMMI synergy {p['obs']['S']:.3f} (firm-bootstrap 95% CI {ci[0]:.3f}–{ci[1]:.3f}; null p = {p['p_S_freedman_lane']:.4f})",fontsize=9)
ax.set_xlim(0,0.40); ax.legend(fontsize=7.5,frameon=False,loc='upper right'); fig.tight_layout(); fig.savefig('fig/pid_atoms.png'); plt.close()
# 3. Barrett plane
a,c=p['corr_z'][0][1],p['corr_z'][0][2]; bo=p['corr_z'][1][2]
bs=np.linspace(-0.2,0.97,300); Sm=[]; Sd=[]
for b in bs:
    C=np.array([[1,a,c],[a,1,b],[c,b,1.]])
    if np.linalg.eigvalsh(C).min()<=1e-6: Sm.append(np.nan); Sd.append(np.nan); continue
    Sm.append(mmi_from_cov(C)['S']); Sd.append(idep_from_corr(b,a,c)['S'])
fig,ax=plt.subplots(figsize=(6.4,3.3))
ax.plot(bs,Sm,color=PUR,label='MMI synergy (Barrett 2015)'); ax.plot(bs,Sd,color=TEAL,ls='--',label='Idep synergy (Kay & Ince 2018)')
ax.axvline(a/c,color=GREY,ls=':'); ax.text(a/c+0.01,0.25,'b = a/c:\nzero synergy',fontsize=7.5,color='#4b5563')
ax.scatter([bo],[p['plugin']['S']],color=RED,zorder=5); ax.annotate(f"our 2021–25 SCB vs drawdown\nb = {bo:.2f}, plug-in S = {p['plugin']['S']:.3f}",(bo,p['plugin']['S']),xytext=(0.25,0.2),fontsize=8,arrowprops=dict(arrowstyle='->',color=RED))
ax.set_xlabel('correlation between the two sources (SCB, drawdown), b'); ax.set_ylabel('synergy (bits)'); ax.set_ylim(0,0.35)
ax.set_title(f'The Barrett plane: synergy at fixed target links a = {a:.2f} (SCB), c = {c:.2f} (drawdown)',fontsize=9); ax.legend(fontsize=7.5,frameon=False,loc='upper left')
fig.tight_layout(); fig.savefig('fig/pid_plane.png'); plt.close()
# 4. eras
fig,ax=plt.subplots(1,2,figsize=(7.2,3.2))
for j,(tg,lab) in enumerate([('payout','payout/RWA'),('div','dividends/RWA')]):
    e1=R2[f'P3_e1_{tg}']['mmi']; e2=R2[f'P3_e2_{tg}']['mmi']; L=R2['P3_loyo_'+('payout_rwa' if tg=='payout' else 'div_rwa')]
    x=np.arange(2); w=0.35
    ax[j].bar(x-w/2,[e1['R'],e2['R']],w,color=GREY,label='shared (drawdown ∩ pre-tax)'); ax[j].bar(x+w/2,[e1['U2'],e2['U2']],w,color=TEAL,label='unique to pre-tax income')
    r1=[l['mR1'] for l in L]; r2=[l['mR2'] for l in L]; u1=[l['mU1'] for l in L]; u2=[l['mU2'] for l in L]
    ax[j].errorbar(x-w/2,[e1['R'],e2['R']],yerr=[[e1['R']-min(r1),e2['R']-min(r2)],[max(r1)-e1['R'],max(r2)-e2['R']]],fmt='none',ecolor='k',lw=.8,capsize=3)
    ax[j].errorbar(x+w/2,[e1['U2'],e2['U2']],yerr=[[e1['U2']-min(u1),e2['U2']-min(u2)],[max(u1)-e1['U2'],max(u2)-e2['U2']]],fmt='none',ecolor='k',lw=.8,capsize=3)
    pe=R2['P3_era_'+('payout_rwa' if tg=='payout' else 'div_rwa')]['p_two_sided']
    ax[j].set_xticks(x); ax[j].set_xticklabels(['2013–2019','2020–2025']); ax[j].set_title(f'{lab}: shared p = {pe["mR"]:.3f}, unique p = {pe["mU"]:.3f}\n(exact over 1,716 year splits)',fontsize=8.5)
    ax[j].set_ylabel('bits (MMI, bias-corrected)')
ax[0].legend(fontsize=7,frameon=False); fig.suptitle('Drawdown and pre-tax income tell payouts more of the same story after 2020 (bars: leave-one-year-out range)',fontsize=8.5)
fig.tight_layout(); fig.savefig('fig/pid_eras.png'); plt.close()
# 5. mechanism scatter (aggregate public data)
D=pd.read_csv('q3_pim_panel.csv'); S=D[(D.year>=2021)&D.payout_rwa.notna()].copy(); S['addon']=S.scb-S.drawdown; fl=S.scb<=2.5+1e-9
fig,ax=plt.subplots(figsize=(5.6,3.4))
ax.scatter(S.addon[~fl],S.div_rwa[~fl],s=16,color=TEAL,label=f'SCB above the 2.5% floor (n = {int((~fl).sum())})')
ax.scatter(S.addon[fl],S.div_rwa[fl],s=16,color=GREY,marker='x',label=f'at the floor (n = {int(fl.sum())})')
ax.set_xlabel('SCB − SA CET1 drawdown (pp of RWA)'); ax.set_ylabel('realized dividends / RWA (%)'); ax.set_xlim(-0.4,S.addon.max()+0.3)
ax.set_title(f"The synergy is the SCB's dividend add-on (Spearman {mech['spearman_addon_div_nonfloor']:.2f} above the floor)",fontsize=8.5); ax.legend(fontsize=7.5,frameon=False)
fig.tight_layout(); fig.savefig('fig/pid_mech.png'); plt.close()
# 6. home repro
H=json.load(open('pid/home_repro.json'))['AND']
ms=['PID_WB','PID_MMI','PID_BROJA','PID_CCS','PID_dep']; keys=[('((0,), (1,))','shared',GREY),('((0,),)','unique X1',AMB),('((1,),)','unique X2',BLUE),('((0, 1),)','synergy',PUR)]
fig,ax=plt.subplots(figsize=(6.4,2.9))
for i,m in enumerate(ms):
    left=0
    for k,nm,col in keys:
        v=H[m][k]; ax.barh(i,v,left=left,color=col,label=nm if i==0 else None,edgecolor='white')
        if v>0.05: ax.text(left+v/2,i,f'{v:.3f}',ha='center',va='center',fontsize=7.5,color='white')
        left+=v
ax.set_yticks(range(5)); ax.set_yticklabels(['I_min (Williams–Beer)','MMI','BROJA','CCS (Ince)','I_dep (James et al.)'],fontsize=8); ax.invert_yaxis()
ax.set_xlabel('bits (total I = 0.811)'); ax.set_title('Home field, reproduced with dit 2.4: the AND gate under five PID measures',fontsize=9); ax.legend(fontsize=7,frameon=False,ncol=4,loc='lower center',bbox_to_anchor=(0.5,-0.5))
fig.tight_layout(); fig.savefig('fig/pid_home.png'); plt.close()
print('ok')
