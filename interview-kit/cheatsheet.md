# One-page cheat sheet

[← Back to the kit](README.md) · [Refresher](refresher.md)

> **Generic practice material for a Python quant/forecasting coding interview. Synthetic data; illustrative scenarios; not investment advice; not affiliated with any employer.**

**Run sheet:** 0:00 format · 0:02 intro + warm-ups · 0:12 pad setup · **0:14 P1** · **0:20 P2** (0:25 one origin, 0:29 loop+RMSE, 0:33 DM) · **0:33 P3** (0:37 fit, 0:43 SA levels, 0:47 bands/stress, debrief) · 0:50 close · 0:52 candidate's questions. Fast: CW/h=4 → P3 VAR stretch → P6 mini. Stuck: paste `design()` / `fit_arx`.

| Topic | Formula / rule |
|---|---|
| OLS | $\hat\beta=(X^\top X)^{-1}X^\top y$, $\ \widehat{V}=\hat\sigma^2(X^\top X)^{-1}$, $\ \hat\sigma^2=\hat u^\top\hat u/(n-k)$ |
| AR(1) | $y_t=c+\phi y_{t-1}+e_t$; mean $c/(1-\phi)$; $h$-step $\hat y_{T+h}=\mu+\phi^h(y_T-\mu)$; var $\sigma^2\sum_{j<h}\phi^{2j}$ |
| VAR(1) | $Y_t=c+AY_{t-1}+P\varepsilon_t$, $PP^\top=\Sigma$; IRF $A^hP$ |
| Backtest | origin $t$: fit on $\{1..t\}$ only, forecast $t+h$; test: change data $>t$, forecasts at $\le t$ unchanged |
| Metrics | RMSE $=\sqrt{\overline{e^2}}$, MAE $=\overline{\lvert e\rvert}$, MAPE $=100\,\overline{\lvert e/y\rvert}$ (not near 0), $R^2_{OS}=1-\sum e_m^2/\sum e_b^2$ |
| DM | $d_t=e_{1t}^2-e_{2t}^2$; $DM=\bar d/\sqrt{(\hat\gamma_0+2\sum_{k<h}\hat\gamma_k)/n}$; HLN $\times\sqrt{(n+1-2h+h(h-1)/n)/n}$, $t_{n-1}$ |
| Clark–West (nested) | $f_t=e_{s}^2-[e_{b}^2-(\hat y_s-\hat y_b)^2]$, one-sided $t$ on $\bar f>0$ (s = small, b = big) |
| ARX scenario | $\Delta x_{T+1}=x^{path}_{1}-x_T$ (jump-off); recurse on $\hat g$; $D_{T+h}=D_T\prod(1+g/100)$; bands: simulate levels |
| VAR conditioning (WZ) | $\text{dev}=M\varepsilon$, $R\varepsilon=r$ ⇒ $\varepsilon^{*}=R^\top(RR^\top)^{-1}r$; $\text{Cov}=I-R^\top(RR^\top)^{-1}R$ |
| Local projection | $y_{t+h}-y_{t-1}=\alpha_h+\beta_h s_t+\gamma^\top w_t+u_{t+h}$; IRF $=\beta_h$; NW lags $\ge h+1$ |
| Newey–West | $\hat S=\Gamma_0+\sum_{l=1}^L(1-\tfrac{l}{L+1})(\Gamma_l+\Gamma_l^\top)$, $\Gamma_l=\sum_t\hat u_t\hat u_{t-l}x_tx_{t-l}^\top$; $V=(X^\top X)^{-1}\hat S(X^\top X)^{-1}$ |
| 2SLS (just-id.) | $\hat\beta_{IV}=(Z^\top X)^{-1}Z^\top y$ |
| KKT budget | $f_i'(x_i)=\lambda$ interior; $\le\lambda$ at 0; $\ge\lambda$ at cap; $x_i=\text{clip}(\ln(a_ib_i/\lambda)/b_i,0,u_i)$; bisect on $\lambda$; $\lambda$ = shadow price |
| MC | SE $=\hat\sigma/\sqrt N$; VaR$_q$ = quantile; ES$_q=E[L\mid L\ge\text{VaR}_q]$; tail points $=N(1-q)$ |
| Vasicek | default iff $\sqrt\rho Z+\sqrt{1-\rho}\varepsilon<\Phi^{-1}(PD)$; $q$-loss $=\Phi\big((\Phi^{-1}(PD)+\sqrt\rho\Phi^{-1}(q))/\sqrt{1-\rho}\big)$ |

| Task | API |
|---|---|
| Lag in panel | `df.groupby("bank")["x"].shift(1)`; growth `x / g.shift(k) - 1` on a complete grid |
| Full quarter grid | `pd.period_range(a, b, freq="Q")`, `.reindex(...)`; `ts.dt.to_period("Q")` |
| Resample | `df.resample("QE").last()` (stocks) / `.sum()` (flows); pandas < 2.2 uses `"Q"` |
| As-of join | `pd.merge_asof(l, r, on="date", by="bank", direction="backward")` (both sorted) |
| Dedupe latest | `df.sort_values("filed_at").drop_duplicates(keys, keep="last")` |
| OLS | `np.linalg.lstsq(X, y, rcond=None)[0]`; `sm.OLS(y, sm.add_constant(X)).fit()` |
| HAC | `.fit(cov_type="HAC", cov_kwds={"maxlags": L})` |
| AR / VAR | `statsmodels.tsa.ar_model.AutoReg(y, lags=p, exog=X)`; `statsmodels.tsa.api.VAR(df).fit(p)` |
| Optimize | `minimize(f, x0, jac=g, bounds=b, constraints=[{"type":"eq","fun":h}], method="SLSQP")` |
| LP / dual | `linprog(c, A_eq=A, b_eq=b, bounds=bd, method="highs")`; `res.eqlin.marginals` |
| MILP | `milp(c, constraints=LinearConstraint(A, lb, ub), integrality=mask, bounds=Bounds(l, u))` |
| RNG | `rng = np.random.default_rng(seed)`; `rng.standard_normal((N, n))`; `rng.choice(resid, size=(S, H))` |
| Numba | `from numba import njit, prange`; `@njit(parallel=True)`; time the 2nd call |
| SQL | `ROW_NUMBER() OVER (PARTITION BY k ORDER BY t DESC)`; `LAG(x) OVER w`; `SUM(x) OVER (PARTITION BY q)`; `RANGE BETWEEN 3 PRECEDING AND CURRENT ROW` |

**Red flags:** full-sample fit or transforms · growth across gaps or banks · `diff()` on the scenario path (lost jump-off) · bands on growth, not levels · OLS SEs on LPs · "Numba" with no concrete kernel · SQL LAG without a gap check.
