"""KumoRFM via NVIDIA NIM as a pre-registered rival row (PREREG v2 9, T6). Family K only; never a SEL candidate.

The request layout follows the instance-scoped 'arrays' format used by the research-box client (/workspace/kumo-nim,
see docs/learn/kumo_rfm_nim.html), changed to a regression task. Related `entities` rows are instance-scoped and must
declare `instance_id` (live NIM 422 otherwise). Response shape `{predictions:[{row_index, prediction}, ...]}` was
confirmed against the live NVIDIA endpoint on burn-in targets only (see artifacts/ and tests/test_v2_kumo_live_schema.py).
"""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
from .weekly import TYPES

URL = 'https://ai.api.nvidia.com/v1/structured-data/nvidia/kumo-relational/predictions'
NIM_IMAGE = 'nvcr.io/nim/nvidia/kumo-relational:1.1.0'
MODES = ('best', 'fast')   # best is primary; fast is descriptive only
CONTEXT_WEEKS = 156        # usable weeks per entity
MAX_RETRIES = 3
BACKOFF_S = 30
MAX_FAIL_FRACTION = 0.05
TIMEOUT_S = 300
MAX_CONTEXT_ROWS = 10000
RETRY_STATUS = frozenset({429, 500, 501, 502, 503, 504})

class KumoFailure(RuntimeError):
    pass

class KumoKeyMissing(KumoFailure):
    pass

def api_key():
    """The key comes from NVIDIA_API_KEY only; it is never logged or written anywhere."""
    key = os.environ.get('NVIDIA_API_KEY')
    if not key: raise KumoKeyMissing('NVIDIA_API_KEY is not set')
    return key

def entities():
    return [(t, b) for t in TYPES for b in range(6)]

def _ts(week): return pd.Timestamp(week).strftime('%Y-%m-%dT%H:%M:%S.000000Z')

def build_payload(weekly_o, origin, mode='best'):
    """Graph from H_o only. Per entity (type, bucket): the last CONTEXT_WEEKS usable weeks become anchors. Each anchor but
    the newest is a labelled context instance (target = the share in the next usable week); the newest week is not
    labelled and an unlabelled predict instance anchored at the origin carries its facts. Each instance carries only its
    own week's facts (share, log total amount, log issue count, valid days): 24 x 156 = 3,744 fact rows. Entity attribute
    rows are instance-scoped and include `instance_id` (required by the live NIM schema)."""
    if mode not in MODES: raise ValueError('Unknown Kumo mode')
    origin = pd.Timestamp(origin)
    if weekly_o.week.max() > origin: raise ValueError('Weekly frame extends past the origin')
    ctx_i, pre_i, ctx_f, pre_f, ents = [], [], [], [], []
    iid = node = 0
    for ent, (typ, b) in enumerate(entities()):
        ents.append([ent, typ, b])
        h = weekly_o[(weekly_o.cp_type == typ) & weekly_o.usable].sort_values('week').tail(CONTEXT_WEEKS)
        rows = list(h.itertuples())
        def fact(r): return [float(r.mix[b]), float(np.log(r.D.sum())), float(np.log(r.N.sum())), int(r.valid_days)]
        for r, nxt in zip(rows[:-1], rows[1:]):
            ctx_i.append([iid, ent, _ts(r.week), float(nxt.mix[b])])
            ctx_f.append([iid, node, ent, _ts(r.week), *fact(r)]); iid += 1; node += 1
        if rows:
            pre_i.append([iid, ent, _ts(origin)])
            pre_f.append([iid, node, ent, _ts(rows[-1].week), *fact(rows[-1])]); iid += 1; node += 1
    if len(ctx_f) + len(pre_f) > MAX_CONTEXT_ROWS: raise ValueError('Context exceeds the 10k-row cap')
    fcols = ['instance_id', '__node_id', 'entity_id', 'week', 'share', 'log_total_amount', 'log_issue_count', 'valid_days']
    ecols = ['instance_id', 'entity_id', 'cp_type', 'bucket']
    ent_by_id = {e[0]: e for e in ents}
    def entity_rows(inst):
        # One attribute row per instance; live NIM requires declared instance_id on entities.
        return [[iid, eref, ent_by_id[eref][1], ent_by_id[eref][2]] for iid, eref, *_ in inst]
    def pack(inst, facts, labelled):
        return {'instance_table': {'format': 'arrays', 'rows': inst,
                    'columns': ['instance_id', '__kumo_entity_ref_0', '__kumo_anchor_time'] + (['TARGET'] if labelled else [])},
                'related_tables': {'entities': {'format': 'arrays', 'columns': ecols, 'rows': entity_rows(inst)},
                                   'weekly_facts': {'format': 'arrays', 'columns': fcols, 'rows': facts}}}
    schema = {'instance_table': {'columns': {
                  'instance_id': {'dtype': 'int64', 'stype': 'ID', 'nullable': False},
                  '__kumo_entity_ref_0': {'dtype': 'int64', 'stype': 'ID'},
                  '__kumo_anchor_time': {'dtype': 'timestamp[us]', 'stype': 'timestamp', 'nullable': False},
                  'TARGET': {'dtype': 'float64', 'stype': 'numerical'}}, 'primary_key': 'instance_id'},
              'related_tables': {
                  'entities': {'columns': {'instance_id': {'dtype': 'int64', 'stype': 'ID', 'nullable': False},
                                           'entity_id': {'dtype': 'int64', 'stype': 'ID', 'nullable': False},
                                           'cp_type': {'dtype': 'string', 'stype': 'categorical'},
                                           'bucket': {'dtype': 'int64', 'stype': 'categorical'}},
                               'primary_key': ['instance_id', 'entity_id']},
                  'weekly_facts': {'columns': {'instance_id': {'dtype': 'int64', 'stype': 'ID', 'nullable': False},
                                               '__node_id': {'dtype': 'int64', 'stype': 'ID', 'nullable': False},
                                               'entity_id': {'dtype': 'int64', 'stype': 'ID', 'nullable': False},
                                               'week': {'dtype': 'timestamp[us]', 'stype': 'timestamp'},
                                               'share': {'dtype': 'float64', 'stype': 'numerical'},
                                               'log_total_amount': {'dtype': 'float64', 'stype': 'numerical'},
                                               'log_issue_count': {'dtype': 'float64', 'stype': 'numerical'},
                                               'valid_days': {'dtype': 'int64', 'stype': 'numerical'}},
                                   'primary_key': ['instance_id', '__node_id']}},
              'relationships': [
                  {'source_columns': ['__kumo_entity_ref_0'], 'target_table': 'entities', 'target_columns': ['entity_id']},
                  {'source_table': 'weekly_facts', 'source_columns': ['entity_id'], 'target_table': 'entities', 'target_columns': ['entity_id']}]}
    return {'model': 'kumo-relational',
            'task': {'kind': 'regression', 'target': {'column_name': 'TARGET', 'dtype': 'float64'},
                     'entity_table_names': ['entities'], 'anchor_time_column': '__kumo_anchor_time'},
            'schema': schema, 'context': pack(ctx_i, ctx_f, True), 'predict': pack(pre_i, pre_f, False),
            'output': {'fields': ['prediction']}, 'inference': {'run_mode': mode}}

