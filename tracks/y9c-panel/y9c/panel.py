"""Parse consolidated items and de-cumulate within institution/calendar year."""
import csv
import io
import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd
import yaml

from .download import ROOT, RAW, utc

PROCESSED = ROOT / 'data' / 'processed'


def decumulate(frame, column):
    """Return quarterly values and missing-prior flags, aligned to input index.

    An adjacent row is insufficient: the previous calendar quarter of the same
    year must exist, with a nonmissing value. Q1 needs no predecessor.
    """
    ordered = frame.sort_values(['rssd_id', 'report_date'])
    q = ordered.report_date.dt.to_period('Q')
    group = ordered.groupby('rssd_id', sort=False)
    prev_date = group.report_date.shift().dt.to_period('Q')
    prev_value = group[column].shift()
    q1 = ordered.report_date.dt.quarter.eq(1)
    adjacent = prev_date.eq(q - 1) & ~q1
    missing = ~q1 & ordered[column].notna() & (~adjacent | prev_value.isna())
    result = (ordered[column] - prev_value).where(adjacent)
    result = result.where(~q1, ordered[column])
    return result.reindex(frame.index), missing.reindex(frame.index)


def nii_discontinuities(wide):
    """Flag negative Q2–Q4 flows and those after a fully positive year to date.

    The narrower flag requires every earlier calendar quarter in the same year
    to be present and have positive quarterly NII. Neither flag alters values.
    """
    ordered = wide.sort_values(['rssd_id', 'report_date'])
    quarter = ordered.report_date.dt.quarter
    groups = [ordered.rssd_id, ordered.report_date.dt.year]
    earlier_positive = ordered.nii_q.gt(0).groupby(groups).cumsum() - ordered.nii_q.gt(0).astype(int)
    negative = quarter.gt(1) & ordered.nii_q.lt(0)
    after_positive = negative & earlier_positive.eq(quarter - 1)
    return negative.reindex(wide.index), after_positive.reindex(wide.index)


def read_quarter(path, items):
    wanted = {'RSSD9001', 'RSSD9999', 'RSSD9017', *items}
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.lower().endswith('.txt')]
        if len(names) != 1:
            raise ValueError(f'{path}: expected exactly one .txt member')
        text = z.read(names[0]).decode('latin-1')
    lines = text.splitlines()
    header = next(csv.reader([lines[0]], delimiter='^', quoting=csv.QUOTE_NONE))
    second = next(csv.reader([lines[1]], delimiter='^', quoting=csv.QUOTE_NONE))
    # Some bulk vintages include a description row immediately after the header.
    description = not second[header.index('RSSD9001')].strip().isdigit()
    frame = pd.read_csv(io.StringIO(text), sep='^', encoding='latin-1', quoting=csv.QUOTE_NONE,
                        dtype=str, na_values=['--------', ''], keep_default_na=False,
                        skiprows=[1] if description else None, usecols=lambda c: c in wanted)
    if not {'RSSD9001', 'RSSD9999', 'RSSD9017', 'BHCK2170', 'BHCK4074'} <= set(frame.columns):
        raise ValueError(f'{path}: required identity/assets/NII columns missing')
    frame = frame.rename(columns={'RSSD9001': 'rssd_id', 'RSSD9999': 'report_date', 'RSSD9017': 'name'})
    frame['rssd_id'] = pd.to_numeric(frame.rssd_id, errors='raise').astype('int64')
    frame['report_date'] = pd.to_datetime(frame.report_date.str.strip(), format='%Y%m%d', errors='raise')
    expected = pd.to_datetime(path.stem[4:], format='%Y%m%d')
    if not frame.report_date.eq(expected).all():
        raise ValueError(f'{path}: report dates do not match filename')
    for code in items:
        frame[code] = pd.to_numeric(frame.get(code, pd.Series(index=frame.index, dtype=str)), errors='raise')
    return frame


def sanity(wide):
    """Print and enforce NII identity and complete-year telescoping checks."""
    jpm = wide[wide.rssd_id.eq(1039502)].copy()
    print('JPMorgan RSSD 1039502; all amounts in thousands USD')
    print(jpm.loc[jpm.report_date.dt.year.ge(2023), ['report_date', 'nii_ytd', 'nii_q']].to_string(index=False))
    checks = []
    for year, group in jpm.groupby(jpm.report_date.dt.year):
        if len(group) == 4 and group.nii_q.notna().all():
            total, ytd = group.nii_q.sum(), group.loc[group.report_date.dt.quarter.eq(4), 'nii_ytd'].iloc[0]
            assert np.isclose(total, ytd, rtol=0, atol=1), f'JPM {year}: quarterly sum != YTD'
            checks.append({'year': int(year), 'quarterly_sum': float(total), 'q4_ytd': float(ytd)})
    print('JPM complete-year sums equal Q4 YTD:', checks)
    comparable = wide[['total_interest_income_ytd', 'total_interest_expense_ytd', 'nii_ytd']].dropna()
    difference = comparable.total_interest_income_ytd - comparable.total_interest_expense_ytd - comparable.nii_ytd
    max_diff = float(difference.abs().max()) if len(difference) else None
    print(f'4107 - 4073 = 4074: {len(difference)} comparable rows; max absolute difference={max_diff} thousand USD')
    if len(difference) and not difference.abs().le(1).all():
        raise ValueError('Interest-income reconciliation fails (tolerance 1 thousand USD)')
    return {'jpm_complete_year_checks': checks, 'identity_rows': len(difference), 'max_identity_difference_thousands_usd': max_diff}


