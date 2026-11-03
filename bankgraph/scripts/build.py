"""Build the linked relational dataset (parquet + duckdb) from data/raw (Drive) and data/ext (public).
Run: python scripts/build.py   -> data/db/*.parquet, data/db/bankgraph.duckdb, reports/inventory.json, reports/join_coverage.csv"""
import pandas as pd, numpy as np, glob, re, json, zipfile, io, os, duckdb
R='data/raw'; E='data/ext'; D='data/db'; os.makedirs(D,exist_ok=True); os.makedirs('reports',exist_ok=True)
inv={}
def save(name,df,grain,keys,tcol=None):
    df.to_parquet(f'{D}/{name}.parquet',index=False)
    rng=(str(df[tcol].min()),str(df[tcol].max())) if tcol else None
    inv[name]=dict(rows=len(df),cols=len(df.columns),grain=grain,keys=keys,time_col=tcol,range=rng)
    print(name,df.shape,rng)

# --- call report (bank-quarter, top-100 by 2026Q2 assets) ---
cr=pd.read_csv(f'{R}/call_report_panel_top100.csv.gz',low_memory=False)
cr['date']=pd.to_datetime(cr.REPDTE.astype(str))
keep=['date','CERT','RSSDID','RSSDHCR','NAME','NAMEHCR','STALP','ASSET','DEP','DEPDOM','DEPFOR','COREDEP','DEPINS','DEPUNINS','DEPNIDOM','LNLSNET','EQ','NETINC','ROA','ROE','NIMY','EEFFR','NUMEMP','NPERFV','LNATRESR','NTLNLSR','RBC1AAJ','RBCRWAJ','INTEXPY','OFFDOM','SZLNRES','SZLNCRCD','FREPO','CHBAL','LIAB','TRADE','BKCLASS']
bq=cr[keep].copy(); save('bank_quarter',bq,'bank (CERT) x quarter',['CERT','date'],'date')
bank=cr.sort_values('date').groupby('CERT').last().reset_index()[['CERT','RSSDID','RSSDHCR','NAME','NAMEHCR','STALP','BKCLASS']]
save('bank',bank,'bank charter (CERT)',['CERT'])

# --- SOD branches (branch-year, all FDIC-insured, June 30) ---
sod=pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f'{R}/sod_branches_*.csv.gz')) if int(f[-11:-7])>=2008],ignore_index=True)
sod=sod.rename(columns={'SIMS_LATITUDE':'lat','SIMS_LONGITUDE':'lon'})
br=sod[['YEAR','CERT','BRNUM','RSSDID','RSSDHCR','NAMEFULL','NAMEHCR','NAMEBR','STALPBR','DEPSUMBR','lat','lon']].copy()
br['date']=pd.to_datetime(br.YEAR.astype(str)+'-06-30')
save('branch_year',br,'branch (CERT,BRNUM) x year (June 30)',['CERT','BRNUM','YEAR'],'date')
hc=pd.read_csv(f'{R}/sod_panel_hc_state_year.csv'); hc=hc[hc.YEAR>=2008]
hc['date']=pd.to_datetime(hc.YEAR.astype(str)+'-06-30')
save('hc_state_year',hc,'holding co (RSSDHCR) x state x year',['RSSDHCR','STALPBR','YEAR'],'date')
holdco=pd.concat([br[['RSSDHCR','NAMEHCR','YEAR']],cr.assign(YEAR=cr.date.dt.year)[['RSSDHCR','NAMEHCR','YEAR']]]).dropna()
holdco=holdco[holdco.RSSDHCR>0].sort_values('YEAR').groupby('RSSDHCR').last().reset_index()
save('holding_company',holdco[['RSSDHCR','NAMEHCR']],'holding co (RSSDHCR)',['RSSDHCR'])
save('state',pd.DataFrame({'STALP':sorted(br.STALPBR.dropna().unique())}),'state',['STALP'])

# --- HMDA lender x state x year (+ FFIEC reporter panel LEI->RSSD, public ext) ---
hm=pd.read_csv(f'{R}/hmda_panel_lender_state_year.csv.gz'); hm['date']=pd.to_datetime(hm.activity_year.astype(str)+'-12-31')
save('hmda_lender_state_year',hm,'LEI x state x year x loan_purpose (originations)',['lei','state_code','activity_year','loan_purpose'],'date')
pn=pd.concat([pd.read_csv(f,dtype=str) for f in sorted(glob.glob(f'{E}/20*_public_panel_csv.csv'))],ignore_index=True)
pn=pn[['activity_year','lei','agency_code','respondent_rssd','respondent_name','assets','other_lender_code','parent_rssd','topholder_rssd','topholder_name']]
for c in ['activity_year','respondent_rssd','parent_rssd','topholder_rssd','agency_code','other_lender_code']: pn[c]=pd.to_numeric(pn[c],errors='coerce')
save('hmda_lender_year',pn,'LEI x year (FFIEC HMDA reporter panel, ext)',['lei','activity_year'],'activity_year')

