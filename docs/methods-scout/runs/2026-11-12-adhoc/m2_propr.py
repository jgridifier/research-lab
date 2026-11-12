#!/usr/bin/env python3
"""Methods scout 2026-11-12 ad hoc, method 2: Lovell proportionality (phi, rho).

Formulas from Lovell et al. 2015 PLoS Comput Biol 11(3):e1004075 and
Quinn et al. 2017 Sci Rep 7:16520 (the propr package, CRAN-archived 2022-11-10).

  VLR(x,y) = var(log x - log y)
  phi(x,y) = VLR(x,y) / var(log x)          # Lovell 2015; not symmetric
  rho(x,y) = 1 - VLR(x,y)/(var(log x)+var(log y))   # symmetric, in [-1,1]

Sample variance (ddof=1) throughout. PROXY FR Y-9C only. Seed 20261112.
Descriptive; no forecasts. Identity tests are run first and must pass.
"""
import json, time, os
import numpy as np
import pandas as pd
from numpy.linalg import lstsq

SEED = 20261112
BOOT = 999
OUT = "/workspace/scout/1112-adhoc/out/m2_results.json"
DATA = "/workspace/scout/1112-adhoc/data/"
t0 = time.time()
rng = np.random.default_rng(SEED)

def svar(x):
    x = np.asarray(x, float)
    return np.var(x, ddof=1)

def vlr(x, y):
    return svar(np.log(x) - np.log(y))

def phi(x, y):
    return vlr(x, y) / svar(np.log(x))

def rho(x, y):
    den = svar(np.log(x)) + svar(np.log(y))
    return 1.0 - vlr(x, y) / den

def clr(M):
    """CLR by row (each quarter is a composition). M is T x D, all positive."""
    M = np.asarray(M, float)
    L = np.log(M)
    return L - L.mean(axis=1, keepdims=True)

def pairwise(fn, M, names):
    D = M.shape[1]
    R = np.eye(D)
    for i in range(D):
        for j in range(i + 1, D):
            R[i, j] = R[j, i] = fn(M[:, i], M[:, j])
    return pd.DataFrame(R, index=names, columns=names)

def identity_tests():
    """Algebraic identities any correct implementation must satisfy."""
    rng_t = np.random.default_rng(0)
    x = np.exp(rng_t.normal(0, 1, 200))
    # 1. exact proportionality: y = c x  =>  phi=0, rho=1, VLR=0
    y = 3.7 * x
    assert vlr(x, y) < 1e-14, vlr(x, y)
    assert abs(phi(x, y)) < 1e-14
    assert abs(rho(x, y) - 1) < 1e-14
    # 2. scale invariance of VLR: relative and absolute give the same VLR
    #    (Lovell's central point). Totals t_i vary.
    t = np.exp(rng_t.normal(2, 0.5, 200))
    Xabs = np.column_stack([x * t, y * t, np.exp(rng_t.normal(0, 1, 200)) * t])
    Xrel = Xabs / Xabs.sum(1, keepdims=True)
    assert abs(vlr(Xabs[:, 0], Xabs[:, 1]) - vlr(Xrel[:, 0], Xrel[:, 1])) < 1e-12
    # 3. rho is symmetric, phi is not (unless var log x = var log y)
    z = np.exp(rng_t.normal(0, 1.7, 200))
    assert abs(rho(x, z) - rho(z, x)) < 1e-14
    # 4. VLR(x,y) = var(clr_x - clr_y) on a closed composition (same pairwise log-ratio)
    C = clr(Xrel)
    assert abs(vlr(Xrel[:, 0], Xrel[:, 1]) - svar(C[:, 0] - C[:, 1])) < 1e-12
    # 5. Pearson on relative data is NOT equal to Pearson on absolute data (the problem)
    #    while rho via VLR is the same for the proportional pair (both ~1)
    assert abs(rho(Xabs[:, 0], Xabs[:, 1]) - 1) < 1e-12
    assert abs(rho(Xrel[:, 0], Xrel[:, 1]) - 1) < 1e-12
    # 6. a non-proportional pair: rho is not identically 1, and Pearson(raw shares)
    #    can disagree in sign or magnitude with rho (we only check they can differ)
    r_raw = np.corrcoef(Xrel[:, 0], Xrel[:, 2])[0, 1]
    r_rho = rho(Xrel[:, 0], Xrel[:, 2])
    # just record; both are well-defined
    return {"passed": True, "example_pearson_vs_rho_nonprop": {"pearson": float(r_raw), "rho": float(r_rho)}}

