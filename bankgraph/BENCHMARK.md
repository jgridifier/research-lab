# BankGraph — our own relational benchmark (v0.1, 2026-11-03)

Built only from the jgridley.mailinglists Drive ("Bank forecasting datasets", "BHCF 2008-2017") plus FFIEC HMDA reporter panels (LEI↔RSSD crosswalk). Not RelBench.

## Reproduce
```
python -m venv .venv && . .venv/bin/activate && pip install pandas pyarrow duckdb lightgbm scikit-learn
python scripts/build.py      # data/raw -> data/db/*.parquet, bankgraph.duckdb, reports/inventory.json, reports/join_coverage.csv
python scripts/tasks.py      # tasks/<task>/{trainval,test_features,test_labels}.parquet ; holdout only if RELBENCH_UNSEAL=1
python scripts/baselines.py  # train->val only -> reports/baselines_val.csv
```

## Schema (PK / FK / time column)
| table | PK | FKs | time |
|---|---|---|---|
| bank | CERT | RSSDID, RSSDHCR→holding_company | – |
| bank_quarter | (CERT, quarter) | CERT→bank | quarter end; available +45d |
| branch_year | (CERT, BRNUM, year) | CERT→bank; RSSDHCR→holding_company; STALPBR→state | June 30; available +120d |
| holding_company | RSSDHCR | – | – |
| hc_state_year | (RSSDHCR, state, year) | →holding_company, →state | June 30 +120d |
| hmda_lender_year | (lei, year) | respondent_rssd→bank.RSSDID; topholder→holding_company | year Y available Apr 1 Y+1 |
| hmda_lender_state_year | (lei, state, year) | →hmda_lender_year, →state | as above |
| company_entity_map | company | CERT / RSSDHCR (name rule; 4.2% of companies, 47.6% of complaints) | – |
| complaint_company_month_product | (company, month, product) | company→company_entity_map | month end |
| macro_series, sloos_series | (series, date) | – | observation date (+ publication lag for SLOOS) |
| bhcf_hc_quarter_2017q4 | RSSD9001 | →holding_company | 2017Q4 only |

Join coverage is measured, not assumed: reports/join_coverage.csv.

## Tasks
| id | entity × cutoff | label | metric |
|---|---|---|---|
| T1 bank-deposit-decline | bank × quarter | DEP(q+1) < DEP(q) | AUC |
| T2 branch-closure | branch × year | (CERT,BRNUM) absent in Y+1 while CERT alive; no branch within ~100 m (renumbering guard) | AUC |
| T3 complaint-spike | company × month | next month ≥ 2× trailing-6m median and ≥ 20; eligible if ≥ 60 in 6m | AUC |
| T4 hmda-share-drop | lender × state × year | next-year state share < 0.75× current; n ≥ 50 | AUC |
| T5 hc-state-deposit-growth | holdco × state × year | log deposit growth Y→Y+1, clipped ±1; deposits ≥ $10M | MAE |

## Splits (by cutoff date; config/splits.json)
| task | train | val | test | sealed holdout |
|---|---|---|---|---|
| T1 | 2008–2016 | 2017–2019 | 2020–2023 | 2024–2026 |
| T2 | 2008–2015 | 2016–2018 | 2019–2021 | 2022–2025 |
| T3 | 2012–2018 | 2019–2020 | 2021–2023 | 2024–2026 |
| T4 | 2019–2020 | 2021 | 2022–2023 | 2024–2025 |
| T5 | 2008–2015 | 2016–2018 | 2019–2021 | 2022–2025 |

