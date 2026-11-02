# A stuck building sensor can look predictable to the monitor that should catch it

Changing where we injected exactly the same meter faults changed whether ConfoSense appeared to detect them. A benchmark that computes forecasts on the original meter history credited 343 timely stuck-meter detections across two BDG2 cohorts. When faulty readings entered subsequent forecasts, only 23 of those same 343 detections survived. One other event gained a timely detection, giving 24 in total. Both runs used identical target readings, thresholds, event placements, scoring rules and background workload. This is an empirical result about how to evaluate forecasting-based monitors.

## What the overall score concealed

| BDG2 outcome, primary numerical CQR detector | Original 10 buildings, 6 sites | Another 10 buildings at 10 different sites |
|---|---:|---:|
| All effective injected disturbances | 9,825 | 9,337 |
| Overall credited recall with forecasts computed before injection | 45.1% | 49.4% |
| Overall credited recall with readings fed back into forecasts | 47.6% | 48.8% |
| Individual hit/miss decisions that changed | 1,175 (12.0%) | 855 (9.2%) |
| Effective stuck-meter disturbances | 1,527 | 1,505 |
| First alarm during the stuck interval, forecasts computed before injection | 159 (10.4%) | 184 (12.2%) |
| First alarm during the stuck interval, readings fed back into forecasts | 6 (0.4%) | 18 (1.2%) |
| Fixed-forecast timely stuck hits that lost that credit under feedback | 154 of 159 (96.9%) | 166 of 184 (90.2%) |
| Of those lost, first alarm came after the disturbance ended | 79 | 62 |
| Of those lost, no alarm matched in the full scoring window | 75 | 104 |

Timely detection decreased at all 16 sites for the primary detector. Each of the four interval policies showed lower timely stuck detection under feedback in both cohorts. The size differed by policy. Under the historical event-credit rule the seasonal residual detector also moved from fourth to first on the ten additional sites when feedback was enabled. That ranking reversal did not occur in the original cohort. The fixed-versus-feedback comparison changes the information available to the forecast, with no change in when a hit can earn credit. The earlier [recovery analysis](../recovery_replay_20261102/README.md) instead changed the scoring question and isolated the contribution of one specific event to a post-recovery alarm.

In a stuck event the meter repeats an earlier value. A predictor that relies heavily on that meter can move its interval toward the repeated value while the fault is active. When the value starts moving again, it may leave the interval. Restoring the original meter history is an offline comparison with privileged data. The placement experiment allows earlier events to affect the feedback forecasts. It measures the change caused by the treatment of the whole disturbed test stream. See [event transitions by family](results/primary_transitions.csv) and [all four methods and three budgets](results/operating_points.csv).

## Which alarm would actually help?

All deployable variants used observations available by the prediction time. Each used the same 0.5-episode-per-meter-day selection ceiling and 20% selection-time-in-alert cap. The simple specialist counts consecutive identical readings and selects the run length on original data. The four-sample delay excludes the most recent four meter observations from the quantile forecaster but retains calendar, seasonal and weather inputs. Thresholds were fixed before the corresponding test replay.

| Alarm rule | Original cohort, timely stuck hits / 1,527 | Additional cohort, timely stuck hits / 1,505 | Actual background episodes/meter-day, original / additional |
|---|---:|---:|---:|
| Live separate-tail CQR | 6 (0.4%) | 18 (1.2%) | 0.488 / 0.515 |
| CQR with four-hour delayed meter inputs | 115 (7.5%) | 144 (9.6%) | 0.491 / 0.550 |
| Consecutive identical readings | 1,022 (66.9%) | 1,456 (96.7%) | 0.223 / 0.453 |

The specialist performed best for stuck meters and had fewer background episodes in both cohorts. Across all seven disturbance families its first-alarm-during-span counts were only 1,977 and 2,668, versus 3,324 and 3,517 for live CQR. Delaying the forecast inputs improved all-family timely counts to 3,543 and 3,637. The simpler live scaled-quantile policy reached 3,710 and 3,628. The relative importance of sensor supervision and forecast monitoring depends on the fault of interest. A combined detector would need evaluation under its own shared workload ceiling. [Counts for all families and arms](results/practical_controls.csv)

## Independent temperature stream

We ran targeted checks on 9,907 distinct ten-minute PLEIAData temperature observations from a single archived stream. This uses a different forecasting backbone, ridge autoregression with calibrated error bands. We trained and selected its threshold chronologically within that stream. Over the final 1,982 test observations, five schedules produced 148 effective freezes lasting two, four or eight samples. This is a separate building data source with injected sensor faults. Source readings, injection duration and forecast model all differ from BDG2.

| Rule | First alarm during the freeze / 148 | Background episodes on the original test stream |
|---|---:|---:|
| Ridge, forecasts computed before injection | 8 | 6 |
| Same ridge detector with feedback | 0 | 6 |
| Ridge with four-sample delayed inputs and feedback | 0 | 6 |
| Consecutive identical readings | 54 | 0 |

Of the eight offline timely hits, six moved after recovery and two became misses under feedback. The repeated-value check caught 0/48 two-sample freezes, 4/50 four-sample freezes and 50/50 eight-sample freezes. Its selected threshold required six unchanged transitions. A run already under way can contribute to an alarm. Zero background episodes describes approximately 13.8 days of test support in this stream. The four-sample delayed forecaster's BDG2 improvement did not transfer here. [Paired event outcomes](results/pleia_paired.csv) · [Counts by duration and rule](results/pleia_transitions.csv) · [External workloads](results/pleia_policies.csv)

## How to position the article

