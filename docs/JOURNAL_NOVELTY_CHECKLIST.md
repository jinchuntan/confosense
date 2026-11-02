# Journal novelty and evidence checklist

Updated: 2 November 2026. Project: ConfoSense. Continuation of “Verify paper data”.

The current submission plan for the stuck-sensor paper is the [prioritized checklist in the paired replay report](../experiments/injection_feedback_20261102/README.md#submission-checklist). The entries below record the earlier matched-workload study and its original research question.

## Scientific objective

Establish a specific, useful finding about when calibrated uncertainty improves
building alert decisions beyond simpler threshold choices. A collection of known
forecasting, conformal and aggregation methods is not sufficient evidence of
novelty. Neither a larger benchmark nor clearer wording alone establishes it.

Candidate research question, subject to the literature audit and experiments:

> Under alert budgets selected using historical data, when do conformal interval
> choices improve event detection and delay over simple residual and quantile
> thresholds, and when do drift, contamination and aggregation remove that benefit?

This is a candidate empirical contribution, not a claim that budget-constrained
alarm evaluation, CQR, online calibration or onset detection was invented here.
Publication and journal acceptance cannot be guaranteed by completing a checklist.

## Recovered state

- [x] Resolve the existing manuscript, current candidature report and repository.
- [x] Recover experiment branch `experiment/matched-workload-20261102`, code commit
  `81207315c91c3d60fcc543fb58e6a65111be0199`.
- [x] Locate all fifteen BDG2 run completion records (three periods, five seeds,
  ten buildings from six sites).
- [x] Identify an event-file checksum failure in `f2_s43`; retain the original
  failed evidence and rerun that unit using the unchanged scientific source,
  protocol and raw data. See `RECOVERY.json` in the experiment directory.
- [x] Preserve the historical manuscript evidence and its existing result claims.
  The new HGB follow-up is separate from the original XGBoost/Attention-LSTM
  comparisons and is not an exact reproduction of manuscript Table 6.
- [x] Complete the independent reconstruction audit: 15 units, 2,065,350
  workload/event checks, 225 score-equivalence checks and eleven unit tests.
  The pilot does not establish a general CQR advantage. See the experiment's
  `PILOT_REPORT.md`, `results_v1/summary.csv` and `results_v1/VALIDATION.json`.

## Code and experiments, in order

| ID | Status | Work | Evidence required to close it |
| --- | --- | --- | --- |
| C1 | Implemented; audited in BDG2 pilot | Keep the predictor, buildings, timestamps and fault catalogues identical across the four BDG2 detector choices. Include raw intervals, scaled quantiles, symmetric CQR and a seasonal residual baseline. | Saved prediction identities, shared support, selected policies and complete method/budget results. |
| C2 | Implemented; audited in BDG2 pilot | Select thresholds on a separate historical selection stream for 0.25, 0.5 and 1 episode/asset-day, with an active-time limit. Freeze policies before test replay. | Selection surfaces and hashes. Report actual test workload and time in alert; the validation budget does not guarantee equal test workload. |
| C3 | Implemented and unit-tested | Explicitly test symmetric CQR against thresholding its identical maximum nonconformity score. | Exact flag equality, including negative corrections/empty sets. Equality is a control, not a distinct algorithm or evidence of superiority. |
| C4 | Implemented; audited in BDG2 pilot | Rebuild features from corrupted past observations; separate numerical alerts from missing-reading flags; score new episode onsets only. | Independent reconstruction from emitted flags; miss penalties; event counts by family/severity; uninjected-window negative control. |
| C5 | Pending | Complete fair component ablations: calibration on/off, aggregation 1-of-1/3-of-3 and updating on/off, with consistent score definitions. | Change one component at a time. Include simple threshold baselines at each relevant setting. Prevent a change of interval construction from being described as an updating benefit. |
| C6 | Pending | Test contamination and operating-regime changes using a fixed, prespecified protocol and delayed updates. | Workload, recall, delay and coverage through time; recovery and failure cases; matched score/buffer/update controls. Improved coverage alone does not demonstrate improved detection. |
| C7 | Pending | Freeze a prospective extension before inspecting new outcomes: additional previously uninspected BDG2 buildings/sites, and temperature/energy alert tasks where the design transfers. | A committed selection rule, exclusions, split membership, budgets, primary comparisons and failure criteria. Previously inspected periods remain retrospective evidence. |
| C8 | Pending | Strengthen uncertainty estimates and sensitivity analysis without treating seeds, event catalogues or timestamps as independent buildings. | Paired site/building results, event counts, descriptive clustered intervals, and sensitivity to incidence, duration, severity and matching tolerance. Six pilot sites are insufficient for broad guarantees. |
| C9 | Pending | Reproduce relevant published baselines after reading their full methods and checking available implementations. | A baseline specification and deviations table. The current seasonal-residual comparator is an explicit simple baseline, not a reproduction of Takahashi et al. |
| C10 | Pending | Package the full study for independent regeneration. | Pinned dependencies, data/source hashes, code/protocol identities, run command, emitted flags/catalogues, tables and a claim-to-file manifest. Raw source datasets are not republished. |

Infrastructure, tests and reproducibility make the evidence trustworthy. They are
not, by themselves, the paper's scientific novelty.

## Report and manuscript

| ID | Status | Required change | Acceptance check |
| --- | --- | --- | --- |
| M1 | Initial search complete; full audit pending | Build a closest-work comparison focused on decision rules, threshold selection, event aggregation, adaptation, workload, delay and validation. | Read full papers before asserting what they omit. Identify one precise unresolved question rather than claiming forecasting-plus-conformal-plus-alerts is new. |
| M2 | Pending | Rewrite the gap, research questions and contribution statements around the supported finding. | Each claimed contribution names the missing knowledge, the experiment that tests it and the evidence supporting it. Distinguish methodological invention from empirical insight. |
| M3 | Pending | Explain the new protocol and distinguish it from the submitted experiment. | HGB versus the original predictors, new split roles, retrospective cohort reuse, candidate selection, episode definitions, missing flags, tolerance and miss penalty are explicit. |
| M4 | Pending | Make operational comparisons central to the results. | Plot recall against achieved episode rate and time in alert; report restricted delay, all budgets, paired building/site effects and failure cases. Do not claim equal workloads merely from equal validation targets. |
| M5 | Pending | Replace unsupported language throughout the abstract, highlights, discussion and conclusion. | “Background workload” is not “verified false alarms”; injected sensor disturbances are not maintenance-confirmed equipment faults; observed recall is not proof of noninferiority; operator-time/cost/alarm-fatigue savings remain unmeasured. |
| M6 | Pending | Reconcile every table/figure and its inference with generated outputs. | The existing 25.53% comparison remains a fixed-nominal-coverage, same-aggregation result. It does not establish an advantage over a tuned threshold detector. Keep prospective and retrospective results separate. |
| M7 | Pending | Align the candidature report with the journal evidence without changing approved research-objective mappings casually. | Methods, sample counts, metric definitions, limitations, references, appendices and evidence versions agree. Thesis breadth need not dictate the journal's main narrative. |
| M8 | Pending | Produce the submission and reviewer-response evidence map. | Every reviewer point is quoted from the actual decision and linked to a change/result. Verify the target journal's current author instructions and evidence release. The manuscript PDF is not the decision letter. |

## Initial closest-work screen

The following is a screening record, not a completed systematic review. Abstracts
and official publication/author pages were checked on 2 November 2026. Full-method
comparison is still required. These references are background for the novelty
audit; conference papers/preprints are identified as such and do not replace any
UM requirement for recent journal references. No MDPI sources are used here.

| Work | Existing overlap established by the source | Consequence for our claim |
| --- | --- | --- |
| Stjelja, Kuzmanovski, Kosonen, and Jokisalo (2024), *Building consumption anomaly detection: A comparative study of two probabilistic approaches*, Energy and Buildings, 313, 114249. DOI: 10.1016/j.enbuild.2024.114249. | Building-energy forecasting, EnbPI, an alarm matrix, detection tradeoffs and robustness. | Integration and alarm aggregation are established prior art. Compare the operational question and experimental controls directly. |
| Martinez Gil et al. (2026), *Adaptive Conformal Anomaly Detection with Time Series Foundation Models for Signal Monitoring*, ICLR 2026. | Adaptive conformal anomaly scores and weighted calibration under changing distributions. | Adaptation and conformal anomaly monitoring alone cannot be claimed as new. |
| Xu and Boström (2026), *Conformalized Time Series Anomaly Thresholding with Latent Space Features*, PMLR, 329, 676–688. | Calibration-only threshold selection addressing evaluation leakage. | Leakage-safe threshold selection is an essential control, not an adequate standalone novelty claim. |
| İşcanlı and Sabucu Sandal (2026), *CALM-5G: Event-Level Conformal Risk Control for Predictive Service-Assurance Alarms*, October preprint, under review. DOI: 10.48550/arXiv.2610.17962. | Event-level missed-event control, alarm occupancy, chance controls and out-of-sample calibration-scheme selection in communications. | Event-level evaluation and workload-aware conformal alarms also have adjacent-domain prior art. A building-specific result must add knowledge beyond a domain rename. |

## Decision before submission

- [ ] The closest-work audit supports a clearly stated contribution.
- [ ] Strong simple baselines and relevant published comparators have been tested.
- [ ] Benefits survive fair workload/occupancy comparisons or their limits are
  themselves established convincingly across independent settings.
- [ ] At least one prespecified extension tests the conclusion on outcomes that
  were not used to design the method or write its narrative.
- [ ] Any newly proposed mechanism is justified by an identified gap and tested
  against its nearest existing alternatives. Do not add complexity merely to
  rename known methods or to obtain a favourable table.
- [ ] If no useful benefit survives, revise the contribution honestly, investigate
  the failure mechanism, or develop and validate a materially different approach.
  Do not claim guaranteed novelty or tune repeatedly on the same test set.
- [ ] All claims, limitations and source artifacts are consistent and reviewable.

Primary source locators for the screening record:

- https://research.aalto.fi/en/publications/building-consumption-anomaly-detection-a-comparative-study-of-two/
- https://proceedings.iclr.cc/paper_files/paper/2026/hash/f54c9fc57aa6e1c72400cc127917fcf8-Abstract-Conference.html
- https://proceedings.mlr.press/v329/xu26a.html
- https://iscanli.com/papers/calm-5g/
