# Final claims register

Every claim the dissertation may make, with its evidence and its strength.
Strength is assigned as:

* **Strongly supported** — holds on all four targets, or is a direct measurement
  with no competing reading.
* **Supported with caveat** — holds, but only under a stated condition that must
  travel with the claim.
* **Exploratory** — observed and worth reporting, but resting on a single target,
  a single comparison, or a mechanism the study did not isolate.

All numbers come from the frozen outputs under `outputs/full_study/`.

---

## Part 1 — Claims supported by the evidence

### C1. Conformal calibration is necessary
**Claim.** An uncalibrated quantile band fails to deliver its nominal coverage on
every target studied, while conformal calibration substantially closes the gap.
**Evidence.** `combined/interval_metrics.csv` — `quantile_uncalibrated` coverage
deviation at nominal 0.95: 0.0705 (PLEIA temp), 0.1016 (PLEIA energy), 0.1110
(BDG2), 0.3196 (RICO).
**Table/figure.** T5.5, F5.2. **RQ/RO.** RQ2 / RO2.
**Strength.** **Strongly supported** — four of four targets, both nominal levels.

### C2. No conformal method transfers across datasets
**Claim.** The best-calibrated interval method is dataset-dependent.
**Evidence.** `combined/interval_metrics.csv` — best-calibrated arm: `cqr` on
PLEIA temperature (0.9417); `recentred_enbpi_updated` on PLEIA energy (0.9511),
RICO (0.9036), BDG2 (0.9503).
**Table/figure.** T5.5, T5.16. **RQ/RO.** RQ2 / RO2.
**Strength.** **Strongly supported**.

### C3. RICO is not solved by any method evaluated
**Claim.** No interval method reached nominal coverage on the RICO HVAC target.
**Evidence.** `combined/interval_metrics.csv` — best single (method, horizon)
cell 0.9293; best arm averaged over horizons 0.9036; nominal 0.95.
**Table/figure.** T5.5, F5.3. **RQ/RO.** RQ2 / RO2.
**Strength.** **Strongly supported** — this is a negative finding and must be
reported as such.

### C4. CQR substantially undercovered on RICO under the evaluated protocol
**Claim.** CQR attained 0.7719 coverage against nominal 0.95 on RICO, with 3,912
of 66,696 intervals crossing before order-repair across both nominal levels
(2,558 at 0.95), concentrated in 16 of 42 test runs.
**Evidence.** `combined/interval_metrics.csv`,
`combined/rico_quantile_crossings.csv`, `rico_quantile_crossings_by_run.csv`,
`report/rico_quantile_crossing_audit.md`.
**Table/figure.** T5.5, TA.4, TA.5. **RQ/RO.** RQ2 / RO2.
**Strength.** **Supported with caveat** — the caveat is that the *cause* is
untested; use the wording above verbatim and do not attribute it to run
structure.

### C5. The best point forecaster is target-dependent
**Claim.** XGBoost won 9 of 13 dataset/horizon cells and persistence won 4,
including every PLEIA indoor-temperature horizon.
**Evidence.** `combined/point_metrics.csv`.
**Table/figure.** T5.3, F5.1. **RQ/RO.** RQ1 / RO1.
**Strength.** **Strongly supported**.

### C6. Naive persistence is a serious competitor on slow indoor temperature
**Claim.** On PLEIAData indoor temperature, XGBoost was 69.19 % worse than
persistence in MAE at h=1 and persistence won at all three horizons.
**Evidence.** `combined/effect_sizes.csv`, `combined/point_metrics.csv`.
**Table/figure.** T5.3, TA.3. **RQ/RO.** RQ1 / RO1.
**Strength.** **Supported with caveat** — one room, one block; no cross-room
generalisation is claimed.

