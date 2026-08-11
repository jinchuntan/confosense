# Alert-rule selection audit

## What was wrong

In the original full study the calibration intervals used to score
candidate k-of-m rules came from the CQR model conformalized on **that
same calibration partition**. The conformal quantile is fitted to cover
those residuals, so their violation rate is not an out-of-sample
quantity, and any rule chosen against it inherits that optimism.

## What was changed

The calibration partition is now split chronologically inside itself
(`src/alert_study.py::chronological_subsplit`):

```
train                      -> quantile regressors
calibration, earlier 60%   -> conformal calibration of the selection model
calibration, later 40%     -> alert-rule scoring and selection
test                       -> final evaluation only
```

A window joins the later block only when its forecast **origin** is
strictly after the last **target** time of the earlier block, so every
rule-tuning timestamp postdates every conformal-calibration timestamp.
Windows straddling the boundary are dropped; that is the embargo, and it
is exact rather than an approximate h-step guess. The split is
chronological, never shuffled.

Once a rule is frozen it is not revisited. Final test intervals are still
built by the model conformalized on the **complete** calibration
partition: that model is fitted before any test observation is seen and
the rule is already fixed by then, so using the full calibration sample
for the reported intervals costs nothing in validity and wastes no data.
The consequence to keep in mind is that the frozen rule was chosen
against a slightly narrower conformal sample (60% of calibration) than
the one that produces the reported test intervals (100%).

No test observation enters selection at any point; the split, the
sample sizes and the boundary times are persisted per dataset in
`<dataset>/metrics/alert_selection_split.csv`.

## Result per dataset

| dataset | old_rule | new_rule | changed | n_conformal | n_rule_block | n_embargoed | boundary_time |
|---|---|---|---|---|---|---|---|
| pleia | 3-of-5 | 4-of-7 | True | 6065 | 4043 | 1 | 2021-09-10 17:10:00 |
| pleia_energy | 2-of-3 | 2-of-3 | False | 6065 | 4043 | 1 | 2021-09-10 17:20:00 |
| rico | 4-of-7 | 2-of-3 | True | 5437 | 3619 | 5 | 2024-05-08 13:32:00 |
| bdg2 | 1-of-1 | 1-of-1 | False | 20999 | 13978 | 10 | 2017-06-10 12:00:00 |

### pleia

* selection block: 6065 conformal windows, 4043 rule-scoring windows, 1 embargoed at the boundary 2021-09-10 17:10:00
* old rule **3-of-5** -> new rule **4-of-7** (CHANGED)

Calibration surface, pooled (old) vs nested (new):

| rule | far_pooled | far_nested | false_alert_events_per_day_pooled | false_alert_events_per_day_nested | recall_pooled | recall_nested |
|---|---|---|---|---|---|---|
| 1-of-1 | 0.0495 | 0.1102 | 4.5868 | 7.4084 | 1.0000 | 0.9524 |
| 2-of-3 | 0.0268 | 0.0784 | 1.4245 | 3.1343 | 0.9048 | 0.8810 |
| 3-of-5 | 0.0131 | 0.0508 | 0.5128 | 1.6384 | 0.8810 | 0.8571 |
| 4-of-7 | 0.0076 | 0.0351 | 0.2422 | 0.8904 | 0.8810 | 0.8333 |

Test metrics for the old and the new rule (the test surface itself is unchanged; only which row is frozen has moved):

| rule (old, then new) | precision | recall | f1 | far | false_alert_events_per_day | median_detection_delay_min |
|---|---|---|---|---|---|---|
| 3-of-5 | 0.3505 | 0.8095 | 0.4892 | 0.0251 | 0.8975 | 20.0000 |
| 4-of-7 | 0.5763 | 0.8095 | 0.6733 | 0.0132 | 0.3562 | 30.0000 |

### pleia_energy

* selection block: 6065 conformal windows, 4043 rule-scoring windows, 1 embargoed at the boundary 2021-09-10 17:20:00
* old rule **2-of-3** -> new rule **2-of-3** (unchanged)

Calibration surface, pooled (old) vs nested (new):

| rule | far_pooled | far_nested | false_alert_events_per_day_pooled | false_alert_events_per_day_nested | recall_pooled | recall_nested |
|---|---|---|---|---|---|---|
| 1-of-1 | 0.0493 | 0.0479 | 5.3275 | 4.4878 | 0.8571 | 0.7857 |
| 2-of-3 | 0.0177 | 0.0148 | 0.9259 | 0.7836 | 0.5000 | 0.6190 |
| 3-of-5 | 0.0098 | 0.0059 | 0.3704 | 0.2493 | 0.4286 | 0.5238 |
| 4-of-7 | 0.0063 | 0.0016 | 0.1994 | 0.0712 | 0.4286 | 0.5238 |

### rico

* selection block: 5437 conformal windows, 3619 rule-scoring windows, 5 embargoed at the boundary 2024-05-08 13:32:00
* old rule **4-of-7** -> new rule **2-of-3** (CHANGED)

Calibration surface, pooled (old) vs nested (new):

| rule | far_pooled | far_nested | false_alert_events_per_day_pooled | false_alert_events_per_day_nested | recall_pooled | recall_nested |
|---|---|---|---|---|---|---|
| 1-of-1 | 0.0484 | 0.0171 | 20.0243 | 4.3769 | 0.9250 | 0.8571 |
| 2-of-3 | 0.0449 | 0.0175 | 11.2835 | 3.1832 | 0.8500 | 0.7714 |
| 3-of-5 | 0.0406 | 0.0175 | 8.2640 | 3.1832 | 0.8500 | 0.7714 |
| 4-of-7 | 0.0379 | 0.0167 | 6.3569 | 3.1832 | 0.8500 | 0.7714 |

Test metrics for the old and the new rule (the test surface itself is unchanged; only which row is frozen has moved):

| rule (old, then new) | precision | recall | f1 | far | false_alert_events_per_day | median_detection_delay_min |
|---|---|---|---|---|---|---|
| 4-of-7 | 0.3846 | 0.8750 | 0.5344 | 0.2050 | 8.6878 | 3.0000 |
| 2-of-3 | 0.3125 | 0.8750 | 0.4605 | 0.2077 | 11.9457 | 1.0000 |

### bdg2

* selection block: 20999 conformal windows, 13978 rule-scoring windows, 10 embargoed at the boundary 2017-06-10 12:00:00
* old rule **1-of-1** -> new rule **1-of-1** (unchanged)

Calibration surface, pooled (old) vs nested (new):

| rule | far_pooled | far_nested | false_alert_events_per_day_pooled | false_alert_events_per_day_nested | recall_pooled | recall_nested |
|---|---|---|---|---|---|---|
| 1-of-1 | 0.0500 | 0.0625 | 0.8190 | 0.9667 | 0.8810 | 0.9286 |
| 2-of-3 | 0.0277 | 0.0375 | 0.2538 | 0.3400 | 0.8095 | 0.8571 |
| 3-of-5 | 0.0151 | 0.0228 | 0.1111 | 0.1717 | 0.8095 | 0.8571 |
| 4-of-7 | 0.0110 | 0.0180 | 0.0686 | 0.1202 | 0.8095 | 0.8333 |

