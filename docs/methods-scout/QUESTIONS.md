# Methods scout: research questions

Standing questions from Jared that steer the daily methods scout. Each day the scout picks methods aimed at an
open question, and at least one analysis per method targets it directly. Question text is Jared's wording, verbatim.
Status: `open` · `in progress` · `answered` · `parked`.

| ID | Added | Question (verbatim) | Status | Scout pages | Data located | Data missing |
|---|---|---|---|---|---|---|
| Q1 | 2026-11-10 | "How have prime broker revenue/activity share dynamics changed among the top 25 brokers and how can we gain insight into market based ones vs real sticky share migration?" | in progress | [2026-11-11](2026-11-11.html) | PROXY only: FR Y-9C trading panel 2008Q1–2026Q2 (public FFIEC/NIC BHCF; trading assets BHCK3545 and equity trading revenue BHCK8759 for US dealer BHCs and foreign-bank IHCs); FRED VIXCLS, NASDAQCOM. In Drive but not per-firm prime-brokerage data: GS/MS filings 2023–26 (2 firms), Form PF aggregates (Tab 8.28 prime-broker borrowing, aggregate only), SCOOS text, NY Fed fails, OFR repo, OCC quarterly derivatives PDFs 2016–26 (not parsed yet). | Per-firm prime-brokerage revenue for the top 25 (quarterly, 2010+); per-firm client financing balances (margin debits, synthetic/swap notional, shorts); hedge-fund relationship counts per prime broker (free route: SEC Form ADV Schedule D §7.B.(1) private-fund prime-broker entries, not yet built). Coalition Greenwich league tables are paywalled and not in Drive. |

## Q1 progress log

- **2026-11-11** ([edition](2026-11-11.html)). Methods: MARSS (market vs sticky vs transient state-space split; recommended for the promote workflow) and InspectChangepoint (sparse "who moved" change points; interesting). PROXY results:
  - In the dealer trading-asset panel (14 dealers), the foreign-bank IHCs' share fell from 13.8% to 5.9% (2016Q3→2026Q2). JPM rose 21.3% → 27.4%. Market covariates account for almost none of the net shift (|market part| ≤ 0.05 clr for every dealer); the large net moves sit in the sticky state.
  - In big-4 equity trading revenue, market factors drive 59–74% of quarterly share-change variance for JPM, MS and BAC. GS's decline (52.3% → 23.1%, 2011Q1→2026Q2) is sticky, and its sticky losses mirror JPM's gains (corr −0.79, BH q = 0.04).
  - No change point in share levels survives a persistence-matched null, and no drift change is significant: the shifts are gradual, not abrupt.
  - Caveat: with 40 quarters, sticky vs slow mean reversion can't be told apart. With 62 it can.
  - Next: get any per-firm prime-brokerage series (or build the Form ADV prime-broker panel), rerun unchanged.