def cyclic_shift_matrix(M, rng):
    """Independently cyclic-shift each column (Hallett-style persistence-preserving null)."""
    T, D = M.shape
    out = np.empty_like(M)
    for j in range(D):
        k = int(rng.integers(0, T))
        out[:, j] = np.roll(M[:, j], k)
    return out

def iid_permute_matrix(M, rng):
    """iid time permutation, independently by column (the naive null)."""
    T, D = M.shape
    out = np.empty_like(M)
    for j in range(D):
        out[:, j] = rng.permutation(M[:, j])
    return out

def pairwise_rho(M, names):
    return pairwise(rho, M, names)

def pvals_from_null(obs, nulls, alternative="two-sided"):
    """nulls: array B x D x D. Return p_ge of |obs| or signed, and a two-sided p on |rho|."""
    B, D, _ = nulls.shape
    p_ge_abs = np.zeros((D, D))
    p_le = np.zeros((D, D))
    p_ge = np.zeros((D, D))
    null_mean = nulls.mean(0)
    null_q025 = np.quantile(nulls, 0.025, axis=0)
    null_q975 = np.quantile(nulls, 0.975, axis=0)
    for i in range(D):
        for j in range(D):
            o = obs[i, j]
            n = nulls[:, i, j]
            p_ge[i, j] = (1 + np.sum(n >= o)) / (1 + B)
            p_le[i, j] = (1 + np.sum(n <= o)) / (1 + B)
            p_ge_abs[i, j] = (1 + np.sum(np.abs(n) >= abs(o))) / (1 + B)
    return dict(p_ge=p_ge, p_le=p_le, p_ge_abs=p_ge_abs,
                null_mean=null_mean, null_q025=null_q025, null_q975=null_q975)

def residualize_clr(M, X):
    """CLR-transform compositions M (T x D), residualize each coordinate on market matrix X (T x K), with intercept."""
    C = clr(M)
    T, K = X.shape
    Z = np.column_stack([np.ones(T), X])
    resid = np.empty_like(C)
    r2 = np.empty(C.shape[1])
    beta = np.empty((C.shape[1], Z.shape[1]))
    for j in range(C.shape[1]):
        b, _, _, _ = lstsq(Z, C[:, j], rcond=None)
        fit = Z @ b
        resid[:, j] = C[:, j] - fit
        sst = np.sum((C[:, j] - C[:, j].mean()) ** 2)
        sse = np.sum(resid[:, j] ** 2)
        r2[j] = 1 - sse / sst if sst > 0 else 0.0
        beta[j] = b
    return resid, r2, beta

def rho_from_real_vectors(V, names):
    """rho-like association on already-log-ratio (or residual) vectors: 1 - var(u-v)/(var u + var v)."""
    D = V.shape[1]
    R = np.eye(D)
    for i in range(D):
        for j in range(i + 1, D):
            den = svar(V[:, i]) + svar(V[:, j])
            R[i, j] = R[j, i] = 1.0 - svar(V[:, i] - V[:, j]) / den
    return pd.DataFrame(R, index=names, columns=names)

def mat_to_dict(df):
    return {r: {c: float(df.loc[r, c]) for c in df.columns} for r in df.index}

