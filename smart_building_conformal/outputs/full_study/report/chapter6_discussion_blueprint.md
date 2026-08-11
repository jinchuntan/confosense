# Chapter 6 (Discussion) — writing blueprint

Organised around RQ1–RQ3. Every item is tagged:

* **[OBSERVED]** — a measured value in a persisted file. Quote it exactly.
* **[INTERPRETATION]** — the author's reading of observed results. Defensible,
  but not itself a measurement.
* **[HYPOTHESIS]** — a possible explanation the study did **not** test. Must be
  written as a hypothesis and never converted into a causal claim.

The distinction is not stylistic. A hypothesis presented as a finding is the
error this chapter exists to avoid.

---

## 6.1 Overview

State the shape of the argument: four heterogeneous targets, one controlled
protocol, and a framework whose value lies in the procedure rather than in any
single model. Signal early that two headline results are *negative* — no
conformal method transfers, and the conventional robustness protocol misstates
fault sensitivity — and that negative findings are reported as findings.

---

## 6.2 RQ1 — Integrated uncertainty-aware monitoring framework

### Evidence

**[OBSERVED]** A single protocol executed 4 point forecasters × 13
dataset/horizon cells, 5 interval methods × 2 nominal levels, 4 alert rules,
3 recalibration strategies and 15 disturbance scenarios × 2 evaluation modes plus
3 contamination levels, across 4 targets from 3 public datasets, with 0 failed
stages (`manifests/run_history.jsonl`, `manifests/stage_provenance.json`,
`combined/`).

**[OBSERVED]** XGBoost wins 9 of 13 cells, persistence 4
(`combined/point_metrics.csv`).

**[OBSERVED]** The best-calibrated interval method differs by dataset;
the frozen alert rule differs on all four; the best recalibration strategy
differs (`combined/confosense_configurations.csv`).

### Interpretation

**[INTERPRETATION]** The integration is the contribution. Each component exists
in the literature; what did not exist is a single leakage-controlled pipeline in
which forecasting, conformal calibration, operating-point selection, robustness
and recalibration are evaluated on the same partitions with the same seeds, so
that a change in one component can be attributed rather than guessed at.

**[INTERPRETATION]** The evidence answers RQ1 affirmatively but conditionally:
an integrated framework is feasible and produces coherent end-to-end results,
**and** it must be configured per target rather than shipped as a fixed model.

### Comparison with internal benchmarks

**[OBSERVED]** Against the mandatory naive baselines, no learned model dominates:
persistence wins every PLEIA temperature horizon and BDG2 at 1 h
(`combined/point_metrics.csv`).

**[INTERPRETATION]** Including naive baselines as mandatory rather than optional
is what makes this visible; a study reporting only learned models on PLEIA
temperature would have reported an improvement that does not exist.

### Comparison with literature

See §6.6. No published result is directly comparable.

### Practical meaning

**[INTERPRETATION]** A building operator adopting this framework must run the
selection procedure on their own calibration data. The framework transfers; a
configuration does not.

### Limitation

**[OBSERVED]** The point-model family and conformal method were compared on the
test partition, not selected on calibration data
(`report/final_confosense_configuration.md`, evidence-class table). Only the
XGBoost hyperparameters, the alert rule and the recalibration settings are
validated selections.

### Defensible conclusion

An integrated uncertainty-aware monitoring framework was implemented and
evaluated end to end across four heterogeneous smart-building targets under one
controlled protocol. The framework is configurable rather than universal, and a
calibration-side model-selection protocol remains to be specified.

---

## 6.3 RQ2 — Conformal prediction across smart-building datasets

### Evidence

**[OBSERVED]** `quantile_uncalibrated` undercovers on all four datasets at
nominal 0.95: coverage deviation 0.0705 (PLEIA temp), 0.1016 (PLEIA energy),
0.1110 (BDG2), 0.3196 (RICO) (`combined/interval_metrics.csv`).

**[OBSERVED]** Best-calibrated arm: `cqr` on PLEIA temperature (0.9417);
`recentred_enbpi_updated` on PLEIA energy (0.9511), RICO (0.9036) and BDG2
(0.9503).

**[OBSERVED]** On RICO no arm reaches nominal — best single cell 0.9293, best
arm averaged over horizons 0.9036 against 0.95.

**[OBSERVED]** CQR on RICO: coverage 0.7719, Winkler 11.2602, and 3,912 of
66,696 intervals crossed before order-repair across both nominal levels (2,558
at 0.95). Crossings concentrate in 16 of 42 test runs; median magnitude
0.21–1.35 °C (`combined/rico_quantile_crossings.csv`,
`rico_quantile_crossings_by_run.csv`).

**[OBSERVED]** DSCP over-covers on PLEIA energy (0.9840) and PLEIA temperature
(0.9527) but is second-best-calibrated on RICO (0.8972) at 28 % narrower width
than CQR.

