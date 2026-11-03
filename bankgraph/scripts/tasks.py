"""Materialize the 5 benchmark tasks with as-of features.
Output per task: tasks/<task>/{trainval.parquet, test_features.parquet, test_labels.parquet}
Holdout rows are NOT materialized (sealed). Set RELBENCH_UNSEAL=1 only after the
pre-registered comparison is frozen and all models are final.
Feature naming: s_* = single-table (entity's own table only); r_* = needs a link to another table."""
import pandas as pd, numpy as np, os, json, sys
D='data/db'; T='tasks'
UNSEAL=os.environ.get('RELBENCH_UNSEAL')=='1'
SPLITS=json.load(open('config/splits.json'))
def L(n): return pd.read_parquet(f'{D}/{n}.parquet')

def split_of(task,cut):
    s=SPLITS[task]; c=pd.Timestamp(cut)
    for k in ['train','val','test','holdout']:
        a,b=s[k]
        if pd.Timestamp(a)<=c<=pd.Timestamp(b): return k
    return None

def write(task,df):
    df=df.copy(); df['split']=[split_of(task,c) for c in df.cutoff]; df=df[df.split.notna()]
    os.makedirs(f'{T}/{task}',exist_ok=True)
    df[df.split.isin(['train','val'])].to_parquet(f'{T}/{task}/trainval.parquet',index=False)
    te=df[df.split=='test']; te.drop(columns=['label']).to_parquet(f'{T}/{task}/test_features.parquet',index=False)
    te[['row_id','label']].to_parquet(f'{T}/{task}/test_labels.parquet',index=False)
    if UNSEAL: df[df.split=='holdout'].to_parquet(f'{T}/{task}/HOLDOUT.parquet',index=False)
    st=df.groupby('split').agg(n=('label','size'),label_mean=('label','mean')).reset_index()
    print(task); print(st.to_string())
    return st

def macro_asof(cuts):
    m=L('macro_series'); out=pd.DataFrame({'cutoff':sorted(set(cuts))})
    for s in ['DGS10','T10Y2Y','NFCI','MORTGAGE30US']:
        x=m[m.series==s].sort_values('date')[['date','value']]
        a=pd.merge_asof(out,x,left_on='cutoff',right_on='date')['value']
        x2=x.copy(); x2['date']=x2.date+pd.Timedelta(days=91)  # value 91d earlier, still <= cutoff
        b=pd.merge_asof(out,x2,left_on='cutoff',right_on='date')['value']
        out[f'r_mac_{s}']=a.values; out[f'r_mac_{s}_d3m']=(a-b).values
    return out

