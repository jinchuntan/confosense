# Prepared dissertation wording: benchmarking position and ConfoSense contribution

Drop-in prose for Chapter 6 (§6.6, §6.7) and Chapter 3 (§3.2), with the
supporting evidence named. Adjust citation style to the UM template; do not
change the numbers or weaken the qualifications.

---

## 1. Benchmarking position (Chapter 6.6)

### 1.1 Prepared wording

> Comparative evidence in this study is drawn from two levels, and the two are
> deliberately not merged.
>
> The **primary comparative evidence is a controlled internal benchmark**. All
> candidate methods — four point forecasters, five prediction-interval methods,
> four alert-aggregation rules and three recalibration strategies — were
> implemented within the same framework and evaluated on identical partitions,
> with identical features, seeds, forecast horizons and metric definitions.
> Because the experimental setting is held constant, any difference between two
> arms is attributable to the method rather than to the conditions under which it
> was measured. This is the only comparison in the study from which relative
> performance conclusions are drawn.
>
> The **published literature is used as contextual evidence**. Each of the twelve
> benchmark studies reviewed in Chapter 2 was classified according to whether a
> direct numerical comparison with the present results would be legitimate,
> requiring agreement on dataset, target variable, forecast horizon, partitioning
> scheme and metric definition simultaneously. **None of the twelve studies
> satisfied all of these conditions**: seven were classified as partially
> comparable, contributing a method, a protocol convention or a metric
> definition, and five as contextual only, contributing motivation, dataset
> documentation or design rationale. The classification is recorded in full in
> `combined/literature_benchmark_matrix.csv`.
>
> Consequently, **this dissertation makes no claim of numerical superiority over
> any published study**. Where prior work is cited alongside a result, it is cited
> as the source of a method, as corroboration of a design decision, or as
> evidence that a phenomenon has been observed elsewhere — never as a baseline
> that the present results outperform. Reporting a lower error than a published
> figure obtained on different buildings, at a different horizon, under a
> different partitioning scheme would not be a finding; it would be a category
> error.

### 1.2 Permissible and impermissible formulations

| Permissible | Impermissible |
|---|---|
| "EnbPI (Xu & Xie, 2023) and DSCP (Yu et al., 2025) were reimplemented and evaluated under a single protocol alongside CQR and an uncalibrated baseline; under that protocol no method dominated across datasets." | "ConfoSense outperforms EnbPI and DSCP." |
| "The coverage shortfall observed here is consistent with the difficulty reported by Zhang et al. (2024) for building energy targets." | "ConfoSense achieves better coverage than Zhang et al. (2024)." |
| "Our alerting design follows the operating-point framing used by Nguyen et al. (2025)." | "Our alert F1 exceeds that of Nguyen et al. (2025)." |
| "No reviewed study reported results under conditions directly comparable to ours." | "Our results are state of the art." |

### 1.3 Supporting evidence

* `combined/literature_benchmark_matrix.csv` — 12 papers, 0 DIRECTLY_COMPARABLE,
  7 PARTIALLY_COMPARABLE, 5 CONTEXTUAL_ONLY
* `report/benchmark_comparison.md` — full internal benchmark and the classified
  matrix with per-paper reasoning

---

## 2. What ConfoSense is (Chapter 3.2 and Chapter 6.7)

### 2.1 Prepared wording

> ConfoSense is **a configurable uncertainty-aware monitoring framework for
> smart-building sensor and energy data**, not a new forecasting algorithm. It
> specifies a pipeline and, equally importantly, a decision procedure for
> instantiating that pipeline on a given target. Defining ConfoSense as a
> particular model — "XGBoost with conformalized quantile regression", for
> instance — would misstate what the evidence supports, because neither of those
> components is the best choice on all four targets evaluated here.
>
> The framework comprises six components:
>
> 1. **Data preparation.** Group-safe supervised windowing that never allows a
>    window to straddle an experimental run or a building, with direct
>    horizon-specific models rather than recursive feeding, and documented,
>    performance-blind rules for target and subset selection.
> 2. **Point forecasting.** A declared candidate set — persistence, seasonal
>    naive where a full seasonal cycle exists, gradient-boosted trees and an
>    attention-based recurrent network — in which the naive baselines are
>    mandatory rather than optional.
> 3. **Conformal calibration.** A declared candidate set of interval methods —
>    conformalized quantile regression, a recentred EnbPI adaptation in static
>    and sequentially updated forms, and dual-splitting conformal prediction —
>    always reported against an uncalibrated quantile baseline so that the
>    contribution of calibration is measured rather than assumed.
> 4. **Interval-based alerting.** A k-of-m persistence rule over interval
>    violations, with the operating point frozen under a stated false-alert
>    budget on a block of calibration data that the conformal quantile has not
>    seen.
> 5. **Robustness evaluation.** A catalogue of injected disturbances evaluated in
>    two modes — a conventional fixed-interval mode and a closed-loop mode in
>    which the disturbance enters the model's own feature history — with
>    observed-signal and clean-reference metrics reported separately.
> 6. **Recalibration.** Static, periodic and rolling strategies whose parameters
>    are chosen by a calibration replay with a horizon-length embargo, and which
>    never consume a residual before its ground truth has arrived.

