# Dissertation positioning: the UCI Occupancy auxiliary experiment

## Recommendation

**APPENDIX / SUPPLEMENTARY VALIDATION.**

Place this experiment in a short appendix — suggested **Appendix J, "Auxiliary
pipeline-portability check"** — with a single cross-reference of two or three
sentences from Chapter 3 (§3.12, Reproducibility) or Chapter 7 (§7.4,
Experimental contribution).

Do **not** place it in Chapter 5. Do **not** add it to the four-dataset
benchmark matrix, the cross-dataset statistical comparison, the alert benchmark,
or `combined/confosense_configurations.csv`.

## Why appendix rather than main body

1. **It answers a software question, not a research question.** None of RQ1–RQ3
   is advanced by it. Its finding is that the implementation is portable.
2. **The dataset was designed for a different task.** UCI Occupancy is a binary
   occupancy-classification dataset; temperature is a *predictor* in its
   original design. Using it as a forecasting target is a legitimate reuse but
   not an equivalent experimental setting.
3. **Its scope is a fraction of a primary setting.** Two point models against
   four, two interval methods against five, two horizons, no alerting, no
   robustness matrix, no recalibration comparison.
4. **Including it would weaken, not strengthen, the primary claims.** The
   dissertation's careful statement is that four heterogeneous targets were
   evaluated under one controlled protocol. Adding a fifth dataset that was
   *not* evaluated under that protocol would blur exactly the distinction the
   study has been rigorous about.
5. **One result would need heavy qualification if promoted.** CQR reached 0.8169
   coverage against nominal 0.95 at 5 minutes. In an appendix that is an honest
   observation about a portability run; in Chapter 5 it would read as a fifth
   conformal-calibration result and invite comparison it cannot support.

## Prepared wording

### For the appendix opening

> An auxiliary experiment using the UCI Occupancy Detection dataset (Candanedo &
> Feldheim, 2016; UCI Machine Learning Repository dataset 357, DOI
> 10.24432/C5X01N, CC BY 4.0) was conducted as a pipeline-portability check. Its
> purpose was to establish whether the generic ConfoSense architecture — data
> loading, preprocessing, chronological partitioning, feature generation, point
> forecasting, conformal calibration, interval evaluation and reporting — could
> be applied to an independent public building-sensor dataset with only a small
> dataset-specific adapter.
>
> The experiment was **not** included in the primary cross-dataset benchmark.
> The dataset was originally designed for binary occupancy detection rather than
> continuous forecasting, and it differs from the four principal experimental
> settings in scope, intended use and temporal structure: it comprises a single
> office room recorded over sixteen days in three disjoint segments separated by
> recording gaps of seven and twenty-nine hours, and its own train/test division
> is not chronologically ordered. Its results are therefore reported as
> supplementary evidence about the implementation, and are excluded from the
> cross-dataset statistical comparison, the alerting benchmark and every
> conclusion drawn in Chapters 5 and 6.

### For the cross-reference in the main body (two sentences)

> The generic architecture was additionally exercised on an independent public
> dataset, the UCI Occupancy Detection recordings, as a portability check; the
> full pipeline executed without modification to any generic component
> (Appendix J). That check is supplementary evidence about the implementation
> and is not part of the four-dataset experimental comparison reported here.

### For the limitations section, if the examiner asks about generalisation

> Portability was demonstrated on one additional dataset. This establishes that
> the architecture is not specialised to the three datasets on which it was
> developed; it does not establish that the framework's findings generalise
> across building stock, which would require an experimental programme of the
> same scope as the primary study repeated on further datasets.

## What the appendix should contain

| Item | Source | Note |
|---|---|---|
| Dataset verification table (source, DOI, licence, checksums, structure) | `report/uci_auxiliary_results.md` §1 | including the two recording gaps and the filename/chronology mismatch |
| Configuration table | §2 | partitions, horizons, predictors, models |
| Point results (4 rows) | `metrics/point_metrics.csv` | with bootstrap CIs |
| Interval results (8 rows) | `metrics/interval_metrics.csv` | both nominal levels |
| Interval-violation diagnostic (2 rows) | `metrics/interval_violation_diagnostic.csv` | labelled *diagnostic*, never *alert reliability* |
| One figure | `figures/fig_uci_02_cqr_interval.png` | the interval figure is the more informative of the two |
| Limitations | `report/uci_auxiliary_limitations.md` | condensed to a short list |

Roughly three pages. The point-MAE bar chart
(`figures/fig_uci_01_point_mae.png`) can be omitted if space is tight — the
four-row table carries the same information.

## Terminology to hold to

| Use | Never use |
|---|---|
| "auxiliary pipeline-portability check" | "fifth dataset", "additional benchmark" |
| "interval-violation diagnostic" | "alert reliability", "anomaly detection performance" |
| "the pipeline executed without modification" | "the framework generalises" |
| "supplementary validation" | "external validation" *(implies confirmatory power this run does not have)* |
