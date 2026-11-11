"""Build PROXY share panels for Q1 from the FR Y-9C trading panel (public FFIEC/NIC BHCF data).
Outputs aggregate share panels only (shares of named top dealer BHCs + quarterly market factors)."""
import pandas as pd, numpy as np, json, os
SRC='/workspace/rl_check/tracks/y9c-trading-ot/data/processed_v1_1/trading_panel.parquet'
FRED='/workspace/rl_check/tracks/y9c-trading-ot/data/fred_v1_1/'
OUT='/workspace/scout/1111/data/'
p=pd.read_parquet(SRC); p['q']=p.quarter.astype(str)
BIG={'JPM':1039502,'GS':2380443,'MS':2162966,'BAC':1073757,'C':1951350,'WFC':1120754}
IHC={'Barclays':[5006575],'UBS+CS':[4846998,1574834],'DB':[2816906],'BNP':[1575569],'HSBC':[3232316],
     'Mizuho':[5034792],'RBC':[5280254,3226762],'TD':[3606542]}
def series(col, ids, mode='sum'):
    s=p[p.rssd_id.isin(ids)].pivot_table(index='q',columns='rssd_id',values=col,aggfunc='sum')
    if mode=='rbc':  # RBC: use IHC (5280254) when present else holdco (avoid nested double count)
        a=s.get(5280254); b=s.get(3226762); return a.fillna(b) if a is not None else b
    return s.sum(axis=1,min_count=1)
# ---- Panel A: trading-asset (balance/activity) shares, 2016Q3-2026Q2, 14 named dealers
qs=sorted(p.q.unique()); qa=[q for q in qs if q>='2016Q3']
A={}
for k,v in BIG.items(): A[k]=series('trading_assets',[v])
for k,v in IHC.items(): A[k]=series('trading_assets',v,'rbc' if k=='RBC' else 'sum')
A=pd.DataFrame(A).loc[qa]
assert A.notna().all().all() and (A>0).all().all(), A.isna().sum()
# ---- Panel E: equity trading revenue (HI Memo 9.c), trailing-4Q sums
E={}
for k,v in BIG.items(): E[k]=series('trd_equity_q',[v])
ihc_ids=sum(IHC.values(),[])
e_ihc=p[p.rssd_id.isin([i for i in ihc_ids if i!=3226762])].pivot_table(index='q',columns='rssd_id',values='trd_equity_q',aggfunc='sum')
E['FBO_IHCs']=e_ihc.sum(axis=1,min_count=1)
E=pd.DataFrame(E).loc[qs].rolling(4).sum()
E4=E[['JPM','GS','MS','BAC']].loc['2011Q1':]  # start after the 2009-10 base-effect spike in industry growth  # Citi excluded: negative T4 equity trading revenue in some quarters
for nm,df in [('E4',E4)]:
    print(nm, df.shape, 'min', df.min().round(0).to_dict())
# ---- market factors (quarterly)
def fred(n):
    d=pd.read_csv(FRED+n+'.csv',parse_dates=['observation_date']).set_index('observation_date')[n]
    d=pd.to_numeric(d,errors='coerce').dropna(); return d
vix=fred('VIXCLS').resample('QE').mean(); nas=fred('NASDAQCOM').resample('QE').last(); baa=fred('BAA10Y').resample('QE').mean()
M=pd.DataFrame({'vix':vix,'nasdaq_ret4':np.log(nas).diff(4),'baa10y':baa})
M.index=M.index.to_period('Q').astype(str)
M['eq_rev_ind_g4']=np.log(E[['JPM','GS','MS','BAC']].sum(axis=1)).diff(4)   # industry size (big-5 T4 equity rev) growth
M['ta_ind_g1']=np.log(A.sum(axis=1)).reindex(M.index).diff(1)
M.loc['2016Q3','ta_ind_g1']=0.0  # first panel quarter: no prior total
for nm,df in [('A',A),('E4',E4)]:
    df.to_csv(OUT+f'panel_{nm}.csv')
M.loc['2009Q1':'2026Q2'].to_csv(OUT+'market_q.csv')
sh=A.div(A.sum(1),axis=0); she=E4.div(E4.sum(1),axis=0)
summ={'A_first':sh.iloc[0].round(4).to_dict(),'A_last':sh.iloc[-1].round(4).to_dict(),
      'E4_first':she.iloc[0].round(4).to_dict(),'E4_last':she.iloc[-1].round(4).to_dict(),
      'E4_2019Q4':she.loc['2019Q4'].round(4).to_dict(),
      'A_quarters':[qa[0],qa[-1],len(qa)],'E4_quarters':[E4.index[0],E4.index[-1],len(E4)]}
json.dump(summ,open(OUT+'panel_summary.json','w'),indent=1); print(json.dumps(summ,indent=1))