### 2.2 Why the evidence does not support one universal configuration

> The study evaluated one framework on four targets and found that **every
> configurable component resolved differently across them**. The best point
> forecaster was persistence on PLEIAData indoor temperature at all three
> horizons and gradient-boosted trees on both energy targets and on the RICO HVAC
> temperature. The best-calibrated interval method was conformalized quantile
> regression on PLEIAData temperature and the sequentially updated recentred
> EnbPI on the other three targets. The alert rule frozen by the selection
> procedure differed on all four targets. The best recalibration strategy was
> rolling on the two PLEIAData targets and periodic on RICO and BDG2.
>
> Reporting a single "ConfoSense configuration" would therefore require
> discarding the evidence from three of the four targets. The framework's
> contribution is the procedure by which a configuration is obtained and
> validated, not the configuration itself.

Evidence: `combined/confosense_configurations.csv`,
`report/final_confosense_configuration.md`, `combined/point_metrics.csv`,
`combined/interval_metrics.csv`, `combined/alert_metrics.csv`,
`combined/recalibration_metrics.csv`.

### 2.3 A recommended default, stated as a default

> Where no target-specific calibration evidence is yet available, a defensible
> starting configuration is: fit both persistence and gradient-boosted trees and
> retain whichever performs better on calibration data; use the sequentially
> updated recentred EnbPI as the conformal layer, which was best calibrated on
> three of the four targets studied; begin operating-point tuning from a 2-of-3
> or 3-of-5 rule; and apply periodic recalibration. Each of these is a default to
> be re-selected on the deployment target's own calibration data, not a validated
> optimum.

---

## 3. Separating adopted methods from this dissertation's contribution

### 3.1 Adopted from the literature

| Component | Source |
|---|---|
| Split conformal prediction, conformalized quantile regression | established conformal literature; implemented via MAPIE |
| EnbPI (ensemble batch prediction intervals) | Xu & Xie (2023) |
| Dual-Splitting Conformal Prediction | Yu et al. (2025), arXiv:2503.21251 |
| Gradient-boosted trees, attention-based recurrent forecasting | standard forecasting practice |
| Winkler score, empirical coverage, Diebold–Mariano with HLN correction, Friedman with Holm-corrected post-hoc | standard evaluation and statistics literature |
| PLEIAData, RICO, BDG2 datasets | Ibarra et al. (2023), Thiry et al. (2025), BDG2 |

### 3.2 Contribution of this dissertation

> This dissertation does not propose a new forecasting algorithm or a new
> conformal predictor. Its contribution is threefold.
>
> **Methodological.** A leakage-safe procedure for selecting an alerting
> operating point. Existing practice scores candidate alert rules against
> intervals produced by the model conformalized on the same calibration sample,
> so the violation rates driving the choice are not out-of-sample. The procedure
> introduced here splits the calibration period chronologically inside itself: an
> earlier block conformalizes a separate selection model and a later block scores
> the rules, with a window admitted to the later block only if its forecast
> origin strictly postdates every conformal target time. Adopting it changed the
> selected rule on two of four targets, and showed that the pooled procedure had
> understated the false-alert workload by roughly a factor of four on one of them.
>
> **Experimental.** A controlled cross-dataset comparison in which four point
> forecasters, five interval methods, four alert rules, three recalibration
> strategies and fifteen disturbance scenarios under two evaluation modes were
> evaluated on four heterogeneous targets from three public datasets under
> identical partitions, features, seeds and metric definitions, with full
> provenance and a reproducibility record.
>
> **Applied.** A dual-mode robustness evaluation that distinguishes
> observed-signal from clean-reference metrics and demonstrates that conventional
> fixed-interval evaluation misstates the fault sensitivity of an interval-based
> monitor, because an autoregressive forecaster absorbs a sustained sensor bias
> into its own inputs.

Evidence: `report/alert_selection_audit.md`,
`<dataset>/metrics/alert_selection_split.csv`, `combined/` (20 tables),
`manifests/stage_provenance.json`, `combined/robustness_metrics.csv`,
`report/closed_loop_terminology.md`,
`report/figures/fig_13_closed_loop_absorption.png`.

### 3.3 Boundaries of the contribution — write these explicitly

* The framework is not claimed to be optimal, only to be complete, controlled and
  reproducible.
* The leakage-safe selection procedure is not claimed to improve test
  performance; it improves the *validity* of the selection, and on one target it
  produced a worse test operating point.
* The closed-loop finding is established for the injected disturbance catalogue,
  not for real building faults.
