#!/usr/bin/env python3
"""Burn-in gate for the Fed CP maturity-mix study (applied-lab mandate).

Reads CP_data.xml VOL only. Amounts and issue counts are aggregated ONLY for dates
<= 2008-12-26 (last burn-in week). For OOS calendar weeks only a structural
valid-day count per type is computed (no amounts, no counts of issues).
Thresholds: GATE_THRESHOLDS_fed_cp_ot.md (sha256 checked).
"""
from __future__ import annotations
import hashlib, math, re, zipfile
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path("/workspace/research/fed_cp_ot_prereg"); RAW = HERE / "raw"
TH = HERE / "GATE_THRESHOLDS_fed_cp_ot.md"
TH_SHA = "c15eb60cbe1467090fcc920b8f4e311dd14f7b3bbfd0437e21809355721a6c8a"
ZIP_SHA = "16805f2ce102d5b6703de6393e89f345e9e68e15381ab457fb58f3830cff22d2"
SEED = 20261009
TYPES = ["AAA", "FAA", "NAA", "NA2"]
MATS = ["1", "5", "10", "21", "41", "81"]
EDGES = [(1, 4), (5, 9), (10, 20), (21, 40), (41, 80), (81, 270)]
X_LOG = np.array([math.log(math.sqrt(a * b)) for a, b in EDGES])
X_RANK = np.arange(6, dtype=float)
BURN_FIRST, BURN_LAST = pd.Timestamp("2001-01-05"), pd.Timestamp("2008-12-26")
OOS_FIRST, OOS_LAST = pd.Timestamp("2009-01-02"), pd.Timestamp("2026-10-02")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def f(x): return f"{x:.10f}"
print("NUMPY", np.__version__, "PANDAS", pd.__version__)
print("THRESHOLDS_SHA256", sha(TH), "MATCH", sha(TH) == TH_SHA); assert sha(TH) == TH_SHA
print("ZIP_SHA256_MATCH", sha(RAW / "FRB_CP_xml.zip") == ZIP_SHA); assert sha(RAW / "FRB_CP_xml.zip") == ZIP_SHA
print("X_LOG", " ".join(f"{v:.6f}" for v in X_LOG))

# ---------------- parse ----------------
txt = zipfile.ZipFile(RAW / "FRB_CP_xml.zip").read("CP_data.xml").decode("utf-8")
i = txt.find('<frb:DataSet id="VOL"'); vol = txt[i: txt.find("</frb:DataSet>", i)]
rows = []
for b in re.split(r"<kf:Series ", vol)[1:]:
    at = dict(re.findall(r'(\w+)="([^"]*)"', b[: b.find(">")]))
    if at["CP_TYPE"] not in TYPES: continue
    for o in re.findall(r"<frb:Obs ([^/]*)/>", b):
        a = dict(re.findall(r'(\w+)="([^"]*)"', o))
        if a.get("OBS_STATUS") == "ND" or float(a["OBS_VALUE"]) == -9999: continue
        rows.append((at["CP_TYPE"], at["CP_MAT_RANGE"], at["CP_VOL_TYPE"], a["TIME_PERIOD"], float(a["OBS_VALUE"])))
df = pd.DataFrame(rows, columns=["type", "mat", "vt", "date", "value"]); df["date"] = pd.to_datetime(df.date)
df["week"] = df.date.dt.to_period("W-FRI").dt.end_time.dt.normalize()
# structural OOS check: valid days per type per OOS week (no values used)
oos = df[(df.week >= OOS_FIRST) & (df.week <= OOS_LAST)]
oos_days = oos.groupby(["type", "week"]).date.nunique()
oos_weeks = pd.period_range(OOS_FIRST, OOS_LAST, freq="W-FRI")
T_OOS = len(oos_weeks)
print("SECTION oos_structure_only", "T_OOS_CALENDAR_WEEKS", T_OOS)
oos_ok = {}
for t in TYPES:
    s = oos_days.xs(t, level="type").reindex([p.end_time.normalize() for p in oos_weeks]).fillna(0)
    oos_ok[t] = float((s >= 3).mean()); print("OOS_FRAC_WEEKS_GE3_VALID_DAYS", t, f"{oos_ok[t]:.6f}")
