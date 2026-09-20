# Candidate validation contract v1

Status: **candidate, not adopted.** It does not replace the frozen `validate` action and does not waive any scientific gate. It is implemented on the audit branch and imports `src` without modifying it.

## What the frozen validator asserts

The frozen validator asserts, in a single step, that the saved bounds equal those obtained by applying the saved model to a feature vector reconstructed **independently of the engine**. Call this A'.

A' silently conflates two claims, and is **unsatisfiable** on this data: a gradient-boosted tree ensemble is piecewise constant, so a sub-tolerance change in an input can change the output by an arbitrary amount. Demanding agreement of a discontinuous function under a 1-ULP perturbation is not a strict test; it is an impossible one.

## What the candidate asserts

| layer | claim | how |
| --- | --- | --- |
| **A** | Provenance: the saved production features are what the declared causal construction produces from the raw source | independent scalar reconstruction (no production `causal_features`/`inject`/pandas rolling) compared at the UNCHANGED 1e-10 tolerance, plus saved `feature_hash` and `observation_hash` identity |
| **B** | Model application: the saved model reproduces the saved predictions from the exact verified production representation | direct estimator application to the verified saved features |
| **C** | Downstream: calibration, causal release/update state, interval construction and alert outcomes | independent scalar re-derivation from that verified representation |

Saved features are therefore **never** trusted as inputs: layer A establishes their provenance before layer B consumes them.

## Precisely how the contract differs

A ^ B ^ C is strictly weaker than A' in exactly one respect: it does not certify that a prediction is **stable** under a sub-tolerance perturbation of the features. Everything else the frozen validator checks is retained, at the same tolerances.

## What it can detect

- Wrong or tampered causal features, including ones that would pass a coarse eyeball check (layer A, demonstrated at 0.5 degC).
- Tampered observations (layer A).
- A substituted or perturbed model, even when every saved output is left untouched (layer B, demonstrated at 0.05 degC on a baseline).
- Tampered predictions, interval bounds, released scores, rolling corrections, update status and alert flags (layers B and C).

## Remaining limitations, stated plainly

1. **Perturbation stability is not certified.** The audit quantifies what this gives up rather than hiding it: 98 stages and 145 rows out of 2151 x 144 would predict differently under the independent reconstruction, every one attributable to a split threshold.
2. **Common-mode error is not excluded.** If the declared causal construction were itself wrong, and the independent scalar reconstruction reproduced the same wrong value, layer A would pass. The scalar path is deliberately written without the production helpers, which mitigates but does not eliminate this.
3. **It does not re-derive the model.** No validator here refits; the saved estimators are taken as the object under test, and their identity is checked by hash elsewhere in the pipeline.
4. **Single seed.** Nothing here changes the fact that population intervals remain unavailable for this setting.

## Why this was NOT implemented inside `src`

The repository provides `validation_source_compatible()` for exactly this kind of post-completion validator repair. The audit assessed it and did **not** use it, for two concrete reasons:

1. **It mandates a two-file change set.** The check requires the changed set to equal exactly `{conditional_context005.py, context005_validate.py}`. A repair confined to the validator (`context005_validate.py` alone) would FAIL the mechanism, forcing an otherwise unnecessary edit to a second file purely to satisfy a hash-exact gate.
2. **Blast radius.** `source_digest()` covers all of `src`. 88 protocol files in this repository pin a source hash, and all five completed PLEIA-energy seeds pin the identical `a94b3835135749e2...` as this temperature pilot. Editing `src` would invalidate `check_protocol` for the delivered energy study as well, and each affected design would need its own compatibility receipt before it could be re-validated.

Adopting the candidate into `src` is therefore a separate, explicit decision with consequences beyond this pilot. It is proposed, not taken.