### C7. The learned-model advantage grows with horizon
**Claim.** XGBoost's MAE improvement over persistence rose from +23.66 % at 5 min
to +48.77 % at 60 min on RICO, and crossed from −12.86 % at 1 h to +48.00 % at
6 h on BDG2.
**Evidence.** `combined/effect_sizes.csv`.
**Table/figure.** TA.3. **RQ/RO.** RQ1 / RO1.
**Strength.** **Supported with caveat** — consistent on two of four targets;
PLEIA temperature shows the opposite sign at every horizon.

### C8. Statistical significance and practical improvement diverge
**Claim.** The Friedman test rejected equality of the four point models
(χ² = 14.0667, p = 0.002816, 9 blocks), but after Holm correction only
seasonal naive versus XGBoost was significant (p = 0.0234); XGBoost versus
persistence gave p = 1.0000. Per-cell Diebold–Mariano found XGBoost significantly
better than persistence in 10 of 13 cells.
**Evidence.** `combined/ranking_tests.csv`, `combined/posthoc_comparisons.csv`,
`combined/statistical_tests.csv`.
**Table/figure.** T5.13, T5.14, T5.15. **RQ/RO.** RQ1 / RO1.
**Strength.** **Strongly supported** — the two tests answer different questions
and both must be reported.

### C9. Alert operating points must be tuned per target
**Claim.** The rule frozen by the selection procedure differed on all four
targets (4-of-7, 2-of-3, 2-of-3, 1-of-1), with test F1 spanning 0.0490 to 0.6733.
**Evidence.** `combined/alert_metrics.csv`.
**Table/figure.** T5.8, F5.5. **RQ/RO.** RQ3 / RO3.
**Strength.** **Strongly supported**.

### C10. Reusing the conformal calibration sample for rule selection is optimistic
**Claim.** Scoring alert rules on the sample that conformalized the interval
model understated the false-alert workload: on PLEIA the calibration FAR for
3-of-5 was 0.0131 under the pooled procedure against 0.0508 under a leakage-safe
nested split. Correcting the procedure changed the frozen rule on 2 of 4 targets.
**Evidence.** `report/alert_selection_audit.md`,
`<dataset>/metrics/alert_selection_split.csv`,
`<dataset>/metrics/alert_rule_selection_calibration.csv`.
**Table/figure.** T5.7. **RQ/RO.** RQ3 / RO3; methodological contribution.
**Strength.** **Supported with caveat** — the size and even the *direction* of
the optimism varied by dataset, because the two calibration blocks cover
different time periods with different dynamics.

### C11. A leakage-safe selection procedure does not guarantee a better test score
**Claim.** Adopting the nested split improved the PLEIA test operating point
(F1 0.6733 versus 0.4892 for the superseded rule) but worsened RICO's (0.4605
versus 0.5344).
**Evidence.** `report/alert_selection_audit.md`, `combined/alert_metrics.csv`.
**Table/figure.** T5.8. **RQ/RO.** RQ3 / RO3.
**Strength.** **Strongly supported** — a direct comparison of two frozen rules on
the same unchanged test surface.

### C12. The false-alert budget was unattainable on RICO
**Claim.** No candidate rule met the 1 false alert/day budget on RICO; the
quietest was selected and produced 11.9457 false alerts/day on test.
**Evidence.** `combined/alert_metrics.csv`,
`rico/metrics/alert_rule_selection_calibration.csv`.
**Table/figure.** T5.8, F5.6. **RQ/RO.** RQ3 / RO3.
**Strength.** **Strongly supported**.

### C13. Closed-loop evaluation changes the robustness conclusion
**Claim.** Under a 2 σ sensor bias, the fixed-interval protocol reported
observed-signal coverage of 0.0000–0.0749 and an alert rate of 0.9279–0.9999,
while in closed loop observed-signal coverage reached 0.9763 (PLEIA energy) and
0.8876 (BDG2) with clean-reference coverage falling to 0.1804 and 0.0529, and the
alert rate falling on every dataset.
**Evidence.** `combined/robustness_metrics.csv`,
`report/closed_loop_terminology.md`.
**Table/figure.** T5.9, T5.11, F5.7, F5.8. **RQ/RO.** RQ3 / RO3.
**Strength.** **Strongly supported** — the disturbance is manipulated, so a
causal statement about the injected bias is legitimate.

