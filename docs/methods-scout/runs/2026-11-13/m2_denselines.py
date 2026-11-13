"""Method 2: DenseLines on SYNTHETIC mock ZBB programs (Corning_mock, MorganStanley_mock).
Answer-key files are used only to score / reveal, never to build the charts' inputs."""
import json, sys, re, numpy as np, pandas as pd
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0, '/workspace/scout/1113/runs'); from denselines import density, to_pixels
D = '/workspace/scout/1113/data/'; SRC = '/workspace/q2-mock-zbb/output/'; O = '/workspace/scout/1113/out/'
W, H = 500, 300
res = {}; arrays = {}
def paths(F, yrs, cols):
    Y = F[[f'y{t}' for t in yrs]].values
    keep = (~np.isnan(Y)).sum(1) >= 2
    return Y, keep
def build(V, yrs, lo, hi, weights=None, gap_safe=True, norm=True):
    xs_col = np.round(np.arange(len(yrs)) * (W - 1) / (len(yrs) - 1)).astype(int)
    ser, xs = [], []
    for v in V:
        m = ~np.isnan(v)
        ser.append(to_pixels(v[m], lo, hi, H - 1)); xs.append(xs_col[m])
    if norm: return density(ser, W, H, xs=xs, gap_safe=gap_safe, weights=weights), ser, xs
    # unnormalised: binary images summed (count of lines through each pixel, steep lines count many times)
    one = density(ser, W, H, xs=xs, gap_safe=True, weights=None)  # placeholder to get shape
    return None, ser, xs
