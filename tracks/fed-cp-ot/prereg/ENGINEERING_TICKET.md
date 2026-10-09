# DRAFT engineering ticket (NOT filed). Target repo: jgridifier/research-lab

**Title:** CP maturity-mix lab: OOS harness (single run, needs approval) and daily data pipeline

**Context:** the pre-registration is in `research/fed_cp_ot_prereg/`, pinned by PIN.txt. The burn-in gate returned:
- OT_CLAIM = CLEARED. K4 passed narrowly (power 0.5015 against a threshold of 0.50).
- DATASET_USABLE = yes.
- FORECASTABLE_SIGNAL = yes.

`oos_authorized` is false. Out-of-sample scoring is blocked until a separate approval file exists.

## Tasks
1. **Pipeline:** build the daily pipeline exactly as DATA_SPEC_for_app.md specifies.
   - Store each vintage with its sha256.
   - Validate per the repair rules.
   - Build the weekly object.
   - Add unit tests:
     - the CSV-vs-XML NONFIN check;
     - the known 2004 gaps;
     - exactness of W2SQ and its decomposition (identity error < 1e-12).
2. **Candidates:** implement the §5 candidates of GATE_THRESHOLDS_fed_cp_ot.md (sha256 c15eb60c…) exactly as written, with no extra models.
   - Every new candidate counts as a trial and requires a new pre-registration version.
3. **SEL rule and app headline:**
   - Implement the SEL rule: trailing 156 weeks, re-selection every 13 weeks, a 1% tie band, then the fixed complexity order.
   - The app shows the SEL forecast. It falls back to persistence if Family B fails after the OOS run.
4. **OOS harness:** one invocation only.
   - Refuse to run unless `APPROVAL_fed_cp_ot.txt` exists and its hash matches PIN.txt.
   - Write the results and the Holm decisions once, and never re-run.
5. **Stress study:** implement the descriptive stress dashboard (§6). It is not a gate.

## Acceptance
- The burn-in script reproduces `compute_cp_ot_burnin.stdout.txt` byte for byte (sha256 17a0b239…).
- No code path reads amounts after 2008-12-26 unless the approval exists.
