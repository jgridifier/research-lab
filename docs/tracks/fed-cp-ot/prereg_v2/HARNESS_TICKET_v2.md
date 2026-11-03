# Engineering ticket (draft): fed-cp-ot OOS harness per PREREG v2 §12

**Repo:** jgridifier/research-lab, `tracks/fed-cp-ot`. **Spec:** `prereg/PREREG_v2_fed_cp_ot.md`. Where this ticket and the spec differ, the spec wins.

## Do not
- Run OOS.
- Write `APPROVAL_fed_cp_ot.txt`.
- Set `APPROVAL_SHA256` (those happen in §10 steps 2–3).
- Add candidates.

## Tasks
1. **T1:** add `fed_cp_ot/harness.py` with the `run-oos` and `dry-run-burnin` commands. `run-oos` calls `preflight('oos')` and `check_oos_approval()` first and aborts before any post-2008-12-26 amount is parsed.
2. **T2:** implement the v1 §5 candidates exactly.
   - Add `project_qf(c, v, X_LOG)`: Voronoi cutpoints at the X_LOG midpoints, ties go to the lower bucket (§1).
   - Add LS discretization at ln(4.5), ln(9.5), ln(20.5), ln(40.5), ln(80.5), with tails folded (§3).
   - ALR forecasts are mapped back by softmax with no clipping (§7c).
3. **T3:** build `H_o = build_weekly(vol, through=o)` and recompute and assert `input_max_date ≤ o` from the frame itself (§4). Add `test_v2_vintage_injection`, which asserts that forecasts are bit-identical.
4. **T4:** last-usable-week P/MA4; EWMA/EXP update only on usable weeks; the SEL window = the last 156 usable all-4 weeks, with the span logged (§7e); the B* schedule per quarterly re-selection, held forward (§8). Write the schedules before scoring.
5. **T5:**
   - paired weeks = all 4 types usable with all forecasts present;
   - `G = 1 − ΣL_cand/ΣL_comp` and `G_s` by subperiod;
   - the fixed-b Bartlett HAC, L = floor(√T);
   - critical values from an AR(1) grid φ ∈ [−0.98, 0.98], step 0.01;
   - INCOMPLETE if |φ̂| ≥ 0.99 or n_pairs < 800;
   - Holm per family (A: WAR, TMAR vs B*; B: SEL vs P; K: Kumo-best vs SEL, Kumo-best vs P).
6. **T6:** the Kumo NIM client.
   - 24 (type, bucket) entities and the last 156 usable weeks of context, anchored at o.
   - Regression of the next-week share, then `max(·,0)` and renormalize.
   - Modes best (primary) and fast (descriptive).
   - Retry up to 3× on 429/5xx/network errors with the same payload; log every attempt.
   - INCOMPLETE if >5% of origins fail.
   - The key comes from the `NVIDIA_API_KEY` env var only.
7. **T7:** a CI job that replicates the burn-in stdout (sha256 17a0b239…) from the pinned zip; skipped-with-reason if the zip is unavailable. Add unit tests for `q_from_p` zero and single-atom inputs, `Π` idempotence and mass preservation, LS sums to 1 (1e-12), and the φ reject rule.
8. **T8:** `oos_result.json` with G, G_s, p, n_pairs, φ̂, the INCOMPLETE flags and the PREREG v2 §5 non-rejection wording; a Pages results page; a run-once lock recorded in the trial log.

## Acceptance
- All tests pass.
- `dry-run-burnin` runs end to end on targets ≤ 2008-12-26 only.
- `run-oos` raises `OOSNotAuthorized` on main today.
- The PR contains no APPROVAL file and `APPROVAL_SHA256 is None`.
- The follow-up pin PR (`fed-cp-ot: pin APPROVAL_SHA256`) is opened only after Jared's APPROVAL PR merges.
