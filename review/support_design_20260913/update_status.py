"""Prepend current completion status; preserve all historical recovery prose."""
from pathlib import Path
from document_text import prose
ROOT=Path(__file__).resolve().parents[2]
MARK='<!-- support-design-20260913: historical content -->'
front='''13 September 2026. **No-fitting support-design task complete.** The PLEIA forecasting pilot and BDG2 three-fold reduced-grid benchmark are completed and preserved; all three BDG2 primary selections abstained. No model fitting was performed in this task. Main and historical outputs/configurations/protocols remain unchanged.

The support audit distinguishes count impossibility, five-rotation allocation, null realizations and original-unit limitations. At unchanged incidence, RICO's entire eligible dataset yields at most80 requested events across five catalogues; its old one-run outer tests request zero. PLEIA earliest/middle inner banks request65/95 against a necessary105; later banks lose support through null realizations. The recommendation retains amendment004 and adds a separately named conditional-context challenge. All567 proposed role/stratum cells pass the distinct-effective-context screen; precision remains separately limited.

The no-fit task generated1,128 role-specific contexts/47,376 paired variants, not that many independent observations. Independent reconstruction passed all variants and210 operational/forecasting boundaries. The exact13-horizon forecast matrix retains all models/folds/seeds/90–95% levels:9 point/18 interval pilot cells reusable;576 point/1,152 interval core cells still required, representing1,920 new learned fit invocations. Seasonal adds135 point/270 level cells through27 deterministic computations; RICO seasonal remains explicitly inapplicable.

**Single next implementation/run package:** implement `src.matched_forecasting005`, preserving the old pilot entrypoint, then obtain authorization for one PLEIA-energy h1/fold0/seed42 matched unit with persistence, XGBoost and Attention-LSTM. Exact scope:29,719 fit /9,907 calibration /9,909 test rows,8 tuning+2 final learned fits,3 point/6 interval cells, serialized artifacts and zero-fit completed resume. This entrypoint is presently missing; no full study or new fit was launched.

Read [SUPPORT_DESIGN_AUDIT.md](SUPPORT_DESIGN_AUDIT.md), [AMENDMENT005_PROPOSAL.md](AMENDMENT005_PROPOSAL.md), [REMAINING_STUDY_EXECUTION_PLAN.md](REMAINING_STUDY_EXECUTION_PLAN.md), and the [support evidence index](review/support_design_20260913/EVIDENCE_INDEX.md). Full-study and scientific publication readiness remain **false**. Full method/DSCP, seasonal, matched multi-task model comparison and robustness/contamination/recovery obligations remain in the scope ledger; the challenge does not establish four-task deployment feasibility.
'''
def update(path,title,text):
 p=ROOT/path;old=p.read_text(encoding='utf-8')
 if MARK in old:old=old.split(MARK,1)[1].lstrip('\n')
 p.write_bytes((title+'\n\n'+prose(text)+'\n## Previous entries (historical; superseded for current status)\n\n'+MARK+'\n\n'+old).encode('utf-8'))
update('PROJECT_RECOVERY_STATUS.md','# ConfoSense current recovery status',front)
update('PANEL_RESPONSE_MATRIX.md','# ConfoSense current panel response status',front+'''
| Panel requirement | Current evidence | Remaining concrete work |
|---|---|---|
| LSTM versus XGBoost | Pilot retained; exact common-target13-horizon matrix and per-unit fit/level accounting generated | Generalized matched runner and prioritized192-unit queue; begin with the single energy unit above |
| Dataset/evaluation rationale | All three sparse tasks quantified; original groups, exposure, phases, nulls and applicability retained | Evaluate proposal C and matched forecasting; do not claim the original unsupported operational endpoint |
| Calibration/selection/alerts | Unchanged004 thresholds;005 context and reset contract; actual memberships/schedules verified | C method-preserving replay integration; no challenge-score retuning |
| Robustness and methods | Full1950-row interval-method matrix and separate900-cell obligation ledger retained | Validated DSCP/joint horizons, full methods, contamination, cascades, censoring and inference |
''')
current=front.replace('(SUPPORT_DESIGN_AUDIT.md)','(../SUPPORT_DESIGN_AUDIT.md)').replace('(AMENDMENT005_PROPOSAL.md)','(../AMENDMENT005_PROPOSAL.md)').replace('(REMAINING_STUDY_EXECUTION_PLAN.md)','(../REMAINING_STUDY_EXECUTION_PLAN.md)').replace('(review/support_design_20260913/EVIDENCE_INDEX.md)','(support_design_20260913/EVIDENCE_INDEX.md)')
current+='\nPublication branch: [review/support-design-20260913](https://github.com/jinchuntan/confosense/tree/review/support-design-20260913), descendant of `9b5acb49531ce12706285c3f040310c0ab6053dd`. The delivery response and branch history identify the final publication SHA. Production source remains `203f3babf66c98ac072ad450abec5ea7ce3d60473f02708fa64ac2102ea3f7c9`.\n'
update('review/CURRENT_EVIDENCE.md','# Current evidence: support design and executable study plan',current)
print('Updated current evidence, recovery status and panel response; history preserved')
