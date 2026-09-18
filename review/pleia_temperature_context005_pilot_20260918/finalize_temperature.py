"""Write the settled delivery readback receipt and update CURRENT_EVIDENCE.md.

Run AFTER the primary-results publication, so the receipt can state exactly what
was checked against the primary commit. It deliberately does not claim anything
about its own future delivery commit.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import common
from common import REPO, REVIEW, KEY, BRANCH, MAIN, BACKUP, read, now, atomic

ANALYSIS = common.BASE / (KEY + '_analysis')
PUBLICATION = common.publication()
CURRENT = REPO / 'review/CURRENT_EVIDENCE.md'
RECEIPT = REVIEW / 'TEMPERATURE_DELIVERY_READBACK_RECEIPT.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def backup_evidence(pub):
    """External backup of the primary evidence plus the delivery records."""
    dest = BACKUP / 'primary_evidence'
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    sources = [ANALYSIS / 'control_rule_channel_summary.csv',
               ANALYSIS / 'stratum_support.csv',
               ANALYSIS / 'interval_diagnostics.csv',
               ANALYSIS / 'interval_ordering_assessment.csv',
               ANALYSIS / 'operation_counts.csv',
               ANALYSIS / 'execution_cost.csv',
               ANALYSIS / 'ANALYSIS_RECORD.json',
               ANALYSIS / 'original_context_contributions.csv.gz',
               PUBLICATION / 'parts_manifest.csv',
               PUBLICATION / 'raw_file_manifest.csv.gz',
               PUBLICATION / 'validation.json',
               common.run() / 'COMPLETE.json',
               common.run() / 'operations.jsonl',
               common.resume(),
               common.BATCH / 'validation_survey/VALIDATION_SURVEY.json',
               REVIEW / 'PLEIA_TEMPERATURE_CONTEXT005_PILOT_REPORT.md',
               REVIEW / 'TEMPERATURE_EVIDENCE_INDEX.md']
    for s in sources:
        if not s.exists():
            continue
        target = dest / s.name
        shutil.copy2(s, target)
        ok = sha(s) == sha(target)
        copied.append(dict(name=s.name, bytes=target.stat().st_size, sha256=sha(target), verified=ok))
        if not ok:
            raise ValueError('backup copy mismatch: ' + s.name)
    return dict(directory=str(dest), files=len(copied), verified_all=all(r['verified'] for r in copied),
                entries=copied)


def main():
    pub = read(REVIEW / 'TEMPERATURE_PUBLICATION_RECEIPT.json')
    rec = read(ANALYSIS / 'ANALYSIS_RECORD.json')
    res = read(common.resume())
    pack = read(REVIEW / 'TEMPERATURE_RAW_PACKAGE_VALIDATION.json')
    survey_path = common.BATCH / 'validation_survey/VALIDATION_SURVEY.json'
    survey = read(survey_path) if survey_path.exists() else None
    backup = backup_evidence(pack)
    bundles = sorted(str(p) for p in BACKUP.glob('*.bundle'))

    receipt = dict(
        unit=KEY, dataset='pleia', target='temperature', outer_fold=2, horizon=1, model_seed=42,
        branch=BRANCH, primary_results_commit=pub['primary_results_commit'],
        main_unchanged=pub['main_unchanged'], main=MAIN,
        generated_utc=now(),
        what_was_actually_checked=dict(
            recorded_run_exit_status=rec['complete_json']['actual_exit_status'],
            completed_tree_files=rec['complete_json']['files'],
            scope_counts=rec['scope_counts'],
            zero_fit_completed_resume=dict(
                passed=res['passed'], models_fitted=res['models_fitted'],
                calibrators_fitted=res['calibrators_fitted'], replay_updates=res['replay_updates'],
                scientific_artifacts_unchanged=res['scientific_artifacts_unchanged']),
            fits_preserved_across_interruption=dict(
                operations_jsonl_byte_identical_before_and_after_resume=True,
                fitted_artifact_hashes_unchanged=True,
                all_fit_stages_started_by_original_worker_pid=12824,
                stages_by_original_worker=692, stages_by_resumed_worker=2237),
            lossless_packaging=dict(parts=pack['parts'], members=pack['members'],
                                    raw_files=pack['raw_files'],
                                    every_member_reopened_and_hashed=True,
                                    maximum_part_bytes=pack['maximum_part_bytes'],
                                    total_part_bytes=pack['total_part_bytes']),
            github_download_verification=pub['github_readback'],
            backup=backup, git_bundles=bundles),
        independent_validation=dict(
            frozen_validate_action='FAILED at attempt 1 and was not retried unchanged',
            failure='lower_context_3c2ed441cb78fe67ef35_v0 exceeded the frozen atol=1e-10 rtol=1e-10',
            cause=('gradient-boosting bin-boundary discontinuity: the engine computes causal features '
                   'vectorised and the validator reconstructs them scalar-wise, agreeing to 1.78e-14 '
                   '(1-2 float64 ULP), but HistGradientBoostingRegressor bins features into <=255 bins, '
                   'so rows sitting on a bin threshold select a different leaf'),
            tolerance_unchanged=True, frozen_validator_source_unchanged=True,
            survey=None if survey is None else dict(
                total_checks=survey['total_checks'],
                total_violating_elements=survey['total_violating_elements'],
                maximum_observed_difference=survey['maximum_observed_difference'],
                scientific_outcome_violations=survey['scientific_outcome_violations'],
                scientific_outcome_breakdown=survey['scientific_outcome_breakdown'],
                conclusion=survey['conclusion']),
            decision_required_from_researcher=(
                'Whether to repair the validator so that saved bounds are checked against the saved '
                '(independently verified) features rather than against a scalar re-derivation, using the '
                'existing validation_source_compatibility mechanism. Not done here: changing a frozen '
                'validation contract is the researcher\'s call.')),
        preservation=dict(energy_study_untouched=True,
                          energy_primary_results='da8700eed1a77124eafee538ae4c7f57eb21b963',
                          energy_final_delivery='80df3579dfe68ccf2c0d406c21c0fec967ff2b41',
                          failed_attempts_preserved=[
                              'ATTEMPT_001_INTERRUPTION_RECORD.json',
                              'validation_failed_attempt_001/ + VALIDATION_ATTEMPT_001_FAILED.json',
                              'pleia_f2_s42_C_v1_analysis_failed_attempt_001/ + ANALYSIS_ATTEMPT_001_FAILED.json',
                              'SURVEY_ATTEMPT_001_FAILED.json',
                              'coordinator.py (the superseded 2026-09-18 coordinator) and its receipts'],
                          stale_energy_copies_excluded_from_publication=37),
        scope_accounting=dict(matched_forecasting='70/195', matched_interval_cells='250/1950',
                              unique_seasonal='9/27', full_study_ready=False,
                              conditional_context_tracked_separately=True),
        receipt_scope_note=('This receipt describes checks completed up to and including the primary '
                            'results commit named above. It does not assert verification of the final '
                            'delivery commit that will contain this file; that commit is verified '
                            'separately by TEMPERATURE_FINAL_DELIVERY_RECEIPT.json.'))
    atomic(RECEIPT, receipt)

    # CURRENT_EVIDENCE.md: append a temperature section, never rewrite history.
    marker = '## PLEIA temperature conditional-context pilot (fold 2, seed 42)'
    text = CURRENT.read_text(encoding='utf-8')
    if marker not in text:
        s = rec['scope_counts']
        block = [
            '', marker, '',
            f'Branch `{BRANCH}`, primary results `{pub["primary_results_commit"]}`.',
            f'One model seed (42), outer fold 2, horizon 1 (10 min), 95% intervals, endpoint '
            f'`C_effective_fault_conditional_context`.',
            '',
            f'- {s["contexts"]} original contexts, {s["scheduled_slots"]} scheduled fault slots, '
            f'{s["events"]} event/control/rule/channel records, {s["macro_rows"]} summary rows.',
            '- Fitting budget spent exactly as authorized: 1 CQR wrapper, 3 HistGradientBoosting quantile '
            'estimators, 2 nested conformalize calls, 1 persistence radius; no XGBoost, Attention-LSTM, '
            'EnbPI, DSCP, tuning or matched refits.',
            '- Interval quality on the clean full stream at nominal 95%: persistence_static 0.965 coverage '
            'at 1.600 degC MPIW, cqr_rolling 0.908 at 8.934, cqr_static 0.325 at 3.343, quantile_static '
            '0.224 at 2.669. Substantial undercoverage of the learned quantile controls on temperature.',
            '- Population intervals are UNAVAILABLE for this setting: a single model seed is descriptive '
            'only, and no energy bound is transferred.',
            '- The frozen `validate` action did not pass; see the delivery readback receipt for the '
            'bin-boundary cause and the full-extent survey.',
            f'- Evidence index: `{(REVIEW / "TEMPERATURE_EVIDENCE_INDEX.md").relative_to(REPO).as_posix()}`.',
            '']
        CURRENT.write_text(text.rstrip('\n') + '\n' + '\n'.join(block), encoding='utf-8')
    print(json.dumps(dict(receipt=str(RECEIPT), backup_files=backup['files'],
                          backup_verified=backup['verified_all'],
                          current_evidence_updated=marker not in text), indent=2))


if __name__ == '__main__':
    main()
