"""Per-bank probabilistic baselines B0-B6 (prereg §3). Every output is a (n, 99) quantile array on U99.

All functions take a `Wide` built from a panel that has already been hard-truncated
to quarters <= origin, so nothing dated after the origin can enter. `space` selects
the forecast variable: 'usd' (A220_q, $k; bank set T2) or 'ratio' (r, bp of lagged
trading assets; cross-section T3). Predictive quantiles are centre + empirical
(type 7) quantiles of the bank's own historical errors for that baseline and
horizon; with fewer than MIN_OWN_ERRORS own errors, pooled scaled errors across
the population (errors / pooling scale, multiplied back) are used instead.
"""
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from statement_forecast.eb import eb_forecast_origin, seasonal_regressors

from .scoring import U19, U99

MIN_OWN_ERRORS = 8
SES_ALPHA = 0.3
B4_MIN_PAIRS = 8
SAA_WINDOW = 8
MAD_K = 1.4826
MEMBERS = ['B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6']


def mad(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(MAD_K * np.median(np.abs(x - np.median(x)))) if len(x) else np.nan


class Wide:
    """Bank x quarter arrays from a (truncated) panel. Quarters run `first`..last quarter in the panel.

    v1.0/R1: first = 2018Q1 (no 2017Q4 rows exist, so the 2018Q1 lag is NaN as before).
    v1.1: first = 2009Q1; Dlag[:, 0] is TA(2008Q4), the only pre-sample value that is ever used.
    """

    def __init__(self, panel, banks, denom='trading_assets', first='2018Q1', target='trading_revenue_q'):
        self.banks = list(banks)
        last = panel.quarter.max()
        self.quarters = pd.period_range(first, last, freq='Q')
        sub = panel[panel.rssd_id.isin(self.banks)].set_index(['rssd_id', 'quarter'])
        keys = pd.MultiIndex.from_product([self.banks, self.quarters])
        shape = (len(self.banks), len(self.quarters))
        self.Y = sub[target].reindex(keys).to_numpy(float).reshape(shape)
        self.A = sub['total_assets'].reindex(keys).to_numpy(float).reshape(shape)
        # denominator on first-1..last so the first quarter's lag is a calendar lag (v1.1: TA 2008Q4 -> 2009Q1 r)
        ext = pd.period_range(pd.Period(first, freq='Q') - 1, last, freq='Q')
        Dext = sub[denom].reindex(pd.MultiIndex.from_product([self.banks, ext])).to_numpy(float)
        Dext = Dext.reshape(len(self.banks), len(ext))
        self.D = Dext[:, 1:]
        self.Dlag = Dext[:, :-1]
        Dl = self.Dlag
        self.R = 1e4 * self.Y / np.where(Dl > 0, Dl, np.nan)
        self.denom = denom
        self.panel = panel

    def idx(self, quarter):
        return int(self.quarters.get_loc(pd.Period(quarter, freq='Q')))

    def Z(self, space):
        return self.Y if space == 'usd' else self.R


def q7(x, taus=U99):
    """Type-7 empirical quantiles (flat beyond the extreme order statistics by construction)."""
    return np.quantile(np.asarray(x, float), taus, method='linear')


def error_quantiles(centres, errors, pool_scale, min_own=MIN_OWN_ERRORS):
    """centre_i + quantiles of own errors, or of pooled scaled errors x s_i if fewer than min_own.

    errors: list of 1-D arrays (finite values only), one per bank; pool_scale: (n,) scales.
    Returns (Q (n,99), used_pool (n,) bool).
    """
    n = len(centres)
    pooled = np.concatenate([e / s for e, s in zip(errors, pool_scale) if len(e) and np.isfinite(s) and s > 0]
                            or [np.array([])])
    Q = np.full((n, len(U99)), np.nan)
    used_pool = np.zeros(n, bool)
    for i in range(n):
        if not np.isfinite(centres[i]):
            continue
        if len(errors[i]) >= min_own:
            Q[i] = centres[i] + q7(errors[i])
        elif len(pooled) >= 2 and np.isfinite(pool_scale[i]) and pool_scale[i] > 0:
            Q[i] = centres[i] + pool_scale[i] * q7(pooled)
            used_pool[i] = True
    return Q, used_pool


def _errs(Zt, F, upto):
    """Per-bank finite errors Z_s - F_s for s <= upto."""
    E = Zt[:, :upto + 1] - F[:, :upto + 1]
    return [row[np.isfinite(row)] for row in E]


def _shift(M, h):
    out = np.full_like(M, np.nan)
    if h < M.shape[1]:
        out[:, h:] = M[:, :M.shape[1] - h]
    return out


def ses_levels(R, alpha=SES_ALPHA):
    """l_s = alpha r_s + (1-alpha) l_(s-1); initialised at the first observed r; a missing r leaves l unchanged."""
    L = np.full_like(R, np.nan)
    for i in range(R.shape[0]):
        level = np.nan
        for s in range(R.shape[1]):
            r = R[i, s]
            if np.isfinite(r):
                level = r if not np.isfinite(level) else alpha * r + (1 - alpha) * level
            L[i, s] = level
    return L


def _min_own(W):
    """Own-error minimum: 8 (default); H1d's single series sets W.min_own = 2 (addendum §6 Q6)."""
    return getattr(W, 'min_own', MIN_OWN_ERRORS)


def _use_q1(W):
    """Q1 dummy in B4/B5: on by default; sensitivity S6 sets W.use_q1 = False (term dropped)."""
    return getattr(W, 'use_q1', True)


def _with_horizon(W, t, h):
    """f(M): keep columns 0..t (data <= origin) and NaN-pad so that index t+h exists."""
    def f(M):
        M = np.asarray(M, float)[:, :t + 1]
        return np.pad(M, ((0, 0), (0, h)), constant_values=np.nan)
    return f


def b0_saa8(W, t, h, space, pool_scale=None):
    Z = W.Z(space)[:, :t + 1]
    Q = np.full((len(W.banks), len(U99)), np.nan)
    for i in range(len(W.banks)):
        vals = Z[i][np.isfinite(Z[i])][-SAA_WINDOW:]
        if len(vals) == SAA_WINDOW:
            Q[i] = q7(vals)
    return Q, dict(used_pool=np.zeros(len(W.banks), bool))


def _rule_baseline(W, t, h, space, F_ratio_or_usd, pool_scale):
    pad = _with_horizon(W, t, h)
    Zt = pad(W.Z(space))
    F = np.asarray(F_ratio_or_usd, float)
    centres = F[:, t + h]
    Q, used = error_quantiles(centres, _errs(Zt, F, t), pool_scale, min_own=_min_own(W))
    return Q, dict(used_pool=used)


def b1_snaive(W, t, h, space, pool_scale):
    pad = _with_horizon(W, t, h)
    F = _shift(pad(W.Z(space)), 4)          # forecast of Z_s is Z_(s-4); valid for h <= 4
    return _rule_baseline(W, t, h, space, F, pool_scale)


def b2_ratio_rw(W, t, h, space, pool_scale):
    pad = _with_horizon(W, t, h)
    R, D = pad(W.R[:, :t + 1]), pad(W.D[:, :t + 1])
    Fr = _shift(R, h)
    F = Fr if space == 'ratio' else Fr * _shift(D, h) / 1e4
    return _rule_baseline(W, t, h, space, F, pool_scale)


def b3_ses(W, t, h, space, pool_scale):
    pad = _with_horizon(W, t, h)
    L = pad(ses_levels(W.R[:, :t + 1]))
    D = pad(W.D[:, :t + 1])
    Fr = _shift(L, h)
    F = Fr if space == 'ratio' else Fr * _shift(D, h) / 1e4
    return _rule_baseline(W, t, h, space, F, pool_scale)


def b4_ar1q1(W, t, h, space, pool_scale):
    """Per bank direct h-step OLS r_(s+h) = a + b r_s + c 1[Q1(s+h)] on pairs with s+h <= t; < 8 pairs -> B2."""
    pad = _with_horizon(W, t, h)
    R, D = pad(W.R[:, :t + 1]), pad(W.D[:, :t + 1])
    Zt = pad(W.Z(space))
    nT = R.shape[1]
    q1 = np.array([(W.quarters[0] + k).quarter == 1 for k in range(nT)], float)
    n = len(W.banks)
    centres, errors, fallback = np.full(n, np.nan), [], np.zeros(n, bool)
    rw_Q, rw_info = b2_ratio_rw(W, t, h, space, pool_scale)
    for i in range(n):
        s = np.arange(0, t - h + 1)
        x, y = R[i, s], R[i, s + h]
        ok = np.isfinite(x) & np.isfinite(y)
        if ok.sum() < B4_MIN_PAIRS or not np.isfinite(R[i, t]):
            fallback[i] = True
            errors.append(np.array([]))
            continue
        cols = [np.ones(ok.sum()), x[ok]] + ([q1[s[ok] + h]] if _use_q1(W) else [])
        X = np.column_stack(cols)
        coef, *_ = np.linalg.lstsq(X, y[ok], rcond=None)
        fit = X @ coef
        cen = coef[0] + coef[1] * R[i, t] + (coef[2] * q1[t + h] if _use_q1(W) else 0.0)
        if space == 'ratio':
            centres[i] = cen
            errors.append(y[ok] - fit)
        else:
            centres[i] = cen * D[i, t] / 1e4
            errors.append(Zt[i, s[ok] + h] - fit * D[i, s[ok]] / 1e4)
    Q, used = error_quantiles(centres, errors, pool_scale, min_own=_min_own(W))
    Q[fallback] = rw_Q[fallback]
    used = np.where(fallback, rw_info['used_pool'], used)
    return Q, dict(used_pool=used, fallback=fallback)


def quantile_regression(X, y, tau):
    """Linear quantile regression by LP (HiGHS): min sum tau u+ + (1-tau) u-, X b + u+ - u- = y."""
    n, p = X.shape
    c = np.concatenate([np.zeros(p), tau * np.ones(n), (1 - tau) * np.ones(n)])
    A = np.hstack([X, np.eye(n), -np.eye(n)])
    bounds = [(None, None)] * p + [(0, None)] * (2 * n)
    res = linprog(c, A_eq=A, b_eq=y, bounds=bounds, method='highs')
    if res.status != 0:
        raise ValueError(f'quantile regression failed: {res.message}')
    return res.x[:p]


def b5_panel_qr(W, t, h, space, pool_scale, macro, train_mask=None):
    """Pooled QR on the ratio over the population, tau in U19, sorted (rearranged), interpolated to U99.

    macro: DataFrame indexed by quarter with standardisable covariate columns (quarter-t aggregates).
    train_mask: optional (n, T) bool of bank-target cells eligible for training (cross-section membership).
    Levels outside [0.05, 0.95] are held flat at the U19 end values.
    """
    pad = _with_horizon(W, t, h)
    R, D = pad(W.R[:, :t + 1]), pad(W.D[:, :t + 1])
    nT = R.shape[1]
    q1 = np.array([(W.quarters[0] + k).quarter == 1 for k in range(nT)], float)
    cols = list(macro.columns)
    Xm = np.full((nT, len(cols)), np.nan)
    for k in range(nT):
        q = W.quarters[0] + k
        if q in macro.index:
            Xm[k] = macro.loc[q, cols].to_numpy(float)
    rows, ys = [], []
    lag4 = h - 4  # r_(s+h-4) offset relative to s
    use_season = h != 4  # at h = 4, r_(t+h-4) = r_t (collinear): seasonal lag term omitted
    train_q = []
    for i in range(len(W.banks)):
        for s in range(0, t - h + 1):
            tgt = s + h
            if train_mask is not None and not train_mask[i, tgt]:
                continue
            if use_season and s + lag4 < 0:
                continue
            feats = [R[i, s]] + ([R[i, s + lag4]] if use_season else [])
            y = R[i, tgt]
            row = [*feats, *([q1[tgt]] if _use_q1(W) else []), *Xm[s]]
            if np.isfinite(y) and np.all(np.isfinite(row)):
                rows.append(row)
                ys.append(y)
                train_q.append(s)
    n = len(W.banks)
    Q = np.full((n, len(U99)), np.nan)
    if len(rows) < 3 * (len(rows[0]) + 1 if rows else 10):
        return Q, dict(used_pool=np.zeros(n, bool), n_train=len(rows), undefined=True)
    X = np.asarray(rows, float)
    y = np.asarray(ys, float)
    k0 = X.shape[1] - len(cols)
    tq = np.unique(train_q)
    mu, sd = np.nanmean(Xm[tq], axis=0), np.nanstd(Xm[tq], axis=0, ddof=1)
    sd = np.where(sd > 0, sd, 1.0)
    X[:, k0:] = (X[:, k0:] - mu) / sd
    X = np.column_stack([np.ones(len(X)), X])
    betas = np.array([quantile_regression(X, y, tau) for tau in U19])
    for i in range(n):
        feats = [R[i, t]] + ([R[i, t + lag4]] if use_season else [])
        xm = (Xm[t] - mu) / sd
        x = np.array([1.0, *feats, *([q1[t + h]] if _use_q1(W) else []), *xm])
        if not np.all(np.isfinite(x)):
            continue
        q19 = np.sort(betas @ x)
        qr = np.interp(U99, U19, q19)
        Q[i] = qr if space == 'ratio' else qr * D[i, t] / 1e4
    if space == 'usd':
        bad = ~(D[:, t] > 0)
        Q[bad] = np.nan
    return Q, dict(used_pool=np.zeros(n, bool), n_train=len(rows), undefined=False)


def b6_eb(W, t, h, space, pool_scale, residual_rule='in_sample'):
    """LMS EB via statement_forecast.eb.eb_forecast_origin (unchanged defaults, T=12), h = 1 only.

    The denominator column W.denom is passed in the `total_assets` slot of
    asset_ratio, so the EB ratio is 400 x A220_q / denom_(t-1) and the level
    forecast is the posterior-mean ratio x denom_t / 400 (prereg: "ratio x TA_t").
    Predictive spread: centre + empirical quantiles of the bank's in-sample
    one-step residuals over the EB window (12 per bank), reconstructed from the
    returned fit. Returns all-NaN with undefined=True when eb cannot be fit
    (e.g. fewer than 3 banks with a complete 13-quarter window).
    """
    n = len(W.banks)
    Q = np.full((n, len(U99)), np.nan)
    if h != 1:
        return Q, dict(used_pool=np.zeros(n, bool), undefined=True, reason='eb is one-step only')
    origin = W.quarters[t]
    panel = W.panel[W.panel.quarter.le(origin)].copy()
    panel['total_assets'] = panel[W.denom]
    try:
        fc, params = eb_forecast_origin(panel, origin, W.banks, 'trading_revenue_q')
    except ValueError as error:
        return Q, dict(used_pool=np.zeros(n, bool), undefined=True, reason=str(error))
    T = params['T']
    ratio = 400 * W.Y / np.where(W.Dlag > 0, W.Dlag, np.nan)
    S = seasonal_regressors(pd.period_range(origin - T + 1, origin + 1, freq='Q'))
    alpha = np.asarray(params['alpha'])
    centres, errors = np.full(n, np.nan), [np.array([])] * n
    pos = {b: k for k, b in enumerate(W.banks)}
    for row in fc.itertuples():
        i = pos[row.rssd_id]
        d_t = W.D[i, t]
        post = row.eb_panel * 400 / d_t - params['rho'] * ratio[i, t] - S[-1] @ alpha
        win = np.arange(t - T + 1, t + 1)
        fitted = post + params['rho'] * ratio[i, win - 1] + S[:-1] @ alpha
        resid = (ratio[i, win] - fitted)
        if space == 'ratio':
            centres[i] = row.eb_panel / d_t * 1e4
            errors[i] = resid * 1e4 / 400
        else:
            centres[i] = row.eb_panel
            errors[i] = resid * W.Dlag[i, win] / 400
    Q, used = error_quantiles(centres, errors, pool_scale)
    return Q, dict(used_pool=used, undefined=False, eb_params=params)


RIDGE_LAMBDA_GRID = 10.0 ** np.round(np.arange(-4.0, 4.0 + 1e-9, 0.05), 2)   # log10 lambda in -4..4, step 0.05


def _ridge_design(W, t, h, macro):
    """B5's T2 regressors (r_s, r_(s+h-4) unless h = 4, Q1 of the target if W.use_q1, the macro columns at s) plus a
    one-hot bank intercept for every bank in W.banks. Training pairs: banks in W.banks, targets s + h <= t, all
    entries finite (exactly B5's row rule, train_mask=None). Returns (X, y, bank_index, xrow) where xrow(i) is the
    origin regressor row of bank i (NaN entries if undefined)."""
    pad = _with_horizon(W, t, h)
    R = pad(W.R[:, :t + 1])
    nT = R.shape[1]
    q1 = np.array([(W.quarters[0] + k).quarter == 1 for k in range(nT)], float)
    cols = list(macro.columns)
    Xm = np.full((nT, len(cols)), np.nan)
    for k in range(nT):
        q = W.quarters[0] + k
        if q in macro.index and k <= t:
            Xm[k] = macro.loc[q, cols].to_numpy(float)
    lag4, use_season = h - 4, h != 4
    n = len(W.banks)

    def feats(i, s, tgt):
        return [R[i, s]] + ([R[i, s + lag4]] if use_season else []) + ([q1[tgt]] if _use_q1(W) else []) + list(Xm[s])

    rows, ys, bank = [], [], []
    for i in range(n):
        for s in range(0, t - h + 1):
            if use_season and s + lag4 < 0:
                continue
            row, y = feats(i, s, s + h), R[i, s + h]
            if np.isfinite(y) and np.all(np.isfinite(row)):
                rows.append(row)
                ys.append(y)
                bank.append(i)
    k = len(rows[0]) if rows else 0
    X = np.zeros((len(rows), k + n))
    if rows:
        X[:, :k] = np.asarray(rows, float)
        X[np.arange(len(rows)), k + np.asarray(bank)] = 1.0

    def xrow(i):
        x = np.zeros(k + n)
        x[:k] = feats(i, t, t + h)
        x[k + i] = 1.0
        return x
    return X, np.asarray(ys, float), np.asarray(bank, int), xrow


def _ridge_prep(X):
    """glmnet convention: every non-intercept column standardised on the training rows (mean, population sd);
    zero-variance columns (e.g. a bank without training rows) are dropped."""
    mu, sd = X.mean(axis=0), X.std(axis=0)
    keep = sd > 0
    return mu, sd, keep


def _ridge_svd(X, y):
    mu, sd, keep = _ridge_prep(X)
    Z = (X[:, keep] - mu[keep]) / sd[keep]
    ybar = float(y.mean())
    U, d, Vt = np.linalg.svd(Z, full_matrices=False)
    return dict(mu=mu, sd=sd, keep=keep, ybar=ybar, U=U, d=d, Vt=Vt, uty=U.T @ (y - ybar))


def ridge_gcv(X, y, grid=RIDGE_LAMBDA_GRID):
    """Objective (1/n) RSS + lambda ||beta||^2 on standardised columns, unpenalised global intercept.
    GCV(lambda) = n RSS / (n - df)^2 with df = 1 + sum d_j^2 / (d_j^2 + n lambda). Returns (lambda*, table)."""
    n = len(y)
    f = _ridge_svd(X, y)
    yc = y - f['ybar']
    out = []
    for lam in grid:
        shrink = f['d'] ** 2 / (f['d'] ** 2 + n * lam)
        fitted = f['U'] @ (shrink * f['uty'])
        rss = float(np.sum((yc - fitted) ** 2))
        df = 1.0 + float(shrink.sum())
        out.append((float(lam), rss, df, n * rss / (n - df) ** 2))
    tab = np.array(out)
    k = int(np.argmin(tab[:, 3]))
    return float(tab[k, 0]), dict(gcv_min=float(tab[k, 3]), df=float(tab[k, 2]), n_train=int(n),
                                  n_columns=int(f['keep'].sum()), grid_min=float(grid[0]), grid_max=float(grid[-1]),
                                  at_grid_boundary=bool(k in (0, len(grid) - 1)))


def ridge_gcv_lambda(W, t, h, macro, grid=RIDGE_LAMBDA_GRID):
    """lambda by GCV on the pairs available at origin index t (prereg §3: once, on burn-in; the caller freezes it)."""
    X, y, _, _ = _ridge_design(W, t, h, macro)
    if len(y) < 3 * (X.shape[1] + 1):
        raise ValueError(f'ridge GCV: {len(y)} training rows for {X.shape[1]} columns')
    return ridge_gcv(X, y, grid)


def ridge_point(W, t, h, macro, lam):
    """Pooled ridge point forecast (secondary MAE; prereg §3 '(pt)'): B5 regressors plus bank intercepts, fitted on
    the pairs available at origin index t with the frozen lambda. Returns (centres in ratio space, info); $ centre
    = ratio x D_(i,t) / 1e4 (as B5). Banks without a finite origin regressor row get NaN."""
    n = len(W.banks)
    out = np.full(n, np.nan)
    X, y, bank, xrow = _ridge_design(W, t, h, macro)
    if len(y) < 3 * (X.shape[1] + 1):
        return out, dict(n_train=int(len(y)), undefined=True)
    f = _ridge_svd(X, y)
    m = len(y)
    beta = f['Vt'].T @ (f['d'] / (f['d'] ** 2 + m * lam) * f['uty'])
    keep = f['keep']
    for i in range(n):
        x = xrow(i)
        if np.all(np.isfinite(x)):
            out[i] = f['ybar'] + ((x[keep] - f['mu'][keep]) / f['sd'][keep]) @ beta
    return out, dict(n_train=int(m), undefined=False, banks_with_training_rows=int(len(np.unique(bank))))


def run_members(W, t, h, space, pool_scale, macro, train_mask=None, members=MEMBERS):
    """All requested members at origin index t; returns {member: (Q, info)}."""
    out = {}
    for m in members:
        if m == 'B0':
            out[m] = b0_saa8(W, t, h, space)
        elif m == 'B1':
            out[m] = b1_snaive(W, t, h, space, pool_scale)
        elif m == 'B2':
            out[m] = b2_ratio_rw(W, t, h, space, pool_scale)
        elif m == 'B3':
            out[m] = b3_ses(W, t, h, space, pool_scale)
        elif m == 'B4':
            out[m] = b4_ar1q1(W, t, h, space, pool_scale)
        elif m == 'B5':
            out[m] = b5_panel_qr(W, t, h, space, pool_scale, macro, train_mask)
        elif m == 'B6':
            out[m] = b6_eb(W, t, h, space, pool_scale)
    return out
