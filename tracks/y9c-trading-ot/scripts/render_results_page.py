"""Render docs/tracks/y9c-trading-ot/results/index.html from committed aggregate tables.

v1.1 layout: primary gate on 2014Q1-2026Q2, the subperiod rule, P3 next to the R1 companion (v1.0 design).
While results/tables/gate.json does not exist (OOS not run), the page is rendered
as a template with every verdict marked PENDING and no OOS numbers. Static HTML,
shared site.css, no scripts, no external requests.
"""
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trading_ot.paths import DESIGN_PATH_V1_1, RESULTS, TRIALS_PATH  # noqa: E402
from statement_forecast.prereg import (TRADING_OT_V1_1_PREREG_COMMIT as V11_COMMIT,  # noqa: E402
                                       TRADING_OT_V1_1_PREREG_SHA256 as V11_SHA)
from trading_ot.run import trial_count  # noqa: E402

OT_PAGE = '../../../notes/ot_classical_learning.html'
STYLE = """
    .prose code, .prose a, .prose p, .prose li, .prose td, .callout { overflow-wrap: anywhere; word-break: break-word; }
    .table-scroll { max-width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
    .verdict { display: inline-block; padding: .15rem .55rem; border: 2px solid #0b1f3a; color: #0b1f3a; font-weight: 700; letter-spacing: .04em; }
    .placeholder { border: 1px dashed #0b1f3a; padding: .9rem 1rem; color: #111; background: #fff; margin: .8rem 0 1.2rem; }
    @media (max-width: 640px) {
      .site-nav__inner { flex-wrap: wrap; }
      .site-nav__links { flex-wrap: wrap; }
      .site-nav__links a { padding: .5rem .55rem; }
    }
"""


def e(x):
    return html.escape(str(x))


def _fmt(v, fmt):
    try:
        return fmt.format(v) if v is not None and v == v else '—'
    except (TypeError, ValueError):
        return '—'


HYPS = [('H1', 'H1 · §4 BARY-EW (equal-weight W₂ barycenter, annually refreshed bank set)', 'B* (epoch)'),
        ('H2', 'H2 · §3 WAR-RM (Wasserstein AR + rank map, cross-section)', 'B*<sub>CS</sub> (epoch)')]


def gate_rows(gate):
    rows = []
    for key, label, comp in HYPS:
        g = ((gate or {}).get('hypotheses') or {}).get(key, {})
        sp = g.get('subperiods') or {}
        n_pos = sum(1 for v in sp.values() if (v.get('G') or 0) > 0) if sp else None
        rows.append(f"<tr><td>{label}</td><td>{comp}</td><td>{_fmt(g.get('G'), '{:+.1%}')}</td>"
                    f"<td>{_fmt((g.get('dm') or {}).get('p'), '{:.3f}')}</td><td>{_fmt(g.get('p_holm'), '{:.3f}')}</td>"
                    f"<td>{_fmt(g.get('G_U'), '{:+.1%}')}</td><td>{_fmt(g.get('coverage90'), '{:.2f}')}</td>"
                    f"<td>{_fmt(g.get('lobo_min'), '{:+.1%}')}</td><td>{_fmt(n_pos, '{:d} of 3')}</td>"
                    f"<td>{_fmt(g.get('n_targets'), '{:d}')}</td>"
                    f"<td><span class=\"verdict\">{e(g.get('verdict', 'PENDING'))}</span></td></tr>")
    return '\n'.join(rows)


def subperiod_rows(gate):
    rows = []
    for key, label, _ in HYPS:
        sp = (((gate or {}).get('hypotheses') or {}).get(key) or {}).get('subperiods') or {}
        for p, rng in [('P1', '2014Q1–2017Q4'), ('P2', '2018Q1–2021Q4'), ('P3', '2022Q1–2026Q2')]:
            v = sp.get(p, {})
            rows.append(f"<tr><td>{key}</td><td>{p} · {rng}</td><td>{_fmt(v.get('G'), '{:+.1%}')}</td>"
                        f"<td>{_fmt(v.get('p'), '{:.3f}')}</td><td>{_fmt(v.get('coverage90'), '{:.2f}')}</td>"
                        f"<td>{_fmt(v.get('lobo_min'), '{:+.1%}')}</td><td>{_fmt(v.get('n_targets'), '{:d}')}</td>"
                        f"<td><span class=\"verdict\">{'PENDING' if not v else ('G &gt; 0' if (v.get('G') or 0) > 0 else 'G ≤ 0')}</span></td></tr>")
    return '\n'.join(rows)


