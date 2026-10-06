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


def _cfg_kw(engine_kw):
    return {k: [str(x) for x in v] for k, v in engine_kw.items()}


def _primary(panel, macro, pre, out_dir, trials_path, store=False, companions=(), **engine_kw):
    from . import gate, walkforward_v1_1 as V
    config = dict(design='v1_1', design_sha256=pre['designs']['v1_1']['design_sha256'], run='primary H1+H2',
                  **_cfg_kw(engine_kw))
    log_trial(config, 'v1.1 primary', path=trials_path)
    res = V.primary(panel, macro, store=store, **engine_kw)
    ev = gate.evaluate_primary_v1_1(res['h1'], res['h2'])
    provenance = dict(**pre['designs']['v1_1'], errata=pre['errata'])
    gate_json = _write(out_dir, 'gate.json', dict(design='v1_1', provenance=provenance,
                                                  config_hash=config_hash(config), git_head=git_head(),
                                                  hypotheses=ev, selection_log=res['selection_log'],
                                                  set_sizes={k: len(v) for k, v in res['sets'].items()},
                                                  companions=list(companions)))
    return res, ev, gate_json


def run_oos_v1_1(panel, macro, design, out_dir, trials_path=TRIALS_PATH, **engine_kw):
    """Primary v1.1 run only. preflight (authorization, design pin, errata) runs before the trial is logged."""
    pre = preflight(design, ('v1_1',))
    return _primary(panel, macro, pre, out_dir, trials_path, **engine_kw)[2]


def _r1(panel, macro, pre, out_dir, trials_path):
    from . import gate, walkforward as W10
    config = dict(design='v1_0 (R1)', design_sha256=pre['designs']['v1_0']['design_sha256'], policy='exclude_b6',
                  ytd_reset_guard=True)
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


def run_oos_v1_0(panel, macro, design_v1_1, out_dir, trials_path=TRIALS_PATH):
    """R1: the v1.0 design (B6 excluded from M0/B*, reported), non-gating; authorized via the v1.1 design."""
    pre = preflight(design_v1_1, ('v1_1', 'v1_0'))
    return _r1(panel, macro, pre, out_dir, trials_path)


def _jsonable(obj):
    """Period keys/values -> str, DataFrames -> column lists, numpy scalars -> python (json default=str does
    not cover dict keys)."""
    import numpy as np
    import pandas as pd
    if isinstance(obj, dict):
        return {(str(k) if not isinstance(k, (str, int, float, bool)) or k is None else k): _jsonable(v)
                for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, pd.DataFrame):
        return _jsonable({c: [str(x) if isinstance(x, pd.Period) else x for x in obj[c].tolist()]
                          for c in obj.columns})
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, pd.Period):
        return str(obj)
    return obj


