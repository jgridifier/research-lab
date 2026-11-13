"""Sensitivity of the label-free 'branch brush' in residual DenseLines to the smoothing bandwidth and to the
number of columns brushed. Scored against answer-key clusters (SYNTHETIC mocks)."""
import numpy as np, json
from scipy.ndimage import gaussian_filter1d
A = np.load('/workspace/scout/1113/out/m2_arrays.npy', allow_pickle=True).item(); W, H = 500, 300; out = []
for firm, c in [('Corning_mock', 'ai_datacenter_demand'), ('MorganStanley_mock', 'equity_market_activity'), ('MorganStanley_mock', 'wealth_fee_based_growth')]:
    a = A[firm]; DR = a['DR']; R = a['R']; T = R.shape[1]; cols = np.round(np.arange(T) * (W - 1) / (T - 1)).astype(int); truth = a['clus'] == c
    for sm in [2, 4, 6, 8]:
        th = []
        for cc in cols:
            prof = gaussian_filter1d(DR[:, cc], sm); main = int(np.argmax(prof))
            pk = [i for i in range(main + 8, H - 1) if prof[i] > prof[i - 1] and prof[i] >= prof[i + 1]]
            th.append(a['rlo'] + (main + int(np.argmin(prof[main:max(pk, key=lambda p: prof[p]) + 1]))) / (H - 1) * (a['rhi'] - a['rlo']) if pk else None)
        for need in [[T - 1], [T - 2, T - 1]]:
            if any(th[j] is None for j in need): out.append({'firm': firm, 'cluster': c, 'smooth_px': sm, 'cols': [int(j) for j in need], 'branch_found': False}); continue
            sel = np.ones(len(R), bool)
            for j in need: sel &= R[:, j] > th[j]
            out.append({'firm': firm, 'cluster': c, 'smooth_px': sm, 'cols': [int(j) for j in need], 'branch_found': True, 'selected': int(sel.sum()),
                        'precision': float((sel & truth).sum() / max(sel.sum(), 1)), 'recall': float((sel & truth).sum() / truth.sum())})
json.dump(out, open('/workspace/scout/1113/out/m2b_brush_sensitivity.json', 'w'), indent=1)
for o in out: print(o)