del oos
# burn-in only from here
b = df[(df.week >= BURN_FIRST) & (df.week <= BURN_LAST)].copy(); del df
print("BURNIN_DATE_RANGE", b.date.min().date(), b.date.max().date(), "NO_AMOUNT_AFTER_2008_12_26", bool(b.date.max() <= BURN_LAST))
weeks = sorted(b.week.unique())
print("BURNIN_CAL_WEEKS", len(weeks))
D, N, DAYS, DAILY = {}, {}, {}, {}
for t in TYPES:
    g = b[b.type == t]
    D[t] = g[g.vt == "D"].pivot_table(index="week", columns="mat", values="value", aggfunc="sum").reindex(index=weeks, columns=MATS)
    N[t] = g[g.vt == "N"].pivot_table(index="week", columns="mat", values="value", aggfunc="sum").reindex(index=weeks, columns=MATS)
    DAYS[t] = g.groupby("week").date.nunique().reindex(weeks).fillna(0)
    DAILY[t] = (g[g.vt == "D"].pivot_table(index="date", columns="mat", values="value", aggfunc="sum").reindex(columns=MATS),
                g[g.vt == "N"].pivot_table(index="date", columns="mat", values="value", aggfunc="sum").reindex(columns=MATS))
usable = {}
for t in TYPES:
    u = (DAYS[t] >= 3) & (N[t].sum(axis=1) >= 100) & (D[t].sum(axis=1) > 0)
    usable[t] = u
    bad = int(((D[t] > 0) & (N[t] == 0)).sum().sum())
    print("USABLE", t, "weeks", int(u.sum()), "of", len(weeks), "frac", f"{u.mean():.6f}", "cells_D_pos_N_zero", bad)

# ---------------- step quantile machinery ----------------
def q_from_p(p, x):
    p = np.asarray(p, float); k = p > 0; c = np.cumsum(p[k]) / p[k].sum(); c[-1] = 1.0
    return (c, x[k].astype(float))
def _merge(*qs):
    c = np.unique(np.concatenate([q[0] for q in qs])); c = c[c > 0]
    lens = np.diff(np.r_[0.0, c]); mids = c - lens / 2
    vals = [q[1][np.minimum(np.searchsorted(q[0], mids, side="left"), len(q[1]) - 1)] for q in qs]
    return c, lens, vals
def w2sq(q1, q2):
    _, l, (v1, v2) = _merge(q1, q2); return float(np.sum(l * (v1 - v2) ** 2))
def decomp(q1, q2):
    _, l, (v1, v2) = _merge(q1, q2)
    m1, m2 = np.sum(l * v1), np.sum(l * v2)
    s1, s2 = math.sqrt(max(np.sum(l * (v1 - m1) ** 2), 0)), math.sqrt(max(np.sum(l * (v2 - m2) ** 2), 0))
    cov = np.sum(l * (v1 - m1) * (v2 - m2))
    shape = s1 * s1 + s2 * s2 - 2 * cov - (s1 - s2) ** 2
    return (m1 - m2) ** 2, (s1 - s2) ** 2, shape
def bary(qs, w=None):
    c, l, vals = _merge(*qs); w = np.ones(len(qs)) / len(qs) if w is None else np.asarray(w) / np.sum(w)
    return (c, np.sum([wi * v for wi, v in zip(w, vals)], axis=0))
def qmix(q1, q2, a):  # a*q1 + (1-a)*q2
    return bary([q1, q2], [a, 1 - a])

Q = {t: {w: q_from_p(D[t].loc[w].fillna(0).values, X_LOG) for w in weeks if usable[t][w]} for t in TYPES}
QR = {t: {w: q_from_p(D[t].loc[w].fillna(0).values, X_RANK) for w in weeks if usable[t][w]} for t in TYPES}
widx = {w: i for i, w in enumerate(weeks)}

