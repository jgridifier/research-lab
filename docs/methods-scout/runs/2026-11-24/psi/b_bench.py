"""B: walk-forward, monthly log change of PB borrowing, test 2019-01..2025-12. Pre-registered rule: PSI-gated beats best other by >=3% RMSE and DM p<0.10."""
import json, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.api import ARDL
from scipy.stats import norm
from psi_core import psi
import data_psi as D
d = pd.concat([D.MONTHLY['pb'], D.MONTHLY['rr']], axis=1, keys=['pb', 'rr']).dropna(); d.index = d.index.to_timestamp()
test_idx = [i for i, t in enumerate(d.index) if t >= pd.Timestamp('2019-01-01')]
P = D.PARAM['monthly']; preds = {k: [] for k in ['zero', 'ols', 'ardl', 'sarima', 'sarimax', 'psi_gated']}; actual = []; gated = []; ARDL_ERR = []
for i in test_idx:
    tr = d.iloc[:i]; y = tr.pb.values; x = tr.rr.values; a = d.pb.iloc[i]; actual.append(a)
    preds['zero'].append(y.mean() * 0 + 0.0)
    X = np.column_stack([np.ones(len(y) - 1), x[:-1]]); b = np.linalg.lstsq(X, y[1:], rcond=None)[0]; preds['ols'].append(b[0] + b[1] * x[-1])
    try:
        best = None
        for p in range(0, 4):
            for q in range(1, 4):   # lags 1..q of reverse repo (lag 0 is unknown at forecast time)
                m = ARDL(y, p, pd.DataFrame({'rr': x}), {'rr': list(range(1, q + 1))}, trend='c').fit(); bic = m.bic
                if best is None or bic < best[0]: best = (bic, m, p, q)
        preds['ardl'].append(float(np.asarray(best[1].forecast(1))[0])); ardl_ok = True
    except Exception as e:
        ARDL_ERR.append(repr(e)[:120]); preds['ardl'].append(preds['ols'][-1])
    try: s1 = SARIMAX(y, order=(1, 0, 1), trend='c').fit(disp=False); preds['sarima'].append(float(s1.forecast(1)[0]))
    except Exception: preds['sarima'].append(float(y.mean()))
    try:
        s2 = SARIMAX(y[1:], exog=x[:-1], order=(1, 0, 1), trend='c').fit(disp=False); preds['sarimax'].append(float(s2.forecast(1, exog=np.array([[x[-1]]]))[0]))
    except Exception: preds['sarimax'].append(preds['sarima'][-1])
    r = psi(y, x, **P); use = abs(r['z']) > 2 and r['z'] < 0   # y=pb, x=rr: z<0 means rr leads pb
    gated.append(bool(use)); preds['psi_gated'].append(preds['sarimax'][-1] if use else preds['sarima'][-1])
act = np.array(actual); res = {}
for k, v in preds.items(): e = act - np.array(v); res[k] = dict(rmse=float(np.sqrt((e ** 2).mean())), mae=float(np.abs(e).mean()))
best_other = min((k for k in res if k != 'psi_gated'), key=lambda k: res[k]['rmse'])
e1 = (act - np.array(preds['psi_gated'])) ** 2; e0 = (act - np.array(preds[best_other])) ** 2; dd = e0 - e1
dm = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))) if dd.std() > 0 else 0.0; pdm = 2 * (1 - norm.cdf(abs(dm)))
out = dict(ardl_fallbacks=len(ARDL_ERR), ardl_first_error=(ARDL_ERR[0] if ARDL_ERR else None), n_test=len(act), test_start=str(d.index[test_idx[0]].date()), test_end=str(d.index[test_idx[-1]].date()), results=res, best_other=best_other,
           gated_share=float(np.mean(gated)), rmse_gain_vs_best_other=1 - res['psi_gated']['rmse'] / res[best_other]['rmse'], dm_stat=float(dm), dm_p=float(pdm),
           promising=bool((1 - res['psi_gated']['rmse'] / res[best_other]['rmse'] >= .03) and pdm < .10))
json.dump(out, open('b_bench.json', 'w'), indent=1); print(json.dumps(out, indent=1))
