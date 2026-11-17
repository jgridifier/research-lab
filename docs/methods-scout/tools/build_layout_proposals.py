#!/usr/bin/env python3
"""Build the 2026-11-17 layout proposals under docs/methods-scout/proposals/.

Mockups only: they do not replace the daily pages or the daily generator.
Every number below is copied from a published scout page (2026-11-13, 2026-11-16, ...)
or from feedback-state.json. Nothing is re-run here.
"""
import html, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent          # docs/methods-scout
OUT = HERE / "proposals"
STATE = json.loads((HERE / "feedback-state.json").read_text())["issues"]
REPO = "https://github.com/jgridifier/research-lab"
BASE = "/research-lab/methods-scout"
ICON_HEAD = (HERE / "icons" / "head.html").read_text()
e = html.escape

STATUS = {  # one icon + one plain word per status, used everywhere
    "proposed":   ("○", "New"),
    "approved":   ("✓", "Go"),
    "in-progress":("▶", "Building"),
    "refine":     ("✎", "Needs direction"),
    "parked":     ("❚❚", "Parked"),
    "dropped":    ("✕", "Dropped"),
    "promoted":   ("★", "Promoted"),
}
PICK = {"math": "Math", "engineering": "Engineering", "new-use": "New use", None: "—"}

def words(s): return len(re.sub(r"<[^>]+>", " ", s).split())
def budget(s, n, what):
    w = words(s)
    assert w <= n, f"word budget {what}: {w} > {n}: {s[:80]}"
    return s

def chip_status(st, issue):
    ic, lab = STATUS[st]
    return f'<span class="chip st-{st}" data-issue="{issue}" title="Status from issue #{issue}">{ic} {lab}</span>'

def chip_q(q):
    if not q: return '<span class="chip q">No question</span>'
    lab = {"Q1-retired": "Old Q1", "watchlist": "Watchlist"}.get(q, q)
    return f'<span class="chip q">{e(lab)}</span>'

def chip_v(v):
    cls = "v-rec" if v in ("Recommend", "Adopt-candidate") else "v-int"
    return f'<span class="chip {cls}">{e(v)}</span>'

def respond(issue, big=False):
    return (f'<a class="btn{" big" if big else ""}" href="{REPO}/issues/{issue}">Respond on #{issue}</a>'
            f'<p class="howto">👍 go with top pick · 👎 drop · 👀 park · or comment <code>refine: …</code></p>')

# ---------------------------------------------------------------- tiny SVG charts (phone-first)
INK, AMB, TEAL, GRN, RED, MUT, LINE = "#1c150d", "#e8902e", "#1f9e8e", "#54b441", "#df5236", "#6f5f46", "#d9c8a6"
FONT = "font-family=\"JetBrains Mono, monospace\""

def svg_hbars(rows, vmax, ref=None, unit="", title=None, W=360):
    """rows: (label, value, color, valuetext). One bar per row; labels above bars so they fit at 360 px."""
    h_row, top = 40, (26 if title else 6)
    H = top + h_row * len(rows) + (22 if ref else 8)
    x0, x1 = 6, W - 64
    sc = lambda v: x0 + (x1 - x0) * v / vmax
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" xmlns="http://www.w3.org/2000/svg">']
    if title: s.append(f'<text x="6" y="16" {FONT} font-size="11" fill="{MUT}" letter-spacing="1">{e(title.upper())}</text>')
    if ref:
        xr = sc(ref[0])
        s.append(f'<line x1="{xr:.1f}" x2="{xr:.1f}" y1="{top+14}" y2="{H-16}" stroke="{RED}" stroke-width="2" stroke-dasharray="4 3" opacity=".75"/>')
        s.append(f'<text x="{min(xr+4, W-150):.1f}" y="{H-4}" {FONT} font-size="10.5" fill="{RED}">{e(ref[1])}</text>')
    for i, (lab, v, col, vt) in enumerate(rows):
        y = top + i * h_row
        s.append(f'<text x="{x0}" y="{y+12}" {FONT} font-size="12" fill="{INK}">{e(lab)}</text>')
        s.append(f'<rect x="{x0}" y="{y+17}" width="{max(sc(v)-x0,2):.1f}" height="16" fill="{col}" stroke="{INK}" stroke-width="1.5"/>')
        s.append(f'<text x="{sc(v)+6:.1f}" y="{y+30}" font-family="Bricolage Grotesque, sans-serif" font-weight="800" font-size="15" fill="{INK}">{e(vt)}</text>')
    s.append("</svg>")
    return "".join(s)

def svg_dots(rows, lo, hi, ref, ref_lab, title=None, W=360, ticks=None):
    """rows: (label, value, color, valuetext). Dot-on-a-line chart; ref line (e.g. 0.5 = no ordering)."""
    h_row, top = 38, (26 if title else 6)
    H = top + h_row * len(rows) + 30
    x0, x1 = 10, W - 14
    sc = lambda v: x0 + (x1 - x0) * (v - lo) / (hi - lo)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" xmlns="http://www.w3.org/2000/svg">']
    if title: s.append(f'<text x="6" y="16" {FONT} font-size="11" fill="{MUT}" letter-spacing="1">{e(title.upper())}</text>')
    xr = sc(ref)
    s.append(f'<line x1="{xr:.1f}" x2="{xr:.1f}" y1="{top}" y2="{H-24}" stroke="{RED}" stroke-width="2" stroke-dasharray="4 3"/>')
    for i, (lab, v, col, vt) in enumerate(rows):
        y = top + i * h_row
        s.append(f'<text x="{x0}" y="{y+12}" {FONT} font-size="11.5" fill="{INK}">{e(lab)}</text>')
        s.append(f'<line x1="{x0}" x2="{x1}" y1="{y+25}" y2="{y+25}" stroke="{LINE}" stroke-width="2"/>')
        s.append(f'<line x1="{xr:.1f}" x2="{sc(v):.1f}" y1="{y+25}" y2="{y+25}" stroke="{col}" stroke-width="4"/>')
        s.append(f'<circle cx="{sc(v):.1f}" cy="{y+25}" r="7.5" fill="{col}" stroke="{INK}" stroke-width="2"/>')
        s.append(f'<text x="{W-6}" y="{y+12}" text-anchor="end" font-family="Bricolage Grotesque, sans-serif" font-weight="800" font-size="14" fill="{INK}">{e(vt)}</text>')
    for t, tl in (ticks or []):
        s.append(f'<text x="{sc(t):.1f}" y="{H-10}" text-anchor="middle" {FONT} font-size="10" fill="{MUT}">{e(tl)}</text>')
    s.append(f'<text x="{xr:.1f}" y="{H-24+12}" text-anchor="middle" {FONT} font-size="10" fill="{RED}">{e(ref_lab)}</text>' if not ticks else "")
    s.append("</svg>")
    return "".join(s)

