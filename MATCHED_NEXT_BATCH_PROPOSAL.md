# Proposed next matched batch: twelve fixed units

14 September 2026. **Proposal only; no additional fitting authorization and no batch launch.** The two newly authorized units completed. The generalized runner has no demonstrated unresolved implementation blocker for these matched units. Pending execution is distinct from the unimplemented broader interval/operational obligations.

Select the earliest three still-pending keys for each dataset from the unchanged published queue, then retain their original queue order. This balances all four settings while broadening horizon/fold coverage, uses seed42 as declared in that queue, and does not use model rankings, error sizes or coverage to select work. Five-seed inference remains pending.

| batch_order | original_priority | dataset | horizon | outer_fold | model_seed | fit_n | updated_low_model_seconds | updated_high_model_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 4 | pleia_energy | 1 | 2 | 42 | 14858 | 106.623 | 639.74 |
| 2 | 5 | pleia_energy | 3 | 2 | 42 | 14855 | 106.602 | 639.611 |
| 3 | 6 | pleia_energy | 6 | 2 | 42 | 14850 | 106.566 | 639.396 |
| 4 | 48 | rico | 15 | 2 | 42 | 12322 | 77.8939 | 467.363 |
| 5 | 49 | rico | 30 | 2 | 42 | 11407 | 72.1097 | 432.658 |
| 6 | 50 | rico | 60 | 2 | 42 | 9577 | 60.5413 | 363.248 |
| 7 | 107 | bdg2 | 3 | 2 | 42 | 51634 | 769.337 | 4616.02 |
| 8 | 108 | bdg2 | 6 | 2 | 42 | 51584 | 768.592 | 4611.55 |
| 9 | 109 | bdg2 | 1 | 1 | 42 | 77682 | 1157.45 | 6944.68 |
| 10 | 151 | pleia | 1 | 2 | 42 | 14858 | 55.9555 | 513.013 |
| 11 | 152 | pleia | 3 | 2 | 42 | 14855 | 55.9442 | 512.909 |
| 12 | 153 | pleia | 6 | 2 | 42 | 14850 | 55.9254 | 512.737 |


Exact scope: **12 paired units, 96 tuning + 24 final =120 learned fits, 36 point and 72 interval cells**, with persistence/XGBoost/Attention-LSTM, both own-model 90%/95% split-conformal levels and unchanged candidates. Each row's exact planned output/argv and prerequisites are in [next_batch_units.csv](smart_building_conformal/outputs/matched_forecasting005/rico_bdg2_report_v2/next_batch_units.csv). These bare run argv require the prior freeze/readiness steps below.

## Measured timing and resource assumptions

Each proposed unit uses its own dataset's measured model-phase seconds per final-fitting row, scaled by that unit's fixed fit count. For temperature, use the min/max rates across its three measured horizons; other settings currently have one measured unit. Retain the explicit [.5,3] planning factors. This gives **56.56–348.22 model-minutes** for this batch. These are scheduling scenarios, not statistical bounds, deadlines or wall-time promises; they exclude preparation, serialization/I/O, validation/resume, changing epochs and channel/history costs. No operational HistGradientBoosting/CQR timing is used.

| dataset | horizon | outer_fold | model_seed | fit_n | model_phase_seconds |
| --- | --- | --- | --- | --- | --- |
| bdg2 | 1 | 2 | 42 | 51664 | 1539.57 |
| pleia | 1 | 0 | 42 | 29719 | 342.043 |
| pleia | 3 | 0 | 42 | 29715 | 316.536 |
| pleia | 6 | 0 | 42 | 29710 | 223.777 |
| pleia_energy | 1 | 0 | 42 | 29719 | 426.537 |
| rico | 5 | 2 | 42 | 12932 | 163.5 |


The updated full remaining core queue scenario is **18.96–116.76 model-hours**; broader methods are excluded. Preserve actual per-unit phase measurements instead of treating a row-scaled estimate as evidence.

For the two new units, measured preparation, validation/resume and lifetime peaks are:

| dataset | command_seconds | preparation_seconds | validation_seconds | resume_seconds | lifetime_peak_rss_MiB | output_bytes | audit_bytes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rico | 183.966 | 9.97719 | 29.741 | 27.2861 | 621.879 | 9176401 | 10519 |
| bdg2 | 1587.35 | 14.9093 | 45.1975 | 24.6434 | 983.934 | 34653755 | 10609 |


The larger of these lifetime peaks is **983.9 MiB**. Budget approximately **1475.9 MiB** per active process as a planning allowance, not a new blocking launch rule or a guarantee. Run one experiment at a time, with lazy batch256 and one numerical/Torch thread. Preserve the nonblocking 3 GiB available-RAM reference, 256 MiB epoch floor and 8 GiB free-disk check. Retain actual available RAM, disk and process peaks at every unit.

The largest new run plus audit occupies **33.1 MiB**. A conservative twelve-unit storage allowance of twice that size per unit is **0.77 GiB**, excluding source data and any backup/publication duplication; verify free disk before the batch and each unit. Allocation/I/O failures require preserved evidence and correction, never a smaller scientific cohort/grid.

## Exact execution package after separate authorization

1. Create a new authorization listing exactly the twelve CSV keys. Freeze all protocols with current source/config/package/data/role identities and the unchanged original memberships; select unused output versions. Pass fresh no-fit readiness and commit the evaluated code plus joint manifest before any fit. The authorization in this completed task continues to allow only RICO h5/f2/s42 and BDG2 h1/f2/s42.
2. For each row in CSV order, run `src.matched_forecasting005 run` through `scripts/log_pilot_command.py`, passing its frozen `--design-dir` or explicit protocol/readiness. The CLI already exists; no second runner or model redesign is required.
3. Persist one atomic checkpoint per model. On interruption, explicitly resume under the same source/config/data identity and reuse complete models; mid-fit recovery is not available. Keep failed logs and incomplete attempts. Never rerun a valid complete fit for improved scores.
4. Before advancing, require actual exit0, 8 tuning/2 final learned fits, independent 3-point/6-interval arithmetic, six fitted-artifact prediction checks, original-group summaries and zero-fit completed resume with all run files unchanged. Publish incremental evidence at sensible completed-unit boundaries.
5. Stop for an unresolved source/config/data/role mismatch, checkpoint corruption, failed arithmetic/artifact check, nonfinite model output, actual allocation failure, epoch-floor failure or disk guard failure. Preserve completed checkpoints. Disappointing rankings, missed nominal coverage, an exceeded timing scenario or a sub-3-GiB launch reading alone are not stop conditions.

This proposal does not launch seasonal, full interval methods/DSCP, injected-fault selection, recalibration, conditional challenge or robustness experiments. Those remain separately scoped implementation/execution obligations.
