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
