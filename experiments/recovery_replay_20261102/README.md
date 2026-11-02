# When the meter recovers before the first alarm

**A building monitor can miss every altered reading and earn detection credit hours later because those readings changed its forecast.** This study measures how often that happens in a building-electricity benchmark and shows how the choice of scoring rule can change which detector appears best.

## A trace from the replication

At the Beatrice building on 6 December 2016, an injected bias raised the 06:00 and 07:00 readings from 6.25 to 12.18. Both stayed inside the forecast interval. The original meter readings resumed at 08:00. The first alarm arrived at 11:00, when the meter read 13.25. The lower forecast limit was 20.11. In a paired replay that restored the two earlier readings, that limit was 11.92. The same 13.25 reading was then inside the interval and generated no flag.

The benchmark credited the 11:00 alarm to the earlier bias. An operator looking for an ongoing sensor disturbance would have missed it. The alarm could still be useful for retrospective review. This illustration is the first qualifying non-missing example in building and time order in the first replication catalogue. [Eight hourly observations and both forecast intervals](results/example.csv)

## How often did that happen?

The primary detector used separate-tail conformalized quantile regression (CQR), numerical alarms, and a threshold selected against a budget of 0.5 background alarm episodes per meter-day. The published selection rule used only original observations. The event scorer accepted a new alarm episode from the beginning of a four-hour slot through three hours after the slot. We identified the last **actually altered** reading in each event.

For each credited first alarm after that reading, we restored only the current event's observations and replayed the forecast using the full preceding history. The model, threshold, weather, earlier disturbances and current target value were identical. We counted a hit only when the alarm flag itself disappeared at that hour. A timing match alone or an episode boundary shifting while the flag persisted was insufficient.

| Numerical alarm outcome | Original 10 buildings, 6 sites | Another 10 buildings, 10 different sites |
|---|---:|---:|
| Effective injected events | 9,825 | 9,337 |
| Events credited with a hit | 4,678 | 4,556 |
| First alarm after last altered reading | 1,232 | 886 |
| Of those, flag disappeared when this event's history was restored | 909 | 521 |
| **History-attributable first alarms / credited hits** | **19.4%** | **11.4%** |
| Same count / all effective events | 9.3% | 5.6% |
| Equal-site mean of the share among hits | 19.6% | 11.4% |
| Sites with a positive count | 6 of 6 | 10 of 10 |
| Strict cases that also occurred after the whole nominal slot | 683 | 362 |
| Strict cases with no other credited-window onset in the restored replay | 780 | 414 |

The share varied from 11.9% to 28.8% across the original sites and 6.5% to 16.1% across the additional sites. Among hits for the five disturbance families that leave a numerical reading, the shares were 11.1% and 7.9%. Among hits for injected missing readings they were 70.2% and 45.5%. Adding a direct missing-reading flag to the numerical detector reduced the overall shares to 6.7% and 4.9%. That is a different alarm policy with its own hit denominator. [Primary counts](results/primary.csv) · [Disturbance-family sensitivity](results/primary_families.csv) · [All operating points](results/operating_points.csv)

## The scoring rule changed the detector ranking

For the additional ten sites, the seasonal residual detector ranked first of four on the existing event score, and last when the first matched alarm had to fall between the first and last altered readings. The scaled-quantile detector led on that second measure. This is an exploratory comparison at the primary selection budget. The original cohort's scaled-quantile detector led on both measures.

| Detector on the additional sites | Credited hits / events | First hit during disturbance span / events | Actual test background episodes per meter-day |
|---|---:|---:|---:|
| Seasonal residual | 56.0% | 36.6% | 0.536 |
| Scaled quantile | 48.9% | 38.9% | 0.509 |
| Separate-tail CQR | 48.8% | 37.7% | 0.515 |
| Symmetric CQR | 48.4% | 37.6% | 0.527 |

Each percentage divides by the same 9,337 effective events. The second column of percentages is a timing measure. It does not attribute every within-span hit to the disturbance. The ranking comparison combines multiple timing effects. The paired replay isolates the contribution of past corrupted readings to individual post-recovery flags. [Counts and achieved workload for every method, budget and cohort](results/policy_comparison.csv)

## Contribution and limits

The proposed contribution is a reproducible way to quantify how much building-monitoring detection credit comes from the effect of earlier corrupted readings on later forecasts. The original target at the credited hour is known because the disturbances were injected. This makes a same-hour, same-reading comparison possible.