# ---------------- T1 bank-deposit-decline (bank x quarter) ----------------
def t1():
    b=L('bank_quarter').sort_values(['CERT','date']); g=b.groupby('CERT')
    b['dep_g']=g.DEP.pct_change(); b['label']=(g.DEP.shift(-1)/b.DEP-1<0).astype(float)
    b.loc[g.DEP.shift(-1).isna(),'label']=np.nan
    # Call report for quarter q is public ~q+30-45d; cutoff = quarter end + 45d. Label = q+1 vs q.
    b['cutoff']=b.date+pd.Timedelta(days=45)
    f=pd.DataFrame({'row_id':b.CERT.astype(str)+'_'+b.date.dt.strftime('%Y%m%d'),'CERT':b.CERT,'date':b.date,'cutoff':b.cutoff,'label':b.label})
    f['s_dep_g']=b.dep_g; f['s_dep_g_l1']=g.dep_g.shift(1); f['s_dep_g_l2']=g.dep_g.shift(2); f['s_dep_g_l4']=g.DEP.pct_change(4)
    for c in ['ASSET','ROA','NIMY','EEFFR','INTEXPY','RBC1AAJ','LNATRESR']: f['s_'+c]=b[c]
    f['s_log_asset']=np.log1p(b.ASSET); f['s_unins_share']=b.DEPUNINS/b.DEP; f['s_core_share']=b.COREDEP/b.DEP
    f['s_loan_dep']=b.LNLSNET/b.DEP; f['s_nonint_share']=b.DEPNIDOM/b.DEPDOM; f['s_brokered_proxy']=1-b.COREDEP/b.DEP
    f['s_qtr']=b.date.dt.quarter
    # relational: SOD branches (June Y, public ~Oct Y) -> latest SOD year with Y-06-30+120d <= cutoff
    br=L('branch_year'); bs=br.groupby(['CERT','YEAR']).agg(nbr=('BRNUM','size'),nst=('STALPBR','nunique'),bdep=('DEPSUMBR','sum')).reset_index()
    bs=bs.sort_values(['CERT','YEAR']); gb=bs.groupby('CERT'); bs['nbr_g']=gb.nbr.pct_change(); bs['bdep_g']=gb.bdep.pct_change()
    # state-level market deposit growth for bank's home-state footprint (deposit-weighted)
    st=br.groupby(['STALPBR','YEAR']).DEPSUMBR.sum().reset_index().sort_values(['STALPBR','YEAR']); st['st_g']=st.groupby('STALPBR').DEPSUMBR.pct_change()
    w=br.merge(st[['STALPBR','YEAR','st_g']],on=['STALPBR','YEAR']); w['wg']=w.DEPSUMBR*w.st_g
    ww=w.groupby(['CERT','YEAR']).agg(a=('wg','sum'),b=('DEPSUMBR','sum')).reset_index(); ww['foot_st_g']=ww.a/ww.b
    bs=bs.merge(ww[['CERT','YEAR','foot_st_g']],on=['CERT','YEAR'],how='left')
    bs['avail']=pd.to_datetime(bs.YEAR.astype(str)+'-06-30')+pd.Timedelta(days=120)
    f=pd.merge_asof(f.sort_values('cutoff'),bs.sort_values('avail')[['CERT','avail','nbr','nst','nbr_g','bdep_g','foot_st_g']].rename(columns=lambda c:c if c in('CERT','avail') else 'r_sod_'+c),left_on='cutoff',right_on='avail',by='CERT').drop(columns='avail')
    # relational: peers (other top-100 banks) same quarter -> cross-sectional mean dep growth & same-HQ-state mean (leave-one-out)
    pe=b[['CERT','date','dep_g','STALP']].copy()
    tot=pe.groupby('date').dep_g.agg(['sum','count']); pe=pe.join(tot,on='date'); f['r_peer_dep_g']=((pe['sum']-pe.dep_g.fillna(0))/(pe['count']-pe.dep_g.notna())).values if False else None
    pe['loo']=(pe['sum']-pe.dep_g.fillna(0))/(pe['count']-pe.dep_g.notna().astype(int))
    f=f.merge(pe[['CERT','date','loo']].rename(columns={'loo':'r_peer_dep_g'}),on=['CERT','date'],how='left').drop(columns=['r_peer_dep_g_x'],errors='ignore')
    if 'r_peer_dep_g_y' in f: f=f.rename(columns={'r_peer_dep_g_y':'r_peer_dep_g'})
    # relational: holding company has other top-100 charters
    hcn=b.groupby(['RSSDHCR','date']).CERT.nunique().rename('r_hc_ncharters').reset_index()
    f=f.merge(b[['CERT','date','RSSDHCR']],on=['CERT','date']).merge(hcn,on=['RSSDHCR','date'],how='left').drop(columns='RSSDHCR')
    # relational: HMDA originations of the bank (via LEI->RSSD panel); HMDA year Y public ~Mar Y+1 -> avail Y+1-04-01
    f=f.merge(hmda_bank_year(),how='left',on='CERT') if False else f
    hb=hmda_by_rssd(); bk=L('bank')[['CERT','RSSDID']]; hb=hb.merge(bk,left_on='respondent_rssd',right_on='RSSDID')
    hb['avail']=pd.to_datetime((hb.activity_year+1).astype(str)+'-04-01')
    f=pd.merge_asof(f.sort_values('cutoff'),hb.sort_values('avail')[['CERT','avail','n_loans','refi_share','n_loans_g']].rename(columns=lambda c:c if c in('CERT','avail') else 'r_hmda_'+c),left_on='cutoff',right_on='avail',by='CERT').drop(columns='avail')
    # relational: CFPB complaints mapped to this bank (by CERT or its RSSDHCR), months strictly before cutoff month
    cm=complaints_by_cert(); f['ym']=(f.cutoff.dt.to_period('M')-1).dt.to_timestamp()
    f=f.merge(cm,left_on=['CERT','ym'],right_on=['CERT','date'],how='left',suffixes=('','_c')).drop(columns=['ym','date_c'])
    f=f.merge(macro_asof(f.cutoff),on='cutoff',how='left')
    return write('bank-deposit-decline',f.dropna(subset=['label']))

