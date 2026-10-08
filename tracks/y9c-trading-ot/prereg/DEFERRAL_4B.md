# DEFERRAL — §4-B barycentric scenarios, W2 reduction, energy score

Date: 2026-10-08 (America/New_York). Written before any out-of-sample score. This note is the pinned record that §4-B does not run in the authorized v1.1 out-of-sample run.

## Decision

§4-B (prereg v1 §4.3; secondary, descriptive, not gating) is deferred. It is not implemented, not logged as a trial, and not scored. The authorized run stays at 39 pre-logged trials. Any §4-B result produced later is reported as not blind and exploratory, and it cannot support or qualify a primary verdict.

## Why it cannot be specified soundly on this sample

The registered object is a Gaussian copula over (bank, horizon), about 48 dimensions, with correlation estimated from pseudo-out-of-sample probability-integral transforms and shrunk halfway to equicorrelation. At the first forecast origin there are about three complete origins of that vector. That correlation is not identified, and filling the gaps (which banks, which horizons, how to project onto a positive-definite matrix) would be invention, not a pre-registered choice.

A low-dimensional substitute was checked and does not rescue it. A one-parameter AR(1) copula on the industry-total 4-quarter path, scored by the energy score against an independence copula, was simulated for 300 replications (seed 20261006). The series was an AR(1) plus a first-quarter level shift, calibrated only on 2009Q1–2013Q4 industry totals (phi 0.276, first-quarter shift 12.4, residual scale 4.0, in billions). Evaluation used 47 overlapping origins, the same fixed-b one-sided 5% test as the primary design, and 500 paths per origin. Rejection rates:

- No cross-horizon dependence (phi 0): 0.0% against independence. The test is conservative, not oversized.
- Dependence at the burn-in value (phi 0.28): 7.3% against independence. Mean energy-score gap 0.0008.
- Strong dependence (phi 0.80), well above anything in the burn-in: 54%.

So at the dependence this series actually has, the energy score does not detect the copula. The same simulation's historical-simulation benchmark rejected 78% of the time when there was no cross-horizon dependence at all, so that comparison does not identify the dependence model either. Script and output: `v1_1/spec_4B/sim_4B.py`, `v1_1/spec_4B/sim_4B_output.txt`. The simulation uses one stand-in marginal and 500 paths rather than 2,000; neither changes the conclusion that the test has no power here.

The prereg already marked §4-B descriptive only (about 15 overlapping 4-quarter origins under v1; about 47 under v1.1). Descriptive reporting of an unidentified copula would still be a specification choice made with the design of the scored run, so it waits.

## What this does not change

- Primary gate, H1/H2, the secondary Holm family, FPCA, ridge, sensitivities, and R1 are unchanged.
- h = 4 coverage: a case with no scale stays in the coverage denominator. At the first h = 4 freeze that caps every member at 83.3%, which does not change the kept set. Already recorded in ERRATA_v1_1b. No new ruling.
- Exploratory items (entropic barycenter, residual WDRO, drift monitor, Gelbrich bound) stay exploratory and are not part of this run.

## Before any later §4-B work

A new dated spec, pinned the same way as this note, is required before any scenario paths are generated on out-of-sample origins. That spec has to state the dimension, the dependence parameter, both benchmarks, the reduction seed and restarts, and that the result is not blind.
