# Final writing handoff — ConfoSense dissertation

Master of Computer Science (Applied Computing), Universiti Malaya — WOC7024.

The implementation and experimental study are **frozen**. This is the master
document for controlled chapter-by-chapter writing. Every numerical statement
below names its persisted source; all paths are relative to
`outputs/full_study/`.

Companion documents in this folder:

| Document | Use |
|---|---|
| `final_dissertation_structure.md` | chapter and section plan |
| `final_dissertation_migration_plan.md` | what to do with each progress-report section |
| `chapter5_results_blueprint.md` | Chapter 5, subsection by subsection |
| `chapter6_discussion_blueprint.md` | Chapter 6, organised by RQ |
| `benchmarking_and_contribution_wording.md` | drop-in prose for §6.6 and §6.7 |
| `table_figure_placement_map.md` | what goes in the main body, what to the appendix |
| `final_claims_register.md` | 21 permitted claims, 18 prohibited ones |

---

## 1. Final dissertation structure

Seven chapters, references, nine appendices. Full section list in
`final_dissertation_structure.md`. Recommended writing order: **Ch. 3 → Ch. 4 →
Ch. 5 → Ch. 6 → Ch. 2 → Ch. 1 → Ch. 7**, so that no interpretation is written
before the result it interprets.

Main body carries **18 tables and 9 figures**; everything else goes to the
appendices (`table_figure_placement_map.md`).

---

## 2. Research questions and objectives

Unchanged and not to be reworded. Mapping to evidence:
`combined/rq_ro_evidence_matrix.csv`, `report/rq_ro_evidence_matrix.md`.

| | Question | Objective |
|---|---|---|
| **RQ1** | How accurately can short-term building sensor and energy values be forecast, and do learned models improve on naive baselines? | **RO1** Implement and evaluate short-term point forecasting across heterogeneous building datasets against mandatory naive baselines. |
| **RQ2** | Does conformal prediction deliver calibrated intervals for building time series, and which conformal method is preferable? | **RO2** Implement CQR, recentred EnbPI and DSCP under one protocol and compare them against an uncalibrated quantile baseline. |
| **RQ3** | Can calibrated intervals support practical alerting, and does that alerting remain trustworthy under realistic disturbance and drift? | **RO3** Evaluate interval-based alerting, its rule sensitivity, its robustness to disturbance, and the effect of periodic and rolling recalibration. |

---

## 3. Dataset summary

Source: `<dataset>/data_profiles/series_profile.csv`, `window_summary.csv`,
`manifests/dataset_sources.json`.

| Dataset | Target | Units | Series | Obs. | Sampling | Span | Horizons | Seasonal naive |
|---|---|---|---|---|---|---|---|---|
| PLEIA temperature | B-room11-V2 | °C | 1 | 50,543 | 10 min | 2021-01-01 – 2021-12-17 | 1, 3, 6 | applicable |
| PLEIA energy | blockB-dif_cons | kWh/interval | 1 | 50,545 | 10 min | 2021-01-01 – 2021-12-18 | 1, 3, 6 | applicable |
| RICO HVAC | B.RTD3 | °C | 207 runs | 49,680 | 1 min | 2023-07-26 – 2024-05-18 | 5, 15, 30, 60 | **not applicable** |
| BDG2 electricity | electricity | kWh | 10 buildings | 175,440 | 1 h | 2016-01-01 – 2017-12-31 | 1, 3, 6 | applicable |

Supervised windows at the operating horizon (train / calibration / test):
PLEIA temp 29,318 / 10,109 / 10,108 · PLEIA energy 29,320 / 10,109 / 10,108 ·
RICO 27,404 / 9,061 / 9,282 · BDG2 103,527 / 34,987 / 34,838.

Selection was performance-blind: RICO retains 207 of 287 scheduler groups,
excluding 80 on the authors' own quality flag (`rico/data_profiles/run_audit.csv`);
BDG2 retains 10 of 1,258 eligible buildings across 6 sites and 3 use types
(`bdg2/data_profiles/subset_selection.csv`). Neither audit contains a
performance column.

---

## 4. Experimental methods

* **Partitioning.** Chronological 60/20/20, group-safe. RICO partitions whole
  experimental runs; BDG2 partitions within each building
  (`<dataset>/data_profiles/partitioning.json`).
* **Forecasting.** Direct horizon-specific models — one model per horizon, no
  recursive feeding. Arms: persistence, seasonal naive (where a full cycle
  exists), XGBoost, Attention-LSTM.
