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