def p3_r1_rows(gate, r1):
    rows = []
    for key, _, _ in HYPS:
        p3 = ((((gate or {}).get('hypotheses') or {}).get(key) or {}).get('subperiods') or {}).get('P3', {})
        r = ((r1 or {}).get('hypotheses') or {}).get(key, {})
        rows.append(f"<tr><td>{key}</td><td>{_fmt(p3.get('G'), '{:+.1%}')}</td><td>{_fmt(p3.get('p'), '{:.3f}')}</td>"
                    f"<td>{_fmt(r.get('G'), '{:+.1%}')}</td><td>{_fmt((r.get('test_A') or {}).get('p'), '{:.3f}')}</td>"
                    f"<td><span class=\"verdict\">{'PENDING' if not r else 'non-gating'}</span></td></tr>")
    return '\n'.join(rows)


SET_COUNTS = [('2013Q4', 12), ('2014Q4', 16), ('2015Q4', 17), ('2016Q4', 18), ('2017Q4', 18), ('2018Q4', 19),
              ('2019Q4', 17), ('2020Q4', 19), ('2021Q4', 19), ('2022Q4', 21), ('2023Q4', 22), ('2024Q4', 19),
              ('2025Q4', 21)]


def render():
    design = json.loads(DESIGN_PATH_V1_1.read_text(encoding='utf-8'))
    gate_path, r1_path = RESULTS / 'tables/gate.json', RESULTS / 'tables/r1.json'
    gate = json.loads(gate_path.read_text()) if gate_path.exists() else None
    r1 = json.loads(r1_path.read_text()) if r1_path.exists() else None
    pending = gate is None
    trials = trial_count(TRIALS_PATH)
    authorized = bool(design.get('oos_authorized'))
    headline = 'Verdict: PENDING (out-of-sample scoring not run)' if pending else e(gate.get('headline', 'Primary gate'))
    status = ("<div class=\"callout\"><strong>Status: OOS not run. Design v1.1 is pinned and awaiting approval.</strong> "
              "<code>tracks/y9c-trading-ot/test_design_trading_ot_v1_1.json</code> (prereg addendum v1.1, extended history "
              f"2008–2026) is pinned in its own commit <code>{e(V11_COMMIT[:7])}</code>, sha256 <code>{e(V11_SHA[:12])}…</code>. "
              f"<code>oos_authorized</code> is <strong>{str(authorized).lower()}</strong>, so the pipeline refuses to score "
              "any 2014Q1+ target. The leakage tests pass. No out-of-sample forecast, score or test statistic has been "
              f"computed. Trials logged on OOS data: <strong>{trials}</strong> (the log holds only the v1.0 → v1.1 "
              "design revision, which is not a trial).</div>") if pending else ''
    ph = lambda what: f'<div class="placeholder"><strong>PENDING.</strong> {what}</div>' if pending else ''
    set_cells = ''.join(f'<td>{n}</td>' for _, n in SET_COUNTS)
    set_heads = ''.join(f'<th>{q}</th>' for q, _ in SET_COUNTS)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Y-9C Trading Revenue × OT: Results — Research Lab</title>
  <meta name="description" content="Pre-registered forecasts of FR Y-9C trading revenue (BHCKA220): per-bank baselines with optimal-transport layers (W2 barycenters, Wasserstein autoregression)." />
  <link rel="stylesheet" href="../../../assets/site.css" />
  <style>{STYLE}  </style>
</head>
<body>
<nav class="site-nav" aria-label="Site navigation">
  <div class="site-nav__inner">
    <a class="site-nav__logo" href="../../../index.html">Research Lab</a>
    <ul class="site-nav__links">
      <li><a href="../../../index.html">Home</a></li>
      <li><a href="../index.html" class="active">Trading × OT</a></li>
      <li><a href="../../y9c-panel/index.html">Y-9C Panel</a></li>
      <li><a href="{OT_PAGE}">Classical OT guide</a></li>
    </ul>
  </div>
</nav>
<header class="page-header">
  <div class="page-header__inner">
    <div class="page-header__eyebrow">Track · Results · Pre-registered v1.1</div>
    <h1>Y-9C trading revenue: baselines + optimal-transport layers</h1>
    <p class="page-header__sub">Next-quarter BHCKA220 (Schedule HI 5.c), 50 one-step targets 2014Q1–2026Q2, walk-forward from 2009Q1. Research only.</p>
  </div>