def run_all_v1_1(panel, macro, design, out_dir, trials_path=TRIALS_PATH, inputs=None, secondary=None,
                 sensitivities=None, run_r1=True, **engine_kw):
    """One authorized run: primary (gate.json), secondary family + F1-F5 + secondary metrics (secondary.json),
    sensitivities S1-S16/S4b/FB4 (sensitivities.json) and R1 (r1.json).

    preflight runs first (authorization, both design pins, errata hash) and its provenance is reused in every
    JSON. Every execution is appended to trials.jsonl (config hash) immediately before it runs.
    inputs: macro_dt (S9), panel_rule_b (S11), panel_v1_0 and macro_v1_0 (R1). secondary / sensitivities: optional
    subsets (names / 'ID:variant' strings) for tests; None = all registered members.
    """
    pre = preflight(design, ('v1_1', 'v1_0') if run_r1 else ('v1_1',))
    import numpy as np
    import pandas as pd
    from . import secondary_v1_1 as SEC, sensitivity_v1_1 as SENS, walkforward_v1_1 as V
    inputs = inputs or {}
    base = dict(design='v1_1', design_sha256=pre['designs']['v1_1']['design_sha256'],
                errata_sha256=pre['errata']['sha256'], **_cfg_kw(engine_kw))
    companions = ['secondary.json', 'sensitivities.json'] + (['r1.json'] if run_r1 else [])
    res, ev, gate_json = _primary(panel, macro, pre, out_dir, trials_path, store=True, companions=companions,
                                  **engine_kw)
    store = res['store']
    epochs = list(engine_kw.get('epochs', V.select.EPOCH_ORIGINS))
    targets = engine_kw.get('targets', V.TARGETS_H1)
    provenance = dict(**pre['designs']['v1_1'], errata=pre['errata'])

    # ── secondary family ──
    names = SEC.FAMILY if secondary is None else [n for n in SEC.FAMILY if n in secondary]
    results, details, h1d_raw = {}, {}, None

    def trial(label, **cfg):
        log_trial(dict(base, run=label, **cfg), f'v1.1 {label}', path=trials_path)

    for name in names:
        if name == 'H2c_climatology' and 'H2c_persistence' in names:
            continue                                            # computed with H2c_persistence (logged there)
        if name.startswith('H2c'):
            trial('secondary H2c (persistence and climatology comparators)', member='H2c')
            h2c = SEC.h2c(store, panel)
            for k in ('persistence', 'climatology'):
                if f'H2c_{k}' in names:
                    results[f'H2c_{k}'] = SEC.evaluate(h2c[k])
            continue
        trial(f'secondary {name}', member=name)
        if name == 'H1b':
            cases, info = SEC.h1b(store)
        elif name == 'H1c':
            cases, info = SEC.h1c(store)
        elif name == 'H1d':
            cases, info = SEC.h1d(panel, epochs=epochs, targets=targets)
            h1d_raw = info['raw']
        elif name.startswith('H1e'):
            h = int(name[-1])
            tq = [t for t in SEC.h1e_targets(h) if targets[0] <= t <= targets[-1]]
            cases, info = SEC.h1e(panel, macro, h, epochs=epochs, targets=pd.PeriodIndex(tq, freq='Q'))
        elif name == 'H2b':
            cases, info = SEC.h2b(store, panel)
        elif name == 'H2d':
            cases, info = SEC.h2d(store, macro)
        elif name == 'H2e':
            cases, info = SEC.h2e(store)
        elif name == 'H2f':
            cases, info = SEC.h2f(store)
        if name == 'H2f' and info.get('status') == 'N/A':
            results[name] = dict(status='N/A', reason=info['reason'], p=np.nan)
        else:
            results[name] = SEC.evaluate(cases)
        details[name] = info
    holm = SEC.holm_family(results)
    trial('falsification F3 rank-permutation placebo', perms=SEC.F3_PERMS, seed=SEC.F3_SEED)
    f3 = SEC.f3_placebo(store)
    metrics = {h: SEC.secondary_metrics(store, h) for h in ('H1', 'H2')}
    fals = SEC.falsification(ev, results, store, res['h1'], res['h2_all'].dropna(subset=['S_ot', 'S_ref']),
                             metrics, f3)
    _write(out_dir, 'secondary.json', _jsonable(dict(
        design='v1_1', label='secondary (Holm within family; non-gating)', provenance=provenance,
        family=SEC.FAMILY, holm=holm, results=results, details=details, falsification=fals,
        secondary_metrics=metrics, h1d_raw=h1d_raw)))

    # ── sensitivities ──
    ctx = dict(panel=panel, macro=macro, engine_kw=engine_kw, macro_dt=inputs.get('macro_dt'),
               panel_rule_b=inputs.get('panel_rule_b'), h1d_raw=h1d_raw,
               primary=dict(res, sets_periods=V.rolling_set_by_epoch(panel, epochs)))
    sens = []
    for item in SENS.PLAN:
        key = f"{item['id']}:{item['variant']}"
        if sensitivities is not None and key not in sensitivities and item['id'] not in sensitivities:
            continue
        need = {'S9': 'macro_dt', 'S11': 'panel_rule_b'}.get(item['id'])
        if need and ctx.get(need) is None:
            sens.append(dict(item, status='N/A', reason=f'input {need} not supplied'))
            continue
        trial(f'sensitivity {key}', sensitivity=item)
        out, extra = SENS.run_item(item, ctx)
        sens.append(dict(item, label=item['config'].get('label'), status='ok', results=out, details=extra))
    _write(out_dir, 'sensitivities.json', _jsonable(dict(
        design='v1_1', label='sensitivities (pre-registered; none can change a primary verdict)',
        provenance=provenance, primary_reference={k: dict(G=v['G'], p=v['dm']['p'], verdict=v['verdict'])
                                                  for k, v in ev.items()}, sensitivities=sens)))

    r1 = None
    if run_r1:
        if inputs.get('panel_v1_0') is None or inputs.get('macro_v1_0') is None:
            raise ValueError('run_r1=True needs inputs panel_v1_0 and macro_v1_0')
        r1 = _r1(inputs['panel_v1_0'], inputs['macro_v1_0'], pre, out_dir, trials_path)
    return dict(gate=gate_json, secondary=results, sensitivities=sens, r1=r1)


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(out_dir, name, obj):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / name).write_text(json.dumps(obj, indent=2, default=str) + '\n', encoding='utf-8')
    return obj


def stage_oos(design_name, as_of):
    """Gate first (nothing is loaded or computed before it). R1 is authorized only through the v1.1 design.

    --design v1_1 runs everything registered in one go (primary, secondary, sensitivities, R1);
    --design v1_0 runs R1 alone."""
    governing = load_design(DESIGN_PATH_V1_1)
    preflight(governing, ('v1_1', 'v1_0'))
    import pandas as pd
    from .paths import RESULTS
    from . import macro as M, panel as P
    raw = pd.read_parquet(DATA / 'processed_v1_1' / 'trading_panel.parquet')
    panel_v1_0 = P.prepare_v1_0(raw)
    mac_v1_0 = M.quarter_features(pd.period_range('2018Q1', '2026Q2', freq='Q'))
    if design_name == 'v1_1':
        qs = pd.period_range('2009Q1', '2026Q2', freq='Q')
        inputs = dict(macro_dt=M.quarter_features_v1_1(qs, asof_rule='Dt'), panel_rule_b=P.prepare_v1_1(raw, 'b'),
                      panel_v1_0=panel_v1_0, macro_v1_0=mac_v1_0)
        return run_all_v1_1(P.prepare_v1_1(raw), M.quarter_features_v1_1(qs), governing, RESULTS / 'tables',
                            inputs=inputs)
    return run_oos_v1_0(panel_v1_0, mac_v1_0, governing, RESULTS / 'tables')


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
