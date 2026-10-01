# Internal report-readiness assessment

This is an internal checklist for writing. It is not dissertation prose and it
does not use the preset `full_study_ready` flag as an acceptance criterion.

## Evidence ready to write

| Report need | Readiness | Authoritative package table or fact sheet |
|---|---|---|
| Dataset, target, temporal split and horizon descriptions | Ready | `METHODOLOGY_FACTS.md`; `EVIDENCE_MAP.csv` |
| Point forecasting against persistence and applicable seasonal-naive baselines | Ready | `REPORT_TABLES/POINT_FORECASTING.csv` |
| Own-model 90%/95% interval quality | Ready | `REPORT_TABLES/INTERVAL_OWN_MODEL.csv` |
| Matched CQR/EnbPI/DSCP/uncalibrated-quantile interval comparison | Ready | `REPORT_TABLES/INTERVAL_METHODS_COMMON_SUPPORT.csv` |
| Seasonal point and interval benchmark | Ready | `REPORT_TABLES/SEASONAL_BASELINES.csv` |
| PLEIA direct conditional-fault alert comparison | Ready, with endpoint limitation | `REPORT_TABLES/CONDITIONAL_ALERTS_PLEIA.csv` |
| BDG2 one-hour complete monitoring-configuration comparison | Ready | `REPORT_TABLES/OPERATIONAL_ALERTS_BDG2_H1.csv` |
| Robustness, calibration contamination and recovery | Ready | three `REPORT_TABLES/ROBUSTNESS_*.csv` files |
| Attention-LSTM computational cost versus predictive benefit | Ready | `REPORT_TABLES/ATTENTION_LSTM_VS_XGBOOST.csv`; `COMPUTATIONAL_OVERHEAD.csv` |
| Validation and provenance statements | Ready | `EVIDENCE_MAP.csv` and the pinned delivery receipts |

The completed evidence is sufficient for bounded empirical conclusions under
RO2 and RO3. The false `full_study_ready` values were frozen planning fields;
they do not overturn later accepted completion, validation, backup and delivery
records.

## Evidence-to-objective assessment

### RO1

The code and results support a structured empirical review of persistence,
seasonal-naive, XGBoost, Attention-LSTM, split conformal, CQR, EnbPI, DSCP,
online recalibration and interval-derived alert rules. What remains necessary is
literature-review writing: current scholarly citations, rationale for the
selected methods and a clear separation between literature claims and this
study's empirical findings. No new experiment is needed for that work.

### RO2

Ready. Every stated stage has implementation and validation evidence: causal
features; matched forecasting; calibration; interval construction; delayed
residual updates; alert episode formation; fault, contamination and recovery
evaluation; and independent validation/zero-fit resume. Chapter 3 should use
the exact protocol distinctions in `METHODOLOGY_FACTS.md` rather than a single
generic “conformal alerting” description.

### RO3

Ready if the conclusion is framed as identifying reliable combinations within
the evaluated conditions. Forecasting and interval-only matrices must not be
described as direct alert evaluations. Direct alert evidence is available for
the two PLEIA conditional challenges and BDG2 one-hour operational replay;
robustness adds primary-horizon fault/recovery evidence for all four tasks. A
universal winner is not supported because detection/workload trade-offs and
recalibration effects change by dataset and rule.

## Material gaps and writing controls

1. **Population inference remains unavailable.** Do not attach confidence
   intervals or significance language to folds, seeds, catalogue repetitions,
   groups or stream rows. The PLEIA detection bounds have their own
   original-context block interpretation only.
2. **Endpoint differences must remain visible.** Conditional-context detection
   is not ordinary precision/F1 or natural-prevalence performance. Operational
   custom synthetic F1 is not ordinary F1. Interval clean-workload tables with
   empty event catalogues cannot supply recall or F1.
3. **Direct operational scope is bounded.** The complete causal replay is BDG2
   at the one-hour horizon. RICO and PLEIA robustness cells do not turn into a
   complete operational candidate-grid comparison.
4. **Internal grid-coverage note:** 99 planned operational candidate
   definitions lacked exact saved owners under the zero-fit contract. This is
   preserved in the delivery evidence for audit, but no dissertation narrative
   about those candidates is required. The Chapter 4 table should describe the
   165 directly evaluated definitions and their protocol, not speculate about
   unevaluated outcomes.
5. **Cross-task numbers use different units and supports.** Do not rank a kWh
   width against a degrees-Celsius width or mix native/common views as if they
   were independent observations.
6. **Attention-LSTM conclusion is bounded.** The frozen experiments do not show
   a general computational benefit. Do not generalise this to all recurrent
   architectures or tuning budgets.
7. **Robustness is not universality.** Synthetic corruption and calibration
   contamination validate the declared mechanisms only; natural faults,
   additional buildings and deployment drift remain outside scope.

## Tables that should replace older draft tables

- Replace earlier point-model or pilot tables with
  `POINT_FORECASTING.csv`; use `ATTENTION_LSTM_VS_XGBOOST.csv` for the explicit
  cost-benefit statement.
- Replace partial own-model interval tables with `INTERVAL_OWN_MODEL.csv`.
- Replace preliminary CQR/EnbPI/DSCP summaries with
  `INTERVAL_METHODS_COMMON_SUPPORT.csv`; retain native-support values only when
  that support is explicitly required.
- Replace seed-expanded seasonal tables with `SEASONAL_BASELINES.csv`.
- Replace single-seed PLEIA alert tables with
  `CONDITIONAL_ALERTS_PLEIA.csv`.
- Replace partial operational tables with
  `OPERATIONAL_ALERTS_BDG2_H1.csv`, sourced from substantive commit
  `477151c0df4834fa1e26d6fbed260e0155bf5ff6`.
- Replace robustness pilot tables with the three consolidated robustness tables
  sourced from the completed 900-cell extension.

## Remaining work

### Necessary for the approved objectives

- Write and cite the RO1 literature synthesis.
- Use the package's protocol-specific terminology in Chapter 3.
- Select report-sized subsets/figures from the full CSVs without changing the
  underlying comparisons.
- State dependence, units, endpoint and population-inference limitations next
  to the relevant Chapter 4 tables.

### Optional extensions, not candidature prerequisites

- Acquire new independent buildings/periods for population inference.
- Execute complete operational candidate grids for PLEIA or RICO.
- Evaluate additional horizons, natural-fault labels or alternative neural
  architectures/tuning budgets.
- Construct extra owners for exploratory candidates outside the delivered
  zero-fit scope.

No further computation is genuinely necessary to answer the approved RO2 and
RO3 within their validated scope. Remaining necessary work is analysis writing,
literature review, table presentation and disciplined qualification—not new
scientific execution.
