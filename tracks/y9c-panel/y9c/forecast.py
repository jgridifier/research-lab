"""Pre-specified next-quarter NII forecasts; no test-window tuning."""
import numpy as np
import pandas as pd

METHODS = ['naive', 'seasonal_naive', 'pooled_ar']


def design(panel):
    data = panel.copy()
    data['quarter'] = data.report_date.dt.to_period('Q')
    data = data.set_index(['rssd_id', 'quarter']).sort_index()
    # Calendar-key joins, never row shifts across gaps in a bank's history.
    y = data.nii_q
    ids = data.index.get_level_values('rssd_id')
    dates = data.index.get_level_values('quarter')
    for lag in [1, 3, 4, -1]:
        keys = pd.MultiIndex.from_arrays([ids, dates - lag], names=data.index.names)
        data[f'y_lag{lag}'] = y.reindex(keys).to_numpy()
    positive = data[['nii_q', 'y_lag1', 'y_lag3', 'y_lag4']].gt(0).all(axis=1)
    data['g_now'] = np.log(data.nii_q.where(positive)) - np.log(data.y_lag1.where(positive))
    data['g_season'] = np.log(data.y_lag3.where(positive)) - np.log(data.y_lag4.where(positive))
    data['g_next'] = np.log(data['y_lag-1'].where(data['y_lag-1'].gt(0))) - np.log(data.nii_q.where(data.nii_q.gt(0)))
    data = data.reset_index()
    selected = (data.dropna(subset=['total_assets'])
                .sort_values(['quarter', 'total_assets', 'rssd_id'], ascending=[True, False, True])
                .groupby('quarter').head(50).index)
    data['selected'] = data.index.isin(selected)
    return data


def evaluate(panel):
    data = design(panel)
    last = data.quarter.max()
    origins = pd.period_range('2021Q4', last - 1, freq='Q')
    predictions, audit = [], []
    for origin in origins:
        candidates = data[data.quarter.eq(origin) & data.selected].copy()
        target_ok = candidates['y_lag-1'].notna()
        history_ok = candidates[['nii_q', 'y_lag3']].notna().all(axis=1)
        cases = candidates[target_ok & history_ok].copy()
        # A historical training row's origin is s, so s < t guarantees s+1 <= t.
        train = data[data.selected & data.quarter.lt(origin)].dropna(subset=['g_now', 'g_season', 'g_next'])
        if len(train) < 3:
            raise ValueError(f'{origin}: insufficient pooled AR burn-in')
        x = np.column_stack([np.ones(len(train)), train.g_now, train.g_season])
        coefficients, _, rank, _ = np.linalg.lstsq(x, train.g_next, rcond=None)
        if rank != 3:
            raise ValueError(f'{origin}: rank-deficient pooled AR training matrix')
        cases['actual'] = cases['y_lag-1']
        cases['naive'] = cases.nii_q
        cases['seasonal_naive'] = cases.y_lag3
        cases['pooled_ar'] = cases.nii_q
        usable = cases[['g_now', 'g_season']].notna().all(axis=1)
        xp = np.column_stack([np.ones(usable.sum()), cases.loc[usable, 'g_now'], cases.loc[usable, 'g_season']])
        cases.loc[usable, 'pooled_ar'] = cases.loc[usable, 'nii_q'] * np.exp(xp @ coefficients)
        if not np.isfinite(cases[METHODS + ['actual']].to_numpy()).all():
            raise ValueError(f'{origin}: nonfinite forecast; no clipping or silent case removal')
        cases['target_quarter'] = origin + 1
        cases['ar_fallback'] = ~usable
        predictions.append(cases[['rssd_id', 'quarter', 'target_quarter', 'actual', *METHODS, 'ar_fallback']])
        audit.append(dict(origin=str(origin), target=str(origin + 1), selected=len(candidates),
                          dropped_target_missing=int((~target_ok).sum()),
                          dropped_history=int((target_ok & ~history_ok).sum()), evaluated=len(cases),
                          ar_fallbacks=int((~usable).sum()), training_rows=len(train),
                          training_last_target=str(train.quarter.max() + 1)))
    forecasts = pd.concat(predictions, ignore_index=True)
    if forecasts.empty:
        raise ValueError('No evaluation cases')
    forecasts['target_year'] = forecasts.target_quarter.dt.year
    overall = metrics(forecasts)
    by_year = pd.concat([metrics(group).assign(target_year=int(year))
                         for year, group in forecasts.groupby('target_year')], ignore_index=True)
    summary = dict(target='BHCK4074 quarterly net interest income', units='thousands USD',
                   fixed_test_start='2022Q1', test_end=str(last), first_origin='2021Q4', last_origin=str(last - 1),
                   n_forecasts_per_method=len(forecasts), n_target_quarters=len(origins),
                   selected_origin_bhc_pairs=sum(a['selected'] for a in audit),
                   dropped_target_missing=sum(a['dropped_target_missing'] for a in audit),
                   dropped_history=sum(a['dropped_history'] for a in audit),
                   ar_fallbacks=sum(a['ar_fallbacks'] for a in audit),
                   zero_actuals_excluded_from_mape=int(forecasts.actual.eq(0).sum()),
                   nonpositive_actuals=int(forecasts.actual.le(0).sum()),
                   supplementary_metric_note='MdAPE (median absolute percentage error, %): supplementary, added after observing MAPE outliers; does not replace MAPE',
                   supplementary_mdape_winners=overall.loc[overall.mdape.eq(overall.mdape.min()), 'method'].tolist(),
                   supplementary_by_year_mdape_winners={str(year): group.loc[group.mdape.eq(group.mdape.min()), 'method'].tolist()
                                                        for year, group in by_year.groupby('target_year')},
                   winners={metric: overall.loc[overall[metric].eq(overall[metric].min()), 'method'].tolist()
                            for metric in ['mae', 'rmse', 'mape']},
                   by_year_winners={str(year): {metric: group.loc[group[metric].eq(group[metric].min()), 'method'].tolist()
                                              for metric in ['mae', 'rmse', 'mape']}
                                    for year, group in by_year.groupby('target_year')},
                   origin_audit=audit)
    return forecasts, overall, by_year, summary


def metrics(cases):
    rows = []
    for method in METHODS:
        error = cases[method] - cases.actual
        nonzero = cases.actual.ne(0)
        rows.append(dict(method=method, n_forecasts=len(cases), mae=float(error.abs().mean()),
                         rmse=float(np.sqrt((error ** 2).mean())),
                         mape=float((error[nonzero].abs() / cases.loc[nonzero, 'actual'].abs()).mean() * 100),
                         n_mape=int(nonzero.sum()),
                         mdape=float((error[nonzero].abs() / cases.loc[nonzero, 'actual'].abs()).median() * 100)))
    return pd.DataFrame(rows)
