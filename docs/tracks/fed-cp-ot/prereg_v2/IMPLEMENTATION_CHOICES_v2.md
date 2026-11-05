# Pinned implementation choices — v2

These choices describe the current harness, before approval. Changing them after
approval is a deviation. Code locations below are relative to
`tracks/fed-cp-ot/fed_cp_ot/`. This document is hashed in `prereg/PIN_v2.txt`.

- **Minimum fit/selection window: 52 usable weeks.** `candidates.py`:
  `MIN_FIT` and `_Fitted.fit_predict_both` fall back to persistence below 52
  usable type-weeks. `schedule.py`: `MIN_SEL_WEEKS` and `select` require 52
  common usable all-four-type target weeks in the trailing 156-week selection
  window; otherwise there is no new selection.
- **LS log-sd floor: 1e-4.** `candidates.py`: `LOG_SD_FLOOR`, `LS._fit`
  floor the standard deviation before taking its logarithm.
- **MNL Hessian jitter: 1e-8.** `candidates.py`: `MNL_AR.RIDGE` is numerical
  Hessian jitter, not a new regularisation candidate.
- **RIDGE intercept is unpenalised.** `candidates.py`: `Ridge._fit` centres
  predictors and responses, penalises slopes, and restores the response mean.
- **Hyperparameters are separate SEL entries.** `candidates.py`: `NON_OT`
  and `ENTRIES` enumerate each registered EWMA alpha and RIDGE lambda separately.
  `schedule.py`: `select` uses that entry order for simplicity ties. No candidates
  or hyperparameter values are added here.
- **First origin: 2002-01-04.** `harness.py`: `ORIGIN_START`; earlier weeks
  supply history only. The target is origin plus seven days.
- **Exact input_max_date:** `harness.py`: `origin_frame` builds the weekly
  frame after excluding daily rows later than the origin. `frame_input_max_date`
  returns `pd.Timestamp(weekly_o.week.max())` over the entire frame actually
  passed in, including unusable rows and every type. It is the maximum Friday
  week label, not the latest valid daily observation, publication date, or
  vintage date. A label later than the origin raises `ScoringWallError`.

## Decision rule

**The runtime p-value decides; the phi-grid critical value is logged only as a
 diagnostic.** `scoring.py`: `evaluate_pair` obtains `p` from `runtime_p` using
100,000 AR(1) draws at the estimated phi. `grid_cv` interpolates within the grid
(no extrapolation), but its result does not enter rejection or claim decisions.
`run_family` applies Holm to runtime p-values within each registered family;
a claim also requires the existing hurdles and a complete result. `holm` treats
an INCOMPLETE test without a p-value as p=1 and retains the family size. The
Family K failure guard in `harness.finalize` additionally suppresses claims and
rejections when that family is incomplete. No thresholds change.
