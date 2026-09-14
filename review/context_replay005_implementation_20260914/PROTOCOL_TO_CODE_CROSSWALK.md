# Protocol to implementation crosswalk

| Requirement | Implementation / evidence | Current status |
|---|---|---|
| Frozen four-dataset interval matrix and fold support | `matched_intervals005.scope_policy`; `support_diagnostic.py`; scope crosswalk | Five declared methods implemented; 250/1950 cells executed. Future owners are explicit dependencies. |
| C manifest, exact contexts, roles, schedules and identity crosswalk | `context005_spec`, `context005_data`, `conditional_context005.freeze/readiness` | Implemented. Real source support checked without fitting. |
| Observation-time injection and causal lag/rolling/seasonal/missingness features | `context005_features`; scalar oracle in `context005_validate` | Implemented and synthetic tested at 10-minute and 1-minute cadences. |
| Native static CQR, rolling max-score CQR, raw quantiles, fixed persistence | `context005_owner`; shared serialized controls; `operational004_stream.replay` | Four fixed .95 controls. No new method family or C selection. |
| Independent context initialization, original groups, nulls, aliases, clean controls | `conditional_context005.run/output_variant`; exact feature/owner/variant cache keys | Implemented; original schedule slots remain recorded. Full-stream clean trajectory is separate. |
| Delayed issued/compared/released bounds and scores | `operational004_stream.replay`; independent scalar release in `context005_validate` | Missing readings release no score. No clean truth enters adaptation. |
| Three channels, onset-aware episodes, restricted delay, equal-context strata/macro | `context005_metrics`, `read_event_metrics`; independent validator and hand calculations | Implemented. All 21 strata must meet support; unavailable results remain unavailable. |
| Original exposure and unused tails | Full-stream clean stages, workload CSV and scalar reconstruction | Original support counted once per control/rule/channel, never multiplied by variants. |
| Paired original-unit inference | `context005_metrics.inference` | Interface implemented. Five-seed completeness/support required; single-seed summaries descriptive. Future RICO phase metadata is mandatory for phase-aware inference. |
| Checkpoints, logger adoption, resume | `Stages`, `coordinator.Engine`; coordinator regression tests | Corruption rejected, live workers adopted, known failures stop; completed resume forbids fitting and updates. |
| Energy keep/mask sensitivity | `energy_sensitivity005`; `ENERGY_SENSITIVITY_SPEC.md` | Separately versioned proposed retrospective rule implemented/tested. Adoption unresolved; no real mask applied. |
| First real C unit | Manifest, published contexts/schedules, no-fit readiness, first-run coordinator | Concrete proposal only; no real fitting or replay in this package. |
| Matched forecasting/interval/seasonal remaining scope | Scope crosswalk and updated remaining-work plan | 70/195 forecasting, 250/1950 intervals, 9/27 unique seasonal computations. |
| Natural-frequency A and legacy robustness | Existing operational004 and remaining-study plan | C does not supply primary A feasibility, full BDG2 264-grid execution, calibration contamination, cascades or recovery completion. |

The same `ContextOwner` prediction and calibration-state interface can later accept a separately authorized contaminated calibration pool; composition of sensor transforms can express cascades, and a specified fault-off schedule can define recovery. Those packages need explicit ownership, schedules, matching windows and independent tests. The current single-fault C implementation does not certify those legacy obligations.
