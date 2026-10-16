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