* **Intervals.** CQR, recentred EnbPI (static and sequentially updated), DSCP,
  and an uncalibrated quantile baseline, at nominal 0.90 and 0.95.
* **Alerting.** k-of-m persistence over interval violations. The operating rule
  is frozen on the later 40 % of the calibration partition, admitted only if its
  forecast origin strictly postdates every conformal target time
  (`<dataset>/metrics/alert_selection_split.csv`).
* **Robustness.** 15 injected disturbance scenarios in two modes
  (`legacy_fixed_intervals`, `closed_loop`) plus calibration contamination at
  1 / 5 / 10 %.
* **Recalibration.** Static, periodic and rolling; parameters from a calibration
  replay with an h-step embargo; no residual consumed before its ground truth
  exists.
* **Statistics.** Moving-block bootstrap, Diebold–Mariano with HLN correction,
  Friedman, Holm-corrected Wilcoxon post-hoc.
* **Environment.** Python 3.11.9 in a clean virtual environment; seeds, thread
  configuration, package versions and dataset checksums recorded in
  `manifests/`. The full study ran non-fast with 0 failed stages; 170 automated
  tests pass.

---

## 5. The most important final findings

1. **Uncalibrated quantile intervals undercover on all four targets** —
   coverage deviation 0.0705 to 0.3196 at nominal 0.95.
   `combined/interval_metrics.csv`
2. **No conformal method transfers.** Best-calibrated arm: `cqr` on PLEIA
   temperature (0.9417); `recentred_enbpi_updated` on PLEIA energy (0.9511),
   RICO (0.9036), BDG2 (0.9503). `combined/interval_metrics.csv`
3. **RICO is unsolved.** No arm reaches nominal; best single cell 0.9293, best
   arm averaged over horizons 0.9036. `combined/interval_metrics.csv`
4. **CQR substantially undercovered on RICO under the evaluated protocol**
   (0.7719), with 3,912 of 66,696 intervals crossing before order-repair across
   both levels, concentrated in 16 of 42 test runs.
   `combined/rico_quantile_crossings.csv`
5. **The best point forecaster is target-dependent** — XGBoost 9 of 13 cells,
   persistence 4, including every PLEIA temperature horizon.
   `combined/point_metrics.csv`
6. **The learned-model advantage grows with horizon** — RICO +23.66 % at 5 min
   to +48.77 % at 60 min; BDG2 −12.86 % at 1 h to +48.00 % at 6 h.
   `combined/effect_sizes.csv`
7. **Significance and practical improvement diverge** — Friedman χ² = 14.0667,
   p = 0.002816; Holm post-hoc leaves only seasonal naive vs XGBoost
   (p = 0.0234); XGBoost vs persistence p = 1.0000 across blocks, yet
   significant in 10 of 13 individual Diebold–Mariano cells.
   `combined/ranking_tests.csv`, `posthoc_comparisons.csv`, `statistical_tests.csv`
8. **Reusing the conformal sample for rule selection is optimistic** — PLEIA
   calibration FAR 0.0131 pooled versus 0.0508 nested; correcting it moved the
   frozen rule on 2 of 4 targets. `report/alert_selection_audit.md`
9. **A leakage-safe procedure does not guarantee a better test score** — PLEIA
   improved (F1 0.6733 vs 0.4892), RICO worsened (0.4605 vs 0.5344).
   `combined/alert_metrics.csv`
10. **Alert operating points differ on every target** — 4-of-7, 2-of-3, 2-of-3,
    1-of-1; test F1 0.0490 to 0.6733. `combined/alert_metrics.csv`
11. **The false-alert budget was unattainable on RICO** — no rule met 1/day; the
    quietest still produced 11.9457/day on test. `combined/alert_metrics.csv`
12. **Closed-loop evaluation reverses the robustness reading** — at 2 σ bias the
    fixed-interval protocol reports observed-signal coverage 0.0000–0.0749 and
    alert rate up to 0.9999; in closed loop observed-signal coverage reaches
    0.9763 (PLEIA energy) and 0.8876 (BDG2) while clean-reference coverage falls
    to 0.1804 and 0.0529 and the alert rate falls on every target.
    `combined/robustness_metrics.csv`
13. **Absorption is a gradient** — PLEIA temperature retains observed-signal
    coverage 0.2580 and alert rate 0.7315 at the same severity.
    `combined/robustness_metrics.csv`
