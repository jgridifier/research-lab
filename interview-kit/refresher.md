# Refresher: methods and reference-solution walkthroughs

[← Back to the kit](README.md) · [Cheat sheet](cheatsheet.md)

> **Generic practice material for a Python quant/forecasting coding interview. Synthetic data; illustrative scenarios; not investment advice; not affiliated with any employer.**

Plain-language summaries you can use if you need to explain or check something mid-interview. Each subsection ends with the one-line answer you'd want from the candidate.

## 3.1 pandas idioms for panels

- **`groupby(key)[col].shift(k)`** moves values *within* each group by k rows. On a panel you **must** group, or bank B's first quarter picks up bank A's last value. `shift` moves **rows**, not dates, so it is only "one quarter back" if every quarter is present. That's why P1 reindexes onto a complete grid first.
- **Complete grid:** `pd.period_range(start, end, freq="Q")` plus `reindex`. Missing quarters become NaN rows, and `x / x.shift(1) - 1` then returns NaN after a gap instead of silently computing a two-quarter change.
- **`pct_change` pitfalls:** (1) before pandas 2.1 it **forward-filled NaNs by default** (`fill_method='pad'`), so a gap produced 0% and then the full two-quarter change. That default was deprecated in 2.1 and removed in 3.0, so behavior is version-dependent. (2) It must be grouped (`groupby(...).pct_change()`). (3) It is meaningless for series that cross zero or are near zero (net income, spreads); use differences instead. (4) Log differences $\Delta \ln x$ add up over time, while simple growth rates don't.
- **`resample`** works on a `DatetimeIndex` (e.g. daily → quarterly: `df.resample("QE").last()` for stocks such as balances, `.sum()` for flows such as income, `.mean()` for rates). In pandas ≥ 2.2 the quarter-end alias is `"QE"` (`"Q"` is deprecated for offsets). `Period` uses `freq="Q"`. In a panel: `df.groupby("bank").resample("QE", on="date")`.
- **`merge_asof(left, right, on="date", by="bank", direction="backward")`** joins each left row to the most recent right row at or before its date. It is the standard way to attach the information available at the time (e.g. the latest macro vintage or the latest filing) without look-ahead. Both frames must be sorted on `on`. `allow_exact_matches=False` excludes same-day matches (useful when a release happens after the market close).
- **`drop_duplicates(keys, keep="last")` after sorting by filing time** keeps the latest restatement.
- **`sum(min_count=1)`** keeps an all-NaN group as NaN instead of 0, which matters when summing the acquirer and target in a pro-forma.
- **pandas 3.0 notes:** copy-on-write is the default (chained assignment like `df[df.a>0]["b"] = 1` silently does nothing; use `.loc`), and strings default to the `str` dtype. None of the reference code depends on either.

*Candidate one-liner:* "Group, put it on a full calendar, then shift; never `pct_change` across gaps."

## 3.2 OLS, AR, ARX and VAR estimation

- **OLS:** $\hat\beta = (X^\top X)^{-1}X^\top y$, residuals $\hat u = y - X\hat\beta$, $\hat\sigma^2 = \hat u^\top \hat u/(n-k)$, classical $\widehat{\text{Var}}(\hat\beta) = \hat\sigma^2 (X^\top X)^{-1}$. In numpy: `np.linalg.lstsq(X, y, rcond=None)[0]`, which uses QR/SVD and is more stable than forming the inverse. In statsmodels: `sm.OLS(y, sm.add_constant(X)).fit()`, with `.params`, `.bse`, `.resid`.
- **AR(p):** $y_t = c + \sum_{j=1}^p \phi_j y_{t-j} + e_t$, estimated by OLS on lagged columns. It is stationary if the roots of $1-\phi_1 z-\dots-\phi_p z^p$ lie outside the unit circle; for AR(1), $|\phi|<1$, and the mean is $c/(1-\phi)$. Lag length is chosen by AIC/BIC, **inside each backtest window** if you want no look-ahead. statsmodels: `AutoReg(y, lags=p, exog=X)`.
- **ARX:** an AR plus exogenous regressors $x_t$ (macro drivers). Whether you use $x_t$ or $x_{t-1}$ matters: with contemporaneous $x$, a forecast needs a value of $x$ (from a scenario, or from its own forecast).
- **VAR(p):** a vector $Y_t = c + A_1 Y_{t-1} + \dots + A_p Y_{t-p} + u_t$, $\text{Var}(u_t)=\Sigma$. Estimate **equation by equation with OLS** (efficient here because all equations share the same regressors). Structural shocks come from $u_t = P\varepsilon_t$ with $PP^\top = \Sigma$, e.g. a Cholesky factor (recursive ordering). statsmodels: `VAR(df).fit(p)`, with `.forecast(y_last, steps)` and `.irf()`.
- **Multi-step forecasts:** *iterated* (fit a one-step model and feed forecasts back in; P3) vs *direct* (regress $y_{t+h}$ on information at $t$; P2 with h > 1). Direct is more robust to misspecification; iterated is more efficient if the model is right.

