# Research Lab plan: CP funding forecasts (2026-10-09, Quant)

**Question:** Which forecasts of CP issuance and maturity mix are best, is any of them useful for spotting funding stress early, and does optimal transport (OT) earn a place against strong standard baselines?
**Rules (unchanged):** classical statistical and ML methods only; papers from 2020 or later (older ones labelled background); pinned design; burn-in gates set before any computation; ONE held-out run; an honest trial count. Gates protect *claims*. They do not stop the app from shipping the best validated model, even a simple one.

## Paper outline (working paper)
1. **Intro.** Why the maturity mix matters: rollover risk and terming-out under stress.
2. **Data.** The Fed CP release (daily from 2001; issuer types × maturity buckets). Repairs: the duplicated non-financial rows are re-parsed from the raw source. The definition of the vintage and snapshot, and the series identifiers.
3. **Methods.**
   - Baselines: persistence, EWMA of the mix, expanding mean, ALR-VAR (compositional), a Dirichlet or multinomial-logit AR, location-scale on log-duration, and ridge on lagged ALR.
   - OT candidates: Wasserstein AR on the quantile function over the ordered maturity ladder (JTSA 2022, doi:10.1111/jtsa.12590, arXiv:2006.12640); a transport-map AR (arXiv:2105.05439); and a barycenter combination of baselines (Entropy 2020, doi:10.3390/e22090929).
   - 1-D OT on an ordered ladder is exact. W1 is the sum of |CDF difference| × bucket width.
4. **Evaluation design.** Expanding walk-forward; W1/W2 and a ranked-probability-style loss; a fixed-b HAC test on weekly loss differentials; Holm across primary hypotheses; a power simulation; a model-selection rule pinned on validation.
5. **Held-out results** for every model, every trial included, losers too.
6. **Early warning.** Event dates fixed in advance from published sources. Lead time, hit rate and false-alarm rate versus volume and spread indicators. Labelled descriptive if there are too few events for a test.
7. **Where distributional methods fail.** Y-9C (T=50: primary FAIL, and a linear pool beat the barycenter); CFPB and FDIC (killed at burn-in because year-to-year shape change sat below the sampling noise floor; FDIC also had T≈22 and common year shocks). The lesson for practice: you need large T *and* signal above the noise floor.
8. **Application and limits.** Snapshot versus revisions, regime breaks, and what the monitor can't tell you.
Appendix (possible): the HMDA cross-sectional shift study, 2021→2023.

## Application spec: "CP funding monitor" (Pages, static, rebuilt daily)
- **Inputs:** public Fed CP data, outstanding and issuance by issuer type and maturity bucket, pulled through the Fed Data Download Program after each release. Developer gets the series identifiers and repair rules in DATA_SPEC_for_app.md once burn-in finishes.
- **Cadence:** a daily build after the Fed release; forecasts at a weekly horizon; data-quality flags whenever the release is late or the schema changes.
- **Outputs:**
  1. A next-week forecast of the maturity mix for each issuer type, with 80/90% intervals, from the model chosen by the pre-pinned rule. A label always names which model it is.
  2. A stress indicator. Its hit and false-alarm record is shown next to it. If the indicator is not validated, it is labelled "experimental".
  3. A backtest panel with rolling loss against persistence and calibration (PIT/coverage).
  4. A forward log. Every live forecast is stored before its outcome is known, which gives a real prospective test.
- **What a user decides with it:** whether funding is shortening (rollover concentration), which tells a treasury or risk user when to term out funding or escalate a liquidity review; and how much to trust that read, based on the hit and false-alarm record. It does not support trading claims.
- PM to sharpen the user story.

## Milestones
| # | Step | Owner | Gate / approval |
|---|---|---|---|
| M1 | CP data repair + facts + burn-in gate (OT claim; dataset usable; any-method signal) | Quant | in progress |
| M2 | Pin the prereg: all models, selection rule, stress events, power, trial count; teaching page | Quant | **Jared approves the pin** |
| M3 | Live data pipeline + leakage tests (no held-out scoring) | Developer | Quant reviews code |
| M4 | One held-out run (separate approval file, as in Y-9C) | Developer | **Jared approves the run** |
| M5 | App v1 live using the selected model; stress indicator labelled by its validation status | Developer + PM | **Jared approves going public** |
| M6 | Working paper draft on Pages | Quant | **Jared approves publication** |
| M7 | HMDA appendix prereg (cross-sectional) | Quant | Jared approves the pin |

**Steps needing Jared:** the M2 pin, the M4 held-out run, the M5 public app, and M6 publication. Everything else proceeds without him.
**Already fixed:** a kill ends the OT claim, not the project. If OT loses, the paper says so and the app ships the winner.