def run_panel(wide, market, mcols, pname):
    names = list(wide.columns)
    Mraw = wide.values.astype(float)
    assert np.all(Mraw > 0), "zeros present; rho/phi require strictly positive data"
    Msh = Mraw / Mraw.sum(1, keepdims=True)
    T, D = Msh.shape

    rho_sh = pairwise_rho(Msh, names)
    phi_sh = pairwise(phi, Msh, names)  # asymmetric; we store lower? full matrix as phi(i,j)=phi(col_i, col_j)
    pearson_sh = pd.DataFrame(np.corrcoef(Msh, rowvar=False), index=names, columns=names)
    C = clr(Msh)
    pearson_clr = pd.DataFrame(np.corrcoef(C, rowvar=False), index=names, columns=names)
    # rho on CLR coordinates (denominator uses var(clr) not var(log share))
    rho_clr = rho_from_real_vectors(C, names)
    # rho on RAW amounts (VLR is identical to shares; rho is NOT, because var(log x) changes)
    rho_raw = pairwise_rho(Mraw, names)
    pearson_raw = pd.DataFrame(np.corrcoef(Mraw, rowvar=False), index=names, columns=names)

    # disagreements: pairs where Pearson(shares) and rho(shares) differ in sign, or by > 0.2
    disag = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pr, rh, pc = float(pearson_sh.loc[a, b]), float(rho_sh.loc[a, b]), float(pearson_clr.loc[a, b])
            disag.append({"a": a, "b": b, "pearson_share": pr, "rho_share": rh,
                          "pearson_clr": pc, "rho_clr": float(rho_clr.loc[a, b]),
                          "rho_raw": float(rho_raw.loc[a, b]),
                          "pearson_raw": float(pearson_raw.loc[a, b]),
                          "delta_pearson_share_minus_rho": pr - rh,
                          "sign_flip_vs_rho": (pr * rh) < 0})
    disag = sorted(disag, key=lambda d: -abs(d["delta_pearson_share_minus_rho"]))

    # Cyclic-shift and iid nulls on SHARE rho
    null_cyc = np.zeros((BOOT, D, D))
    null_iid = np.zeros((BOOT, D, D))
    rng_c = np.random.default_rng(SEED + (0 if pname == "A" else 17))
    rng_i = np.random.default_rng(SEED + 100 + (0 if pname == "A" else 17))
    for b in range(BOOT):
        Mc = cyclic_shift_matrix(Msh, rng_c)
        Mi = iid_permute_matrix(Msh, rng_i)
        null_cyc[b] = pairwise_rho(Mc, names).values
        null_iid[b] = pairwise_rho(Mi, names).values
    pv_c = pvals_from_null(rho_sh.values, null_cyc)
    pv_i = pvals_from_null(rho_sh.values, null_iid)

    # Significant pairs under cyclic-shift (two-sided on |rho|), FDR not applied in the
    # headline (small D); we also report BH later.
    pairs_sig = []
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if j <= i:
                continue
            pairs_sig.append({
                "a": a, "b": b,
                "rho": float(rho_sh.values[i, j]),
                "pearson_share": float(pearson_sh.values[i, j]),
                "pearson_clr": float(pearson_clr.values[i, j]),
                "p_cyc_abs": float(pv_c["p_ge_abs"][i, j]),
                "p_cyc_le": float(pv_c["p_le"][i, j]),
                "p_cyc_ge": float(pv_c["p_ge"][i, j]),
                "p_iid_abs": float(pv_i["p_ge_abs"][i, j]),
                "null_cyc_mean": float(pv_c["null_mean"][i, j]),
                "null_cyc_q025": float(pv_c["null_q025"][i, j]),
                "null_cyc_q975": float(pv_c["null_q975"][i, j]),
            })
    pairs_sig = sorted(pairs_sig, key=lambda d: d["rho"])

    # Benjamini-Hochberg on cyclic-shift two-sided p
    ps = np.array([d["p_cyc_abs"] for d in pairs_sig])
    m = len(ps)
    order = np.argsort(ps)
    bh = np.empty(m)
    prev = 1.0
    for k in range(m, 0, -1):
        idx = order[k - 1]
        prev = min(prev, ps[idx] * m / k)
        bh[idx] = prev
    for d, q in zip(pairs_sig, bh):
        d["bh_q_cyc"] = float(q)

    # Market-partial: residualize CLR on market factors, then residual-rho
    # Align market (same index)
    X = market.loc[wide.index, mcols].astype(float)
    if X.isna().any().any():
        raise ValueError(f"{pname}: market NA in {mcols}: {X.isna().sum().to_dict()}")
    resid, r2, beta = residualize_clr(Msh, X.values)
    rho_part = rho_from_real_vectors(resid, names)
    pearson_part = pd.DataFrame(np.corrcoef(resid, rowvar=False), index=names, columns=names)
    # cyclic-shift null in residual space: shift residual columns
    null_part = np.zeros((BOOT, D, D))
    rng_p = np.random.default_rng(SEED + 200 + (0 if pname == "A" else 17))
    for b in range(BOOT):
        Rp = cyclic_shift_matrix(resid, rng_p)
        null_part[b] = rho_from_real_vectors(Rp, names).values
    pv_p = pvals_from_null(rho_part.values, null_part)

    pairs_part = []
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if j <= i:
                continue
            pairs_part.append({
                "a": a, "b": b,
                "rho": float(rho_sh.values[i, j]),
                "rho_partial": float(rho_part.values[i, j]),
                "delta": float(rho_part.values[i, j] - rho_sh.values[i, j]),
                "p_part_abs": float(pv_p["p_ge_abs"][i, j]),
                "p_part_le": float(pv_p["p_le"][i, j]),
                "null_part_q025": float(pv_p["null_q025"][i, j]),
                "null_part_q975": float(pv_p["null_q975"][i, j]),
                "pearson_clr": float(pearson_clr.values[i, j]),
            })
    pairs_part = sorted(pairs_part, key=lambda d: d["rho_partial"])
    ps = np.array([d["p_part_abs"] for d in pairs_part])
    m = len(ps); order = np.argsort(ps); bh = np.empty(m); prev = 1.0
    for k in range(m, 0, -1):
        idx = order[k - 1]
        prev = min(prev, ps[idx] * m / k)
        bh[idx] = prev
    for d, q in zip(pairs_part, bh):
        d["bh_q_part"] = float(q)

    # Window stability of rho (shares)
    def window_rho(idx, tag):
        Mw = Msh[idx]
        if Mw.shape[0] < 8:
            return None
        R = pairwise_rho(Mw, names)
        return {"tag": tag, "n": int(Mw.shape[0]), "rho": mat_to_dict(R)}

    # default windows by panel length
    idx = np.arange(T)
    qs = list(wide.index)
    windows = []
    if pname == "A":
        cuts = [("2016Q3", "2019Q4"), ("2020Q1", "2026Q2")]
    else:
        cuts = [("2011Q1", "2015Q4"), ("2016Q1", "2019Q4"), ("2020Q1", "2026Q2")]
    for a, b in cuts:
        sel = [i for i, q in enumerate(qs) if a <= q <= b]
        windows.append(window_rho(sel, f"{a}-{b}"))

    # How much of Pearson(share)'s story is spurious: Frobenius distance etc.
    def offdiag(df):
        v = df.values.copy(); np.fill_diagonal(v, 0); return v
    fro_pr_rho = float(np.linalg.norm(offdiag(pearson_sh) - offdiag(rho_sh)))
    fro_pc_rho = float(np.linalg.norm(offdiag(pearson_clr) - offdiag(rho_sh)))
    fro_pr_pc = float(np.linalg.norm(offdiag(pearson_sh) - offdiag(pearson_clr)))
    n_sign_flip = int(sum(d["sign_flip_vs_rho"] for d in disag))

    return {
        "panel": pname, "nT": T, "species": names, "q": qs,
        "market_cols": mcols,
        "clr_r2_on_market": {n: float(r) for n, r in zip(names, r2)},
        "rho_share": mat_to_dict(rho_sh),
        "rho_clr": mat_to_dict(rho_clr),
        "rho_raw": mat_to_dict(rho_raw),
        "rho_partial": mat_to_dict(rho_part),
        "phi_share": mat_to_dict(phi_sh),
        "pearson_share": mat_to_dict(pearson_sh),
        "pearson_clr": mat_to_dict(pearson_clr),
        "pearson_raw": mat_to_dict(pearson_raw),
        "pearson_partial": mat_to_dict(pearson_part),
        "disagreements": disag,
        "n_sign_flip_pearson_share_vs_rho": n_sign_flip,
        "frobenius": {"pearson_share_vs_rho": fro_pr_rho,
                      "pearson_clr_vs_rho": fro_pc_rho,
                      "pearson_share_vs_pearson_clr": fro_pr_pc},
        "pairs_rho": pairs_sig,
        "pairs_partial": pairs_part,
        "n_cyc_sig_05": int(sum(d["p_cyc_abs"] <= 0.05 for d in pairs_sig)),
        "n_cyc_sig_bh05": int(sum(d["bh_q_cyc"] <= 0.05 for d in pairs_sig)),
        "n_part_sig_05": int(sum(d["p_part_abs"] <= 0.05 for d in pairs_part)),
        "n_part_sig_bh05": int(sum(d["bh_q_part"] <= 0.05 for d in pairs_part)),
        "n_pairs": len(pairs_sig),
        "windows": windows,
        # store matrices as lists for figures
        "_mats": {
            "names": names,
            "rho_share": rho_sh.values.tolist(),
            "rho_partial": rho_part.values.tolist(),
            "pearson_share": pearson_sh.values.tolist(),
            "pearson_clr": pearson_clr.values.tolist(),
            "p_cyc_abs": pv_c["p_ge_abs"].tolist(),
            "p_part_abs": pv_p["p_ge_abs"].tolist(),
        },
    }