def unnormalised(ser, xs):
    from denselines import _bresenham
    agg = np.zeros(W * H)
    for c0 in range(0, len(ser), 2000):
        S = ser[c0:c0 + 2000]; X = xs[c0:c0 + 2000]
        a = [np.asarray(x[:-1]) for x in X]; b = [np.asarray(s[:-1]) for s in S]; c = [np.asarray(x[1:]) for x in X]; d = [np.asarray(s[1:]) for s in S]
        sid = np.concatenate([np.full(len(s) - 1, j) for j, s in enumerate(S)])
        gi, px, py = _bresenham(np.concatenate(a), np.concatenate(b), np.concatenate(c), np.concatenate(d))
        ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        key = np.unique((sid[gi[ok]] * W + px[ok]) * H + py[ok]); py2 = key % H; px2 = (key // H) % W
        agg += np.bincount(py2 * W + px2, minlength=W * H)
    return agg.reshape(H, W)
def tv(A, B):  # mean over columns of total-variation distance between column distributions
    a = A / np.maximum(A.sum(0, keepdims=True), 1e-12); b = B / np.maximum(B.sum(0, keepdims=True), 1e-12)
    m = (A.sum(0) > 0) & (B.sum(0) > 0); return float(0.5 * np.abs(a - b)[:, m].sum(0).mean())
def emd(A, B, lo, hi):  # mean over columns of 1-D Wasserstein-1 between column distributions, in log units
    a = A / np.maximum(A.sum(0, keepdims=True), 1e-12); b = B / np.maximum(B.sum(0, keepdims=True), 1e-12)
    m = (A.sum(0) > 0) & (B.sum(0) > 0); px = (hi - lo) / (H - 1)
    return float((np.abs(np.cumsum(a, 0) - np.cumsum(b, 0)).sum(0)[m] * px).mean())
for firm in ['Corning_mock', 'MorganStanley_mock']:
    F = pd.read_csv(D + f'{firm}_features.csv'); P = pd.read_csv(SRC + f'{firm}/programs.csv')
    L = pd.read_csv(D + f'{firm}_KEY_labels.csv').set_index('program_id').loc[F.program_id]
    K = pd.read_csv(D + f'{firm}_KEY_true_levels.csv')
    yrs = sorted(int(c[1:]) for c in F.columns if re.fullmatch(r'y\d{4}', c))
    Y, keep = paths(F, yrs, None); F = F[keep].reset_index(drop=True); Y = Y[keep]; L = L[keep]
    V = Y - np.nanmean(Y, 1, keepdims=True)                                  # index each program to its own mean (log)
    lo, hi = np.nanpercentile(V, 0.5) - 0.02, np.nanpercentile(V, 99.5) + 0.02
    Dn, ser, xs = build(V, yrs, lo, hi)
    Du = unnormalised(ser, xs)
    # ---- D1: ink share of the noisiest decile (by observable sigma_hat), normalised vs not
    top = F.sigma.values >= np.quantile(F.sigma.values, 0.9)
    sub = [s for s, t in zip(ser, top) if t]; subx = [x for x, t in zip(xs, top) if t]
    ink_u = unnormalised(sub, subx).sum() / Du.sum()
    ink_n = density(sub, W, H, xs=subx, gap_safe=True).sum() / Dn.sum()
    cover_share = sum(x[-1] - x[0] + 1 for x in subx) / sum(x[-1] - x[0] + 1 for x in xs)
    # ---- truth comparison: same chart built from TRUE paths (answer key) — which noisy chart is closer?
    T = K.pivot(index='program_id', columns='fiscal_year', values='true_usd').reindex(F.program_id)[yrs].values
    T = np.where(np.isnan(Y), np.nan, np.log(T)); VT = T - np.nanmean(T, 1, keepdims=True)
    DnT, serT, xsT = build(VT, yrs, lo, hi); DuT = unnormalised(serT, xsT)
    res[firm] = {'n_series': len(F), 'years': yrs, 'y_range_log': [float(lo), float(hi)],
        'D1': {'noisy_decile_share_of_series': float(top.mean()), 'noisy_decile_share_of_covered_columns': float(cover_share),
               'noisy_decile_ink_unnormalised': float(ink_u), 'noisy_decile_ink_denselines': float(ink_n),
               'tv_to_truth_unnormalised': tv(Du, DuT), 'tv_to_truth_denselines': tv(Dn, DnT),
               'w1_to_truth_unnormalised': emd(Du, DuT, lo, hi), 'w1_to_truth_denselines': emd(Dn, DnT, lo, hi)}}
    # ---- D2: residual DenseLines + branch brush (label-free), scored vs answer-key clusters
    R = V - np.nanmedian(V, 0, keepdims=True)
    rlo, rhi = np.nanpercentile(R, 0.5) - 0.02, np.nanpercentile(R, 99.5) + 0.02
    DR, serR, xsR = build(R, yrs, rlo, rhi)
    col = W - 1; prof = gaussian_filter1d(DR[:, col], 4)
    pk = [i for i in range(1, H - 1) if prof[i] > prof[i - 1] and prof[i] >= prof[i + 1] and prof[i] > 0.02 * prof.max()]
    main = int(np.argmax(prof)); upper = [p for p in pk if p > main + 8]
    brush = None
    if upper:
        u = max(upper, key=lambda p: prof[p]); valley = main + int(np.argmin(prof[main:u + 1])); brush = rlo + valley / (H - 1) * (rhi - rlo)
    r25 = R[:, -1]
    clus = L.cluster.fillna('none').values
    co = [c['cluster_id'] for c in json.load(open(D + f'{firm}_KEY_summary.json'))['clusters'] if c['type'] == 'co_move']
    desc = P.set_index('program_id').loc[F.program_id, 'description'].str.lower().values
    kw = {'Corning_mock': r'generative-ai|datacenter|data center|hyperscale', 'MorganStanley_mock': r'equity market|market activity|trading volume|fee-based|advisory asset|managed account'}[firm]
    txt = np.array([bool(re.search(kw, d)) for d in desc])
    def pr(sel, truth): return {'selected': int(sel.sum()), 'hits': int((sel & truth).sum()), 'precision': float((sel & truth).sum() / max(sel.sum(), 1)), 'recall': float((sel & truth).sum() / truth.sum())}
    d2 = {'peaks_px': pk, 'main_px': main, 'brush_threshold_log': brush, 'keyword_regex': kw, 'clusters': {}}
    for c in co:
        truth = clus == c
        d2['clusters'][c] = {'n_members': int(truth.sum()), 'keyword_text': pr(txt, truth),
            'brush': pr(r25 > brush, truth) if brush is not None else None,
            'brush_or_text': pr((r25 > brush) | txt, truth) if brush is not None else None,
            'top_k_by_residual': pr(r25 >= np.sort(r25[~np.isnan(r25)])[::-1][truth.sum() - 1], truth)}
    res[firm]['D2'] = d2
    # ---- D3: start/stop programs — reference NaN behaviour vs gap-safe, live-normalised
    partial = np.isnan(Y).any(1)
    Dref = density(ser, W, H, xs=xs, gap_safe=False)
    live = np.array([(np.array([x[0] <= c <= x[-1] for x in xs])).sum() for c in range(W)])
    res[firm]['D3'] = {'partial_span_series': int(partial.sum()), 'reference_nan_columns': int(np.isnan(Dref).any(0).sum()), 'width': W,
                       'live_min': int(live.min()), 'live_max': int(live.max())}
    # entrants vs incumbents
    first = np.array([int(np.argmax(~np.isnan(v))) for v in Y])
    ent = first > 0
    Dent = density([s for s, e in zip(ser, ent) if e], W, H, xs=[x for x, e in zip(xs, ent) if e], gap_safe=True) if ent.any() else np.zeros((H, W))
    arrays[firm] = dict(Dn=Dn, Du=Du, DnT=DnT, DR=DR, prof=prof, live=live, Dent=Dent, lo=lo, hi=hi, rlo=rlo, rhi=rhi, brush=brush if brush is not None else np.nan,
                        V=V, R=R, clus=clus, txt=txt, ent=ent, sigma=F.sigma.values, seg=F.segment.values, Dref_nan=np.isnan(Dref).any(0))
    # small multiples by stated segment and by answer-key cluster (reveal)
    sm = {}
    for kind, labs in [('segment', F.segment.values), ('cluster', clus)]:
        for g in pd.unique(labs):
            m = labs == g
            if m.sum() < 15: continue
            sm[f'{kind}:{g}'] = density([s for s, t in zip(serR, m) if t], W, H, xs=[x for x, t in zip(xsR, m) if t], gap_safe=True)
    arrays[firm]['sm'] = sm
    print(firm, json.dumps(res[firm], indent=1, default=float))
json.dump(res, open(O + 'm2_results.json', 'w'), indent=1, default=float)
np.save(O + 'm2_arrays.npy', arrays, allow_pickle=True)
