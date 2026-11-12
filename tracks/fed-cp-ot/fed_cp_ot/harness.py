"""OOS harness (PREREG v2 12; HARNESS_TICKET_v2). `run-oos` is gated by preflight('oos') + check_oos_approval() and aborts
before any post-wall amount is parsed. `dry-run-burnin` runs the same pipeline on burn-in targets only (<= 2008-12-26)."""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from . import preflight as pf
from .paths import DATA_DIR, SCORING_WALL, OOS, SEED, TRIALS_PATH
from .preflight import preflight, check_oos_approval, sha256
from .errors import OOSNotAuthorized, RunOnceError, ScoringWallError
from .parse import load_vol
from .weekly import build_weekly, TYPES
from .metric import q_from_p, w2sq, X_LOG
from .candidates import ENTRIES, forecast_all, floored_fraction
from .schedule import build_schedules, write_schedules
from .scoring import weekly_loss, score_all, SUBPERIODS
from . import kumo as kumo_mod
from . import trials as trials_mod

ORIGIN_START = '2002-01-04'  # IMPL: first origin (52 weeks of history); earlier weeks only warm the fitted models up
LOCK_PATH = DATA_DIR / 'oos_run.lock'
RESULT_PATH = Path(__file__).resolve().parents[1] / 'oos_result.json'
DAY = pd.Timedelta(days=7)
LABEL_DRY = 'DRY RUN on burn-in targets only (<= 2008-12-26); not evidence, not a trial'

def frame_input_max_date(weekly_o, origin):
    """PREREG v2 4 step 2: computed from the frame actually passed in; a caller-supplied value does not exist."""
    imd = pd.Timestamp(weekly_o.week.max())
    if imd > pd.Timestamp(origin): raise ScoringWallError(f'input_max_date {imd.date()} is after the origin {pd.Timestamp(origin).date()}')
    return imd

def origin_frame(vol, origin, provenance):
    """PREREG v2 4 steps 1-2: drop every daily row after the origin before any aggregation, then check the frame itself."""
    h = build_weekly(vol, through=origin, provenance=provenance)
    return h, frame_input_max_date(h, origin)

def outcome_at(weekly_o, week):
    rows = weekly_o[(weekly_o.week == pd.Timestamp(week)) & weekly_o.usable]
    return {r.cp_type: r.mix for r in rows.itertuples()} if len(rows) == len(TYPES) else None

def origin_list(first, last_target):
    return [w for w in pd.date_range(first, pd.Timestamp(last_target) - DAY, freq='W-FRI')]

def walk_forward(vol, origins, provenance, kumo_client=None, kumo_from=None, progress=None):
    """Phase 1: per origin, build H_o from the vintage, forecast every entry, and realise the loss of the previous
    origin's forecasts as soon as the target week is in the frame. Nothing is scored here."""
    st = {'forecasts': {}, 'imd': {}, 'entry_loss': {e: {} for e in ENTRIES}, 'native_loss': {e: {} for e in ENTRIES},
          'kumo_fc': {m: {} for m in kumo_mod.MODES}, 'kumo_loss': {m: {} for m in kumo_mod.MODES},
          'kumo_failed': 0, 'kumo_origins': 0, 'native': {}}
    pending = {}
    for i, w in enumerate(list(origins) + [origins[-1] + DAY]):
        h, imd = origin_frame(vol, w, provenance)
        prev = w - DAY
        out = outcome_at(h, w)
        if prev in pending and out is not None:
            fc, nat = pending.pop(prev)
            for e in ENTRIES:
                st['entry_loss'][e][w] = weekly_loss({t: fc[(e, t)] for t in TYPES}, out)
                st['native_loss'][e][w] = sum(w2sq(nat[(e, t)], q_from_p(out[t], X_LOG)) for t in TYPES) / 4
            for m in kumo_mod.MODES:
                if st['kumo_fc'][m].get(prev): st['kumo_loss'][m][w] = weekly_loss(st['kumo_fc'][m][prev], out)
        if w not in set(origins): break
        fc, nat = forecast_all(h, w, TYPES)
        pending[w] = (fc, nat)
        st['forecasts'][w] = fc; st['imd'][w] = imd
        if kumo_client is not None and (kumo_from is None or w >= pd.Timestamp(kumo_from)):
            st['kumo_origins'] += 1; failed = False
            for m in kumo_mod.MODES:
                mix, f = kumo_mod.kumo_forecast(kumo_client, h, w, m, {t: fc[('P', t)] for t in TYPES})
                st['kumo_fc'][m][w] = mix; failed = failed or (m == 'best' and f)
            st['kumo_failed'] += int(failed)
        if progress and i % 50 == 0: progress(f'origin {w.date()}')
    return st