def svg_strip(groups, W=360, title=None):
    """groups: (label, [values 0-100], color). Percentile strip chart."""
    h_row, top = 46, (26 if title else 6)
    H = top + h_row * len(groups) + 22
    x0, x1 = 10, W - 14
    sc = lambda v: x0 + (x1 - x0) * v / 100
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" xmlns="http://www.w3.org/2000/svg">']
    if title: s.append(f'<text x="6" y="16" {FONT} font-size="11" fill="{MUT}" letter-spacing="1">{e(title.upper())}</text>')
    for i, (lab, vals, col) in enumerate(groups):
        y = top + i * h_row
        s.append(f'<text x="{x0}" y="{y+12}" {FONT} font-size="11.5" fill="{INK}">{e(lab)}</text>')
        s.append(f'<line x1="{x0}" x2="{x1}" y1="{y+28}" y2="{y+28}" stroke="{LINE}" stroke-width="2"/>')
        for j, v in enumerate(vals):
            s.append(f'<circle cx="{sc(v):.1f}" cy="{y+28 + (j%3-1)*3}" r="6" fill="{col}" fill-opacity=".8" stroke="{INK}" stroke-width="1.5"/>')
    for t in (0, 50, 100):
        s.append(f'<text x="{sc(t):.1f}" y="{H-6}" text-anchor="middle" {FONT} font-size="10" fill="{MUT}">{t}th pct</text>')
    s.append("</svg>")
    return "".join(s)

def img_pair(a, b, la, lb):
    return (f'<div class="pair"><div><span class="lab">{e(la)}</span><img src="{a}" alt="{e(la)}"></div>'
            f'<div class="new"><span class="lab">{e(lb)}</span><img src="{b}" alt="{e(lb)}"></div></div>')