### C14. Closed-loop absorption is a gradient, not a uniform effect
**Claim.** At 2 σ, observed-signal coverage in closed loop ranged from 0.9763
(PLEIA energy) to 0.2580 (PLEIA temperature), where the alert rate remained
0.7315.
**Evidence.** `combined/robustness_metrics.csv`.
**Table/figure.** T5.11, F5.8. **RQ/RO.** RQ3 / RO3.
**Strength.** **Strongly supported**.

### C15. Calibration contamination is the most damaging disturbance studied
**Claim.** 10 % contamination of the calibration partition inflated PLEIA mean
interval width from 1.8526 (at 1 %) to 26.8179 and drove coverage to 1.0000; BDG2
width reached 1,468.7591.
**Evidence.** `combined/robustness_metrics.csv`.
**Table/figure.** T5.10. **RQ/RO.** RQ3 / RO3.
**Strength.** **Strongly supported** — monotonic on all four targets. Note that
coverage of 1.0000 is a failure mode, not a success.

### C16. Adaptive recalibration improves coverage on every target
**Claim.** Periodic or rolling recalibration reduced coverage deviation relative
to static on all four targets; the largest gain was PLEIA temperature
(0.0176 → 0.0020 under rolling).
**Evidence.** `combined/recalibration_metrics.csv`.
**Table/figure.** T5.12, F5.9. **RQ/RO.** RQ3 / RO3.
**Strength.** **Strongly supported**.

### C17. Recalibration does not rescue BDG2, and BDG2 has no distinct rolling result
**Claim.** BDG2 coverage improved only from 0.8432 to 0.8592 against nominal 0.95,
and the calibration replay selected an unwindowed configuration, so the rolling
row reproduces periodic exactly (`strategy_is_distinct = False`).
**Evidence.** `combined/recalibration_metrics.csv`.
**Table/figure.** T5.12. **RQ/RO.** RQ3 / RO3.
**Strength.** **Strongly supported**.

### C18. Coverage and Winkler can disagree, so both must be reported
**Claim.** On BDG2 the uncalibrated baseline attained the lowest Winkler score
(200.2032 versus CQR 200.2521) while covering 0.8390 against nominal 0.95,
because it is narrower.
**Evidence.** `combined/interval_metrics.csv`.
**Table/figure.** T5.5, F5.4. **RQ/RO.** RQ2 / RO2.
**Strength.** **Supported with caveat** — the two Winkler values differ by 0.02 %,
so this is a warning about single-metric reporting, not a ranking result.

### C19. The PLEIA energy RMSE reflects a data artefact, not load volatility
**Claim.** Two meter-stall catch-up observations follow 556 and 385 consecutive
zero-increment steps in a monotonically non-decreasing cumulative meter; the one
in the test partition inflates XGBoost RMSE from 0.1550 to 2.4510.
**Evidence.** `report/pleia_energy_audit.md`,
`combined/pleia_energy_meter_stalls.csv`,
`combined/pleia_energy_artefact_sensitivity.csv`.
**Table/figure.** TA.6, TA.7. **RQ/RO.** RQ1 / RO1; data-quality finding.
**Strength.** **Strongly supported** — diagnosed from the dataset's own
cumulative column. The observation was retained, not removed.

### C20. The study is reproducible from its recorded configuration
**Claim.** The full study executed non-fast with zero failed stages; point,
interval, bootstrap, Diebold–Mariano and effect-size tables were verified
bit-identical on re-execution; provenance, seeds, thread configuration and
package versions are recorded; 170 automated tests pass.
**Evidence.** `manifests/run_history.jsonl`, `manifests/stage_provenance.json`,
`manifests/dataset_sources.json`, `manifests/experiment_manifest.json`.
**Table/figure.** TA.9, TA.10. **RQ/RO.** all; methodology.
**Strength.** **Supported with caveat** — verified same-machine; cross-machine
reproducibility of the neural arm is not established.

