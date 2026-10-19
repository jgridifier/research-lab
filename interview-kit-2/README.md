# Python quant coding interview kit 2: challenger models, scenario simulation, optimization, AI-app guardrails

> **Generic practice material for a Python quant coding interview. Synthetic data; illustrative scenarios; not investment advice; not affiliated with any employer.**

A 60-minute CoderPad-style kit for a quant role on a bank planning (FP&A) team: seven problems with starter files (paste into the pad), tested reference solutions, tiered hints, follow-ups, rubrics, a methods refresher and a one-page cheat sheet. All data are generated synthetically inside the scripts.

**Contents**

- [0. At a glance](#0-at-a-glance)
- [1. Interview plan](#1-interview-plan) (run sheet, warm-up questions, problem menu, environment notes, scoring sheet)
- [2. Problems](#2-problems): P1–P7, each with the prompt, starter and reference solution inline
- [Refresher: methods and line-by-line walkthroughs](refresher.md)
- [One-page cheat sheet](cheatsheet.md)
- [Appendix A. Files, how to run, test results](#appendix-a-files-how-to-run-test-results)

**Files in this folder:** [`solutions/`](solutions/) (p1–p7 reference solutions with data generators and asserts) · [`starters/`](starters/) (p1–p7 starter files) · [`test_starters.py`](test_starters.py) · [`run_all.sh`](run_all.sh)


# 0. At a glance

| | |
|--|-------|
| **Format** | 60 min, Python CoderPad: **~12 min intros** (3–4 warm-ups), **~37 min coding**, **~9 min for the candidate's questions** |
| **The team's four pillars** | **A** scenario design · **B** challenger models (banking-industry and internal) · **C** optimization/simulation models that change decisions · **D** AI apps adopted by business users |
| **What we must verify** | (1) **Code ownership:** the candidate writes fluent numpy/pandas live, unaided. (2) **Validator → builder:** catches a leaky backtest and builds an honest benchmark in code (Pillar B). (3) **Scenario simulation:** builds and vectorizes a compartmental (stock-flow) scenario grid (Pillars A + C). (4) **Challenger design:** a small overlay on a frozen champion that is validated out-of-time and leaves the trusted regime untouched (Pillar B). (5) **Range:** LP/MILP tooling (Pillar C), SQL/data pipelines, and guardrails for an AI app (Pillar D) via the swap-ins. |
| **Core path (34 min + transitions)** | **P1** champion outcomes analysis: leak test + honest backtest + DM (11) → **P2** deposit-runoff compartmental model + scenario grid (12) → **P3** ridge overlay on a frozen champion (11) |
| **Swap-ins** | **P4** scenario distance with optimal transport (LP + sliced Wasserstein) · **P5** planning allocation LP → MILP with duals · **P6** SQL on messy GL actuals · **P7** AI variance explainer: price/volume/mix + narrative guardrail |
| **Files** | `solutions/p1…p7_*.py` (reference + generator + asserts) · `starters/p1…p7_starter.py` (paste into the pad) · `test_starters.py` · `run_all.sh` |
| **Hire bar (suggested)** | **≥ 3/4 on two of the three core problems, one of which is P1 or P2**, and **≥ 3/4 on "own Python"**. A 2 on P3 is fine if the candidate *explains* the overlay idea well. A 1 on any core problem, or code the candidate can't explain line by line, is a no. |

# 1. Interview plan

## 1.1 Minute-by-minute run sheet (60 min)

| Clock | Segment | What you do | Checkpoints / hard stop |
|--|---|---------|------|
| 0:00–0:02 | **Your intro + format** | "About 35–40 minutes in the pad, then time for your questions. Think out loud. Looking up API docs is fine; please keep AI assistants off for this one so I can see your own code." | — |
| 0:02–0:04 | **Candidate 2-minute background** | Let them talk; don't interrupt. | — |
| 0:04–0:12 | **Warm-ups W1–W3** (§1.2, ~2.5 min each) | Each one primes a core problem. W4 only if someone ran short. | Hard stop at **0:12** ("let's pick that up in code"). |
| 0:12–0:13 | **Pad setup** | Paste the version-check cell (§1.4), run it, then paste `p1_starter.py`. | Note what's missing (scipy? sklearn? `milp`?). |
| 0:13–0:24 | **P1 champion outcomes analysis** (11) | Leak test → leak-free backtest → RMSE/MAE → DM. | **0:16** names the leak (oracle $x_{t+1}$) · **0:19** `leak_test` runs · **0:22** `fixed_backtest` passes · **0:24** DM (verbal if behind). |
| 0:24–0:25 | Transition | Paste `p2_starter.py` below or replace. | — |
| 0:25–0:37 | **P2 deposit runoff scenarios** (12) | `simulate` → vectorized `trough_grid` → (stretch) breach frontier. | **0:29** `simulate` passes the hand check · **0:34** grid vectorized and matches · **0:35–0:37** debrief: "Which cell is *severe but plausible*?" |
| 0:37–0:38 | Transition | Paste `p3_starter.py`. | — |
| 0:38–0:49 | **P3 overlay on a frozen champion** (11) | Hinge basis → ridge on residuals → time-ordered λ → holdout report. | **0:41** basis + `fit_overlay` · **0:45** λ chosen on a time split · **0:47** report · **0:47–0:49** debrief: "Would you sign off on this challenger?" |
| 0:49–0:51 | **Close the pad** | Ownership question: "If you had another hour, what would you change first in P2 or P3?" Score the cross-cutting rows now. | — |
| 0:51–1:00 | **Candidate's questions** | Protect this time; it's part of the sell. | End on time. |

**Coding time:** 0:12–0:49 = **37 min** (P1 11 + P2 12 + P3 11, plus pad setup and transitions). Core problem budget ≈ 34–36 min.

## 1.2 Warm-up questions for the intro (W1–W3 core, W4 if time)

These ease the candidate in, and each one primes a coding problem so the switch to the pad is natural.

1. **W1 → P1 (Pillar B).** *"Tell me about a model you've had to validate or benchmark. What was the champion, what challenger or naive benchmark did you use, and how did you check that the backtest was honest? Which tools did you do it in?"*
   Good: a concrete model family, outcomes analysis and benchmarking described concretely (out-of-time windows, naive benchmarks, "what was known at the origin?"), and a way to *test* for leakage rather than read the document. Weak: governance vocabulary only, nothing hands-on.
2. **W2 → P2 (Pillars A + C).** *"Tell me about a simulation or scenario model you built yourself. Which part was yours, how did you choose the scenario grid, and how would you make it fast?"*
   Good: owns a specific piece (equations, calibration, code, grid design) and says "broadcast over the grid, loop over time." Weak: describes conclusions, not code.
3. **W3 → P3 (Pillar B).** *"Suppose a production forecast owned by another team has started to miss, and you're not allowed to re-fit it. How would you build a challenger or overlay, and how would you show it doesn't damage what already works?"*
   Good: fit on residuals, regularize, make the correction exactly zero where the champion is trusted, validate out-of-time, champion untouched. Weak: "retrain the whole model."
4. **W4 (if time) → swap-ins P4/P7 (curiosity, code ownership).** *"Tell me about something you built that nobody asked you to build. Did anyone else end up using it?"*
   Good: a concrete small tool or experiment, what broke, what's next. Weak: only formal deliverables.


## 1.3 Problem menu, pillar map and how to adapt

| ID | Problem | Role | Min | Pillar | Primary signal |
|-|--------|---|-|-|----|
| **P1** | Champion outcomes analysis: perturbation leak test, find the oracle-regressor leak, leak-free expanding backtest vs RW/mean, DM (HLN) | **Core** | 11 | **B** (validation of challenger/benchmark models) | Backtest discipline in finance |
| **P2** | Two-segment deposit-runoff compartmental model; vectorized shock × pass-through grid; breach frontier by bisection | **Core** | 12 | **A** + **C** (scenario design; simulation that changes a decision) | Simulation code ownership, broadcasting, monotonicity sanity |
| **P3** | Ridge overlay on a frozen champion: hinge basis that is zero in the old regime, time-ordered λ, out-of-time holdout | **Core** | 11 | **B** (internal challenger models) | Challenger design and validation |
| P4 | Distance of a stress-scenario distribution from history: 1-D Wasserstein, OT as an LP (linprog), vectorized sliced W2 | Swap-in | 8–10 | **A** (scenario plausibility) + **C** (LP) | Optimal-transport fluency; turning a method into an LP |
| P5 | Planning allocation: LP with budget and regulatory floor, duals checked by finite difference; MILP with set-up costs/min scale/cardinality, verified by brute force; greedy counterexample | Swap-in | 10–12 | **C** (optimization that changes decisions) | Solver tooling, duals, MILP formulation |
| P6 | SQL on GL actuals: latest re-post wins, cost-centre re-org mapping, budget variance, YTD, gap-aware MoM (sqlite3 + pandas cross-check) | Swap-in | 8–10 | **B**/**D** (internal data that feeds challengers and apps) | SQL window functions, data instincts |
| P7 | AI variance explainer: exact price/volume/mix decomposition + a guardrail that flags unsupported numbers and wrong directions in an LLM-drafted narrative | Swap-in | 8–10 | **D** (AI apps adopted by business users) | Building trustworthy AI tooling for finance users |

**If the candidate is fast:**

- **P1 done by 0:20:** ask the nested-model question (Clark–West) and "is the full-sample z-score a leak too?" (no: OLS with an intercept is affine-invariant, which is why the perturbation test, not code-reading, is the arbiter). Then move on; bank the time.
- **P2 grid done by 0:32:** the breach frontier in code (bisection), then the rate-reversal follow-up (trough mid-path).
- **P3 done by 0:45:** a **4-minute P4 mini** (paste `p4_starter.py`, ask only for `sliced_wasserstein`). Or P7 part 1 (PVM) as a 4-minute exercise if you'd rather probe Pillar D.

**If the candidate is stuck:**

- **P1 past 0:19 with no leak test:** give Hint 2 (the perturbation idea), and if needed paste `leak_test`. What we score is the leak-free backtest and the explanation.
- **P2 past 0:31 on vectorization:** accept the loop version (`trough_loop`), and ask for the broadcasting shapes verbally: `(n_shock, 1, H)` × `(1, n_beta, 1)`.
- **P3 past 0:43:** paste `hinge_basis` and `fit_overlay`; ask only for the time-ordered λ choice and the holdout report. Then go straight to the sign-off debrief; conceptual answers still count.
- **Shaky Python overall** (no broadcasting, row loops everywhere, can't read a traceback): don't use P4 as a swap-in, since a candidate's research home turf can flatter them. Use the last minutes on P7 part 1 or P6 to see basic pandas/SQL.

**When to swap a core problem out:** if W2 shows the candidate clearly owned simulation code, keep P2 but go fast to the frontier. If P1 and P2 are both strong by 0:36, **swap P3 for P5** (the Pillar C gap is more informative than a third strong signal). If the candidate is visibly unfamiliar with deposits, keep P2 anyway; the domain is in the prompt and the code is generic.

**Second round** (recommended if the candidate clears the bar): P5 (12) + P6 (10) + P7 (10) is a ~35-minute pad covering the remaining gaps (solvers, SQL, AI-app guardrails). Add P4 (8) if you want the OT check.

## 1.4 Environment notes, version-check cell and fallbacks

**Run this first in the pad** (one cell; it never fails):

```python
import sys, importlib, sqlite3
print("python", sys.version.split()[0], "| sqlite", sqlite3.sqlite_version)
for m in ["numpy", "pandas", "scipy", "statsmodels", "sklearn"]:
    try:
        print(f"{m:12s}", importlib.import_module(m).__version__)
    except ImportError:
        print(f"{m:12s} MISSING")
try:
    from scipy.optimize import milp  # noqa: F401  (scipy >= 1.9)
    print("scipy.optimize.milp available")
except ImportError:
    print("no milp: P5 uses the brute-force verifier")
```

- **What CoderPad documents:** the standard Python 3 pad ships numpy, scipy, pandas, scikit-learn and statsmodels. CoderPad's older "Screen" product has documented older versions (Python 3.11-era with NumPy 1.20 / pandas 1.2 / SciPy 1.6). I could not see your pad; trust the version cell on the day.
- **Tested here** (every reference solution and every starter, see Appendix A): (a) Python 3.13.5 / numpy 2.5.4 / pandas 3.0.6 / scipy 1.18.1 / statsmodels 0.15.0 / scikit-learn 1.9.1 with FutureWarnings promoted to errors; (b) Python 3.12 / numpy 2.0.2 / pandas 2.2.3 / scipy 1.18.1 / statsmodels 0.15.0 / scikit-learn 1.9.1 with FutureWarning and DeprecationWarning as errors; (c) **Python 3.9 / numpy 1.20.2 / pandas 1.2.4 / scipy 1.6.3 / statsmodels 0.12.2 / scikit-learn 0.24.2** (CoderPad-Screen-like); (d) **numpy + pandas only** (no scipy, statsmodels or scikit-learn).

| Missing | Numpy-only fallback built into the reference code |
|---|---|
| statsmodels | P1 OLS via `np.linalg.lstsq`; the statsmodels cross-check is skipped |
| scipy.stats | P1 DM p-value from the normal CDF via `math.erf` (instead of $t_{n-1}$) |
| scipy.optimize.linprog | P4 skips the LP part (1-D formula and sliced W still run); P5 skips the LP and solves the MILP by brute force (fixed funding set ⇒ greedy is exact) |
| `scipy.optimize.milp` (scipy < 1.9) | P5 brute-force verifier over all $2^8$ funding sets; duals need scipy ≥ 1.7, otherwise the finite difference is the dual |
| scikit-learn | P3 uses the closed-form ridge (it does anyway); the `Ridge(fit_intercept=False)` cross-check is skipped |
| SQLite < 3.25 (no window functions) | P6: run `pandas_reference` instead and discuss the SQL verbally |

- **pandas-version gotchas** the candidate might hit (don't penalize): `pct_change()` forward-filled gaps by default before pandas 2.1 (removed in 3.0); copy-on-write is the default in 3.0, so chained assignment silently does nothing; offset alias `"Q"` → `"QE"` for `resample` since 2.2 (Period frequencies still use `"Q"`).
- **AI assistance:** switch CoderPad's AI assistant off for this pad. LLM-tooling experience is better probed verbally (W4, P7 debrief).

## 1.5 Scoring sheet

Score each problem used on its 1–4 rubric (in each problem section), plus five cross-cutting dimensions:

| Dimension | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| **Own Python** (fluency, idiom, debugging) | Can't get a basic numpy/pandas step running without heavy help | Gets there with row loops, trial and error, API guessing | Idiomatic numpy/pandas; reads tracebacks and fixes quickly | Fluent; writes small checks unprompted; clean functions; broadcasting comes naturally |
| **Validation instinct** (Pillar B) | Trusts the champion's numbers | Spots the leak only when pointed at the line | Finds it, and *tests* for it (perturbation) | Also separates material from immaterial issues (affine z-score), nested-model inference, vintages, small-n caution |
| **Scenario/simulation sense** (A + C) | Plugs numbers in, no sanity checks | Correct mechanics, no checks on conservation or monotonicity | Conservation/monotonicity checks; explains what the grid means for a decision | Also reverse stress test, plausibility of the severe cell, parameter uncertainty, where the model breaks |
| **Optimization/decision framing** (C, if P2 frontier or P5 used) | No link from model to decision | Solves but can't interpret | Reads duals/frontiers as decision information | Proposes the constraint the business actually cares about; knows when LP vs MILP vs heuristic |
| **Communication** (D-readiness) | Silent or unclear | Explains only when asked | Narrates choices clearly | Explains trade-offs the way they would to a finance partner |

**Decision guide:** strong yes = two core problems ≥ 3 (incl. P1 or P2), own Python ≥ 3, plus one 4 anywhere. Yes = two core ≥ 3 and own Python ≥ 3. Lean no = only one core ≥ 3, or own Python = 2. No = any core 1, or code the candidate can't explain.



# 2. Problems

Each problem has the prompt to paste, the starter (paste the whole file into the pad; its docstring repeats the prompt), the tested reference solution, tiered hints, follow-ups, mistakes and red flags, strong vs weak answers, and a 1–4 rubric. **Core path: P1 → P2 → P3.**

## P1. Champion outcomes analysis: leak test, honest backtest, DM (core, 11 min)

**Pillar:** **B**, challenger models (validation of a champion against benchmarks).
**Why this problem:** outcomes analysis and benchmarking are the core of model validation on a planning team. A reviewer who reads code should find the leak; a builder should *prove* it with a test and then write the honest version. The full-sample z-score is a deliberate red herring: an over-literal reviewer flags it; a careful one sees that OLS with an intercept is affine-invariant.

**Prompt to paste (or say):**

> A business line hands you its champion deposit-growth model and the backtest that "proves" it works: `champion_backtest(df)`. It re-fits at every origin and reports a very good RMSE. You're the reviewer. (1) Write `leak_test(backtest_fn, df, k)` that overwrites everything after row k with junk and returns True if any forecast made at an origin ≤ k changes. Run it on the champion. What leaks? Is the z-score a problem too? (2) Write `fixed_backtest`: the same model spec, leak-free, plus random-walk and historical-mean benchmarks. (3) RMSE/MAE and a Diebold–Mariano test versus the random walk.

**Starter ([`starters/p1_starter.py`](starters/p1_starter.py)):**

```python
# file: interview-kit-2/starters/p1_starter.py
"""
Outcomes analysis of a champion forecast. ~11 minutes.

df: quarterly, y = deposit growth (%), x = change in unemployment (pp).
champion_backtest(df) is the business line's backtest of its champion model
    y_{t+1} = c + a*y_t + b*x_{t+1} + d*x_t
It re-fits at every origin and reports a very good RMSE. You are the reviewer.

1. leak_test(backtest_fn, df, k): overwrite every row after position k with
   junk, re-run backtest_fn, and return True if ANY forecast whose origin is
   <= k changed. Run it on champion_backtest. What leaks, and is the
   full-sample z-score also a problem?
2. fixed_backtest(df, first_origin=60): same spec, leak-free. Return a
   DataFrame indexed by target date with columns origin, actual, forecast,
   rw (random walk: y_t) and mean (historical mean of y up to t).
3. RMSE/MAE for forecast, rw, mean; then diebold_mariano(e1, e2) -> (stat, p).
numpy/pandas are enough; scipy and statsmodels are available.
"""
import math
import numpy as np
import pandas as pd

try:
    from scipy import stats
except ImportError:          # numpy-only fallback: normal CDF via math.erf
    stats = None


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def make_data(T: int = 140, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x = np.zeros(T)
    y = np.zeros(T)
    for t in range(1, T):
        x[t] = 0.6 * x[t - 1] + rng.normal(0, 0.35)
        y[t] = 0.5 + 0.4 * y[t - 1] - 1.5 * x[t] - 0.6 * x[t - 1] + rng.normal(0, 0.4)
    idx = pd.period_range("1991Q1", periods=T, freq="Q")
    return pd.DataFrame({"y": y, "x": x}, index=idx)


# ----------------------------------------------------------------------------
# The champion's backtest, as handed over (contains a leak; do not "fix" here)
# ----------------------------------------------------------------------------
def champion_backtest(df: pd.DataFrame, first_origin: int = 60) -> pd.DataFrame:
    """Champion spec: y_{t+1} = c + a*y_t + b*x_{t+1} + d*x_t.
    Re-fits at every origin (looks careful) but plugs in the REALIZED x_{t+1}."""
    xs = (df["x"] - df["x"].mean()) / df["x"].std()   # full-sample z-score (harmless: affine)
    recs = []
    for t in range(first_origin, len(df) - 1):
        yy = df["y"].iloc[1:t + 1].to_numpy()
        X = np.column_stack([np.ones(t), df["y"].iloc[:t].to_numpy(),
                             xs.iloc[1:t + 1].to_numpy(), xs.iloc[:t].to_numpy()])
        b = np.linalg.lstsq(X, yy, rcond=None)[0]
        xrow = np.array([1.0, df["y"].iloc[t], xs.iloc[t + 1], xs.iloc[t]])   # <- x_{t+1}: oracle
        recs.append(dict(origin=t, target=df.index[t + 1], actual=df["y"].iloc[t + 1],
                         forecast=float(xrow @ b)))
    return pd.DataFrame(recs).set_index("target")



def leak_test(backtest_fn, df: pd.DataFrame, k: int, junk: float = 1e3) -> bool:
    raise NotImplementedError


def fixed_backtest(df: pd.DataFrame, first_origin: int = 60) -> pd.DataFrame:
    raise NotImplementedError


def diebold_mariano(e1, e2, h: int = 1):
    """Return (stat, p_value). Negative stat => model 1 more accurate."""
    raise NotImplementedError


def check():
    df = make_data()
    champ = champion_backtest(df)
    print(champ.head(3))
    assert leak_test(champion_backtest, df, k=90), "the champion should fail the leak test"
    bt = fixed_backtest(df)
    assert {"origin", "actual", "forecast", "rw", "mean"} <= set(bt.columns)
    assert not leak_test(fixed_backtest, df, k=90), "your backtest leaks"
    rmse = {c: float(np.sqrt(((bt.actual - bt[c]) ** 2).mean())) for c in ["forecast", "rw", "mean"]}
    print("champion RMSE", round(float(np.sqrt(((champ.actual - champ.forecast) ** 2).mean())), 3), "| honest", rmse)
    assert rmse["forecast"] < rmse["rw"] < rmse["mean"]
    stat, p = diebold_mariano(bt.actual - bt.forecast, bt.actual - bt.rw)
    print("DM", round(stat, 2), round(p, 4))
    assert stat < 0
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p1_champion_outcomes.py`](solutions/p1_champion_outcomes.py)):**

```python
# file: interview-kit-2/solutions/p1_champion_outcomes.py
"""
Problem 1 (core, ~11 min): outcomes analysis of a "champion" forecast.

A business line hands you its champion deposit-growth model and the backtest
that "proves" it works. As the independent reviewer you must:
  1. Write a generic leak test: perturb every observation after origin k and
     check that no forecast made at an origin <= k moves.
  2. Find the leak in champion_backtest (it uses the realized x_{t+1}: an
     oracle regressor) and write a leak-free backtest of the same spec.
  3. Benchmark against a random walk and the historical mean (RMSE/MAE) and
     run a Diebold-Mariano test (HLN-corrected) vs the random walk.

DGP: x_t = 0.6 x_{t-1} + eta_t (change in unemployment, pp)
     y_t = 0.5 + 0.4 y_{t-1} - 1.5 x_t - 0.6 x_{t-1} + e_t (deposit growth, %)
Only numpy + pandas required; scipy (t CDF) and statsmodels (OLS
cross-check) are used when available.
"""
import math
import numpy as np
import pandas as pd

try:
    from scipy import stats
except ImportError:          # numpy-only fallback: normal CDF via math.erf
    stats = None


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def make_data(T: int = 140, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x = np.zeros(T)
    y = np.zeros(T)
    for t in range(1, T):
        x[t] = 0.6 * x[t - 1] + rng.normal(0, 0.35)
        y[t] = 0.5 + 0.4 * y[t - 1] - 1.5 * x[t] - 0.6 * x[t - 1] + rng.normal(0, 0.4)
    idx = pd.period_range("1991Q1", periods=T, freq="Q")
    return pd.DataFrame({"y": y, "x": x}, index=idx)


# ----------------------------------------------------------------------------
# The champion's backtest, as handed over (contains a leak; do not "fix" here)
# ----------------------------------------------------------------------------
def champion_backtest(df: pd.DataFrame, first_origin: int = 60) -> pd.DataFrame:
    """Champion spec: y_{t+1} = c + a*y_t + b*x_{t+1} + d*x_t.
    Re-fits at every origin (looks careful) but plugs in the REALIZED x_{t+1}."""
    xs = (df["x"] - df["x"].mean()) / df["x"].std()   # full-sample z-score (harmless: affine)
    recs = []
    for t in range(first_origin, len(df) - 1):
        yy = df["y"].iloc[1:t + 1].to_numpy()
        X = np.column_stack([np.ones(t), df["y"].iloc[:t].to_numpy(),
                             xs.iloc[1:t + 1].to_numpy(), xs.iloc[:t].to_numpy()])
        b = np.linalg.lstsq(X, yy, rcond=None)[0]
        xrow = np.array([1.0, df["y"].iloc[t], xs.iloc[t + 1], xs.iloc[t]])   # <- x_{t+1}: oracle
        recs.append(dict(origin=t, target=df.index[t + 1], actual=df["y"].iloc[t + 1],
                         forecast=float(xrow @ b)))
    return pd.DataFrame(recs).set_index("target")


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def leak_test(backtest_fn, df: pd.DataFrame, k: int, junk: float = 1e3) -> bool:
    """True if a leak is detected: some forecast with origin <= k changes when
    every observation dated after k is overwritten."""
    base = backtest_fn(df)
    bad = df.copy()
    bad.iloc[k + 1:] = junk
    pert = backtest_fn(bad)
    keep = base["origin"] <= k
    a = base.loc[keep, "forecast"].to_numpy()
    b = pert.loc[pert["origin"] <= k, "forecast"].to_numpy()
    return not (len(a) == len(b) and np.allclose(a, b, rtol=0, atol=1e-10))


def ols(X, y):
    return np.linalg.lstsq(X, y, rcond=None)[0]


def fixed_backtest(df: pd.DataFrame, first_origin: int = 60) -> pd.DataFrame:
    """Same champion spec, but x_{t+1} is replaced by its own AR(1) forecast
    fitted on data <= t. Also returns the two naive benchmarks."""
    recs = []
    for t in range(first_origin, len(df) - 1):
        hist = df.iloc[: t + 1]                       # <- the no-look-ahead line
        y, x = hist["y"].to_numpy(), hist["x"].to_numpy()
        # 1) forecast x_{t+1} with an AR(1) on x (data <= t only)
        ax = ols(np.column_stack([np.ones(t), x[:-1]]), x[1:])
        x_next = ax[0] + ax[1] * x[-1]
        # 2) champion regression on rows s = 1..t: y_s on (1, y_{s-1}, x_s, x_{s-1})
        X = np.column_stack([np.ones(t), y[:-1], x[1:], x[:-1]])
        b = ols(X, y[1:])
        f = float(np.array([1.0, y[-1], x_next, x[-1]]) @ b)
        recs.append(dict(origin=t, target=df.index[t + 1], actual=df["y"].iloc[t + 1],
                         forecast=f, rw=y[-1], mean=y.mean()))
    return pd.DataFrame(recs).set_index("target")


def error_table(bt: pd.DataFrame, cols=("forecast", "rw", "mean")) -> pd.DataFrame:
    out = {}
    for c in cols:
        e = bt["actual"] - bt[c]
        out[c] = {"RMSE": float(np.sqrt(np.mean(e ** 2))), "MAE": float(np.mean(np.abs(e)))}
    return pd.DataFrame(out).T


def _norm_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def diebold_mariano(e1, e2, h: int = 1):
    """DM with squared-error loss, rectangular LRV to lag h-1, HLN correction.
    Negative stat => model 1 more accurate. Returns (stat, two-sided p)."""
    e1, e2 = np.asarray(e1, float), np.asarray(e2, float)
    d = e1 ** 2 - e2 ** 2
    n = len(d)
    dc = d - d.mean()
    gam = [dc @ dc / n] + [dc[k:] @ dc[:-k] / n for k in range(1, h)]
    lrv = gam[0] + 2 * sum(gam[1:])
    if lrv <= 0:
        lrv = gam[0] + 2 * sum((1 - k / h) * gam[k] for k in range(1, h))
    stat = d.mean() / math.sqrt(lrv / n)
    stat *= math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    p = 2 * (1 - stats.t.cdf(abs(stat), df=n - 1)) if stats else 2 * (1 - _norm_cdf(abs(stat)))
    return float(stat), float(p)


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    df = make_data()
    champ = champion_backtest(df)
    fixed = fixed_backtest(df)
    # 1. the leak test flags the champion and clears the fixed version
    assert leak_test(champion_backtest, df, k=90), "champion should leak"
    assert not leak_test(fixed_backtest, df, k=90), "fixed version must not leak"
    # 2. the leak flatters the champion: oracle RMSE is far below the honest one
    rm_champ = float(np.sqrt(np.mean((champ.actual - champ.forecast) ** 2)))
    tab = error_table(fixed)
    assert rm_champ < 0.75 * tab.loc["forecast", "RMSE"], (rm_champ, tab)
    # 3. the honest model still beats both naive benchmarks
    assert tab.loc["forecast", "RMSE"] < tab.loc["rw", "RMSE"]
    assert tab.loc["forecast", "RMSE"] < tab.loc["mean", "RMSE"]
    dm = diebold_mariano(fixed.actual - fixed.forecast, fixed.actual - fixed.rw)
    assert dm[0] < 0 and dm[1] < 0.05, dm
    # 4. DM is antisymmetric
    assert np.isclose(dm[0], -diebold_mariano(fixed.actual - fixed.rw, fixed.actual - fixed.forecast)[0])
    # 5. the full-sample z-score alone is NOT a leak (OLS with intercept is affine-invariant)
    #    (the AR(1) forecast of x is affine-equivariant too, so y forecasts are unchanged)
    d2 = df.copy()
    d2["x"] = (df["x"] - df["x"].mean()) / df["x"].std()
    a = fixed_backtest(df)["forecast"].to_numpy()
    b = fixed_backtest(d2)["forecast"].to_numpy()
    assert np.allclose(a, b, atol=1e-8), "affine rescaling of x should not change forecasts"
    # 5b. a champion variant that keeps the full-sample z-score but drops x_{t+1}
    #     passes the leak test: the z-score is not a material leak for OLS
    def champion_lagged_only(d):
        xs = (d["x"] - d["x"].mean()) / d["x"].std()
        recs = []
        for t in range(60, len(d) - 1):
            X = np.column_stack([np.ones(t), d["y"].iloc[:t].to_numpy(), xs.iloc[:t].to_numpy()])
            b = ols(X, d["y"].iloc[1:t + 1].to_numpy())
            f = float(np.array([1.0, d["y"].iloc[t], xs.iloc[t]]) @ b)
            recs.append(dict(origin=t, target=d.index[t + 1], forecast=f))
        return pd.DataFrame(recs).set_index("target")
    assert not leak_test(champion_lagged_only, df, k=90, junk=5.0)
    # 6. statsmodels cross-check of the regression, if installed
    try:
        import statsmodels.api as sm
        y, x = df.y.to_numpy(), df.x.to_numpy()
        X = np.column_stack([np.ones(len(y) - 1), y[:-1], x[1:], x[:-1]])
        assert np.allclose(sm.OLS(y[1:], X).fit().params, ols(X, y[1:]))
        sm_ok = True
    except ImportError:
        sm_ok = False
    print("p1 OK  | n_oos =", len(fixed), "| statsmodels cross-check:", sm_ok)
    print("champion (oracle x) RMSE = %.3f" % rm_champ)
    print(tab.round(3).to_string())
    print("DM fixed vs rw: stat=%.2f p=%.4f" % dm)


if __name__ == "__main__":
    _tests()
```

**Hints (tiered):**

1. "The champion's regression has $x_{t+1}$ on the right-hand side. At origin $t$, do you know $x_{t+1}$?" (No: unemployment for next quarter isn't published yet. That's an **oracle regressor**.)
2. "Don't argue from the code; make the backtest tell you. If you scramble every row after $k$, which forecasts are *allowed* to change?" (Only those with origin $> k$. That is the leak test.)
3. "For the honest version, either drop $x_{t+1}$ or forecast it from data ≤ t. An AR(1) on $x$ fitted inside `hist` is enough." Paste the `x_next` lines from the reference if needed.

**Follow-ups:**

- "Is the full-sample z-score a leak?" (Mechanically it uses future data, but for OLS with an intercept an affine transform of a regressor leaves fitted values unchanged, so the forecasts don't move. **Not material.** The test proves it: the reference's `champion_lagged_only` passes the leak test with the z-score in place. It *would* matter for ridge/lasso, a PCA, or anything non-affine.)
- "When is using realized $x_{t+1}$ legitimate?" (In a **conditional** evaluation, "how good is the model if the scenario is right?", which is exactly how stress-test models are used. It must be labeled as such and never reported as forecast accuracy.)
- "The honest model nests the mean benchmark. Is DM right?" (Clark–West for nested models; DM is undersized under the null.)
- "Only 79 out-of-sample points. How do you write this up?" (DM p-value plus stability across split points and subperiods; RMSE ratios with a caveat; no single headline number.)
- "How would this show up in a validation report?" (Finding: performance overstated by an oracle regressor; required remediation: unconditional backtest or explicit relabeling; compensating control: benchmark against RW/mean on the same windows.)

**Common mistakes / red flags:**

- Re-reading the code for five minutes instead of writing the test; or writing a "leak test" that only perturbs one row.
- Comparing forecasts by *position* instead of by origin, so the leak test passes or fails for the wrong reason.
- Historical mean computed over the full sample in the benchmark (a leak in the benchmark is still a leak).
- Off-by-one: pairing $y_{t+1}$ with $x_t$ in one place and $x_{t+1}$ in another.
- *Red flag:* calls the z-score a "critical finding" and never notices the oracle regressor.
- *Red flag:* can't explain why the champion's RMSE (≈ 0.39) is so much better than the honest one (≈ 0.65).

**Strong vs weak:**

- *Strong:* names the oracle regressor within a minute, writes the perturbation test first, labels the z-score as immaterial *with the reason*, writes the hist slice as the first line of the loop, mentions conditional vs unconditional evaluation and Clark–West unprompted.
- *Weak:* finds the leak only with Hint 1; leak test needs heavy help; DM only verbal; treats every full-sample statistic as equally bad.

**Rubric:** **4** leak found and proven, honest backtest + DM in ~11 min, z-score correctly judged immaterial · **3** leak found, honest backtest and metrics; leak test or DM needs a nudge · **2** honest backtest only after Hints 1–2; DM verbal · **1** doesn't find the leak, or the "fixed" version still leaks.

## P2. Deposit runoff scenarios: a two-segment compartmental model (core, 12 min)

**Pillars:** **A** scenario design and **C** simulation that changes a decision (where is the runoff limit breached?).
**Why this problem:** compartmental (stock-flow) models are a natural way to build deposit scenarios: two segments (stable and rate-sensitive), migration between them driven by the rate gap, and a scenario grid (shock × pass-through). It tests simulation code, broadcasting, and whether the candidate sanity-checks a model before trusting it. The breach frontier turns the grid into a decision: "at our expected pass-through, how big a rate shock can we absorb before breaching a 15% runoff limit?" (a small reverse stress test).

**Prompt to paste:**

> Deposits are split into stable balances S and rate-sensitive balances R. Each quarter the market rate follows `rate_path` (it ramps to `m0 + shock` over two quarters), the bank pays `beta × m`, and the rate gap is `g = max(m − beta·m, 0)`. Each quarter a fraction `mu·g` of S migrates to R, `s0` of S runs off, and `r0 + k·g` of R runs off. (1) Write `simulate(p, shock, beta)` returning S and R for quarters 0..8. (2) Write `trough_grid(p, shocks, betas)`: the lowest total deposits over the 8 quarters as a share of today, for every (shock, beta), without a Python loop over the grid. (3) If time: for each beta, the smallest shock that takes the trough below 85%.

**Starter ([`starters/p2_starter.py`](starters/p2_starter.py)):**

```python
# file: interview-kit-2/starters/p2_starter.py
"""
Deposit runoff scenarios: a two-segment compartmental model. ~13 minutes.

S = stable deposits, R = rate-sensitive deposits (start: S0, R0 in PARAMS).
Quarter h = 1..H: market rate m_h = m0 + shock * min(h / ramp, 1)
(rate_path gives you this), the bank pays beta * m_h, so the gap is
g_h = max(m_h - beta * m_h, 0). Fractions of start-of-quarter balances:
    S -> R migration : mu * g_h      S -> out : s0      R -> out : r0 + k * g_h
(cap each flow so no balance goes negative).

1. simulate(p, shock, beta) -> (S, R), numpy arrays of length H + 1.
2. trough_grid(p, shocks, betas) -> array (len(shocks), len(betas)) of
   min_h (S_h + R_h) / (S0 + R0). No Python loop over the grid
   (looping over the 8 quarters is fine).
3. If time: for each beta, the smallest shock whose trough is <= 0.85.
"""
import numpy as np

PARAMS = dict(S0=700.0, R0=300.0, m0=0.5, ramp=2, mu=0.01, s0=0.002, r0=0.005, k=0.025, H=8)


# ----------------------------------------------------------------------------
# Synthetic setup (parameters are illustrative, not calibrated to any bank)
# ----------------------------------------------------------------------------
def make_setup():
    shocks = np.linspace(0.0, 5.0, 21)      # pp of market-rate shock
    betas = np.linspace(0.0, 0.8, 9)        # deposit pass-through
    return dict(PARAMS), shocks, betas


def rate_path(m0, shock, ramp, H):
    h = np.arange(1, H + 1)
    return m0 + np.multiply.outer(np.asarray(shock, float), np.minimum(h / ramp, 1.0))



def simulate(p: dict, shock: float, beta: float):
    raise NotImplementedError


def trough_grid(p, shocks, betas):
    raise NotImplementedError


def check():
    p, shocks, betas = make_setup()
    S, R = simulate(p, 2.0, 0.3)
    assert len(S) == p["H"] + 1 and S[0] == p["S0"] and R[0] == p["R0"]
    g1 = (0.5 + 2.0 * 0.5) * 0.7
    assert np.isclose(S[1], 700 * (1 - 0.01 * g1 - 0.002)), S[1]
    assert np.isclose(R[1], 300 * (1 - 0.005 - 0.025 * g1) + 700 * 0.01 * g1), R[1]
    q = dict(p, s0=0.0, r0=0.0, k=0.0)
    S, R = simulate(q, 3.0, 0.2)
    assert np.allclose(S + R, 1000.0), "with no outflows total deposits are conserved"
    tg = trough_grid(p, shocks, betas)
    assert tg.shape == (len(shocks), len(betas))
    S, R = simulate(p, shocks[8], betas[3])
    assert np.isclose(tg[8, 3], (S + R).min() / 1000.0), "grid must match simulate()"
    assert (np.diff(tg, axis=0) <= 1e-12).all(), "bigger shock should not help"
    print(np.round(tg[::4, ::2], 3))
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p2_deposit_runoff_scenarios.py`](solutions/p2_deposit_runoff_scenarios.py)):**

```python
# file: interview-kit-2/solutions/p2_deposit_runoff_scenarios.py
"""
Problem 2 (core, ~13 min): two-segment deposit runoff simulation and a
scenario grid (a stock-flow compartmental model applied to deposits).

Balances: S = stable/core deposits, R = rate-sensitive deposits.
Each quarter h = 1..H the market rate is m_h = m0 + shock * min(h / ramp, 1)
and the bank pays d_h = beta * m_h, so the rate gap is g_h = max(m_h - d_h, 0).
Flows (fractions of the start-of-quarter balance, each capped at 1):
    S -> R  migration   : mu * g_h                 ("force of infection")
    S -> out organic    : s0
    R -> out runoff     : r0 + k * g_h
Tasks
  1. simulate(...) -> arrays S, R of length H + 1 (index 0 = today).
  2. trough_grid(shocks, betas): trough of total deposits as a share of
     today's total, for every (shock, beta). Vectorize (no Python loop over
     the grid) and check it against the loop version.
  3. breach_frontier: for each beta, the smallest shock whose trough falls
     below a limit (e.g. 85% of today = a 15% runoff limit), by bisection.
Only numpy required.
"""
import numpy as np

PARAMS = dict(S0=700.0, R0=300.0, m0=0.5, ramp=2, mu=0.01, s0=0.002, r0=0.005, k=0.025, H=8)


# ----------------------------------------------------------------------------
# Synthetic setup (parameters are illustrative, not calibrated to any bank)
# ----------------------------------------------------------------------------
def make_setup():
    shocks = np.linspace(0.0, 5.0, 21)      # pp of market-rate shock
    betas = np.linspace(0.0, 0.8, 9)        # deposit pass-through
    return dict(PARAMS), shocks, betas


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def rate_path(m0, shock, ramp, H):
    h = np.arange(1, H + 1)
    return m0 + np.multiply.outer(np.asarray(shock, float), np.minimum(h / ramp, 1.0))


def simulate(p: dict, shock: float, beta: float):
    """Loop version: one scenario. Returns (S, R) arrays of length H+1."""
    H = p["H"]
    S = np.empty(H + 1); R = np.empty(H + 1)
    S[0], R[0] = p["S0"], p["R0"]
    m = rate_path(p["m0"], shock, p["ramp"], H)
    for h in range(1, H + 1):
        g = max(m[h - 1] - beta * m[h - 1], 0.0)
        mig = min(p["mu"] * g, 1.0)
        out_s = min(p["s0"], 1.0 - mig)            # total S outflow fraction <= 1
        run_r = min(p["r0"] + p["k"] * g, 1.0)
        S[h] = S[h - 1] * (1 - mig - out_s)
        R[h] = R[h - 1] * (1 - run_r) + S[h - 1] * mig
    return S, R


def trough_loop(p, shocks, betas):
    out = np.empty((len(shocks), len(betas)))
    D0 = p["S0"] + p["R0"]
    for i, sh in enumerate(shocks):
        for j, b in enumerate(betas):
            S, R = simulate(p, sh, b)
            out[i, j] = (S + R).min() / D0
    return out


def trough_grid(p, shocks, betas):
    """Vectorized over the whole grid: arrays of shape (n_shock, n_beta)."""
    shocks = np.asarray(shocks, float); betas = np.asarray(betas, float)
    m = rate_path(p["m0"], shocks, p["ramp"], p["H"])          # (n_shock, H)
    g = np.maximum(m[:, None, :] * (1 - betas[None, :, None]), 0.0)  # (ns, nb, H)
    mig = np.minimum(p["mu"] * g, 1.0)
    out_s = np.minimum(p["s0"], 1.0 - mig)
    run_r = np.minimum(p["r0"] + p["k"] * g, 1.0)
    S = np.full(g.shape[:2], p["S0"]); R = np.full(g.shape[:2], p["R0"])
    trough = S + R
    for h in range(p["H"]):                    # loop over time only (8 steps)
        S, R = S * (1 - mig[..., h] - out_s[..., h]), R * (1 - run_r[..., h]) + S * mig[..., h]
        trough = np.minimum(trough, S + R)
    return trough / (p["S0"] + p["R0"])


def breach_frontier(p, betas, limit=0.85, lo=0.0, hi=20.0, tol=1e-6):
    """Smallest shock with trough <= limit, per beta (np.inf if none in [lo, hi])."""
    out = []
    for b in betas:
        f = lambda sh: trough_grid(p, [sh], [b])[0, 0] - limit
        if f(hi) > 0:
            out.append(np.inf); continue
        if f(lo) <= 0:
            out.append(lo); continue
        a, c = lo, hi
        while c - a > tol:
            mid = 0.5 * (a + c)
            a, c = (mid, c) if f(mid) > 0 else (a, mid)
        out.append(c)
    return np.array(out)


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    p, shocks, betas = make_setup()
    # 1. conservation: no flows out -> total constant; balances never negative
    q = dict(p, s0=0.0, r0=0.0, k=0.0)
    S, R = simulate(q, 3.0, 0.2)
    assert np.allclose(S + R, q["S0"] + q["R0"]) and R[-1] > q["R0"]
    S, R = simulate(dict(p, k=5.0), 5.0, 0.0)          # extreme runoff is capped
    assert (S >= 0).all() and (R >= 0).all()
    # 2. a hand-checked first quarter
    S, R = simulate(p, 2.0, 0.3)
    g1 = (0.5 + 2.0 * 0.5) * 0.7
    assert np.isclose(S[1], 700 * (1 - 0.01 * g1 - 0.002))
    assert np.isclose(R[1], 300 * (1 - 0.005 - 0.025 * g1) + 700 * 0.01 * g1)
    # 3. vectorized grid == loop
    tl, tg = trough_loop(p, shocks, betas), trough_grid(p, shocks, betas)
    assert tg.shape == (len(shocks), len(betas)) and np.allclose(tl, tg)
    # 4. monotone: bigger shock -> deeper trough; higher pass-through -> shallower
    assert (np.diff(tg, axis=0) <= 1e-12).all() and (np.diff(tg, axis=1) >= -1e-12).all()
    # 5. frontier hits the limit and rises with beta
    fr = breach_frontier(p, betas[:6])
    finite = np.isfinite(fr)
    assert finite.all() and (np.diff(fr) > 0).all()
    for b, sh in zip(betas[:6], fr):
        assert abs(trough_grid(p, [sh], [b])[0, 0] - 0.85) < 1e-5
    print("p2 OK  | grid", tg.shape, "| trough at (5pp, beta 0) = %.3f" % tg[-1, 0])
    print("trough share (rows: shock pp 0,1,..,5; cols: beta 0,0.2,..,0.8)")
    sel = tg[::4, ::2]
    print(np.array2string(sel, precision=3, suppress_small=True))
    print("breach frontier (shock pp for 15% runoff) by beta",
          dict(zip(np.round(betas[:6], 1).tolist(), np.round(fr, 2).tolist())))


if __name__ == "__main__":
    _tests()
```

**Hints (tiered):**

1. "Write one quarter by hand: what leaves S, what enters R, what leaves R? Use the start-of-quarter balances on the right-hand side." (A simultaneous update; updating S first and then using the new S for migration is the classic bug.)
2. "For the grid, what shape is the rate gap? Put shocks on axis 0, betas on axis 1, quarters on axis 2: `m[:, None, :] * (1 - betas[None, :, None])`." Loop over the 8 quarters only.
3. "The trough is monotone in the shock, so for each beta you can bisect on the shock." Paste the `breach_frontier` skeleton if needed.

**Follow-ups:**

- "What checks would you run before showing this grid to anyone?" (Conservation with outflows switched off; no negative balances under extreme parameters; monotonicity in shock and beta; a hand-checked first quarter. The reference tests all four.)
- "The trough here is always the last quarter. When wouldn't it be?" (A path where rates reverse, or migration back from R to S; then the min over the path matters, which is why the code takes the min, not the end value.)
- "Which cell is *severe but plausible*?" (Anchor the shock to history (e.g. the 2022–23 cycle's ~5pp in ~16 months) and the pass-through to observed deposit betas in that cycle; corners of a grid are not automatically plausible. Ties to P4 if you want a quantitative distance from history.)
- "Where does this model break?" (Flows linear in the gap; no confidence/run dynamics (digital runs are nonlinear and fast); constant parameters across regimes; no behavioural feedback from the bank's own repricing decision. That last one is the decision variable: the bank *chooses* beta.)
- "How would you calibrate mu, r0 and k?" (Fit to observed outflows by segment across past rate cycles; report parameter uncertainty; check out-of-sample on a different cycle.)

**Common mistakes / red flags:**

- Sequential update (S updated, then migration computed from the new S), which breaks conservation. The conservation check catches it.
- No caps on flows, so balances go negative under large shocks.
- Python double loop over the grid presented as "vectorized" via `np.vectorize` (that's still a Python loop).
- Using `(S+R)[-1]` instead of the min over the path.
- *Red flag:* never sanity-checks anything; or can't explain broadcasting shapes after writing them.

**Strong vs weak:**

- *Strong:* writes `simulate` in ~4 minutes with a simultaneous update, adds the conservation check unprompted, broadcasts over the grid in one go, and frames the frontier as a reverse stress test and a decision ("price deposits at beta ≥ x").
- *Weak:* needs Hint 1 for the update, loops over the grid, treats the output as a picture rather than a decision.

**Rubric:** **4** simulate + vectorized grid + frontier (or a clear bisection plan) with sanity checks unprompted · **3** simulate + grid correct; frontier verbal · **2** simulate correct, grid looped; no checks · **1** simulate wrong after hints.

## P3. Challenger overlay on a frozen champion (core, 11 min)

**Pillar:** **B**, internal challenger models.
**Why this problem:** a common bank situation: a champion deposit-cost model owned by another team, fit in the low-rate era, cannot be re-fit. Build an additive overlay that fixes the high-rate regime and is **exactly zero** where the champion is trusted, choose the penalty on a time-ordered split, and validate out-of-time. It tests challenger design, regularization, and whether the candidate validates like a forecaster (time order) rather than like an ML benchmark (shuffled CV).

**Prompt to paste:**

> `old` has 48 quarters of market rate `m` (0–2%) and the deposit rate paid `dep`. `new` has 28 quarters with `m` rising from 2% to 5.5%. The champion `champion(m, w) = w[0] + w[1]·m` was fit on `old` and is frozen. Deposit betas rise at higher rates, so it under-predicts costs now. Build an overlay `delta(m) = Σ v_k · max(m − knot_k, 0)` with knots 2, 3, 4, 5, fit by ridge on the champion's residuals. Hold out the last 8 quarters; choose λ on a time-ordered split of the rest; report holdout RMSE for champion vs champion + overlay, and the largest change the overlay makes on the old data.

**Starter ([`starters/p3_starter.py`](starters/p3_starter.py)):**

```python
# file: interview-kit-2/starters/p3_starter.py
"""
Challenger overlay on a frozen champion. ~12 minutes.

old: 48 quarters in a low-rate era (market rate m in 0-2%), new: 28 quarters
with m rising 2 -> 5.5%. Column dep = deposit rate paid (%).
The champion, champion(m, w) = w[0] + w[1]*m, was fit on old and is FROZEN
(owned by another team). It under-predicts deposit costs at high rates.

Build an additive overlay delta(m) = sum_k v_k * max(m - knot_k, 0),
knots = KNOTS = [2, 3, 4, 5], fit by ridge on the champion's residuals:
1. hinge_basis(m) -> (n, 4) array; fit_overlay(m, resid, lam) -> v.
2. Hold out the last 8 quarters of `new`. Choose lam from LAMS using a
   time-ordered validation split inside the remaining new data (fit on the
   earlier part, score on the last 4 quarters). Refit with that lam.
3. Report holdout RMSE (champion vs champion + overlay) and the largest
   change the overlay makes on the old-regime data.
"""
import numpy as np
import pandas as pd

KNOTS = np.array([2.0, 3.0, 4.0, 5.0])


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def true_deposit_rate(m):
    m = np.asarray(m, float)
    return 0.05 + 0.25 * m + 0.35 * np.maximum(m - 2.5, 0) + 0.15 * np.maximum(m - 4.0, 0)


def make_data(seed: int = 3):
    """Returns (old, new, champion_w).
    old: 48 quarters, market rate 0-2%; new: 28 quarters, rate climbing 2 -> 5.5%."""
    rng = np.random.default_rng(seed)
    m_old = np.clip(1.0 + np.cumsum(rng.normal(0, 0.15, 48)), 0.0, 2.0)
    m_new = np.linspace(2.0, 5.5, 28) + rng.normal(0, 0.1, 28)
    noise = 0.05
    old = pd.DataFrame({"m": m_old, "dep": true_deposit_rate(m_old) + rng.normal(0, noise, 48)},
                       index=pd.period_range("2010Q1", periods=48, freq="Q"))
    new = pd.DataFrame({"m": m_new, "dep": true_deposit_rate(m_new) + rng.normal(0, noise, 28)},
                       index=pd.period_range("2022Q1", periods=28, freq="Q"))
    X = np.column_stack([np.ones(48), old.m])
    champion_w = np.linalg.lstsq(X, old.dep.to_numpy(), rcond=None)[0]   # frozen
    return old, new, champion_w


def champion(m, w):
    return w[0] + w[1] * np.asarray(m, float)


LAMS = np.logspace(-4, 2, 25)


def hinge_basis(m):
    raise NotImplementedError


def fit_overlay(m, resid, lam):
    raise NotImplementedError


def build_challenger(old, new, w, n_hold: int = 8) -> dict:
    """Return dict with keys lam, v, rmse_champion, rmse_challenger, max_change_old."""
    raise NotImplementedError


def check():
    old, new, w = make_data()
    print("champion w =", np.round(w, 3))
    assert hinge_basis(np.array([1.0, 3.5])).shape == (2, 4)
    rep = build_challenger(old, new, w)
    print({k: (np.round(v, 3) if not isinstance(v, float) else round(v, 4)) for k, v in rep.items()})
    assert rep["rmse_challenger"] < 0.5 * rep["rmse_champion"]
    assert rep["max_change_old"] < 1e-12, "the overlay must leave the old regime unchanged"
    assert rep["lam"] in LAMS
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p3_frozen_champion_overlay.py`](solutions/p3_frozen_champion_overlay.py)):**

```python
# file: interview-kit-2/solutions/p3_frozen_champion_overlay.py
"""
Problem 3 (core, ~12 min): a challenger overlay on a FROZEN champion model.

The champion deposit-cost model was fit in a low-rate era (market rate 0-2%):
    deposit_rate_hat = w0 + w1 * market_rate
It belongs to another team and cannot be re-fit. Rates are now 2-5.5%, and
deposit pass-through ("beta") rises at higher rates, so the champion
under-predicts deposit costs. Build a small additive overlay
    delta(m) = sum_k v_k * max(m - knot_k, 0),   knots = 2, 3, 4, 5
fit by ridge on the champion's residuals over the recent window, so that:
  - it improves the out-of-time holdout (last 8 quarters),
  - it leaves the champion EXACTLY unchanged in the old regime (m <= 2),
  - the ridge penalty is chosen on a time-ordered validation split
    (never shuffled K-fold).
Only numpy required; scikit-learn is used for a cross-check if installed.
"""
import numpy as np
import pandas as pd

KNOTS = np.array([2.0, 3.0, 4.0, 5.0])


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def true_deposit_rate(m):
    m = np.asarray(m, float)
    return 0.05 + 0.25 * m + 0.35 * np.maximum(m - 2.5, 0) + 0.15 * np.maximum(m - 4.0, 0)


def make_data(seed: int = 3):
    """Returns (old, new, champion_w).
    old: 48 quarters, market rate 0-2%; new: 28 quarters, rate climbing 2 -> 5.5%."""
    rng = np.random.default_rng(seed)
    m_old = np.clip(1.0 + np.cumsum(rng.normal(0, 0.15, 48)), 0.0, 2.0)
    m_new = np.linspace(2.0, 5.5, 28) + rng.normal(0, 0.1, 28)
    noise = 0.05
    old = pd.DataFrame({"m": m_old, "dep": true_deposit_rate(m_old) + rng.normal(0, noise, 48)},
                       index=pd.period_range("2010Q1", periods=48, freq="Q"))
    new = pd.DataFrame({"m": m_new, "dep": true_deposit_rate(m_new) + rng.normal(0, noise, 28)},
                       index=pd.period_range("2022Q1", periods=28, freq="Q"))
    X = np.column_stack([np.ones(48), old.m])
    champion_w = np.linalg.lstsq(X, old.dep.to_numpy(), rcond=None)[0]   # frozen
    return old, new, champion_w


def champion(m, w):
    return w[0] + w[1] * np.asarray(m, float)


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def hinge_basis(m, knots=KNOTS):
    return np.maximum(np.asarray(m, float)[:, None] - knots[None, :], 0.0)


def fit_overlay(m, resid, lam):
    """Ridge without intercept: v = (Phi'Phi + lam I)^{-1} Phi' r.
    No intercept on purpose: an intercept would shift the old regime too."""
    Phi = hinge_basis(m)
    return np.linalg.solve(Phi.T @ Phi + lam * np.eye(Phi.shape[1]), Phi.T @ resid)


def overlay(m, v):
    return hinge_basis(m) @ v


def rmse(e):
    return float(np.sqrt(np.mean(np.square(e))))


def choose_lambda(train: pd.DataFrame, w, lams, n_val: int = 4):
    """Time-ordered split: fit on the first part of train, score on the last n_val."""
    fit, val = train.iloc[:-n_val], train.iloc[-n_val:]
    r_fit = fit.dep.to_numpy() - champion(fit.m, w)
    scores = []
    for lam in lams:
        v = fit_overlay(fit.m.to_numpy(), r_fit, lam)
        pred = champion(val.m, w) + overlay(val.m.to_numpy(), v)
        scores.append(rmse(val.dep.to_numpy() - pred))
    return float(lams[int(np.argmin(scores))]), np.array(scores)


def build_challenger(old, new, w, n_hold: int = 8, lams=None):
    lams = np.logspace(-4, 2, 25) if lams is None else lams
    train, hold = new.iloc[:-n_hold], new.iloc[-n_hold:]
    lam, scores = choose_lambda(train, w, lams)
    r = train.dep.to_numpy() - champion(train.m, w)
    v = fit_overlay(train.m.to_numpy(), r, lam)          # refit on all of train
    champ_h = champion(hold.m, w)
    chall_h = champ_h + overlay(hold.m.to_numpy(), v)
    report = dict(lam=lam, v=v,
                  rmse_champion=rmse(hold.dep - champ_h),
                  rmse_challenger=rmse(hold.dep - chall_h),
                  max_change_old=float(np.abs(overlay(old.m.to_numpy(), v)).max()))
    return report


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    old, new, w = make_data()
    # champion is a decent fit in its own era but biased low at high rates
    assert rmse(old.dep - champion(old.m, w)) < 0.08
    assert (new.dep.iloc[-8:] - champion(new.m.iloc[-8:], w)).mean() > 0.5
    rep = build_challenger(old, new, w)
    # 1. the overlay improves the out-of-time holdout a lot
    assert rep["rmse_challenger"] < 0.5 * rep["rmse_champion"], rep
    # 2. it leaves the old regime exactly unchanged (all hinges are zero for m <= 2)
    assert rep["max_change_old"] == 0.0
    # 3. ridge limits: lam -> infinity gives the champion, lam -> 0 gives OLS on residuals
    train = new.iloc[:-8]
    r = train.dep.to_numpy() - champion(train.m, w)
    assert np.abs(fit_overlay(train.m.to_numpy(), r, 1e12)).max() < 1e-9
    Phi = hinge_basis(train.m.to_numpy())
    v_ols = np.linalg.lstsq(Phi, r, rcond=None)[0]
    assert np.allclose(fit_overlay(train.m.to_numpy(), r, 1e-12), v_ols, atol=1e-5)
    # 4. lambda was chosen on a time-ordered split (validation is the latest data)
    lam, scores = choose_lambda(train, w, np.logspace(-4, 2, 25))
    assert np.isclose(lam, rep["lam"]) and np.isfinite(scores).all()
    # 5. scikit-learn cross-check, if installed
    try:
        from sklearn.linear_model import Ridge
        sk = Ridge(alpha=rep["lam"], fit_intercept=False).fit(Phi, r).coef_
        assert np.allclose(sk, rep["v"], atol=1e-8)
        sk_ok = True
    except ImportError:
        sk_ok = False
    print("p3 OK  | lam = %.4g | holdout RMSE champion %.3f -> challenger %.3f | old-regime max change %.1f | sklearn check: %s"
          % (rep["lam"], rep["rmse_champion"], rep["rmse_challenger"], rep["max_change_old"], sk_ok))
    print("overlay coefficients on hinges at", KNOTS.tolist(), ":", np.round(rep["v"], 3).tolist())


if __name__ == "__main__":
    _tests()
```

**Hints (tiered):**

1. "What's the target for the overlay?" (The champion's residual, `dep − champion(m, w)`. The champion itself is never touched.)
2. "Ridge in closed form: $v = (\Phi^\top\Phi + \lambda I)^{-1}\Phi^\top r$. Why no intercept?" (An intercept would shift the old regime too; the hinges are exactly zero for $m \le 2$.)
3. "For λ: fit on the first part of the training window, score on its last 4 quarters, pick the best, then refit on the whole training window. Never shuffle."

**Follow-ups:**

- "Would you sign off on this challenger?" (Out-of-time improvement is large (≈ 0.80 → 0.08 RMSE); the old regime is unchanged by construction. **But:** the knot-5 coefficient is ~0 because training data stop around 4.5%, so the overlay extrapolates linearly above that, and the holdout reaches 5.5%. Strong candidates spot this from the printed coefficients.)
- "Why not K-fold CV for λ?" (Shuffling lets the model see later quarters when predicting earlier ones; with a trending regressor that's look-ahead. `TimeSeriesSplit` or a last-block split instead.)
- "Why ridge and not OLS?" (Few points per hinge, collinear hinges; ridge shrinks toward *zero overlay*, i.e. toward the champion, which is the right prior for a challenger. λ → ∞ recovers the champion exactly; the reference tests both limits.)
- "How do you show the overlay doesn't damage what works?" (Here it's exact: the max change on old-regime inputs is 0.0. More generally: a do-no-harm test on the champion's trusted domain, plus monitoring of the overlay's size over time.)
- "Governance: is the overlay a model?" (Yes: under SR 11-7-style model risk management, an overlay that changes outputs needs documentation, validation and monitoring like any model; a "management adjustment" label doesn't exempt it.)

**Common mistakes / red flags:**

- Re-fitting the champion ("just add the hinge terms to the original regression"), which violates the brief.
- Adding an intercept to the overlay, which shifts old-regime predictions.
- Choosing λ on the holdout (then the holdout is no longer out-of-time).
- Shuffled K-fold.
- *Red flag:* can't connect this to regularization toward a prior, or to the idea of adapting a frozen model when asked.

**Strong vs weak:**

- *Strong:* sees the overlay = residual model immediately, explains the no-intercept choice, writes the time-ordered λ search, and flags the extrapolation above the last knot with data.
- *Weak:* re-fits everything, uses random CV, reports only in-sample fit.

**Rubric:** **4** correct overlay + time-ordered λ + holdout report + extrapolation/governance points unprompted · **3** correct overlay and holdout; λ choice needs a nudge · **2** overlay works after Hints 1–2; λ arbitrary or chosen on the holdout · **1** re-fits the champion or can't get a working overlay.

## P4. How far is a stress scenario from history? Optimal transport (swap-in, 8–10 min)

**Pillars:** **A** scenario design (plausibility of a scenario distribution) and **C** (OT as a linear program).
**Why this problem:** optimal transport gives a principled distance between a scenario generator's joint distribution and history, which is useful for "severe but plausible." It checks numpy fluency (sorting, broadcasting) and whether the candidate can express OT as an LP in scipy. Because some candidates know OT from research, don't use it to rescue a weak core performance.

**Prompt to paste:**

> `hist` and `stress` are 400 draws each of joint quarterly changes (ΔUR, ΔY10) from history and from a stress-scenario generator. (1) `wasserstein_1d(x, y, p)` for equal-size samples. (2) `ot_lp(a, b, C)`: discrete OT between two histograms with cost matrix C, as an LP with `scipy.optimize.linprog`; check it against the 1-D answer. (3) `sliced_wasserstein(X, Y, n_proj)`: sliced W2 in 2-D, vectorized.

**Starter ([`starters/p4_starter.py`](starters/p4_starter.py)):**

```python
# file: interview-kit-2/starters/p4_starter.py
"""
How far is a stress scenario from history? Optimal transport. ~10 minutes.

hist, stress: (400, 2) arrays of quarterly (dUR, dY10) changes in pp.
1. wasserstein_1d(x, y, p=1): W_p between two equal-size 1-D samples.
2. ot_lp(a, b, C) -> (cost, plan): discrete OT between histograms a (n,)
   and b (m,) with cost matrix C (n, m), as a linear program with
   scipy.optimize.linprog. Check it against the 1-D answer.
3. sliced_wasserstein(X, Y, n_proj=500, seed=0): sliced W2 between 2-D
   samples, vectorized (no loop over projections).
"""
import numpy as np

try:
    from scipy.optimize import linprog
except ImportError:
    linprog = None


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def make_samples(n: int = 400, seed: int = 11):
    """Historical vs scenario-generator draws of (dUR pp, dY10 pp) per quarter."""
    rng = np.random.default_rng(seed)
    cov_h = np.array([[0.09, -0.03], [-0.03, 0.16]])
    hist = rng.multivariate_normal([0.0, 0.0], cov_h, size=n)
    # stress generator: UR drifts up, yields fall, fatter UR tail
    cov_s = np.array([[0.25, -0.08], [-0.08, 0.20]])
    stress = rng.multivariate_normal([0.6, -0.4], cov_s, size=n)
    return hist, stress



def wasserstein_1d(x, y, p: int = 1):
    raise NotImplementedError


def ot_lp(a, b, C):
    raise NotImplementedError


def sliced_wasserstein(X, Y, n_proj: int = 500, seed: int = 0):
    raise NotImplementedError


def check():
    hist, stress = make_samples()
    x = hist[:, 0]
    assert np.isclose(wasserstein_1d(x, x + 0.7), 0.7)
    print("W1 dUR hist vs stress:", round(wasserstein_1d(x, stress[:, 0]), 3))
    try:
        import scipy  # noqa: F401
        grid = np.array([0.0, 1.0, 2.0])
        cost, P = ot_lp(np.array([0.5, 0.5, 0.0]), np.array([0.0, 0.5, 0.5]),
                        np.abs(grid[:, None] - grid[None, :]))
        assert np.isclose(cost, 1.0) and np.allclose(P.sum(1), [0.5, 0.5, 0.0])
    except ImportError:
        print("scipy missing: skip the LP part")
    assert sliced_wasserstein(hist, hist) == 0.0
    sw = sliced_wasserstein(hist, hist + np.array([0.6, -0.4]), n_proj=4000)
    assert abs(sw ** 2 - 0.52 / 2) < 0.01, sw
    print("SW2 hist vs stress:", round(sliced_wasserstein(hist, stress), 3))
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p4_scenario_distance_ot.py`](solutions/p4_scenario_distance_ot.py)):**

```python
# file: interview-kit-2/solutions/p4_scenario_distance_ot.py
"""
Problem 4 (swap-in, ~10 min): how far is a stress scenario from history?
Optimal transport three ways.

  1. wasserstein_1d(x, y): W_p between two equal-size 1-D samples (sorted
     samples = quantile coupling).
  2. ot_lp(a, b, C): discrete OT between histograms a, b with cost matrix C,
     solved as a linear program with scipy.optimize.linprog. Return the cost
     and the transport plan; check it against the 1-D closed form.
  3. sliced_wasserstein(X, Y, n_proj): vectorized sliced W2 between 2-D
     samples (e.g. joint quarterly changes in unemployment and the 10y yield).
Application: compare the joint (dUR, dY10) distribution implied by a
scenario generator with the historical one.
numpy required; scipy needed only for part 2 (skipped otherwise).
"""
import numpy as np

try:
    from scipy.optimize import linprog
except ImportError:
    linprog = None


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def make_samples(n: int = 400, seed: int = 11):
    """Historical vs scenario-generator draws of (dUR pp, dY10 pp) per quarter."""
    rng = np.random.default_rng(seed)
    cov_h = np.array([[0.09, -0.03], [-0.03, 0.16]])
    hist = rng.multivariate_normal([0.0, 0.0], cov_h, size=n)
    # stress generator: UR drifts up, yields fall, fatter UR tail
    cov_s = np.array([[0.25, -0.08], [-0.08, 0.20]])
    stress = rng.multivariate_normal([0.6, -0.4], cov_s, size=n)
    return hist, stress


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def wasserstein_1d(x, y, p: int = 1):
    x, y = np.sort(np.asarray(x, float)), np.sort(np.asarray(y, float))
    assert len(x) == len(y), "equal sizes for the sorted-sample formula"
    return float(np.mean(np.abs(x - y) ** p) ** (1 / p))


def wasserstein_1d_hist(a, b, grid):
    """W1 between histograms on a common sorted grid: integral of |F_a - F_b|."""
    Fa, Fb = np.cumsum(a), np.cumsum(b)
    return float(np.sum(np.abs(Fa - Fb)[:-1] * np.diff(grid)))


def ot_lp(a, b, C):
    """min <C, P>  s.t.  P 1 = a,  P' 1 = b,  P >= 0.   Variables: vec(P) row-major."""
    n, m = C.shape
    A_eq = np.zeros((n + m, n * m))
    for i in range(n):
        A_eq[i, i * m:(i + 1) * m] = 1.0          # row sums
    for j in range(m):
        A_eq[n + j, j::m] = 1.0                   # column sums
    res = linprog(C.ravel(), A_eq=A_eq, b_eq=np.r_[a, b], bounds=(0, None), method="highs")
    assert res.status == 0, res.message
    return float(res.fun), res.x.reshape(n, m)


def sliced_wasserstein(X, Y, n_proj: int = 500, seed: int = 0):
    """SW2: average over random unit directions of W2^2 of the 1-D projections."""
    rng = np.random.default_rng(seed)
    theta = rng.standard_normal((n_proj, X.shape[1]))
    theta /= np.linalg.norm(theta, axis=1, keepdims=True)
    px = np.sort(X @ theta.T, axis=0)             # (n, n_proj), sorted per direction
    py = np.sort(Y @ theta.T, axis=0)
    return float(np.sqrt(np.mean((px - py) ** 2)))


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    hist, stress = make_samples()
    # 1. 1-D: W is a metric-like quantity; a pure shift moves W1 by exactly the shift
    x = hist[:, 0]
    assert wasserstein_1d(x, x) == 0.0
    assert np.isclose(wasserstein_1d(x, x + 0.7), 0.7)
    assert np.isclose(wasserstein_1d(x, stress[:, 0]), wasserstein_1d(stress[:, 0], x))
    # 2. LP agrees with the 1-D CDF formula on a histogram grid
    lp_ok = linprog is not None
    if lp_ok:
        grid = np.linspace(-2, 3, 26)
        bins = np.r_[grid - 0.1, grid[-1] + 0.1]
        a = np.histogram(np.clip(hist[:, 0], -2, 3), bins=bins)[0].astype(float); a /= a.sum()
        b = np.histogram(np.clip(stress[:, 0], -2, 3), bins=bins)[0].astype(float); b /= b.sum()
        C = np.abs(grid[:, None] - grid[None, :])
        cost, P = ot_lp(a, b, C)
        assert np.allclose(P.sum(1), a, atol=1e-9) and np.allclose(P.sum(0), b, atol=1e-9)
        assert np.isclose(cost, wasserstein_1d_hist(a, b, grid), atol=1e-8)
    # 3. sliced W2: zero on identical samples; a shift a gives SW2^2 ~ |a|^2 / d
    assert sliced_wasserstein(hist, hist) == 0.0
    shift = np.array([0.6, -0.4])
    sw_shift = sliced_wasserstein(hist, hist + shift, n_proj=4000)
    assert abs(sw_shift ** 2 - shift @ shift / 2) < 0.01, sw_shift
    sw_stress = sliced_wasserstein(hist, stress)
    sw_null = sliced_wasserstein(hist[:200], hist[200:])       # sampling noise level
    assert sw_stress > 4 * sw_null
    print("p4 OK  | W1(dUR hist, stress) = %.3f | LP check: %s | SW2 stress %.3f vs noise %.3f"
          % (wasserstein_1d(x, stress[:, 0]), lp_ok, sw_stress, sw_null))


if __name__ == "__main__":
    _tests()
```

**Hints (tiered):**

1. "In 1-D the optimal coupling is monotone: match sorted samples." `np.mean(np.abs(np.sort(x) - np.sort(y))**p)**(1/p)`.
2. "LP variables are the n·m entries of the plan; constraints are row sums = a and column sums = b; cost is ⟨C, P⟩." Build `A_eq` with one row per marginal constraint.
3. "Sliced: project both clouds on many random unit vectors at once (`X @ theta.T`), sort each column, average squared differences."

**Follow-ups:**

- "Why does a shift by vector a give $SW_2^2 \approx |a|^2/d$?" (Projected shift is $\theta^\top a$; $E[(\theta^\top a)^2] = |a|^2/d$ for uniform θ on the sphere. The reference tests it.)
- "Is W the right distance for 'severe but plausible'?" (W measures how much mass must move and how far, so it's good for "how unusual is this scenario overall"; but it averages, so a scenario can be close in W yet extreme in one tail. Pair it with tail quantiles or a likelihood under a historical model.)
- "What's the LP's dual?" (Kantorovich potentials $f, g$ with $f_i + g_j \le C_{ij}$; for $C = |x - y|$ it becomes the 1-Lipschitz dual. `res.eqlin.marginals` gives them, up to a constant.)
- "Size limits?" (n·m variables; for large n use the 1-D formula, sliced W, or entropic OT (Sinkhorn).)
- 

**Common mistakes / red flags:** unequal-size samples fed to the sorted formula; a Python loop over projections; forgetting to normalize θ; LP with only row constraints. *Red flag:* can explain OT beautifully but can't produce the sliced-W code in a few minutes.

**Strong vs weak:** *Strong:* 1-D and sliced in ~4 minutes, LP built correctly with a marginal check, and a sensible caveat about what W does and doesn't say about tails. *Weak:* only the theory.

**Rubric:** **4** all three parts plus the shift identity or the dual · **3** 1-D + sliced correct; LP with a nudge · **2** 1-D only; sliced looped · **1** can't code the 1-D case.

## P5. Planning allocation: LP, duals, then MILP (swap-in, 10–12 min)

**Pillar:** **C**, optimization models that change decisions.
**Why this problem:** allocation of a planning budget is the canonical decision model: a budget, a regulatory floor, duals as decision information, then fixed costs, minimum scale and a cardinality limit that need binaries.

**Prompt to paste:**

> Eight initiatives. `x_i` units of budget go to initiative i, worth `v_i` per unit, capped at `u_i`. Budget B = 30; the two regulatory initiatives must together get at least 8. (1) Solve the LP with `linprog`; what's the shadow price of the budget? Check it by re-solving with B + 1. (2) Now each funded initiative has a set-up cost `f_i` and a minimum scale `m_i`, and at most K = 4 can be funded. Formulate and solve the MILP with `scipy.optimize.milp`. (3) Why does "fund the highest value per unit first" fail?

**Starter ([`starters/p5_starter.py`](starters/p5_starter.py)):**

```python
# file: interview-kit-2/starters/p5_starter.py
"""
Planning allocation: LP, duals, then MILP. ~12 minutes.

P (from make_problem): v value per unit, u caps, m minimum scale if funded,
f fixed set-up cost, reg (bool) regulatory flags, B budget, R_min regulatory
floor, K max number of funded initiatives.
1. solve_lp(P, B=None, R_min=None) -> (x, objective):
       max v'x  s.t. sum x <= B, sum_{reg} x >= R_min, 0 <= x <= u
   with scipy.optimize.linprog. What is the shadow price of the budget?
   Confirm with a finite difference.
2. solve_milp(P) -> (x, z, objective): add binaries z with
   m_i z_i <= x_i <= u_i z_i, sum z <= K, keep the floor, objective v'x - f'z.
3. Why does "fund the highest value per unit first" fail here?
"""
import itertools
import numpy as np

try:
    from scipy.optimize import linprog
except ImportError:
    linprog = None
try:
    from scipy.optimize import milp, LinearConstraint, Bounds
except ImportError:
    milp = None


# ----------------------------------------------------------------------------
# Synthetic problem
# ----------------------------------------------------------------------------
def make_problem(seed: int = 5):
    rng = np.random.default_rng(seed)
    n = 8
    v = np.round(rng.uniform(1.0, 3.0, n), 2)        # value per unit
    u = np.round(rng.uniform(4.0, 12.0, n), 1)       # caps
    m = np.round(u * rng.uniform(0.4, 0.7, n), 1)    # minimum scale if funded
    f = np.round(rng.uniform(2.0, 8.0, n), 1)        # fixed set-up cost (value units)
    reg = np.zeros(n, bool); reg[np.argsort(v)[:2]] = True   # regulatory = two lowest-value
    return dict(v=v, u=u, m=m, f=f, reg=reg, B=30.0, R_min=8.0, K=4)



def solve_lp(P, B=None, R_min=None):
    raise NotImplementedError


def solve_milp(P):
    raise NotImplementedError


def check():
    P = make_problem()
    print({k: v for k, v in P.items()})
    try:
        from scipy.optimize import linprog  # noqa: F401
    except ImportError:
        print("scipy missing: discuss the LP/MILP verbally or solve by hand"); print("checks passed"); return
    x, obj = solve_lp(P)[:2]
    assert x.sum() <= P["B"] + 1e-9 and x[P["reg"]].sum() >= P["R_min"] - 1e-9
    _, obj_up = solve_lp(P, B=P["B"] + 1)[:2]
    print("LP objective %.2f, budget shadow price ~ %.2f" % (obj, obj_up - obj))
    assert obj_up >= obj
    try:
        from scipy.optimize import milp  # noqa: F401
    except ImportError:
        print("milp needs scipy >= 1.9: discuss part 2 verbally"); print("checks passed"); return
    x, z, val = solve_milp(P)
    assert z.sum() <= P["K"] and x.sum() <= P["B"] + 1e-9
    assert np.all((x <= 1e-9) | (x >= P["m"] - 1e-9)), "minimum scale violated"
    assert np.isclose(val, 47.11, atol=0.01), val
    print("MILP objective %.2f, funded %s" % (val, np.round(z).astype(int).tolist()))
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p5_planning_allocation_milp.py`](solutions/p5_planning_allocation_milp.py)):**

```python
# file: interview-kit-2/solutions/p5_planning_allocation_milp.py
"""
Problem 5 (swap-in, ~12 min): allocate a planning budget across initiatives
(an optimization model that changes a decision).

n initiatives; x_i = units of budget (e.g. $m or FTE) given to initiative i.
value per unit v_i, cap u_i. Budget B. Some initiatives are regulatory and
must together receive at least R_min units.
  1. LP: max v'x  s.t. sum x <= B, sum_{reg} x >= R_min, 0 <= x <= u.
     Solve with linprog; report the shadow price of the budget and check it
     with a finite difference (re-solve with B + 1).
  2. MILP: each initiative also has a fixed set-up cost f_i and a minimum
     scale m_i if funded (x_i = 0 or m_i <= x_i <= u_i), and at most K can be
     funded; the regulatory floor still applies. max v'x - f'z. Solve with scipy.optimize.milp and verify by
     brute force over all 2^n funding sets.
  3. Show that greedy-by-value fails on the MILP.
numpy required; scipy >= 1.9 for milp (the brute-force solver works without it).
"""
import itertools
import numpy as np

try:
    from scipy.optimize import linprog
except ImportError:
    linprog = None
try:
    from scipy.optimize import milp, LinearConstraint, Bounds
except ImportError:
    milp = None


# ----------------------------------------------------------------------------
# Synthetic problem
# ----------------------------------------------------------------------------
def make_problem(seed: int = 5):
    rng = np.random.default_rng(seed)
    n = 8
    v = np.round(rng.uniform(1.0, 3.0, n), 2)        # value per unit
    u = np.round(rng.uniform(4.0, 12.0, n), 1)       # caps
    m = np.round(u * rng.uniform(0.4, 0.7, n), 1)    # minimum scale if funded
    f = np.round(rng.uniform(2.0, 8.0, n), 1)        # fixed set-up cost (value units)
    reg = np.zeros(n, bool); reg[np.argsort(v)[:2]] = True   # regulatory = two lowest-value
    return dict(v=v, u=u, m=m, f=f, reg=reg, B=30.0, R_min=8.0, K=4)


# ----------------------------------------------------------------------------
# Reference solution 1: LP and its duals
# ----------------------------------------------------------------------------
def solve_lp(P, B=None, R_min=None):
    B = P["B"] if B is None else B
    R_min = P["R_min"] if R_min is None else R_min
    n = len(P["v"])
    A_ub = np.vstack([np.ones(n), -P["reg"].astype(float)])
    b_ub = np.array([B, -R_min])
    res = linprog(-P["v"], A_ub=A_ub, b_ub=b_ub, bounds=list(zip(np.zeros(n), P["u"])), method="highs")
    assert res.status == 0, res.message
    duals = -res.ineqlin.marginals if hasattr(res, "ineqlin") else None   # scipy >= 1.7
    return res.x, -res.fun, duals


# ----------------------------------------------------------------------------
# Reference solution 2: MILP and a brute-force verifier
# ----------------------------------------------------------------------------
def solve_milp(P):
    v, u, m, f, K, B = P["v"], P["u"], P["m"], P["f"], P["K"], P["B"]
    n = len(v)
    c = -np.r_[v, -f]                         # variables [x (n), z (n)]; minimize -(v'x - f'z)
    I = np.eye(n)
    cons = [LinearConstraint(np.r_[np.ones(n), np.zeros(n)][None, :], -np.inf, B),
            LinearConstraint(np.hstack([I, -np.diag(u)]), -np.inf, 0.0),     # x <= u z
            LinearConstraint(np.hstack([I, -np.diag(m)]), 0.0, np.inf),      # x >= m z
            LinearConstraint(np.r_[np.zeros(n), np.ones(n)][None, :], -np.inf, K),
            LinearConstraint(np.r_[P["reg"].astype(float), np.zeros(n)][None, :], P["R_min"], np.inf)]
    integrality = np.r_[np.zeros(n), np.ones(n)]
    res = milp(c, constraints=cons, integrality=integrality,
               bounds=Bounds(np.zeros(2 * n), np.r_[u, np.ones(n)]))
    assert res.status == 0, res.message
    x, z = res.x[:n], np.round(res.x[n:]).astype(int)
    return x, z, -res.fun


def best_given_z(P, z):
    """With the funding set fixed, the problem is a bounded fractional knapsack
    with unit costs: give every funded initiative its minimum, top up the
    regulatory floor with the best regulatory lines, then fill by value."""
    v, u, m, reg = P["v"], P["u"], P["m"], P["reg"]
    x = np.where(z, m, 0.0)
    left = P["B"] - x.sum()
    if left < -1e-12:
        return None, -np.inf
    need = P["R_min"] - x[reg].sum()
    for i in np.argsort(-v):
        if z[i] and reg[i] and need > 0:
            add = min(u[i] - x[i], left, need); x[i] += add; left -= add; need -= add
    if need > 1e-9:
        return None, -np.inf                      # floor cannot be met with this z
    for i in np.argsort(-v):
        if z[i]:
            add = min(u[i] - x[i], left); x[i] += add; left -= add
    return x, float(v @ x - P["f"] @ z)


def brute_force(P):
    n = len(P["v"]); best = (None, None, -np.inf)
    for bits in itertools.product([0, 1], repeat=n):
        z = np.array(bits)
        if z.sum() > P["K"]:
            continue
        x, val = best_given_z(P, z)
        if val > best[2]:
            best = (x, z, val)
    return best


def greedy(P):
    """Fund the best regulatory line (to meet the floor), then initiatives in
    order of value per unit until K or the budget runs out."""
    z = np.zeros(len(P["v"]), int); spent = 0.0
    order = list(np.argsort(-P["v"]))
    regs, cap = [], 0.0
    for i in order:                                  # enough regulatory lines for the floor
        if P["reg"][i] and cap < P["R_min"]:
            regs.append(i); cap += P["u"][i]
    order = regs + [i for i in order if i not in regs]
    for i in order:
        if z.sum() < P["K"] and spent + P["m"][i] <= P["B"]:
            z[i] = 1; spent += P["m"][i]
    return best_given_z(P, z)


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    P = make_problem()
    msg = []
    if linprog is not None:
        x, obj, duals = solve_lp(P)
        assert x.sum() <= P["B"] + 1e-9 and x[P["reg"]].sum() >= P["R_min"] - 1e-9
        assert (x >= -1e-9).all() and (x <= P["u"] + 1e-9).all()
        _, obj_up, _ = solve_lp(P, B=P["B"] + 1.0)
        _, obj_reg, _ = solve_lp(P, R_min=P["R_min"] + 1.0)
        assert obj_reg < obj                       # the floor binds: it costs value
        if duals is not None:
            # duals of the <= rows; the floor is written as -sum_reg x <= -R_min,
            # so raising R_min by 1 changes the objective by -duals[1]
            assert np.isclose(duals[0], obj_up - obj, atol=1e-8), (duals, obj_up - obj)
            assert np.isclose(-duals[1], obj_reg - obj, atol=1e-8), (duals, obj_reg - obj)
        msg.append("LP obj %.2f, budget shadow price %.2f/unit, cost of +1 unit of reg floor %.2f"
                   % (obj, obj_up - obj, obj - obj_reg))
    xb, zb, vb = brute_force(P)
    xg, vg = greedy(P)
    assert vg < vb - 1e-9, "greedy should be suboptimal on this instance"
    if milp is not None:
        x, z, val = solve_milp(P)
        assert np.isclose(val, vb, atol=1e-6), (val, vb)
        assert z.sum() <= P["K"] and x.sum() <= P["B"] + 1e-9
        assert np.all((x <= 1e-9) | ((x >= P["m"] - 1e-9) & (x <= P["u"] + 1e-9)))
        if linprog is not None:
            assert val <= obj + 1e-9      # the LP is a relaxation (no fixed costs, no minimums)
        msg.append("MILP %.2f == brute force %.2f, funded %s" % (val, vb, z.tolist()))
    else:
        msg.append("milp unavailable; brute force %.2f, funded %s" % (vb, zb.tolist()))
    msg.append("greedy %.2f (gap %.2f)" % (vg, vb - vg))
    print("p5 OK  | " + " | ".join(msg))


if __name__ == "__main__":
    _tests()
```

**Hints (tiered):**

1. "`linprog` minimizes, so negate v. The floor `Σ_reg x ≥ R` becomes `−Σ_reg x ≤ −R` in `A_ub`."
2. "Binary z_i links to x_i with two inequalities: `x_i ≤ u_i z_i` and `x_i ≥ m_i z_i`." Stack variables as `[x, z]`, `integrality = [0]*n + [1]*n`.
3. "To verify: with z fixed, what's left is a fractional knapsack with unit costs, so greedy is exact. Enumerate the 256 z's."

**Follow-ups:**

- "Interpret the duals for the CFO." (Budget: ≈ 2.03 of value per extra unit; regulatory floor: each extra required unit costs ≈ 0.94. That's the price of the regulation in planning terms.)
- "LP 63.2 vs MILP 47.1. Where does the gap come from?" (Set-up costs and minimum scale; the LP is a relaxation and an upper bound.)
- "Greedy got 35.4. Why?" (It funds by value per unit, ignores set-up costs and the lumpy minimums; classic knapsack failure.)
- "This would be a 200-initiative, multi-year model in real life. What changes?" (Multi-period budgets and carry-over, uncertainty in v (scenario-based or robust), solver choice (HiGHS is fine to thousands of binaries; Gurobi/OR-Tools beyond), and explaining the answer to business users.)

**Common mistakes / red flags:** forgetting the negation (minimizing value); sign errors on duals; big-M constants instead of the natural `u_i`; no check that the solution respects the minimum scale. *Red flag:* can't formulate a binary on/off constraint at all.

**Strong vs weak:** *Strong:* LP + dual + finite-difference check in ~5 minutes, clean MILP formulation, and a verification strategy (brute force or bounds). *Weak:* only the LP, can't read the duals.

**Rubric:** **4** LP + duals interpreted + MILP correct + verification idea · **3** LP + duals; MILP formulated with a nudge · **2** LP only · **1** can't set up the LP.

## P6. SQL on messy general-ledger actuals (swap-in, 8–10 min)

**Pillars:** **B** and **D** (the internal data that feeds internal challengers and finance apps).
**Why this problem:** internal FP&A data has exactly these traps: re-posted journal entries, cost-centre re-orgs, YTD logic and missing months. This is a short check of SQL window functions and data instincts.

**Prompt to paste:**

> Three tables in SQLite: `gl` (cost_center, month, amount, posted_at) with some months re-posted; `cc_map` (CC31 merged into CC30); `budget` on the new hierarchy. Write one query (CTEs fine) giving, per new cost centre and month: actual (latest posting wins, old centres mapped, then summed), budget, variance, YTD actual (restarts in January) and month-over-month change (NULL if the previous calendar month is missing).

**Starter ([`starters/p6_starter.py`](starters/p6_starter.py)):**

```python
# file: interview-kit-2/starters/p6_starter.py
"""
SQL on messy general-ledger actuals. ~10 minutes.

Tables in an in-memory SQLite db (con):
  gl(cost_center, month 'YYYY-MM', amount, posted_at)  -- some months re-posted
  cc_map(old_cc, new_cc, effective_month)              -- CC31 merged into CC30
  budget(cost_center, month, amount)                   -- on the new hierarchy
Write SQL returning one row per (cc, month) with columns
  cc, month, actual, budget, variance, ytd_actual, mom
  - the latest posting per (cost_center, month) wins
  - old centres are mapped to their new centre, then summed
  - ytd_actual restarts every January
  - mom = actual - previous month's actual, NULL if the previous calendar
    month is missing
"""
import sqlite3
import numpy as np
import pandas as pd


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def make_tables(seed: int = 2):
    rng = np.random.default_rng(seed)
    months = pd.period_range("2025-01", "2026-06", freq="M")
    ccs = ["CC10", "CC20", "CC30", "CC31"]           # CC31 merges into CC30 from 2025-07
    rows = []
    for cc in ccs:
        base = {"CC10": 100.0, "CC20": 60.0, "CC30": 40.0, "CC31": 20.0}[cc]
        for i, mth in enumerate(months):
            if cc == "CC31" and mth >= pd.Period("2025-07", "M"):
                continue                                 # after the re-org it posts as CC30
            amt = base * (1 + 0.01 * i) + rng.normal(0, 1.0)
            if cc == "CC30" and mth >= pd.Period("2025-07", "M"):
                amt += 20.0 * (1 + 0.01 * i)             # absorbed CC31's spend
            rows.append(dict(cost_center=cc, month=str(mth), amount=round(amt, 2),
                             posted_at=str((mth + 1).start_time.date() + pd.Timedelta(days=3))))
    gl = pd.DataFrame(rows)
    # re-posts: a wrong first posting, corrected 10 days later
    fix = gl[(gl.cost_center == "CC10") & (gl.month == "2025-03")].copy()
    wrong = fix.copy(); wrong["amount"] = wrong["amount"] * 3
    fix["posted_at"] = str(pd.Timestamp(fix["posted_at"].iloc[0]).date() + pd.Timedelta(days=10))
    gl = gl[~((gl.cost_center == "CC10") & (gl.month == "2025-03"))]
    gl = pd.concat([gl, wrong, fix], ignore_index=True)
    # a missing month: CC20 did not post 2026-02
    gl = gl[~((gl.cost_center == "CC20") & (gl.month == "2026-02"))].reset_index(drop=True)
    cc_map = pd.DataFrame({"old_cc": ["CC31"], "new_cc": ["CC30"], "effective_month": ["2025-07"]})
    bud = []
    for cc, base in {"CC10": 100.0, "CC20": 60.0, "CC30": 60.0}.items():
        for i, mth in enumerate(months):
            bud.append(dict(cost_center=cc, month=str(mth), amount=round(base * (1 + 0.012 * i), 2)))
    budget = pd.DataFrame(bud)
    return gl, cc_map, budget


def load(gl, cc_map, budget):
    con = sqlite3.connect(":memory:")
    gl.to_sql("gl", con, index=False)
    cc_map.to_sql("cc_map", con, index=False)
    budget.to_sql("budget", con, index=False)
    return con


SQL = """
SELECT 1
"""


def check():
    gl, cc_map, budget = make_tables()
    con = load(gl, cc_map, budget)
    print(pd.read_sql_query("SELECT * FROM gl ORDER BY cost_center, month LIMIT 5", con))
    out = pd.read_sql_query(SQL, con)
    print(out.head(8))
    assert list(out.columns) == ["cc", "month", "actual", "budget", "variance", "ytd_actual", "mom"]
    assert set(out.cc) == {"CC10", "CC20", "CC30"} and len(out) == 53
    assert out[(out.cc == "CC10") & (out.month == "2025-03")].actual.iloc[0] < 120, "re-post not resolved"
    assert pd.isna(out[(out.cc == "CC20") & (out.month == "2026-03")].mom.iloc[0]), "mom bridged a gap"
    jan = out[(out.cc == "CC10") & (out.month == "2026-01")].iloc[0]
    assert np.isclose(jan.ytd_actual, jan.actual), "YTD should restart in January"
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p6_gl_sql_pipeline.py`](solutions/p6_gl_sql_pipeline.py)):**

```python
# file: interview-kit-2/solutions/p6_gl_sql_pipeline.py
"""
Problem 6 (swap-in, ~10 min): SQL on messy general-ledger (GL) actuals.

Tables (SQLite in memory, built from pandas):
  gl(cost_center, month TEXT 'YYYY-MM', amount, posted_at)   -- re-posts happen
  cc_map(old_cc, new_cc, effective_month)                     -- a re-org
  budget(cost_center, month, amount)                          -- on the NEW hierarchy
Write ONE query (CTEs are fine) that returns, per (new cost center, month):
  actual       latest posting per (cost_center, month) wins, old centres
               mapped to their new centre, then summed
  budget, variance = actual - budget
  ytd_actual   running sum within the calendar year
  mom          month-over-month change in actual, NULL if the previous
               calendar month is missing (LAG counts rows, not months)
Then check the result against a pandas implementation.
Standard library sqlite3 (window functions need SQLite >= 3.25) + pandas.
"""
import sqlite3
import numpy as np
import pandas as pd


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def make_tables(seed: int = 2):
    rng = np.random.default_rng(seed)
    months = pd.period_range("2025-01", "2026-06", freq="M")
    ccs = ["CC10", "CC20", "CC30", "CC31"]           # CC31 merges into CC30 from 2025-07
    rows = []
    for cc in ccs:
        base = {"CC10": 100.0, "CC20": 60.0, "CC30": 40.0, "CC31": 20.0}[cc]
        for i, mth in enumerate(months):
            if cc == "CC31" and mth >= pd.Period("2025-07", "M"):
                continue                                 # after the re-org it posts as CC30
            amt = base * (1 + 0.01 * i) + rng.normal(0, 1.0)
            if cc == "CC30" and mth >= pd.Period("2025-07", "M"):
                amt += 20.0 * (1 + 0.01 * i)             # absorbed CC31's spend
            rows.append(dict(cost_center=cc, month=str(mth), amount=round(amt, 2),
                             posted_at=str((mth + 1).start_time.date() + pd.Timedelta(days=3))))
    gl = pd.DataFrame(rows)
    # re-posts: a wrong first posting, corrected 10 days later
    fix = gl[(gl.cost_center == "CC10") & (gl.month == "2025-03")].copy()
    wrong = fix.copy(); wrong["amount"] = wrong["amount"] * 3
    fix["posted_at"] = str(pd.Timestamp(fix["posted_at"].iloc[0]).date() + pd.Timedelta(days=10))
    gl = gl[~((gl.cost_center == "CC10") & (gl.month == "2025-03"))]
    gl = pd.concat([gl, wrong, fix], ignore_index=True)
    # a missing month: CC20 did not post 2026-02
    gl = gl[~((gl.cost_center == "CC20") & (gl.month == "2026-02"))].reset_index(drop=True)
    cc_map = pd.DataFrame({"old_cc": ["CC31"], "new_cc": ["CC30"], "effective_month": ["2025-07"]})
    bud = []
    for cc, base in {"CC10": 100.0, "CC20": 60.0, "CC30": 60.0}.items():
        for i, mth in enumerate(months):
            bud.append(dict(cost_center=cc, month=str(mth), amount=round(base * (1 + 0.012 * i), 2)))
    budget = pd.DataFrame(bud)
    return gl, cc_map, budget


def load(gl, cc_map, budget):
    con = sqlite3.connect(":memory:")
    gl.to_sql("gl", con, index=False)
    cc_map.to_sql("cc_map", con, index=False)
    budget.to_sql("budget", con, index=False)
    return con


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
SQL = """
WITH latest AS (
    SELECT cost_center, month, amount,
           ROW_NUMBER() OVER (PARTITION BY cost_center, month ORDER BY posted_at DESC) AS rn
    FROM gl
),
mapped AS (
    SELECT COALESCE(m.new_cc, l.cost_center) AS cc, l.month, l.amount
    FROM latest l LEFT JOIN cc_map m ON l.cost_center = m.old_cc
    WHERE l.rn = 1
),
actuals AS (
    SELECT cc, month, SUM(amount) AS actual,
           CAST(substr(month, 1, 4) AS INTEGER) AS yr,
           CAST(substr(month, 1, 4) AS INTEGER) * 12 + CAST(substr(month, 6, 2) AS INTEGER) AS m_idx
    FROM mapped GROUP BY cc, month
),
w AS (
    SELECT a.*, b.amount AS budget,
           LAG(actual) OVER (PARTITION BY cc ORDER BY m_idx) AS prev_actual,
           LAG(m_idx)  OVER (PARTITION BY cc ORDER BY m_idx) AS prev_idx,
           SUM(actual) OVER (PARTITION BY cc, yr ORDER BY m_idx
                             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ytd_actual
    FROM actuals a LEFT JOIN budget b ON b.cost_center = a.cc AND b.month = a.month
)
SELECT cc, month, actual, budget, actual - budget AS variance, ytd_actual,
       CASE WHEN prev_idx = m_idx - 1 THEN actual - prev_actual END AS mom
FROM w ORDER BY cc, month
"""


def pandas_reference(gl, cc_map, budget):
    g = gl.sort_values("posted_at").drop_duplicates(["cost_center", "month"], keep="last")
    g = g.assign(cc=g.cost_center.map(dict(zip(cc_map.old_cc, cc_map.new_cc))).fillna(g.cost_center))
    a = g.groupby(["cc", "month"], as_index=False)["amount"].sum().rename(columns={"amount": "actual"})
    a = a.merge(budget.rename(columns={"cost_center": "cc", "amount": "budget"}), on=["cc", "month"], how="left")
    a["variance"] = a.actual - a.budget
    p = pd.PeriodIndex(a.month, freq="M")
    a["yr"], a["m_idx"] = p.year, p.year * 12 + p.month
    a = a.sort_values(["cc", "m_idx"]).reset_index(drop=True)
    a["ytd_actual"] = a.groupby(["cc", "yr"])["actual"].cumsum()
    prev = a.groupby("cc")["actual"].shift(1)
    prev_idx = a.groupby("cc")["m_idx"].shift(1)
    a["mom"] = np.where(prev_idx == a.m_idx - 1, a.actual - prev, np.nan)
    return a[["cc", "month", "actual", "budget", "variance", "ytd_actual", "mom"]]


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    gl, cc_map, budget = make_tables()
    con = load(gl, cc_map, budget)
    out = pd.read_sql_query(SQL, con)
    ref = pandas_reference(gl, cc_map, budget)
    assert set(out.cc) == {"CC10", "CC20", "CC30"}, "CC31 must be mapped into CC30"
    assert len(out) == len(ref) == 18 * 3 - 1
    for col in ["actual", "budget", "variance", "ytd_actual", "mom"]:
        assert np.allclose(out[col].to_numpy(float), ref[col].to_numpy(float), equal_nan=True), col
    # re-post resolved: no 3x spike in CC10 2025-03
    v = out[(out.cc == "CC10") & (out.month == "2025-03")].actual.iloc[0]
    assert v < 120, v
    # gap: the month after CC20's missing month has NULL mom
    assert pd.isna(out[(out.cc == "CC20") & (out.month == "2026-03")].mom.iloc[0])
    # YTD restarts in January
    jan = out[(out.cc == "CC10") & (out.month == "2026-01")].iloc[0]
    assert np.isclose(jan.ytd_actual, jan.actual)
    # mapped CC30 has no step change at the re-org (pre-period includes CC31)
    c30 = out[out.cc == "CC30"].set_index("month").actual
    assert abs(c30["2025-07"] - c30["2025-06"]) < 6
    print("p6 OK  | sqlite", sqlite3.sqlite_version, "| rows", len(out))
    print(out[out.cc == "CC20"].tail(5).round(2).to_string(index=False))


if __name__ == "__main__":
    _tests()
```

**Hints (tiered):** (1) "Dedupe first: `ROW_NUMBER() OVER (PARTITION BY cost_center, month ORDER BY posted_at DESC)` and keep rn = 1." (2) "Map with a LEFT JOIN and `COALESCE(new_cc, cost_center)`, then GROUP BY." (3) "LAG counts rows, not months: build an integer month index and compare `LAG(m_idx)` with `m_idx − 1`."

**Follow-ups:** "Should the missing month be zero or NULL in YTD?" (Ask the business: a cost centre that didn't post is usually a late posting, not zero spend; flag it.) · "The re-org: map history to the new hierarchy (restated view) or keep as-was?" (Both are legitimate; planning usually wants restated so trends are comparable.) · "How would you test this in production?" (Row-count reconciliation to the ledger, sum-of-children = parent, duplicates = 0.)

**Common mistakes / red flags:** `MAX(posted_at)` joined back (works, but clumsy); mapping after summing (double counts); YTD partitioned by cost centre only. *Red flag:* LAG with no gap check, or no instinct that re-posts exist.

**Rubric:** **4** correct query with gap-aware MoM and a reconciliation idea · **3** correct except one detail · **2** dedupe + mapping only · **1** can't write a window function.

## P7. AI variance explainer: price/volume/mix + narrative guardrail (swap-in, 8–10 min)

**Pillar:** **D**, AI apps adopted by business users.
**Why this problem:** the numeric core of a real FP&A AI app: an exact decomposition the LLM is allowed to talk about, plus a guardrail that checks every number and direction word in the LLM's draft against the computed facts. It tests whether the candidate thinks about trust and verification, not just generation.

**Prompt to paste:**

> Plan vs actual balances and margins for four products; NII = balance × margin. (1) `pvm(plan, actual)`: split the NII variance into volume, mix and rate effects that add up **exactly** to the total. (2) `check_narrative(text, facts)`: an LLM drafted the commentary. Extract every number with a unit ($bn, $m, %, bp), match it to a computed fact within 2%, and flag numbers that match nothing and direction words ("added", "drag", "below"…) that contradict the sign.

**Starter ([`starters/p7_starter.py`](starters/p7_starter.py)):**

```python
# file: interview-kit-2/starters/p7_starter.py
"""
Variance explainer + narrative guardrail (the core of a finance AI app). ~10 minutes.

plan, actual: index = product, columns balance ($bn) and margin (%).
NII_i = balance_i * margin_i / 100 ($bn).
1. pvm(plan, actual) -> dict with nii_plan, nii_actual, total, volume, mix, rate:
     volume = (B1_tot - B0_tot) * mbar0 / 100,   mbar0 = sum w0_i m0_i
     mix    = B1_tot * sum (w1_i - w0_i) m0_i / 100,   w = balance shares
     rate   = sum B1_i (m1_i - m0_i) / 100
   volume + mix + rate must equal total exactly.
2. check_narrative(text, facts, tol=0.02) -> list of problems. Extract the
   numbers with units ($..bn, $..m, %, bp), match each to a fact (abs value,
   relative tol), and flag (a) numbers that match no fact and (b) direction
   words (up/added/higher vs down/drag/cost/below) that contradict the sign.
"""
import re
import numpy as np
import pandas as pd


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def make_books():
    plan = pd.DataFrame({"product": ["Checking", "Savings", "CDs", "Commercial"],
                         "balance": [40.0, 30.0, 10.0, 20.0],
                         "margin": [2.50, 1.80, 0.60, 2.10]}).set_index("product")
    actual = pd.DataFrame({"product": ["Checking", "Savings", "CDs", "Commercial"],
                           "balance": [36.0, 29.0, 17.0, 21.0],
                           "margin": [2.60, 1.60, 0.45, 2.00]}).set_index("product")
    return plan, actual



def pvm(plan, actual) -> dict:
    raise NotImplementedError


def check_narrative(text: str, facts: dict, tol: float = 0.02):
    raise NotImplementedError


def check():
    plan, actual = make_books()
    d = pvm(plan, actual)
    print({k: round(v, 4) for k, v in d.items()})
    assert np.isclose(d["volume"] + d["mix"] + d["rate"], d["total"])
    assert np.isclose(d["total"], -0.1235, atol=1e-4)
    facts = {k: round(v, 3) for k, v in d.items()}
    facts["Savings_margin_bp"] = -20.0
    good = ("NII came in at $1.90bn, $123m below plan. Volume added $61m, but mix was a "
            "$116m drag, and rates cost $68m; Savings margin was down 20bp.")
    bad = good.replace("Volume added", "Volume fell by").replace("20bp", "35bp")
    assert check_narrative(good, facts) == [], check_narrative(good, facts)
    probs = check_narrative(bad, facts)
    print(probs)
    assert len(probs) == 2
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p7_variance_explainer_guardrail.py`](solutions/p7_variance_explainer_guardrail.py)):**

```python
# file: interview-kit-2/solutions/p7_variance_explainer_guardrail.py
"""
Problem 7 (swap-in, ~10 min): the numeric core of an AI "variance explainer"
for finance users, plus a guardrail that checks an LLM-written narrative.

plan and actual: per product, average balance ($bn) and net margin (%).
NII_i = balance_i * margin_i / 100 ($bn, annualized).
  1. pvm(plan, actual): split total NII variance into
       volume = (B1_tot - B0_tot) * mbar0                 mbar0 = sum w0_i m0_i
       mix    = B1_tot * sum_i (w1_i - w0_i) * m0_i        w = balance shares
       rate   = sum_i B1_i * (m1_i - m0_i)
     (all /100). The three must add up EXACTLY to the total variance.
  2. check_narrative(text, facts, tol): pull every number out of a draft
     narrative (handles $, commas, 'bn', 'm', '%', 'bp'), match each to a
     computed fact within a relative tolerance, check the direction words
     ('up', 'down', 'higher', 'lower', ...), and return the unsupported claims.
Only numpy, pandas and the standard library (re).
"""
import re
import numpy as np
import pandas as pd


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def make_books():
    plan = pd.DataFrame({"product": ["Checking", "Savings", "CDs", "Commercial"],
                         "balance": [40.0, 30.0, 10.0, 20.0],
                         "margin": [2.50, 1.80, 0.60, 2.10]}).set_index("product")
    actual = pd.DataFrame({"product": ["Checking", "Savings", "CDs", "Commercial"],
                           "balance": [36.0, 29.0, 17.0, 21.0],
                           "margin": [2.60, 1.60, 0.45, 2.00]}).set_index("product")
    return plan, actual


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def pvm(plan: pd.DataFrame, actual: pd.DataFrame) -> dict:
    B0, m0 = plan.balance, plan.margin
    B1, m1 = actual.balance.reindex(B0.index), actual.margin.reindex(B0.index)
    w0, w1 = B0 / B0.sum(), B1 / B1.sum()
    mbar0 = float((w0 * m0).sum())
    out = dict(
        nii_plan=float((B0 * m0).sum() / 100),
        nii_actual=float((B1 * m1).sum() / 100),
        volume=float((B1.sum() - B0.sum()) * mbar0 / 100),
        mix=float(B1.sum() * ((w1 - w0) * m0).sum() / 100),
        rate=float((B1 * (m1 - m0)).sum() / 100),
    )
    out["total"] = out["nii_actual"] - out["nii_plan"]
    return out


_NUM = re.compile(r"(?P<sign>[-+]|\u2212)?\$?(?P<num>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*"
                  r"(?P<unit>bn|billion|m|mm|million|%|bp|bps)?", re.I)
_UP = {"up", "higher", "above", "increase", "increased", "rose", "grew", "gain", "tailwind", "added", "beat"}
_DOWN = {"down", "lower", "below", "decrease", "decreased", "fell", "declined", "drag", "headwind",
         "cost", "reduced", "miss", "shortfall"}


def extract_claims(text: str):
    """Yield (value_in_$bn_or_raw, unit, direction or None, matched text)."""
    claims = []
    for mt in _NUM.finditer(text):
        num = float(mt.group("num").replace(",", ""))
        unit = (mt.group("unit") or "").lower()
        if mt.group("sign") in ("-", "\u2212"):
            num = -num
        if unit in ("m", "mm", "million"):
            num, unit = num / 1000.0, "bn"
        elif unit == "billion":
            unit = "bn"
        # direction = the direction word nearest to the number within its clause
        seps = [m.end() for m in re.finditer(r"[,;!?\n]|\.\s", text[:mt.start()])]
        a = seps[-1] if seps else 0
        ends = [i for i in (text.find(ch, mt.end()) for ch in ",;!?\n") if i != -1]
        dot = re.search(r"\.(\s|$)", text[mt.end():])
        if dot:
            ends.append(mt.end() + dot.start())
        b = min(ends) if ends else len(text)
        best, direction = None, None
        for w in re.finditer(r"[a-z]+", text[a:b].lower()):
            kind = "up" if w.group() in _UP else "down" if w.group() in _DOWN else None
            if kind:
                dist = abs((a + w.start()) - mt.start())
                if best is None or dist < best:
                    best, direction = dist, kind
        claims.append(dict(value=num, unit=unit, direction=direction, text=mt.group(0).strip()))
    return claims


def check_narrative(text: str, facts: dict, tol: float = 0.02):
    """Return a list of problems. A claim is supported if |value| matches |fact|
    within tol (relative) for some fact, and its direction word agrees with the
    sign of that fact. Numbers without a unit (e.g. years, quarter labels) are ignored."""
    problems = []
    for c in extract_claims(text):
        if c["unit"] == "":
            continue
        cands = [(k, v) for k, v in facts.items()
                 if np.isclose(abs(c["value"]), abs(v), rtol=tol, atol=1e-3)]
        if not cands:
            problems.append(("unsupported number", c["text"]))
            continue
        k, v = cands[0]
        if c["direction"] is not None and v != 0:
            if (c["direction"] == "up") != (v > 0):
                problems.append(("wrong direction", c["text"] + " vs " + k))
    return problems


def facts_from(plan, actual, d):
    f = {k: round(v, 3) for k, v in d.items()}
    for p in plan.index:                                       # per-product margin moves in bp
        f[f"{p}_margin_bp"] = round((actual.margin[p] - plan.margin[p]) * 100, 1)
    return f


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    plan, actual = make_books()
    d = pvm(plan, actual)
    assert np.isclose(d["volume"] + d["mix"] + d["rate"], d["total"], atol=1e-12)
    # sanity: no change -> zero everywhere; pure rate change -> rate effect only
    z = pvm(plan, plan)
    assert all(abs(z[k]) < 1e-12 for k in ("volume", "mix", "rate", "total"))
    p2 = plan.assign(margin=plan.margin + 0.10)
    r = pvm(plan, p2)
    assert np.isclose(r["rate"], plan.balance.sum() * 0.10 / 100) and abs(r["mix"]) < 1e-12
    facts = facts_from(plan, actual, d)
    good = ("NII came in at ${:.2f}bn, ${:.0f}m below plan. Volume added ${:.0f}m, "
            "but mix was a ${:.0f}m drag as balances moved into CDs, and rates cost ${:.0f}m; "
            "Savings margin was down {:.0f}bp.").format(
        d["nii_actual"], abs(d["total"]) * 1000, d["volume"] * 1000, abs(d["mix"]) * 1000,
        abs(d["rate"]) * 1000, abs(facts["Savings_margin_bp"]))
    assert check_narrative(good, facts) == [], check_narrative(good, facts)
    bad = good.replace("Volume added", "Volume fell by").replace(
        "Savings margin was down {:.0f}bp".format(abs(facts["Savings_margin_bp"])),
        "Savings margin was down 35bp")
    probs = check_narrative(bad, facts)
    kinds = sorted(p[0] for p in probs)
    assert kinds == ["unsupported number", "wrong direction"], probs
    # parser details
    cl = extract_claims("a gain of $1,250m and a -0.4% move in 2026")
    assert np.isclose(cl[0]["value"], 1.25) and cl[0]["unit"] == "bn" and cl[1]["value"] == -0.4
    assert cl[2]["unit"] == ""          # the year is not a claim
    print("p7 OK  | total %.3f = volume %.3f + mix %.3f + rate %.3f ($bn)" %
          (d["total"], d["volume"], d["mix"], d["rate"]))
    print("good draft:", good)
    print("bad draft problems:", probs)


if __name__ == "__main__":
    _tests()
```

**Hints (tiered):** (1) "Write total = Σ B1·m1 − Σ B0·m0 and add and subtract Σ B1·m0; the rate effect falls out, and the rest is volume + mix." (2) "One regex for numbers with an optional sign, `$`, commas, decimals and a unit; normalize $m to $bn." (3) "Direction: take the nearest direction word in the same clause."

**Follow-ups:**

- "Order dependence: your decomposition puts rate last. What changes if you do rate first?" (Volume/mix/rate split is order-dependent; the interaction term moves. Pick a convention and keep it; or use a symmetric (Shapley-style) split.)
- "How would you ship this to FP&A users?" (Deterministic facts table → LLM writes only from the table → guardrail blocks or flags unsupported numbers → human approves; log every rejection; measure adoption and edit rate.)
- "What can the regex guardrail not catch?" (Correct numbers attached to the wrong driver; causal claims ("due to competitor pricing") with no data; rounding games. Next step: structured output (JSON with fact IDs) instead of free text.)
- "What would a stronger guarantee look like here?" (Constrain generation to templates or fact IDs; property-based tests on the decomposition; reject on any unmatched number.)

**Common mistakes / red flags:** a decomposition that doesn't reconcile (the residual "other" bucket); a regex that turns "2026" into a claim; matching signed values only (narratives use absolute values with direction words). *Red flag:* thinks the LLM itself should do the arithmetic.

**Rubric:** **4** exact PVM + working guardrail + a credible shipping plan · **3** exact PVM + partial guardrail · **2** PVM with a residual, guardrail verbal · **1** can't reconcile the decomposition.

> **Refresher and cheat sheet:** [refresher.md](refresher.md) (methods + line-by-line walkthroughs of every reference solution) · [cheatsheet.md](cheatsheet.md) (one page).

# Appendix A. Files, how to run, test results

```text
interview-kit-2/
  README.md                                    this kit (run sheet, problems, code inline)
  refresher.md                                 methods + line-by-line walkthroughs
  cheatsheet.md                                one-page cheat sheet
  solutions/
    p1_champion_outcomes.py                    P1 reference + generator + asserts
    p2_deposit_runoff_scenarios.py             P2 (loop, vectorized grid, breach frontier)
    p3_frozen_champion_overlay.py              P3 (hinge ridge overlay, time-ordered lambda)
    p4_scenario_distance_ot.py                 P4 (1-D W, OT LP, sliced W2)
    p5_planning_allocation_milp.py             P5 (LP + duals, MILP, brute force, greedy)
    p6_gl_sql_pipeline.py                      P6 (sqlite3 window functions vs pandas)
    p7_variance_explainer_guardrail.py         P7 (PVM + narrative checker)
  starters/p1_starter.py ... p7_starter.py     paste into CoderPad (generator + stubs + check())
  test_starters.py                             stubs must fail; reference functions must pass check()
  run_all.sh                                   runs everything (PYTHON=... picks the interpreter)
```

Run: `bash run_all.sh` (or `PYTHON=/path/to/python bash run_all.sh`). Each file is also standalone: `python3 p1_champion_outcomes.py`.

**Output of the last full run** (Python 3.13.5 / numpy 2.5.4 / pandas 3.0.6 / scipy 1.18.1 / statsmodels 0.15.0):

```text
python 3.13.5 | numpy 2.5.4 | pandas 3.0.6
== p1_champion_outcomes.py
p1 OK  | n_oos = 79 | statsmodels cross-check: True
champion (oracle x) RMSE = 0.393
           RMSE    MAE
forecast  0.648  0.505
rw        0.800  0.624
mean      1.209  0.989
DM fixed vs rw: stat=-3.07 p=0.0029
== p2_deposit_runoff_scenarios.py
p2 OK  | grid (21, 9) | trough at (5pp, beta 0) = 0.691
trough share (rows: shock pp 0,1,..,5; cols: beta 0,0.2,..,0.8)
[[0.948 0.954 0.96  0.965 0.971]
 [0.894 0.91  0.927 0.944 0.96 ]
 [0.841 0.868 0.895 0.922 0.949]
 [0.789 0.826 0.863 0.9   0.939]
 [0.739 0.785 0.831 0.879 0.928]
 [0.691 0.745 0.8   0.858 0.917]]
breach frontier (shock pp for 15% runoff) by beta {0.0: 1.83, 0.1: 2.09, 0.2: 2.42, 0.3: 2.84, 0.4: 3.4, 0.5: 4.19}
== p3_frozen_champion_overlay.py
p3 OK  | lam = 0.03162 | holdout RMSE champion 0.801 -> challenger 0.076 | old-regime max change 0.0 | sklearn check: True
overlay coefficients on hinges at [2.0, 3.0, 4.0, 5.0] : [0.016, 0.326, 0.151, 0.0]
== p4_scenario_distance_ot.py
p4 OK  | W1(dUR hist, stress) = 0.600 | LP check: True | SW2 stress 0.542 vs noise 0.060
== p5_planning_allocation_milp.py
p5 OK  | LP obj 63.16, budget shadow price 2.03/unit, cost of +1 unit of reg floor 0.94 | MILP 47.11 == brute force 47.11, funded [0, 1, 1, 0, 0, 0, 0, 1] | greedy 35.40 (gap 11.71)
== p6_gl_sql_pipeline.py
p6 OK  | sqlite 3.46.1 | rows 53
  cc   month  actual  budget  variance  ytd_actual  mom
CC20 2026-01   68.04   68.64     -0.60       68.04 2.94
CC20 2026-03   69.48   70.08     -0.60      137.52  NaN
CC20 2026-04   69.72   70.80     -1.08      207.24 0.24
CC20 2026-05   69.81   71.52     -1.71      277.05 0.09
CC20 2026-06   70.48   72.24     -1.76      347.53 0.67
== p7_variance_explainer_guardrail.py
p7 OK  | total -0.123 = volume 0.061 + mix -0.116 + rate -0.068 ($bn)
good draft: NII came in at $1.90bn, $123m below plan. Volume added $61m, but mix was a $116m drag as balances moved into CDs, and rates cost $68m; Savings margin was down 20bp.
bad draft problems: [('wrong direction', '$61m vs volume'), ('unsupported number', '35bp')]
== starters
starter p1: stubs fail cleanly; check() passes with reference functions
starter p2: stubs fail cleanly; check() passes with reference functions
starter p3: stubs fail cleanly; check() passes with reference functions
starter p4: stubs fail cleanly; check() passes with reference functions
starter p5: stubs fail cleanly; check() passes with reference functions
starter p6: stubs fail cleanly; check() passes with reference functions
starter p7: stubs fail cleanly; check() passes with reference functions
```

**Compatibility matrix** (all seven solutions pass their asserts; every starter's stubs fail cleanly and its `check()` passes with the reference functions):

| Stack | Result |
|---|---|
| Py 3.13.5, numpy 2.5.4, pandas 3.0.6, scipy 1.18.1, statsmodels 0.15.0, scikit-learn 1.9.1; FutureWarning → error | all pass |
| Py 3.12, numpy 2.0.2, pandas 2.2.3, scipy 1.18.1, statsmodels 0.15.0, scikit-learn 1.9.1; FutureWarning and DeprecationWarning → error | all pass |
| Py 3.9, numpy 1.20.2, pandas 1.2.4, scipy 1.6.3, statsmodels 0.12.2, scikit-learn 0.24.2 (CoderPad-Screen-like) | all pass (P5 uses the brute-force MILP verifier: no `milp`) |
| Py 3.12, numpy + pandas only | all pass (statsmodels/sklearn cross-checks, P4 LP and P5 LP/MILP skipped; P5 brute force still runs) |

**Not verified:** the exact library versions in *your* pad (run the version cell first); CoderPad's execution-time limits (everything here runs in a few seconds); the deposit, rate and ledger numbers are stylized and illustrative, not calibrated to any institution.
