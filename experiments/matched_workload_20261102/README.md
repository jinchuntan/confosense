# Matched-workload follow-up

This experiment tests whether conformal calibration offers useful building-alert
performance beyond simpler threshold choices. It is a new retrospective study,
not a reproduction or replacement of the manuscript's Table 6. The original
scientific source and accepted outputs are unchanged.

## Design

- The same ten BDG2 buildings named in the manuscript, with hourly electricity,
  origin-time air/dew temperature, historical consumption and calendar features.
- Three expanding chronological histories, each followed by a distinct 20% test
  period. Within each history, 75% is for fitting, 12.5% for calibration and 12.5%
  for threshold selection. One-hour target-to-origin embargoes separate roles.
- Five model seeds. Each unit fits the same 2.5%, median and 97.5% histogram
  gradient boosting models. No method receives a different predictor.
- Four interval choices: separate-tail CQR, symmetric maximum-score CQR,
  scaled raw quantile intervals, and a seasonal absolute-error threshold around
  the shared median forecast. The last is an explicitly specified simple
  baseline, **not a claimed reproduction of Takahashi et al.**
- For each method, choose the candidate closest to, but not above, 0.25, 0.5 or
  1 background episode per asset-day on the original selection stream. Reject
  candidates active for more than 20% of selection time. No injected event
  outcome is used in selection. No policy is retuned on test data.
- Report achieved test workload; it is not forced to equal the target or to
  match across methods. Compare the complete set of operating points rather
  than selecting whichever test result looks best.
- Keep the raw 95% quantile band and separate-tail 95% CQR as descriptive
  references. Their `budget=-1` label means **not budget-selected**.

Threshold grids and tie-breaking are fixed in `protocol.json` and `study.py`.
The seasonal scale uses calibration errors by building, target hour and
weekday/weekend, with a building-level fallback. Missing input values are filled
from the past for at most three hours. Remaining corrupted features stay missing;
HGB handles them without borrowing clean or future readings. Raw quantile
crossings are ordered. Empty calibrated sets are retained as empty rather than
turned into nonempty intervals by swapping endpoints.

## Fault replay and checks

Each test stream receives five deterministic catalogues of the original seven
sensor-disturbance families at three severities. Events last four readings, have
three additional hours of matching tolerance, and cannot cross support gaps or
building boundaries. Magnitudes use fitting-period building MAD scales. Model
features are rebuilt from corrupted histories, so later predictions respond to
the disturbed sensor readings. Fault times are independent of all predictions.

Numerical alerts and alerts that include missing-reading flags are scored
separately. Only a new episode onset can match an event. Original uninjected
streams are also scored against the same event windows (`clean_window`) to
measure coincidental matches. That is a negative control, not a causal correction
to recall. Misses contribute the full six-hour limit to restricted mean delay.

The symmetric CQR flags are independently checked against direct thresholding
of `max(raw_lower - observed, observed - raw_upper)`. At the same calibration
quantile these are the **same detector**, including empty prediction sets.
Such equality is not evidence of a new detection algorithm.

## Reproduce

The source BDG2 files are available from the authors' Git LFS media endpoints
listed in `protocol.json`. Place `electricity.csv`, `metadata.csv` and
`weather.csv` in a local directory. `results_v1/environment.json` records their
full SHA-256 checksums and the execution environment. Raw source datasets are
not republished in this experiment.

```sh
python -m pip install -r experiments/matched_workload_20261102/requirements.txt
python -m unittest discover -s experiments/matched_workload_20261102 -p test_study.py -v
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
python experiments/matched_workload_20261102/study.py \
  --raw /path/to/bdg2_files --out /path/to/fresh_results --workers 2
python experiments/matched_workload_20261102/summarize.py /path/to/fresh_results
```

Completed units resume only when source, protocol, input and output checksums
match. Use a fresh output directory after a scientific change. Saved models
are pickle-based joblib files: load only a trusted, checksum-verified copy.

## Evidence and interpretation

Each unit retains fitted models, calibration/selection/test predictions, the
selection surface, frozen chosen policies, event catalogues, packed emitted
alert flags and per-event outcomes. `summarize.py` independently reconstructs
episode starts and event matches from the packed flags and checks all hashes.

Building summaries pool catalogue outcomes, average seeds within a chronological
period, and then give the three periods equal weight. Aggregate tables give
each building equal weight. Missing strata remain explicitly reported through
`observed_strata`. Source event counts are retained in `stratum_counts.csv.gz`.
Paired intervals resample the six original sites after averaging repeated seeds
and periods. They condition on these buildings and fitted models, have few site
clusters, and are descriptive. They are not population guarantees or proof of
noninferiority. All budgets and methods are reported.

The cohort and historical test periods were already inspected in previous
studies. This is retrospective follow-up, not untouched confirmatory evidence.
Background episodes are a workload measure, not verified false alarms. Injected
sensor disturbances do not establish detection of maintenance-confirmed physical
equipment failures. Fewer episodes do not by themselves establish less operator
time, cost or alarm fatigue.