*Candidate one-liner:* "OLS with lstsq; VAR is OLS equation by equation; decide iterated vs direct and say why."

## 3.3 Rolling-origin backtests and look-ahead bias

- **Rolling origin (time-series CV):** for each origin $t = t_0, \dots, T-h$, fit on data available at $t$, forecast $t+h$, store the error. An **expanding window** uses all of $1..t$ (more data, assumes stability). A **rolling window** uses the last $w$ points (adapts to breaks, noisier).
- **Look-ahead (leakage) comes in several forms. Ask the candidate to list them:**
  1. Fitting on the full sample and evaluating "out of sample" (the cardinal sin).
  2. Full-sample transformations: standardizing, PCA/factors, detrending, a two-sided HP filter, seasonal adjustment with the full-sample X-13. **Re-estimating the PCA/factors at each origin is the fix; give credit if the candidate mentions it.**
  3. **Oracle regressors:** using realized $x_{t+h}$ to forecast $y_{t+h}$. That's legitimate *only* for a conditional evaluation ("how good is the model if the scenario is right?"), and it should be labeled as such.
  4. **Data vintages:** macro data and call reports get revised. A real-time backtest uses what was published at the origin (ALFRED for macro).
  5. Model selection on the full sample (lag length, variable choice, hyperparameters).
  6. Survivorship: a bank panel of today's survivors.
- **The test you can always run:** change future data and check that past forecasts don't move. P2 does exactly this with `df_bad.iloc[t0+1:] = 999`.

*Candidate one-liner:* "At origin t I slice the data to ≤ t before anything else, including transforms and model selection."

## 3.4 Forecast-error metrics

With $e_t = y_t - \hat y_t$ over $n$ OOS points:

$$\text{RMSE} = \sqrt{\tfrac1n\textstyle\sum e_t^2}, \quad \text{MAE} = \tfrac1n\textstyle\sum |e_t|, \quad \text{MAPE} = \tfrac{100}{n}\textstyle\sum \left|e_t / y_t\right|.$$

- RMSE penalizes big misses, which is what matters for stress. MAE is robust to outliers. **MAPE explodes near zero and is undefined at zero**, which makes it a bad choice for growth rates, NII changes or anything that crosses zero; it's fine for strictly positive levels such as deposit balances. It is also asymmetric (over-forecasts can cost more than 100%; under-forecasts are capped at 100%).
- Alternatives: **sMAPE**, and **MASE** (MAE divided by the in-sample MAE of a naive forecast; scale-free, so it compares series).
- **Out-of-sample R²**: $R^2_{OS} = 1 - \sum e_{\text{model}}^2 / \sum e_{\text{bench}}^2$. Positive means the model beats the benchmark.

## 3.5 Diebold–Mariano and Clark–West

- **DM (1995):** loss differential $d_t = L(e_{1,t}) - L(e_{2,t})$ (e.g. $e_{1,t}^2 - e_{2,t}^2$). $H_0: E[d_t]=0$.
  $$DM = \frac{\bar d}{\sqrt{\widehat{LRV}(d)/n}}, \quad \widehat{LRV} = \hat\gamma_0 + 2\sum_{k=1}^{h-1}\hat\gamma_k,$$
  which is asymptotically $N(0,1)$. h-step forecast errors are MA(h−1), hence the h−1 autocovariances. A negative DM means model 1 has the lower loss.