# ---------------------------------------------------------------- method data (copied from published pages)
M = {}
M["ecofolio"] = dict(
    issue=62, q="Q2", date="2026-11-16", verdict="Interesting", grade=("Promising but thin", ""),
    name="Mean-variance portfolio effect", short="ecofolio",
    title="Is the program book really diversified?",
    field="Salmon fisheries ecology",
    what="Judge how steady a portfolio is against how volatility grows with size, not against the average program.",
    pick="Math", pick_line="Use the budget-vs-actual gap to strip measurement noise, then refit the size law.", pick_eff="M",
    data="SYNTHETIC mock budgets (Corning_mock, MS_mock), not any firm's budget",
    pair=("Usual measure", "3.36×", "steadier than its programs (average-CV, Corning mock)",
          "Size-aware", "0.99×", "no steadier than one program that size"),
    findings=[
        dict(h="The book is no steadier than one program of the same size.",
             t="Usual measures say about 3× steadier. Allowing for how volatility grows with size gives 0.99 (Corning mock) and 1.15 (MS mock).",
             viz=lambda: svg_hbars([
                 ("Average-CV effect · Corning", 3.36, AMB, "3.36×"),
                 ("Diversification ratio · Corning", 3.14, AMB, "3.14×"),
                 ("Size-aware (mean-var) · Corning", 0.99, TEAL, "0.99×"),
                 ("Average-CV effect · MS", 3.25, AMB, "3.25×"),
                 ("Size-aware (mean-var) · MS", 1.15, TEAL, "1.15×")], 4.0, ref=(1, "1× = one program that size"),
                 title="How much steadier is the book?"),
             fig="../../fig/2026-11-16/eco_taylor.png"),
        dict(h="Part of the apparent diversification is just measurement noise.",
             t="On the mocks' noise-free true levels, the average-CV effect falls from 3.36 to 1.54 (Corning mock).",
             viz=lambda: svg_hbars([
                 ("Reported numbers", 3.36, AMB, "3.36×"),
                 ("Noise-free true levels", 1.54, TEAL, "1.54×")], 4.0, ref=(1, "1×"),
                 title="Average-CV effect, Corning mock"),
             fig=None),
        dict(h="Honest miss: a plain correlation check finds hidden groups better.",
             t="Correlation puts all 9 planted groups at the 100th percentile. The portfolio effect scatters them from the 0th to the 81st.",
             viz=lambda: svg_strip([
                 ("Plain YoY correlation", [100]*9, GRN),
                 ("Portfolio effect", [10, 81, 47, 61, 23, 0, 16, 71, 58], RED)],
                 title="Where each planted group ranks (higher = found)"),
             fig="../../fig/2026-11-16/eco_screen.png"),
    ],
    how=["Fit one line across programs: log variance against log mean spend (Taylor's power law). Its slope is <b>z</b>.",
         "Extrapolate the line to the size of the whole book: that is the volatility one program that big would have.",
         "Compare with the book's real volatility. Above 1 means real diversification.",
         "If z = 2 this equals the usual average-CV measure. Here z is 1.67 (Corning mock) and 1.77 (MS mock), so big programs are calmer and the usual measure overstates.",
         "Fast: one log-log regression, 0.1 ms per portfolio."],
    robust=["<b>Taylor's law is solid.</b> Reported since 1961 across insects, fish and plants; Cohen &amp; Xu (PNAS 2015) show why it appears.",
            "<b>The portfolio metric is thin.</b> One methods paper (Anderson, Cooper &amp; Dulvy 2013; 88 citations). Across 51 metapopulations the usual measure was stronger in 84%, by up to 7×.",
            "<b>Package:</b> v0.1.0, single author, no tests. Our reproduction of its vignette matched exactly (1.412).",
            "<b>Known failure:</b> it extrapolates about two orders of magnitude; the quadratic variant blew up here (34.7)."],
    sauce=[("Engineering", "S–M", False, "Ragged-panel port, R as oracle",
            "ecofolio needs every program in every year, so 24–28% of programs were dropped. A NumPy/Rust port could keep entrants and exiters.",
            "Parity ≤ 1e-10 with ecofolio on 1,000 random subsets; 999-shuffle null on 1,404 programs in < 1 s."),
           ("Math", "M", True, "A noise-corrected Taylor's law and portfolio effect",
            "Budget and actual are two noisy readings of each program. Their disagreement estimates the noise, which can be removed before fitting z.",
            "On both mocks plus 20 new-seed mocks, the corrected effect is closer to the true-level effect in ≥ 80% of cells. Pre-registered."),
           ("New use", "S", False, "Stability cost of FY2026 decision packages",
            "Recompute z and the effect under the minimum, current and enhanced package scenarios.",
            "Change per scenario against 999 random same-cost package swaps, stated in advance.")],
    qlinks=[("Q2.4", "Hidden structure", "Answers “is the book diversified?”; does not find groups."),
            ("Q2.3", "Real change vs noise", "Shows noise inflates diversification; per-program volatility did not flag planted movers (AUC 0.28–0.34).")],
    missing="Real program budgets and actuals.",
    page="2026-11-16.html#ecofolio",
)
M["pim"] = dict(
    issue=63, q="Q3", date="2026-11-16", verdict="Recommend", grade=("Well established", "ok"),
    name="Probabilistic index models", short="pim",
    title="How often does the more-stressed bank pay out more?",
    field="Clinical biostatistics",
    what="A rank-based regression whose effect is a plain probability: “A beats B x% of the time.”",
    pick="New use", pick_line="Flag Q2 programs whose numbers contradict their text label. Must beat the 0.78 AUC from 11-13.", pick_eff="S",
    data="Public filings (Fed DFAST results, FR Y-9C); descriptive only",
    pair=("Usual regression", "−43%", "of the slope lost when 8 of 360 extreme rows are trimmed",
          "PIM", "0.468 → 0.470", "same trim: the effect barely moves (0.4675 → 0.4697)"),
    findings=[
        dict(h="Stress-test pre-tax income orders payouts; drawdown adds nothing beyond it.",
             t="A bank one IQR better on severely adverse pre-tax income has the higher payout 68% of the time (Holm p = 0.02).",
             viz=lambda: svg_dots([
                 ("Pre-tax income, alone", 0.68, TEAL, "68%"),
                 ("Pre-tax income, given drawdown", 0.69, TEAL, "69%"),
                 ("Drawdown, alone", 0.40, AMB, "40%"),
                 ("Drawdown, given pre-tax income", 0.50, MUT, "50%")], 0.3, 0.8, 0.5, "50% = no ordering",
                 title="Chance the better-placed bank pays more"),
             fig="../../fig/2026-11-16/pim_forest.png"),
        dict(h="It holds where the usual regression is fragile.",
             t="Trimming the 8 most extreme payout ratios cuts the regression slope from −0.070 to −0.040. The PIM effect moves from 0.4675 to 0.4697.",
             viz=lambda: svg_hbars([
                 ("Usual regression (OLS + year FE)", 57, AMB, "57%"),
                 ("PIM (distance from 0.5)", 93, TEAL, "93%")], 100,
                 title="Effect kept after trimming 2% of rows"),
             note="Bars computed from the page's numbers: 0.040/0.070 and (0.5−0.4697)/(0.5−0.4675).",
             fig="../../fig/2026-11-16/pim_trim.png"),
        dict(h="Before 2020 stress showed up in dividends; after, maybe buybacks.",
             t="Pre-2020 dividends: 36% per IQR (Holm p = 0.02); buybacks 49%. Post-2020 buybacks 44% (p = 0.034), which does not survive Holm.",
             viz=lambda: svg_dots([
                 ("Dividends, 2013–19", 0.36, TEAL, "36% ✓"),
                 ("Buybacks, 2013–19", 0.49, MUT, "49%"),
                 ("Dividends, 2021–25", 0.35, MUT, "35%"),
                 ("Buybacks, 2021–25", 0.44, AMB, "44% ?")], 0.25, 0.6, 0.5, "50% = no ordering",
                 title="Deeper drawdown → pays more? (per IQR)"),
             note="✓ survives Holm · ? p < 0.05 but not after Holm.",
             fig="../../fig/2026-11-16/pim_mix.png"),
    ],
    how=["Take two banks in the <b>same test year</b>. Ask: how likely is bank A's payout above bank B's, given their stress numbers?",
         "That probability is the effect. 50% means the stress metric does not order payouts.",
         "Pairs are only formed within a year, so changes in the scenario and in payout norms cancel out.",
         "It reads ranks, so a near-zero income cannot dominate; it is a regression, so it gives partial effects.",
         "Fast: 49,500 pairs fit in 0.05 s."],
    robust=["<b>Theory:</b> JRSS-B 2012 (Thas et al.; 163 citations) with asymptotics, sandwich variance and simulations.",
            "<b>Generalises classic rank tests</b> (Wilcoxon–Mann–Whitney, Kruskal–Wallis, Friedman). Our check: PI 0.749275, identical to WMW.",
            "<b>Small-sample bias is known</b> (Amorim et al. 2018) and has published fixes.",
            "<b>Package:</b> pim 2.0.4 on CRAN, maintained by the Ghent group.",
            "<b>Known failure modes here:</b> 18–35 firms per year, ties (many zero buybacks), collinear covariates."],
    sauce=[("Engineering", "M", False, "A streaming within-block PIM fitter",
            "A Rust core that batches permutation and bootstrap refits without rebuilding pair matrices; scales to thousands of Q2 programs.",
            "β and SE parity ≤ 1e-8 with pim on all 29 models; 10,000 permutations on 360 firm-years in < 2 s."),
           ("Math", "M", False, "Firm-clustered inference for PIMs",
            "Firms repeat across years, but pim's sandwich treats firm-years as independent. Derive a two-way U-statistic variance.",
            "Simulation at our design: 95% coverage within ±1.5 points."),
           ("New use", "S", True, "Text versus numbers as a probabilistic index (Q2.2)",
            "Within each subsegment, fit P(program A grows faster than B | stated intent, cost type). The worst contradictions are text–number mismatches.",
            "AUC against the planted mismatch key; must beat 0.78 (11-13). Pre-registered.")],
    qlinks=[("Q3.1 / Q3.2", "Buffer vs path", "Pre-tax path carries the ordering; SCB alone shows no link (p = 0.20)."),
            ("Q3.4", "Adverse vs severely adverse", "The gap adds nothing (2014–19)."),
            ("Q3.5", "Dividends vs buybacks", "Tentative: dividends before 2020, maybe buybacks after.")],
    missing="Firm-level baseline projections (not published) and the October 2020 SCB PDF.",
    page="2026-11-16.html#pim",
)
M["ebnm"] = dict(
    issue=55, q="Q2", date="2026-11-13", verdict="Recommend", grade=("Not graded (edition predates grading)", "na"),
    name="Empirical Bayes normal means", short="ebnm",
    title="How much to trust each program's own number",
    field="Statistical genetics",
    what="Learn from the data how programs vary, then shrink each noisy number by the right amount. No tuning.",
    pick="New use", pick_line="A “Is this move real?” flag for every program in each budget cycle.", pick_eff="S",
    data="SYNTHETIC mock budgets (Corning_mock, MS_mock), not any firm's budget",
    pair=("Usual test (BH)", "14", "programs called “really changed” (Corning mock)",
          "ebnm", "91", "called, all with the right sign"),
    findings=[
        dict(h="It finds 6–7× more real moves, with almost no wrong signs.",
             t="Calls of “this program really changed”: 91 vs 14 (Corning mock) and 200 vs 28 (MS mock). Wrong sign: 0% and 1.5%.",
             viz=lambda: svg_hbars([
                 ("BH test · Corning", 14, AMB, "14"),
                 ("ebnm · Corning (0% wrong)", 91, TEAL, "91"),
                 ("BH test · MS", 28, AMB, "28"),
                 ("ebnm · MS (1.5% wrong)", 200, TEAL, "200")], 230,
                 title="Programs called “really changed”"),
             fig="../../fig/2026-11-13/m1_lfsr.png"),
        dict(h="Pooling cuts each program's level error by about a quarter.",
             t="Log error 0.146 → 0.108 (Corning mock) and 0.138 → 0.109 (MS mock). Programs alone in their group lose a little.",
             viz=lambda: svg_hbars([
                 ("Own number · Corning", 0.146, AMB, "0.146"),
                 ("ebnm · Corning", 0.108, TEAL, "0.108"),
                 ("Own number · MS", 0.138, AMB, "0.138"),
                 ("ebnm · MS", 0.109, TEAL, "0.109")], 0.17,
                 title="Error in 2025 level (log RMSE, lower is better)"),
             fig="../../fig/2026-11-13/m1_shrink.png"),
        dict(h="Honest: shrinkage adds nothing to the text-vs-numbers check.",
             t="Comparing with peers does the work. On the MS mock: AUC 0.777 with ebnm, 0.775 with a plain z-score.",
             viz=lambda: svg_hbars([
                 ("Absolute slope (ebnm)", 0.624, MUT, "0.624"),
                 ("Peer-relative, plain z", 0.775, AMB, "0.775"),
                 ("Peer-relative, ebnm", 0.777, TEAL, "0.777")], 1.0, ref=(0.5, "0.5 = chance"),
                 title="Finding “says grow, actually shrinking” (MS mock AUC)"),
             fig="../../fig/2026-11-13/m1_text.png"),
    ],
    how=["Each program gives one noisy number and its standard error.",
         "ebnm estimates how the true values are spread across programs (the prior) from the data itself.",
         "It then shrinks each program toward its group by an amount that depends on how noisy it is.",
         "It returns a better estimate, an interval and the <b>lfsr</b>: the chance you have the direction wrong.",
         "Fast: 0.003–0.6 s per fit on 1,000–1,700 programs."],
    robust=["<b>Grading started on 11-16, so this edition has no grade.</b> What the page records:",
            "Peer-reviewed: Willwerscheid, Carbonetto &amp; Stephens, Journal of Statistical Software 114(3), 2025.",
            "Maintained CRAN package (ebnm 1.1-42, 2025-10) from the Stephens lab; the default prior comes from Stephens (2017, Biostatistics).",
            "Checked here: 90% intervals covered 89.5% of true levels; lfsr was calibrated (11–13% wrong at 0.05–0.2)."],
    sauce=[("Engineering", "M", False, "A Rust core for the ash and point-normal fits",
            "Thousands of fits (programs × categories × cycles × bootstraps). Port the mixture-weight solve to Rust with a thin Python binding.",
            "Log-likelihood parity (−145.7808 Corning, −238.8506 MS), posterior means within 1e-6."),
           ("Math", "M–L", False, "Let the description set the prior",
            "Make the prior depend on text-derived features (category, intent, driver). Today one global prior hurt lone programs.",
            "On non-family programs beat both the own number and global ash on both mocks."),
           ("New use", "S", True, "“Is this move real?” flags every budget cycle",
            "One column per program per cycle: shrunk change, interval, lfsr. 6–7× BH's calls at ≤ 1.5% wrong sign.",
            "New-seed mock: wrong sign ≤ 5% among lfsr < 0.05 calls, ≥ 3× BH's calls.")],
    qlinks=[("Q2.1", "Borrowing strength", "Yes: 21–26% lower level error; 37% inside real families."),
            ("Q2.3", "Real change vs noise", "Calibrated program-level calls; portfolio totals were already 98% right."),
            ("Q2.2", "Text vs numbers", "Gain comes from peer comparison, not shrinkage.")],
    missing="Real program budgets and actuals (real-panel validation still owed).",
    page="2026-11-13.html#ebnm",
)
M["denselines"] = dict(
    issue=56, q="Q2", date="2026-11-13", verdict="Interesting", grade=("Not graded (edition predates grading)", "na"),
    name="DenseLines (density line charts)", short="DenseLines",
    title="A thousand short lines as one picture",
    field="Visualization research",
    what="Give every series one unit of ink per column, so a thousand lines become a readable density, not spaghetti.",
    pick="Engineering", pick_line="Gap-safe, weighted DenseLines in Rust with a Python binding.", pick_eff="S–M",
    data="SYNTHETIC mock budgets (Corning_mock, MS_mock), not any firm's budget",
    pair=None,
    findings=[
        dict(h="The shared 2022–24 dip and the 2025 split appear; spaghetti hides them.",
             t="1,052 Corning-mock programs, each indexed to its own mean. Same data, two drawings.",
             viz=lambda: img_pair("../img/denselines_spaghetti.png", "../img/denselines_density.png", "Spaghetti", "DenseLines"),
             viz_feed=lambda: img_pair("img/denselines_spaghetti.png", "img/denselines_density.png", "Spaghetti", "DenseLines"),
             fig="../../fig/2026-11-13/m2_hero.png"),
        dict(h="The authors' code breaks on programs that start or stop.",
             t="One partial series turns a column blank (NaN). 274 of 1,052 Corning-mock programs are partial, so every column fails. Our one-line fix: none.",
             viz=lambda: svg_hbars([
                 ("Reference code (MS mock panel)", 500, RED, "500 / 500"),
                 ("Gap-safe fix", 0, TEAL, "0 / 500")], 600,
                 title="Columns that come out blank"),
             fig="../../fig/2026-11-13/m2_startstop.png"),
        dict(h="Chart plus keyword finds 94% of a hidden group, but it is fragile.",
             t="AI-demand group, Corning mock. The brush works at 2–4 px smoothing and vanishes at 6–8 px.",
             viz=lambda: svg_hbars([
                 ("Text keyword only", 66, AMB, "66%"),
                 ("Chart brush only", 75, AMB, "75%"),
                 ("Brush OR keyword", 94, TEAL, "94%")], 110,
                 title="Share of the hidden group found (recall)"),
             note="Precision: 100%, 51% and 56%.",
             fig="../../fig/2026-11-13/m2_residual_corning.png"),
    ],
    how=["Draw each series into its own picture.",
         "In each column, divide that series' ink by how many pixels it covers, so a steep noisy line does not paint more.",
         "Add all the pictures: every column now holds exactly n units. Ridges are trends; faint strands are outliers.",
         "No parameters beyond canvas size.",
         "Our NumPy port matches the authors' Rust pixel for pixel (≤ 2.1e-7) but is 10–120× slower."],
    robust=["<b>Grading started on 11-16, so this edition has no grade.</b> What the page records:",
            "Source: Moritz &amp; Fisher (2018), arXiv:1808.06019 (cs.HC), with the first author's own Rust and WebGL implementations.",
            "Checked here: exact parity with the reference; a NaN bug in the reference on partial series.",
            "At our 5–6 points per line the normalisation barely matters (noisiest 10% take 12.0% vs 10.7% of ink). The paper's gain is for long, high-frequency series."],
    sauce=[("Engineering", "S–M", True, "Gap-safe, weighted DenseLines in Rust",
            "The reference fails on start/stop programs and the port is slow. Rust core with gap-safe columns, weights and a live-count channel.",
            "≤ 1e-6 vs commit 083890c, zero NaN columns on both mocks, ≤ 2× reference time at 10,000 series."),
           ("Math", "M", False, "Posterior DenseLines",
            "Draw each program's probable path (ebnm posterior draws), not its noisy reported one.",
            "Closer to the true-path chart than today's (0.053 / 0.035), no false branch with clusters switched off."),
           ("New use", "S", False, "Residual brush plus text keyword as a group finder",
            "Text and chart find different members; together 94% recall. Needs a bandwidth-free branch test.",
            "Recall ≥ 0.7 at precision ≥ 0.5 on both mocks at any smoothing from 2 to 8 px.")],
    qlinks=[("Q2.5", "Seeing many short series", "Yes: a density view plus a live-count strip."),
            ("Q2.4", "Hidden structure", "Points at groups; not a test (bandwidth-fragile).")],
    missing="Real program budgets; Rust parity check still owed.",
    page="2026-11-13.html#denselines",
)
for k, m in M.items():
    st = STATE[str(m["issue"])]
    m["status"], m["slug"] = st["status"], k
    budget(m["what"], 22, k + " what"); budget(m["pick_line"], 22, k + " pick")
    for f in m["findings"]:
        budget(f["h"], 14, k + " headline"); budget(f["t"], 32, k + " takeaway")

