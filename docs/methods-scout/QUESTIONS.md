# Methods scout: research questions

Standing questions from Jared that steer the daily methods scout. Each day the scout picks methods aimed at an
open question, and at least one analysis per method targets it directly. Jared's original question text is kept
for the record; approved or cleaned-up wordings are labelled as such and are the ones in force.
Status: `open` · `in progress` · `answered` · `parked` · `retired`.

**Only questions with status `open` or `in progress` are scout targets.** Retired questions are kept for the record
and must not be targeted by future scout runs.

## Open questions

| ID | Added | Question | Status | Scout pages | Data located | Data missing |
|---|---|---|---|---|---|---|
| Q1 | 2026-11-14 | What is the connection between Form PF aggregate prime-broker borrowings (and related private-fund leverage tabs) and short-term funding conditions in OFR cleared-repo volumes and rates and NY Fed primary-dealer settlement fails? Do borrowings, repo, and fails co-move, lead or lag one another, or disconnect in stress? | in progress | [2026-11-14](2026-11-14.html), [2026-11-15](2026-11-15.html) | Real public series already in the lab's Drive copies and on the box: SEC Form PF / private-fund statistics (2012Q4–2025Q4, aggregate tabs including 8.28); OFR cleared and tri-party repo (daily 2014-08-22–2026-10-05); NY Fed primary-dealer settlement fails (weekly 2013-04-03–2026-09-23). Optional companions: CFTC Traders in Financial Futures (weekly 2010-07-20–2026-09-29) and FINRA customer margin statistics (monthly 1997-01–2026-08). Official sources linked in the Q1 section below. | The lab copy of CFTC TFF has a gap from 2025-12-30 to 2026-09-29 (refresh from CFTC; public). Per-firm prime-brokerage revenue or balances; a Form ADV Schedule D §7.B.(1) prime-broker panel (not built). This question is aggregate-only by design. |
| Q2 | 2026-11-13 | With hundreds to thousands of programs, each with free-text descriptions and tabular data (turned into categories and implied features) but only a few noisy periods of history, what can we reliably learn beyond trends and category mix over time? Sub-questions: borrowing strength, text vs numbers, real change vs noise, hidden structure, and visualizing many short series (see the Q2 section below). | in progress | [2026-11-13](2026-11-13.html), [2026-11-16](2026-11-16.html) | SYNTHETIC mocks only (built 2026-11-13): program-level zero-based-budgeting datasets modeled on publicly reported figures for a manufacturer like Corning Incorporated and a financial firm like Morgan Stanley, in the Drive folder "Q2 mock ZBB datasets (synthetic, 2026-11-13)". Teaching page: [What the Q2 mock budget datasets are doing](q2-mock-zbb.html). Clearly labelled synthetic; they are not either firm's actual budgets and contain no private data. | Real program-level budgets, actuals, headcount and decision packages for any firm. The mocks are a stand-in so methods can be tried before any real data arrives. |
| Q3 | 2026-11-14 | What is the connection between supervisory stress-test projections—severely adverse pre-tax net income, loan losses, capital-ratio drawdowns, and the stress capital buffer—and the same firms' realized payout ratios from FR Y-9C dividends and share repurchases? Do the buffer or the projected earnings path help describe subsequent payouts, and how do cross-firm patterns move from one test year to the next? | in progress | [2026-11-14](2026-11-14.html), [2026-11-16](2026-11-16.html) | Fed DFAST/CCAR firm results, 2013–2026 ([public CSV](https://www.federalreserve.gov/supervisionreg/files/public_results_DFAST_2026.csv); join key `id_rssd`). FR Y-9C / BHCF zips, 2008Q1–2026Q2, payout and income items BHCK4460, BHCK4598, BHCK4783, BHCK4782, BHCK4340 (join `id_rssd` = RSSD9001). Fed scenario variables (baseline and severely adverse, plus history) and annual Large Bank Capital Requirements PDFs (SCB, 2020–2026, by name). Coverage and firm counts are in the Q3 section below. | Firm-level *baseline* projected earnings or capital paths are not published (baseline is macro-only). A tidy SCB panel is not published as a CSV (annual PDFs, name-based). |

<a id="q1"></a>

## Q1 — Form PF borrowings, repo, and settlement fails (approved 2026-11-14)

On 2026-11-14 Jared approved this pairing, together with Q3, with the wording "Number 1 and 4." The statement below is the approved wording, not a verbatim first draft from Jared. Status is `in progress` since the 2026-11-14 scheduled scout (completed 2026-11-15); see the Q1 progress log below. This question replaces the retired 2026-11-10 prime-broker top-25 share question, which the available data cannot support at the firm level.

