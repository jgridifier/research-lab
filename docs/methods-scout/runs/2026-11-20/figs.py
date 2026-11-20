import numpy as np, pandas as pd, json, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, sys
sys.path.insert(0,'nca'); from nca_port import ce_fdh
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
TEAL='#0f766e'; AMB='#d97706'; RED='#b91c1c'; BLUE='#1d4ed8'; GREY='#9ca3af'
lab={'dl_fails':'fails','d_spread':'DVP−TP\nspread','dl_dvp':'DVP vol','dl_tri':'tri-party\nvol','d_lev':'lev. fund\nnet short','d_vix':'VIX'}
L1=pd.read_csv('lkif/L1_edges.csv').merge(pd.read_csv('lkif/L1_bootp.csv'),on=['src','tgt'])
V=list(lab); ang=np.linspace(np.pi/2,np.pi/2+2*np.pi,7)[:-1]; pos={v:(np.cos(a),np.sin(a)) for v,a in zip(V,ang)}
def graph(ax,edges,title):
    for v,(x,y) in pos.items():
        ax.add_patch(plt.Circle((x,y),0.17,color='#f3f4f6',ec='#374151',zorder=3)); ax.text(x,y,lab[v],ha='center',va='center',fontsize=7.5,zorder=4)
    for (s,t,w,col,ls,txt) in edges:
        x0,y0=pos[s]; x1,y1=pos[t]; dx,dy=x1-x0,y1-y0; L=np.hypot(dx,dy); ux,uy=dx/L,dy/L
        off=0.05*np.array([-uy,ux])
        ax.annotate('',xy=(x1-0.2*ux+off[0],y1-0.2*uy+off[1]),xytext=(x0+0.2*ux+off[0],y0+0.2*uy+off[1]),arrowprops=dict(arrowstyle='-|>',lw=w,color=col,ls=ls,mutation_scale=12),zorder=2)
        if txt: ax.text((x0+x1)/2+2.2*off[0],(y0+y1)/2+2.2*off[1],txt,fontsize=7,color=col,ha='center',va='center',bbox=dict(fc='white',ec='none',pad=0.5))
    ax.set_xlim(-1.35,1.35); ax.set_ylim(-1.3,1.3); ax.set_aspect('equal'); ax.axis('off'); ax.set_title(title,fontsize=9.5)
g=L1[L1.holm_gbic<0.05]
fig,ax=plt.subplots(figsize=(4.6,4.4)); graph(ax,[(r.src,r.tgt,2.2,'#374151','-','p<0.05 Holm') for r in g.itertuples()],'Usual tool: VAR(BIC=1) Granger, Holm 5%\n(direction only, no size, no sign)'); fig.tight_layout(); fig.savefig('fig/lkif_granger_graph.png'); plt.close()
e=L1[L1.p_boot<0.10]
fig,ax=plt.subplots(figsize=(4.6,4.4))
graph(ax,[(r.src,r.tgt,1+60*abs(r.tau),RED if r.tau>0 else BLUE,'-' if r.p_boot<0.05 else '--',f"τ={100*r.tau:+.1f}%\np={r.p_boot:.3f}") for r in e.itertuples()],'LKIF: signed normalized flow τ, calibrated\nbootstrap p (red raises, blue damps uncertainty)')
fig.tight_layout(); fig.savefig('fig/lkif_flow_graph.png'); plt.close()
# size
S=json.load(open('lkif/L3_size.json')); B=json.load(open('lkif/B_timing.json'))
ks=list(S); x=np.arange(len(ks)); w=0.2
fig,ax=plt.subplots(figsize=(6.4,3.2))
ax.bar(x-1.5*w,[S[k]['asym'] for k in ks],w,color=AMB,label='LKIF asymptotic (= VAR(1) t)')
ax.bar(x-0.5*w,[S[k]['shift_surrogate'] for k in ks],w,color=RED,label='LKIF circular-shift surrogate')
hc=B['hc3_size']; ax.bar(x+0.5*w,[hc.get(k,np.nan) for k in ks],w,color=TEAL,label='VAR(1) t with HC3 (2 edges)')
ax.axhline(0.05,color='k',lw=0.8,ls=':'); ax.text(len(ks)-0.5,0.07,'nominal 5%',fontsize=7,ha='right')
ax.set_xticks(x); ax.set_xticklabels([k.replace('->',' → ') for k in ks],fontsize=7.5); ax.set_ylabel('false-alarm rate when true link = 0')
ax.legend(fontsize=7,frameon=False); ax.set_title('Size on our weekly data (VAR(1) null, block-bootstrapped residuals)',fontsize=9.5)
fig.tight_layout(); fig.savefig('fig/lkif_size.png'); plt.close()
# rolling
R=pd.read_csv('lkif/L2_rolling.csv',parse_dates=['end'])
fig,ax=plt.subplots(figsize=(6.4,3.0))
ax.plot(R.end,100*R['d_spread->dl_fails_tau'],color=RED,label='spread → fails')
ax.plot(R.end,100*R['d_spread->dl_dvp_tau'],color=BLUE,label='spread → DVP volume')
ax.plot(R.end,100*R['dl_fails->d_spread_tau'],color=GREY,label='fails → spread')
ax.axhline(0,color='k',lw=0.6); ax.set_ylabel('τ, % of target entropy budget'); ax.legend(fontsize=7.5,frameon=False)
ax.set_title('Rolling 104-week LKIF (5 series, no positioning), window end',fontsize=9.5); fig.tight_layout(); fig.savefig('fig/lkif_rolling.png'); plt.close()
# monthly heat
M=pd.read_csv('lkif/L4_monthly.csv'); VM=['dl_pb','dl_rr','dl_tot','dl_fails','d_spread','dl_dvp']; nm={'dl_pb':'PF prime broker','dl_rr':'PF reverse repo','dl_tot':'PF total','dl_fails':'fails','d_spread':'spread','dl_dvp':'DVP vol'}
H=np.full((6,6),np.nan); P=np.full((6,6),np.nan)
for r in M.itertuples(): H[VM.index(r.tgt),VM.index(r.src)]=100*r.tau; P[VM.index(r.tgt),VM.index(r.src)]=r.p_boot
fig,ax=plt.subplots(figsize=(5.4,4.4)); im=ax.imshow(H,cmap='RdBu_r',vmin=-16,vmax=16)
for i in range(6):
    for j in range(6):
        if not np.isnan(H[i,j]): ax.text(j,i,f"{H[i,j]:+.1f}\np={P[i,j]:.2f}",ha='center',va='center',fontsize=6.5)