# ---------------------------------------------------------------- every method, for the ranked queue (one-liners from the pages)
VPTS = {"Recommend": 3, "Adopt-candidate": 3, "Interesting": 2, "Watchlist": 0}
ALL = {  # issue: (verdict, one-liner)
    46: ("Adopt-candidate", "The VIX→spread link roughly doubles when NFCI > 0.06; tree splits did not forecast out of sample."),
    47: ("Interesting", "0 mean breaks but 35 distribution breaks in weekly changes; no false breaks on shuffled data."),
    48: ("Recommend", "Market covariates explain 59–74% of share changes for three dealers, but only 22% for GS."),
    49: ("Interesting", "A “who moved” readout, once a break clears a persistence null."),
    50: ("Recommend", "Python port at 1,260/1,280 parity. Accept the 20 R quirks, or pre-register the power curve (P2)?"),
    51: ("Interesting", "Flow matrices on consecutive quarters are not identified; a planted 1% flow is not recovered."),
    52: ("Recommend", "Raw dealer volumes co-move (VR 4.45 vs null 0.44–2.00); foreign IHC volumes do not."),
    53: ("Recommend", "Approved 11-13, direction still open. JPM–GS ρ −0.698, −0.882 after removing the market."),
    54: ("Watchlist", "Your MD's pick (11-12). Watchlist only, not a scout method."),
    55: ("Recommend", M["ebnm"]["findings"][0]["h"]),
    56: ("Interesting", M["denselines"]["findings"][0]["h"]),
    57: ("Interesting", "Fails and the rate spread move in step the same week (p = 0.011), but not after July 2025."),
    58: ("Recommend", "Stress pre-tax income gives 15% skill on next payouts; the SCB itself has none."),
    59: ("Interesting", "Fails and leveraged-fund positioning both cross-map the repo spread; Holm-borderline."),
    60: ("Recommend", "Repo mix alone recovers calendar order; a “mix clock” dates new months with 1.06-yr error vs 1.92."),
    62: ("Interesting", M["ecofolio"]["findings"][0]["h"]),
    63: ("Recommend", M["pim"]["findings"][0]["h"]),
}
WAITING = {53: "Approved 11-13; the direction for this work is still yours to set.", 50: "Accept the 20 R quirks and pause, or pre-register P2."}
ONEPAGER = {62: "ecofolio", 63: "pim", 55: "ebnm", 56: "denselines"}