14. **Calibration contamination is the most damaging disturbance** — 10 %
    inflates PLEIA width 1.8526 → 26.8179 and saturates coverage at 1.0000
    (a failure mode). `combined/robustness_metrics.csv`
15. **Adaptive recalibration helps everywhere but does not rescue BDG2** —
    deviation falls on all four targets (PLEIA 0.0176 → 0.0020 rolling); BDG2
    reaches only 0.8592 against 0.95, and its rolling row is not a distinct
    strategy. `combined/recalibration_metrics.csv`
16. **PLEIA energy RMSE is a data artefact** — two meter-stall catch-ups after
    556 and 385 zero-increment steps; the test-partition one inflates XGBoost
    RMSE from 0.1550 to 2.4510. `report/pleia_energy_audit.md`

---

## 6. Benchmarking position

Primary comparative evidence is the **controlled internal benchmark**: all arms
share partitions, features, seeds, horizons and metric definitions, so
differences are attributable to the method.

Published literature is **contextual**. Of twelve reviewed studies, **0 are
directly comparable**, 7 partially comparable, 5 contextual only
(`combined/literature_benchmark_matrix.csv`). **No claim of numerical
superiority over any published study is made.** Prepared wording:
`benchmarking_and_contribution_wording.md` §1.

---

## 7. Final ConfoSense definition

> ConfoSense is a **configurable uncertainty-aware monitoring framework** for
> smart-building sensor and energy data — a specified pipeline together with a
> decision procedure for instantiating it on a given target — **not a new
> forecasting algorithm**.

Six components: data preparation · point forecasting · conformal calibration ·
interval-based alerting · robustness evaluation · recalibration.

The evidence does not support one universal configuration: the best point
forecaster, the best-calibrated conformal method, the frozen alert rule and the
best recalibration strategy all resolve differently across the four targets
(`combined/confosense_configurations.csv`).

**Critical distinction to preserve in writing:** XGBoost hyperparameters, the
alert rule and the recalibration settings are **validated selections** made
without test data; the point-model family and the conformal method are
**reported comparisons on test data**, not selections the framework made blind
(`report/final_confosense_configuration.md`). Full wording:
`benchmarking_and_contribution_wording.md` §2–§3.

---

## 8. RQ1 conclusion

An integrated uncertainty-aware monitoring framework was implemented and
evaluated end to end across four heterogeneous smart-building targets under one
controlled protocol, with zero failed stages. Learned models improved on naive
baselines where the signal is spiky or the horizon long, and did not where the
target is thermally slow: XGBoost won 9 of 13 dataset/horizon cells, persistence
won 4 including every PLEIA indoor-temperature horizon. The improvement is real
in magnitude but is not statistically separable from persistence at the block
level. **The framework is configurable rather than universal**, and a
calibration-side model-selection protocol remains to be specified.

## 9. RQ2 conclusion

Conformal calibration substantially and consistently improved interval coverage
over an uncalibrated quantile baseline on all four targets, so it is **necessary**.
It is **not sufficient**: no single conformal method transferred across datasets,
and on RICO none reached nominal coverage — CQR substantially undercovered under
the evaluated protocol. Coverage deviation and Winkler score must be reported
together, since on BDG2 the uncalibrated baseline attains the lowest Winkler
while missing nominal coverage by 0.111.

## 10. RQ3 conclusion

Interval-based alerting is workable, but its operating point must be tuned per
target on data the conformal quantile has not seen — and doing so honestly can
lower the test score, as it did on RICO. The alerting is **not uniformly
trustworthy under disturbance**: in closed-loop evaluation the forecaster
absorbed a sustained sensor bias on three of four targets, so observed-signal
coverage stayed high and the monitor quietened exactly as the forecast diverged
from reality, and calibration contamination degraded intervals to the point of
being uninformative. Adaptive recalibration reduced coverage deviation on every
target but did not restore nominal coverage on BDG2.

---

## 11. Contributions

1. **Methodological** — a leakage-safe operating-point selection procedure for
   interval-based alerting: a nested chronological split inside the calibration
   partition with an exact embargo. Changed 2 of 4 frozen rules and revealed a
   roughly fourfold understatement of false-alert workload on one target.
   `report/alert_selection_audit.md`