ax.set_xticks(range(6)); ax.set_xticklabels([nm[v] for v in VM],rotation=40,ha='right',fontsize=7.5); ax.set_yticks(range(6)); ax.set_yticklabels([nm[v] for v in VM],fontsize=7.5)
ax.set_xlabel('source'); ax.set_ylabel('target'); plt.colorbar(im,ax=ax,label='τ (%)'); ax.set_title('Monthly LKIF, Form PF 8.27 vs repo and fails\n2018-07..2025-12 (bootstrap p; none survive Holm)',fontsize=9)
fig.tight_layout(); fig.savefig('fig/lkif_monthly.png'); plt.close()
# home repro
H0=json.load(open('lkif/home_repro.json')); pv=H0['paper_values']; ks=['t62','t65','t45','t54']; nmk={'t62':'6→2','t65':'6→5','t45':'4→5','t54':'5→4'}
fig,ax=plt.subplots(figsize=(4.8,2.8)); x=np.arange(4)
ax.bar(x-0.2,[100*pv[k] for k in ks],0.4,color=GREY,label='Liang 2021, printed'); ax.bar(x+0.2,[100*H0['b1_n10000'][k] for k in ks],0.4,color=TEAL,label='ours, mean of 20 runs')
ax.set_xticks(x); ax.set_xticklabels([nmk[k] for k in ks]); ax.set_ylabel('|τ| (%)'); ax.legend(fontsize=7.5,frameon=False); ax.set_title('Home-field check: Liang (2021) Sec. 5.1 network',fontsize=9.5)
fig.tight_layout(); fig.savefig('fig/lkif_home.png'); plt.close()
# ---------- NCA
d=pd.read_csv('q3_pim_panel.csv'); d=d[d.payout_rwa.notna()]
x=d.cet1_min.values; y=d.payout_rwa.values
fig,ax=plt.subplots(figsize=(4.8,3.8)); ax.scatter(x,y,s=10,color=GREY,alpha=0.8)
b=np.polyfit(x,y,1); xx=np.linspace(x.min(),x.max(),50); ax.plot(xx,np.polyval(b,xx),color=AMB,lw=2,label=f'OLS: R² = {np.corrcoef(x,y)[0,1]**2:.2f}')
ax.set_xlabel('SA minimum CET1 ratio (%)'); ax.set_ylabel('payout / RWA (%)'); ax.legend(frameon=False,fontsize=8); ax.set_title('Usual tool: mean regression\n(weak fit, says "small average effect")',fontsize=9.5)
fig.tight_layout(); fig.savefig('fig/nca_ols.png'); plt.close()
f=ce_fdh(x,y); fig,ax=plt.subplots(figsize=(4.8,3.8)); ax.scatter(x,y,s=10,color=GREY,alpha=0.8)
ux=np.append(f['ux'],x.max()); cu=np.append(f['cu'],f['cu'][-1])
ax.step(ux,cu,where='post',color=TEAL,lw=2,label=f"CE-FDH ceiling, d = {f['d']:.2f}")
ax.fill_between(ux,cu,y.max(),step='post',color=TEAL,alpha=0.12,label='empty zone')
ax.set_xlabel('SA minimum CET1 ratio (%)'); ax.set_ylabel('payout / RWA (%)'); ax.legend(frameon=False,fontsize=8,loc='upper right'); ax.set_title('NCA: a ceiling (no low-trough firm paid high)\nbeyond what correlation gives (p = 0.012)',fontsize=9.5)
fig.tight_layout(); fig.savefig('fig/nca_ceiling.png'); plt.close()
N1=json.load(open('nca/N1.json'))
cs=['x_dd','x_pt','x_loss','x_cet1min']; cn={'x_dd':'− CET1 drawdown','x_pt':'SA pre-tax income','x_loss':'− loan-loss rate','x_cet1min':'SA minimum CET1'}
fig,ax=plt.subplots(figsize=(6.2,3.2)); yy=np.arange(4)
for k,c in enumerate(cs):
    r=N1[f'payout_rwa|{c}']; ax.plot([r['spur_mean'],r['spur_95']],[k,k],color=GREY,lw=6,solid_capstyle='butt')
    ax.scatter([r['d']],[k],color=TEAL if r['finding'] else (AMB if r['p_within']<0.05 else RED),zorder=3,s=40)
    ax.text(0.72,k,f"perm p={r["p_within"]:.4f} · spur p={r['p_spur']:.3f} · ρ={r['spearman']:.2f}",va='center',fontsize=7)