def fit_pts(q): return 2 if q in ("Q1", "Q2", "Q3") else (0 if q == "watchlist" else 1)

def rows_all():
    out = []
    for n, (v, one) in ALL.items():
        st = STATE[str(n)]
        budget(one, 20, f"one-liner {n}")
        out.append(dict(n=n, method=st["method"], q=st["question"], status=st["status"], pick=st["top_pick"],
                        date=st["scout_date"], page=st["page"] + st["page_anchor"], verdict=v, one=one,
                        score=VPTS[v] * fit_pts(st["question"]), vp=VPTS[v], fp=fit_pts(st["question"])))
    return out

# ---------------------------------------------------------------- page shell
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800'
         '&family=Newsreader:ital,opsz,wght@0,6..72,400..600;1,6..72,400..500&family=JetBrains+Mono:wght@400;500;700&display=swap">')

def page(title, body, depth=0, wide=False):
    up = "../" * depth
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
{FONTS}
<link rel="stylesheet" href="/research-lab/assets/brief.css">
<link rel="stylesheet" href="{up}proposals.css">
{ICON_HEAD}
<meta name="robots" content="noindex">
</head><body>
<header class="topbar"><a class="brand" href="{up}index.html">Methods scout <span class="mockflag">LAYOUT MOCKUP</span></a>
<a href="{BASE}/index.html">Live site</a></header>
<div class="pz{' wide' if wide else ''}">
{body}
</div>
<footer class="pf">Layout proposal, 2026-11-17. Not the live daily page; nothing in the daily generator changed. Every number is copied from a published scout edition or feedback-state.json.
Status chips refresh from the GitHub issue when the page loads. Q2 numbers are on SYNTHETIC mock budgets; no private rows are shown.</footer>
<script src="{up}status.js"></script>
</body></html>"""

def finding_card(m, f, idx, for_feed=True, depth=0):
    """Front-door card: one finding, one picture, one line, chips, respond."""
    link = f"m/{m['slug']}.html" if depth == 0 else f"{m['slug']}.html"
    viz = (f.get("viz_feed") or f["viz"])() if for_feed else f["viz"]()
    note = f'<p class="small">{e(f["note"])}</p>' if f.get("note") else ""
    call = " call" if m["status"] in ("proposed", "refine") else ""
    shade = {0: "", 1: " teal", 2: " red"}[idx] if "Honest" not in f["h"] else " red"
    return f"""<article class="fcard{shade} {m['q']}{call}">
