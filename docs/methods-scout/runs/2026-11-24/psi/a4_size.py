"""A4 size on our sampling: independent AR(p) pairs fitted to real log differences; plus common instantaneous shock."""
import json, numpy as np, warnings; warnings.filterwarnings('ignore')
from statsmodels.tsa.ar_model import AutoReg, ar_select_order
from statsmodels.tsa.api import VAR
from psi_core import psi
import data_psi as D
R = 1000; out = {}
def fit_ar(x):
    sel = ar_select_order(x, maxlag=4, ic='bic'); lags = sel.ar_lags or []
    m = AutoReg(x, lags=lags if lags else 0, trend='c').fit()
    return m, (lags if lags else [])
def simulate(m, lags, n, rng, innov):
    p = max(lags) if lags else 0; par = np.asarray(m.params); c = par[0]; phi = dict(zip(lags, par[1:]))
    x = np.zeros(n + 50)
    for t in range(n + 50):
        v = c + innov[t]
        for l, ph in phi.items():
            if t - l >= 0: v += ph * x[t - l]
        x[t] = v
    return x[50:]
for name in ('W1', 'M2'):
    pr = [q for q in D.PAIRS if q[0] == name][0]; d = D.pair(*pr[1:]); P = D.PARAM[pr[1]]; n = len(d)
    fx, lx = fit_ar(d[pr[2]].values); fy, ly = fit_ar(d[pr[3]].values)
    rx = fx.resid / fx.resid.std(); ry = fy.resid / fy.resid.std(); sx, sy = fx.resid.std(), fy.resid.std()
    rng = np.random.default_rng(20261124 + (1 if name == 'M2' else 0)); res = {}
    for scen in ('independent', 'common_shock'):
        psi_rej = gc_any = gc_dir = 0; zs = []
        for _ in range(R):
            ex = rng.choice(rx, n + 50) * sx; ey = rng.choice(ry, n + 50) * sy
            if scen == 'common_shock':
                g = rng.normal(size=n + 50); ex = np.sqrt(.5) * ex + np.sqrt(.5) * sx * g; ey = np.sqrt(.5) * ey + np.sqrt(.5) * sy * g
            x = simulate(fx, lx, n, rng, ex); y = simulate(fy, ly, n, rng, ey)
            r = psi(x, y, **P); zs.append(r['z']); psi_rej += abs(r['z']) > 2
            v = VAR(np.column_stack([x, y])).fit(maxlags=8, ic='aic')
            if v.k_ar > 0:
                pxy = v.test_causality(1, 0, kind='f').pvalue; pyx = v.test_causality(0, 1, kind='f').pvalue
                gc_any += (pxy < .05) or (pyx < .05); gc_dir += pxy < .05
        res[scen] = dict(psi_reject_abs_z_gt2=psi_rej / R, granger_either_direction=gc_any / R, granger_stated_direction=gc_dir / R, z_sd=float(np.nanstd(zs)))
        print(name, scen, res[scen], flush=True)
    out[name] = dict(n=n, ar_lags_x=lx, ar_lags_y=ly, **res,
                     pass_size={s: bool(.03 <= res[s]['psi_reject_abs_z_gt2'] <= .08) for s in res})
json.dump(out, open('a4_size.json', 'w'), indent=1, default=float)