| Closest prior work | What it already establishes | What this experiment adds |
|---|---|---|
| Stjelja et al., *Building consumption anomaly detection* (2024) | Conformal intervals and an alarm matrix for building consumption | Holding the monitoring policy fixed, quantify what changes when the faulty meter participates in subsequent predictions. [Paper](https://www.sciencedirect.com/science/article/pii/S0378778824003657) |
| *Explainable Smart-Building Energy Consumption Forecasting and Anomaly Diagnosis* (2026), §3.4 | BDG2 synthetic faults and event-level scoring against model forecasts | An explicit paired comparison of both injection paths under the same event scoring. We did not reproduce that paper's model or figures. [Methods](https://doi.org/10.3390/app16083836) |
| Lowe, Fung and Bauer (2026), *On the Application of Time-Series Foundation Models for Detecting Long-Context Anomalies in Industrial Control Systems* | Industrial forecasters can absorb sustained faults, and replacing suspect inputs with predictions can improve detection | Count which identical building-sensor events lose timely credit, where that credit moves, and which simple alarm actually helps at a measured workload. [Workshop paper](https://clementfung.github.io/gallery/papers/fmsd26-tsfm.pdf) |
| *Minute-Level Dataset from a Naturally Ventilated Building for Benchmarking and Learning-Based Modeling* (2026) | Repetition filters for building data quality | Quantify their operating trade-offs against a conformal forecasting detector on the same measurement faults. [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC13680368/) |

A defensible lead is that overall event recall can conceal an almost complete loss of timely stuck-sensor detection when an evaluation restores the operational feedback path. The useful engineering output is a paired replay protocol, a fault-specific performance table, and a workload-measured comparison against a simple sensor rule. The method for counting repeated readings and the general observation that forecasts adapt to faults both have prior art. The paper should make a scoped empirical contribution claim.

## Submission checklist

- [x] Compare the same events and alert policies with and without meter feedback. Report both individual switches and changes in aggregate recall.
- [x] Separate first alarms during the disturbance from alarms that start after it, and verify the previously reported live margins.
- [x] Include a deployable specialist rule, its achieved workload and its short-duration limitations. Report the delayed-input control even where it fails.
- [x] Repeat the stuck-sensor comparison on a separate temperature stream with a different forecaster.
- [ ] Verify the submission-bound XGBoost implementation and audit the original manuscript's event-injection path before reusing its headline numbers.
- [ ] Validate against naturally occurring, independently documented freezes and legitimate steady readings. Seek a device heartbeat, a redundant instrument, or a fault ticket with start and clearance times. Ground truth determined by the repeated-value rule itself would make this comparison circular.
- [ ] Rewrite the abstract, first figure and discussion around the paired experiment. Present general interval coverage and the earlier recovery result as supporting analyses. Report the fault mixture, prospective alarm budget, achieved workload and operational limitations.

## Reproduction and scope

The primary protocol was specified before inspecting detached-forecast or delayed-input results. The stuck-family focus, specialist control and external follow-up were prompted by the first BDG2 results and were specified before inspecting those control outcomes. The two BDG2 cohorts share one source and generator. Repeated placements are not independent equipment incidents. PLEIAData supplies one external stream with a related generator. The counts describe these tests. Naturally occurring faults require independent corroboration. [Initial design](DESIGN.md) · [Subsequent controls](CONTROLS.md)

From the repository root, use the parent experiment's pinned Python packages. Recreate the original BDG2 models and the site-disjoint run using the [parent reproduction instructions](../recovery_replay_20261102/README.md#reproduction). Set BDG2_RAW and REPLAY_WORK to those same locations, then run the following.

```sh
E=experiments/injection_feedback_20261102
OUT="$REPLAY_WORK/injection_comparison"
mkdir -p "$OUT"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
for cohort in pilot replication; do
  if [ "$cohort" = pilot ]; then
    runner=experiments/matched_workload_20261102
    runs="$REPLAY_WORK/pilot"
  else
    runner="$REPLAY_WORK/replication"
    runs="$runner/runs"
  fi
  for fold in 0 1 2; do
    for arm in placement delay; do
      python "$E/compare.py" "$BDG2_RAW" "$runner" "$runs" "$OUT" "$cohort" "$fold" "$arm"
    done
    python "$E/controls.py" bdg "$BDG2_RAW" "$runner" "$runs" "$OUT" "$cohort" "$fold"
  done
done
SOURCE=smart_building_conformal/outputs/matched_forecasting005/pleia_h1_f2_s42_v1/units/pleia_h1_f2_s42_persistence/predictions.csv.gz
git show "2db2ac6:$SOURCE" > "$OUT/pleia_source.csv.gz"
python "$E/controls.py" pleia "$OUT/pleia_source.csv.gz" "$OUT"
python "$E/summarize.py" "$OUT" "$OUT/tables"
python -m unittest discover -s "$E" -p 'test_*.py'
```

The checks validate the original data files, code, protocols, run receipts, split identities, injector catalogues, and clean-stream episode counts. Every set of published event, credited-hit and timely-hit totals for the live policy is reconciled across 48 operating points, 384 method/site combinations, and 1,008 disturbance/severity operating points against the earlier archived results. PLEIAData was created by Antonio Martínez Ibarra, Aurora González-Vidal and Antonio Skarmeta Gómez, and is licensed under CC BY 4.0. Here archived temperature targets were deduplicated, chronologically partitioned, and modified only for the synthetic experiments. The source authors do not endorse the analysis. [PLEIAData attribution](../../review/DATA_NOTICE.md) · [BDG2 attribution](../../review/bdg2_operational_pilot_20260913/DATA_NOTICE.md)