def gate_block(Qd, label, wsel=None):
    rng = np.random.default_rng(SEED)
    half, hdec, nxt, ndec, hw = [], [], [], [], []
    for t in TYPES:
        for w in weeks:
            if w not in Qd[t]: continue
            c = N[t].loc[w].fillna(0).values.astype(np.int64)
            a = np.where(c > 0, D[t].loc[w].fillna(0).values / np.maximum(c, 1), 0.0)
            c1 = rng.multivariate_hypergeometric(c, int(c.sum() // 2)); c2 = c - c1
            x = X_LOG if Qd is Q else X_RANK
            if (wsel is None or wsel(w)) and (c1 * a).sum() > 0 and (c2 * a).sum() > 0:
                q1, q2 = q_from_p(c1 * a, x), q_from_p(c2 * a, x)
                half.append(w2sq(q1, q2)); hdec.append(decomp(q1, q2))
            nw = w + pd.Timedelta(days=7)
            if nw in Qd[t] and (wsel is None or wsel(nw)):
                nxt.append(w2sq(Qd[t][w], Qd[t][nw])); ndec.append(decomp(Qd[t][w], Qd[t][nw]))
            # half-week day split (non-gating)
            if wsel is None or wsel(w):
                dd, nn = DAILY[t]
                days = sorted(dd.index[(dd.index >= w - pd.Timedelta(days=4)) & (dd.index <= w)])
                if len(days) >= 4:
                    s1 = dd.loc[days[0::2]].fillna(0).sum().values; s2 = dd.loc[days[1::2]].fillna(0).sum().values
                    if s1.sum() > 0 and s2.sum() > 0: hw.append(w2sq(q_from_p(s1, x), q_from_p(s2, x)))
    half, nxt, hw = map(np.array, (half, nxt, hw)); hdec, ndec = np.array(hdec), np.array(ndec)
    mh, mn, mhw = np.median(half), np.median(nxt), np.median(hw)
    print(f"[{label}] N_HALF", len(half), "N_NEXT", len(nxt), "N_HALFWEEK", len(hw))
    print(f"[{label}] MEDIAN_HALF_W2SQ", f(mh), "MEDIAN_NEXT_W2SQ", f(mn), "RATIO_NEXT_OVER_HALF", f(mn / mh))
    print(f"[{label}] MEAN_HALF_W2SQ", f(half.mean()), "MEAN_NEXT_W2SQ", f(nxt.mean()))
    print(f"[{label}] K1B_NONGATING MEDIAN_HALFWEEK_W2SQ", f(mhw), "RATIO_NEXT_OVER_HALFWEEK", f(mn / mhw))
    tot = nxt.sum()
    for j, nm in enumerate(["LOC", "SCALE", "SHAPE"]):
        print(f"[{label}] NEXT_POOLED_SHARE_{nm}", f(ndec[:, j].sum() / tot), f"NEXT_MEDIAN_{nm}", f(np.median(ndec[:, j])),
              f"HALF_POOLED_SHARE_{nm}", f(hdec[:, j].sum() / half.sum()), f"HALF_MEDIAN_{nm}", f(np.median(hdec[:, j])))
    print(f"[{label}] DECOMP_MAX_ABS_IDENTITY_ERROR", f"{np.max(np.abs(ndec.sum(1) - nxt)):.3e}")
    shp = ndec[:, 2].sum() / tot; mns, mhs = np.median(ndec[:, 2]), np.median(hdec[:, 2])
    print(f"[{label}] SHAPE_SHARE_POOLED", f(shp), "LOC_ONLY_SHARE_POOLED", f(ndec[:, 0].sum() / tot))
    print(f"[{label}] MEDIAN_NEXT_SHAPE", f(mns), "MEDIAN_HALF_SHAPE", f(mhs), "RATIO", f(mns / mhs))
    for t_ in TYPES: pass
    return mn <= mh, shp < 0.15, mns <= mhs

print("SECTION gate_primary_logdays label=BURN-IN")
K1, K2, K3 = gate_block(Q, "LOG_ALL")
print("K1", K1, "K2", K2, "K3", K3)
print("SECTION gate_nongating_calm_2001_2006")
gate_block(Q, "LOG_CALM", wsel=lambda w: w <= pd.Timestamp("2006-12-29"))
print("SECTION gate_nongating_rank_metric")
gate_block(QR, "RANK_ALL")
# per-type next/half medians for primary (non-gating detail)
print("SECTION per_type_detail_nongating")
rng = np.random.default_rng(SEED)
for t in TYPES:
    nx = [w2sq(Q[t][w], Q[t][w + pd.Timedelta(days=7)]) for w in weeks if w in Q[t] and (w + pd.Timedelta(days=7)) in Q[t]]
    print("PER_TYPE_MEDIAN_NEXT", t, f(np.median(nx)), "n", len(nx))

# ---------------- forecasting baselines (burn-in) ----------------
print("SECTION baselines label=BURN-IN")
ALPHAS = [0.1, 0.2, 0.3, 0.5]
L = {k: {} for k in ["P", "EXP", "MA4"] + [f"EWMA{a}" for a in ALPHAS]}
for t in TYPES:
    past = []; ew = {a: None for a in ALPHAS}; exp = None; n_exp = 0
    for w in weeks:
        if w in Q[t] and past:
            y = Q[t][w]
            L["P"][(t, w)] = w2sq(past[-1], y)
            L["EXP"][(t, w)] = w2sq(exp, y)
            if len(past) >= 4: L["MA4"][(t, w)] = w2sq(bary(past[-4:]), y)
            for a in ALPHAS: L[f"EWMA{a}"][(t, w)] = w2sq(ew[a], y)
        if w in Q[t]:
            q = Q[t][w]; past.append(q)
            n_exp += 1; exp = q if exp is None else qmix(q, exp, 1.0 / n_exp)
            for a in ALPHAS: ew[a] = q if ew[a] is None else qmix(q, ew[a], a)
def wk_mean(model, w0, w1, need=("P", "EXP", "MA4")):
    out = {}
    for w in weeks:
        if not (w0 <= w <= w1): continue
        ts = [t for t in TYPES if all((t, w) in L[m] for m in (model,) + tuple(need))]
        if ts: out[w] = float(np.mean([L[model][(t, w)] for t in ts]))
    return pd.Series(out)
sel_w = (pd.Timestamp("2002-01-04"), pd.Timestamp("2004-12-31")); ev_w = (pd.Timestamp("2005-01-07"), BURN_LAST)
alpha_scores = {a: wk_mean(f"EWMA{a}", *sel_w).mean() for a in ALPHAS}
a_star = min(ALPHAS, key=lambda a: (round(alpha_scores[a], 12), a))
print("EWMA_ALPHA_SELECTION_2002_2004", " ".join(f"{a}:{f(s)}" for a, s in alpha_scores.items()), "ALPHA_STAR", a_star)
ev = {m: wk_mean(m, *ev_w) for m in ["P", "EXP", "MA4", f"EWMA{a_star}"]}
for m, s in ev.items(): print("EVAL_2005_2008 MEAN_LOSS", m, f(s.mean()), "n_weeks", len(s))
calm = (pd.Timestamp("2005-01-07"), pd.Timestamp("2006-12-29"))
for m in ["P", "EXP", f"EWMA{a_star}"]: print("EVAL_2005_2006_NONGATING MEAN_LOSS", m, f(wk_mean(m, *calm).mean()))
mP, mE, mX = ev["P"].mean(), ev[f"EWMA{a_star}"].mean(), ev["EXP"].mean()
SIGNAL = min(mP, mE) <= 0.90 * mX
print("RATIO_P_OVER_EXP", f(mP / mX), "RATIO_EWMA_OVER_EXP", f(mE / mX), "RATIO_EWMA_OVER_P", f(mE / mP))
print("FORECASTABLE_SIGNAL", "yes" if SIGNAL else "no")

# ---------------- power ----------------
print("SECTION planning_power label=PLANNING not_an_oos_result")
dser = (wk_mean("P", BURN_FIRST, BURN_LAST) - wk_mean("MA4", BURN_FIRST, BURN_LAST)).dropna()
scale = min(wk_mean(m, BURN_FIRST, BURN_LAST).mean() for m in ["P", "MA4", "EXP"])
for m in ["P", "MA4", "EXP"]: print("PROXY_MEAN_LOSS", m, f(wk_mean(m, BURN_FIRST, BURN_LAST).mean()))
dv = dser.values
X = np.c_[np.ones(len(dv) - 1), dv[:-1]]; coef = np.linalg.lstsq(X, dv[1:], rcond=None)[0]
res = dv[1:] - X @ coef; phi_d = float(coef[1]); sd_e = float(np.sqrt(res @ res / (len(res) - 2)))
print("PROXY_D_N", len(dv), "MEAN", f(dv.mean()), "SD", f(dv.std(ddof=1)), "AR1_PHI", f(phi_d), "RESID_SD", f(sd_e), "GAIN_SCALE", f(scale))
acf = [float(np.corrcoef(dv[k:], dv[:-k])[0, 1]) for k in (1, 2, 4, 13, 26)]
print("PROXY_D_ACF_LAGS_1_2_4_13_26", " ".join(f"{a:.4f}" for a in acf))
Tn = T_OOS; Lb = int(math.floor(math.sqrt(Tn)))
print("T", Tn, "L_BARTLETT", Lb)
def zstat(d, Lb):
    Tn = d.shape[1]; m = d.mean(1, keepdims=True); c = d - m; s2 = (c * c).mean(1)
    for j in range(1, Lb + 1): s2 = s2 + 2 * (1 - j / (Lb + 1)) * (c[:, j:] * c[:, :-j]).sum(1) / Tn
    return np.sqrt(Tn) * m[:, 0] / np.sqrt(np.maximum(s2, 1e-300))
def ar_paths(rng, n, Tn, phi, burn=200):
    e = rng.standard_normal((n, Tn + burn)); x = np.empty_like(e); x[:, 0] = e[:, 0] / math.sqrt(max(1 - phi * phi, 1e-12))
    for k in range(1, Tn + burn): x[:, k] = phi * x[:, k - 1] + e[:, k]
    return x[:, burn:]
def ar1_rows(x):
    a = x[:, :-1] - x[:, :-1].mean(1, keepdims=True); bb = x[:, 1:] - x[:, 1:].mean(1, keepdims=True)
    return (a * bb).sum(1) / (a * a).sum(1)
def cv_table(Tn, Lb, draws=20000, chunk=5000):
    grid = np.round(np.arange(-0.90, 0.951, 0.05), 2); c95, c975 = [], []
    rng = np.random.default_rng(SEED)
    for ph in grid:
        z = np.concatenate([zstat(ar_paths(rng, chunk, Tn, float(ph)), Lb) for _ in range(draws // chunk)])
        c95.append(np.quantile(z, .95)); c975.append(np.quantile(z, .975))
    return grid, np.array(c95), np.array(c975)
def run_power(Tn, label, gains=(0.0, 0.02, 0.05, 0.10), reps=2000, chunk=500, do_boot=True):
    Lb = int(math.floor(math.sqrt(Tn))); grid, c95, c975 = cv_table(Tn, Lb)
    print(f"[{label}] T", Tn, "L", Lb, "CV_AT_PHI0 95/97.5", f"{np.interp(0, grid, c95):.4f}", f"{np.interp(0, grid, c975):.4f}",
          "CV_AT_PROXY_PHI", f"{np.interp(phi_d, grid, c95):.4f}", f"{np.interp(phi_d, grid, c975):.4f}")
    out = {}
    for dgp in (["G", "B"] if do_boot else ["G"]):
        for g in gains:
            rng = np.random.default_rng(SEED); rej95 = rej975 = inc = 0
            for _ in range(reps // chunk):
                if dgp == "G":
                    d = ar_paths(rng, chunk, Tn, phi_d) * sd_e
                else:
                    base = dv - dv.mean(); n0 = len(base); d = np.empty((chunk, Tn))
                    for r in range(chunk):
                        idx = []; 
                        while len(idx) < Tn:
                            s0 = rng.integers(n0); bl = rng.geometric(1 / 13)
                            idx.extend(((s0 + np.arange(bl)) % n0).tolist())
                        d[r] = base[idx[:Tn]]
                d = d + g * scale
                z = zstat(d, Lb); ph = ar1_rows(d); bad = (ph <= -0.99) | (ph >= 0.99)
                rej95 += int(((z > np.interp(np.clip(ph, grid[0], grid[-1]), grid, c95)) & ~bad).sum())
                rej975 += int(((z > np.interp(np.clip(ph, grid[0], grid[-1]), grid, c975)) & ~bad).sum()); inc += int(bad.sum())
            out[(dgp, g)] = rej975 / reps
            print(f"[{label}] POWER dgp", dgp, "gain", f"{g:.2f}", "mu", f(g * scale), "at5pct", f"{rej95 / reps:.4f}", "at2.5pct", f"{rej975 / reps:.4f}", "incomplete", inc)
    return out
pw = run_power(Tn, "OOS_T")
pmin = min(pw[("G", 0.05)], pw[("B", 0.05)])
K4 = pmin < 0.50
print("POWER_MIN_G_B_AT_GAIN_0.05_2.5PCT", f"{pmin:.4f}", "K4", K4)
print("SECTION nongating_contrast_T50 (Y-9C-like length, Gaussian DGP only)")
run_power(50, "T50", gains=(0.05, 0.10), do_boot=False)

# ---------------- verdicts ----------------
print("SECTION verdicts")
usable_ok = all(usable[t].mean() >= 0.95 for t in TYPES)
oos_cov_ok = all(oos_ok[t] >= 0.95 for t in TYPES)
print("DATASET_CRITERIA a_xml_has_NAA_NA2 True(see facts) b_csv_pair_match_0.999845>=0.999 True(see facts)",
      "c_burnin_usable_ge95", usable_ok, "d_oos_days_ge95", oos_cov_ok, "e_public_url_200 True(checked 2026-10-09)")
DATASET = usable_ok and oos_cov_ok
print("OT_CLAIM", "KILLED" if (K1 or K2 or K3 or K4) else "CLEARED", "K1", K1, "K2", K2, "K3", K3, "K4", K4)
print("DATASET_USABLE", "yes" if DATASET else "no")
print("FORECASTABLE_SIGNAL", "yes" if SIGNAL else "no")
