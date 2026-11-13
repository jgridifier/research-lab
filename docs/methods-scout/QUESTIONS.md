# Methods scout: research questions

Standing questions from Jared that steer the daily methods scout. Each day the scout picks methods aimed at an
open question, and at least one analysis per method targets it directly. Question text is Jared's wording, verbatim.
Status: `open` · `in progress` · `answered` · `parked`.

| ID | Added | Question (verbatim) | Status | Scout pages | Data located | Data missing |
|---|---|---|---|---|---|---|
| Q1 | 2026-11-10 | "How have prime broker revenue/activity share dynamics changed among the top 25 brokers and how can we gain insight into market based ones vs real sticky share migration?" | in progress | [2026-11-11](2026-11-11.html), [2026-11-12 ad hoc](2026-11-12-adhoc.html), [2026-11-12 scheduled](2026-11-12.html) | PROXY only: FR Y-9C trading panel 2008Q1–2026Q2 (public FFIEC/NIC BHCF; trading assets BHCK3545 and equity trading revenue BHCK8759 for US dealer BHCs and foreign-bank IHCs); FRED VIXCLS, NASDAQCOM. In Drive but not per-firm prime-brokerage data: GS/MS filings 2023–26 (2 firms), Form PF aggregates (Tab 8.28 prime-broker borrowing, aggregate only), SCOOS text, NY Fed fails, OFR repo, OCC quarterly derivatives PDFs 2016–26 (not parsed yet). | Per-firm prime-brokerage revenue for the top 25 (quarterly, 2010+); per-firm client financing balances (margin debits, synthetic/swap notional, shorts); hedge-fund relationship counts per prime broker (free route: SEC Form ADV Schedule D §7.B.(1) private-fund prime-broker entries, not yet built). Coalition Greenwich league tables are paywalled and not in Drive. |
| Q2 | 2026-11-13 | "Want to add a guiding question about like let’s say you have a ton of decriptions, and we extract out some classifications and then get some implied features, understanding the trends and composition over time but like what else would be really interesting to look at -think ok like a budgeting use case where the rest hundreds or thousands of program all with their own noise and not that much history" | open | — | SYNTHETIC mocks only (built 2026-11-13): program-level zero-based-budgeting datasets modeled on publicly reported figures for a manufacturer like Corning Incorporated and a financial firm like Morgan Stanley, in the Drive folder "Q2 mock ZBB datasets (synthetic, 2026-11-13)". Clearly labelled synthetic; they are not either firm's actual budgets and contain no private data. | Real program-level budgets, actuals, headcount and decision packages for any firm. The mocks are a stand-in so methods can be tried before any real data arrives. |

## Q2 — refined statement (approved 2026-11-13)

Jared's original wording is in the table above, kept verbatim (including "decriptions" and "the rest hundreds"). On 2026-11-13 he approved the refined question, all five sub-questions, and the addition of tabular data alongside the free-text descriptions. Status is `open`. Nothing has been run against this question yet.

**Refined question.** Suppose we have hundreds to thousands of programs. Each one has free-text descriptions plus tabular data, which we turn into categories and implied features, and each has only a few noisy periods of numbers. Past tracking trends and category mix over time, what can we reliably learn about each program and about the portfolio as a whole?

**Sub-questions.**

1. **Borrowing strength.** If we pool similar programs, how much better do we estimate each one's real level and trend than by looking at it alone, given how short its history is?
2. **Text versus numbers.** Which programs' spending doesn't match what their descriptions say, and which ones quietly change category over time?
3. **Real change or noise.** When a total moves, how much comes from the program mix changing, how much from programs actually behaving differently, and how much is just noise?
4. **Structure.** Do programs form groups that rise and fall together, or trade off against each other, in ways the categories don't show?
5. **Seeing it.** How can one chart show a thousand short, noisy series without turning into spaghetti?

## Q1 progress log

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