def hmda_by_rssd():
    h=L('hmda_lender_state_year'); p=L('hmda_lender_year')[['lei','activity_year','respondent_rssd']].drop_duplicates(['lei','activity_year'])
    h=h.merge(p,on=['lei','activity_year']); h=h[h.respondent_rssd>0]
    a=h.groupby(['respondent_rssd','activity_year']).agg(n_loans=('n_loans','sum')).reset_index()
    r=h[h.loan_purpose.isin([31,32])].groupby(['respondent_rssd','activity_year']).n_loans.sum().rename('refi')
    a=a.join(r,on=['respondent_rssd','activity_year']); a['refi_share']=a.refi.fillna(0)/a.n_loans
    a=a.sort_values(['respondent_rssd','activity_year']); a['n_loans_g']=a.groupby('respondent_rssd').n_loans.pct_change()
    return a

def complaints_by_cert():
    c=L('complaint_company_month_product'); m=L('company_entity_map'); bk=L('bank')
    c=c.merge(m[['company','key','level']],on='company')
    c1=c[c.level=='bank'].rename(columns={'key':'CERT'})
    c2=c[c.level=='holdco'].merge(bk[['CERT','RSSDHCR']],left_on='key',right_on='RSSDHCR')
    c=pd.concat([c1[['CERT','date','complaints']],c2[['CERT','date','complaints']]])
    a=c.groupby(['CERT','date']).complaints.sum().reset_index().sort_values(['CERT','date'])
    a['r_cfpb_3m']=a.groupby('CERT').complaints.transform(lambda s:s.rolling(3,min_periods=1).sum())
    a['r_cfpb_g']=a.groupby('CERT').r_cfpb_3m.pct_change(3)
    return a[['CERT','date','r_cfpb_3m','r_cfpb_g']]