def payload_bytes(payload): return json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def payload_sha256(payload): return hashlib.sha256(payload_bytes(payload)).hexdigest()

def urllib_transport(url, body, headers, timeout):
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status, dict(r.headers), r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode(errors='replace')

class KumoClient:
    """transport(url, body, headers, timeout) -> (status, headers, text); network failures raise OSError. Injectable for tests."""
    def __init__(self, log_path, transport=urllib_transport, sleep=time.sleep, key=None):
        self.log_path, self.transport, self.sleep = Path(log_path), transport, sleep
        self._key = key or api_key()
    def _log(self, row):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open('a') as f: f.write(json.dumps(row, sort_keys=True) + '\n')
    def predict(self, payload, origin, mode):
        """One call, with up to MAX_RETRIES retries (same payload) on HTTP 429/5xx or network error. Returns the 24 predictions
        in predict-instance order. Raises KumoFailure when retries run out or the response is not usable."""
        body, sha = payload_bytes(payload), payload_sha256(payload)
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self._key}
        for attempt in range(MAX_RETRIES + 1):
            t0, status, rh, text, err = time.monotonic(), None, {}, '', None
            try: status, rh, text = self.transport(URL, body, headers, TIMEOUT_S)
            except OSError as exc: err = type(exc).__name__
            self._log({'origin': str(pd.Timestamp(origin).date()), 'mode': mode, 'attempt': attempt, 'status': status, 'error': err,
                       'latency_s': round(time.monotonic() - t0, 3), 'payload_sha256': sha, 'endpoint': URL,
                       'model_headers': {k: v for k, v in rh.items() if 'model' in k.lower() or 'version' in k.lower()}})
            if status == 200: return self._parse(text)
            if status is not None and status not in RETRY_STATUS: raise KumoFailure(f'HTTP {status}')
            if attempt < MAX_RETRIES: self.sleep(BACKOFF_S)
        raise KumoFailure('retries exhausted')
    @staticmethod
    def _parse(text, n=None):
        """Parse a live/mock NIM regression body. `n` defaults to len(entities()) (=24 in production)."""
        n = len(entities()) if n is None else int(n)
        try:
            preds = sorted(json.loads(text)['predictions'], key=lambda x: x['row_index'])
            values = np.array([float(p['prediction']) for p in preds])
        except (KeyError, TypeError, ValueError) as exc: raise KumoFailure('Unparseable response') from exc
        if values.shape != (n,) or not np.isfinite(values).all():
            raise KumoFailure(f'Expected {n} finite predictions')
        return values

def to_mixes(values, persistence):
    """max(s, 0) renormalised per type. A type whose six shares are all <= 0 gets P and flags the origin as a failure.
    Returns ({type: mix}, failed)."""
    out, failed = {}, False
    for i, typ in enumerate(TYPES):
        s = np.maximum(np.asarray(values[6 * i:6 * i + 6], float), 0.0)
        if s.sum() <= 0: out[typ], failed = np.asarray(persistence[typ], float), True
        else: out[typ] = s / s.sum()
    return out, failed

def kumo_forecast(client, weekly_o, origin, mode, persistence):
    """({type: mix} or None, failed). None means no forecast at this origin (the origin drops out of Family K pairs only)."""
    try: values = client.predict(build_payload(weekly_o, origin, mode), origin, mode)
    except KumoFailure: return None, True
    return to_mixes(values, persistence)

def family_k_incomplete(n_failed, n_origins):
    return n_origins == 0 or n_failed / n_origins > MAX_FAIL_FRACTION
