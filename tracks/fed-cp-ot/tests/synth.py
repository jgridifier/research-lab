from pathlib import Path
from xml.sax.saxutils import quoteattr
import zipfile
from fed_cp_ot.parse import EXPECTED_VOL_SERIES

DATES = ('2004-04-05','2004-04-06','2004-04-07','2004-04-08','2004-04-09',
         '2004-12-20','2004-12-21','2004-12-22','2004-12-23','2004-12-24',
         '2008-12-22','2008-12-23','2008-12-24','2008-12-25','2008-12-26','2009-01-02')

def make_zip(path, mutate=None, gaps=False):
    chunks = ['<message:Message xmlns:message="urn:message" xmlns:frb="urn:frb"><message:Header><message:Prepared>2026-10-05</message:Prepared></message:Header>']
    for dataset in ('RATES','VOL','OUTST','OUTST_YREND','OUTST_OLD','RATES_OLD'):
        chunks.append(f'<frb:DataSet id="{dataset}" xmlns:kf="urn:{dataset}">')
        series = EXPECTED_VOL_SERIES if dataset == 'VOL' else {'RATE1':('AAA','1','D'),'RATE2':('FAA','5','D')}
        for sid,(typ,mat,vt) in series.items():
            attrs = dict(SERIES_NAME=sid,CP_TYPE=typ,CP_MAT_RANGE=mat,CP_VOL_TYPE=vt,FREQ='9',UNIT_MULT='1000000' if vt=='D' else '1')
            observations=[]
            for date in DATES:
                missing = date == '2008-12-25' or (gaps and ((typ=='NA2' and date in ('2004-04-09','2004-12-24')) or (typ=='NAA' and date=='2004-12-24')))
                obs=dict(TIME_PERIOD=date,OBS_STATUS='ND' if missing else 'A',OBS_VALUE='-9999' if missing else ('99999' if date>'2008-12-26' else str(int(mat)*10+20)))
                observations.append(obs)
            if dataset=='VOL' and mutate: mutate(attrs,observations)
            if attrs.get('skip'): continue
            chunks.append('<kf:Series '+' '.join(k+'='+quoteattr(v) for k,v in attrs.items())+'>')
            for obs in observations: chunks.append('<frb:Obs '+' '.join(k+'='+quoteattr(v) for k,v in obs.items())+'/>')
            chunks.append('</kf:Series>')
        chunks.append('</frb:DataSet>')
    chunks.append('</message:Message>')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z: z.writestr('CP_data.xml',''.join(chunks))
    return Path(path)
