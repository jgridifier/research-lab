"""Forecast interfaces and an append-only, hash-chained forward record."""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Protocol
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .paths import FORWARD_LOG_PATH
from .weekly import check_wall
from .metric import q_from_p, w2sq, X_LOG
from .fedcal import data_available_at as _fed_available_at, last_fed_business_day_of_week

class Forecaster(Protocol):
    def fit_predict(self, history, origin): ...

class Persistence:
    def fit_predict(self, history, origin):
        history = origin_view(history, origin)
        usable = history[history.usable].sort_values('week')
        if usable.empty: raise ValueError('No usable history')
        if usable.cp_type.nunique() != 1: raise ValueError('Forecast one type at a time')
        return usable.iloc[-1]['mix'].copy()

def origin_view(weekly, origin):
    result = weekly[weekly.week <= pd.Timestamp(origin)].copy(deep=True)
    # pandas deep copy does not copy arrays in object columns.
    for column in ('D','N','mix'):
        if column in result: result[column] = result[column].map(lambda a: np.array(a,copy=True))
    assert (result.week <= pd.Timestamp(origin)).all()
    return result

def walk_forward(weekly, forecaster, origins):
    rows = []
    for origin in origins:
        origin = pd.Timestamp(origin)
        if origin.dayofweek != 4: raise ValueError('Origin must be a Friday')
        target = origin + pd.Timedelta(days=7)
        assert target.dayofweek == 4 and target > origin
        rows.append({'origin':origin,'target':target,'mix':forecaster.fit_predict(origin_view(weekly,origin),origin)})
    return rows

def data_available_at(friday):
    """A completed W-FRI week is available at 13:00 ET on the next Fed business day after its Friday."""
    if pd.Timestamp(friday).dayofweek != 4: raise ValueError('Expected Friday')
    return _fed_available_at(friday)

def _aware(value):
    if isinstance(value,str) and not value[:4].isdigit():
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(value)  # HTTP Last-Modified, e.g. 'Fri, 09 Oct 2026 17:00:03 GMT'
    result = datetime.fromisoformat(value) if isinstance(value,str) else value
    if result.tzinfo is None or result.utcoffset() is None: raise ValueError('Timezone-aware timestamp required')
    return result

def _mix(value):
    a = np.asarray(value,dtype=float)
    if a.shape != (6,) or not np.isfinite(a).all() or (a < 0).any() or not np.isclose(a.sum(),1):
        raise ValueError('Expected six probability shares')
    return a.tolist()

def _hash(record):
    return hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def _vintage(vintage_sha256, vintage_through, friday, what):
    """Every row names its input vintage; the vintage must contain the week's last Fed business day."""
    if not isinstance(vintage_sha256, str) or len(vintage_sha256) != 64 or any(c not in '0123456789abcdef' for c in vintage_sha256):
        raise ValueError('vintage_sha256 must be a lowercase sha256 hex digest')
    if vintage_through is None: raise ValueError('vintage_through is required')
    need = last_fed_business_day_of_week(friday)
    if need is not None and pd.Timestamp(vintage_through).date() < need:
        raise ValueError(f'Vintage ends {pd.Timestamp(vintage_through).date()} before the {what} week\'s last Fed business day {need}')
    return dict(vintage_sha256=vintage_sha256, vintage_through=str(pd.Timestamp(vintage_through).date()))

