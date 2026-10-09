"""Replication of printed descriptive numbers; never reruns the gate."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .paths import DATA_DIR, PINNED_RESEARCH_ZIP_SHA256, PINNED_CSV_SHA256, SCORING_WALL
from .preflight import preflight, sha256
from .parse import load_vol
from .weekly import build_weekly, TYPES
from .metric import q_from_p, w2sq, decomp, barycenter, qmix, X_LOG
from .csv_check import cross_check_csv

EXPECTED = {'median_next':.1411976508,'LOC':.2434826461,'SCALE':.0852632883,'SHAPE':.6712540656,
            'P':.2693876042,'EXP':.4493067987,'MA4':.2078828687,'EWMA0.2':.1894077263}

def replicate(weekly, strict=True):
    weekly = weekly[(weekly.week >= '2001-01-05') & (weekly.week <= SCORING_WALL)]
    weeks = sorted(weekly.week.unique())
    Q = {t:{r.week:q_from_p(r.D,X_LOG) for r in weekly[(weekly.cp_type == t) & weekly.usable].itertuples()} for t in TYPES}
    nxt, dec = [], []
    L = {m:{} for m in ('P','EXP','MA4','EWMA0.2')}
    for t in TYPES:
        past = []; exp = ew = None; n_exp = 0
        for w in weeks:
            if w not in Q[t]: continue
            q = Q[t][w]
            nw = w + pd.Timedelta(days=7)
            if nw in Q[t]:
                nxt.append(w2sq(q,Q[t][nw])); dec.append(decomp(q,Q[t][nw]))
            if past:
                L['P'][(t,w)] = w2sq(past[-1],q)
                L['EXP'][(t,w)] = w2sq(exp,q)
                if len(past) >= 4: L['MA4'][(t,w)] = w2sq(barycenter(past[-4:]),q)
                L['EWMA0.2'][(t,w)] = w2sq(ew,q)
            past.append(q); n_exp += 1
            exp = q if exp is None else qmix(q,exp,1.0/n_exp)
            ew = q if ew is None else qmix(q,ew,.2)
    nxt,dec = np.array(nxt),np.array(dec)
    result = {'usable':{t:len(Q[t]) for t in TYPES},'calendar_weeks':len(weeks),'N_NEXT':len(nxt),
              'median_next':float(np.median(nxt)), 'identity_error':float(np.max(np.abs(dec.sum(1)-nxt)))}
    for j,name in enumerate(('LOC','SCALE','SHAPE')): result[name] = float(dec[:,j].sum()/nxt.sum())
    for model in L:
        means = []
        for w in weeks:
            if not (pd.Timestamp('2005-01-07') <= w <= pd.Timestamp(SCORING_WALL)): continue
            ts = [t for t in TYPES if all((t,w) in L[m] for m in (model,'P','EXP','MA4'))]
            if ts: means.append(float(np.mean([L[model][(t,w)] for t in ts])))
        result[model] = float(pd.Series(means).mean())
    matches = all(f'{result[key]:.10f}' == f'{expected:.10f}' for key, expected in EXPECTED.items())
    matches = matches and result['N_NEXT'] == 1664 and result['calendar_weeks'] == 417
    matches = matches and all(n == 417 for n in result['usable'].values()) and result['identity_error'] < 1e-12
    result['matches_pinned_numbers'] = bool(matches)
    if strict and not matches:
        raise AssertionError('Burn-in numbers differ from pinned replication: ' + str(result))
    return result

def csv_source(path=None):
    if path is not None: return Path(path)
    research = Path('/workspace/research/fed_cp_ot_prereg/raw/fed_cp_volume_stats_by_maturity.csv')
    return research if research.exists() else DATA_DIR/'fed_cp_volume_stats_by_maturity.csv'

def pinned_zip():
    candidates = [Path('/workspace/research/fed_cp_ot_prereg/raw/FRB_CP_xml.zip'),
                  *sorted((DATA_DIR/'vintages').glob('*.zip'))]
    for path in candidates:
        if path.exists() and sha256(path) == PINNED_RESEARCH_ZIP_SHA256: return path
    raise FileNotFoundError('Pinned research zip unavailable')

def run(zip_path=None, csv_path=None, compare_to_pinned=False):
    provenance = preflight('burnin')
    if zip_path is None:
        from .ingest import latest_vintage
        zip_path = latest_vintage()
    zip_sha = sha256(zip_path)
    print('Zip SHA256:', zip_sha)
    print('Equals PINNED_RESEARCH_ZIP_SHA256:', zip_sha == PINNED_RESEARCH_ZIP_SHA256)
    csv_path = csv_source(csv_path)
    if sha256(csv_path) != PINNED_CSV_SHA256: raise ValueError('Pinned CSV hash mismatch')
    vol,report = load_vol(provenance,zip_path)
    if compare_to_pinned:
        from .vintages import diff_vintages
        baseline,_ = load_vol(provenance,pinned_zip())
        # Both readers retain structural metadata only beyond the wall.
        diff = diff_vintages(baseline,vol)
        check = cross_check_csv(csv_path,baseline,SCORING_WALL)
        result = replicate(build_weekly(vol), strict=False)
        result['changed_series_dates'] = len(diff['value_changes'])
        result['burnin_diff'] = {k:v for k,v in diff.items() if k != 'post_wall_counts'}
        print('Changed burn-in value series-dates:', result['changed_series_dates'])
        print('Replicated numbers still match:', result['matches_pinned_numbers'])
    else:
        check = cross_check_csv(csv_path,vol,SCORING_WALL)
        result = replicate(build_weekly(vol))
    result.update(zip_sha256=zip_sha, pinned_zip_matches=zip_sha == PINNED_RESEARCH_ZIP_SHA256,
                  validation=report,csv_check=check,label='Burn-in replication only; not a trial or gate rerun')
    DATA_DIR.mkdir(parents=True,exist_ok=True)
    name = 'burnin_comparison.json' if compare_to_pinned else 'burnin_checks.json'
    (DATA_DIR/name).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('Usable weeks per type:',result['usable'], '; N_NEXT =',result['N_NEXT'])
    for key in EXPECTED: print(f'{key}: {result[key]:.10f}')
    print('Identity error:',result['identity_error'])
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--zip')
    parser.add_argument('--csv')
    parser.add_argument('--compare-to-pinned', action='store_true')
    args=parser.parse_args()
    run(args.zip, args.csv, args.compare_to_pinned)
if __name__ == '__main__': main()
