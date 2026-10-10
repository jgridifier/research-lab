"""Streaming SDMX reader: values beyond the wall never reach float()."""
import re
import xml.etree.ElementTree as ET
import zipfile
import numpy as np
import pandas as pd
from .paths import SCORING_WALL
from .preflight import validate_provenance
from .errors import ValidationError, ScoringWallError

MAT_MAP = dict(zip(('1_4','5_9','10_20','21_40','41_80','GT80'), ('1','5','10','21','41','81')))
GROUPS = (('AB','AA','AAA'), ('FIN','AA','FAA'), ('NONFIN','AA','NAA'),
          ('NONFIN','A2P2','NA2'), ('MKT','MKT','M'))
EXPECTED_VOL_SERIES = {f'{g}.{b}.{tier}.{measure}': (typ, mat, vt)
    for g,tier,typ in GROUPS for b,mat in MAT_MAP.items() for measure,vt in [('AMT','D'),('VOL','N')]}
OBS_STATUSES = frozenset({'A', 'ND'})
INTEGER_TEXT = re.compile(r'[0-9]+')
KNOWN_GAPS = {'NA2': ['2004-04-09','2004-12-24'], 'NAA': ['2004-12-24']}

def parse_vol(zip_path, provenance, wall=SCORING_WALL):
    validate_provenance(provenance)
    if wall is None or pd.Timestamp(wall) > pd.Timestamp(SCORING_WALL):
        validate_provenance(provenance, require_oos=True)
    cutoff = None if wall is None else pd.Timestamp(wall).strftime('%Y-%m-%d')
    rows, seen, rates = [], {}, set()
    dataset = series = None
    with zipfile.ZipFile(zip_path) as z, z.open('CP_data.xml') as stream:
        for event, elem in ET.iterparse(stream, events=('start','end')):
            tag = elem.tag.rsplit('}',1)[-1]
            if event == 'start':
                if tag == 'DataSet': dataset = elem.get('id')
                elif tag == 'Series':
                    series = elem.get('SERIES_NAME')
                    if dataset == 'RATES': rates.add(series)
                    if dataset == 'VOL':
                        attrs = tuple(elem.get(k) for k in ('CP_TYPE','CP_MAT_RANGE','CP_VOL_TYPE'))
                        if series in seen or EXPECTED_VOL_SERIES.get(series) != attrs:
                            raise ValidationError('Unexpected series or changed attributes: ' + str(series))
                        seen[series] = attrs
                continue
            if tag == 'Obs' and dataset == 'VOL':
                date = elem.get('TIME_PERIOD')
                if date >= '2001-01-01':
                    raw = elem.get('OBS_VALUE')
                    status = elem.get('OBS_STATUS')
                    if status not in OBS_STATUSES:
                        raise ValidationError(f'Unexpected OBS_STATUS {status!r} in {series} on {date}')
                    valid = status != 'ND' and raw != '-9999'
                    value = np.nan
                    if valid and pd.Timestamp(date).dayofweek >= 5:
                        raise ValidationError(f'Valid weekend observation in {series} on {date}')
                    if valid:
                        # DATA_SPEC rule 3 on every date, checked AS TEXT so post-wall amounts are never converted
                        if raw is None or '-' in raw:
                            raise ValidationError(f'Negative or missing value in {series} on {date}')
                        if not INTEGER_TEXT.fullmatch(raw):
                            raise ValidationError(f'Non-integer value in {series} on {date}')
                    if valid and (cutoff is None or date <= cutoff):
                        try: value = float(raw)
                        except (TypeError, ValueError) as exc: raise ValidationError('Invalid numeric observation') from exc
                        if not np.isfinite(value) or value < 0 or value % 1:
                            raise ValidationError('Negative, nonfinite or non-integer observation')
                    rows.append((series, *seen[series], date, valid, value))
            elem.clear()
    if set(seen) != set(EXPECTED_VOL_SERIES) or set(seen.values()) != set(EXPECTED_VOL_SERIES.values()):
        raise ValidationError('Missing series or changed attribute combinations')
    frame = pd.DataFrame(rows, columns=['series','cp_type','mat','vt','date','valid','value'])
    frame['date'] = pd.to_datetime(frame.date)
    if frame.duplicated(['series','date']).any(): raise ValidationError('Duplicate series/date')
    days = frame.groupby(['cp_type','date']).valid.agg(['sum','count'])
    if ((days['sum'] != 0) & ((days['sum'] != 12) | (days['count'] != 12))).any():
        raise ValidationError('Partial type-day')
    valid_dates = set(frame.loc[frame.valid,'date'])
    missing, known, anomalies = {}, {}, {}
    for typ in sorted({a[0] for a in seen.values()}):
        have = set(frame.loc[(frame.cp_type == typ) & frame.valid,'date'])
        gaps = sorted(d.strftime('%Y-%m-%d') for d in valid_dates-have)
        missing[typ] = gaps
        known[typ] = sorted(set(gaps) & set(KNOWN_GAPS.get(typ,[])))
        anomalies[typ] = sorted(set(gaps) - set(KNOWN_GAPS.get(typ,[])))
    report = {'series_count': len(seen), 'rows': len(frame), 'valid_rows': int(frame.valid.sum()),
              'rates_series_ids': sorted(rates), 'missing_dates_per_type': missing,
              'known_gaps': known, 'anomalies': anomalies,
              'post_wall_values_withheld': cutoff is not None,
              'post_wall_rows': int((frame.date > SCORING_WALL).sum())}
    return frame, report

def load_vol(provenance, zip_path=None):
    validate_provenance(provenance)
    if zip_path is None:
        from .ingest import latest_vintage
        zip_path = latest_vintage()
    return parse_vol(zip_path, provenance, wall=None if provenance.oos_approved else SCORING_WALL)


def vintage_through(vol_long):
    """Last date with any valid VOL observation in a parsed vintage (structural; uses no amounts)."""
    return pd.Timestamp(vol_long.loc[vol_long.valid, 'date'].max()).date()
