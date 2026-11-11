import json, pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
F='fig/'; INK='#1c150d'; AC=['#e8902e','#1f9e8e','#54b441','#df5236','#3b6fb6','#8a5a9e','#777']
A=pd.read_csv('data/panel_A.csv',index_col=0); E=pd.read_csv('data/panel_E4.csv',index_col=0)
SA=A.div(A.sum(axis=1),axis=0)*100; SE=E.div(E.sum(axis=1),axis=0)*100
def qx(idx): return np.arange(len(idx))
def ticks(ax,idx,step=4):
    ax.set_xticks(range(0,len(idx),step)); ax.set_xticklabels([idx[i] for i in range(0,len(idx),step)],rotation=45,ha='right')
def m2():
    b=json.load(open('out/m2_results.json'))
    fig,axs=plt.subplots(1,2,figsize=(11,3.8))
    ax=axs[0]; big=['JPM','GS','C','MS','BAC','WFC']
    for i,c in enumerate(big): ax.plot(SA[c].values,label=c,color=AC[i],lw=1.6)
    ax.plot(SA.drop(columns=big).sum(axis=1).values,label='8 foreign IHCs (sum)',color=INK,lw=1.6,ls='--')
    for cp in b['B1_A']['market_adjusted']:
        ax.axvline(list(SA.index).index(cp['break_after'])+0.5,color='#999',lw=.8,ls=':')
    ticks(ax,SA.index); ax.set_ylabel('% of 14-dealer trading assets'); ax.set_title('PROXY · trading-asset shares, Inspect breaks (market-adjusted levels)',fontsize=9); ax.legend(fontsize=7,ncol=2)
    ax=axs[1]
    for i,c in enumerate(SE.columns): ax.plot(SE[c].values,label=c,color=AC[i],lw=1.6)
    for cp in b['B4_E4']['breaks']: ax.axvline(list(SE.index[1:]).index(cp['break_after'])+1.5,color=AC[3],lw=1.2,ls='--')
    ticks(ax,SE.index,6); ax.set_ylabel('% of big-4 trailing-4Q equity trading revenue'); ax.set_title('PROXY · equity trading revenue shares (Y-9C HI Memo 9.c); dashed = drift break',fontsize=9); ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(F+'m2_shares_breaks.png'); plt.close(fig)
    # null comparison
    fig,axs=plt.subplots(1,3,figsize=(11,3.2))
    for ax,pn in zip(axs[:2],['A','E4']):
        n2=b['B2_'+pn]; labs=['observed','iid shuffle','AR(1) matched','random walk']
        vals=[n2['observed_adj'],n2['shuffle']['mean'],n2['ar1_matched']['mean'],n2['random_walk']['mean']]
        ax.bar(labs,vals,color=[AC[3],'#bbb',AC[1],AC[4]]); ax.set_title(f'Levels test, panel {pn}: breaks found',fontsize=9); ax.tick_params(axis='x',rotation=20)
        for i,v in enumerate(vals): ax.text(i,v+.1,f'{v:.1f}',ha='center',fontsize=8)
    ax=axs[2]; labs=['A obs','A null(AR1)','E4 obs','E4 null(shuffle)','E4 null(block4)']
    vals=[b['B4_A']['observed'],b['B4_A']['null_ar1']['mean'],b['B4_E4']['observed'],b['B4_E4']['null_shuffle']['mean'],b['B4_E4']['null_block4']['mean']]
    ax.bar(labs,vals,color=[AC[3],AC[1],AC[3],'#bbb','#999']); ax.set_title('Drift test (first differences): breaks found',fontsize=9); ax.tick_params(axis='x',rotation=25)
    for i,v in enumerate(vals): ax.text(i,v+.02,f'{v:.2f}',ha='center',fontsize=8)
    fig.tight_layout(); fig.savefig(F+'m2_nulls.png'); plt.close(fig)
    # projection heatmap
    cps=b['B1_A']['market_adjusted']; cols=list(A.columns); cols=[c.replace('UBS+CS','UBS.CS') for c in cols]
    Mx=np.zeros((len(cps),len(cols)))
    for i,cp in enumerate(cps):
        for k,v in cp['share_change_pp'].items(): Mx[i,cols.index(k)]=v
    fig,ax=plt.subplots(figsize=(9,3.2)); lim=np.abs(Mx).max()
    im=ax.imshow(Mx,cmap='RdBu',vmin=-lim,vmax=lim,aspect='auto'); ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols,rotation=45,ha='right')
    ax.set_yticks(range(len(cps))); ax.set_yticklabels([f"after {c['break_after']} (cusum {c['cusum']})" for c in cps])
    for i in range(len(cps)):
        for j in range(len(cols)): ax.text(j,i,f'{Mx[i,j]:.1f}',ha='center',va='center',fontsize=6.5)
    plt.colorbar(im,ax=ax,label='share change, pp'); ax.set_title('Who moved at each Inspect break (mean share after − before, adjacent segments)',fontsize=9)
    fig.tight_layout(); fig.savefig(F+'m2_who_moved.png'); plt.close(fig)
def m1():
    a=json.load(open('out/m1_results.json'))
    for pn,firms,fn in [('E4',['JPM','GS','MS','BAC'],'m1_decomp_E4.png'),('A',['JPM','GS','MS','BAC','C','UBS.CS'],'m1_decomp_A.png')]:
        r=a['A1_'+pn]; n=len(firms); fig,axs=plt.subplots(1,n,figsize=(2.9*n,2.9),sharey=False)
        for ax,f in zip(axs,firms):
            s=r[f]['series']; q=s['q']; y=np.array(s['y']); st=np.array(s['sticky']); mk=np.array(s['market'])
            ax.plot(y,color=INK,lw=1.4,label='clr share (demeaned)'); ax.plot(st,color=AC[1],lw=1.6,label='sticky state'); ax.plot(st+mk,color=AC[0],lw=1,ls='--',label='sticky + market')
            ax.set_title(f"{f}: best={r[f]['best']}",fontsize=9); ticks(ax,q,8 if len(q)>45 else 6)
        axs[0].legend(fontsize=6.5); fig.suptitle(f'PROXY panel {pn}: MARSS decomposition (M1: random-walk state + market covariates + noise)',fontsize=9)
        fig.tight_layout(); fig.savefig(F+fn); plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(9,3))
    for ax,pn in zip(axs,['E4','A']):
        o=a['A3'][pn]; ks=list(o['rmse_share_pp'].keys()); v=[o['rmse_share_pp'][k] for k in ks]
        ax.bar(ks,v,color=[AC[3] if k=='RW' else (AC[1] if k.startswith('MARSS') else '#bbb') for k in ks]); ax.tick_params(axis='x',rotation=25)
        for i,x in enumerate(v): ax.text(i,x,f'{x:.2f}',ha='center',va='bottom',fontsize=7)
        ax.set_title(f"Panel {pn}: one-step OOS RMSE, share pp ({o['origins'][0]}–{o['origins'][1]}, n={o['n']})",fontsize=8.5)
    fig.tight_layout(); fig.savefig(F+'m1_oos.png'); plt.close(fig)
import sys
if 'm2' in sys.argv: m2()
if 'm1' in sys.argv: m1()
