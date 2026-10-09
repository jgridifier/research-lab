# PREREG: Fed CP issuance maturity mix (applied lab; OT is one candidate)

**Status:** BURN-IN GATE PASSED. Out-of-sample (OOS) scoring is NOT authorized (`oos_authorized: false`).

**Verdicts** (from `compute_cp_ot_burnin.stdout.txt`):
- (i) **OT_CLAIM = CLEARED.** K4 cleared only narrowly; see §4.
- (ii) **DATASET_USABLE = yes.**
- (iii) **FORECASTABLE_SIGNAL (any method) = yes.**

Prepared 2026-10-09 (ET). Draft only; not sent anywhere.

## 1. Files
| file | sha256 |
|---|---|
| GATE_THRESHOLDS_fed_cp_ot.md (hashed before any distance was computed) | c15eb60cbe1467090fcc920b8f4e311dd14f7b3bbfd0437e21809355721a6c8a |
| compute_cp_facts.py | a3c79f457083a639be489f6cc7060ee4dfa5ee97bb057d222730fb32529c4c56 |
| compute_cp_facts.stdout.txt | d06ac2c3e0d4fcc8a046b56027bc921f79ec8ed83a6d362ff020ca71786d735a |
| compute_cp_ot_burnin.py | 34021c50bf30efbe2541b119816e8ef98c455ab5819ee232a892ca990ab11857 |
| compute_cp_ot_burnin.stdout.txt | 17a0b23936e5b0c56e15a4937830e0f032a55ff20713f45cda7cf2d5adc11e8e |
| DATA_FACTS.md | 63f3b0dff5751afee95de8028b550c2727965e6393c32f9dd3de6b97f8186b1e |
| DATA_SPEC_for_app.md | 9c50a16e994cdb04e2598b270800e2941d027e314b375e33cbf5caa98f102c6c |
| ENGINEERING_TICKET.md (draft, not filed) | 088d9f2e72a162daf25436b2c76c3b4cfe6b93abd0082d480b5f94befa86346d |
| drive_manifest.json | 95b31d3e955e3530887f0f5baf2e493a634f34795bc6c005a8a509fff5c6a52b |
| raw/FRB_CP_xml.zip | 16805f2ce102d5b6703de6393e89f345e9e68e15381ab457fb58f3830cff22d2 |
| raw/fed_cp_volume_stats_by_maturity.csv | aeab7b0941af5e2b492e42dbe4fe05c6752efd6bc9eff3fa9b620b5545596d7a |

## 2. Data
- **Source:** the XML VOL dataset (see DATA_FACTS.md).
- **NONFIN duplication repaired** by reading NAA and NA2 from the XML. The CSV pairs equal {NAA, NA2} in 0.999845 of keys. The CSV is used only as a check.
- **Primary types:** AAA, FAA, NAA, NA2.
- **MKT** is excluded from the object because it is not the sum of the types (exact match 0.001109). It is used only as a stress comparator.
- **Caveats:**
  - The volumes cover rate-eligible issues only.
  - The rating criteria changed on 2007-06-18 (Fitch dropped), inside the burn-in.

## 3. Object and windows
- **Object:** the weekly (Mon–Fri, Friday label) dollar mix over 6 maturity buckets, for each type.
- **Ground metric:** log geometric bucket midpoints in days (0.693, 1.903, 2.649, 3.367, 4.048, 4.996). Log-days were chosen over rank because a location shift then reads as a proportional change in maturity. The step between buckets is nearly uniform, so rank is close and is kept as a sensitivity check.
- **Weekly, not daily**, aggregation. Daily data have day-of-week effects and thin NAA days (a burn-in daily minimum of 0 issues).
- **Distance:** exact W2² between step quantile functions.
- **Windows:**
  - Burn-in: weeks ending 2001-01-05..2008-12-26, 417 weeks. It includes the 2007–08 stress so the warm-up sees a stressed regime.
  - OOS: weeks ending 2009-01-02..2026-10-02, 927 calendar weeks. CPFF was active 2008–2010, so the first OOS years are a policy regime.

## 4. Gate (labelled burn-in values; pooled over 4 types)
| quantity | value |
|---|---|
| usable type-weeks | 417/417 for every type |
| MEDIAN_NEXT_W2SQ (week to week) | 0.1411976508 |
| MEDIAN_HALF_W2SQ (issue-level half split, K1 floor) | 0.0352191046 |
| ratio next/half | 4.009 → **K1 not fired** |
| K1b half-week day split (NON-gating) median | 0.1155302457; ratio next/halfweek 1.222 |
| pooled share of next-week W2² (LOC / SCALE / SHAPE) | 0.2435 / 0.0853 / **0.6713** → **K2 not fired** (threshold 0.15) |
| median SHAPE (next / half) | 0.1119603788 / 0.0333280627, ratio 3.36 → **K3 not fired** |
| decomposition identity error | 2.2e-15 |
| calm 2001–2006 (non-gating) | next/half 3.94; SHAPE share 0.723 |
| rank metric (non-gating) | next/half 4.01; SHAPE share 0.647 |

How to read this:
- The weekly mix moves about 4× more than the issue-level sampling floor, and about two-thirds of that movement is shape, not location or scale.
- **Caveat:** the day-split floor is only 22% below the week-to-week change. Much of the week-to-week movement is within-week, day-level variation. That limits how well any model can forecast it. The issue-level floor is a lower bound on noise (it ignores the spread of issue sizes within a bucket).