- **Harvey–Leybourne–Newbold (1997)** small-sample correction: multiply by $\sqrt{(n+1-2h+h(h-1)/n)/n}$ and compare with $t_{n-1}$.
- **Nested models:** when the challenger nests the benchmark (ARX vs AR, or vs the mean), DM is undersized under the null. The big model's noise from estimating zero coefficients makes it look worse than it is. **Clark–West (2007)** adjusts for this:
  $$f_t = e_{1,t}^2 - \left[e_{2,t}^2 - (\hat y_{1,t} - \hat y_{2,t})^2\right],$$
  with a one-sided t-test of $\bar f > 0$ (1 = small model, 2 = big model).
- **Giacomini–White (2006):** tests conditional predictive ability of *forecasting methods* (with estimation windows), and is valid with rolling windows. Worth knowing the name.
- **DM tests forecasts, not models.** Small n (e.g. a few dozen OOS points) means low power. Report the stability across split points.

## 3.6 Conditional forecasting under an imposed path

- **The task in CCAR/DFAST:** the Fed provides 9-quarter paths for 28 macro variables (Baseline, Severely Adverse). Banks project revenues, losses and balances *conditional* on those paths.
- **Approach 1, exogenous drivers (ARX / regression):** treat the scenario variables as known and iterate the model. Watch for: (i) **jump-off**: the first difference is path[0] minus the last actual; (ii) the recursion uses forecasts of the lagged dependent variable; (iii) cumulate growth into levels, $D_{T+h} = D_T\prod_{j\le h}(1+g_{T+j}/100)$; (iv) bands come from simulating shocks (residual bootstrap) through the recursion. Parameter uncertainty needs re-estimation per draw (bootstrap or Bayesian posterior).
- **Approach 2, conditioning a VAR (Waggoner–Zha 1999 "hard conditions"):** when the scenario variables are endogenous, the path can only happen if certain shocks occur, and those shocks move the other variables too. Write the h-step deviation from the unconditional forecast as $Y_{T+h} - \hat Y_{T+h} = \sum_{j=1}^{h} \Psi_{h-j}P\,\varepsilon_{T+j}$ with $\Psi_m = A^m$ for a VAR(1). Stack this to $\text{dev} = M\varepsilon$, pick the rows of the conditioned variables ($R\varepsilon = r$), and with $\varepsilon \sim N(0,I)$ the conditional mean of the shocks is the min-norm solution
  $$\varepsilon^{*} = R^\top (RR^\top)^{-1} r,\qquad \text{Cov}(\varepsilon\mid\cdot) = I - R^\top(RR^\top)^{-1}R.$$
  The conditioned variables then have zero variance, and the others get the right conditional bands. The same answer comes from a Kalman filter/smoother that treats the path as observations (Bańbura, Giannone & Lenza 2015).
- **Structural (shock-specific) conditioning:** produce the path using only selected structural shocks (e.g. only "demand" shocks), which is closer to a narrative scenario. Antolín-Díaz, Petrella & Rubio-Ramírez (2021) formalize this.
- **What a thoughtful candidate flags:** the Lucas critique and regime dependence (deposit betas differ by rate regime), extrapolation outside the historical joint distribution, scenario paths that are internally inconsistent with the model's dynamics (WZ makes this visible through large implied shocks), and the fact that bands exclude scenario uncertainty by construction.

## 3.7 Local projections and Newey–West

- **LP (Jordà 2005):** for each horizon, run a separate regression $y_{t+h} - y_{t-1} = \alpha_h + \beta_h s_t + \gamma_h^\top w_t + u_{t+h}$, where $\beta_h$ is the impulse response at h. It's flexible (state dependence, nonlinearity, panels) and robust to VAR misspecification, but noisier at long horizons. In population, LPs and VARs estimate the same IRFs (Plagborg-Møller & Wolf 2021), and in finite samples it's a bias–variance trade-off (Li, Plagborg-Møller & Wolf 2024).
- **Why HAC:** $u_{t+h}$ overlaps across $t$ (MA(h) at least), so OLS SEs are too small.
- **Newey–West (1987):** $\widehat{\text{Var}}(\hat\beta) = (X^\top X)^{-1}\hat S(X^\top X)^{-1}$ with
  $$\hat S = \sum_t \hat u_t^2 x_t x_t^\top + \sum_{l=1}^{L} \left(1 - \tfrac{l}{L+1}\right)\sum_t \hat u_t \hat u_{t-l}\left(x_t x_{t-l}^\top + x_{t-l} x_t^\top\right).$$
  The Bartlett weights keep $\hat S$ positive semi-definite. A common choice is $L \ge h+1$, or the rule-of-thumb $L = \lfloor 4(n/100)^{2/9}\rfloor$. statsmodels: `fit(cov_type="HAC", cov_kwds={"maxlags": L})`, which applies an $n/(n-k)$ correction by default (`use_correction=True`, matched in P4). Montiel Olea & Plagborg-Møller (2021) show that adding lags of $y$ and $s$ as controls lets you use plain heteroskedasticity-robust SEs; mention it only if the candidate does.
