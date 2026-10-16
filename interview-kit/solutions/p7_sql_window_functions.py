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
