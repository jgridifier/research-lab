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

print("== ECA deep dive (2026-11-19): partial ECA and the Hawkes bridge, same toy")
Cev = [3]  # a confounder event C in week 3
keep = [t for t in Aev if not any(t - dT <= c <= t for c in Cev)]
kpc = sum(any(t - dT <= s <= t for s in Bev) for t in keep)
print("partial ECA: A events with no C in [t-dT, t]:", keep, "K", kpc, "r_p(A|B, not C)", kpc / len(keep))
mu, w, rt_obs = 0.10, dT + 1, 0.40  # background A rate per week, window length, observed trigger rate
r0 = 1 - math.exp(-mu * w)
Phi = -math.log(1 - rt_obs) - mu * w
print("Hawkes bridge: null trigger rate 1-exp(-mu*w) =", round(r0, 3), " implied kernel mass Phi =", round(Phi, 3),
      " window intensity multiple (mu*w+Phi)/(mu*w) =", round((mu * w + Phi) / (mu * w), 2),
      " check E[r_t] =", round(1 - math.exp(-mu * w - Phi), 3))

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

print("== Poset ranking (2026-11-19): 4 firms, 2 stress indicators (higher = more stressed); A=(1,1), B=(2,3), C=(3,2), D=(4,4)")
import itertools
F = {"A": (1, 1), "B": (2, 3), "C": (3, 2), "D": (4, 4)}
names = list(F)
below = {(u, v) for u in names for v in names if u != v and all(a <= b for a, b in zip(F[u], F[v])) and F[u] != F[v]}
print("dominance pairs (less stressed, more stressed):", sorted(below), "incomparable:", [(u, v) for u, v in itertools.combinations(names, 2) if (u, v) not in below and (v, u) not in below])
ext = [p for p in itertools.permutations(names) if all(p.index(u) < p.index(v) for u, v in below)]
print("linear extensions (low to high stress):", ["".join(p) for p in ext])
er = {u: sum(p.index(u) + 1 for p in ext) / len(ext) for u in names}
print("expected stress ranks", er, " P(rank of B = 2) =", sum(p.index("B") == 1 for p in ext) / len(ext))
pay = {"A": 3.0, "B": 1.0, "C": 2.0, "D": 0.5}
conc = sum(pay[v] < pay[u] for u, v in below) / len(below)
print("payouts", pay, " dominance concordance (more stressed pays less):", conc)
print("trade-off pair B vs C: indicator 1 says C more stressed -> C pays", pay["C"], "vs B", pay["B"], "(disagrees); indicator 2 says B more stressed -> B pays less (agrees)")
ideals = [frozenset(s) for k in range(5) for s in itertools.combinations(names, k) if all((u in s) for (u, v) in below if v in s)]
print("ideals (downsets):", ["".join(sorted(s)) or "{}" for s in ideals], "count", len(ideals))

print("== Phylogenetic signal / LIPA (2026-11-19): tree ((p1,p2),(p3,p4)), sister-only weights; slopes x = (0.10, 0.08, -0.02, 0.06)")
x = np.array([0.10, 0.08, -0.02, 0.06]); W = np.array([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], float)
z = (x - x.mean()) / x.std()
lag = W @ z
I_loc = z * lag
I_glob = (len(x) / W.sum()) * (z @ W @ z) / (z @ z)
print("mean", round(x.mean(), 4), "z", z.round(3).tolist(), "neighbour z", lag.round(3).tolist(), "local I_i = z_i * lag_i", I_loc.round(3).tolist(), "global Moran I", round(I_glob, 3))
print("program minus its sister:", (x - W @ x).round(3).tolist())

print("== Liang-Kleeman information flow (2026-11-20): X_{t+1} = A X_t + e_t, A = [[0.5, 0.3], [0, 0.5]], e ~ N(0, I); x2 drives x1, not the reverse")
A = np.array([[0.5, 0.3], [0.0, 0.5]])
S = np.eye(2)
for _ in range(500): S = A @ S @ A.T + np.eye(2)   # stationary covariance (discrete Lyapunov)
D = A - np.eye(2)                                     # Euler drift, dt = 1
T21 = D[0, 1] * S[0, 1] / S[0, 0]; T12 = D[1, 0] * S[1, 0] / S[1, 1]
print("stationary cov", S.round(4).tolist())
print("T(2->1) = a12 * s12 / s11 =", round(D[0, 1], 3), "*", round(S[0, 1], 4), "/", round(S[0, 0], 4), "=", round(T21, 4), " T(1->2) =", round(T12, 4))
dH1 = D[0, 0]; noise1 = 1.0 / (2 * S[0, 0])
Z1 = abs(dH1) + abs(T21) + abs(noise1)
print("self term dH1*/dt = a11 =", round(dH1, 3), " noise term = g11/(2 s11) =", round(noise1, 4), " normalizer Z1 =", round(Z1, 4), " tau(2->1) = T/Z1 =", round(T21 / Z1, 4))
A2 = np.array([[0.5, 0.3], [-0.3, 0.5]]); S2 = np.eye(2)
for _ in range(500): S2 = A2 @ S2 @ A2.T + np.eye(2)
print("rotation case A = [[0.5,0.3],[-0.3,0.5]]: s12 =", round(S2[0, 1], 6), "so T(2->1) = 0.3 * s12 / s11 =", round(0.3 * S2[0, 1] / S2[0, 0], 6), "although the Granger coefficient a12 = 0.3 is not zero")

