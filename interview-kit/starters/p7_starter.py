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