# --- CFPB complaints company x month x product ---
cf=pd.read_csv(f'{R}/cfpb_panel_company_month_product.csv.gz'); cf['date']=pd.to_datetime(cf.yyyymm+'-01')
save('complaint_company_month_product',cf,'company x month x product',['company','yyyymm','product'],'date')

# --- macro ---
mac=[]
for s in ['DGS10','T10Y2Y','NFCI','MORTGAGE30US']:
    m=pd.read_csv(f'{R}/{s}.csv'); m.columns=['date','value']; m['series']=s; mac.append(m)
mac=pd.concat(mac); mac['date']=pd.to_datetime(mac.date); mac['value']=pd.to_numeric(mac.value,errors='coerce'); mac=mac.dropna()
mac=mac[mac.date>='2000-01-01']
save('macro_series',mac,'series x date (as observed date)',['series','date'],'date')
sl=pd.read_csv(f'{R}/sloos_panel.csv.gz'); sl['date']=pd.to_datetime(sl.date)
save('sloos_series',sl[['series','date','value','description']],'SLOOS series x survey quarter',['series','date'],'date')

# --- BHCF (FR Y-9C) holding company quarter, one local quarter only ---
with zipfile.ZipFile(f'{R}/BHCF20171231.zip') as z:
    t=pd.read_csv(io.BytesIO(z.read(z.namelist()[0])),sep='^',low_memory=False,usecols=['RSSD9001','RSSD9999','BHCK2170'])
t=t.iloc[1:] if not str(t.iloc[0,0]).isdigit() else t
t=t.rename(columns={'RSSD9001':'RSSDHCR','RSSD9999':'date','BHCK2170':'total_assets'}).apply(pd.to_numeric,errors='coerce')
save('bhcf_hc_quarter_2017q4',t,'holding co x quarter (Y-9C, 2017Q4 sample only)',['RSSDHCR'])

# ================= JOIN COVERAGE (measured) =================
cov=[]
def add(src,tgt,key,num,den,note=''):
    cov.append(dict(source=src,target=target if False else tgt,key=key,matched=int(num),total=int(den),share=round(num/den,4) if den else None,note=note))
# 1 HMDA LEI -> RSSD (panel) by LEI and by loan volume
hl=hm.groupby(['lei','activity_year']).n_loans.sum().reset_index()
pk=pn.dropna(subset=['respondent_rssd']); pk=pk[pk.respondent_rssd>0][['lei','activity_year','respondent_rssd','topholder_rssd','agency_code']]
pk=pk.drop_duplicates(['lei','activity_year'])
m=hl.merge(pk,on=['lei','activity_year'],how='left')
add('HMDA lender-year (LEI)','FFIEC panel RSSD','lei+year',m.respondent_rssd.notna().sum(),len(m),'LEI-years')
add('HMDA loans','FFIEC panel RSSD','lei+year',m.loc[m.respondent_rssd.notna(),'n_loans'].sum(),m.n_loans.sum(),'loan-weighted')
sod_rssd=set(br.RSSDID); 
mm=m[m.respondent_rssd.notna()]
add('HMDA lender-year w/ RSSD','SOD bank RSSDID (any year)','respondent_rssd',mm.respondent_rssd.isin(sod_rssd).sum(),len(mm),'depository banks only; nonbanks/CUs expected to miss')
add('HMDA loans','SOD bank RSSDID','respondent_rssd',m.loc[m.respondent_rssd.isin(sod_rssd),'n_loans'].sum(),m.n_loans.sum(),'loan-weighted')
add('HMDA loans','Call report top100 RSSDID','respondent_rssd',m.loc[m.respondent_rssd.isin(set(cr.RSSDID)),'n_loans'].sum(),m.n_loans.sum(),'loan-weighted')
add('Call report top100 banks','HMDA reporter (RSSD, 2018-23)','RSSDID',bank.RSSDID.isin(set(pk.respondent_rssd)).sum(),len(bank))
# 2 SOD branches -> call report
add('SOD branch CERTs (2008-25)','Call report top100 CERT','CERT',len(set(br.CERT)&set(cr.CERT)),br.CERT.nunique(),'distinct CERTs')
b24=br[br.YEAR==2025]
add('SOD branches 2025','Call report top100 CERT','CERT',b24.CERT.isin(set(cr.CERT)).sum(),len(b24),'branch rows')
add('SOD deposits 2025','Call report top100 CERT','CERT',b24.loc[b24.CERT.isin(set(cr.CERT)),'DEPSUMBR'].sum(),b24.DEPSUMBR.sum(),'deposit-weighted')
add('Call report top100 CERT','SOD branches (2025)','CERT',bank.CERT.isin(set(b24.CERT)).sum(),len(bank))
# RSSD agreement between sources for same CERT
x=bank.merge(br[br.YEAR==2025][['CERT','RSSDID']].drop_duplicates(),on='CERT',suffixes=('','_sod'))
add('Call report CERT->RSSDID','SOD CERT->RSSDID (2025)','CERT',(x.RSSDID==x.RSSDID_sod).sum(),len(x),'consistency check')
# 3 holdcos
crh=set(cr.RSSDHCR.dropna())-{0}
add('Call report RSSDHCR','SOD RSSDHCR','RSSDHCR',len(crh&set(br.RSSDHCR)),len(crh))
add('Call report RSSDHCR','BHCF 2017Q4 RSSD9001','RSSDHCR',len(crh&set(t.RSSDHCR)),len(crh),'BHCF covers only 2017Q4 locally')
h17=set(br[br.YEAR==2017].RSSDHCR)-{0}
add('SOD 2017 RSSDHCR','BHCF 2017Q4 RSSD9001','RSSDHCR',len(h17&set(t.RSSDHCR)),len(h17),'small HCs below Y-9C threshold expected to miss')
th=set(pk.topholder_rssd.dropna())-{-1,0}
add('HMDA topholder RSSD','SOD RSSDHCR','RSSD',len(th&set(br.RSSDHCR)),len(th))
# 4 CFPB company names -> banks
def norm(s):
    s=str(s).upper(); s=re.sub(r'[^A-Z0-9 ]',' ',s.replace('&',' AND '))
    s=re.sub(r'\b(NATIONAL ASSOCIATION|N A|NA|INC|INCORPORATED|CORP|CORPORATION|CO|COMPANY|LLC|LTD|THE|AND|HOLDINGS?|GROUP|FSB|USA|FINANCIAL|SERVICES)\b',' ',s)
    return re.sub(r'\s+',' ',s).strip()
