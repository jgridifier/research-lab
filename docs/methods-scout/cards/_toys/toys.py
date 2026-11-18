#!/usr/bin/env python3
"""Toy examples printed on the research cards' "The math" tabs. Run: python3 toys.py
Pure Python + NumPy; every number on a card's toy box comes from this script."""
import math
import numpy as np

expit = lambda u: 1 / (1 + math.exp(-u))
logit = lambda p: math.log(p / (1 - p))
Phi = lambda t: 0.5 * (1 + math.erf(t / math.sqrt(2)))

print("== ecofolio: three programs on v = a m^z, a=0.04, z=1.5")
a, z, m = 0.04, 1.5, [1, 4, 16]
cv = lambda mm: math.sqrt(a * mm ** z) / mm
avg = sum(cv(x) for x in m) / 3
M, cvp = sum(m), 0.060
print([round(cv(x), 3) for x in m], "avg", round(avg, 3), "CV(M)", round(cv(M), 3),
      "PE_avgCV", round(avg / cvp, 2), "PE_mv", round(cv(M) / cvp, 2))

print("== pim: A={1.0,2.0} vs B={1.5,3.0,4.0}")
A, B = [1.0, 2.0], [1.5, 3.0, 4.0]
I = [1 if x < y else (0.5 if x == y else 0) for x in A for y in B]
pi = sum(I) / len(I)
print("PI", round(pi, 3), "beta", round(logit(pi), 2))
for p1, iqr in [(0.606, 1.8), (0.460, 2.5)]:
    print("per-unit", p1, "IQR", iqr, "-> per-IQR", round(expit(logit(p1) * iqr), 3))

print("== ebnm: x=(2,0.5,-0.5,3), s=1, normal prior")
x, s = [2.0, 0.5, -0.5, 3.0], 1.0
mu = sum(x) / 4
v = sum((xi - mu) ** 2 for xi in x) / 4
sig2 = max(0.0, v - s * s)
Bf = sig2 / (sig2 + s * s)
pm = [mu + Bf * (xi - mu) for xi in x]
psd = math.sqrt(sig2 * s * s / (sig2 + s * s))
lfsr = [min(Phi(-p / psd), 1 - Phi(-p / psd)) for p in pm]
print("mu", mu, "spread", round(v, 3), "sigma2", round(sig2, 3), "B", round(Bf, 3),
      "post", [round(p, 2) for p in pm], "sd", round(psd, 2), "lfsr", [round(l, 3) for l in lfsr])

print("== CRQA: a=(1,2,2,3,1), b=(2,2,3,1,1); DRP(k) = share of t with a_t == b_{t+k}")
aa, bb = [1, 2, 2, 3, 1], [2, 2, 3, 1, 1]
for k in (-2, -1, 0, 1, 2):
    pairs = [(t, t + k) for t in range(5) if 0 <= t + k < 5]
    hits = sum(aa[t] == bb[u] for t, u in pairs)
    print("k", k, f"{hits}/{len(pairs)}")

print("== IDR: x=(1,2,3,4), y=(0.5,2.0,1.0,3.0), isotonic in x (CDF non-increasing in x)")
def pava_nonincreasing(v):
    out = []
    for val in v:
        out.append([val, 1])
        while len(out) > 1 and out[-2][0] < out[-1][0]:
            m2, w2 = out.pop(); m1, w1 = out.pop()
            out.append([(m1 * w1 + m2 * w2) / (w1 + w2), w1 + w2])
    r = []
    for mval, w in out:
        r += [mval] * w
    return r
y = [0.5, 2.0, 1.0, 3.0]
for thr in sorted(set(y)):
    ind = [1 if yi <= thr else 0 for yi in y]
    print("z", thr, "1{y<=z}", ind, "IDR F(z)", pava_nonincreasing(ind))

