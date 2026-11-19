import pandas as pd,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT='/workspace/methods-scout/2026-11-19/fig/'
AMB,TEAL,INK,MUT,RED='#e8902e','#1f9e8e','#1c150d','#6f5f46','#df5236'
PAL=['#1f9e8e','#e8902e','#5b6abf','#9c5bb5','#3c8d3c','#b5835a','#c2417a']
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':130})
d=pd.read_csv('MorganStanley_mock_scored.csv',keep_default_na=False,na_values=['']); d['cluster']=d.cluster.fillna('')
d=d.sort_values(['segment','subsegment','function','stated_intent','slope']).reset_index(drop=True); n=len(d)
fig,ax=plt.subplots(figsize=(6,7.5)); g=d.groupby('function').slope; order=g.median().sort_values().index
ax.boxplot([d.slope[d.function==k] for k in order],orientation='horizontal',widths=.6,flierprops=dict(markersize=1.5),medianprops=dict(color=AMB))
ax.set_yticks(range(1,len(order)+1)); ax.set_yticklabels([k[:30] for k in order],fontsize=6); ax.set_xlabel('Per-program OLS slope of log actual (per year)')
ax.set_title(f'Usual: growth by function ({len(order)} boxes), SYNTHETIC MS-like',fontsize=9.5,loc='left'); fig.tight_layout(); fig.savefig(OUT+'phylo_std_box_ms.png'); plt.close()
th=np.linspace(0,2*np.pi,n,endpoint=False)+np.pi/2
fig=plt.figure(figsize=(7,7.5)); ax=fig.add_subplot(projection='polar'); ax.set_axis_off(); r0=1.0; sc=3.0/np.quantile(np.abs(d.slope),.99)
col=np.where((d.p<0.05)&(d.lipa>0),TEAL,np.where((d.p<0.05)&(d.lipa<0),RED,'#cfc4ae'))
ax.bar(th,np.clip(d.slope*sc,-0.95,3.2),width=2*np.pi/n*0.95,bottom=r0+1.0,color=col,lw=0)
segs=d.segment.astype('category').cat.codes; ax.bar(th,0.35,width=2*np.pi/n,bottom=r0,color=[PAL[s%len(PAL)] for s in segs],lw=0)
cl=sorted([c for c in d.cluster.unique() if c]); cc={c:['#000000','#7a5c00','#8a2be2'][i%3] for i,c in enumerate(cl)}; m=d.cluster!=''
ax.scatter(th[m],np.full(m.sum(),r0+4.5),s=6,color=[cc[c] for c in d.cluster[m]]); ax.set_ylim(0,5.8)
ax.set_title('Tree view: 1,404 programs around the hierarchy (inner ring = segment);\nbar = growth, teal = like relatives, red = unlike (LIPA p < 0.05);\nouter dots = planted groups (answer key, scoring only)',fontsize=9)
fig.tight_layout(); fig.savefig(OUT+'phylo_tree_only_ms.png'); plt.close(); print('ok')
