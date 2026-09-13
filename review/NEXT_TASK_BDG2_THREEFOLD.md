# Next task: complete the three-fold BDG2 reduced-grid benchmark

13 September 2026. This handoff follows the completed BDG2 operational pilot at `d63251b75f5c70c4d51c19456fbec6724e712516`.

## Goal and authorization

When the user supplies this handoff to the local coding agent, implement the confirmed checkpoint memory repair, verify compatibility with the preserved completed unit without fitting, then execute the two remaining BDG2 outer folds under the identical nine-candidate pilot design. Finish a three-fold, seed-42 reduced-grid benchmark and publish the evidence on a new review branch.

This replaces the previous maintenance-only next step with a concrete research milestone. Complete both phases without asking the user to authorize each routine step again. A failed integrity check, unresolved scientific discrepancy, or inadequate measured resources is a real reason to stop; a disappointing valid result is not.

Use the latest local descendant of `review/bdg2-operational-pilot-20260913`, recording its relationship to d63251b. Preserve later local work if present. The instruction branch `review/pilot-evidence-20260913` has older code beneath its review files: read this document using git show; do not check out or merge that old source over the current implementation. Preserve main, existing review branches, historical runs, protocols and external backups. Publish to `review/bdg2-threefold-20260913` or a clearly named unused review branch; no main updates or force pushes.

## What the existing pilot establishes

Read `BDG2_OPERATIONAL_PILOT_REPORT.md` and `review/bdg2_operational_pilot_20260913/EVIDENCE_INDEX.md` at the current source branch.

- Fold 2, model seed 42 completed with nine candidates, two inner folds and five catalogue seeds.
- Primary selection abstained. Rolling CQR's inner-0 workload UCB is 1.000161467488, which exceeds the unchanged ceiling of 1.0. Its separate inverse-objective selection is not primary feasibility.
- Static CQR versus the same uncalibrated quantile fit produced outer coverage 95.11% versus 88.24%, clean workload 1.032 versus 1.604 episodes/asset-day, and macro recall 79.19% versus 84.07%. That is a workload/recall trade-off, not equal-recall superiority.
- Hourly temporal aggregation strongly reduced both workload and recall. Treat its 3-of-3/4-of-6 durations as actual operational choices, not evidence of a software defect without further proof.
- The current source shows `checkpointed_unit` calling `load` and then `require_complete`, which calls `load` again. The original measured resume peak was 4.422 GiB; its exact reducible component is not yet measured.
- These are ten known buildings, synthetic faults, one model seed and one outer fold. The operational predictor is the CQR-owned quantile model, not the separately benchmarked Attention-LSTM or point XGBoost.

## Phase A — memory repair and unchanged-result verification

1. Separate checkpoint completeness/provenance/file-hash verification from CSV materialization. Use a hash-only second verification in the completed-unit path and avoid reloading all computed frames merely to verify a newly saved checkpoint. Preserve existing consumers' required semantics.
2. Keep missing/incomplete/corrupt units, wrong unit keys, provenance mismatches, duplicate/missing experimental cells and damaged payload/frame files detectable. Do not remove checks to obtain a lower memory measurement.
3. Test the confirmed allocation defect and compatibility with focused tests. In particular, verify that completeness checking does not parse CSVs and an ordinary completed-unit read materializes each required frame only once.
4. Read the preserved fold-2 checkpoint using a clearly identified read-only compatibility verifier. Record both the historical evaluated-source identity and the new reader-source identity. A changed source hash must not be hidden: do not rewrite its manifest, impersonate the old code, or bypass the production training-resume identity guard. New experiments will have their own new source hashes.
5. Forbid all fitting/computation routes during the compatibility check; compare every scientific payload/frame value, original file hash and the existing primary/inverse decisions with the preserved evidence. Retain the original 30 unit files unchanged.
6. Measure wall time, process peak RSS and available RAM using the same scope as the historical resume. Label the comparison as a measured run on the current machine; do not promise a particular percentage reduction. If comparable before/after verification is needed, use isolated processes and keep the original source available. Do not repeat the previous PLEIA preparation-memory study.
7. Commit the implementation and verification before fitting. If memory remains unsafe, resolve the demonstrated allocation issue and rerun the no-fit check before proceeding.

## Phase B — two additional real-data units

Run BDG2 outer folds **1 and 0**, model seed **42**, sequentially in that order, retaining the completed fold-2 result. Existing fold IDs run backward in time: do not relabel fold 0 as the earliest fold.

Before either new fit, save a single execution/analysis manifest covering BOTH new units and the combined three-fold report. Freeze:
- the exact same nine candidate IDs/settings as fold 2;
- all ten retained buildings, one-hour horizon and existing targets/features;
- five catalogue seeds 42–46 for every unit, with existing role/fold namespaces;
- unchanged amendment-004 membership rules, training-only preprocessing, two inner folds and reserved final calibration;
- 95% operating intervals; static uncalibrated and CQR, and CQR rolling every 12 origins with window 200; the existing immediate/180-minute 3-of-3/360-minute 4-of-6 rules;
- incidence 0.5 events/asset-day, 21 strata, support requirements, recall LCB >=0.60 and workload UCB <=1.0 in BOTH inner folds;
- the same 2,000 bootstrap replicates, seed, selection utility, tie ordering, diagnostic fallback and separately labelled inverse objective;
- all already declared outer controlled/reference comparisons, including persistence.