print("== CCM: Sugihara-style coupled logistic maps, X drives Y (beta_yx = 0.1), E = 2")
n = 400
X = np.zeros(n); Y = np.zeros(n); X[0], Y[0] = 0.4, 0.2
for t in range(1, n):
    X[t] = 3.8 * X[t-1] * (1 - X[t-1])
    Y[t] = Y[t-1] * (3.5 - 3.5 * Y[t-1] - 0.1 * X[t-1])
def ccm(src, tgt, L, E=2, reps=50, seed=1):
    rng = np.random.default_rng(seed)
    Mf = np.column_stack([src[E-1-i:len(src)-i] for i in range(E)]); T = tgt[E-1:]
    rs = []
    for _ in range(reps):
        lib = rng.choice(len(Mf), L, replace=False)
        pred = []
        for t in range(len(Mf)):
            d = np.linalg.norm(Mf[lib] - Mf[t], axis=1); keep = lib != t
            dd, ll = d[keep], lib[keep]; o = np.argsort(dd)[:E+1]; d1 = max(dd[o[0]], 1e-12)
            w = np.exp(-dd[o] / d1); pred.append((w * T[ll[o]]).sum() / w.sum())
        rs.append(np.corrcoef(pred, T)[0, 1])
    return float(np.mean(rs))
for L in (10, 25, 100, 300):
    print("L", L, "Y-manifold recovers X (X->Y)", round(ccm(Y, X, L), 2), "| X-manifold recovers Y", round(ccm(X, Y, L), 2))

print("== kairos/EPPM: 3 months x 3 segments")
C = [[60, 30, 10], [40, 40, 20], [20, 30, 50]]
S = [[c / sum(r) for c in r] for r in C]
mean = [sum(S[i][j] for i in range(3)) / 3 for j in range(3)]
print("shares", [[round(v, 2) for v in r] for r in S], "column means", [round(v, 3) for v in mean])
print("EPPM", [[round(max(0, S[i][j] - mean[j]), 3) for j in range(3)] for i in range(3)])
def modes(seq):
    return sum(1 for i in range(len(seq)) if (i == 0 or seq[i] > seq[i-1]) and (i == len(seq)-1 or seq[i] >= seq[i+1]) and seq[i] > 0)
print("modes per segment in this order", [modes([S[i][j] for i in range(3)]) for j in range(3)])

print("== kairos/CA + event date on the same 3x3 toy")
N = np.array([[60, 30, 10], [40, 40, 20], [20, 30, 50]], float)
P = N / N.sum(); r = P.sum(1); c = P.sum(0)
Sres = np.diag(r ** -.5) @ (P - np.outer(r, c)) @ np.diag(c ** -.5)
U, s, Vt = np.linalg.svd(Sres)
sign = 1.0  # sign of a CA axis is arbitrary
Fr = (np.diag(r ** -.5) @ U * s)[:, 0]
Gstd = (np.diag(c ** -.5) @ Vt.T)[:, 0]
print("inertia share axis1", round(s[0] ** 2 / (s ** 2).sum(), 3))
print("row coords axis1", Fr.round(3), "check via profiles", ((N / N.sum(1, keepdims=True)) @ Gstd).round(3))
t = np.array([2018, 2020, 2022.]); X = np.c_[np.ones(3), Fr]
b = np.linalg.lstsq(X, t, rcond=None)[0]
print("event model beta", b.round(3), "fitted", (X @ b).round(2))
new = np.array([50, 35, 15.]); f = (new / new.sum()) @ Gstd
print("new mix 50/35/15: coord", round(f, 3), "event date", round(b[0] + b[1] * f, 2))

