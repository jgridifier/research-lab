"""
Problem 3 (core, ~12 min): a challenger overlay on a FROZEN champion model.

The champion deposit-cost model was fit in a low-rate era (market rate 0-2%):
    deposit_rate_hat = w0 + w1 * market_rate
It belongs to another team and cannot be re-fit. Rates are now 2-5.5%, and
deposit pass-through ("beta") rises at higher rates, so the champion
under-predicts deposit costs. Build a small additive overlay
    delta(m) = sum_k v_k * max(m - knot_k, 0),   knots = 2, 3, 4, 5
fit by ridge on the champion's residuals over the recent window, so that:
  - it improves the out-of-time holdout (last 8 quarters),
  - it leaves the champion EXACTLY unchanged in the old regime (m <= 2),
  - the ridge penalty is chosen on a time-ordered validation split
    (never shuffled K-fold).
Only numpy required; scikit-learn is used for a cross-check if installed.
"""
import numpy as np
import pandas as pd

KNOTS = np.array([2.0, 3.0, 4.0, 5.0])


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def true_deposit_rate(m):
    m = np.asarray(m, float)
    return 0.05 + 0.25 * m + 0.35 * np.maximum(m - 2.5, 0) + 0.15 * np.maximum(m - 4.0, 0)


def make_data(seed: int = 3):
    """Returns (old, new, champion_w).
    old: 48 quarters, market rate 0-2%; new: 28 quarters, rate climbing 2 -> 5.5%."""
    rng = np.random.default_rng(seed)
    m_old = np.clip(1.0 + np.cumsum(rng.normal(0, 0.15, 48)), 0.0, 2.0)
    m_new = np.linspace(2.0, 5.5, 28) + rng.normal(0, 0.1, 28)
    noise = 0.05
    old = pd.DataFrame({"m": m_old, "dep": true_deposit_rate(m_old) + rng.normal(0, noise, 48)},
                       index=pd.period_range("2010Q1", periods=48, freq="Q"))
    new = pd.DataFrame({"m": m_new, "dep": true_deposit_rate(m_new) + rng.normal(0, noise, 28)},
                       index=pd.period_range("2022Q1", periods=28, freq="Q"))
    X = np.column_stack([np.ones(48), old.m])
    champion_w = np.linalg.lstsq(X, old.dep.to_numpy(), rcond=None)[0]   # frozen
    return old, new, champion_w


def champion(m, w):
    return w[0] + w[1] * np.asarray(m, float)


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def hinge_basis(m, knots=KNOTS):
    return np.maximum(np.asarray(m, float)[:, None] - knots[None, :], 0.0)


def fit_overlay(m, resid, lam):
    """Ridge without intercept: v = (Phi'Phi + lam I)^{-1} Phi' r.
    No intercept on purpose: an intercept would shift the old regime too."""
    Phi = hinge_basis(m)
    return np.linalg.solve(Phi.T @ Phi + lam * np.eye(Phi.shape[1]), Phi.T @ resid)


def overlay(m, v):
    return hinge_basis(m) @ v


def rmse(e):
    return float(np.sqrt(np.mean(np.square(e))))


def choose_lambda(train: pd.DataFrame, w, lams, n_val: int = 4):
    """Time-ordered split: fit on the first part of train, score on the last n_val."""
    fit, val = train.iloc[:-n_val], train.iloc[-n_val:]
    r_fit = fit.dep.to_numpy() - champion(fit.m, w)
    scores = []
    for lam in lams:
        v = fit_overlay(fit.m.to_numpy(), r_fit, lam)
        pred = champion(val.m, w) + overlay(val.m.to_numpy(), v)
        scores.append(rmse(val.dep.to_numpy() - pred))
    return float(lams[int(np.argmin(scores))]), np.array(scores)


def build_challenger(old, new, w, n_hold: int = 8, lams=None):
    lams = np.logspace(-4, 2, 25) if lams is None else lams
    train, hold = new.iloc[:-n_hold], new.iloc[-n_hold:]
    lam, scores = choose_lambda(train, w, lams)
    r = train.dep.to_numpy() - champion(train.m, w)
    v = fit_overlay(train.m.to_numpy(), r, lam)          # refit on all of train
    champ_h = champion(hold.m, w)
    chall_h = champ_h + overlay(hold.m.to_numpy(), v)
    report = dict(lam=lam, v=v,
                  rmse_champion=rmse(hold.dep - champ_h),
                  rmse_challenger=rmse(hold.dep - chall_h),
                  max_change_old=float(np.abs(overlay(old.m.to_numpy(), v)).max()))
    return report


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    old, new, w = make_data()
    # champion is a decent fit in its own era but biased low at high rates
    assert rmse(old.dep - champion(old.m, w)) < 0.08
    assert (new.dep.iloc[-8:] - champion(new.m.iloc[-8:], w)).mean() > 0.5
    rep = build_challenger(old, new, w)
    # 1. the overlay improves the out-of-time holdout a lot
    assert rep["rmse_challenger"] < 0.5 * rep["rmse_champion"], rep
    # 2. it leaves the old regime exactly unchanged (all hinges are zero for m <= 2)
    assert rep["max_change_old"] == 0.0
    # 3. ridge limits: lam -> infinity gives the champion, lam -> 0 gives OLS on residuals
    train = new.iloc[:-8]
    r = train.dep.to_numpy() - champion(train.m, w)
    assert np.abs(fit_overlay(train.m.to_numpy(), r, 1e12)).max() < 1e-9
    Phi = hinge_basis(train.m.to_numpy())
    v_ols = np.linalg.lstsq(Phi, r, rcond=None)[0]
    assert np.allclose(fit_overlay(train.m.to_numpy(), r, 1e-12), v_ols, atol=1e-5)
    # 4. lambda was chosen on a time-ordered split (validation is the latest data)
    lam, scores = choose_lambda(train, w, np.logspace(-4, 2, 25))
    assert np.isclose(lam, rep["lam"]) and np.isfinite(scores).all()
    # 5. scikit-learn cross-check, if installed
    try:
        from sklearn.linear_model import Ridge
        sk = Ridge(alpha=rep["lam"], fit_intercept=False).fit(Phi, r).coef_
        assert np.allclose(sk, rep["v"], atol=1e-8)
        sk_ok = True
    except ImportError:
        sk_ok = False
    print("p3 OK  | lam = %.4g | holdout RMSE champion %.3f -> challenger %.3f | old-regime max change %.1f | sklearn check: %s"
          % (rep["lam"], rep["rmse_champion"], rep["rmse_challenger"], rep["max_change_old"], sk_ok))
    print("overlay coefficients on hinges at", KNOTS.tolist(), ":", np.round(rep["v"], 3).tolist())


if __name__ == "__main__":
    _tests()