# ---------------- T2 branch-closure (branch x year) ----------------
def t2():
    br=L('branch_year')[['YEAR','CERT','BRNUM','RSSDHCR','STALPBR','DEPSUMBR','lat','lon']]
    br=br.drop_duplicates(['CERT','BRNUM','YEAR'])
    nxt=br[['YEAR','CERT','BRNUM','lat','lon']].copy(); nxt['YEAR']-=1
    certs_next=nxt[['YEAR','CERT']].drop_duplicates().assign(cert_alive=1)
    df=br.merge(certs_next,on=['YEAR','CERT'],how='left'); df=df[df.cert_alive==1]  # exclude whole-charter exits (mergers/failures)
    df=df.merge(nxt[['YEAR','CERT','BRNUM']].assign(same=1),on=['YEAR','CERT','BRNUM'],how='left')
    # renumbered branch guard: same CERT has a branch in Y+1 within ~100m -> not a closure
    nxt['k']=nxt.lat.round(3).astype(str)+'_'+nxt.lon.round(3).astype(str)
    df['k']=df.lat.round(3).astype(str)+'_'+df.lon.round(3).astype(str)
    df=df.merge(nxt[['YEAR','CERT','k']].drop_duplicates().assign(near=1),on=['YEAR','CERT','k'],how='left')
    df['label']=((df.same!=1)&(df.near!=1)).astype(float)
    df=df[df.YEAR<=df.YEAR.max()]  # last SOD year has no label (dropped by cert_alive merge)
    df['cutoff']=pd.to_datetime(df.YEAR.astype(str)+'-06-30')+pd.Timedelta(days=120)
    df['row_id']=df.CERT.astype(str)+'_'+df.BRNUM.astype(str)+'_'+df.YEAR.astype(str)
    # single-table: branch's own deposit history
    full=br.sort_values(['CERT','BRNUM','YEAR']); gg=full.groupby(['CERT','BRNUM'])
    full['s_dep_g1']=gg.DEPSUMBR.pct_change(); full['s_dep_g2']=gg.DEPSUMBR.pct_change(2); full['s_age_obs']=gg.cumcount()
    df=df.merge(full[['CERT','BRNUM','YEAR','s_dep_g1','s_dep_g2','s_age_obs']],on=['CERT','BRNUM','YEAR'],how='left')
    df['s_log_dep']=np.log1p(df.DEPSUMBR.clip(lower=0)); df['s_main_office']=(df.BRNUM==0).astype(int)
    df['s_lat']=df.lat; df['s_lon']=df.lon
    # relational: parent bank (CERT) footprint, bank closure rate last year (labels of Y-1 known at Y), holdco size
    bk=br.groupby(['CERT','YEAR']).agg(nbr=('BRNUM','size'),bdep=('DEPSUMBR','sum'),nst=('STALPBR','nunique')).reset_index().sort_values(['CERT','YEAR'])
    bk['nbr_g']=bk.groupby('CERT').nbr.pct_change(); bk['bdep_g']=bk.groupby('CERT').bdep.pct_change()
    df=df.merge(bk.rename(columns=lambda c:c if c in('CERT','YEAR') else 'r_bank_'+c),on=['CERT','YEAR'],how='left')
    prev=df.groupby(['CERT','YEAR']).label.mean().reset_index(); prev['YEAR']+=1  # closures during Y-1 -> Y, observed at Y
    df=df.merge(prev.rename(columns={'label':'r_bank_prev_closure_rate'}),on=['CERT','YEAR'],how='left')
    hc=br[br.RSSDHCR>0].groupby(['RSSDHCR','YEAR']).agg(hc_nbr=('BRNUM','size'),hc_ncert=('CERT','nunique')).reset_index()
    df=df.merge(hc.rename(columns={'hc_nbr':'r_hc_nbr','hc_ncert':'r_hc_ncert'}),on=['RSSDHCR','YEAR'],how='left')
    df['s_dep_share_of_bank']=df.DEPSUMBR/df.r_bank_bdep  # needs bank aggregate -> relational
    df=df.rename(columns={'s_dep_share_of_bank':'r_dep_share_of_bank'})
    # relational: local density via ~0.05deg grid (other banks' branches / own-bank branches in same cell)
    br2=br.copy(); br2['cell']=(br2.lat/0.05).round().astype('Int64').astype(str)+'_'+(br2.lon/0.05).round().astype('Int64').astype(str)
    df['cell']=(df.lat/0.05).round().astype('Int64').astype(str)+'_'+(df.lon/0.05).round().astype('Int64').astype(str)
    cn=br2.groupby(['YEAR','cell']).agg(cell_n=('BRNUM','size'),cell_dep=('DEPSUMBR','sum')).reset_index()
    co=br2.groupby(['YEAR','cell','CERT']).BRNUM.size().rename('own_n').reset_index()
    df=df.merge(cn,on=['YEAR','cell'],how='left').merge(co,on=['YEAR','cell','CERT'],how='left')
    df['r_cell_other_n']=df.cell_n-df.own_n; df['r_cell_own_n']=df.own_n-1; df['r_cell_log_dep']=np.log1p(df.cell_dep.clip(lower=0))
    st=br.groupby(['STALPBR','YEAR']).DEPSUMBR.sum().reset_index().sort_values(['STALPBR','YEAR']); st['r_state_dep_g']=st.groupby('STALPBR').DEPSUMBR.pct_change()
    df=df.merge(st[['STALPBR','YEAR','r_state_dep_g']],on=['STALPBR','YEAR'],how='left')
    keep=['row_id','CERT','BRNUM','YEAR','cutoff','label']+[c for c in df if c.startswith(('s_','r_'))]
    return write('branch-closure',df[keep])

