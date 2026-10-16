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
