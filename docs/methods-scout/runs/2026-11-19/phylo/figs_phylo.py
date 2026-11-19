import pandas as pd,numpy as np,json,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT='/workspace/methods-scout/2026-11-19/fig/'
AMB,TEAL,INK,MUT,RED='#e8902e','#1f9e8e','#1c150d','#6f5f46','#df5236'
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
PAL=['#1f9e8e','#e8902e','#5b6abf','#9c5bb5','#3c8d3c','#b5835a','#c2417a']
S=json.load(open('q2_scores_Corning_mock_MorganStanley_mock.json'))
for f,tag,ttl in [('Corning_mock','corning','Corning-like'),('MorganStanley_mock','ms','Morgan Stanley-like')]:
    d=pd.read_csv(f+'_scored.csv',keep_default_na=False,na_values=['']); d['cluster']=d.cluster.fillna('')
    d=d.sort_values(['segment','subsegment','function','stated_intent','slope']).reset_index(drop=True); n=len(d)
    th=np.linspace(0,2*np.pi,n,endpoint=False)+np.pi/2
    fig=plt.figure(figsize=(13,6.6))
    ax=fig.add_subplot(1,2,2,projection='polar'); ax.set_axis_off()
    r0=1.0; sc=3.0/np.quantile(np.abs(d.slope),.99)
    col=np.where((d.p<0.05)&(d.lipa>0),TEAL,np.where((d.p<0.05)&(d.lipa<0),RED,'#cfc4ae'))
    ax.bar(th,np.clip(d.slope*sc,-0.95,3.2),width=2*np.pi/n*0.95,bottom=r0+1.0,color=col,lw=0)
    segs=d.segment.astype('category').cat.codes
    ax.bar(th,0.35,width=2*np.pi/n,bottom=r0,color=[PAL[s%len(PAL)] for s in segs],lw=0)
    # function boundaries as thin rings (the tree's lowest grouping)
    fn=(d.function!=d.function.shift()).values
    ax.bar(th[fn],0.25,width=2*np.pi/n*0.6,bottom=r0+0.4,color=INK,lw=0)
    # answer-key overlay ring (scoring only)
    cl=sorted([c for c in d.cluster.unique() if c]); cc={c:['#000000','#7a5c00','#8a2be2'][i%3] for i,c in enumerate(cl)}
    m=d.cluster!=''
    ax.scatter(th[m],np.full(m.sum(),r0+4.5),s=6,color=[cc[c] for c in d.cluster[m]])
    ax.set_ylim(0,5.8)
    ax.set_title(f'This method: program tree, growth bars coloured by LIPA\n(teal = like its relatives, red = unlike, grey = n.s.; outer dots = planted groups, answer key)',fontsize=9.5)
    for i,c in enumerate(cl): fig.text(0.56+0.13*i,0.04,f'• {c.replace("_"," ")}',color=cc[c],fontsize=7.5)
    # standard: boxplot by function
    ax2=fig.add_subplot(1,2,1); g=d.groupby('function').slope; order=g.median().sort_values().index
    ax2.boxplot([d.slope[d.function==k] for k in order],orientation="horizontal",widths=.6,flierprops=dict(markersize=1.5),medianprops=dict(color=AMB))
    ax2.set_yticks(range(1,len(order)+1)); ax2.set_yticklabels([k[:28] for k in order],fontsize=5.2); ax2.set_xlabel('Per-program OLS slope of log actual (per year)')
    ax2.set_title(f'Usual tool: growth by function ({len(order)} boxes)',fontsize=9.5,loc='left')
    fig.suptitle(f'SYNTHETIC {ttl} mock, {n} programs: same slopes, two views',fontsize=11)
    fig.tight_layout(rect=(0,0.05,1,0.95)); fig.savefig(OUT+f'phylo_tree_{tag}.png'); plt.close()
# signal attenuation chart
fig,ax=plt.subplots(figsize=(7.6,3.3)); rows=[]
for f,lab in [('Corning_mock','Corning-like'),('MorganStanley_mock','MS-like')]:
    st={r['_row']:r for r in S[f]['signal']['label']['stat']}; stt={r['_row']:r for r in S[f]['signal']['text']['stat']}
    rows+= [(f'{lab}: labels, true',st['slope_true']['Lambda']),(f'{lab}: labels, observed',st['slope']['Lambda']),(f'{lab}: text, observed',stt['slope']['Lambda'])]
ax.barh(range(len(rows))[::-1],[r[1] for r in rows],color=[AMB,TEAL,'#b8ab92']*2)
for i,(l,v) in zip(range(len(rows))[::-1],rows): ax.text(v+.01,i,f'{v:.2f}',va='center',fontsize=8)
ax.set_yticks(range(len(rows))[::-1]); ax.set_yticklabels([r[0] for r in rows],fontsize=8); ax.set_xlabel("Pagel's λ of program growth on the tree (0 = tree says nothing, 1 = Brownian)")
fig.tight_layout(); fig.savefig(OUT+'phylo_lambda.png'); plt.close()
# walk-forward bars
fig,axs=plt.subplots(1,2,figsize=(9,3.2))
for ax,(f,lab) in zip(axs,[('Corning_mock','Corning-like'),('MorganStanley_mock','MS-like')]):
    R=S[f]['P4_rmse_vs_observed']; ks=['ols_trend','sarimax100','ardl1','zero','blend','phylo_nb']; nm=['OLS trend','SARIMAX(1,0,0)','ARDL(1) pooled','No change','50/50 blend','Relatives (tree)']
    v=[min(R[k],0.4) for k in ks]
    ax.barh(range(len(ks)),v,color=['#b8ab92','#b8ab92','#b8ab92','#b8ab92',TEAL,TEAL]); ax.set_yticks(range(len(ks))); ax.set_yticklabels(nm,fontsize=8)
    for i,k in enumerate(ks): ax.text(v[i]+.003,i,f'{R[k]:.3f}' if R[k]<10 else 'diverged',va='center',fontsize=7.5)
    ax.set_xlim(0,.42); ax.set_title(lab,fontsize=9,loc='left'); ax.set_xlabel('RMSE, last-year log growth')
fig.tight_layout(); fig.savefig(OUT+'phylo_walkforward.png'); plt.close()
# cluster localisation
C=json.load(open('cluster_localisation.json'))
fig,ax=plt.subplots(figsize=(7.6,2.9)); labs=[];vals=[];cols=[]
for f,lab in [('Corning_mock','Corning-like'),('MorganStanley_mock','MS-like')]:
    p=C[f]['co_move_precision']
    for k,nm,c in [('own_slope','own slope (top-k)','#b8ab92'),('lipa','LIPA like-relatives','#1f9e8e'),('abs_cell_mean','|category-cell mean|','#e8902e')]:
        labs.append(f'{lab}: {nm}'); vals.append(p[k]); cols.append(c)
ax.barh(range(len(vals))[::-1],vals,color=cols)
for i,v in zip(range(len(vals))[::-1],vals): ax.text(v+.005,i,f'{v:.2f}',va='center',fontsize=8)
ax.set_yticks(range(len(vals))[::-1]); ax.set_yticklabels(labs,fontsize=7.5); ax.set_xlabel('Share of flagged programs in a planted group (same number of flags)')
fig.tight_layout(); fig.savefig(OUT+'phylo_cluster_precision.png'); plt.close()
print('ok')
