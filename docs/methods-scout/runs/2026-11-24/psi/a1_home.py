"""A1 home-field reproduction (SYNTHETIC). Seeds fixed."""
import json, time, numpy as np, warnings; warnings.filterwarnings('ignore')
from psi_core import psi, seg_fft
from statsmodels.tsa.api import VAR
out = {}
# (i) parity vs mne-connectivity
try:
    from mne_connectivity import phase_slope_index
    rng = np.random.default_rng(20261124); diffs = []; nper, nover = 64, 32
    for _ in range(20):
        n = 2048; a = rng.normal(size=n + 4); x = a[4:] + 0.3 * rng.normal(size=n); y = 0.8 * a[2:-2] + 0.5 * rng.normal(size=n)
        mine = psi(x, y, nper, nover, (0.05, 0.25))['psi']
        # mne: epochs array (n_epochs, n_signals, n_times); use the same overlapping segments, hann, detrended
        from psi_core import segments
        from scipy.signal import get_window
        w = get_window('hann', nper)
        ep = np.stack([np.stack([segments(x, nper, nover)[k] - segments(x, nper, nover)[k].mean(), segments(y, nper, nover)[k] - segments(y, nper, nover)[k].mean()]) for k in range(len(segments(x, nper, nover)))]) * w
        out.setdefault('mne_raw', []).append(mine)
        try:
            c = phase_slope_index(ep, indices=([0], [1]), sfreq=1.0, mode='fourier', fmin=0.05, fmax=0.25, verbose=False)
            diffs.append((mine, float(np.ravel(c.get_data())[0])))
        except Exception as e:
            out['mne_error'] = repr(e); break
    out['parity_pairs'] = diffs[:5]
    if diffs:
        a = np.array(diffs); out['parity_max_abs_diff'] = float(np.abs(a[:, 0] - a[:, 1]).max()); out['parity_corr'] = float(np.corrcoef(a[:, 0], a[:, 1])[0, 1])
        out['parity_ratio_median'] = float(np.median(a[:, 1] / a[:, 0]))
    out.pop('mne_raw', None)
except Exception as e:
    out['mne_error'] = repr(e)
# (ii) Nolte-style: coupled delay, and mixture of independent sources
def ar_pair(rng, n, coupled):
    s = rng.normal(size=(n + 10, 2))
    for t in range(1, n + 10): s[t] = 0.7 * s[t - 1] + rng.normal(size=2) * 0.7  # two AR(1) sources, coloured
    s1, s2 = s[:, 0], s[:, 1]
    if coupled: y1 = s1[10:]; y2 = 0.8 * s1[8:-2] + 0.6 * s2[10:]
    else:  # random mixture of two independent sources (volume conduction)
        m = rng.normal(size=(2, 2)); y1 = m[0, 0] * s1[10:] + m[0, 1] * s2[10:]; y2 = m[1, 0] * s1[10:] + m[1, 1] * s2[10:]
    return y1, y2
def gc_p(x, y):
    v = VAR(np.column_stack([x, y])).fit(maxlags=8, ic='aic')
    if v.k_ar == 0: return 1., 1.
    return v.test_causality(1, 0, kind='f').pvalue, v.test_causality(0, 1, kind='f').pvalue   # (x->y ... see below)
rng = np.random.default_rng(20261124); N = 5000; R = 200; res = {}
for name, coupled in [('coupled', True), ('mixture', False)]:
    ok = sig = gcs = gc_dir = 0
    for _ in range(R):
        x, y = ar_pair(rng, N, coupled)
        r = psi(x, y, 128, 64, (0.02, 0.45)); sig += abs(r['z']) > 2; ok += r['z'] > 0
        # p for "x does not Granger-cause y" is test_causality(caused=1, causing=0); and reverse
        v = VAR(np.column_stack([x, y])).fit(maxlags=8, ic='aic')
        p_xy = v.test_causality(1, 0, kind='f').pvalue; p_yx = v.test_causality(0, 1, kind='f').pvalue
        gcs += (p_xy < .05) or (p_yx < .05); gc_dir += (p_xy < .05)
    res[name] = dict(psi_sig_rate=sig / R, psi_positive_rate=ok / R, granger_either_dir_sig=gcs / R, granger_x_to_y_sig=gc_dir / R)
    print(name, res[name], flush=True)
out['sim'] = res
out['pass'] = dict(parity=bool(out.get('parity_max_abs_diff', 1) <= 1e-8),
                   coupled_dir_correct=bool(res['coupled']['psi_positive_rate'] >= .95 and res['coupled']['psi_sig_rate'] >= .95),
                   mixture_psi_false_sig_le_10pct=bool(res['mixture']['psi_sig_rate'] <= .10))
json.dump(out, open('a1_home.json', 'w'), indent=1, default=float); print(json.dumps(out, indent=1, default=float))
