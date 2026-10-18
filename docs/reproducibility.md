# Reproducing results

Reading saved tables and drawing figures are different tasks from training models
or replaying an experiment. Start with the [results index](../RESULTS_INDEX.md)
and follow the evidence record for the study you need.

## Inspect without running an experiment

- [Results index](../RESULTS_INDEX.md): completed scope, limitations and result locations.
- [Candidature evidence package](../review/candidature_evidence_package_20261002_v1/):
  methodology facts, supported findings and consolidated tables.
- [JBE figure package](../report_figures/jbe_operational_20261018/): saved input CSVs,
  captions, checksums and a standalone plotting script.

The figure script redraws saved results; it does not fit models or recalculate
event matches. Its README describes the plotting environment and commands.

## Reproduce a recorded study

Use the source version, locked environment, data checksums, frozen protocol and
argument arrays recorded in that study's evidence index. Keep fresh output
separate from accepted results.

| Study | Evidence and commands |
| --- | --- |
| Matched forecasting | [Completion index](../review/matched_forecasting005_completion_20260923/EVIDENCE_INDEX.md) |
| Interval methods and seasonal benchmark | [Completion index](../review/matched_intervals_seasonal005_completion_20260924/EVIDENCE_INDEX.md) |
| PLEIA energy conditional context | [Five-seed index](../review/pleia_energy_context005_multiseed_20260915/EVIDENCE_INDEX.md) |
| PLEIA temperature conditional context | [Five-seed index](../review/pleia_temperature_context005_multiseed_20260923/EVIDENCE_INDEX.md) |
| Robustness and coverage recovery | [Completion report](../review/robustness_contamination_recovery_20260928/COMPLETION_REPORT.md) |
| BDG2 one-hour operational replay | [Replay index](../review/operational005_causal_replay_20260925/EVIDENCE_INDEX.md) |

Some studies use versioned code in `review/` as well as the reusable package:

- [corrected_validator_v2.py](../review/matched_intervals_seasonal005_completion_20260924/corrected_validator_v2.py)
  retains the independent interval-rank correction and fresh-process import setup;
- [robustness_saved_owner_v1.py](../review/robustness_contamination_recovery_20260928/robustness_saved_owner_v1.py)
  and [validate_saved_owner_v1.py](../review/robustness_contamination_recovery_20260928/validate_saved_owner_v1.py)
  implement and independently validate the frozen saved-owner extension;
- the [operational replay package](../review/operational005_causal_replay_20260925/)
  binds its candidate definitions, saved owners and block validation.

Keep these dependencies at their recorded paths. Their historical launch and
publication scripts describe specific completed deliveries, rather than general
commands for a new experiment.

## Why source identity matters

[unit_checkpoint.py](../smart_building_conformal/src/unit_checkpoint.py) hashes all
Python files under `src`. Checkpoints and protocols use that identity to reject
incompatible resumes. Changes to whitespace, comments or filenames can therefore
invalidate an old source identity even when numerical calculations are unchanged.

A scientific change needs a new execution identity and output directory. For
maintenance that should leave the science untouched, use the source comparison
command in the [development guide](development.md).

## Data and retained evidence

Raw data is obtained separately from the sources listed in the
[repository README](../README.md). Preserve the recorded cohort, memberships,
timestamps, checksums and preprocessing rules.

The repository also retains saved streams, model-owner records, validation
receipts and backup manifests. A file excluded by `.gitignore` may still be
required local evidence. Removing generated caches is different from deleting
an experiment checkpoint or its only saved prediction stream.

The earlier generic `src.run_experiment`, `src.run_study --all` and
`src.run_uci_auxiliary` commands remain available for their original studies.
They are not substitutes for the family-specific completed workflows above.