## Leakage rules
1. Every feature uses only rows whose availability date (time column + publication lag) ≤ cutoff.
2. Labels look strictly after the cutoff; no label-window data in features.
3. Peer aggregates are leave-one-out (the entity is excluded from its own peer group).
4. Static mappings (company_entity_map, bank→holdco RSSDHCR, LEI↔RSSD crosswalk) are treated as time-invariant in v0.1. This is a known, documented approximation (ownership changes over time); the NIC relationships file (data list #1) would remove it.
5. Test labels live in a separate file; models and Kumo calls receive only test_features. Holdout rows are not materialized unless RELBENCH_UNSEAL=1, which is set only for a final, pre-announced run.
6. Hyperparameters fixed in advance (LightGBM: 400 trees, lr 0.03, 31 leaves, min_child 50, subsample/colsample 0.8, seed 0; l1 for regression). No tuning on test.

## Metrics
AUC (classification) / MAE (regression), with 95% entity-cluster bootstrap CI (B=500; 200 when n_val > 50k). Paired deltas are bootstrapped with the same resamples.

## Pre-registered comparison bars (fixed before any Kumo/TRACE run)
- A challenger (KumoRFM, TRACE) "beats" a task only if, on **test**, challenger − lgbm_relational has a paired bootstrap 95% CI excluding 0 in its favor.
- "Ties" if the CI covers 0; "loses" if the CI excludes 0 against it.
- Headline = count of wins/ties/losses across T1–T5; no averaging across metrics.
- Challengers get the same tables and cutoffs; no test or holdout data in context.
- T4 is flagged: all baselines are near AUC 0.5 on val, so a T4 result is reported but given low weight.
- The holdout is opened once, after test results are written down.

## Validation baselines (train→val) — see reports/baselines_val.csv
| task | model | metric | val | 95% CI |
|---|---|---|---|---|
| bank-deposit-decline | naive | AUC | 0.5079 | [0.4681, 0.5462] |
| bank-deposit-decline | linear_single | AUC | 0.5791 | [0.5416, 0.6210] |
| bank-deposit-decline | lgbm_single | AUC | 0.6443 | [0.6050, 0.6788] |
| bank-deposit-decline | lgbm_relational | AUC | 0.6253 | [0.5869, 0.6625] |
| bank-deposit-decline | lgbm_relational - lgbm_single | delta rel-single | -0.0190 | [-0.0405, 0.0019] |
| branch-closure | naive | AUC | 0.5707 | [0.5590, 0.5819] |
| branch-closure | linear_single | AUC | 0.6749 | [0.6562, 0.6929] |
| branch-closure | lgbm_single | AUC | 0.6922 | [0.6748, 0.7096] |
| branch-closure | lgbm_relational | AUC | 0.7603 | [0.7444, 0.7769] |
| branch-closure | lgbm_relational - lgbm_single | delta rel-single | 0.0681 | [0.0559, 0.0827] |
| complaint-spike | naive | AUC | 0.8246 | [0.7634, 0.8736] |
| complaint-spike | linear_single | AUC | 0.8463 | [0.7920, 0.8938] |
| complaint-spike | lgbm_single | AUC | 0.8609 | [0.8147, 0.8995] |
| complaint-spike | lgbm_relational | AUC | 0.8440 | [0.7925, 0.8852] |
| complaint-spike | lgbm_relational - lgbm_single | delta rel-single | -0.0169 | [-0.0418, 0.0113] |
| hmda-share-drop | naive | AUC | 0.4691 | [0.4387, 0.4976] |
| hmda-share-drop | linear_single | AUC | 0.4976 | [0.4729, 0.5228] |
| hmda-share-drop | lgbm_single | AUC | 0.4800 | [0.4522, 0.5053] |
| hmda-share-drop | lgbm_relational | AUC | 0.4988 | [0.4629, 0.5329] |
| hmda-share-drop | lgbm_relational - lgbm_single | delta rel-single | 0.0187 | [0.0023, 0.0375] |
| hc-state-deposit-growth | naive | MAE | 0.0894 | [0.0864, 0.0922] |
| hc-state-deposit-growth | naive_last_growth | MAE | 0.1049 | [0.1005, 0.1093] |
| hc-state-deposit-growth | linear_single | MAE | 0.0800 | [0.0770, 0.0828] |
| hc-state-deposit-growth | lgbm_single | MAE | 0.0783 | [0.0753, 0.0813] |
| hc-state-deposit-growth | lgbm_relational | MAE | 0.0772 | [0.0744, 0.0803] |
| hc-state-deposit-growth | train_median | MAE | 0.0806 | [0.0777, 0.0835] |
| hc-state-deposit-growth | lgbm_relational - lgbm_single | delta rel-single | -0.0011 | [-0.0015, -0.0006] |