<div class="viz">{viz}</div>
<div class="body"><div class="chips"><a class="chip m" href="{link}">{e(m['short'])}</a>{chip_q(m['q'])}{chip_status(m['status'], m['issue'])}<span class="date">{m['date']}</span></div>
<h3><a href="{link}#t1">{e(f['h'])}</a></h3><p class="take">{e(f['t'])}</p>{note}</div>
<div class="act"><a class="btn ghost" href="{link}">Open method →</a><a class="btn" href="{REPO}/issues/{m['issue']}">Respond #{m['issue']}</a></div>
</article>"""

# ---------------------------------------------------------------- C: per-method one-pager
def method_page(m):
    p = m["pair"]
    pair = ""
    if p:
        pair = (f'<div class="pair"><div><span class="lab">{e(p[0])}</span><div class="big">{e(p[1])}</div><div class="sub">{e(p[2])}</div></div>'
                f'<div class="new"><span class="lab">{e(p[3])}</span><div class="big">{e(p[4])}</div><div class="sub">{e(p[5])}</div></div></div>')
    else:
        pair = m["findings"][0]["viz"]()
    finds = []
    for i, f in enumerate(m["findings"], 1):
        note = f'<p class="small">{e(f["note"])}</p>' if f.get("note") else ""
        fig = (f'<details class="qrow" style="margin-top:.4rem"><summary><span></span><span class="small">Original chart from the edition (tap)</span><span class="chev">›</span></summary>'
               f'<div class="drawer"><a href="{f["fig"]}"><img src="{f["fig"]}" alt="original figure" style="width:100%;border:2px solid #1c150d"></a></div></details>') if f.get("fig") else ""
        finds.append(f"""<article class="fcard{' red' if 'Honest' in f['h'] else ''}"><div class="viz">{f['viz']()}</div>
<div class="body"><span class="chip">Finding {i}</span><h3>{e(f['h'])}</h3><p class="take">{e(f['t'])}</p>{note}{fig}</div></article>""")
    sauce = "".join(
        f'<div class="sauce{" top" if top else ""}"><span class="t">{i} · {e(kind)} · Effort {e(eff)}{" · ★ Top pick" if top else ""}</span>'
        f'<h5>{e(t)}</h5><p>{e(d)}</p><p class="small"><b>Test.</b> {e(test)}</p></div>'
        for i, (kind, eff, top, t, d, test) in enumerate(m["sauce"], 1))
    ql = "".join(f'<div class="sauce"><span class="t">{e(a)} · {e(b)}</span><p>{e(c)}</p></div>' for a, b, c in m["qlinks"])
    g, gcls = m["grade"]
    body = f"""<p class="crumb"><a href="../feed.html">← Feed</a> · <a href="../queue.html">Queue</a></p>
<div class="chips">{chip_q(m['q'])}{chip_status(m['status'], m['issue'])}{chip_v(m['verdict'])}<span class="date">Scouted {m['date']}</span></div>
<section class="hero" style="padding-top:.5rem"><p class="kicker">{e(m['name'])} · from {e(m['field'])}</p>
<h1>{e(m['title'])}</h1></section>
<div class="sum">
<div class="row"><span class="k">What it is</span><span class="v">{e(m['what'])}</span></div>
<div class="row"><span class="k">Verdict</span><span class="v"><b>{e(m['verdict'])}.</b> Home field: {e(g.split(' (')[0].lower())}.</span></div>
<div class="row"><span class="k">Top pick</span><span class="v"><b>{e(m['pick'])}</b> (effort {e(m['pick_eff'])}): {e(m['pick_line'])}</span></div>
<div class="row"><span class="k">Data</span><span class="v">{e(m['data'])}</span></div>
</div>
<p class="kicker" style="margin-top:1rem">The one picture</p>
{pair}
<div style="margin:1rem 0 .4rem">{respond(m['issue'], big=True)}</div>
<div class="tabs">
<input type="radio" name="tab" id="t1" checked><input type="radio" name="tab" id="t2"><input type="radio" name="tab" id="t3"><input type="radio" name="tab" id="t4"><input type="radio" name="tab" id="t5">
<div class="tabbar"><label for="t1">Findings</label><label for="t2">How it works</label><label for="t3">Robust at home</label><label for="t4">Secret sauce</label><label for="t5">Questions</label></div>
<div class="panels">
<div class="panel p1">{''.join(finds)}</div>
<div class="panel p2"><ol>{''.join(f'<li>{x}</li>' for x in m['how'])}</ol><p class="small">Formulas and full tables: <a href="../../{m['page']}">the {m['date']} edition</a>.</p></div>
<div class="panel p3"><p><span class="grade {gcls}">{e(g)}</span></p><ul>{''.join(f'<li>{x}</li>' for x in m['robust'])}</ul></div>
<div class="panel p4">{sauce}<p class="small">👍 on the issue means go with the ★ top pick; comment <code>go math</code>, <code>go engineering</code> or <code>go new use</code> to choose another.</p></div>
<div class="panel p5">{ql}<p class="small"><b>Still missing:</b> {e(m['missing'])} · <a href="{REPO}/blob/main/docs/methods-scout/QUESTIONS.md">All questions</a></p></div>
</div></div>
<div style="margin:1.4rem 0">{respond(m['issue'])}</div>
<script>/* deep-link a tab: #t1..#t5 */(function(){{var h=location.hash.slice(1);var el=document.getElementById(h);if(el&&el.type==="radio")el.checked=true;}})();</script>"""
    return page(f"{m['name']} · method page (mockup)", body, depth=1)

# ---------------------------------------------------------------- A: finding feed
def feed_page():
    cards = []
    for k in ("ecofolio", "pim", "ebnm", "denselines"):   # newest edition first
        m = M[k]
        for i, f in enumerate(m["findings"]):
            cards.append(finding_card(m, f, i))
    body = f"""<section class="hero"><p class="kicker">Front door A · Finding feed</p>