2. **Experimental** — a controlled cross-dataset comparison of 4 point
   forecasters, 5 interval methods, 4 alert rules, 3 recalibration strategies and
   15 disturbance scenarios in 2 modes, over 4 targets from 3 public datasets,
   under identical partitions, features, seeds and metrics, with full provenance.
   `combined/`, `manifests/stage_provenance.json`
3. **Applied** — a dual-mode robustness evaluation separating observed-signal
   from clean-reference metrics, demonstrating that conventional fixed-interval
   evaluation misstates the fault sensitivity of an interval-based monitor.
   `combined/robustness_metrics.csv`, `report/closed_loop_terminology.md`

---

## 12. Limitations

**Methodological.** Injected events, not real faults. No pre-registered
calibration-side protocol for choosing the point model or conformal method. DSCP
assembles its multi-step vector across direct per-horizon models rather than one
multi-output model. The EnbPI arm is a documented *recentred* adaptation. CQR
required order-repair of 2,558 crossed intervals on RICO at the 0.95 level. The
frozen alert rule was selected against a model conformalized on 60 % of the
calibration partition while reported test intervals use 100 %.

**Dataset.** PLEIA is one room in one block. The PLEIA energy target contains two
meter-stall artefacts, one in calibration and one in test. 80 RICO scheduler
points excluded on the authors' quality flag. BDG2 is 10 of 1,258 eligible
buildings.

**Computational.** The BDG2 interval stage takes about 2.6 h, dominated by
EnbPI's online updates. XGBoost refits are single-threaded to remove thread-order
nondeterminism. Reproducibility is verified same-machine.

Full lists: `report/dissertation_handoff.md` §14–§16,
`report/full_study_limitations.md`.

---

## 13. Recommended main-body tables (18)

T5.1 dataset profiles · T5.2 window counts · T5.3 best point forecaster ·
T5.4 mean ranks · T5.5 intervals at 0.95 · T5.7 nested calibration split ·
T5.8 frozen alert rule on test · T5.9 bias, fixed-interval · T5.10 calibration
contamination · T5.11 bias, closed loop · T5.12 recalibration · T5.13 Friedman ·
T5.14 post-hoc · T5.15 Diebold–Mariano summary · T5.16 per-target configuration ·
T6.1 literature comparability · T6.2 evidence class of each choice.

## 14. Recommended main-body figures (9)

F5.1 `fig_01_point_forecasting_comparison.png` ·
F5.2 `fig_02_coverage_vs_width.png` ·
F5.3 `fig_03_coverage_deviation_by_horizon.png` ·
F5.4 `fig_04_winkler_comparison.png` ·
F5.5 `fig_05_alert_rule_sensitivity.png` ·
F5.6 `fig_06_alert_tradeoff.png` ·
F5.7 `fig_07_robustness_degradation.png` ·
**F5.8 `fig_13_closed_loop_absorption.png` — the single most important figure** ·
F5.9 `fig_08_recalibration_recovery.png`.

## 15. Appendix material

A dataset selection audits · B full interval tables and the three interval
timelines · C complete alert-rule surfaces · D complete robustness tables ·
E bootstrap CIs, all 48 Diebold–Mariano tests, effect sizes, `fig_09` ·
F RICO quantile-crossing audit incl. per-run counts · G PLEIA energy target
audit · H reproducibility record (manifests, provenance, environment) ·
I preliminary experiment results, retained for continuity with the progress
report.

## 16. Claims to avoid

Check the final draft against all 18 prohibitions in
`final_claims_register.md` Part 2. The six that are easiest to write by accident:

1. "ConfoSense outperforms published work" — 0 of 12 studies are comparable.
2. "XGBoost is significantly better than persistence" — Holm p = 1.0000.
3. "RICO's run structure caused CQR to fail" — untested hypothesis.
4. "Fault absorption occurs identically on every dataset" — 0.2580 to 0.9763.
5. "BDG2 has periodic *and* rolling results" — `strategy_is_distinct = False`.
6. "The framework selected the best conformal method" — that was a test-set
   comparison, not a validated selection.

---

## 17. Verification before submission

1. Every number in the draft traces to a file under `outputs/full_study/`.
2. No pre-audit value appears — in particular the PLEIA alert rule is **4-of-7**
   and the RICO alert rule is **2-of-3**.
3. Every coverage figure in a robustness context is qualified as
   *observed-signal* or *clean-reference*.
4. No sentence from `final_claims_register.md` Part 2 appears.
5. Progress-report language ("will be evaluated", "planned", "preliminary",
   "expected contribution", "pending") appears only in Appendix I.