def model_losses(st, sel, bstar, origins):
    """SEL and B* loss for target t = loss of the entry in force at origin t-1w; P, WAR, TMAR and the Kumo modes directly."""
    L = {e: dict(st['entry_loss'][e]) for e in ('P', 'WAR', 'TMAR')}
    for name, sched in (('SEL', sel), ('B*', bstar)):
        L[name] = {o + DAY: st['entry_loss'][sched[o]][o + DAY] for o in origins if sched[o] and (o + DAY) in st['entry_loss'][sched[o]]}
    for m in kumo_mod.MODES: L[f'KUMO_{m}'] = dict(st['kumo_loss'][m])
    return L

def in_window(series, lo, hi):
    return {w: v for w, v in series.items() if pd.Timestamp(lo) <= w <= pd.Timestamp(hi)}

def disclosures(vol_or_none, weekly_full):
    path = DATA_DIR / 'vintage_diffs.jsonl'
    revised = None
    if path.exists():
        revised = sum(len(r['value_changes']) + len(r['valid_flag_changes']) for r in map(json.loads, path.read_text().splitlines()))
    return {'revised_pre_wall_values_across_archived_vintages': revised,
            'faa_gt80_floored_input_share_fraction': floored_fraction(weekly_full),
            'pseudo_real_time': 'one late vintage contains revisions to pre-origin days that were not known at the origin'}

def finalize(st, origins, out_dir, window, label, weekly_full):
    """Phase 2 writes both schedules to disk; only then phase 3 scores."""
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    sel, bstar, records = build_schedules(st['entry_loss'], origins)
    sched_sha = write_schedules(records, out_dir)
    fpath = out_dir / 'forecasts.jsonl'
    with fpath.open('w') as f:
        for o, fc in st['forecasts'].items():
            for (e, t), mix in fc.items():
                f.write(json.dumps({'origin': str(o.date()), 'target': str((o + DAY).date()), 'entry': e, 'cp_type': t,
                                    'mix': [float(x) for x in mix], 'input_max_date': str(st['imd'][o].date())}) + '\n')
    L = {k: in_window(v, *window) for k, v in model_losses(st, sel, bstar, origins).items()}
    scored = score_all(L)
    k_incomplete = kumo_mod.family_k_incomplete(st['kumo_failed'], st['kumo_origins'])
    if st['kumo_origins']:
        for label_, r in scored['families'].items():
            if r['family'] == 'K' and k_incomplete:
                r.update(incomplete=True, incomplete_reason=f"Kumo failed at {st['kumo_failed']}/{st['kumo_origins']} origins (> 5%)",
                         claim=False, holm_reject=False)
    native = {e: {'mean_projected': float(np.mean(list(in_window(st['entry_loss'][e], *window).values()) or [np.nan])),
                  'mean_native': float(np.mean(list(in_window(st['native_loss'][e], *window).values()) or [np.nan]))} for e in ENTRIES}
    return {'label': label, 'score_window': list(window), 'seed': SEED, 'families': scored['families'],
            'descriptive': scored['descriptive'],
            'family_K': {'failed_origins': st['kumo_failed'], 'origins': st['kumo_origins'], 'incomplete': bool(st['kumo_origins'] == 0 or k_incomplete)},
            'native_diagnostic_nongating': native, 'disclosures': disclosures(None, weekly_full),
            'schedule_sha256': sched_sha, 'forecasts_sha256': sha256(fpath), 'subperiods': [list(s) for s in SUBPERIODS]}

def _jsonable(o):
    if isinstance(o, dict): return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [_jsonable(v) for v in o]
    if isinstance(o, (np.floating, float)): return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.bool_,)): return bool(o)
    return o

def acquire_lock(lock_path, record):
    """Run-once lock: created exclusively, its sha256 goes into every trial row."""
    lock_path = Path(lock_path)
    if lock_path.exists(): raise RunOnceError('OOS has already been run (lock file exists); refusing a second run')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(record, sort_keys=True)
    try:
        with open(lock_path, 'x') as f: f.write(body)
    except FileExistsError: raise RunOnceError('OOS has already been run (lock file exists); refusing a second run') from None
    return hashlib.sha256(body.encode()).hexdigest()