# ---------------- T3 complaint-spike (company x month) ----------------
def t3():
    c=L('complaint_company_month_product')
    c=c[c.date<'2026-10-01']  # Oct-2026 partial month in snapshot
    tot=c.groupby(['company','date']).complaints.sum().unstack(fill_value=0).stack().rename('n').reset_index().sort_values(['company','date'])
    g=tot.groupby('company').n
    tot['med6']=g.transform(lambda s:s.rolling(6,min_periods=6).median()); tot['nxt']=g.shift(-1)
    tot['vol6']=g.transform(lambda s:s.rolling(6,min_periods=6).sum())
    tot=tot[(tot.vol6>=60)&tot.nxt.notna()]  # eligible: >=10/month avg over trailing 6 months
    tot['label']=((tot.nxt>=2*tot.med6.clip(lower=1))&(tot.nxt>=20)).astype(float)
    tot['cutoff']=tot.date+pd.offsets.MonthEnd(0)
    f=tot[['company','date','cutoff','label']].copy(); f['row_id']=f.company+'_'+f.date.dt.strftime('%Y%m')
    full=c.groupby(['company','date']).complaints.sum().rename('n').reset_index().sort_values(['company','date'])
    full=full.set_index(['company','date']).n.unstack(fill_value=0).stack().rename('n').reset_index().sort_values(['company','date'])
    gf=full.groupby('company').n
    for k in [0,1,2,3,6,12]: full[f's_lag{k}']=gf.shift(k)
    full['s_ratio_med6']=full.n/gf.transform(lambda s:s.rolling(6,min_periods=1).median()).clip(lower=1)
    full['s_ratio_mean12']=full.n/gf.transform(lambda s:s.rolling(12,min_periods=1).mean()).clip(lower=1)
    full['s_max6']=gf.transform(lambda s:s.rolling(6,min_periods=1).max())
    f=f.merge(full.drop(columns='n'),on=['company','date'],how='left'); f['s_month']=f.date.dt.month
    # relational: product mix of the company (product table) + market-wide product momentum (other companies)
    pm=c.groupby(['company','date','product']).complaints.sum().reset_index()
    mk=pm.groupby(['date','product']).complaints.sum().rename('mkt').reset_index().sort_values(['product','date'])
    mk['mkt_g']=mk.groupby('product').mkt.pct_change(); mk['mkt_g3']=mk.groupby('product').mkt.pct_change(3)
    pm=pm.merge(mk,on=['date','product']); pm['w']=pm.complaints/pm.groupby(['company','date']).complaints.transform('sum')
    agg=pm.assign(a=pm.w*pm.mkt_g,b=pm.w*pm.mkt_g3,h=pm.w**2).groupby(['company','date']).agg(r_mix_mkt_g=('a','sum'),r_mix_mkt_g3=('b','sum'),r_prod_hhi=('h','sum'),r_nprod=('product','nunique')).reset_index()
    f=f.merge(agg,on=['company','date'],how='left')
    top=pm.sort_values('complaints').groupby(['company','date']).tail(1)[['company','date','product']].rename(columns={'product':'r_top_product'})
    f=f.merge(top,on=['company','date'],how='left'); f['r_top_product']=f.r_top_product.astype('category').cat.codes
    allm=full.groupby('date').n.sum().rename('r_all_n').reset_index(); allm['r_all_g']=allm.r_all_n.pct_change()
    f=f.merge(allm,on='date',how='left')
    # relational: linked bank fundamentals (call report via name->CERT/RSSDHCR), as of cutoff (call report lag 45d)
    m=L('company_entity_map'); bq=L('bank_quarter'); bk=L('bank')
    bq=bq.sort_values(['CERT','date']); bq['dep_g']=bq.groupby('CERT').DEP.pct_change(); bq['avail']=bq.date+pd.Timedelta(days=45)
    lk=pd.concat([m[m.level=='bank'].rename(columns={'key':'CERT'})[['company','CERT']], m[m.level=='holdco'].merge(bk[['CERT','RSSDHCR']],left_on='key',right_on='RSSDHCR')[['company','CERT']]])
    lk=lk.merge(bq[['CERT','ASSET']].groupby('CERT').ASSET.max().reset_index()).sort_values('ASSET').groupby('company').tail(1)[['company','CERT']]
    f=f.merge(lk,on='company',how='left'); f['r_linked_bank']=f.CERT.notna().astype(int)
    fa=f[f.CERT.notna()].copy(); fa['CERT']=fa.CERT.astype('int64'); fb=f[f.CERT.isna()].copy()
    fa=pd.merge_asof(fa.sort_values('cutoff'),bq.sort_values('avail')[['CERT','avail','ASSET','dep_g','ROA']].rename(columns={'ASSET':'r_bank_asset','dep_g':'r_bank_dep_g','ROA':'r_bank_roa'}),left_on='cutoff',right_on='avail',by='CERT').drop(columns='avail')
    f=pd.concat([fa,fb]).drop(columns='CERT')
    f=f.merge(macro_asof(f.cutoff),on='cutoff',how='left')
    return write('complaint-spike',f)

