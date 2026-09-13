# Frozen PLEIA temperature model-comparison pilot v1

Frozen before research fitting. This protocol is specific to the model-comparison pilot; it does not amend the operational alert-selection protocol.

- Dataset: existing retained PLEIA temperature series; no cohort reduction.
- Existing fold order: latest test block is outer fold ID 0 (first in the declared order).
- Horizons: 1/3/6 steps (10/30/60 minutes); model seed 42; persistence, XGBoost, Attention-LSTM.
- Final calibration is reserved before tuning. Two expanding, purged validation folds within the fitting pool tune both learned models.
- Selection: equally weighted mean inner-fold MAE in original units; exact ties choose the earlier frozen candidate.
- Budget: two candidates per learned model per horizon, two folds each: 12 tuning fits per learned model, plus three final fits each. Persistence has no tuning.
- XGBoost: 400 trees, depths 3 or 5; other values in the configuration. These are a declared pilot budget, not the full historical 20-draw search.
- Attention-LSTM: existing 64 hidden units, dropout 0.2, batch 256, max 30 epochs, patience 5; learning rates 0.001 or 0.0005. Inner validation handles early stopping.
- Final LSTM epoch count is ceil(mean of the selected candidate best epochs across the two inner folds)); final normalisation and refit use all permitted fitting rows.
- Intervals: ordinary fixed split conformal with each final model own absolute calibration errors; rank ceil((n_cal+1)*level), no quantile interpolation. Unsupported rank yields infinite q with an explicit insufficient-calibration status.
- No fault injection, alert selection, adaptive recalibration or test-driven setting changes.
- Common valid row IDs are fixed within horizon before any fit. Sequence inputs are lazy and batched, including validation.
- CPU only, serial units, all controlled numerical/Torch threads 1, n_jobs=1. Baseline/peak working set and private memory measured with native Windows APIs.
- Launch guard: 768 MiB available RAM; epoch guard: 256 MiB. Neither guard changes scientific settings.
- Expected outputs: nine point summaries and eighteen interval-quality cells, with model artifacts, all predictions/calibration errors/bounds and checkpoints.

| Horizon | Role | n | First origin | Last origin | Last target |
|---|---|---:|---|---|---|
| 1 | fit | 29719 | 2021-01-08 00:00:00 | 2021-08-02 09:00:00 | 2021-08-02 09:10:00 |
| 1 | calibration | 9907 | 2021-08-02 09:20:00 | 2021-10-10 04:20:00 | 2021-10-10 04:30:00 |
| 1 | test | 9907 | 2021-10-10 04:40:00 | 2021-12-17 23:40:00 | 2021-12-17 23:50:00 |
| 1 | inner0_train | 9905 | 2021-01-08 00:00:00 | 2021-03-17 18:40:00 | 2021-03-17 18:50:00 |
| 1 | inner0_validation | 9905 | 2021-03-17 19:00:00 | 2021-05-25 13:40:00 | 2021-05-25 13:50:00 |
| 1 | inner1_train | 19810 | 2021-01-08 00:00:00 | 2021-05-25 13:40:00 | 2021-05-25 13:50:00 |
| 1 | inner1_validation | 9907 | 2021-05-25 14:00:00 | 2021-08-02 09:00:00 | 2021-08-02 09:10:00 |
| 3 | fit | 29715 | 2021-01-07 23:40:00 | 2021-08-02 08:00:00 | 2021-08-02 08:30:00 |
| 3 | calibration | 9906 | 2021-08-02 08:50:00 | 2021-10-10 03:40:00 | 2021-10-10 04:10:00 |
| 3 | test | 9907 | 2021-10-10 04:20:00 | 2021-12-17 23:20:00 | 2021-12-17 23:50:00 |
| 3 | inner0_train | 9902 | 2021-01-07 23:40:00 | 2021-03-17 17:50:00 | 2021-03-17 18:20:00 |
| 3 | inner0_validation | 9902 | 2021-03-17 18:30:00 | 2021-05-25 12:40:00 | 2021-05-25 13:10:00 |
| 3 | inner1_train | 19804 | 2021-01-07 23:40:00 | 2021-05-25 12:40:00 | 2021-05-25 13:10:00 |
| 3 | inner1_validation | 9905 | 2021-05-25 13:20:00 | 2021-08-02 08:00:00 | 2021-08-02 08:30:00 |
| 6 | fit | 29710 | 2021-01-07 23:10:00 | 2021-08-02 06:40:00 | 2021-08-02 07:40:00 |
| 6 | calibration | 9904 | 2021-08-02 08:10:00 | 2021-10-10 02:40:00 | 2021-10-10 03:40:00 |
| 6 | test | 9907 | 2021-10-10 03:50:00 | 2021-12-17 22:50:00 | 2021-12-17 23:50:00 |
| 6 | inner0_train | 9897 | 2021-01-07 23:10:00 | 2021-03-17 16:30:00 | 2021-03-17 17:30:00 |
| 6 | inner0_validation | 9897 | 2021-03-17 17:40:00 | 2021-05-25 11:00:00 | 2021-05-25 12:00:00 |
| 6 | inner1_train | 19794 | 2021-01-07 23:10:00 | 2021-05-25 11:00:00 | 2021-05-25 12:00:00 |
| 6 | inner1_validation | 9904 | 2021-05-25 12:10:00 | 2021-08-02 06:40:00 | 2021-08-02 07:40:00 |

All three horizons evaluate 9,907 observations, with target timestamps from 2021-10-10 04:50 to 2021-12-17 23:50. Origin times differ by horizon. Full membership and boundary hashes are in the adjacent frozen JSON and CSV files.

This is previously inspected data. Temporal dependence limits the ordinary exchangeability-based split-conformal guarantee. One outer fold and one seed cannot establish statistical superiority or final dissertation performance. Read width alongside coverage.

Operational endpoints, core inner-fold aggregation, fault definitions, DSCP/seasonal evaluation and group-recovery inference remain pending in the completion plan.