- **LP-IV:** when the shock is mismeasured or endogenous, instrument it: 2SLS $\hat\beta = (Z^\top X)^{-1}Z^\top y$ in the just-identified case. Check instrument strength (effective F, Montiel Olea–Pflueger).

## 3.8 Lagrangian, KKT and bisection

- Problem: $\max_x \sum_i f_i(x_i)$ s.t. $\sum_i x_i = B$, $0\le x_i\le u_i$, with $f_i$ concave and increasing.
- **Lagrangian:** $\mathcal L = \sum_i f_i(x_i) - \lambda(\sum_i x_i - B)$. **KKT:** $f_i'(x_i) = \lambda$ if $0<x_i<u_i$; $f_i'(0)\le\lambda$ if $x_i=0$; $f_i'(u_i)\ge\lambda$ if $x_i=u_i$. Concavity makes KKT sufficient, so the solution is globally optimal.
- For $f_i = a_i(1-e^{-b_i x_i})$: $f_i' = a_i b_i e^{-b_i x_i}$, so $x_i(\lambda) = \text{clip}\left(\tfrac{1}{b_i}\ln\tfrac{a_i b_i}{\lambda}, 0, u_i\right)$.
- **Bisection:** total spend $S(\lambda)=\sum_i x_i(\lambda)$ is continuous and non-increasing. Bracket $[\lambda_{lo}, \lambda_{hi}]$ with $S(\lambda_{hi}) = 0 \le B \le S(\lambda_{lo})$, halve repeatedly, and you need $\log_2((\lambda_{hi}-\lambda_{lo})/\text{tol})$ iterations, which is guaranteed convergence. If $B\ge\sum u_i$, the constraint doesn't bind and $\lambda=0$.
- **Interpretation:** $\lambda$ is the **shadow price** of budget: the objective gain from one more unit of budget. LP solvers report it as the dual on the budget row.

## 3.9 LP and convex optimization in scipy

- **`scipy.optimize.linprog(c, A_ub, b_ub, A_eq, b_eq, bounds, method="highs")`** *minimizes* $c^\top x$, so negate to maximize. With HiGHS (scipy ≥ 1.7), `res.eqlin.marginals` and `res.ineqlin.marginals` give the duals (the sign convention follows minimization, hence the minus sign in P5).
- **Concave objectives as an LP:** split each $x_i$ into K segments with decreasing slopes (piecewise-linear outer approximation). Because the slopes decrease, the LP fills segments in order, so no binaries are needed. The error shrinks as K grows (P5: objective 97.6239 with K = 200 vs 97.6241 exact).
- **`scipy.optimize.minimize(fun, x0, jac, bounds, constraints, method="SLSQP")`** handles smooth constrained NLPs locally. With a concave objective and linear constraints, local = global. `trust-constr` is the more robust alternative.
- **`scipy.optimize.milp`** (scipy ≥ 1.9, HiGHS) handles integer and binary variables. Use it for fixed costs, minimum spend if funded ($x_i \ge m_i z_i$, $x_i \le u_i z_i$, $z_i\in\{0,1\}$), cardinality ($\sum z_i \le K$), and project selection. Bisection no longer works there because the feasible set is non-convex.
- Outside CoderPad: cvxpy (modeling), OR-Tools, Gurobi/CPLEX (commercial).

## 3.10 Monte Carlo, vectorization and Numba

