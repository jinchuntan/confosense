# Dissertation evidence status

> Previously inspected test data remain previously inspected. A corrected rerun or additional seeds do not create an untouched holdout. Historical results require recomputation after the integration repairs; passing software tests does not establish scientific validity.

Core source: `outputs\final_dissertation_v2\runs\full_20260831_220811` — **historical_requires_rerun**.
Extension source: `outputs\final_dissertation_v2\runs\robx_full_20260902_080752` — **missing**.

Current numerical dissertation findings are not established by this report. See repository-root `INTEGRATION_REPAIR_REPORT.md` for repairs, unresolved design decisions and the required rerun.

Historical accounting only; these are dispositions of the archived run, not feasibility findings for repaired code.
- bdg2: 0/15 archived units feasible; 15 `no_feasible_configuration` outcomes. Source: `metrics/OUTER_UNIT_LEDGER.csv`.
- pleia: 10/15 archived units feasible; 5 `no_feasible_configuration` outcomes. Source: `metrics/OUTER_UNIT_LEDGER.csv`.
- pleia_energy: 2/15 archived units feasible; 13 `no_feasible_configuration` outcomes. Source: `metrics/OUTER_UNIT_LEDGER.csv`.
- rico: 0/15 archived units feasible; 15 `no_feasible_configuration` outcomes. Source: `metrics/OUTER_UNIT_LEDGER.csv`.

No corrected CIs for the repaired execution are available. `final_cis.csv` is superseded statistically. `final_cis_corrected.csv` corrects historical inference but still describes the pre-repair computation. Neither supplies current findings.
BDG2 supports within-building temporal evaluation only. Equal-recall workload improvement, real-fault precision and unseen-building portability are not established.
