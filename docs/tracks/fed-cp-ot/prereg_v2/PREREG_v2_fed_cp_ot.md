# PREREG v2: Fed CP maturity-mix OT track: resolves the Quant math review (PR #20)

**Written:** 2026-11-03 (ET). Jared OK'd writing v2 ("Sure", 2026-11-03 14:10 ET).
**Status:** OOS scoring is **NOT authorized** (`oos_authorized: false`). Nothing OOS has been computed, loaded, or run for this document.
**Amends:** GATE_THRESHOLDS_fed_cp_ot.md (sha256 `c15eb60c…6c8a`) and PREREG_fed_cp_ot.md (sha256 `e3da87af…0ecf`).
- Those v1 files are left byte-identical, so their pin tests still hold.
- **Location:** this file lives at `docs/tracks/fed-cp-ot/prereg_v2/` because `test_track_layout` freezes the `prereg/` file set. The harness PR copies it into `tracks/fed-cp-ot/prereg/`, adds it to `PINS` and updates `test_track_layout` (§10 step 1).
- Where v2 and v1 conflict, v2 wins.
- Anything not mentioned here stays as in v1.

**Information set when written:** the same as v1 §7, plus the Quant review in PR #20. No new data was read. Every choice below is made blind to OOS.

**Rule for choices:** where the review left an option open, the more conservative one is pinned. Conservative means harder to pass, or no new degree of freedom.

---

## §1 Scoring OT forecasts that are not 6-share mixes (Finding 1, blocker)

**Decision: project, then score.**
- Every candidate's forecast (WAR, TMAR, LS and the KumoRFM rival) is mapped to a 6-share mix on the support `X_LOG` before logging and scoring.
- Rationale:
  - The target is a 6-point law.
  - The app can only display a mix.
  - Scoring an off-support quantile function would let OT models put mass between support points, which no comparator can do.
- Projection operator `Π`, the W2-nearest law on the fixed support:
  - Given a forecast quantile function `Q` on (0,1), send each quantile mass to the nearest support point in log-days.
  - Equivalently, `p_b = Leb{u : Q(u) ∈ C_b}`, with Voronoi cells `C_b` cut at the midpoints of `X_LOG`:
    `m = (1.2982, 2.2762, 3.0079, 3.7073, 4.5221)`, where `X_LOG = (0.6931, 1.9033, 2.6492, 3.3667, 4.0478, 4.9964)`.
  - Ties (`Q(u)` exactly at a midpoint) go to the **lower** bucket.
  - `Π` is the exact W2 metric projection onto laws supported on `X_LOG`. In 1-D the monotone nearest-point map is optimal.
- **Conservatism:** `W2(Π Q, target) ≤ W2(Π Q, Q) + W2(Q, target)`. So projection can help or hurt; it is not a free gain. The native (unprojected) score is printed as a **non-gating diagnostic** only.
- **Implementation:** `ForwardLog.record_forecast` is unchanged; it still takes a 6-share `mix`. A forecaster that returns `(c, v)` must call `project_qf(c, v, X_LOG)` inside `fit_predict`.
- **Tests:**
  - `Π` is idempotent on 6-point laws.
  - `Π` is mass-preserving.
  - The tie goes to the lower bucket.
  - A random-QF property test checks that the `Π` result is no farther in W2 than any of 10^4 random 6-point laws.

## §2 The hurdle G and paired weeks (Finding 2, blocker)

- **Weekly loss:** `L_t(m) = (1/4) Σ_τ W2SQ(f_τ,t(m), y_τ,t)`, using the primary log-days metric.
- **Paired week:** a target week `t` in the OOS window where
  - **all 4 types are usable** (the conservative balanced panel, so the comparison is not driven by composition changes), and
  - both models have a logged forecast for every type.
- **Hurdle:** `G(cand, comp) = 1 − Σ_t L_t(cand) / Σ_t L_t(comp)` over the paired weeks. This is the ratio of sums, equivalent to the ratio of means on the same set.
- **Subperiod version:** `G_s` is the same formula restricted to the paired weeks with target in subperiod s ∈ {2009–2014, 2015–2020, 2021–2026-10-02}.
- **A claim requires all of:**
  - (i) the test rejects at its level;
  - (ii) `G > 0.02`;
  - (iii) `G_s > 0` in ≥2 of the 3 subperiods;
  - (iv) **≥800 paired weeks** (all-4-usable). If fewer, the family is **INCOMPLETE**, not failed.