ax.set_yticks(yy); ax.set_yticklabels([cn[c] for c in cs],fontsize=8); ax.set_xlim(0,1.15); ax.set_xlabel('ceiling effect size d (payout/RWA, 360 firm-years)')
ax.set_title('Dot = observed d; grey = mean→95th pct. of d from correlation alone',fontsize=9); fig.tight_layout(); fig.savefig('fig/nca_spurious.png'); plt.close()
L=pd.read_csv('nca/N2_limits.csv'); ct=pd.crosstab(L.year,L.limit,normalize='index')
order=['x_cet1min','x_dd','x_pt','x_loss','tie']; cols={'x_cet1min':TEAL,'x_dd':AMB,'x_pt':BLUE,'x_loss':RED,'tie':GREY}
fig,ax=plt.subplots(figsize=(6.4,3.0)); bot=np.zeros(len(ct))
for o in order:
    if o in ct: ax.bar(ct.index,ct[o],bottom=bot,color=cols[o],label=cn.get(o,'tie')); bot+=ct[o].values
ax.set_ylabel('share of firm-years'); ax.legend(fontsize=7,frameon=False,ncol=5,loc='upper center',bbox_to_anchor=(0.5,-0.15)); ax.set_title('Which ceiling binds (Liebig limiting factor), by test year',fontsize=9.5)
fig.tight_layout(); fig.savefig('fig/nca_limiting.png'); plt.close()
fig,ax=plt.subplots(figsize=(5.2,3.6))
for lbl,m,col in [('2013–2019',d.year<=2019,GREY),('2020–2025',d.year>=2020,TEAL)]:
    dd=d[m]; ff=ce_fdh(dd.cet1_min,dd.payout_rwa); ax.scatter(dd.cet1_min,dd.payout_rwa,s=8,color=col,alpha=0.5)
    ax.step(np.append(ff['ux'],dd.cet1_min.max()),np.append(ff['cu'],ff['cu'][-1]),where='post',color=col,lw=2,label=f"{lbl}: d = {ff['d']:.2f}")
ax.set_xlabel('SA minimum CET1 ratio (%)'); ax.set_ylabel('payout / RWA (%)'); ax.set_xlim(2,20); ax.legend(frameon=False,fontsize=8); ax.set_title('Ceiling by era (x axis cut at 20%)',fontsize=9.5)
fig.tight_layout(); fig.savefig('fig/nca_eras.png'); plt.close()
N4=json.load(open('nca/N2_N3_N4.json'))['N4']; ks=['ceil','qr95','ols','ardl','sarimax']; kn=['NCA ceiling','QR τ=0.95','OLS+1.645s','ARDL(1,0) 95%','SARIMAX 95%']
fig,ax=plt.subplots(1,2,figsize=(7.2,2.8))
ax[0].barh(kn,[N4[k]['viol'] for k in ks],color=[TEAL,GREY,GREY,GREY,GREY]); ax[0].axvline(0.05,ls=':',color='k'); ax[0].set_xlabel('share above the bound (OOS)')
ax[1].barh(kn,[N4[k]['headroom_mean'] for k in ks],color=[TEAL,GREY,GREY,GREY,GREY]); ax[1].set_xlabel('mean headroom (pp of RWA)'); ax[1].set_yticklabels([])
fig.suptitle('Walk-forward upper envelopes, test years 2015–2025',fontsize=9.5); fig.tight_layout(); fig.savefig('fig/nca_walkforward.png'); plt.close()
print('figs ok')
