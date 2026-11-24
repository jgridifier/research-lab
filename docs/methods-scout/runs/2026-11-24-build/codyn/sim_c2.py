"""C2: share-space compensation test (PREREG.md C2). SYNTHETIC panels only."""
import json, time, numpy as np
import codynport as C
T, S, K, B, R = 40, 10, 8, 199, 1000
L = (T - 1) - K

def ar1(rng, n, phi, sd, size=None):
    e = rng.normal(0, sd, n); x = np.zeros(n); x[0] = e[0] / np.sqrt(1 - phi**2)
    for t in range(1, n): x[t] = phi * x[t-1] + e[t]
    return x

def panel(rng, swap):
    n = T - 1
    z = ar1(rng, n, .9, .10); lam = rng.normal(1, .3, S)
    D = np.outer(z, lam) + np.column_stack([ar1(rng, n, .3, .15) for _ in range(S)])
    if swap:
        w = ar1(rng, n, .8, .12); D[:, 0] += w; D[:, 1] -= w
    return D

def stat(Dw):  # Dw (..., L, S) -> min off-diagonal residual corr after removing market loading
    m = Dw.mean(-1, keepdims=True)
    mc = m - m.mean(-2, keepdims=True); Dc = Dw - Dw.mean(-2, keepdims=True)
    beta = (mc * Dc).sum(-2, keepdims=True) / (mc ** 2).sum(-2, keepdims=True)
    E = Dc - beta * mc
    En = E / np.sqrt((E ** 2).sum(-2, keepdims=True))
    Rm = np.einsum('...ti,...tj->...ij', En, En)
    iu = np.triu_indices(S, 1)
    return Rm[..., iu[0], iu[1]].min(-1)

def pval(D, rng):
    obs = stat(D[:L])
    ks = rng.integers(0, K + 1, (B, S))
    idx = ks[:, None, :] + np.arange(L)[None, :, None]       # (B, L, S)
    Dn = D[idx, np.arange(S)[None, None, :]]
    nul = stat(Dn)
    return (1 + (nul <= obs).sum()) / (B + 1), obs

def raw_vr_p(D, rng):
    X = np.exp(np.vstack([np.zeros(S), np.cumsum(D, 0)]))     # volumes, T x S
    v = C.variance_ratio(X); nl = C.variance_ratio_null(X, B, seed=int(rng.integers(1 << 30)), level=0.95)
    return v < nl["lowerCI"], v

out = {}
ss = np.random.SeedSequence(20261124).spawn(2)
for name, swap, sq in [("S0", False, ss[0]), ("S1", True, ss[1])]:
    rng = np.random.default_rng(sq); rej = 0; rr = 0; obs = []; t0 = time.time(); ps = []
    for r in range(R):
        D = panel(rng, swap); p, o = pval(D, rng); rej += p <= .05; obs.append(o); ps.append(p)
        a, _ = raw_vr_p(D, rng); rr += a
    out[name] = dict(reject_rate=rej / R, mc_se=float(np.sqrt(.05 * .95 / R)), raw_VR_wrap_lower_reject=rr / R,
                     mean_stat=float(np.mean(obs)), seconds=time.time() - t0, p_hist=np.histogram(ps, bins=10, range=(0, 1))[0].tolist())
    print(name, out[name], flush=True)
# official VR on shares for one S1 panel
rng = np.random.default_rng(1); D = panel(rng, True)
X = np.exp(np.vstack([np.zeros(S), np.cumsum(D, 0)])); Sh = X / X.sum(1, keepdims=True)
out["official_VR_on_shares_S1_panel"] = C.variance_ratio(Sh); out["official_VR_raw_S1_panel"] = C.variance_ratio(X)
s, pw = out["S0"]["reject_rate"], out["S1"]["reject_rate"]
out["pass"] = dict(size_in_band=bool(.02 <= s <= .08), power_ge_080=bool(pw >= .8), vr_shares_zero=bool(abs(out["official_VR_on_shares_S1_panel"]) < 1e-12))
json.dump(out, open("c2_results.json", "w"), indent=1); print(out["pass"], out["official_VR_on_shares_S1_panel"], out["official_VR_raw_S1_panel"])
