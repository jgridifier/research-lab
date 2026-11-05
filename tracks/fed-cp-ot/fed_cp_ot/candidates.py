"""The v1 GATE_THRESHOLDS 5 candidate list, with the PREREG v2 projection (1), LS cutpoints (3) and edge-case rules (7).

Every forecaster fits one type on its origin_view and returns a 6-share mix on X_LOG. Forecasters that produce a quantile
function call project_qf inside fit_predict. History is the usable-week sequence at or before the origin (last-usable-week
convention, 7e). Documented implementation defaults the specs do not fix are marked IMPL below.
"""
import math
import numpy as np
from .forecast import origin_view
from .metric import X_LOG, q_from_p, barycenter, qmix, alr, softmax_alr, project_qf, _merge

LS_CUTS = np.log([4.5, 9.5, 20.5, 40.5, 80.5])  # PREREG v2 3: data-bucket boundaries at half days
EWMA_ALPHAS = (0.1, 0.2, 0.3, 0.5)
RIDGE_LAMBDAS = (0.1, 1.0, 10.0, 100.0)
MIN_FIT = 52        # IMPL: usable weeks needed before a fitted model is used; below it the forecast is P
LOG_SD_FLOOR = 1e-4  # IMPL: single-atom weeks have sd 0; floored before the log in LS
RIDGE_LAGS = 4

def usable_mixes(history, origin):
    """(n, 6) array of usable-week mixes at or before the origin, oldest first. One type only."""
    view = origin_view(history, origin)
    if view.cp_type.nunique() > 1: raise ValueError('Forecast one type at a time')
    usable = view[view.usable].sort_values('week')
    if usable.empty: raise ValueError('No usable history')
    return np.vstack(list(usable['mix']))

_QF_CACHE = {}
def _qf(p):
    key = p.tobytes()  # pure function of the mix, so caching cannot change any forecast
    if key not in _QF_CACHE:
        if len(_QF_CACHE) > 50000: _QF_CACHE.clear()
        _QF_CACHE[key] = q_from_p(p, X_LOG)
    return _QF_CACHE[key]

def _qfs(mixes): return [_qf(p) for p in mixes]

def _ar1(y):
    """Per-column OLS AR(1) with intercept on a (n, k) series; returns the one-step forecast from the last row."""
    x, z = y[:-1], y[1:]
    xm, zm = x.mean(0), z.mean(0)
    var = ((x - xm) ** 2).sum(0)
    b = np.divide(((x - xm) * (z - zm)).sum(0), var, out=np.zeros(y.shape[1]), where=var > 0)
    return zm + b * (y[-1] - xm)

def normal_buckets(mu, sigma):
    """PREREG v2 3: normal on ln(days) cut at LS_CUTS, tails folded into the end buckets; Phi via math.erf."""
    cdf = [0.5 * (1 + math.erf((c - mu) / (sigma * math.sqrt(2)))) for c in LS_CUTS]
    p = np.diff(np.r_[0.0, cdf, 1.0])
    assert abs(p.sum() - 1) < 1e-12 and (p >= 0).all()
    return p

class _Base:
    """fit_predict_both returns (6-share mix on X_LOG, native quantile function). The mix is what is scored; the native
    quantile function (before project_qf) feeds the non-gating native diagnostic of PREREG v2 1."""
    def fit_predict(self, history, origin): return self.fit_predict_both(history, origin)[0]
    def _both(self, out):
        if isinstance(out, tuple): return project_qf(*out, X_LOG), out
        return out, q_from_p(out, X_LOG)

class Persistence(_Base):
    name = 'P'
    def fit_predict_both(self, history, origin): return self._both(usable_mixes(history, origin)[-1].copy())

class MA4(_Base):
    """Barycenter of the 4 most recent usable weeks (7e). A planning proxy only; not a SEL entry."""
    name = 'MA4'
    def fit_predict_both(self, history, origin):
        return self._both(barycenter(_qfs(usable_mixes(history, origin)[-4:])))

class EWMA(_Base):
    def __init__(self, alpha): self.alpha, self.name = alpha, f'EWMA{alpha}'
    def fit_predict_both(self, history, origin):
        ew = None
        for q in _qfs(usable_mixes(history, origin)):  # updates only on usable weeks
            ew = q if ew is None else qmix(q, ew, self.alpha)
        return self._both(ew)

