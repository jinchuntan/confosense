# Post-results validation-contract amendment v1

This acceptance review adopts `candidate_representation_compatible_v1` from the validation-audit delivery by immutable source identity. It is a separate, review-scoped validator: no file under `smart_building_conformal/src` is changed, and it does not replace or relabel the original frozen `validate` action as passing.

The original action required the saved bounds to equal predictions from independently scalar-reconstructed features. That combined requirement is not satisfiable for the saved HistGradientBoosting estimators: scalar and vectorized causal feature values agree within the unchanged `1e-10` absolute and relative tolerance, but a last-bit difference can cross an exact tree split threshold. The audit traced every such prediction difference to a serialized tree node.

The adopted contract is A ∧ B ∧ C:

- A — independently reconstruct causal observations, feature provenance, values, order, availability, and identities. Saved features are checked against that reconstruction and are not accepted only because their hashes agree.
- B — apply the serialized saved owner to the exact production feature representation that A has verified, and compare the saved point/raw predictions.
- C — independently reconstruct conformal interval construction, causal released-score/update state, alert flags and episode onsets, event outcomes, equal-context summaries, workload, and original-stream exposure.

The candidate retains the frozen `1e-10` tolerances. It executes under `Operations(forbid=True)`: no estimator fit, calibration, experiment replay, rounding, clipping, sorting, or output mutation is authorized. Its only relaxation versus the original frozen assertion is that it does not claim prediction stability under an independently reconstructed, sub-tolerance representation. That limitation, and the split-threshold evidence, remain explicit.

The reproducible commands are in [acceptance_runner.py](acceptance_runner.py). The full action uses the audited source at `review/pleia_temperature_context005_validation_audit_20260919/candidate_validate_v1.py`; its SHA-256 is checked against the audit commit before acceptance evidence is used.