Verify every current role/membership/catalogue hash against the corresponding published preflight. Candidate support and actual boundaries must be checked for each fold. Do not stop or change the second run's design after seeing the first one's scores.

Use unique, fresh output directories, for example:
- `outputs/amendment004/bdg2_threefold_f1_s42_v1`
- `outputs/amendment004/bdg2_threefold_f0_s42_v1`

Use the existing operational entrypoint, with the appropriate fold, existing config and new directory; resolve the actual Python environment rather than creating an unnecessary replacement. Keep real fits sequential and numerical threads at the existing setting. Check available RAM/disk before each launch. The previous 16.46 minutes was one smaller fold, not a guaranteed per-fold runtime: report a planning estimate separately from actual measurements. Larger folds require their own resource assessment. Persist command, source/config/data identity, PID, timestamps, logs and actual exit code; do not launch a duplicate while a process is running.

Do not refit fold 2. Do not change model hyperparameters, the grid, catalogue incidence, rule durations, feasibility thresholds or bootstrap settings to make a candidate pass. This is the unchanged reduced-grid temporal replication, not a full-grid search or a full-study run. Preserve failures in their own directories. Completed-unit resume is supported; do not promise mid-fit recovery.

For each completed new unit:
- validate exact 18 inner cells and 90 inner candidate/catalogue pairs;
- derive expected outer cells/pairs/streams from that fold's actual frozen decision and comparison ledger: do not hard-code fold 2's 25 pairs/138 streams when decisions may differ;
- independently reconstruct the reported metrics, bounds and selection from saved streams, catalogues and bootstrap draws; generalize the existing audit's fold/path assumptions only as required;
- verify completed-unit resume with zero new fits and unchanged unit files;
- retain all valid abstentions and their rejection reasons.

## Combined analysis, frozen before new results

Produce a clearly labelled **three-fold BDG2 reduced-grid benchmark, model seed 42**.

1. Give a per-fold decision table with actual dates, original building count, eligible asset-days, event support, primary selection or abstention, candidate ID and all failed gates. Keep the inverse objective, controlled components and persistence diagnostic separate.
2. Show per-fold controlled static CQR versus its shared-fit uncalibrated baseline: macro recall, clean episodes/asset-day, coverage, MPIW and Winkler95. Also show persistence and temporal/inverse comparisons where actually evaluated, identifying exact settings. A comparison name alone does not establish that its configuration is identical across folds.
3. Freeze the main exploratory paired contrast as static immediate CQR minus static immediate uncalibrated quantiles, for macro recall and clean workload. Report the two changes together. Do not describe a workload improvement as a same-recall improvement.
4. Verify outer test rows are disjoint. Combine clean workload from original episode counts divided by original eligible asset-days; calculate combined macro recall by pooling N/TP within each of the 21 strata across folds/catalogues then taking the equal-stratum mean. Report per-fold results alongside pooled results; never average fold percentages without naming that different estimand.
5. For optional approximate paired 95% intervals, resample the ten original buildings with all their fold and catalogue contributions kept together, using the declared draws/seed. Seed 42 is the only model seed: pass that scope explicitly to any reused inference function. Do not pretend that 3 folds x 10 buildings gives 30 independent buildings, that five catalogues create independent buildings, or that the five-model-seed full study was completed. Preserve pairing and report unavailable bounds honestly. No equivalence or confirmatory significance claim is required.
6. Report availability-only, numerical-only and combined detection by fault family/severity. Missing-data alarms are shared with baselines; do not attribute their detection to conformal prediction. Preserve missed events, censored recovery and building-specific workload.
7. Include actual fitting, replay, preparation, checkpoint/resume and validation costs with non-overlapping totals and correctly labelled nested phases. Record actual estimator owners and counts.
8. Disclose the post-inspection design and previously inspected fold-2 evidence. The comparison assesses repeatability across historical periods, not a pristine prospective trial or unseen-building portability.

## Deliverables and publication

Finish and publish:
- `CHECKPOINT_MEMORY_REPAIR_REPORT.md` with same-unit zero-fit measurements and compatibility evidence;
- `BDG2_THREEFOLD_BENCHMARK_REPORT.md`;
- machine-readable fold decisions, per-fold operational/interval results, paired contrast inputs/results, support and resource tables;
- indexed new run inputs/streams/catalogues/draws sufficient for independent recomputation, with exact provenance and existing lossless-file handling where necessary;
- an updated `review/CURRENT_EVIDENCE.md` and panel-response status reflecting what is actually completed.

Keep the old fold-2 report as historical evidence; do not silently relabel or replace it. Publish relevant code, readable summaries and reproducible evidence on the new review branch, verify its URL/SHA, and leave main untouched. The user should not need to upload CSVs manually.

End with the combined results and decisions, actual costs, source/publication SHAs and the precise remaining research scope. Do not end after the memory fix if both additional units can run safely.

The broader work remains: matched point/interval/compute comparison across the declared tasks and horizons (including the panel's LSTM versus XGBoost question), full candidate/method scope, and a justified operational evaluation plan for PLEIA temperature, PLEIA energy and RICO, which lack the current structural event support. Do not silently drop those tasks or inflate incidence to manufacture support. Keep full-study readiness false until its own requirements are met. This task authorizes the two additional BDG2 units and their analysis, not an automatic full-grid, four-task, five-model-seed or 900-cell robustness launch.
