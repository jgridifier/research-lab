"""
Challenger overlay on a frozen champion. ~12 minutes.

old: 48 quarters in a low-rate era (market rate m in 0-2%), new: 28 quarters
with m rising 2 -> 5.5%. Column dep = deposit rate paid (%).
The champion, champion(m, w) = w[0] + w[1]*m, was fit on old and is FROZEN
(owned by another team). It under-predicts deposit costs at high rates.

Build an additive overlay delta(m) = sum_k v_k * max(m - knot_k, 0),
knots = KNOTS = [2, 3, 4, 5], fit by ridge on the champion's residuals:
1. hinge_basis(m) -> (n, 4) array; fit_overlay(m, resid, lam) -> v.
2. Hold out the last 8 quarters of `new`. Choose lam from LAMS using a
   time-ordered validation split inside the remaining new data (fit on the
   earlier part, score on the last 4 quarters). Refit with that lam.
3. Report holdout RMSE (champion vs champion + overlay) and the largest
   change the overlay makes on the old-regime data.
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


LAMS = np.logspace(-4, 2, 25)


def hinge_basis(m):
    raise NotImplementedError


def fit_overlay(m, resid, lam):
    raise NotImplementedError


def build_challenger(old, new, w, n_hold: int = 8) -> dict:
    """Return dict with keys lam, v, rmse_champion, rmse_challenger, max_change_old."""
    raise NotImplementedError


def check():
    old, new, w = make_data()
    print("champion w =", np.round(w, 3))
    assert hinge_basis(np.array([1.0, 3.5])).shape == (2, 4)
    rep = build_challenger(old, new, w)
    print({k: (np.round(v, 3) if not isinstance(v, float) else round(v, 4)) for k, v in rep.items()})
    assert rep["rmse_challenger"] < 0.5 * rep["rmse_champion"]
    assert rep["max_change_old"] < 1e-12, "the overlay must leave the old regime unchanged"
    assert rep["lam"] in LAMS
    print("checks passed")


if __name__ == "__main__":
    check()
