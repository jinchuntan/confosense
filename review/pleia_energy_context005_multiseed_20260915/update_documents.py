"""Render the report, evidence index, panel response and current-status notes."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from common import *

def md(frame,columns=None):
    f=frame[columns] if columns else frame
    def v(x):
        if pd.isna(x):return 'unavailable'
        if isinstance(x,(float,np.floating)):return f'{x:.5g}'
        return str(x).replace('|','\\|')
    return '\n'.join(['| '+' | '.join(f.columns)+' |','| '+' | '.join(['---']*len(f.columns))+' |']+['| '+' | '.join(v(x) for x in row)+' |' for row in f.itertuples(index=False,name=None)])

def main():
    val=read(ANALYSIS/'validation.json');ind=read(ANALYSIS/'independent_validation.json');pack=read(REVIEW/'RAW_PACKAGE_VALIDATION.json')
    if not val['passed'] or not ind['passed'] or not pack['passed']:raise ValueError('evidence incomplete')
    comp=pd.read_csv(ANALYSIS/'five_seed_control_rule_channel.csv');cost=pd.read_csv(ANALYSIS/'worker_cost_summary.csv');ops=pd.read_csv(ANALYSIS/'operation_reconciliation.csv')
    combined=comp[comp.channel=='combined'].sort_values(['rule_id','control_id'])
    cols=['control_id','rule_id','conditional_context_detection','lower','upper','status_inference','seed_sd_detection','mean_restricted_ttd_minutes','mean_misses','mean_background_episodes_per_asset_day','mean_fraction_time_in_alert']
    totals={r.action:r.total_wall_seconds for r in cost.itertuples()}
    report=['# PLEIA-energy conditional-context005 five-seed report','',
        'The authorized outer-fold-2/h1 batch completed model seeds 43–46 and reused the preserved seed-42 unit without rerunning it. All five seeds use the same 68 original contexts, 2,856 fault slots, four fixed 95% controls, five rules, three channels, calibration schedules and 68.798611 asset-day clean workload. Fault-slot seeds remain 42/43 and the energy-sensitivity mask remained inactive. No result-driven selection or retuning occurred.','',
        '## Combined-channel comparisons','',
        'The point is the frozen equal-seed-within-context, equal-context-within-stratum, equal-21-stratum detection endpoint. Bounds are approximate original-context block-bootstrap uncertainty conditional on this historical setting and protocol. Workload and restricted TTD remain descriptive. The directly accessible CSV contains all 60 control/rule/channel cells.','',md(combined,cols),'',
        '## Validation and computation','',
        f'All four new runs contain {4*171360:,} event records; the combined five-seed evidence contains {val["event_records"]:,} records and 300 seed-specific macro cells. Independent aggregate validation reproduced all {ind["cells"]} endpoints using the saved contributions and the exact {ind["draws"]:,} paired chronological block draws. It found maximum point difference {ind["maximum_absolute_point_difference"]:.3g} and maximum bound difference {ind["maximum_absolute_bound_difference"]:.3g}.', '',
        f'The four new seeds performed 4 CQR wrapper fits containing 12 native quantile-estimator fits, four logical conformalizations (eight nested profiler calls), four persistence-radius computations and zero persistence learned fits. Serialized native estimators carried their actual model seeds. Every new completed resume performed zero model fits, zero calibrator fits and zero replay updates.', '',md(cost),'',
        f'Across all five units, run commands used {totals.get("run",0)/3600:.3f} wall-hours, independent validation {totals.get("validate",0)/3600:.3f} wall-hours, and completed resume verification {totals.get("resume",0)/3600:.3f} wall-hours. These are summed sequential command durations; nested profiler calls are not added to them. The four new raw trees were packaged into {pack["parts"]} lossless parts ({pack["total_part_bytes"]/2**30:.3f} GiB), with every member read back and hash-verified.','',
        '## Interpretation limits','',
        'The 68 original contexts remain the independent observational units; the five training seeds are averaged within context and do not become 340 contexts. Repeated deterministic persistence results do not add data replicates. Detection intervals do not apply to workload or delay because those endpoints use different full-stream exposure, including the held-out tails. Degenerate or unsupported bounds remain explicitly unavailable. This conditional synthetic-fault endpoint does not estimate natural fault prevalence, deployment precision/F1, or amendment-004 feasibility, and it does not add cells to the matched forecasting or interval-quality matrices.','']
    atomic(REVIEW/'PLEIA_ENERGY_CONTEXT005_MULTISEED_REPORT.md','\n'.join(report))
    panel=['# Panel-response evidence: five-seed conditional-context result','',
        '- Completed all predeclared PLEIA-energy fold-2/h1 C model seeds 42–46; seed 42 was reused unchanged and seeds 43–46 passed independent per-unit validation and zero-fit resume.',
        '- Preserved all 68 original contexts, 2,856 fault slots per seed, four controls, five rules, three channels, observation delays and workload denominators.',
        '- Aggregated in the declared order and used paired seven-adjacent-context block draws. Training-seed variability is reported separately from original-context uncertainty.',
        '- Published all 60 comparisons with detection, workload, restricted TTD, misses and interval diagnostics. No control or seed was selected after viewing results.',
        '- Scope remains one historical PLEIA-energy outer fold. Matched forecasting remains 70/195, interval quality 250/1950, and unique seasonal computations 9/27.','']
    atomic(REVIEW/'PANEL_RESPONSE.md','\n'.join(panel))
    atomic(REVIEW/'REMAINING_WORK.md','# Remaining work\n\nThis batch completes five model seeds only for PLEIA-energy outer-fold-2/h1 conditional context C. It does not complete other C datasets or folds, the BDG2 operational grid, energy sensitivity, legacy robustness/recovery, or the matched forecasting/interval matrices (70/195 and 250/1950; seasonal 9/27).\n\nThe next bounded dependency is a no-fitting activation/readiness package for the first PLEIA-temperature outer-fold-2/h1/model-seed-42 C pilot, using its already published contexts and the same fixed four-control/five-rule contract. That package should freeze exact memberships, operations, storage and cost expectations before any separate real-fit authorization. Do not launch it from this batch.\n')
    out='../../smart_building_conformal/outputs/conditional_context005/'
    lines=['# PLEIA-energy context005 multiseed evidence index','',
        '[Five-seed report](PLEIA_ENERGY_CONTEXT005_MULTISEED_REPORT.md), [panel response](PANEL_RESPONSE.md), [remaining work](REMAINING_WORK.md), [durable progress](PROGRESS_AND_RESTART.md), [authorization](USER_AUTHORIZATION.txt), [handoff reference](AUTHORIZING_HANDOFF_REFERENCE.md).','',
        '## Frozen batch and per-seed acceptance','',
        '[Batch scope](BATCH_SCOPE.json), [frozen batch manifest](FROZEN_BATCH_MANIFEST.json), [evaluated commit](EVALUATED_COMMIT.json), [preflight validation](PREFLIGHT_VALIDATION.json), [preservation baseline](PRESERVATION_BASELINE.json).','']
    for seed in SEEDS:
        k=key(seed);lines.append(f'- Seed {seed}: [manifest]({k}_execution_manifest.json), [protocol](../../smart_building_conformal/protocols/conditional_context005/{k}/frozen_protocol.json), [readiness](../../smart_building_conformal/protocols/conditional_context005/{k}/readiness.json), [completion]({out}{k}/COMPLETE.json), [operations]({out}{k}/operations.jsonl), [independent validation]({out}pleia_energy_f2_context005_multiseed_v1_coordinator/seed_{seed}_validation/validation.json), [zero-fit resume]({out}pleia_energy_f2_context005_multiseed_v1_coordinator/seed_{seed}_completed_resume.json), [archive validation]({out}{k}_publication_v1/validation.json), [archive parts]({out}{k}_publication_v1/parts_manifest.csv), [raw member manifest]({out}{k}_publication_v1/raw_file_manifest.csv.gz).')
    lines+=['','## Direct five-seed results','']
    purposes=[('per_seed_control_rule_channel.csv','all 300 seed/control/rule/channel summaries'),('five_seed_control_rule_channel.csv','all 60 frozen aggregate comparisons with detection bounds and descriptive workload/delay'),
        ('original_context_seed_contributions.csv.gz','all saved per-seed original-context/stratum contributions'),('original_context_seed_averages.csv.gz','seed-averaged contributions at each original context/stratum'),
        ('five_seed_stratum_averages.csv','equal-context results for every stratum'),('inference_bounds.csv','all detection interval statuses and percentile endpoints'),
        ('bootstrap_design.json','fixed seed, draw indices and shared draw hash'),('bootstrap_draw_estimates.csv.gz','all 120,000 cell/draw detection values'),
        ('paired_control_detection_contrasts.csv','the fixed 90 paired control contrasts'),('per_seed_background_workload.csv','full-stream workload contributions without bootstrap bounds'),
        ('per_seed_interval_diagnostics.csv','conditional and clean interval diagnostics by seed'),('five_seed_interval_diagnostics.csv','descriptive five-seed interval summaries'),
        ('operation_reconciliation.csv','owner, fit and actual native seed reconciliation'),('worker_costs_and_exits.csv','all 25 seed/action exits and costs including preserved seed 42'),
        ('worker_cost_summary.csv','summed and mean sequential command costs'),('independent_inference_checks.csv','independently reconstructed real-data cells'),
        ('independent_validation.json','aggregate acceptance receipt'),('validation.json','analysis acceptance and fixed matrix counts')]
    for name,purpose in purposes:lines.append(f'- [{name}]({out}pleia_energy_f2_context005_five_seed_analysis_v1/{name}): {purpose}.')
    lines+=['',f'[Comparison PNG]({out}pleia_energy_f2_context005_five_seed_analysis_v1/five_seed_detection.png), [PDF]({out}pleia_energy_f2_context005_five_seed_analysis_v1/five_seed_detection.pdf), [figure source hashes]({out}pleia_energy_f2_context005_five_seed_analysis_v1/five_seed_detection.sources.json).','',
        'The seed-42 raw archive remains linked from the prior pilot index and was not downloaded, repackaged or rerun. For each new seed, extract every ZIP part into one empty directory and verify each byte using that seed’s raw member manifest.','']
    atomic(REVIEW/'EVIDENCE_INDEX.md','\n'.join(lines))
    marker='<!-- pleia-energy-context005-multiseed-20260915 -->'
    current=REPO/'review/CURRENT_EVIDENCE.md';text=current.read_text(encoding='utf-8')
    section=f'''# Current evidence\n\n{marker}\n15 September 2026: PLEIA-energy conditional-context C now has all five model seeds 42–46 for outer fold 2/h1. Seeds 43–46 completed per-unit independent validation and zero-fit resume; seed 42 was reused unchanged. The [five-seed report](pleia_energy_context005_multiseed_20260915/PLEIA_ENERGY_CONTEXT005_MULTISEED_REPORT.md), [evidence index](pleia_energy_context005_multiseed_20260915/EVIDENCE_INDEX.md), [all 60 comparisons](../smart_building_conformal/outputs/conditional_context005/pleia_energy_f2_context005_five_seed_analysis_v1/five_seed_control_rule_channel.csv), and [independent aggregate validation](../smart_building_conformal/outputs/conditional_context005/pleia_energy_f2_context005_five_seed_analysis_v1/independent_validation.json) are canonical. Original-context uncertainty uses 68 contexts and paired chronological blocks; seeds are averaged within context. Main and previous evidence remain unchanged. Full-study readiness remains false.\n\n'''
    if marker not in text:
        rest=text.split('\n',1)[1].lstrip() if text.startswith('# Current evidence') else text
        atomic(current,section+rest)
    print(json.dumps(dict(updated=True,report_cells=len(comp),supported_bounds=ind['supported_bounds'],unavailable_bounds=ind['unavailable_bounds']),indent=2))

if __name__=='__main__':main()