<h1>One finding per card</h1>
<p class="lede">Each card is one result: a picture, one plain line, and who it belongs to. Tap the method chip for the full page. About 20 seconds a card.</p>
<div class="legend">{''.join(f'<span class="chip st-{s}">{i} {l}</span>' for s, (i, l) in STATUS.items() if s in ('proposed','approved','in-progress','refine','parked'))}</div></section>
<div class="filt">
<input type="radio" name="f" id="f-all" checked><input type="radio" name="f" id="f-q2"><input type="radio" name="f" id="f-q3"><input type="radio" name="f" id="f-call">
<div class="fbar"><label for="f-all">All</label><label for="f-q2">Q2</label><label for="f-q3">Q3</label><label for="f-call">Needs your call</label></div>
<div class="feed">{''.join(cards)}</div></div>
<p class="small">Mockup shows the four methods with one-pagers (12 findings). The real feed would hold every method's findings, newest first.</p>"""
    return page("Front door A · finding feed (mockup)", body)

# ---------------------------------------------------------------- B: ranked queue
def qrow(r, rank=None, wait=None):
    ic, lab = STATUS[r["status"]]
    link = f"m/{ONEPAGER[r['n']]}.html" if r["n"] in ONEPAGER else f"../{r['page']}"
    linklab = "Open method page →" if r["n"] in ONEPAGER else f"Open {r['date']} edition →"
    why = (f'<span class="score">Rank score {r["score"]} = verdict {r["vp"]} × question fit {r["fp"]}</span>' if rank else "")
    ask = f'<p><b>Your call:</b> {e(wait)}</p>' if wait else ""
    rk = rank if rank else ic
    return f"""<details class="qrow{' wait' if wait else ''}"><summary><span class="rk">{rk}</span>
<span><span class="nm">{e(r['method'])}</span><p class="one">{e(r['one'])}</p>
<span class="chips">{chip_status(r['status'], r['n'])}{chip_q(r['q'])}{chip_v(r['verdict']) if r['verdict']!='Watchlist' else ''}</span></span><span class="chev">›</span></summary>
<div class="drawer">{ask}{why}<p><b>Top pick:</b> {e(PICK[r['pick']])} · scouted {r['date']}</p>
<p><a class="btn" href="{REPO}/issues/{r['n']}">Respond #{r['n']}</a> <a class="btn ghost" href="{link}">{linklab}</a></p>
<p class="howto">👍 go · 👎 drop · 👀 park · or comment <code>refine: …</code></p></div></details>"""

def queue_sections():
    R = rows_all()
    by = {r["n"]: r for r in R}
    waiting = [qrow(by[n], wait=w) for n, w in WAITING.items()]
    todo = sorted([r for r in R if r["status"] == "proposed"], key=lambda r: (-r["score"], r["date"]), reverse=False)
    todo = sorted(todo, key=lambda r: (-r["score"], -int(r["date"].replace("-", ""))))
    ranked = [qrow(r, rank=i) for i, r in enumerate(todo, 1)]
    moving = [qrow(r) for r in R if r["status"] == "approved"]
    parked = [qrow(r) for r in R if r["status"] == "parked"]
    return waiting, ranked, moving, parked, todo

RULE = """<div class="rule"><b>How the ranking works.</b> <code>score = verdict × question fit</code>.
Verdict: recommend or adopt-candidate = 3, interesting = 2. Question fit: a live question (Q1, Q2, Q3) = 2, the old Q1 or none = 1.
Ties go to the newest. Both inputs are already on each method's page; nothing is hidden. (Home-field grade and top-pick effort join the rule once every method has them.)</div>"""

def queue_page():
    waiting, ranked, moving, parked, _ = queue_sections()
    body = f"""<section class="hero"><p class="kicker">Front door B · Ranked queue</p>
<h1>Work down the list</h1>
<p class="lede">Every scouted method, in one order. Top: what is blocked on you. Then the undecided methods, best first. Tap a row for the one-paragraph drawer.</p>
<div class="legend">{''.join(f'<span class="chip st-{s}">{i} {l}</span>' for s, (i, l) in STATUS.items() if s in ('proposed','approved','in-progress','refine','parked'))}</div></section>
<h2 class="sect">Waiting on you <span class="cnt">{len(waiting)}</span></h2>{''.join(waiting)}
<h2 class="sect">Undecided, ranked <span class="cnt">{len(ranked)}</span></h2>{RULE}{''.join(ranked)}
<h2 class="sect">Moving <span class="cnt">{len(moving)}</span></h2>{''.join(moving)}
<h2 class="sect">Parked <span class="cnt">{len(parked)}</span></h2>{''.join(parked)}"""
    return page("Front door B · ranked queue (mockup)", body)

# ---------------------------------------------------------------- Hybrid: queue head + feed
def hybrid_page():
    waiting, ranked, moving, parked, todo = queue_sections()
    newest = [finding_card(M[k], M[k]["findings"][0], 0) for k in ("ecofolio", "pim")]
    older = [finding_card(M[k], M[k]["findings"][0], 0) for k in ("ebnm", "denselines")]
    body = f"""<section class="hero"><p class="kicker">Front door A+B · Hybrid</p>
<h1>Today, in three blocks</h1>
<p class="lede">First what is blocked on you, then the top three undecided methods, then the newest findings as picture cards.</p></section>
<h2 class="sect">1 · Waiting on you <span class="cnt">{len(waiting)}</span></h2>{''.join(waiting)}
<h2 class="sect">2 · Top of the queue <span class="cnt">3 of {len(ranked)}</span></h2>{''.join(ranked[:3])}
<p class="small"><a href="queue.html">See the full ranked queue →</a></p>
<h2 class="sect">3 · New findings <span class="cnt">2026-11-16</span></h2>{''.join(newest)}
<h2 class="sect">Earlier <span class="cnt">2026-11-13</span></h2>{''.join(older)}
<p class="small"><a href="feed.html">See every finding →</a></p>"""
    return page("Front door hybrid (mockup)", body)

