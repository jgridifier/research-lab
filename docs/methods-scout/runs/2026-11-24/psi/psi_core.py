"""Independent NumPy phase slope index (Nolte et al. 2008, PRL 100:234101, eq. 3-4) with segment jackknife.
Convention: S_ij = <X_i X_j*>; y_j = y_i delayed by tau => S_ij ~ exp(+i 2 pi f tau); PSI_ij > 0 means i leads j."""
import numpy as np
from scipy.signal import get_window

def segments(x, nper, nover):
    step = nper - nover; n = (len(x) - nper) // step + 1
    idx = np.arange(nper)[None, :] + step * np.arange(n)[:, None]
    return x[idx]

def seg_fft(x, nper, nover, window="hann", detrend=True):
    s = segments(np.asarray(x, float), nper, nover)
    if detrend: s = s - s.mean(1, keepdims=True)
    w = get_window(window, nper) if window else np.ones(nper)
    return np.fft.rfft(s * w, axis=1)        # (K, F)

def _psi_from(Xi, Xj, band):
    """Xi, Xj: (K, F) segment spectra. band: slice of frequency indices (inclusive start, exclusive end), needs end<=F."""
    Sij = (Xi * np.conj(Xj)).mean(0); Sii = (np.abs(Xi) ** 2).mean(0); Sjj = (np.abs(Xj) ** 2).mean(0)
    C = Sij / np.sqrt(Sii * Sjj)
    lo, hi = band
    return float(np.imag(np.sum(np.conj(C[lo:hi - 1]) * C[lo + 1:hi])))

def psi(x, y, nper, nover, fband, fs=1.0, jackknife=True):
    """fband=(fmin,fmax) in cycles per sample unit * fs. Returns dict(psi, sd, z, K)."""
    Xi = seg_fft(x, nper, nover); Xj = seg_fft(y, nper, nover)
    f = np.fft.rfftfreq(nper, 1 / fs)
    lo = int(np.searchsorted(f, fband[0], 'left')); hi = int(np.searchsorted(f, fband[1], 'right'))
    K = Xi.shape[0]; p = _psi_from(Xi, Xj, (lo, hi))
    out = dict(psi=p, K=K, nfreq=hi - lo)
    if jackknife and K > 2:
        ps = np.array([_psi_from(np.delete(Xi, k, 0), np.delete(Xj, k, 0), (lo, hi)) for k in range(K)])
        sd = float(np.sqrt((K - 1) / K * ((ps - ps.mean()) ** 2).sum()))
        out.update(sd=sd, z=p / sd if sd > 0 else np.nan)
    return out

def psi_spectrum(x, y, nper, nover, fs=1.0):
    """Local phase slope per frequency pair: Im(C*(f) C(f+df)) and coherency modulus, for plotting."""
    Xi = seg_fft(x, nper, nover); Xj = seg_fft(y, nper, nover); f = np.fft.rfftfreq(nper, 1 / fs)
    Sij = (Xi * np.conj(Xj)).mean(0); C = Sij / np.sqrt((np.abs(Xi) ** 2).mean(0) * (np.abs(Xj) ** 2).mean(0))
    return f[:-1], np.imag(np.conj(C[:-1]) * C[1:]), np.abs(C)
