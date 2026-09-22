# PLEIA-temperature context005 seed-42: validated acceptance

## Decision

**Accepted under post-results A ∧ B ∧ C contract v1.** This is acceptance of the completed PLEIA temperature pilot's saved scientific record under the separately versioned representation-compatible validator. It is not a claim that the original frozen `validate` action passed, and it does not modify `smart_building_conformal/src`, the frozen protocol, the saved model, or the completed pilot tree.

The full current validation passed **271,920 assertions**, with **0 violations**. Its own whole-tree before/after check and the preflight `COMPLETE.json` check both report unchanged scientific artifacts. The validator ran with fitting and calibration forbidden.

## Scope and preserved identity

The accepted record is PLEIA indoor temperature, outer fold 2, horizon 1, model seed 42, 95% confidence, 68 contexts and 2,856 scheduled fault slots. The immutable completion manifest declares 127,161 files. `operations.jsonl` remains 9,201 bytes with SHA-256 `db6b2ad378bad83b29a5d8f1f3839ea431bc4507b71df4475e84b637acfdc9d4`. The frozen source digest remains `a94b3835135749e2f18b89fb6017d8d0b8b9d419cb0a1f9be11122d93d0a217f` and `check_protocol` passed for this temperature design plus the five delivered PLEIA-energy seeds.

## Why the contract changed

The original one-step frozen action conflated independent feature provenance with stability of a discontinuous gradient-boosted-tree prediction under a sub-tolerance numerical representation change. The threshold proof reran on `context_3c2ed441cb78fe67ef35_v0`: scalar/vectorized features differed by at most `1.7763568394002505e-14`, within the unchanged `1e-10` tolerance, while three serialized-tree routing cases straddled exact thresholds. In every case the manual tree walk reproduced sklearn and exactly one boosting stage diverged.

The adopted A ∧ B ∧ C contract therefore verifies: (A) independent causal features, observations, order, availability and identity; (B) serialized-model application to A-verified production features; and (C) interval/release/update state, alerts, events, and workload. It does **not** certify prediction stability under a sub-tolerance representation perturbation. See [VALIDATION_CONTRACT_AMENDMENT.md](VALIDATION_CONTRACT_AMENDMENT.md).

## Rejection evidence

All nine focused disposable-sandbox cases passed: one unmodified acceptance plus rejections for feature, observation, prediction/model application, interval, rolling update, alert flag, released-score and serialized-model corruption. Nothing in the genuine pilot tree was altered.

## Scientific limitations retained

Rolling CQR clean-stream coverage is **0.9081**, below nominal 0.95 by 0.0419; that finding is retained, not repaired away. Persistence does not dominate every detection/workload trade-off. This is a single-model-seed descriptive pilot, so population bounds are unavailable. No energy uncertainty bounds are transferred to temperature. The explicit [inference-status table](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/INFERENCE_STATUS.csv) records why no population interval is available and why the blank inference export is intentional.

## Direct summaries

- [Conditional control/rule/channel macro summary](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/ACCEPTANCE_CONDITIONAL_MACRO.csv)
- [Full clean-stream workload summary](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/ACCEPTANCE_FULLSTREAM_WORKLOAD.csv)
- [Preserved blank inference export](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/ACCEPTANCE_INFERENCE.csv) (no population interval is estimated)
- [Inference-status table](../../smart_building_conformal/outputs/conditional_context005/pleia_f2_s42_C_v1_validated_acceptance_v1/INFERENCE_STATUS.csv)

## External-backup recovery proof

The acceptance sequence was restored into an empty temporary Git repository using only local external bundles: a self-contained `c143fa16` base, the existing full audit archive, a small audit-receipt delta, the existing primary-acceptance delta, and a delivery delta. The restored tip was exactly `18d8dd15d06459b3b54ba629e9948b78494f4c8f`; the temporary repository had no remotes or object alternates, and `git fsck --full --no-dangling` passed. The complete scoped receipt is [EXTERNAL_BACKUP_RECOVERY_RECEIPT.json](EXTERNAL_BACKUP_RECOVERY_RECEIPT.json).

The operational receipts and evidence index are linked from [EVIDENCE_INDEX.md](EVIDENCE_INDEX.md).
