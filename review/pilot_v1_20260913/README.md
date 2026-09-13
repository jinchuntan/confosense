# PLEIA pilot evidence review — 13 September 2026

This folder contains the owner's four uploaded CSVs and completed pilot report, plus an independent reconciliation of those aggregates. It is shared on `review/pilot-evidence-20260913` for subsequent GitHub review. The owner explicitly approved public publication of these four CSVs, the supplied pilot report, review notes and next-task instructions on 13 September 2026. No experiment was run here.

## Source and limits

- Repository base: published repair commit `041714a18e89173eb47da9c5fb2bb27efd2b93cd`.
- At review time main remained `06fe967be2be8d7898812c0c2d6e464d4e942351`.
- The latest local repaired/pilot implementation has not yet been published. The source elsewhere on this branch is therefore an older base, not the evaluated pilot implementation.
- The supplied pilot report identifies frozen implementation commit `d4bc1bc4af7b20d990618df09064ac310809a8ab`, protocol hash `af29d2340427f043c605f777e54389bc86ccbb44c9630aba57964536d0845ce3`, evaluated source hash `965ff02d8cb67183210632bfbc3a2251c430a2b027b8b44d87df356fd19e3d71`, run `pilot_v1_20260913`.
- Those lineage claims are transcribed from the report. They were not independently verified against unpublished source or local checkpoints.
- Scope: PLEIA temperature, one outer fold, seed 42, horizons 10/30/60 minutes, fixed own-model symmetric split-conformal 90%/95% intervals. This does not replace CQR/DSCP/EnbPI or the operational alerting study.

## Files

| File | Role |
|---|---|
| [comparison.csv](comparison.csv) | Nine model/horizon rows, point errors, both interval levels and computational summaries |
| [tuning_results.csv](tuning_results.csv) | Twenty-four inner candidate/fold results |
| [resource_measurements.csv](resource_measurements.csv) | Thirty-six measured computational phases |
| [pleia_preparation_memory.csv](pleia_preparation_memory.csv) | Nine preparation records across execution attempts |
| [MODEL_COMPARISON_PILOT_REPORT.md](MODEL_COMPARISON_PILOT_REPORT.md) | Exact owner-supplied completed report, renamed from the uploaded filename |
| [aggregate_review.json](aggregate_review.json) | Reconciliation checks and computed findings |
| [manifest.json](manifest.json) | SHA-256 hashes of the five supplied files |
| [NEXT_AGENT_TASK.md](NEXT_AGENT_TASK.md) | Local Astra handoff: publish current code, diagnose specific findings, prepare the operational evaluation plan |

## Review findings

The aggregates reconcile after accounting for the report's documented persistence-timing convention: comparison.csv records no tuning work, while raw resource measurements retain empty-branch overhead. Candidate choices match the minimum equally weighted inner MAE; selected LSTM epochs follow the declared ceiling-of-mean rule. Counts, ranks, width/radius identities, throughput and phase measurements agree.

Persistence has the lowest point MAE/RMSE at every pilot horizon. LSTM intervals are wider and have worse Winkler scores than both comparators in every interval cell. Recorded phase totals are 864.3173 seconds for LSTM and 18.0087 seconds for XGBoost, a ratio of 47.99. They exclude preparation, I/O and abandoned partial computation and are CPU measurements.

| Model at 60 minutes | MAE (°C) | Empirical coverage, nominal 95% | MPIW (°C) | Winkler (°C) |
|---|---:|---:|---:|---:|
| Persistence | 0.5481 | 94.02% | 3.2000 | 5.5474 |
| XGBoost | 0.7590 | 88.19% | 2.7936 | 5.3711 |
| Attention-LSTM | 1.2464 | 80.73% | 3.9119 | 10.0489 |

Sixteen of eighteen coverage estimates fall below nominal. This is descriptive, not a significance test. XGBoost's slightly lower Winkler score at 60 minutes/95% does not imply that it achieved 95% coverage. None of these numbers establishes operational alert performance.

The selected LSTM's first/second inner-fold MAE is 0.5010/1.7418 at 10 minutes, 0.7451/1.9241 at 30 minutes and 1.1698/2.2556 at 60 minutes. This supports targeted investigation on the development folds. It does not establish a scaling bug or the cause of temporal degradation.

The preparation CSV records a 2.2857 GiB process peak and a transient minimum of 794,624 bytes (0.758 MiB) available system RAM. Model-phase peak RSS is 681.4 MiB and minimum available RAM there is 2.2422 GiB. Verify the preparation measurement and allocations locally. Do not attribute the earlier interrupted run to memory without evidence.

## What remains unverified here

Only the aggregate CSVs were independently checked. The current implementation, raw per-observation predictions, calibration residuals, actual row identities, fitted models, run manifests, cited test results and original source-data transformations were not inspected. Equal counts are not proof of equal row identities. No uncertainty interval, leakage-free result or full-study readiness is established by this review.

## Continued sharing

Use a separate branch from the latest local implementation for subsequent code and evidence, as described in NEXT_AGENT_TASK.md. Publish a current-evidence index, versioned run paths and hashes after completed work so a reviewer can retrieve them without manual uploads. This does not automatically upload files from the owner's computer: the local coding session must perform that push. Neither this evidence branch nor the next review branch is to be pushed or merged into main.
