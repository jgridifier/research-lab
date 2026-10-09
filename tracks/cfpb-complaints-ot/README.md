# CFPB complaints × OT: killed at burn-in (negative result)

Pre-registered forecast of the monthly cross-section of CFPB complaint counts across companies
(equal-weighted empirical law of `log(1 + total complaints)`, three pinned bureau names excluded), with a
W₂-barycenter combination (H1) and a Wasserstein autoregression (H2) against simple baselines.

**Status: `KILLED_AT_BURNIN`. No out-of-sample run, no new runs.** On the 99-point grid the burn-in
(2013-01 to 2017-12) median next-month squared W₂ distance was 0.0064 (0.0063598632), below the median
half-sample noise floor of 0.0269 (0.0268769480); ratio 0.2366. The pre-registered rule kills the object when the
next-month distance is at or below the noise floor: month-to-month changes are smaller than sampling noise
within a month. No replacement object is proposed.

| File | sha256 |
|---|---|
| `prereg/PREREG_cfpb_complaints_ot.md` | `d3e8ac46de75fdd181a99d3fc3519107ff84d704ae37034390cbf9bd8ac24a46` |
| `prereg/cfpb_ot_learning.html` | `9c5d5dc30264673cefe68df15163a6ddae5b89be63cad752843d37801d9f9061` |
| `prereg/test_design_cfpb_ot_v1.json` | `a5170147070a25163ed3549403ffe48860c749c4ccb4e0243d20aa6befada584` |

The three files are verbatim copies of `/workspace/research/cfpb_ot_prereg/`; `tests/test_prereg_pin_cfpb_ot.py` pins them.
The design's `oos_authorized` stays `false` and is not the switch; the burn-in kill forbids an out-of-sample run
of this object even if an approval file were written later.

Pages: `docs/tracks/cfpb-complaints-ot/index.html` (track page) and `learning.html` (verbatim learning page).

Tests: `PYTHONPATH= .venv/bin/python -m pytest tracks/cfpb-complaints-ot/tests -q`