print("== Lovell rho: clr series u, v over 4 periods; market m = (0,1,2,3)")
m = np.array([0, 1, 2, 3.])
u = 0.5 * m + np.array([0.1, -0.1, -0.1, 0.1]); v = -0.5 * m + np.array([0.1, -0.1, 0.1, -0.1])
sv = lambda x: np.var(x, ddof=1)
rho = lambda a, b: 1 - sv(a - b) / (sv(a) + sv(b))
print("u", u.round(2), "v", v.round(2), "var u", round(sv(u), 4), "var v", round(sv(v), 4), "var(u-v)", round(sv(u - v), 4), "raw rho", round(rho(u, v), 3))
Z = np.c_[np.ones(4), m]; ru = u - Z @ np.linalg.lstsq(Z, u, rcond=None)[0]; rv = v - Z @ np.linalg.lstsq(Z, v, rcond=None)[0]
print("level residuals u", ru.round(3), "v", rv.round(3), "level-partial rho", round(rho(ru, rv), 3))
du, dv, dm = np.diff(u), np.diff(v), np.diff(m)
Zi = np.c_[np.ones(3), dm]
print("increments du", du.round(2), "dv", dv.round(2), "dm", dm, "(dm is constant, so [1, dm] is rank 1: partial on increments = demeaned increments)")
eu, ev = du - du.mean(), dv - dv.mean()
print("demeaned increments u", eu.round(3), "v", ev.round(3), "increment-partial rho", round(rho(eu, ev), 3))

print("== ecotraj directionality: path y1=(0,0), y2=(1,0), y3=(2,1)")
y = np.array([[0, 0], [1, 0], [2, 1.]])
s12 = np.linalg.norm(y[1] - y[0]); s23 = np.linalg.norm(y[2] - y[1])
a = y[1] - y[0]; b = y[2] - y[1]; th = np.degrees(np.arccos(a @ b / (s12 * s23)))
print("s12", round(s12, 3), "s23", round(s23, 3), "theta", round(th, 1), "dir", round(1 - th / 180, 3))
print("sign-flip null with 2 steps: flips (+,+) dir", round(1 - th / 180, 3), "(+,-) or (-,+): angle", round(180 - th, 1), "dir", round(1 - (180 - th) / 180, 3), "(-,-) dir", round(1 - th / 180, 3))
print("p = share of the 4 sign vectors with dir >= observed =", 2 / 4)

print("== pim firm-clustered meat: firms A,B,C in two years; pair scores u (one covariate)")
u1 = {('A', 'B'): 0.2, ('A', 'C'): -0.1, ('B', 'C'): 0.3}; u2 = {('A', 'B'): 0.25, ('A', 'C'): -0.05, ('B', 'C'): 0.2}
def meat(groups):  # groups: list of (pair key in cluster ids, u)
    S = {}; V = {}
    for (a, b), u in groups:
        S[a] = S.get(a, 0) + u; S[b] = S.get(b, 0) + u; k = tuple(sorted((a, b))); V[k] = V.get(k, 0) + u
    return sum(s * s for s in S.values()) - sum(v * v for v in V.values())
fy = [((a + '1', b + '1'), u) for (a, b), u in u1.items()] + [((a + '2', b + '2'), u) for (a, b), u in u2.items()]
fm = [((a, b), u) for (a, b), u in list(u1.items()) + list(u2.items())]
print("firm-year meat (pim sandwich)", round(meat(fy), 4), " firm meat", round(meat(fm), 4), " ratio", round(meat(fm) / meat(fy), 3))

print("== ECA: T=10 weeks, A events {3,7}, B events {2,6,9}, delT=1, tau=0")
T, Aev, Bev, dT = 10, [3, 7], [2, 6, 9], 1
kp = sum(any(t - dT <= s <= t for s in Bev) for t in Aev)
kt = sum(any(s <= t <= s + dT for t in Aev) for s in Bev)
q_p = (1 - (dT + 1) / T) ** len(Bev); q_t = (1 - (dT + 1) / T) ** len(Aev)
pp = sum(math.comb(len(Aev), k) * (1 - q_p) ** k * q_p ** (len(Aev) - k) for k in range(kp, len(Aev) + 1))
pt = sum(math.comb(len(Bev), k) * (1 - q_t) ** k * q_t ** (len(Bev) - k) for k in range(kt, len(Bev) + 1))
print("K_p", kp, "r_p", kp / len(Aev), "K_t", kt, "r_t", round(kt / len(Bev), 3),
      "P(no B in a window) =", round(q_p, 3), "Poisson p_prec", round(pp, 3), "p_trig", round(pt, 3))