class EXP(_Base):
    name = 'EXP'
    def fit_predict_both(self, history, origin):
        exp = None
        for n, q in enumerate(_qfs(usable_mixes(history, origin)), 1):
            exp = q if exp is None else qmix(q, exp, 1.0 / n)
        return self._both(exp)

class _Fitted(_Base):
    """Fitted candidates fall back to P with fewer than MIN_FIT usable weeks."""
    def fit_predict_both(self, history, origin):
        mixes = usable_mixes(history, origin)
        return self._both(mixes[-1].copy() if len(mixes) < MIN_FIT else self._fit(mixes))

class LS(_Fitted):
    name = 'LS'
    def _fit(self, mixes):
        m = mixes @ X_LOG
        s = np.sqrt(np.maximum((mixes * (X_LOG - m[:, None]) ** 2).sum(1), 0))
        y = np.c_[m, np.log(np.maximum(s, LOG_SD_FLOOR))]
        mu, log_sd = _ar1(y)
        return normal_buckets(mu, math.exp(log_sd))

class ALR_AR(_Fitted):
    name = 'ALR-AR'
    def _fit(self, mixes): return softmax_alr(_ar1(np.array([alr(p) for p in mixes])))

class ALR_VAR(_Fitted):
    name = 'ALR-VAR'
    def _fit(self, mixes):
        y = np.array([alr(p) for p in mixes])
        X = np.c_[np.ones(len(y) - 1), y[:-1]]
        coef = np.linalg.lstsq(X, y[1:], rcond=None)[0]
        return softmax_alr(np.r_[1.0, y[-1]] @ coef)

class MNL_AR(_Fitted):
    """Fractional multinomial logit of the next mix on the lagged ALR, quasi-ML by Newton with step halving."""
    name = 'MNL-AR'
    RIDGE, ITERS, TOL = 1e-8, 50, 1e-10  # IMPL: numerical jitter on the Hessian only
    def _fit(self, mixes):
        a = np.array([alr(p) for p in mixes])
        X, Y = np.c_[np.ones(len(a) - 1), a[:-1]], mixes[1:]
        B = np.zeros((X.shape[1], 5))
        def probs(B):
            z = np.c_[np.zeros(len(X)), X @ B]; z = np.exp(z - z.max(1, keepdims=True))
            return z / z.sum(1, keepdims=True)
        def ll(B): return float((Y * np.log(np.maximum(probs(B), 1e-300))).sum())
        cur = ll(B)
        for _ in range(self.ITERS):
            P = probs(B)
            grad = (X.T @ (Y - P)[:, 1:]).ravel('F')
            k = X.shape[1]
            H = np.zeros((5 * k, 5 * k))
            for j in range(5):
                for l in range(5):
                    w = P[:, j + 1] * ((j == l) - P[:, l + 1])
                    H[j*k:(j+1)*k, l*k:(l+1)*k] = (X * w[:, None]).T @ X
            step = np.linalg.solve(H + self.RIDGE * np.eye(5 * k), grad).reshape((5, k)).T
            t, new = 1.0, cur
            while t > 1e-6:
                new = ll(B + t * step)
                if new >= cur: break
                t /= 2
            else: break
            B, gain, cur = B + t * step, new - cur, new
            if gain < self.TOL: break
        return self._predict(B, a)
    @staticmethod
    def _predict(B, a):
        z = np.r_[0.0, np.r_[1.0, a[-1]] @ B]; z = np.exp(z - z.max())
        return z / z.sum()

class Ridge(_Fitted):
    """Lagged ALR (lags 1-4) to next ALR; ridge on centred columns, intercept unpenalised."""
    def __init__(self, lam): self.lam, self.name = lam, f'RIDGE{lam}'
    def _fit(self, mixes):
        a = np.array([alr(p) for p in mixes])
        n = len(a)
        X = np.array([np.r_[tuple(a[t - l] for l in range(1, RIDGE_LAGS + 1))] for t in range(RIDGE_LAGS, n)])
        Y = a[RIDGE_LAGS:]
        xm, ym = X.mean(0), Y.mean(0)
        B = np.linalg.solve((X - xm).T @ (X - xm) + self.lam * np.eye(X.shape[1]), (X - xm).T @ (Y - ym))
        x_new = np.r_[tuple(a[n - l] for l in range(1, RIDGE_LAGS + 1))]
        return softmax_alr(ym + (x_new - xm) @ B)

