# Pre-registration, scheduled methods scout 2026-11-17 (written 14:40 ET before any Q1/Q3 run)

## Method 1 — Event coincidence analysis (ECA), Q1 (public aggregates)
Data: weekly (Wednesday) 2018-05-16..2026-09-23 from the lab copies (NY Fed financing fails PDFTD-USTET; OFR DVP outstanding; OFR DVP overnight minus tri-party rate; CFTC TFF leveraged-fund net short UST 2Y+5Y+10Y, through 2025-12-31 only). Single-week gaps interpolated (2 weeks).
Events: top 10% of weekly changes (fails = log change, spread = bp change, DVP = log change, lev = change in net short k contracts); lev also bottom 10% (unwind).
Family F1 (48 tests): pairs (A <- B) fails<-spread, spread<-fails, fails<-levbuild, fails<-levunwind, spread<-levbuild, spread<-levunwind, dvp<-fails, fails<-dvp; tau in {0,2,4} weeks, delT = 1; precursor and trigger rates.
Null: circular shift of B (shift >= 8 weeks), 4999 surrogates; Holm over the 48. Finding = Holm p < 0.05.
Secondary: CoinCalc Poisson p for the same 48 (to compare).
Calibration check (pass bar): Poisson-test false-positive rate on 2,000 circularly shifted (independent-by-construction) fails<-spread pairs at tau 0; Poisson is "miscalibrated here" if FPR > 0.10 at nominal 0.05.
Standard comparator: Pearson correlation of the continuous changes at lags 0..5 with the same circular-shift null.
Stability (pass bar for any F1 finding): rate exceeds its null 95th percentile in both halves (split 2022-06-29/2022-07-06) and at event thresholds 80% and 95%.
Time-resolved: rolling 104-week precursor rate for the top pair (descriptive).
Family F2 (monthly, 12 tests): Form PF tab 8.27 prime-broker and total borrowing growth top 20% months vs months whose mean financing fails rose most (top 20% log change), 2013-05..2025-12; tau in {0,3,6} months, delT = 2; precursor and trigger, PF->fails direction only (A = fails, B = PF) plus reverse at tau 0. Circular-shift null 4999, Holm within F2. Reference month, not publication date.
Home-field reproduction: CoinCalc paper examples 4.1 and 4.2 must reproduce to printed digits; NumPy port must match CoinCalc to 1e-9.

## Method 2 — STATIS family (COVSTATIS / dual STATIS; partial triadic analysis), Q3 (public)
Data: lab's verified 11-14/11-16 Q3 panel (Fed stress-test results, severely adverse; Y-9C HI-A Q4 payouts), exercises 2013..2025 (13 tables).
Variables (7): SA CET1 drawdown, SA pre-tax net income rate, SA total loan-loss rate, starting CET1, payout/RWA, dividends/RWA, net buybacks/RWA. Per year: Spearman correlation matrix over the firms that year.
COVSTATIS: MFA-normalised (first eigenvalue = 1) matrices, RV interstructure, weights = first eigenvector, compromise, partial factor scores.
B1 era split (Q3.3): statistic D = mean within-era RV - mean between-era RV for eras 2013-2019 vs 2020-2025; exact permutation over all C(13,6) era assignments; pass p < 0.05.
B2 noise: firm bootstrap within year (299) of RV(year, compromise); a year "departs" if its bootstrap 95% upper bound is below the median of other years' RV to compromise. Robustness: Smilde modified RV.
B3 which link moved: per variable, total distance of its yearly partial points from the compromise point; per variable pair, era change in compromise-space cosine; compare to the standard plot (year-by-year Spearman payout vs drawdown with bootstrap band).
B4 balanced firms: X-STATIS/PTA via ade4 on the firms present in every exercise of a window; parity of NumPy port vs ade4 (RV matrix, weights, compromise eigenvalues) to 1e-6.
Descriptive only. Payouts are calendar year Y; association, not causation. No Y-9C forecasts.
