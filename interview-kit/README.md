# Python quant/forecasting coding interview kit

> **Generic practice material for a Python quant/forecasting coding interview. Synthetic data; illustrative scenarios; not investment advice; not affiliated with any employer.**

A 60-minute CoderPad-style kit for a quant / forecasting role on a bank planning team: seven problems with starter files (paste into the pad), tested reference solutions, tiered hints, follow-ups, rubrics, a methods refresher and a one-page cheat sheet. All data are synthetically generated inside the scripts.

**Contents**

- [0. At a glance](#0-at-a-glance)
- [1. Interview plan](#1-interview-plan) (run sheet, warm-up questions, problem menu, environment notes, scoring sheet)
- [2. Problems](#2-problems): [P1](#p1-warm-up-clean-a-quarterly-bank-panel-core-5-min) · [P2](#p2-challenger-vs-naive-rolling-origin-backtest--dieboldmariano-core-13-min) · [P3](#p3-conditional-scenario-forecast-deposits-under-a-ccar-style-path-core-main-event-17-min) · [P4](#p4-local-projection-irf-with-neweywest-ses-swap-in-1012-min) · [P5](#p5-budget-allocation-lagrange-bisection-vs-scipy-swap-in-1012-min) · [P6](#p6-monte-carlo-credit-losses-vectorize-numba-swap-in-812-min) · [P7](#p7-sql-window-functions-on-a-quarterly-panel-swap-in-810-min) (each with the starter and reference solution inline)
- [Refresher: methods and walkthroughs of the reference solutions](refresher.md)
- [One-page cheat sheet](cheatsheet.md)
- [Appendix A. Files, how to run, test results](#appendix-a-files-how-to-run-test-results)

**Files in this folder:** [`solutions/`](solutions/) (p1–p7 reference solutions with data generators and asserts) · [`starters/`](starters/) (p1–p7 starter files) · [`test_starters.py`](test_starters.py) · [`run_all.sh`](run_all.sh)

# 0. At a glance

| | |
|--|-------|
| **Format** | 60 min total, Python CoderPad: **~12 min intros**, **~36 min coding**, **~8–10 min for the candidate's questions** |
| **What we must verify** | (1) The candidate writes clean Python *themselves*. (2) Time-series and backtest discipline, with no look-ahead. (3) Turning an imposed scenario path into a forecast, which is often the least-proven skill for scenario work. |
| **Core path (36 min)** | **P1** pandas warm-up (5) → **P2** challenger vs naive backtest + DM (13) → **P3** conditional scenario forecast, the main event (17) |
| **Swap-ins** | **P4** local projection + Newey–West (checks whether the candidate really codes econometric methods) · **P5** budget allocation: Lagrange bisection vs scipy · **P6** Monte Carlo + vectorization/Numba · **P7** SQL window functions |
| **Files** | `solutions/p1…p7_*.py` (reference solutions with generators and asserts) · `starters/p1…p7_starter.py` (paste into the pad) · `run_all.sh` |
| **Hire bar (suggested)** | At least **3/4 on P2 and on P3**, and at least **3/4 on the "own Python" cross-cutting score**. A 2 on P1 is OK if P2 and P3 are strong. A 1 on any core problem, or code that only appears in big pasted blocks the candidate can't explain, is a no. |

# 1. Interview plan

## 1.1 Minute-by-minute run sheet (60 min)

| Clock | Segment | What you do | Exit criterion / hard stop |
|--|---|---------|------|
| 0:00–0:02 | **Your intro + format** | "About 35–40 minutes in the pad, then time for your questions. Think out loud. Looking up API docs is fine; please keep AI assistants off for this one so I can see your own code." | — |
| 0:02–0:12 | **Candidate intro + warm-up questions** | Let the candidate give a 2-minute background, then ask 2–3 of the warm-up questions in §1.2. They lead straight into P2 and P3. | Hard stop at **0:12** even if mid-story ("let's pick that up in code"). |
| 0:12–0:14 | **Pad setup** | Paste `p1_starter.py`. Have the candidate run the version line (§1.4) so you both know what's installed. | — |
| 0:14–0:19 | **P1 warm-up** (core tasks 1–3 only) | Dedupe restatements, complete quarterly grid, QoQ/YoY without bridging gaps. | At **0:19**: if not done, give Hint 3 and move on. YTD NII and mergers are verbal-only unless the candidate is fast. |
| 0:19–0:20 | Transition | Paste `p2_starter.py` (replace the pad contents, or add it below). | — |
| 0:20–0:33 | **P2 backtest** (13 min) | Expanding-window ARX vs random walk and historical mean; RMSE/MAE; DM. | Checkpoints: **0:25** one-origin forecast works · **0:29** full loop and RMSE table · **0:33** DM (or a verbal DM if behind). |
| 0:33–0:50 | **P3 conditional scenario forecast** (17 min, the main event) | Fit the ARX, project under baseline and severely adverse paths, levels, bands, stress overlay. | Checkpoints: **0:37** `fit_arx` · **0:43** SA path in levels · **0:47** bands or stress · **0:47–0:50** debrief: "What's wrong with this under SA?" |
| 0:50–0:52 | **Close the pad** | One ownership question: "If you had another hour on P3, what would you change first?" Score the cross-cutting dimensions now while it's fresh. | — |
| 0:52–1:00 | **Candidate's questions** | Protect this time; it is part of the sell. | End on time. |

**Coding time:** 0:14–0:50 = **36 min** (P1 5 + P2 13 + P3 17, plus about 1 min of transitions).

## 1.2 Warm-up questions for the intro (pick 2–3, about 3 min each)

These ease the candidate in, and each one primes a coding problem so the switch to the pad is natural.

1. **"Tell me about a forecasting project where you avoided look-ahead bias. What was the benchmark, and how did you make sure nothing from the future leaked into the out-of-sample forecasts?"** *(primes P2.)* Good: expanding or rolling window, any transforms (PCA, standardization) re-estimated at each origin, the right test for nested models (Clark–West), and an unprompted caveat if the out-of-sample sample is small or the result is split-sensitive. Weak: "R² went up."
2. **"What does your Python setup look like day to day? Tell me about a time you had to make slow numerical code fast."** *(primes P6 and the ownership question.)* Good: a concrete kernel (a simulation or recursive loop), a speedup number, and a gotcha (e.g. Numba's first-call compile time, no pandas inside `@njit`; or memory blow-up from vectorizing). Weak: vague, or no hands-on example.
3. **"Have you ever had to force a model through a given path, e.g. a policy-rate, unemployment or oil-price assumption? How did you do it?"** *(primes P3.)* Good: distinguishes treating a variable as exogenous from conditioning a VAR (Waggoner–Zha / Kalman), and mentions the uncertainty bands. Weak: never thought about it. That isn't disqualifying, but P3 then matters even more.
4. *(Motivation, only if time allows)* **"What draws you to applied forecasting and planning work?"** Keep it short; the full motivation conversation belongs in a different round.

## 1.3 Problem menu and how to adapt

| ID | Problem | Role in this interview | Minutes | Primary signal |
|-|--------|---|-|----|
| **P1** | Clean a quarterly bank panel (restatements, gaps, QoQ/YoY; stretch: YTD NII, merger pro-forma) | **Core**, warm-up | 5 | pandas fluency; call-report data instincts |
| **P2** | Expanding-window ARX challenger vs naive, RMSE/MAE, Diebold–Mariano (+ Clark–West) | **Core** | 13 | Backtest discipline, no look-ahead, honest inference |
| **P3** | Conditional forecast of deposits under baseline / severely adverse UR and 10y paths, with bands and a stress overlay (stretch: VAR with Waggoner–Zha conditioning) | **Core**, main event | 17 | Scenario → forecast translation |
| P4 | Local projection IRF with hand-coded Newey–West (stretch: LP-IV) | Swap-in | 10–12 | Does the candidate really code their own methods? |
| P5 | Budget allocation: bisection on λ vs scipy SLSQP/linprog (stretch: MILP with min spend) | Swap-in | 10–12 | Optimization range beyond a single hand-rolled method |
| P6 | Vasicek credit-loss Monte Carlo: loop → vectorize → Numba | Swap-in | 8–12 | Vectorization, Numba/performance, MC error |
| P7 | SQL window functions on a quarterly panel (sqlite3 in Python) | Swap-in | 8–10 | SQL fluency; gap-aware LAG; frames |

**If the candidate is fast:**

- **Finishes P1 by 0:17:** ask for task 4 (YTD → quarterly NII) in code, and talk through the merger part (task 5). Don't start P2 early; bank the time for P3.
- **Finishes P2 by 0:29:** ask for Clark–West ("the ARX nests the mean model, so is DM the right test?") and h = 4 direct forecasts. Two minutes, then go to P3.
- **Finishes P3 core by 0:45:** go to the P3 stretch (the VAR with conditioning on endogenous variables), *or* do a **5-minute P6 mini**: paste only `losses_loop` from the reference solution and say, "make this 50× faster, with Numba if it's installed, otherwise numpy." This is a cheap performance probe.
- **Everything done by 0:45:** P7 query 2 (gap-aware LAG) as a 5-minute verbal or SQL probe.

**If the candidate is stuck:**

- **P1 stuck past 0:19:** give Hint 3 (`reindex` onto `period_range`) and move on. P1 is a warm-up, so don't let it eat P3's time.
- **P2 stuck on the design matrix by 0:25:** give Hint 2 (paste the `design()` helper). If the loop still isn't running by 0:30, skip DM in code and ask for it verbally (formula and why HAC).
- **P3 stuck on the fit by 0:38:** paste `fit_arx` from the reference solution and ask the candidate to write only `project()`. The recursion and the jump-off difference are what we're scoring. If the projection isn't done by 0:45, go straight to the debrief questions. The conceptual answers still count toward the rubric.
- **Shaky Python overall** (doesn't know `groupby().shift()`, writes loops over DataFrame rows everywhere): don't use P4 as a swap-in if econometrics is the candidate's strong suit, since it would flatter them. Use P6 at the end to see whether loops and vectorization are within reach.

**For a second round** (recommended if the candidate clears the bar): P4 + P5 + P6 make a good 45-minute second pad (LP 12, budget 15, Monte Carlo/Numba 12), and P7 works as a 10-minute SQL add-on. Together they cover performance, SQL and optimization skills.

## 1.4 Environment notes and fallbacks

- **Run this first in the pad:**
  `import sys, numpy, pandas, scipy, statsmodels; print(sys.version, numpy.__version__, pandas.__version__, scipy.__version__, statsmodels.__version__)`
  then `import numba` (it may fail; see below).
- **What CoderPad documents:** the standard Python 3 pad ships numpy, scipy, pandas, scikit-learn and statsmodels. **Numba is not on that list.** It is in CoderPad's *Jupyter (SciPy)* notebook pads. CoderPad's "Screen" product documents older versions (Python 3.11.5, NumPy 1.20.2, pandas 1.2.4, SciPy 1.6.3). Check the version line on the day.
- **Tested:** every reference solution passes on four stacks: (a) Python 3.13 / pandas 3.0.6 / numpy 2.5.4 / scipy 1.18.1 / statsmodels 0.15.0 / numba 0.68.0; (b) Python 3.12 / pandas 2.2.3 / numpy 2.0.2 / same scipy, statsmodels, numba, with FutureWarnings promoted to errors; (c) **Python 3.9 / pandas 1.2.4 / numpy 1.20.2 / scipy 1.6.3 / statsmodels 0.12.2**, which mimics CoderPad Screen; (d) **numpy + pandas only** (no scipy, statsmodels or numba).
- **Fallbacks built into the solutions** (worth telling the candidate about if an import fails):

| Missing | Fallback used in the reference code |
|---|---|
| statsmodels | Hand-rolled OLS with `np.linalg.lstsq` (P2, P3, P4) and hand-rolled Newey–West (P4). The statsmodels cross-checks are skipped. |
| scipy.stats | Normal CDF via `math.erf` (P2 DM/CW p-values); inverse normal via `statistics.NormalDist` (P6) |
| scipy.optimize | P5 runs bisection only, and the solver comparison becomes a verbal discussion |
| `scipy.optimize.milp` (scipy < 1.9) | P5's MILP extension is skipped; `linprog` duals are skipped on scipy < 1.7 |
| numba | P6 runs the loop and vectorized versions; ask the candidate to *describe* the `@njit` version (or write it untested) |
| A SQL pad | P7 uses `sqlite3` from the standard library inside a Python pad (window functions need SQLite ≥ 3.25; the `RANGE` frame needs ≥ 3.28) |

- **pandas-version gotchas the candidate might hit** (and you shouldn't penalize): `pct_change()` filled gaps forward by default in pandas < 2.1, which silently bridged missing quarters. That default was deprecated in 2.1 and removed in 3.0, so behavior differs by version. The solutions use an explicit `x / x.shift(k) - 1` on a complete grid. Offset aliases changed in 2.2 (`'Q'` → `'QE'` for `resample`); `Period` frequencies still use `'Q'`.
- **AI assistance:** if your CoderPad plan has an AI assistant, switch it off for this pad. Experience with AI coding tools is better probed verbally.

## 1.5 Scoring sheet

Score each problem used on its 1–4 rubric (in each problem section), plus four cross-cutting dimensions:

| Dimension | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| **Own Python** (fluency, idiom, debugging) | Can't get a basic pandas/numpy step to run without heavy help | Gets there, but with row loops, trial and error, and API guessing | Idiomatic numpy/pandas, reads tracebacks and fixes them quickly | Fluent, writes small checks unprompted, structures functions cleanly |
| **Time-series discipline** | Uses future data or full-sample transforms without noticing | Avoids the obvious leak only when prompted | Volunteers the no-look-ahead design; knows the oracle-regressor issue | Also raises vintages/revisions, nested-model inference, small-n caution |
| **Scenario translation** | Plugs numbers into a regression with no thought about jump-off, levels or uncertainty | Gets a path but misses the levels/jump-off/band issues | Correct recursion, levels, bands; explains the exogeneity assumption | Also flags Lucas critique, extrapolation beyond the historical range, VAR conditioning, structural vs observed conditioning |
| **Communication** | Silent or unclear | Explains only when asked | Narrates choices clearly | Explains trade-offs the way they would to a finance partner |

**Decision guide:** strong yes = P2 ≥ 3, P3 ≥ 3, own Python ≥ 3, plus one 4 anywhere. Yes = P2 and P3 ≥ 3. Lean no = either core problem at 2 with own Python ≤ 2. No = any 1 on the core problems, or code the candidate can't explain.

# 2. Problems

Each problem has the prompt to paste, the starter file (paste the whole file into the pad; the docstring repeats the prompt), the tested reference solution, tiered hints, follow-ups, mistakes and red flags, strong vs weak answers, and a 1–4 rubric. **Core path: P1 → P2 → P3.**

## P1. Warm-up: clean a quarterly bank panel (core, 5 min)

**Why this problem:** call-report panels (FR Y-9C, FFIEC 031/041) have exactly these traps: refiled or amended reports, banks that miss a quarter, income items reported **year-to-date**, and mergers that create fake growth. It is a quick test of pandas fluency and of whether the candidate has data instincts for bank data, which may be new territory for someone from an academic or policy background.

**Prompt to paste (or say):**

> Here's a synthetic call-report-style panel: one row per bank per filing, with quarter-end date, filing date, total deposits and year-to-date net interest income. Write `clean_panel(raw)` that returns one row per bank-quarter on a complete quarterly grid: keep the latest filing when a bank filed twice, make missing quarters show up as NaN rows, and compute QoQ and YoY deposit growth without computing growth across a gap. If you have time: convert YTD NII to quarterly, then compute bank A's merger-adjusted deposit growth (it bought bank B in 2021Q3).

**Starter ([`starters/p1_starter.py`](starters/p1_starter.py)):**

```python
# file: interview-kit/starters/p1_starter.py
"""
Warm-up: clean a quarterly bank panel (call-report-like). ~5 minutes.

raw has columns: bank_id, report_date (quarter-end Timestamp), filed_at,
total_deposits, nii_ytd (net interest income, YEAR-TO-DATE cumulative).

Write clean_panel(raw) returning one row per (bank_id, quarter) with:
  quarter (pandas Period, freq Q), total_deposits, dep_qoq, dep_yoy
  1. If a bank filed twice for the same quarter, keep the LATEST filing.
  2. Missing quarters must show up as rows with NaN (not be skipped), and growth
     must not be computed across a gap.
  3. dep_qoq = QoQ growth, dep_yoy = growth vs same quarter last year.
If time: (4) add nii_q = quarterly NII from the YTD column;
         (5) bank A acquired bank B in 2021Q3 (see `mergers`): compute A's
             merger-adjusted (organic) deposit growth.
"""
import numpy as np
import pandas as pd


def make_panel(seed: int = 0):
    """Return (raw, mergers, truth).

    raw      : long panel with columns bank_id, report_date, filed_at,
               total_deposits, nii_ytd   (one bad duplicate row, one gap)
    mergers  : DataFrame acquirer, target, deal_quarter (Period)
    truth    : dict of known quantities used by the asserts
    """
    rng = np.random.default_rng(seed)
    quarters = pd.period_range("2019Q1", "2023Q4", freq="Q")
    rows = []
    g = {"A": 0.02, "B": 0.02, "C": 0.01}        # constant organic QoQ growth
    d0 = {"A": 1000.0, "B": 400.0, "C": 250.0}   # starting deposits
    q_nii = {"A": 10.0, "B": 4.0, "C": 2.5}      # constant quarterly NII
    deal_q = pd.Period("2021Q3", freq="Q")        # A acquires B in 2021Q3
    for bank in ["A", "B", "C"]:
        dep = d0[bank]
        for i, q in enumerate(quarters):
            if i > 0:
                dep *= 1 + g[bank]
            if bank == "B" and q >= deal_q:
                break                              # B stops filing at the deal
            rows.append(dict(bank_id=bank, report_date=q.end_time.normalize(),
                             filed_at=q.end_time.normalize() + pd.Timedelta(days=30),
                             total_deposits=dep, nii_ytd=q_nii[bank] * q.quarter))
    raw = pd.DataFrame(rows)
    # After the deal, A's reported deposits include B's book.
    b_dep = {q: d0["B"] * (1 + g["B"]) ** i for i, q in enumerate(quarters)}
    mask = (raw.bank_id == "A") & (raw.report_date.dt.to_period("Q") >= deal_q)
    raw.loc[mask, "total_deposits"] += raw.loc[mask, "report_date"].dt.to_period("Q").map(b_dep)
    # Restatement: an early wrong filing for C 2020Q2, later corrected.
    bad = raw[(raw.bank_id == "C") & (raw.report_date == pd.Timestamp("2020-06-30"))].copy()
    bad["total_deposits"] *= 1.5
    bad["filed_at"] -= pd.Timedelta(days=20)          # filed earlier -> stale
    raw = pd.concat([raw, bad], ignore_index=True)
    # Missing quarter: C did not file 2022Q1.
    raw = raw[~((raw.bank_id == "C") & (raw.report_date == pd.Timestamp("2022-03-31")))]
    raw = raw.sample(frac=1.0, random_state=seed).reset_index(drop=True)  # shuffle
    mergers = pd.DataFrame({"acquirer": ["A"], "target": ["B"], "deal_quarter": [deal_q]})
    truth = dict(g=g, q_nii=q_nii, deal_q=deal_q, gap=("C", pd.Period("2022Q1", freq="Q")))
    return raw, mergers, truth


def clean_panel(raw: pd.DataFrame) -> pd.DataFrame:
    # your code here
    raise NotImplementedError


def check():
    raw, mergers, truth = make_panel()
    print(raw.sort_values(["bank_id", "report_date"]).head(8))
    c = clean_panel(raw)
    assert not c.duplicated(["bank_id", "quarter"]).any(), "duplicates remain"
    gap = c[(c.bank_id == "C") & (c.quarter == pd.Period("2022Q1", freq="Q"))]
    assert len(gap) == 1 and gap.total_deposits.isna().all(), "missing quarter should be a NaN row"
    after = c[(c.bank_id == "C") & (c.quarter == pd.Period("2022Q2", freq="Q"))]
    assert after.dep_qoq.isna().all(), "growth bridged a gap"
    assert np.allclose(c[c.bank_id == "C"].dep_qoq.dropna(), 0.01), "C grows 1%/qtr organically"
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p1_bank_panel_cleaning.py`](solutions/p1_bank_panel_cleaning.py)):**

```python
# file: interview-kit/solutions/p1_bank_panel_cleaning.py
"""
Problem 1 (warm-up, ~5-8 min): clean a call-report-like quarterly bank panel.

Tasks
  1. Keep only the latest filing per (bank_id, quarter) (restatements).
  2. Put every bank on a complete quarterly grid so missing quarters are NaN,
     not silently skipped.
  3. Convert YTD-cumulative net interest income (NII) to quarterly NII.
  4. Compute QoQ and YoY deposit growth without bridging gaps.
  5. Merger-adjust: build pro-forma (organic) deposit growth for acquirers by
     adding the target's history to the acquirer before the deal quarter.

Runs on pandas 2.x and 3.x. Only numpy + pandas required.
"""
import numpy as np
import pandas as pd


# ----------------------------------------------------------------------------
# Synthetic data generator
# ----------------------------------------------------------------------------
def make_panel(seed: int = 0):
    """Return (raw, mergers, truth).

    raw      : long panel with columns bank_id, report_date, filed_at,
               total_deposits, nii_ytd   (one bad duplicate row, one gap)
    mergers  : DataFrame acquirer, target, deal_quarter (Period)
    truth    : dict of known quantities used by the asserts
    """
    rng = np.random.default_rng(seed)
    quarters = pd.period_range("2019Q1", "2023Q4", freq="Q")
    rows = []
    g = {"A": 0.02, "B": 0.02, "C": 0.01}        # constant organic QoQ growth
    d0 = {"A": 1000.0, "B": 400.0, "C": 250.0}   # starting deposits
    q_nii = {"A": 10.0, "B": 4.0, "C": 2.5}      # constant quarterly NII
    deal_q = pd.Period("2021Q3", freq="Q")        # A acquires B in 2021Q3
    for bank in ["A", "B", "C"]:
        dep = d0[bank]
        for i, q in enumerate(quarters):
            if i > 0:
                dep *= 1 + g[bank]
            if bank == "B" and q >= deal_q:
                break                              # B stops filing at the deal
            rows.append(dict(bank_id=bank, report_date=q.end_time.normalize(),
                             filed_at=q.end_time.normalize() + pd.Timedelta(days=30),
                             total_deposits=dep, nii_ytd=q_nii[bank] * q.quarter))
    raw = pd.DataFrame(rows)
    # After the deal, A's reported deposits include B's book.
    b_dep = {q: d0["B"] * (1 + g["B"]) ** i for i, q in enumerate(quarters)}
    mask = (raw.bank_id == "A") & (raw.report_date.dt.to_period("Q") >= deal_q)
    raw.loc[mask, "total_deposits"] += raw.loc[mask, "report_date"].dt.to_period("Q").map(b_dep)
    # Restatement: an early wrong filing for C 2020Q2, later corrected.
    bad = raw[(raw.bank_id == "C") & (raw.report_date == pd.Timestamp("2020-06-30"))].copy()
    bad["total_deposits"] *= 1.5
    bad["filed_at"] -= pd.Timedelta(days=20)          # filed earlier -> stale
    raw = pd.concat([raw, bad], ignore_index=True)
    # Missing quarter: C did not file 2022Q1.
    raw = raw[~((raw.bank_id == "C") & (raw.report_date == pd.Timestamp("2022-03-31")))]
    raw = raw.sample(frac=1.0, random_state=seed).reset_index(drop=True)  # shuffle
    mergers = pd.DataFrame({"acquirer": ["A"], "target": ["B"], "deal_quarter": [deal_q]})
    truth = dict(g=g, q_nii=q_nii, deal_q=deal_q, gap=("C", pd.Period("2022Q1", freq="Q")))
    return raw, mergers, truth


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def clean_panel(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["quarter"] = df["report_date"].dt.to_period("Q")
    # 1. latest filing wins
    df = (df.sort_values(["bank_id", "quarter", "filed_at"])
            .drop_duplicates(["bank_id", "quarter"], keep="last"))
    # 2. complete grid per bank, from its first to its last filing
    def _reindex(g):
        full = pd.period_range(g["quarter"].min(), g["quarter"].max(), freq="Q")
        return g.set_index("quarter").reindex(full)
    out = []
    for bank, g in df.groupby("bank_id", sort=True):
        r = _reindex(g)
        r["bank_id"] = bank
        out.append(r)
    df = pd.concat(out)
    df.index.name = "quarter"
    df = df.reset_index()[["bank_id", "quarter", "total_deposits", "nii_ytd"]]
    # 3. YTD -> quarterly: Q1 is as reported; Qn = YTD_n - YTD_{n-1}, same year.
    df["year"] = df["quarter"].dt.year
    prev_ytd = df.groupby(["bank_id", "year"])["nii_ytd"].shift(1)
    is_q1 = df["quarter"].dt.quarter == 1
    df["nii_q"] = np.where(is_q1, df["nii_ytd"], df["nii_ytd"] - prev_ytd)
    # 4. growth on the complete grid; shift() never bridges a NaN gap
    gb = df.groupby("bank_id")["total_deposits"]
    df["dep_qoq"] = df["total_deposits"] / gb.shift(1) - 1
    df["dep_yoy"] = df["total_deposits"] / gb.shift(4) - 1
    return df.drop(columns="year")


def pro_forma(clean: pd.DataFrame, mergers: pd.DataFrame) -> pd.DataFrame:
    """Organic growth: before the deal, acquirer history = acquirer + target."""
    df = clean.copy()
    df["pf_id"] = df["bank_id"]
    for m in mergers.itertuples(index=False):
        tgt = (df["bank_id"] == m.target) & (df["quarter"] < m.deal_quarter)
        df.loc[tgt, "pf_id"] = m.acquirer
    pf = (df.groupby(["pf_id", "quarter"], as_index=False)["total_deposits"]
            .sum(min_count=1)                       # all-NaN stays NaN, not 0
            .rename(columns={"pf_id": "bank_id"}))
    # drop targets as stand-alone entities (they are folded into acquirers)
    pf = pf[~pf["bank_id"].isin(mergers["target"])]
    pf = pf.sort_values(["bank_id", "quarter"])
    gb = pf.groupby("bank_id")["total_deposits"]
    pf["pf_dep_qoq"] = pf["total_deposits"] / gb.shift(1) - 1
    pf["pf_dep_yoy"] = pf["total_deposits"] / gb.shift(4) - 1
    return pf


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    raw, mergers, truth = make_panel()
    c = clean_panel(raw)
    # one row per bank-quarter, and the gap is present as a NaN row
    assert not c.duplicated(["bank_id", "quarter"]).any()
    bank, gq = truth["gap"]
    gap_row = c[(c.bank_id == bank) & (c.quarter == gq)]
    assert len(gap_row) == 1 and gap_row["total_deposits"].isna().all()
    # growth right after the gap is NaN (not bridged across two quarters)
    after = c[(c.bank_id == bank) & (c.quarter == gq + 1)]
    assert after["dep_qoq"].isna().all()
    # restatement resolved: C's QoQ growth equals 1% wherever defined
    cq = c[(c.bank_id == "C")]["dep_qoq"].dropna()
    assert np.allclose(cq, truth["g"]["C"])
    # quarterly NII is constant where defined
    for b, v in truth["q_nii"].items():
        s = c[c.bank_id == b]["nii_q"].dropna()
        assert np.allclose(s, v), b
    # raw growth for A jumps at the deal; pro-forma growth does not
    dq = truth["deal_q"]
    raw_jump = c[(c.bank_id == "A") & (c.quarter == dq)]["dep_qoq"].iloc[0]
    assert raw_jump > 0.3
    pf = pro_forma(c, mergers)
    a = pf[pf.bank_id == "A"]["pf_dep_qoq"].dropna()
    assert np.allclose(a, 0.02), a.describe()
    assert np.allclose(pf[pf.bank_id == "A"]["pf_dep_yoy"].dropna(), 1.02 ** 4 - 1)
    assert "B" not in set(pf.bank_id)
    # pitfall demo: pct_change behaviour differs by pandas version; shift() is explicit
    s = pd.Series([100.0, np.nan, 102.0])
    assert np.isnan((s / s.shift(1) - 1).iloc[2])
    print("p1 OK  | pandas", pd.__version__, "| raw A jump at deal:", round(raw_jump, 3))
    return c, pf


if __name__ == "__main__":
    c, pf = _tests()
    print(c[c.bank_id == "C"].head(6).to_string(index=False))
```

**Hints (tiered):**

1. "What makes a row unique? What should happen when two rows share that key?" (Sort by `filed_at`, then `drop_duplicates(keep="last")`.)
2. "If bank C skipped 2022Q1, what does `groupby('bank_id').shift(1)` give you for 2022Q2?" (The 2021Q4 value, which is wrong: growth over two quarters labeled as one.)
3. "Build the full quarter range per bank with `pd.period_range(min, max, freq='Q')` and `reindex` onto it; then `shift` is safe." (This is the key move, so give it at 0:19 if the candidate is stuck.)

**Follow-ups (if fast, or verbal):**

- YTD → quarterly: $NII^{q}_{t} = NII^{YTD}_{t} - NII^{YTD}_{t-1}$ within the calendar year, and Q1 is as reported. What breaks if Q2 is missing? (Q3 can't be computed either, so it should be NaN, not Q3 YTD minus Q1 YTD labeled as one quarter.)
- Mergers: why does A's raw QoQ jump to about 43% at 2021Q3? How do you get organic growth? (Pro-forma: add the target's history to the acquirer's before the deal date, or drop the deal quarter, or use a constant-sample panel.) Which would you show the business?
- "Real Y-9C data: what other traps?" Definition and schedule changes (periodic FR Y-9C form revisions that redefine line items), holding-company vs bank-level reporting, survivorship if you only keep current filers, and seasonality in deposits.

**Common mistakes / red flags:**

- Using `pct_change()` directly on the unbalanced panel without `groupby`, so growth leaks *across banks*.
- Not noticing the gap, or "fixing" it with `ffill()`, which manufactures 0% growth and then a two-quarter jump.
- Keeping the first filing (`keep="first"`) without sorting by `filed_at`.
- Iterating over rows with `iterrows` for everything (a slow-Python signal; note it for the "own Python" score).
- *Red flag:* can't explain why the growth right after a gap must be NaN.

**Strong vs weak:**

- *Strong:* sorts, dedupes, reindexes per bank, uses `groupby(...).shift()`, and asks unprompted, "are income items YTD?" or "any M&A in here?" Finishes core in under 5 minutes.
- *Weak:* gets QoQ but bridges the gap; needs Hint 3 and still struggles with `reindex`; no instinct about YTD.

**Rubric:** **4** core correct in under 5 min and raises YTD/merger issues unprompted · **3** core correct with ≤ 1 hint · **2** dedup and growth right but the gap is bridged until Hint 3 · **1** can't produce clean growth with hints.

## P2. Challenger vs naive: rolling-origin backtest + Diebold–Mariano (core, 13 min)

**Why this problem:** challenger-vs-benchmark backtesting is the bread and butter of model validation on a bank planning team. Many candidates have run an expanding-window OOS test against an AR benchmark in research; we want to see that the candidate can *write* it, not just describe it, and that the no-look-ahead line is deliberate.

**Prompt to paste:**

> Quarterly data: `y` is deposit growth (%), `x` is the change in the unemployment rate. The challenger is an ARX(1): $y_{t+1} = c + \phi y_t + \beta x_t + e$. The benchmarks are a random walk ($\hat y_{t+1} = y_t$) and the historical mean. Starting at origin 60, run an expanding-window backtest: at each origin, fit using only data available at that origin, forecast one quarter ahead, and store actuals and forecasts. Report RMSE and MAE per model, then write a Diebold–Mariano test comparing the ARX to the random walk.

**Starter ([`starters/p2_starter.py`](starters/p2_starter.py)):**

```python
# file: interview-kit/starters/p2_starter.py
"""
Challenger vs naive: expanding-window backtest with no look-ahead. ~13 minutes.

df: quarterly, columns y (deposit growth, %) and x (change in unemployment, pp).
Challenger ARX(1):   y_{t+1} = c + phi * y_t + beta * x_t + e
Benchmarks:          random walk (forecast y_{t+1} = y_t), historical mean.

1. backtest(df, first_origin=60, h=1): for each origin t >= first_origin,
   fit the ARX using ONLY data dated <= t, forecast y_{t+1}, store
   actual / arx / rw / mean. Return a DataFrame indexed by target date.
2. Report RMSE and MAE for each model.
3. diebold_mariano(e1, e2, h): DM statistic and p-value (squared-error loss).
Use numpy for OLS if you like; statsmodels is available.
"""
import numpy as np
import pandas as pd


def make_data(T: int = 160, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x = np.zeros(T)
    y = np.zeros(T)
    for t in range(1, T):
        x[t] = 0.5 * x[t - 1] + rng.normal(0, 0.3)
        # unemployment rising today lowers deposit growth next quarter
        y[t] = 0.4 + 0.5 * y[t - 1] - 1.2 * x[t - 1] + rng.normal(0, 0.5)
    idx = pd.period_range("1985Q1", periods=T, freq="Q")
    return pd.DataFrame({"y": y, "x": x}, index=idx)


def backtest(df: pd.DataFrame, first_origin: int = 60, h: int = 1) -> pd.DataFrame:
    raise NotImplementedError


def diebold_mariano(e1, e2, h: int = 1):
    """Return (stat, p_value). Negative stat => model 1 more accurate."""
    raise NotImplementedError


def check():
    df = make_data()
    bt = backtest(df, first_origin=60, h=1)
    assert {"actual", "arx", "rw", "mean"} <= set(bt.columns)
    # look-ahead guard: overwrite the future; forecasts made before it must not move
    df_bad = df.copy(); df_bad.iloc[81:] = 999.0
    bt_bad = backtest(df_bad.iloc[:82], first_origin=60, h=1)
    assert np.allclose(bt_bad.arx.to_numpy(), bt.arx.iloc[:len(bt_bad)].to_numpy()), "look-ahead!"
    rmse = {m: np.sqrt(((bt.actual - bt[m]) ** 2).mean()) for m in ["arx", "rw", "mean"]}
    print(rmse)
    print(diebold_mariano(bt.actual - bt.arx, bt.actual - bt.rw, h=1))
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p2_rolling_backtest_dm.py`](solutions/p2_rolling_backtest_dm.py)):**

```python
# file: interview-kit/solutions/p2_rolling_backtest_dm.py
"""
Problem 2 (core, ~12-15 min): expanding-window (rolling-origin) backtest of an
ARX challenger vs naive benchmarks, with RMSE/MAE and a Diebold-Mariano test.
No look-ahead: at origin t the model only sees data dated <= t.

y_t : quarterly deposit growth (%), x_t : change in the unemployment rate (pp)
Challenger: y_{t+h} = c + sum_j phi_j y_{t+1-j} + beta x_t + e   (direct h-step)
Benchmarks: random walk (y_t) and historical mean (mean of y_1..y_t)

Needs numpy + scipy (for the t/normal CDF). statsmodels used only for a cross-check.
"""
import numpy as np
import pandas as pd

try:
    from scipy import stats
except ImportError:          # fallback: normal CDF via math.erf
    stats = None
import math


# ----------------------------------------------------------------------------
# Synthetic data
# ----------------------------------------------------------------------------
def make_data(T: int = 160, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x = np.zeros(T)
    y = np.zeros(T)
    for t in range(1, T):
        x[t] = 0.5 * x[t - 1] + rng.normal(0, 0.3)
        # unemployment rising today lowers deposit growth next quarter
        y[t] = 0.4 + 0.5 * y[t - 1] - 1.2 * x[t - 1] + rng.normal(0, 0.5)
    idx = pd.period_range("1985Q1", periods=T, freq="Q")
    return pd.DataFrame({"y": y, "x": x}, index=idx)


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """OLS coefficients via least squares (numerically safer than inv(X'X))."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def design(df: pd.DataFrame, p: int, h: int, use_x: bool = True):
    """Rows t with regressors dated <= t and target y_{t+h}.
    Returns (X, target, X_last) where X_last is the regressor row at the last
    date (used for the forecast, its target is unknown)."""
    cols = {"const": np.ones(len(df))}
    for j in range(p):
        cols[f"y_l{j}"] = df["y"].shift(j).to_numpy()
    if use_x:
        cols["x_l0"] = df["x"].to_numpy()
    Z = pd.DataFrame(cols, index=df.index)
    target = df["y"].shift(-h)
    ok = Z.notna().all(axis=1) & target.notna()
    return Z[ok].to_numpy(), target[ok].to_numpy(), Z.iloc[-1].to_numpy()


def forecast_at_origin(hist: pd.DataFrame, p: int, h: int, use_x=True) -> float:
    """hist contains ONLY data up to the forecast origin. Fit and forecast."""
    X, yt, x_last = design(hist, p, h, use_x)
    b = ols(X, yt)
    return float(x_last @ b)


def backtest(df: pd.DataFrame, first_origin: int, h: int = 1, p: int = 1):
    """Expanding window. Origin t uses df.iloc[:t+1]; target is y at t+h."""
    recs = []
    for t in range(first_origin, len(df) - h):
        hist = df.iloc[: t + 1]                      # <- the no-look-ahead line
        recs.append(dict(origin=df.index[t], target_date=df.index[t + h],
                         actual=df["y"].iloc[t + h],
                         arx=forecast_at_origin(hist, p, h, True),
                         ar=forecast_at_origin(hist, p, h, False),
                         rw=hist["y"].iloc[-1],
                         mean=hist["y"].mean()))
    return pd.DataFrame(recs).set_index("target_date")


def error_table(bt: pd.DataFrame, models=("arx", "ar", "rw", "mean")) -> pd.DataFrame:
    out = {}
    for m in models:
        e = bt["actual"] - bt[m]
        out[m] = {"RMSE": np.sqrt(np.mean(e ** 2)), "MAE": np.mean(np.abs(e))}
    return pd.DataFrame(out).T


def _norm_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def diebold_mariano(e1, e2, h: int = 1, loss: str = "se", hln: bool = True):
    """DM test of equal predictive accuracy. d_t = L(e1_t) - L(e2_t).
    Negative stat => model 1 more accurate. Long-run variance uses
    autocovariances up to lag h-1 (rectangular, as in DM 1995), with
    a Bartlett fallback if that is non-positive. HLN (1997) small-sample
    correction and t_{n-1} reference distribution when hln=True."""
    e1, e2 = np.asarray(e1), np.asarray(e2)
    d = e1 ** 2 - e2 ** 2 if loss == "se" else np.abs(e1) - np.abs(e2)
    n = len(d)
    dbar = d.mean()
    dc = d - dbar
    gam = [dc @ dc / n] + [dc[k:] @ dc[:-k] / n for k in range(1, h)]
    lrv = gam[0] + 2 * sum(gam[1:])
    if lrv <= 0:  # Bartlett weights guarantee positivity
        lrv = gam[0] + 2 * sum((1 - k / h) * gam[k] for k in range(1, h))
    stat = dbar / math.sqrt(lrv / n)
    if hln:
        stat *= math.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
        p = 2 * (1 - stats.t.cdf(abs(stat), df=n - 1)) if stats else 2 * (1 - _norm_cdf(abs(stat)))
    else:
        p = 2 * (1 - _norm_cdf(abs(stat)))
    return stat, p


def clark_west(actual, f_small, f_big):
    """Clark-West (2007) for nested models: big model nests small one.
    One-sided: H1 big model better. Adjusts for the noise from estimating
    parameters that are zero under the null."""
    actual, f_small, f_big = map(np.asarray, (actual, f_small, f_big))
    f = (actual - f_small) ** 2 - ((actual - f_big) ** 2 - (f_small - f_big) ** 2)
    n = len(f)
    stat = f.mean() / (f.std(ddof=1) / math.sqrt(n))
    p = 1 - (stats.norm.cdf(stat) if stats else _norm_cdf(stat))
    return stat, p


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    df = make_data()
    bt = backtest(df, first_origin=60, h=1, p=1)
    tab = error_table(bt)
    # 1. look-ahead guard: scrambling the future must not change any forecast
    t0 = 80
    f_true = forecast_at_origin(df.iloc[: t0 + 1], 1, 1)
    df_bad = df.copy()
    df_bad.iloc[t0 + 1:] = 999.0
    f_bad = forecast_at_origin(df_bad.iloc[: t0 + 1], 1, 1)
    assert f_true == f_bad
    bt_bad = backtest(df_bad.iloc[: t0 + 2], first_origin=60)  # last target = t0+1
    assert np.allclose(bt_bad["arx"].to_numpy(), bt["arx"].iloc[: len(bt_bad)].to_numpy())
    # 2. the true DGP is ARX, so the challenger should win on RMSE
    assert tab.loc["arx", "RMSE"] < tab.loc["rw", "RMSE"]
    assert tab.loc["arx", "RMSE"] < tab.loc["mean", "RMSE"]
    e = {m: bt["actual"] - bt[m] for m in ["arx", "ar", "rw", "mean"]}
    dm_rw = diebold_mariano(e["arx"], e["rw"], h=1)
    assert dm_rw[0] < 0 and dm_rw[1] < 0.05, dm_rw
    # 3. DM is antisymmetric in the two models
    s1, _ = diebold_mariano(e["arx"], e["rw"], h=2)
    s2, _ = diebold_mariano(e["rw"], e["arx"], h=2)
    assert np.isclose(s1, -s2)
    # 4. OLS cross-check vs statsmodels if available
    X, yt, _ = design(df, 2, 1)
    try:
        import statsmodels.api as sm
        assert np.allclose(sm.OLS(yt, X).fit().params, ols(X, yt))
        sm_ok = True
    except ImportError:
        sm_ok = False
    # 5. Clark-West: ARX nests AR(1); should reject in favour of ARX
    cw = clark_west(bt["actual"], bt["ar"], bt["arx"])
    assert cw[0] > 0 and cw[1] < 0.05, cw
    # 6. h = 4 direct forecasts also run and line up
    bt4 = backtest(df, first_origin=60, h=4)
    assert (bt4["origin"].apply(lambda p: p + 4) == bt4.index).all()
    print("p2 OK  | n_oos =", len(bt), "| statsmodels cross-check:", sm_ok)
    print(tab.round(3).to_string())
    print("DM arx vs rw: stat=%.2f p=%.4f | CW arx vs ar: stat=%.2f p=%.4f" % (*dm_rw, *cw))


if __name__ == "__main__":
    _tests()
```

**Hints (tiered):**

1. "At origin $t$, which observations are you allowed to touch? Write that as one slicing line before anything else." (`hist = df.iloc[:t+1]`.)
2. "Build the regression as rows $(1, y_t, x_t) \to y_{t+1}$ inside `hist`. The last row of `hist` has regressors but no target; that's the row you forecast from." If the candidate is still stuck at 0:25, paste `design()` from the reference.
3. DM: "Take the loss differential $d_t = e_{1,t}^2 - e_{2,t}^2$, then a t-test on its mean using a long-run variance (for h = 1 the plain variance is fine)." Formula in [refresher §3.5](refresher.md#35-dieboldmariano-and-clarkwest).

**Follow-ups:**

- "The ARX nests the historical-mean model. Is DM the right test?" (No. Under the null, the larger model's estimation noise biases its MSE upward, so DM undersizes. Use **Clark–West**; it's in the reference solution.)
- "Make it h = 4. Direct or iterated? What changes in DM?" (With direct forecasts the regression target shifts by h. Errors are MA(h−1), so the long-run variance needs h−1 autocovariances, plus the HLN correction.)
- "Your x is lagged. What if the model used contemporaneous $x_{t+1}$?" (Then the backtest needs a forecast of $x$. Using the realized value is an **oracle-regressor** look-ahead: fine for a conditional/scenario evaluation, wrong for an unconditional one. This ties straight into P3.)
- "What else leaks the future in real life?" (Full-sample standardization or PCA, HP filters, seasonal adjustment, revised data vintages, picking the lag length on the full sample.)
- "With n ≈ 100 OOS points, how would you present a 10% RMSE improvement to the business?" (A small-sample caveat, the DM/CW p-value, stability across split points.)

**Common mistakes / red flags:**

- Fitting once on the full sample and then "forecasting" in-sample: the cardinal sin. **Red flag** if the candidate doesn't see it when asked "where could the future leak in?"
- Off-by-one alignment: target $y_{t+1}$ paired with $x_{t+1}$, or the forecast compared against $y_t$.
- The historical mean computed over the full sample instead of `hist`.
- `np.linalg.inv(X.T @ X)` is fine here, but if the candidate does it, ask why `lstsq` is usually preferred (conditioning).
- DM computed on raw errors instead of the loss differential; quoting a p-value without saying which sign means "better."

**Strong vs weak:**

- *Strong:* writes the slicing line first and *says* why; small clean functions; adds a quick sanity check unprompted (e.g. "the RW error equals $\Delta y$"); raises Clark–West for nested models unprompted; notes that 99 OOS points is modest.
- *Weak:* a working loop only after hints; can't write DM without the formula; no awareness of nested-model issues even with a research background in forecasting.

**Rubric:** **4** correct, leak-free backtest + DM in about 13 min, raises CW/oracle-regressor issues unprompted · **3** correct backtest and metrics; DM needs a nudge · **2** backtest works only after Hint 2; DM verbal only · **1** look-ahead the candidate doesn't catch, or no working loop.

## P3. Conditional scenario forecast: deposits under a CCAR-style path (core, main event, 17 min)

**Why this problem:** scenario work is about turning a scenario (e.g. the Fed's Severely Adverse paths for unemployment and the 10y yield) into a 9-quarter path for a bank line. **Conditional forecasting** is often the least-proven skill on a CV. This is the most important problem in the interview.

**Prompt to paste:**

> `hist` is quarterly history: unemployment rate, 10y yield, deposit growth (% QoQ) and the deposit level. `scenarios` has two 9-quarter paths for unemployment and the 10y yield, `baseline` and `severely_adverse`, starting the quarter after the last history date. (1) Estimate $g_t = c + a\,g_{t-1} + b_1 \Delta UR_t + b_2 \Delta Y10_t + e_t$ by OLS. (2) Project deposit growth over the 9 quarters given each path, and turn it into a deposit level path. (3) Add 5–95% bands. (4) Make a stress version: severely adverse plus an idiosyncratic outflow of −3pp of growth in quarter 1, halving each quarter after.

**Starter ([`starters/p3_starter.py`](starters/p3_starter.py)):**

```python
# file: interview-kit/starters/p3_starter.py
"""
Conditional scenario forecast (CCAR-style). ~17 minutes. The main event.

hist: quarterly ur (unemployment %), y10 (10y yield %), g (deposit growth, % QoQ),
deposits (level). scenarios: {"baseline", "severely_adverse"} -> 9-quarter
DataFrames with imposed paths for ur and y10 (first row = first forecast quarter).

1. fit_arx(hist): OLS of  g_t = c + a g_{t-1} + b1 dUR_t + b2 dY10_t + e_t.
   Return (beta, residuals).
2. project(beta, hist, path): iterate g over the 9 quarters given the imposed
   paths (careful with the first difference at the jump-off quarter) and turn
   it into a deposit LEVEL path.
3. Run baseline and severely adverse; add 5%/95% bands (your choice of method).
4. Stress version: on top of severely adverse, add a deposit outflow of -3pp
   of growth in quarter 1, halving each quarter after.
"""
import numpy as np
import pandas as pd


H = 9


TRUE = dict(c=1.0, a=0.4, b1=-1.5, b2=0.8, sigma=0.4)


def make_history(T: int = 120, seed: int = 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ur = np.empty(T); y10 = np.empty(T); g = np.empty(T)
    ur[0], y10[0], g[0] = 5.0, 4.0, 1.5
    for t in range(1, T):
        ur[t] = 0.3 + 0.95 * ur[t - 1] + rng.normal(0, 0.25)
        y10[t] = 0.1 + 0.97 * y10[t - 1] + rng.normal(0, 0.25)
        g[t] = (TRUE["c"] + TRUE["a"] * g[t - 1] + TRUE["b1"] * (ur[t] - ur[t - 1])
                + TRUE["b2"] * (y10[t] - y10[t - 1]) + rng.normal(0, TRUE["sigma"]))
    idx = pd.period_range("1996Q1", periods=T, freq="Q")
    dep = 1000 * np.cumprod(1 + g / 100)
    return pd.DataFrame({"ur": ur, "y10": y10, "g": g, "deposits": dep}, index=idx)


def make_scenarios(last: pd.Series, start: pd.Period) -> dict:
    """Return {'baseline': df, 'severely_adverse': df} with UR and Y10 paths."""
    q = pd.period_range(start, periods=H, freq="Q")
    base = pd.DataFrame({"ur": np.linspace(last.ur, last.ur + 0.2, H),
                         "y10": np.linspace(last.y10, last.y10 - 0.1, H)}, index=q)
    # UR jumps ~5.5pp to a peak in quarter 6 then eases; Y10 falls ~2.5pp fast
    peak = last.ur + 5.5
    ur_sa = np.concatenate([np.linspace(last.ur, peak, 7)[1:], np.linspace(peak, peak - 1.0, 4)[1:]])
    y10_sa = np.maximum(last.y10 - 2.5 * (1 - np.exp(-0.8 * np.arange(1, H + 1))), 0.5)
    sa = pd.DataFrame({"ur": ur_sa, "y10": y10_sa}, index=q)
    return {"baseline": base, "severely_adverse": sa}


def fit_arx(hist: pd.DataFrame):
    raise NotImplementedError


def project(beta, hist: pd.DataFrame, path: pd.DataFrame):
    """Return a DataFrame indexed like path with columns g and deposits."""
    raise NotImplementedError


def check():
    hist = make_history()
    sc = make_scenarios(hist.iloc[-1], hist.index[-1] + 1)
    print(hist.tail(3)); print(sc["severely_adverse"].round(2))
    beta, resid = fit_arx(hist)
    print("beta", np.round(beta, 3))           # truth: c=1.0, a=0.4, b1=-1.5, b2=0.8
    base = project(beta, hist, sc["baseline"])
    sa = project(beta, hist, sc["severely_adverse"])
    assert len(sa) == H and (sa.deposits < base.deposits).all()
    print(pd.DataFrame({"base": base.deposits, "SA": sa.deposits}).round(1))
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p3_conditional_scenario_forecast.py`](solutions/p3_conditional_scenario_forecast.py)):**

```python
# file: interview-kit/solutions/p3_conditional_scenario_forecast.py
"""
Problem 3 (main event, ~15-20 min): conditional scenario forecast.

Part A (core). Estimate an ARX for quarterly deposit growth g_t (%):
    g_t = c + a g_{t-1} + b1 dUR_t + b2 dY10_t + e_t
Impose a 9-quarter path for the unemployment rate (UR) and 10y yield (Y10)
(CCAR-style Baseline and Severely Adverse), iterate g forward, cumulate to a
deposit LEVEL path, and give 5/95% bands by residual bootstrap.
Part B (stress). Severely Adverse paths plus an idiosyncratic outflow overlay.
Part C (extension). VAR(1) in (UR, Y10, g) treating the paths as conditions on
endogenous variables: Waggoner-Zha / conditional-mean shocks via min-norm.

Scenario paths below are ILLUSTRATIVE, shaped like a Fed Severely Adverse path,
not the published numbers. Needs numpy + pandas only.
"""
import numpy as np
import pandas as pd

H = 9  # CCAR horizon in quarters


# ----------------------------------------------------------------------------
# Synthetic history and scenarios
# ----------------------------------------------------------------------------
TRUE = dict(c=1.0, a=0.4, b1=-1.5, b2=0.8, sigma=0.4)


def make_history(T: int = 120, seed: int = 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ur = np.empty(T); y10 = np.empty(T); g = np.empty(T)
    ur[0], y10[0], g[0] = 5.0, 4.0, 1.5
    for t in range(1, T):
        ur[t] = 0.3 + 0.95 * ur[t - 1] + rng.normal(0, 0.25)
        y10[t] = 0.1 + 0.97 * y10[t - 1] + rng.normal(0, 0.25)
        g[t] = (TRUE["c"] + TRUE["a"] * g[t - 1] + TRUE["b1"] * (ur[t] - ur[t - 1])
                + TRUE["b2"] * (y10[t] - y10[t - 1]) + rng.normal(0, TRUE["sigma"]))
    idx = pd.period_range("1996Q1", periods=T, freq="Q")
    dep = 1000 * np.cumprod(1 + g / 100)
    return pd.DataFrame({"ur": ur, "y10": y10, "g": g, "deposits": dep}, index=idx)


def make_scenarios(last: pd.Series, start: pd.Period) -> dict:
    """Return {'baseline': df, 'severely_adverse': df} with UR and Y10 paths."""
    q = pd.period_range(start, periods=H, freq="Q")
    base = pd.DataFrame({"ur": np.linspace(last.ur, last.ur + 0.2, H),
                         "y10": np.linspace(last.y10, last.y10 - 0.1, H)}, index=q)
    # UR jumps ~5.5pp to a peak in quarter 6 then eases; Y10 falls ~2.5pp fast
    peak = last.ur + 5.5
    ur_sa = np.concatenate([np.linspace(last.ur, peak, 7)[1:], np.linspace(peak, peak - 1.0, 4)[1:]])
    y10_sa = np.maximum(last.y10 - 2.5 * (1 - np.exp(-0.8 * np.arange(1, H + 1))), 0.5)
    sa = pd.DataFrame({"ur": ur_sa, "y10": y10_sa}, index=q)
    return {"baseline": base, "severely_adverse": sa}


# ----------------------------------------------------------------------------
# Part A: ARX estimated by OLS, path forecast with bootstrap bands
# ----------------------------------------------------------------------------
def fit_arx(hist: pd.DataFrame):
    d = pd.DataFrame({"g": hist.g, "g_l1": hist.g.shift(1),
                      "dur": hist.ur.diff(), "dy10": hist.y10.diff()}).dropna()
    X = np.column_stack([np.ones(len(d)), d.g_l1, d.dur, d.dy10])
    beta, *_ = np.linalg.lstsq(X, d.g.to_numpy(), rcond=None)
    resid = d.g.to_numpy() - X @ beta
    return beta, resid


def project(beta, hist: pd.DataFrame, path: pd.DataFrame, shocks=None,
            overlay=None) -> pd.DataFrame:
    """Iterate the ARX over the imposed path. shocks: (n_sims, H) residual
    draws, or None for the mean path. overlay: (H,) add-on to growth (pp)."""
    c, a, b1, b2 = beta
    dur = np.diff(np.r_[hist.ur.iloc[-1], path.ur.to_numpy()])     # first diff vs jump-off
    dy10 = np.diff(np.r_[hist.y10.iloc[-1], path.y10.to_numpy()])
    eps = np.zeros((1, H)) if shocks is None else shocks
    ov = np.zeros(H) if overlay is None else np.asarray(overlay)
    g = np.empty_like(eps)
    g_prev = np.full(eps.shape[0], hist.g.iloc[-1])
    for h in range(H):                                             # recursion in g
        g[:, h] = c + a * g_prev + b1 * dur[h] + b2 * dy10[h] + ov[h] + eps[:, h]
        g_prev = g[:, h]
    level = hist.deposits.iloc[-1] * np.cumprod(1 + g / 100, axis=1)
    return g, level


def scenario_forecast(hist, path, n_sims=4000, seed=0, overlay=None):
    beta, resid = fit_arx(hist)
    g_mean, lvl_mean = project(beta, hist, path, overlay=overlay)
    rng = np.random.default_rng(seed)
    draws = rng.choice(resid, size=(n_sims, H), replace=True)      # residual bootstrap
    _, lvl_sims = project(beta, hist, path, shocks=draws, overlay=overlay)
    out = pd.DataFrame({"g": g_mean[0], "deposits": lvl_mean[0],
                        "p05": np.percentile(lvl_sims, 5, axis=0),
                        "p95": np.percentile(lvl_sims, 95, axis=0)}, index=path.index)
    return out, beta


# ----------------------------------------------------------------------------
# Part C: VAR(1) conditional forecast (Waggoner-Zha, hard conditions)
# ----------------------------------------------------------------------------
def fit_var1(Y: np.ndarray):
    X = np.column_stack([np.ones(len(Y) - 1), Y[:-1]])
    B, *_ = np.linalg.lstsq(X, Y[1:], rcond=None)
    U = Y[1:] - X @ B
    Sigma = U.T @ U / (len(U) - X.shape[1])
    return B[0], B[1:].T, Sigma          # c, A (k x k), Sigma


def var_conditional(c, A, Sigma, y_T, cond_idx, cond_path):
    """Mean of y_{T+1..T+H} given y_T and y_{T+h}[cond_idx] = cond_path[h].
    Shocks eps ~ N(0, I) with u = P eps (Cholesky). Deviations from the
    unconditional forecast are linear in eps: dev = M eps. The conditional
    mean of eps given R eps = r is the min-norm solution R'(RR')^-1 r."""
    k = len(y_T); Hc = cond_path.shape[0]
    P = np.linalg.cholesky(Sigma)
    # unconditional path
    yhat = np.empty((Hc, k)); y = y_T.copy()
    for h in range(Hc):
        y = c + A @ y; yhat[h] = y
    # impulse matrix: block (h, j) = A^{h-j} P for j <= h
    M = np.zeros((Hc * k, Hc * k))
    Apow = [np.linalg.matrix_power(A, n) for n in range(Hc)]
    for h in range(Hc):
        for j in range(h + 1):
            M[h * k:(h + 1) * k, j * k:(j + 1) * k] = Apow[h - j] @ P
    rows = [h * k + i for h in range(Hc) for i in cond_idx]
    R = M[rows]
    r = (cond_path - yhat[:, cond_idx]).ravel()
    eps = R.T @ np.linalg.solve(R @ R.T, r)
    ycond = yhat + (M @ eps).reshape(Hc, k)
    # conditional covariance of the path (for bands)
    V = np.eye(Hc * k) - R.T @ np.linalg.solve(R @ R.T, R)
    cov = M @ V @ M.T
    return ycond, yhat, cov


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    hist = make_history()
    sc = make_scenarios(hist.iloc[-1], hist.index[-1] + 1)
    base, beta = scenario_forecast(hist, sc["baseline"])
    sa, _ = scenario_forecast(hist, sc["severely_adverse"])
    # parameters recovered roughly
    assert np.allclose(beta, [TRUE[k] for k in ("c", "a", "b1", "b2")], atol=0.35), beta
    # rising UR lowers deposits: SA below baseline at every horizon
    assert (sa.deposits < base.deposits).all()
    # bands bracket the mean path and widen with horizon
    assert ((base.p05 < base.deposits) & (base.deposits < base.p95)).all()
    width = base.p95 - base.p05
    assert width.iloc[-1] > width.iloc[0]
    # the mean path is the deterministic recursion: check quarter 1 by hand
    c, a, b1, b2 = beta
    g1 = c + a * hist.g.iloc[-1] + b1 * (sc["baseline"].ur.iloc[0] - hist.ur.iloc[-1]) \
        + b2 * (sc["baseline"].y10.iloc[0] - hist.y10.iloc[-1])
    assert np.isclose(base.g.iloc[0], g1)
    # Part B stress: SA + outflow overlay of -3pp in Q1 decaying by half each quarter
    overlay = -3.0 * 0.5 ** np.arange(H)
    stress, _ = scenario_forecast(hist, sc["severely_adverse"], overlay=overlay)
    assert (stress.deposits < sa.deposits).all()
    # Part C: VAR conditional forecast hits the imposed paths exactly
    Y = hist[["ur", "y10", "g"]].to_numpy()
    cV, AV, SV = fit_var1(Y)
    cond = sc["severely_adverse"][["ur", "y10"]].to_numpy()
    ycond, yhat, cov = var_conditional(cV, AV, SV, Y[-1], [0, 1], cond)
    assert np.allclose(ycond[:, :2], cond, atol=1e-8)
    var_diag = np.diag(cov)
    assert np.allclose(var_diag[0::3], 0, atol=1e-8)   # conditioned vars: no uncertainty
    assert np.all(var_diag[2::3] > 0)                  # deposits still uncertain
    # SA path pushes VAR deposit growth below its unconditional forecast (on average)
    assert ycond[:, 2].mean() < yhat[:, 2].mean()
    print("p3 OK  | beta =", np.round(beta, 3))
    show = pd.DataFrame({"UR_SA": sc["severely_adverse"].ur.round(2),
                         "base": base.deposits.round(1), "SA": sa.deposits.round(1),
                         "SA_p05": sa.p05.round(1), "SA_p95": sa.p95.round(1),
                         "stress": stress.deposits.round(1),
                         "VAR_g_SA": np.round(ycond[:, 2], 2)})
    print(show.to_string())


if __name__ == "__main__":
    _tests()
```

Sample output (illustrative paths; at jump-off, deposits are about 6,874, UR is 6.4% and the 10y is 3.6%):

```text
p3 OK  | beta = [ 0.964  0.419 -1.526  0.82 ]
        UR_SA    base      SA  SA_p05  SA_p95  stress  VAR_g_SA
2026Q1   7.31  6985.5  6811.8  6765.3  6849.2  6605.6     -1.19
2026Q2   8.23  7096.9  6721.8  6647.2  6795.8  6336.2     -1.67
2026Q3   9.15  7209.2  6640.0  6539.4  6740.3  6138.4     -1.64
2026Q4  10.06  7323.0  6570.5  6448.2  6693.1  6002.1     -1.59
2027Q1  10.98  7438.4  6510.0  6368.7  6650.0  5906.2     -1.58
2027Q2  11.90  7555.6  6455.3  6297.6  6611.0  5834.1     -1.57
2027Q3  11.56  7674.7  6527.0  6350.4  6698.2  5886.9      0.32
2027Q4  11.23  7795.5  6653.1  6457.3  6838.9  5994.3      1.10
2028Q1  10.90  7918.3  6804.8  6592.3  7011.8  6127.5      1.45
```

**Hints (tiered):**

1. "The scenario gives UR *levels*; the model wants $\Delta UR$. What is $\Delta UR$ in the first scenario quarter?" (Path[0] minus the **last historical** value: the jump-off.)
2. "The model is recursive in $g$: quarter 2 needs your quarter-1 *forecast* of $g$, not an actual." Write the loop over h.
3. "For bands: either simulate by drawing residuals with replacement at each step and push them through the same recursion, or use the analytic h-step variance $\sigma^2 \sum_{j<h} a^{2j}$ on growth. Then cumulate to levels per simulated path, and take percentiles of the *levels*."

If `fit_arx` isn't done by 0:37, paste it from the reference and let the candidate focus on `project()`.

**Debrief questions (0:47–0:50; these count toward the score even if the code isn't finished):**

- "Treating UR and the 10y as exogenous: when is that OK, and when is it wrong?" (OK if the scenario is a *given* conditioning path and deposits don't feed back into macro. In a VAR where UR, the 10y and deposits interact, plugging in the paths ignores the fact that the shocks needed to produce that path also move deposits. The **Waggoner–Zha** conditional forecast picks the most likely shock sequence consistent with the path; see the stretch in Part C of the reference.)
- "Severely Adverse has UR far outside most of your sample. What worries you?" (Extrapolation and nonlinearity, the Lucas critique and regime change (e.g. deposit betas behave differently at zero rates vs 5%), structural breaks such as 2020's deposit surge, and bands that only reflect shock uncertainty, not parameter or model uncertainty.)
- "The bands: what uncertainty do they include, and what's missing?" (Shock uncertainty only. Missing: parameter uncertainty (fix with a pairs or block bootstrap that re-estimates), model uncertainty, and the scenario itself, which is fixed by construction.)
- "How would you validate this before using it for CCAR?" (Back-test conditional on *realized* macro paths in 2008–09 and 2020; compare against the incumbent; run sensitivity to the jump-off; check that the model is stable across subsamples.)
- "How would you set the size of that −3pp outflow overlay?" (From 2023 regional-bank run data, deposit-beta research, or historical tail outflows from past stress episodes.)

**Stretch (if the candidate finishes early):** "Now suppose UR, the 10y and deposit growth are a VAR(1). Impose the SA paths for UR and the 10y as conditions. How do you get the deposit path?" The reference `var_conditional` builds the impulse-response matrix $M$ mapping structural shocks to path deviations, solves for the minimum-norm shocks that hit the conditions, $\varepsilon^{*} = R^\top (R R^\top)^{-1} r$, and returns the conditional covariance. A strong candidate at least describes this; a very strong one codes a version of it.

**Common mistakes / red flags:**

- **Jump-off error:** taking `path.ur.diff()`, which makes the first $\Delta UR$ NaN or zero, so the biggest shock in the scenario disappears.
- Using *actual* lagged $g$ inside the recursion (there are none in the forecast period), or mixing up growth in % and decimals when cumulating ($\times(1+g/100)$).
- Adding growth rates to get levels, or applying bands to growth and then cumulating the 5th percentile (percentiles don't cumulate; simulate the levels).
- Not noticing that SA should *lower* deposits under this model ($b_1 < 0$), i.e. no sanity check on the sign.
- **Red flag:** "just plug the scenario numbers into `model.predict`" with no thought about jump-off, recursion or uncertainty, and nothing to say on exogeneity or extrapolation in the debrief.

**Strong vs weak:**

- *Strong:* gets the recursion and jump-off right without hints, simulates levels for bands, sanity-checks SA < baseline, and in the debrief separates exogenous plug-in from VAR conditioning, raises extrapolation and regime issues, and suggests a conditional backtest on 2008/2020. Bonus: mentions how they'd explain the path to a business partner ("deposits end up about 15% below baseline by quarter 6, driven mostly by the UR jump").
- *Weak:* needs Hints 1 and 2; bands missing or computed on growth; debrief answers generic ("the model may not hold").

**Rubric:** **4** baseline + SA levels correct, bands right, stress overlay done, and a strong debrief (exogeneity vs conditioning, extrapolation, validation) · **3** correct level paths with ≤ 1 hint and a solid debrief; bands or stress may be partial · **2** a path is produced but with a jump-off or levels error fixed only after a hint; generic debrief · **1** no working projection, and the debrief shows no grasp of conditional forecasting.

## P4. Local projection IRF with Newey–West SEs (swap-in, 10–12 min)

**Why this problem:** local projections (and LP-IV) are home turf for many macro-econometrics candidates. If the candidate says they code them, this should be fast and fluent. It checks code ownership. Because it flatters such candidates, don't use it to rescue a weak core performance.

**Prompt to paste:**

> `df` has an outcome `y` and an observed, identified shock `s`. For $h = 0,\dots,8$ estimate $y_{t+h} - y_{t-1} = a_h + b_h s_t + \sum_{l=1}^{2}(\gamma_l y_{t-l} + \delta_l s_{t-l}) + u_{t+h}$ and return the IRF $b_h$ with 95% bands using Newey–West standard errors you code yourself. How many lags, and why? Then check against statsmodels' HAC.

**Starter ([`starters/p4_starter.py`](starters/p4_starter.py)):**

```python
# file: interview-kit/starters/p4_starter.py
"""
Local projection impulse response with Newey-West SEs. ~12 minutes.

df: columns y, s (an observed, identified shock). For h = 0..8 estimate
    y_{t+h} - y_{t-1} = a_h + b_h s_t + 2 lags of y and s + u_{t+h}
Return a DataFrame indexed by h with irf (b_h), se, lo, hi (95%).
Write the Newey-West covariance yourself (numpy), then check it against
statsmodels' HAC if you have time. How many lags, and why?
"""
import numpy as np
import pandas as pd


def make_data(T: int = 3000, seed: int = 3):
    """y_t = rho y_{t-1} + theta s_t + e_t, s iid N(0,1).
    The cumulative response of y_{t+h} - y_{t-1} to s_t is theta * rho^h."""
    rng = np.random.default_rng(seed)
    rho, theta = 0.8, 1.0
    s = rng.normal(size=T)
    y = np.zeros(T)
    for t in range(1, T):
        y[t] = rho * y[t - 1] + theta * s[t] + rng.normal(0, 1.0)
    true_irf = lambda h: theta * rho ** h
    z = s + rng.normal(0, 1.0, size=T)          # instrument correlated with s
    s_noisy = s + rng.normal(0, 1.0, size=T)    # mismeasured shock
    df = pd.DataFrame({"y": y, "s": s, "s_noisy": s_noisy, "z": z})
    return df, true_irf


def newey_west(X: np.ndarray, u: np.ndarray, L: int) -> np.ndarray:
    raise NotImplementedError


def local_projection(df: pd.DataFrame, Hmax: int = 8) -> pd.DataFrame:
    raise NotImplementedError


def check():
    df, true_irf = make_data()
    irf = local_projection(df, Hmax=8)
    truth = np.array([true_irf(h) for h in irf.index])
    print(irf.assign(true=truth).round(3))
    assert np.max(np.abs(irf.irf - truth)) < 0.15
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p4_local_projection_nw.py`](solutions/p4_local_projection_nw.py)):**

```python
# file: interview-kit/solutions/p4_local_projection_nw.py
"""
Problem 4 (swap-in, ~12 min): local projection impulse response
with Newey-West standard errors, coded by hand, cross-checked with statsmodels.

For h = 0..Hmax:
    y_{t+h} - y_{t-1} = a_h + b_h s_t + sum_{l=1..L} (g_l y_{t-l} + d_l s_{t-l}) + u_{t+h}
b_h is the impulse response at horizon h. u_{t+h} is MA(h) by construction,
so use HAC (Newey-West) SEs with at least h+1 lags.
Extension: LP-IV when s_t is observed with noise and z_t is an instrument.
"""
import numpy as np
import pandas as pd


# ----------------------------------------------------------------------------
# Synthetic data with a known IRF
# ----------------------------------------------------------------------------
def make_data(T: int = 3000, seed: int = 3):
    """y_t = rho y_{t-1} + theta s_t + e_t, s iid N(0,1).
    The cumulative response of y_{t+h} - y_{t-1} to s_t is theta * rho^h."""
    rng = np.random.default_rng(seed)
    rho, theta = 0.8, 1.0
    s = rng.normal(size=T)
    y = np.zeros(T)
    for t in range(1, T):
        y[t] = rho * y[t - 1] + theta * s[t] + rng.normal(0, 1.0)
    true_irf = lambda h: theta * rho ** h
    z = s + rng.normal(0, 1.0, size=T)          # instrument correlated with s
    s_noisy = s + rng.normal(0, 1.0, size=T)    # mismeasured shock
    df = pd.DataFrame({"y": y, "s": s, "s_noisy": s_noisy, "z": z})
    return df, true_irf


# ----------------------------------------------------------------------------
# Reference solution
# ----------------------------------------------------------------------------
def newey_west(X: np.ndarray, u: np.ndarray, L: int, small_sample: bool = True):
    """HAC covariance (Bartlett kernel, L lags): (X'X)^-1 S (X'X)^-1,
    S = G0 + sum_{l=1..L} w_l (G_l + G_l'), w_l = 1 - l/(L+1), G_l = sum_t x_t u_t u_{t-l} x_{t-l}'.
    small_sample multiplies by n/(n-k) (statsmodels' default use_correction)."""
    n, k = X.shape
    Xu = X * u[:, None]
    S = Xu.T @ Xu
    for l in range(1, L + 1):
        w = 1 - l / (L + 1)
        G = Xu[l:].T @ Xu[:-l]
        S += w * (G + G.T)
    XtX_inv = np.linalg.inv(X.T @ X)
    V = XtX_inv @ S @ XtX_inv
    return V * (n / (n - k)) if small_sample else V


def lp_design(df: pd.DataFrame, h: int, shock: str = "s", n_lags: int = 2):
    d = pd.DataFrame({"lhs": df.y.shift(-h) - df.y.shift(1),
                      "const": 1.0, "shock": df[shock]})
    for l in range(1, n_lags + 1):
        d[f"y_l{l}"] = df.y.shift(l)
        d[f"s_l{l}"] = df[shock].shift(l)
    d = d.dropna()
    return d.drop(columns="lhs"), d["lhs"]


def local_projection(df, Hmax=8, shock="s", n_lags=2):
    rows = []
    for h in range(Hmax + 1):
        X, y = lp_design(df, h, shock, n_lags)
        Xn, yn = X.to_numpy(), y.to_numpy()
        b, *_ = np.linalg.lstsq(Xn, yn, rcond=None)
        u = yn - Xn @ b
        V = newey_west(Xn, u, L=h + 1)
        j = list(X.columns).index("shock")
        se = np.sqrt(V[j, j])
        rows.append(dict(h=h, irf=b[j], se=se, lo=b[j] - 1.96 * se, hi=b[j] + 1.96 * se))
    return pd.DataFrame(rows).set_index("h")


def lp_iv(df, h, endog="s_noisy", instr="z", n_lags=2):
    """Just-identified 2SLS: beta = (Z'X)^-1 Z'y, with HAC on the 2SLS residuals."""
    X, y = lp_design(df, h, endog, n_lags)
    Z = X.copy()
    Z["shock"] = df.loc[X.index, instr]
    Xn, Zn, yn = X.to_numpy(), Z.to_numpy(), y.to_numpy()
    b = np.linalg.solve(Zn.T @ Xn, Zn.T @ yn)
    u = yn - Xn @ b
    # HAC sandwich for IV: (Z'X)^-1 S_zu (X'Z)^-1
    Zu = Zn * u[:, None]
    S = Zu.T @ Zu
    for l in range(1, h + 2):
        G = Zu[l:].T @ Zu[:-l]
        S += (1 - l / (h + 2)) * (G + G.T)
    A = np.linalg.inv(Zn.T @ Xn)
    V = A @ S @ A.T
    j = list(X.columns).index("shock")
    return b[j], np.sqrt(V[j, j])


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    df, true_irf = make_data()
    irf = local_projection(df, Hmax=8)
    truth = np.array([true_irf(h) for h in irf.index])
    # point estimates close to the truth (large T), and most CIs cover it
    assert np.max(np.abs(irf.irf - truth)) < 0.15, (irf.irf - truth)
    cover = ((irf.lo <= truth) & (truth <= irf.hi)).mean()
    assert cover >= 0.75, cover
    # SEs grow with horizon (overlapping errors)
    assert irf.se.iloc[-1] > irf.se.iloc[0]
    # cross-check NW against statsmodels if available
    try:
        import statsmodels.api as sm
        X, y = lp_design(df, 4)
        res = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 5, "use_correction": True})
        b, *_ = np.linalg.lstsq(X.to_numpy(), y.to_numpy(), rcond=None)
        V = newey_west(X.to_numpy(), y.to_numpy() - X.to_numpy() @ b, L=5)
        assert np.allclose(res.bse.to_numpy(), np.sqrt(np.diag(V)), rtol=1e-8)
        sm_ok = True
    except ImportError:
        sm_ok = False
    # LP with a mismeasured shock is attenuated; LP-IV fixes it
    b_ols = local_projection(df, Hmax=0, shock="s_noisy").irf.iloc[0]
    b_iv, se_iv = lp_iv(df, 0)
    assert b_ols < 0.7 * true_irf(0)              # attenuation ~ 1/2
    assert abs(b_iv - true_irf(0)) < 3 * se_iv
    print("p4 OK  | statsmodels HAC match:", sm_ok, "| OLS(noisy)=%.2f  IV=%.2f (se %.2f)" % (b_ols, b_iv, se_iv))
    print(pd.concat([irf.round(3), pd.Series(truth.round(3), index=irf.index, name="true")], axis=1).to_string())


if __name__ == "__main__":
    _tests()
```

**Hints:** (1) "Build the LHS with `shift(-h)` and `shift(1)`, then drop NaNs." (2) "NW: $S = \sum_t \hat u_t^2 x_t x_t^\top + \sum_{l=1}^{L} w_l (\Gamma_l + \Gamma_l^\top)$ with Bartlett weights $w_l = 1 - l/(L+1)$." (3) "statsmodels: `sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': L})`."

**Follow-ups:** Why is $u_{t+h}$ serially correlated (overlapping horizons: MA(h))? LP vs VAR IRFs: the bias–variance trade-off (Plagborg-Møller & Wolf: same population IRF; Li, Plagborg-Møller & Wolf 2024: LPs have lower bias, higher variance). Measurement error in `s`: what happens (attenuation) and the fix (LP-IV with an instrument; in the reference, OLS on the noisy shock gives about 0.51 vs a true value of 1.0, and IV recovers about 1.02). How would the candidate turn an IRF into a scenario path (impulse × shock sequence, plus state dependence)?

**Mistakes / red flags:** using plain OLS SEs; NW lags fixed at 1 for all h; LHS $y_{t+h}$ in levels without the $y_{t-1}$ difference while still calling it cumulative; forgetting to align the rows after `dropna`. *Red flag:* can't write NW at all, or describes LP fluently but can't code the `shift(-h)` LHS.

**Strong vs weak:** *Strong:* done in under 10 min, NW from memory, lags ≥ h+1 with a reason, and spontaneously discusses LP-IV and the LP-vs-VAR trade-off. *Weak:* needs the NW formula and doesn't know why the lag count grows with h.

**Rubric:** **4** fast, correct NW matching statsmodels, sharp discussion · **3** correct with a nudge on NW · **2** OLS IRF right but NW wrong or missing · **1** can't code a method they claim.

## P5. Budget allocation: Lagrange bisection vs scipy (swap-in, 10–12 min)

**Why this problem:** a classic way to solve a budget allocation is to equate marginal values to a Lagrange multiplier and bisect on it. Planning work (resource and budget allocation) also needs general solvers. This tests whether the candidate can move from a hand-rolled method to LP/NLP/MILP and read a dual.

**Prompt to paste:**

> Allocate a budget $B$ across $n$ business lines to maximize $\sum_i a_i(1-e^{-b_i x_i})$ subject to $\sum_i x_i = B$ and $0 \le x_i \le u_i$. First solve it with the first-order conditions and bisection on the multiplier; return the allocation and $\lambda$. Then solve it with scipy and compare. Finally: what changes if each funded line needs at least 6, and at most 5 lines can be funded?

**Starter ([`starters/p5_starter.py`](starters/p5_starter.py)):**

```python
# file: interview-kit/starters/p5_starter.py
"""
Budget allocation across n business lines. ~12 minutes.

    max_x  sum_i a_i (1 - exp(-b_i x_i))   s.t.  sum_i x_i = B,  0 <= x_i <= u_i

1. Solve it with the first-order conditions + bisection on the Lagrange
   multiplier. Return (x, lam).
2. Solve it again with scipy (scipy.optimize.minimize or linprog) and compare
   allocations, objective values, and lam vs the solver's dual if you get one.
3. Talk: what changes if each line needs a minimum spend of 6 when funded,
   and at most 5 lines can be funded?
"""
import numpy as np


def make_problem(n: int = 8, seed: int = 4):
    rng = np.random.default_rng(seed)
    a = rng.uniform(5, 20, n)        # saturation level of each line's payoff
    b = rng.uniform(0.05, 0.4, n)    # how fast payoff saturates
    u = rng.uniform(8, 25, n)        # caps
    B = 0.45 * u.sum()
    return a, b, u, B


def objective(x, a, b):
    return np.sum(a * (1 - np.exp(-b * x)))


def allocate_bisection(a, b, u, B):
    raise NotImplementedError


def check():
    a, b, u, B = make_problem()
    x, lam = allocate_bisection(a, b, u, B)
    print(np.round(x, 3), lam, objective(x, a, b))
    assert np.isclose(x.sum(), B) and np.all(x >= -1e-12) and np.all(x <= u + 1e-12)
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p5_budget_allocation.py`](solutions/p5_budget_allocation.py)):**

```python
# file: interview-kit/solutions/p5_budget_allocation.py
"""
Problem 5 (swap-in, ~12 min): allocate a budget B across n business lines.

    max_x  sum_i a_i (1 - exp(-b_i x_i))   s.t.  sum_i x_i = B,  0 <= x_i <= u_i

Concave, separable. KKT: a_i b_i exp(-b_i x_i) = lam for interior x_i, so
    x_i(lam) = clip( ln(a_i b_i / lam) / b_i , 0, u_i ),
and sum_i x_i(lam) is decreasing in lam -> bisection on lam.
Cross-checks: scipy.optimize.minimize (SLSQP), a piecewise-linear LP with
scipy.optimize.linprog (dual of the budget row ~ lam), and an extension MILP
with "minimum spend if funded" (scipy.optimize.milp).
"""
import numpy as np

try:
    from scipy.optimize import minimize, linprog
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False
try:                                    # milp needs scipy >= 1.9
    from scipy.optimize import milp, LinearConstraint, Bounds
    HAVE_MILP = True
except ImportError:
    HAVE_MILP = False


# ----------------------------------------------------------------------------
# Synthetic problem
# ----------------------------------------------------------------------------
def make_problem(n: int = 8, seed: int = 4):
    rng = np.random.default_rng(seed)
    a = rng.uniform(5, 20, n)        # saturation level of each line's payoff
    b = rng.uniform(0.05, 0.4, n)    # how fast payoff saturates
    u = rng.uniform(8, 25, n)        # caps
    B = 0.45 * u.sum()
    return a, b, u, B


def objective(x, a, b):
    return np.sum(a * (1 - np.exp(-b * x)))


# ----------------------------------------------------------------------------
# Reference solution 1: bisection on the multiplier
# ----------------------------------------------------------------------------
def x_of_lam(lam, a, b, u):
    return np.clip(np.log(a * b / lam) / b, 0.0, u)


def allocate_bisection(a, b, u, B, tol=1e-12, max_iter=200):
    if B >= u.sum():
        return u.copy(), 0.0                     # budget not binding
    lo, hi = 1e-12, np.max(a * b)                # at lam = max(a b) every x_i = 0
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        if x_of_lam(mid, a, b, u).sum() > B:     # spending too much -> raise price
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    lam = 0.5 * (lo + hi)
    return x_of_lam(lam, a, b, u), lam


# ----------------------------------------------------------------------------
# Reference solution 2: general NLP solver
# ----------------------------------------------------------------------------
def allocate_slsqp(a, b, u, B):
    x0 = np.full(len(a), B / len(a))
    res = minimize(lambda x: -objective(x, a, b), x0,
                   jac=lambda x: -(a * b * np.exp(-b * x)),
                   bounds=list(zip(np.zeros_like(u), u)),
                   constraints=[{"type": "eq", "fun": lambda x: x.sum() - B,
                                 "jac": lambda x: np.ones_like(x)}],
                   method="SLSQP", options={"ftol": 1e-12, "maxiter": 500})
    assert res.success, res.message
    return res.x


# ----------------------------------------------------------------------------
# Reference solution 3: piecewise-linear LP (outer approximation by segments)
# ----------------------------------------------------------------------------
def allocate_lp(a, b, u, B, K=200):
    """Split [0,u_i] into K equal segments; segment k of line i pays its average
    slope. Concavity => slopes decrease, so the LP fills segments in order
    without needing binaries."""
    n = len(a)
    w = u / K                                            # segment widths
    edges = np.linspace(0, 1, K + 1)[None, :] * u[:, None]
    f = a[:, None] * (1 - np.exp(-b[:, None] * edges))
    slope = np.diff(f, axis=1) / w[:, None]              # n x K
    c = -slope.ravel()                                   # linprog minimizes
    A_eq = np.ones((1, n * K)); b_eq = [B]
    bounds = [(0, w[i]) for i in range(n) for _ in range(K)]
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    assert res.status == 0, res.message
    x = res.x.reshape(n, K).sum(axis=1)
    try:                                                 # scipy >= 1.7 (HiGHS duals)
        lam_lp = -res.eqlin.marginals[0]                 # shadow price of budget
    except AttributeError:
        lam_lp = float("nan")
    return x, lam_lp


# ----------------------------------------------------------------------------
# Extension: minimum spend if funded (MILP), plus at most m lines funded
# ----------------------------------------------------------------------------
def allocate_milp(a, b, u, B, m_min, max_funded, K=60):
    n = len(a)
    w = u / K
    edges = np.linspace(0, 1, K + 1)[None, :] * u[:, None]
    f = a[:, None] * (1 - np.exp(-b[:, None] * edges))
    slope = (np.diff(f, axis=1) / w[:, None]).ravel()
    nx = n * K
    c = np.r_[-slope, np.zeros(n)]                       # vars: segments, then z_i
    cons = []
    cons.append(LinearConstraint(np.r_[np.ones(nx), np.zeros(n)][None, :], -np.inf, B))
    for i in range(n):
        row = np.zeros(nx + n); row[i * K:(i + 1) * K] = 1; row[nx + i] = -m_min[i]
        cons.append(LinearConstraint(row[None, :], 0, np.inf))       # sum x_i >= m_i z_i
        for k in range(K):
            row = np.zeros(nx + n); row[i * K + k] = 1; row[nx + i] = -w[i]
            cons.append(LinearConstraint(row[None, :], -np.inf, 0))  # x_ik <= w_i z_i
    row = np.r_[np.zeros(nx), np.ones(n)]
    cons.append(LinearConstraint(row[None, :], 0, max_funded))
    integrality = np.r_[np.zeros(nx), np.ones(n)]
    bounds = Bounds(np.zeros(nx + n), np.r_[np.repeat(w, K), np.ones(n)])
    res = milp(c, constraints=cons, integrality=integrality, bounds=bounds)
    assert res.status == 0, res.message
    x = res.x[:nx].reshape(n, K).sum(axis=1)
    z = np.round(res.x[nx:]).astype(int)
    return x, z


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------
def _tests():
    a, b, u, B = make_problem()
    x_bis, lam = allocate_bisection(a, b, u, B)
    assert np.isclose(x_bis.sum(), B, atol=1e-8)
    assert np.all(x_bis >= 0) and np.all(x_bis <= u + 1e-12)
    # KKT check: interior lines have marginal value = lam; at 0 marginal <= lam; at cap >= lam
    mv = a * b * np.exp(-b * x_bis)
    interior = (x_bis > 1e-9) & (x_bis < u - 1e-9)
    assert np.allclose(mv[interior], lam, rtol=1e-6)
    assert np.all(mv[x_bis <= 1e-9] <= lam + 1e-9)
    assert np.all(mv[x_bis >= u - 1e-9] >= lam - 1e-9)
    # tight budget: some lines get zero (corner), still matches SLSQP below
    x_small, lam_small = allocate_bisection(a, b, u, 5.0)
    assert np.isclose(x_small.sum(), 5.0) and (x_small < 1e-9).any()
    # budget not binding edge case
    xu, l0 = allocate_bisection(a, b, u, u.sum() * 2)
    assert np.allclose(xu, u) and l0 == 0.0
    if not HAVE_SCIPY:
        print("p5 OK (bisection only; scipy missing)")
        return
    x_sl = allocate_slsqp(a, b, u, B)
    assert np.isclose(objective(x_sl, a, b), objective(x_bis, a, b), rtol=1e-6)
    assert np.allclose(x_sl, x_bis, atol=1e-3)
    assert np.allclose(allocate_slsqp(a, b, u, 5.0), x_small, atol=1e-3)
    x_lp, lam_lp = allocate_lp(a, b, u, B)
    assert np.isclose(x_lp.sum(), B)
    assert objective(x_lp, a, b) <= objective(x_bis, a, b) + 1e-9    # bisection is optimal
    assert np.isclose(objective(x_lp, a, b), objective(x_bis, a, b), rtol=1e-4)
    assert np.isnan(lam_lp) or np.isclose(lam_lp, lam, rtol=0.05), (lam_lp, lam)  # dual ~ multiplier
    if not HAVE_MILP:
        print("p5 OK  (no scipy.optimize.milp; MILP extension skipped) lam=%.5f" % lam)
        return
    # MILP extension: min spend 6 if funded, at most 5 lines
    m_min = np.full(len(a), 6.0)
    x_mi, z = allocate_milp(a, b, u, B, m_min, max_funded=5)
    assert z.sum() <= 5 and np.all(x_mi[z == 0] < 1e-9) and np.all(x_mi[z == 1] >= 6 - 1e-6)
    assert objective(x_mi, a, b) <= objective(x_bis, a, b) + 1e-9    # extra constraints cost value
    print("p5 OK  | lam bisection=%.5f  lam LP dual=%.5f" % (lam, lam_lp))
    print("x bisection:", np.round(x_bis, 2))
    print("x SLSQP    :", np.round(x_sl, 2))
    print("x LP(K=200):", np.round(x_lp, 2))
    print("x MILP     :", np.round(x_mi, 2), "funded:", z)
    print("objective  : bis %.4f  slsqp %.4f  lp %.4f  milp %.4f" % (
        objective(x_bis, a, b), objective(x_sl, a, b), objective(x_lp, a, b), objective(x_mi, a, b)))


if __name__ == "__main__":
    _tests()
```

**Hints:** (1) "Interior FOC: $a_i b_i e^{-b_i x_i} = \lambda$. Solve for $x_i(\lambda)$, then clip to $[0, u_i]$." (2) "Total spend is decreasing in $\lambda$, so bisect: too much spend means raise $\lambda$." (3) "`scipy.optimize.minimize(..., method='SLSQP', bounds=..., constraints=[{'type':'eq', ...}])` minimizes, so negate the objective."

**Follow-ups:** What is $\lambda$ economically? (The marginal value of one more unit of budget; compare it with the LP dual `res.eqlin.marginals`, about 0.312 vs 0.310.) Why can the piecewise-linear LP skip binaries? (Concavity makes segment slopes decrease, so the LP fills segments in order.) Why do minimum spend and a count limit need a MILP (non-convex feasible set)? What happens to bisection then (it breaks, and you need branch-and-bound)? What would the candidate use in production (HiGHS via scipy, OR-Tools, Gurobi)?

**Mistakes / red flags:** bisecting in the wrong direction; not clipping at the bounds; a bracket that doesn't contain the root (the upper bound must be $\max_i a_i b_i$); forgetting to negate for `minimize`. *Red flag:* can't map the first-order conditions onto this, or has never touched an LP/MILP solver and doesn't see when one is needed.

**Strong vs weak:** *Strong:* bisection in about 5 min, checks the KKT conditions on corner lines, interprets the dual, and explains clearly why the MILP is needed. *Weak:* bisection only, no solver, and the MILP question draws a blank.

**Rubric:** **4** bisection + solver match + dual interpretation + MILP reasoning · **3** bisection + solver match · **2** one method only · **1** neither works.

## P6. Monte Carlo credit losses, vectorize, Numba (swap-in, 8–12 min)

**Why this problem:** simulation is central to risk and planning work, and performance claims ("vectorized", "Numba-accelerated") are easy to put on a CV. This shows whether the candidate naturally thinks in arrays and knows Numba's real constraints.

**Prompt to paste:**

> One-factor Gaussian (Vasicek) credit model with $\rho = 0.15$: loan $i$ defaults in scenario $s$ if $\sqrt{\rho} Z_s + \sqrt{1-\rho}\,\varepsilon_{s,i} < \Phi^{-1}(PD_i)$. Loss is $\sum_i EAD_i \cdot LGD_i \cdot \mathbf 1\{\text{default}\}$. Simulate 20,000 scenarios for this 500-loan portfolio and report expected loss, 99.9% VaR and expected shortfall. Check EL against the analytic value. Then make it fast: vectorize, and use Numba if it's available.

**Starter ([`starters/p6_starter.py`](starters/p6_starter.py)):**

```python
# file: interview-kit/starters/p6_starter.py
"""
Monte Carlo credit losses, then make it fast. ~12 minutes.

One-factor Gaussian (Vasicek) model, rho = 0.15. Loan i defaults in sim s if
    sqrt(rho) * Z_s + sqrt(1 - rho) * eps_{s,i} < Phi^{-1}(PD_i)
Loss_s = sum_i EAD_i * LGD_i * 1{default}.
1. Simulate 20,000 scenarios; report expected loss, 99.9% VaR and ES.
   Check EL against the analytic value sum(EAD * LGD * PD).
2. Make it fast: vectorize with numpy and/or use numba (if available).
   Show both versions give the same answer on the same random draws.
"""
import math
import time
import numpy as np
from scipy.stats import norm


def make_portfolio(n_loans: int = 500, seed: int = 5):
    rng = np.random.default_rng(seed)
    ead = rng.lognormal(mean=0.0, sigma=1.0, size=n_loans)   # exposures
    pd_ = rng.uniform(0.005, 0.05, size=n_loans)              # default probs
    lgd = rng.uniform(0.3, 0.6, size=n_loans)
    return ead, pd_, lgd


def simulate_losses(n_sims, ead, pd_, lgd, rho, seed=0):
    raise NotImplementedError


def check():
    ead, pd_, lgd = make_portfolio()
    L = simulate_losses(20_000, ead, pd_, lgd, 0.15)
    print("EL MC", L.mean(), "EL analytic", np.sum(ead * lgd * pd_))
    print("checks passed")


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p6_monte_carlo_numba.py`](solutions/p6_monte_carlo_numba.py)):**

```python
# file: interview-kit/solutions/p6_monte_carlo_numba.py
"""
Problem 6 (swap-in, performance, ~10-12 min): simulate a portfolio credit-loss
distribution with the one-factor Gaussian (Vasicek) model, three ways:
  (1) plain Python loops, (2) vectorized numpy, (3) Numba @njit (optional).
Report EL, VaR_99.9 and ES_99.9 (expected shortfall).

Loan i defaults in sim s if  sqrt(rho) Z_s + sqrt(1-rho) eps_{s,i} < Phi^{-1}(PD_i).
Loss_s = sum_i EAD_i * LGD_i * 1{default}.
Analytic checks: E[Loss] = sum EAD*LGD*PD;  for a large homogeneous pool the
loss fraction quantile is Phi( (Phi^{-1}(PD) + sqrt(rho) Phi^{-1}(q)) / sqrt(1-rho) ).
Extension in the kit: deposit-runoff paths under a rate shock.
"""
import math
import time
import numpy as np

try:
    from scipy.stats import norm
    ppf, cdf = norm.ppf, norm.cdf
except ImportError:                       # fallback via statistics.NormalDist
    from statistics import NormalDist
    _N = NormalDist()
    ppf = np.vectorize(_N.inv_cdf); cdf = np.vectorize(_N.cdf)

try:
    from numba import njit, prange
    HAVE_NUMBA = True
except ImportError:
    HAVE_NUMBA = False


def make_portfolio(n_loans: int = 500, seed: int = 5):
    rng = np.random.default_rng(seed)
    ead = rng.lognormal(mean=0.0, sigma=1.0, size=n_loans)   # exposures
    pd_ = rng.uniform(0.005, 0.05, size=n_loans)              # default probs
    lgd = rng.uniform(0.3, 0.6, size=n_loans)
    return ead, pd_, lgd


# (1) loops: correct but slow
def losses_loop(Z, eps, ead, pd_, lgd, rho):
    thr = ppf(pd_)
    n_sims, n_loans = eps.shape
    out = np.zeros(n_sims)
    a, b = math.sqrt(rho), math.sqrt(1 - rho)
    for s in range(n_sims):
        tot = 0.0
        for i in range(n_loans):
            if a * Z[s] + b * eps[s, i] < thr[i]:
                tot += ead[i] * lgd[i]
        out[s] = tot
    return out


# (2) vectorized: broadcasting (n_sims x n_loans) boolean matrix
def losses_vec(Z, eps, ead, pd_, lgd, rho):
    thr = ppf(pd_)
    latent = math.sqrt(rho) * Z[:, None] + math.sqrt(1 - rho) * eps
    return (latent < thr[None, :]) @ (ead * lgd)


# (3) Numba: same loops, compiled; draws inside so memory is O(n_loans)
if HAVE_NUMBA:
    @njit(cache=False)
    def _losses_from_draws_nb(Z, eps, thr, el_i, a, b):
        n_sims, n_loans = eps.shape
        out = np.zeros(n_sims)
        for s in range(n_sims):
            tot = 0.0
            for i in range(n_loans):
                if a * Z[s] + b * eps[s, i] < thr[i]:
                    tot += el_i[i]
            out[s] = tot
        return out

    @njit(parallel=True, cache=False)
    def _losses_sim_nb(n_sims, thr, el_i, a, b, seed):
        out = np.zeros(n_sims)
        for s in prange(n_sims):
            np.random.seed(seed + s)        # per-sim seed -> reproducible under prange
            z = np.random.standard_normal()
            tot = 0.0
            for i in range(thr.shape[0]):
                if a * z + b * np.random.standard_normal() < thr[i]:
                    tot += el_i[i]
            out[s] = tot
        return out


def losses_numba(Z, eps, ead, pd_, lgd, rho):
    return _losses_from_draws_nb(Z, eps, ppf(pd_), ead * lgd, math.sqrt(rho), math.sqrt(1 - rho))


def risk_measures(L, q=0.999):
    var = np.quantile(L, q)
    es = L[L >= var].mean()
    return dict(EL=L.mean(), VaR=var, ES=es)


def _tests():
    rho = 0.15
    ead, pd_, lgd = make_portfolio()
    rng = np.random.default_rng(0)
    # exact equivalence on identical draws (small)
    Zs, Es = rng.standard_normal(300), rng.standard_normal((300, len(ead)))
    L1 = losses_loop(Zs, Es, ead, pd_, lgd, rho)
    L2 = losses_vec(Zs, Es, ead, pd_, lgd, rho)
    assert np.allclose(L1, L2)
    # statistical checks (vectorized, 20k sims)
    n = 20_000
    Z, E = rng.standard_normal(n), rng.standard_normal((n, len(ead)))
    t0 = time.perf_counter(); L = losses_vec(Z, E, ead, pd_, lgd, rho); t_vec = time.perf_counter() - t0
    el_true = np.sum(ead * lgd * pd_)
    se = L.std() / math.sqrt(n)
    assert abs(L.mean() - el_true) < 4 * se, (L.mean(), el_true, se)
    rm = risk_measures(L)
    assert rm["ES"] >= rm["VaR"] >= rm["EL"]
    # Vasicek asymptotic check: big homogeneous pool, loss fraction quantile
    nh, p_h = 2000, 0.02
    Zh, Eh = rng.standard_normal(4000), rng.standard_normal((4000, nh))
    Lh = losses_vec(Zh, Eh, np.ones(nh), np.full(nh, p_h), np.ones(nh), rho) / nh
    q = 0.99
    vas = cdf((ppf(p_h) + math.sqrt(rho) * ppf(q)) / math.sqrt(1 - rho))
    assert abs(np.quantile(Lh, q) - vas) < 0.15 * vas, (np.quantile(Lh, q), vas)
    msg = "numba not installed (skipped)"
    if HAVE_NUMBA:
        L3 = losses_numba(Zs, Es, ead, pd_, lgd, rho)          # first call compiles
        assert np.allclose(L1, L3)
        t0 = time.perf_counter(); losses_numba(Z, E, ead, pd_, lgd, rho); t_nb = time.perf_counter() - t0
        thr, eli = ppf(pd_), ead * lgd
        _losses_sim_nb(10, thr, eli, math.sqrt(rho), math.sqrt(1 - rho), 1)   # compile
        t0 = time.perf_counter()
        Lp = _losses_sim_nb(200_000, thr, eli, math.sqrt(rho), math.sqrt(1 - rho), 123)
        t_par = time.perf_counter() - t0
        Lp2 = _losses_sim_nb(200_000, thr, eli, math.sqrt(rho), math.sqrt(1 - rho), 123)
        assert np.array_equal(Lp, Lp2)                           # reproducible
        assert abs(Lp.mean() - el_true) < 4 * Lp.std() / math.sqrt(len(Lp))
        msg = "vec(20k) %.3fs | njit(20k) %.3fs | njit-parallel(200k, draws inside) %.3fs" % (t_vec, t_nb, t_par)
    # time the loop on a small slice to show the gap
    t0 = time.perf_counter(); losses_loop(Z[:1000], E[:1000], ead, pd_, lgd, rho); t_loop = (time.perf_counter() - t0) * n / 1000
    print("p6 OK  | EL true %.3f  MC %.3f | VaR99.9 %.2f  ES99.9 %.2f" % (el_true, rm["EL"], rm["VaR"], rm["ES"]))
    print("timing (20k sims x %d loans): loop ~%.2fs (extrapolated) | %s" % (len(ead), t_loop, msg))


if __name__ == "__main__":
    _tests()
```

Timings on a test machine (20,000 × 500): pure Python loop about 2.8 s, numpy vectorized about 0.2–0.3 s, `@njit` about 0.02 s; the `prange` version with draws inside handles 200,000 sims in about 0.5 s. CoderPad timings will differ.

**Hints:** (1) "Draw `Z` with shape `(n,)` and `eps` with shape `(n, loans)`; broadcast `Z[:, None]`." (2) "Default matrix `@ (ead * lgd)` gives the loss per scenario." (3) "Numba: `from numba import njit`; plain loops over numpy arrays; no pandas inside; the first call includes compile time."

**Follow-ups:** MC standard error of EL ($\hat\sigma/\sqrt N$) and how many sims a stable 99.9% VaR needs (the tail has only 20 points at N = 20k, so use importance sampling or more sims); ES vs VaR (coherence, tail shape); memory (the 20k × 500 float64 array is 80 MB, so chunk it or use Numba with draws inside); reproducibility with `prange` (per-iteration seeds, as in the reference); the analytic Vasicek large-pool quantile as a check. **Deposit-runoff variant** (verbal): simulate account-level or segment-level runoff with a rate-sensitive hazard, $\text{runoff}_{s,t} = \alpha + \beta\,\Delta r_t + \text{jump}_{s,t}$, and report the distribution of 9-quarter cumulative outflows.

**Mistakes / red flags:** a Python loop over scenarios *and* loans with no attempt to vectorize; computing VaR on the wrong tail; ES as the mean of all losses; timing Numba including compile time and concluding it's slow; `np.random` seeding confusion. *Red flag:* lists Numba as a skill but can't say what `@njit` requires (typed numpy, no Python objects, nopython mode) or what it sped up in past work.

**Strong vs weak:** *Strong:* writes the vectorized version first, checks EL against the analytic value with an MC SE, then a clean `@njit` loop, and talks about memory and compile time. *Weak:* loop only, no check against the analytic value, nothing concrete on Numba.

**Rubric:** **4** vectorized + Numba (or a credible Numba sketch if it isn't installed) + MC error reasoning · **3** vectorized and correct, Numba described well · **2** loop only but correct · **1** incorrect, or a Numba claim the candidate can't support.

## P7. SQL window functions on a quarterly panel (swap-in, 8–10 min)

**Why this problem:** this is a short check of window-function fluency on the panel shape a bank planning team typically works with. It runs in Python via `sqlite3`, so no separate SQL pad is needed. The queries are Postgres-compatible.

**Prompt to paste:**

> In-memory SQLite table `filings(bank_id, yr, qtr, filed_at, deposits, nii_ytd)`. Write one query that returns one row per bank-quarter with (1) only the latest filing per bank-quarter, (2) QoQ deposit growth, NULL if the previous quarter is missing, (3) quarterly NII from the YTD column, (4) the bank's deposit rank and share of total deposits within the quarter, and (stretch) (5) a 4-quarter moving average that is NULL unless 4 full quarters are present.

**Starter ([`starters/p7_starter.py`](starters/p7_starter.py)):**

```python
# file: interview-kit/starters/p7_starter.py
"""
SQL window functions on a quarterly bank panel. ~8-10 minutes.
SQLite in memory (window functions supported). Table:
  filings(bank_id TEXT, yr INT, qtr INT, filed_at TEXT, deposits REAL, nii_ytd REAL)
Write ONE query returning one row per bank-quarter with:
  1. only the latest filing per (bank_id, yr, qtr)
  2. dep_qoq: QoQ deposit growth, NULL if the previous quarter is missing
  3. nii_q: quarterly NII from the year-to-date column
  4. dep_rank: rank of the bank by deposits within the quarter, and its share
     of the quarter's total deposits
  5. (stretch) 4-quarter moving average of deposits, NULL unless 4 full quarters
"""
import sqlite3
import numpy as np
import pandas as pd


def make_db(seed: int = 7):
    rng = np.random.default_rng(seed)
    rows = []
    for b, d0 in [("A", 1000.0), ("B", 600.0), ("C", 300.0), ("D", 150.0)]:
        dep = d0
        for yr in (2022, 2023, 2024):
            for q in (1, 2, 3, 4):
                dep *= 1 + rng.normal(0.01, 0.02)
                rows.append((b, yr, q, f"{yr}-{3*q:02d}-28", round(dep, 4), round(2.5 * q * d0 / 100, 4)))
    df = pd.DataFrame(rows, columns=["bank_id", "yr", "qtr", "filed_at", "deposits", "nii_ytd"])
    # restatement for B 2023Q2: an earlier wrong filing
    bad = df[(df.bank_id == "B") & (df.yr == 2023) & (df.qtr == 2)].copy()
    bad["filed_at"] = "2023-06-01"; bad["deposits"] *= 2
    df = pd.concat([df, bad], ignore_index=True)
    # gap: D missing 2023Q3
    df = df[~((df.bank_id == "D") & (df.yr == 2023) & (df.qtr == 3))]
    con = sqlite3.connect(":memory:")
    df.to_sql("filings", con, index=False)
    return con, df


SQL = """
SELECT * FROM filings LIMIT 5   -- replace me
"""


def check():
    con, df = make_db()
    out = pd.read_sql(SQL, con)
    print(out.head(20).to_string())


if __name__ == "__main__":
    check()
```

**Reference solution ([`solutions/p7_sql_window_functions.py`](solutions/p7_sql_window_functions.py)):**

```python
# file: interview-kit/solutions/p7_sql_window_functions.py
"""
Problem 7 (optional SQL, ~8-10 min): window functions over a quarterly bank
panel. Runs in sqlite3 (stdlib; window functions need SQLite >= 3.25), and the
same SQL is valid in Postgres / CoderPad's PostgreSQL pad with minor edits
(noted inline). Results cross-checked against pandas.

Table filings(bank_id TEXT, yr INT, qtr INT, filed_at TEXT, deposits REAL, nii_ytd REAL)
  Q1  dedupe restatements: latest filed_at per (bank_id, yr, qtr)   [ROW_NUMBER]
  Q2  QoQ deposit growth, NULL if the prior quarter is missing       [LAG + gap check]
  Q3  quarterly NII from YTD                                         [LAG partitioned by year]
  Q4  4-quarter moving average of deposits                           [RANGE frame on q_idx]
  Q5  rank banks by deposits each quarter + share of industry total  [RANK, SUM OVER]
"""
import sqlite3
import numpy as np
import pandas as pd


def make_db(seed: int = 7):
    rng = np.random.default_rng(seed)
    rows = []
    for b, d0 in [("A", 1000.0), ("B", 600.0), ("C", 300.0), ("D", 150.0)]:
        dep = d0
        for yr in (2022, 2023, 2024):
            for q in (1, 2, 3, 4):
                dep *= 1 + rng.normal(0.01, 0.02)
                rows.append((b, yr, q, f"{yr}-{3*q:02d}-28", round(dep, 4), round(2.5 * q * d0 / 100, 4)))
    df = pd.DataFrame(rows, columns=["bank_id", "yr", "qtr", "filed_at", "deposits", "nii_ytd"])
    # restatement for B 2023Q2: an earlier wrong filing
    bad = df[(df.bank_id == "B") & (df.yr == 2023) & (df.qtr == 2)].copy()
    bad["filed_at"] = "2023-06-01"; bad["deposits"] *= 2
    df = pd.concat([df, bad], ignore_index=True)
    # gap: D missing 2023Q3
    df = df[~((df.bank_id == "D") & (df.yr == 2023) & (df.qtr == 3))]
    con = sqlite3.connect(":memory:")
    df.to_sql("filings", con, index=False)
    return con, df


SQL_CLEAN = """
WITH ranked AS (
  SELECT f.*,
         ROW_NUMBER() OVER (PARTITION BY bank_id, yr, qtr ORDER BY filed_at DESC) AS rn
  FROM filings f
)
SELECT bank_id, yr, qtr, deposits, nii_ytd, yr * 4 + qtr - 1 AS q_idx
FROM ranked WHERE rn = 1
"""

SQL_GROWTH = f"""
WITH clean AS ({SQL_CLEAN}),
lagged AS (
  SELECT c.*,
         LAG(deposits) OVER w AS dep_prev,
         LAG(q_idx)    OVER w AS q_prev,
         LAG(nii_ytd)  OVER (PARTITION BY bank_id, yr ORDER BY qtr) AS ytd_prev,
         LAG(qtr)      OVER (PARTITION BY bank_id, yr ORDER BY qtr) AS qtr_prev,
         -- RANGE on the integer quarter index = last 4 calendar quarters, so a
         -- missing quarter shrinks the count (ROWS would silently span the gap)
         AVG(deposits) OVER (w RANGE BETWEEN 3 PRECEDING AND CURRENT ROW) AS dep_ma4,
         COUNT(*)      OVER (w RANGE BETWEEN 3 PRECEDING AND CURRENT ROW) AS n_ma4,
         RANK()        OVER (PARTITION BY yr, qtr ORDER BY deposits DESC) AS dep_rank,
         deposits * 1.0 / SUM(deposits) OVER (PARTITION BY yr, qtr) AS dep_share
  FROM clean c
  WINDOW w AS (PARTITION BY bank_id ORDER BY q_idx)   -- Postgres: same syntax
)
SELECT bank_id, yr, qtr, deposits,
       CASE WHEN q_prev = q_idx - 1 THEN deposits / dep_prev - 1 END AS dep_qoq,
       CASE WHEN qtr = 1 THEN nii_ytd
            WHEN qtr_prev = qtr - 1 THEN nii_ytd - ytd_prev END AS nii_q,
       CASE WHEN n_ma4 = 4 THEN dep_ma4 END AS dep_ma4,   -- NULL unless 4 full quarters
       dep_rank, dep_share
FROM lagged
ORDER BY bank_id, yr, qtr
"""


def pandas_reference(df: pd.DataFrame) -> pd.DataFrame:
    c = (df.sort_values("filed_at").drop_duplicates(["bank_id", "yr", "qtr"], keep="last")
           .sort_values(["bank_id", "yr", "qtr"]).reset_index(drop=True))
    c["q_idx"] = c.yr * 4 + c.qtr - 1
    g = c.groupby("bank_id")
    prev_ok = g.q_idx.shift(1) == c.q_idx - 1
    c["dep_qoq"] = np.where(prev_ok, c.deposits / g.deposits.shift(1) - 1, np.nan)
    gy = c.groupby(["bank_id", "yr"])
    c["nii_q"] = np.where(c.qtr == 1, c.nii_ytd,
                          np.where(gy.qtr.shift(1) == c.qtr - 1, c.nii_ytd - gy.nii_ytd.shift(1), np.nan))
    return c


def _tests():
    con, df = make_db()
    out = pd.read_sql(SQL_GROWTH, con)
    ref = pandas_reference(df)
    assert len(out) == len(ref) == 4 * 12 - 1
    m = out.merge(ref, on=["bank_id", "yr", "qtr"], suffixes=("", "_pd"))
    assert np.allclose(m.deposits, m.deposits_pd)
    assert np.allclose(m.dep_qoq.astype(float), m.dep_qoq_pd, equal_nan=True)
    assert np.allclose(m.nii_q.astype(float), m.nii_q_pd, equal_nan=True)
    # gap handling: D 2023Q4 growth is NULL (prior quarter missing)
    d4 = out[(out.bank_id == "D") & (out.yr == 2023) & (out.qtr == 4)]
    assert d4.dep_qoq.isna().all() and d4.nii_q.isna().all()
    # 4Q moving average is NULL for D until 4 consecutive quarters exist again
    d_ma = out[out.bank_id == "D"].set_index(["yr", "qtr"]).dep_ma4
    assert d_ma.loc[[(2023, 4), (2024, 1), (2024, 2)]].isna().all() and d_ma.notna().loc[(2024, 3)]
    a = out[out.bank_id == "A"].reset_index(drop=True)
    assert np.isclose(a.dep_ma4.iloc[3], a.deposits.iloc[:4].mean())
    # shares sum to 1 per quarter; A ranks 1st every quarter
    assert np.allclose(out.groupby(["yr", "qtr"]).dep_share.sum(), 1.0)
    assert (out[out.bank_id == "A"].dep_rank == 1).all()
    # restatement resolved: no 2x jump for B
    assert out[out.bank_id == "B"].dep_qoq.abs().max() < 0.2
    print("p7 OK  | sqlite", sqlite3.sqlite_version, "| rows", len(out))
    print(out[out.bank_id == "D"].round(4).to_string(index=False))


if __name__ == "__main__":
    _tests()
```

**Hints:** (1) "`ROW_NUMBER() OVER (PARTITION BY bank_id, yr, qtr ORDER BY filed_at DESC)`, then keep `rn = 1`." (2) "Make an integer quarter index `yr*4 + qtr - 1`; LAG it too and check that it equals the current index minus 1." (3) "Shares: `deposits / SUM(deposits) OVER (PARTITION BY yr, qtr)`."

**Follow-ups:** ROWS vs RANGE frames (RANGE on the quarter index respects calendar gaps; ROWS counts rows); RANK vs DENSE_RANK vs ROW_NUMBER on ties; `QUALIFY` (Snowflake/BigQuery/Databricks, not Postgres or SQLite); doing the same in pandas (the reference `pandas_reference` function).

**Mistakes / red flags:** LAG without a gap check; partitioning the YTD LAG by bank only (not by year), so Q1 subtracts the prior year's Q4; integer division in engines where `deposits` is an integer; filtering `rn = 1` in the same SELECT as the window (it needs a CTE or subquery). *Red flag:* can't write a window function at all despite claiming SQL.

**Strong vs weak:** *Strong:* a CTE for dedup, a named `WINDOW`, the gap-aware LAG, and RANGE vs ROWS raised unprompted. *Weak:* GROUP BY attempts and self-joins for everything.

**Rubric:** **4** all five, gap-aware · **3** 1–4 correct · **2** dedup + LAG without gap handling · **1** no working window function.

# Appendix A. Files, how to run, test results

```text
interview-kit/
  README.md                                     this kit (plan, problems with inline code, scoring)
  refresher.md                                  methods refresher + walkthroughs of the reference solutions
  cheatsheet.md                                 one-page cheat sheet
  solutions/
    p1_bank_panel_cleaning.py                   P1 reference + generator + asserts
    p2_rolling_backtest_dm.py                   P2
    p3_conditional_scenario_forecast.py         P3 (ARX + bootstrap bands + stress + VAR/WZ)
    p4_local_projection_nw.py                   P4 (LP + hand NW + LP-IV)
    p5_budget_allocation.py                     P5 (bisection, SLSQP, LP + dual, MILP)
    p6_monte_carlo_numba.py                     P6 (loop, vectorized, numba, numba-parallel)
    p7_sql_window_functions.py                  P7 (sqlite3 window functions vs pandas)
  starters/p1_starter.py ... p7_starter.py      paste into CoderPad (stubs + checks)
  test_starters.py                              plugs reference functions into each starter's check()
  run_all.sh                                    runs everything
```

Run: `bash interview-kit/run_all.sh`. Each file is also standalone: `python3 interview-kit/solutions/p2_rolling_backtest_dm.py`.

| Problem | Starter | Reference solution |
|---|---|---|
| P1 | [starters/p1_starter.py](starters/p1_starter.py) | [solutions/p1_bank_panel_cleaning.py](solutions/p1_bank_panel_cleaning.py) |
| P2 | [starters/p2_starter.py](starters/p2_starter.py) | [solutions/p2_rolling_backtest_dm.py](solutions/p2_rolling_backtest_dm.py) |
| P3 | [starters/p3_starter.py](starters/p3_starter.py) | [solutions/p3_conditional_scenario_forecast.py](solutions/p3_conditional_scenario_forecast.py) |
| P4 | [starters/p4_starter.py](starters/p4_starter.py) | [solutions/p4_local_projection_nw.py](solutions/p4_local_projection_nw.py) |
| P5 | [starters/p5_starter.py](starters/p5_starter.py) | [solutions/p5_budget_allocation.py](solutions/p5_budget_allocation.py) |
| P6 | [starters/p6_starter.py](starters/p6_starter.py) | [solutions/p6_monte_carlo_numba.py](solutions/p6_monte_carlo_numba.py) |
| P7 | [starters/p7_starter.py](starters/p7_starter.py) | [solutions/p7_sql_window_functions.py](solutions/p7_sql_window_functions.py) |

**Output of the last full run** (Python 3.13.5 / pandas 3.0.6 / numpy 2.5.4 / scipy 1.18.1 / statsmodels 0.15.0 / numba 0.68.0):

```text
== solutions/p1_bank_panel_cleaning.py
p1 OK  | pandas 3.0.6 | raw A jump at deal: 0.428
bank_id quarter  total_deposits  nii_ytd  nii_q  dep_qoq  dep_yoy
      C  2019Q1      250.000000      2.5    2.5      NaN      NaN
      C  2019Q2      252.500000      5.0    2.5     0.01      NaN
      C  2019Q3      255.025000      7.5    2.5     0.01      NaN
      C  2019Q4      257.575250     10.0    2.5     0.01      NaN
      C  2020Q1      260.151003      2.5    2.5     0.01 0.040604
      C  2020Q2      262.752513      5.0    2.5     0.01 0.040604
== solutions/p2_rolling_backtest_dm.py
p2 OK  | n_oos = 99 | statsmodels cross-check: True
       RMSE    MAE
arx   0.465  0.351
ar    0.527  0.402
rw    0.582  0.443
mean  0.656  0.525
DM arx vs rw: stat=-3.04 p=0.0031 | CW arx vs ar: stat=4.41 p=0.0000
== solutions/p3_conditional_scenario_forecast.py
p3 OK  | beta = [ 0.964  0.419 -1.526  0.82 ]
        UR_SA    base      SA  SA_p05  SA_p95  stress  VAR_g_SA
2026Q1   7.31  6985.5  6811.8  6765.3  6849.2  6605.6     -1.19
2026Q2   8.23  7096.9  6721.8  6647.2  6795.8  6336.2     -1.67
2026Q3   9.15  7209.2  6640.0  6539.4  6740.3  6138.4     -1.64
2026Q4  10.06  7323.0  6570.5  6448.2  6693.1  6002.1     -1.59
2027Q1  10.98  7438.4  6510.0  6368.7  6650.0  5906.2     -1.58
2027Q2  11.90  7555.6  6455.3  6297.6  6611.0  5834.1     -1.57
2027Q3  11.56  7674.7  6527.0  6350.4  6698.2  5886.9      0.32
2027Q4  11.23  7795.5  6653.1  6457.3  6838.9  5994.3      1.10
2028Q1  10.90  7918.3  6804.8  6592.3  7011.8  6127.5      1.45
== solutions/p4_local_projection_nw.py
p4 OK  | statsmodels HAC match: True | OLS(noisy)=0.51  IV=1.02 (se 0.04)
     irf     se     lo     hi   true
h                                   
0  1.024  0.019  0.987  1.062  1.000
1  0.845  0.030  0.785  0.905  0.800
2  0.657  0.036  0.586  0.728  0.640
3  0.515  0.041  0.434  0.597  0.512
4  0.442  0.043  0.358  0.526  0.410
5  0.362  0.043  0.278  0.447  0.328
6  0.304  0.042  0.221  0.388  0.262
7  0.300  0.042  0.217  0.383  0.210
8  0.226  0.045  0.137  0.314  0.168
== solutions/p5_budget_allocation.py
p5 OK  | lam bisection=0.31013  lam LP dual=0.31201
x bisection: [ 8.7   9.5   8.59  6.77 11.02  7.41  7.8   8.27]
x SLSQP    : [ 8.7   9.5   8.59  6.77 11.02  7.41  7.8   8.27]
x LP(K=200): [ 8.69  9.52  8.6   6.79 10.99  7.44  7.82  8.21]
x MILP     : [12.64 15.14 11.02  0.   17.98  0.   11.27  0.  ] funded: [1 1 1 0 1 0 1 0]
objective  : bis 97.6241  slsqp 97.6241  lp 97.6239  milp 81.1195
== solutions/p6_monte_carlo_numba.py
p6 OK  | EL true 9.210  MC 9.213 | VaR99.9 73.99  ES99.9 93.14
timing (20k sims x 500 loans): loop ~2.76s (extrapolated) | vec(20k) 0.148s | njit(20k) 0.018s | njit-parallel(200k, draws inside) 0.537s
== solutions/p7_sql_window_functions.py
p7 OK  | sqlite 3.46.1 | rows 47
bank_id   yr  qtr  deposits  dep_qoq  nii_q  dep_ma4  dep_rank  dep_share
      D 2022    1  151.4024      NaN   3.75      NaN         4     0.0730
      D 2022    2  155.5944   0.0277   3.75      NaN         4     0.0745
      D 2022    3  155.3343  -0.0017   3.75      NaN         4     0.0744
      D 2022    4  156.5406   0.0078   3.75 154.7179         4     0.0747
      D 2023    1  158.4518   0.0122   3.75 156.4803         4     0.0758
      D 2023    2  160.2385   0.0113   3.75 157.6413         4     0.0768
      D 2023    4  159.7345      NaN    NaN      NaN         4     0.0760
      D 2024    1  165.6728   0.0372   3.75      NaN         4     0.0793
      D 2024    2  162.2032  -0.0209   3.75      NaN         4     0.0778
      D 2024    3  166.6131   0.0272   3.75 163.5559         4     0.0790
      D 2024    4  168.6769   0.0124   3.75 165.7915         4     0.0789
== starters
starter p1: check() passes with reference functions | last line: checks passed
starter p2: check() passes with reference functions | last line: checks passed
starter p3: check() passes with reference functions | last line: checks passed
starter p4: check() passes with reference functions | last line: checks passed
starter p5: check() passes with reference functions | last line: checks passed
starter p6: check() passes with reference functions | last line: checks passed
starter p7: check() passes with reference functions | last line: 19       B  2023    4   585.6907 -0.015791   15.0   601.1876
```

**Compatibility matrix (all seven files pass their asserts; rows 2–4 are from the original multi-stack test pass, and the only code changes since are docstrings and file paths):**

| Stack | Result |
|---|---|
| Py 3.13, pandas 3.0.6, numpy 2.5.4, scipy 1.18.1, statsmodels 0.15.0, numba 0.68.0 | all pass |
| Py 3.12, pandas 2.2.3, numpy 2.0.2, scipy 1.18.1, statsmodels 0.15.0, numba 0.68.0 (FutureWarning → error) | all pass |
| Py 3.9, pandas 1.2.4, numpy 1.20.2, scipy 1.6.3, statsmodels 0.12.2 (CoderPad-Screen-like) | all pass (P5 MILP skipped: no `milp`; LP dual skipped) |
| Py 3.9 / 3.12, numpy + pandas only | all pass (statsmodels cross-checks, scipy solvers and numba paths skipped) |

**Not verified:** the exact library versions and Numba availability in *your* CoderPad pad (run the version line first); CoderPad execution-time limits for P6 at 20k × 500 (if it's slow, drop to 5,000 sims). The scenario paths are stylized and are **not** the Fed's published Severely Adverse numbers; for real work, use the official scenario files from the Fed's stress-test pages.