def main():
    items = yaml.safe_load((ROOT / 'core_items.yaml').read_text())['core_items']
    paths = sorted(RAW.glob('BHCF*.zip'))
    if not paths:
        raise ValueError('No cached ZIPs; run make y9c-data')
    frames = []
    for path in paths:
        print(f'Parsing {path.name}', flush=True)
        frames.append(read_quarter(path, items))
    raw = pd.concat(frames, ignore_index=True).sort_values(['rssd_id', 'report_date']).reset_index(drop=True)
    if raw.duplicated(['rssd_id', 'report_date']).any():
        raise ValueError('Duplicate RSSD/report-date keys')
    wide = raw[['rssd_id', 'report_date', 'name']].copy()
    long_parts = []
    missing_any = pd.Series(False, index=raw.index)
    missing_nii = missing_any.copy()
    for code, meta in items.items():
        part = raw[['rssd_id', 'report_date']].copy()
        part['item_code'], part['item_name'] = code, meta['name']
        part['value_reported'] = raw[code]
        part['value_quarterly'] = np.nan
        if meta['kind'] == 'flow_ytd':
            quarterly, missing = decumulate(raw, code)
            part['value_quarterly'] = quarterly
            wide[meta['name'] + '_ytd'] = raw[code]
            wide[meta['name'] + '_q'] = quarterly
            missing_any |= missing
            if code == 'BHCK4074':
                missing_nii = missing
        else:
            wide[meta['name']] = raw[code]
        long_parts.append(part)
    wide['nii_missing_prior'] = missing_nii
    negative, after_positive = nii_discontinuities(wide)
    wide['nii_negative_decumulation'] = negative
    wide['nii_negative_after_positive'] = after_positive
    print(f'Negative Q2–Q4 NII de-cumulations: {int(negative.sum())}; '
          f'after all prior quarters in the year were observed and positive: {int(after_positive.sum())}')
    coverage = wide.assign(missing_prior_any_flow=missing_any).groupby('report_date').agg(
        n_raw_records=('rssd_id', 'size'), n_bhcs=('total_assets', 'count'),
        n_nii_ytd=('nii_ytd', 'count'), n_nii_q=('nii_q', 'count'),
        negative_nii_decumulations=('nii_negative_decumulation', 'sum'),
        negative_nii_after_positive=('nii_negative_after_positive', 'sum'),
        dropped_missing_prior_nii=('nii_missing_prior', 'sum'),
        dropped_missing_prior_any_flow=('missing_prior_any_flow', 'sum')).reset_index()
    cutoffs = wide.dropna(subset=['total_assets']).sort_values(['report_date', 'total_assets', 'rssd_id'], ascending=[True, False, True]).groupby('report_date').head(50).groupby('report_date').total_assets.min()
    coverage['top50_asset_cutoff_thousands_usd'] = coverage.report_date.map(cutoffs)
    checks = sanity(wide)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    pd.concat(long_parts, ignore_index=True).to_parquet(PROCESSED / 'panel_long.parquet', index=False)
    wide.to_parquet(PROCESSED / 'panel_wide.parquet', index=False)
    coverage.to_csv(PROCESSED / 'coverage.csv', index=False)
    periods = sorted(wide.report_date.dt.to_period('Q').astype(str).unique())
    manifest = json.loads((RAW / 'manifest.json').read_text())
    vintage = dict(first_quarter=periods[0], last_quarter=periods[-1], n_quarters=len(periods), quarters=periods,
                   build_time_utc=utc(), downloads={p.name: manifest[p.name] for p in paths},
                   n_bhcs_per_quarter={str(row.report_date.to_period('Q')): int(row.n_bhcs) for row in coverage.itertuples()},
                   dropped_missing_prior_nii=int(missing_nii.sum()), dropped_missing_prior_any_flow=int(missing_any.sum()),
                   negative_nii_decumulations=int(negative.sum()), negative_nii_after_positive=int(after_positive.sum()),
                   negative_nii_definition='Negative de-cumulated Q2–Q4 NII; after_positive requires every earlier quarter of the same year observed and positive. Values retained as reported.',
                   units='thousands USD', sanity=checks)
    (PROCESSED / 'vintage.json').write_text(json.dumps(vintage, indent=2) + '\n')
    print(coverage.to_string(index=False))
    return 0
