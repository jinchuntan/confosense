# UCI Occupancy auxiliary check — limitations

Read alongside `uci_auxiliary_results.md`. These limitations are the reason this
experiment is auxiliary evidence about the *software* and not evidence about
forecasting, uncertainty quantification or monitoring.

---

## 1. Scope limitations — what this experiment cannot support

| It cannot show | Why |
|---|---|
| That any model is generally superior | Two point models on one target at two horizons. |
| That conformal prediction is universally valid | Two interval methods, one dataset, and CQR reached only 0.8169 coverage at nominal 0.95 at 5 minutes. |
| Improved anomaly detection or alert reliability | No alert rule was tuned and no fault labels exist; only a descriptive violation rate is reported. |
| Superiority over the original UCI study | That study is a binary *occupancy classification* task. This is continuous temperature forecasting. The two are not comparable, and no comparison is attempted. |
| Generalisation across smart buildings | One office room, sixteen days, one winter period, one building. |
| Anything about the ConfoSense configuration | These results were not used to select or redefine any component. |

The single claim supported is: **the generic pipeline operated correctly on an
independent public building-sensor dataset with only a small adapter.**

---

## 2. Dataset limitations

1. **One room, one building, sixteen days.** 2015-02-02 to 2015-02-18, a single
   office. No spatial or seasonal variety.
2. **Two recording discontinuities**, of 7 h 08 min and 1 d 05 h 15 min. They
   were preserved as segment boundaries rather than bridged, which is correct,
   but it means the series is not one continuous record.
3. **The dataset's own train/test split is unusable for forecasting.** The file
   named `datatraining.txt` is chronologically the *middle* segment, so the
   authors' division would train on data postdating part of its test set.
4. **Purpose mismatch.** The dataset was built for binary occupancy detection.
   Temperature is present as a *predictor* in the original design; using it as a
   forecasting target is a legitimate reuse, but it is a reuse.
5. **The target is very smooth.** Minute-sampled office air temperature gives
   MAE of 0.03–0.06 °C, so the forecasting task is close to trivial at these
   horizons and does not discriminate strongly between methods.

---

## 3. Methodological limitations of this run

1. **CQR is poorly calibrated in one cell and over-covers in another** — 0.8169
   at h = 5 and 0.9834 at h = 15, both against nominal 0.95. Retained as
   measured; no method was retuned to improve it.
2. **Modest hyperparameter search.** 10 random search iterations against 20 in
   the primary study, deliberately, since this is a portability check.
3. **One CQR seed.** Multi-seed interval spread is not characterised.
4. **No Attention-LSTM.** The generic pipeline path was demonstrable without it,
   and running it would have added cost without adding evidence.
5. **Calibration and test both fall inside one segment** (`datatest2`). That is
   the honest consequence of a pooled chronological cut on a 60/20/20 split with
   these segment lengths, but it means calibration and test share a single
   recording session, which is a weaker test of exchangeability than the primary
   datasets provide.
6. **Only 5 and 15 minute horizons.** No statement about longer horizons.
7. **A new partitioning strategy was introduced for this dataset**
   (`PooledChronologicalPartitioner`). It is defined inside the UCI adapter
   module rather than in the core so that the frozen primary experiments cannot
   be affected. It has not been exercised on any other dataset.

---

## 4. Statistical limitations

1. **Excluded from every cross-dataset statistical test.** UCI does not appear
   in the Friedman analysis, the Holm post-hoc, or the Diebold–Mariano tables in
   `outputs/full_study/combined/`. Those remain 4 datasets, 13 dataset/horizon
   cells, 9 complete blocks.
2. **No formal significance testing was performed here.** Bootstrap confidence
   intervals are reported because the generic routine made them free; no
   hypothesis test is run and none should be inferred. At h = 15 the persistence
   and XGBoost MAE intervals overlap substantially.
3. **No multiple-comparison correction** was applied, because no family of tests
   was performed.

---

## 5. Reproducibility notes

* The archive is downloaded on demand and its sha256 is recorded
  (`manifests/dataset_source.json`); raw files stay gitignored.
* XGBoost refits are single-threaded, so the fit does not depend on core count.
* Seed 42 throughout; 3 XGBoost seeds with MAE standard deviation 0.0002.
* Tests use synthetic fixtures and never download.

---

## 6. Correct framing for the dissertation

Permissible:

> "An auxiliary experiment on the UCI Occupancy dataset confirmed that the
> generic pipeline operates on an independent public building-sensor dataset."

Not permissible:

> "ConfoSense generalises to the UCI Occupancy dataset."
> "Conformal prediction was validated on a fifth dataset."
> "ConfoSense outperforms the original UCI occupancy study."
> "The framework achieved 0.92 coverage on UCI." *(true only at nominal 0.90 and
> h = 5; quoting it without the level and horizon misrepresents the run)*

See `dissertation_positioning.md` for placement and prepared wording.
