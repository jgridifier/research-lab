# Burn-in gate thresholds: FDIC SOD state branch-deposit OT study

**Written:** 2026-10-09, before any Wasserstein distance, quantile function, half-sample split,
shape decomposition, loss, or power simulation of this object was computed.
**Already seen at writing time (disclosed):** `compute_sod_facts.stdout.txt` (structure of all 32 files;
burn-in-only main-office shares and burn-in-only state branch counts), the inventory memo
`/workspace/research/drive_ot_datasets_2026-10-08.md` (which printed 1994 and 2024 national median
log10 branch deposits, 4.39 and 4.90). Nothing else about deposit levels or shapes.

## Object (primary, the only one that gates)
- Rows of `sod_branches_{t}.csv.gz` with `STALPBR` in the 51 jurisdictions (50 states + DC; PR and
  the territories AS, FM, GU, MH, MP, PW, VI excluded), `BRNUM != 0` (office number 0 is the main
  office per the FDIC SOD reporting instructions, so main offices are excluded), and `DEPSUMBR > 0`.
- `x = ln(DEPSUMBR) - ln(M_t)`, `M_t` = `numpy.median` of `DEPSUMBR` over all such rows in year t
  (all 51 jurisdictions pooled). Natural log.
- State-year usable iff it has at least 50 such rows.
- Quantile function on `u_k = k/100`, `k = 1..99`, `numpy.quantile(method="linear")`.
- `W2SQ(Q1,Q2) = mean_k (Q1(u_k) - Q2(u_k))**2`.

## Windows
Burn-in measures: years 1994-2003. Next-year pairs: (t, t+1) with both in 1994-2003 (targets
1995-2003). No year after 2003 is read by the gate script.

## Gate statistics
1. **Noise floor (same rule as CFPB).** `MEDIAN_NEXT` = median over usable state pairs of
   `W2SQ(Q_{s,t}, Q_{s,t+1})`. `MEDIAN_HALF` = median over usable state-years of
   `W2SQ` between the two halves of a random split (permute rows with
   `numpy.random.default_rng(20261009)`, one stream, state-years in (year, state) sorted order;
   first `n//2` vs the rest).
2. **Shape share.** Exact grid decomposition, for any two grid quantile functions:
   `W2SQ = (m1-m2)^2 + (s1-s2)^2 + 2*s1*s2*(1-rho)` with `m` the grid mean, `s` the grid sd
   (ddof=0) and `rho` the grid correlation of Q1 and Q2. Called LOC, SCALE, SHAPE.
   `SHAPE_SHARE_POOLED` = sum SHAPE / sum W2SQ over usable next-year pairs.
   Also printed (not gating): median of per-pair SHAPE/W2SQ.
   `MEDIAN_NEXT_SHAPE` and `MEDIAN_HALF_SHAPE`: medians of the SHAPE term over next-year pairs and
   over half-sample splits.

## Kill rules (any one fires => KILLED_AT_BURNIN)
- **K1:** `MEDIAN_NEXT <= MEDIAN_HALF`.
- **K2:** `SHAPE_SHARE_POOLED < 0.15`. Reason: OT methods can only beat a location-scale model
  through the shape term; if under 15% of the year-on-year move is shape, the ceiling on an OT
  gain over an oracle location-scale forecast is under 15% of loss, and realistic gains a small
  fraction of that.
- **K3:** `MEDIAN_NEXT_SHAPE <= MEDIAN_HALF_SHAPE` (shape change is not above split-sample shape noise).

## Power rule (fires => status UNDERPOWERED: recommend kill or a redesigned test, no OOS)
Planning simulation at T = 22 OOS years (targets 2004-2025) and N = 51 states, calibrated on
burn-in proxies only (loss differential between two burn-in baselines). If simulated power of the
pre-registered primary test (one-sided, at the Holm 2.5% level for a two-hypothesis family) at
relative gain 0.05 is below 0.50 at the burn-in-calibrated dependence, the design is UNDERPOWERED.
A panel test that ignores common year shocks (state clustering / state-block bootstrap) may be the
primary only if its simulated size at 5% nominal under burn-in-calibrated year effects is at most
0.075; otherwise it is reported as conditional-on-years, non-gating.

## Seeds
Half split: 20261009. Power simulations: 20261009, restarted per block.
