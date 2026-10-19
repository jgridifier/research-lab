# Refresher: methods and reference-solution walkthroughs

[← Back to the kit](README.md) · [Cheat sheet](cheatsheet.md)

> **Generic practice material for a Python quant coding interview. Synthetic data; illustrative scenarios; not investment advice; not affiliated with any employer.**

Plain-language summaries you can use to explain or check something mid-interview. Each subsection ends with the one-line answer you'd want from the candidate.

## 3.1 Backtests, look-ahead and the perturbation leak test

- **Rolling-origin (expanding-window) backtest:** for each origin $t$, slice the data to $\le t$ (`hist = df.iloc[:t+1]`), fit, forecast $t+h$, store the error. Everything (transforms, model selection, the benchmark's mean) must use `hist` only.
- **The perturbation test** is the general-purpose leak detector: overwrite every observation after $k$ with junk and re-run. Forecasts with origin $\le k$ must be bit-for-bit unchanged. It catches leaks you can't see in the code (a helper that reads the full frame, a cached full-sample statistic). Compare by **origin**, not by row position.
- **Oracle regressor:** using the realized $x_{t+1}$ to forecast $y_{t+1}$. Legitimate only in a *conditional* evaluation ("if the scenario path is right, how good is the model?"), which is how stress-test models are used; it must be labeled as such and never reported as forecast accuracy. In P1 it cuts RMSE from ≈ 0.65 to ≈ 0.39.
- **Material vs immaterial:** an affine transform of a regressor ($a + b x$) leaves OLS fitted values unchanged when there's an intercept, so a full-sample z-score doesn't change OLS forecasts. It *does* matter for penalized regressions, PCA/factor extraction, nonlinear transforms (logs of a demeaned series), and anything thresholded. Validators who flag everything equally lose credibility.
- **Other leak sources to list:** full-sample model or lag selection; two-sided filters (HP, centered moving averages); seasonal adjustment with full-sample factors; revised data vintages (use what was published at the origin); survivorship.
- **Model-risk vocabulary** (useful for W1): SR 11-7 (Fed/OCC, 2011) organizes validation into *conceptual soundness*, *ongoing monitoring* and *outcomes analysis* (backtesting, benchmarking against alternative models). 

*Candidate one-liner:* "I don't argue about leaks; I scramble the future and see what moves."

## 3.2 Forecast comparison: metrics, Diebold–Mariano, Clark–West

- $\text{RMSE} = \sqrt{\overline{e^2}}$ (penalizes big misses), $\text{MAE} = \overline{|e|}$, $R^2_{OS} = 1 - \sum e_m^2/\sum e_b^2$. Avoid MAPE for growth rates (explodes near zero).
- **DM:** $d_t = e_{1t}^2 - e_{2t}^2$; $DM = \bar d / \sqrt{\widehat{LRV}/n}$, $\widehat{LRV} = \hat\gamma_0 + 2\sum_{k=1}^{h-1}\hat\gamma_k$. Negative ⇒ model 1 better. **HLN** small-sample factor $\sqrt{(n+1-2h+h(h-1)/n)/n}$ and $t_{n-1}$ critical values.
- **Nested models** (the challenger contains the benchmark): DM is undersized; use **Clark–West**, $f_t = e_s^2 - [e_b^2 - (\hat y_s - \hat y_b)^2]$, one-sided $t$ on $\bar f > 0$.
- DM tests *forecasts*, not models. With ~80 OOS points, report stability across split points.

*Candidate one-liner:* "DM on the loss differential with HAC variance, HLN for small n, Clark–West if nested."

## 3.3 Compartmental (stock-flow) scenario models

- **Structure:** balances in compartments (S stable, R rate-sensitive) with flows that are fractions of start-of-period balances. Same mathematics as any discrete-time compartmental model: $S \to R$ migration is the transition, driven by a "force" (here the rate gap $g = (1-\beta)m$).
- **Simultaneous update:** compute all flows from the start-of-quarter balances, then update. Sequential updates (using the new $S$ in the $R$ equation) silently break conservation.
- **Caps:** each outflow fraction ≤ 1 and total outflow from a compartment ≤ 1, otherwise balances go negative under extreme shocks.
- **Sanity tests before any chart:** (1) conservation with outflows off; (2) non-negativity under extreme parameters; (3) monotonicity (bigger shock ⇒ lower trough; higher pass-through ⇒ higher trough); (4) one quarter by hand.
- **Vectorizing a grid:** broadcast parameters over axes, loop only over time. Shapes: `m` is `(n_shock, H)`; the gap is `m[:, None, :] * (1 - beta[None, :, None])` → `(n_shock, n_beta, H)`; the state is `(n_shock, n_beta)`. `np.vectorize` is not vectorization (it's a Python loop).
- **Reverse stress test:** instead of "what happens under scenario X?", ask "what scenario breaks limit L?" With a monotone response, bisection on the shock gives the breach frontier per pass-through. Bisection needs $\log_2((hi-lo)/tol)$ steps and always converges on a bracketed root.
- **Plausibility:** grid corners aren't automatically plausible; anchor to historical episodes (the 2022–23 hiking cycle: ~5pp in ~16 months; deposit betas that rose through the cycle) or measure distance from history (P4).

*Candidate one-liner:* "Simultaneous update, caps, conservation check, broadcast over the grid, loop over time, then bisect for the breach."

## 3.4 Overlays on a frozen champion: ridge, hinge bases, time-ordered validation

- **Overlay = residual model:** $\hat y = f_0(x) + \delta(x)$ with $f_0$ frozen; fit $\delta$ to $r = y - f_0(x)$.
- **Hinge (ReLU) basis:** $\phi_k(m) = \max(m - \kappa_k, 0)$. A linear combination is a piecewise-linear function with kinks at the knots, and it's **exactly zero** for $m \le \min_k \kappa_k$. That's the do-no-harm property by construction. No intercept, or the old regime shifts.
- **Ridge:** $v = (\Phi^\top\Phi + \lambda I)^{-1}\Phi^\top r$. Shrinks toward $v = 0$, i.e. toward the champion. $\lambda \to \infty$ gives the champion; $\lambda \to 0$ gives OLS on residuals. Bayesian reading: Gaussian prior $v \sim N(0, \sigma^2/\lambda\, I)$; the posterior mean is the ridge solution.
- **Choosing λ in time series:** fit on the earlier block, score on the later block (or `sklearn.model_selection.TimeSeriesSplit`), pick λ, refit on the full training window, then evaluate *once* on the untouched holdout. Shuffled K-fold leaks the future when regressors trend.
- **Extrapolation:** a hinge above the training range has no data, so ridge sets its coefficient ≈ 0, and the overlay extrapolates linearly from the last active segment. In P3 the training rates stop near 4.5% and the holdout goes to 5.5%: say so in the sign-off.
- **Governance:** an overlay that changes model output is itself a model under SR 11-7-style MRM (documentation, validation, monitoring); management overlays aren't exempt.

*Candidate one-liner:* "Model the champion's residual, make the correction zero where the champion is trusted, shrink toward zero, choose λ in time order."

## 3.5 Optimal transport, briefly

- **Kantorovich problem:** $W_p(\mu,\nu)^p = \min_{P \ge 0,\ P\mathbf 1 = a,\ P^\top\mathbf 1 = b} \langle C, P\rangle$ with $C_{ij} = |x_i - y_j|^p$. It's a **linear program** with $nm$ variables and $n+m$ equality constraints (one redundant).
- **1-D closed form:** the optimal coupling is monotone, so $W_p^p = \int_0^1 |F^{-1}(u) - G^{-1}(u)|^p du$ ⇒ for equal-size samples, mean of $|x_{(i)} - y_{(i)}|^p$ over sorted samples. For $p = 1$ also $W_1 = \int |F(t) - G(t)|\,dt$ (histogram version in P4).
- **Dual:** $\max_{f,g} \sum a_i f_i + \sum b_j g_j$ s.t. $f_i + g_j \le C_{ij}$; for $W_1$ this is the sup over 1-Lipschitz functions (Kantorovich–Rubinstein).
- **Sliced Wasserstein:** average the 1-D $W_2^2$ of projections on random unit directions θ: $SW_2^2 = E_\theta[W_2^2(\theta_\#\mu, \theta_\#\nu)]$. Cost $O(L\, n\log n)$ for L projections. For a pure shift $a$: $SW_2^2 = E[(\theta^\top a)^2] = |a|^2/d$.
- **Scaling:** LP is fine for a few hundred points per side; beyond, use sliced W or entropic OT (Sinkhorn: iterative scaling, `POT` library outside CoderPad).
- **Scenario use:** W between a scenario generator's joint distribution and history quantifies "how unusual overall"; pair with tail metrics, since W averages.

*Candidate one-liner:* "Sort in 1-D, project and sort in d-D, and in general it's an LP on the transport plan."

## 3.6 LP and MILP in scipy

- **`linprog(c, A_ub, b_ub, A_eq, b_eq, bounds, method="highs")`** *minimizes* $c^\top x$; negate to maximize; write $\ge$ rows as negated $\le$ rows.
- **Duals** (scipy ≥ 1.7, HiGHS): `res.ineqlin.marginals` and `res.eqlin.marginals` are $\partial(\text{min objective})/\partial b$, so for a maximization written as min of $-v^\top x$, the shadow price of a $\le$ row is `-marginal`. Always confirm by finite difference (re-solve with $b + 1$), as P5 does.
- **Reading duals for a planner:** budget dual = value of one more unit of budget; a binding floor's dual = what the regulation costs per unit. Zero dual = non-binding.
- **`milp(c, constraints=[LinearConstraint(A, lb, ub), ...], integrality=mask, bounds=Bounds(l, u))`** (scipy ≥ 1.9). On/off logic with natural bounds: $x_i \le u_i z_i$, $x_i \ge m_i z_i$, $z_i \in \{0,1\}$; cardinality $\sum z_i \le K$; set-up costs $-f^\top z$ in the objective.
- **Verification:** the LP relaxation is an upper bound; for small n enumerate the binaries (with $z$ fixed, a unit-cost box-constrained LP is solved greedily).
- **Why greedy fails:** fixed costs and minimum scales make the problem lumpy (knapsack), so ratio-ordering can be arbitrarily bad.
- Outside CoderPad: Pyomo or cvxpy for modeling; HiGHS, OR-Tools CP-SAT, Gurobi for solving.

*Candidate one-liner:* "LP for the continuous plan and its prices, binaries for on/off decisions, and always a bound or brute force to check."

## 3.7 SQL window functions on ledger data

- `ROW_NUMBER() OVER (PARTITION BY key ORDER BY posted_at DESC)` then `WHERE rn = 1` in an outer query: latest posting wins.
- `LAG(x) OVER (PARTITION BY cc ORDER BY m_idx)` counts **rows**; build `m_idx = year*12 + month` and require `LAG(m_idx) = m_idx − 1` for a true month-over-month.
- Running totals: `SUM(x) OVER (PARTITION BY cc, yr ORDER BY m_idx ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` restarts each year.
- Re-orgs: map *before* summing (`LEFT JOIN cc_map … COALESCE(new_cc, cost_center)`), otherwise you compare different perimeters across time.
- Window functions need SQLite ≥ 3.25; `QUALIFY` exists in Snowflake/BigQuery/Databricks but not SQLite or Postgres.

*Candidate one-liner:* "Dedupe with ROW_NUMBER, map then sum, and never trust LAG without a gap check."

## 3.8 Price/volume/mix and guardrails for LLM narratives

- With $B$ balances, $m$ margins, $w = B/\sum B$: total $\Delta NII = \sum B_1 m_1 - \sum B_0 m_0$ splits **exactly** into volume $(\sum B_1 - \sum B_0)\,\bar m_0$, mix $\sum B_1 \sum_i (w_{1i} - w_{0i}) m_{0i}$, and rate $\sum_i B_{1i}(m_{1i} - m_{0i})$ (divide by 100 for % margins). Order matters (rate last here); state the convention.
- **Guardrail pattern for a finance AI app:** compute facts deterministically → the LLM writes only from a facts table → a checker extracts every number and direction word and matches it to a fact (tolerance for rounding) → unmatched numbers or contradicted directions block or flag the draft → human approval → log rejections and measure edit rates.
- What regex checks miss: right number on the wrong driver, unsupported causal claims, rounding games. Stronger: structured output with fact IDs, templated sentences, or constrained decoding.

*Candidate one-liner:* "The model can phrase it; it can't compute it. Every number in the narrative must trace to a fact."

## 3.9 Walking through the reference solutions, line by line

Read these alongside the code in [§2 of the README](README.md#2-problems). Function names refer to the files in [`solutions/`](solutions/).

### P1 `p1_champion_outcomes.py`

1. **`make_data`**: $x_t = 0.6x_{t-1} + \eta_t$ and $y_t = 0.5 + 0.4y_{t-1} - 1.5x_t - 0.6x_{t-1} + e_t$. Contemporaneous $x$ matters a lot, so the oracle leak is large and visible.
2. **`champion_backtest`** (the handed-over code): `xs = (x − mean)/std` on the **full sample** (the red herring). Inside the loop, `X` has columns `1, y_{s-1}, xs_s, xs_{s-1}` for rows $s = 1..t$, fitted by `lstsq`. The forecast row `xrow = [1, y_t, xs_{t+1}, xs_t]` uses **$x_{t+1}$**: the oracle leak.
3. **`leak_test`**: run the backtest on the original frame; copy the frame and set `bad.iloc[k+1:] = junk`; run again; keep only rows with `origin <= k` in both; return True if the forecasts differ (or the counts differ). Exact comparison with `atol=1e-10`, since a non-leaky backtest is deterministic on identical inputs.
4. **`fixed_backtest`**: `hist = df.iloc[:t+1]` is the no-look-ahead line. Then (1) an AR(1) for $x$ on `hist`: `ax = ols([1, x_{s-1}], x_s)`, `x_next = ax[0] + ax[1]*x_t`; (2) the same champion regression on `hist`; (3) the forecast row `[1, y_t, x_next, x_t]`. Benchmarks `rw = y_t` and `mean = hist mean` also use only `hist`.
5. **`error_table`**: RMSE and MAE per column.
6. **`diebold_mariano`**: loss differential `d = e1² − e2²`, centred autocovariances to lag h−1, long-run variance (Bartlett fallback if non-positive), the HLN factor, then the $t_{n-1}$ p-value (normal via `math.erf` if scipy is missing).
7. **`_tests`**: the champion fails the leak test and the fixed version passes; the oracle RMSE is < 75% of the honest one (0.393 vs 0.648); the honest model beats RW (0.800) and the mean (1.209); DM vs RW rejects (stat −3.07, p 0.003); DM is antisymmetric; z-scoring $x$ leaves the honest forecasts unchanged (affine invariance); a champion variant with the z-score but no oracle passes the leak test; OLS matches statsmodels.

### P2 `p2_deposit_runoff_scenarios.py`

1. **`PARAMS`**: S0 = 700, R0 = 300, m0 = 0.5%, ramp = 2 quarters, mu = 0.01, s0 = 0.002, r0 = 0.005, k = 0.025, H = 8. Illustrative only.
2. **`rate_path`**: `m0 + outer(shock, min(h/ramp, 1))`, so it works for a scalar shock (shape `(H,)`) or a vector of shocks (shape `(n_shock, H)`).
3. **`simulate`** (loop): for each quarter, `g = max(m − beta·m, 0)`; `mig = min(mu·g, 1)`; `out_s = min(s0, 1 − mig)` (so S's total outflow ≤ 1); `run_r = min(r0 + k·g, 1)`. The update uses only previous-quarter balances: `S[h] = S[h−1](1 − mig − out_s)`, `R[h] = R[h−1](1 − run_r) + S[h−1]·mig`.
4. **`trough_loop`**: double loop over the grid calling `simulate`, `min(S+R)/D0`: the correctness baseline.
5. **`trough_grid`** (vectorized): `m` `(ns, H)`; `g = max(m[:, None, :]*(1 − betas[None, :, None]), 0)` `(ns, nb, H)`; flow fractions with the same caps; state arrays `(ns, nb)`; loop over 8 quarters with a **tuple assignment** `S, R = S*(…), R*(…) + S*mig` so the right-hand side uses old S (that's the simultaneous update); keep a running `trough = minimum(trough, S+R)`.
6. **`breach_frontier`**: for each beta, `f(shock) = trough − limit`; if even `hi` doesn't breach → `inf`; else bisect until the bracket < tol and return the upper end (which is guaranteed to breach).
7. **`_tests`**: conservation with no outflows; no negatives with k = 5; a hand-computed first quarter; grid == loop; monotone in shock and beta; frontier is finite, rises with beta, and the trough at the frontier is within 1e-5 of 0.85. Output: trough at (5pp, β = 0) = 0.691; frontier 1.83pp at β = 0 up to 4.19pp at β = 0.5.

### P3 `p3_frozen_champion_overlay.py`

1. **`true_deposit_rate`**: $0.05 + 0.25m + 0.35\max(m-2.5,0) + 0.15\max(m-4,0)$: betas rise with the rate level.
2. **`make_data`**: `old` = 48 quarters with rates in [0, 2] (a clipped random walk); `new` = 28 quarters on a 2 → 5.5 ramp plus noise; `champion_w` = OLS of `dep` on `[1, m]` on `old` only. Frozen from here on.
3. **`hinge_basis`**: `max(m[:, None] − KNOTS[None, :], 0)`, shape `(n, 4)`.
4. **`fit_overlay`**: `solve(Phi'Phi + lam I, Phi' r)`; no intercept by design.
5. **`choose_lambda`**: split `train` into `fit` (all but the last 4 quarters) and `val` (the last 4); for each λ in the grid, fit on `fit`, score RMSE on `val`; return the argmin and the score curve.
6. **`build_challenger`**: `train = new[:-8]`, `hold = new[-8:]`; λ from `choose_lambda`; refit on all of `train`; holdout predictions for champion and champion + overlay; `max_change_old` = max |overlay| on the old data (0.0 exactly).
7. **`_tests`**: champion fits its own era (RMSE < 0.08) but is biased > 0.5pp low on the holdout; challenger RMSE < half the champion's (0.076 vs 0.801); old-regime change is exactly 0; λ → ∞ gives zero overlay and λ → 0 gives OLS; λ was chosen on the time split; matches `sklearn.linear_model.Ridge(fit_intercept=False)`. Coefficients `[0.016, 0.326, 0.151, 0.0]`: the last hinge (5%) has no training data.

### P4 `p4_scenario_distance_ot.py`

1. **`make_samples`**: 400 bivariate normal draws each; history mean 0 with negative UR–yield correlation; stress has mean (+0.6, −0.4) and wider spread.
2. **`wasserstein_1d`**: sort both, `mean(|x − y|^p)^(1/p)`.
3. **`wasserstein_1d_hist`**: $\sum |F_a - F_b|\,\Delta$ over the grid (the CDF form of $W_1$).
4. **`ot_lp`**: `A_eq` has n rows of ones over each row-block of `vec(P)` (row sums) and m rows picking every m-th entry (column sums); `linprog(C.ravel(), A_eq, b_eq = [a, b], bounds = (0, None))`; returns cost and the reshaped plan.
5. **`sliced_wasserstein`**: random `theta` `(L, d)` normalized to unit rows; projections `X @ theta.T` `(n, L)`; sort along axis 0; RMS difference over everything = $\sqrt{\text{mean}_\theta W_2^2}$.
6. **`_tests`**: W(x, x) = 0; a shift by 0.7 gives exactly 0.7; symmetry; LP cost == CDF formula on a 26-point grid, plan marginals correct; SW(X, X) = 0; shift identity $SW_2^2 \approx |a|^2/2$ within 0.01 with 4,000 projections; stress SW (0.542) is > 4× the sampling-noise SW between two halves of history (0.060).

### P5 `p5_planning_allocation_milp.py`

1. **`make_problem`**: 8 initiatives with random v, u, m (40–70% of u), f; the two lowest-value initiatives are regulatory; B = 30, R_min = 8, K = 4.
2. **`solve_lp`**: `linprog(−v, A_ub = [ones; −reg], b_ub = [B, −R_min], bounds = [0, u])`; duals = `−ineqlin.marginals` when available.
3. **`solve_milp`**: variables `[x, z]`; objective `−(v'x − f'z)`; constraints: budget, `x − diag(u) z ≤ 0`, `x − diag(m) z ≥ 0`, `Σ z ≤ K`, regulatory floor; `integrality = [0]*n + [1]*n`; bounds z ∈ [0, 1].
4. **`best_given_z`**: with z fixed: give each funded line its minimum; top up the regulatory floor with the best regulatory lines; fill the rest by value. Exact because costs are unit and only box constraints remain.
5. **`brute_force`**: all 256 z with Σ z ≤ K.
6. **`greedy`**: enough regulatory lines for the floor, then the highest value per unit, ignoring set-up costs.
7. **`_tests`**: LP feasibility; budget dual == finite difference (2.03); floor binds and its dual == finite difference (0.94); MILP == brute force (47.11) and respects min scale/cardinality; MILP ≤ LP (63.16); greedy (35.40) strictly worse.

### P6 `p6_gl_sql_pipeline.py`

1. **`make_tables`**: 4 cost centres × 18 months; CC31 stops posting at the 2025-07 re-org and CC30 absorbs its spend; CC10 2025-03 has a wrong posting (×3) and a correction 10 days later; CC20 2026-02 is missing; budget is on the new hierarchy.
2. **`SQL`**: `latest` (ROW_NUMBER by posted_at DESC) → `mapped` (LEFT JOIN cc_map, COALESCE, rn = 1) → `actuals` (GROUP BY cc, month; integer `yr` and `m_idx`) → `w` (budget join, `LAG(actual)`, `LAG(m_idx)`, YTD running sum partitioned by cc and year) → final SELECT with the gap-aware `CASE WHEN prev_idx = m_idx − 1`.
3. **`pandas_reference`**: the same in pandas (sort + `drop_duplicates(keep="last")`, `map` + `fillna`, `groupby().sum()`, `merge`, `cumsum` by (cc, yr), shifted index check).
4. **`_tests`**: CC31 disappears into CC30; 53 rows; every column matches pandas; no ×3 spike; NULL MoM after the gap; YTD restarts in January; no step change in CC30 at the re-org.

### P7 `p7_variance_explainer_guardrail.py`

1. **`make_books`**: four products; actual shifts balances into CDs (low margin) and compresses Savings margins.
2. **`pvm`**: aligns indexes, computes weights, `mbar0`, then volume, mix and rate exactly as in §3.8; `total = nii_actual − nii_plan` (−$123m = +61 volume − 116 mix − 68 rate).
3. **`_NUM`** regex: optional sign, optional `$`, comma-grouped or decimal number, optional unit (`bn`, `billion`, `m`, `mm`, `million`, `%`, `bp`, `bps`).
4. **`extract_claims`**: normalizes $m → $bn; finds the clause around the number (bounded by `, ; ! ? newline` or a sentence-ending period, not a decimal point) and takes the nearest direction word from the up/down vocabularies.
5. **`check_narrative`**: ignores unit-less numbers (years); a claim is supported if its absolute value matches some fact within 2% relative (or 0.001 absolute); then the direction word must agree with the fact's sign.
6. **`_tests`**: the decomposition reconciles to 1e-12; zero change ⇒ zeros; a pure margin change ⇒ rate effect only, mix 0; the generated good draft passes; the bad draft ("Volume fell by $61m", "down 35bp") yields exactly one wrong direction and one unsupported number; parser edge cases ($1,250m → 1.25bn; −0.4%; year ignored).
