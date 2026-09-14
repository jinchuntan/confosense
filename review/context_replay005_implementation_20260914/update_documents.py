"""Update current pointers after evidence has passed; retain historical sections."""
from common import *
analysis=SMART/'outputs/conditional_context005/implementation_analysis_v1'
assert read(analysis/'validation.json')['passed']
assert read(SMART/'outputs/conditional_context005/aggregate_validation_v2/validation.json')['passed']
base='review/context_replay005_implementation_20260914/'
intro='''# Conditional-context replay implemented and synthetically validated

The amendment-005 C engine now executes observation-time faults through actual causal features and serialized predictors, with four fixed .95 controls, five rules, independent context state and original-stream workload. Both synthetic cadence workflows and zero-fit completed resumes passed. Real C fitting/replay was not launched.

Current totals remain **70/195 matched forecasting units, 250/1950 interval cells, and 9/27 unique seasonal computations**. All five declared interval methods are implemented; the 1,700 remaining interval cells require scope execution and their recorded owner prerequisites, not additional method families. Full-study readiness remains false.

The next bounded execution proposal is **PLEIA energy, fold 2, seed 42, h1: 68 published contexts, 2,856 fault slots, 68 clean identities, four controls and five rules, plus original clean workload**. Its C role masks require three new shared quantile estimators and one CQR conformalization; matched owners cannot be reused. This proposal awaits a new execution instruction. The separately versioned retrospective energy mask is proposed and unapproved; it does not block primary C execution.

Links: [evidence index]({base}EVIDENCE_INDEX.md), [implementation report]({base}IMPLEMENTATION_REPORT.md), [support and exact dependencies]({base}SUPPORT_GATE_STATUS.md), [interval diagnosis]({base}INTERVAL_FAILURE_DIAGNOSTIC.md), [protocol crosswalk]({base}PROTOCOL_TO_CODE_CROSSWALK.md), [energy sensitivity proposal]({base}ENERGY_SENSITIVITY_SPEC.md), [exact first-run proposal]({base}FIRST_CONDITIONAL_CONTEXT_RUN_PROPOSAL.md).

<!-- context-replay005-implementation-20260914: historical status follows; current status is above -->

'''
for name in ['MATCHED_METHOD_READINESS_MAP.md','PROJECT_RECOVERY_STATUS.md','REMAINING_STUDY_EXECUTION_PLAN.md','PANEL_RESPONSE_MATRIX.md','review/CURRENT_EVIDENCE.md']:
    path=ROOT/name;text=path.read_text(encoding='utf-8')
    if 'context-replay005-implementation-20260914: historical status follows' in text:raise ValueError('preserve existing current update')
    # Repair an observed stale root-level link without rewriting old results.
    if name!='review/CURRENT_EVIDENCE.md':text=text.replace('(matched_intervals005_four_settings_20260914/EVIDENCE_INDEX.md)','(review/matched_intervals005_four_settings_20260914/EVIDENCE_INDEX.md)')
    atomic(path,intro.format(base=base.removeprefix('review/') if name.startswith('review/') else base)+text)
atomic(REVIEW/'PANEL_RESPONSE.md','''# Panel response evidence added by this package

The numerical model comparison remains the preserved matched forecasting evidence: persistence, XGBoost and Attention-LSTM use matched memberships and their own intervals. This package adds no new real-study comparison cells and no favourable retuning.

The support crosswalk replaces a vague missing-method statement: all five interval families already exist; 250/1950 cells are complete and 1,700 are outstanding execution. The read-only 130-cell native/common diagnostic retains failed coverage and separates fixed-owner error shifts, native CQR corrections and EnbPI OOB calibration from conjectured physical causes. Validation is not a nominal-coverage guarantee.

The new C implementation makes injected faults enter the actual causal predictor inputs. Its fixed conditional-context detection estimand, original-exposure workload, availability channel, delayed adaptation and null denominators are independently tested. It does not establish natural-frequency A feasibility or deployment precision/F1. The PLEIA/RICO A support limitations and BDG2 reduced-grid abstentions remain intact.

First real C execution is proposed, not completed. Single-model-seed C results will be descriptive. Five-seed inference must pool seeds within original units and preserve PLEIA week blocks/RICO phase support. Energy sensitivity is a concrete retrospective proposal with unresolved adoption, not an invented historical rule.

Remaining work includes 125 matched forecasting units; 1,700 interval cells and 18 unique seasonal computations with prerequisites; separately authorized C execution across settings/seeds; the full 264-candidate BDG2 operational wrapper/execution; calibration contamination, cascades and recovery obligations; dissertation synthesis. No full-study completion is claimed.

See the evidence index, independent validation records, protocol crosswalk and exact first-run proposal in this directory.
''')
print('CURRENT POINTERS UPDATED; HISTORICAL REPORTS RETAINED')
