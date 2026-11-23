"""DenseLines #56 build step 3, exactly runs/2026-11-23-build/PREREG-D3.md. SYNTHETIC mocks regenerated with seed 20261123.
Chart construction copied unchanged from runs/2026-11-13/m2_denselines.py (build / unnormalised / tv / emd)."""
import json, os, sys, re, numpy as np, pandas as pd, diptest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '2026-11-13')); from denselines import density, to_pixels, _bresenham
D = '/workspace/scout/1123-build/data/'; W, H = 500, 300; SEED = 20261123
def build(V, yrs, lo, hi):
    xs_col = np.round(np.arange(len(yrs)) * (W - 1) / (len(yrs) - 1)).astype(int)
    ser, xs = [], []
    for v in V:
        m = ~np.isnan(v); ser.append(to_pixels(v[m], lo, hi, H - 1)); xs.append(xs_col[m])
    return density(ser, W, H, xs=xs, gap_safe=True), ser, xs
def unnormalised(ser, xs):
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
def tv(A, B):
    a = A / np.maximum(A.sum(0, keepdims=True), 1e-12); b = B / np.maximum(B.sum(0, keepdims=True), 1e-12)
    m = (A.sum(0) > 0) & (B.sum(0) > 0); return float(0.5 * np.abs(a - b)[:, m].sum(0).mean())
def emd(A, B, lo, hi):
    a = A / np.maximum(A.sum(0, keepdims=True), 1e-12); b = B / np.maximum(B.sum(0, keepdims=True), 1e-12)
    m = (A.sum(0) > 0) & (B.sum(0) > 0); px = (hi - lo) / (H - 1)
    return float((np.abs(np.cumsum(a, 0) - np.cumsum(b, 0)).sum(0)[m] * px).mean())
def resid_last(Y):
    V = Y - np.nanmean(Y, 1, keepdims=True); R = V - np.nanmedian(V, 0, keepdims=True)
    r = R[:, -1]; return r[~np.isnan(r)]
out = {'prereg': 'runs/2026-11-23-build/PREREG-D3.md', 'data': 'SYNTHETIC Q2 mock ZBB regenerated with seed 20261123', 'mocks': {}}
for firm in ['Corning_mock', 'MorganStanley_mock']:
    F = pd.read_csv(D + f'{firm}_features.csv'); K = pd.read_csv(D + f'{firm}_KEY_true_levels.csv')
    yrs = sorted(int(c[1:]) for c in F.columns if re.fullmatch(r'y\d{4}', c))
    Y = F[[f'y{t}' for t in yrs]].values; keep = (~np.isnan(Y)).sum(1) >= 2; F = F[keep].reset_index(drop=True); Y = Y[keep]
    V = Y - np.nanmean(Y, 1, keepdims=True)
    lo, hi = np.nanpercentile(V, 0.5) - 0.02, np.nanpercentile(V, 99.5) + 0.02
    Dn, ser, xs = build(V, yrs, lo, hi); Du = unnormalised(ser, xs)
    T = K.pivot(index='program_id', columns='fiscal_year', values='true_usd').reindex(F.program_id)[yrs].values
    T = np.where(np.isnan(Y), np.nan, np.log(T)); VT = T - np.nanmean(T, 1, keepdims=True)
    DnT, serT, xsT = build(VT, yrs, lo, hi); DuT = unnormalised(serT, xsT)
    m = {'n_series': int(len(F)), 'years': yrs,
         'w1_to_truth_denselines': emd(Dn, DnT, lo, hi), 'w1_to_truth_unnormalised': emd(Du, DuT, lo, hi),
         'tv_to_truth_denselines': tv(Dn, DnT), 'tv_to_truth_unnormalised': tv(Du, DuT)}
    m['clusters_on_pass'] = m['w1_to_truth_denselines'] < m['w1_to_truth_unnormalised']
    d0, p0 = diptest.diptest(resid_last(Y)); m['dip_unshuffled'] = {'dip': float(d0), 'p': float(p0)}
    ps = []
    for k in range(200):
        rng = np.random.default_rng(SEED + k); Ys = Y.copy()
        for i in range(len(Ys)):
            o = np.nonzero(~np.isnan(Ys[i]))[0]; Ys[i, o] = Ys[i, o][rng.permutation(len(o))]
        ps.append(float(diptest.diptest(resid_last(Ys))[1]))
    ps = np.array(ps); m['shuffles'] = 200; m['shuffle_flags_p_lt_0.05'] = int((ps < 0.05).sum())
    m['shuffle_flag_rate'] = float((ps < 0.05).mean()); m['shuffle_p_quantiles'] = [float(q) for q in np.quantile(ps, [0.05, 0.5, 0.95])]
    m['clusters_off_pass'] = m['shuffle_flag_rate'] <= 0.05
    out['mocks'][firm] = m; print(firm, json.dumps(m, indent=1), flush=True)
out['step3_pass'] = all(v['clusters_on_pass'] and v['clusters_off_pass'] for v in out['mocks'].values())
out['kill_triggered'] = not all(v['clusters_on_pass'] for v in out['mocks'].values())
json.dump(out, open(os.path.join(HERE, 'd3_results.json'), 'w'), indent=1); print('step3_pass', out['step3_pass'], 'kill', out['kill_triggered'])
