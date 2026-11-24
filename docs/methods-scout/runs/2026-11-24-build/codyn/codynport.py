"""Independent NumPy port of codyn 2.0.6 metrics (variance_ratio, rate_change,
rank_shift). Written from the R source semantics, validated against R as an oracle.

Input convention: abundance matrix X of shape (T, S), rows sorted by time,
columns = species. NaN = species has no record at that time (absent row in
codyn's long format). transpose_community fills absences with 0 for VR and
rate_change; rank_shift uses presence (record exists, even if abundance 0).
"""
import numpy as np


def _fill0(X):
    return np.nan_to_num(np.asarray(X, float), nan=0.0)


def variance_ratio(X):
    """Schluter VR = sum(cov matrix) / sum(var), sample (ddof=1) moments."""
    X = _fill0(X)
    C = np.cov(X, rowvar=False, ddof=1)
    return float(C.sum() / np.trace(C))


def cyclic_shift(X, rng):
    """Rotate each column by an independent uniform shift in 0..T-1
    (matches permute::shuffleSeries)."""
    X = np.asarray(X, float)
    T, S = X.shape
    out = np.empty_like(X)
    for j, k in enumerate(rng.integers(0, T, S)):
        out[:, j] = np.roll(X[:, j], -k)
    return out


def variance_ratio_null(X, nboot=999, seed=0, level=0.95):
    """Hallett cyclic-shift null for VR (vectorised moments); deterministic via seed."""
    X = _fill0(X)
    T, S = X.shape
    rng = np.random.default_rng(seed)
    idx = (np.arange(T)[:, None] + rng.integers(0, T, (nboot, S))[:, None, :]) % T
    B = X[idx, np.arange(S)[None, None, :]]          # (nboot, T, S)
    B = B - B.mean(axis=1, keepdims=True)
    # sum of cov = var(row-sum); sum of var = sum of column variances
    num = (B.sum(axis=2) ** 2).sum(axis=1)
    den = (B ** 2).sum(axis=(1, 2))
    null = num / den
    lo = (1 - level) / 2
    return dict(lowerCI=float(np.quantile(null, lo)), upperCI=float(np.quantile(null, 1 - lo)),
                nullmean=float(null.mean()), null=null)


def lagged_distances(X):
    """(interval, euclidean distance) for all time pairs, by index lag."""
    X = _fill0(X)
    T = X.shape[0]
    D = np.sqrt(((X[:, None, :] - X[None, :, :]) ** 2).sum(-1))
    i, j = np.triu_indices(T, 1)
    return j - i, D[i, j]


def rate_change(X):
    lag, d = lagged_distances(X)
    return float(np.polyfit(lag, d, 1)[0])


def _rank_avg(v):
    from scipy.stats import rankdata
    return rankdata(v, method="average")


def rank_shift(X):
    """MRS per consecutive pair: species with a record at both times; ranks
    (ascending, average ties) within that common set; mean |rank diff|.
    Returns array of length T-1 (NaN if no common species)."""
    X = np.asarray(X, float)
    out = np.full(X.shape[0] - 1, np.nan)
    for t in range(X.shape[0] - 1):
        m = ~np.isnan(X[t]) & ~np.isnan(X[t + 1])
        if m.any():
            out[t] = np.abs(_rank_avg(X[t + 1, m]) - _rank_avg(X[t, m])).mean()
    return out


def mean_rank_shift(X):
    return float(np.nanmean(rank_shift(X)))


def rank_clocks(X, descending=True):
    """Ranks per time per species (1 = largest by default; average ties)."""
    X = _fill0(X)
    return np.vstack([_rank_avg(-r if descending else r) for r in X])