</header>
<main class="page-content prose">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="../../../index.html">Home</a><span aria-hidden="true"> › </span>
    <a href="../index.html">Trading × OT</a><span aria-hidden="true"> › </span>Results
  </nav>
  {status}
  <h2>{headline}</h2>
  <p>One primary gate: two hypotheses on the 2014Q1–2026Q2 targets, Holm-adjusted across the pair (FWER 0.05). The methods come from the classical-OT guide:
  <a href="{OT_PAGE}#family-4">§4 barycenters for forecast combination</a> (H1) and
  <a href="{OT_PAGE}#family-3">§3 density time series in Wasserstein space</a> (H2).</p>
  <p><strong>PASS</strong> needs all five: Holm p &lt; 0.05; relative CRPS gain G ≥ 3%; pooled 90% coverage in [0.80, 0.97];
  G &gt; 0 when any one bank is dropped; and G &gt; 0 in at least 2 of the 3 subperiods (P1 2014–17, P2 2018–21, P3 2022–26Q2).
  If only the drop-one-bank or subperiod condition fails, the result is <strong>PASS-fragile</strong> (not adopted).
  <strong>FAIL</strong> if G ≤ 0 or the fixed-b upper bound G<sub>U</sub> is below 3%.
  Anything else, or fewer than 40 valid target quarters, is <strong>INCOMPLETE</strong>.</p>
  <h3>Primary gate, 2014Q1–2026Q2</h3>
  <div class="table-scroll"><table class="dataframe">
    <thead><tr><th>Hypothesis</th><th>Comparator</th><th>G (scaled CRPS)</th><th>p (fixed-b, one-sided)</th><th>p (Holm)</th><th>G<sub>U</sub></th><th>90% coverage</th><th>Min G, drop one bank</th><th>Subperiods with G &gt; 0</th><th>Targets</th><th>Verdict</th></tr></thead>
    <tbody>
{gate_rows(gate)}
    </tbody>
  </table></div>
  <p>Test C: DM on the per-quarter cross-bank mean loss differential d̄<sub>t</sub> (positive favours the OT method), Bartlett long-run variance with M = ⌊√T⌋ (7 at T = 50),
  p-value from 200,000 simulated null statistics (seed 20261006). Scores are scaled by each bank's trailing-16-quarter MAD at the forecast origin.
  B*, the trimmed members and the widening s are re-selected every Q4 on the trailing 12 target quarters, from walk-forward forecasts only.</p>
  <h3>Subperiods (pre-registered, descriptive except the G &gt; 0 count)</h3>
  <div class="table-scroll"><table class="dataframe">
    <thead><tr><th>Hypothesis</th><th>Subperiod</th><th>G</th><th>p (raw)</th><th>90% coverage</th><th>Min G, drop one bank</th><th>Targets</th><th>Sign</th></tr></thead>
    <tbody>
{subperiod_rows(gate)}
    </tbody>
  </table></div>
  <h3>P3 next to R1 (v1.0 design): not independent evidence</h3>
  <div class="table-scroll"><table class="dataframe">
    <caption>P3 (the primary run restricted to 2022Q1–2026Q2) and R1 (the pinned v1.0 design: 2018+ history, 2021Q4 freeze, B6 excluded from selection but reported) share the same 18 target quarters. They are not independent evidence, and neither can change the primary verdict.</caption>
    <thead><tr><th>Hypothesis</th><th>P3 G</th><th>P3 p (raw, test C)</th><th>R1 G</th><th>R1 p (v1 test A)</th><th>Role</th></tr></thead>
    <tbody>
{p3_r1_rows(gate, r1)}
    </tbody>
  </table></div>
  <h3>Break checks (FB1–FB4)</h3>
  {ph('Fluctuation test on rolling 15-quarter means of d̄<sub>t</sub>; mean-shift tests at 2015Q3, 2016Q3, 2020Q1 and 2022Q1 (Holm within FB2); excluding 2020Q1–Q2; training from 2010Q1; leave one OOS year out.')}
  <h3>Per-bank CRPS gains (H1)</h3>
  {ph('Distribution of per-bank relative CRPS gains of BARY-EW over B* (anonymised; no per-BHC rows are published).')}
  <h3>Coverage and calibration</h3>
  {ph('Pooled 50% and 90% central-interval coverage and 10-bin PIT histograms for BARY-EW, WAR-RM and the reference baselines.')}
  <h3>Industry total (T1): forecast vs actual</h3>
  {ph('BARY-EW on the industry total ($bn, secondary H1d) with 50%/90% bands against realised totals, 2014Q1–2026Q2.')}
  <h3>Cross-section (T3): WAR-RM density fan</h3>
  {ph('One-step WAR-RM forecasts of the cross-sectional quantile function of revenue / lagged trading assets (bp), with the realised cross-section.')}
  <h3>Sensitivities S1–S16</h3>
  {ph('Fixed first-freeze set, mid-year entrant rule (b), rolling windows, frozen settings, frozen scale, test A / WPE p-values, B5 without BAA10Y, training from 2010Q1.')}
  <h2>Design (v1.1)</h2>
  <ul>
    <li><strong>Target.</strong> Quarterly BHCKA220, de-cumulated from year-to-date (Q1 as reported, no bridging over gaps), thousands of USD. Negative values kept; no logs.
      A first filing outside Q1 has no quarterly value. Flows are blanked in 16 bank-quarters where year-to-date interest income falls within a year. Two tiered subsidiaries are dropped in 2016Q3–Q4, when their parents also file.</li>
    <li><strong>History.</strong> 2009Q1–2026Q2, with expanding estimation windows. 2008 is pre-sample: only 2008Q4 trading assets are used, as the denominator of the 2009Q1 ratio. Burn-in 2009Q1–2013Q4.</li>
    <li><strong>Views.</strong> T1 industry total. T2 an annually refreshed ex-ante bank set: at each Q4, banks with |quarterly A220| ≥ $10m in all of the last 16 quarters. T3 banks with lagged trading assets ≥ $100m.</li>
    <li><strong>Baselines.</strong> SAA-8, seasonal naive, ratio random walk, SES (α = 0.3), AR(1)+Q1, pooled quantile regression on FRED covariates (VIX, 10-year rate volatility, Nasdaq volatility, Baa–10-year spread), and an empirical-Bayes dynamic panel.</li>
    <li><strong>H1.</strong> Equal-weight quantile average (the 1-D W₂ barycenter) of the trimmed baselines, widened by s about the median.</li>
    <li><strong>H2.</strong> The forecast cross-section is a point on the W₂ geodesic from the Fréchet mean to the latest cross-section (scalar β). It maps to banks through a Gaussian-copula AR on probit ranks (scalar ρ).</li>
  </ul>
  <h3>Ex-ante bank-set size by Q4 origin (membership counts only)</h3>
  <div class="table-scroll"><table class="dataframe">
    <thead><tr><th>Origin</th>{set_heads}</tr></thead>
    <tbody><tr><td>Banks</td>{set_cells}</tr></tbody>
  </table></div>
  <p>The 2021Q4 set is exactly the v1.0 ex-ante set. At the first freeze (2013Q4), all seven baselines produce forecasts for all 72 burn-in pseudo-out-of-sample cases (12 banks × 6 targets, 2012Q3–2013Q4).</p>
  <p>Data: FFIEC NIC FR Y-9C bulk files, 74 quarters 2008Q1–2026Q2. Macro: FRED VIXCLS, DGS10, NASDAQCOM, BAA10Y. Report-quarter backtest on the latest vintage; filing revisions are not modelled.
  The v1.0 design (<code>test_design_trading_ot.json</code>, sha256 <code>dffd1323…</code>) stays pinned and byte-identical; it runs only as R1.</p>
</main>
<footer class="site-footer">
  <div class="site-footer__inner">
    <p class="site-footer__disclaimer"><strong>Independent research lab</strong> ·
      Not affiliated with any employer or financial institution · Not investment advice.</p>
    <div class="site-footer__links">
      <a href="../../../index.html">Home</a>
      <a href="../index.html">Trading × OT</a>
      <a href="{OT_PAGE}">Classical OT guide</a>
      <a href="https://github.com/jgridifier/research-lab">GitHub</a>
    </div>
  </div>
</footer>
</body>
</html>
"""


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / 'index.html').write_text(render(), encoding='utf-8')
    print(RESULTS / 'index.html')


if __name__ == '__main__':
    main()
