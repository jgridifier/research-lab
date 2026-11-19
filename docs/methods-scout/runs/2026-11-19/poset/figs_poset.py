import json,pickle,numpy as np,pandas as pd,matplotlib,re; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import cm, colors
OUT='/workspace/methods-scout/2026-11-19/fig/'
AMB,TEAL,INK,MUT,RED='#e8902e','#1f9e8e','#1c150d','#6f5f46','#df5236'
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
Y=pickle.load(open('Y.pkl','rb')); A=json.load(open('q3_poset_A1A2.json')); B=json.load(open('q3_poset_A1b_A4.json')); T2=json.load(open('A1b_twosided.json'))
def short(n):
    n=re.sub(r',? (Inc\.|Corporation|Corp\.|Financial Corporation|Holdings|Group|USA|Company|N\.A\.|LLC|plc|Bancorp|Bancorporation|Financial Services|& Co\.|The)\b','',n)
    n=n.replace('The ','').replace('Financial','Fin.').replace('Bank of America','BofA').replace('JPMorgan Chase','JPM').replace('Goldman Sachs','GS').replace('Morgan Stanley','MS')
    n=n.replace(', Inc.','').replace(' Inc.','').replace(' & Company','').replace('Citizens Fin.','Citizens').replace(' Hol','')
    return re.sub(r'[\s,&.]+$','',n.strip()[:16])
y=2024; d=Y[y]; M=np.array(d['M']); n=len(M); pay=np.array(d['pay']); names=[short(x) for x in d['names']]
# cover relations
C=M.copy()
for i in range(n):
    for j in range(n):
        if M[i,j] and any(M[i,k] and M[k,j] for k in range(n)): C[i,j]=0
# level = longest chain from bottom (least stressed)
lev=np.zeros(n,int)
for _ in range(n):
    for i in range(n):
        for j in range(n):
            if M[i,j]: lev[j]=max(lev[j],lev[i]+1)
e=np.array(d['e'])
norm=colors.Normalize(vmin=0,vmax=np.quantile(pay,.95)); cmap=matplotlib.colormaps['YlGnBu']
fig,axs=plt.subplots(1,2,figsize=(13,7.2),gridspec_kw={'width_ratios':[1,1.55]})
# standard: equal-weight composite bars
ew=np.array(d['ew']); o=np.argsort(ew)
ax=axs[0]; ax.barh(range(n),ew[o],color=[cmap(norm(pay[k])) for k in o],edgecolor='#8c7b62',lw=.4)
ax.set_yticks(range(n)); ax.set_yticklabels([names[k] for k in o],fontsize=7); ax.set_xlabel('Equal-weight stress score (z, higher = more stressed)')
ax.set_title('Usual tool: one composite score\n(a single forced order; weights chosen by us)',fontsize=10,loc='left')
ax=axs[1]
pos={}
for L in range(lev.max()+1):
    ids=[k for k in range(n) if lev[k]==L]; ids=sorted(ids,key=lambda k:e[k])
    for r,k in enumerate(ids): pos[k]=((r-(len(ids)-1)/2)*1.0,L)
for i in range(n):
    for j in range(n):
        if C[i,j]: ax.plot([pos[i][0],pos[j][0]],[pos[i][1],pos[j][1]],color='#b8ab92',lw=.7,zorder=1)
for k in range(n):
    ax.scatter(*pos[k],s=330,color=cmap(norm(pay[k])),edgecolor=INK,lw=.6,zorder=2)
    ax.text(pos[k][0],pos[k][1]-0.32,names[k],ha='center',va='top',fontsize=6.3,color=INK)