Forecast echoes were described in a 2015 patent application. PATE grades early and late detections by temporal proximity. Recent work also evaluates anomaly episodes with repair-based counterfactual explanations. These are relevant precedents for the mechanism, timing metrics and intervention. Our candidate contribution is the specific measurement of **first credited alarms after recovery attributable to the detector's input history**, its size across buildings, and its bearing on detector comparisons. The literature search supports a scoped contribution claim. Priority for this exact endpoint remains open. [Thibaux, US20150339265A1](https://patents.google.com/patent/US20150339265A1) · [Ghorbani et al., PATE, KDD 2024](https://doi.org/10.1145/3637528.3671971) · [Event-level evaluation and counterfactual explanation, 2026](https://doi.org/10.3390/app16115450)

Both cohorts used BDG2 electricity and the same synthetic injector, three chronological test periods and five placement schedules. Each cohort fitted its own shared histogram gradient boosting forecaster on earlier data, using seed 42. The ten replication sites were chosen from early readings before model fitting. The endpoint and a 10% threshold for pursuing the question were fixed locally before inspecting these replay outcomes. Both cohorts met that editorial threshold. The counts describe repeated benchmark events, and the site range shows heterogeneity. An original reading establishes that the injected corruption ended. The health of the equipment and the cost of a delayed operator response were unobserved. This experiment is separate from the manuscript's original Table 6. [Design](DESIGN.md) · [Replication membership](results/replication_membership.json)

## Checklist for the journal revision

- [x] **Code and evidence.** Freeze the endpoint and selection rule, reproduce the archived alarms, restore one event at a time, and test on sites outside the original cohort.
- [x] **Report.** Show an hourly trace, the share among credited hits and among all events, the missing-reading sensitivity, and the ranking under both timing rules.
- [ ] **Code.** Repeat the paired replay with the manuscript's XGBoost forecaster. Compare with a weather-and-calendar-only forecaster under the same budget. Its post-recovery numerical flag should be identical between replays when it has no meter history or adaptive threshold.
- [ ] **Independent evidence.** Select a second building dataset with documented fault clearance. Verify that it contains post-clear observations and an appropriate undisturbed reference before using it for attribution. Separate physical settling from a change in the model's forecast. Berkeley Lab's controlled HVAC series are a candidate. [Dataset descriptions](https://faultdetection.lbl.gov/data/)
- [ ] **Manuscript.** Lead with the decision the monitor supports, show active-disturbance detection alongside retrospective logging, and state whether detector rankings survive the second forecaster and dataset. An online mitigation claim would additionally need a deployable history-update rule and a comparison at comparable achieved alarm workload.

## Reproduction

From the repository root, install the parent experiment's pinned dependencies. Set `BDG2_RAW` to the directory containing the original electricity, metadata and weather CSVs, and `REPLAY_WORK` to a fresh output directory. A fresh run rebuilds the original models and the new cohort. The archived run receipts include timings and compressed-file hashes that may differ across rebuilds. Compare the numerical outputs after each fresh run verifies its own receipts.

```sh
PILOT=experiments/matched_workload_20261102
REPLAY=experiments/recovery_replay_20261102
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
mkdir -p "$REPLAY_WORK/tables"
python "$PILOT/study.py" --raw "$BDG2_RAW" --out "$REPLAY_WORK/pilot" --workers 2
python "$REPLAY/replicate.py" "$BDG2_RAW" "$REPLAY_WORK/replication"
python "$REPLAY/replay.py" "$BDG2_RAW" "$PILOT" "$REPLAY_WORK/pilot" pilot "$REPLAY_WORK/pilot.csv"
python "$REPLAY/replay.py" "$BDG2_RAW" "$REPLAY_WORK/replication" "$REPLAY_WORK/replication/runs" replication "$REPLAY_WORK/replication.csv" --example "$REPLAY_WORK/tables/example.csv"
python "$REPLAY/summarize.py" "$REPLAY_WORK/pilot.csv" "$REPLAY_WORK/replication.csv" "$REPLAY_WORK/tables"
python "$REPLAY/validate.py" "$REPLAY_WORK/pilot.csv" "$REPLAY_WORK/pilot" "$REPLAY_WORK/replication.csv" "$REPLAY_WORK/replication/runs" "$REPLAY_WORK/tables"
python -m unittest discover -s "$REPLAY" -p 'test_*.py'
```

The replay verified the factual flags around every effective event against the packed alarm streams. A separate check reconciled the hit counts against the archived scorer over 146,328 strata covering 459,888 event, policy and channel records. The checked output tables cover all three selection budgets, four detectors, two channels, all sites, periods, and disturbance types and severities. [Validation receipt](results/validation.json)
