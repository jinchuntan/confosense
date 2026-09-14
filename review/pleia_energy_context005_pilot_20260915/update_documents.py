"""Update current pointers after the real C pilot has independently passed."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SMART=ROOT/'smart_building_conformal';REVIEW=Path(__file__).resolve().parent
sys.path.insert(0,str(SMART))
from src.intervals005_common import atomic,read,tree
import pandas as pd

OUT=SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1_analysis'
RUN=SMART/'outputs/conditional_context005/pleia_energy_f2_s42_C_v1'
BATCH=SMART/'outputs/conditional_context005/first_real_C_v1_coordinator'
validation=read(OUT/'validation.json');assert validation['passed']
summary=pd.read_csv(OUT/'control_rule_channel_summary.csv')
workers=pd.read_csv(OUT/'worker_costs_and_exits.csv')
run_seconds=float(workers.loc[workers.task=='pleia_energy/run','wall_seconds'].iloc[0]);validate_seconds=float(workers.loc[workers.task=='pleia_energy/validate','wall_seconds'].iloc[0])
raw_bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
combined=summary[summary.channel=='combined']

next_text=f'''# Next bounded proposal: complete PLEIA-energy fold-2 C model seeds

Proposed scope, not authorized or launched: run model seeds **43, 44, 45 and 46** sequentially for the identical PLEIA-energy outer-fold-2/h1 C endpoint. Each seed retains the same 68 published contexts, 2,856 schedule slots, four 95% controls, five rules, 9,907-row original workload, role memberships, observation delays and inactive energy-sensitivity mask. The model seed changes only the quantile-owner seed; slot seeds 42/43 remain fixed schedule identities.

This four-unit batch is the smallest coherent extension that completes the five declared model seeds for this setting. It would permit the predeclared seed-within-original-context aggregation and PLEIA adjacent-week block inference, subject to the existing support/nondegeneracy checks. It must report all seeds rather than selecting a favorable seed.

Measured seed-42 coordinator costs were {run_seconds:.1f} seconds for execution and {validate_seconds:.1f} seconds for independent validation; raw scientific output occupied {raw_bytes/2**20:.1f} MiB before publication packaging. A linear four-seed planning allowance is {4*run_seconds/3600:.2f} execution hours, {4*validate_seconds/3600:.2f} validation hours and {4*raw_bytes/2**30:.2f} GiB raw output, plus freeze/readiness/resume, packaging and backup overhead. These are measured local extrapolations, not deadlines; sequential execution and the current nonblocking RAM reference/disk floor remain required.

Required implementation is limited to a four-unit manifest/coordinator using unused versioned paths, exact source/input gates, per-seed owner identities, durable adoption, independent validation and zero-fit resumes. No context, method, rule, calibration policy, fault schedule, threshold or endpoint change is proposed. Do not launch until explicitly authorized.
'''
atomic(REVIEW/'NEXT_BOUNDED_PROPOSAL.md',next_text)

panel=f'''# Panel response: first real conditional-context pilot

The implementation claim is now backed by one completed real-data C pilot rather than synthetic execution alone. PLEIA energy fold 2 / model seed 42 / h1 completed all 68 published contexts and 2,856 schedule slots. Corruption entered actual causal features and serialized predictions; the independent validator reconstructed 171,360 event records and the clean workload. Completed resume invoked zero fits or updates.

All 20 control/rule combinations are reported in each of three channels, with equal-context/equal-stratum detection, miss and delay summaries, and original clean episodes per asset-day/time in alert. The observed combined-channel detection range was {combined.conditional_context_detection.min():.3f}–{combined.conditional_context_detection.max():.3f}; this is descriptive and no control/rule was selected from outer outcomes.

The result remains conditional on declared synthetic faults and fixed contexts. It does not estimate natural fault prevalence, deployment precision/F1 or amendment-004 feasibility. It is one model seed on one inspected outer period, so population uncertainty remains unavailable. The energy sensitivity mask stayed inactive. Matched forecasting remains 70/195, interval quality 250/1950 and seasonal computations 9/27.

The next bounded proposal is the four remaining PLEIA-energy fold-2 model seeds, which would complete this setting's five-seed inferential input. It is not authorized or launched.
'''
atomic(REVIEW/'PANEL_RESPONSE.md',panel)

remaining='''# Remaining work after the first real C pilot

- Conditional-context C: PLEIA-energy fold 2 / seed 42 / h1 is complete. Remaining fixed C scope includes model seeds 43–46 for this setting and declared PLEIA-temperature/RICO folds and seeds. Five-seed/original-unit inference is still unavailable.
- Matched forecasting remains 70/195. Interval quality remains 250/1950. Unique seasonal computations remain 9/27.
- Amendment-004 natural-frequency feasibility remains separate. PLEIA/RICO support limitations and BDG2 reduced-grid abstentions are unchanged; the full 264-candidate BDG2 wrapper/execution remains outstanding.
- Calibration contamination, cascades, recovery and the independently proposed energy sensitivity analysis remain future packages. The energy mask was not adopted or applied here.
- Dissertation synthesis and full-study readiness remain incomplete.
'''
atomic(REVIEW/'REMAINING_WORK.md',remaining)

root_intro=f'''# First real amendment-005 conditional-context pilot completed

PLEIA energy outer fold 2 / model seed 42 / h1 completed all 68 published contexts, 2,856 scheduled fault slots, 68 clean identities, four fixed 95% controls, five rules and the full 9,907-row clean workload. All five CLI actions, independent validation and zero-fit resume passed. The published analysis reports all 60 control/rule/channel cells; no outer-result selection occurred.

This adds **one completed C pilot**. Matched forecasting remains **70/195**, interval quality **250/1950**, and unique seasonal computations **9/27**. C remains separate from natural-frequency deployment feasibility. Population inference is unavailable at one model seed; the energy-sensitivity mask stayed inactive. Full-study readiness remains false.

Evidence: [pilot report](review/pleia_energy_context005_pilot_20260915/PLEIA_ENERGY_CONTEXT005_PILOT_REPORT.md), [evidence index](review/pleia_energy_context005_pilot_20260915/EVIDENCE_INDEX.md), [every comparison](smart_building_conformal/outputs/conditional_context005/pleia_energy_f2_s42_C_v1_analysis/control_rule_channel_summary.csv), [independent validation](smart_building_conformal/outputs/conditional_context005/first_real_C_v1_coordinator/validation/validation.json), and [next bounded proposal](review/pleia_energy_context005_pilot_20260915/NEXT_BOUNDED_PROPOSAL.md).

<!-- pleia-energy-context005-pilot-20260915: historical status follows -->

'''
review_intro=root_intro.replace('(review/','(').replace('(smart_building_conformal/','(../smart_building_conformal/')
for relative in ['MATCHED_METHOD_READINESS_MAP.md','PROJECT_RECOVERY_STATUS.md','REMAINING_STUDY_EXECUTION_PLAN.md','PANEL_RESPONSE_MATRIX.md']:
    path=ROOT/relative;text=path.read_text(encoding='utf-8')
    if 'pleia-energy-context005-pilot-20260915: historical status follows' in text:raise ValueError('current pointer already updated')
    atomic(path,root_intro+text)
path=ROOT/'review/CURRENT_EVIDENCE.md';text=path.read_text(encoding='utf-8')
if 'pleia-energy-context005-pilot-20260915: historical status follows' in text:raise ValueError('current evidence already updated')
atomic(path,review_intro+text)
print('CURRENT STATUS, PANEL RESPONSE AND NEXT BOUNDED PROPOSAL UPDATED')