ax.set_yticks(range(lev.max()+1)); ax.set_ylabel('Dominance level (0 = no firm is less stressed on all three)'); ax.set_xticks([])
ax.spines['bottom'].set_visible(False)
ax.set_title(f'This method: Hasse diagram of the 2024 severely adverse results ({n} firms)\nLine up = worse on drawdown, pre-tax income AND loan losses. {100*(1-M.sum()/(n*(n-1)/2)):.0f}% of pairs have no order.',fontsize=10,loc='left')
sm=cm.ScalarMappable(norm=norm,cmap=cmap); cb=fig.colorbar(sm,ax=axs,fraction=0.025,pad=0.01); cb.set_label('Realized 2024 payout / RWA (%), Y-9C')
fig.savefig(OUT+'poset_hasse_2024.png',bbox_inches='tight'); plt.close()
# rank-probability heat map 2024
R=np.array(d['R']); o2=np.argsort(e)
fig,ax=plt.subplots(figsize=(8,6.6)); ax.imshow(R[o2],aspect='auto',cmap='Oranges',origin='lower',extent=(0.5,n+0.5,-0.5,n-0.5))
ax.scatter(np.argsort(np.argsort(ew))[o2]+1,range(n),s=10,color=TEAL,label='equal-weight composite rank',zorder=3)
ax.set_yticks(range(n)); ax.set_yticklabels([names[k] for k in o2],fontsize=6.5); ax.set_xlabel('Stress rank (1 = least stressed) over all orders consistent with dominance')
ax.set_title('2024: probability of each stress rank (exact, all linear extensions)\nwide orange rows = rank depends on the weights you pick',fontsize=10,loc='left'); ax.legend(loc='lower right',fontsize=8)
fig.tight_layout(); fig.savefig(OUT+'poset_rankprob_2024.png'); plt.close()
# trade-off pairs bar chart
inc=B['A1b_incomparable']['obs']
fig,ax=plt.subplots(figsize=(7.6,3.6))
labs=['Dominance pairs\n(any weights agree)','Trade-off pairs:\nequal-weight score','Trade-off pairs:\npre-tax income','Trade-off pairs:\nCET1 drawdown','Trade-off pairs:\nloan-loss rate']
vals=[A['A1_same_year']['C'],inc['ew'],inc['neg_pti'],inc['drawdown'],inc['loss_total_loan_rate']]
cols=[TEAL,'#b8ab92',TEAL,'#b8ab92',RED]
ax.barh(range(5)[::-1],vals,color=cols); ax.axvline(.5,color=INK,lw=.8,ls='--'); ax.set_yticks(range(5)[::-1]); ax.set_yticklabels(labs,fontsize=8)
for i,v in zip(range(5)[::-1],vals): ax.text(v+.005,i,f'{v:.2f}',va='center',fontsize=8)
ax.set_xlim(.3,.8); ax.set_xlabel('Share of pairs where the more-stressed firm paid out less (0.5 = coin flip)')
ax.set_title('2013–2025, 360 firm-years: 2,203 dominance pairs, 2,814 trade-off pairs (computed)',fontsize=9.5,loc='left')
fig.tight_layout(); fig.savefig(OUT+'poset_tradeoff_pairs.png'); plt.close()
# SCB vs path
a3=B['A3_scb_vs_path_2021_2025']
fig,ax=plt.subplots(figsize=(7,2.8))
v=[a3['scb_conc'],a3['path_conc'],a3['path_conc_in_disagree']]; l=[f"SCB order\n({a3['scb_pairs']} pairs)",f"Path dominance\n({a3['path_pairs']} pairs)",f"Path, where SCB disagrees\n({a3['disagree_pairs']} pairs; {int(a3['floor_tied'])} both at 2.5% floor)"]
ax.barh(range(3)[::-1],v,color=['#b8ab92',TEAL,TEAL]); ax.axvline(.5,color=INK,lw=.8,ls='--')
for i,x in zip(range(3)[::-1],v): ax.text(x+.005,i,f'{x:.2f}',va='center',fontsize=8)
ax.set_yticks(range(3)[::-1]); ax.set_yticklabels(l,fontsize=8); ax.set_xlim(.3,.85); ax.set_xlabel('Share where the more-stressed firm paid out less, 2021–2025')
fig.tight_layout(); fig.savefig(OUT+'poset_scb_vs_path.png'); plt.close()
# stability
T4=pd.read_csv('A4_stability.csv')
fig,ax=plt.subplots(figsize=(8,3.4)); x=np.arange(len(T4)); tot=T4.dom_a.values
ax.bar(x,T4.kept/tot,color=TEAL,label='kept'); ax.bar(x,T4.lost/tot,bottom=T4.kept/tot,color='#d8cdb8',label='became a trade-off'); ax.bar(x,T4.flipped/tot,bottom=(T4.kept+T4.lost)/tot,color=RED,label='reversed')
ax.plot(x,T4.tau_payout,'o-',color=AMB,label='payout rank Kendall τ'); ax.set_xticks(x); ax.set_xticklabels(T4.pair,rotation=45,fontsize=7.5); ax.set_ylim(0,1.02)
ax.set_ylabel('Share of last year\'s dominance pairs'); ax.legend(fontsize=7.5,ncol=4,loc='lower center',bbox_to_anchor=(.5,1.0),frameon=False)
fig.tight_layout(); fig.savefig(OUT+'poset_stability.png'); plt.close()
# walk-forward
W=pd.read_csv('A2_walkforward.csv'); fig,ax=plt.subplots(figsize=(7.6,3.2))
for k,c,lab in [('poset',TEAL,'Poset expected rank (no fitted weights)'),('ols','#b8ab92','OLS on 3 stress variables'),('ardl',AMB,'ARDL(1,0) pooled'),('sarimax',RED,'SARIMAX(1,0,0)+exog')]:
    ax.plot(W.year,W[k],'o-',color=c,label=f'{lab}: mean {W[k].mean():.2f}',ms=3)
ax.set_ylabel('Spearman, predicted vs realized\npayout/RWA (year y)'); ax.legend(fontsize=7,frameon=False); ax.set_xlabel('Walk-forward test year (fits use earlier years only)')
fig.tight_layout(); fig.savefig(OUT+'poset_walkforward.png'); plt.close()
print('ok')