**Question.** What is the connection between Form PF aggregate prime-broker borrowings (and related private-fund leverage tabs) and short-term funding conditions in OFR cleared-repo volumes and rates and NY Fed primary-dealer settlement fails? Do borrowings, repo, and fails co-move, lead or lag one another, or disconnect in stress?

**Datasets, coverage, and join.** All series are real public data. Join on calendar time (aggregate repo and fails to the Form PF quarter, or compare at weekly/daily frequency against the last known quarterly PF point). Core overlap is 2014–2025, about 44–46 quarters; the weekly and daily legs are denser.

- SEC Form PF / Private Fund Statistics, quarterly 2012Q4–2025Q4, 140 aggregate tabs (the lab copy is a long panel of 89,991 rows). Tab 8.28 is prime-broker borrowings; related leverage and borrowing tabs include 8.27 and 8.29. Source: [SEC private funds statistics](https://www.sec.gov/data-research/statistics-data-visualizations/private-funds-statistics). The series lag publication by about two quarters.
- OFR U.S. Repo Markets Data Release, daily 2014-08-22–2026-10-05 (DVP from 2018-05-07): average rates, outstanding and transaction volumes by venue, tenor and collateral. Source: [OFR short-term funding monitor, repo dataset](https://www.financialresearch.gov/short-term-funding-monitor/datasets/repo/). Final vintage through 2026-06-30; later observations are preliminary.
- NY Fed primary-dealer settlement fails, weekly (Wednesday) 2013-04-03–2026-09-23, including headline aggregates and on-the-run Treasury tenors. Source: [NY Fed primary dealer statistics](https://www.newyorkfed.org/markets/counterparties/primary-dealers-statistics) and the Markets Data API.
- Optional companions: CFTC [Traders in Financial Futures](https://www.cftc.gov/MarketReports/commitmentsoftraders/index.htm) leveraged-fund and dealer positioning, weekly 2010-07-20–2026-09-29 (Treasury-futures names harmonized across the February 2022 rename); FINRA [customer margin statistics](https://www.finra.org/rules-guidance/key-topics/margin-accounts/margin-statistics), monthly 1997-01–2026-08, industry aggregates.

**Sub-questions.**

1. **Lead/lag.** Do Form PF borrowings move before repo volumes and rates or settlement fails, or after?
2. **Co-movement versus coincidence.** Is the joint movement tighter in 2020, March 2023, or the late-2025 fails spike than in quiet periods?
3. **Regime breaks.** Do the relationships themselves change, not just the levels?
4. **Tenor and venue mix.** Does the repo composition (GCF, DVP, tri-party; tenor; collateral) change when Form PF borrowings rise?
5. **Positioning versus funding.** Does CFTC TFF leveraged-fund positioning line up with the funding and fails legs, or is "where they are positioned" disconnected from "how it is funded"?

**Methods that fit.** DenseLines across the many repo and fails series; optimal transport or Lovell proportionality on repo tenor mix (or Fed commercial-paper maturity mix as a nearby public companion); lead/lag and regime-break tools; codyn if the series are treated as a small community. ebnm is a weaker fit here.

**Caveats.** This is market- or industry-aggregate data: it cannot recover top-25 prime-broker shares, and it is not a substitute for the retired firm-level Q1. Form PF lags about two quarters and some period labels are mixed. OFR series have a final versus preliminary vintage split and confidentiality gaps (missing days are not zeros). Fails are primary-dealer only, with some cells suppressed. SCOOS is available only as eight full-text releases (2024-12–2026-09) without tabulated net-percentage series. ICI free flow history is short. The work is descriptive; it is not a trading signal.

## Q1 progress log

- **2026-11-14 (scheduled; interrupted, completed 2026-11-15)** ([edition](2026-11-14.html)). Method: CRQA (cross-recurrence quantification analysis, cognitive science; interesting). Public aggregates: Form PF tab 8.27 (monthly 2013-01–2025-12), OFR repo (daily → Thu–Wed weekly), NY Fed fails (weekly); 432 complete weeks 2018-06-06–2026-09-23. Quintile states, circular-shift nulls.
  - Q1.1 lead/lag: Form PF prime-broker borrowing growth shows no lead, lag or co-movement with tri-party volume, DVP volume, the DVP−tri-party spread or financing fails at a familywise level (8 tests; smallest uncorrected p = 0.041). Form PF "reverse repo" borrowing growth leads DVP outstanding growth by ~4 months (familywise p = 0.001; asymmetry p = 0.001), by reference month, not publication date.
  - Q1.2 stress: weekly financing fails and the DVP−tri-party overnight spread are anti-recurrent in the same week (0.287 vs null, p = 0.011; no lead/lag). The coupling is significant in 52/96 rolling 52-week windows from late 2018 to mid-2025 (peak 0.54 in the year to June 2022), and in none of the 15 windows ending after July 2025, the late-2025 fails spike. In the windows ending August–December 2025, fails and DVP volume growth are co-recurrent instead.
  - Q1.3 regime: the rolling CRQA shows the fails–spread coupling turning on (late 2018) and off (mid-2025). Descriptive, not a formal break test.
  - Q1.4 (tenor/venue mix) and Q1.5 (CFTC TFF) not run yet. Next: an order-aware CRQA null (stationary-bootstrap surrogates, max-T over lags); a joint stress-state recurrence across fails, spread, Form PF repo and TFF leveraged-fund positioning on a pre-registered episode list.
  - Data still missing: nothing new for the aggregate design. Form PF publication dates would let leads be read in real time.

- **2026-11-15 (scheduled)** ([edition](2026-11-15.html)). Methods: convergent cross mapping (pyEDM; fisheries ecology; interesting) and archaeological seriation + Bellanger–Husi event dates + EPPM/Ford plots (kairos/tabula; recommended for the promote workflow — not promoted). Public aggregates: CFTC TFF leveraged-fund net short (UST 2y+5y+10y futures), NY Fed financing fails, OFR DVP volume and DVP−tri-party spread (weekly 2019-01-16–2025-12-31, n = 364); OFR volumes for 9 venue × tenor segments (monthly 2018-05–2026-09); Form PF tab 8.27 (monthly to 2025-12).
  - Q1.4 tenor/venue mix (first run): the mix seriates to calendar order (Spearman −0.96; Porčić p < 0.001; CA axis 1 = 69% of inertia) — a one-way drift from term DVP and tri-party overnight to overnight and short-term DVP, via a 2023–24 GCF-term episode. A walk-forward "mix clock" (train ≤ 2022) dates 2023–26 months with MAE 1.06 y vs 1.92 naive. Form PF total borrowing growth leads mix speed by 3–6 months (r = 0.56/0.54, Holm p = 0.009 over 18 tests; holds in 2019–22 and 2023–25 and without the 2025-08 bucket change). Prime-broker growth alone: no link (p ≥ 0.14).
  - Q1.5 positioning vs funding (first run): leveraged-fund position changes cross-map into the DVP−tri-party spread (ρ = 0.25, shift p = 0.005, Holm 0.05 = 200-surrogate floor; stable in both halves), not into fails (no link either way, p = 0.21/0.47), although linear Granger rejects positioning ↔ fails both ways (p = 0.001/0.004).
  - Q1.1/Q1.3: CCM gives the 11-14 fails–spread coupling a direction (fails → spread ρ = 0.33 vs spread → fails 0.16, p = 0.04 not Holm-significant). Links into DVP volume (from fails and positioning) appear only after mid-2022 (half-sample ρ 0.02 → 0.38 and 0.03 → 0.19).
  - Next: more surrogates (Holm floor), partial CCM conditioning on fails, rolling CCM over the late-2025 switch-off; a taxonomy-robust mix clock; collateral-mix and positioning-mix clocks.
  - Data gaps: the lab's TFF copy stops at 2025-12-30 (plus 2026-09-29); OFR split the ≤30-day bucket on 2025-08-14. Form PF publication dates still missing.

<a id="q2"></a>
- **2026-11-16 (scheduled)** ([edition](2026-11-16.html)). No Q1 analysis; the picks targeted Q2 and Q3. Status and missing data unchanged.

## Q2 — Learning from many short, noisy programs (approved 2026-11-13)

On 2026-11-13 Jared approved the question, all five sub-questions, and the addition of tabular data alongside the free-text descriptions. On 2026-11-16 he asked for the wording to be cleaned up ("Just format it so it's clearer and less like me rambling"); the cleaned wording below is the one in force. Status is `in progress` since the 2026-11-13 scheduled scout, which ran on the SYNTHETIC mocks only (see the Q2 progress log below).

**Question.** We have hundreds to thousands of programs (for example, budget lines). Each has free-text descriptions and tabular data, which we turn into categories and implied features, but only a few noisy periods of numbers. Beyond tracking trends and category mix over time, what can we reliably learn about each program and about the portfolio as a whole?

**Setting.**

- **Units:** hundreds to thousands of programs.
- **Inputs:** free-text descriptions plus tabular data → classifications and implied features.
- **History:** short (a handful of periods) and noisy per program.
- **Already covered:** trends and composition over time. The question is what else is worth studying.

**Sub-questions.**

1. **Borrowing strength.** If we pool similar programs, how much better do we estimate each one's real level and trend than by looking at it alone, given how short its history is?
2. **Text versus numbers.** Which programs' spending doesn't match what their descriptions say, and which ones quietly change category over time?
3. **Real change or noise.** When a total moves, how much comes from the program mix changing, how much from programs actually behaving differently, and how much is just noise?
4. **Structure.** Do programs form groups that rise and fall together, or trade off against each other, in ways the categories don't show?
5. **Seeing it.** How can one chart show a thousand short, noisy series without turning into spaghetti?

<details><summary>Original wording (2026-11-13, kept for the record)</summary>

"Want to add a guiding question about like let’s say you have a ton of decriptions, and we extract out some classifications and then get some implied features, understanding the trends and composition over time but like what else would be really interesting to look at -think ok like a budgeting use case where the rest hundreds or thousands of program all with their own noise and not that much history"

</details>

## Q2 progress log

- **2026-11-13 (teaching page).** Explainer for the SYNTHETIC mocks: [What the Q2 mock budget datasets are doing](q2-mock-zbb.html). Covers the generator, file schemas, the planted answer key for all five sub-questions, public sources, assumptions, and self-checks. Linked from the research-lab home.
- **2026-11-13 (scheduled)** ([edition](2026-11-13.html)). Methods: ebnm (empirical Bayes normal means, statistical genetics; recommended for the promote workflow) and DenseLines (density line charts, visualization research; interesting). SYNTHETIC mock ZBB data only (Corning_mock 1,079 programs FY2020–25; MorganStanley_mock 1,840 programs FY2021–25; seed 20261113). Answer key used only for scoring.
  - Q2.1 borrowing strength: ebnm with a scale-mixture prior on deviations from segment × function means cuts 2025-level log RMSE from 0.146 to 0.108 (Corning mock) and from 0.138 to 0.109 (Morgan Stanley mock). In planted pooling families the drop is 0.161 → 0.101. Programs alone in their group get slightly worse (0.110 → 0.120). 90% intervals cover 89.5%.
  - Q2.3 real change vs noise: lfsr < 0.05 calls 91 (Corning mock) and 200 (Morgan Stanley mock) year-on-year moves real, with wrong-sign rates of 0% and 1.5%. Naive z calls 141 and 292 (4.3% and 2.7% wrong); BH calls 14 and 28. lfsr is calibrated. At portfolio level, noise is about 2% of the change, and EB-denoised behaviour does not improve the mix-vs-behaviour split.
  - Q2.2 text vs numbers: finding "stated growth, actually declining" works best by comparing each program with its peers (AUC 0.62 → 0.78 on the Morgan Stanley mock). ebnm adds nothing over a z-score here.
  - Q2.4 structure: residual DenseLines makes a hidden co-moving group visible. A label-free brush recovers 75% of the Corning AI-demand group at 51% precision; brush OR text keyword reaches 94% recall. The brush disappears at ≥ 6 px smoothing.
  - Q2.5 seeing it: DenseLines works for about 1,000–1,800 short series once made gap-safe. The authors' reference returns NaN in every column when any program starts or stops. Arc-length normalisation barely matters at 5–6 points per series.
  - Still missing: real program-level budgets, actuals, headcount and decision packages for any firm. Next: a text-moderated prior for programs alone in their group; posterior DenseLines; rerun on a new-seed mock.
- **2026-11-14 (scheduled; completed 2026-11-15)** ([edition](2026-11-14.html)). No Q2 analysis; the picks targeted Q1 and Q3. Status and missing data unchanged.
- **2026-11-15 (scheduled)** ([edition](2026-11-15.html)). No Q2 analysis; the picks targeted Q1.4 and Q1.5. Watch item added for Q2: seriated lasagna plots (R seriation). Status and missing data unchanged.
- **2026-11-16 (scheduled)** ([edition](2026-11-16.html)). Method: mean-variance portfolio effect and Taylor's power law (ecofolio; fisheries ecology; interesting). SYNTHETIC mock ZBB data only (balanced panels: Corning_mock 778 of 1,079 programs, FY2020–25; MorganStanley_mock 1,404 of 1,840, FY2021–25). Answer key used only for scoring.
  - Q2.4 structure: the book co-moves far more than independent programs would (mean-variance PE 0.99 vs year-shuffle null median 7.28 on the Corning mock; 1.15 vs 13.22 on the MS mock; both p = 0.001), partly through the generator's raking to public totals. As a hidden-group screen the PE loses to plain mean pairwise correlation: planted clusters sit at the 0th–81st PE percentile vs the 100th correlation percentile.
  - Q2.3 real change vs noise: volatility scales with size at Taylor z = 1.67 / 1.77 (stable leaving out any year), so CV-based measures (average-CV PE 3.36 / 3.25; diversification ratio 3.14 / 3.10) overstate stability about threefold against the mean-variance PE (0.99 / 1.15). On noise-free true levels the average-CV PE falls to 1.54 / 2.63, so part of the apparent diversification is observation noise. Per-program volatility from 5–6 points does not flag planted movers (AUC 0.28–0.34 for the Taylor residual and CV).
  - Still missing: real program-level budgets, actuals, headcount and decision packages for any firm. Next: noise-corrected Taylor's law using budget–actual disagreement (top pick); PIM text-vs-numbers index for Q2.2 (pim's top pick).

<a id="q3"></a>

## Q3 — Stress-test projections and realized Y-9C payouts (approved 2026-11-14)

On 2026-11-14 Jared approved this pairing, together with Q1, with the wording "Number 1 and 4." The statement below is the approved wording. Status is `in progress` since the 2026-11-14 scheduled scout (completed 2026-11-15); see the Q3 progress log below.

**Question.** What is the connection between supervisory stress-test projections—severely adverse pre-tax net income, loan losses, capital-ratio drawdowns, and the stress capital buffer—and the same firms' realized payout ratios from FR Y-9C dividends and share repurchases? Do the buffer or the projected earnings path help describe subsequent payouts, and how do cross-firm patterns move from one test year to the next?

**Datasets, coverage, and join.**

- Federal Reserve supervisory stress-test results by firm, 2013–2026: [Stress Test Results, 2013–2026 (CSV)](https://www.federalreserve.gov/supervisionreg/files/public_results_DFAST_2026.csv) and the [data dictionary](https://www.federalreserve.gov/supervisionreg/files/DFAST_data_dictionary_2026.pdf), linked from the [DFAST 2026 results page](https://www.federalreserve.gov/supervisionreg/dfa-stress-tests-2026.htm). Join key: `id_rssd`. Fields include starting, ending and minimum CET1 / tier-1 / total / leverage ratios, loan losses by category, pre-provision net revenue, provisions, and projected pre-tax net income (`income_pretax_net_amt`, `income_pretax_net_rate`). Drop the 22 aggregate "participating banks" rows, which have no RSSD.
- FR Y-9C (BHCF) filings, 2008Q1–2026Q2, from the [FFIEC NIC Financial Data Download](https://www.ffiec.gov/npw/FinancialReport/FinancialDataDownload). Realized payouts from Schedule HI-A, year-to-date (use Q4): common dividends BHCK4460, preferred dividends BHCK4598, treasury-stock purchases BHCK4783 less sales BHCK4782, over net income BHCK4340 (or BHCT4340). Join `id_rssd` = RSSD9001.
- Supervisory scenario variables (macro paths, not firm-level earnings): baseline and severely adverse domestic series, plus history, as CSV files on each year's DFAST page (for 2026, paths run 2026Q1–2029Q1; history 1976Q1–2025Q4).
- Stress capital buffer: annual [Large Bank Capital Requirements](https://www.federalreserve.gov/supervisionreg/large-bank-capital-requirements.htm) PDFs, 2020–2026, by bank name. Map names to RSSD via the results file's `disclosure_legal_name` or Y-9C legal names. There is no official SCB CSV.

Natural timing: results are published mid-year Y, the SCB is effective 1 October Y, and realized payouts are measured in calendar Y and/or Y+1. Overlap with Y-9C covers the full 2013–2026 window.

**Firm counts** in the severely adverse scenario, after dropping aggregate rows. 45 unique RSSDs appear at least once. Only 11 firms are in all 14 annual severely adverse exercises (23 in at least 10; median 10). Odd-year drops are mostly Category IV biennial testers.

| Exercise | As-of date | Firms (severely adverse) | Other published firm-level scenarios |
|---|---|---:|---|
| DFAST 2013 | 2012-09-30 | 18 | none |
| DFAST 2014 | 2013-09-30 | 30 | Adverse (30) |
| DFAST 2015 | 2014-09-30 | 31 | Adverse (31) |
| DFAST 2016 | 2015-12-31 | 33 | Adverse (33) |
| DFAST 2017 | 2016-12-31 | 34 | Adverse (34) |
| DFAST 2018 | 2017-12-31 | 35 | Adverse (35) |
| DFAST 2019 | 2018-12-31 | 18 | Adverse (18) |
| DFAST 2020 | 2019-12-31 | 33 | none |
| December 2020 | 2020-06-30 | 33 | Alternative Severe (33) |
| DFAST 2021 | 2020-12-31 | 23 | none |
| 2022 Stress Test | 2021-12-31 | 33 | none |
| 2023 Stress Test | 2022-12-31 | 23 | none |
| 2024 Stress Test | 2023-12-31 | 31 | none |
| 2025 Stress Test | 2024-12-31 | 22 | none |
| 2026 Stress Test | 2025-12-31 | 32 | none |

**Sub-questions.**

1. **Cross-section.** Do firms with a worse severely adverse pre-tax path or a larger CET1 drawdown pay out less afterward, relative to peers?
2. **Buffer versus path.** Does the SCB (from 2020) describe realized payout ratios better than the raw projected earnings or drawdown?
3. **Year-to-year movement.** How stable is the cross-firm payout ranking between tests?
4. **Easier versus severe, where it exists.** For 2014–2019, does the Adverse-versus-Severely-Adverse gap relate to payouts? In December 2020, does Alternative Severe versus Severely Adverse?
5. **Composition.** Is it the payout mix (dividends versus buybacks) that moves, or the total ratio, especially once the stress test assumes standardized capital actions?

**Methods that fit.** ebnm across a small, noisy 18–35 firm cross-section; DenseLines of payout and drawdown paths; Lovell proportionality on the dividend-versus-buyback mix; codyn rank clocks of payout or capital-ratio ranks. A descriptive comparison of loss-mix compositions is optional; optimal transport is not central.

**Caveats.** There is **no firm-level baseline projected earnings or capital path** in the public results. Scenario identifiers are 2 (Supervisory Adverse), 3 (Supervisory Severely Adverse), and 30 (Supervisory Alternative Severe, December 2020 only). Baseline exists only as *macro* scenario variables. Adverse versus severely adverse firm results are available only for 2014–2019. The 2026 detailed nine-quarter paths file is an aggregate total under the severely adverse scenario, not a firm panel. After 2020 the supervisory projections use standardized capital-action assumptions, not each bank's own plan, so the SCB and later payouts are related in one direction by construction and must be read carefully. 2026 SCB requirements were held at 2025 levels pending model comments; new entrants get the 2.5% floor. SCB PDFs are name-based. Payout ratios are unstable when net income is near zero. HI-A items are year-to-date. Mergers and IHC versus BHC structures need a NIC map. The work is descriptive; it makes no claim about how a firm should set its dividend.

## Q3 progress log

- **2026-11-14 (scheduled; interrupted, completed 2026-11-15)** ([edition](2026-11-14.html)). Method: IDR (isotonic distributional regression, probabilistic weather forecasting; recommended for the promote workflow — not promoted). Public data: Fed stress-test results (severely adverse, 2013–2025; 643 rows verified against `public_results_DFAST_2026.csv`), Y-9C HI-A Q4 payouts (verified against BHCF zips), SCB from LBCR PDFs effective 2021–2026 (165 values verified). 360 firm-years, 40 firms. Leave-one-test-year-out CRPS skill vs climatology, within-year shuffle null (299).
  - Q3.1 cross-section: payout/RWA rank is antitonic in CET1-drawdown rank (skill 3.9%, p = 0.003) and isotonic in projected pre-tax income rank (15.0%, p = 0.003). On raw payout/RWA, IDR 5.8% vs OLS-normal −2.2%.
  - Q3.2 buffer vs path: in 2021–2025 (132 firm-years) the SCB has no skill (−1.9%, p = 0.24) despite Spearman 0.92 with drawdown; 37.9% of firm-years are at the 2.5% floor. Drawdown 7.0%, pre-tax income 11.3%; SCB + drawdown as a 2-D partial order 5.4% (OLS 10.6%).
  - Q3.3 year-to-year: a 2013–2019 fit transfers to 2021–2025 (skill 7.0%); the reverse does not (−6.1%). Payout-rank Kendall τ fell from 0.82–0.84 (2014–16) to 0.40–0.69 (2021–25).
  - Caveat: payouts are calendar year Y for test year Y, so about half precede that year's results; association only.
  - Q3.4 (Adverse vs Severely Adverse, 2014–2019) and Q3.5 (dividends vs buybacks) not run yet. Next: a monotone stress index (distributional single index) over pre-tax income, drawdown, losses and SCB, with a firm-block null; IDR on dividend and buyback shares separately.
  - Data still missing: firm-level baseline projections (not published); the October 2020 SCB PDF (the 11-14 download was an HTML error page).
- **2026-11-15 (scheduled)** ([edition](2026-11-15.html)). No Q3 analysis; the picks targeted Q1.4 and Q1.5. Status and missing data unchanged.
- **2026-11-16 (scheduled)** ([edition](2026-11-16.html)). Method: probabilistic index models (pim; biostatistics; recommended for the promote workflow — not promoted). Public data (the lab's verified 11-14 copies): Fed stress-test results incl. Adverse 2014–2019 and December 2020 Alternative Severe, Y-9C HI-A Q4 payouts incl. gross buybacks (BHCK4783), SCB 2021–2025. 360 firm-years, 40 firms; pairs only within a test year; 499 within-year permutations, 299 firm-block bootstraps; Holm within families.
  - Q3.1/Q3.2: per one-IQR difference, P(the firm higher has the higher payout/RWA) = 0.68 for SA pre-tax income (Holm 0.02) and 0.40 for SA CET1 drawdown (Holm 0.02); with both in the model drawdown is 0.50 (p = 0.89). SCB alone 0.46 (p = 0.20). SCB + drawdown jointly is unidentified (collinear). Next-year payouts keep the drawdown effect (0.44, p = 0.014). OLS on payout/net income loses 43% of its slope when 8 of 360 extreme ratios are trimmed; PIM moves < 2%.
  - Q3.4 (first run): the SA−Adverse drawdown gap adds nothing beyond the SA drawdown (0.42 per IQR, p = 0.12, Holm 0.72); same for next-year payouts and the pre-tax gap. December 2020 Alternative Severe gap: p = 0.21 (n = 33).
  - Q3.5 (first run): before 2020 the drawdown ranking lines up with dividends/RWA (0.36, Holm 0.02), not net buybacks (0.49, p = 0.82); after 2020 buybacks show it (0.44, p = 0.034, Holm 0.27) and the dividend-share effect vanishes. Tentative.
  - Data still missing: firm-level baseline projections (not published); the October 2020 SCB PDF. Next: firm-clustered PIM inference; Mallows rank model for Q3.3 (watch).

<a id="retired"></a>

## Retired

These questions are not scout targets. They stay here so earlier editions and the data gap remain on the record.

| ID | Added | Question (verbatim) | Status | Scout pages | Data located | Data missing |
|---|---|---|---|---|---|---|
| Q1 | 2026-11-10 | "How have prime broker revenue/activity share dynamics changed among the top 25 brokers and how can we gain insight into market based ones vs real sticky share migration?" | retired 2026-11-14 — data can't support firm-level PB shares; replaced by new Q1 | [2026-11-11](2026-11-11.html), [2026-11-12 ad hoc](2026-11-12-adhoc.html), [2026-11-12 scheduled](2026-11-12.html) | PROXY only: FR Y-9C trading panel 2008Q1–2026Q2 (public FFIEC/NIC BHCF; trading assets BHCK3545 and equity trading revenue BHCK8759 for US dealer BHCs and foreign-bank IHCs); FRED VIXCLS, NASDAQCOM. In Drive but not per-firm prime-brokerage data: GS/MS filings 2023–26 (2 firms), Form PF aggregates (Tab 8.28 prime-broker borrowing, aggregate only), SCOOS text, NY Fed fails, OFR repo, OCC quarterly derivatives PDFs 2016–26 (not parsed yet). | Per-firm prime-brokerage revenue for the top 25 (quarterly, 2010+); per-firm client financing balances (margin debits, synthetic/swap notional, shorts); hedge-fund relationship counts per prime broker (free route: SEC Form ADV Schedule D §7.B.(1) private-fund prime-broker entries, not yet built). Coalition Greenwich league tables are paywalled and not in Drive. |

<a id="retired-q1-2026-11-10"></a>

## Retired Q1 (2026-11-10) progress log

Retired on 2026-11-14: the available data cannot support firm-level prime-brokerage shares among the top 25, and this question was replaced by the new aggregate Q1 (Form PF borrowings, repo, and fails). The 2026-11-11 and 2026-11-12 scout editions below were aimed at this retired question, using a Y-9C trading-revenue proxy. They are historical; do not treat them as work on the current Q1.


- **2026-11-11** ([edition](2026-11-11.html)). Methods: MARSS (market vs sticky vs transient state-space split; recommended for the promote workflow) and InspectChangepoint (sparse "who moved" change points; interesting). PROXY results:
  - In the dealer trading-asset panel (14 dealers), the foreign-bank IHCs' share fell from 13.8% to 5.9% (2016Q3→2026Q2). JPM rose 21.3% → 27.4%. Market covariates account for almost none of the net shift (|market part| ≤ 0.05 clr for every dealer); the large net moves sit in the sticky state.
  - In big-4 equity trading revenue, market factors drive 59–74% of quarterly share-change variance for JPM, MS and BAC. GS's decline (52.3% → 23.1%, 2011Q1→2026Q2) is sticky, and its sticky losses mirror JPM's gains (corr −0.79, BH q = 0.04).
  - No change point in share levels survives a persistence-matched null, and no drift change is significant: the shifts are gradual, not abrupt.
  - Caveat: with 40 quarters, sticky vs slow mean reversion can't be told apart. With 62 it can.
  - Next: get any per-firm prime-brokerage series (or build the Form ADV prime-broker panel), rerun unchanged.

- **2026-11-12 (ad hoc)** ([edition](2026-11-12-adhoc.html)). Methods: codyn (ecology community dynamics and rank clocks; recommended for the promote workflow) and Lovell proportionality ρ (compositional genomics; recommended). PROXY results:
  - US dealer raw volumes co-move: Schluter VR = 4.45 on 14-dealer trading assets (cyclic-shift null 0.44–2.00) and 2.36 on big-4 equity trading revenue (null 0.57–1.66). The eight foreign IHCs, alone, do not (VR = 0.73, inside 0.29–2.19).
  - The share composition walks in one direction (Collins rate of change beats a cyclic-shift null at p = 0.001 on both panels). Incidence turnover is 0: this is a closed balanced panel, so migration is reordering, not entry/exit. UBS+CS falls from rank 7 to 14 (4.23% → 0.15%); on equity revenue, GS 52.3% → 23.1% and JPM 14.5% → 43.4%.
  - JPM–GS equity-revenue ρ = −0.698 (BH q = 0.021). After residualizing clr on VIX, Nasdaq, the BAA spread and industry growth, ρ = −0.882 (q = 0.036): a sticky swap. JPM–MS goes from −0.554 to −0.253 and is no longer significant: that opposition was the market’s. Pearson on raw shares overstates many 14-dealer pairs (Citi–UBS+CS −0.67 vs ρ −0.07); on 91 pairs and 40 quarters, no A-panel pair survives FDR.
  - Still missing: per-firm prime-brokerage revenue and balances for the top 25, or a Form ADV prime-broker panel. Next: get that series, rerun both pipelines unchanged (with a pre-registered pair list for ρ).
- **2026-11-12 (scheduled, catch-up published 2026-11-13)** ([edition](2026-11-12.html)). Methods: ecotraj (ecological trajectory analysis; recommended for the promote workflow) and lphom (LP voter-transfer matrices; interesting). PROXY results:
  - On 14-dealer trading-asset shares, residual (non-market) clr increments are directional: dir = 0.595 vs a sign-flip null, p = 0.008. Market steps explain only 16% of step energy; residual net displacement is 3.81 vs market 0.54. Overall path directionality 0.577 also beats sign-flip (p = 0.027) and a persistence-matched AR(1) (p = 0.001).
  - On big-4 equity trading revenue, residual net is a GS→JPM swap (GS −1.16, JPM +1.03 clr), consistent with MARSS and residual Lovell ρ, but residual directionality is not significant (p = 0.365) and the overall path fails a sign-flip null (p = 0.664). The path wiggles; the endpoints still move.
  - lphom cannot identify a quarterly transfer matrix from this single closed panel (median deterministic bound width 0.88; 63% of cells wider than 0.80). A planted 1% GS→JPM flow is not recovered (median L1 error 0.68). Product-year units (54) are a better design but still high-error. The method needs Form ADV Schedule D filers as voting units.
  - Still missing: per-firm prime-brokerage revenue and balances for the top 25, or a Form ADV prime-broker panel. Next: build that panel; rerun ecotraj’s increment split unchanged; retry lphom with tslphom/nslphom on real units.

- **2026-11-13 (scheduled)** ([edition](2026-11-13.html)). No Q1 analysis; today's picks targeted Q2. Missing data unchanged: per-firm prime-brokerage revenue and balances for the top 25, or a Form ADV Schedule D prime-broker panel.