### Forecastable signal (any method; burn-in only)
- EWMA alpha selected on 2002–2004: 0.2 (losses: 0.1: 0.1433, 0.2: 0.1399, 0.3: 0.1425, 0.5: 0.1534).
- Evaluated on 2005–2008 (208 weeks), mean W2²: P 0.2694, EWMA0.2 0.1894, MA4 0.2079, EXP 0.4493.
- Ratios:
  - P/EXP 0.600.
  - EWMA/EXP 0.422.
  - EWMA/P 0.703.
- **SIGNAL = yes** (threshold 0.90).
- Calm 2005–2006 (non-gating): P 0.2158, EWMA 0.1408, EXP 0.2614.
- Smoothing beats persistence: last week alone is noisy.

### Planning power (K4; PLANNING ONLY, not an OOS result)
- **Proxy differential** d = L(P) − L(MA4), averaged over types:
  - n 413, mean 0.05725, sd 0.15779;
  - AR(1) phi −0.155, residual sd 0.15620;
  - gain scale 0.17873 (the MA4 mean loss).
- **Test:** T = 927, Bartlett L = 30, fixed-b with an AR(1)-simulated critical value.

| DGP | gain 0 (size) | 0.02 | 0.05 | 0.10 |
|---|---|---|---|---|
| Gaussian AR(1), 2.5% one-sided | 0.0260 | 0.1185 | **0.5015** | 0.9760 |
| block bootstrap (mean block 13), 2.5% | 0.0135 | 0.1250 | 0.7285 | 1.0000 |
| Gaussian AR(1), 5% | 0.0585 | 0.1930 | 0.6335 | 0.9915 |
| block bootstrap, 5% | 0.0300 | 0.2150 | 0.8380 | 1.0000 |

- **K4:** min power at gain 0.05 and 2.5% = **0.5015 ≥ 0.50 → not fired**.
  - **This is knife-edge.** The Monte Carlo SE is about 0.011 (2000 reps), so another seed could fall below 0.50. The pinned rule and seed decide, and the result is CLEARED.
  - Read it this way: the OOS test can detect about a 10% gain reliably, and a 5% gain only about half the time.
- **Non-gating contrast** (a short-series test at T = 50, Gaussian DGP): power 0.062 at gain 5% and 0.135 at gain 10%. The 927-week length is what makes the test useful.
- The bootstrap null is conservative (size 0.0135 at nominal 0.025).

## 5. Methods (specified, not fit)
These are as in GATE_THRESHOLDS §5:
- P, EWMA, EXP;
- LS (location-scale on log-duration);
- ALR-AR, ALR-VAR(1), MNL-AR (fractional multinomial logit), RIDGE on lagged ALR;
- WAR(1) (JTSA 2022, DOI 10.1111/jtsa.12590);
- TMAR (transport-map AR, arXiv:2105.05439).

**SEL rule** (trailing 156 weeks, re-selection every 13 weeks, 1% tie band, then complexity order) decides the shipped app model. If Family B fails, the app headline is persistence.

Background: Fréchet regression (AoS 2019, DOI 10.1214/17-AOS1624; background only) and Wasserstein regression (JASA 2021, DOI 10.1080/01621459.2021.1956937).

## 6. Trials (TRIAL_COUNT)
- **Confirmatory OOS tests: 3.**
  - Family A: WAR vs B*, TMAR vs B*, Holm 0.05.
  - Family B: SEL vs P, at 0.05.
- **Burn-in gate runs:** 1 (no reruns).
- **Facts runs:** 2. The second added missing-date detail and fixed a mislabel. No threshold depended on the first.
- **Outputs printed beyond the thresholds file, all non-gating:**
  - per-type medians;
  - the d ACF;
  - the T = 50 contrast;
  - MA4 and alpha-grid losses.
- **Stress study:** descriptive only, 4 signals × 3 events (+E4). No p-values. Not computed.

## 7. Leakage and exposure log
1. FS structural facts over all dates: series ids, valid and ND counts, zero-day counts per series for 2001–2026 (e.g. FIN.10_20 has 1764 zero days), and the missing dates.
2. FS consistency checks over all dates: CSV vs XML value-match fractions, and MKT vs sum-of-types fractions. These involve value comparisons over OOS dates, but no distributional statistics.
3. FS burn-in summaries included 2008-12-29..31, 3 days of the first OOS week.
4. BS: OOS valid-day counts per type-week (structural; no amounts).
5. The 2026-10-08 inventory memo mentioned FIN volume detail for 2026-10-01.
6. Web: the Fed CP About page, release and DDP URLs, the FRASER crisis timeline, the Fed 2020-03-17 press release, FDIC PR-16-2023, DFPI, LII 15 U.S.C. 77c.
7. No RATES values have been parsed; only RATES series ids were listed.
8. Drive: read-only metadata search.

## 8. Authorization
OOS requires a separate `APPROVAL_fed_cp_ot.txt`, written by the user, that references PIN.txt. The `oos_authorized` flag is a record, not the switch.

## 9. Constraints
- Classical statistics only.
- NumPy and pandas, no SciPy.
- Citations come from the verified list; papers older than 2020 are labelled background.
