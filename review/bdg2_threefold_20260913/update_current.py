"""Update current indexes from completed evidence, retaining entry text as history."""
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'smart_building_conformal/outputs/amendment004'
MARK='<!-- bdg2-threefold-20260913: historical content -->'


def replace_front(path,front):
    old=path.read_text(encoding='utf-8')
    if MARK in old:old=old.split(MARK,1)[1].lstrip('\n')
    path.write_text(front+'\n\n'+MARK+'\n\n'+old,encoding='utf-8')


def main():
    combined=BASE/'bdg2_threefold_combined_v1'
    validation=json.loads((combined/'validation.json').read_text());assert validation['passed']
    decisions=pd.read_csv(combined/'fold_decisions.csv');primary=decisions[decisions.selection=='primary']
    assert len(primary)==3
    selected=int(primary.operational_feasible.sum())
    cost=json.loads((BASE/'bdg2_threefold_costs_v1/cost_scope.json').read_text())
    preservation=json.loads((BASE/'bdg2_threefold_validation_v1/preservation.json').read_text());assert preservation['passed']
    summary=f'{selected}/3 units selected a primary configuration; {3-selected}/3 abstained under the unchanged confidence-bound gates.'
    front=f'''# Current ConfoSense evidence: three-fold BDG2 reduced-grid benchmark

13 September 2026. **Completed:** preserved fold 2 plus newly authorized folds 1 then 0, model seed 42, the same nine candidates and five catalogue seeds, all ten buildings and the one-hour horizon. All study commands exited **0**. **{summary}** The separate inverse objective and fixed diagnostics do not replace primary feasibility. Full-study readiness remains **false**.

Publication: [review/bdg2-threefold-20260913](https://github.com/jinchuntan/confosense/tree/review/bdg2-threefold-20260913). Evaluated new-unit commit: `18e5db5f2d81ed641ae90c5e257e512cf7ebbcc7`; source SHA-256 `203f3babf66c98ac072ad450abec5ea7ce3d60473f02708fa64ac2102ea3f7c9`. The final publication SHA is supplied with delivery and in branch history. The older source beneath the instruction branch was never checked out over the implementation.

- [Completed benchmark report](../BDG2_THREEFOLD_BENCHMARK_REPORT.md), [complete evidence index and reproduction commands](bdg2_threefold_20260913/EVIDENCE_INDEX.md)
- [Memory repair report](../CHECKPOINT_MEMORY_REPAIR_REPORT.md), [fold-2 read-only compatibility](../smart_building_conformal/outputs/amendment004/bdg2_checkpoint_compatibility_v1/validation.json)
- [Execution/analysis freeze before both new fits](../smart_building_conformal/outputs/amendment004/bdg2_threefold_frozen_v2/execution_analysis_manifest.json), [39 memberships, 18 boundaries, 189 strata and 45 catalogue-hash checks](../smart_building_conformal/outputs/amendment004/bdg2_threefold_validation_v1/support_validation.json)
- [Fold decisions](../smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/fold_decisions.csv), [per-fold operational/interval metrics](../smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/per_fold_operational_interval_metrics.csv), [pooled metrics](../smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/pooled_metrics.csv), [frozen paired contrasts](../smart_building_conformal/outputs/amendment004/bdg2_threefold_combined_v1/paired_contrasts.csv)
- [Actual command costs](../smart_building_conformal/outputs/amendment004/bdg2_threefold_costs_v1/command_measurements.csv), [process CPU](../smart_building_conformal/outputs/amendment004/bdg2_threefold_costs_v1/process_measurements.csv), [nested phase measurements](../smart_building_conformal/outputs/amendment004/bdg2_threefold_costs_v1/phase_measurements.csv)
- [Fold-1 independent audit](../smart_building_conformal/outputs/amendment004/bdg2_threefold_f1_audit_v2/validation.json), [fold-0 audit](../smart_building_conformal/outputs/amendment004/bdg2_threefold_f0_audit_v1/validation.json), [fold-1 zero-fit resume](../smart_building_conformal/outputs/amendment004/bdg2_threefold_validation_v1/fold1_resume_validation.json), [fold-0 zero-fit resume](../smart_building_conformal/outputs/amendment004/bdg2_threefold_validation_v1/fold0_resume_validation.json)
- [Preserved failed audit and numeric diagnosis](../smart_building_conformal/outputs/amendment004/bdg2_threefold_validation_v1/recovery_numerics.json), [preservation proof](../smart_building_conformal/outputs/amendment004/bdg2_threefold_validation_v1/preservation.json), [panel status](../PANEL_RESPONSE_MATRIX.md)

The checkpoint reader removes duplicate CSV materialization and preserves all old fold-2 values and files with zero fits. A separate independent-audit convolution-rounding defect was repaired without changing production source, thresholds or results; the failed attempt remains published. The benchmark has 9 CQR objects / 27 quantile sub-estimators in total, including the preserved fold-2 fits; controls share fits and persistence adds none. Three original study commands total {cost['study_command_seconds']:.3f} seconds, with verification costs separate.

This is a post-inspection, historical-period comparison on ten known buildings and one model seed. Paired uncertainty keeps every building's folds and catalogues together; it is not 30 independent buildings or a completed five-model-seed study. Missing-data alarms are shared with baselines. PLEIA temperature, PLEIA energy and RICO retain their lack of inner operational support. Matched multi-task/horizon point, interval and computational evaluation, including Attention-LSTM versus XGBoost, and the full method/candidate scope remain required.

The single next bounded step is a no-fitting support-design audit for those three unsupported tasks, followed by a justified amendment or explicit non-estimability decision. No next run or full study was launched. The original forecasting pilot remains complete at 9/9 point and 18/18 interval cells; its historical evidence and report are preserved below.

## Earlier delivery stages (historical)
'''
    replace_front(ROOT/'review/CURRENT_EVIDENCE.md',front)
    panel=f'''# ConfoSense current panel response matrix

13 September 2026, after the completed three-fold BDG2 reduced-grid operational benchmark. **{summary}** All three original commands exited 0; both new units passed saved-stream metric reconstruction and zero-fit completed resume. The checkpoint repair preserved the prior fold-2 result. The original forecasting pilot, historical results, main and backups remain preserved. See the [completed benchmark](BDG2_THREEFOLD_BENCHMARK_REPORT.md), [memory repair](CHECKPOINT_MEMORY_REPAIR_REPORT.md) and [current evidence index](review/CURRENT_EVIDENCE.md). Full-study readiness remains **false**.

| Panel topic | Completed evidence | Still required |
|---|---|---|
| Explain conformal prediction | Own-model split-conformal forecasting pilot plus CQR operational intervals compared with the shared uncalibrated quantile fit; empirical coverage, width and Winkler95 retained. | Concise final presentation of calibration, temporal-dependence limits and prediction intervals versus metric confidence intervals. |
| Dataset sources, purpose and selection | Four-task structural preflight; all ten retained BDG2 buildings, actual temporal memberships and source/derived-data attribution published. | Complete broader source-purpose-selection bibliography and justify operational support treatment for each task. |
| Separate datasets or merge | BDG2 benchmark pools only commensurate hourly kWh metrics across its own periods; three source datasets/four tasks remain separate. | Broader matched task/horizon evaluation without pooling raw errors across physical units. |
| Justify methods | Nine frozen operational candidates, CQR-owned HistGradientBoosting quantiles, shared uncalibrated controls and zero-fit persistence; actual estimator ownership recorded. | Full method/candidate scope, including remaining DSCP/seasonal questions; this is not the point XGBoost/Attention-LSTM comparison. |
| Explain train/calibration/test protocol | Three BDG2 historical outer periods, two expanding purged inner folds, reserved final calibration, 39 unchanged role hashes and 18 validated boundaries. | Complete broader declared folds/model seeds and explain prior inspection and repeated buildings in the dissertation. |
| Explain k-of-m rules | Immediate, 180-minute 3-of-3 and 360-minute 4-of-6 frozen candidates; causal replay, confidence-bound gates, abstention, clean workload and censored detection accounting verified. | Justified handling of unsupported tasks; no threshold or incidence changes simply to produce feasibility. |
| Simplify presentation | Source-linked per-fold and pooled reports, exact settings, conditional paired recall/workload contrasts and all channel/stratum CSVs. | Revised final slides/manuscript with clear limitations; no blanket same-recall superiority or prospective-generalization claim. |
| Verify methodology and ablation | Both new 18-cell/90-pair inner matrices and derived outer matrices pass independent reconstruction; shared controls, inverse objective, persistence, original-building pairing and zero-fit resume are retained. | Full-grid/method and broader robustness scope, justified unsupported-task design, and inference at the actual study scope. |
| Is LSTM's extra cost worthwhile? | Preserved PLEIA point/interval/computational pilot and its prior diagnostics; the current operational model is explicitly distinct. | Matched point/interval/compute evidence across all 13 declared task/horizon combinations and broader folds/seeds. No requirement that LSTM win. |

The next bounded step is the no-fitting support-design audit for PLEIA temperature, PLEIA energy and RICO. They are retained in scope; their current inner banks are unsupported at the unchanged incidence. No full-study, extra-seed or additional dataset run is authorized by this delivery.

## Earlier delivery stages and assessments (historical)
'''
    replace_front(ROOT/'PANEL_RESPONSE_MATRIX.md',panel)
    print('Updated current evidence and panel status; entry contents retained as history')


if __name__=='__main__':main()
