"""Entry point. Verifies the pinned pre-registration first; the OOS stage is gated.

Stages:
  panel  - parse the cached NIC ZIPs (complete quarters only) and write data/processed*/ (gitignored)
  oos    - walk-forward OOS scoring + gate; REFUSES to run unless the pin verifies, the governing
           design has oos_authorized = true and every open question is resolved.

--design v1_1 (default, primary gate): 2008Q1-2026Q2 ZIPs, test_design_trading_ot_v1_1.json.
--design v1_0 (R1, non-gating sensitivity pre-registered by v1.1): 2018+ data, the byte-identical
  v1.0 JSON. R1 is authorized by the v1.1 design (the v1.0 file itself never changes), so both pins
  must verify and the v1.1 design must authorize OOS.
Every OOS execution is appended to trials.jsonl with config hash, timestamp and git head *before*
scoring starts, so aborted runs still count.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import subprocess
import sys

from .paths import (DATA, DESIGN_PATH, DESIGN_PATH_V1_1, ERRATA_PATH, ERRATA_SHA256, RAW_DIR, RAW_DIRS_V1_1, ROOT,
                    TRIALS_PATH, load_design)


class OOSNotAuthorized(RuntimeError):
    pass


def assert_oos_authorized(design):
    """Stop-gate: no OOS scoring until the design authorizes it and has no unresolved questions."""
    if not design.get('oos_authorized', False):
        raise OOSNotAuthorized('OOS scoring is not authorized by the pinned design (oos_authorized=false; '
                               'awaiting approval, recorded as a separate commit). Nothing was scored.')
    open_q = [q['id'] for q in design.get('open_questions', []) if q.get('resolution') in (None, '')]
    if open_q:
        raise OOSNotAuthorized(f'Unresolved pre-registration questions: {open_q}. Nothing was scored.')


def git_head():
    return subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def config_hash(config):
    return hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest()


def log_trial(config, label, registered=True, path=TRIALS_PATH):
    """Append one trial record (JSON line). Non-registered configs are labelled EXPLORATORY."""
    record = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), git_head=git_head(),
                  config_hash=config_hash(config), label=label,
                  status='registered' if registered else 'EXPLORATORY', config=config)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, sort_keys=True, default=str) + '\n')
    return record


def trial_count(path=TRIALS_PATH):
    """Number of OOS trials; design-revision and other entries with counts_as_trial=false are not trials."""
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.strip() and json.loads(line).get('counts_as_trial', True):
            n += 1
    return n


def stage_panel(as_of, design='v1_1'):
    from .panel import build_trading_panel
    if design == 'v1_1':
        _, vintage = build_trading_panel(RAW_DIRS_V1_1, as_of, DATA / 'processed_v1_1', first='2008Q1')
    else:
        _, vintage = build_trading_panel(RAW_DIR, as_of, DATA / 'processed')
    return vintage


def verify_pins(design):
    """Pin checks for the requested run; returns provenance dict(s). Raises on any mismatch."""
    from statement_forecast.prereg import (verify_trading_ot_preregistration,
                                           verify_trading_ot_v1_1_preregistration)
    prov = dict(v1_1=verify_trading_ot_v1_1_preregistration())
    if design == 'v1_0':
        prov['v1_0'] = verify_trading_ot_preregistration()
    return prov


class ProvenanceError(RuntimeError):
    pass


def design_sha_check(which=('v1_1',)):
    """sha256 of each named design file vs the pinned value in statement_forecast.prereg; raises on mismatch."""
    from statement_forecast.prereg import TRADING_OT_PREREG_SHA256, TRADING_OT_V1_1_PREREG_SHA256
    pins = dict(v1_1=(DESIGN_PATH_V1_1, TRADING_OT_V1_1_PREREG_SHA256), v1_0=(DESIGN_PATH, TRADING_OT_PREREG_SHA256))
    out = {}
    for k in which:
        path, want = pins[k]
        got = _sha(path)
        if got != want:
            raise ProvenanceError(f'design {k} at {path}: sha256 {got} != pinned {want}. Nothing was logged or scored.')
        out[k] = dict(design=str(path.relative_to(ROOT)), design_sha256=got)
    return out


def preflight(design, which=('v1_1',)):
    """Every OOS entry point calls this first: authorization, then design pin(s), then errata hash.

    Runs before log_trial and before any data is touched; the returned provenance is reused when writing
    gate.json / r1.json / companion JSONs, so nothing is recomputed after scoring."""
    assert_oos_authorized(design)
    designs = design_sha_check(which)
    return dict(designs=designs, errata=errata_provenance())


def errata_provenance():
    """Path + sha256 of the v1.1 errata; raises if the committed copy does not match the recorded hash."""
    got = _sha(ERRATA_PATH)
    if got != ERRATA_SHA256:
        raise ProvenanceError(f'{ERRATA_PATH} sha256 {got} != recorded {ERRATA_SHA256}. Nothing was logged or scored.')
    return dict(path=str(ERRATA_PATH.relative_to(ROOT)), sha256=got,
                precedence='where a stated value conflicts with an operative rule of the pinned design, the rule governs')


def run_oos_v1_1(panel, macro, design, out_dir, trials_path=TRIALS_PATH, **engine_kw):
    """Primary v1.1 run. The authorization check is the first statement; the trial is logged before scoring."""
    pre = preflight(design, ('v1_1',))
    from . import gate, walkforward_v1_1 as V
    config = dict(design='v1_1', design_sha256=pre['designs']['v1_1']['design_sha256'], run='primary H1+H2', **{
        k: [str(x) for x in v] for k, v in engine_kw.items()})
    log_trial(config, 'v1.1 primary', path=trials_path)
    res = V.primary(panel, macro, **engine_kw)
    ev = gate.evaluate_primary_v1_1(res['h1'], res['h2'])
    provenance = dict(**pre['designs']['v1_1'], errata=pre['errata'])
    return _write(out_dir, 'gate.json', dict(design='v1_1', provenance=provenance,
                                             config_hash=config_hash(config), git_head=git_head(),
                                             hypotheses=ev, selection_log=res['selection_log'],
                                             set_sizes={k: len(v) for k, v in res['sets'].items()}))


def run_oos_v1_0(panel, macro, design_v1_1, out_dir, trials_path=TRIALS_PATH):
    """R1: the v1.0 design (B6 excluded from M0/B*, reported), non-gating; authorized via the v1.1 design."""
    pre = preflight(design_v1_1, ('v1_1', 'v1_0'))
    from . import gate, walkforward as W10
    config = dict(design='v1_0 (R1)', design_sha256=pre['designs']['v1_0']['design_sha256'], policy='exclude_b6', ytd_reset_guard=True)
    log_trial(config, 'R1 (v1.0 design, non-gating)', path=trials_path)
    frozen = W10.freeze_decisions(panel, macro, 'exclude_b6')
    h1 = W10.h1_oos(panel, macro, frozen)
    h2, params = W10.h2_oos(panel, macro, frozen)
    out = {}
    for name, long, ot, ref in [('H1', h1, 'BARY', frozen['b_star']), ('H2', h2, 'WAR', frozen['b_star_cs'])]:
        cases, counts = W10.matched_cases(long, ot, ref)
        pq = gate.per_quarter(cases)
        ci = gate.relative_gain_ci(pq)
        out[name] = dict(counts=counts, G=ci['G'], test_A=ci, coverage90=float(cases.cov_ot.mean()),
                         lobo=gate.lobo(cases), n_targets=int(len(pq)))
    adj = gate.holm({k: v['test_A']['p'] for k, v in out.items()})
    for k, v in out.items():
        v['p_holm'] = adj[k]
        v['verdict_descriptive'] = gate.verdict(adj[k], v['G'], v['test_A']['G_upper'], v['coverage90'], v['lobo'],
                                                v['n_targets'])
    provenance = dict(**pre['designs']['v1_0'], authorized_by=pre['designs']['v1_1']['design'],
                      authorized_by_sha256=pre['designs']['v1_1']['design_sha256'], errata=pre['errata'])
    return _write(out_dir, 'r1.json', dict(design='v1_0 (R1, non-gating)', provenance=provenance,
                                           config_hash=config_hash(config),
                                           frozen=frozen, hypotheses=out, war_params=params.to_dict(orient='list')))


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(out_dir, name, obj):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / name).write_text(json.dumps(obj, indent=2, default=str) + '\n', encoding='utf-8')
    return obj


def stage_oos(design_name, as_of):
    """Gate first (nothing is loaded or computed before it). R1 is authorized only through the v1.1 design."""
    governing = load_design(DESIGN_PATH_V1_1)
    assert_oos_authorized(governing)
    import pandas as pd
    from .paths import RESULTS
    from . import macro as M, panel as P
    if design_name == 'v1_1':
        panel = P.prepare_v1_1(pd.read_parquet(DATA / 'processed_v1_1' / 'trading_panel.parquet'))
        mac = M.quarter_features_v1_1(pd.period_range('2009Q1', '2026Q2', freq='Q'))
        return run_oos_v1_1(panel, mac, governing, RESULTS / 'tables')
    panel = P.prepare_v1_0(pd.read_parquet(DATA / 'processed_v1_1' / 'trading_panel.parquet'))
    mac = M.quarter_features(pd.period_range('2018Q1', '2026Q2', freq='Q'))
    return run_oos_v1_0(panel, mac, governing, RESULTS / 'tables')


def main(argv=None):
    os.environ.setdefault('OMP_NUM_THREADS', '1')
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['panel', 'oos'])
    parser.add_argument('--as-of', default='2026-10-06')
    parser.add_argument('--design', choices=['v1_1', 'v1_0'], default='v1_1')
    args = parser.parse_args(argv)
    provenance = verify_pins(args.design)
    if args.stage == 'panel':
        vintage = stage_panel(args.as_of, args.design)
        print(json.dumps(dict(provenance=provenance, last_complete_quarter=vintage['last_complete_quarter'],
                              n_quarters=vintage['n_quarters']), indent=2, default=str))
        return 0
    stage_oos(args.design, args.as_of)
    return 0


if __name__ == '__main__':
    sys.exit(main())
