# Robustness evidence status

> Previously inspected test data remain previously inspected. A corrected rerun or additional seeds do not create an untouched holdout. Historical results require recomputation after the integration repairs; passing software tests does not establish scientific validity.

Core source: `outputs\final_dissertation_v2\runs\full_20260831_220811` — **historical_requires_rerun**.
Extension source: `outputs\final_dissertation_v2\runs\robx_full_20260902_080752` — **missing**.

Current numerical dissertation findings are not established by this report. See repository-root `INTEGRATION_REPAIR_REPORT.md` for repairs, unresolved design decisions and the required rerun.

A missing full extension supplies no fault, contamination or recovery results. Smoke cells verify execution only. Closed-loop fault absorption is a hypothesis to test, not an achievement established here.
A repaired full extension must verify every dataset/fold/seed/cell, retained prediction bounds, clean/zero identity, and group-specific recovery accounting.