- **MC estimate:** $\hat\mu = \frac1N\sum L_s$ with standard error $\hat\sigma/\sqrt N$, so precision improves only at $\sqrt N$. **Tail quantiles need far more sims:** at q = 99.9% only $N(1-q)$ draws lie beyond the VaR (20 of 20,000). Use more sims, importance sampling, or report a CI for the quantile.
- **VaR$_q$** is the q-quantile of loss. **ES$_q$** is the mean loss given $L\ge \text{VaR}_q$. ES is coherent (subadditive) and is what Basel FRTB uses (at 97.5%).
- **Vasicek one-factor model:** default if $\sqrt\rho Z + \sqrt{1-\rho}\,\varepsilon_i < \Phi^{-1}(PD_i)$. Conditional on $Z$, $PD_i(Z) = \Phi\!\left(\frac{\Phi^{-1}(PD_i) - \sqrt\rho Z}{\sqrt{1-\rho}}\right)$. For a large homogeneous pool, the loss-fraction q-quantile is $\Phi\!\left(\frac{\Phi^{-1}(PD) + \sqrt\rho\,\Phi^{-1}(q)}{\sqrt{1-\rho}}\right)$, which is the Basel IRB formula.
- **Vectorization:** replace Python loops with array operations and broadcasting (`Z[:, None]` against `eps` of shape `(N, n)`), and matrix products (`defaults @ (ead*lgd)`). It is typically 10–100× faster than pure Python, at the cost of memory ($N\times n$ float64 = $8Nn$ bytes).
- **Numba:** `@njit` compiles a Python function over numpy arrays and scalars to machine code (LLVM). Rules: no pandas, no arbitrary Python objects, stable types. The **first call compiles** (seconds), so time the second call. `parallel=True` with `prange` splits loops across cores. `np.random` works inside `@njit`, with its own per-thread state, and needs care for reproducibility. `cache=True` persists the compiled code. It is best for loop-heavy code that doesn't vectorize well (recursions, dynamic-programming loops, path-dependent simulation) and lets you avoid giant intermediate arrays.

## 3.11 SQL window functions

- **Syntax:** `f(...) OVER (PARTITION BY ... ORDER BY ... [frame])`. Unlike GROUP BY, it keeps every row.
- **Ranking:** `ROW_NUMBER()` (unique, ties broken arbitrarily: use it to dedupe), `RANK()` (ties share a rank, then gaps: 1, 1, 3), `DENSE_RANK()` (1, 1, 2).
- **Offsets:** `LAG(x, k)` / `LEAD(x, k)`, the previous and next rows *in the partition order*. They count rows, not quarters, so add a gap check on an integer period index.
- **Aggregates over windows:** `SUM(x) OVER (PARTITION BY qtr)` gives a group total on each row (shares). With `ORDER BY` and no frame, the default is a running total (`RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`).
- **Frames:** `ROWS BETWEEN 3 PRECEDING AND CURRENT ROW` means the last 4 rows. `RANGE BETWEEN 3 PRECEDING AND CURRENT ROW` on an integer quarter index means the last 4 *calendar* quarters, so gaps are respected (SQLite ≥ 3.28, Postgres ≥ 11).
- **Filtering on a window result** needs a CTE or subquery (`WHERE rn = 1` in the outer query). `QUALIFY` exists in Snowflake, BigQuery and Databricks, but not in Postgres or SQLite.
- **Named windows:** `WINDOW w AS (PARTITION BY bank_id ORDER BY q_idx)`, then `LAG(x) OVER w`.


## 3.12 Walking through the reference solutions

