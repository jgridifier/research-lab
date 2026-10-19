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