**[OBSERVED]** On BDG2 the uncalibrated baseline attains the lowest Winkler
(200.2032 versus CQR 200.2521) while covering 0.8390 against 0.95.

### Interpretation

**[INTERPRETATION]** Conformal calibration is *necessary* — the uncalibrated
baseline fails everywhere — but not *sufficient*: on RICO every conformal arm
still undercovers. The contribution of calibration is therefore best stated as
substantial and consistent, not as a solution.

**[INTERPRETATION]** The BDG2 Winkler result is a warning about single-metric
reporting, not a result in favour of uncalibrated intervals. A method that is
narrower can win on Winkler while missing its nominal coverage by 0.111.
Coverage deviation and Winkler must be reported as a pair.

**[INTERPRETATION]** DSCP's behaviour is consistent with a method designed for
multi-step dependence: it helps most where the target is fast and
regime-structured (RICO) and over-covers where the target is smooth.

### Required wording for RICO

Use exactly:

> CQR substantially undercovered on RICO under the evaluated protocol.

**[HYPOTHESIS]** RICO's calibration and test partitions are disjoint sets of
four-hour runs following different set-point programmes, so calibration and test
residuals may not be exchangeable. **Not tested here.** Testing it would require
a designed exchangeability test across run partitions.

**[HYPOTHESIS]** Independent conditional quantile estimates are more likely to
cross where the conditional distribution shifts sharply between regimes; the
concentration of crossings in a minority of runs is *consistent* with this, but
consistency is not evidence of cause. **Not tested here.**

Do **not** write "RICO's run structure caused CQR to fail."

### Comparison with internal benchmarks

**[OBSERVED]** Ranking by coverage deviation at 0.95 differs from ranking by
Winkler on BDG2 and PLEIA energy; the two criteria disagree in 2 of 4 datasets.

### Comparison with literature

Yu et al. (2025) is the method source for DSCP and Xu & Xie (2023) for EnbPI,
both classified PARTIALLY_COMPARABLE. Neither supplies a number this study can
compare against (§6.6).

### Practical meaning

**[INTERPRETATION]** For deployment, the conformal layer must be chosen per
target and validated on that target's own calibration data. Reporting coverage
without width, or width without coverage, would mislead an operator.

### Limitations

**[OBSERVED]** DSCP assembles its multi-step vector across direct per-horizon
models rather than one multi-output model — a documented deviation from Yu et
al. (2025). The EnbPI arm is a documented *recentred* adaptation.

### Defensible conclusion

Conformal calibration substantially and consistently improved interval coverage
over an uncalibrated quantile baseline on all four targets, but no single
conformal method transferred across datasets, and on RICO none achieved nominal
coverage under the evaluated protocol.

---

## 6.4 RQ3 — Alert reliability and robustness

### Evidence

**[OBSERVED]** Frozen rules: PLEIA temp 4-of-7, PLEIA energy 2-of-3, RICO
2-of-3, BDG2 1-of-1. Test F1: 0.6733, 0.5565, 0.4605, 0.0490
(`combined/alert_metrics.csv`).

**[OBSERVED]** Recall is stable (0.7619–0.8810); precision varies by more than
twentyfold (0.0252–0.5763).

**[OBSERVED]** On RICO no candidate rule met the 1 false alert/day budget; the
quietest was taken and still produced 11.9457 false alerts/day on test.

**[OBSERVED]** Under the pooled selection procedure this study replaced, the
PLEIA calibration FAR for 3-of-5 was 0.0131 against 0.0508 under the
leakage-safe split (`report/alert_selection_audit.md`).

**[OBSERVED]** 2 σ sensor bias, fixed-interval protocol: observed-signal
coverage 0.0000–0.0749, alert rate 0.9279–0.9999, clean-reference metrics flat.

**[OBSERVED]** 2 σ sensor bias, closed loop: observed-signal coverage 0.9763
(PLEIA energy), 0.8876 (BDG2), 0.5025 (RICO), 0.2580 (PLEIA temp); clean-reference
coverage 0.1804, 0.0529, 0.0001, 0.0006; clean-reference MAE multiplied by
6.7, 23.6, 94.4 and 23.4 respectively; alert rate falls on every dataset
(`combined/robustness_metrics.csv`).

**[OBSERVED]** 10 % calibration contamination: PLEIA interval width 1.8526 (at
1 %) → 26.8179, coverage 1.0000; BDG2 width 1,468.7591.

**[OBSERVED]** Adaptive recalibration reduces coverage deviation on all four
datasets; BDG2 remains at 0.8592 against 0.95, and its rolling row is not a
distinct strategy (`strategy_is_distinct = False`).

### Interpretation

**[INTERPRETATION]** The leakage in the original selection procedure was real
and material: the pooled calibration surface understated the false-alert workload
roughly fourfold on PLEIA, and correcting it moved 2 of 4 frozen rules. This is
a methodological finding, not a bug report.