def _isotonic(values, weights):
    """Weighted pool-adjacent-violators (non-decreasing)."""
    blocks = []
    for v, w in zip(values, weights):
        blocks.append([v * w, w, 1])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
            s, w2, c = blocks.pop(); blocks[-1][0] += s; blocks[-1][1] += w2; blocks[-1][2] += c
    return np.concatenate([np.full(c, s / w) for s, w, c in blocks])

class WAR(_Fitted):
    """WAR(1): Q_hat = Qbar + rho (Q_last - Qbar) around the expanding barycenter, rho from L2 least squares on
    consecutive usable pairs, clipped to [0, 1]; the result is then made isotone."""
    name = 'WAR'
    def _fit(self, mixes):
        qs = _qfs(mixes)
        qbar = qs[0]
        for n, q in enumerate(qs[1:], 2): qbar = qmix(q, qbar, 1.0 / n)
        num = den = 0.0
        for q, q_next in zip(qs[:-1], qs[1:]):
            _, l, (a, b, bar) = _merge(q, q_next, qbar)
            num += float(np.sum(l * (a - bar) * (b - bar))); den += float(np.sum(l * (a - bar) ** 2))
        rho = min(max(num / den, 0.0), 1.0) if den > 0 else 0.0
        c, v = qmix(qs[-1], qbar, rho)
        l = np.diff(np.r_[0.0, c])
        return c, _isotonic(v, l)

class TMAR(_Fitted):
    """Transport-map AR: Q_next = a + b Q_prev, (a, b) by pooled L2 least squares over consecutive usable pairs, b in [0, 2]."""
    name = 'TMAR'
    def _fit(self, mixes):
        qs = _qfs(mixes)
        sx = sy = sxx = sxy = 0.0
        for q, q_next in zip(qs[:-1], qs[1:]):
            _, l, (x, y) = _merge(q, q_next)
            sx += np.sum(l * x); sy += np.sum(l * y); sxx += np.sum(l * x * x); sxy += np.sum(l * x * y)
        n = len(qs) - 1
        var = sxx - sx * sx / n
        b = min(max((sxy - sx * sy / n) / var, 0.0), 2.0) if var > 0 else 0.0
        a = (sy - b * sx) / n
        c, v = qs[-1]
        return c, a + b * v

NON_OT = ('P', *[f'EWMA{a}' for a in EWMA_ALPHAS], 'EXP', 'LS', 'ALR-AR', 'ALR-VAR', 'MNL-AR', *[f'RIDGE{l}' for l in RIDGE_LAMBDAS])
OT = ('WAR', 'TMAR')
ENTRIES = NON_OT + OT  # list order = the simplicity order used for SEL ties

def make_forecaster(name):
    table = {'P': Persistence, 'EXP': EXP, 'LS': LS, 'ALR-AR': ALR_AR, 'ALR-VAR': ALR_VAR, 'MNL-AR': MNL_AR, 'WAR': WAR, 'TMAR': TMAR}
    if name in table: return table[name]()
    if name.startswith('EWMA'): return EWMA(float(name[4:]))
    if name.startswith('RIDGE'): return Ridge(float(name[5:]))
    raise KeyError(name)

def forecast_all(weekly_o, origin, types, entries=ENTRIES):
    """({(entry, type): mix}, {(entry, type): native QF}) from one origin view of the weekly frame. Forecasters see only origin_view copies."""
    out, native = {}, {}
    fs = {e: make_forecaster(e) for e in entries}
    for typ in types:
        h = weekly_o[weekly_o.cp_type == typ]
        for e, f in fs.items():
            mix, native[(e, typ)] = f.fit_predict_both(origin_view(h, origin), origin)
            out[(e, typ)] = np.asarray(mix, float)
    return out, native

def floored_fraction(weekly, cp_type='FAA', bucket=5):
    """Share of usable type-weeks whose bucket share is zero and so hits the 1e-4 ALR floor (7c; FAA GT80 by default)."""
    mixes = usable_mixes(weekly[weekly.cp_type == cp_type], weekly.week.max())
    return float((mixes[:, bucket] == 0).mean())