class ForwardLog:
    def __init__(self, path=FORWARD_LOG_PATH, live=True):
        """live=True (default; the app's log): every forecast must carry the vintage fetch timestamp and the
        release's Last-Modified time, and may not be stamped before either. live=False is for burn-in replays."""
        self.path = Path(path); self.live = live
    def _rows(self):
        return [json.loads(s) for s in self.path.read_text().splitlines()] if self.path.exists() else []
    def verify(self):
        previous = '0'*64
        for row in self._rows():
            claimed = row.pop('hash')
            if row['prev_hash'] != previous or _hash(row) != claimed: raise ValueError('Forward log chain tampered')
            previous = claimed
        return True
    def _append(self, row):
        self.verify()
        rows = self._rows()
        row['prev_hash'] = rows[-1]['hash'] if rows else '0'*64
        row['hash'] = _hash(row)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open('a') as f: f.write(json.dumps(row,sort_keys=True)+'\n')
        return row
    def record_forecast(self, origin, target, cp_type, mix, model, issued_at, input_max_date,
                        fetched_at=None, release_last_modified=None, *, vintage_sha256, vintage_through):
        self.verify()
        origin,target = pd.Timestamp(origin),pd.Timestamp(target)
        issued_at = _aware(issued_at)
        stamps = {}
        if self.live:
            if fetched_at is None or release_last_modified is None:
                raise ValueError('Live forecasts need the vintage fetch time and the release Last-Modified time')
            fetched_at, release_last_modified = _aware(fetched_at), _aware(release_last_modified)
            if issued_at < fetched_at or issued_at < release_last_modified:
                raise ValueError('Forecast stamped before the data fetch or the release update')
            stamps = dict(fetched_at=fetched_at.isoformat(), release_last_modified=release_last_modified.isoformat())
        if origin.dayofweek != 4 or target != origin + pd.Timedelta(days=7):
            raise ValueError('Expected Friday origin and target exactly seven days later')
        if (pd.Timestamp(input_max_date) > origin or issued_at < data_available_at(origin)
                or issued_at >= data_available_at(target)):
            raise ValueError('Invalid forecast timing')
        vintage = _vintage(vintage_sha256, vintage_through, origin, 'origin')
        key = (str(target.date()),cp_type)
        if any((r['target'],r['cp_type']) == key and
               (r['kind'] == 'outcome' or r.get('model') == model) for r in self._rows()):
            raise ValueError('Forecast key already recorded; records cannot be edited')
        return self._append(dict(kind='forecast',origin=str(origin.date()),target=key[0],cp_type=cp_type,
            mix=_mix(mix),model=model,issued_at=issued_at.isoformat(),input_max_date=str(pd.Timestamp(input_max_date).date()),**stamps,**vintage))
    def record_outcome(self, target, cp_type, mix, recorded_at, provenance=None, *, vintage_sha256, vintage_through):
        check_wall(target, provenance)
        vintage = _vintage(vintage_sha256, vintage_through, target, 'target')
        self.verify()
        target = str(pd.Timestamp(target).date()); recorded_at = _aware(recorded_at)
        rows = [r for r in self._rows() if (r['target'],r['cp_type']) == (target,cp_type)]
        if not rows or any(r['kind'] == 'outcome' for r in rows): raise ValueError('Need forecasts without an outcome')
        if recorded_at < data_available_at(target) or any(_aware(r['issued_at']) >= recorded_at for r in rows):
            raise ValueError('Invalid outcome timing')
        return self._append(dict(kind='outcome',target=target,cp_type=cp_type,mix=_mix(mix),recorded_at=recorded_at.isoformat(),**vintage))
    def score(self, target, cp_type, model, provenance=None):
        check_wall(target, provenance)
        self.verify()
        target = str(pd.Timestamp(target).date())
        rows = {r['kind']:r for r in self._rows() if (r['target'],r['cp_type']) == (target,cp_type)
                and (r['kind'] == 'outcome' or r.get('model') == model)}
        return w2sq(q_from_p(rows['forecast']['mix'],X_LOG),q_from_p(rows['outcome']['mix'],X_LOG))


def vintage_stamps(manifest_record):
    """(fetched_at, release_last_modified) from an ingest manifest row, for live record_forecast calls."""
    if not manifest_record.get('last_modified') or not manifest_record.get('fetched_at_utc'):
        raise ValueError('Manifest row lacks fetch time or Last-Modified (local seeds cannot back live forecasts)')
    return manifest_record['fetched_at_utc'], manifest_record['last_modified']
