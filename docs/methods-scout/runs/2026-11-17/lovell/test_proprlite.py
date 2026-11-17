"""Identity suite (from the 11-12 run), E4 parity, and speed. Writes eng_results.json."""
import json, time, numpy as np, pandas as pd
import proprlite as P
res = {}
r = np.random.default_rng(0)
x = np.exp(r.normal(0, 1, 200)); y = 3.7 * x
assert P.vlr(x, y) < 1e-14 and abs(P.phi(x, y)) < 1e-14 and abs(P.rho(x, y) - 1) < 1e-14
t = np.exp(r.normal(2, .5, 200)); Xa = np.column_stack([x*t, y*t, np.exp(r.normal(0, 1, 200))*t]); Xr = Xa / Xa.sum(1, keepdims=True)
assert abs(P.vlr(Xa[:, 0], Xa[:, 1]) - P.vlr(Xr[:, 0], Xr[:, 1])) < 1e-12
z = np.exp(r.normal(0, 1.7, 200)); assert abs(P.rho(x, z) - P.rho(z, x)) < 1e-14
C = P.clr(Xr); assert abs(P.vlr(Xr[:, 0], Xr[:, 1]) - np.var(C[:, 0]-C[:, 1], ddof=1)) < 1e-12
assert abs(P.rho(Xa[:, 0], Xa[:, 1]) - 1) < 1e-12 and abs(P.rho(Xr[:, 0], Xr[:, 1]) - 1) < 1e-12
L = np.log(Xr); R = P.pairwise_rho(L)
assert abs(R[0, 2] - P.rho(Xr[:, 0], Xr[:, 2])) < 1e-12   # vectorised == scalar
from statsmodels.stats.multitest import multipletests as _mt; _pp = np.random.default_rng(3).uniform(size=50); assert np.allclose(P.bh(_pp), _mt(_pp, method="fdr_bh")[1])
res['identity_suite'] = 'passed (7 identities + vectorised==scalar + BH)'
# E4 parity (public FR Y-9C proxy; same files as 2026-11-12)
D = '/workspace/scout/1112-adhoc/data/'
E = pd.read_csv(D + 'panel_E4.csv', index_col=0); M = pd.read_csv(D + 'market_q.csv', index_col=0)
S = E.values / E.values.sum(1, keepdims=True); names = list(E.columns)
i, j = names.index('JPM'), names.index('GS')
r_share = P.rho(S[:, i], S[:, j])
Xm = M.loc[E.index, ['vix', 'nasdaq_ret4', 'baa10y', 'eq_rev_ind_g4']].values.astype(float)
Rl = P.partial_level(S, Xm); r_part = P.rho_vec(Rl[:, i], Rl[:, j])
res['E4'] = dict(rho_share=r_share, target_share=-0.6976291186378243, err_share=abs(r_share + 0.6976291186378243),
                 rho_partial_level=r_part, target_partial=-0.8820532158226098, err_partial=abs(r_part + 0.8820532158226098))
Ri = P.partial_increment(S, Xm); o, p, _ = P.cyclic_shift_pvalue(Ri[:, i], Ri[:, j])
o2, p2, _ = P.cyclic_shift_pvalue(Rl[:, i], Rl[:, j])
res['E4']['rho_partial_increment'] = o; res['E4']['p_partial_increment_cyclic'] = p
res['E4']['p_partial_level_cyclic_exact'] = p2
assert res['E4']['err_share'] <= 1e-9 and res['E4']['err_partial'] <= 1e-9
# speed: 500 parts x 62 quarters, all 124,750 pairwise rho
W = np.exp(np.random.default_rng(1).normal(size=(62, 500)))
t0 = time.perf_counter(); Rw = P.pairwise_rho(P.clr(W)); dt = time.perf_counter() - t0
res['speed'] = dict(parts=500, T=62, pairs=500*499//2, seconds=dt, pass_under_1s=dt < 1.0)
json.dump(res, open('eng_results.json', 'w'), indent=1, default=float); print(json.dumps(res, indent=1, default=float))
