# Data to collect (prioritized) — URLs checked 2026-11-03

| # | Dataset | Why (which join/task it fixes) | URL | Check |
|---|---|---|---|---|
| 1 | FFIEC NIC attributes + relationships + transformations | Ownership over time (bank→holdco by date) and mergers; replaces the one-snapshot RSSDHCR; lets branch-closure separate mergers from closures | https://www.ffiec.gov/npw/FinancialReport/DataDownload | page read 2026-11-03 (curl 403, browser/WebFetch OK) |
| 2 | FDIC SOD full branch file (API) with UNINUMBR + STCNTYBR | Stable branch id (fixes BRNUM renumbering guard) and county FIPS (Drive extract has 0% county) | https://api.fdic.gov/banks/sod (fields UNINUMBR, STCNTYBR confirmed in live response) | 200 |
| 3 | Call report for all banks (FFIEC CDR bulk) | Drive panel is top-100 only; SOD has 8,615 CERTs, only 98 in call report (1.1%) | https://cdr.ffiec.gov/public/PWS/DownloadBulkData.aspx | 200 |
| 4 | FR Y-9C all quarters 2008–2026 (Chicago Fed history + FFIEC NIC) | Drive BHCF locally used 2017Q4 only (69% of top-100 holdcos); full series makes holdco a time-varying table | https://www.chicagofed.org/banking/financial-institution-reports/bhc-data | 200 |
| 5 | HMDA reporter panel 2024 + LEI↔RSSD | 2024 panel 404 at files.ffiec.cfpb.gov; 2018–23 panels downloaded | https://files.ffiec.cfpb.gov/static-data/snapshot/2023/2023_public_panel_csv.zip (pattern) | 200 (2024: 404) |
| 6 | HMDA applications incl. denials (data-browser API) | Drive HMDA is originations only, so no denial rate | https://ffiec.cfpb.gov/v2/data-browser-api/view/aggregations?years=2023&actions_taken=3&states=CA | 200 |
| 7 | GLEIF LEI records + relationship files | Covers HMDA nonbanks (20% LEI-years unmatched) and CFPB fintechs | https://www.gleif.org/en/lei-data/gleif-golden-copy/download-the-golden-copy ; https://api.gleif.org/api/v1/lei-records | 200 |
| 8 | FDIC institution history + failures | Charter events, mergers, failures as labels/events | https://api.fdic.gov/banks/history ; https://api.fdic.gov/banks/failures ; https://www.fdic.gov/bank-failures/failed-bank-list | 200 |
| 9 | CFPB complaints full file (company + ZIP + issue) | Already in Drive (351 MB) but not used; adds state/ZIP and issue granularity | https://files.consumerfinance.gov/ccdb/complaints.csv.zip | 200 |
| 10 | CRA disclosure files by bank | Small-business lending by county per bank | https://www.ffiec.gov/data/cra/flat-files | page read (curl 403) |
| 11 | Census ACS (county) + county codes | County covariates once SOD county is available | https://api.census.gov/data/2022/acs/acs5 ; https://www2.census.gov/geo/docs/reference/codes2020/national_county2020.txt | 200 |
| 12 | BLS LAUS county unemployment; QCEW | Local labor shocks | https://www.bls.gov/lau/ ; https://www.bls.gov/cew/downloadable-data-files.htm | page read (curl 403) |
| 13 | BEA regional income; FHFA HPI | Local income/house prices | https://apps.bea.gov/regional/downloadindex.cfm ; https://www.fhfa.gov/data/hpi/datasets | 200 |
| 14 | Census County Business Patterns | County establishment counts | https://www2.census.gov/programs-surveys/cbp/datasets/2022/cbp22co.zip | 200 |
| 15 | NCUA credit-union call reports | Navy Federal etc. unmatched in CFPB/HMDA | https://www.ncua.gov/analysis/credit-union-corporate-call-report-data/quarterly-data | 200 |
| 16 | SEC XBRL frames | Public holdco financials, market-facing | https://data.sec.gov/api/xbrl/frames/us-gaap/Assets/USD/CY2023Q4I.json | 200 |
| 17 | Fed enforcement actions | Event labels / features | https://www.federalreserve.gov/supervisionreg/enforcementactions.htm | 200 |
| 18 | NY Fed CRSP–FRB link | Market data for listed holdcos | https://www.newyorkfed.org/research/banking_research/crsp-frb | 200 |

Not verified (404 or unreachable from box, so not listed as a working source): Fed mergers app, OCC and FDIC enforcement-order pages.
