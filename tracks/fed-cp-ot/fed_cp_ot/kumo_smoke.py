"""Exactly one NIM request on a burn-in target; no retries, scoring, or trial log."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import pandas as pd
from . import kumo
from .errors import ScoringWallError
from .paths import BURNIN
from .preflight import preflight, sha256
from .parse import parse_vol
from .weekly import build_weekly


def burnin_origin(target):
    target = pd.Timestamp(target)
    if (pd.isna(target) or target.tzinfo is not None or
            target != target.normalize() or target.dayofweek != 4 or
            not pd.Timestamp(BURNIN[0]) + pd.Timedelta(weeks=1) <= target <= pd.Timestamp(BURNIN[1])):
        raise ScoringWallError('Smoke target must be a Friday strictly within burn-in, never OOS')
    return target - pd.Timedelta(weeks=1)


def run(zip_path, output, target='2008-12-26', transport=None):
    origin = burnin_origin(target)  # reject before any file, key, or network access
    provenance = preflight('burnin')
    vol, _ = parse_vol(zip_path, provenance, wall=str(origin.date()))
    frame = build_weekly(vol, through=origin, provenance=provenance)
    if frame.empty or frame.week.max() > origin:
        raise ScoringWallError('Smoke input extends beyond its burn-in origin')
    payload = kumo.build_payload(frame, origin, 'best')
    if len(payload['predict']['instance_table']['rows']) != 24:
        raise ValueError('Smoke requires all 24 prediction instances')
    key = kumo.api_key()
    evidence = {'purpose': 'Live regression schema smoke only; not a trial or replication',
                'started_utc': datetime.now(timezone.utc).isoformat(),
                'origin': str(origin.date()), 'target': str(pd.Timestamp(target).date()),
                'input_max_date': str(frame.week.max().date()), 'zip_sha256': sha256(zip_path),
                'endpoint': kumo.URL, 'request_count': 1, 'retries': 0,
                'timeout_s': kumo.TIMEOUT_S, 'status': None, 'response': None,
                'parser_verified': False,
                'request_sha256': kumo.payload_sha256(payload), 'request': payload}
    # Exclusive creation prevents accidentally repeating the smoke at this evidence path.
    with Path(output).open('x') as f:
        try:
            status, _, body = (transport or kumo.urllib_transport)(
                kumo.URL, kumo.payload_bytes(payload),
                {'Accept': 'application/json', 'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + key}, kumo.TIMEOUT_S)
            evidence['status'] = status
            # Persist no headers or credentials, even if a server echoes the bearer key.
            body = body.replace(key, '[REDACTED]')
            try: evidence['response'] = json.loads(body)
            except ValueError: evidence['response'] = body
            evidence['parser_verified'] = False
            if status == 200:
                values = kumo.KumoClient._parse(body)
                evidence.update(parser_verified=True, finite_prediction_count=len(values))
        except OSError as exc:
            evidence['error'] = type(exc).__name__  # never persist exception text/credentials
        finally:
            f.write(json.dumps(evidence, sort_keys=True, indent=1, allow_nan=False) + '\n')
    if not evidence.get('parser_verified'):
        raise kumo.KumoFailure('Live smoke did not verify regression schema; see evidence (no retry)')
    return evidence


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--zip', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--target', default='2008-12-26')
    args = ap.parse_args()
    result = run(args.zip, args.out, args.target)
    print(json.dumps({k: result[k] for k in ('status', 'origin', 'target', 'parser_verified')}))


if __name__ == '__main__':
    main()