# ---------------------------------------------------------------- comparison index
def index_page():
    def opt(cls, shot, href, tag, h, pts):
        return (f'<div class="opt{cls}"><a class="shot" href="{href}"><img src="img/shot-{shot}.png" alt="{e(h)} at phone width"></a>'
                f'<div class="ob"><span class="chip">{e(tag)}</span><h3><a href="{href}">{e(h)}</a></h3><ul>{"".join(f"<li>{p}</li>" for p in pts)}</ul>'
                f'<p><a class="btn" href="{href}">Open</a></p></div></div>')
    doors = "".join([
        opt("", "feed", "feed.html", "Front door A", "Finding feed",
            ["One result per card: picture, one line, method · question · status chips.",
             "Best for “what did we learn?” on the commute.",
             "Filter: Q2 · Q3 · Needs your call (no JS)."]),
        opt("", "queue", "queue.html", "Front door B", "Ranked queue",
            ["Every method in one ordered list; <b>Waiting on you</b> at the top.",
             "Rank = verdict × question fit, shown on each row.",
             "Tap a row: drawer with top pick, Respond, method page."]),
        opt("", "hybrid", "hybrid.html", "Front door A+B", "Hybrid",
            ["Waiting on you → top 3 of the queue → newest finding cards.",
             "One screen answers “what do you need from me?” and “what's new?”.",
             "Full queue and full feed one tap away."]),
    ])
    pagers = "".join(
        f'<div class="opt base"><a class="shot" href="m/{k}.html"><img src="img/shot-m-{k}.png" alt="{e(M[k]["short"])} page at phone width"></a>'
        f'<div class="ob"><span class="chip">C · method page</span><h3><a href="m/{k}.html">{e(M[k]["short"])}</a></h3><p class="small">{e(M[k]["title"])}</p></div></div>'
        for k in ("ecofolio", "pim", "ebnm", "denselines"))
    body = f"""<section class="hero"><p class="kicker">Layout proposals · 2026-11-17</p>
<h1>A cleaner scout</h1>
<p class="lede">Settled: <b>one page per method</b> (C), with a 3-second summary and tabs. Open: which <b>front door</b> leads into those pages. Three options below, each built with real scout content and screenshotted at phone width.</p>
<div class="legend">{''.join(f'<span class="chip st-{s}">{i} {l}</span>' for s, (i, l) in STATUS.items())}</div>
<p class="small">One icon and one plain word per status, everywhere. Chips refresh from the GitHub issue labels on load.</p></section>
<h2 class="sect">Pick a front door</h2>
<div class="cmp">{doors}</div>
<h2 class="sect">The base: one page per method (C)</h2>
<p>Top of every method page: <b>what it is</b> (one line), <b>verdict</b>, <b>top pick</b>, <b>data</b>, then <b>the one picture</b> as a “usual tool vs this method” pair, then one big Respond button. Everything else sits behind tabs: <b>Findings · How it works · Robust at home · Secret sauce · Questions</b>.</p>
<div class="cmp" style="grid-template-columns:repeat(auto-fit,minmax(160px,1fr))">{pagers}</div>
<h2 class="sect">Borrowed from the Nitro proposals site</h2>
<ul>
<li><b>One card = one thing.</b> Picture first, one-line why, a status chip, one button. No paragraphs on the front door.</li>
<li><b>“Today vs proposed” picture pairs.</b> Nitro shows today's screen next to the mockup; we show the usual tool's answer next to the borrowed method's.</li>
<li><b>Status is a chip that updates itself</b> from the issue (Nitro's <code>status.js</code>), with a vote button and a one-line how-to on every card and at the top and bottom of every detail page.</li>
<li><b>Index → one page per item.</b> Nitro links each card to <code>p/&lt;slug&gt;.html</code>; that is the method page here.</li>
</ul>
<p class="small">Kept ours: the paper-and-ink theme, fonts, hard shadows and the Respond-on-GitHub loop. No Nitro branding or wording was copied.</p>
<h2 class="sect">Word budgets (enforced by the build)</h2>
<ul><li>Finding headline ≤ 14 words; takeaway ≤ 32 words.</li><li>Queue one-liner ≤ 20 words; “what it is” and “top pick” ≤ 22 words.</li><li>Charts are drawn at 360 px wide with labels above bars, so nothing is unreadable on a phone.</li></ul>
<div class="rec"><h3>Recommendation</h3>
<p style="color:#f5ecd7">Hybrid front door, on top of the per-method pages.</p>
<ul><li><b>Waiting on you first</b>, because the daily loop only moves when you react.</li>
<li><b>Top 3 of the ranked queue</b>, so the order is decided for you, without a 17-row list every morning.</li>
<li><b>Newest finding cards last</b>, because one picture plus one line is the fastest way to grasp a method.</li>
<li>The full feed and the full queue stay one tap away, and the dated editions stay as the archive.</li></ul></div>
<p class="small">Next step if you like one: switch the daily generator to write a method page per method plus the chosen front door, and keep the dated pages as the archive. Nothing on the live site changed yet.</p>"""
    return page("Methods scout layout proposals", body, wide=True)

STATUS_JS = """// Progressive enhancement (idea borrowed from the Nitro proposals site): refresh status chips from the live issues.
(function(){
  var els=document.querySelectorAll("[data-issue]"); if(!els.length) return;
  var MAP={"proposed":["\\u25cb","New"],"approved":["\\u2713","Go"],"in-progress":["\\u25b6","Building"],"refine":["\\u270e","Needs direction"],
           "parked":["\\u275a\\u275a","Parked"],"dropped":["\\u2715","Dropped"],"promoted":["\\u2605","Promoted"]};
  fetch("https://api.github.com/repos/jgridifier/research-lab/issues?labels=scout&state=all&per_page=100",{headers:{Accept:"application/vnd.github+json"}})
    .then(function(r){return r.ok?r.json():null}).then(function(list){
      if(!list) return; var by={};
      list.forEach(function(i){var s=null;(i.labels||[]).forEach(function(l){var n=l.name||"";if(n.indexOf("status:")===0)s=n.slice(7);});
        if(i.state==="closed"&&!s)s="dropped"; if(s&&MAP[s])by[i.number]=s;});
      els.forEach(function(el){var s=by[el.getAttribute("data-issue")]; if(!s) return;
        el.className="chip st-"+s; el.textContent=MAP[s][0]+" "+MAP[s][1];});
    }).catch(function(){});
})();
"""

def main():
    (OUT / "m").mkdir(parents=True, exist_ok=True)
    (OUT / "status.js").write_text(STATUS_JS)
    for k, m in M.items():
        (OUT / "m" / f"{k}.html").write_text(method_page(m))
    (OUT / "feed.html").write_text(feed_page())
    (OUT / "queue.html").write_text(queue_page())
    (OUT / "hybrid.html").write_text(hybrid_page())
    (OUT / "index.html").write_text(index_page())
    print("built", sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob("*.html")))

if __name__ == "__main__":
    main()