def run_oos(zip_path=None, out_dir=None, kumo_client=None, lock_path=None, trials_path=None, result_path=None):
    provenance = preflight('oos')   # (1) pinned files, then
    check_oos_approval()            # (2) the approval switch: both before anything is read
    approval = pf.APPROVAL_PATH.read_text()
    if zip_path is None:
        from .ingest import latest_vintage
        zip_path = latest_vintage()
    zip_sha = sha256(zip_path)
    if zip_sha not in approval:
        raise OOSNotAuthorized('Approval does not name this vintage zip sha256. Nothing was logged or loaded')
    if kumo_client is None: kumo_client = kumo_mod.KumoClient(Path(out_dir or DATA_DIR / 'oos') / 'kumo_attempts.jsonl')  # needs NVIDIA_API_KEY
    out_dir = Path(out_dir or DATA_DIR / 'oos'); lock_path = lock_path or LOCK_PATH
    trials_path = trials_path or TRIALS_PATH; result_path = Path(result_path or RESULT_PATH)
    manifest = {'zip_sha256': zip_sha, 'approval_sha256': sha256(pf.APPROVAL_PATH), 'endpoint': kumo_mod.URL, 'nim_image': kumo_mod.NIM_IMAGE,
                'kumo_modes': list(kumo_mod.MODES), 'seed': SEED, 'started_utc': datetime.now(timezone.utc).isoformat(), 'git_head': trials_mod.git_head()}
    if Path(trials_path).exists() and any('lock_sha256' in json.loads(r) for r in Path(trials_path).read_text().splitlines()):
        raise RunOnceError('The trial log already records an OOS run; refusing a second run')
    lock_sha = acquire_lock(lock_path, manifest)
    for label, config in trials_mod.CONFIRMATORY_TRIALS_V2: trials_mod.log_trial(config, label, provenance, trials_path, extra={'lock_sha256': lock_sha})
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'run_manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=1) + '\n')  # before the run
    vol, report = load_vol(provenance, zip_path)  # the only place amounts after the wall are parsed
    full = build_weekly(vol, through=OOS[1], provenance=provenance)
    origins = origin_list(ORIGIN_START, OOS[1])
    st = walk_forward(vol, origins, provenance, kumo_client, kumo_from=SCORING_WALL, progress=lambda m: print(m, file=sys.stderr))
    result = finalize(st, origins, out_dir, OOS, 'OOS result, one run (PREREG v2)', full)
    result.update(mode='oos', manifest=manifest, lock_sha256=lock_sha, finished_utc=datetime.now(timezone.utc).isoformat())
    result_path.write_text(json.dumps(_jsonable(result), sort_keys=True, indent=1, allow_nan=False) + '\n')
    return result

def dry_run_burnin(zip_path=None, out_dir=None, progress=None):
    """Same pipeline on burn-in only. Parsing is walled at 2008-12-26 (non-OOS provenance); nothing is logged as a trial."""
    provenance = preflight('burnin')
    if zip_path is None:
        from .ingest import latest_vintage
        zip_path = latest_vintage()
    vol, report = load_vol(provenance, zip_path)
    if provenance.oos_approved or vol.loc[vol.value.notna(), 'date'].max() > pd.Timestamp(SCORING_WALL):
        raise ScoringWallError('Dry run must not see amounts after the scoring wall')
    full = build_weekly(vol)
    origins = origin_list(ORIGIN_START, SCORING_WALL)
    assert origins[-1] + DAY <= pd.Timestamp(SCORING_WALL)
    st = walk_forward(vol, origins, provenance, None, progress=progress)
    out_dir = Path(out_dir or DATA_DIR / 'dryrun')
    result = finalize(st, origins, out_dir, ('2005-01-07', SCORING_WALL), LABEL_DRY, full)
    h, _ = origin_frame(vol, origins[-1], provenance)
    payload = kumo_mod.build_payload(h, origins[-1], 'best')
    result['kumo_payload_smoke'] = {'instances': len(payload['context']['instance_table']['rows']) + len(payload['predict']['instance_table']['rows']),
                                    'fact_rows': len(payload['context']['related_tables']['weekly_facts']['rows']) + len(payload['predict']['related_tables']['weekly_facts']['rows']),
                                    'bytes': len(kumo_mod.payload_bytes(payload)), 'sha256': kumo_mod.payload_sha256(payload), 'live_call': False}
    result.update(mode='dry-run-burnin', max_target=str((origins[-1] + DAY).date()))
    (out_dir / 'dryrun_result.json').write_text(json.dumps(_jsonable(result), sort_keys=True, indent=1, allow_nan=False) + '\n')
    return result

def main(argv=None):
    ap = argparse.ArgumentParser(prog='python -m fed_cp_ot.harness')
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('run-oos', 'dry-run-burnin'):
        p = sub.add_parser(name); p.add_argument('--zip'); p.add_argument('--out')
    args = ap.parse_args(argv)
    if args.cmd == 'run-oos': result = run_oos(args.zip, args.out)
    else: result = dry_run_burnin(args.zip, args.out, progress=lambda m: print(m, file=sys.stderr))
    print(json.dumps(_jsonable({k: v for k, v in result.items() if k in ('label', 'families', 'family_K', 'kumo_payload_smoke')}), sort_keys=True, indent=1))

if __name__ == '__main__': main()