- **Differential for the test:** `d_t = L_t(comp) − L_t(cand)` over the paired weeks, in time order. Gaps in the sequence are closed up; the HAC treats the series as consecutive. This is disclosed.
- **Gain scale (Finding 6, also resolved):**
  - The "gain" axis of K4 used `min(P, MA4, EXP)` burn-in mean losses. In the burn-in this minimum was MA4 = 0.17873, so the documents agree.
  - G above is unit-free and does not use that scale.

## §3 LS discretization cutpoints (Finding 3)

- The LS forecast `N(μ̂, σ̂²)` on ln(days) is discretized with gap-free cutpoints at half-days:
  `c = (ln 4.5, ln 9.5, ln 20.5, ln 40.5, ln 80.5) = (1.5041, 2.2513, 3.0204, 3.7013, 4.3883)`.
- Mass below `c1` goes to bucket 1, and mass above `c5` goes to bucket 6. This includes beyond 270 days: tails are folded.
- `Φ` is evaluated via `math.erf`, since SciPy is not allowed.
- **Assert:** the six shares sum to 1 within 1e-12.
- **Note:** these are the *data-bucket* boundaries. They differ from the §1 Voronoi midpoints, which belong to the *metric* projection. The difference is intentional: LS models the day-level law, while `Π` models an off-support quantile function.

## §4 Vintage as-of rule (Finding 4)

- **Historical OOS run:** it uses exactly one pinned vintage, `FRB_CP_xml.zip`. Its sha256 is recorded in the run manifest *before* the run, and it must equal the vintage named in the APPROVAL file (§10).
- For every origin `o` (a Friday), the harness itself must:
  1. build `H_o = build_weekly(vol, through=o)` from that vintage, dropping every daily row with date > o, before any aggregation;
  2. compute `input_max_date := max(date in H_o)` from the frame actually passed in. It then asserts `input_max_date ≤ o` and logs that value. A value supplied by the caller is ignored.
  3. pass forecasters only `origin_view(H_o, o)`, which is a deep copy.