# ---------------- T4 hmda-share-drop (lender x state x year) ----------------
def t4():
    h=L('hmda_lender_state_year'); a=h.groupby(['lei','state_code','activity_year']).agg(n=('n_loans','sum'),amt=('total_amount','sum')).reset_index()
    mk=a.groupby(['state_code','activity_year']).n.sum().rename('mkt').reset_index(); a=a.merge(mk); a['share']=a.n/a.mkt
    nx=a[['lei','state_code','activity_year','share']].copy(); nx['activity_year']-=1
    a=a.merge(nx.rename(columns={'share':'share_next'}),on=['lei','state_code','activity_year'],how='left')
    a=a[(a.activity_year<a.activity_year.max())&(a.n>=50)]
    a['share_next']=a.share_next.fillna(0); a['label']=(a.share_next<0.75*a.share).astype(float)
    a['cutoff']=pd.to_datetime((a.activity_year+1).astype(str)+'-04-01')  # HMDA Y published ~Mar Y+1
    a['row_id']=a.lei+'_'+a.state_code+'_'+a.activity_year.astype(str)
    pr=a[['lei','state_code','activity_year','share','n']].copy(); pr['activity_year']+=1
    a=a.merge(pr.rename(columns={'share':'s_share_prev','n':'s_n_prev'}),on=['lei','state_code','activity_year'],how='left')
    a['s_share']=a.share; a['s_log_n']=np.log1p(a.n); a['s_share_g']=a.share/a.s_share_prev-1; a['s_avg_amt']=a.amt/a.n
    pp=h.pivot_table(index=['lei','state_code','activity_year'],columns='loan_purpose',values='n_loans',aggfunc='sum',fill_value=0)
    pp=pp.div(pp.sum(1),axis=0); pp.columns=[f's_purp_{c}' for c in pp.columns]; a=a.merge(pp.reset_index(),on=['lei','state_code','activity_year'],how='left')
    # relational: lender national footprint (other states), lender type (FFIEC panel), parent bank branches in state (SOD), state market growth
    nat=a.groupby(['lei','activity_year']).agg(r_lender_nstates=('state_code','nunique')).reset_index()
    tot=h.groupby(['lei','activity_year']).n_loans.sum().rename('r_lender_log_n').reset_index(); tot['r_lender_log_n']=np.log1p(tot.r_lender_log_n)
    a=a.merge(nat,how='left').merge(tot,how='left')
    a['r_state_share_of_lender']=a.n/np.expm1(a.r_lender_log_n)
    mk=mk.sort_values(['state_code','activity_year']); mk['r_mkt_g']=mk.groupby('state_code').mkt.pct_change(); a=a.merge(mk[['state_code','activity_year','r_mkt_g']],how='left')
    p=L('hmda_lender_year').drop_duplicates(['lei','activity_year'])
    a=a.merge(p[['lei','activity_year','respondent_rssd','topholder_rssd','agency_code','other_lender_code','assets']].rename(columns={'agency_code':'r_agency','other_lender_code':'r_other_lender_code'}),on=['lei','activity_year'],how='left')
    a['r_log_assets']=np.log1p(pd.to_numeric(a.assets,errors='coerce').clip(lower=0))
    br=L('branch_year'); br=br[br.YEAR<=2024]
    # SOD June Y+0 published ~Oct Y -> available before cutoff (Apr Y+1)
    bs=br.groupby(['RSSDID','STALPBR','YEAR']).agg(r_sod_nbr_state=('BRNUM','size'),r_sod_dep_state=('DEPSUMBR','sum')).reset_index()
    a=a.merge(bs,left_on=['respondent_rssd','state_code','activity_year'],right_on=['RSSDID','STALPBR','YEAR'],how='left').drop(columns=['RSSDID','STALPBR','YEAR'])
    hs=br[br.RSSDHCR>0].groupby(['RSSDHCR','STALPBR','YEAR']).agg(r_hc_nbr_state=('BRNUM','size')).reset_index()
    a=a.merge(hs,left_on=['topholder_rssd','state_code','activity_year'],right_on=['RSSDHCR','STALPBR','YEAR'],how='left').drop(columns=['RSSDHCR','STALPBR','YEAR'])
    a['r_is_depository']=a.respondent_rssd.isin(set(br.RSSDID)).astype(int)
    a['r_log_assets']=a.r_log_assets
    a=a.merge(macro_asof(a.cutoff),on='cutoff',how='left')
    keep=['row_id','lei','state_code','activity_year','cutoff','label']+[c for c in a if c.startswith(('s_','r_'))]
    return write('hmda-share-drop',a[keep])