print("== STATIS: three 3x3 correlation matrices (years); R3 is the odd one")
R = [np.array([[1, .8, .2], [.8, 1, .1], [.2, .1, 1]]), np.array([[1, .7, .3], [.7, 1, .2], [.3, .2, 1]]),
     np.array([[1, .1, .6], [.1, 1, .5], [.6, .5, 1]])]
J = np.eye(3) - np.ones((3, 3)) / 3
S = [J @ r @ J for r in R]; S = [s / np.linalg.eigvalsh(s)[-1] for s in S]
rvf = lambda A, B: np.trace(A @ B) / math.sqrt(np.trace(A @ A) * np.trace(B @ B))
C = np.array([[rvf(a, b) for b in S] for a in S])
w, U = np.linalg.eigh(C); u = U[:, -1] * np.sign(U[:, -1].sum()); alpha = u / u.sum()
Sp = sum(a * s for a, s in zip(alpha, S))
print("RV matrix", C.round(3).tolist(), "weights", alpha.round(3).tolist(),
      "RV to compromise", [round(float(rvf(s, Sp)), 3) for s in S])

print("== STEM: 4 programs x 3 years (log levels), two model profiles (0,1,2) up and (0,-1,0) dip")
X = np.array([[10.0, 10.2, 10.5], [8.0, 8.3, 8.5], [9.0, 8.7, 9.1], [7.0, 7.4, 7.2]])
P = np.array([[0, 1, 2], [0, -1, 0]], float)
def assign(X):
    V = X - X[:, [0]]
    return [int(np.argmax([np.corrcoef(v, p)[0, 1] for p in P])) for v in V]
lab = assign(X); cnt = np.bincount(lab, minlength=2)
import itertools
perms = list(itertools.permutations(range(3)))
exp = sum(np.bincount(assign(X[:, list(q)]), minlength=2) for q in perms) / len(perms)
btail = lambda x, n, p: sum(math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(x, n + 1))
pv = [btail(int(cnt[i]), 4, exp[i] / 4) for i in range(2)]
print("assigned", lab, "counts", cnt.tolist(), "expected over 6 orderings", [round(float(e), 3) for e in exp],
      "binomial p", [round(float(v), 3) for v in pv])

print("== Hysteresis index (Lloyd 2016): one storm, Q and C at 5 weekly steps; C peaks one week after Q")
q = np.array([1.0, 3.0, 5.0, 2.0, 1.0]); c = np.array([2.0, 2.0, 4.0, 6.0, 2.0])
qn = (q - q.min()) / np.ptp(q); cn = (c - c.min()) / np.ptp(c)
print("Q norm", qn.round(3).tolist(), "C norm", cn.round(3).tolist())
def limb(qs, cs, lev):
    for i in range(len(qs) - 1):
        a, b = qs[i], qs[i + 1]
        if (a - lev) * (b - lev) <= 0 and a != b: return cs[i] + (cs[i + 1] - cs[i]) * (lev - a) / (b - a)
k = int(np.argmax(q)); vals = []
for lev in [0.25, 0.5, 0.75]:
    r = limb(qn[:k + 1], cn[:k + 1], lev); f = limb(qn[k:], cn[k:], lev); vals.append(r - f)
    print("Q level", lev, "C rising", round(r, 3), "C falling", round(f, 3), "HI_j", round(r - f, 3))
print("HI (mean of 3 levels)", round(float(np.mean(vals)), 3), " FI = C_norm(peak) - C_norm(start) =", round(float(cn[k] - cn[0]), 3))