- **Pseudo-real-time disclosure:** a single late vintage contains revisions to pre-origin days that were not known at the origin. The harness prints the count of revised pre-wall values across the archived vintages (`vintage_diffs.jsonl`) as a disclosure. That count does not gate.
- **Live/forward log:** the vintage used for origin `o` must be fetched at or after `o` 18:00 ET. Rows dated after `o` are truncated by step 1. The forward-log issue-time rules (PR #11) are unchanged.
- **Required test** (`test_v2_vintage_injection`): append synthetic target-week rows (o+1..o+7) with extreme values to the vintage frame. The forecast for every model must be bit-identical with and without the injection.

## §5 K4 knife-edge: reporting (Finding 5, resolved as a reporting rule)

- K4 stands as CLEARED by the pinned seed. This is recorded verbatim: power 0.5015 against the 0.50 bar, MC SE ≈ 0.011.
- A Family A non-rejection must be reported as **"underpowered to detect a 5% gain (planning power ≈0.50); not evidence of no gain."**

## §6 Burn-in replication in CI (Finding 7)

- This is a harness-ticket item (§12 T7): a CI job reruns the pinned burn-in script with seed 20261009 on the pinned zip.
- It asserts that sha256 of stdout = `17a0b239…`.
- If the zip is not available to CI, the job is marked skipped-with-reason. **The OOS run is not allowed until the job has passed at least once on main.**

## §7 Numerical edge cases (Finding 8)

- **(a)** `q_from_p` raises `ValueError` if `sum(p) ≤ 0` or if any `p < 0`. Single-atom laws are valid (SCALE = SHAPE = 0). Tests cover the all-zero and single-atom cases.
- **(b)** No change.
- **(c) ALR models:**
  - The 1e-4 floor is applied to the *input* shares, which are then renormalized.
  - The *forecast* ALR vector is mapped back by softmax, with no clipping and no floor.
  - The harness reports the fraction of FAA GT80 (81–270d) input shares that were floored.
- **(d) φ rule:** `φ̂` is estimated by OLS of `d_t` on `d_{t−1}`. If `|φ̂| ≥ 0.99`, the test is **INCOMPLETE**: no interpolation or extrapolation, and the harness asserts this.
  - The critical-value grid is φ ∈ {−0.98, −0.97, …, 0.98} (step 0.01). Linear interpolation is used inside the grid only.
  - The runtime p-value uses 100,000 AR(1) null draws at `φ̂`, seed 20261009. This is v1 §5, unchanged.
- **(e) Holiday and unusable weeks.** A type-week is *usable* per v1 §0: ≥3 valid days, ΣN ≥ 100, ΣD > 0.
  - **Last usable week:** P for type τ at origin o = the most recent usable τ-week ≤ o. MA4 = the barycenter of the 4 most recent usable τ-weeks ≤ o.
  - EWMA/EXP recursions update only on usable weeks.
  - If the origin week itself is unusable, a forecast is still issued from the last usable week.
  - Unusable target weeks are not scored (see §2 for paired weeks).
  - **SEL "156 usable weeks":** the trailing window is the most recent 156 *usable all-4* target weeks ≤ o. Its calendar span may exceed 156 weeks, and the span is logged.

## §8 B* per origin (Finding 9)

- At each re-selection origin (the first origin of each calendar quarter), B* is re-chosen from the **non-OT** candidates (P, EWMA, EXP, LS, ALR-AR, ALR-VAR, MNL-AR, RIDGE) by the SEL trailing rule.
- B* is held until the next re-selection. The Family A comparator forecast for target t is the forecast of the B* that was in force at origin t−1 week.
- This is a forecast-level comparator; the ex-post best is never used.
- The B* schedule is logged before any OOS target is scored.

## §9 KumoRFM via NIM: pre-registered rival row (new)

**Purpose:** an external, non-OT, black-box foundation-model rival. It is **not** a SEL candidate, not in the app, and not in TRACE core. It is a separate **Family K** and does not change Families A or B.

- **Service:** NVIDIA-hosted `kumo-relational` NIM, at `POST https://ai.api.nvidia.com/v1/structured-data/nvidia/kumo-relational/predictions`.
  - The model version string is returned in the response headers and logged.
  - The endpoint URL and the image tag (`nvcr.io/nim/nvidia/kumo-relational:1.1.0` if self-hosted) are frozen in the run manifest.
- **Graph per origin o:** built only from `H_o` (§4).
  - Entity table: 24 rows, one per (type, bucket).
  - Fact table: weekly rows for each usable week ≤ o (share `p_b`, log total amount, log issue count, valid days).
  - Context: the most recent **156 usable weeks per entity** (3,744 fact rows; under the 10k-row and 30 MB caps).
  - Anchor time = o.
- **Target:** regression of the next-week share `p_{τ,b,o+1}`.
  - The forecast mix is `max(ŝ, 0)` renormalized per type.
  - If all six shares are ≤0 for a type, the forecast is P and the origin is counted as a Kumo failure.
- **Run modes:**
  - primary `best`;
  - secondary `fast`. This is descriptive, with the same table, no test.
  - Mode and context are fixed; no tuning, and no other mode is reported.
- **Calls:**
  - One call per origin per mode, with 24 entities.
  - Retries happen only on HTTP 429/5xx or network error, with the same deterministic payload, up to 3 retries and a 30 s backoff.
  - Every attempt is logged (status, latency, payload sha256).
  - An origin still failing after retries has no Kumo forecast and drops out of Family K pairs only.
  - If **>5% of OOS origins** fail, Family K is **INCOMPLETE**.
- **Dry run:** schema/regression support may be smoke-tested on **burn-in targets only** (2006–2008) before approval. This uses no OOS data, and the results are not reported as evidence.
- **Same targets, metrics, and paired-week definition as §2.**
- **Family K tests (confirmatory, 2 tests, Holm 0.05 one-sided):**
  - K-a: Kumo-best vs **SEL** (the shipped model).
  - K-b: Kumo-best vs **P**.
  - Both use the K4 statistic on `d_t`, the §7(d) φ rule, and the §2 bars (G > 0.02, ≥2/3 subperiods, ≥800 pairs).
  - Direction: H1 = Kumo has lower loss.
  - Also printed (non-gating): Kumo vs B*, WAR, TMAR, and the native latency/cost table.
- **Trial count:** 3 → **5 confirmatory tests** (A: 2, B: 1, K: 2). Each family keeps its own Holm control. Family-wise control across families is **not** claimed, and this is disclosed.
- **Data egress:** only public Federal Reserve CP data leaves the box.
- **Seed:** the service is called deterministically. Any server-side nondeterminism is noted. Two re-requests of the first OOS origin are made purely to measure it; they are logged and not used.

## §10 APPROVAL mechanism (Finding 10)

1. **v2 pin:** this PR is merged. Engineering then appends a v2 line to a **new** file, `PIN_v2.txt`, with the sha256 of PREREG_v2, GATE_THRESHOLDS, PREREG v1 and the design JSON. PIN.txt stays untouched.
2. **Approval:** Jared (only) commits `prereg/APPROVAL_fed_cp_ot.txt`. It must contain:
   - the PIN_v2.txt sha256;
   - the vintage zip sha256;
   - the scope "one OOS run: Families A, B, K plus the stress study";
   - the date.
   It is merged by its own PR. An agent never writes this file.
3. **Pin PR:** Engineering opens a separate PR titled `fed-cp-ot: pin APPROVAL_SHA256`. It sets `APPROVAL_SHA256` in `fed_cp_ot/preflight.py` to the file's sha256 and extends `PINS` with PIN_v2.txt.
   - CI asserts that the hash matches and that the file references the PIN_v2 sha.
   - It needs one Quant review.
   - **This PR is the switch.** `oos_authorized` remains a record only.
4. **Run:** the harness runs once from the merge commit of step 3. It writes `oos_result.json` plus a trial-log row and refuses a second run (a lock file whose sha is in the trial log).

## §11 Interval addendum (spec; non-gating)

- **Object:** a 90% prediction region for the app's SEL forecast. It is a W2 ball `{y : W2SQ(f, y) ≤ r}` per type.
- **Radius:** `r_{τ,o}` = the empirical 0.90 quantile, using the conservative "higher" convention `⌈0.9(n+1)⌉`-th order statistic, of the realized one-step W2SQ losses of the model **in force** over the trailing 156 usable τ-weeks ≤ o. Split-conformal calibration is on the past only.
- **Per-bucket share bands (display only):** the 5%/95% trailing quantiles of the share residuals.
- **Evaluation:** OOS coverage per type and pooled, plus subperiod coverage. Reported, with a target band of 0.87–0.93 printed as an annotation only. **Non-gating; no claim.**
- **Before OOS approval:** computed in the app only for burn-in targets.

## §12 OOS harness spec (for Engineering; also see HARNESS_TICKET_v2.md)

- **T1 Entry:** `python -m fed_cp_ot.harness run-oos`. It calls `preflight('oos')` and then `check_oos_approval()` (§10). It aborts before reading any post-wall amount.
- **T2 Candidates:** the v1 §5 list exactly, plus `project_qf` (§1) and the LS cutpoints (§3). It fits per type on an expanding window via `origin_view`.
- **T3 Vintage wall:** §4 steps 1–3, plus the injection test.
- **T4 SEL and B\*:** §7(e) windows and §8 schedule. Both schedules are written to disk before scoring.
- **T5 Scoring:** §2 paired weeks, weekly loss, `G`, `G_s`, and the K4 fixed-b HAC test with the §7(d) φ rule. Holm per family.
- **T6 Kumo client:** §9, with an attempt log and the burn-in-only dry-run mode.
- **T7 CI:** §6 burn-in replication, plus unit tests for §1, §3, §4 and §7.
- **T8 Output:** `oos_result.json` (all G, G_s, p, n_pairs, φ̂, the INCOMPLETE flags, the §5 wording) and a Pages results page. Run-once lock.
- **Acceptance:** all tests green, and the dry run is on burn-in only. The harness PR must not contain the APPROVAL file or a non-None `APPROVAL_SHA256`.

## §13 Seeds
20261009 everywhere, restarted per block (unchanged).

## §14 Choices left for Jared (risk tolerance)
- **R1:** paired weeks require all 4 types usable (pinned, conservative). If OOS yields <800 such weeks, the result is INCOMPLETE rather than a looser any-type count. Changing this needs a v3 *before* approval.
- **R2:** Family K is confirmatory (2 extra tests). The alternative is descriptive-only, which would keep the confirmatory count at 3.
