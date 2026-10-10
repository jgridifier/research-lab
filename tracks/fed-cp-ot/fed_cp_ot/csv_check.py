"""CSV is a validation source only; filter dates before converting amounts."""
import csv
from collections import defaultdict, Counter
import numpy as np
import pandas as pd
from .parse import MAT_MAP
from .paths import SCORING_WALL
from .weekly import check_wall
from .errors import ValidationError

def cross_check_csv(csv_path, vol_long, wall=SCORING_WALL, provenance=None):
    check_wall(wall, provenance)
    cutoff = pd.Timestamp(wall).strftime('%Y-%m-%d') if wall else '9999-12-31'
    values = defaultdict(list)
    with open(csv_path, newline='') as f:
        for row in csv.DictReader(f):
            if not ('2001-01-01' <= row['date'] <= cutoff): continue
            key = (row['date'], MAT_MAP[row['maturity_range_days']], row['issuer_category'])
            values[key].append(float(row['amount_usd_mm']))
    xml = vol_long[(vol_long.date <= cutoff) & vol_long.valid & (vol_long.vt == 'D')]
    lookup = {(r.date.strftime('%Y-%m-%d'),r.mat,r.cp_type):r.value for r in xml.itertuples()}
    result = {}
    for cat, typ in [('AB','AAA'),('FIN','FAA'),('MKT','M')]:
        keys = {(d,m) for d,m,c in values if c == cat} | {(d,m) for d,m,t in lookup if t == typ}
        ok = [values.get((d,m,cat)) == [lookup.get((d,m,typ))] for d,m in keys]
        result[cat] = float(np.mean(ok)) if ok else 0.0
    keys = {(d,m) for d,m,c in values if c == 'NONFIN'} | {(d,m) for d,m,t in lookup if t in ('NAA','NA2')}
    ok = [sorted(values.get((d,m,'NONFIN'),[])) == sorted([lookup.get((d,m,'NAA'),np.nan),lookup.get((d,m,'NA2'),np.nan)]) for d,m in keys]
    result['NONFIN_pair_fraction'] = float(np.mean(ok)) if ok else 0.0
    result['NONFIN_rows_per_key'] = dict(Counter(len(values.get((d,m,'NONFIN'),[])) for d,m in keys))
    result['passed'] = all(result[c] == 1.0 for c in ('AB','FIN','MKT')) and result['NONFIN_pair_fraction'] >= .999
    if not result['passed']: raise ValidationError('CSV cross-check failed: ' + str(result))
    return result