# ---------------- T5 hc-state-deposit-growth (regression) ----------------
def t5():
    h=L('hc_state_year'); h=h[(h.RSSDHCR>0)]
    h=h.groupby(['RSSDHCR','STALPBR','YEAR']).branch_deposits_000s.sum().rename('dep').reset_index()
    nx=h.copy(); nx['YEAR']-=1
    a=h.merge(nx.rename(columns={'dep':'dep_next'}),on=['RSSDHCR','STALPBR','YEAR'])
    a=a[(a.dep>=10000)&(a.dep_next>0)]
    a['label']=np.log(a.dep_next/a.dep).clip(-1,1)
    a['cutoff']=pd.to_datetime(a.YEAR.astype(str)+'-06-30')+pd.Timedelta(days=120)
    a['row_id']=a.RSSDHCR.astype(int).astype(str)+'_'+a.STALPBR+'_'+a.YEAR.astype(str)
    pr=h.copy(); pr['YEAR']+=1; a=a.merge(pr.rename(columns={'dep':'dep_prev'}),on=['RSSDHCR','STALPBR','YEAR'],how='left')
    pr2=h.copy(); pr2['YEAR']+=2; a=a.merge(pr2.rename(columns={'dep':'dep_prev2'}),on=['RSSDHCR','STALPBR','YEAR'],how='left')
    a['s_log_dep']=np.log(a.dep); a['s_g1']=np.log(a.dep/a.dep_prev).clip(-3,3); a['s_g2']=np.log(a.dep_prev/a.dep_prev2).clip(-3,3)
    # relational: holdco total & #states, state market growth, branch counts (SOD branch table), HMDA lending in state by topholder (Y-1, avail)
    hc=h.groupby(['RSSDHCR','YEAR']).agg(t=('dep','sum'),ns=('STALPBR','nunique')).reset_index().sort_values(['RSSDHCR','YEAR'])
    hc['r_hc_g']=np.log(hc.t/hc.groupby('RSSDHCR').t.shift(1)).clip(-3,3); hc['r_hc_log_tot']=np.log(hc.t); hc['r_hc_nstates']=hc.ns
    a=a.merge(hc[['RSSDHCR','YEAR','r_hc_g','r_hc_log_tot','r_hc_nstates']],how='left'); a['r_state_share_of_hc']=a.dep/np.exp(a.r_hc_log_tot)
    st=h.groupby(['STALPBR','YEAR']).dep.sum().reset_index().sort_values(['STALPBR','YEAR']); st['r_state_g']=np.log(st.dep/st.groupby('STALPBR').dep.shift(1))
    a=a.merge(st[['STALPBR','YEAR','r_state_g']],how='left')
    br=L('branch_year'); bs=br[br.RSSDHCR>0].groupby(['RSSDHCR','STALPBR','YEAR']).agg(n=('BRNUM','size')).reset_index().sort_values(['RSSDHCR','STALPBR','YEAR'])
    bs['r_nbr_g']=bs.groupby(['RSSDHCR','STALPBR']).n.pct_change(); bs['r_log_nbr']=np.log1p(bs.n)
    a=a.merge(bs[['RSSDHCR','STALPBR','YEAR','r_nbr_g','r_log_nbr']],how='left')
    hm=L('hmda_lender_state_year'); p=L('hmda_lender_year').drop_duplicates(['lei','activity_year'])[['lei','activity_year','topholder_rssd']]
    hm=hm.merge(p,on=['lei','activity_year']); hs=hm.groupby(['topholder_rssd','state_code','activity_year']).n_loans.sum().reset_index()
    hs['YEAR']=hs.activity_year+1  # HMDA Y available ~Apr Y+1 < cutoff Oct Y+1
    a=a.merge(hs.rename(columns={'topholder_rssd':'RSSDHCR','state_code':'STALPBR','n_loans':'r_hmda_n_prev'})[['RSSDHCR','STALPBR','YEAR','r_hmda_n_prev']],how='left')
    a['r_hmda_n_prev']=np.log1p(a.r_hmda_n_prev)
    a=a.merge(macro_asof(a.cutoff),on='cutoff',how='left')
    keep=['row_id','RSSDHCR','STALPBR','YEAR','cutoff','label']+[c for c in a if c.startswith(('s_','r_'))]
    return write('hc-state-deposit-growth',a[keep])

if __name__=='__main__':
    which=sys.argv[1:] or ['t1','t2','t3','t4','t5']
    for w in which: globals()[w]()