### C21. No published result in the reviewed set is directly comparable
**Claim.** Of twelve reviewed benchmark studies, none matched this study's
dataset, target, horizon, partitioning and metric definition simultaneously;
seven were partially comparable and five contextual only.
**Evidence.** `combined/literature_benchmark_matrix.csv`,
`report/benchmark_comparison.md`.
**Table/figure.** T6.1. **RQ/RO.** all; positioning.
**Strength.** **Strongly supported**.

---

## Part 2 — Claims NOT supported by the study

State these as explicitly prohibited in the writing guide, and check the final
draft against them.

| # | Prohibited claim | Why it fails |
|---|---|---|
| N1 | "ConfoSense universally outperforms all forecasting methods." | Persistence beats XGBoost on every PLEIA temperature horizon and at BDG2 h=1 (`combined/point_metrics.csv`). |
| N2 | "ConfoSense numerically outperforms prior published studies." | 0 of 12 reviewed studies are directly comparable (`combined/literature_benchmark_matrix.csv`). |
| N3 | "CQR's failure on RICO is caused by its run structure." | Exchangeability was never tested; this is a labelled hypothesis (`report/rico_quantile_crossing_audit.md`). |
| N4 | "Closed-loop fault absorption occurs identically on every dataset." | Observed-signal coverage at 2 σ ranges 0.2580–0.9763 (`combined/robustness_metrics.csv`). |
| N5 | "XGBoost is significantly better than persistence." | Holm-corrected post-hoc p = 1.0000 across blocks (`combined/posthoc_comparisons.csv`). |
| N6 | "The framework detects real building faults." | All events are injected; no labelled real faults exist for these datasets. |
| N7 | "BDG2 has distinct periodic and rolling recalibration results." | `strategy_is_distinct = False`; the rolling row reproduces periodic exactly. |
| N8 | "Any method is well calibrated on RICO." | Best arm 0.9036 against nominal 0.95. |
| N9 | "The framework selected the best point model and conformal method." | Both are test-set comparisons, not validated selections (`report/final_confosense_configuration.md`). |
| N10 | "PLEIA energy RMSE shows the target is highly volatile." | One meter-stall artefact dominates the squared error. |
| N11 | "The uncalibrated baseline is competitive on BDG2 because it wins on Winkler." | It undercovers by 0.111; the Winkler margin is 0.02 %. |
| N12 | "The leakage-safe alert selection improved alerting performance." | It worsened RICO's test F1 (0.4605 versus 0.5344); it improves selection validity, not test score. |
| N13 | "Attention-LSTM underperformed due to insufficient training data." | Not tested; no ablation over training size was run. |
| N14 | "The BDG2 results generalise to building stock." | 10 of 1,258 eligible buildings. |
| N15 | "Rolling recalibration is the best strategy." | Best on two targets; periodic is best on the other two. |
| N16 | "The crossing repair rescued CQR on RICO." | It raises coverage by 0.000–0.039 per cell and never to nominal. |
| N17 | "Coverage of 1.0000 under contamination shows robustness." | The intervals became uninformative; it is a failure mode. |
| N18 | "The framework is optimal." | No optimality argument was made or tested; only completeness, control and reproducibility are claimed. |

---

## Part 3 — Claim-to-RQ coverage check

| RQ | Supporting claims | Negative/qualifying claims |
|---|---|---|
| RQ1 (integrated framework) | C5, C6, C7, C8, C19, C20 | N1, N5, N9, N13 |
| RQ2 (conformal across datasets) | C1, C2, C3, C4, C18 | N3, N8, N11, N16 |
| RQ3 (alert reliability and robustness) | C9, C10, C11, C12, C13, C14, C15, C16, C17 | N4, N6, N7, N12, N15, N17 |
| Positioning | C21 | N2, N14, N18 |

Every research question is supported by at least five claims and constrained by
at least four prohibitions. A draft that asserts a Part 2 claim has overstated
the evidence and must be corrected before submission.
