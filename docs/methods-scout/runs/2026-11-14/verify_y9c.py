import pandas as pd, zipfile, io, numpy as np
y=pd.read_csv('q3/y9c_payouts.csv')
items=['BHCK4460','BHCK4598','BHCK4783','BHCK4782','BHCK4340','BHCKA223','BHCAA223','BHCWA223']
mx={}
for yr in range(2013,2026):
    z=zipfile.ZipFile(f'y9c/BHCF{yr}1231.zip'); n=z.namelist()[0]
    raw=z.read(n).decode('latin1')
    df=pd.read_csv(io.StringIO(raw),sep='^',low_memory=False,quoting=3,skiprows=[1] if raw.splitlines()[1].startswith('--') else None)
    df.columns=[c.strip().upper() for c in df.columns]
    df=df[['RSSD9001']+[c for c in items if c in df.columns]].copy()
    for c in df.columns[1:]: df[c]=pd.to_numeric(df[c],errors='coerce')
    df['RSSD9001']=pd.to_numeric(df.RSSD9001,errors='coerce')
    s=y[y.year==yr].merge(df,on='RSSD9001',suffixes=('','_z'))
    for c in ['BHCK4460','BHCK4598','BHCK4783','BHCK4782','BHCK4340']:
        d=(s[c].fillna(0)-s[c+'_z'].fillna(0)).abs().max(); mx[c]=max(mx.get(c,0),d)
    print(yr,len(y[y.year==yr]),'matched',len(s))
print('max abs diff by item',mx)
