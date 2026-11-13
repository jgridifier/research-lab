"""Faithful NumPy port of DenseLines (Moritz & Fisher, arXiv:1808.06019), checked against the authors'
Rust reference (github.com/domoritz/line-density-rust @083890c, src/main.rs run_series + sum_images).

Reference semantics reproduced exactly:
  * each segment is rasterised with imageproc 0.25 BresenhamLineIter (f32 error term, truncating casts),
    pixels outside the canvas are dropped; a pixel is SET to 1 (not incremented), so shared endpoints count once;
  * each series' binary image is normalised column-by-column by its own column sum (arc-length normalisation);
  * per-series images are summed.
Two documented extensions (off by default so the default path matches the reference):
  * `xs`: vertex x-positions (the reference fixes vertex spacing at 1 column);
  * `gap_safe=True`: columns a series does not cover contribute 0 (the reference divides 0/0 -> NaN,
    which poisons the whole column of the aggregate).
"""
import numpy as np

def _bresenham(x0, y0, x1, y1):
    """Vectorised imageproc BresenhamLineIter over many segments. Inputs are float32 arrays.
    Returns (seg_index, px, py) int arrays for every emitted point."""
    x0 = x0.astype(np.float32); y0 = y0.astype(np.float32); x1 = x1.astype(np.float32); y1 = y1.astype(np.float32)
    steep = np.abs(y1 - y0) > np.abs(x1 - x0)
    X0 = np.where(steep, y0, x0); Y0 = np.where(steep, x0, y0); X1 = np.where(steep, y1, x1); Y1 = np.where(steep, x1, y1)
    sw = X0 > X1
    X0, X1 = np.where(sw, X1, X0), np.where(sw, X0, X1); Y0, Y1 = np.where(sw, Y1, Y0), np.where(sw, Y0, Y1)
    dx = (X1 - X0).astype(np.float32); dy = np.abs(Y1 - Y0).astype(np.float32)
    x = X0.astype(np.int64); y = Y0.astype(np.int64)          # Rust `as i32` truncates toward zero
    err = (dx / np.float32(2)).astype(np.float32); endx = X1.astype(np.int64)
    ystep = np.where(Y0 < Y1, 1, -1).astype(np.int64)
    out_i, out_x, out_y = [], [], []
    idx = np.arange(len(x))
    while idx.size:
        live = x[idx] <= endx[idx]; idx = idx[live]
        if not idx.size: break
        st = steep[idx]
        out_i.append(idx); out_x.append(np.where(st, y[idx], x[idx])); out_y.append(np.where(st, x[idx], y[idx]))
        x[idx] += 1
        e = (err[idx] - dy[idx]).astype(np.float32)
        neg = e < 0
        y[idx] += np.where(neg, ystep[idx], 0)
        err[idx] = np.where(neg, (e + dx[idx]).astype(np.float32), e)
    return np.concatenate(out_i), np.concatenate(out_x), np.concatenate(out_y)

def density(series, width, height, xs=None, gap_safe=False, chunk=20000, weights=None, dtype=np.float64):
    """series: list/array of 1-D integer pixel arrays (y per vertex). Returns (height, width) density."""
    agg = np.zeros(width * height, dtype=dtype)
    nan_cols = np.zeros(width, bool)
    for c0 in range(0, len(series), chunk):
        S = series[c0:c0 + chunk]
        sx0, sy0, sx1, sy1, sid = [], [], [], [], []
        for j, s in enumerate(S):
            s = np.asarray(s, np.float32)
            if len(s) < 2: continue
            vx = np.arange(len(s), dtype=np.float32) if xs is None else np.asarray(xs[c0 + j], np.float32)
            sx0.append(vx[:-1]); sy0.append(s[:-1]); sx1.append(vx[1:]); sy1.append(s[1:]); sid.append(np.full(len(s) - 1, j))
        if not sid: continue
        sid = np.concatenate(sid)
        gi, px, py = _bresenham(np.concatenate(sx0), np.concatenate(sy0), np.concatenate(sx1), np.concatenate(sy1))
        ok = (px >= 0) & (px < width) & (py >= 0) & (py < height)
        ser = sid[gi[ok]]; px = px[ok]; py = py[ok]
        key = np.unique((ser * width + px) * height + py)          # set-to-1 semantics: dedupe pixels per series
        sc = key // height; py = key % height; px = sc % width
        cnt = np.bincount(sc, minlength=len(S) * width)
        w = 1.0 / cnt[sc]
        if weights is not None: w = w * np.asarray(weights[c0:c0 + chunk])[sc // width]
        agg += np.bincount(py * width + px, weights=w, minlength=width * height)
        if not gap_safe:  # reference behaviour: any series missing a column makes that column NaN
            covered = cnt.reshape(len(S), width) > 0
            used = np.array([len(s) >= 2 for s in S])
            nan_cols |= (~covered[used]).any(0)
    D = agg.reshape(height, width)
    if not gap_safe and nan_cols.any(): D[:, nan_cols] = np.nan
    return D

def to_pixels(v, lo, hi, height):
    """Map values to integer rows the way the reference does (clamp, truncate to u32)."""
    p = (np.asarray(v, float) - lo) / (hi - lo) * height
    return np.clip(p, 0, height).astype(np.int64)
