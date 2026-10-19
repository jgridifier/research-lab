# One-page cheat sheet

[← Back to the kit](README.md) · [Refresher](refresher.md)

> **Generic practice material for a Python quant coding interview. Synthetic data; illustrative scenarios; not investment advice; not affiliated with any employer.**

**Run sheet:** 0:00 format · 0:02 candidate background · 0:04 W1 (validation → P1) · W2 (simulation → P2) · W3 (frozen model → P3) · 0:12 version cell + P1 · **0:13 P1** (0:16 leak named, 0:19 `leak_test`, 0:22 fixed, 0:24 DM) · **0:25 P2** (0:29 `simulate`, 0:34 grid, 0:35 "severe but plausible?") · **0:38 P3** (0:41 basis+ridge, 0:45 λ time split, 0:47 "sign off?") · 0:49 close · 0:51 candidate's questions. **Fast:** CW / z-score question → frontier → P4 sliced-W mini or P7 PVM. **Stuck:** paste `leak_test` / accept `trough_loop` / paste `hinge_basis`+`fit_overlay`. **P1+P2 strong by 0:36:** swap P3 → P5.

| Pillar | Problems |
|---|---|
| A scenario design | P2 (grid, reverse stress), P4 (distance from history) |
| B challenger models | P1 (outcomes analysis), P3 (overlay on a frozen champion), P6 (internal data) |
| C optimization/simulation → decisions | P2 (breach frontier), P5 (LP duals, MILP), P4 (OT as an LP) |
| D AI apps for business users | P7 (PVM facts + narrative guardrail) |

| Topic | Formula / rule |
|---|---|
| Leak test | overwrite rows $>k$; forecasts with origin $\le k$ unchanged (compare by origin) |
| Oracle regressor | realized $x_{t+1}$ in a forecast of $y_{t+1}$: only for *conditional* evaluation, labeled |
| Affine invariance | OLS with intercept: $x \to a+bx$ leaves fits unchanged ⇒ full-sample z-score immaterial (not for ridge/PCA) |
| DM / HLN | $d_t=e_{1t}^2-e_{2t}^2$; $DM=\bar d/\sqrt{(\hat\gamma_0+2\sum_{k<h}\hat\gamma_k)/n}$; $\times\sqrt{(n+1-2h+h(h-1)/n)/n}$, $t_{n-1}$ |
| Clark–West | $f_t=e_s^2-[e_b^2-(\hat y_s-\hat y_b)^2]$, one-sided $t$ on $\bar f>0$ |
| Two-segment runoff | $g=(1-\beta)m$; $S'=S(1-\mu g-s_0)$; $R'=R(1-r_0-kg)+S\mu g$ (simultaneous; caps ≤ 1) |
| Grid shapes | `m[:,None,:]*(1-beta[None,:,None])` → `(ns, nb, H)`; loop over H only |
| Bisection | bracket, halve, $\log_2((hi-lo)/tol)$ steps; monotone ⇒ frontier |
| Ridge overlay | $v=(\Phi^\top\Phi+\lambda I)^{-1}\Phi^\top r$, $r=y-f_0$, $\phi_k=\max(m-\kappa_k,0)$, no intercept; λ on a time split |
| 1-D OT | $W_p^p=\frac1n\sum|x_{(i)}-y_{(i)}|^p$; $W_1=\int|F-G|$ |
| OT LP | $\min\langle C,P\rangle$, $P\mathbf1=a$, $P^\top\mathbf1=b$, $P\ge0$ |
| Sliced W2 | $SW_2^2=E_\theta W_2^2(\theta^\top X,\theta^\top Y)$; shift $a$ ⇒ $|a|^2/d$ |
| LP duals | shadow price = Δobjective per unit of RHS; check by re-solve at $b+1$ |
| MILP on/off | $m_iz_i\le x_i\le u_iz_i$, $\sum z\le K$, objective $v^\top x-f^\top z$ |
| PVM | vol $(\Sigma B_1-\Sigma B_0)\bar m_0$; mix $\Sigma B_1\Sigma(w_1-w_0)m_0$; rate $\Sigma B_1(m_1-m_0)$; sum = total |

| Task | API |
|---|---|
| No-look-ahead slice | `hist = df.iloc[:t+1]` |
| OLS | `np.linalg.lstsq(X, y, rcond=None)[0]`; `sm.OLS(y, X).fit().params` |
| Ridge | `np.linalg.solve(P.T@P + lam*np.eye(k), P.T@r)`; `Ridge(alpha=lam, fit_intercept=False)` |
| Time split | `TimeSeriesSplit(n_splits=…)` or last-block validation |
| Sort-based OT | `np.sort(X @ theta.T, axis=0)` |
| LP | `linprog(-v, A_ub=A, b_ub=b, bounds=bd, method="highs")`; `res.ineqlin.marginals` |
| MILP | `milp(c, constraints=[LinearConstraint(A, lb, ub)], integrality=mask, bounds=Bounds(l, u))` |
| SQL dedupe / gap | `ROW_NUMBER() OVER (PARTITION BY k ORDER BY posted_at DESC)`; `CASE WHEN LAG(m_idx) OVER w = m_idx-1 …` |
| Regex number | `r"[-+]?\$?(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(bn|m|%|bp)?"` |

**Red flags:** trusts the champion's RMSE · leak "found" by reading only, never tested · flags the z-score, misses the oracle · sequential compartment update · `np.vectorize` called vectorization · re-fits the frozen champion · shuffled CV for λ · λ chosen on the holdout · OT theory without code · LP sign errors · LAG without a gap check · LLM doing the arithmetic.
