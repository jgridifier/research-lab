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