Read these alongside the code in [§2 of the README](README.md#2-problems). Function names and quoted lines refer to the files in [`solutions/`](solutions/).

### P1 `p1_bank_panel_cleaning.py`

1. **`make_panel`** builds three banks with *known* constant organic growth (A 2%, B 2%, C 1%) and constant quarterly NII, so every assert has an exact target. It then injects the traps: from 2021Q3 A's deposits include B's (`raw.loc[mask, "total_deposits"] += ...`), B stops filing, C gets a stale, wrong duplicate for 2020Q2 (`bad["filed_at"] -= 20 days`, deposits × 1.5), C's 2022Q1 is deleted, and the rows are shuffled.
2. **`clean_panel`**, line by line:
   - `df["quarter"] = df["report_date"].dt.to_period("Q")` converts the timestamp to a quarterly `Period`, so quarter arithmetic (`gq + 1`) works.
   - `sort_values([... "filed_at"]).drop_duplicates([...], keep="last")` makes the latest filing win, and handles the restatement.
   - `_reindex` builds `pd.period_range(min, max, freq="Q")` per bank and `reindex`es, so the missing quarter becomes an explicit NaN row. The loop over `groupby` is deliberate: it's clear and fast enough for a handful of banks (a `MultiIndex.from_product` reindex is the vectorized alternative).
   - YTD → quarterly: `groupby(["bank_id","year"])["nii_ytd"].shift(1)` is the previous YTD *within the same year*; `np.where(is_q1, ytd, ytd - prev)`. A missing previous quarter gives NaN automatically.
   - Growth: `total_deposits / gb.shift(1) - 1` and `/ gb.shift(4) - 1`. The shifts are in rows, but rows are now quarters because of the grid.
3. **`pro_forma`** relabels the target's pre-deal rows with the acquirer's id (`pf_id`), sums by `(pf_id, quarter)` with `min_count=1`, drops the target as a stand-alone bank, and recomputes growth. Because the synthetic A and B both grow 2%, the combined series grows exactly 2% (the asserts check QoQ = 0.02 and YoY = 1.02⁴ − 1).
4. **`_tests`** checks: no duplicate keys; the gap row exists and is NaN; growth right after the gap is NaN; C's growth is exactly 1% (which proves the restatement was dropped); quarterly NII is constant; raw A growth jumps above 30% at the deal but pro-forma growth doesn't. The last check shows why `x/x.shift()-1` is explicit and version-proof.

### P2 `p2_rolling_backtest_dm.py`

1. **`make_data`**: $x_t = 0.5x_{t-1} + \eta_t$ and $y_t = 0.4 + 0.5y_{t-1} - 1.2x_{t-1} + e_t$. Lagged $x$ truly predicts $y$, so the ARX *should* win, which the asserts use.
2. **`ols`** wraps `np.linalg.lstsq`.
3. **`design(df, p, h, use_x)`** builds columns `const, y_l0..y_l{p-1}, x_l0`, all dated ≤ t, and the target `y.shift(-h)`. `ok` keeps rows with complete data. `Z.iloc[-1]` is the *last available* regressor row: its target is in the future, which is exactly the row to forecast from. Because `design` is only ever called on `hist`, `shift(-h)` can't reach past the origin.
4. **`forecast_at_origin(hist, ...)`** fits on `hist`'s complete rows and returns `x_last @ b`.
5. **`backtest`**: `hist = df.iloc[: t + 1]` **is the no-look-ahead line.** Every model, including the random walk (`hist["y"].iloc[-1]`) and the historical mean (`hist["y"].mean()`), sees only `hist`. Results are indexed by target date, with the origin kept for auditing.
6. **`error_table`** reports RMSE and MAE per model.
7. **`diebold_mariano`**: `d = e1**2 - e2**2`; autocovariances up to h−1 (`gam`); the long-run variance, falling back to Bartlett weights if it comes out non-positive; then `stat = dbar / sqrt(lrv/n)`; the HLN factor; the t(n−1) p-value (normal via `math.erf` if scipy is missing).
8. **`clark_west`**: `f = (a - f_small)**2 - ((a - f_big)**2 - (f_small - f_big)**2)`, a t-stat on its mean, and a one-sided p-value.
9. **`_tests`**: (1) **look-ahead guard**: overwrite everything after origin 80 with 999 and check that the forecast at 80 and every earlier backtest forecast are unchanged; (2) the ARX beats RW and the mean on RMSE; DM vs RW rejects (stat −3.04, p 0.003); (3) DM is antisymmetric; (4) OLS matches statsmodels; (5) Clark–West rejects AR(1) in favor of ARX (stat 4.41); (6) h = 4 target dates are origin + 4.

### P3 `p3_conditional_scenario_forecast.py`

1. **`make_history`**: UR and Y10 are persistent AR(1)s; $g_t = 1.0 + 0.4g_{t-1} - 1.5\Delta UR_t + 0.8\Delta Y10_t + e_t$; `deposits = 1000 * cumprod(1 + g/100)`.
2. **`make_scenarios`**: Baseline drifts gently. Severely Adverse raises UR by 5.5pp to a peak in quarter 6 and then eases; Y10 falls about 2.5pp quickly with a 0.5% floor. The paths start the quarter after the last history date. *They are illustrative, not the Fed's numbers.*
3. **`fit_arx`** builds `g, g_l1, dur, dy10` with `.diff()` on history, drops the first rows, and runs OLS. It returns the coefficients and residuals (for the bootstrap).
4. **`project`**:
   - `dur = np.diff(np.r_[hist.ur.iloc[-1], path.ur])` is the **jump-off**: prepend the last actual so the first scenario change is path[0] − last actual. This is the most common bug, so check it.
   - `eps` is either zeros (the mean path) or an `(n_sims, H)` matrix of residual draws, so one code path serves both. `overlay` adds the stress add-on in pp of growth.
   - The loop `for h in range(H)` is the recursion: `g_prev` starts at the last actual growth and is then replaced by the forecast.
   - `level = D_T * cumprod(1 + g/100, axis=1)` converts growth to levels per path.
5. **`scenario_forecast`**: the mean path, then `rng.choice(resid, size=(n_sims, H))` (an iid residual bootstrap) pushed through the same recursion, then percentiles **of levels**. Parameter uncertainty is not included (say so in the debrief).
6. **`fit_var1` / `var_conditional`** (the stretch):
   - A VAR(1) by OLS, `Sigma` from the residuals, `P = cholesky(Sigma)`.
   - `yhat` is the unconditional path.
   - `M[h-block, j-block] = A^{h-j} P` for j ≤ h maps the stacked shocks to stacked deviations.
   - `R = M[rows]` keeps the rows for (UR, Y10) at every horizon; `r = path − yhat` on those rows.
   - `eps = R.T @ solve(R R.T, r)` gives the min-norm (conditional-mean) shocks; `ycond = yhat + M eps`.
   - `V = I − R.T (R R.T)^{-1} R` is the conditional shock covariance, and `cov = M V M.T` the path covariance.
7. **`_tests`**: coefficients near the truth; SA < baseline at every horizon; bands bracket the mean and widen; quarter 1 matches a by-hand calculation; stress < SA; the VAR conditional path hits the imposed UR and Y10 exactly with zero variance on those variables, while deposits keep positive variance; the SA conditioning lowers average VAR deposit growth.

### P4 `p4_local_projection_nw.py`

1. **`make_data`**: $y_t = 0.8y_{t-1} + s_t + e_t$, so the true cumulative response is $0.8^h$. It also creates `s_noisy` (the shock plus noise, for attenuation) and `z` (an instrument correlated with the true shock and independent of the measurement noise).
2. **`newey_west`**: `Xu = X * u[:,None]` (the scores); `S = Xu.T @ Xu` (lag 0); for each lag, `G = Xu[l:].T @ Xu[:-l]` with Bartlett weight `1 - l/(L+1)`, adding `G + G.T`; the sandwich `XtX_inv @ S @ XtX_inv`; and the `n/(n-k)` correction to match statsmodels.
3. **`lp_design`**: `lhs = y.shift(-h) - y.shift(1)` (that is, $y_{t+h} - y_{t-1}$), the shock at t, and two lags of y and s; then `dropna` aligns everything.
4. **`local_projection`**: per h, OLS, residuals, NW with `L = h + 1`, picking out the shock coefficient and its SE, and a 95% band.
5. **`lp_iv`**: replace the shock column with the instrument in Z, $\hat\beta=(Z^\top X)^{-1}Z^\top y$, and a HAC sandwich $(Z^\top X)^{-1}S_{zu}(X^\top Z)^{-1}$.
6. **`_tests`**: max error < 0.15 across h; at least 75% of CIs cover the truth; the SE grows with h; the hand NW equals statsmodels HAC to 1e-8; OLS on the noisy shock is attenuated (about 0.51) and IV recovers about 1.02.

### P5 `p5_budget_allocation.py`

1. **`make_problem`**: random $a_i, b_i, u_i$, with $B$ at 45% of total caps so the constraint binds and some caps may bind too.
2. **`x_of_lam`**: the closed-form FOC solution, clipped to $[0,u_i]$.
3. **`allocate_bisection`**: if $B \ge \sum u_i$, return the caps with $\lambda = 0$. Otherwise bracket $[10^{-12}, \max a_ib_i]$ (at the upper end every $x_i = 0$). If spend > B, raise `lo` (λ is too low); otherwise lower `hi`. Stop when the bracket is narrower than tol.
4. **`allocate_slsqp`**: the negated objective with its analytic gradient, box bounds, the equality constraint with its Jacobian, and a tight `ftol`.
5. **`allocate_lp`**: K segments per line of width $u_i/K$; segment slope = the payoff increment divided by the width; `linprog` maximizes total slope × fill subject to sum = B and $0\le$ fill $\le$ width; the shadow price is `-res.eqlin.marginals[0]`.
6. **`allocate_milp`**: the variables are the segments plus binaries $z_i$. Constraints: total ≤ B; $\sum_k x_{ik} \ge m_i z_i$; $x_{ik} \le w_i z_i$ (nothing is spent unless funded); $\sum z_i \le$ `max_funded`; then `integrality` marks the $z$ variables as binary.
7. **`_tests`**: budget met; bounds respected; **KKT check** (interior marginals = λ, zeros have marginal ≤ λ, caps have marginal ≥ λ); a tight-budget case with corners; the non-binding case; SLSQP matches bisection; the LP objective is within 1e-4 and its dual within 5% of λ (0.312 vs 0.310); the MILP respects the funding rules and does weakly worse.

### P6 `p6_monte_carlo_numba.py`

1. **`make_portfolio`**: lognormal EADs, PD 0.5–5%, LGD 30–60%.
2. **`losses_loop`**: a double loop, thresholds `ppf(pd)`, accumulating `ead*lgd` on default. This is the baseline for correctness.
3. **`losses_vec`**: `latent = sqrt(rho) Z[:,None] + sqrt(1-rho) eps` (shape N × n), then `(latent < thr) @ (ead*lgd)`.
4. **Numba**: `_losses_from_draws_nb` is the same loop as (2) under `@njit`, taking the same draws so results are *identical*. `_losses_sim_nb` draws inside, with `prange` across sims and a per-sim `np.random.seed(seed + s)`, so it's reproducible under parallelism and needs only O(n) memory.
5. **`risk_measures`**: `VaR = quantile(L, q)` and `ES = mean(L[L >= VaR])`.
6. **`_tests`**: loop == vectorized on the same draws; MC EL within 4 SE of the analytic $\sum EAD\cdot LGD\cdot PD$; ES ≥ VaR ≥ EL; a homogeneous 2,000-loan pool's 99% loss quantile within 15% of the Vasicek formula; Numba == loop; the parallel version is reproducible and its EL is within 4 SE; plus timings.

### P7 `p7_sql_window_functions.py`

1. **`make_db`**: 4 banks × 12 quarters, a stale duplicate for B 2023Q2 (deposits × 2, an earlier `filed_at`), and D's 2023Q3 deleted. It loads into in-memory SQLite with `df.to_sql`.
2. **`SQL_CLEAN`**: a CTE with `ROW_NUMBER() ... ORDER BY filed_at DESC` and `rn = 1`, which also builds `q_idx = yr*4 + qtr - 1`.
3. **`SQL_GROWTH`**: a named window `w` (bank, ordered by `q_idx`); `LAG(deposits)` and `LAG(q_idx)` for the gap-aware QoQ (`CASE WHEN q_prev = q_idx - 1`); the YTD LAG partitioned by **bank and year**; the moving average with a `RANGE BETWEEN 3 PRECEDING` frame on `q_idx` plus a count = 4 check; `RANK()` and the share with `SUM() OVER (PARTITION BY yr, qtr)`.
4. **`pandas_reference`** computes the same columns in pandas for a cross-check.
5. **`_tests`**: the row count; deposits, QoQ and NII match pandas; D 2023Q4 growth and NII are NULL; D's moving average is NULL until 4 consecutive quarters exist again; A's first moving average equals the mean of its first 4 quarters; shares sum to 1; A ranks first; B has no 2× jump.