names=[]
for df,nc,kc,lvl in [(bank,'NAME','CERT','bank'),(bank,'NAMEHCR','RSSDHCR','holdco'),(br.drop_duplicates('CERT'),'NAMEFULL','CERT','bank'),(br.drop_duplicates('RSSDHCR'),'NAMEHCR','RSSDHCR','holdco')]:
    z=df[[nc,kc]].dropna(); names.append(pd.DataFrame({'norm':z[nc].map(norm),'key':z[kc],'level':lvl,'top100':z[kc].isin(set(bank[kc]) if kc in bank else set())}))
nm=pd.concat(names); nm=nm[nm.norm.str.len()>=4]
# prefer top100 & bank-level when ambiguous
nm=nm.sort_values(['top100','level'],ascending=[False,True]).drop_duplicates('norm')
bp=pd.read_csv(f'{R}/cfpb_panel_company_month_bankproducts.csv.gz')
ct=bp.groupby('company').bank_product_complaints.sum().reset_index(); ct['norm']=ct.company.map(norm)
ct=ct.merge(nm,on='norm',how='left')
add('CFPB companies (bank products)','bank/holdco by normalized name','name',ct.key.notna().sum(),len(ct),'distinct companies')
add('CFPB bank-product complaints','bank/holdco by normalized name','name',ct.loc[ct.key.notna(),'bank_product_complaints'].sum(),ct.bank_product_complaints.sum(),'complaint-weighted')
add('CFPB bank-product complaints','top-100 call-report bank/holdco','name',ct.loc[ct.top100==True,'bank_product_complaints'].sum(),ct.bank_product_complaints.sum(),'complaint-weighted')
cmap=ct[ct.key.notna()][['company','norm','key','level','top100']]
save('company_entity_map',cmap,'CFPB company -> CERT or RSSDHCR (name rule)',['company'])
# 5 geography: no county FIPS / UNINUMBR in local SOD extract
add('SOD branches','county FIPS','STCNTYBR',0,len(b24),'column absent in Drive extract (only state + lat/lon)')
add('SOD branches with lat/lon','coordinates present','lat,lon',b24.lat.notna().sum(),len(b24))
add('HMDA state codes','SOD states','state',len(set(hm.state_code)&set(br.STALPBR)),hm.state_code.nunique())
cv=pd.DataFrame(cov); cv.to_csv('reports/join_coverage.csv',index=False); print(cv.to_string())
json.dump(inv,open('reports/inventory.json','w'),indent=1,default=str)
con=duckdb.connect(f'{D}/bankgraph.duckdb')
for n in inv: con.execute(f"create or replace table {n} as select * from read_parquet('{D}/{n}.parquet')")
con.close()