print("== NCA CE-FDH (2026-11-20): 6 firm-years, x = min stressed CET1 (%), y = payout/RWA (%)")
x = np.array([5.0, 6.0, 7.0, 8.0, 9.0, 10.0]); y = np.array([0.4, 0.2, 1.0, 0.6, 1.5, 0.9])
o = np.argsort(x); c = np.maximum.accumulate(y[o])
print("ceiling c(x) = max y among x_k <= x:", dict(zip(x[o].tolist(), c.tolist())))
edges = np.append(x[o], x.max()); zone = float(np.sum((y.max() - c) * np.diff(edges)))
scope = float((x.max() - x.min()) * (y.max() - y.min()))
print("empty zone =", round(zone, 3), " scope =", round(scope, 3), " effect size d = zone/scope =", round(zone / scope, 3))
need = {v: float(x[o][np.argmax(c >= v)]) for v in [0.5, 1.0, 1.5]}
print("bottleneck: payout >= v needs x >=", need, " Pearson r =", round(float(np.corrcoef(x, y)[0, 1]), 3))

print("== ICCF (2026-11-22): driver x at t = 0..9 (step 1); response y sampled at t = 0.5, 2.5, ..., 8.5 equals x delayed by 2 (linear interpolation)")
tx = np.arange(10.0); xv = np.array([0, 1, 3, 2, 4, 6, 5, 7, 6, 8], float)
ty = np.arange(0.5, 9.0, 2.0); yv = np.interp(ty - 2.0, tx, xv)
def r_side(tA, A, tB, B, tau):
    # interpolate B at tA + tau, keep points inside B's span, Pearson r
    s = tA + tau; ok = (s >= tB.min()) & (s <= tB.max())
    return float(np.corrcoef(A[ok], np.interp(s[ok], tB, B))[0, 1]), int(ok.sum())
for tau in [0.0, 1.0, 2.0, 3.0]:
    r1, n1 = r_side(tx, xv, ty, yv, tau); r2, n2 = r_side(ty, yv, tx, xv, -tau)
    print(f"tau={tau}: r(x(t), y(t+tau) interp) = {r1:.3f} (n={n1}); r(y(t), x(t-tau) interp) = {r2:.3f} (n={n2}); ICCF = mean = {(r1 + r2) / 2:.3f}")

print("== L-moments, discordancy, heterogeneity (2026-11-22): one site x = (0.9, 1.0, 1.1, 1.4)")
xs = np.sort(np.array([0.9, 1.0, 1.1, 1.4])); n = len(xs); i = np.arange(n)
b0 = xs.mean(); b1 = np.sum(i / (n - 1) * xs) / n; b2 = np.sum(i * (i - 1) / ((n - 1) * (n - 2)) * xs) / n
l1, l2, l3 = b0, 2 * b1 - b0, 6 * b2 - 6 * b1 + b0
print("b0, b1, b2 =", round(b0, 4), round(b1, 4), round(b2, 4), " l1 =", round(l1, 4), " l2 =", round(l2, 4), " l3 =", round(l3, 4), " L-CV t = l2/l1 =", round(l2 / l1, 4), " L-skew t3 =", round(l3 / l2, 4))
print("check: l2 = half the mean |xi - xj| over pairs =", round(np.mean([abs(a - b) for k, a in enumerate(xs) for b in xs[k + 1:]]) / 2, 4))
u = np.array([[0.10, 0.0, 0.10], [0.05, 0.1, 0.12], [0.08, -0.1, 0.11], [0.06, 0.05, 0.10], [0.20, 0.3, 0.15]])  # (t, t3, t4) for 5 sites
d = u - u.mean(0); A = d.T @ d
Di = len(u) / 3 * np.einsum("ij,jk,ik->i", d, np.linalg.inv(A), d)
print("five sites (t, t3, t4):", u.tolist(), " D_i =", Di.round(3).tolist(), " sum =", round(Di.sum(), 3), "(always = N) max possible D_i = (N-1)/3 =", round((len(u) - 1) / 3, 3))
nrec = np.array([5, 5, 5, 5, 5]); tR = np.sum(nrec * u[:, 0]) / nrec.sum()
V = np.sqrt(np.sum(nrec * (u[:, 0] - tR) ** 2) / nrec.sum())
print("regional L-CV tR =", round(tR, 4), " observed dispersion V =", round(V, 4), " H1 = (V - mean V_sim) / sd V_sim, with V_sim from a kappa fitted to the regional L-moments (not run in the toy)")