def main():
    tests = identity_tests()
    print("identity tests passed:", tests)

    A = pd.read_csv(DATA + "panel_A.csv", index_col=0)
    E = pd.read_csv(DATA + "panel_E4.csv", index_col=0)
    M = pd.read_csv(DATA + "market_q.csv", index_col=0)
    # columns: vix, nasdaq_ret4, baa10y, eq_rev_ind_g4, ta_ind_g1
    resA = run_panel(A, M, ["vix", "nasdaq_ret4", "baa10y", "ta_ind_g1"], "A")
    resE = run_panel(E, M, ["vix", "nasdaq_ret4", "baa10y", "eq_rev_ind_g4"], "E4")

    # Highlight Q1 pairs
    def getp(res, a, b, key="rho_share"):
        return res[key][a][b]

    out = {
        "meta": {
            "method": "proportionality (Lovell 2015; Quinn 2017 propr formulas)",
            "seed": SEED, "boot": BOOT, "date": "2026-11-12",
            "elapsed_s": time.time() - t0,
            "var": "sample variance, ddof=1",
            "note": "PROXY FR Y-9C. rho/phi on strictly positive shares. Cyclic-shift null preserves each dealer's autocorrelation. Market-partial residualizes CLR coordinates on VIX, 4Q Nasdaq return, BAA-Treasury spread, and industry growth, then applies the same 1-var(diff)/sum(var) association in residual space (an extension, not in the original papers).",
            "identity_tests": tests,
        },
        "A": {k: v for k, v in resA.items()},
        "E4": {k: v for k, v in resE.items()},
    }
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(f"WROTE {OUT} in {out['meta']['elapsed_s']:.1f}s")

    print("\n==== KEY: E4 rho (shares) ====")
    for d in resE["pairs_rho"]:
        print(f"  {d['a']:5s}-{d['b']:5s}  rho={d['rho']:+.3f}  pearson_sh={d['pearson_share']:+.3f}  pearson_clr={d['pearson_clr']:+.3f}  p_cyc={d['p_cyc_abs']:.3f} q={d['bh_q_cyc']:.3f}")
    print("==== E4 partial ====")
    for d in resE["pairs_partial"]:
        print(f"  {d['a']:5s}-{d['b']:5s}  rho={d['rho']:+.3f}  partial={d['rho_partial']:+.3f}  d={d['delta']:+.3f}  p={d['p_part_abs']:.3f}")
    print("==== A: most negative and most positive rho (cyclic p) ====")
    for d in resA["pairs_rho"][:8]:
        print(f"  {d['a']:10s}-{d['b']:10s}  rho={d['rho']:+.3f}  pearson_sh={d['pearson_share']:+.3f}  p_cyc={d['p_cyc_abs']:.3f} q={d['bh_q_cyc']:.3f}")
    print("  ...")
    for d in resA["pairs_rho"][-8:]:
        print(f"  {d['a']:10s}-{d['b']:10s}  rho={d['rho']:+.3f}  pearson_sh={d['pearson_share']:+.3f}  p_cyc={d['p_cyc_abs']:.3f} q={d['bh_q_cyc']:.3f}")
    print("sign flips A", resA["n_sign_flip_pearson_share_vs_rho"], "E4", resE["n_sign_flip_pearson_share_vs_rho"])
    print("frobenius A", resA["frobenius"], "E4", resE["frobenius"])
    print("clr R2 on market A", resA["clr_r2_on_market"])
    print("clr R2 on market E4", resE["clr_r2_on_market"])
    print("n sig cyc A", resA["n_cyc_sig_05"], "bh", resA["n_cyc_sig_bh05"], "of", resA["n_pairs"])
    print("n sig cyc E4", resE["n_cyc_sig_05"], "bh", resE["n_cyc_sig_bh05"], "of", resE["n_pairs"])
    print("n sig part A", resA["n_part_sig_05"], "bh", resA["n_part_sig_bh05"])
    print("n sig part E4", resE["n_part_sig_05"], "bh", resE["n_part_sig_bh05"])

if __name__ == "__main__":
    main()
