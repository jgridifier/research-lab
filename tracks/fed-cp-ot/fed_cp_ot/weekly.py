import numpy as np
import pandas as pd
from .paths import SCORING_WALL
from .preflight import validate_provenance
from .errors import ScoringWallError, ValidationError
MATS = ['1','5','10','21','41','81']
TYPES = ('AAA','FAA','NAA','NA2')

def check_wall(through, provenance=None):
    if through is None or pd.Timestamp(through) > pd.Timestamp(SCORING_WALL):
        try: validate_provenance(provenance, require_oos=True)
        except ValueError as exc: raise ScoringWallError('Beyond scoring wall') from exc

def build_weekly(vol_long, types=TYPES, through=SCORING_WALL, provenance=None):
    check_wall(through, provenance)
    through = vol_long.date.max() if through is None else pd.Timestamp(through)
    df = vol_long.loc[(vol_long.date <= pd.Timestamp(through)) & vol_long.cp_type.isin(types)].copy()
    if (df.valid & (df.date.dt.dayofweek >= 5)).any(): raise ValidationError('Valid weekend observation')
    df = df[df.date.dt.dayofweek < 5]  # only ND weekend rows remain to drop
    df['week'] = df.date.dt.to_period('W-FRI').dt.end_time.dt.normalize()
    df = df[df.week <= pd.Timestamp(through)]
    records = []
    if df.empty: return pd.DataFrame(columns=['cp_type','week','valid_days','D','N','usable','mix'])
    weeks = pd.date_range(df.week.min(), df.week.max(), freq='W-FRI')
    for typ in types:
        for week in weeks:
            g = df[(df.cp_type == typ) & (df.week == week) & df.valid]
            if g.value.isna().any(): raise ValidationError('Required values withheld or missing')
            days = g.date.nunique()
            D,N = [g[g.vt == vt].groupby('mat').value.sum().reindex(MATS, fill_value=0).to_numpy() for vt in ('D','N')]
            usable = bool(days >= 3 and N.sum() >= 100 and D.sum() > 0)
            records.append((typ, week, days, D, N, usable, D/D.sum() if usable else np.full(6,np.nan)))
    return pd.DataFrame(records, columns=['cp_type','week','valid_days','D','N','usable','mix'])

def mkt_weekly_total(vol_long, through=SCORING_WALL, provenance=None):
    w = build_weekly(vol_long, types=('M',), through=through, provenance=provenance)
    return pd.Series([d.sum() for d in w.D], index=w.week, name='MKT_amount_usd_mm')

def provisional_partial_week(vol_long, asof, provenance=None):
    check_wall(asof, provenance)
    asof = pd.Timestamp(asof)
    monday = asof.normalize() - pd.Timedelta(days=asof.dayofweek)
    data = vol_long[(vol_long.date >= monday) & (vol_long.date <= asof)].copy()
    # Aggregate the partial observations using a completed historical Friday label.
    friday = monday + pd.Timedelta(days=4)
    check_wall(friday, provenance)
    result = build_weekly(data, through=friday, provenance=provenance)
    result['provisional'] = True
    return result
