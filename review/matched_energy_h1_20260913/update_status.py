"""Prepend the completed result; preserve all previous status text verbatim."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'smart_building_conformal/outputs/matched_forecasting005'
MARK='<!-- matched-energy-h1-20260913: historical content -->'

def main():
 result=json.loads((BASE/'energy_h1_report_v1/report_validation.json').read_text())
 assert result['passed'] and result['real_exit']==0
 text=f'''14 September 2026. **PLEIA-energy h1/fold0/seed42 matched unit completed and validated.** Actual run exit 0; eight tuning and two final learned fits; persistence has zero learned fits. All three point and six own-model 90%/95% interval cells passed independent recalculation. Saved artifacts reproduce calibration/test predictions, and completed resume performs zero fits without changing run files.

The primary comparison now has **4/195 paired units, 12/585 point cells and 24/1,170 interval cells completed**. The remaining core queue has 191 paired units and 1,910 learned fits. The new completion overlay preserves the original amendment-005 proposal/matrix, old temperature pilot and three-fold BDG2 benchmark, including all primary abstentions. Seasonal, broader interval methods/DSCP, operational and robustness obligations remain separate; full-study readiness remains false.

Read the [energy report](PLEIA_ENERGY_MATCHED_H1_REPORT.md) and [complete evidence index](review/matched_energy_h1_20260913/EVIDENCE_INDEX.md) for actual errors, interval quality, costs, fitted artifacts and verification. Real command wall time was {result['run_command_seconds']:.3f} seconds; measured model phases totalled {result['model_phase_seconds']:.3f} seconds. Validation/resume/tiny-test costs are listed separately.

**Single next bounded proposal:** separately authorize and freeze RICO horizon5/fold2/seed42 with the same three models and the published whole-run memberships. RICO and BDG2 queue units and the conditional challenge remain unlaunched. The updated queue gives explicitly labelled scenarios; their learned-model costs have not yet been measured.
'''
 updates=[('PROJECT_RECOVERY_STATUS.md','# Current recovery status: matched energy unit completed',text),
          ('PANEL_RESPONSE_MATRIX.md','# Current panel response status: matched energy evidence',text+'''
| Panel requirement | Completed evidence | Remaining work |
|---|---|---|
| Attention-LSTM versus XGBoost | Temperature pilot plus the new energy h1 matched unit; own-model intervals and measured compute | Remaining 191 paired task/horizon/fold/seed units; no multi-task superiority claim yet |
| Valid evaluation design | Published support audit and versioned memberships; current implementation verifies 39 role banks | Separate conditional challenge and original-unit uncertainty evaluation |
| Reproducibility and model ownership | Pre-fit commit, immutable protocol, serialized models, independent metrics, no-fit model reload and completed resume | Preserve the same controls for each newly authorized unit |
| Full dissertation scope | Completion overlay and full scope ledger remain visible | Seasonal, DSCP/full methods, robustness, contamination/recovery and full-grid operational evidence |
'''),('review/CURRENT_EVIDENCE.md','# Current evidence: completed matched PLEIA-energy unit',text.replace('(PLEIA_ENERGY_MATCHED_H1_REPORT.md)','(../PLEIA_ENERGY_MATCHED_H1_REPORT.md)').replace('(review/matched_energy_h1_20260913/EVIDENCE_INDEX.md)','(matched_energy_h1_20260913/EVIDENCE_INDEX.md)')+'''
Publication branch: [review/matched-energy-h1-20260913](https://github.com/jinchuntan/confosense/tree/review/matched-energy-h1-20260913). Evaluated pre-fit commit: `697d0e6e8a7de0a2fc55c98b8341117d789390ce`; source SHA-256 `7335d436f6e4f8c2144de372e8817d036bae216426c157f5bbdc1eb921927955`. The final delivery and branch history identify the final publication SHA.
''')]
 for name,title,new in updates:
  path=ROOT/name;old=path.read_text(encoding='utf-8')
  if MARK in old:old=old.split(MARK,1)[1].lstrip('\n')
  path.write_bytes((title+'\n\n'+new+'\n## Previous entries (historical)\n\n'+MARK+'\n\n'+old).encode('utf-8'))
 print('Updated current evidence, recovery and panel status; historical entries preserved')

if __name__=='__main__':main()
