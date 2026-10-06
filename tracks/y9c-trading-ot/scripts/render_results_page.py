"""Render docs/tracks/y9c-trading-ot/results/index.html from committed aggregate tables.

While results/tables/gate.json does not exist (OOS not run), the page is rendered
as a template with every verdict marked PENDING and no OOS numbers. Static HTML,
shared site.css, no scripts, no external requests.
"""
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from trading_ot.paths import DESIGN_PATH, RESULTS, TRIALS_PATH  # noqa: E402
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


def gate_rows(gate):
    rows = []
    for key, label, comp in [('H1', 'H1 · §4 BARY-EW (equal-weight W₂ barycenter, ex-ante bank set)', 'B*'),
                             ('H2', 'H2 · §3 WAR-RM (Wasserstein AR + rank map, cross-section)', 'B*<sub>CS</sub>')]:
        g = (gate or {}).get(key, {})
        f = lambda k, fmt='{:.3f}': fmt.format(g[k]) if g.get(k) is not None else '—'
        rows.append(f"<tr><td>{label}</td><td>{comp}</td><td>{f('G', '{:+.1%}')}</td><td>{f('p_raw')}</td>"
                    f"<td>{f('p_holm')}</td><td>{f('coverage90', '{:.2f}')}</td><td>{f('lobo_min_G', '{:+.1%}')}</td>"
                    f"<td>{f('n_targets', '{:d}')}</td><td><span class=\"verdict\">{e(g.get('verdict', 'PENDING'))}</span></td></tr>")
    return '\n'.join(rows)


def render():
    design = json.loads(DESIGN_PATH.read_text(encoding='utf-8'))
    gate_path = RESULTS / 'tables/gate.json'
    gate = json.loads(gate_path.read_text()) if gate_path.exists() else None
    pending = gate is None
    trials = trial_count(TRIALS_PATH)
    headline = 'Verdict: PENDING (out-of-sample scoring not run)' if pending else e(gate.get('headline', ''))
    status = ("<div class=\"callout\"><strong>Status: OOS not run.</strong> The design "
              "(<code>tracks/y9c-trading-ot/test_design_trading_ot.json</code>, v1.0) is pinned, the leakage tests pass, "
              "and the pipeline refuses to score 2022Q1+ targets until a prereg addendum (v1.1) fixes which run is primary "
              "and resolves the open design questions listed below. No out-of-sample forecast, score or test statistic "
              f"has been computed. Trials logged on OOS data: <strong>{trials}</strong>.</div>") if pending else ''
    ph = lambda what: f'<div class="placeholder"><strong>PENDING.</strong> {what}</div>' if pending else ''
    questions = ''.join(f"<li><code>{e(q['id'])}</code>: {e(q['text'])}</li>" for q in design.get('open_questions', [])
                        if not q.get('resolution'))
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
    <div class="page-header__eyebrow">Track · Results · Pre-registered v1.0</div>
    <h1>Y-9C trading revenue: baselines + optimal-transport layers</h1>
    <p class="page-header__sub">Next-quarter BHCKA220 (Schedule HI 5.c), 2022Q1–2026Q2, one-step walk-forward. Research only.</p>
  </div>
</header>
<main class="page-content prose">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="../../../index.html">Home</a><span aria-hidden="true"> › </span>
    <a href="../index.html">Trading × OT</a><span aria-hidden="true"> › </span>Results
  </nav>
  {status}
  <h2>{headline}</h2>
  <p>Two gated hypotheses, Holm-adjusted across the pair (FWER 0.05). The methods come from the classical-OT guide:
  <a href="{OT_PAGE}#family-4">§4 barycenters for forecast combination</a> (H1) and
  <a href="{OT_PAGE}#family-3">§3 density time series in Wasserstein space</a> (H2).
  PASS needs Holm p &lt; 0.05, relative CRPS gain G ≥ 3%, pooled 90% coverage in [0.80, 0.97], and G &gt; 0 when any one bank is dropped.
  FAIL if the one-sided 95% upper bound on G is below 3%. Anything else is INCOMPLETE.</p>
  <h3>Gate</h3>
  <div class="table-scroll"><table class="dataframe">
    <thead><tr><th>Hypothesis</th><th>Comparator</th><th>G (scaled CRPS)</th><th>p (one-sided)</th><th>p (Holm)</th><th>90% coverage</th><th>Min G, drop one bank</th><th>Targets</th><th>Verdict</th></tr></thead>
    <tbody>
{gate_rows(gate)}
    </tbody>
  </table></div>
  <p>DM test on the per-quarter cross-bank mean loss differential d̄<sub>t</sub> (positive favours the OT method), Newey–West lag h−1, HLN small-sample factor, Student t(T−1).
  Industry-total and single-bank tests are secondary: with 18 target quarters they can only detect gains of roughly 18–29%.</p>
  <h3>Per-bank CRPS gains (H1)</h3>
  {ph('Distribution of per-bank relative CRPS gains of BARY-EW over B* (anonymised; no per-BHC rows are published).')}
  <h3>Coverage and calibration</h3>
  {ph('Pooled 50% and 90% central-interval coverage and 10-bin PIT histograms for BARY-EW, WAR-RM and the reference baselines.')}
  <h3>Industry total (T1): forecast vs actual</h3>
  {ph('BARY-EW on the industry total ($bn, secondary H1d) with 50%/90% bands against realised totals, 2022Q1–2026Q2.')}
  <h3>Cross-section (T3): WAR-RM density fan</h3>
  {ph('One-step WAR-RM forecasts of the cross-sectional quantile function of revenue / lagged trading assets (bp), with the realised cross-section.')}
  <h3>Sensitivity: 13-bank full-sample set</h3>
  {ph('S1: H1 on the full-sample balanced-13 set (selected with future data; sensitivity only).')}
  <h2>Design</h2>
  <ul>
    <li><strong>Target.</strong> Quarterly BHCKA220, de-cumulated from year-to-date (Q1 as reported, no bridging over gaps), thousands of USD. Negative values kept; no logs.</li>
    <li><strong>Views.</strong> T1 industry total; T2 19 banks with |quarterly A220| ≥ $10m in all 16 burn-in quarters (2018Q1–2021Q4), chosen from burn-in data only; T3 banks with lagged trading assets ≥ $100m.</li>
    <li><strong>Timing.</strong> Burn-in 2018Q1–2021Q4; 18 one-step origins 2021Q4–2026Q1. A quarter is usable 7 days after its Y-9C due date.</li>
    <li><strong>Baselines.</strong> SAA-8, seasonal naive, ratio random walk, SES (α = 0.3), AR(1)+Q1, pooled quantile regression with FRED covariates, empirical-Bayes dynamic panel.</li>
    <li><strong>H1.</strong> Equal-weight quantile average (the 1-D W₂ barycenter) of the baselines, with a trim rule and one widening factor frozen at 2021Q4. No cross-validation.</li>
    <li><strong>H2.</strong> The forecast cross-section is a point on the W₂ geodesic from the Fréchet mean to the latest cross-section (scalar β). It maps to banks through a Gaussian-copula AR on probit ranks (scalar ρ).</li>
  </ul>
  <h3>Open design questions (must be resolved before scoring)</h3>
  <ul>{questions or '<li>None.</li>'}</ul>
  <p>Data: FFIEC NIC FR Y-9C bulk files (34 quarters). Macro: FRED VIXCLS, DGS10, SP500. Report-quarter backtest on the latest vintage; filing revisions are not modelled.</p>
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