**[INTERPRETATION]** Correcting the leakage did not uniformly improve test
performance. On PLEIA it selected a better operating point (F1 0.6733 versus
0.4892 for the superseded rule); on RICO it selected a worse one (0.4605 versus
0.5344). That is the expected behaviour of an honest procedure: it optimises the
quantity it can legitimately see, not the test score.

**[INTERPRETATION]** The closed-loop result is the study's most consequential
finding for practice. The conventional protocol reports a loud, obvious fault;
the closed-loop protocol shows the forecaster absorbing the same fault, so
observed-signal coverage stays high and the monitor goes quiet exactly as the
forecast diverges from reality.

**[INTERPRETATION]** Coverage saturating at 1.0 under contamination is a failure
mode, not robustness: the intervals have become uninformative.

### Causality — what may and may not be claimed

The disturbance experiments **manipulate** the cause, so a causal statement about
the injected bias is legitimate: *injecting a 2 σ sensor bias into the feature
history caused clean-reference coverage to fall to 0.0529 on BDG2.* This is the
one place in the dissertation where causal language is earned.

It does **not** license: that absorption occurs identically on every dataset (it
does not — PLEIA temperature retains an alert rate of 0.7315); that the framework
would behave this way under fault types not injected; or that real building
faults resemble the injected catalogue.

### Comparison with internal benchmarks

**[OBSERVED]** Across k-of-m rules, precision rises and recall falls
monotonically with k where the false-alert budget is attainable
(`fig_05_alert_rule_sensitivity.png`).

### Comparison with literature

Nguyen et al. (2025) and Park et al. (2025) are CONTEXTUAL_ONLY: they use
labelled real faults, so their precision and recall are not comparable
quantities to ours.

### Practical meaning

**[INTERPRETATION]** A deployed monitor should be evaluated in closed loop, and
its calibration data should be screened for contamination before use. An
operator who evaluates only in fixed-interval mode will overestimate the
system's fault sensitivity.

### Limitations

**[OBSERVED]** All events are injected; no labelled real faults exist for these
datasets. Alert precision and recall therefore measure sensitivity to controlled
disturbances.

### Defensible conclusion

Interval-based alerting is workable but its operating point must be tuned per
target on out-of-conformal-calibration data, and it is not uniformly robust:
under closed-loop evaluation the forecaster absorbed a sustained sensor bias on
three of four targets, and calibration contamination degraded intervals to the
point of being uninformative.

---

## 6.5 Comparison with controlled benchmark methods (primary evidence)

Draw entirely on `report/benchmark_comparison.md` §A. State the design
argument once: all arms share partitions, features, seeds, horizons and metric
definitions, so differences are attributable to the method rather than to the
experimental setting. That is what makes this the *primary* comparative evidence
and the published literature merely contextual.

Summarise the four internal comparisons — point, interval, alerting,
recalibration — and note that in each the winner is dataset-dependent.

---

## 6.6 Comparison with published literature (contextual evidence)

Use the prepared wording in `benchmarking_and_contribution_wording.md` §1.
The load-bearing fact: **0 of 12 reviewed studies satisfied all conditions for
direct numerical comparison** (`combined/literature_benchmark_matrix.csv`;
7 PARTIALLY_COMPARABLE, 5 CONTEXTUAL_ONLY).

---

## 6.7 Definition and configuration of ConfoSense

Use the prepared wording in `benchmarking_and_contribution_wording.md` §2–§4.

---

## 6.8 Practical implications for smart-building monitoring

**[INTERPRETATION]** Six implications, each traceable to an observed result:

1. Do not deploy uncalibrated quantile intervals — they undercover on every
   target studied.
2. Select the conformal layer per target; do not assume a published method
   transfers.
3. Report coverage deviation and Winkler together; either alone can mislead.
4. Tune the alert operating point on data the conformal quantile has not seen.
5. Evaluate in closed loop; fixed-interval evaluation overstates fault
   sensitivity.
6. Screen calibration data for contamination; 10 % contamination made intervals
   uninformative on every dataset.

---

## 6.9 Limitations

Take the full list from `report/dissertation_handoff.md` §14–§16 and
`report/full_study_limitations.md`. The four that most affect interpretation:

1. Injected events, not real faults.
2. No pre-registered calibration-side protocol for selecting the point model or
   conformal method — those comparisons are test-set comparisons.
3. RICO is unsolved: no arm reaches nominal coverage.
4. PLEIA energy RMSE is dominated by one meter-stall artefact and must always be
   reported with that explanation.

---

## 6.10 Chapter Summary

Close by separating what was demonstrated from what was hypothesised, and state
plainly that two of the study's principal findings are negative. A dissertation
that reports a negative finding cleanly is stronger than one that does not.
