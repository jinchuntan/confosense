# Energy sensitivity proposal v1

Status: concrete, separately versioned **proposal requiring scientific adoption**. The historical plan specifies keep/mask sensitivity but no authoritative numerical stalled/zero/catch-up rule was found. This proposal is not historical preregistration. No real mask or sensitivity experiment was executed.

The primary analysis keeps the meter readings, original membership and exposure. A zero can be real low demand. The proposed retrospective stratum is a contiguous run of at least six exactly zero 10-minute readings followed immediately, within the same original continuous segment, by a finite reading strictly above the higher empirical 99th percentile of positive permitted fitting outcomes. At least 400 positive fitting readings are required to define that threshold. The numerical percentile comes only from fitting data; no outer-error search chooses it.

The optional mask removes that zero run and its immediate successor from a separately reported evaluation subset. A zero run without the large successor remains kept and labelled unadjudicated. Nonzero constant readings, delayed successors, negatives and near-zero values are not automatically labelled faults or masked. Those broader stall/catch-up interpretations remain unresolved without source evidence. The pattern is a sensitivity hypothesis, not a meter-fault adjudication or proof of conserved energy.

`energy_sensitivity005.parameters(train, train_ids)` records exact training IDs/value hashes, support and threshold; `stratify(frame, spec)` emits row ID, original group/time, primary keep flag, zero/catch-up flags, mask, reason and specification hash. It refuses an online or retraining specification. Segment gaps and group changes end runs. Nonfinite observations do not form zero runs.

Reports must retain original eligible count/asset-days, masked count, retained count/asset-days and separate numerical availability. Primary workload denominators remain unchanged. Retrospective subset interval scores use only retained finite values; they cannot be substituted for primary coverage or deployment workload.

This rule looks ahead by one observation to identify a successor, so it is **retrospective evaluation stratification**. It does not modify causal features, fill missing readings, recalibrate, refit, or change alert episodes. A causal treatment policy or retraining sensitivity would require a new specification and authorization. Adoption or revision of this proposal is independent of the already specified primary C replay.

Implementation: [energy_sensitivity005.py](../../smart_building_conformal/src/energy_sensitivity005.py). Synthetic provenance, exact threshold boundary, group isolation and denominator tests: [test_context005.py](../../smart_building_conformal/tests/test_context005.py). The current proposal remains unapproved in the readiness map.
